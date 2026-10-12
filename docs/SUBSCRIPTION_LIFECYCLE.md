# VoiceClone AI — Obuna Hayotiy Sikli va To‘lovlar Arxitekturasi (VC-102)

**Hujjat turi:** Texnik Arxitektura va Biznes Mantiq Qo‘llanmasi (Technical Specification)  
**Tegishli Task:** `VC-102` — Subscription lifecycle, failed payments va refunds  
**Qabul qilish mezoni (Acceptance Criteria):** *"To‘lov xatolari quota’ni buzmaydi."*  
**Holat:** `COMPLETED` / `VALIDATED` (15 yangi unit/integration test, 100% yashil)  

---

## 1. Umumiy Arxitektura va Holatlar Mashinasi (State Machine)

VoiceClone platformasida foydalanuvchilar obunasi (`Subscription`) va har bir to‘lov amaliyoti (`PaymentTransaction`) qat'iy asinxron va tranzaksiyaviy (`@transaction.atomic`) holatlar mashinasi orqali boshqariladi.

```
       +--------------+
       |   TRIALING   |  (Boshlang'ich 5 min bepul sinov)
       +-------+------+
               |
               v To'lov muvaffaqiyatli (79,000 UZS / 199,000 UZS)
       +--------------+  Bekor qilish (davr oxirida)
+----->|    ACTIVE    |----------------------------+
|      +-------+------+                            |
|              |                                   |
|              v Qayta yechish xatosi (kartada pul yo'q)   |
|      +--------------+                            |
|      |   PAST_DUE   | (3 kunlik Grace Period)    |
|      +-------+------+                            |
|              |                                   |
|              | Grace period tugadi               |
|              v (To'lov o'tmadi)                  |
|      +--------------+                            |
|      |   EXPIRED    |                            |
|      +-------+------+                            |
|              |                                   |
|              v Downgrade: FREE                   v
|      +-------------------------------------------+
+------|                   CANCELED                |
       +-------------------------------------------+
```

---

## 2. Asosiy Qoidalar va Kafolatlar (Invariants)

### 2.1. Eng asosiy qoida: To‘lov xatolari kvotani buzmaydi
Agar foydalanuvchining navbatdagi oylik to‘lovi amalga oshmasa (kartada mablag‘ yetarli emas, karta bloklangan, yoki to‘lov tizimida vaqtinchalik xatolik):
- Foydalanuvchining hisobidagi mavjud va qonuniy sotib olingan audio sekundlar kvotasi **o‘chirilmaydi yoki kamaytirilmaydi**.
- `UsageLedger` tarixiga soxta yoki manfiy debet yozilmaydi.
- Obunaga `PAST_DUE` maqomi beriladi va unga **3 kunlik imtiyozli muddat (Grace Period)** belgilanadi.
- Imtiyozli muddat davomida foydalanuvchi generatsiya xizmatlaridan uzluksiz foydalana oladi (`is_active_or_in_grace == True`).

### 2.2. Grace Period tugashi (`handle_grace_period_expiry`)
- Agar 3 kun ichida to‘lov qayta amalga oshirilmasa, tizim avtomatik tarzda obunani `EXPIRED` holatiga o‘tkazadi.
- Foydalanuvchi hisobi xavfsiz tarzda `FREE` tarifiga o‘tkaziladi (`300` soniya bazaviy limit).
- O‘zgarish `UsageLedger` da `ADMIN_OVERRIDE` sifatida audit qilinadi.

### 2.3. Obunani bekor qilish (`cancel_subscription`)
1. **Davr oxirida bekor qilish (`immediate=False` — standart):**
   - Obuna `cancel_at_period_end = True` qilib belgilanadi.
   - Foydalanuvchi joriy oyning oxirigacha barcha imtiyozlar va kvotadan to‘liq foydalanishda davom etadi.
2. **Darhol bekor qilish (`immediate=True`):**
   - Obuna holati `CANCELED` ga o‘zgartiriladi va foydalanuvchi `FREE` tarifiga qaytariladi.

### 2.4. Mablag‘ni qaytarish (Refunds — `process_refund`)
- Faqatgina `SUCCEEDED` (to‘langan) tranzaksiyalar bo‘yicha to‘lov qaytariladi.
- Qisman va to‘liq qaytarish imkoniyati mavjud.
- To‘liq qaytarilganda obuna darhol `CANCELED` qilinadi, kvota xavfsiz va manfiy qoldiq hosil qilmagan holda `UsageLedger.OPERATION_REFUND` orqali balansga kiritiladi.

---

## 3. Ma’lumotlar Modellari

