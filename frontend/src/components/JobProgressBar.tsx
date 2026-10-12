import React, { useEffect, useState } from "react";
import { api } from "../api/client";
import { GenerationJob } from "../types";

interface JobProgressBarProps {
  initialJob: GenerationJob;
  onJobFinished: (completedJob: GenerationJob) => void;
  onRetry: () => void;
}

export const JobProgressBar: React.FC<JobProgressBarProps> = ({
  initialJob,
  onJobFinished,
  onRetry,
}) => {
  const [job, setJob] = useState<GenerationJob>(initialJob);

  useEffect(() => {
    setJob(initialJob);
  }, [initialJob]);

  useEffect(() => {
    if (job.status === "SUCCEEDED" || job.status === "FAILED" || job.status === "CANCELLED") {
      return;
    }

    const interval = setInterval(async () => {
      try {
        const updated = await api.getJobById(job.id);
        setJob(updated);
        if (updated.status === "SUCCEEDED" || updated.status === "FAILED") {
          onJobFinished(updated);
          clearInterval(interval);
        }
      } catch (err) {
        // Log silently or ignore temporary network blip
      }
    }, 1500);

    return () => clearInterval(interval);
  }, [job.id, job.status, onJobFinished]);

  const getStatusBadge = () => {
    switch (job.status) {
      case "PENDING":
        return <span className="badge badge-amber">Navbatda (Pending)</span>;
      case "RUNNING":
        return <span className="badge badge-indigo">Ishlanmoqda (Running)</span>;
      case "SUCCEEDED":
        return <span className="badge badge-emerald">Yakunlandi (Succeeded)</span>;
      case "FAILED":
        return <span className="badge badge-rose">Xatolik (Failed)</span>;
      default:
        return <span className="badge badge-indigo">{job.status}</span>;
    }
  };

  return (
    <div
      className="glass-panel"
      style={{
        padding: "1.5rem",
        borderLeft:
          job.status === "SUCCEEDED"
            ? "4px solid var(--accent-emerald)"
            : job.status === "FAILED"
            ? "4px solid var(--accent-rose)"
            : "4px solid var(--accent-primary)",
      }}
    >
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "0.75rem" }}>
        <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
          <span style={{ fontSize: "1.1rem" }}>⚡</span>
          <span style={{ fontSize: "0.95rem", fontWeight: 700 }}>Generatsiya holati:</span>
          <code style={{ fontSize: "0.8rem", color: "var(--text-dim)" }}>#{job.id.substring(0, 8)}</code>
        </div>
        {getStatusBadge()}
      </div>

      <p style={{ fontSize: "0.85rem", color: "var(--text-muted)", marginBottom: "1rem" }}>
        {job.status === "PENDING" && "Vazifa Celery navbatida kutmoqda..."}
        {job.status === "RUNNING" && "GPU xotirasida AI inference modeli orqali nutq sintezlanmoqda..."}
        {job.status === "SUCCEEDED" && "Nutq muvaffaqiyatli sintezlandi va audio fayl saqlandi!"}
        {job.status === "FAILED" && `Xatolik: ${job.error_message || "Generatsiya amalga oshmadi."}`}
      </p>

      {/* Progress Bar Container */}
      <div
        style={{
          width: "100%",
          height: "10px",
          backgroundColor: "rgba(15, 23, 42, 0.8)",
          borderRadius: "var(--radius-full)",
          overflow: "hidden",
          position: "relative",
          marginBottom: "0.5rem",
        }}
      >
        <div
          style={{
            height: "100%",
            width: `${Math.min(100, Math.max(5, job.progress_percent))}%`,
            background:
              job.status === "SUCCEEDED"
                ? "linear-gradient(90deg, var(--accent-emerald), #34d399)"
                : job.status === "FAILED"
                ? "var(--accent-rose)"
                : "linear-gradient(90deg, var(--accent-primary), var(--accent-cyan))",
            borderRadius: "var(--radius-full)",
            transition: "width 0.4s ease-out",
          }}
        />
      </div>

      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", fontSize: "0.8rem", color: "var(--text-dim)" }}>
        <span>Progress: {job.progress_percent}%</span>
        {job.status === "FAILED" && (
          <button
            type="button"
            className="btn-secondary"
            style={{ fontSize: "0.75rem", padding: "0.25rem 0.65rem" }}
            onClick={onRetry}
          >
            Qayta urinish
          </button>
        )}
      </div>
    </div>
  );
};
