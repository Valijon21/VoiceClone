import React from "react";
import { GenerationJob } from "../types";

interface GenerationHistoryProps {
  jobs: GenerationJob[];
  onSelectJobAudio: (url: string, title: string) => void;
}

export const GenerationHistory: React.FC<GenerationHistoryProps> = ({
  jobs,
  onSelectJobAudio,
}) => {
  return (
    <div className="glass-panel" style={{ padding: "1.5rem" }}>
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "1.25rem" }}>
        <div>
          <h3 style={{ fontSize: "1.1rem", fontWeight: 700, display: "flex", alignItems: "center", gap: "0.5rem" }}>
            <span>📜</span> Sintezlangan audio tarixi
          </h3>
          <p style={{ fontSize: "0.8rem", color: "var(--text-muted)" }}>
            Generatsiya qilingan fayllar va ularni yuklab olish
          </p>
        </div>
        <span className="badge badge-indigo">{jobs.length} ta natija</span>
      </div>

      {jobs.length === 0 ? (
        <div
          style={{
            padding: "2.5rem 1rem",
            textAlign: "center",
            color: "var(--text-dim)",
            border: "1px dashed var(--border-subtle)",
            borderRadius: "var(--radius-md)",
          }}
        >
          <div style={{ fontSize: "2rem", marginBottom: "0.5rem" }}>🔊</div>
          <div style={{ fontSize: "0.95rem", fontWeight: 600, color: "var(--text-main)" }}>Hozircha generatsiya tarixi mavjud emas</div>
          <div style={{ fontSize: "0.8rem", marginTop: "0.25rem" }}>
            Matn kiriting va birinchi audio faylingizni sintezlab ko‘ring!
          </div>
        </div>
      ) : (
        <div style={{ display: "flex", flexDirection: "column", gap: "0.85rem", maxHeight: "400px", overflowY: "auto" }}>
          {jobs.map((job) => {
            const downloadUrl = job.result_audio?.asset?.download_url;
            return (
              <div
                key={job.id}
                style={{
                  padding: "1rem",
                  borderRadius: "var(--radius-md)",
                  backgroundColor: "rgba(15, 23, 42, 0.5)",
                  border: "1px solid var(--border-subtle)",
                  display: "flex",
                  flexDirection: "column",
                  gap: "0.5rem",
                }}
              >
                <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", flexWrap: "wrap", gap: "0.5rem" }}>
                  <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
                    <span className="badge badge-indigo" style={{ fontSize: "0.7rem" }}>
                      {job.language.toUpperCase()}
                    </span>
                    <span style={{ fontSize: "0.8rem", color: "var(--text-dim)" }}>
                      {new Date(job.created_at).toLocaleString("uz-UZ")}
                    </span>
                  </div>

                  <div>
                    {job.status === "SUCCEEDED" ? (
                      <span className="badge badge-emerald" style={{ fontSize: "0.7rem" }}>Muvaffaqiyatli</span>
                    ) : job.status === "FAILED" ? (
                      <span className="badge badge-rose" style={{ fontSize: "0.7rem" }}>Xato</span>
                    ) : (
                      <span className="badge badge-amber" style={{ fontSize: "0.7rem" }}>{job.status}</span>
                    )}
                  </div>
                </div>

                <p
                  style={{
                    fontSize: "0.88rem",
                    color: "var(--text-main)",
                    lineHeight: 1.4,
                    overflow: "hidden",
                    textOverflow: "ellipsis",
                    whiteSpace: "nowrap",
                  }}
                  title={job.input_text}
                >
                  "{job.input_text}"
                </p>

                {/* Actions row if succeeded */}
                {job.status === "SUCCEEDED" && downloadUrl && (
                  <div style={{ display: "flex", alignItems: "center", gap: "0.75rem", marginTop: "0.25rem" }}>
                    <button
                      type="button"
                      className="btn-primary"
                      style={{ fontSize: "0.78rem", padding: "0.35rem 0.8rem" }}
                      onClick={() => onSelectJobAudio(downloadUrl, job.input_text.substring(0, 30))}
                    >
                      ▶️ Tinglash
                    </button>

                    <a
                      href={downloadUrl}
                      download={`audio_${job.id.substring(0, 8)}.wav`}
                      className="btn-secondary"
                      style={{ fontSize: "0.78rem", padding: "0.35rem 0.8rem", textDecoration: "none" }}
                    >
                      💾 Yuklab olish
                    </a>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};
