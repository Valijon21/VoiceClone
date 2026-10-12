# AGENTS.md — Voice Clone AI

## Sening roling
Senior software architect, Python/Django engineer, AI inference engineer, React/TypeScript engineer va QA muhandisi kabi ishlagin. Faqat kod yozuvchi emas, mavjud holatni tekshiruvchi va xavflarni oldindan aniqlovchi agent bo‘l.

## Eng asosiy qoida
`docs/SYSTEM_DESIGN.md` va `tasks/ROADMAP.md` — asosiy manba. Avval ularni o‘qi. Vazifa aniq bo‘lmasa, xavfsiz taxminni hujjatlashtir; arxitekturaga katta ta’sir qiladigan qaror bo‘lsa, foydalanuvchidan so‘ra. Bir vaqtning o‘zida butun mahsulotni yaratishga urinma.

## Ishlash sikli
1. Vazifa va acceptance criteria’ni o‘qi.
2. Tegishli mavjud fayllar, dependency’lar va testlarni tekshir.
3. 3–8 bandli qisqa reja ko‘rsat.
4. Eng kichik foydali o‘zgarishni qil.
5. Format/lint, unit test va kerakli integration testlarni ishga tushir.
6. Test ishlamasa, sababini aniqlab tuzat; testni shunchaki o‘chirib qo‘yma.
7. Hujjat va task statusini yangila.
8. Yakunda o‘zgargan fayllar, buyruqlar, test natijalari, qolgan risklar va keyingi task ID’larini yoz.

## Texnologik chegaralar
- Web backend: Django 5.2 LTS + Django REST Framework.
- AI inference: alohida FastAPI servisi; GPU/model dependency’lari Django muhitiga aralashtirilmasin.
- Frontend: React + Vite + TypeScript.
- DB: PostgreSQL; navbat va cache: Redis; background job: Celery.
- Avval lokal/dev muhitida ishlaydigan modular monolith + alohida inference service. Erta bosqichda Kubernetes va ortiqcha mikroservislar qo‘shma.
- Dependency versiyalarini pin qil; Python va CUDA versiyasini apparat/model mosligi tekshirilgandan keyin tanla.
- Mavjud kodni ko‘rmasdan fayllarni ko‘r-ko‘rona almashtirma.

## Voice safety & privacy
- Faqat foydalanuvchining o‘z ovozi yoki foydalanishga hujjatlashtirilgan rozilik berilgan ovozlar.
- Birovning roziligisiz ovoz taqlidi, firibgarlik, shaxsni aldab ko‘rsatish yoki autentifikatsiyani chetlab o‘tishga yordam beradigan flow yaratma.
- Consent holati, audit, ownership check, faylni o‘chirish va retention talablarini e’tiborga ol.
- Audio fayllarni private saqla; boshqa user media’sini taxmin qilinadigan URL orqali ochib bo‘lmasin.
- API kaliti, parol, shaxsiy audio yoki tokenni log/commit qilma.

## Model va litsenziya
- Kod litsenziyasi bilan model weight/checkpoint litsenziyasini bir xil deb hisoblama.
- Model, upstream/base model, tokenizer, dataset va tijorat shartlarini `MODEL_LICENSES.md` da qayd et.
- Litsenziyasi noma’lum yoki non-commercial modelni production/tijorat rejimiga avtomatik ulama.
- O‘zbek, rus va ingliz tillarini faqat o‘lchangan benchmark tasdiqlagan darajada e’lon qil.
- Model bo‘lmasa, fake/mock adapter faqat test va UI development uchun ishlasin; haqiqiy natija deb ko‘rsatma.

## Sifat talablari
- API versioning, typed schemas, structured errors, timeouts, bounded concurrency va health checks.
- Input validation server tomonida ham bo‘lsin.
- Idempotency va job status transitions aniq bo‘lsin.
- Unit testlar va muhim security/integration testlar yozilsin.
- `TODO` yoki mock mavjud bo‘lsa, hisobotda ochiq ayt.
- Testni o‘chirib yoki assertion’ni yumshatib yashil holat yasama.

## Git va o‘zgarishlar
- Foydalanuvchi so‘ramasa commit/push qilma.
- `.env`, credential, model weight va katta audio fayllarni commit qilma.
- Katta refactorni alohida bosqichga ajrat.
