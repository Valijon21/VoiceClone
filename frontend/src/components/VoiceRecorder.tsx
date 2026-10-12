import React, { useRef, useState } from "react";
import { api } from "../api/client";
import { AudioAsset } from "../types";

interface VoiceRecorderProps {
  onAudioUploaded: (asset: AudioAsset) => void;
}

export const VoiceRecorder: React.FC<VoiceRecorderProps> = ({ onAudioUploaded }) => {
  const [isRecording, setIsRecording] = useState(false);
  const [recordSeconds, setRecordSeconds] = useState(0);
  const [audioUrl, setAudioUrl] = useState<string | null>(null);
  const [audioBlob, setAudioBlob] = useState<Blob | null>(null);
  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [uploadSuccess, setUploadSuccess] = useState<string | null>(null);

  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const timerRef = useRef<any>(null);
  const fileInputRef = useRef<HTMLInputElement | null>(null);

  // Start recording
  const startRecording = async () => {
    setUploadError(null);
    setUploadSuccess(null);
    setAudioUrl(null);
    setAudioBlob(null);

    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      mediaRecorderRef.current = new MediaRecorder(stream);
      chunksRef.current = [];

      mediaRecorderRef.current.ondataavailable = (e) => {
        if (e.data.size > 0) {
          chunksRef.current.push(e.data);
        }
      };

      mediaRecorderRef.current.onstop = () => {
        const blob = new Blob(chunksRef.current, { type: "audio/wav" });
        setAudioBlob(blob);
        const url = URL.createObjectURL(blob);
        setAudioUrl(url);

        // Stop all audio tracks
        stream.getTracks().forEach((track) => track.stop());
      };

      mediaRecorderRef.current.start();
      setIsRecording(true);
      setRecordSeconds(0);

      timerRef.current = setInterval(() => {
        setRecordSeconds((prev) => prev + 1);
      }, 1000);
    } catch (err: any) {
      setUploadError("Mikrofondan foydalanishga ruxsat berilmadi yoki mikrofon topilmadi.");
    }
  };

  // Stop recording
  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
      clearInterval(timerRef.current);
    }
  };

  // Upload recorded blob or chosen file
  const handleUpload = async (fileToUpload?: File) => {
    setUploadError(null);
    setUploadSuccess(null);
    setUploading(true);

    try {
      let file: File;
      if (fileToUpload) {
        file = fileToUpload;
      } else if (audioBlob) {
        file = new File([audioBlob], `recording_${Date.now()}.wav`, { type: "audio/wav" });
      } else {
        throw new Error("Yuklash uchun audio topilmadi.");
      }

      if (file.size > 25 * 1024 * 1024) {
        throw new Error("Fayl hajmi 25 MB dan oshmasligi kerak.");
      }

      const asset = await api.uploadAudio(file, "REFERENCE_VOICE");
      setUploadSuccess(`Audio muvaffaqiyatli yuklandi: ${file.name}`);
      onAudioUploaded(asset);
    } catch (err: any) {
      const msg = err?.detail || err?.message || "Audio yuklashda xatolik yuz berdi.";
      setUploadError(msg);
    } finally {
      setUploading(false);
    }
  };

  // File drag & drop handler
  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setAudioUrl(URL.createObjectURL(file));
      setAudioBlob(file);
      handleUpload(file);
    }
  };

  const formatTime = (secs: number) => {
    const m = Math.floor(secs / 60);
    const s = secs % 60;
    return `${m.toString().padStart(2, "0")}:${s.toString().padStart(2, "0")}`;
  };

  return (
    <div className="glass-panel" style={{ padding: "1.5rem" }}>
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "1rem" }}>
        <h3 style={{ fontSize: "1.05rem", fontWeight: 700, display: "flex", alignItems: "center", gap: "0.5rem" }}>
          <span>🎙️</span> Ovoz namunasini yozish yoki yuklash
        </h3>
        <span className="badge badge-indigo">16–48 kHz WAV</span>
      </div>

      <p style={{ fontSize: "0.82rem", color: "var(--text-muted)", marginBottom: "1.25rem" }}>
        Ovoz klonlash sifati yuqori bo‘lishi uchun 5–15 soniyalik shovqinsiz va aniq gapirilgan audio tavsiya etiladi.
      </p>

      {uploadError && (
        <div className="badge badge-rose" style={{ width: "100%", padding: "0.6rem", marginBottom: "1rem", display: "block" }}>
          ⚠️ {uploadError}
        </div>
      )}

      {uploadSuccess && (
        <div className="badge badge-emerald" style={{ width: "100%", padding: "0.6rem", marginBottom: "1rem", display: "block" }}>
          ✅ {uploadSuccess}
        </div>
      )}

      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "1rem", alignItems: "stretch" }}>
        
        {/* Microphone Recording Section */}
        <div
          style={{
            border: "1px dashed var(--border-subtle)",
            borderRadius: "var(--radius-md)",
            padding: "1.25rem",
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            justifyContent: "center",
            textAlign: "center",
            backgroundColor: isRecording ? "rgba(244, 63, 94, 0.08)" : "rgba(15, 23, 42, 0.4)",
            transition: "all 0.3s ease",
          }}
        >
          <div
            className={isRecording ? "animate-recording" : ""}
            style={{
              width: "56px",
              height: "56px",
              borderRadius: "50%",
              backgroundColor: isRecording ? "var(--accent-rose)" : "var(--bg-tertiary)",
              color: "#fff",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              marginBottom: "0.75rem",
              cursor: "pointer",
            }}
            onClick={isRecording ? stopRecording : startRecording}
            title={isRecording ? "Yozishni to‘xtatish" : "Mikrofondan yozishni boshlash"}
          >
            {isRecording ? (
              <div style={{ width: "18px", height: "18px", backgroundColor: "#fff", borderRadius: "3px" }}></div>
            ) : (
              <svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3Z" />
                <path d="M19 10v2a7 7 0 0 1-14 0v-2" />
                <line x1="12" y1="19" x2="12" y2="22" />
              </svg>
            )}
          </div>

          <div style={{ fontSize: "0.9rem", fontWeight: 600, marginBottom: "0.25rem" }}>
            {isRecording ? "Yozilmoqda..." : "Mikrofon orqali yozish"}
          </div>

          <div style={{ fontFamily: "var(--font-mono)", fontSize: "0.85rem", color: isRecording ? "var(--accent-rose)" : "var(--text-dim)", marginBottom: "0.75rem" }}>
            {formatTime(recordSeconds)}
          </div>

          <button
            type="button"
            className={isRecording ? "btn-secondary" : "btn-primary"}
            style={{ fontSize: "0.82rem", padding: "0.45rem 1rem" }}
            onClick={isRecording ? stopRecording : startRecording}
          >
            {isRecording ? "To‘xtatish" : "Yozishni boshlash"}
          </button>
        </div>

        {/* File Drag and Drop Section */}
        <div
          style={{
            border: "1px dashed var(--border-subtle)",
            borderRadius: "var(--radius-md)",
            padding: "1.25rem",
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            justifyContent: "center",
            textAlign: "center",
            backgroundColor: "rgba(15, 23, 42, 0.4)",
            cursor: "pointer",
          }}
          onClick={() => fileInputRef.current?.click()}
        >
          <input
            type="file"
            ref={fileInputRef}
            onChange={handleFileChange}
            accept=".wav,.mp3,.ogg,.m4a"
            style={{ display: "none" }}
          />

          <div
            style={{
              width: "56px",
              height: "56px",
              borderRadius: "50%",
              backgroundColor: "var(--bg-tertiary)",
              color: "var(--accent-cyan)",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              marginBottom: "0.75rem",
            }}
          >
            <svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
              <polyline points="17 8 12 3 7 8" />
              <line x1="12" y1="3" x2="12" y2="15" />
            </svg>
          </div>

          <div style={{ fontSize: "0.9rem", fontWeight: 600, marginBottom: "0.25rem" }}>
            Audio faylni yuklash
          </div>

          <div style={{ fontSize: "0.8rem", color: "var(--text-dim)", marginBottom: "0.75rem" }}>
            WAV yoki MP3 (maksimal 25MB)
          </div>

          <button
            type="button"
            className="btn-secondary"
            style={{ fontSize: "0.82rem", padding: "0.45rem 1rem" }}
            onClick={(e) => {
              e.stopPropagation();
              fileInputRef.current?.click();
            }}
          >
            Faylni tanlash
          </button>
        </div>

      </div>

      {/* Audio Playback Preview */}
      {audioUrl && (
        <div
          style={{
            marginTop: "1.25rem",
            padding: "0.85rem",
            borderRadius: "var(--radius-md)",
            backgroundColor: "rgba(15, 23, 42, 0.7)",
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            flexWrap: "wrap",
            gap: "0.75rem",
          }}
        >
          <div style={{ display: "flex", alignItems: "center", gap: "0.6rem" }}>
            <span style={{ fontSize: "1.1rem" }}>🎧</span>
            <span style={{ fontSize: "0.85rem", fontWeight: 600 }}>Namunani eshitish:</span>
          </div>

          <audio src={audioUrl} controls style={{ height: "36px", outline: "none" }} />

          {audioBlob && !uploadSuccess && (
            <button
              type="button"
              className="btn-primary"
              style={{ fontSize: "0.82rem", padding: "0.4rem 0.9rem" }}
              onClick={() => handleUpload()}
              disabled={uploading}
            >
              {uploading ? "Yuklanmoqda..." : "Serverga yuklash"}
            </button>
          )}
        </div>
      )}
    </div>
  );
};
