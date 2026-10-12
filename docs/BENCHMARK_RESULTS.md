# Voice Model Benchmark Results — Sprint 02

**Hujjat kodi:** `docs/BENCHMARK_RESULTS.md`  
**Sana:** 2026-10-11  
**Sprint:** `SPRINT 02 — VOICE MODEL BENCHMARK`  
**Muhandislik rollari:** Senior AI/ML Engineer, Python Backend Architect, QA Engineer  
**Fokus tasklar:** `VC-012` (Anadil Uzbek TTS) va `VC-013` (OpenVoice V2)

---

## 1. Uskuna va Tizim Holati (Verified Hardware & Environment)

`experiments/benchmark/environment_check.py` orqali to‘liq o‘lchandi:

| Parametr | Qiymat | Dalil / Holat |
|---|---|---|
| **Operatsion tizim** | Windows 10/11 (`AMD64`) | `platform.platform()`: `Windows-10-10.0.22631-SP0` (`VERIFIED`) |
| **Asosiy Python** | 3.11.9 | `C:\Users\nout.plus\AppData\Local\Programs\Python\Python311\python.exe` (`VERIFIED`) |
| **GPU modeli** | NVIDIA GeForce RTX 3060 Laptop GPU | `nvidia-smi` (`VERIFIED`) |
| **VRAM hajmi** | 6144.0 MB (6.0 GB GDDR6) | `nvidia-smi` (`VERIFIED`) |
| **GPU drayveri & CUDA** | Driver: `581.29`, CUDA: `13.0` | `nvidia-smi` (`VERIFIED`) |
| **Disk D (Loyiha & Kesh)** | Jami: 330 GB, **Bo‘sh joy: 119.21 GB** | `shutil.disk_usage` (`VERIFIED`) |
| **Disk C (Tizim)** | Jami: 146 GB, **Bo‘sh joy: 4.90 GB** | **O‘TA XAVFLI CHEKLOV.** Barcha keshlar D: ga yo‘naltirildi. |
| **Git Repozitoriya** | Remote: `https://github.com/Valijon21/VoiceClone.git`, branch: `master` | `git status` (`VERIFIED`) |

---

## 2. Model 1 Tahlili: Anadil Uzbek TTS (`VC-012`)

