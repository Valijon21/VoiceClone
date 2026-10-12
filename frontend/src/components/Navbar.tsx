import React from "react";
import { User } from "../types";

interface NavbarProps {
  user: User | null;
  onOpenAuth: () => void;
  onLogout: () => void;
}

export const Navbar: React.FC<NavbarProps> = ({ user, onOpenAuth, onLogout }) => {
  return (
    <header className="glass-panel" style={{ margin: "1rem auto", maxWidth: "1280px", padding: "1rem 1.5rem" }}>
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", flexWrap: "wrap", gap: "1rem" }}>
        
        {/* Brand */}
        <div style={{ display: "flex", alignItems: "center", gap: "0.85rem" }}>
          <div
            style={{
              width: "42px",
              height: "42px",
              borderRadius: "var(--radius-md)",
              background: "linear-gradient(135deg, var(--accent-primary), var(--accent-cyan))",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              boxShadow: "var(--shadow-glow)",
            }}
          >
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#fff" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3Z" />
              <path d="M19 10v2a7 7 0 0 1-14 0v-2" />
              <line x1="12" y1="19" x2="12" y2="22" />
            </svg>
          </div>
          <div>
            <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
              <h1 style={{ fontSize: "1.25rem", fontWeight: 800, letterSpacing: "-0.02em" }}>VoiceClone AI</h1>
              <span className="badge badge-emerald" style={{ fontSize: "0.65rem" }}>MVP v0.1</span>
            </div>
            <p style={{ fontSize: "0.8rem", color: "var(--text-muted)" }}>
              O‘zbek, ingliz va rus tillari uchun axloqiy ovoz klonlash platformasi
            </p>
          </div>
        </div>

        {/* System Badges & User Status */}
        <div style={{ display: "flex", alignItems: "center", gap: "0.75rem", flexWrap: "wrap" }}>
          <div className="badge badge-emerald" title="Faqat tasdiqlangan rozilik bilan generatsiya qilinadi">
            <span style={{ display: "inline-block", width: "6px", height: "6px", borderRadius: "50%", background: "currentColor" }}></span>
            Consent Gate: STRICT
          </div>

          <div className="badge badge-indigo" title="OpenVoice V2 + MeloTTS AI Adapter">
            Model: OpenVoice V2
          </div>

          {user ? (
            <div style={{ display: "flex", alignItems: "center", gap: "0.75rem", marginLeft: "0.5rem" }}>
              <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
                <div
                  style={{
                    width: "32px",
                    height: "32px",
                    borderRadius: "50%",
                    background: "var(--bg-tertiary)",
                    border: "1px solid var(--accent-primary)",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    fontWeight: 700,
                    fontSize: "0.85rem",
                    color: "var(--accent-primary)",
                  }}
                >
                  {user.username.charAt(0).toUpperCase()}
                </div>
                <span style={{ fontSize: "0.9rem", fontWeight: 600 }}>{user.username}</span>
              </div>
              <button
                type="button"
                className="btn-secondary"
                style={{ padding: "0.4rem 0.85rem", fontSize: "0.82rem" }}
                onClick={onLogout}
                aria-label="Chiqish"
              >
                Chiqish
              </button>
            </div>
          ) : (
            <button
              type="button"
              className="btn-primary"
              style={{ padding: "0.5rem 1.1rem", fontSize: "0.85rem" }}
              onClick={onOpenAuth}
              aria-label="Kirish yoki Ro‘yxatdan o‘tish"
            >
              Kirish / Ro‘yxatdan o‘tish
            </button>
          )}
        </div>

      </div>
    </header>
  );
};
