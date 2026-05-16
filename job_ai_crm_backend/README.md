# Job AI CRM — Backend

FastAPI tabanlı API ve AI agent pipeline katmanı. OpenAI + Pinecone ile CV analizi, strateji belirleme, e-posta üretimi/review/refine ve RAG tabanlı şirket chatbotu sağlar.

## Teknolojiler

- FastAPI + Uvicorn
- SQLAlchemy + PostgreSQL
- OpenAI GPT-4o-mini (chat completions + embeddings)
- Pinecone (vector database)
- Requests + BeautifulSoup
- SMTP (Gmail)

## AI Agent Pipeline

`Mail / ilan ile üret` akışında çalışır:

```
İş İlanı + Hedef Rol
        ↓
  job_analyzer          → İlan türü, şirket bağlamı, alan tespiti
        ↓
  email_strategy_agent  → Ton, uzunluk, email tipi belirleme
        ↓
  cv_experience_extractor → CV'den role uygun beceri/deneyim çıkarımı
        ↓
  email_writer_agent    → E-posta üretimi (ALLOWED EXPERIENCE + strateji)
        ↓
  email_reviewer_agent  → Kalite değerlendirmesi (naturalness, genericness, cv_summary, personalization)
        ↓
  [gerekirse yeniden yaz, maks. 3 iterasyon]
        ↓
  generate_email_subject → Kısa, sabit formatlı konu satırı
```

## Kurulum

```bash
python -m venv .venv
.venv\Scripts\activate
pip install fastapi uvicorn sqlalchemy psycopg2-binary python-dotenv pydantic openai pinecone requests beautifulsoup4
uvicorn app.main:app --reload
```

- API: `http://127.0.0.1:8000`
- Swagger: `http://127.0.0.1:8000/docs`

## Ortam Değişkenleri (`.env`)

| Değişken | Açıklama |
|----------|----------|
| `DATABASE_URL` | PostgreSQL bağlantı URL'si |
| `OPENAI_API_KEY` | OpenAI API anahtarı |
| `PINECONE_API_KEY` | Pinecone API anahtarı |
| `PINECONE_INDEX_NAME` | Pinecone index adı |
| `FULL_NAME` | İmzada kullanılan ad soyad |
| `PHONE_NUMBER` | İmzada kullanılan telefon |
| `EMAIL_ADDRESS` | İmzada kullanılan e-posta |
| `LINKEDIN_URL` | LinkedIn profil URL'si |
| `GITHUB_URL` | GitHub profil URL'si |
| `PORTFOLIO_URL` | Portfolyo URL'si (ilan istediğinde otomatik eklenir) |
| `SMTP_EMAIL` | SMTP gönderen e-posta |
| `SMTP_APP_PASSWORD` | Gmail SMTP uygulama şifresi |
| `AI_ENGINEER_CV_PATH` | AI Engineer CV PDF yolu |
| `BACKEND_AI_ENGINEER_CV_PATH` | Backend AI Engineer CV PDF yolu |

## API Referansı

### Companies

| Yöntem | Yol | Açıklama |
|--------|-----|----------|
| `GET` | `/companies/` | Şirket listesi |
| `POST` | `/companies/analyze-url` | URL'den şirket çıkar + Pinecone upsert |
| `POST` | `/companies/generate-application-email` | İlan metniyle AI agent e-posta üretimi |
| `POST` | `/companies/{id}/contact-email` | Şirket iletişim e-postasını güncelle |
| `POST` | `/companies/{id}/chat` | RAG tabanlı şirket soru-cevap |
| `DELETE` | `/companies/{id}/chat` | Şirket sohbet geçmişini temizle |

### Applications

| Yöntem | Yol | Açıklama |
|--------|-----|----------|
| `POST` | `/applications/prepare` | URL/kayıtlı şirket ile başvuru + e-posta |
| `POST` | `/applications/{id}/refine-email` | E-postayı talimatla düzenle |
| `POST` | `/applications/{id}/send` | CV ekiyle e-posta gönder |
| `GET` | `/applications/sent` | Gönderilmiş başvurular |

## RAG Akışı (Şirket Chatbot)

1. Şirket URL'sinden metin çekilir ve chunk'lara bölünür.
2. Her chunk `text-embedding-3-small` ile embedding'e çevrilir.
3. Pinecone'a `company_id` metadata'sıyla upsert edilir.
4. Kullanıcı soru sorduğunda soru embedding'i alınır.
5. Pinecone'dan `company_id` filtresiyle en ilgili chunk'lar çekilir.
6. Bağlam + soru OpenAI'ya verilerek yanıt üretilir.

## Dizin Yapısı

```text
app/
├── main.py
├── database.py
├── models/
│   ├── application.py
│   ├── company.py
│   ├── company_chat_message.py
│   ├── cv.py
│   ├── generated_email.py
│   └── user_ai_preference.py
├── schemas/
├── routes/
│   ├── companies.py
│   └── applications.py
└── services/
    ├── ai_agents/
    │   ├── orchestrator.py
    │   ├── job_analyzer.py
    │   ├── email_strategy_agent.py
    │   ├── cv_experience_extractor.py
    │   ├── email_writer_agent.py
    │   ├── email_reviewer_agent.py
    │   └── portfolio_utils.py
    ├── url_analyzer.py
    ├── ai_analyzer.py
    ├── vector_store.py
    ├── company_chat.py
    ├── email_generator.py
    ├── email_refiner.py
    ├── email_history.py
    ├── mail_sender.py
    └── user_ai_memory.py
```
