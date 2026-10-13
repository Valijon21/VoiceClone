import React, { useState } from "react";

interface LegalModalProps {
  isOpen: boolean;
  onClose: () => void;
  initialTab?: "TERMS" | "PRIVACY" | "RETENTION" | "REFUND";
}

export const LegalModal: React.FC<LegalModalProps> = ({
  isOpen,
  onClose,
  initialTab = "TERMS",
}) => {
  const [activeTab, setActiveTab] = useState<"TERMS" | "PRIVACY" | "RETENTION" | "REFUND">(
    initialTab
  );

  if (!isOpen) return null;

  return (
    <div
      style={{
        position: "fixed",
        inset: 0,
        zIndex: 1000,
        background: "rgba(10, 15, 29, 0.82)",
        backdropFilter: "blur(12px)",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        padding: "1rem",
      }}
    >
      <div
        className="glass-panel"
        style={{
          width: "100%",
          maxWidth: "800px",
          maxHeight: "88vh",
          display: "flex",
          flexDirection: "column",
          borderRadius: "var(--radius-lg)",
          padding: "2rem",
          background: "var(--bg-secondary)",
          border: "1px solid var(--border-subtle)",
          boxShadow: "0 25px 50px -12px rgba(0, 0, 0, 0.5)",
        }}
      >
        {/* Header */}
        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            marginBottom: "1.25rem",
          }}
        >
          <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
            <span style={{ fontSize: "1.4rem" }}>📜</span>
            <h2 style={{ fontSize: "1.3rem", fontWeight: 800 }}>
              Qonuniy Hujjatlar va Axloqiy Siyosat
            </h2>
          </div>

          <button
            type="button"
            onClick={onClose}
            style={{
              background: "transparent",
              border: "none",
              color: "var(--text-muted)",
              fontSize: "1.5rem",
              cursor: "pointer",
            }}
            aria-label="Yopish"
          >
            &times;
          </button>
        </div>

        {/* Tab Navigation */}
        <div
          style={{
            display: "flex",
            gap: "0.5rem",
            borderBottom: "1px solid var(--border-subtle)",
            paddingBottom: "0.75rem",
            marginBottom: "1.25rem",
            flexWrap: "wrap",
          }}
        >
          <button
            type="button"
            onClick={() => setActiveTab("TERMS")}
            style={{
              padding: "0.4rem 0.8rem",
              borderRadius: "var(--radius-sm)",
              fontSize: "0.85rem",
              fontWeight: activeTab === "TERMS" ? 700 : 500,
              background: activeTab === "TERMS" ? "var(--accent-primary)" : "transparent",
              color: activeTab === "TERMS" ? "#fff" : "var(--text-muted)",
              border: "none",
              cursor: "pointer",
            }}
          >
            Foydalanish Shartlari
          </button>

          <button
            type="button"
            onClick={() => setActiveTab("PRIVACY")}
            style={{
              padding: "0.4rem 0.8rem",
              borderRadius: "var(--radius-sm)",
              fontSize: "0.85rem",
              fontWeight: activeTab === "PRIVACY" ? 700 : 500,
              background: activeTab === "PRIVACY" ? "var(--accent-primary)" : "transparent",
              color: activeTab === "PRIVACY" ? "#fff" : "var(--text-muted)",
              border: "none",
              cursor: "pointer",
            }}
          >
            Maxfiylik Siyosati
          </button>

          <button
            type="button"
            onClick={() => setActiveTab("RETENTION")}
            style={{
              padding: "0.4rem 0.8rem",
              borderRadius: "var(--radius-sm)",
              fontSize: "0.85rem",
              fontWeight: activeTab === "RETENTION" ? 700 : 500,
              background: activeTab === "RETENTION" ? "var(--accent-primary)" : "transparent",
              color: activeTab === "RETENTION" ? "#fff" : "var(--text-muted)",
              border: "none",
              cursor: "pointer",
            }}
          >
            7 Kunlik Saqlash (Retention)
          </button>

          <button
            type="button"
            onClick={() => setActiveTab("REFUND")}
            style={{
              padding: "0.4rem 0.8rem",
              borderRadius: "var(--radius-sm)",
              fontSize: "0.85rem",
              fontWeight: activeTab === "REFUND" ? 700 : 500,
              background: activeTab === "REFUND" ? "var(--accent-primary)" : "transparent",
              color: activeTab === "REFUND" ? "#fff" : "var(--text-muted)",
              border: "none",
              cursor: "pointer",
            }}
          >
            To‘lov va Pul Qaytarish
          </button>
        </div>

        {/* Tab Content */}
        <div
          style={{
            flex: 1,
            overflowY: "auto",
            fontSize: "0.88rem",
            lineHeight: 1.65,
            color: "var(--text-secondary)",
            paddingRight: "0.5rem",
          }}
        >
          {activeTab === "TERMS" && (
            <div>
              <h3 style={{ color: "var(--text-primary)", marginBottom: "0.5rem" }}>
                1. Axloqiy Ovoz Xavfsizligi va Consent Gate
              </h3>
              <p style={{ marginBottom: "0.75rem" }}>
                VoiceClone AI platformasida ovoz klonlash faqat va faqat ovoz egasining qonuniy, hujjatlashtirilgan roziligi bilan amalga oshiriladi. Har bir ovoz profili yaratishda tizim majburiy <strong>Consent Record</strong> yaratadi.
              </p>
              <h4 style={{ color: "var(--text-primary)", marginTop: "1rem", marginBottom: "0.25rem" }}>
                Qat'iy taqiqlangan harakatlar:
              </h4>
              <ul style={{ paddingLeft: "1.25rem", marginBottom: "1rem" }}>
                <li>Birovning shaxsiga ruxsatsiz taqlid qilish (Deepfake impersonation);</li>
                <li>Firibgarlik, yolg‘on xabarlar tarqatish yoki moliyaviy tizimlarni aldash;</li>
                <li>Siyosatchilar, mashhurlar yoki jamoat arboblari nomidan ruxsatsiz bayonotlar tayyorlash;</li>
                <li>Birovni obro‘sizlantiruvchi yoki tuhmat xarakteridagi audio materiallar tayyorlash.</li>
              </ul>
              <p>
                Ushbu qoidalar buzilganda, hisob zudlik bilan bloklanadi va tegishli audio materiallar o‘chirib tashlanadi.
              </p>
            </div>
          )}

          {activeTab === "PRIVACY" && (
            <div>
              <h3 style={{ color: "var(--text-primary)", marginBottom: "0.5rem" }}>
                2. Shaxsga Doir Ma'lumotlar Maxfiyligi (GDPR)
              </h3>
              <p style={{ marginBottom: "0.75rem" }}>
                Biz sizning shaxsiy ma'lumotlaringiz va ovoz namunalaringiz xavfsizligini ta'minlashga eng yuqori darajada mas'uliyat bilan yondashamiz:
              </p>
              <ul style={{ paddingLeft: "1.25rem", marginBottom: "1rem" }}>
                <li>
                  <strong>Audio Izolyatsiyasi:</strong> Siz yuklagan va generatsiya qilgan audio fayllar faqat sizning hisobingizga tegishli bo‘lib, boshqa foydalanuvchilar ularga kirish huquqiga ega emas.
                </li>
                <li>
                  <strong>Parollar Xavfsizligi:</strong> Parollar va sessiya ma'lumotlari sanoat standarti bo‘lgan PBKDF2 / Argon2 algoritmlari bilan shifrlangan.
                </li>
                <li>
                  <strong>Uchinchi tomonlar:</strong> Sizning shaxsiy audiolaringiz marketing maqsadida hech qanday uchinchi shaxslarga berilmaydi va sotilmaydi.
                </li>
              </ul>
            </div>
          )}

          {activeTab === "RETENTION" && (
            <div>
              <h3 style={{ color: "var(--text-primary)", marginBottom: "0.5rem" }}>
                3. Ma'lumotlarni Saqlash va Avtomatik Tozalash (Retention Policy)
              </h3>
              <p style={{ marginBottom: "0.75rem" }}>
                Server resurslarini optimallashtirish va xavfsizlikni kuchaytirish maqsadida quyidagi saqlash muddati o‘rnatilgan:
              </p>
              <div
                style={{
                  background: "rgba(6, 182, 212, 0.08)",
                  border: "1px solid var(--accent-cyan)",
                  borderRadius: "var(--radius-md)",
                  padding: "1rem",
                  marginBottom: "1rem",
                }}
              >
                <div style={{ fontWeight: 700, color: "var(--accent-cyan)", marginBottom: "0.25rem" }}>
                  ⏳ 7 Kunlik Saqlash Qoidasi:
                </div>
                <div>
                  Platforma orqali sintez qilingan barcha audio fayllar serverda yaratilganidan boshlab <strong>aniq 7 kun</strong> saqlanadi. 7 kundan so‘ng Celery avtomatik tozalash vazifasi fayllarni diskdan qayta tiklanmas qilib o‘chiradi.
                </div>
              </div>
              <p>
                <strong>Tavsiya:</strong> Tayyor bo‘lgan muhim audio fayllarni yaratilgandan so‘ng o‘z kompyuteringizga yuklab olishni unutmang.
              </p>
            </div>
          )}

          {activeTab === "REFUND" && (
            <div>
              <h3 style={{ color: "var(--text-primary)", marginBottom: "0.5rem" }}>
                4. To‘lovlar, Obunani Boshqarish va Pulni Qaytarish
              </h3>
              <p style={{ marginBottom: "0.75rem" }}>
                To‘lovlar O‘zbekiston milliy shlyuzlari (Payme va Click) orqali xavfsiz qabul qilinadi.
              </p>
              <ul style={{ paddingLeft: "1.25rem", marginBottom: "1rem" }}>
                <li>
                  <strong>3 Kunlik Imtiyozli Davr (Grace Period):</strong> Obuna yangilanishida mablag‘ yetarli bo‘lmasa, hisob darhol to‘xtatilmaydi. Sizga kartani to‘ldirish uchun 3 kun beriladi va mavjud kvotangiz o‘chirilmaydi.
                </li>
                <li>
                  <strong>Pulni Qaytarish (Refund):</strong> Obuna to‘langandan so‘ng 72 soat ichida xizmatdan qoniqmasangiz va kvotangizning 20% dan ko‘prog‘ini ishlatmagan bo‘lsangiz, support@voiceclone.uz orqali to‘liq refund talab qilishingiz mumkin.
                </li>
              </ul>
            </div>
          )}
        </div>

        {/* Footer */}
        <div
          style={{
            borderTop: "1px solid var(--border-subtle)",
            paddingTop: "1rem",
            display: "flex",
            justifyContent: "flex-end",
          }}
        >
          <button type="button" className="btn-primary" onClick={onClose}>
            Tushundim
          </button>
        </div>
      </div>
    </div>
  );
};
