# Workflow 01 — Discovery va model benchmark

## Maqsad
Kod bazasini katta hajmda yaratishdan oldin kompyuter imkoniyatlarini, model mosligini, til sifatini va litsenziyani tekshirish.

## Agent prompti
Sen senior AI/audio engineer va software architect sifatida ishlaysan. Avval `AGENTS.md`, `docs/SYSTEM_DESIGN.md`, `tasks/ROADMAP.md` va `MODEL_LICENSES.md` fayllarini o‘qi.

1. Ish muhiti OS, Python, RAM, GPU, VRAM va disk bo‘yicha mavjud ma’lumotni aniqlashga harakat qil. Aniqlab bo‘lmasa, taxmin qilma; foydalanuvchidan so‘ra yoki benchmarkni optional deb belgila.
2. OpenVoice V2, Anadil Uzbek TTS va boshqa nomzodlarning rasmiy repo/model card’larini tekshir. Tarmoq bo‘lmasa, tekshirilmagan faktlarni tasdiqlangan deb yozma.
3. Kod, model weights/checkpoint, upstream/base model va dataset litsenziyalarini alohida yoz.
4. O‘zbek lotin, rus va ingliz uchun kichik, qonuniy benchmark matnlar to‘plamini yarat. Haqiqiy inson ovozidan foydalanilsa, aniq rozilik olingan bo‘lsin.
5. Faqat izolyatsiyalangan prototipda modelni ishga tushirish rejasini tayyorla. Og‘ir modelni foydalanuvchi tasdig‘isiz yuklab olma va tizimga mosligi noma’lum CUDA paketlarini global muhitga o‘rnatma.
6. Natijalarni `docs/MODEL_BENCHMARK.md` ga yoz: tillar, talaffuz, tabiiylik, ovoz o‘xshashligi, RTF, RAM/VRAM, xatolar va litsenziya holati.
7. `tasks/ROADMAP.md` dagi tegishli task statuslarini faqat dalil bo‘lsa yangila.

## Yakuniy hisobot
- Tekshirilgan muhit
- Manbalar va sana
- Har bir modelning `PASS / FAIL / UNKNOWN` holati
- Litsenziya risklari
- Keyingi aniq task ID’lari
- Hali tasdiqlanmagan taxminlar

## Qabul mezonlari
Hali production model tanlanmagan bo‘lsa ham mayli; qaror dalilga asoslangan va noaniqliklar aniq qayd etilgan bo‘lishi kerak.
