"""VoiceClone AI Inference Service — FastAPI Application."""

import base64
import logging
import os
import time
import uuid
from contextlib import asynccontextmanager
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Final

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from inference.app.adapters.mock_adapter import MockVoiceModelAdapter
from inference.app.core.audio_processor import (
    concatenate_wav_chunks,
    inspect_wav_audio,
    validate_reference_audio,
)
from inference.app.core.concurrency import BoundedInferenceLock
from inference.app.core.exceptions import (
    InferenceException,
    ModelNotFoundError,
    TextNormalizationError,
)
from inference.app.core.registry import ModelRegistry
from inference.app.core.text_normalizer import UzbekTextNormalizer
from inference.app.schemas.requests import ExtractSpeakerRequest, SynthesisRequest
from inference.app.schemas.responses import (
    ErrorResponse,
    HealthResponse,
    SpeakerResponse,
    SynthesisResponse,
)

SERVICE_VERSION: Final[str] = "0.1.0"
IS_PRODUCTION: Final[bool] = os.getenv("ENVIRONMENT", "development").lower() == "production"

# Setup Inference Rotating Log File
INFERENCE_LOG_DIR = Path(
    os.getenv("LOG_DIR", Path(__file__).resolve().parents[2] / "var" / "logs")
).resolve()
INFERENCE_LOG_DIR.mkdir(parents=True, exist_ok=True)

inference_logger = logging.getLogger("voiceclone.inference")
inference_logger.setLevel(logging.INFO)
if not inference_logger.handlers:
    _formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s] [req:%(request_id)s] [%(name)s:%(lineno)d] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    _rf_handler = RotatingFileHandler(
        filename=str(INFERENCE_LOG_DIR / "inference.log"),
        maxBytes=10 * 1024 * 1024,
        backupCount=10,
        encoding="utf-8",
    )
    _rf_handler.setFormatter(_formatter)
    inference_logger.addHandler(_rf_handler)

    _c_handler = logging.StreamHandler()
    _c_handler.setFormatter(_formatter)
    inference_logger.addHandler(_c_handler)

# Initialize singletons
registry = ModelRegistry(is_production=IS_PRODUCTION)
lock = BoundedInferenceLock(max_concurrent_jobs=1, timeout_seconds=30.0)

