# Job AI CRM — Frontend

Job AI CRM uygulamasının kullanıcı arayüzü. Vite ile çalışır, backend API'sine istek atar.

## Teknolojiler

- HTML + Vanilla JavaScript
- Tailwind CSS (CDN)
- Vite

## Sayfalar

- `index.html` / `main.js` — Ana başvuru akışı + şirket chatbot
- `companies.html` / `companies.js` — Şirket listeleme ve başvuru durumu görüntüleme
- `applications.html` / `applications.js` — Başvuru kayıtları ekranı

## Kurulum ve Çalıştırma

```bash
npm install
npm run dev
```

Varsayılan adres: `http://localhost:5174`

```bash
npm run build
npm run preview
```

## Ana Özellikler

### Başvuru Modları (index)
- **URL ile yeni şirket:** Şirket sitesi taranır, e-posta üretilir
- **Kayıtlı şirket seç:** Daha önce eklenen şirketlerden seçim
- **Mail / ilan ile üret:** İlan metni veya alıcı bilgisiyle AI agent pipeline tetiklenir

### E-posta Yönetimi
- Hedef rol + dil seçimi ile taslak e-posta oluşturma
- Yazılı talimatla konu/gövde düzenleme (refine)
- İletişim e-postası bulunamadıysa elle girme veya değiştirme
- Geçerli iletişim e-postası yoksa gönder butonu pasif

### CV Yönetimi
- Role göre önerilen CV kartı
- Birden fazla CV yüklenebilir, aktif CV değiştirilebilir

### Şirket Chatbot (RAG)
- Seçili şirkete soru sorabilme
- Sohbet geçmişini arayüzde görme
- Enter ile hızlı gönderim
- Sohbet temizleme

### Arayüz
- Karanlık / Aydınlık tema (localStorage'da saklanır)
- Responsive tasarım

## Kullanılan API Endpoint'leri

| Yöntem | Yol |
|--------|-----|
| `GET` | `/companies/` |
| `POST` | `/companies/analyze-url` |
| `POST` | `/companies/generate-application-email` |
| `POST` | `/companies/{id}/contact-email` |
| `POST` | `/companies/{id}/chat` |
| `DELETE` | `/companies/{id}/chat` |
| `GET` | `/applications/sent` |
| `POST` | `/applications/prepare` |
| `POST` | `/applications/{id}/refine-email` |
| `POST` | `/applications/{id}/send` |
| `PATCH` | `/applications/{id}/status` |
| `GET` | `/profile/avatar` |
| `POST` | `/profile/avatar` |
| `GET` | `/profile/cvs` |
| `POST` | `/profile/cvs` |
| `DELETE` | `/profile/cvs/{cv_id}` |

## Sık Karşılaşılan Sorunlar

- **"İstek başarısız. Backend çalışıyor mu?"** — Backend process'i kapalı olabilir.
- **Chatbot yanıt vermiyor** — Pinecone/OpenAI env değerlerini ve backend loglarını kontrol edin.
- **Gönderim SMTP hatası** — Backend `.env` içindeki SMTP bilgilerini kontrol edin.
