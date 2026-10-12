# VoiceClone Documentation Index

Ushbu katalog loyihaning barcha arxitektura, tadqiqot, benchmark va texnik qarorlari (ADR) saqlanadigan yagona rasmiy bilimlar bazasidir.

## Asosiy Hujjatlar

1. **[SYSTEM_DESIGN.md](file:///docs/SYSTEM_DESIGN.md)**  
   Loyihaning to‘liq tizimli dizayni: mahsulot maqsadi, arxitektura sxemasi (Django + Celery + FastAPI Inference + React), ma'lumotlar bazasi tuzilmasi, audio pipeline, xavfsizlik va rozilik siyosati.

2. **[DISCOVERY_REPORT.md](file:///docs/DISCOVERY_REPORT.md)**  
   Phase 00 tahlil hisoboti: MVP chegaralari, tashqarida qoldirilgan funksiyalar, apparat profili, rozilik va huquqiy talablar.

3. **[BENCHMARK_ENVIRONMENT.md](file:///docs/BENCHMARK_ENVIRONMENT.md)**  
   Apparat va operatsion tizim tekshiruvi: NVIDIA RTX 3060 Laptop GPU (6.0 GB VRAM), CUDA 13.0 / 12.1, Python 3.11.9, Disk C va Disk D xavfsizlik choralari.

4. **[MODEL_BENCHMARK.md](file:///docs/MODEL_BENCHMARK.md)**  
   Modelni sinash uslubiyoti: O‘zbek (lotin), Rus va Ingliz tillari uchun 45 ta jumlali benchmark korpusi hamda 1–5 ballik MOS audio sifat jadvali.

5. **[BENCHMARK_RESULTS.md](file:///docs/BENCHMARK_RESULTS.md)**  
   Amaliy benchmark natijalari: OpenVoice V2 ToneColorConverter (131 MB) va Anadil Uzbek TTS (VoxCPM2 2B parametr, 5.03 GB) resurs o‘lchovlari.

## Arxitektura Qarorlari (Architecture Decision Records — ADR)

- **[0001-mvp-model-strategy.md](file:///docs/DECISIONS/0001-mvp-model-strategy.md)**  
  ADR-0001: MVP model va til strategiyasi (OpenVoice V2 ToneColorConverter + gibrid TTS adapterlar, ingliz tili rasmiy, rus tili eksperimental, 6GB VRAM OOM xatari mitigatsiyasi).
