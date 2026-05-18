from fastapi import APIRouter, Depends, HTTPException, Body, UploadFile, File, Form
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
import os
import re
import tempfile
import shutil

from app.database import get_db
from app.models.company import Company
from app.models.cv import CV
from app.models.application import Application
from app.models.generated_email import GeneratedEmail

from app.schemas.application import (
    PrepareApplicationRequest,
    PrepareApplicationResponse,
    RefineEmailRequest,
    RefineEmailResponse,
    SendApplicationRequest,
    SendApplicationResponse,
    SentApplicationsResponse,
    UpdateContactEmailRequest,
    UpdateContactEmailResponse,
    ApplicationStatusUpdateRequest,
    ApplicationStatusUpdateResponse,
    VALID_STATUSES,
)

from app.services.url_analyzer import (
    fetch_website_text,
    extract_company_data_from_text,
    normalize_url
)
from app.services.ai_analyzer import analyze_with_ai
from app.services.email_generator import generate_email
from app.services.email_refiner import refine_email
from app.services.mail_sender import send_real_email
from app.services.vector_store import upsert_company_text, search_company_context
from app.services.company_chat import answer_company_question
from app.services.user_learning import learn_from_sent_email, learn_from_refine_instruction
router = APIRouter(
    prefix="/applications",
    tags=["Applications"]
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


def choose_best_cv(db: Session, role: str):
    cvs = db.query(CV).filter(CV.is_active == True).all()
    if not cvs:
        return None
    if len(cvs) == 1:
        return cvs[0]

    role_words = set(w for w in role.lower().split() if len(w) > 2)
    best, best_score = cvs[0], -1
    for cv in cvs:
        title_lower = (cv.title or "").lower()
        score = sum(1 for w in role_words if w in title_lower)
        if score > best_score:
            best_score, best = score, cv
    return best


@router.get("/sent", response_model=SentApplicationsResponse)
def get_sent_applications(db: Session = Depends(get_db)):
    rows = (
        db.query(Application, GeneratedEmail, Company)
        .join(GeneratedEmail, GeneratedEmail.application_id == Application.id)
        .join(Company, Company.id == Application.company_id)
        .filter(Application.status == "sent")
        .order_by(Application.updated_at.desc())
        .all()
    )

    applications = []

    for application, generated_email, company in rows:
        applications.append({
            "application_id": application.id,
            "generated_email_id": generated_email.id,
            "company_name": company.name,
            "company_email": company.contact_email,
            "role": application.position_title,
            "subject": generated_email.subject,
            "body": generated_email.body,
            "status": application.status,
            "sent_at": application.updated_at
        })

    return {
        "applications": applications
    }

@router.post("/prepare", response_model=PrepareApplicationResponse)
def prepare_application(
    request: PrepareApplicationRequest,
    db: Session = Depends(get_db)
):
    if not request.url and not request.company_id:
        raise HTTPException(
            status_code=400,
            detail="Either url or company_id is required"
        )

    if request.company_id:
        company = (
            db.query(Company)
            .filter(Company.id == request.company_id)
            .first()
        )

        if not company:
            raise HTTPException(status_code=404, detail="Company not found")

    else:
        normalized_url = normalize_url(request.url)

        existing_company = (
            db.query(Company)
            .filter(Company.website == normalized_url)
            .first()
        )

        if existing_company:
            raise HTTPException(status_code=409, detail="Bu şirket zaten kayıtlı")
        else:
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

            ai_data = analyze_with_ai(text, request.url)

            company_data.update({
                "name": ai_data.get("name") or company_data["name"],
                "industry": ai_data.get("industry") or company_data.get("industry"),
                "country": company_data.get("country") or ai_data.get("country"),
                "city": company_data.get("city") or ai_data.get("city"),
                "description": ai_data.get("description") or company_data.get("description"),
                "ai_summary": ai_data.get("summary") or company_data.get("ai_summary"),
                "contact_email": company_data.get("contact_email") or ai_data.get("contact_email"),
            })

            existing_by_email = get_existing_company_by_email(
                db,
                company_data.get("contact_email")
            )
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
            except Exception as e:
                print("PINECONE UPSERT ERROR:", e)

    if request.cv_id:
        cv = db.query(CV).filter(CV.id == request.cv_id, CV.is_active == True).first()
        if not cv:
            cv = choose_best_cv(db, request.role)
    else:
        cv = choose_best_cv(db, request.role)

    if not cv:
        raise HTTPException(
            status_code=404,
            detail="Aktif CV bulunamadı. Lütfen ⚙️ menüsünden CV yükleyin."
        )

    result = generate_email(
        company=company,
        cv=cv,
        role=request.role,
        language=request.language,
        user_instruction=request.user_instruction,
    )

    application = Application(
        company_id=company.id,
        cv_id=cv.id,
        role_type=cv.role_type,
        position_title=request.role,
        status="draft",
        source=company.website
    )

    db.add(application)
    db.commit()
    db.refresh(application)

    email_language = request.language or "tr"

    generated_email = GeneratedEmail(
        application_id=application.id,
        subject=result["subject"],
        body=result["body"],
        tone="professional",
        language=email_language,
        status="draft"
    )

    db.add(generated_email)
    db.commit()
    db.refresh(generated_email)

    return {
        "application_id": application.id,
        "company_id": company.id,
        "generated_email_id": generated_email.id,
        "contact_email": company.contact_email,
        "subject": generated_email.subject,
        "body": generated_email.body,
        "status": generated_email.status
    }


@router.post("/{application_id}/refine-email", response_model=RefineEmailResponse)
def refine_application_email(
    application_id: str,
    request: RefineEmailRequest,
    db: Session = Depends(get_db)
):
    application = (
        db.query(Application)
        .filter(Application.id == application_id)
        .first()
    )

    if not application:
        raise HTTPException(status_code=404, detail="Application not found")

    if application.status == "sent":
        raise HTTPException(
            status_code=400,
            detail="Sent applications cannot be refined"
        )

    generated_email = (
        db.query(GeneratedEmail)
        .filter(GeneratedEmail.application_id == application.id)
        .first()
    )

    if not generated_email:
        raise HTTPException(status_code=404, detail="Generated email not found")

    result = refine_email(
        current_subject=generated_email.subject,
        current_body=generated_email.body,
        instruction=request.instruction
    )

    if not result:
        raise HTTPException(status_code=500, detail="Refine email failed")

    generated_email.subject = result.get("subject", generated_email.subject)
    generated_email.body = result.get("body", generated_email.body)
    generated_email.status = "draft"
    application.status = "draft"

    db.commit()
    db.refresh(generated_email)
    db.refresh(application)

    try:
        learn_from_refine_instruction(db, request.instruction)
    except Exception:
        pass

    return {
        "application_id": application.id,
        "generated_email_id": generated_email.id,
        "subject": generated_email.subject,
        "body": generated_email.body,
        "status": generated_email.status
    }


@router.post("/{application_id}/send", response_model=SendApplicationResponse)
def send_application(
    application_id: str,
    subject: str | None = Form(default=None),
    body: str | None = Form(default=None),
    to_email: str | None = Form(default=None),
    extra_file: UploadFile | None = File(default=None),
    db: Session = Depends(get_db)
):
    application = (
        db.query(Application)
        .filter(Application.id == application_id)
        .first()
    )

    if not application:
        raise HTTPException(status_code=404, detail="Application not found")

    company = (
        db.query(Company)
        .filter(Company.id == application.company_id)
        .first()
    )

    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    generated_email = (
        db.query(GeneratedEmail)
        .filter(GeneratedEmail.application_id == application.id)
        .first()
    )

    if not generated_email:
        raise HTTPException(status_code=404, detail="Generated email not found")

    if application.status == "sent":
        raise HTTPException(
            status_code=400,
            detail="This application has already been sent"
        )

    if subject and subject.strip():
        generated_email.subject = subject.strip()

    if body and body.strip():
        generated_email.body = body.strip()

    resolved_to = None
    if to_email and str(to_email).strip():
        resolved_to = str(to_email).strip()
    elif company.contact_email:
        resolved_to = str(company.contact_email).strip()

    if not resolved_to:
        raise HTTPException(
            status_code=400,
            detail="Alıcı e-postası bulunamadı. Önizlemede alıcı alanını doldurun veya şirket kaydına iletişim ekleyin."
        )

    db_cv = db.query(CV).filter(CV.id == application.cv_id).first()
    if not db_cv:
        db_cv = db.query(CV).filter(CV.is_active == True).first()
    cv_file_data = db_cv.file_data if db_cv else None
    cv_filename = f"{db_cv.title}.pdf" if db_cv else "CV.pdf"
    cv_path = None

    extra_path = None
    tmp_dir = None
    if extra_file and extra_file.filename:
        tmp_dir = tempfile.mkdtemp()
        extra_path = os.path.join(tmp_dir, extra_file.filename)
        with open(extra_path, "wb") as f:
            shutil.copyfileobj(extra_file.file, f)

    try:
        send_real_email(
            to_email=resolved_to,
            subject=generated_email.subject,
            body=generated_email.body,
            cv_path=cv_path,
            extra_attachment_path=extra_path,
            cv_file_data=cv_file_data,
            cv_filename=cv_filename,
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Email could not be sent: {str(e)}"
        )
    finally:
        if tmp_dir:
            shutil.rmtree(tmp_dir, ignore_errors=True)

    application.status = "sent"
    generated_email.status = "sent"

    db.commit()
    db.refresh(application)
    db.refresh(generated_email)

    try:
        learn_from_sent_email(db, generated_email)
    except Exception:
        pass

    return {
        "application_id": application.id,
        "generated_email_id": generated_email.id,
        "status": "sent",
        "message": "Email sent successfully and saved"
    }


@router.patch("/{application_id}/status", response_model=ApplicationStatusUpdateResponse)
def update_application_status(
    application_id: str,
    request: ApplicationStatusUpdateRequest,
    db: Session = Depends(get_db)
):
    if request.status not in VALID_STATUSES:
        raise HTTPException(
            status_code=400,
            detail=f"Geçersiz durum. Geçerli değerler: {', '.join(VALID_STATUSES)}"
        )

    application = (
        db.query(Application)
        .filter(Application.id == application_id)
        .first()
    )
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")

    application.status = request.status
    if request.notes is not None:
        application.notes = request.notes

    db.commit()
    db.refresh(application)

    return {
        "application_id": application.id,
        "status": application.status,
        "notes": application.notes,
    }


@router.post("/{application_id}/contact-email", response_model=UpdateContactEmailResponse)
def update_application_contact_email(
    application_id: str,
    request: UpdateContactEmailRequest,
    db: Session = Depends(get_db)
):
    application = (
        db.query(Application)
        .filter(Application.id == application_id)
        .first()
    )
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")

    company = (
        db.query(Company)
        .filter(Company.id == application.company_id)
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
        "application_id": application.id,
        "company_id": company.id,
        "contact_email": company.contact_email
    }