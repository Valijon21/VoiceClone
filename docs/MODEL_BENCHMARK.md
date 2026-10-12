# Model Benchmark & Evaluation Plan — Voice Clone AI

**Hujjat kodi:** `docs/MODEL_BENCHMARK.md`  
**Task ID:** `VC-010`, `VC-015`, `VC-016`  
**Sana:** 2026-10-11  
**Apparat:** Windows 11, NVIDIA GeForce RTX 3060 (6 GB VRAM), CUDA 13.0  

---

## 1. Maqsad va Sinov Shartlari

Ushbu benchmark rejasi quyidagi savollarga javob berish uchun xizmat qiladi:
1. Qaysi model o‘zbek tilida tabiiy va tushunarli ovoz chiqara oladi?
2. 6 GB VRAM chegarasida qaysi model barqaror ishlaydi (OOM xatolarisiz)?
3. Har bir modelning Real-Time Factor (RTF) va xotira sarfi qanday?
4. Qaysi model tijoratda foydalanishga to‘liq qonuniy ruxsatga ega?

---

## 2. O‘lchanadigan Metrikalar

### Texnik Metrikalar:
- **RTF (Real-Time Factor):** $\text{RTF} = \frac{\text{Sintez vaqti (soniya)}}{\text{Yaratilgan audio davomiyligi (soniya)}}$. RTF < 1.0 bo‘lsa, sintez real vaqtdan tezroq.
- **Cold Start Latency:** Model birinchi marta xotiraga (VRAM) yuklanish vaqti (soniyalarda).
- **Peak VRAM (MB):** Model ishlash vaqtida maksimal band qilgan video xotira (6144 MB gacha).
- **Peak RAM (MB):** Tizim asosiy xotirasi (RAM) sarfi.
- **Failures / OOM Count:** 30 ta uzluksiz sinovda yuzaga kelgan xatoliklar soni.

### Sifat Metrikalari (Insoniy Baholash, 1–5 ball):
1. **Talaffuz va Fonetika (1–5):** Apostroflar (`o‘`, `g‘`), harflar chalkashmasligi, to‘g‘ri bo‘g‘inlash.
2. **Tabiiylik va Intonatsiya (1–5):** Robot ohangi yo‘qligi, tinish belgilarida to‘g‘ri to‘xtash.
3. **Tembr O‘xshashligi (Speaker Similarity, 1–5):** Asl namuna ovozga qanchalik o‘xshashligi.
4. **Tushunarlilik (Intelligibility, 1–5):** Shovqinsiz, xiralanmagan, aniq eshitilish.

---

## 3. Sinov Matnlari Korpusi (Benchmark Corpus — 25 ta har bir tilda)

### A. O‘zbek tili (Lotin alifbosi — Asosiy e’tibor)

