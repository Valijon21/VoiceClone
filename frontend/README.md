# VoiceClone Frontend Web App

## 1. Vazifasi va Arxitekturadagi O‘rni
VoiceClone veb-mijozi foydalanuvchiga audio yozish, ovoz namunalarini yuklash, huquqiy rozilik bildirish (Consent Gate UI), matn kiritish, sintez jarayonini real vaqtda kuzatish va hosil bo‘lgan audioni tinglash/yuklab olish imkonini beruvchi zamonaviy SPA (Single Page Application) hisoblanadi.

## 2. Texnologik Stek
- **Framework:** React 19 / 18 + Vite + TypeScript
- **Styling:** Vanilla CSS / Tailwind CSS v4 dizayn tokenlari bilan
- **Holat boshqaruvi & API:** TanStack Query (React Query) + Axios / Fetch
- **Audio boshqaruvi:** Web Audio API (MediaRecorder, AudioContext)
- **Tillar:** O‘zbek (Lotin), Rus, Ingliz (i18n)

## 3. Asosiy Foydalanuvchi Oqimlari (User Flows)
1. **Ovoz profilini yaratish va Consent:**
   - Foydalanuvchi mikrofon orqali o‘z ovozini yozadi yoki WAV fayl yuklaydi.
   - Ekranda qat'iy rozilik matni chiqadi: "Men ushbu ovoz mening shaxsiy ovozim ekanini yoki undan foydalanishga to‘liq huquqim borligini tasdiqlayman."
   - Foydalanuvchi rozilik bergandan so‘nggina ovoz profili faollashadi.
2. **Audio Sintezi:**
   - Til tanlash (O‘zbek lotin, Ingliz, Rus - experimental).
   - Matn kiritish (maksimal 5000 belgi, avtomatik bo‘laklarga ajratish ko‘rsatkichi bilan).
   - Generatsiya jarayoni (asinxron polling orqali progress bar ko‘rinadi).
3. **Audio Tinglash va Eksport:**
   - Waveform preview.
   - Natijaviy WAV faylni yuklab olish.
   - Ovoz profilini va audio tarixini to‘liq o‘chirish (Privacy right).
