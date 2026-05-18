import io
import re
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
    cvs = db.query(CV).filter(CV.is_active == True).order_by(CV.created_at.desc()).all()
    return [{"id": str(c.id), "title": c.title, "role_type": c.role_type} for c in cvs]


@router.post("/cvs")
async def upload_cv(
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

    role_type = re.sub(r"[^a-z0-9]+", "_", title.lower()).strip("_")

    file_data_b64 = base64.b64encode(content).decode("utf-8")
    cv = CV(title=title.strip(), role_type=role_type, content_text=text,
            file_data=file_data_b64, is_active=True)
    db.add(cv)
    db.commit()
    return {"ok": True, "id": str(cv.id), "title": cv.title, "chars": len(text)}


@router.delete("/cvs/{cv_id}")
def delete_cv(cv_id: str, db: Session = Depends(get_db)):
    cv = db.query(CV).filter(CV.id == cv_id).first()
    if not cv:
        raise HTTPException(status_code=404, detail="CV bulunamadı")
    db.delete(cv)
    db.commit()
    return {"ok": True}


def _extract_pdf_text(data: bytes) -> str:
    try:
        from pypdf import PdfReader
        reader = PdfReader(io.BytesIO(data))
        return "\n".join(page.extract_text() or "" for page in reader.pages)
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"PDF okunamadı: {e}")
