from fastapi import APIRouter, Depends, HTTPException
from app.models.generated_email import GeneratedEmail
from app.services.email_history import get_recent_email_patterns
from sqlalchemy.orm import Session
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError

import re

from app.database import get_db
from app.models.company_chat_message import CompanyChatMessage
from app.models.company import Company
from app.models.application import Application
from app.models.cv import CV
from app.schemas.company import (
    CompanyCreate,
    CompanyAnalyzeRequest,
    CompanyResponse,
    CompanyContactEmailUpdateRequest,
    CompanyContactEmailUpdateResponse,
    CompanyChatRequest,
    CompanyChatResponse,
    ApplicationEmailRequest,
    ApplicationEmailResponse
)
from app.services.url_analyzer import (
    fetch_website_text,
    extract_company_data_from_text,
    normalize_url
)
from app.services.ai_analyzer import analyze_with_ai
from app.services.vector_store import upsert_company_text
from app.services.company_chat import answer_company_question
from app.services.ai_agents.orchestrator import generate_agentic_email
from app.services.ai_agents.portfolio_utils import resolve_portfolio_url
from app.services.user_ai_memory import get_or_create_ai_preferences

router = APIRouter(
    prefix="/companies",
    tags=["Companies"]
)


def normalize_email(email: str | None) -> str | None:
    if not email:
        return None
    normalized = email.strip().lower()
    return normalized or None


def get_existing_company_by_email(db: Session, email: str | None):
    normalized_email = normalize_email(email)
    if not normalized_email:
        return None
    return (
        db.query(Company)
        .filter(Company.contact_email.isnot(None))
        .filter(Company.contact_email.ilike(normalized_email))
        .first()
    )


def is_valid_email(email: str) -> bool:
    return bool(re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email))


@router.get("/", response_model=list[CompanyResponse])
def get_companies(db: Session = Depends(get_db)):
    companies = db.query(Company).all()
    unique_companies = []
    seen_emails = set()

    for company in companies:
        normalized_email = normalize_email(company.contact_email)
        if normalized_email:
            if normalized_email in seen_emails:
                continue
            seen_emails.add(normalized_email)
        unique_companies.append(company)

    return unique_companies


@router.post("/analyze-url", response_model=CompanyResponse)
def analyze_company_url(
    request: CompanyAnalyzeRequest,
    db: Session = Depends(get_db)
):
    normalized_url = normalize_url(request.url)

    existing_company = (
        db.query(Company)
        .filter(Company.website == normalized_url)
        .first()
    )

    if existing_company:
        raise HTTPException(status_code=409, detail="Bu şirket zaten kayıtlı")

    text = fetch_website_text(request.url)

    if not text:
        raise HTTPException(
            status_code=400,
            detail="Website content could not be fetched"
        )

    company_data = extract_company_data_from_text(
        url=request.url,
        text=text
    )

    try:
        ai_data = analyze_with_ai(text, request.url)
        company_data.update({
            "name": ai_data.get("name") or company_data["name"],
            "industry": ai_data.get("industry") or company_data.get("industry"),
            "country": company_data.get("country") or ai_data.get("country"),
            "city": company_data.get("city") or ai_data.get("city"),
            "description": ai_data.get("description") or company_data.get("description"),
            "ai_summary": ai_data.get("summary") or company_data.get("ai_summary"),
            "contact_email": company_data.get("contact_email"),
            "website": normalized_url,
            "source_url": normalized_url,
        })

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    existing_by_email = get_existing_company_by_email(db, company_data.get("contact_email"))
    if existing_by_email:
        raise HTTPException(status_code=409, detail="Bu şirket zaten kayıtlı")

    company_data["contact_email"] = normalize_email(company_data.get("contact_email"))
    company = Company(**company_data)

    db.add(company)
    db.commit()
    db.refresh(company)

    try:
        upsert_company_text(
            company_id=str(company.id),
            website=company.website,
            text=text
        )
    except Exception:
        pass

    return company


@router.post("/{company_id}/contact-email", response_model=CompanyContactEmailUpdateResponse)
def update_company_contact_email(
    company_id: str,
    request: CompanyContactEmailUpdateRequest,
    db: Session = Depends(get_db)
):
    company = (
        db.query(Company)
        .filter(Company.id == company_id)
        .first()
    )
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    normalized_email = normalize_email(request.contact_email)
    if not normalized_email:
        raise HTTPException(status_code=400, detail="Geçerli bir e-posta girin")
    if not is_valid_email(normalized_email):
        raise HTTPException(status_code=400, detail="E-posta formatı geçersiz")

    company.contact_email = normalized_email
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Bu şirket zaten kayıtlı")
    db.refresh(company)

    return {
        "company_id": company.id,
        "contact_email": company.contact_email
    }


@router.post("/{company_id}/chat", response_model = CompanyChatResponse)
def chat_with_company(
    company_id: str,
    request: CompanyChatRequest,
    db: Session = Depends(get_db)
):
    company = (
        db.query(Company)
        .filter(Company.id == company_id)
        .first()
    )

    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    answer = answer_company_question(
    db=db,
    company_id=str(company.id),
    question=request.question
    )

    return {
        "company_id": company.id,
        "question": request.question,
        "answer": answer
    }

