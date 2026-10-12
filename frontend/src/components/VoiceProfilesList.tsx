import React, { useState } from "react";
import { api } from "../api/client";
import { VoiceProfile } from "../types";

interface VoiceProfilesListProps {
  voices: VoiceProfile[];
  onProfileDeleted: (id: string) => void;
  onOpenCreateModal: () => void;
}

export const VoiceProfilesList: React.FC<VoiceProfilesListProps> = ({
  voices,
  onProfileDeleted,
  onOpenCreateModal,
}) => {
  const [deletingId, setDeletingId] = useState<string | null>(null);
  const [confirmId, setConfirmId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleDelete = async (id: string) => {
    setError(null);
    setDeletingId(id);
    try {
      await api.deleteVoice(id);
      onProfileDeleted(id);
      setConfirmId(null);
    } catch (err: any) {
      setError(err?.detail || err?.message || "Ovoz profilini o‘chirishda xatolik yuz berdi.");
    } finally {
      setDeletingId(null);
    }
  };

  return (
    <div className="glass-panel" style={{ padding: "1.5rem" }}>
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "1.25rem" }}>
        <div>
          <h3 style={{ fontSize: "1.1rem", fontWeight: 700, display: "flex", alignItems: "center", gap: "0.5rem" }}>
            <span>👥</span> Ro‘yxatdan o‘tgan ovoz profillari
          </h3>
          <p style={{ fontSize: "0.8rem", color: "var(--text-muted)" }}>
            Faqat qonuniy rozilik berilgan shaxsiy ovozlar
          </p>
        </div>

        <button
          type="button"
          className="btn-primary"
          style={{ fontSize: "0.82rem", padding: "0.45rem 1rem" }}
          onClick={onOpenCreateModal}
        >
          + Yangi profil
        </button>
      </div>

      {error && (
        <div className="badge badge-rose" style={{ width: "100%", padding: "0.6rem", marginBottom: "1rem", display: "block" }}>
          ⚠️ {error}
        </div>
      )}

      {voices.length === 0 ? (
        <div
          style={{
            padding: "2.5rem 1rem",
            textAlign: "center",
            color: "var(--text-dim)",
            border: "1px dashed var(--border-subtle)",
            borderRadius: "var(--radius-md)",
          }}
        >
          <div style={{ fontSize: "2rem", marginBottom: "0.5rem" }}>🎙️</div>
          <div style={{ fontSize: "0.95rem", fontWeight: 600, color: "var(--text-main)" }}>Hozircha ovoz profili mavjud emas</div>
          <div style={{ fontSize: "0.8rem", marginTop: "0.25rem" }}>
            O‘z ovozingizni qo‘shish uchun yuqoridagi tugmani bosing va rozilik deklaratsiyasini to‘ldiring.
          </div>
        </div>
      ) : (
        <div style={{ display: "flex", flexDirection: "column", gap: "0.75rem" }}>
          {voices.map((voice) => (
            <div
              key={voice.id}
              style={{
                display: "flex",
                alignItems: "center",
                justifyContent: "space-between",
                padding: "1rem",
                borderRadius: "var(--radius-md)",
                backgroundColor: "rgba(15, 23, 42, 0.5)",
                border: "1px solid var(--border-subtle)",
                flexWrap: "wrap",
                gap: "0.75rem",
              }}
            >
              <div style={{ display: "flex", alignItems: "center", gap: "0.85rem" }}>
                <div
                  style={{
                    width: "40px",
                    height: "40px",
                    borderRadius: "var(--radius-md)",
                    backgroundColor: "var(--bg-tertiary)",
                    border: "1px solid var(--border-subtle)",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    fontSize: "1.2rem",
                  }}
                >
                  🗣️
                </div>
                <div>
                  <div style={{ fontSize: "0.95rem", fontWeight: 700 }}>{voice.name}</div>
                  <div style={{ display: "flex", gap: "0.4rem", marginTop: "0.25rem", alignItems: "center" }}>
                    <span className="badge badge-indigo" style={{ fontSize: "0.7rem", padding: "0.15rem 0.5rem" }}>
                      {voice.language.toUpperCase()}
                    </span>
                    {voice.has_consent ? (
                      <span className="badge badge-emerald" style={{ fontSize: "0.7rem", padding: "0.15rem 0.5rem" }}>
                        Rozilik: Tasdiqlangan
                      </span>
                    ) : (
                      <span className="badge badge-rose" style={{ fontSize: "0.7rem", padding: "0.15rem 0.5rem" }}>
                        Rozilik: Kutilmoqda
                      </span>
                    )}
                  </div>
                </div>
              </div>

              {/* Action buttons */}
              <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
                {confirmId === voice.id ? (
                  <div style={{ display: "flex", alignItems: "center", gap: "0.4rem" }}>
                    <button
                      type="button"
                      className="btn-primary"
                      style={{
                        backgroundColor: "var(--accent-rose)",
                        fontSize: "0.78rem",
                        padding: "0.35rem 0.75rem",
                      }}
                      onClick={() => handleDelete(voice.id)}
                      disabled={deletingId === voice.id}
                    >
                      {deletingId === voice.id ? "O‘chirilmoqda..." : "Ha, o‘chirish"}
                    </button>
                    <button
                      type="button"
                      className="btn-secondary"
                      style={{ fontSize: "0.78rem", padding: "0.35rem 0.65rem" }}
                      onClick={() => setConfirmId(null)}
                    >
                      Yo‘q
                    </button>
                  </div>
                ) : (
                  <button
                    type="button"
                    className="btn-secondary"
                    style={{ fontSize: "0.8rem", padding: "0.35rem 0.75rem", color: "var(--accent-rose)" }}
                    onClick={() => setConfirmId(voice.id)}
                    title="Profilni butunlay o‘chirish"
                  >
                    O‘chirish
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
