import React, { useEffect, useRef } from "react";

interface AudioVisualizerProps {
  analyser: AnalyserNode | null;
  isRecording: boolean;
}

export const AudioVisualizer: React.FC<AudioVisualizerProps> = ({ analyser, isRecording }) => {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const animationFrameRef = useRef<number | null>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    if (!analyser || !isRecording) {
      // Draw resting idle state when not recording
      drawIdleState(ctx, canvas.width, canvas.height);
      return;
    }

    const bufferLength = analyser.frequencyBinCount;
    const dataArray = new Uint8Array(bufferLength);

    const render = () => {
      animationFrameRef.current = requestAnimationFrame(render);
      analyser.getByteFrequencyData(dataArray);

      ctx.clearRect(0, 0, canvas.width, canvas.height);

      const width = canvas.width;
      const height = canvas.height;
      const numBars = 36;
      const step = Math.floor(bufferLength / numBars);
      const barWidth = Math.max(3, Math.floor((width - numBars * 4) / numBars));
      const centerX = width / 2;

      // Draw background glow
      const bgGradient = ctx.createRadialGradient(centerX, height / 2, 5, centerX, height / 2, width / 2);
      bgGradient.addColorStop(0, "rgba(56, 189, 248, 0.08)");
      bgGradient.addColorStop(1, "rgba(15, 23, 42, 0)");
      ctx.fillStyle = bgGradient;
      ctx.fillRect(0, 0, width, height);

      // Draw centered symmetric frequency bars
      for (let i = 0; i < numBars; i++) {
        const value = dataArray[i * step] || 0;
        const percent = value / 255;
        const minHeight = 4;
        const barHeight = Math.max(minHeight, percent * (height * 0.78));

        const x = i * (barWidth + 4) + 6;
        const y = (height - barHeight) / 2;

        // Dynamic neon gradient (Cyan -> Purple -> Coral)
        const gradient = ctx.createLinearGradient(0, y, 0, y + barHeight);
        if (percent > 0.75) {
          gradient.addColorStop(0, "#f43f5e"); // Hot peak
          gradient.addColorStop(0.5, "#a855f7");
          gradient.addColorStop(1, "#38bdf8");
        } else if (percent > 0.4) {
          gradient.addColorStop(0, "#a855f7");
          gradient.addColorStop(1, "#38bdf8");
        } else {
          gradient.addColorStop(0, "#38bdf8");
          gradient.addColorStop(1, "#0284c7");
        }

        ctx.fillStyle = gradient;
        // Rounded bar tops
        ctx.beginPath();
        if (ctx.roundRect) {
          ctx.roundRect(x, y, barWidth, barHeight, 3);
        } else {
          ctx.rect(x, y, barWidth, barHeight);
        }
        ctx.fill();
      }

      // Draw baseline center divider line
      ctx.strokeStyle = "rgba(56, 189, 248, 0.25)";
      ctx.lineWidth = 1;
      ctx.beginPath();
      ctx.moveTo(0, height / 2);
      ctx.lineTo(width, height / 2);
      ctx.stroke();
    };

    render();

    return () => {
      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current);
      }
    };
  }, [analyser, isRecording]);

  const drawIdleState = (ctx: CanvasRenderingContext2D, width: number, height: number) => {
    ctx.clearRect(0, 0, width, height);
    const numBars = 36;
    const barWidth = Math.max(3, Math.floor((width - numBars * 4) / numBars));

    ctx.fillStyle = "rgba(148, 163, 184, 0.2)";
    for (let i = 0; i < numBars; i++) {
      const x = i * (barWidth + 4) + 6;
      const barHeight = 4;
      const y = (height - barHeight) / 2;
      ctx.fillRect(x, y, barWidth, barHeight);
    }
  };

  return (
    <div style={{ width: "100%", display: "flex", flexDirection: "column", alignItems: "center" }}>
      <canvas
        ref={canvasRef}
        width={340}
        height={76}
        style={{
          width: "100%",
          maxWidth: "340px",
          height: "76px",
          borderRadius: "8px",
          backgroundColor: "rgba(10, 15, 29, 0.6)",
          border: isRecording ? "1px solid rgba(244, 63, 94, 0.35)" : "1px solid rgba(255, 255, 255, 0.08)",
          boxShadow: isRecording ? "0 0 15px rgba(244, 63, 94, 0.15)" : "none",
          transition: "border 0.3s ease, box-shadow 0.3s ease",
        }}
      />
      {isRecording && (
        <div
          style={{
            marginTop: "6px",
            display: "flex",
            alignItems: "center",
            gap: "6px",
            fontSize: "0.74rem",
            color: "#f43f5e",
            fontWeight: 600,
            letterSpacing: "0.03em",
          }}
        >
          <span
            style={{
              width: "7px",
              height: "7px",
              borderRadius: "50%",
              backgroundColor: "#f43f5e",
              animation: "pulse 1.2s infinite ease-in-out",
            }}
          />
          JONLI OVOZ SIGNALI QABUL QILINMOQDA
        </div>
      )}
    </div>
  );
};
