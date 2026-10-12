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

## Hozirgi faol sprint (Sprint 05: Django Domain & REST API / Phase 04)
- [ ] `VC-040`: Django 5.2 LTS + DRF project va applar strukturasi (`accounts`, `voices`, `consent`, `audio`, `generations`, `audit`)
- [ ] `VC-041`: Custom User modeli va autentifikatsiya strategiyasi
- [ ] `VC-042`: VoiceProfile va qat'iy ConsentRecord modellari / migratsiyalari
- [ ] `VC-043`: AudioAsset metadata modeli va storage abstraction
- [ ] `VC-044`: GenerationJob, GeneratedAudio va holat mashinasi (`PENDING`, `RUNNING`, `SUCCEEDED`, `FAILED`)
- [ ] `VC-045`: ModelRegistry va license gate DRF qatlami
- [ ] `VC-046`: DRF serializers, ruxsatlar va versioned API routes
- [ ] `VC-047`: OpenAPI schema generatori
- [ ] `VC-048`: Strukturaviy xatolar va API logging

