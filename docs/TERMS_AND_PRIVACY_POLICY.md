# VoiceClone AI — Ommaviy Oferta, Maxfiylik Siyosati va Narxlar (VC-103)

**Hujjat turi:** Ommaviy foydalanish shartlari, Maxfiylik siyosati, Ma'lumotlarni o'chirish va To'lov nizomlari  
**Tegishli Task:** `VC-103` — Public pricing, terms, privacy policy va deletion policy  
**Holat:** `COMPLETED` / `ACTIVE`  

---

## 1. Ommaviy Tariflar va Xizmat Rejalari (Public Pricing & Quota Table)

VoiceClone AI platformasi shaffof va oylik kvotaga asoslangan obuna tizimida faoliyat yuritadi. Har bir foydalanuvchi hisobida generatsiya qilingan har bir soniya nutq immutable (o'zgartirib bo'lmas) `UsageLedger` orqali hisoblab boriladi.

| Tarif nomi | Oylik to'lov | Yillik to'lov (17% chegirma) | Oylik kvota | Imkoniyatlar va Funksiyalar | Qo'llab-quvvatlash |
|---|:---:|:---:|:---:|---|:---:|
| **Free Trial** | **0 so'm** | **0 so'm** | 300 soniya (5 daqiqa) | Sinov rejimi, 1 ta ovoz profili, OpenVoice V2 tayanchi, 7 kunlik retention | Jamiyat / FAQ |
| **Creator** | **79,000 so'm/oy** | **790,000 so'm/yil** | 1,800 soniya (30 daqiqa) | 5 ta ovoz profili, WAV studio yuklab olish, yuqori sifatli intonatsiya, tezkor navbat | Standart (24h) |
| **Pro Studio** | **199,000 so'm/oy** | **1,990,000 so'm/yil** | 7,200 soniya (120 daqiqa) | Cheksiz ovoz profili, ustuvor navbat (Priority Queue), API foydalanish huquqi | VIP / Ustuvor (4h) |
| **Enterprise / VIP** | Shartnoma asosida | Shartnoma asosida | Maxsus / Cheksiz | Maxsus model finetuning, SLA 99.9%, cheksiz generatsiya, ajratilgan worker | Shaxsiy menejer |

*Izoh: Owner, superuser va ma'murlar uchun tizimda doimiy cheksiz `is_unlimited=True` imtiyozi o'rnatilgan bo'lib, ular barcha kvota tekshiruvlarini bevosita aylanib o'tadi.*

---

## 2. Foydalanish Shartlari va Ommaviy Oferta (Terms of Service)

Ushbu shartlar VoiceClone AI platformasidan foydalanish bo'yicha foydalanuvchi va xizmat ko'rsatuvchi o'rtasidagi yuridik kelishuv hisoblanadi.

### 2.1. Axloqiy Ovoz Xavfsizligi va Consent Gate
1. **Shaxsiy Rozilik Majburiyati:** Foydalanuvchi platformaga faqat o'zining ovoz yozuvini yoki ovoz egasining qonuniy, hujjatlashtirilgan yozma roziligi mavjud bo'lgan audio faylni yuklash huquqiga ega.
2. **Qat'iy Man Etilgan Harakatlar:**
   - Shaxsni aldash, firibgarlik (deepfake scam), biometrik autentifikatsiyani buzib o'tish yoki obro'sizlantirish maqsadida ovoz klonlash;
   - Siyosatchilar, jamoat arboblari yoki uchinchi shaxslarning ruxsatisiz ularning nomidan yolg'on xabarlar tarqatish;
   - Har qanday noqonuniy, tajovuzkor yoki ekstremistik audio materiallar ishlab chiqarish.
3. **Audit va Bloklash:** Tizim har bir ovoz profili uchun `ConsentRecord` va `AuditEvent` yuritadi. Shikoyat (`AbuseReport`) kelib tushganda yoki xavfsizlik filtri buzilganda profil va hisob ogohlantirishsiz darhol bloklanadi.

### 2.2. Audio Ma'lumotlarning Intellektual Mulki
- Foydalanuvchi tomonidan kiritilgan asl ovoz namunalari va platforma orqali sintez qilingan barcha yakuniy audio fayllarga bo'lgan mualliflik huquqi to'liq **foydalanuvchiga tegishli**.
- VoiceClone AI foydalanuvchining shaxsiy ovoz namunalarini ommaga oshkor qilmaydi va ruxsatsiz uchinchi tomonlarga sotmaydi.

---

## 3. Maxfiylik Siyosati (Privacy Policy)

