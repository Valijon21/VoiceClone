# ADR-0001: MVP Voice Model va Til Strategiyasi

- **Hujjat kodi:** `docs/DECISIONS/0001-mvp-model-strategy.md`
- **Task ID:** `VC-014`, `VC-017`
- **Sana:** 2026-10-12
- **Muallif:** Senior Software Architect / AI Inference Engineer
- **Holat:** `ACCEPTED` (Tasdiqlangan)

---

## 1. Kontekst va Muammo (Context)

Loyiha oldida o‘zbek, rus va ingliz tillarida rozilik asosida ishlaydigan ovoz sintezi va ovoz klonlash tizimini yaratish vazifasi turibdi. Ishchi apparat — **NVIDIA GeForce RTX 3060 Laptop GPU (6.0 GB VRAM)**.

Sprint 01 va Sprint 02 dagi amaliy o‘lchovlar quyidagi muhim faktlarni ko‘rsatdi:
1. **6 GB VRAM cheklovi:** O‘zbek tili uchun yagona ochiq nomzod bo‘lgan `Anadil Uzbek TTS` 2 milliard parametrli `openbmb/VoxCPM2` autoregressive diffuziya modeliga asoslangan bo‘lib, 5.03 GB vaznga ega va FP16 rejimida 5.5–6.5 GB VRAM talab qiladi. Standart sozlamada 6GB GPU’da **OOM (Out Of Memory) xavfi yuqori**.
2. **OpenVoice V2 imkoniyatlari:** `ToneColorConverter` atigi **131 MB** vaznga ega, xotiraga **1.43 soniyada** yuklanadi, MIT litsenziyali va 2–2.5 GB VRAM da barqaror ishlaydi. Biroq, OpenVoice universal TTS emas — u ovoz rangini o‘zgartiruvchi adapter bo‘lib, uning bazaviy `MeloTTS` modeli faqat ingliz, ispan, fransuz, xitoy, yapon va koreys tillarini qo‘llab-quvvatlaydi. Rus va o‘zbek tillari unda **mavjud emas**.
3. **Litsenziya tozaligi:** Coqui XTTS (CPML) va F5-TTS (CC-BY-NC) tijoratda foydalanishni cheklaydi, shuning uchun production tizimiga olinmaydi.

---

## 2. Qabul qilingan Qaror (Decision)

Quyidagi **Gibrid Model Arxitekturasi** tasdiqlandi:

### A. Ovozni Klonlash Mexanizmi (Voice Color Cloning)
- **Tanlangan model:** `OpenVoice V2 ToneColorConverter` (MyShell).
- **Litsenziya:** MIT License (`VERIFIED` — tijoratga to‘liq yaroqli).
- **Vazn:** 131 MB checkpoint.
- **Vazifasi:** Har qanday bazaviy TTS yaratgan audioni foydalanuvchining ma’lumot beruvchi (reference) ovozi tembriga moslab o‘zgartirish.

### B. Til bo‘yicha Bazaviy TTS Strategiyasi (Backbone Strategy)

| Til | Tanlangan Yondashuv | Maqom | Litsenziya |
|---|---|---|---|
| **Ingliz tili** | `MeloTTS-English` + OpenVoice V2 | **SUPPORTED (Rasmiy qo‘llab-quvvatlanadi)** | MIT (`VERIFIED`) |
| **O‘zbek tili** | `VoiceModelAdapter` orqali Anadil / VITS Uzbek | **SUPPORTED (MVP Primary Target)** | MIT / Apache-2.0 (`NEEDS_REVIEW` on dataset) |
| **Rus tili** | `VoiceModelAdapter` orqali Silero TTS v4 | **EXPERIMENTAL (Sinov rejimida)** | GNU GPL / Muqobil MIT |

### C. 6 GB VRAM Hardware Mitigatsiyasi
- Model inference alohida FastAPI xizmatiga (`inference/`) chiqariladi.
- Model yuklanishi: `bounded concurrency = 1` (bir vaqtning o‘zida faqat 1 ta model xotirada faol bo‘ladi).
- 2B parametrli VoxCPM2 og‘ir modeli uchun rasmiy `low-memory` / `torch.compile(mode="reduce-overhead")` yoki CPU fallback rejimlaridan foydalaniladi.
- Barcha model chaqiruvlari umumiy `VoiceModelAdapter` interfeysi ortiga yashiriladi.

---

## 3. Qaror Oqibatlari (Consequences)

### Ijobiy jihatlari:
- **Xavfsiz va barqaror:** RTX 3060 6GB VRAM to‘lib qolmaydi; tizim OOM tufayli qulab tushmaydi.
- **Qonuniy tozalik:** Tizimga tijoriy taqiqlangan CPML yoki CC-BY-NC vaznlari kiritilmaydi.
- **Arxitektura moslashuvchanligi:** `VoiceModelAdapter` tufayli ertaga o‘zbek tili uchun yengilroq VITS/FastSpeech2 modeli paydo bo‘lsa, backend kodini o‘zgartirmasdan ulab ketish mumkin.

### Cheklovlar va Majburiyatlar:
- Rus tili birinchi MVPda "to‘liq qo‘llab-quvvatlanadi" deb e’lon qilinmaydi, "experimental" deb belgilanadi.
- O‘zbek tili o‘quv korpusi litsenziyasi bo‘yicha qo‘shimcha audit talab etiladi.
- OpenVoice har doim 2 bosqichli pipeline (Base TTS -> Tone Converter) orqali ishlaydi.

---

## 4. Holat va Bog‘liq Tasklar
- `VC-014` — Rus va ingliz model strategiyasi: `DONE`.
- `VC-017` — MVP model strategiyasi ADR: `DONE`.
- Keyingi qadam: Phase 02 (Monorepo va developer muhiti, `VC-020`–`VC-025`).
