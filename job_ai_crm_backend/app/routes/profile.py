import io
import base64
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user_settings import UserSettings, SINGLETON_ID
from app.models.cv import CV

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


@router.get("/cvs")
def list_cvs(db: Session = Depends(get_db)):
    cvs = db.query(CV).all()
    return [{"id": str(c.id), "title": c.title, "role_type": c.role_type, "is_active": c.is_active} for c in cvs]


@router.post("/cvs")
async def upload_cv(
    role_type: str = Form(...),
    title: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Sadece PDF dosyası yüklenebilir.")

    content = await file.read()
    text = _extract_pdf_text(content)
    if not text.strip():
        raise HTTPException(status_code=400, detail="PDF'ten metin çıkarılamadı.")

    db.query(CV).filter(CV.role_type == role_type).delete()

    file_data_b64 = base64.b64encode(content).decode("utf-8")
    cv = CV(title=title, role_type=role_type, content_text=text,
            file_data=file_data_b64, is_active=True)
    db.add(cv)
    db.commit()
    return {"ok": True, "role_type": role_type, "chars": len(text)}


def _extract_pdf_text(data: bytes) -> str:
    try:
        from pypdf import PdfReader
        reader = PdfReader(io.BytesIO(data))
        return "\n".join(page.extract_text() or "" for page in reader.pages)
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"PDF okunamadı: {e}")
