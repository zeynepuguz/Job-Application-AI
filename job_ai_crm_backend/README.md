# Job AI CRM — Backend

Bu backend, Job AI CRM uygulamasının API ve AI servis katmanını sağlar.  
FastAPI + PostgreSQL üzerinde çalışır; OpenAI ve Pinecone ile RAG tabanlı şirket chatbot desteği içerir.

## Teknolojiler

- FastAPI
- SQLAlchemy
- PostgreSQL
- Pydantic
- OpenAI (chat completions + embeddings)
- Pinecone (vector database)
- Requests + BeautifulSoup
- SMTP (Gmail)

## Özellikler

- Şirket URL analizi ve şirket kaydı oluşturma
- Şirketleri e-posta bazında tekilleştirme, mükerrer kaydı engelleme
- Şirket metnini chunk + embedding ile Pinecone’a upsert etme
- RAG tabanlı şirket soru-cevap endpoint’i
- Başvuru e-postası üretme / refine etme / gönderme
- Şirket iletişim e-postasını manuel güncelleme

## Gereksinimler

- Python 3.10+
- PostgreSQL
- OpenAI API key
- Pinecone API key + index
- Gmail SMTP app password (gönderim için)

## Kurulum

```bash
python -m venv .venv
.venv\Scripts\activate
pip install fastapi uvicorn sqlalchemy psycopg2-binary python-dotenv pydantic openai pinecone requests beautifulsoup4
```

Uygulamayı çalıştırma:

```bash
uvicorn app.main:app --reload
```

- API: `http://127.0.0.1:8000`
- Swagger: `http://127.0.0.1:8000/docs`

## Ortam Değişkenleri (`.env`)

| Değişken | Açıklama |
|----------|----------|
| `DATABASE_URL` | PostgreSQL bağlantı URL’si |
| `OPENAI_API_KEY` | OpenAI istemcisi için API anahtarı |
| `PINECONE_API_KEY` | Pinecone API anahtarı |
| `PINECONE_INDEX_NAME` | Kullanılacak Pinecone index adı |
| `SMTP_EMAIL` | Gönderen e-posta adresi |
| `SMTP_APP_PASSWORD` | SMTP uygulama şifresi |
| `AI_ENGINEER_CV_PATH` | `ai_engineer` rolü için CV PDF yolu |
| `BACKEND_AI_ENGINEER_CV_PATH` | `backend_ai_engineer` rolü için CV PDF yolu |

## API Özeti

### Companies

| Yöntem | Yol | Açıklama |
|--------|-----|----------|
| `GET` | `/companies/` | Şirketleri listele |
| `POST` | `/companies/analyze-url` | URL’den şirket çıkar + kaydet + Pinecone upsert |
| `POST` | `/companies/{company_id}/contact-email` | Şirket iletişim e-postasını güncelle |
| `POST` | `/companies/{company_id}/chat` | Seçili şirket için RAG tabanlı soru-cevap |
| `DELETE` | `/companies/{company_id}/chat` | Seçili şirketin sohbet geçmişini temizle |

### Applications

| Yöntem | Yol | Açıklama |
|--------|-----|----------|
| `POST` | `/applications/prepare` | Başvuru + taslak e-posta üretimi |
| `POST` | `/applications/{application_id}/refine-email` | E-posta metnini talimatla düzenleme |
| `POST` | `/applications/{application_id}/send` | E-postayı gönderme |
| `GET` | `/applications/sent` | Gönderilmiş başvuruları listeleme |

## RAG Akışı (Şirket Chatbot)

1. Şirket URL’sinden çekilen metin chunk’lara bölünür.
2. Her chunk embedding’e çevrilir (`text-embedding-3-small`).
3. Pinecone index’e `company_id` metadata’sı ile upsert edilir.
4. Kullanıcı soru sorduğunda soru embedding’i alınır.
5. Pinecone’dan `company_id` filtresiyle en ilgili parçalar çekilir.
6. Bu bağlam OpenAI chat modeline verilerek Türkçe yanıt üretilir.

## Sohbet Geçmişi

- Şirket sohbeti `company_id` bazında yönetilir.
- `DELETE /companies/{company_id}/chat` endpoint’i, ilgili şirkete ait kayıtlı sohbet mesajlarını temizlemek için kullanılır.

## Dizin Yapısı

```text
app/
  main.py
  database.py
  models/
  schemas/
  routes/
    companies.py
    applications.py
  services/
    url_analyzer.py
    ai_analyzer.py
    vector_store.py
    company_chat.py
    email_generator.py
    email_refiner.py
    mail_sender.py
```