@router.delete("/{company_id}/chat")
def clear_company_chat(
    company_id: str,
    db: Session = Depends(get_db)
):
    company = (
        db.query(Company)
        .filter(Company.id == company_id)
        .first()
    )

    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    db.query(CompanyChatMessage).filter(
        CompanyChatMessage.company_id == company.id
    ).delete()

    db.commit()

    return {
        "message": "Company chat history cleared successfully"
    }

@router.post("/generate-application-email", response_model=ApplicationEmailResponse)
def generate_application_email(
    request: ApplicationEmailRequest,
    db: Session = Depends(get_db)
):
    job_desc = (request.job_description or "").strip()
    company_name = (request.company_name or "").strip()
    has_anchor = bool(company_name or request.recipient_email or job_desc)

    if not has_anchor:
        raise HTTPException(
            status_code=400,
            detail="Şirket adı, alıcı e-postası veya iş ilanı metninden en az biri gereklidir."
        )

    if (
        request.recipient_email
        and not company_name
        and not job_desc
        and not (request.user_instruction or "").strip()
    ):
        raise HTTPException(
            status_code=400,
            detail="User instruction is required when only recipient email is provided"
        )

    memory = get_or_create_ai_preferences(db)

    memory_payload = {
        "preferred_tone": memory.preferred_tone,
        "email_length": memory.email_length,
        "preferred_focus": memory.preferred_focus,
        "avoid_phrases": memory.avoid_phrases,
        "preferred_language": memory.preferred_language,
    }

    recent_email_patterns = get_recent_email_patterns(
        db=db,
        limit=5,
    )

    portfolio_url = resolve_portfolio_url(
        request.portfolio_url,
        request.job_description,
        request.user_instruction,
    )

    mail_language = (request.language or "tr").strip() or "tr"

    cv = None
    if request.cv_id:
        cv = db.query(CV).filter(CV.id == request.cv_id, CV.is_active == True).first()
    if not cv:
        cvs = db.query(CV).filter(CV.is_active == True).all()
        if not cvs:
            raise HTTPException(status_code=404, detail="Aktif CV bulunamadı. Lütfen ⚙️ menüsünden CV yükleyin.")
        role_text = (request.position or "").lower()
        best, best_score = cvs[0], -1
        for c in cvs:
            words = set(w for w in (c.title or "").lower().split() if len(w) > 2)
            score = sum(1 for w in words if w in role_text)
            if score > best_score:
                best_score, best = score, c
        cv = best

    agent_result = generate_agentic_email(
        company_name=company_name or None,
        role=request.position,
        job_description=request.job_description,
        user_instruction=request.user_instruction,
        memory=memory_payload,
        recipient_email=request.recipient_email,
        recent_email_patterns=recent_email_patterns,
        portfolio_url=portfolio_url,
        language=mail_language,
        cv_text=cv.content_text if cv else None,
    )

    email_body = agent_result["body"]
    subject = (agent_result.get("subject") or "").strip() or (
        "Job Application" if mail_language.lower() in ("en", "english") else "İş Başvurusu"
    )

    display_name = (company_name or "İş başvurusu")[:255] or "İş başvurusu"

    recipient_email = (
        str(request.recipient_email).strip().lower()
        if request.recipient_email
        else None
    )

    company_row = None

    if recipient_email:
        company_row = (
            db.query(Company)
            .filter(func.lower(func.trim(Company.contact_email)) == recipient_email)
            .first()
        )

    if not company_row and company_name:
        company_row = (
            db.query(Company)
            .filter(func.lower(func.trim(Company.name)) == company_name.strip().lower())
            .first()
        )

    if not company_row:
        company_row = Company(
            name=display_name,
            website=None,
            contact_email=recipient_email,
            notes="generate-application-email",
        )
        db.add(company_row)

        try:
            db.flush()
        except IntegrityError:
            db.rollback()

            if recipient_email:
                company_row = (
                    db.query(Company)
                    .filter(func.lower(func.trim(Company.contact_email)) == recipient_email)
                    .first()
                )

            if not company_row:
                raise HTTPException(
                    status_code=409,
                    detail="Bu e-posta ile kayıtlı şirket zaten var ama mevcut kayıt okunamadı."
                )

    application_row = Application(
        company_id=company_row.id,
        cv_id=cv.id,
        role_type=cv.role_type,
        position_title=request.position,
        status="draft",
        source="agent_email",
    )
    db.add(application_row)
    db.flush()

    generated_email = GeneratedEmail(
        application_id=application_row.id,
        subject=subject,
        body=email_body,
        tone="natural",
        language=mail_language,
        status="draft",

        strategy=agent_result.get("strategy"),
        review=agent_result.get("review"),
        job_analysis=agent_result.get("job_analysis"),
        rewrite_count=agent_result.get("rewrite_count", 0),
    )

    db.add(generated_email)
    db.commit()
    db.refresh(generated_email)
    db.refresh(application_row)
    db.refresh(company_row)

    return ApplicationEmailResponse(
        id=str(generated_email.id),
        application_id=str(application_row.id),
        company_id=str(company_row.id),
        subject=generated_email.subject,
        body=generated_email.body,
        recipient_email=recipient_email,
    )