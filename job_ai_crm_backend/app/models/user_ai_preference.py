import uuid

from sqlalchemy import Column, String, DateTime, JSON
from sqlalchemy.sql import func

from app.database import Base


class UserAIPreference(Base):
    __tablename__ = "user_ai_preferences"

    id = Column(
        String,
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )

    preferred_tone = Column(
        String,
        nullable=False,
        default="natural"
    )

    email_length = Column(
        String,
        nullable=False,
        default="short"
    )

    preferred_focus = Column(
        String,
        nullable=True
    )

    avoid_phrases = Column(
        JSON,
        nullable=True,
        default=list
    )

    preferred_language = Column(
        String,
        nullable=False,
        default="tr"
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )

    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )