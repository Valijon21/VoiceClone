# O‘zbek Tili Talaffuz Xatoliklari Texnik Backlog’i (VC-092)

**Loyiha:** VoiceClone AI  
**Bosqich:** Phase 09 — Closed beta & product validation  
**Manba:** 16 nafar beta-foydalanuvchi sinovi, 84 ta sintez topshirig‘i va fonetik audit  
**Holat:** Ustuvorlashtirilgan (`P0`, `P1`, `P2`)  
**Mas'ul:** Senior Software Architect & AI Inference Engineer  

---

## 1. Umumiy Ko‘rinish va Mezonlar

O‘zbek tili lotin alifbosi asosidagi TTS (matnni nutqqa aylantirish) tizimlarida eng katta sifat yo‘qotishlari odatda akustik modeldan emas, balki **fonetik matn normalizatsiyasidagi kamchiliklar** tufayli yuzaga keladi.

Xatolar jiddiyligi bo‘yicha 3 darajaga ajratildi:
- **P0 (Kritik / Halokatli):** So‘z ma'nosi butunlay o‘zgaradi yoki eshituvchi uchun g‘aliz, tushunarsiz robot ovozi paydo bo‘ladi.
- **P1 (Yuqori ustuvorlik):** Raqamlar, yillar, foizlar, valyutalar yoki ommabop chet so‘zlarining nofonetik o‘qilishi.
- **P2 (O‘rta ustuvorlik):** Qisqartmalar, punktuatsion akustik pauzalar va ritmik urg‘ular.

---

## 2. P0 — Kritik Talaffuz Xatolari (Urgent / Critical)