### `Subscription` modeli (`accounts_subscription`)
| Maydon | Turi | Tavsif |
|---|---|---|
| `id` | UUID | Birlamchi kalit |
| `user` | ForeignKey(User) | Obuna egasi |
| `plan` | CharField | `CREATOR` (1800s), `PRO` (7200s), `UNLIMITED` |
| `status` | CharField | `TRIALING`, `ACTIVE`, `PAST_DUE`, `CANCELED`, `EXPIRED` |
| `billing_cycle` | CharField | `MONTHLY`, `YEARLY` |
| `price_amount` | DecimalField | Oylik/yillik narx (UZS) |
| `current_period_start` | DateTimeField | Joriy to‘lov davri boshlanishi |
| `current_period_end` | DateTimeField | Joriy davr tugashi |
| `cancel_at_period_end` | BooleanField | Davr oxirida bekor qilish bayrog‘i |
| `grace_period_until` | DateTimeField | To‘lov o‘tmagan taqdirda imtiyozli muddat |
| `failed_payment_count` | PositiveIntegerField | Ketma-ket muvaffaqiyatsiz to‘lov urinishlari soni |

### `PaymentTransaction` modeli (`accounts_payment_transaction`)
| Maydon | Turi | Tavsif |
|---|---|---|
| `id` | UUID | Birlamchi kalit |
| `user` | ForeignKey(User) | Foydalanuvchi |
| `subscription` | ForeignKey(Subscription) | Bog‘liq obuna |
| `provider` | CharField | `CLICK`, `PAYME`, `UZUM`, `STRIPE`, `MOCK`, `MANUAL` |
| `provider_transaction_id` | CharField | Provayderdagi tranzaksiya ID |
| `amount` | DecimalField | Tranzaksiya summasi (so‘m) |
| `status` | CharField | `PENDING`, `SUCCEEDED`, `FAILED`, `REFUNDED` |
| `failure_code` | CharField | Xatolik kodi (`INSUFFICIENT_FUNDS`, `CARD_BLOCKED` va h.k.) |
| `failure_reason` | TextField | Xatolik tafsiloti |
| `refund_amount` | DecimalField | Qaytarilgan summa |
| `idempotency_key` | CharField | Idempotentlik kaliti (takroriy yechishdan himoya) |

---

## 4. REST API Endpointlari

| HTTP Metod | URL | Ruxsat | Tavsif |
|---|---|---|---|
| `GET` | `/api/v1/accounts/subscription/` | Authenticated | Joriy obuna holati, davr sanalari va imtiyozlar |
| `POST` | `/api/v1/accounts/subscription/` | Authenticated | Yangi obunaga yozilish yoki tarifni yangilash |
| `POST` | `/api/v1/accounts/subscription/cancel/` | Authenticated | Obunani bekor qilish (`immediate` yoki davr oxirida) |
| `GET` | `/api/v1/accounts/subscription/transactions/` | Authenticated | Foydalanuvchining to‘lov va refund tarixi |
| `POST` | `/api/v1/accounts/subscription/simulate-failure/` | Authenticated | To‘lov xatosini test qilish (Sandbox) |
| `POST` | `/api/v1/accounts/subscription/refund/` | Admin Only | Tranzaksiya summasini qaytarish va kvotani xavfsiz tiklash |

---

## 5. Avtomatlashtirilgan Testlar Natijasi (`tests/test_subscription_lifecycle.py`)

15 ta yangi unit va integratsion testlar 100% muvaffaqiyatli o‘tdi:
- `test_subscription_activation_creator_tier` — Creator tarifi (1800s, 79,000 UZS) va ledger yozuvi.
- `test_subscription_activation_pro_tier_yearly` — Pro tarifi yillik chegirma va 7200s kvota.
- `test_subscription_activation_idempotency` — Idempotency kaliti bo‘yicha takrorlanishdan himoya.
- `test_payment_failure_does_not_corrupt_quota` — **Asosiy qabul mezonining sinovi**: To‘lov xatosi paytida kvota saqlanishi va 3 kunlik grace period berilishi.
- `test_grace_period_expiry_downgrades_safely` — Imtiyozli muddat tugaganda FREE tarifiga xavfsiz tushirish.
- `test_cancellation_at_period_end_preserves_access` — Davr oxirigacha foydalanish huquqi saqlanishi.
- `test_immediate_cancellation_terminates_plan` — Darhol bekor qilish oqimi.
- `test_refund_succeeded_transaction_cancels_sub_and_rolls_back_quota` — Refund va ledger qaytarilishi.
- `test_cannot_refund_failed_transaction` — Xato tranzaksiyaga refund berishni bloklash.
- `test_api_*` — Barcha 6 ta DRF API endpointlarining ruxsat va ma’lumotlar yaxlitligi sinovlari.
