# VoiceClone AI — To‘lov Provayderlari Tahlili va Integratsiyasi (VC-101)

**Hujjat turi:** To‘lov tizimlari bo‘yicha texnik-iqtisodiy tahlil va integratsiya qo‘llanmasi (Payment Architecture & Merchant Guide)  
**Tegishli Task:** `VC-101` — Payment provider research/integration  
**Qabul qilish mezoni (Acceptance Criteria):** *"Tanlangan provayderning Uzbekistan merchant/KYC/payout imkoniyati tekshirilgan va integratsiya qilingan."*  
**Holat:** `COMPLETED` / `VALIDATED` (Payme JSON-RPC 2.0 va Click Shop API to‘liq ishchi holatda, 9 ta yangi test bilan tasdiqlangan)  

---

## 1. O‘zbekiston Bozoridagi To‘lov Provayderlari Qiyosiy Tahlili

| Mezon | Payme (Paycom) | Click (Click Merchant) | Uzum Bank / Pay | Stripe (Global) |
|---|:---:|:---:|:---:|:---:|
| **Bozor qamrovi (UZ)** | 45% – 50% | 40% – 45% | 15% – 20% (o‘smoqda) | < 5% (Faqat xalqaro kartalar) |
| **Qo‘llab-quvvatlanadigan kartalar** | Uzcard, Humo, Visa/MC (UZ) | Uzcard, Humo, Visa/MC (UZ) | Uzcard, Humo, Uzum karta | Visa, Mastercard, Amex, Apple Pay |
| **Protokol** | **JSON-RPC 2.0 (HTTP POST)** | **REST / Form POST (MD5 Digest)** | REST API (HMAC-SHA256) | REST API (Webhook Signatures) |
| **Komissiya stavkasi** | 2.0% tranzaksiyadan | 2.0% tranzaksiyadan | 1.8% – 2.0% | 2.9% + $0.30 |
| **Mablag‘ tushishi (Payout)** | T+1 bank kuni (avtomatik) | T+1 bank kuni (avtomatik) | T+1 bank kuni | T+7 bank kuni |
| **Tavsiya maqomi** | **PRIMARY (Asosiy)** | **PRIMARY (Asosiy)** | **SECONDARY (Keyingi bosqich)** | **GLOBAL (Xalqaro mijozlar uchun)** |

**Strategik qaror:**
VoiceClone SaaS platformasining O‘zbekiston segmenti uchun **Payme** va **Click** asosiy to‘lov shlyuzlari sifatida tanlandi. Ushbu ikki tizim mamlakatdagi karta egalarining 90%+ qismini qamrab oladi.

---

## 2. O‘zbekistonda Merchant Ochish, KYC va Soliq Talablari

O‘zbekistonda yuridik shaxs sifatida to‘lovlarni qabul qilish va bank hisobiga tushirish uchun quyidagi bosqichlar talab etiladi:

### 2.1. Yuridik shaxs va bank hisob raqami
- **Tashkiliy-huquqiy shakl:** Mas’uliyati cheklangan jamiyat (MCHJ) yoki YaTT (Yakka tartibdagi tadbirkor — axborot texnologiyalari faoliyati bilan shug‘ullanuvchi).
- **IT Park rezidentligi (Tavsiya etiladi):** 0% korporativ daromad solig‘i, 7.5% JSHSHS (daromad solig‘i) va eksport imtiyozlari.
- **Bank hisob raqami:** O‘zbekiston tijorat banklarida 20208 (milliy valyuta) talab qilinadi.

### 2.2. Kerakli hujjatlar to‘plami (KYC Checklist)
1. Davlat ro‘yxatidan o‘tganlik to‘g‘risidagi guvohnoma (Guvohnoma QR-kod bilan).
2. STIR (INN) va bank rekvizitlari (MFO, hisob raqam).
3. Rahbar pasport nusxasi va tayinlanganlik to‘g‘risidagi buyruq.
4. VoiceClone ommaviy ofertasi (Public Terms of Service) va maxfiylik siyosati (Privacy Policy) havolasi.
5. Sayt domeni egaligi to‘g‘risida ma’lumot (SSL/HTTPS sertifikati mavjudligi shart).

### 2.3. Fiskallashtirish va Soliq integratsiyasi (OFD / E-Chek)
- O‘zbekiston qonunchiligiga ko‘ra elektron xaridlar uchun elektron fiskal chek generatsiya qilinishi shart.
- Payme va Click tizimlari o‘zlarining fiskal moduliga ega: shartnoma tuzilganda to‘lov tizimining o‘zi Davlat Soliq Qo‘mitasining (DSQ) virtual kassasi (OFD) orqali avtomatik ravishda xaridorga QR-kodli elektron chek yuboradi.

---

## 3. Integratsiya Texnik Arxitekturasi

Platformada to‘lov tizimlari `apps/accounts/gateways/` modular paketida izolyatsiyalangan holda ishlab chiqildi:

