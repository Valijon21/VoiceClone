# Discovery Report — Voice Clone AI

**Sana:** 2026-10-11  
**Holat:** Dastlabki audit yakunlandi (Phase 00 & Phase 01 Gate)  
**Tuzuvchi:** Senior Software Architect / AI Inference Engineer (Antigravity)  
**Repozitoriy:** `https://github.com/Valijon21/VoiceClone.git` (branch: `master`)

---

## 1. Ishchi Muhit va Apparat Auditi (Hardware & OS)

| Parametr | Qiymat / Holat | Dalil / Manba | Holat |
|---|---|---|---|
| **Operatsion tizim** | Windows (x64) | PowerShell muhiti | `VERIFIED` |
| **GPU** | NVIDIA GeForce RTX 3060 Laptop GPU | `nvidia-smi` | `VERIFIED` |
| **VRAM** | 6144 MiB (6.0 GB GDDR6) | `nvidia-smi` | `VERIFIED` |
| **Drayver versiyasi** | 581.29 | `nvidia-smi` | `VERIFIED` |
| **CUDA qo‘llab-quvvatlash** | CUDA 13.0 | `nvidia-smi` | `VERIFIED` |
| **Git** | 2.51.0.windows.2 | `git --version` | `VERIFIED` |
| **Python** | Tizimda mavjud, izolyatsiyalangan venv/conda talab etiladi | Sandbox PATH cheklovi | `ASSUMPTION` |
| **Node.js** | 20+ (ag-kit CLI orqali tasdiqlangan) | Antigravity IDE | `VERIFIED` |
| **Docker** | Aniqlanmadi (Windows Container / WSL2) | Tekshiruvda | `UNKNOWN` |

### Apparat xulosasi va cheklovlar:
- **6 GB VRAM cheklovi:** O‘rta va yengil TTS modellar (OpenVoice V2, MeloTTS, Anadil Uzbek TTS, XTTS-v2 single-stream FP16) 6GB VRAM’da ishlay oladi.
- **Xavf:** Bir vaqtning o‘zida bir nechta og‘ir modelni VRAM’ga yuklash yoki uzoq audio generatsiya qilish OOM (Out Of Memory) xatosiga olib kelishi mumkin.
- **Qaror:** Inference worker faqat 1 ta modelni faol VRAM’da ushlab turadi, batch size = 1, timeout va bounded concurrency cheklovlari majburiy bo‘ladi.

---

## 2. Mahsulot Ko‘lami va Chegaralari (Scope & Boundaries — VC-001)

### MVP Ko‘lami (In-Scope):
1. **Faqat ruxsatli audio:** Foydalanuvchining o‘z ovozi yoki yozma/tasdiqlangan roziligi bo‘lgan ovoz profili.
2. **Uch til:**
   - **O‘zbek tili (Lotin):** Asosiy e’tibor, alifbo belgilari (`o‘`, `g‘`, `sh`, `ch`, `ng`, tutuq belgisi).
   - **Rus tili:** Fonetik to‘g‘rilik va urg‘ular.
   - **Ingliz tili:** Bazaviy benchmark va xalqaro moslik.
3. **Arxitektura:** Modular Monolith (Django 5.2 + DRF) + Ajratilgan FastAPI Inference Worker + Celery/Redis fon rejimi.
4. **Lokal ishga tushirish:** Developer o‘z shaxsiy kompyuterida (RTX 3060) to‘liq ishga tushira olishi.

### MVPdan Chiqarilgan Qismlar (Out-of-Scope / Non-MVP):
- ❌ Mashhurlar (celebrities) yoki jamoat arboblari ovozini klonlash katalogi.
- ❌ Real-time (jonli mikrofon orqali suhbatda ovozni o‘zgartirish / stream).
- ❌ Telefon orqali qo‘ng‘iroq qilish yoki avtomatlashtirilgan spam/robocall tizimlari.
- ❌ Katta hajmdagi model fine-tuning (MVP faqat few-shot / zero-shot cloning bilan cheklanadi).
- ❌ Erta bosqichda Kubernetes yoki tarmoqlangan microservices klasteri.

---

## 3. Xavfsizlik, Rozilik va Maxfiylik Siyosati (VC-002)

1. **Consent Gate:** Har bir yaratilgan `VoiceProfile` uchun rozilik tekshiruvi backend darajasida majburiy (`ConsentRecord`).
2. **Audio Maxfiyligi:** Foydalanuvchi yuklagan audio fayllar va sintez natijalari ochiq static papkaga qo‘yilmaydi; har bir faylga faqat uning egasi kirishi ta’minlanadi.
3. **Anti-Impersonation:** Shaxsni aldash, firibgarlik yoki ovozli biometriyani buzish maqsadidagi foydalanish taqiqlanadi. Abuse/Report mexanizmi bo‘ladi.
4. **Data Retention & Deletion:** Foydalanuvchi o‘z profilini yoki audiosini o‘chirganda, diskdagi barcha bog‘liq fayllar to‘liq tozalanadi.

---

## 4. Lokal va Oflayn Rejim Chegaralari (VC-003)

- **Local Developer Mode:** Backend, frontend, database va inference xizmati bitta kompyuterda (localhost) ishlaydi. Model fayllari lokal keshdan yuklanadi.
- **Offline Capability:** Internet aloqasi uzilganda ham, lokal yuklangan model va PostgreSQL orqali sintez qilish mumkin bo‘lishi lozim. Tashqi API’larga (OpenAI, ElevenLabs va h.k.) bog‘lanmaslik talab etiladi.

---

## 5. Xatarlar va Noaniqliklar (Risk Register)

| ID | Xatar tavsifi | Daraja | Yechim / Mitigatsiya |
|---|---|---|---|
| **R-01** | O‘zbek tili uchun tayyor TTS modellarining kamligi | YUQORI | `Anadil Uzbek TTS` va OpenVoice V2 birlashmasini test qilish; benchmark natijalariga qarab fallback tanlash. |
| **R-02** | 6GB VRAM cheklovi (OOM) | O‘RTA | Modelni FP16 / INT8 kvantlash, chunking (matnni bo‘laklash) va qat’iy worker concurrency = 1 qilish. |
| **R-03** | Model litsenziyalari (Tijoriy cheklovlar) | YUQORI | Coqui XTTS (CPML) va F5-TTS (CC-BY-NC) tijoriy litsenziyasi cheklangan. Ularni faqat texnik solishtirish uchun ishlatish, tijoratga MIT/Apache-2 litsenziyali modellarni ustuvor qilish. |
| **R-04** | O‘zbek tilidagi apostrof va urg‘ular | O‘RTA | Maxsus `text_normalizer` moduli orqali `o‘`, `g‘`, `'` va boshqa harflarni standartlashtirish. |

---

## 6. Xulosa va Faza Natijasi

- **Phase 00 (Discovery):** Bajarildi (`PASS`).
- **Phase 01 (Benchmark & License Gate):** Navbatdagi faol faza. `docs/MODEL_BENCHMARK.md` va `MODEL_LICENSES.md` yaratishga o‘tiladi.
