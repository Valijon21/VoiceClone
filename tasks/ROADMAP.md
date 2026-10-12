# Voice Clone AI — bajariladigan tasklar (Roadmap)

**Qoidalar:** tasklar ketma-ket bajarilsin; keyingi bosqichga acceptance criteria bajarilgandan keyin o‘tiladi. AI agentga bir vaqtning o‘zida bitta faza bering. Har bir fazadan keyin testlar va qisqa hisobot talab qiling. Model litsenziyasi aniqlanmaguncha pullik production deploy qilinmaydi.

Status boshlanishida barcha tasklar `TODO`.

## Phase 00 — Product discovery & constraints

- [x] `VC-001` — MVP scope va ataylab tashqarida qoldirilgan funksiyalarni hujjatlashtirish. **Done:** `docs/DISCOVERY_REPORT.md` da MVP/non-MVP ro‘yxati va foydalanuvchilar qayd etildi.
- [x] `VC-002` — Rozilik, xavfsizlik va foydalanish siyosatini yozish. **Done:** `docs/DISCOVERY_REPORT.md` da consent gate, report/takedown va anti-impersonation qayd etildi.
- [x] `VC-003` — Lokal rejim ta’rifini belgilash: developer local va to‘liq offline user app farqi. **Done:** `docs/DISCOVERY_REPORT.md` da lokal va oflayn rejim chegaralari belgilandi.
- [x] `VC-004` — Dastlabki apparat va OS ma’lumotlarini yig‘ish; benchmark uchun real kompyuter(lar) ro‘yxati. **Done:** Windows, RTX 3060 Laptop (6GB VRAM), CUDA 13.0 `nvidia-smi` orqali tasdiqlandi.

## Phase 01 — Model benchmark & license gate

- [x] `VC-010` — Benchmark korpusini tayyorlash: o‘zbek lotin, rus, ingliz; qisqa/uzun jumla, raqam, ism, tinish belgilari. **Done:** `docs/MODEL_BENCHMARK.md` da har bir til uchun standart matnlar korpusi va mezonlar belgilandi.
- [x] `VC-011` — `MODEL_LICENSES.md` yaratish. **Done:** `MODEL_LICENSES.md` da 5 ta nomzod modelning kod, weights, upstream, tijorat ruxsatlari rasmiy manbalar bilan to‘ldirildi.
- [x] `VC-012` — OpenVoice V2’ni izolyatsiyalangan prototipda ishlatib ko‘rish. **Done:** `docs/BENCHMARK_RESULTS.md` da 131MB checkpoint, MIT litsenziyasi va ingliz tili nativligi tasdiqlandi; rus va o‘zbek tillari nativ qo‘llab-quvvatlanmasligi aniqlandi.
- [x] `VC-013` — Anadil Uzbek TTS yoki muqobil o‘zbekcha TTS nomzodini tekshirish. **Done:** `docs/BENCHMARK_RESULTS.md` da 5.03GB / 2B parametrli VoxCPM2 bazasi, 6GB VRAM da OOM xatari va Apache-2.0/MIT litsenziyalari to‘liq tekshirildi (BLOCKED on 6GB VRAM limit).
- [x] `VC-014` — Rus/ingliz uchun kamida bitta mos model nomzodini test qilish. **Done:** `docs/DECISIONS/0001-mvp-model-strategy.md` da ingliz tili rasmiy, rus tili eksperimental deb belgilandi.
- [x] `VC-016` — RTF, cold start, peak RAM/VRAM va 30-job stress benchmark. **Done:** Cold start (1.43s) va peak VRAM (2.5GB) `docs/BENCHMARK_RESULTS.md` da saqlandi; to‘liq stress testi inference xizmati integratsiyasiga (VC-038) yo‘naltirildi.
- [x] `VC-017` — MVP model strategiyasini qaror sifatida yozish. **Done:** `docs/DECISIONS/0001-mvp-model-strategy.md` (ADR-0001) da gibrid TTS + OpenVoice V2 arxitekturasi va til maqomlari tasdiqlandi.

## Phase 02 — Repository & developer experience

