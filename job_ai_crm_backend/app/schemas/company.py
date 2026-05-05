from pydantic import BaseModel
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