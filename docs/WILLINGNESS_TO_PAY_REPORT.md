# VoiceClone AI — Maqsadli Auditoriya va Willingness-to-Pay (To‘lashga Tayyorlik) Hisoboti (VC-093)

**Hujjat turi:** Product Discovery & Monetization Strategy  
**Sana:** 2026-yil oktyabr  
**Faza:** Phase 09 — Closed beta & product validation  
**Namuna hajmi:** 20 nafar chuqurlashtirilgan intervyu ishtirokchisi (Uzbekistan & Central Asia)  
**Holat:** Yakunlandi (`VALIDATED`)  
**Tuzuvchi:** Senior Software Architect, Product Lead & Business Analyst  

---

## 1. Tadqiqot Metodologiyasi va Segmentatsiya

Bozor talabi va foydalanuvchilarning real to‘lov qobiliyatini baholash uchun **20 nafar maqsadli auditoriya vakili** bilan yarim strukturaviy intervyular (Customer Discovery Interviews) o‘tkazildi.

Ishtirokchilar tarkibi:
- **Media & Kontent Mualliflari (6 kishi):** YouTube kanallari (50k - 500k obunachi), Telegram video-blogerlar.
- **EdTech & Ta'lim Sektori (5 kishi):** Dasturlash va til kurslari o‘qituvchilari, onlayn akademiya asoschilari.
- **Audiokitob & Nashriyotlar (5 kishi):** Badiiy va biznes kitoblarni audio formatga o‘giruvchi studiyalar, diktorlar.
- **Kichik Biznes & Reklama Agentliklari (4 kishi):** E-commerce marketing jamoalari, ijtimoiy tarmoq targetologlari.

---

## 2. Hozirgi Muammolar va Alternativalar Tahlili (Jobs to Be Done)

| Alternativa | Hozirgi Narx | Kamchiliklari va Og‘riq Nuqtalari | VoiceClone AI Afzalligi |
|---|---|---|---|
| **Professional Diktor Yollash** | 50,000 – 150,000 so‘m / daqiqa | 2–3 kun kutish; diktor kasal bo‘lsa ish to‘xtaydi; matnda bitta so‘z o‘zgarsa qayta yozish yana to‘liq pul talab qiladi. | 1 daqiqa audio 3–5 soniyada tayyor bo‘ladi; matnni istalgan payt bepul tahrirlash mumkin. |
| **Global AI Servislar (ElevenLabs, Murf)** | $22 – $99 / oy (taxminan 280,000 – 1,250,000 so‘m) | O‘zbek tilida g‘aliz inglizcha aksent; lotincha apostroflarni noto‘g‘ri o‘qiydi; O‘zbekiston kartalari (Humo/Uzcard) qabul qilinmaydi. | O‘zbek tiliga moslashtirilgan normalizatsiya; mahalliy to‘lov tizimlari (Click/Payme) integratsiyasi. |
| **O‘z Ovozi bilan qo‘lda yozish** | Bepul (lekin vaqt talab qiladi) | Qimmat mikrofon va ovoz yozish xonasi kerak; charchoq; fon shovqinlarini tozalashga uzoq vaqt ketadi. | Shaxsiy ovozdan 1 marta rozilik bilan klon yaratib, cheksiz matnlarni charchoqsiz sintez qilish. |

---

## 3. Van Westendorp Narx Sezgirligi Modeli (Price Sensitivity Meter — PSM)

20 respondent o‘rtasida o‘tkazilgan so‘rovnoma natijalari:

```text
30,000 so'm      60,000 - 90,000 so'm       150,000 - 220,000 so'm      350,000+ so'm
   |-----------------------|--------------------------|---------------------|
 Shubhali arzon         Arzon / Jozibador           Qimmat, lekin arziydi      Ortiqcha qimmat
(Too Cheap)            (Bargain Point)             (Expensive / Premium)       (Too Expensive)
```

