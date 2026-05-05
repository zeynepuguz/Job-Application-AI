# Job AI CRM — Backend

AI destekli iş başvuru takibi: şirket web sitesinden bilgi çıkarma, başvuru ve kişiselleştirilmiş e-posta üretimi, isteğe bağlı düzeltme ve Gmail üzerinden gönderim. API, **FastAPI** ve **PostgreSQL** üzerinde çalışır.

## Özellikler

- **Şirketler:** Manuel kayıt veya URL ile site içeriğini çekip (BeautifulSoup) yapılandırılmış alanlar + OpenAI ile zenginleştirme (`/companies`).
- **Başvurular:** Verilen URL ve hedef rol için aktif CV seçimi, AI ile konu ve gövde üretimi, taslak olarak veritabanına yazma (`/applications/prepare`).
- **E-posta iyileştirme:** Doğal dil talimatıyla konu/gövde güncelleme (`/applications/{id}/refine-email`).
- **Gönderim:** SMTP (Gmail) ile ileti ve rol tipine göre PDF CV eki (`/applications/{id}/send`).

## Gereksinimler

- Python 3.10+
- PostgreSQL
- OpenAI API anahtarı
- Gmail için uygulama şifresi (SMTP)

## Kurulum

```bash
python -m venv .venv
.venv\Scripts\activate
pip install fastapi uvicorn sqlalchemy psycopg2-binary python-dotenv pydantic openai requests beautifulsoup4
```

Proje kökünde `.env` dosyası oluşturun (örnek değişkenler aşağıda). Veritabanı tabloları için repoda Alembic yok; şemayı kendi sürecinizle oluşturmanız gerekir (ör. SQL ile veya bir kerelik `Base.metadata.create_all(engine)` script’i).

Uygulamayı çalıştırma:

```bash
uvicorn app.main:app --reload
```

- API: `http://127.0.0.1:8000`
- Swagger: `http://127.0.0.1:8000/docs`

## Ortam değişkenleri (`.env`)

| Değişken | Açıklama |
|----------|----------|
| `DATABASE_URL` | PostgreSQL bağlantı URL’si (örn. `postgresql://user:pass@localhost:5432/dbname`) |
| `OPENAI_API_KEY` | OpenAI istemcisi için |
| `SMTP_EMAIL` | Gönderen Gmail adresi |
| `SMTP_APP_PASSWORD` | Gmail uygulama şifresi |
| `AI_ENGINEER_CV_PATH` | `ai_engineer` rolü için PDF CV dosya yolu |
| `BACKEND_AI_ENGINEER_CV_PATH` | `backend_ai_engineer` rolü için PDF CV dosya yolu |

`.env` ve `CVs/` gibi hassas/yerel dosyalar `.gitignore` içindedir.

## API özeti

| Yöntem | Yol | Açıklama |
|--------|-----|----------|
| `GET` | `/` | Sağlık kontrolü |
| `POST` | `/companies/` | Şirket oluştur |
| `GET` | `/companies/` | Tüm şirketleri listele |
| `POST` | `/companies/analyze-url` | URL’den site metni + AI analizi ile şirket kaydı |
| `POST` | `/applications/prepare` | URL, `role`, isteğe bağlı `language` — başvuru + taslak e-posta |
| `POST` | `/applications/{application_id}/refine-email` | Gövde/konu iyileştirme (`instruction`) |
| `POST` | `/applications/{application_id}/send` | E-postayı gönder, durumu `sent` yap |

**Not:** `prepare` akışı, veritabanında `is_active = true` ve uygun `role_type` (`ai_engineer` veya `backend_ai_engineer`) ile bir **CV** kaydı bekler. Rol metni içinde “backend” geçerse `backend_ai_engineer` seçilir; aksi halde `ai_engineer`. Gönderimde ilgili `*_CV_PATH` ile PDF eklenir.

## Proje yapısı

```
app/
  main.py           # FastAPI uygulaması ve router’lar
  database.py       # SQLAlchemy engine ve session
  models/           # Tablo modelleri (companies, cvs, applications, generated_emails)
  schemas/          # Pydantic şemaları
  routes/           # companies, applications
  services/         # url_analyzer, ai_analyzer, email_generator, email_refiner, mail_sender
```

## Lisans

Belirtilmemiş; depo sahibinin tercihine göre eklenebilir.
