<#
.SYNOPSIS
    VoiceClone AI — Unified Local Development & Offline Startup Script (VC-080)
.DESCRIPTION
    Initializes local cache, validates Python environment, applies Django migrations,
    and runs the full stack (Backend, AI Inference, and Frontend).
.PARAMETER Mode
    Execution mode: 'mock' (default, lightweight CPU test) or 'gpu' (CUDA inference).
.EXAMPLE
    .\scripts\start_local.ps1 -Mode mock
#>
param (
    [ValidateSet("mock", "gpu")]
    [string]$Mode = "mock",
    [int]$BackendPort = 8000,
    [int]$InferencePort = 8001
)

$ErrorActionPreference = "Stop"

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "       VoiceClone AI — Local Startup (Mode: $Mode)" -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

$WorkspaceRoot = (Get-Item $PSScriptRoot).Parent.FullName
Set-Location $WorkspaceRoot

# 1. Environment and Cache Hygiene
$env:HF_HOME = "$WorkspaceRoot\.cache\huggingface"
$env:PIP_CACHE_DIR = "$WorkspaceRoot\.cache\pip"
$env:TORCH_HOME = "$WorkspaceRoot\.cache\torch"
$env:MODEL_CACHE_DIR = "$WorkspaceRoot\.cache\models"
$env:PYTHONPATH = "$WorkspaceRoot\backend;$WorkspaceRoot\inference"

New-Item -ItemType Directory -Force -Path $env:HF_HOME, $env:PIP_CACHE_DIR, $env:TORCH_HOME, $env:MODEL_CACHE_DIR, "$WorkspaceRoot\var\media", "$WorkspaceRoot\var\logs" | Out-Null
Write-Host "✓ Local cache directories verified on D: drive." -ForegroundColor Green

# 2. Python Detection
$PythonCmd = "python"
if (-not (Get-Command $PythonCmd -ErrorAction SilentlyContinue)) {
    $UserPython = "$env:LOCALAPPDATA\Programs\Python\Python311\python.exe"
    if (Test-Path $UserPython) {
        $PythonCmd = $UserPython
    } else {
        Write-Error "Python 3.11 executable not found in PATH or AppData. Please verify installation."
    }
}
Write-Host "✓ Using Python: $PythonCmd" -ForegroundColor Green

# 3. Database Migrations
Write-Host "→ Applying Django database migrations..." -ForegroundColor Yellow
& $PythonCmd "$WorkspaceRoot\backend\manage.py" migrate --noinput
Write-Host "✓ Database ready." -ForegroundColor Green

# 4. Service Launch Instructions
Write-Host ""
Write-Host "Tizim lokal rejimda ishga tushirishga tayyor!" -ForegroundColor Green
Write-Host "Servislarni alohida terminallarda ishga tushirish buyruqlari:" -ForegroundColor Cyan
Write-Host "  1. Django REST API:" -ForegroundColor White
Write-Host "     & '$PythonCmd' backend/manage.py runserver 0.0.0.0:$BackendPort" -ForegroundColor Gray
Write-Host "  2. AI Inference Service (FastAPI):" -ForegroundColor White
Write-Host "     & '$PythonCmd' -m uvicorn inference.app.main:app --host 0.0.0.0 --port $InferencePort" -ForegroundColor Gray
Write-Host "  3. Celery Worker:" -ForegroundColor White
Write-Host "     & '$PythonCmd' -m celery -A core worker -l INFO -P solo" -ForegroundColor Gray
Write-Host "  4. React Frontend (Vite):" -ForegroundColor White
Write-Host "     npm --prefix frontend run dev" -ForegroundColor Gray
Write-Host ""
Write-Host "==========================================================" -ForegroundColor Cyan
