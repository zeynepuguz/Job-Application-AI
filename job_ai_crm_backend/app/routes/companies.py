from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.company import Company
from app.schemas.company import (
    CompanyCreate,
    CompanyAnalyzeRequest,
    CompanyResponse
)
from app.services.url_analyzer import (
    fetch_website_text,
    extract_company_data_from_text
)
from app.services.ai_analyzer import analyze_with_ai


router = APIRouter(
    prefix="/companies",
    tags=["Companies"]
)


@router.post("/", response_model=CompanyResponse)
def create_company(
    company_data: CompanyCreate,
    db: Session = Depends(get_db)
):
    company = Company(**company_data.model_dump())

    db.add(company)
    db.commit()
    db.refresh(company)

    return company


@router.get("/", response_model=list[CompanyResponse])
def get_companies(db: Session = Depends(get_db)):
    return db.query(Company).all()


@router.post("/analyze-url", response_model=CompanyResponse)
def analyze_company_url(
    request: CompanyAnalyzeRequest,
    db: Session = Depends(get_db)
):
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
        })

    except Exception as e:
        print("AI ERROR:", e)
        raise HTTPException(status_code=500, detail=str(e))

    company = Company(**company_data)

    db.add(company)
    db.commit()
    db.refresh(company)

    return company