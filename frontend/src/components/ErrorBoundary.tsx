import { Component, ErrorInfo, ReactNode } from "react";
import { logger } from "../utils/logger";

interface Props {
  children: ReactNode;
}

interface State {
  hasError: boolean;
  errorMessage: string;
}

export class ErrorBoundary extends Component<Props, State> {
  public state: State = {
    hasError: false,
    errorMessage: "",
  };

  public static getDerivedStateFromError(error: Error): State {
    return { hasError: true, errorMessage: error.message };
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    logger.error("REACT_RENDER_CRASH", error, {
      componentStack: errorInfo.componentStack,
    });
  }

  public render() {
    if (this.state.hasError) {
      return (
        <div
          className="glass-panel"
          style={{
            margin: "2rem auto",
            maxWidth: "600px",
            padding: "2rem",
            textAlign: "center",
            border: "1px solid rgba(239, 68, 68, 0.3)",
          }}
        >
          <h2 style={{ color: "#ef4444", marginBottom: "1rem" }}>
            Kutilmagan xatolik yuz berdi
          </h2>
          <p style={{ color: "#94a3b8", marginBottom: "1.5rem" }}>
            Dasturda xatolik yuz berdi. Xatolik tafsilotlari server audit logiga avtomatik yozib olindi.
          </p>
          <div
            style={{
              padding: "0.75rem",
              background: "rgba(0, 0, 0, 0.4)",
              borderRadius: "6px",
              fontFamily: "monospace",
              fontSize: "0.85rem",
              color: "#fca5a5",
              marginBottom: "1.5rem",
              wordBreak: "break-all",
            }}
          >
            {this.state.errorMessage || "Unknown application error"}
          </div>
          <button
            onClick={() => window.location.reload()}
            className="btn btn-primary"
            style={{
              background: "#38bdf8",
              color: "#0f172a",
              border: "none",
              padding: "0.6rem 1.5rem",
              borderRadius: "6px",
              cursor: "pointer",
              fontWeight: 600,
            }}
          >
            Sahifani qayta yuklash
          </button>
        </div>
      );
    }

    return this.props.children;
  }
}
