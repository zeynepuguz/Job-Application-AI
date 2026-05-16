# Job AI CRM

Kişisel iş başvuru süreçlerini otomatize eden AI destekli CRM. Şirket araştırması, RAG tabanlı şirket chatbotu, CV'ye dayalı e-posta üretimi, düzenleme ve gönderi tek akışta.

## Modüller

| Modül | Açıklama |
|-------|----------|
| `job_ai_crm_backend` | FastAPI API + AI agent pipeline + RAG servisleri |
| `job_ai_crm_frontend` | Vite + Vanilla JS arayüzü |

## Kullanılan Teknolojiler

- **Backend:** FastAPI, SQLAlchemy, PostgreSQL, Pydantic, Uvicorn
- **AI:** OpenAI GPT-4o-mini (e-posta yazma, strateji, review, CV analizi)
- **RAG:** Pinecone (şirket bilgisi vektör indeksi, semantic search)
- **Scraping:** Requests, BeautifulSoup
- **Mail:** SMTP (Gmail app password)
- **Frontend:** Vanilla JS, TailwindCSS (CDN), Vite

## Temel Özellikler

- **3 başvuru modu:** URL ile yeni şirket / kayıtlı şirket / ilan metni ile üret
- **AI Agent Pipeline:** İş ilanını analiz → strateji belirle → e-posta yaz → review → gerekirse yeniden yaz
- **CV'ye dayalı deneyim çıkarımı:** Hedef role göre ilgili CV otomatik seçilir, içeriği analiz edilerek e-postaya yansıtılır
- **Portfolyo & GitHub otomatik tespiti:** İlan portfolyo istediğinde otomatik eklenir
- **Dil desteği:** Türkçe / İngilizce
- **Şirket Chatbot (RAG):** Kayıtlı şirket hakkında Pinecone bağlamıyla soru-cevap
- **E-posta refine:** Talimatla mevcut e-postayı düzenleme
- **SMTP gönderimi:** CV eki ile e-posta gönderme

## Hızlı Başlangıç

### Backend

```bash
cd job_ai_crm_backend
python -m venv .venv
.venv\Scripts\activate
pip install fastapi uvicorn sqlalchemy psycopg2-binary python-dotenv pydantic openai pinecone requests beautifulsoup4
uvicorn app.main:app --reload
```

`http://127.0.0.1:8000` — Swagger: `http://127.0.0.1:8000/docs`

### Frontend

```bash
cd job_ai_crm_frontend
npm install
npm run dev
```

`http://127.0.0.1:5174`

## Kullanım Akışı

1. Backend ve frontend'i başlat.
2. **Mail / ilan ile üret** modunda: alıcı e-postası + ilan metni + hedef pozisyon gir → E-posta Oluştur.
3. **URL ile yeni şirket** modunda: kariyer sayfası URL'si + hedef pozisyon gir → sistem şirketi kaydeder ve e-posta üretir.
4. **Kayıtlı şirket seç** modunda: listeden şirket seç + hedef pozisyon gir.
5. Üretilen e-postayı önizle, gerekirse refine et.
6. Başvuruyu gönder (CV otomatik eklenir).

## Klasör Yapısı

```text
Job_AI_CRM/
├── README.md
├── job_ai_crm_backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── database.py
│   │   ├── models/
│   │   ├── schemas/
│   │   ├── routes/
│   │   └── services/
│   │       └── ai_agents/       ← agent pipeline
│   ├── CVs/
│   └── README.md
└── job_ai_crm_frontend/
    ├── index.html
    ├── main.js
    ├── companies.js
    └── README.md
```

## Notlar

- `.env` ve CV dosyalarını repoya eklemeyin.
- Backend değişikliklerinden sonra process restart gerekir (`.env` değişiklikleri dahil).
- Chatbot kalitesi Pinecone'a eklenen şirket metninin kalitesine bağlıdır.
