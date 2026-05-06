# Job AI CRM — Frontend

Bu klasör, Job AI CRM uygulamasının kullanıcı arayüzünü içerir. Arayüz Vite ile çalışır ve backend API’sine istek atar.

## Teknolojiler

- HTML + Vanilla JavaScript
- Tailwind (CDN üzerinden)
- Vite

## Sayfalar

- `index.html` / `main.js`  
  Ana başvuru akışı + şirket chatbot (RAG) ekranı
- `companies.html` / `companies.js`  
  Şirket listeleme/görüntüleme
- `applications.html` / `applications.js`  
  Başvuru kayıtları ekranı

## Kurulum

```bash
npm install
```

## Çalıştırma

```bash
npm run dev
```

Varsayılan adres: `http://127.0.0.1:5174`

## Build ve Preview

```bash
npm run build
npm run preview
```

## Backend Bağımlılığı

Frontend, API çağrılarını backend’e yapar. Backend çalışmıyorsa:

- şirket listesi yüklenmez,
- e-posta üretimi ve gönderimi başarısız olur,
- şirket chatbot yanıt üretemez.

Bu nedenle geliştirme sırasında backend’in de açık olması gerekir.

## Ana Özellikler (index)

- **Başvuru modu:**
  - URL ile yeni şirket
  - Kayıtlı şirket seç
- **E-posta üretimi:** hedef rol + dil ile taslak e-posta oluşturma
- **CV kartı:** role göre önerilen CV bilgisini gösterme
- **Refine:** yazılı talimatla konu/gövde düzenleme
- **Manuel iletişim e-postası düzenleme:**
  - Mail bulunamadıysa elle girme
  - Bulunan mail yanlışsa değiştirme
- **Gönderim kontrolü:** geçerli iletişim e-postası yoksa gönder butonunu pasif tutma
- **Şirket Chatbot (RAG):**
  - Seçili şirkete soru sorabilme
  - Sohbet geçmişini arayüzde görebilme
  - Enter ile hızlı gönderim
  - Sohbet temizleme (backend `DELETE` endpoint çağrısı ile)

## API Beklentileri (Özet)

Arayüzün kullandığı temel endpoint’ler:

- `GET /companies/`
- `POST /companies/{company_id}/chat`
- `DELETE /companies/{company_id}/chat`
- `POST /companies/{company_id}/contact-email`
- `POST /applications/prepare`
- `POST /applications/{application_id}/refine-email`
- `POST /applications/{application_id}/send`

Not: `prepare` yanıtında `application_id`, `company_id`, `contact_email`, `subject`, `body` alanları beklenir.

## Sık Karşılaşılan Sorunlar

- **“İstek başarısız. Backend çalışıyor mu?”**
  - Backend process’i kapalı olabilir.
- **Chatbot yanıt vermiyor**
  - Pinecone/OpenAI env değerlerini ve backend loglarını kontrol edin.
- **Aynı şirket için tekrar kayıt hatası**
  - E-posta veya URL zaten kayıtlı olabilir.
- **Gönderim SMTP hatası**
  - Backend `.env` içindeki SMTP bilgilerini kontrol edin.

## Geliştirici Notu

`main.js` içinde şirket seçiminde aktif şirket kimliği (`company_id`) takip edilir.  
Hem chatbot hem mail güncelleme çağrıları seçili şirketin `company_id` değeriyle yapılır; bu sayede farklı şirkete yanlışlıkla işlem yapılması engellenir.

`Sohbeti Temizle` butonu sadece UI temizlemez; seçili şirket varsa backend’e `DELETE /companies/{company_id}/chat` isteği atarak kayıtlı geçmişi de temizler.