| ID | Toifa | Matn | Huquqiy manba |
|---|---|---|---|
| `UZ-01` | Qisqa salom | Assalomu alaykum, Voice Clone tizimiga xush kelibsiz! | Public Domain / Muallif |
| `UZ-02` | `o‘` va `g‘` harflari | O‘zbekiston tog‘lari va go‘zal bog‘larida bahor nafasi sezilmoqda. | Public Domain |
| `UZ-03` | Tutuq belgisi | Ma’naviyat va ma’rifat inson qalbini yuksaltiruvchi buyuk ne’matdir. | Public Domain |
| `UZ-04` | `sh`, `ch`, `ng` | Shahrimiz ko‘chalarida tong paytida qushlarning yoqimli sayrashi eshitiladi. | Public Domain |
| `UZ-05` | Raqam va sana | Bugun 2026-yil 11-oktabr, havo harorati 18 daraja iliq bo‘lishi kutilmoqda. | Public Domain |
| `UZ-06` | Valyuta va hisob-kitob | Umumiy summa 450 000 so‘m bo‘lib, to‘lov muvaffaqiyatli qabul qilindi. | Public Domain |
| `UZ-07` | Ismlar | Shohruh, Nodira, Abdulla va G‘ayrat bugungi uchrashuvga yetib kelishdi. | Public Domain |
| `UZ-08` | Savol ohangi | Ertaga soat to‘qqizda bo‘lib o‘tadigan anjumanga siz ham borasizmi? | Public Domain |
| `UZ-09` | Hayrat / Undov | Qoyil! Bu ovoz xuddi haqiqiy insonga o‘xshab jaranglayapti-ku! | Public Domain |
| `UZ-10` | Texnik atamalar | Sun’iy intellekt modeli neyron tarmoqlar orqali ovoz to‘lqinlarini sintez qiladi. | Public Domain |
| `UZ-11` | O‘rta matn | Ta’lim tizimida raqamli texnologiyalardan foydalanish yoshlarning bilim olish tezligini sezilarli darajada oshiradi. | Public Domain |
| `UZ-12` | Uzun murakkab matn | Mustaqillik yillarida yurtimizda amalga oshirilgan keng ko‘lamli islohotlar xalqimiz farovonligini ta’minlash va iqtisodiy barqarorlikni mustahkamlashga xizmat qilmoqda. | Public Domain |
| `UZ-13` | Shovqinga sezgirlik | Past tovushda, xotirjam va sokin tarzda aytilgan jumlalarning ifodasi. | Public Domain |
| `UZ-14` | Fonetik qiyin so‘zlar | G‘ildirak, po‘lat, qoramtir, g‘o‘zapoya, e’tibor, qorong‘ulik. | Public Domain |
| `UZ-15` | Tez aytish | Oq choynakka oq qopqoq, ko‘k choynakka ko‘k qopqoq. | Folklor / Public Domain |
| `UZ-16` | Foiz va o‘lchovlar | Korxona samaradorligi 12.5 foizga oshdi, hajm esa 350 litrga yetdi. | Public Domain |
| `UZ-17` | So‘zlashuv uslubi | Xo‘sh, bu ishni qanday hal qilamiz? Hamma narsa tayyormi o‘zi? | Public Domain |
| `UZ-18` | Rasmiy axborot | Hurmatli yo‘lovchilar, Toshkent-Samarqand tezyurar poyezdi 2-yo‘lga yaqinlashmoqda. | Public Domain |
| `UZ-19` | Dialog namunasi | — Kechirasiz, kutubxona qayerda joylashgan? — To‘g‘riga yuring, o‘ng tomonda. | Public Domain |
| `UZ-20` | Qisqartmalar (Abbreviatura) | O‘zbekiston Respublikasi OAV va IT sohasida yangi loyihalarni qo‘llab-quvvatlaydi. | Public Domain |
| `UZ-21` | Vaqt birligi | Soat 14:45 da tanaffus tugaydi va darslar qayta boshlanadi. | Public Domain |
| `UZ-22` | Adabiy parcha | Bahor kelishi bilan qirlarda lolalar ochilib, zamin yashil libosga burkandi. | Public Domain |
| `UZ-23` | Emotsional matn (Xursandchilik) | Tabriklaymiz! Sizning loyihangiz eng yaxshi innovatsion g‘oya deb topildi! | Public Domain |
| `UZ-24` | Emotsional matn (Jiddiylik) | Diqqat qiling, xavfsizlik qoidalariga qat’iy rioya etish har birimizning burchimizdir. | Public Domain |
| `UZ-25` | Yakuniy tasdiq | Sinov muvaffaqiyatli yakunlandi. Barcha parametrlar me’yorida ishlamoqda. | Public Domain |

### B. Rus tili (Русский язык)

| ID | Toifa | Matn | Huquqiy manba |
|---|---|---|---|
| `RU-01` | Приветствие | Здравствуйте! Добро пожаловать в систему синтеза речи Voice Clone. | Public Domain |
| `RU-02` | Числа и даты | Сегодня 11 октября 2026 года, температура воздуха составляет плюс 18 градусов. | Public Domain |
| `RU-03` | Имена и фамилии | Александр Сергеевич и Екатерина Ивановна подтвердили участие в конференции. | Public Domain |
| `RU-04` | Сложная фонетика | В недрах тундры выдры в гетрах тырят в вёдра ядра кедров. | Скороговорка / PD |
| `RU-05` | Вопросительная интонация | Скажите, пожалуйста, удалось ли вам завершить тестирование всех модулей вовремя? | Public Domain |
| `RU-06` | Восклицание | Потрясающе! Сгенерированный голос звучит невероятно естественно и чисто! | Public Domain |
| `RU-07` | Официальное объявление | Уважаемые пассажиры, посадка на рейс номер 405 заканчивается через десять минут. | Public Domain |
| `RU-08` | Технический текст | Искусственный интеллект и нейронные сети преобразуют текст в аудиоволны. | Public Domain |
| `RU-09` | Длинное предложение | Разработка современных систем требует внимательного отношения к архитектуре, безопасности данных и оптимизации ресурсов. | Public Domain |
| `RU-10` | Диалог | — Простите, где находится конференц-зал? — Пройдите прямо по коридору до конца. | Public Domain |

