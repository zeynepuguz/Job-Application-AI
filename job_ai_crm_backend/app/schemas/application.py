from pydantic import BaseModel
from uuid import UUID
from datetime import datetime


class SentApplicationItem(BaseModel):
    application_id: UUID
    generated_email_id: UUID
    company_name: str | None
    company_email: str | None
    role: str | None
    subject: str | None
    body: str
    status: str
    sent_at: datetime | None


class SentApplicationsResponse(BaseModel):
    applications: list[SentApplicationItem]

class PrepareApplicationRequest(BaseModel):
    url: str | None = None
    company_id: UUID | None = None
    role: str
    language: str | None = None


class PrepareApplicationResponse(BaseModel):
    application_id: UUID
    company_id: UUID
    generated_email_id: UUID
    contact_email: str | None
    subject: str
    body: str
    status: str


class RefineEmailRequest(BaseModel):
    instruction: str


class RefineEmailResponse(BaseModel):
    application_id: UUID
    generated_email_id: UUID
    subject: str
    body: str
    status: str


class SendApplicationResponse(BaseModel):
    application_id: UUID
    generated_email_id: UUID
    status: str
    message: str


class UpdateContactEmailRequest(BaseModel):
    contact_email: str


class UpdateContactEmailResponse(BaseModel):
    application_id: UUID
    company_id: UUID
    contact_email: str

