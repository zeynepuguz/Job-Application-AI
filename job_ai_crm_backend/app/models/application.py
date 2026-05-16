import uuid
from sqlalchemy import Column, String, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from app.database import Base


class Application(Base):
    __tablename__ = "applications"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False)
    cv_id = Column(UUID(as_uuid=True), ForeignKey("cvs.id"), nullable=True)

    role_type = Column(String(50), nullable=False)
    position_title = Column(String(255), nullable=True)

    status = Column(String(50), default="email_generated")
    source = Column(String(100), nullable=True)

    applied_at = Column(DateTime(timezone=True), nullable=True)
    notes = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())