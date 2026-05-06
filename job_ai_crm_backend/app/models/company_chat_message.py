import uuid
from datetime import datetime

from sqlalchemy import Column, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID

from app.database import Base


class CompanyChatMessage(Base):
    __tablename__ = "company_chat_messages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    company_id = Column(
        UUID(as_uuid=True),
        ForeignKey("companies.id"),
        nullable=False
    )

    role = Column(String, nullable=False)  # user / assistant
    content = Column(Text, nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow)

    company = relationship("Company")