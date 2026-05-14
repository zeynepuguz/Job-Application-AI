from pydantic import BaseModel, EmailStr
from typing import Optional
from uuid import UUID
from datetime import datetime


class CompanyCreate(BaseModel):
    name: str
    website: Optional[str] = None
    country: Optional[str] = None
    city: Optional[str] = None
    work_mode: Optional[str] = None
    contact_email: Optional[str] = None
    industry: Optional[str] = None
    notes: Optional[str] = None


class CompanyAnalyzeRequest(BaseModel):
    url: str


class CompanyResponse(BaseModel):
    id: UUID
    name: str
    website: Optional[str] = None
    country: Optional[str] = None
    city: Optional[str] = None
    work_mode: Optional[str] = None
    contact_email: Optional[str] = None
    industry: Optional[str] = None
    notes: Optional[str] = None
    source_url: Optional[str] = None
    description: Optional[str] = None
    ai_summary: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CompanyContactEmailUpdateRequest(BaseModel):
    contact_email: str


class CompanyContactEmailUpdateResponse(BaseModel):
    company_id: UUID
    contact_email: str


class CompanyChatRequest(BaseModel):
    question: str


class CompanyChatResponse(BaseModel):
    company_id: UUID
    question: str
    answer: str



class ApplicationEmailRequest(BaseModel):
    company_name: Optional[str] = None
    position: Optional[str] = None
    recipient_email: Optional[EmailStr] = None
    job_description: Optional[str] = None
    user_instruction: Optional[str] = None
    cv_role_type: Optional[str] = None


class ApplicationEmailResponse(BaseModel):
    id: str
    application_id: Optional[str] = None
    company_id: Optional[str] = None
    subject: str
    body: str
    recipient_email: Optional[str] = None