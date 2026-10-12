import React, { useState } from "react";
import { api } from "../api/client";
import { VoiceProfile } from "../types";

interface ConsentModalProps {
  isOpen: boolean;
  onClose: () => void;
  onProfileCreated: (profile: VoiceProfile) => void;
}

export const ConsentModal: React.FC<ConsentModalProps> = ({
  isOpen,
  onClose,
  onProfileCreated,
}) => {
  const [profileName, setProfileName] = useState("");
  const [language, setLanguage] = useState<"uz" | "en" | "ru">("uz");
  const [hasAgreed, setHasAgreed] = useState(false);
  const [loading, setLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  if (!isOpen) return null;

  const defaultConsentStatement = `Men, foydalanuvchi sifatida, ushbu ovoz namunasi shaxsan o‘zimga tegishli ekanligini yoki uning qonuniy egasidan sun'iy intellekt orqali ovoz klonlash va nutq sintezlash uchun rasmiy va erkin rozilik olinganligini tasdiqlayman. Men ushbu tizimdan birovning shaxsiga zarar yetkazish, firibgarlik (impersonation/fraud) yoki ruxsatsiz manipulyatsiya maqsadlarida foydalanmaslik majburiyatini olaman.`;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!hasAgreed) {
      setErrorMessage("Ovoz klonlash qoidalari va axloqiy rozilik shartlarini qabul qilishingiz shart.");
      return;
    }
    if (!profileName.trim()) {
      setErrorMessage("Ovoz profili nomini kiriting.");
      return;
    }

    setLoading(true);
    setErrorMessage(null);

    try {
      // 1. Create profile
      const profile = await api.createVoice(profileName.trim(), language);
      // 2. Submit explicit verified consent
      await api.provideConsent(profile.id, defaultConsentStatement);
      // 3. Notify parent
      onProfileCreated({ ...profile, has_consent: true });
      onClose();
    } catch (err: any) {
      const msg = err?.detail || err?.message || "Ovoz profilini yaratishda xatolik yuz berdi.";
      setErrorMessage(msg);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div
      style={{
        position: "fixed",
        inset: 0,
        backgroundColor: "rgba(0, 0, 0, 0.8)",
        backdropFilter: "blur(8px)",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        zIndex: 1000,
        padding: "1rem",
      }}
      role="dialog"
      aria-modal="true"
      aria-labelledby="consent-modal-title"
    >
      <div
        className="glass-panel"
        style={{
          width: "100%",
          maxWidth: "560px",
          padding: "2rem",
          position: "relative",
          maxHeight: "90vh",
          overflowY: "auto",
        }}
      >
        <button
          type="button"
          onClick={onClose}
          style={{
            position: "absolute",
            top: "1.25rem",
            right: "1.25rem",
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

        <div style={{ display: "flex", alignItems: "center", gap: "0.75rem", marginBottom: "0.5rem" }}>
          <div
            style={{
              padding: "0.5rem",
              borderRadius: "var(--radius-sm)",
              backgroundColor: "rgba(245, 158, 11, 0.15)",
              color: "var(--accent-amber)",
            }}
          >
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10" />
              <path d="m9 12 2 2 4-4" />
            </svg>
          </div>
          <h2 id="consent-modal-title" style={{ fontSize: "1.3rem", fontWeight: 700 }}>
            Yangi ovoz profili va Rozilik Deklaratsiyasi
          </h2>
        </div>

        <p style={{ fontSize: "0.85rem", color: "var(--text-muted)", marginBottom: "1.25rem" }}>
          Axloqiy me'yorlar (Voice Safety & Ethics) bo‘yicha faqat qonuniy rozilik berilgan ovozlarni klonlashga ruxsat etiladi.
        </p>

        {errorMessage && (
          <div className="badge badge-rose" style={{ width: "100%", padding: "0.75rem", marginBottom: "1rem", display: "block" }}>
            ⚠️ {errorMessage}
          </div>
        )}

        <form onSubmit={handleSubmit} style={{ display: "flex", flexDirection: "column", gap: "1.25rem" }}>
          <div>
            <label style={{ display: "block", fontSize: "0.85rem", fontWeight: 600, marginBottom: "0.4rem" }}>
              Ovoz profili nomi
            </label>
            <input
              type="text"
              className="form-input"
              placeholder="Masalan: Shaxsiy ovozim (Valijon)"
              value={profileName}
              onChange={(e) => setProfileName(e.target.value)}
              required
            />
          </div>

          <div>
            <label style={{ display: "block", fontSize: "0.85rem", fontWeight: 600, marginBottom: "0.4rem" }}>
              Nativ tili
            </label>
            <select
              className="form-select"
              value={language}
              onChange={(e) => setLanguage(e.target.value as any)}
            >
              <option value="uz">O‘zbek tili (Lotin yozuvi — MVP Asosiy)</option>
              <option value="en">Ingliz tili (English — Supported)</option>
              <option value="ru">Rus tili (Русский — Eksperimental)</option>
            </select>
          </div>

          {/* Legal Consent Box */}
          <div
            style={{
              padding: "1rem",
              borderRadius: "var(--radius-md)",
              backgroundColor: "rgba(15, 23, 42, 0.6)",
              border: "1px solid var(--border-subtle)",
              fontSize: "0.82rem",
              lineHeight: 1.6,
              color: "var(--text-muted)",
            }}
          >
            <div style={{ fontWeight: 700, color: "var(--text-main)", marginBottom: "0.4rem", display: "flex", alignItems: "center", gap: "0.4rem" }}>
              <span>📜</span> Rasmiy rozilik matni (Audit & Compliance):
            </div>
            <p style={{ fontStyle: "italic", marginBottom: "0.75rem" }}>
              "{defaultConsentStatement}"
            </p>
            <div style={{ fontSize: "0.75rem", color: "var(--text-dim)" }}>
              • Audit yozuvi va sha256 identifikatori xavfsizlik jurnalida qayd etiladi.<br />
              • Istalgan vaqtda profilni va audio fayllarni butunlay o‘chirib tashlashingiz mumkin (Retention: 7 kun).
            </div>
          </div>

          {/* Mandatory Checkbox */}
          <label
            style={{
              display: "flex",
              alignItems: "flex-start",
              gap: "0.75rem",
              cursor: "pointer",
              userSelect: "none",
            }}
          >
            <input
              type="checkbox"
              checked={hasAgreed}
              onChange={(e) => setHasAgreed(e.target.checked)}
              style={{
                marginTop: "0.2rem",
                width: "18px",
                height: "18px",
                accentColor: "var(--accent-primary)",
                cursor: "pointer",
              }}
            />
            <span style={{ fontSize: "0.85rem", color: "var(--text-main)", fontWeight: 500 }}>
              Men ushbu ovoz egasiman yoki foydalanishga to‘liq qonuniy rozilik olganman. Barcha javobgarlikni o‘z zimmamga olaman.
            </span>
          </label>

          <div style={{ display: "flex", justifyContent: "flex-end", gap: "0.75rem", marginTop: "0.5rem" }}>
            <button
              type="button"
              className="btn-secondary"
              onClick={onClose}
              disabled={loading}
            >
              Bekor qilish
            </button>
            <button
              type="submit"
              className="btn-primary"
              disabled={!hasAgreed || loading}
            >
              {loading ? "Tasdiqlanmoqda..." : "Profilni yaratish va Tasdiqlash"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