VoiceClone AI O'zbekiston Respublikasining "Shaxsga doir ma'lumotlar to'g'risida"gi Qonuni va xalqaro GDPR standartlariga qat'iy rioya qiladi.

1. **To'planadigan Ma'lumotlar:**
   - Hisob ma'lumotlari: Elektron pochta, foydalanuvchi nomi, shifrlangan parol xeshi (Argon2 / PBKDF2);
   - Audio ma'lumotlar: Ovoz profili yaratish uchun yuklangan WAV/MP3 mos yozuv audiolari;
   - Operatsion telemetriya: So'rov identifikatori (`X-Request-ID`), IP manzili, foydalanilgan model va generatsiya davomiyligi (shaxsiy matn va audio mazmuni xavfsizlik maqsadida telemetriyaga qo'shilmaydi).
2. **Ma'lumotlar Izolyatsiyasi:**
   - Foydalanuvchilar faqat o'zlariga tegishli ovoz profillari va audio arxivlariga kirish huquqiga ega (`IsOwner` ruxsati);
   - Boshqa foydalanuvchilarning audio fayllarini taxminiy URL orqali ko'rish texnik jihatdan bloklangan.

---

## 4. Ma'lumotlarni Saqlash va O'chirish Siyosati (Data Retention & Deletion Policy)

### 4.1. 7 Kunlik Avtomatik Retention Siyosati
* Generatsiya qilingan barcha oraliq va natijaviy audio fayllar (`GeneratedAudio`) serverda yaratilgan vaqtdan boshlab **7 kun** davomida saqlanadi.
* 7 kundan keyin Celery avtomatik tozalash vazifasi (`cleanup_expired_audio_assets`) fayllarni diskdan va ma'lumotlar bazasidan xavfsiz va qayta tiklab bo'lmaydigan qilib o'chiradi.
* Foydalanuvchilarga kerakli audio fayllarni 7 kunlik muddat tugashidan oldin o'z kompyuterlariga yuklab olish tavsiya etiladi.

### 4.2. Foydalanuvchi Talabi Bilan Tezkor O'chirish (Right to Erasure)
* Foydalanuvchi istalgan vaqtda veb-interfeys orqali o'z ovoz profilini yoki alohida audio yozuvlarini o'chirish tugmasini bosishi mumkin.
* Profil o'chirilganda unga bog'langan barcha audio fayllar va o'rganilgan akustik embeddinglar zudlik bilan yo'q qilinadi.

---

## 5. To'lovlar, Obunani Bekor Qilish va Pulni Qaytarish (Billing & Refund Policy)

### 5.1. To'lov Shlyuzlari
- To'lovlar O'zbekiston milliy to'lov tizimlari — **Payme** (JSON-RPC 2.0) va **Click** (Shop API) orqali rasmiy merchant shartnomasi asosida UZS (so'm) valyutasida qabul qilinadi.
- Karta ma'lumotlari platforma serverlarida saqlanmaydi; barcha tranzaksiyalar PCI-DSS xavfsizlik sertifikatiga ega to'lov operatorlari tomonidan amalga oshiriladi.

### 5.2. 3 Kunlik Imtiyozli Davr (Grace Period)
- Agar navbatdagi obuna to'lovida kartada mablag' yetarli bo'lmasa, hisob darhol to'xtatilmaydi.
- Foydalanuvchiga to'lov kartasini to'ldirish uchun **3 kunlik imtiyozli davr** beriladi.
- Ushbu davrda foydalanuvchining mavjud kvotasi daxlsiz saqlanadi ("to'lov xatolari mavjud kvotani buzmaydi").

### 5.3. Pulni Qaytarish (Refund Policy)
- Foydalanuvchi xizmatdan qoniqmagan taqdirda, obuna to'langan kundan boshlab **72 soat ichida** mijozlarni qo'llab-quvvatlash xizmatiga murojaat qilib to'liq yoki qisman refund talab qilishi mumkin.
- Agar olingan kvotaning 20% dan ortig'i sarflanmagan bo'lsa, to'lov to'liq qaytariladi.
- Refund amalga oshirilganda, o'tkazilgan kvota `UsageLedger` orqali audit qilinib, hisob bekor qilinadi.

---

## 6. Aloqa va Mijozlarni Qo'llab-quvvatlash
- **Qo'llab-quvvatlash xizmati:** support@voiceclone.uz  
- **Xavfsizlik va suiiste'mollik (Abuse):** abuse@voiceclone.uz  
- **Ish vaqti:** Dushanba – Juma, 09:00 – 18:00 (Toshkent vaqti bilan)
