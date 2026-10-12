# Sprint Board — Voice Clone AI

## Hozirgi holat (Sprint 02: Model Benchmark Gate)
- [x] `VC-001` - `VC-004`: Discovery va apparat auditi (`docs/DISCOVERY_REPORT.md`)
- [x] `VC-011`: Model litsenziyasi va dataset tahlili (`MODEL_LICENSES.md`)
- [x] `VC-010`: Uch til uchun benchmark korpusi (`docs/MODEL_BENCHMARK.md`)
- [x] `VC-012`: Anadil Uzbek TTS / VoxCPM2 resurs va arxitektura tahlili (`docs/BENCHMARK_RESULTS.md` — 5.03GB / 2B parametr, 6GB VRAM OOM xatari aniqlangan, `BLOCKED`)
- [x] `VC-013`: OpenVoice V2 va MeloTTS tayanchi prototipi (`docs/BENCHMARK_RESULTS.md` — 131MB converter, ingliz tili nativ tasdiqlandi, o‘zbek va rus tillari nativ qo‘llab-quvvatlanmaydi, `PARTIALLY_VERIFIED`)
- [x] `VC-014`: Rus va ingliz tili strategiyasi (`docs/DECISIONS/0001-mvp-model-strategy.md` — ingliz rasmiy, rus eksperimental)
- [x] `VC-016`: Hardware profiling va cold start baholash (`docs/BENCHMARK_RESULTS.md`)
- [x] `VC-017`: MVP model strategiyasi va qarorini yozish (`docs/DECISIONS/0001-mvp-model-strategy.md` ADR-0001)

