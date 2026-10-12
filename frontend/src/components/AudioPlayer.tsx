import React, { useEffect, useRef, useState } from "react";

interface AudioPlayerProps {
  src: string;
  title?: string;
  filename?: string;
  durationSec?: number;
}

export const AudioPlayer: React.FC<AudioPlayerProps> = ({
  src,
  title = "Generatsiya qilingan nutq",
  filename = "synthesized_voice.wav",
  durationSec,
}) => {
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(durationSec || 0);

  useEffect(() => {
    const audio = audioRef.current;
    if (!audio) return;

    const handleTimeUpdate = () => setCurrentTime(audio.currentTime);
    const handleLoadedMetadata = () => {
      if (audio.duration && !isNaN(audio.duration)) {
        setDuration(audio.duration);
      }
    };
    const handleEnded = () => setIsPlaying(false);

    audio.addEventListener("timeupdate", handleTimeUpdate);
    audio.addEventListener("loadedmetadata", handleLoadedMetadata);
    audio.addEventListener("ended", handleEnded);

    return () => {
      audio.removeEventListener("timeupdate", handleTimeUpdate);
      audio.removeEventListener("loadedmetadata", handleLoadedMetadata);
      audio.removeEventListener("ended", handleEnded);
    };
  }, [src]);

  const togglePlay = () => {
    if (!audioRef.current) return;
    if (isPlaying) {
      audioRef.current.pause();
      setIsPlaying(false);
    } else {
      audioRef.current.play();
      setIsPlaying(true);
    }
  };

  const handleSeek = (e: React.ChangeEvent<HTMLInputElement>) => {
    const time = parseFloat(e.target.value);
    setCurrentTime(time);
    if (audioRef.current) {
      audioRef.current.currentTime = time;
    }
  };

  const formatTime = (secs: number) => {
    if (isNaN(secs) || secs < 0) return "00:00";
    const m = Math.floor(secs / 60);
    const s = Math.floor(secs % 60);
    return `${m.toString().padStart(2, "0")}:${s.toString().padStart(2, "0")}`;
  };

  return (
    <div className="glass-panel" style={{ padding: "1.5rem" }}>
      <audio ref={audioRef} src={src} preload="metadata" />

      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "1rem" }}>
        <div style={{ display: "flex", alignItems: "center", gap: "0.6rem" }}>
          <div
            style={{
              width: "36px",
              height: "36px",
              borderRadius: "50%",
              backgroundColor: "rgba(99, 102, 241, 0.15)",
              color: "var(--accent-primary)",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
            }}
          >
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
              <polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5" />
              <path d="M19.07 4.93a10 10 0 0 1 0 14.14M15.54 8.46a5 5 0 0 1 0 7.07" />
            </svg>
          </div>
          <div>
            <div style={{ fontSize: "0.95rem", fontWeight: 700 }}>{title}</div>
            <div style={{ fontSize: "0.75rem", color: "var(--text-dim)" }}>WAV Audio • 24 kHz / 16-bit</div>
          </div>
        </div>

        {/* Download WAV button */}
        <a
          href={src}
          download={filename}
          className="btn-secondary"
          style={{ padding: "0.45rem 0.9rem", fontSize: "0.82rem", textDecoration: "none" }}
          title="Audio faylni yuklab olish"
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
            <polyline points="7 10 12 15 17 10" />
            <line x1="12" y1="15" x2="12" y2="3" />
          </svg>
          WAV yuklab olish
        </a>
      </div>

      {/* Waveform graphic visualization bars */}
      <div
        className="waveform-visualizer"
        style={{
          display: "flex",
          alignItems: "center",
          gap: "4px",
          height: "36px",
          marginBottom: "1rem",
          padding: "0 0.5rem",
        }}
      >
        {[20, 45, 75, 30, 85, 60, 40, 95, 70, 50, 35, 80, 65, 45, 90, 30, 60, 85, 40, 70, 55, 35, 80, 50, 30].map(
          (h, i) => {
            const isPassed = (i / 25) * (duration || 1) <= currentTime;
            return (
              <div
                key={i}
                style={{
                  flex: 1,
                  height: `${h}%`,
                  borderRadius: "2px",
                  backgroundColor: isPassed
                    ? "var(--accent-cyan)"
                    : "rgba(255, 255, 255, 0.15)",
                  transition: "all 0.15s ease",
                }}
              />
            );
          }
        )}
      </div>

      {/* Controls row */}
      <div style={{ display: "flex", alignItems: "center", gap: "1rem" }}>
        <button
          type="button"
          onClick={togglePlay}
          className="btn-primary"
          style={{
            width: "44px",
            height: "44px",
            borderRadius: "50%",
            padding: 0,
            flexShrink: 0,
          }}
          aria-label={isPlaying ? "To‘xtatish" : "Ijro etish"}
        >
          {isPlaying ? (
            <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor">
              <rect x="6" y="4" width="4" height="16" rx="1" />
              <rect x="14" y="4" width="4" height="16" rx="1" />
            </svg>
          ) : (
            <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor" style={{ marginLeft: "2px" }}>
              <polygon points="5 3 19 12 5 21 5 3" />
            </svg>
          )}
        </button>

        {/* Seek bar */}
        <input
          type="range"
          min={0}
          max={duration || 100}
          step={0.1}
          value={currentTime}
          onChange={handleSeek}
          style={{
            flex: 1,
            accentColor: "var(--accent-primary)",
            cursor: "pointer",
          }}
        />

        <div style={{ fontFamily: "var(--font-mono)", fontSize: "0.82rem", color: "var(--text-muted)", flexShrink: 0 }}>
          {formatTime(currentTime)} / {formatTime(duration)}
        </div>
      </div>
    </div>
  );
};
