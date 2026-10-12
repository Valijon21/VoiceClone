# VoiceClone AI Inference Service

## 1. Vazifasi va Arxitekturadagi O‘rni
AI Inference xizmati barcha mashinali o‘rganish (PyTorch, Torchaudio, OpenVoice, TTS) modellarini xotiraga yuklash va audio xom-ashyosini generatsiya qilishga javobgar alohida mikroservisdir.

U tashqi ochiq internetga ochilmaydi. Faqat Django Celery worker'laridan ichki xavfsiz HTTP so‘rovlarni qabul qiladi. Bu Django veb-serveri va ma'lumotlar bazasini og‘ir GPU/C-CUDA dependency'laridan butunlay toza saqlash imkonini beradi.

## 2. Texnologik Stek
- **Framework:** Python 3.11 + FastAPI + Uvicorn
- **AI/ML Runtime:** PyTorch 2.5+ (CUDA 12/13), Torchaudio
- **Audio ishlov berish:** Librosa, SoundFile, FFmpeg
- **Modellar:**
  - `OpenVoice V2 ToneColorConverter` (131 MB) — ovoz tembrini moslash.
  - `MeloTTS` — ingliz tili bazaviy TTS.
  - `VoiceModelAdapter` orqali ulangan milliy o‘zbekcha va ruscha modellar.

## 3. Resurs va Xotira Cheklovlari (RTX 3060 6GB VRAM)
1. **Bounded Concurrency:** GPU'da bir vaqtning o‘zida faqat 1 ta sintez vazifasi (`concurrency=1`) bajariladi; qolgan so‘rovlar navbatda turadi yoki rad etiladi.
2. **Memory Cleanup:** Har bir generatsiya sessiyasidan so‘ng `torch.cuda.empty_cache()` chaqiriladi.
3. **No Dynamic Arbitrary Loading:** Faqat `MODEL_LICENSES.md` da tekshirilgan va `ModelRegistry` da ro‘yxatga olingan modellargina yuklanadi.
4. **Endpoints:**
   - `GET /health` — GPU holati, VRAM bo‘shligi va faol modellar ro‘yxati.
   - `POST /synthesize` — Matn, til va ovoz namunasi asosida WAV generatsiya qilish.
   - `POST /extract-speaker` — Reference audiodan spiker embedding'ini ajratib olish.
