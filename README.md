# Voice Clone AI — Antigravity Starter Pack

Bu repo paketi Antigravity va boshqa AI coding agentlar bilan loyihani bosqichma-bosqich qurish uchun tayyorlangan. Hozircha bu **reja va agent yo‘riqnomasi**, tayyor ishlaydigan ilova kodi emas.

## Boshlash

1. ZIPni alohida papkaga oching.
2. Papkani Antigravity’da workspace sifatida oching.
3. `AGENTS.md`, `docs/SYSTEM_DESIGN.md`, `tasks/ROADMAP.md` va `.agent/rules/voice-clone-project.md` fayllarini agentga o‘qiting.
4. Birinchi bo‘lib `.agent/workflows/01-discovery-and-benchmark.md` topshirig‘ini bajartiring. Dastlab model benchmark va kompyuter resurslarini tekshiring; darhol butun ilovani generatsiya qildirmang.
5. Har faza oxirida testlar, o‘zgargan fayllar, qolgan muammolar va keyingi task ID’lari haqida hisobot talab qiling.

## Tavsiya etilgan ish usuli

- Bir vaqtning o‘zida bitta faza va 1–3 ta bog‘liq task.
- Avval mavjud kodni tekshirish, keyin kichik o‘zgarish, so‘ng test.
- Model, checkpoint va dataset litsenziyasi tekshirilmaguncha pullik production ishlatmaslik.
- API kalitlari, parollar va haqiqiy foydalanuvchi ovozlarini Git’ga joylamaslik.
- Ovoz klonlashni faqat o‘z ovozi yoki aniq ruxsat berilgan ovozlar bilan cheklash.

## Tuzilma

- `AGENTS.md` — agent uchun asosiy loyiha qoidalari.
- `.agent/rules/` — doimiy kodlash va xavfsizlik qoidalari.
- `.agent/workflows/` — qayta ishlatiladigan ish tartiblari.
- `docs/SYSTEM_DESIGN.md` — system design va arxitektura.
- `tasks/ROADMAP.md` — bosqichlar va qabul mezonlari.
- `tasks/SPRINT_BOARD.md` — bajariladigan ishlar holatini belgilash.
- `MODEL_LICENSES.md` — model litsenziyasini tekshirish shabloni.
- `PROMPTS/` — agentga beriladigan tayyor promptlar.