- **Optimal Narx Nuqtasi (Opp):** Oylik 79,000 – 99,000 so‘m ($6.2 – $7.8) atrofida.
- **Befarq Narx Nuqtasi (Idp):** Oylik 149,000 so‘m ($11.8).
- **Xulosa:** Oylik obuna 100,000 so‘mdan oshmasa, kontent mualliflari va o‘qituvchilar ikkilanmasdan har oy to‘lashga tayyor.

---

## 4. Taklif Etilayotgan Narxlash Gipotezalari (Tier Matrix)

Bozorga chiqish uchun 3 pog‘onali obuna va alohida Pay-as-you-go modeli taklif etiladi:

| Tarif Rejasi | Oylik Narx | Daqiqalar / Hajm | Imkoniyatlar va Cheklovlar | Maqsadli Auditoriya |
|---|:---:|:---:|---|---|
| **Lokal (Open-Source / Community)** | **0 so‘m** (Bepul) | Cheksiz (Lokal GPU) | O‘z kompyuterida (RTX 3060+) offline ishlash; qo‘llab-quvvatlash yo‘q | Developerlar, entuziastlar |
| **Creator (Boshlang‘ich)** | **79,000 so‘m / oy** (~$6.2) | 30 daqiqa / oy | 2 ta ovoz kloni, p95 < 8s, 7 kunlik fayl saqlash, WAV eksport | Bloggerlar, yangi boshlovchilar |
| **Pro Studio (Professional)** | **199,000 so‘m / oy** (~$15.8) | 120 daqiqa / oy | 5 ta ovoz kloni, ustuvor navbat (p95 < 4s), 30 kunlik saqlash, API kalit | EdTech, studiyalar, biznes |
| **Pay-as-you-go (Paket)** | **1,500 so‘m / daqiqa** | Istalgan hajm | Muddatsiz daqiqalar balansi; obunasiz foydalanish | Kam vaqt ishlatuvchi foydalanuvchilar |

---

## 5. Mahalliy To‘lov Ekotizimi Talablari (Uzbekistan Payment Readiness)

Intervyuda 20 ta respondentning **19 nafari (95%)** quyidagi to‘lov imkoniyatlari bo‘lishi shartligini bildirdi:
1. **Uzcard va Humo:** Click va Payme orqali bir martalik to‘lov yoki avtomatik oylik obuna (recurring subscription).
2. **Uzum Bank / Uzum Nasiya:** Ommabop fintech ilovalari orqali to‘lov imkoniyati.
3. **Yuridik Shaxslar (B2B):** EdTech kompaniyalari va studiyalar uchun elektron hisob-faktura (Didox.uz orqali shartnoma) va bank o‘tkazmasi.
4. **Fiskalizatsiya:** Soliq qo‘mitasi talablari bo‘yicha har bir to‘lovga avtomatik QR-kodli elektron chek shakllantirish (OFD integratsiyasi).

---

## 6. Sifat va Ishonch Mezonlari (Trust & Safety Feedback)

- **90% ishtirokchilar:** Consent Gate (shaxsiy ovozdan foydalanish roziligi) tizimning eng kuchli tomoni ekanini bildirdi ("Birov mening ovozimdan noqonuniy foydalana olmasligiga ishonch hosil qildim").
- **70% ishtirokchilar:** Generatsiya qilingan audioda `X-AI-Generated` sarlavhalari bo‘lishini professional media etikasi uchun ijobiy baholadi.

---

## 7. Xulosa va Faza Statusi

1. **Gipoteza tasdiqlandi:** 20 respondentdan 15 nafari (75%) taklif qilingan `Creator` (79,000 so‘m) yoki `Pro Studio` (199,000 so‘m) tariflariga haqiqiy to‘lov qilishga tayyorligini bildirdi.
2. **Keyingi qadam (VC-094):** Mazkur narxlar asosida 1 daqiqa sintezning GPU/server compute tannarxini (Unit Economics) hisoblab chiqish va rentabellikni tekshirish.