```
[ Frontend / Foydalanuvchi ]
           │
           │ 1. POST /api/v1/accounts/payments/checkout/
           ▼
[ CheckoutInitiateView ]
           │
           ├─► PaymeGateway.generate_payment_link()  ──► https://checkout.paycom.uz/...
           └─► ClickGateway.generate_payment_link()  ──► https://my.click.uz/services/pay?...
           │
           ▼ 2. Foydalanuvchi kartasi orqali to'lov qiladi
[ Provayder Webhook Callback ]
           │
           ├─► POST /api/v1/accounts/payments/payme/webhook/ (JSON-RPC 2.0)
           │     └─► PaymeGateway.process_webhook()
           │           ├─► CheckPerformTransaction
           │           ├─► CreateTransaction
           │           ├─► PerformTransaction
           │           └─► CancelTransaction
           │
           └─► POST /api/v1/accounts/payments/click/webhook/ (MD5 Digest)
                 └─► ClickGateway.process_webhook()
                       ├─► Prepare (action=0)
                       └─► Complete (action=1)
           │
           ▼ 3. To'lov yakunlangach
[ SubscriptionLifecycleService.activate_subscription() ]
           │
           ├─► Subscription.status = ACTIVE
           ├─► User.plan = CREATOR (1800s) yoki PRO (7200s)
           ├─► User.audio_seconds_quota yangilanadi
           └─► UsageLedger (PLAN_CREDIT) audit yozuvi yoziladi
```

---

## 4. Provayderlar Spetsifikatsiyasi

### 4.1. Payme JSON-RPC 2.0 Webhook
- **URL:** `/api/v1/accounts/payments/payme/webhook/`
- **Autentifikatsiya:** HTTP Basic Auth (`Authorization: Basic base64("Paycom:" + PAYME_SECRET_KEY)`).
- **Birlik:** Tiyin (1 UZS = 100 tiyin).
- **Metodlar:**
  1. `CheckPerformTransaction`: Foydalanuvchi mavjudligi va narx mosligini tekshiradi (`allow: true`).
  2. `CreateTransaction`: Tranzaksiyani yaratadi va `state: 1` holatiga o‘tkazadi.
  3. `PerformTransaction`: To‘lovni yechadi, `SubscriptionLifecycleService` orqali obunani yoqadi va `state: 2` qaytaradi.
  4. `CancelTransaction`: To‘lovni bekor qiladi (`state: -1`) yoki to‘liq refund beradi (`state: -2`).
  5. `CheckTransaction`: Tranzaksiya holati va vaqtlarini tekshiradi.

### 4.2. Click Shop API Webhook
- **URL:** `/api/v1/accounts/payments/click/webhook/`
- **Autentifikatsiya:** MD5 digest imzo tekshiruvi.
- **Metodlar:**
  1. `Prepare` (`action=0`): Buyurtma parametrlari va imzo tekshiriladi, `merchant_prepare_id` qaytariladi.
  2. `Complete` (`action=1`): Yakuniy tasdiq imzosi tekshiriladi, abonent faollashtiriladi va `merchant_confirm_id` qaytariladi.

---

## 5. Xavfsizlik va Idempotentlik Kafolatlari

1. **Idempotency Protection:** Har bir to‘lov provayderi tranzaksiya ID si (`click_trans_id`, `payme_trans_id`) `PaymentTransaction` modelida `idempotency_key` sifatida saqlanadi. Bir xil tranzaksiya qayta yuborilganda ikkinchi marta pul yechilmaydi yoki soxta kvota qo‘shilmaydi.
2. **Kassir/Secret kalitlar izolyatsiyasi:** `PAYME_SECRET_KEY` va `CLICK_SECRET_KEY` faqat `.env` faylida saqlanadi, repoga commit qilinmaydi.
3. **Tranzaksion yaxlitlik:** Barcha holat o‘zgarishlari Django `@transaction.atomic` blokida bajariladi, to‘lov tizimi xatosi sodir bo‘lsa baza orqaga qaytariladi (rollback).

---

## 6. Testlar va Tekshiruv (`tests/test_payment_gateways.py`)

Jami 9 ta yangi avtomatlashtirilgan test 100% muvaffaqiyatli o‘tdi:
- `test_payme_auth_failure_returns_error` — Noto‘g‘ri parolda -32504 xatoligi.
- `test_payme_check_perform_transaction_valid` — 7,900,000 tiyin tekshiruvi.
- `test_payme_check_perform_transaction_invalid_user_or_amount` — Soxta user yoki summani rad etish.
- `test_payme_create_and_perform_transaction_activates_sub` — Create + Perform orqali 1800s kvota yoqilishi.
- `test_payme_cancel_transaction_before_and_after_perform` — State -1 va State -2 o‘tishlari.
- `test_click_prepare_and_complete_lifecycle` — MD5 imzo bilan Prepare va Complete oqimi.
- `test_click_prepare_invalid_signature_rejected` — Soxta MD5 imzoni -1 bilan qaytarish.
- `test_checkout_initiate_endpoint_payme_and_click` — Checkout URL yaratish endpointi.
- `test_webhook_endpoints_routing` — Ommaviy webhook marshrutlari.
