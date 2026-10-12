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

## Hozirgi faol sprint (Sprint 03: Monorepo & Developer Setup / Phase 02)
- [ ] `VC-020`: Monorepo strukturasi (`backend/`, `frontend/`, `inference/`, `infra/`, `docs/`)
- [ ] `VC-021`: Python versiyasi va dependency boshqaruv siyosati
- [ ] `VC-022`: `.env.example` va xavfsizlik/maxfiylik shartlari
- [ ] `VC-023`: Ruff, pytest va CI workflow (`.github/workflows/ci.yml`)
- [ ] `VC-024`: Docker Compose developer stack
- [ ] `VC-025`: README: Windows developer setup va Linux deploy farqlari
