import uuid
from sqlalchemy import Column, String, Text, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from app.database import Base


class GeneratedEmail(Base):
    __tablename__ = "generated_emails"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    application_id = Column(UUID(as_uuid=True), ForeignKey("applications.id"), nullable=False)

    subject = Column(String(255), nullable=True)
    body = Column(Text, nullable=False)

    tone = Column(String(50), nullable=True)
    language = Column(String(20), nullable=True)

    status = Column(String(50), default="draft")

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())