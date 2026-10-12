import React, { useRef, useState, useEffect, useCallback } from "react";
import { api } from "../api/client";
import { AudioAsset } from "../types";
import { encodeAudioBufferToWav } from "../utils/wavEncoder";
import { AudioVisualizer } from "./AudioVisualizer";
import { logger } from "../utils/logger";

// Studio recording engine with Device Selector, Live Mic Tester, and MediaRecorder

interface AudioDeviceOption {
  deviceId: string;
  label: string;
  isVirtual: boolean;
}

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

  // Audio Device selection & Live Mic Meter states
  const [audioDevices, setAudioDevices] = useState<AudioDeviceOption[]>([]);
  const [selectedDeviceId, setSelectedDeviceId] = useState<string>("");
  const [isTestingMic, setIsTestingMic] = useState(false);
  const [testVolume, setTestVolume] = useState(0); // 0 - 100%
  const [zeroSignalWarning, setZeroSignalWarning] = useState(false);

  // Audio streams & Web Audio API refs
  const audioContextRef = useRef<AudioContext | null>(null);
  const mediaStreamRef = useRef<MediaStream | null>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const analyserRef = useRef<AnalyserNode | null>(null);
  const muteGainRef = useRef<GainNode | null>(null);
  const recordedChunksRef = useRef<Blob[]>([]);
  const timerRef = useRef<number | null>(null);
  const fileInputRef = useRef<HTMLInputElement | null>(null);

  // Live tester refs
  const testStreamRef = useRef<MediaStream | null>(null);
  const testCtxRef = useRef<AudioContext | null>(null);
  const testAnimFrameRef = useRef<number | null>(null);

  // Enumerate available microphones
  const loadAudioDevices = useCallback(async (promptPermission = false) => {
    try {
      if (promptPermission) {
        // Quick permission prompt to get actual device labels
        const tempStream = await navigator.mediaDevices.getUserMedia({ audio: true });
        tempStream.getTracks().forEach((t) => t.stop());
      }

      const devices = await navigator.mediaDevices.enumerateDevices();
      const audioInputs = devices
        .filter((d) => d.kind === "audioinput")
        .map((d, index) => {
          const label = d.label || `Mikrofon #${index + 1}`;
          const isVirtual = /voicemod|virtual|stereo mix|aux/i.test(label);
          return {
            deviceId: d.deviceId,
            label,
            isVirtual,
          };
        });

      // Sort: Real physical microphones first, virtual/mix at the end
      audioInputs.sort((a, b) => {
        if (a.isVirtual === b.isVirtual) return 0;
        return a.isVirtual ? 1 : -1;
      });

      setAudioDevices(audioInputs);

      // Auto-select preferred device if current selection is empty or virtual
      if (audioInputs.length > 0) {
        setSelectedDeviceId((prev) => {
          if (prev && audioInputs.some((d) => d.deviceId === prev)) {
            return prev;
          }
          // Pick the first non-virtual device if available
          const preferred = audioInputs.find((d) => !d.isVirtual) || audioInputs[0];
          return preferred.deviceId;
        });
      }
    } catch (err) {
      logger.warn("Failed to enumerate audio input devices", { error: String(err) });
    }
  }, []);

  useEffect(() => {
    loadAudioDevices(false);
  }, [loadAudioDevices]);

  // Clean up audio streams and object URLs on unmount
  useEffect(() => {
    return () => {
      cleanupAudioSession();
      stopMicTest();
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
    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== "inactive") {
      try {
        mediaRecorderRef.current.stop();
      } catch {
        // Ignored
      }
      mediaRecorderRef.current = null;
    }
    if (mediaStreamRef.current) {
      mediaStreamRef.current.getTracks().forEach((track) => track.stop());
      mediaStreamRef.current = null;
    }
    if (muteGainRef.current) {
      muteGainRef.current.disconnect();
      muteGainRef.current = null;
    }
    if (audioContextRef.current && audioContextRef.current.state !== "closed") {
      audioContextRef.current.close().catch(() => {});
      audioContextRef.current = null;
    }
    analyserRef.current = null;
  };

  // Live Microphone Test (VU Meter)
  const stopMicTest = () => {
    if (testAnimFrameRef.current) {
      cancelAnimationFrame(testAnimFrameRef.current);
      testAnimFrameRef.current = null;
    }
    if (testStreamRef.current) {
      testStreamRef.current.getTracks().forEach((t) => t.stop());
      testStreamRef.current = null;
    }
    if (testCtxRef.current && testCtxRef.current.state !== "closed") {
      testCtxRef.current.close().catch(() => {});
      testCtxRef.current = null;
    }
    setIsTestingMic(false);
    setTestVolume(0);
  };

  const startMicTest = async () => {
    stopMicTest();
    cleanupAudioSession();
    setUploadError(null);

    try {
      const constraints: MediaStreamConstraints = {
        audio: selectedDeviceId
          ? {
              deviceId: { exact: selectedDeviceId },
              echoCancellation: true,
              noiseSuppression: true,
              autoGainControl: true,
            }
          : {
              echoCancellation: true,
              noiseSuppression: true,
              autoGainControl: true,
            },
      };

      const stream = await navigator.mediaDevices.getUserMedia(constraints);
      testStreamRef.current = stream;

      // Update devices list with fresh labels if needed
      loadAudioDevices(false);

      const AudioCtx = window.AudioContext || (window as unknown as { webkitAudioContext: typeof AudioContext }).webkitAudioContext;
      const audioCtx = new AudioCtx();
      testCtxRef.current = audioCtx;

      const source = audioCtx.createMediaStreamSource(stream);
      const analyser = audioCtx.createAnalyser();
      analyser.fftSize = 256;
      source.connect(analyser);

      const pcmData = new Float32Array(analyser.fftSize);

      const checkVolume = () => {
        analyser.getFloatTimeDomainData(pcmData);
        let sumSquares = 0;
        let peak = 0;
        for (let i = 0; i < pcmData.length; i++) {
          const val = Math.abs(pcmData[i]);
          if (val > peak) peak = val;
          sumSquares += val * val;
        }
        const rms = Math.sqrt(sumSquares / pcmData.length);
        // Exponential gain curve to display intuitive 0-100% volume
        const computedPercent = Math.min(100, Math.round(Math.pow(rms, 0.6) * 160));
        setTestVolume(computedPercent);

        testAnimFrameRef.current = requestAnimationFrame(checkVolume);
      };

      setIsTestingMic(true);
      checkVolume();
    } catch (err) {
      logger.error("Failed to start mic test", err);
      setUploadError("Mikrofonni sinab ko'rishda xatolik yuz berdi. Qurilma ruxsatini tekshiring.");
      stopMicTest();
    }
  };

  // Start live microphone recording with hardware MediaRecorder + AnalyserNode
  const startRecording = async () => {
    stopMicTest();
    setUploadError(null);
    setUploadSuccess(null);
    setZeroSignalWarning(false);
    if (audioUrl) {
      URL.revokeObjectURL(audioUrl);
      setAudioUrl(null);
    }
    setAudioBlob(null);
    setAudioDuration(0);
    recordedChunksRef.current = [];

    try {
      const constraints: MediaStreamConstraints = {
        audio: selectedDeviceId
          ? {
              deviceId: { exact: selectedDeviceId },
              echoCancellation: true,
              noiseSuppression: true,
              autoGainControl: true,
            }
          : {
              echoCancellation: true,
              noiseSuppression: true,
              autoGainControl: true,
            },
      };

      const stream = await navigator.mediaDevices.getUserMedia(constraints);
      mediaStreamRef.current = stream;

      // Check track properties
      const track = stream.getAudioTracks()[0];
      if (track) {
        logger.info(`Microphone track active: "${track.label}" (muted=${track.muted}, readyState=${track.readyState})`);
        if (track.muted) {
          setUploadError("Diqqat: Ushbu mikrofon operatsion tizimda 'MUTED' (o'chirilgan). Windows sozlamalari yoki klaviaturadagi mikrofon tugmasini tekshiring.");
        }
      }

      // 1. Setup Web Audio API exclusively for the real-time visualizer
      const AudioCtx = window.AudioContext || (window as unknown as { webkitAudioContext: typeof AudioContext }).webkitAudioContext;
      const audioCtx = new AudioCtx();
      audioContextRef.current = audioCtx;

      if (audioCtx.state === "suspended") {
        await audioCtx.resume();
      }

      const source = audioCtx.createMediaStreamSource(stream);
      const analyser = audioCtx.createAnalyser();
      analyser.fftSize = 256;
      analyser.smoothingTimeConstant = 0.55;
      source.connect(analyser);
      analyserRef.current = analyser;

      // Connect analyser to silent gain node so Web Audio graph runs actively
      // without looping back audio to speakers (which causes echo cancellation muting)
      const muteGain = audioCtx.createGain();
      muteGain.gain.value = 0;
      analyser.connect(muteGain);
      muteGain.connect(audioCtx.destination);
      muteGainRef.current = muteGain;

      // 2. Setup standard MediaRecorder
      let mimeType = "";
      const candidates = [
        "audio/webm;codecs=opus",
        "audio/webm",
        "audio/ogg;codecs=opus",
        "audio/mp4",
      ];
      for (const cand of candidates) {
        if (typeof MediaRecorder !== "undefined" && MediaRecorder.isTypeSupported && MediaRecorder.isTypeSupported(cand)) {
          mimeType = cand;
          break;
        }
      }

      const recorderOptions = mimeType ? { mimeType } : undefined;
      const mediaRecorder = new MediaRecorder(stream, recorderOptions);
      mediaRecorderRef.current = mediaRecorder;

      mediaRecorder.ondataavailable = (event: BlobEvent) => {
        if (event.data && event.data.size > 0) {
          recordedChunksRef.current.push(event.data);
        }
      };

      mediaRecorder.start(200); // 200ms slice chunks

      setIsRecording(true);
      setRecordSeconds(0);

      timerRef.current = window.setInterval(() => {
        setRecordSeconds((prev) => prev + 1);
      }, 1000);

      logger.info(`Microphone recording started with MediaRecorder (${mimeType || "default"}) using device "${track?.label || "default"}"`);
    } catch (err: unknown) {
      logger.error("Failed to access microphone", err);
      setUploadError("Mikrofonga ulanishda xatolik yuz berdi. Iltimos, brauzerda mikrofon ruxsatini yoqing yoki boshqa mikrofonni tanlang.");
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

    const mediaRecorder = mediaRecorderRef.current;
    if (!mediaRecorder || mediaRecorder.state === "inactive") {
      cleanupAudioSession();
      return;
    }

    mediaRecorder.onstop = async () => {
      const chunks = recordedChunksRef.current;
      if (chunks.length === 0) {
        setUploadError("Audio signali yozilmadi. Iltimos, qaytadan urinib ko'ring.");
        cleanupAudioSession();
        return;
      }

      try {
        const rawBlob = new Blob(chunks, { type: mediaRecorder.mimeType || "audio/webm" });
        logger.info(`Raw audio recorded: ${rawBlob.size} bytes (${chunks.length} chunks)`);

        // Decode into AudioBuffer using AudioContext
        const arrayBuffer = await rawBlob.arrayBuffer();
        const AudioCtx = window.AudioContext || (window as unknown as { webkitAudioContext: typeof AudioContext }).webkitAudioContext;
        const decodeCtx = new AudioCtx();
        const decodedBuffer = await decodeCtx.decodeAudioData(arrayBuffer);

        // Check audio signal energy / peak amplitude
        const channelData = decodedBuffer.getChannelData(0);
        let maxPeak = 0;
        let sumSquares = 0;
        for (let i = 0; i < channelData.length; i++) {
          const val = Math.abs(channelData[i]);
          if (val > maxPeak) maxPeak = val;
          sumSquares += val * val;
        }
        const rms = Math.sqrt(sumSquares / channelData.length);
        const durationSec = Math.round(decodedBuffer.duration * 10) / 10;

        logger.info(`Audio analysis: peak=${maxPeak.toFixed(3)}, rms=${rms.toFixed(4)}, duration=${durationSec}s, rate=${decodedBuffer.sampleRate}Hz`);

        // Convert to standard 16-bit PCM WAV
        const wavBlob = encodeAudioBufferToWav(decodedBuffer);
        setAudioBlob(wavBlob);
        setAudioDuration(durationSec);

        const url = URL.createObjectURL(wavBlob);
        setAudioUrl(url);

        if (maxPeak < 0.005) {
          setZeroSignalWarning(true);
          setUploadError(
            "Diqqat: Ovoz signali mutlaq 0 bo'ldi. Tanlangan mikrofoningiz o'chiq bo'lishi yoki virtual (Voicemod) qurilma tanlangan bo'lishi mumkin. Iltimos, pastdagi mikrofon tanlovidan boshqasini tanlang."
          );
        } else {
          setZeroSignalWarning(false);
          setUploadError(null);
        }

        logger.info(`WAV encoded successfully: ${wavBlob.size} bytes, ${durationSec}s at ${decodedBuffer.sampleRate}Hz`);
        decodeCtx.close().catch(() => {});
      } catch (err) {
        logger.warn("WAV transcode failed, falling back to raw recording blob", { error: String(err) });
        const fallbackBlob = new Blob(chunks, { type: mediaRecorder.mimeType || "audio/webm" });
        setAudioBlob(fallbackBlob);
        setAudioDuration(recordSeconds);
        setAudioUrl(URL.createObjectURL(fallbackBlob));
      } finally {
        cleanupAudioSession();
      }
    };

    mediaRecorder.stop();
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
        const ext = audioBlob.type.includes("wav") ? "wav" : "webm";
        file = new File([audioBlob], `recorded_voice_${Date.now()}.${ext}`, { type: audioBlob.type });
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

      <p style={{ fontSize: "0.82rem", color: "var(--text-muted)", marginBottom: "1rem" }}>
        Ovoz klonlash sifati yuqori bo‘lishi uchun 5–15 soniyalik shovqinsiz va aniq gapirilgan audio tavsiya etiladi.
      </p>

      {/* Hardware Microphone Device Selector Bar */}
      <div
        style={{
          padding: "0.85rem 1rem",
          borderRadius: "var(--radius-md)",
          backgroundColor: "rgba(15, 23, 42, 0.6)",
          border: "1px solid var(--border-subtle)",
          marginBottom: "1.25rem",
          display: "flex",
          flexDirection: "column",
          gap: "0.6rem",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", flexWrap: "wrap", gap: "0.5rem" }}>
          <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", fontSize: "0.82rem", fontWeight: 600 }}>
            <span>🎧 Tanlangan mikrofon:</span>
            <select
              value={selectedDeviceId}
              onChange={(e) => {
                setSelectedDeviceId(e.target.value);
                if (isTestingMic) {
                  stopMicTest();
                }
              }}
              style={{
                backgroundColor: "var(--bg-secondary)",
                color: "var(--text-main)",
                border: "1px solid var(--border-subtle)",
                borderRadius: "6px",
                padding: "0.35rem 0.6rem",
                fontSize: "0.82rem",
                outline: "none",
                maxWidth: "260px",
              }}
            >
              {audioDevices.length === 0 && <option value="">Tizim birlamchi mikrofoni</option>}
              {audioDevices.map((d) => (
                <option key={d.deviceId} value={d.deviceId}>
                  {d.isVirtual ? `⚠️ ${d.label} (Virtual)` : `🎙️ ${d.label}`}
                </option>
              ))}
            </select>
          </div>

          <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
            <button
              type="button"
              className={isTestingMic ? "btn-secondary" : "btn-primary"}
              style={{
                fontSize: "0.78rem",
                padding: "0.35rem 0.75rem",
                borderRadius: "6px",
                backgroundColor: isTestingMic ? "var(--accent-rose)" : undefined,
                color: isTestingMic ? "#fff" : undefined,
              }}
              onClick={isTestingMic ? stopMicTest : startMicTest}
              disabled={isRecording}
              title="Mikrofoningiz ovozni olayotganini yozishdan oldin tekshiring"
            >
              {isTestingMic ? "⏹️ Testni to‘xtatish" : "🔊 Mikrofonni tekshirish (Test)"}
            </button>

            <button
              type="button"
              className="btn-secondary"
              style={{ fontSize: "0.78rem", padding: "0.35rem 0.65rem", borderRadius: "6px" }}
              onClick={() => loadAudioDevices(true)}
              title="Qurilmalar ro‘yxatini yangilash"
            >
              🔄
            </button>
          </div>
        </div>

        {/* Live VU-Meter during Test */}
        {isTestingMic && (
          <div style={{ marginTop: "0.3rem" }}>
            <div style={{ display: "flex", justifyContent: "space-between", fontSize: "0.74rem", marginBottom: "0.25rem" }}>
              <span style={{ color: testVolume > 5 ? "var(--accent-cyan)" : "var(--accent-rose)", fontWeight: 600 }}>
                {testVolume > 5 ? "✅ Ovoz signali aniq sezilmoqda" : "⚠️ Ovoz sezilmadi (0%) - gapirib ko‘ring yoki boshqa mikrofon tanlang"}
              </span>
              <span style={{ fontFamily: "var(--font-mono)", fontWeight: 700 }}>{testVolume}%</span>
            </div>
            <div
              style={{
                width: "100%",
                height: "8px",
                backgroundColor: "rgba(255, 255, 255, 0.1)",
                borderRadius: "4px",
                overflow: "hidden",
              }}
            >
              <div
                style={{
                  width: `${testVolume}%`,
                  height: "100%",
                  backgroundColor: testVolume > 70 ? "#f43f5e" : testVolume > 20 ? "#38bdf8" : "#22c55e",
                  transition: "width 0.08s ease-out",
                  borderRadius: "4px",
                }}
              />
            </div>
          </div>
        )}
      </div>

      {uploadError && (
        <div className="badge badge-rose" style={{ width: "100%", padding: "0.7rem", marginBottom: "1rem", display: "block", textAlign: "left", lineHeight: "1.4" }}>
          ⚠️ {uploadError}
        </div>
      )}

      {zeroSignalWarning && (
        <div
          style={{
            backgroundColor: "rgba(244, 63, 94, 0.1)",
            border: "1px solid rgba(244, 63, 94, 0.4)",
            borderRadius: "var(--radius-md)",
            padding: "0.85rem",
            marginBottom: "1rem",
            fontSize: "0.8rem",
            color: "#fecdd3",
            lineHeight: "1.5",
          }}
        >
          <strong>💡 Mikrofon 0% signal berishini bartaraf qilish bo‘yicha qo‘llanma:</strong>
          <ul style={{ paddingLeft: "1.2rem", marginTop: "0.35rem", marginBottom: 0 }}>
            <li>Yuqoridagi <strong>"Tanlangan mikrofon"</strong> ro‘yxatidan <em>Voicemod</em> emas, noutbukning o‘z mikrofoni (Intel Smart Sound yoki Realtek)ni tanlang.</li>
            <li>Klaviaturangizda mikrofonni o‘chirish tugmasi (masalan <code>F4</code> yoki <code>Fn+F4</code>) yonib turmaganligini tekshiring.</li>
            <li>Windows Maxfiylik sozlamalarida (<em>Settings → Privacy & Security → Microphone</em>) brauzerga ruxsat yoqilganligiga ishonch hosil qiling.</li>
          </ul>
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
