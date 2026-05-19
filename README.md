# Job AI CRM

AI destekli kişisel iş başvuru takip sistemi. Şirket araştırması, e-posta üretimi, düzenleme ve gönderimi tek akışta.

## Özellikler

- 3 başvuru modu: URL ile yeni şirket / kayıtlı şirket seç / mail veya ilan metni ile üret
- AI Agent Pipeline: ilan analizi → strateji → e-posta yazımı → kalite review
- CV yönetimi: PDF yükle, metin veritabanına kaydedilir, role göre otomatik seçilir
- Şirket Chatbot (RAG — Pinecone)
- Gmail API veya SMTP ile e-posta gönderimi
- Başvuru takibi (durum, notlar, geçmiş)
- Profil fotoğrafı (veritabanına kaydedilir, cihazlar arası senkron)
- Karanlık / Aydınlık tema

---

## Kurulum (Railway — Önerilen)

### 1. Repoyu fork'la veya klonla

```bash
git clone https://github.com/zeynepuguz/Job-Application-AI.git
cd Job-Application-AI
```

### 2. Gerekli servisler

| Servis | Amaç | Ücretsiz Plan |
|--------|------|---------------|
| [Railway](https://railway.app) | Backend + PostgreSQL hosting | ✓ (5 $/ay kredi) |
| [OpenAI](https://platform.openai.com) | E-posta üretimi (GPT-4o-mini) | Ücretli (kullanım bazlı) |
| [Pinecone](https://pinecone.io) | Şirket bilgisi RAG | ✓ |
| Gmail | E-posta gönderimi (API veya SMTP) | ✓ |

### 3. Railway'de proje oluştur

1. [railway.app](https://railway.app) → **New Project** → **Deploy from GitHub repo** → bu repoyu seç
2. Sol panelde **+ Add Service** → **Database** → **Add PostgreSQL**
3. `web` servisine tıkla → **Variables** sekmesi → **Raw Editor**

### 4. Environment variables

Aşağıdaki değerleri kendi bilgilerinle doldur ve Railway Variables'a yapıştır:

```env
# OpenAI
OPENAI_API_KEY=sk-proj-...

# Pinecone
PINECONE_API_KEY=pcsk_...
PINECONE_INDEX_NAME=job-ai-crm

# Uygulama şifresi (uygulamaya giriş için)
APP_PASSWORD=güçlü-bir-şifre-belirle

# JWT (rastgele uzun bir string — örn: openssl rand -base64 48)
JWT_SECRET=cok-uzun-ve-rastgele-bir-string

# Kişisel bilgiler (e-posta içeriğinde kullanılır)
FULL_NAME=Adın Soyadın
EMAIL_ADDRESS=eposta@ornek.com
PHONE_NUMBER=+90 5XX XXX XXXX
LINKEDIN_URL=https://linkedin.com/in/kullanici-adin
PORTFOLIO_URL=https://portfoyun.com
GITHUB_URL=https://github.com/kullanici-adin

# Gmail SMTP (e-posta göndermek için — yeterli)
SMTP_EMAIL=eposta@gmail.com
SMTP_APP_PASSWORD=xxxx xxxx xxxx xxxx

# Gmail API (isteğe bağlı — ayarlıysa SMTP yerine kullanılır)
# GMAIL_CLIENT_ID=...
# GMAIL_CLIENT_SECRET=...
# GMAIL_REFRESH_TOKEN=...
```

> **Not:** `DATABASE_URL` Railway tarafından otomatik eklenir — kendin ekleme.

> **Gmail App Password nasıl alınır?**
> Google Hesabım → Güvenlik → 2 Adımlı Doğrulama (aktif olmalı) → Uygulama Şifreleri → "Mail" için şifre oluştur

### 5. Deploy tamamlandı

Railway `web-xxxx.up.railway.app` formatında bir URL verir. Bu URL'e git, `APP_PASSWORD` ile giriş yap.

### 6. CV yükle (ilk kurulum)

1. Sağ üstte **⚙️** simgesine tıkla
2. Pozisyon türünü seç (AI Engineer / Backend AI Engineer)
3. Bir başlık yaz ve PDF dosyasını seç → **Yükle**
4. Backend metni otomatik çıkarır, veritabanına kaydeder

---

## Yerel Geliştirme

### Gereksinimler
- Python 3.10+
- Node.js 18+
- PostgreSQL

### Backend

```bash
cd job_ai_crm_backend
python -m venv .venv

# Windows
.venv\Scripts\activate
# Mac/Linux
source .venv/bin/activate

pip install -r requirements.txt
```

`.env` dosyası oluştur (`job_ai_crm_backend/.env`):
```env
DATABASE_URL=postgresql://postgres:sifre@localhost:5432/veritabani_adi
OPENAI_API_KEY=...
PINECONE_API_KEY=...
PINECONE_INDEX_NAME=job-ai-crm
APP_PASSWORD=sifren
JWT_SECRET=uzun-string
FULL_NAME=Adın Soyadın
EMAIL_ADDRESS=...
PHONE_NUMBER=...
LINKEDIN_URL=...
PORTFOLIO_URL=...
GITHUB_URL=...
SMTP_EMAIL=...
SMTP_APP_PASSWORD=...
```

```bash
uvicorn app.main:app --reload
```

Backend: `http://127.0.0.1:8000` — Swagger: `http://127.0.0.1:8000/docs`

### Frontend (geliştirme proxy'si)

```bash
cd job_ai_crm_frontend
npm install
npx vite
```

Frontend: `http://localhost:5174`

> Production'da frontend, backend tarafından `http://127.0.0.1:8000` adresinde serve edilir.

---

## Teknolojiler

| Katman | Teknoloji |
|--------|-----------|
| Backend | FastAPI, SQLAlchemy, PostgreSQL, Uvicorn |
| AI | OpenAI GPT-4o-mini |
| RAG | Pinecone |
| Scraping | Requests, BeautifulSoup |
| E-posta | Gmail API / SMTP (Gmail) |
| Frontend | Vanilla JS, TailwindCSS, Vite |

---

## Notlar

- `.env` ve CV dosyaları git'e **eklenmez** (`.gitignore`'da)
- CV metinleri veritabanında saklanır — Railway'de kalıcıdır
- Pinecone index adı `job-ai-crm` olarak ayarlanmalıdır (veya `.env`'de değiştir)