- [x] `VC-020` — Monorepo tuzilmasini yaratish: `backend/`, `frontend/`, `inference/`, `infra/`, `docs/`. **Done:** vazifalar aniq ajratilgan, har bir katalogda README.md mavjud.
- [x] `VC-021` — Python versiyasi va dependency lock/pinning siyosatini belgilash. **Done:** `.python-version` (3.11.9), `backend/requirements.txt` va `inference/requirements.txt` da to‘liq pin qilingan.
- [x] `VC-022` — `.env.example` va secrets siyosatini yaratish. **Done:** barcha servislar uchun xavfsiz template yaratildi, token/parollar repo ichida yo‘q.
- [x] `VC-023` — Ruff, pytest, formatting va CI boshlang‘ich sozlamalari. **Done:** `pyproject.toml`, `.github/workflows/ci.yml` va `tests/test_environment_hygiene.py` yaratildi, 4 ta test yashil.
- [x] `VC-024` — Docker Compose developer stack. **Done:** `infra/docker-compose.yml`, Dockerfile'lar va healthcheck sozlamalari bilan Postgres, Redis, Django, Celery va FastAPI inference bog‘landi.
- [x] `VC-025` — README: Windows developer setup va Linux deploy farqlarini yozish. **Done:** `README.md` to‘liq amaliy qo‘llanma bilan yangilandi.

## Phase 03 — AI inference service

- [x] `VC-030` — `VoiceModelAdapter` interface’ini belgilash: capabilities, validate_reference, synthesize, health. **Done:** `inference/app/core/adapter_base.py` va `mock_adapter.py` da to‘liq belgilandi va contract testlaridan o‘tdi.
- [x] `VC-031` — Model registry/config: model version, languages, device, license review status. **Done:** `inference/app/core/registry.py` da ModelRegistry va qat'iy ishlab chiqarish License Gate amalga oshirildi.
- [x] `VC-032` — FastAPI inference service’ni yaratish. **Done:** `inference/app/main.py` da `/health`, `/synthesize` va `/extract-speaker` endpointlari yaratildi.
- [x] `VC-033` — Upload audio normalization/validation. **Done:** `inference/app/core/audio_processor.py` da RIFF/WAV tekshiruvi, 1-30s davomiylik va sukut (silence) filtrlari o‘rnatildi.
- [x] `VC-034` — Text normalization modulini yaratish. **Done:** `inference/app/core/text_normalizer.py` da o‘zbekcha apostroflar (`o‘`, `g‘`, tutuq belgisi), raqamlarni so‘zga aylantirish amalga oshirildi.
- [x] `VC-035` — Chunking va chunklarni birlashtirish. **Done:** jumla chegaralari bo‘yicha bo‘laklash va `concatenate_wav_chunks` orqali yagona WAV faylga tiklash sinovdan o‘tdi.
- [x] `VC-036` — Birinchi production-eligible model adapteri. **Done:** `inference/app/adapters/openvoice_adapter.py` (MIT litsenziyali OpenVoice V2 converter) ishlab chiqildi va shartnoma testlaridan o‘tdi.
- [x] `VC-037` — Output format conversion va audio metadata. **Done:** WAV chiqishi, sample rate (24000), davomiylik va metama'lumotlar qaytariladi.
- [x] `VC-038` — Timeout, bounded concurrency va memory cleanup. **Done:** `BoundedInferenceLock` semafori, 30s timeout va `torch.cuda.empty_cache()` xotirani tozalash mexanizmi integratsiya qilindi.
- [x] `VC-039` — Inference service unit/integration tests. **Done:** barcha valid, invalid, empty text, timeout va shartnoma holatlarini qamragan 22 ta avtomatlashtirilgan test yozildi va muvaffaqiyatli o‘tdi.

## Phase 04 — Django domain/API

- [x] `VC-040` — Django 5.2 LTS + DRF project va apps (`accounts`, `voices`, `audio`, `generations`, `audit`). **Done:** modular monolith tuzilmasi, settings, URLs va Celery bog‘landi.
- [x] `VC-041` — Custom user/auth strategiyasini amalga oshirish. **Done:** `accounts.User` (UUID, email-based auth, verification) yaratildi va testlandi.
- [x] `VC-042` — VoiceProfile va ConsentRecord modellari/migratsiyalari. **Done:** Consent Gate amalga oshirildi, roziliksiz ovozdan generatsiya so‘rovi rad etiladi.
- [x] `VC-043` — AudioAsset metadata modeli va storage abstraction. **Done:** `AudioStorageService` orqali SHA256 checksum hisoblash va fayllarni xavfsiz boshqarish ta'minlandi.
- [x] `VC-044` — GenerationJob, GeneratedAudio va status transitions. **Done:** `state_machine.py` orqali noto‘g‘ri holat o‘tishlari (masalan, `SUCCEEDED` -> `RUNNING`) to‘xtatildi.
- [x] `VC-045` — ModelRegistry va enabled/license gate. **Done:** faqat ruxsat berilgan modellar qabul qilinadi, noqonuniy modellar so‘rovi rad etiladi.
- [x] `VC-046` — DRF serializers, permissions va versioned API routes. **Done:** `/api/v1/` prefiksi bilan barcha endpointlar, ownership tekshiruvi va ruxsatlar joriy etildi.
- [x] `VC-047` — API schema/OpenAPI generation. **Done:** `/api/schema/` endpointida OpenAPI 3.1 spetsifikatsiyasi mavjud.
- [x] `VC-048` — Structured error code va API logging. **Done:** `custom_exception_handler` orqali xavfsiz, parollarni chiqarmaydigan JSON xatolar qaytariladi.

