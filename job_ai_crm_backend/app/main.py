from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.routes.companies import router as companies_router
from app.routes import applications
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(
    title="Job AI CRM API",
    description="AI destekli iş başvuru takip ve mail üretme sistemi",
    version="1.0.0"
)

app.include_router(companies_router)
app.include_router(applications.router)

# Frontend'i backend portundan da servis et.
# Boylece /applications.html gibi sayfalar, Vite portu karisikliklarinda bile acilir.
frontend_dir = Path(__file__).resolve().parents[2] / "job_ai_crm_frontend"
if frontend_dir.exists():
    app.mount("/", StaticFiles(directory=str(frontend_dir), html=True), name="frontend")
