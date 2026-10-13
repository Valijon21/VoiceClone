import React, { useState } from "react";
import { api } from "../api/client";
import { User } from "../types";

interface PricingModalProps {
  isOpen: boolean;
  onClose: () => void;
  user: User | null;
  onOpenAuth: () => void;
}

export const PricingModal: React.FC<PricingModalProps> = ({
  isOpen,
  onClose,
  user,
  onOpenAuth,
}) => {
  const [cycle, setCycle] = useState<"MONTHLY" | "YEARLY">("MONTHLY");
  const [loadingProvider, setLoadingProvider] = useState<string | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  if (!isOpen) return null;

  const handleSubscribe = async (plan: string, provider: "PAYME" | "CLICK") => {
    if (!user) {
      onClose();
      onOpenAuth();
      return;
    }

    setLoadingProvider(`${plan}_${provider}`);
    setErrorMsg(null);

    try {
      const res = await api.initiateCheckout({
        plan,
        billing_cycle: cycle,
        provider,
        return_url: window.location.origin,
      });

      if (res.checkout_url) {
        window.location.href = res.checkout_url;
      }
    } catch (err: any) {
      setErrorMsg(
        err?.message ||
          "To‘lov havolasini yaratishda xatolik yuz berdi. Iltimos qaytadan urinib ko‘ring."
      );
    } finally {
      setLoadingProvider(null);
    }
  };

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
        overflowY: "auto",
      }}
    >
      <div
        className="glass-panel"
        style={{
          width: "100%",
          maxWidth: "1050px",
          maxHeight: "92vh",
          overflowY: "auto",
          borderRadius: "var(--radius-lg)",
          padding: "2rem",
          background: "var(--bg-secondary)",
          border: "1px solid var(--border-subtle)",
          boxShadow: "0 25px 50px -12px rgba(0, 0, 0, 0.5)",
          position: "relative",
        }}
      >
        {/* Header */}
        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "flex-start",
            marginBottom: "1.5rem",
          }}
        >
          <div>
            <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
              <span style={{ fontSize: "1.5rem" }}>💎</span>
              <h2 style={{ fontSize: "1.5rem", fontWeight: 800 }}>
                Shaffof Tariflar va Obuna
              </h2>
            </div>
            <p style={{ color: "var(--text-muted)", fontSize: "0.88rem", marginTop: "0.25rem" }}>
              O‘zbekiston milliy to‘lov tizimlari (Payme va Click) orqali xavfsiz to‘lov qiling
            </p>
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
              lineHeight: 1,
            }}
            aria-label="Yopish"
          >
            &times;
          </button>
        </div>

        {errorMsg && (
          <div
            style={{
              background: "rgba(239, 68, 68, 0.15)",
              border: "1px solid #ef4444",
              borderRadius: "var(--radius-md)",
              padding: "0.75rem 1rem",
              color: "#fca5a5",
              fontSize: "0.85rem",
              marginBottom: "1.25rem",
            }}
          >
            {errorMsg}
          </div>
        )}

        {/* Cycle Toggle */}
        <div
          style={{
            display: "flex",
            justifyContent: "center",
            alignItems: "center",
            gap: "1rem",
            marginBottom: "2rem",
          }}
        >
          <span
            style={{
              fontSize: "0.9rem",
              fontWeight: cycle === "MONTHLY" ? 700 : 500,
              color: cycle === "MONTHLY" ? "var(--text-primary)" : "var(--text-muted)",
            }}
          >
            Oylik to‘lov
          </span>

          <button
            type="button"
            onClick={() => setCycle((c) => (c === "MONTHLY" ? "YEARLY" : "MONTHLY"))}
            style={{
              width: "56px",
              height: "28px",
              borderRadius: "14px",
              background: cycle === "YEARLY" ? "var(--accent-primary)" : "var(--bg-tertiary)",
              border: "1px solid var(--border-subtle)",
              position: "relative",
              cursor: "pointer",
              transition: "background 0.2s ease",
            }}
            aria-label="Obuna davrini o‘zgartirish"
          >
            <span
              style={{
                position: "absolute",
                top: "3px",
                left: cycle === "YEARLY" ? "30px" : "4px",
                width: "20px",
                height: "20px",
                borderRadius: "50%",
                background: "#fff",
                transition: "left 0.2s ease",
              }}
            />
          </button>

          <div style={{ display: "flex", alignItems: "center", gap: "0.4rem" }}>
            <span
              style={{
                fontSize: "0.9rem",
                fontWeight: cycle === "YEARLY" ? 700 : 500,
                color: cycle === "YEARLY" ? "var(--text-primary)" : "var(--text-muted)",
              }}
            >
              Yillik to‘lov
            </span>
            <span
              className="badge badge-emerald"
              style={{ fontSize: "0.72rem", padding: "0.15rem 0.45rem" }}
            >
              -17% chegirma
            </span>
          </div>
        </div>

        {/* Pricing Cards Grid */}
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))",
            gap: "1.25rem",
            marginBottom: "2rem",
          }}
        >
          {/* FREE TRIAL */}
          <div
            className="glass-panel"
            style={{
              padding: "1.5rem",
              borderRadius: "var(--radius-md)",
              display: "flex",
              flexDirection: "column",
              background: "rgba(255, 255, 255, 0.02)",
              border: "1px solid var(--border-subtle)",
            }}
          >
            <div style={{ fontSize: "1.1rem", fontWeight: 700, marginBottom: "0.25rem" }}>
              Free Trial
            </div>
            <div style={{ fontSize: "0.8rem", color: "var(--text-muted)", marginBottom: "1rem" }}>
              Platformani sinab ko‘rish uchun
            </div>
            <div style={{ fontSize: "1.8rem", fontWeight: 800, marginBottom: "1rem" }}>
              0 <span style={{ fontSize: "0.85rem", fontWeight: 500, color: "var(--text-muted)" }}>so‘m</span>
            </div>

            <ul style={{ listStyle: "none", padding: 0, margin: "0 0 1.5rem 0", flex: 1, fontSize: "0.83rem", lineHeight: 1.8 }}>
              <li>✓ 300 soniya (5 daqiqa) sinov kvotasi</li>
              <li>✓ 1 ta ovoz profili yaratish</li>
              <li>✓ OpenVoice V2 + MeloTTS tayanchi</li>
              <li>✓ O‘zbek, ingliz va rus tillari</li>
              <li>✓ 7 kunlik audio saqlash (retention)</li>
            </ul>

            <button
              type="button"
              className="btn-secondary"
              style={{ width: "100%", fontSize: "0.85rem", opacity: user?.plan === "FREE" ? 0.7 : 1 }}
              disabled={user?.plan === "FREE"}
            >
              {user?.plan === "FREE" ? "Hozirgi tarifingiz" : "Bepul boshlash"}
            </button>
          </div>

          {/* CREATOR */}
          <div
            className="glass-panel"
            style={{
              padding: "1.5rem",
              borderRadius: "var(--radius-md)",
              display: "flex",
              flexDirection: "column",
              background: "rgba(79, 70, 229, 0.05)",
              border: "2px solid var(--accent-primary)",
              boxShadow: "0 0 20px rgba(79, 70, 229, 0.2)",
              position: "relative",
            }}
          >
            <div
              style={{
                position: "absolute",
                top: "-12px",
                right: "16px",
                background: "var(--accent-primary)",
                color: "#fff",
                fontSize: "0.68rem",
                fontWeight: 700,
                padding: "0.2rem 0.6rem",
                borderRadius: "10px",
              }}
            >
              TAVSIYA ETILADI
            </div>

            <div style={{ fontSize: "1.1rem", fontWeight: 700, marginBottom: "0.25rem" }}>
              Creator
            </div>
            <div style={{ fontSize: "0.8rem", color: "var(--text-muted)", marginBottom: "1rem" }}>
              Kontent mualliflari va blogerlar uchun
            </div>

            <div style={{ fontSize: "1.8rem", fontWeight: 800, marginBottom: "1rem" }}>
              {cycle === "MONTHLY" ? "79,000" : "790,000"}{" "}
              <span style={{ fontSize: "0.85rem", fontWeight: 500, color: "var(--text-muted)" }}>
                so‘m / {cycle === "MONTHLY" ? "oy" : "yil"}
              </span>
            </div>

            <ul style={{ listStyle: "none", padding: 0, margin: "0 0 1.5rem 0", flex: 1, fontSize: "0.83rem", lineHeight: 1.8 }}>
              <li>✓ <strong>1,800 soniya (30 daqiqa)</strong> oylik kvota</li>
              <li>✓ 5 tagacha ovoz profili</li>
              <li>✓ Yuqori sifatli 24kHz WAV studio export</li>
              <li>✓ Tezkor audio generatsiya navbati</li>
              <li>✓ 3 kunlik grace period himoyasi</li>
            </ul>

            <div style={{ display: "flex", flexDirection: "column", gap: "0.5rem" }}>
              <button
                type="button"
                className="btn-primary"
                style={{ width: "100%", fontSize: "0.82rem", padding: "0.55rem" }}
                disabled={loadingProvider !== null}
                onClick={() => handleSubscribe("CREATOR", "PAYME")}
              >
                {loadingProvider === "CREATOR_PAYME" ? "Yuklanmoqda..." : "💳 Payme bilan to‘lash"}
              </button>

              <button
                type="button"
                className="btn-secondary"
                style={{ width: "100%", fontSize: "0.82rem", padding: "0.55rem" }}
                disabled={loadingProvider !== null}
                onClick={() => handleSubscribe("CREATOR", "CLICK")}
              >
                {loadingProvider === "CREATOR_CLICK" ? "Yuklanmoqda..." : "⚡ Click bilan to‘lash"}
              </button>
            </div>
          </div>

          {/* PRO STUDIO */}
          <div
            className="glass-panel"
            style={{
              padding: "1.5rem",
              borderRadius: "var(--radius-md)",
              display: "flex",
              flexDirection: "column",
              background: "rgba(6, 182, 212, 0.04)",
              border: "1px solid var(--accent-cyan)",
            }}
          >
            <div style={{ fontSize: "1.1rem", fontWeight: 700, marginBottom: "0.25rem" }}>
              Pro Studio
            </div>
            <div style={{ fontSize: "0.8rem", color: "var(--text-muted)", marginBottom: "1rem" }}>
              Media studiyalar va professional dublyaj
            </div>

            <div style={{ fontSize: "1.8rem", fontWeight: 800, marginBottom: "1rem" }}>
              {cycle === "MONTHLY" ? "199,000" : "1,990,000"}{" "}
              <span style={{ fontSize: "0.85rem", fontWeight: 500, color: "var(--text-muted)" }}>
                so‘m / {cycle === "MONTHLY" ? "oy" : "yil"}
              </span>
            </div>

            <ul style={{ listStyle: "none", padding: 0, margin: "0 0 1.5rem 0", flex: 1, fontSize: "0.83rem", lineHeight: 1.8 }}>
              <li>✓ <strong>7,200 soniya (120 daqiqa)</strong> oylik kvota</li>
              <li>✓ Cheksiz ovoz profillari</li>
              <li>✓ Eng yuqori ustuvorlik (Priority Queue)</li>
              <li>✓ API kirish kaliti (REST API ruxsati)</li>
              <li>✓ 24/7 VIP texnik qo‘llab-quvvatlash</li>
            </ul>

            <div style={{ display: "flex", flexDirection: "column", gap: "0.5rem" }}>
              <button
                type="button"
                className="btn-primary"
                style={{ width: "100%", fontSize: "0.82rem", padding: "0.55rem" }}
                disabled={loadingProvider !== null}
                onClick={() => handleSubscribe("PRO", "PAYME")}
              >
                {loadingProvider === "PRO_PAYME" ? "Yuklanmoqda..." : "💳 Payme bilan to‘lash"}
              </button>

              <button
                type="button"
                className="btn-secondary"
                style={{ width: "100%", fontSize: "0.82rem", padding: "0.55rem" }}
                disabled={loadingProvider !== null}
                onClick={() => handleSubscribe("PRO", "CLICK")}
              >
                {loadingProvider === "PRO_CLICK" ? "Yuklanmoqda..." : "⚡ Click bilan to‘lash"}
              </button>
            </div>
          </div>

          {/* UNLIMITED / ENTERPRISE */}
          <div
            className="glass-panel"
            style={{
              padding: "1.5rem",
              borderRadius: "var(--radius-md)",
              display: "flex",
              flexDirection: "column",
              background: "rgba(255, 255, 255, 0.02)",
              border: "1px solid var(--border-subtle)",
            }}
          >
            <div style={{ fontSize: "1.1rem", fontWeight: 700, marginBottom: "0.25rem" }}>
              Enterprise
            </div>
            <div style={{ fontSize: "0.8rem", color: "var(--text-muted)", marginBottom: "1rem" }}>
              Yirik tashkilotlar va maxsus integratsiya
            </div>

            <div style={{ fontSize: "1.6rem", fontWeight: 800, marginBottom: "1rem" }}>
              Kelishuv asosida
            </div>

            <ul style={{ listStyle: "none", padding: 0, margin: "0 0 1.5rem 0", flex: 1, fontSize: "0.83rem", lineHeight: 1.8 }}>
              <li>✓ Cheksiz audio generatsiya kvotasi</li>
              <li>✓ Alohida ajratilgan GPU server</li>
              <li>✓ Shaxsiy model fine-tuning (akustik moslashuv)</li>
              <li>✓ 99.9% SLA kafolati</li>
              <li>✓ Shaxsiy hisob menejeri</li>
            </ul>

            <a
              href="mailto:contact@voiceclone.uz?subject=Enterprise%20Tarifi%20So'rovi"
              className="btn-secondary"
              style={{
                width: "100%",
                fontSize: "0.85rem",
                textAlign: "center",
                textDecoration: "none",
                display: "block",
                padding: "0.6rem 0",
              }}
            >
              Menejer bilan bog‘lanish
            </a>
          </div>
        </div>

        {/* Footer Guarantee */}
        <div
          style={{
            borderTop: "1px solid var(--border-subtle)",
            paddingTop: "1.25rem",
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            flexWrap: "wrap",
            gap: "1rem",
            fontSize: "0.8rem",
            color: "var(--text-muted)",
          }}
        >
          <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
            <span>🛡️</span>
            <span>
              <strong>Kafolat:</strong> 72 soat ichida so‘rov yuborilganda pulni to‘liq qaytarish (Refund Policy)
            </span>
          </div>

          <div style={{ display: "flex", gap: "1rem" }}>
            <span>To‘lov xavfsizligi: PCI-DSS, Payme & Click</span>
          </div>
        </div>
      </div>
    </div>
  );
};