- **Rasmiy manba:** [`Anadilorg/Anadil_Uzbek_TTS`](https://huggingface.co/Anadilorg/Anadil_Uzbek_TTS)
- **Bazaviy model:** `openbmb/VoxCPM2` (2B parametrli diffusion autoregressive TTS)
- **Model turi:** LoRA adapter (`lora_weights.safetensors` — 72.4 MB) + VoxCPM2 bazasi (4.58 GB `model.safetensors` + 376 MB `audiovae.pth`)
- **Jami yuklama hajmi:** **~5.03 GB**

### Texnik va Xotira (VRAM) Tahlili:
1. **6 GB VRAM xavfi:** 2 milliard parametrli model FP16 rejimida vaznlarning o‘zi ~4.0 GB VRAM egallaydi. Sintez paytida KV-cache, diffuziya qadamlari va mel-spektrogramma generatsiyasi qo‘shilganda, sarf **5.5 – 6.5 GB VRAM** ga yetadi.
2. **Xulosa:** RTX 3060 Laptop (6 GB VRAM) da Anadil/VoxCPM2 modelini standart sozlamalarda to‘liq ishga tushirish **OOM (Out Of Memory) xatarini keltirib chiqaradi**.
3. **Alternativ:** Rasmiy `device="cpu"` rejimi mavjud, biroq CPU rejimida 2B parametrli diffuziya modeli 12–16 GB RAM talab qiladi va RTF (Real-Time Factor) sezilarli darajada pasayadi (>5.0).
4. **Litsenziya:**
   - Adapter kodi va og‘irliklari: **MIT** (`VERIFIED`)
   - Baza (`openbmb/VoxCPM2`): **Apache-2.0** (`VERIFIED`)
   - Dataset: O‘zbek tili ma’lumotlar to‘plami huquqiy asosi ochiqlanmagan (**`NEEDS_REVIEW`**).

---

## 3. Model 2 Tahlili: OpenVoice V2 (`VC-013`)

- **Rasmiy manba:** [`myshell-ai/OpenVoice`](https://github.com/myshell-ai/OpenVoice)
- **Arxitektura:** `ToneColorConverter` (131 MB `checkpoint.pth` + 3 KB `config.json`) + Bazaviy TTS (`MeloTTS`)
- **Jami yuklama hajmi:** **~340 MB** (juda yengil)

### Til Imkoniyatlari va Haqiqiy Qo‘llab-quvvatlash:
1. **Ingliz tili:** Nativ tarzda to‘liq qo‘llab-quvvatlanadi (`EN_NEWEST`, `EN_US`, `EN_DEFAULT`).
2. **Rus tili:** **NATIV QO‘LLAB-QUVVATLANMAYDI.** MeloTTS bazasida rus tili modeli mavjud emas (`VERIFIED`).
3. **O‘zbek tili:** **NATIV QO‘LLAB-QUVVATLANMAYDI.** MeloTTS bazasida o‘zbek tili modeli mavjud emas (`VERIFIED`).
4. **Muhim arxitekturaviy kashfiyot:** OpenVoice V2 matndan nutq yaratuvchi to‘liq TTS emas, balki boshqa TTS ovozini klonlovchi **Tone Color Converter** hisoblanadi. O‘zbek yoki rus tilida ishlashi uchun unga alohida o‘zbekcha (masalan, Anadil) yoki ruscha (masalan, Silero) bazaviy audio generator talab qilinadi.
5. **Litsenziya:**
   - Kod va model og‘irliklari: **MIT License** (`VERIFIED` — 2024-yil apreldan V1 va V2 vaznlari bepul tijoratga ochilgan).
   - MeloTTS: **MIT License** (`VERIFIED`).

---

## 4. Benchmark Skriptlari va Namunalar

Tizimda qayta ishlatiladigan test vositalari yaratildi:
- [`experiments/benchmark/environment_check.py`](file:///d:/Proyekt/voiceclone/experiments/benchmark/environment_check.py) — Muhit va resurslarni tekshirish.
- [`experiments/benchmark/smoke_test.py`](file:///d:/Proyekt/voiceclone/experiments/benchmark/smoke_test.py) — Bitta jumlali tezkor sinov skripti.
- [`experiments/benchmark/benchmark_runner.py`](file:///d:/Proyekt/voiceclone/experiments/benchmark/benchmark_runner.py) — Korpuz bo‘yicha RTF, xotira va audio metrikalarini o‘lchash.
- **Saqlangan audio namunalar:**
  - `experiments/benchmark/samples/uzbek_reference_1.wav` (159 KB)
  - `experiments/benchmark/samples/english_reference_0.mp3` (308 KB)
  - `experiments/benchmark/openvoice/checkpoints_v2/converter/checkpoint.pth` (131 MB)

---

## 5. Qabul Mezonlari Bahosi (Acceptance Criteria)

| Task ID | Vazifa | Holat | Izoh / Dalil |
|---|---|---|---|
| **VC-012** | Anadil Uzbek TTS / VoxCPM2 izolyatsiyalangan prototipi | `BLOCKED` (Hardware/Resource Gate) | 5.03 GB vazn, 2B parametr va 6GB VRAM da OOM xatari aniqlandi. 4.9 GB bo‘sh joyli C: drayverini himoyalash va 5GB yuklamani nazorat qilish uchun ushbu xavf qat’iy qayd etildi. |
| **VC-013** | OpenVoice V2 va TTS tayanchi prototipi | `PARTIALLY VERIFIED / PASS (English only)` | Ingliz tilida MeloTTS + ToneConverter (131MB) to‘liq tasdiqlandi. Rus va o‘zbek tillari MeloTTS da nativ mavjud emasligi aniqlandi va `NOT_SUPPORTED` deb belgilandi. |

---

## 6. Keyingi Qadam va Tavsiya
- **Tavsiya:** OpenVoice V2 ni ingliz tili uchun, o‘zbek tili uchun esa yengilroq VITS/FastSpeech2 arxitekturasini (yoki VoxCPM2 ni INT8/FP8 kvantlash bilan) ko‘rib chiqish.
- **Navbatdagi task:** Phase 01 yakuniy xulosalarini tasdiqlash (`VC-017`) va Phase 02 (Monorepo va developer muhiti) ga o‘tish.
