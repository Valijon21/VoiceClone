import React, { useState } from "react";
import { api } from "../api/client";
import { User } from "../types";

interface AuthModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: (user: User) => void;
}

export const AuthModal: React.FC<AuthModalProps> = ({ isOpen, onClose, onSuccess }) => {
  const [isLoginTab, setIsLoginTab] = useState(true);
  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMessage(null);
    setLoading(true);

    try {
      if (isLoginTab) {
        const user = await api.login(username, password);
        onSuccess(user);
        onClose();
      } else {
        if (!email) {
          setErrorMessage("Email manzilini kiriting.");
          setLoading(false);
          return;
        }
        await api.register(username, email, password);
        // After registration, log in
        const user = await api.login(username, password);
        onSuccess(user);
        onClose();
      }
    } catch (err: any) {
      const msg =
        err?.detail ||
        err?.message ||
        (err?.password ? err.password.join(", ") : null) ||
        (err?.username ? err.username.join(", ") : null) ||
        "Xatolik yuz berdi. Iltimos ma'lumotlarni tekshiring.";
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
        backgroundColor: "rgba(0, 0, 0, 0.75)",
        backdropFilter: "blur(8px)",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        zIndex: 1000,
        padding: "1rem",
      }}
      role="dialog"
      aria-modal="true"
      aria-labelledby="auth-modal-title"
    >
      <div
        className="glass-panel"
        style={{
          width: "100%",
          maxWidth: "420px",
          padding: "2rem",
          position: "relative",
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
            lineHeight: 1,
          }}
          aria-label="Yopish"
        >
          &times;
        </button>

        <h2 id="auth-modal-title" style={{ fontSize: "1.35rem", fontWeight: 700, marginBottom: "0.5rem" }}>
          {isLoginTab ? "Tizimga kirish" : "Ro‘yxatdan o‘tish"}
        </h2>
        <p style={{ fontSize: "0.85rem", color: "var(--text-muted)", marginBottom: "1.5rem" }}>
          {isLoginTab
            ? "Ovoz profillaringiz va audio tarixingizni boshqaring"
            : "Yangi akkaunt yarating va o‘z ovozingizni xavfsiz klonlang"}
        </p>

        {/* Tab switch */}
        <div
          style={{
            display: "flex",
            backgroundColor: "var(--bg-tertiary)",
            borderRadius: "var(--radius-md)",
            padding: "0.25rem",
            marginBottom: "1.5rem",
          }}
        >
          <button
            type="button"
            onClick={() => {
              setIsLoginTab(true);
              setErrorMessage(null);
            }}
            style={{
              flex: 1,
              padding: "0.5rem",
              borderRadius: "var(--radius-sm)",
              border: "none",
              backgroundColor: isLoginTab ? "var(--accent-primary)" : "transparent",
              color: "#fff",
              fontWeight: 600,
              fontSize: "0.85rem",
              cursor: "pointer",
              transition: "all 0.2s",
            }}
          >
            Kirish
          </button>
          <button
            type="button"
            onClick={() => {
              setIsLoginTab(false);
              setErrorMessage(null);
            }}
            style={{
              flex: 1,
              padding: "0.5rem",
              borderRadius: "var(--radius-sm)",
              border: "none",
              backgroundColor: !isLoginTab ? "var(--accent-primary)" : "transparent",
              color: "#fff",
              fontWeight: 600,
              fontSize: "0.85rem",
              cursor: "pointer",
              transition: "all 0.2s",
            }}
          >
            Ro‘yxatdan o‘tish
          </button>
        </div>

        {errorMessage && (
          <div
            className="badge badge-rose"
            style={{
              width: "100%",
              padding: "0.75rem",
              marginBottom: "1rem",
              borderRadius: "var(--radius-md)",
              display: "block",
              textAlign: "left",
              textTransform: "none",
              letterSpacing: "normal",
              fontSize: "0.85rem",
            }}
          >
            ⚠️ {errorMessage}
          </div>
        )}

        <form onSubmit={handleSubmit} style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
          <div>
            <label style={{ display: "block", fontSize: "0.8rem", color: "var(--text-muted)", marginBottom: "0.35rem" }}>
              Foydalanuvchi nomi
            </label>
            <input
              type="text"
              className="form-input"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              placeholder="masalan: user_01"
              required
              autoFocus
            />
          </div>

          {!isLoginTab && (
            <div>
              <label style={{ display: "block", fontSize: "0.8rem", color: "var(--text-muted)", marginBottom: "0.35rem" }}>
                Elektron pochta (Email)
              </label>
              <input
                type="email"
                className="form-input"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="name@example.com"
                required
              />
            </div>
          )}

          <div>
            <label style={{ display: "block", fontSize: "0.8rem", color: "var(--text-muted)", marginBottom: "0.35rem" }}>
              Parol (kamida 8 belgi)
            </label>
            <input
              type="password"
              className="form-input"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
              minLength={8}
              required
            />
          </div>

          <button
            type="submit"
            className="btn-primary"
            disabled={loading}
            style={{ marginTop: "0.5rem", width: "100%" }}
          >
            {loading ? "Jarayonda..." : isLoginTab ? "Tizimga kirish" : "Akkaunt yaratish"}
          </button>
        </form>
      </div>
    </div>
  );
};
