# VoiceClone Infrastructure & Deployment

## 1. Vazifasi
Ushbu katalog loyihaning barcha xizmatlarini (PostgreSQL, Redis, Django Web, Celery Worker, FastAPI Inference, Frontend) ishlab chiquvchi muhitida (Developer Stack) va Linux server muhitida (Production) orkestratsiya qilish uchun konteyner konfiguratsiyalarini o‘z ichiga oladi.

## 2. Tarkib
- `docker-compose.yml`: Developer stekining yagona buyruq orqali ishga tushadigan konfiguratsiyasi.
- `docker-compose.gpu.yml`: NVIDIA GPU drayveri bilan FastAPI inference xizmatini yoqish uchun override fayli.
- `Dockerfile.backend`: Django API va Celery worker uchun yengil Python tasviri (GPU-siz).
- `Dockerfile.inference`: PyTorch va CUDA drayverlari bilan ta'minlangan inference xizmati tasviri.
- `Dockerfile.frontend`: Vite production build va Nginx static server tasviri.

## 3. Tarmoq va Izolyatsiya Siyosati
- Tashqi tarmoqqa faqat `frontend` (80/443) va `backend` (8000) portlari ochiladi.
- `inference` (8001), `postgres` (5432) va `redis` (6379) faqat ichki Docker tarmog‘ida (`voiceclone-network`) ishlaydi.
