/** Browser logger and error telemetry reporter for frontend (TASK-LOG-4). */

type LogLevel = "DEBUG" | "INFO" | "WARN" | "ERROR";

interface TelemetryPayload {
  level: LogLevel;
  message: string;
  context?: Record<string, unknown>;
  stack?: string;
  url?: string;
  requestId?: string;
}

// In-memory deduplication set to prevent telemetry flooding
const reportedErrors = new Set<string>();

async function reportTelemetry(payload: TelemetryPayload): Promise<void> {
  const dedupeKey = `${payload.message}_${payload.url || ""}`;
  if (reportedErrors.has(dedupeKey)) {
    return;
  }
  reportedErrors.add(dedupeKey);
  // Auto-expire dedupe keys after 30 seconds
  setTimeout(() => reportedErrors.delete(dedupeKey), 30000);

  try {
    await fetch("/api/v1/audit/telemetry/", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...(payload.requestId ? { "X-Request-ID": payload.requestId } : {}),
      },
      credentials: "include",
      body: JSON.stringify({
        level: payload.level,
        message: payload.message,
        url: payload.url || window.location.href,
        stack: payload.stack || "",
        context: payload.context || {},
        user_agent: navigator.userAgent,
      }),
    });
  } catch {
    // Fail-safe: telemetry network error must never crash the UI
  }
}

export const logger = {
  debug(message: string, context?: Record<string, unknown>): void {
    if ((import.meta as unknown as { env?: { DEV?: boolean } }).env?.DEV) {
      console.debug(`%c[VoiceClone:DEBUG]`, "color: #94a3b8; font-weight: bold;", message, context || "");
    }
  },

  info(message: string, context?: Record<string, unknown>): void {
    console.info(`%c[VoiceClone:INFO]`, "color: #38bdf8; font-weight: bold;", message, context || "");
  },

  warn(message: string, context?: Record<string, unknown>): void {
    console.warn(`%c[VoiceClone:WARN]`, "color: #f59e0b; font-weight: bold;", message, context || "");
  },

  error(message: string, error?: unknown, context?: Record<string, unknown>): void {
    const stack = error instanceof Error ? error.stack : undefined;
    console.error(`%c[VoiceClone:ERROR]`, "color: #ef4444; font-weight: bold;", message, error || "", context || "");

    // Forward to backend error telemetry
    reportTelemetry({
      level: "ERROR",
      message: `${message}: ${error instanceof Error ? error.message : String(error || "")}`,
      stack,
      context,
      url: window.location.href,
    });
  },
};
