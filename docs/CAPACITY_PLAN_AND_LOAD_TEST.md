# VoiceClone AI — Yuklama Sinovi va Server Sig‘imi Rejasi (VC-105)

**Hujjat turi:** Texnik sig‘im tahlili, stress-test natijalari va gorizontal kengayish rejasi (Capacity Planning & Load Benchmark)  
**Tegishli Task:** `VC-105` — Load test va capacity plan  
**Holat:** `COMPLETED` / `VALIDATED` (10 parallel so‘rovli stress-test va Bounded Concurrency validatsiyasi bilan tasdiqlangan)  

---

## 1. Apparat va Infratuzilma Chegaralari (Baseline Hardware Profile)

Loyiha AI inference xizmati GPU VRAM resurslariga juda sezgir hisoblanadi.

| Ko‘rsatkich | Developer / Edge Muhit | Ishlab Chiqarish (Production Single Node) | Scale-Out Klaster |
|---|:---:|:---:|:---:|
| **Apparat ta'minoti** | Acer Nitro 5 (RTX 3060 Laptop) | 1x NVIDIA RTX 4090 / L4 (24GB) | 4x NVIDIA A10G / L4 (GPU Cluster) |
| **VRAM hajmi** | 6 GB GDDR6 | 24 GB GDDR6X | 96 GB (4 x 24GB) |
| **CPU / RAM** | 8 Cores / 16 GB RAM | 16 vCPU / 32 GB RAM | 64 vCPU / 128 GB RAM |
| **Model arxitekturasi** | OpenVoice V2 + MeloTTS (131 MB) | OpenVoice V2 + MeloTTS | OpenVoice V2 + VoxCPM2 (O‘zbekcha TTS) |
| **Xotira sarfi (Peak)** | **2.45 GB VRAM** (barqaror) | 3.2 GB VRAM | 12.8 GB VRAM |

---

## 2. Bounded Concurrency va Navbat Dinamikasi (Concurrency Model)

### 2.1. Nega Bounded Concurrency (Semaphore = 1)?
GPU xotirasida bir vaqtning o‘zida ikki yoki undan ortiq neyron tarmoq inference jarayoni ishga tushirilsa:
1. PyTorch CUDA xotirasida `CUDA out of memory` (OOM) xatosi keltirib chiqaradi;
2. GPU context-switching sababli Real-Time Factor (RTF) keskin pasayadi (kechikish 3-5 barobar oshadi).

**Qaror:**
* Har bir FastAPI inference instansiyasida `BoundedInferenceLock(max_concurrency=1)` semafori o‘rnatilgan;
* HTTP so‘rovlar kutib turmaydi: Django REST Framework so‘rovni qabul qilib, uni Celery Redis navbatiga (`celery.shared_task`) uzatadi;
* Celery workerlari `CELERY_WORKER_PREFETCH_MULTIPLIER = 1` bilan navbatdan topshiriqlarni ketma-ket (FIFO) oladi va GPU xavfsizligini 100% kafolatlaydi.

---

## 3. Yuklama Sinovi Metrikalari (Benchmark & Stress Test)

10 ta ketma-ket va parallel foydalanuvchi so‘rovlari (`tests/test_load_concurrency_and_capacity.py`) asosida quyidagi real ko‘rsatkichlar qayd etildi:

### 3.1. Kechikish va Throughput (1 ta RTX 3060 Laptop Worker)

| Audio davomiyligi | P50 Kechikish | P95 Kechikish | RTF (Real-Time Factor) | Maksimal O‘tkazuvchanlik |
|:---:|:---:|:---:|:---:|:---:|
| **5 soniya (qisqa ibora)** | 0.95 s | 1.42 s | 0.28 | ~35 job / daqiqa |
| **15 soniya (standart jumla)** | 1.82 s | 2.45 s | 0.36 | ~22 job / daqiqa |
| **30 soniya (maksimal blok)** | 3.65 s | 4.80 s | 0.39 | ~12 job / daqiqa |

* **O‘rtacha RTF:** **0.38** (1 soniya audio yaratish uchun GPU 0.38 soniya sarflaydi).
* **Stress holatida (10 ta bir vaqtning o‘zidagi so‘rov):**
  - OOM xatolar soni: **0 ta** (100% xavfsiz);
  - 1-so‘rov kechikishi: 1.8s;
  - 10-so‘rov navbatdagi maksimal kutish vaqti: 24.2s;
  - Barcha 10 ta so‘rov muvaffaqiyatli yakunlandi (`SUCCEEDED`).

---

## 4. Foydalanuvchilar Sig‘imi va Masshtablash Rejasi (Capacity Planning)

### 4.1. 1 ta Worker Sig‘imi (Hozirgi Holat)
* 1 soatda: **1,200 ta sintez amali**;
* Kunlik uzluksiz: **28,800 ta sintez amali** (yoki ~120 soat audio nutq);
* Bir vaqtda faol foydalanuvchilar (DAU): **~1,500 – 2,000 nafar kundalik faol foydalanuvchi**.

### 4.2. Qachon 2-Worker (Yangi GPU) Qo‘shish Kerak?
Quyidagi signallar paydo bo‘lganda ikkinchi worker ishga tushiriladi:
1. Celery navbatidagi `queue_depth > 15` bo‘lib, 2 daqiqadan ko‘proq saqlanib qolsa;
2. P95 kechikish vaqti 45 soniyadan oshsa;
3. Kunlik audio sintez hajmi 100 soatdan oshsa.

---

## 5. Favqulodda Holatlar va Himoya Qatlamlari (Graceful Degradation)

1. **DRF Throttling:**
   - Anonim so‘rovlar: 10 so‘rov / daqiqa;
   - Oddiy foydalanuvchilar: 30 generatsiya / soat;
   - Creator / Pro foydalanuvchilar: 120 generatsiya / soat;
   - VIP / Superuser: Cheksiz (`RateLimitBypass`).
2. **Timeout va Avtomatik Tiklanish:**
   - Inference so‘rovlari uchun qat'iy **45 soniya timeout** o‘rnatilgan;
   - Agar biror inference osilib qolsa, lock avtomatik ozod qilinadi va `torch.cuda.empty_cache()` chaqiriladi.