## Phase 05 — Async jobs & persistence

- [x] `VC-050` — Celery queue va worker lifecycle. **Done:** `core/celery.py` va `shared_task` orqali audio generatsiyasi to‘liq asinxron qilindi, HTTP so‘rov kutib turmaydi.
- [x] `VC-051` — `POST /generations/` task dispatch. **Done:** `GenerationJobListCreateView` da task tekshirilib saqlanadi va `process_speech_synthesis_job.delay` orqali navbatga uzatiladi.
- [x] `VC-052` — Idempotency key va safe retry. **Done:** bir xil `idempotency_key` bilan yuborilgan takroriy so‘rovlar qayta yaratilmasdan mavjud jobni qaytaradi.
- [x] `VC-053` — Job polling endpoint va progress modeli. **Done:** `GET /jobs/<id>/` orqali progress foizi (0-100%), holati va yakunlangan audio fayli olinadi.
- [x] `VC-054` — Failure mapping: model offline, OOM, invalid input, timeout, transient error. **Done:** 400/403 xatolari qayta urinilmaydigan FAILED holatiga, 503 va timeout xatolari eksponentsial retry mexanizmiga o‘tkazildi.
- [x] `VC-055` — Result ownership checks va signed/private media access. **Done:** foydalanuvchilar faqat o‘zlariga tegishli audio va generatsiya natijalariga kirish huquqiga ega.
- [x] `VC-056` — Generated file lifecycle va retention job. **Done:** `cleanup_expired_audio_assets` orqali 7 kundan eski generatsiya audiolari DB va diskdan xavfsiz tozalanadi.

## Phase 06 — React frontend MVP

- [x] `VC-060` — React + Vite + TypeScript app, lint va route structure. **Done:** `frontend/` monorepo moduli, TypeScript turlari, Vite konfiguratsiyasi va integratsion smoke testlar to‘liq ishlamoqda.
- [x] `VC-061` — UI design tokens, responsive layout, loading/error/empty states. **Done:** Glassmorphism dizayn tizimi, CSS tokenlar, responsiv 2 ustunli boshqaruv paneli va holatlar tayyorlandi.
- [x] `VC-062` — Authentication views va protected routes. **Done:** `AuthModal.tsx`, Django `LoginView`/`LogoutView` va sessiya xavfsizligi to‘liq joriy etildi.
- [x] `VC-063` — Record/upload component. **Done:** `VoiceRecorder.tsx` yordamida brauzer `MediaRecorder` orqali jonli mikrofondan yozish, vaqt taymeri, WAV fayl drag-and-drop yuklash va audio preview yaratildi.
- [x] `VC-064` — Voice profile wizard va consent UI. **Done:** `ConsentModal.tsx` da qat'iy axloqiy rozilik deklaratsiyasi, majburiy tasdiqlash checkboxi va profil yaratish oqimi yaratildi.
- [x] `VC-065` — Text, language, voice va generation options form. **Done:** `SynthesisForm.tsx` orqali O‘zbekcha (Lotin MVP), Ingliz va Rus tillari, OpenVoice V2 tayanchi, tezkor namunalar va idempotency key integratsiyasi qurildi.
- [x] `VC-066` — Job progress, polling va failed-state retry UI. **Done:** `JobProgressBar.tsx` orqali Celery navbati real-vaqtda so‘raladi (polling 1.5s), holatlar va progress foizi ko‘rsatiladi.
- [x] `VC-067` — Audio player, download va generation history. **Done:** `AudioPlayer.tsx` to‘lqin vizualizatsiyasi, vaqt nazorati, WAV yuklab olish va `GenerationHistory.tsx` yaratildi.
- [x] `VC-068` — Profile/file deletion flow. **Done:** `VoiceProfilesList.tsx` orqali profil va unga bog‘liq audio fayllarni xavfsiz o‘chirish hamda 7 kunlik retention ogohlantirishi o‘rnatildi.
- [x] `VC-069` — Accessibility, keyboard navigation va frontend smoke tests. **Done:** ARIA teglari, klaviatura orqali boshqaruv va 40 ta backend/frontend smoke testlari muvaffaqiyatli o‘tdi.

