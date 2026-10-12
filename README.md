# VoiceClone AI

> **Axloqiy, rozilik asosida ishlaydigan ko‘p tilli ovoz sintezi va klonlash platformasi.**  
> Qo‘llab-quvvatlanadigan tillar: **O‘zbek (lotin alifbosi - MVP maqsad)**, **Ingliz (rasmiy)**, **Rus (eksperimental)**.

---

## 1. Loyiha Haqida va Arxitektura

VoiceClone — foydalanuvchining o‘z ovozi yoki foydalanishga to‘liq yozma rozilik olingan ovoz namunalari asosida yuqori sifatli audio sintez qiluvchi platforma.

Tizim modulli monorepo arxitekturasida qurilgan:
- **`backend/`**: Django 5.2 LTS + Django REST Framework. Biznes mantiqi, foydalanuvchi hisoblari, rozilik auditi (**Consent Gate**), assetlar metadatasi va Celery asinxron navbati.
- **`inference/`**: FastAPI alohida mikroservisi. Barcha PyTorch, CUDA, OpenVoice V2 va TTS modellarini izolyatsiyalangan holatda xotiraga oladi va boshqaradi (GPU resurslari Django muhitiga aralashtirilmaydi).
- **`frontend/`**: React + Vite + TypeScript zamonaviy veb-foydalanuvchi interfeysi (audio yozuvchi, waveform preview, consent modal, progress bar).
- **`infra/`**: Docker Compose developer steki va ishlab chiqarish konteynerlari.
- **`docs/`**: Tizim dizayni, apparat auditi, benchmark natijalari va arxitektura qarorlari (ADR).
- **`tests/`**: Tizim xavfsizligi, gigiyenasi va komponentlar sinovlari.

---

## 2. Tizim Talablari

- **Python:** 3.11.x (qat'iy pin qilingan: `3.11.9`)
- **Node.js:** v20+ LTS va npm
- **Baza & Kesh:** PostgreSQL 16+, Redis 7+
- **GPU (Tavsiya etiladi):** NVIDIA RTX 3060 Laptop (6GB VRAM) yoki undan yuqori (drayver 581.29+, CUDA 12.1/13.0). CPU rejimida ham ishlay oladi.

---

## 3. Ishlab Chiquvchi Uchun O‘rnatish (Developer Setup)

### A. Windows Muhitida Lokal Ishga Tushirish

#### 1. Muhit o‘zgaruvchilari va Keshlarni Himoyalash
Disk C to‘lib qolishining oldini olish uchun (agar C diskda bo‘sh joy kam bo‘lsa), barcha pip va Hugging Face keshlari D diskiga yo‘naltirilishi shart:
```powershell
$env:HF_HOME = "D:\Proyekt\voiceclone\.cache\huggingface"
$env:TORCH_HOME = "D:\Proyekt\voiceclone\.cache\torch"
$env:PIP_CACHE_DIR = "D:\Proyekt\voiceclone\.cache\pip"
```

Konfiguratsiya faylini nusxalang:
```powershell
copy .env.example .env
```

#### 2. Backend (Django + DRF) Sozlash
```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install --upgrade pip
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver 8000
```

#### 3. AI Inference Service (FastAPI) Sozlash
Inference xizmati o‘zining alohida virtual muhitida ishga tushiriladi:
```powershell
cd inference
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install --upgrade pip
pip install -r requirements.txt
uvicorn app.main:app --host 127.0.0.1 --port 8001 --reload
```

#### 4. Frontend (React + Vite + TypeScript)
```powershell
cd frontend
npm install
npm run dev
```

---

### B. Docker Compose Yordamida Barcha Xizmatlarni Ko‘tarish

Developer stekini bir buyruq bilan ishga tushirish (PostgreSQL, Redis, Backend, Worker, Inference):
```bash
docker compose -f infra/docker-compose.yml up -d --build
```

Konteynerlar holatini tekshirish:
```bash
docker compose -f infra/docker-compose.yml ps
```

---

## 4. Linux Production Muhiti va Farqlari

Windows dev muhitidan Linux Production muhitiga o‘tishdagi asosiy farqlar:

| Xususiyat | Windows (Dev) | Linux (Production) |
|---|---|---|
| **OS / Shell** | Windows 10/11, PowerShell | Ubuntu 22.04/24.04 LTS, Bash |
| **GPU Drayveri** | Windows NVIDIA Driver 581+ | Linux NVIDIA Driver + `nvidia-container-toolkit` |
| **GPU Konteyner** | Host rejimida to‘g‘ridan-to‘g‘ri | Docker `deploy.resources.reservations.devices` |
| **Server Runner** | `manage.py runserver`, `uvicorn --reload` | Gunicorn + UvicornWorker, Nginx Reverse Proxy |
| **Audio Storage** | Lokal `var/media` | S3-mos Storage (MinIO / AWS S3) private signed URL |
| **Xavfsizlik** | `DJANGO_DEBUG=True` | `DJANGO_DEBUG=False`, SSL/TLS (HTTPS) majburiy |

### Linux GPU Konteynerini faollashtirish:
```bash
# NVIDIA Container Toolkit o'rnatilgach:
docker compose -f infra/docker-compose.yml -f infra/docker-compose.gpu.yml up -d
```

---

## 5. Xavfsizlik, Rozilik (Consent) va Axloqiy Qoidalar

1. **Roziliksiz Ovoz Taqiqi:** Tizim hech qachon birovning ovozini ruxsatisiz sintez qilmaydi. Har bir ovoz profili egasining tasdiqlangan `ConsentRecord` yozuviga ega bo‘lishi shart.
2. **Anti-Impersonation:** Davlat arboblari, mashhurlar yoki uchinchi shaxslarning ovozini taqlid qilish qat'iyan taqiqlanadi.
3. **Private Media:** Barcha audio namunalar xususiy saqlanadi va faqat vakolatli foydalanuvchigagina xavfsiz token orqali taqdim etiladi.

---

## 6. Sifat Nazorati va Testlar

Linter va formatlashni tekshirish:
```bash
ruff check .
ruff format --check .
```

Testlarni ishga tushirish:
```bash
pytest
```
