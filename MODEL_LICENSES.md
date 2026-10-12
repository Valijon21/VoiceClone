# Model License Register — Voice Clone AI

**Hujjat kodi:** `MODEL_LICENSES.md`  
**Task ID:** `VC-011`  
**Yangilangan sana:** 2026-10-11  
**Qat’iy qoida:** Kod litsenziyasi bilan model og‘irliklari (weights), bazaviy model va dataset shartlari bir xil emas. Manba to‘liq isbotlanmagan bo‘lsa `NEEDS_REVIEW` deb belgilanadi. Litsenziyasi noaniq yoki tijoratga ruxsati bo‘lmagan model production rejimiga chiqarilmaydi.

---

## 1. Model: Anadil Uzbek TTS (LoRA Adapter)
- **Rasmiy repository:** Hugging Face Hub — `Anadilorg/Anadil_Uzbek_TTS`
- **Model card / weights URL:** https://huggingface.co/Anadilorg/Anadil_Uzbek_TTS
- **Tekshirilgan sana:** 2026-10-11
- **Code license:** MIT (`VERIFIED`)
- **Weights/checkpoint license:** MIT (Model card metadata — `VERIFIED`)
- **Bazaviy model (Base Model):** `openbmb/VoxCPM2` (2B parameter diffusion autoregressive TTS)
- **Base model license:** Apache-2.0 (`VERIFIED` — OpenBMB GitHub va Hugging Face)
- **Tokenizer / vocoder license:** Apache-2.0 / AudioVAE (`VERIFIED`)
- **Dataset license / provenance:** `NEEDS_REVIEW` (O‘zbekcha nutq korpusi mualliflik huquqi va rozilik zanjiri to‘liq ochiqlanmagan)
- **Commercial use allowed?** `YES` (MIT + Apache-2.0 doirasida ruxsat berilgan)
- **Redistribution allowed?** `YES`
- **Attribution required?** `YES` (MIT va Apache-2.0 notice talab etiladi)
- **Additional terms / restrictions:** Ovoz klonlashda roziliksiz shaxsga taqlid qilishni taqiqlovchi etika qoidalari
- **Languages explicitly supported by source:** O‘zbek tili (Lotin)
- **Tested languages and benchmark evidence:** `PENDING BENCHMARK EXECUTION`
- **Apparat talabi:** ~5.03 GB disk, 2B parametr sababli kamida 5–6 GB VRAM yoki 16 GB RAM (CPU fallback)
- **Final decision:** `APPROVED FOR BENCHMARK` / `COMMERCIAL: NEEDS_REVIEW ON DATASET`

---

## 2. Model: OpenVoice V2 (Tone Color Converter)
- **Rasmiy repository:** https://github.com/myshell-ai/OpenVoice
- **Model card / weights URL:** https://huggingface.co/myshell-ai/OpenVoiceV2
- **Tekshirilgan sana:** 2026-10-11
- **Code license:** MIT License (`VERIFIED` — repo root)
- **Weights/checkpoint license:** MIT License (`VERIFIED` — 2024-yil apreldan V1 va V2 vaznlari MIT ga o‘tkazilgan)
- **TTS Tayanchi (Base Speaker Backbone):** `MeloTTS` (MyShell)
- **Base TTS license:** MIT License (`VERIFIED`)
- **Tokenizer / vocoder license:** MIT / HiFi-GAN (`VERIFIED`)
- **Dataset license / provenance:** `NEEDS_REVIEW` (MyShell ko‘p tilli korpusi)
- **Commercial use allowed?** `YES` (MyShell tomonidan bepul tijorat foydalanishiga ruxsat berilgan)
- **Redistribution allowed?** `YES`
- **Attribution required?** `YES` (MyShell copyright notice)
- **Additional terms / restrictions:** Noqonuniy impersonationga qarshi xavfsizlik cheklovlari
- **Languages explicitly supported by source:**
  - Natively supported: **English** (US, UK, India, Australia, Default), **Spanish, French, Chinese, Japanese, Korean** (`VERIFIED`)
  - **Russian:** `NOT NATIVELY SUPPORTED` (MeloTTS bazasida ruscha model yo‘q)
  - **Uzbek:** `NOT NATIVELY SUPPORTED` (MeloTTS bazasida o‘zbekcha model yo‘q)
- **Tested languages and benchmark evidence:** Ingliz tili benchmark qilinadi; o‘zbek va rus tillari uchun tashqi TTS tayanchi zarur
- **Apparat talabi:** ~340 MB model vaznlari, 2–3 GB VRAM (RTX 3060 uchun yengil va xavfsiz)
- **Final decision:** `APPROVED FOR BENCHMARK (ENGLISH ONLY AS NATIVE)` / `UZBEK/RUSSIAN: REQUIRES EXTERNAL BACKBONE`

---

## 3. Model: Coqui XTTS-v2 (Taqqoslama nomzod)
- **Rasmiy repository:** https://github.com/coqui-ai/TTS
- **Model card / weights URL:** https://huggingface.co/coqui/XTTS-v2
- **Code license:** MPL-2.0
- **Weights/checkpoint license:** Coqui Public Model License (CPML) (`VERIFIED`)
- **Commercial use allowed?** `NO` (CPML bo‘yicha tijoratda foydalanish qat’iyan cheklangan)
- **Final decision:** `REJECTED FOR PRODUCTION` (Faqat sifat taqqoslash uchun)

---

## 4. Model: F5-TTS (Taqqoslama nomzod)
- **Rasmiy repository:** https://github.com/SWivid/F5-TTS
- **Code license:** MIT
- **Weights/checkpoint license:** CC-BY-NC 4.0 (`VERIFIED` — Non-commercial)
- **Commercial use allowed?** `NO` (Notijoriy cheklov)
- **Final decision:** `REJECTED FOR PRODUCTION`

---

## Litsenziyalar bo‘yicha xulosa:
1. **OpenVoice V2** tijorat nuqtai nazaridan eng toza (MIT) model, biroq u mustaqil TTS emas — ovoz rangini o‘zgartiruvchi (voice conversion) adapter. U faqat ingliz tilida o‘zining bazaviy MeloTTS modeliga ega.
2. **Anadil Uzbek TTS** o‘zbek tili uchun ochiq litsenziyali (MIT adapter + Apache-2.0 VoxCPM2) yagona tayyor nomzod bo‘lib turibdi, biroq dataset huquqiy kelib chiqishi tijoratdan oldin qo‘shimcha tekshiruvni (`NEEDS_REVIEW`) talab etadi.