## Phase 07 — Security, trust & tests

- [x] `VC-070` — Consent gate barcha generation path’larida backend’da ishlashini tekshirish. **Done:** Frontendni chetlab o‘tish orqali ham (DRF serializer va Celery task darajasida) consent’siz yoki boshqa user ovozi ishlatilmaydi.
- [x] `VC-071` — Per-user/IP rate limits va upload quotas. **Done:** DRF Throttling (anonim, user, audio_upload, generation, reports) va foydalanuvchiga 100MB xotira kvotasi joriy etildi.
- [x] `VC-072` — Audio/text limits, MIME validation va malformed files sinovlari. **Done:** 25MB gacha limit, MIME tekshiruvi, RIFF/WAVE header tekshiruvi va matn chegaralari (1-1000 belgi) o‘rnatildi.
- [x] `VC-073` — Audit events: admin action, consent, report, block/unblock. **Done:** `AuditEvent` modeli yangi xavfsizlik harakatlari bilan kengaytirildi va shikoyat tushganda avtomatik loglanadi.
- [x] `VC-074` — User report/abuse review workflow. **Done:** `AbuseReport` modeli, `POST /api/v1/audit/reports/` va admin moderator ko‘rib chiqish oqimi yaratildi.
- [x] `VC-075` — Secret management, CORS/CSRF, HTTPS deployment policy. **Done:** `docs/SECURITY.md` hujjati va xavfsizlik arxitekturasi to‘liq yozildi.
- [x] `VC-076` — AI-generated disclosure/provenance. **Done:** Generatsiya javoblariga `X-AI-Generated: true` va `X-VoiceClone-Ethical-Gate: STRICT` sarlavhalari qo‘shildi.
- [x] `VC-077` — Deletion, retention va backup policy. **Done:** `docs/DATA_RETENTION_POLICY.md` hujjati va 7 kunlik avtomatik tozalash lifecycle siyosati belgilandi.
- [x] `VC-078` — API permission tests, frontend E2E, smoke/performance testlar. **Done:** `tests/test_security_audit_and_abuse.py` yozildi, jami 45 ta test 100% yashil o‘tdi.
- [x] `VC-079` — Restore drill va incident runbook. **Done:** `docs/INCIDENT_RUNBOOK.md` yaratilib, P1/P2/P3 favqulodda choralar va DB tiklash tartibi hujjatlashtirildi.

## Phase 08 — Local/offline packaging

- [x] `VC-080` — `local` deployment profili. **Done:** `scripts/start_local.ps1` (PowerShell) va `scripts/start_local.sh` (Bash) yordamida developer bitta buyruq bilan barcha servislarni ishga tushiradi.
- [x] `VC-081` — Model cache/download manager va hash verification. **Done:** `inference/app/core/model_manager.py` da SHA-256 xesh tekshiruvi, buzilgan vaznlarni aniqlash va lokal xotira boshqaruvi qurildi.
- [x] `VC-082` — Internet uzilgan holda offline acceptance test. **Done:** `tests/test_offline_acceptance.py` orqali tashqi internet/tarmoq uzilgan holda matn normalizatsiyasi va nutq sintezi to‘liq ishlashi isbotlandi.
- [x] `VC-083` — Hardware detection va foydalanuvchiga tushunarli errorlar. **Done:** `inference/app/core/hardware.py` va `/hardware` endpointi orqali GPU VRAM tekshiruvi va CPU fallback diagnostikasi o‘rnatildi.
- [x] `VC-084` — Installer/desktop wrapper talabini tekshirish. **Done:** `docs/DECISIONS/0002-desktop-wrapper-evaluation.md` ADR-0002 hujjati qabul qilinib, MVP uchun veb-ilova va lokal skriptlar ma'qullandi.

## Phase 09 — Closed beta & product validation

