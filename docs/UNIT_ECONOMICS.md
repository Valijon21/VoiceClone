# VoiceClone AI — Unit Economics va Compute Tannarx Hisoboti (VC-094)

**Hujjat turi:** Financial Engineering & Infrastructure Economics  
**Sana:** 2026-yil oktyabr  
**Faza:** Phase 09 — Closed beta & product validation  
**Metodologiya:** Real operatsion telemetriya (RTF 0.38), Cloud GPU tariflari va mahalliy narxlar tahlili  
**Holat:** Tasdiqlandi (`VERIFIED`)  
**Tuzuvchi:** Senior Software Architect & FinOps Engineer  

---

## 1. Asosiy Texnik Parametrlar va Kiritmalar

Operatsion telemetriya ([OperationalMetric](file:///d:/Proyekt/voiceclone/backend/apps/audit/models.py)) va 84 ta sinov generatsiyasi natijalari:
- **O‘rtacha Real-Time Factor (RTF):** **0.38**  
  *(Ya'ni 1 soniyalik audio sintez qilish uchun 0.38 soniya GPU compute vaqti sarflanadi).*
- **1 daqiqa (60 soniya) audio ishlab chiqarish uchun zarur GPU vaqti:**  
  $$60 \times 0.38 = 22.8\text{ soniya}$$
- **Cloud GPU Instansiyasi (NVIDIA T4 / RTX 4000 Ada / L4 16GB):**
  - Oylik narx: ~$250 / oy
  - Soatlik narx: **$0.35 / soat** (on-demand cloud)
  - 1 soniya GPU compute narxi: $\frac{\$0.35}{3600} \approx \$0.0000972$ (~**1.23 so‘m / soniya**)
- **Valyuta kursi (USD / UZS):** 1 USD = 12,650 UZS

---

## 2. 1 Daqiqa Audio Sintezining To‘liq Tannarxi (COGS — Cost of Goods Sold)

| Xarajat Komponenti | Parametr va Hajm | Xarajat (USD) | Xarajat (UZS) | Ulush (%) |
|---|---|:---:|:---:|:---:|
| **GPU Compute Time** | 22.8 soniya hisoblash | $0.00222 | 28.08 so‘m | **84.5%** |
| **Audio Xotirasi (Storage)** | 2.88 MB WAV fayl (7 kunlik saqlash) | $0.00002 | 0.25 so‘m | **0.8%** |
| **Trafik & Egress Bandwidth** | 2.88 MB yuklab olish ($0.05/GB) | $0.00014 | 1.77 so‘m | **5.3%** |
| **Redis / DB / CPU Monolith** | API va Celery boshqaruvi | $0.00025 | 3.16 so‘m | **9.4%** |
| **JAMI 1 DAQIQA TANNARXI (COGS):** | **60s tayyor audio** | **$0.00263** | **~33.26 so‘m** | **100%** |

> **Xulosa:** VoiceClone AI tizimida 1 daqiqalik yuqori sifatli klonlangan audio ishlab chiqarishning sof texnik tannarxi **~33.3 so‘m** (chorak sentdan kamroq)ni tashkil etadi!

---

## 3. Tariflar Bo‘yicha Daromad va Yalpi Foyda Marjasi (Gross Margin)

[docs/WILLINGNESS_TO_PAY_REPORT.md](file:///d:/Proyekt/voiceclone/docs/WILLINGNESS_TO_PAY_REPORT.md) da tasdiqlangan tariflar bilan solishtirma tahlil:

| Tarif Rejasi | Foydalanuvchi To‘lovi | O‘z ichiga olgan hajm | 1 daqiqa tushumi | 1 daqiqa tannarxi (COGS) | Sof Yalpi Foyda (1 daqiqa) | Yalpi Marja (Gross Margin) |
|---|:---:|:---:|:---:|:---:|:---:|:---:|
| **Creator** | 79,000 so‘m / oy | 30 daqiqa | 2,633 so‘m | 33.3 so‘m | **2,600 so‘m** | **98.7%** |
| **Pro Studio** | 199,000 so‘m / oy | 120 daqiqa | 1,658 so‘m | 33.3 so‘m | **1,625 so‘m** | **98.0%** |
| **Pay-as-you-go** | Paket asosida | 1 daqiqa | 1,500 so‘m | 33.3 so‘m | **1,467 so‘m** | **97.8%** |

---

## 4. Bitta GPU Serverning O‘tkazuvchanlik Imkoniyati (Capacity & Throughput)

- 1 ta Cloud GPU (NVIDIA T4 / L4) 1 kunda (24 soat = 86,400 soniya) nazariy jihatdan:
  $$\frac{86,400}{0.38} \approx 227,368\text{ soniya audio} \approx \mathbf{3,789\text{ daqiqa audio}}$$ ishlab chiqara oladi.
- 50% o‘rtacha yuklama (Peak traffic va bufer zaxirasi) hisobga olinganda:
  - 1 ta GPU kuniga: **~1,890 daqiqa audio**
  - 1 ta GPU oyiga: **~56,700 daqiqa audio**
- Bu bitta GPU serverining o‘zi taxminan:
  - **~1,890 ta Creator obunachiga** (har biri 30 daqiqadan), yoki
  - **~470 ta Pro Studio obunachiga** (har biri 120 daqiqadan) barqaror xizmat ko‘rsata olishini bildiradi!

---

## 5. Zararsizlik Nuqtasi (Break-Even Analysis)

- 1 ta doimiy Cloud GPU serverining oylik xarajati: **$250 (~3,162,500 so‘m)**.
- Ushbu server xarajatini qoplash uchun talab qilinadigan minimal mijozlar soni:
  - Faqat Creator tarifida (79,000 so‘m): $\frac{3,162,500}{79,000 - 1,000} \approx \mathbf{41\text{ nafar faol obunachi}}$.
  - Faqat Pro tarifida (199,000 so‘m): $\frac{3,162,500}{199,000 - 4,000} \approx \mathbf{17\text{ nafar faol obunachi}}$.
- 100 nafar Pro obunachi bo‘lganda:
  - Oylik tushum: 19,900,000 so‘m
  - Server va compute xarajati: ~3,570,000 so‘m
  - Oylik operatsion foyda: **+16,330,000 so‘m** (~$1,290 sof foyda).

---

## 6. Xulosa va Tavsiyalar

1. **Juda yuqori marjinallik (98%+):** VoiceClone AI modeli yuqori hisoblash samaradorligiga (RTF 0.38) ega bo‘lgani sababli, infratuzilma tannarxi past va biznes modeli o‘ta rentabelli.
2. **Real-vaqt monitoring:** Adminlar uchun yaratilgan `GET /api/v1/audit/analytics/economics/` API endpointi real-vaqtda generatsiya xarajatlarini kuzatib borish imkonini beradi.
3. **Phase 10 (Paid SaaS) ga tayyorgarlik:** `VC-100` (Quota va usage ledger) uchun har bir foydalanuvchining sarflagan soniya va daqiqalari ushbu model asosida hisoblanadi.
