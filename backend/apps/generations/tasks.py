"""Celery asynchronous background tasks for speech synthesis and lifecycle cleanup."""

import base64
import logging
from datetime import timedelta

import httpx
from celery import shared_task
from django.conf import settings
from django.utils import timezone

from apps.audio.models import AudioAsset
from apps.audio.storage import AudioStorageService

from .models import GeneratedAudio, GenerationJob

logger = logging.getLogger("voiceclone.tasks")


@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=5,
    autoretry_for=(httpx.ConnectError, httpx.TimeoutException),
)
def process_speech_synthesis_job(self, job_id: str) -> dict:
    """Asynchronously execute speech synthesis via the AI inference service."""
    try:
        job = GenerationJob.objects.select_related("voice_profile", "user").get(id=job_id)
    except GenerationJob.DoesNotExist:
        logger.error(f"GenerationJob with id '{job_id}' does not exist.")
        return {"status": "NOT_FOUND"}

    # Transition to RUNNING
    try:
        job.transition_to(GenerationJob.STATUS_RUNNING)
    except Exception as exc:
        logger.warning(f"Could not transition job {job_id} to RUNNING: {exc}")

    # Re-verify Consent Gate
    if job.voice_profile and not job.voice_profile.has_verified_consent:
        error_msg = "Consent was revoked or is unverified. Synthesis aborted."
        job.transition_to(GenerationJob.STATUS_FAILED, error=error_msg)
        try:
            from apps.audit.analytics import record_job_metric

            record_job_metric(job, error_message=error_msg)
        except Exception as metric_err:
            logger.warning(f"Failed to record metric for job {job.id}: {metric_err}")
        return {"status": "FAILED", "reason": error_msg}

    # Prepare payload for FastAPI inference service
    reference_b64 = None
    if job.voice_profile and job.voice_profile.speaker_embedding:
        reference_b64 = base64.b64encode(job.voice_profile.speaker_embedding).decode("ascii")

    inference_payload = {
        "text": job.input_text,
        "language": job.language,
        "adapter_id": job.model_id,
        "reference_audio_base64": reference_b64,
        "speed": 1.0,
    }

    inference_url = f"{settings.INFERENCE_BASE_URL.rstrip('/')}/synthesize"

    try:
        with httpx.Client(timeout=float(settings.INFERENCE_TIMEOUT_SECONDS)) as client:
            resp = client.post(inference_url, json=inference_payload)

        if resp.status_code != 200:
            error_data = (
                resp.json()
                if resp.headers.get("content-type", "").startswith("application/json")
                else {}
            )
            error_code = error_data.get("error_code", "INFERENCE_ERROR")
            err_message = error_data.get(
                "message", f"Inference service failed with status {resp.status_code}"
            )

            # Non-retryable client/input errors
            if resp.status_code in (400, 403, 404):
                job.transition_to(
                    GenerationJob.STATUS_FAILED, error=f"[{error_code}] {err_message}"
                )
                try:
                    from apps.audit.analytics import record_job_metric

                    record_job_metric(job, error_message=f"[{error_code}] {err_message}")
                except Exception as metric_err:
                    logger.warning(f"Failed to record metric for job {job.id}: {metric_err}")
                return {"status": "FAILED", "error_code": error_code}

            # Retryable server errors (503 GPU busy)
            raise self.retry(exc=Exception(f"[{error_code}] {err_message}"))

        data = resp.json()
        raw_wav = base64.b64decode(data["audio_base64"])
        duration = data.get("duration_sec", 0.0)
        sample_rate = data.get("sample_rate", 24000)

        # Persist generated audio asset via storage abstraction
        asset = AudioStorageService.save_audio_bytes(
            user=job.user,
            filename=f"generation_{job.id}.wav",
            audio_bytes=raw_wav,
            duration_sec=duration,
            sample_rate=sample_rate,
            channels=1,
            asset_type=AudioAsset.TYPE_GENERATED,
        )

        GeneratedAudio.objects.create(
            job=job,
            asset=asset,
            duration_sec=duration,
        )

        # Quota Ledger Accounting (VC-100)
        try:
            from apps.accounts.models import UsageLedger

            user = job.user
            if user:
                if user.is_owner_or_unlimited:
                    UsageLedger.objects.create(
                        user=user,
                        job_id=job.id,
                        operation=UsageLedger.OPERATION_UNLIMITED_BYPASS,
                        delta_seconds=0.0,
                        balance_after_seconds=-1.0,
                        notes=f"Unlimited VIP bypass synthesis: {duration:.2f}s (job {job.id})",
                    )
                else:
                    user.audio_seconds_used += float(duration)
                    user.save(update_fields=["audio_seconds_used"])
                    UsageLedger.objects.create(
                        user=user,
                        job_id=job.id,
                        operation=UsageLedger.OPERATION_DEBIT,
                        delta_seconds=-float(duration),
                        balance_after_seconds=user.remaining_seconds,
                        notes=f"Speech synthesis debit: {duration:.2f}s (job {job.id})",
                    )
        except Exception as ledger_err:
            logger.warning(f"Failed to record usage ledger for job {job.id}: {ledger_err}")

        job.progress_percent = 100
        job.transition_to(GenerationJob.STATUS_SUCCEEDED)
        try:
            from apps.audit.analytics import record_job_metric

            record_job_metric(job, audio_duration_sec=duration)
        except Exception as metric_err:
            logger.warning(f"Failed to record metric for job {job.id}: {metric_err}")

        return {"status": "SUCCEEDED", "asset_id": str(asset.id)}

    except Exception as exc:
        if self.request.retries >= self.max_retries:
            err_msg = f"Maximum retries exceeded. Error: {str(exc)}"
            job.transition_to(GenerationJob.STATUS_FAILED, error=err_msg)
            try:
                from apps.audit.analytics import record_job_metric

                record_job_metric(job, error_message=err_msg)
            except Exception as metric_err:
                logger.warning(f"Failed to record metric for job {job.id}: {metric_err}")
            return {"status": "FAILED", "reason": "MAX_RETRIES_EXCEEDED"}
        raise


@shared_task
def cleanup_expired_audio_assets(retention_days: int = 7) -> dict:
    """Retention job: clean up generated audio assets older than retention threshold (VC-056)."""
    cutoff = timezone.now() - timedelta(days=retention_days)
    expired_assets = AudioAsset.objects.filter(
        asset_type=AudioAsset.TYPE_GENERATED,
        created_at__lt=cutoff,
    )
    count = expired_assets.count()
    for asset in expired_assets:
        try:
            if asset.file:
                asset.file.delete(save=False)
        except Exception as exc:
            logger.warning(f"Could not delete physical file for asset {asset.id}: {exc}")
        asset.delete()

    return {"deleted_count": count, "cutoff_date": str(cutoff)}
