# VoiceClone AI — Observability, Structured Logging & Distributed Tracing

> **Versiya:** 1.0.0  
> **Sana:** 2026-10-12  
> **Status:** Ishga tushirilgan (Production-Ready)

---

## 1. Umumiy Ko‘rinish

VoiceClone AI tizimi har bir bosqichda (Frontend, Backend, Celery Workers, AI Inference Microservice) to‘liq kuzatuvchanlik (**Observability**), xatolarni xavfsiz audit qilish va taqsimlangan tahlil (**Distributed Tracing**) tizimi bilan ta’minlangan.

Har bir HTTP so‘rovi, sintez topshirig‘i va brauzer xatoligi unikal **`X-Request-ID`** orqali bog‘lanadi.

```
[Brauzer / Frontend (React)]
    │   Header: X-Request-ID: fe_17287123_abc123
    ▼
[Django REST API Backend]
    │   Middleware: RequestCorrelationMiddleware
    │   ContextVars: request_id, user_id
    ├──► var/logs/app.log        (Barcha HTTP so'rovlar, latency, user, status)
    ├──► var/logs/security.log   (401/403 rad etishlar, auth, quota xatolari)
    └──► var/logs/error.log      (500 xatolar, frontend telemetriya xatoliklari)
    │
    ├── (Asinxron Celery Task)
    │      Header: X-Request-ID: job_<uuid>
    ▼
[FastAPI AI Inference Microservice]
    │   Middleware: inference_correlation_middleware
    └──► var/logs/inference.log  (Model yuklanishi, sintez davomiyligi, GPU xatolari)
```

---

## 2. Log Fayllari Joylashuvi va Vazifalari

Barcha loglar loyiha ildizidagi `var/logs/` katalogida avtomatik aylanuvchi (**RotatingFileHandler**, har bir fayl 10MB x 10 ta nusxa) shaklda saqlanadi:

| Log Fayli | Darajasi | Maqsadi | Tarkibi |
| :--- | :--- | :--- | :--- |
| `var/logs/app.log` | `INFO+` | Tizimning umumiy hayot sikli | Har bir kelgan va ketgan so‘rov, status kod, bajarilish vaqti (`duration_ms`), mijoz IP va foydalanuvchi. |
| `var/logs/error.log` | `ERROR+` | Server va frontend xatolari | Barcha 500 xatoliklar, to‘liq Python Traceback, frontenddan kelgan `REACT_RENDER_CRASH` va API xatoliklari. |
| `var/logs/security.log` | `INFO/WARN` | Xavfsizlik va ruxsatlar | `ACCESS_DENIED` (401/403), noto‘g‘ri parollar, ruxsatsiz ovoz profili ishlatishga urinishlar, kvota tugashi. |
| `var/logs/inference.log` | `INFO+` | AI Model va GPU inferensi | Matn normalizatsiyasi, model adapterlari, VRAM holati, audio sintez davomiyligi va inference xatoliklari. |

---

## 3. Standart Log Formati

Har bir log satri qat'iy standartlashgan va avtomatlashtirilgan tahlil (Logstash, Datadog, Grafana Loki yoki oddiy `grep`) uchun qulay:

```text
2026-10-12 11:26:49 [INFO] [req:req_a1b2c3d4e5f67890] [user:admin] [voiceclone.request:98] <-- POST /api/v1/generations/jobs/ status=201 duration=14.25ms client=127.0.0.1 user=admin
2026-10-12 11:26:50 [WARNING] [req:req_f9e8d7c6b5a43210] [user:anonymous] [voiceclone.security:72] ACCESS_DENIED GET /api/v1/accounts/me/ status=403 duration=3.10ms client=127.0.0.1 user=anonymous
2026-10-12 11:26:51 [ERROR] [req:fe_17287123_abc123] [user:admin] [voiceclone.error:45] FRONTEND_TELEMETRY [ERROR] user=admin url=http://localhost:5173/voices: Uncaught TypeError: Cannot read property 'map'
```

---

## 4. End-to-End Correlation ID (`X-Request-ID`)

