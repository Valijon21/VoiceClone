# Benchmark Environment — Voice Clone AI

**Hujjat kodi:** `docs/BENCHMARK_ENVIRONMENT.md`  
**Sana:** 2026-10-11  
**Holat:** `VERIFIED` (`experiments/benchmark/environment_check.py` yordamida o‘lchandi)

---

## 1. Operatsion Tizim va Uskuna (Hardware)

- **Operatsion tizim:** Windows 10/11 (`Windows-10-10.0.22631-SP0`, x64 / AMD64)
- **Asosiy Python:** Python 3.11.9 (`C:\Users\nout.plus\AppData\Local\Programs\Python\Python311\python.exe`)
- **Global PyTorch:** `2.9.1+cpu` (Global muhitda faqat CPU torch o‘rnatilgan, CUDA mavjud emas)
- **NVIDIA GPU:** `NVIDIA GeForce RTX 3060 Laptop GPU`
  - **VRAM hajmi:** `6144.0 MB` (6.0 GB GDDR6)
  - **Drayver versiyasi:** `581.29`
  - **Qo‘llab-quvvatlanadigan CUDA:** `13.0` (drayver darajasida)

---

## 2. Disk Hajmi va Xavfsizlik Talabi (Disk Allocation)

| Disk | Jami hajm | Ishlatilgan | Bo‘sh joy | Xavf darajasi va qoida |
|---|---|---|---|---|
| **C:** | 146.75 GB | 141.85 GB | **4.90 GB** | **O‘TA YUQORI XAVF.** Pip va Hugging Face keshlarini C: drayveriga yo‘naltirish qat’iyan man etiladi! |
| **D:** (Loyiha) | 330.08 GB | 210.87 GB | **119.21 GB** | **XAVFSIZ.** Barcha virtual muhitlar (`venv`), keshlar va model og‘irliklari D: diskiga joylashtiriladi. |

### Majburiy Muhit O‘zgaruvchilari (Environment Variables):
Disk C to‘lib qolishining oldini olish uchun barcha yuklamalar D diskidagi `.cache` ga yo‘naltiriladi:
```powershell
$env:HF_HOME = "D:\Proyekt\voiceclone\.cache\huggingface"
$env:TORCH_HOME = "D:\Proyekt\voiceclone\.cache\torch"
$env:PIP_CACHE_DIR = "D:\Proyekt\voiceclone\.cache\pip"
```

---

## 3. Tarmoq va Git Holati

- **Internetga ulanish:**
  - `Hugging Face`: `Reachable` (HTTP 200)
  - `GitHub`: `Reachable` (HTTP 200)
- **Git holati:**
  - Branch: `master`
  - Remote: `https://github.com/Valijon21/VoiceClone.git`
  - Commitlar: `No commits yet` (boshlang‘ich holat)
  - Ishchi katalog: o‘zgartirilmagan va toza saqlanmoqda.