| ID | Xato nomi | Kiruvchi matn (Input) | Hozirgi noto‘g‘ri chiqish | To‘g‘ri fonetik shakl (Expected) | Yechim algoritmi |
|---|---|---|---|---|---|
| **P0-1** | **Apostrofsiz `o'` / `g'`** | `ozbekiston`, `oqituvchi`, `togda` | [oz-bekiston], [o-qi-tuv-chi], [tog-da] | `o‘zbekiston`, `o‘qituvchi`, `tog‘da` | Lug‘atli avto-tuzatish xaritasi (`COMMON_MISSING_APOSTROPHE_MAP`) |
| **P0-2** | **Apostrofsiz tutuq belgisi** | `malumot`, `talim`, `etibor`, `sanat` | [ma-lu-mot], [ta-lim], [e-ti-bor] | `ma'lumot`, `ta'lim`, `e'tibor`, `san'at` | Bo‘g‘in ajratish tutuq belgisi xaritasi |
| **P0-3** | **Apostrof belgisi xilma-xilligi** | `o`zbek`, `o’zbek`, `oʻzbek`, `o´zbek` | Ba'zi modellarda harf tushib qoladi | `o‘zbek` (yagona standart) | Unicode regex orqali `o‘` va `g‘` ga birlashtirish |
| **P0-4** | **`ng` tovushining ikkilanishi** | `ko‘ngil`, `dengiz`, `menga` | Ba'zan [n-g] alohida harf sifatida o‘qiladi | Yagona burun tovushi [ŋ] | Akustik model fonema jadvalida `ng` digrafini belgilash |

---

## 3. P1 — Raqamlar, Yillar, Valyutalar va Atamalar (High Priority)

| ID | Xato nomi | Kiruvchi matn (Input) | Hozirgi noto‘g‘ri chiqish | To‘g‘ri fonetik shakl (Expected) | Yechim algoritmi |
|---|---|---|---|---|---|
| **P1-1** | **Yillar va tartib sonlar** | `2026-yil`, `1-o‘rin`, `5-sinf` | "ikki ming yigirma olti tire yil" | `ikki ming yigirma oltinchi yil`, `birinchi o‘rin`, `beshinchi sinf` | Tartib qo‘shimchasi regex qoidasi (`(\d+)-(yil|o‘rin|sinf|dars)`) |
| **P1-2** | **Foiz belgilari (%)** | `50%`, `99.9%` | "ellik foiz belgisi" yoki o‘qilmaydi | `ellik foiz`, `to‘qson to‘qqiz butun o‘ndan to‘qqiz foiz` | `(\d+)%` -> `... foiz` o‘zgartiruvchisi |
| **P1-3** | **Oraliq bo‘shliqli katta sonlar** | `150 000 so‘m`, `1 000 000` | "bir yuz ellik, nol nol nol" | `bir yuz ellik ming so‘m`, `bir million` | Bo‘shliqli sonlarni yagona raqam sifatida birlashtirish |
| **P1-4** | **Mashhur IT/Media atamalari** | `YouTube`, `Python`, `Google`, `AI` | [you-tu-be], [pyt-hon], [goo-gle] | `yutub`, `payton`, `gugl`, `ey ay` | Ommabop so‘zlar fonetik lug‘ati (`LOANWORD_PHONETICS`) |
| **P1-5** | **Valyuta qisqartmalari** | `$100`, `50 evro`, `200 USD` | "dollar yuz" | `yuz dollar`, `ellik yevro`, `ikki yuz AQSH dollari` | Valyuta belgisini so‘z oxiriga o‘tkazib o‘qish |

---

## 4. P2 — Qisqartmalar va Akustik Pauzalar (Medium Priority)

| ID | Xato nomi | Kiruvchi matn (Input) | Hozirgi noto‘g‘ri chiqish | To‘g‘ri fonetik shakl (Expected) | Yechim algoritmi |
|---|---|---|---|---|---|
| **P2-1** | **Standart qisqartmalar** | `va h.k.`, `va boshq.`, `mas.` | "va h k nuqta" | `va hokazo`, `va boshqalar`, `masalan` | Qisqartmalarni to‘liq so‘zga almashtirish lug‘ati |
| **P2-2** | **Katta harfli abbreviaturalar** | `AQSH`, `BMT`, `OAV`, `DXX` | [aqsh], [bmt] sifatida qo‘shib o‘qiladi | `A Q Sh`, `B M T`, `O A V`, `D X X` | Harflar orasiga bo‘shliq kiritish |
| **P2-3** | **Vergul va ikki nuqta pauzasi** | `Salom, do‘stlar!` | 0ms pauza (bir nafasda ketadi) | ~250ms tabiiy akustik pauza | Sintetik WAV bo‘laklarida yoki SSML taglarda pauza inyeksiyasi |
| **P2-4** | **Tire va defis farqi** | `Toshkent - Samarqand poyezdi` | "tire" deb o‘qilishi mumkin | ~300ms pauza bilan o‘qish | ` - ` belgilarini akustik pauzaga almashtirish |

---

## 5. Implementatsiya Rejasi va Texnik Integratsiya

1. **Bosqich 1 (Bugungi yechim - `text_normalizer.py` yangilanishi):**
   - `COMMON_MISSING_APOSTROPHE_MAP`: 50+ eng ko‘p uchraydigan so‘zlarni avtomatik tuzatish.
   - Tartib sonlar qoidasi: `\b(\d+)-(yil|sinf|o‘rin|qavat|dars|bob|modda)\b` -> `...-inchi ...`.
   - Foizlar va qisqartmalar: `%` -> `foiz`, `va h.k.` -> `va hokazo`.
   - Ommabop atamalar xaritasi: `YouTube`, `Python`, `Telegram`, `Google`, `AI`.
2. **Bosqich 2 (Keyingi model fine-tuning va fonemik lug‘at):**
   - O‘zbek tili uchun 50,000 so‘zlik G2P (Grapheme-to-Phoneme) leksikonini yaratish.
   - `ng` tovushi va urg‘u belgilari bo‘yicha akustik model adapterini kalibratsiyalash.