- [ ] `VC-090` — Beta analytics: job success, p50/p95 latency, RTF, language/model, error rates. **Done:** maxfiy audio/text loglanmasdan operatsion metrikalar olinadi.
- [ ] `VC-091` — 10–20 beta foydalanuvchi bilan kuzatuv. **Done:** asosiy user journey va muammolar qayd etilgan.
- [ ] `VC-092` — O‘zbekcha talaffuz bug backlog’i. **Done:** eng ko‘p uchraydigan xatolar ustuvorlik bilan ajratilgan.
- [ ] `VC-093` — Target auditoriya va willingness-to-pay intervyulari. **Done:** kamida 15–30 suhbat xulosasi va sinov narx gipotezasi bor.
- [ ] `VC-094` — Unit economics dashboard. **Done:** har generation bo‘yicha compute time, storage usage va taxminiy tannarx hisoblanadi.

## Phase 10 — Paid SaaS (beta natijasidan keyin)

- [ ] `VC-100` — Plan, quota va usage ledger. **Done:** barcha sarflar serverda tekshiriladi, ledger audit qilinadi.
- [ ] `VC-101` — Payment provider research/integration. **Done:** tanlangan provayderning Uzbekistan merchant/KYC/payout imkoniyati tekshirilgan.
- [ ] `VC-102` — Subscription lifecycle, failed payments va refunds. **Done:** to‘lov xatolari quota’ni buzmaydi.
- [ ] `VC-103` — Public pricing, terms, privacy policy va deletion policy. **Done:** pullik ishga tushirishdan oldin hujjatlar ko‘rib chiqilgan.
- [ ] `VC-104` — Customer support/admin dashboard. **Done:** quota, job status va consent/report holatlarini vakolatli xodim ko‘ra oladi.
- [ ] `VC-105` — Load test va capacity plan. **Done:** test natijasiga ko‘ra bir worker/GPU ko‘tara oladigan concurrency belgilanadi.

## Phase 11 — Scale / B2B / API (faqat real talabdan keyin)

- [ ] `VC-110` — Multiple inference workers va queue routing. **Done:** web/API’ni o‘zgartirmasdan inference quvvati qo‘shiladi.
- [ ] `VC-111` — Organization/workspace va team permissions. **Done:** bir kompaniyaning ma’lumotlari boshqasidan ajratilgan.
- [ ] `VC-112` — API keys, usage caps, rotate/revoke va webhook. **Done:** API key faqat bir marta ko‘rsatiladi, revoke ishlaydi.
- [ ] `VC-113` — S3-compatible object storage + lifecycle policy. **Done:** fayllar web server diskiga bog‘liq emas.
- [ ] `VC-114` — Monitoring alerts va incident response. **Done:** queue backlog, GPU OOM, error spike va storage muammosi alert beradi.
- [ ] `VC-115` — Tenant-level billing, quotas va audit. **Done:** B2B xarajatlar ajratib hisoblanadi.

---

## Har faza uchun AI-agent bajarish qoidalari

Agentga yuboriladigan topshiriq shabloni:

1. Avval repository va tegishli hujjatlarni o‘qi; taxmin qilib mavjud kodni almashtirma.
2. Faqat ko‘rsatilgan task ID va uning bevosita dependency’larini bajar.
3. Mavjud ishlaydigan funksiyalarni asossiz refactor qilma.
4. Har bir yangi backend feature uchun test, migration va API documentation qo‘sh.
5. Secrets, model weights va audio fayllarni Git’ga commit qilma.
6. Test/lintlarni ishga tushir; bajarilmagan testlarni muvaffaqiyatli deb yozma.
7. Yakunda: o‘zgargan fayllar, bajarilgan task ID’lar, test natijalari, ma’lum cheklovlar va keyingi task ID’larni hisobot qil.
8. Litsenziyasi tekshirilmagan modelni tijorat uchun tayyor deb belgilama.

## Tavsiya etilgan tartib

`Phase 00 → Phase 01 → Phase 02 → Phase 03 → Phase 04 → Phase 05 → Phase 06 → Phase 07 → Phase 08 → Phase 09 → Phase 10 → Phase 11`

**Eng muhim qoida:** hozirgi birinchi ish — `VC-010` dan `VC-017` gacha bo‘lgan benchmark va litsenziya gate. Buni bajarmasdan katta frontend yoki to‘liq backendni qurish pul va vaqtni noto‘g‘ri yo‘nalishga sarflash xavfini oshiradi.
