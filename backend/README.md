# VoiceClone Backend Service

## 1. Vazifasi va Arxitekturadagi O‘rni
Backend xizmati VoiceClone tizimining asosiy biznes mantiqini, autentifikatsiyani, audio asset metadata boshqaruvini, foydalanuvchi ovoz profillari va eng muhimi **Rozilik (Consent) Auditini** boshqaradi.

U to‘g‘ridan-to‘g‘ri og‘ir AI/ML modellarini xotiraga yuklamaydi. Buning o‘rniga, u navbat (Celery + Redis) orqali asinxron audio generatsiya vazifalarini yaratadi va alohida ajratilgan `inference` (FastAPI) xizmati bilan ichki HTTP orqali bog‘lanadi.

## 2. Texnologik Stek
- **Framework:** Python 3.11 + Django 5.2 LTS + Django REST Framework (DRF)
- **Ma'lumotlar bazasi:** PostgreSQL 16
- **Asinxron navbat & kesh:** Celery 5.4 + Redis 7
- **Media saqlash:** Abstrakt Storage (Lokal `MEDIA_ROOT` dev muhitida, S3/MinIO productionda)
- **Linter & Test:** Ruff, Pytest-Django

## 3. Loyiha Tuzilmasi (Rejalashtirilgan Applar)
- `apps/accounts/`: Foydalanuvchilar, rollar, API kalitlar va xavfsiz sessiyalar.
- `apps/voices/`: `VoiceProfile`, mos ovoz namunalari, ovoz xususiyatlari.
- `apps/consent/`: `ConsentRecord`, rozilik tasdiqlari, audio audit loglari.
- `apps/generations/`: `GenerationJob`, holat mashinasi (`PENDING`, `RUNNING`, `SUCCEEDED`, `FAILED`).
- `apps/audio/`: Audio assetlar metadatasi, tekshiruv va tozalash lifecycle.
- `apps/audit/`: Harakatlar auditi va qonuniy xavfsizlik loglari.

## 4. Qat'iy Xavfsizlik Qoidalari
1. **Consent Gate:** Har qanday audio generatsiyasidan oldin DB darajasida faol, tasdiqlangan `ConsentRecord` mavjudligi tekshiriladi.
2. **Izolyatsiya:** Boshqa foydalanuvchilarning ovoz namunalari va yaratilgan audiolari ID orqali taxmin qilinishi mumkin emas (UUIDv4 va signed URLs).
3. **No Weights in Django:** PyTorch yoki og‘ir AI kutubxonalari Django muhitiga o‘rnatilmaydi.
