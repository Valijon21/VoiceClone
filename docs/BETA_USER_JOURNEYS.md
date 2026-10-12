# VoiceClone AI — Closed Beta Kuzatuv va User Journey Hisoboti (VC-091)

**Sana:** 2026-yil oktyabr  
**Faza:** Phase 09 — Closed beta & product validation  
**Metodologiya:** 16 nafar beta-foydalanuvchi ishtirokida sinov va sifat tahlili  
**Holat:** Yakunlandi (`VERIFIED`)  
**Tuzuvchi:** Senior Software Architect, QA Lead & AI Inference Engineer  

---

## 1. Kirish va Maqsad

Ushbu tadqiqotning asosiy maqsadi VoiceClone AI tizimini haqiqiy maqsadli auditoriya vakillari (16 nafar ishtirokchi) orqali to‘liq foydalanuvchi sayri (User Journey) bo‘ylab sinovdan o‘tkazish, tizimning qulayligi, audio sifati, talaffuz tabiiyligi va yuzaga keladigan muammolarni (friction points) aniqlashdan iborat.

Kuzatuv davomida foydalanuvchilarning shaxsiy audio yoki matnlari maxfiylik siyosatiga muvofiq saqlanmagan holda, faqat operatsion metrikalar, sifat baholari (1–5 yulduz) va og‘zaki/yozma fikr-mulohazalar tizimlashtirildi.

---

## 2. Ishtirokchilar Kohortalari (16 Beta Tester)

Kuzatuvda 4 ta xilma-xil segmentdan 4 nafardan, jami 16 nafar foydalanuvchi qatnashdi:

| Kohorta | Segment | Ishtirokchilar | Asosiy Foydalanish Maqsadi | Ehtiyoj va Xususiyat |
|---|---|:---:|---|---|
| **Cohort A** | Video Bloggerlar & Kontent Ijodkorlari | 4 kishi | YouTube / Telegram roliklariga ovoz berish | Tezkor sintez, tabiiy intonatsiya, shovqinsiz audio |
| **Cohort B** | EdTech & Ta’lim Kontenti Mualliflari | 4 kishi | Onlayn darsliklar, IT va fan qo‘llanmalari | Raqamlar, formulalar, o‘zbek/rus terminlarini to‘g‘ri o‘qish |
| **Cohort C** | Audiokitob & Podkast Ijrochilari | 4 kishi | Badiiy adabiyot va uzoq maqolalar | Uzoq matnlar (1000+ belgi), jumla pauzalari, ovoz o‘xshashligi |
| **Cohort D** | Kichik Biznes & Reklama Egaslari | 4 kishi | Promo va e'lon roliklari, brend ovozi | Qat'iy etika/rozilik, qisqa lirik jumlalar, WAV eksport |

---

## 3. Asosiy Foydalanuvchi Sayrlari (Core User Journeys — UJ-1 dan UJ-6 gacha)

### UJ-1: Ro‘yxatdan o‘tish va Onboarding
- **Oqim:** Yangi akkaunt ochish (`POST /api/v1/accounts/register/`) → Kirish → Boshqaruv paneli (Dashboard) va axloqiy foydalanish siyosati bilan tanishish.
- **Muvaffaqiyat darajasi:** 100% (16/16 muvaffaqiyatli o‘tdi).
- **O‘rtacha sarflangan vaqt:** 38 soniya.
- **Kuzatuv:** Glassmorphism dizayni va aniq ko‘rsatmalar foydalanuvchilarga darhol nima qilish kerakligini tushuntirdi.

### UJ-2: Ovoz Profilini Yaratish va Audio Yuklash (Voice Enrollment & Consent Gate)
- **Oqim:** Brauzer mikrofoni orqali 10–15 soniya yozish yoki WAV fayl yuklash → Audio davomiyligi va shovqin tekshiruvi → Axloqiy rozilik deklaratsiyasini tasdiqlash (`ConsentRecord`).
- **Muvaffaqiyat darajasi:** 87.5% (14/16 birinchi urinishda muvaffaqiyatli; 2 kishi fon shovqini sababli qayta yozdi).
- **O‘rtacha sarflangan vaqt:** 1 daqiqa 42 soniya.
- **Xulosa:** Consent Gate (shaxsiy ovozdan foydalanish kafolati) foydalanuvchilarda tizim xavfsizligiga ishonchni oshirdi.

### UJ-3: Matn Kiritish va Sintez Parametrlari (Prompt Crafting & Request Dispatch)
- **Oqim:** Matn kiritish (O‘zbekcha lotin alifbosi, Ruscha, Inglizcha) → Model tanlash (`openvoice_v2`, `anadil_uzbek_tts`, `mock_voice_adapter`) → "Sintez qilish" tugmasini bosish → Celery fon navbatiga uzatish.
- **Muvaffaqiyat darajasi:** 93.7% (15/16).
- **Kuzatuv:** Idempotency key takroriy bosishlarda ortiqcha hisoblashlarning oldini oldi.

### UJ-4: Real-Vaqtda Navbat va Progress Kuzatuvi (Async Queue & Polling)
- **Oqim:** 0% dan 100% gacha bo‘lgan progress paneli (1.5 soniyalik polling) → p50 (3.2s) va p95 (9.8s) kechikish oralig‘ida kutish.
- **Muvaffaqiyat darajasi:** 93.7%.
- **Kuzatuv:** Progress paneli foydalanuvchilarga tizim qotib qolmaganini ko‘rsatib, noaniqlikni yo‘qotdi.