1. **Frontend tomonidan generatsiya:**
   - Brauzer `client.ts` orqali so‘rov yuborayotganda `X-Request-ID: fe_<timestamp>_<random>` sarlavhasini biriktiradi.
2. **Backend tomonidan qabul qilish:**
   - [backend/core/middleware.py](file:///d:/Proyekt/voiceclone/backend/core/middleware.py) sarlavhadagi ID'ni o‘qiydi (agar bo‘lmasa, server `req_<uuid>` yaratadi) va `request.request_id` ga saqlaydi.
   - [backend/core/logging.py](file:///d:/Proyekt/voiceclone/backend/core/logging.py) orqali `ContextVars` yordamida ushbu so‘rov doirasida chaqirilgan har bir ichki funksiyaning loglariga avtomatik qo‘shiladi.
3. **Response Header:**
   - Server har bir javobda `X-Request-ID` sarlavhasini mijozga qaytaradi.
4. **AI Inference ga uzatish:**
   - Celery worker yoki ichki HTTP so‘rovida `X-Request-ID: job_<uuid>` yuboriladi va inference servisi loglarida ham aynan shu ID muhrlanadi.

---

## 5. Frontend Xatolarini Tutish (Telemetry & ErrorBoundary)

1. **Avtomatik Telemetriya:**
   - [frontend/src/utils/logger.ts](file:///d:/Proyekt/voiceclone/frontend/src/utils/logger.ts) brauzerdagi `logger.error(...)` chaqiriqlarini avtomatik ravishda `POST /api/v1/audit/telemetry/` endpointiga jo‘natadi.
   - Flooding (haddan tashqari ko‘p so‘rov) bo‘lmasligi uchun xotirada 30 soniyalik deduplikatsiya mexanizmi mavjud.
2. **React ErrorBoundary:**
   - [frontend/src/components/ErrorBoundary.tsx](file:///d:/Proyekt/voiceclone/frontend/src/components/ErrorBoundary.tsx) dasturning butun UI qatlamini o‘rab turadi.
   - Agar render vaqtida kutilmagan crash yuz bersa, oq ekran chiqmaydi: chiroyli xatolik xabari, xato sababi va "Qayta yuklash" tugmasi chiqadi, xato esa darhol serverning `error.log` fayliga tushadi.

---

## 6. Admin Tizim Loglarini Ko‘rish API'si

Platforma egasi yoki administratorlar uchun himoyalangan log inspektori mavjud:

- **Endpoint:** `GET /api/v1/audit/logs/`
- **Ruxsat:** Faqat `IsAdminUser` (Staff / Superuser).
- **Parametrlar:**
  - `type`: `app` | `error` | `security` | `inference` (default: `app`)
  - `lines`: Nechta oxirgi qatorni ko‘rish (1 dan 200 gacha, default: `50`)
  - `query`: Qidiruv matni (masalan `query=ACCESS_DENIED` yoki `query=admin`)

**Namuna so‘rov:**
```bash
curl -X GET "http://localhost:8000/api/v1/audit/logs/?type=error&lines=50" \
     -H "Cookie: sessionid=..."
```

**Namuna javob:**
```json
{
  "log_type": "error",
  "file_path": "error.log",
  "total_returned": 2,
  "lines": [
    "2026-10-12 11:26:38 [ERROR] [req:req_123] [user:admin] [voiceclone.error:150] FRONTEND_TELEMETRY [ERROR] user=admin url=http://localhost:5173/voices: Uncaught TypeError: Cannot read property 'map'"
  ]
}
```

---

## 7. Amaliy Debugging Qo‘llanmasi

Biror foydalanuvchi "Menda xatolik bo‘ldi" deb murojaat qilsa:
1. Brauzer Network panelidagi `X-Request-ID` ni so‘rang (masalan: `fe_17287123_abc123`).
2. Terminalda bitta buyruq bilan butun zanjirni ko‘ring:
   ```bash
   grep "fe_17287123_abc123" var/logs/*
   ```
3. Natijada foydalanuvchi qaysi vaqtda qaysi sahifadan kirgani, qanday xatolik qaytgani va traceback to‘liq ko‘rinadi.