# Pre-register default mock adapter for dev and testing
_default_mock_adapter = MockVoiceModelAdapter()
registry.register(
    adapter=_default_mock_adapter,
    license_name="MIT",
    license_status="VERIFIED",
    commercial_approved=True,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle manager for model warming and teardown."""
    yield


app = FastAPI(
    title="VoiceClone AI Inference Service",
    description="Internal, isolated speech synthesis and voice cloning microservice.",
    version=SERVICE_VERSION,
    lifespan=lifespan,
)


@app.middleware("http")
async def inference_correlation_middleware(request: Request, call_next):
    req_id = request.headers.get("X-Request-ID") or f"inf_{uuid.uuid4().hex[:16]}"
    start_time = time.time()
    extra = {"request_id": req_id}
    inference_logger.info("--> %s %s", request.method, request.url.path, extra=extra)

    try:
        response = await call_next(request)
        duration_ms = round((time.time() - start_time) * 1000, 2)
        inference_logger.info(
            "<-- %s %s status=%d duration=%sms",
            request.method,
            request.url.path,
            response.status_code,
            duration_ms,
            extra=extra,
        )
        response.headers["X-Request-ID"] = req_id
        return response
    except Exception as exc:
        duration_ms = round((time.time() - start_time) * 1000, 2)
        inference_logger.exception(
            "INFERENCE_ERROR %s %s duration=%sms: %s",
            request.method,
            request.url.path,
            duration_ms,
            str(exc),
            extra=extra,
        )
        raise


@app.exception_handler(InferenceException)
async def handle_inference_exception(_request: Request, exc: InferenceException) -> JSONResponse:
    """Map domain inference exceptions to structured HTTP JSON responses."""
    payload = ErrorResponse(error_code=exc.error_code, message=exc.message)
    return JSONResponse(status_code=exc.status_code, content=payload.model_dump())


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Hardware health, VRAM inspection, and registered model capabilities."""
    vram_free = None
    device = "cpu"
    try:
        import torch

        if torch.cuda.is_available():
            device = "cuda"
            free_bytes, _ = torch.cuda.mem_get_info()
            vram_free = round(free_bytes / (1024 * 1024), 2)
    except ImportError:
        pass

    return HealthResponse(
        status="OK",
        service_version=SERVICE_VERSION,
        device=device,
        vram_free_mb=vram_free,
        registered_models=registry.list_models(),
    )


@app.get("/hardware")
async def get_hardware_info():
    """Detailed hardware capability inspection and diagnostics (VC-083)."""
    from .core.hardware import detect_hardware_capabilities

    return detect_hardware_capabilities()


@app.post("/synthesize", response_model=SynthesisResponse)
async def synthesize_speech(req: SynthesisRequest):
    """Synthesize normalized text into WAV audio using bounded concurrency."""
    normalized_text = UzbekTextNormalizer.normalize(req.text, language=req.language)
    if not normalized_text:
        raise TextNormalizationError(
            "Input text contains no audible characters after normalization."
        )

    # Determine adapter
    adapter_id = req.adapter_id
    if not adapter_id:
        models = registry.list_models()
        if not models:
            raise ModelNotFoundError("No voice model registered in the service.")
        adapter_id = models[0]["adapter_id"]

    adapter = registry.get_adapter(adapter_id)

    # Process reference audio if supplied
    speaker_embedding = None
    if req.reference_audio_base64:
        ref_bytes = base64.b64decode(req.reference_audio_base64)
        validate_reference_audio(ref_bytes)
        speaker_embedding = await adapter.extract_speaker_embedding(ref_bytes)

    # Split text into sentence-bounded chunks for stable generation
    chunks = UzbekTextNormalizer.chunk_text(normalized_text, max_chars=200)

    # Acquire lock for bounded execution
    async with lock.acquire():
        audio_chunks: list[bytes] = []
        last_meta: dict = {}

        for chunk in chunks:
            chunk_wav, meta = await adapter.synthesize(
                text=chunk,
                language=req.language,
                speaker_embedding=speaker_embedding,
                options={"speed": req.speed},
            )
            audio_chunks.append(chunk_wav)
            last_meta = meta

        # Stitch all chunks together into a single WAV stream
        final_wav = concatenate_wav_chunks(audio_chunks)
        info = inspect_wav_audio(final_wav)

    b64_audio = base64.b64encode(final_wav).decode("ascii")

    return SynthesisResponse(
        audio_base64=b64_audio,
        duration_sec=info["duration_sec"],
        sample_rate=info["sample_rate"],
        format="WAV",
        metadata={
            **last_meta,
            "total_chunks": len(chunks),
            "channels": info["channels"],
        },
    )


@app.post("/extract-speaker", response_model=SpeakerResponse, status_code=status.HTTP_200_OK)
async def extract_speaker(req: ExtractSpeakerRequest):
    """Validate reference audio and return speaker embedding."""
    audio_bytes = base64.b64decode(req.audio_base64)
    info = validate_reference_audio(audio_bytes)

    adapter_id = req.adapter_id
    if not adapter_id:
        models = registry.list_models()
        if not models:
            raise ModelNotFoundError("No voice model registered in the service.")
        adapter_id = models[0]["adapter_id"]

    adapter = registry.get_adapter(adapter_id)
    embedding_bytes = await adapter.extract_speaker_embedding(audio_bytes)

    return SpeakerResponse(
        embedding_base64=base64.b64encode(embedding_bytes).decode("ascii"),
        duration_sec=info["duration_sec"],
        sample_rate=info["sample_rate"],
        channels=info["channels"],
    )
