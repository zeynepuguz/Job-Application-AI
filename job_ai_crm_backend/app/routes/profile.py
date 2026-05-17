from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user_settings import UserSettings, SINGLETON_ID

router = APIRouter(prefix="/profile", tags=["profile"])


class AvatarPayload(BaseModel):
    avatar_data: str | None = None


@router.get("/avatar")
def get_avatar(db: Session = Depends(get_db)):
    row = db.get(UserSettings, SINGLETON_ID)
    return {"avatar_data": row.avatar_data if row else None}


@router.post("/avatar")
def set_avatar(payload: AvatarPayload, db: Session = Depends(get_db)):
    row = db.get(UserSettings, SINGLETON_ID)
    if row:
        row.avatar_data = payload.avatar_data
    else:
        row = UserSettings(id=SINGLETON_ID, avatar_data=payload.avatar_data)
        db.add(row)
    db.commit()
    return {"ok": True}
