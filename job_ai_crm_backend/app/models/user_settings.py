from sqlalchemy import Column, String, Text, DateTime
from sqlalchemy.sql import func

from app.database import Base

SINGLETON_ID = "singleton"


class UserSettings(Base):
    __tablename__ = "user_settings"

    id = Column(String, primary_key=True, default=SINGLETON_ID)
    avatar_data = Column(Text, nullable=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
