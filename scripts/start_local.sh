#!/usr/bin/env bash
# VoiceClone AI — Unified Local Development & Offline Startup Script (VC-080)
set -euo pipefail

MODE="${1:-mock}"
BACKEND_PORT="${2:-8000}"
INFERENCE_PORT="${3:-8001}"

echo "=========================================================="
echo "       VoiceClone AI — Local Startup (Mode: $MODE)        "
echo "=========================================================="

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKSPACE_ROOT="$(dirname "$SCRIPT_DIR")"
cd "$WORKSPACE_ROOT"

# Cache Directories
export HF_HOME="$WORKSPACE_ROOT/.cache/huggingface"
export PIP_CACHE_DIR="$WORKSPACE_ROOT/.cache/pip"
export TORCH_HOME="$WORKSPACE_ROOT/.cache/torch"
export MODEL_CACHE_DIR="$WORKSPACE_ROOT/.cache/models"
export PYTHONPATH="$WORKSPACE_ROOT/backend:$WORKSPACE_ROOT/inference"

mkdir -p "$HF_HOME" "$PIP_CACHE_DIR" "$TORCH_HOME" "$MODEL_CACHE_DIR" "$WORKSPACE_ROOT/var/media" "$WORKSPACE_ROOT/var/logs"
echo "✓ Local cache directories verified."

PYTHON_BIN="${PYTHON_BIN:-python3}"
echo "✓ Using Python: $($PYTHON_BIN --version)"

# Migrations
echo "→ Applying Django database migrations..."
$PYTHON_BIN "$WORKSPACE_ROOT/backend/manage.py" migrate --noinput
echo "✓ Database ready."

echo ""
echo "Tizim lokal rejimda ishga tushirishga tayyor!"
echo "Servislarni alohida terminallarda ishga tushirish buyruqlari:"
echo "  1. Django REST API:"
echo "     $PYTHON_BIN backend/manage.py runserver 0.0.0.0:$BACKEND_PORT"
echo "  2. AI Inference Service (FastAPI):"
echo "     $PYTHON_BIN -m uvicorn inference.app.main:app --host 0.0.0.0 --port $INFERENCE_PORT"
echo "  3. Celery Worker:"
echo "     $PYTHON_BIN -m celery -A core worker -l INFO"
echo "  4. React Frontend (Vite):"
echo "     npm --prefix frontend run dev"
echo "=========================================================="
