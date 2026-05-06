from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text

from app.database import SessionLocal
from app.routes.companies import router as companies_router
from app.routes import applications

from app.models.company import Company
from app.models.application import Application
from app.models.company_chat_message import CompanyChatMessage

from dotenv import load_dotenv

load_dotenv()

app = FastAPI(
    title="Job AI CRM API",
    description="AI destekli iş başvuru takip ve mail üretme sistemi",
    version="1.0.0"
)

app.include_router(companies_router)
app.include_router(applications.router)


def cleanup_duplicate_companies_by_email() -> None:
    db = SessionLocal()
    try:
        db.execute(text("""
            WITH ranked AS (
                SELECT
                    id,
                    lower(trim(contact_email)) AS email_key,
                    created_at,
                    ROW_NUMBER() OVER (
                        PARTITION BY lower(trim(contact_email))
                        ORDER BY created_at ASC, id ASC
                    ) AS rn,
                    FIRST_VALUE(id) OVER (
                        PARTITION BY lower(trim(contact_email))
                        ORDER BY created_at ASC, id ASC
                    ) AS keep_id
                FROM companies
                WHERE contact_email IS NOT NULL
                  AND trim(contact_email) <> ''
            )
            UPDATE applications a
            SET company_id = r.keep_id
            FROM ranked r
            WHERE a.company_id = r.id
              AND r.rn > 1;
        """))

        db.execute(text("""
            WITH ranked AS (
                SELECT
                    id,
                    ROW_NUMBER() OVER (
                        PARTITION BY lower(trim(contact_email))
                        ORDER BY created_at ASC, id ASC
                    ) AS rn
                FROM companies
                WHERE contact_email IS NOT NULL
                  AND trim(contact_email) <> ''
            )
            DELETE FROM companies c
            USING ranked r
            WHERE c.id = r.id
              AND r.rn > 1;
        """))
        db.execute(text("""
            CREATE UNIQUE INDEX IF NOT EXISTS uq_companies_contact_email_normalized
            ON companies (lower(trim(contact_email)))
            WHERE contact_email IS NOT NULL AND trim(contact_email) <> '';
        """))
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


@app.on_event("startup")
def startup_cleanup_duplicate_companies() -> None:
    cleanup_duplicate_companies_by_email()

# Frontend'i backend portundan da servis et.
# Boylece /applications.html gibi sayfalar, Vite portu karisikliklarinda bile acilir.
frontend_dir = Path(__file__).resolve().parents[2] / "job_ai_crm_frontend"
if frontend_dir.exists():
    app.mount("/", StaticFiles(directory=str(frontend_dir), html=True), name="frontend")