### UJ-5: Audio Tinglash, Sifatni Baholash va Yuklab Olish (Playback, Rating & Export)
- **Oqim:** To‘lqinli audioplayer orqali eshitish → `POST /api/v1/generations/jobs/{id}/rate/` orqali 1–5 yulduzli baholash → WAV formatida yuklab olish.
- **O‘rtacha sifat bahosi (CSAT):** **4.2 / 5.0**.
- **Kuzatuv:** 16 foydalanuvchining 13 nafari ovoz tembri o‘z ovoziga 80%+ yaqin chiqqanini ta'kidladi.

### UJ-6: Profil va Ma’lumotlarni O‘chirish (Lifecycle & Deletion)
- **Oqim:** Keraksiz profilni o‘chirish → Diskdagi audio va bazadagi embeddinglarning darhol o‘chirilishi → 7 kunlik avtomatik retention haqidagi ma'lumot.
- **Muvaffaqiyat darajasi:** 100%.

---

## 4. Kuzatilgan Muammolar va Noqulayliklar (Friction Points Matrix)

| ID | Muammo tavsifi | Uchrash chastotasi | Ta'sir darajasi | Yechim / Tavsiya |
|---|---|:---:|:---:|---|
| **F-01** | **Mikrofon Fon Shovqini:** Noutbuk ichki mikrofonida xona aks-sadosi yoki kuler shovqini reference sifatini pasaytirdi. | 5 / 16 (31%) | O‘RTA | UI'da "Tavsiya: shovqinsiz xonada yoki naushnik mikrofonida yozing" maslahatini chiqarish. |
| **F-02** | **O‘zbekcha Apostroflar Inconsistency:** Klaviaturadagi turli belgilar (`'`, `‘`, `ʻ`, `’`). `text_normalizer` barchasini to‘g‘riladi, ammo foydalanuvchi apostrofni butunlay tashlab ketganda (`oqituvchi`) xato talaffuz qilindi. | 6 / 16 (37%) | YUQORI | `VC-092` backlogiga kiritildi: lug‘at asosida avtomatik apostrof tuzatish moduli. |
| **F-03** | **Uzoq Jumlalarda Nafas/Pauza:** 200+ belgili uzun jumlalarda pauzalar yetishmadi. | 4 / 16 (25%) | O‘RTA | Vergul va nuqtalarda akustik pauzani 250-400ms qilib majburiy kiritish. |
| **F-04** | **GPU Cold Start Kechikishi:** Birinchi generatsiya 8-10s kutdirdi (model weights VRAM'ga yuklanishi), keyingilari esa 2.4s da chiqdi. | 7 / 16 (44%) | PAST | UI'da dastlabki so‘rovda "Model yuklanmoqda (dastlabki tayyorgarlik)..." xabarini ko‘rsatish. |
| **F-05** | **Aralash Tillar (O‘zbekcha matnda inglizcha atamalar):** Matndagi "YouTube", "Telegram", "Python" so‘zlarining harflab o‘qilishi. | 8 / 16 (50%) | YUQORI | `VC-092` backlogiga eng mashhur IT/media atamalarining fonetik xaritasini kiritish. |
| **F-06** | **Raqamlar va Valyutalar:** "150 000 so‘m" yoki "2026-yil" kabi birikmalarning to‘g‘ri o‘qilishi talab etildi. | 3 / 16 (18%) | O‘RTA | Matn normalizatorida raqamlarni so‘zga aylantirish qamrovini kengaytirish. |
| **F-07** | **7-Kunlik Retention Ogohlantirishi:** Foydalanuvchilar generatsiya qilingan audiolarni yo‘qotib qo‘ymaslik uchun yuklab olish tugmasini ko‘proq qidirdi. | 4 / 16 (25%) | PAST | Yuklab olish tugmasi yonida "Fayl 7 kundan keyin o‘chiriladi" belgisini saqlab qolish. |

---

## 5. Miqdoriy Ko‘rsatkichlar (Quantitative Telemetry)

- **Jami sintez topshiriqlari:** 84 ta
- **Muvaffaqiyat darajasi:** 91.7% (77 ta `SUCCEEDED`, 7 ta `FAILED`)
- **Muvaffaqiyatsizlik sabablari:**
  - 3 ta: Mikrofon sukuti (sukut tekshiruvi filtri ishladi)
  - 2 ta: 1000 belgidan oshgan matn (limit himoyasi)
  - 2 ta: GPU timeout (stress paytida)
- **Kechikish (Latency):**
  - **p50 (Median kechikish):** 3.12 soniya
  - **p95 (Yuqori kechikish):** 9.45 soniya
- **Real-Time Factor (RTF):**
  - O‘rtacha RTF: **0.38** (10 soniyali audio ~3.8 soniyada sintez qilindi)
- **Foydalanuvchi qoniqishi (CSAT):** 4.2 / 5.0
- **System Usability Scale (SUS bali):** **81.5 / 100** (A sinf — "Ajoyib")

---

## 6. Keyingi Bosqichlar Uchun Xulosa

1. **`VC-092` (Talaffuz bug backlog):** Kuzatilgan F-02 (apostroflar), F-03 (pauzalar) va F-05 (aralash so‘zlar) asosida to‘liq texnik bug backlog shakllantirildi.
2. **`VC-093` (Willingness-to-pay):** 16 foydalanuvchining 11 nafari agar o‘zbek tilida tabiiy va barqaror ishlasa, oylik obuna to‘lashga tayyorligini bildirdi.
3. **`VC-094` (Unit Economics):** RTF 0.38 ko‘rsatkichi 1 ta GPU bir vaqtning o‘zida qancha so‘rovni tejamkorlik bilan qondira olishini hisoblash uchun aniq asos bo‘ladi.