## Sprint 03 (Monorepo & Developer Setup / Phase 02) — DONE
- [x] `VC-020`: Monorepo strukturasi (`backend/`, `frontend/`, `inference/`, `infra/`, `docs/`)
- [x] `VC-021`: Python versiyasi (3.11.9) va dependency pin siyosati
- [x] `VC-022`: `.env.example` barcha servislar uchun kengaytirilgan konfiguratsiya
- [x] `VC-023`: Ruff, pytest, CI workflow (`.github/workflows/ci.yml`) va testlar
- [x] `VC-024`: Docker Compose developer stack (`infra/docker-compose.yml`, Dockerfile'lar)
- [x] `VC-025`: README: Windows dev va Linux deploy bo‘yicha to‘liq qo‘llanma

## Sprint 04 (AI Inference Service / Phase 03) — DONE
- [x] `VC-030`: `VoiceModelAdapter` interface'ini belgilash (`inference/app/core/adapter_base.py`, `mock_adapter.py`)
- [x] `VC-031`: Model registry va License Gate (`inference/app/core/registry.py`)
- [x] `VC-032`: FastAPI inference service loyihasini yaratish (`inference/app/main.py`)
- [x] `VC-033`: Audio upload validation & normalization (`inference/app/core/audio_processor.py`)
- [x] `VC-034`: Matn normalizatsiyasi (o‘zbek apostroflari, raqamlar) (`inference/app/core/text_normalizer.py`)
- [x] `VC-035`: Chunking moduli va birlashtirish (`concatenate_wav_chunks`)
- [x] `VC-036`: OpenVoice V2 adapteri (`inference/app/adapters/openvoice_adapter.py`)
- [x] `VC-037`: Output format conversion va audio metadata
- [x] `VC-038`: Bounded concurrency (semaphore=1) va VRAM xotira tozalash (`concurrency.py`)
- [x] `VC-039`: Barcha unit va integratsiya testlari (22 ta test to‘liq o‘tdi)

## Sprint 05 (Django Domain & REST API / Phase 04) — DONE
- [x] `VC-040`: Django 5.2 LTS + DRF project va applar strukturasi (`accounts`, `voices`, `audio`, `generations`, `audit`)
- [x] `VC-041`: Custom User modeli va autentifikatsiya strategiyasi
- [x] `VC-042`: VoiceProfile va qat'iy ConsentRecord modellari / migratsiyalari
- [x] `VC-043`: AudioAsset metadata modeli va storage abstraction
- [x] `VC-044`: GenerationJob, GeneratedAudio va holat mashinasi (`state_machine.py`)
- [x] `VC-045`: ModelRegistry va license gate DRF qatlami (`APPROVED_MODELS`)
- [x] `VC-046`: DRF serializers, ruxsatlar va versioned API routes (`/api/v1/`)
- [x] `VC-047`: OpenAPI schema generatori (`/api/schema/`)
- [x] `VC-048`: Strukturaviy xatolar va API logging (`custom_exception_handler`)

## Sprint 06 (Async Jobs & Celery Persistence / Phase 05) — DONE
- [x] `VC-050`: Celery queue va worker lifecycle (`core/celery.py`, `shared_task`)
- [x] `VC-051`: `POST /generations/` asinxron task dispatch (`process_speech_synthesis_job.delay`)
- [x] `VC-052`: Idempotency key va safe retry (`idempotency_key` deduplication, celery backoff)
- [x] `VC-053`: Job polling endpoint va progress modeli (`GET /jobs/<id>/`)
- [x] `VC-054`: Failure mapping: retryable vs non-retryable xatolar ajratildi
- [x] `VC-055`: Result ownership checks va audio natijalar izolyatsiyasi
- [x] `VC-056`: Generated file lifecycle va retention tozalash (`cleanup_expired_audio_assets`)

## Sprint 07 (React Frontend MVP / Phase 06) — DONE
- [x] `VC-060`: React + Vite + TypeScript ilovasi, routing va strukturani yaratish
- [x] `VC-061`: UI dizayn tokenlari, responsiv maket va holatlar (loading, error, empty)
- [x] `VC-062`: Autentifikatsiya sahifalari va himoyalangan yo‘llar (Login, Register, Logout)
- [x] `VC-063`: Audio yozib olish va WAV fayl yuklash komponenti
- [x] `VC-064`: Ovoz profili yaratish va qat'iy Consent UI (Rozilik berish oynasi)
- [x] `VC-065`: Matn, til, ovoz va generatsiya sozlamalari shakli (Form)
- [x] `VC-066`: Generatsiya jarayoni, polling va progress bar komponenti
- [x] `VC-067`: Audio pleer, to‘lqin (waveform) preview va WAV yuklab olish
- [x] `VC-068`: Ovoz profilini va audio tarixini o‘chirish oqimi (Privacy/GDPR)
- [x] `VC-069`: Accessibility (a11y) va frontend smoke testlari (40 ta test to‘liq o‘tdi)

## Sprint 08 (Security, Trust & Tests / Phase 07) — DONE
- [x] `VC-070`: Consent gate barcha generation path'larida backend'da ishlashini tekshirish
- [x] `VC-071`: Per-user/IP rate limits va upload quotas (DRF throttling va 100MB quota)
- [x] `VC-072`: Audio/text limits, MIME validation va malformed files sinovlari (RIFF/WAVE header check)
- [x] `VC-073`: Audit events: admin action, consent, report, block/unblock (`AuditEvent` amallari)
- [x] `VC-074`: User report/abuse review workflow (`AbuseReport` modeli va API endpointlari)
- [x] `VC-075`: Secret management, CORS/CSRF, HTTPS deployment policy (`docs/SECURITY.md`)
- [x] `VC-076`: AI-generated disclosure/provenance (`X-AI-Generated` sarlavhalari)
- [x] `VC-077`: Deletion, retention va backup policy (`docs/DATA_RETENTION_POLICY.md`)
- [x] `VC-078`: API permission tests, frontend E2E, smoke/performance testlar (45 ta test 100% o‘tdi)
- [x] `VC-079`: Restore drill va incident runbook (`docs/INCIDENT_RUNBOOK.md`)

## Sprint 09 (Local/Offline Packaging / Phase 08) — DONE
- [x] `VC-080`: `local` deployment profili va yagona ishga tushirish skripti (`scripts/start_local.ps1`, `scripts/start_local.sh`)
- [x] `VC-081`: Model cache/download manager va hash verification (`model_manager.py`)
- [x] `VC-082`: Internet uzilgan holda offline acceptance test (`tests/test_offline_acceptance.py`)
- [x] `VC-083`: Hardware detection va foydalanuvchiga tushunarli errorlar (`hardware.py`, `/hardware`)
- [x] `VC-084`: Installer/desktop wrapper talabini tekshirish (`docs/DECISIONS/0002-desktop-wrapper-evaluation.md`)

## Hozirgi faol sprint (Sprint 10: Closed Beta & Product Validation / Phase 09) — DONE
- [x] `VC-090`: Beta analytics: job success, p50/p95 latency, RTF, language/model, error rates
- [x] `VC-091`: 10–20 beta foydalanuvchi bilan kuzatuv va user journey
- [x] `VC-092`: O‘zbekcha talaffuz bug backlog'i va normalizatsiya
- [x] `VC-093`: Target auditoriya va willingness-to-pay intervyulari
- [x] `VC-094`: Unit economics dashboard va compute tannarx hisobi



