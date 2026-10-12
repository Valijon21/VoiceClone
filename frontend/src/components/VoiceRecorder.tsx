import React, { useRef, useState, useEffect } from "react";
import { api } from "../api/client";
import { AudioAsset } from "../types";
import { encodeAudioBufferToWav } from "../utils/wavEncoder";
import { AudioVisualizer } from "./AudioVisualizer";
import { logger } from "../utils/logger";

// Studio recording engine using Web Audio API (with MediaRecorder compatibility)

interface VoiceRecorderProps {
  onAudioUploaded: (asset: AudioAsset) => void;
}

export const VoiceRecorder: React.FC<VoiceRecorderProps> = ({ onAudioUploaded }) => {
  const [isRecording, setIsRecording] = useState(false);
  const [recordSeconds, setRecordSeconds] = useState(0);
  const [audioUrl, setAudioUrl] = useState<string | null>(null);
  const [audioBlob, setAudioBlob] = useState<Blob | null>(null);
  const [audioDuration, setAudioDuration] = useState<number>(0);
  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [uploadSuccess, setUploadSuccess] = useState<string | null>(null);

  // Web Audio API refs
  const audioContextRef = useRef<AudioContext | null>(null);
  const mediaStreamRef = useRef<MediaStream | null>(null);
  const analyserRef = useRef<AnalyserNode | null>(null);
  const scriptProcessorRef = useRef<ScriptProcessorNode | null>(null);
  const audioChunksRef = useRef<Float32Array[]>([]);
  const timerRef = useRef<number | null>(null);
  const fileInputRef = useRef<HTMLInputElement | null>(null);

  // Clean up audio streams and object URLs on unmount
  useEffect(() => {
    return () => {
      cleanupAudioSession();
      if (audioUrl) {
        URL.revokeObjectURL(audioUrl);
      }
    };
  }, [audioUrl]);

  const cleanupAudioSession = () => {
    if (timerRef.current) {
      clearInterval(timerRef.current);
      timerRef.current = null;
    }
    if (scriptProcessorRef.current) {
      scriptProcessorRef.current.disconnect();
      scriptProcessorRef.current = null;
    }
    if (mediaStreamRef.current) {
      mediaStreamRef.current.getTracks().forEach((track) => track.stop());
      mediaStreamRef.current = null;
    }
    if (audioContextRef.current && audioContextRef.current.state !== "closed") {
      audioContextRef.current.close().catch(() => {});
      audioContextRef.current = null;
    }
    analyserRef.current = null;
  };

  // Start live microphone recording with Web Audio API
  const startRecording = async () => {
    setUploadError(null);
    setUploadSuccess(null);
    if (audioUrl) {
      URL.revokeObjectURL(audioUrl);
      setAudioUrl(null);
    }
    setAudioBlob(null);
    setAudioDuration(0);
    audioChunksRef.current = [];

    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true,
          sampleRate: 24000,
        },
      });
      mediaStreamRef.current = stream;

      const AudioCtx = window.AudioContext || (window as unknown as { webkitAudioContext: typeof AudioContext }).webkitAudioContext;
      const audioCtx = new AudioCtx();
      audioContextRef.current = audioCtx;

      if (audioCtx.state === "suspended") {
        await audioCtx.resume();
      }

      const source = audioCtx.createMediaStreamSource(stream);

      // Create AnalyserNode for real-time frequency bar visuals
      const analyser = audioCtx.createAnalyser();
      analyser.fftSize = 256;
      analyser.smoothingTimeConstant = 0.65;
      source.connect(analyser);
      analyserRef.current = analyser;

      // Create ScriptProcessorNode for collecting raw 16-bit PCM chunks
      const bufferSize = 4096;
      const scriptProcessor = audioCtx.createScriptProcessor(bufferSize, 1, 1);
      scriptProcessorRef.current = scriptProcessor;

      scriptProcessor.onaudioprocess = (e) => {
        const inputData = e.inputBuffer.getChannelData(0);
        // Copy chunk
        audioChunksRef.current.push(new Float32Array(inputData));
      };

      // Connect script processor to keep audio graph running
      source.connect(scriptProcessor);
      scriptProcessor.connect(audioCtx.destination);

      setIsRecording(true);
      setRecordSeconds(0);

      timerRef.current = window.setInterval(() => {
        setRecordSeconds((prev) => prev + 1);
      }, 1000);

      logger.info("Microphone audio recording started successfully with Web Audio API");
    } catch (err: unknown) {
      logger.error("Failed to access microphone", err);
      setUploadError("Mikrofonga ulanishda xatolik yuz berdi. Iltimos, brauzerda mikrofon ruxsatini yoqing.");
      cleanupAudioSession();
      setIsRecording(false);
    }
  };

  // Stop recording and encode into standards-compliant 16-bit PCM WAV
  const stopRecording = () => {
    if (!isRecording) return;
    setIsRecording(false);

    if (timerRef.current) {
      clearInterval(timerRef.current);
      timerRef.current = null;
    }

    const audioCtx = audioContextRef.current;
    const rawChunks = audioChunksRef.current;

    if (!audioCtx || rawChunks.length === 0) {
      cleanupAudioSession();
      setUploadError("Audio signali yozilmadi. Iltimos, qaytadan urinib ko'ring.");
      return;
    }

    try {
      // Calculate total sample count
      let totalSamples = 0;
      for (const chunk of rawChunks) {
        totalSamples += chunk.length;
      }

      // Merge Float32Array chunks into single continuous buffer
      const mergedSamples = new Float32Array(totalSamples);
      let offset = 0;
      for (const chunk of rawChunks) {
        mergedSamples.set(chunk, offset);
        offset += chunk.length;
      }

      // Create AudioBuffer
      const sampleRate = audioCtx.sampleRate;
      const audioBuffer = audioCtx.createBuffer(1, totalSamples, sampleRate);
      audioBuffer.copyToChannel(mergedSamples, 0);

      // Encode into clean, standard 16-bit PCM WAV Blob
      const wavBlob = encodeAudioBufferToWav(audioBuffer);
      const durationSec = Math.round((totalSamples / sampleRate) * 10) / 10;

      setAudioBlob(wavBlob);
      setAudioDuration(durationSec);

      const url = URL.createObjectURL(wavBlob);
      setAudioUrl(url);

      logger.info(`Recorded WAV encoded successfully: ${wavBlob.size} bytes, ${durationSec}s at ${sampleRate}Hz`);
    } catch (err: unknown) {
      logger.error("Failed to encode WAV audio buffer", err);
      setUploadError("Ovozni WAV formatiga o'tkazishda xatolik yuz berdi.");
    } finally {
      cleanupAudioSession();
    }
  };

  // Upload recorded blob or chosen file to backend
  const handleUpload = async (fileToUpload?: File) => {
    setUploadError(null);
    setUploadSuccess(null);
    setUploading(true);

    try {
      let file: File;
      if (fileToUpload) {
        file = fileToUpload;
      } else if (audioBlob) {
        file = new File([audioBlob], `recorded_voice_${Date.now()}.wav`, { type: "audio/wav" });
      } else {
        throw new Error("Yuklash uchun audio topilmadi.");
      }

      if (file.size > 25 * 1024 * 1024) {
        throw new Error("Fayl hajmi 25 MB dan oshmasligi kerak.");
      }

      const asset = await api.uploadAudio(file, "REFERENCE_VOICE");
      setUploadSuccess(`Audio muvaffaqiyatli saqlandi: ${file.name}`);
      onAudioUploaded(asset);
    } catch (err: unknown) {
      const errObj = err as { detail?: string; message?: string };
      const msg = errObj?.detail || errObj?.message || "Audio yuklashda xatolik yuz berdi.";
      setUploadError(msg);
    } finally {
      setUploading(false);
    }
  };

  // File drag & drop handler
  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      if (audioUrl) {
        URL.revokeObjectURL(audioUrl);
      }
      setAudioUrl(URL.createObjectURL(file));
      setAudioBlob(file);
      setAudioDuration(0);
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
        <span className="badge badge-indigo">16-bit PCM WAV (Studio)</span>
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

      <div style={{ display: "grid", gridTemplateColumns: "1.2fr 0.8fr", gap: "1rem", alignItems: "stretch" }}>
        
        {/* Real-time Studio Microphone Recording Section */}
        <div
          style={{
            border: isRecording ? "1px solid rgba(244, 63, 94, 0.4)" : "1px dashed var(--border-subtle)",
            borderRadius: "var(--radius-md)",
            padding: "1.25rem",
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            justifyContent: "center",
            textAlign: "center",
            backgroundColor: isRecording ? "rgba(244, 63, 94, 0.05)" : "rgba(15, 23, 42, 0.4)",
            boxShadow: isRecording ? "0 0 25px rgba(244, 63, 94, 0.15) inset" : "none",
            transition: "all 0.3s ease",
          }}
        >
          {/* Real-time Visualizer Canvas */}
          <div style={{ width: "100%", marginBottom: "0.85rem" }}>
            <AudioVisualizer analyser={analyserRef.current} isRecording={isRecording} />
          </div>

          {/* Recording Timer and Status */}
          <div style={{ display: "flex", alignItems: "center", gap: "0.75rem", marginBottom: "0.85rem" }}>
            <div
              className={isRecording ? "animate-recording" : ""}
              style={{
                width: "48px",
                height: "48px",
                borderRadius: "50%",
                backgroundColor: isRecording ? "var(--accent-rose)" : "var(--bg-tertiary)",
                color: "#fff",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                cursor: "pointer",
                boxShadow: isRecording ? "0 0 15px rgba(244, 63, 94, 0.5)" : "none",
                transition: "all 0.2s ease",
              }}
              onClick={isRecording ? stopRecording : startRecording}
              title={isRecording ? "Yozishni to‘xtatish" : "Mikrofondan yozishni boshlash"}
            >
              {isRecording ? (
                <div style={{ width: "16px", height: "16px", backgroundColor: "#fff", borderRadius: "3px" }} />
              ) : (
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3Z" />
                  <path d="M19 10v2a7 7 0 0 1-14 0v-2" />
                  <line x1="12" y1="19" x2="12" y2="22" />
                </svg>
              )}
            </div>

            <div style={{ textAlign: "left" }}>
              <div style={{ fontSize: "0.88rem", fontWeight: 700, color: isRecording ? "#f43f5e" : "var(--text-main)" }}>
                {isRecording ? "Ovoz yozilmoqda..." : "Mikrofon orqali yozish"}
              </div>
              <div style={{ fontFamily: "var(--font-mono)", fontSize: "0.95rem", fontWeight: 600, color: isRecording ? "#f43f5e" : "var(--text-dim)" }}>
                {formatTime(recordSeconds)}
                {isRecording && <span style={{ fontSize: "0.75rem", color: "var(--text-muted)", marginLeft: "6px" }}>/ 00:15 tavsiya</span>}
              </div>
            </div>
          </div>

          {/* Action button */}
          <button
            type="button"
            className={isRecording ? "btn-secondary" : "btn-primary"}
            style={{
              fontSize: "0.85rem",
              padding: "0.5rem 1.4rem",
              borderRadius: "20px",
              fontWeight: 600,
              backgroundColor: isRecording ? "#f43f5e" : undefined,
              color: isRecording ? "#fff" : undefined,
              border: "none",
            }}
            onClick={isRecording ? stopRecording : startRecording}
          >
            {isRecording ? "⏹️ Yozishni to‘xtatish" : "🎙️ Yozishni boshlash"}
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
            transition: "all 0.2s ease",
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
              width: "48px",
              height: "48px",
              borderRadius: "50%",
              backgroundColor: "var(--bg-tertiary)",
              color: "var(--accent-cyan)",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              marginBottom: "0.6rem",
            }}
          >
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
              <polyline points="17 8 12 3 7 8" />
              <line x1="12" y1="3" x2="12" y2="15" />
            </svg>
          </div>

          <div style={{ fontSize: "0.88rem", fontWeight: 600, marginBottom: "0.2rem" }}>
            Tayyor audio faylni yuklash
          </div>

          <div style={{ fontSize: "0.78rem", color: "var(--text-dim)", marginBottom: "0.85rem" }}>
            WAV yoki MP3 (maksimal 25MB)
          </div>

          <button
            type="button"
            className="btn-secondary"
            style={{ fontSize: "0.8rem", padding: "0.4rem 1rem", borderRadius: "18px" }}
            onClick={(e) => {
              e.stopPropagation();
              fileInputRef.current?.click();
            }}
          >
            Faylni tanlash
          </button>
        </div>

      </div>

      {/* Audio Playback & Verification Preview Section */}
      {audioUrl && (
        <div
          style={{
            marginTop: "1.25rem",
            padding: "1rem 1.25rem",
            borderRadius: "var(--radius-md)",
            backgroundColor: "rgba(15, 23, 42, 0.85)",
            border: "1px solid rgba(56, 189, 248, 0.25)",
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            flexWrap: "wrap",
            gap: "1rem",
            boxShadow: "0 4px 15px rgba(0, 0, 0, 0.3)",
          }}
        >
          <div style={{ display: "flex", alignItems: "center", gap: "0.75rem" }}>
            <span style={{ fontSize: "1.4rem" }}>🎧</span>
            <div>
              <div style={{ fontSize: "0.88rem", fontWeight: 700, color: "#38bdf8" }}>
                Yozilgan ovoz namunasi tayyor
              </div>
              <div style={{ fontSize: "0.76rem", color: "var(--text-dim)" }}>
                {audioDuration > 0 ? `${audioDuration} soniya • ` : ""}16-bit PCM WAV formati
              </div>
            </div>
          </div>

          {/* Standard HTML5 Audio Player */}
          <audio
            src={audioUrl}
            controls
            style={{
              height: "38px",
              outline: "none",
              borderRadius: "20px",
              flex: "1 1 250px",
              maxWidth: "380px",
            }}
          />

          <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
            <button
              type="button"
              className="btn-secondary"
              style={{ fontSize: "0.82rem", padding: "0.45rem 0.9rem", borderRadius: "6px" }}
              onClick={startRecording}
              disabled={isRecording || uploading}
              title="Avvalgi ovozni bekor qilib, yangitdan yozish"
            >
              🔄 Qayta yozish
            </button>

            {audioBlob && !uploadSuccess && (
              <button
                type="button"
                className="btn-primary"
                style={{
                  fontSize: "0.82rem",
                  padding: "0.45rem 1.1rem",
                  borderRadius: "6px",
                  fontWeight: 600,
                  backgroundColor: "#38bdf8",
                  color: "#0f172a",
                }}
                onClick={() => handleUpload()}
                disabled={uploading}
              >
                {uploading ? "Yuklanmoqda..." : "💾 Ovozni saqlash"}
              </button>
            )}
          </div>
        </div>
      )}
    </div>
  );
};
