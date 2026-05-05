from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import os

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
    SendApplicationResponse,
    SentApplicationsResponse
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


router = APIRouter(
    prefix="/applications",
    tags=["Applications"]
)


def choose_cv_role_type(role: str) -> str:
    role_lower = role.lower()

    if "backend" in role_lower and "ai" in role_lower:
        return "backend_ai_engineer"

    if "backend" in role_lower:
        return "backend_ai_engineer"

    if (
        "ai" in role_lower
        or "machine learning" in role_lower
        or "ml" in role_lower
        or "yapay zeka" in role_lower
    ):
        return "ai_engineer"

    return "ai_engineer"


def choose_cv_file_path(role_type: str) -> str | None:
    if role_type == "backend_ai_engineer":
        return os.getenv("BACKEND_AI_ENGINEER_CV_PATH")

    if role_type == "ai_engineer":
        return os.getenv("AI_ENGINEER_CV_PATH")

    return None


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
    normalized_url = normalize_url(request.url)

    existing_company = (
        db.query(Company)
        .filter(Company.website == normalized_url)
        .first()
    )

    if existing_company:
        company = existing_company
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
            "contact_email": company_data.get("contact_email"),
        })

        company = Company(**company_data)

        db.add(company)
        db.commit()
        db.refresh(company)

    cv_role_type = choose_cv_role_type(request.role)

    cv = (
        db.query(CV)
        .filter(CV.role_type == cv_role_type)
        .filter(CV.is_active == True)
        .first()
    )

    if not cv:
        raise HTTPException(
            status_code=404,
            detail=f"No active CV found for role_type: {cv_role_type}"
        )

    result = generate_email(
        company=company,
        cv=cv,
        role=request.role,
        language=request.language
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

    if not company.contact_email:
        raise HTTPException(
            status_code=400,
            detail="Company contact email not found"
        )

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

    cv_path = choose_cv_file_path(application.role_type)

    try:
        send_real_email(
            to_email=company.contact_email,
            subject=generated_email.subject,
            body=generated_email.body,
            cv_path=cv_path
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Email could not be sent: {str(e)}"
        )

    application.status = "sent"
    generated_email.status = "sent"

    db.commit()
    db.refresh(application)
    db.refresh(generated_email)

    return {
        "application_id": application.id,
        "generated_email_id": generated_email.id,
        "status": "sent",
        "message": "Email sent successfully and saved"
    }