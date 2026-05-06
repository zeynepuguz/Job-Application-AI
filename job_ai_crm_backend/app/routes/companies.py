from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
import re

from app.database import get_db
from app.models.company import Company
from app.schemas.company import (
    CompanyCreate,
    CompanyAnalyzeRequest,
    CompanyResponse,
    CompanyContactEmailUpdateRequest,
    CompanyContactEmailUpdateResponse
)
from app.services.url_analyzer import (
    fetch_website_text,
    extract_company_data_from_text,
    normalize_url
)
from app.services.ai_analyzer import analyze_with_ai


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
        print("AI RESULT:", ai_data)

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
        print("AI ERROR:", e)
        raise HTTPException(status_code=500, detail=str(e))

    existing_by_email = get_existing_company_by_email(db, company_data.get("contact_email"))
    if existing_by_email:
        raise HTTPException(status_code=409, detail="Bu şirket zaten kayıtlı")

    company_data["contact_email"] = normalize_email(company_data.get("contact_email"))
    company = Company(**company_data)

    db.add(company)
    db.commit()
    db.refresh(company)

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