### C. Ingliz tili (English)

| ID | Category | Text | Source |
|---|---|---|---|
| `EN-01` | Greeting | Hello! Welcome to the Voice Clone AI speech synthesis platform. | Public Domain |
| `EN-02` | Numbers & Dates | Today is October 11th, 2026, and the system is operating at 99.8% uptime. | Public Domain |
| `EN-03` | Tongue Twister | She sells seashells by the seashore, and the shells she sells are seashells. | Public Domain |
| `EN-04` | Question | Could you please verify whether the consent verification passed on the server? | Public Domain |
| `EN-05` | Exclamation | Incredible! The synthetic audio matches the original speaker profile seamlessly! | Public Domain |
| `EN-06` | Technical | Voice cloning involves zero-shot speaker adaptation using acoustic prompt embeddings. | Public Domain |
| `EN-07` | Long sentence | Modern software architecture demands modular decoupling between business workflows and hardware-accelerated inference tasks. | Public Domain |
| `EN-08` | Currency & Measurement | The transaction of 250 dollars and 50 cents was processed in approximately 45 milliseconds. | Public Domain |
| `EN-09` | Proper Names | Dr. Christopher Jenkins and Katherine O'Connor presented their findings at the summit. | Public Domain |
| `EN-10` | System Status | Verification completed successfully. All automated checks returned green status. | Public Domain |

---

## 4. Nomzod Modellar va Baholash Rejasi

| Nomzod Model | Tavsif | Rasmiy Manba | Litsenziya Holati | Taxminiy VRAM | Reja |
|---|---|---|---|---|---|
| **Anadil Uzbek TTS** | O‘zbek tili uchun moslashtirilgan TTS | Hugging Face: `Anadilorg/Anadil_Uzbek_TTS` | MIT (Model Card) | ~2–3 GB | 1-ustuvorlik (O‘zbek tili benchmark) |
| **OpenVoice V2** | MeloTTS bazasi + Tone Converter (Zero-shot) | GitHub: `myshell-ai/OpenVoice` | MIT (Repo) | ~3–4 GB | 1-ustuvorlik (Voice cloning & English) |
| **XTTS-v2** | 17 tilda ko‘p tilli sintez | Coqui AI GitHub / HF | Coqui Public Model License (CPML - Non-commercial/Restrictions) | ~4–5 GB | Faqat texnik taqqoslash (Tijoratga olinmaydi) |
| **F5-TTS** | Diffusion-based TTS | GitHub: `SWivid/F5-TTS` | Code: MIT, Weights: CC-BY-NC | ~4–6 GB | Tijoriy cheklov mavjud, zaxira |

---

## 5. Sinov Metodologiyasi va Protokoli

1. **Izolyatsiya:** Sinov faqat alohida virtual muhitda (`venv`) o‘tkaziladi.
2. **Xavfsiz Ovoz Namunasi:** Foydalanuvchining o‘zi yozib bergan 10–15 soniyalik WAV audio fayl (`16kHz` yoki `22.05kHz`, mono, 16-bit PCM). Begona yoki noqonuniy audio olinmaydi.
3. **Avtomatlashtirilgan o‘lchash:** Python skripti orqali har bir audio sintez uchun `time.perf_counter()` va `torch.cuda.max_memory_allocated()` qayd etiladi.
4. **Stress test:** 30 ta uzluksiz jumla ketma-ket yuboriladi; xotira tozalanishi (`torch.cuda.empty_cache()`) tekshiriladi.
