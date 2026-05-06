# Job AI CRM

Job AI CRM, şirket araştırma ve iş başvurusu süreçlerini tek yerde toplayan AI destekli bir CRM uygulamasıdır.  
Sistem; şirket bilgisini toplar, RAG tabanlı şirket chatbot’u sunar, başvuru e-postası üretir, düzenler ve gönderir.

## Modüller

- `job_ai_crm_backend`: FastAPI tabanlı API + RAG servisleri
- `job_ai_crm_frontend`: Vite + Vanilla JS tabanlı arayüz

## Kullanılan Teknolojiler

- **Backend:** FastAPI, SQLAlchemy, PostgreSQL, Pydantic, Uvicorn
- **AI:** OpenAI (chat + embedding modelleri)
- **RAG:** Pinecone (vektör indeks), chunk + embedding + semantic search
- **Scraping/Parsing:** Requests, BeautifulSoup
- **Mail:** SMTP (Gmail app password)
- **Frontend:** HTML, TailwindCSS (CDN), Vanilla JavaScript, Vite

## Temel Özellikler

- URL’den şirket verisi çıkarma ve kayıt
- E-posta bazlı şirket tekilleştirme ve mükerrer kaydı engelleme
- Şirket iletişim e-postasını manuel güncelleme
- Hedef role göre AI başvuru e-postası üretimi
- E-posta refine (talimatla metin iyileştirme)
- SMTP ile başvuru gönderimi
- **Şirket Chatbot (RAG):** Seçili şirket hakkında soru sorup Pinecone bağlamıyla yanıt alma
- **Chat geçmiş yönetimi:** Şirket bazlı sohbet geçmişini temizleme

## Hızlı Başlangıç

### 1) Backend

Detay: [`job_ai_crm_backend/README.md`](job_ai_crm_backend/README.md)

```bash
cd job_ai_crm_backend
python -m venv .venv
.venv\Scripts\activate
pip install fastapi uvicorn sqlalchemy psycopg2-binary python-dotenv pydantic openai pinecone requests beautifulsoup4
uvicorn app.main:app --reload
```

Backend: `http://127.0.0.1:8000`  
Swagger: `http://127.0.0.1:8000/docs`

### 2) Frontend

Detay: [`job_ai_crm_frontend/README.md`](job_ai_crm_frontend/README.md)

```bash
cd job_ai_crm_frontend
npm install
npm run dev
```

Frontend: `http://127.0.0.1:5174`

## Önerilen Kullanım Akışı

1. Backend’i başlat.
2. Frontend’i başlat.
3. Şirket seç veya yeni şirket ekle.
4. Gerekirse şirket chatbot’una soru sor.
5. Gerekirse şirket sohbet geçmişini temizle.
6. Başvuru e-postası üret/refine et.
7. Gerekirse iletişim e-postasını düzelt.
8. Başvuruyu gönder.

## Klasör Yapısı

```text
Job_AI_CRM/
  README.md
  job_ai_crm_backend/
    app/
    CVs/
    README.md
  job_ai_crm_frontend/
    assets/
    index.html
    main.js
    companies.html
    companies.js
    applications.html
    applications.js
    README.md
```

## Notlar

- Hassas dosyaları (`.env`, CV dosyaları vb.) repoya eklemeyin.
- Chatbot’un doğru cevap kalitesi, Pinecone’a eklenen şirket metni kalitesine bağlıdır.
- Backend değişikliklerinden sonra process restart yapmanız önerilir.
