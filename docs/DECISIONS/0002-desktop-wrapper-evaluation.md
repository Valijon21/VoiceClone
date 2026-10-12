# ADR-0002: Desktop Application Wrapper Evaluation (VC-084)

> **Status:** ACCEPTED  
> **Date:** 2026-10-12  
> **Deciders:** Senior Architect, Fullstack Lead, Inference Engineer

---

## 1. Context & Problem Statement

For local and offline execution (`VC-080` - `VC-084`), does VoiceClone AI require a standalone desktop wrapper (such as Tauri or Electron with a native `.exe` installer), or is the responsive React Web App served locally via unified scripts and Docker sufficient for the MVP?

---

## 2. Options Considered

### Option A: Electron Desktop Wrapper
- **Pros:** Full desktop integration, bundled Chromium.
- **Cons:** Bloated distribution (> 150 MB binary), high memory footprint (300+ MB RAM overhead), bundling Python 3.11 with 2+ GB PyTorch/CUDA wheels inside an installer creates severe packaging fragility on Windows.

### Option B: Tauri (Rust + Webview2) Wrapper
- **Pros:** Lightweight (< 15 MB), modern security model, native Windows Webview2 support.
- **Cons:** Requires user to have Rust toolchain for development. Still requires spawning and managing Python/CUDA background child processes; adds build complexity without providing additional AI capability.

### Option C: Responsive Web App + Local Orchestration Profile (Recommended)
- **Pros:**
  - 100% code reuse between local execution and cloud/SaaS deployment.
  - Zero packaging overhead.
  - Unified local startup scripts (`scripts/start_local.ps1`, `scripts/start_local.sh`, and `infra/docker-compose.yml`) cleanly start the services.
  - Browser provides native `MediaRecorder`, audio playback, and clean separation of concerns.
- **Cons:** Requires user to open browser (`http://localhost:5173` or `http://localhost:8000`).

---

## 3. Decision Outcome

**Decision:** Adopt **Option C (Responsive Web App + Local Startup Profile)** for MVP (Phase 08).

### Rationale:
1. The AI inference service and Django backend are already modular and containerized.
2. Embedding a 6GB PyTorch/CUDA environment inside a single desktop installer is anti-pattern for rapid iteration and creates high failure rates across diverse Windows GPU driver versions.
3. If an enterprise offline client requests a single-click desktop package, Tauri will be evaluated in Phase 11 under a dedicated B2B packaging scope.
