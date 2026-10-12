"""Operational beta analytics service and telemetry engine (VC-090).

Privacy Notice:
This module collects ONLY mathematical telemetry, latency distributions,
hardware/model throughput, and categorized error codes. It NEVER logs or stores
audio data, voice embeddings, transcripts, or personal identifying information.
"""

from __future__ import annotations

import math
from datetime import timedelta
from typing import Any

from django.utils import timezone

from .models import OperationalMetric


def categorize_error(error_message: str) -> str:
    """Categorize free-form error messages into structured operational error codes."""
    if not error_message:
        return "NONE"

    low = error_message.lower()
    if "consent" in low or "unverified" in low or "revoked" in low:
        return "CONSENT_DENIED"
    if "timeout" in low or "timed out" in low:
        return "TIMEOUT"
    if "503" in low or "gpu busy" in low or "oom" in low or "out of memory" in low:
        return "GPU_BUSY_503"
    if "400" in low or "invalid input" in low or "unsupported" in low:
        return "CLIENT_ERROR_400"
    if "403" in low or "forbidden" in low or "permission" in low:
        return "FORBIDDEN_403"
    if "404" in low or "not found" in low:
        return "NOT_FOUND_404"
    if "max_retries" in low or "maximum retries" in low:
        return "MAX_RETRIES_EXCEEDED"
    if "connect" in low or "connection refused" in low or "offline" in low:
        return "INFERENCE_OFFLINE"

    return "INTERNAL_ERROR"


def calculate_percentile(data: list[float], percentile: float) -> float:
    """Calculate percentile value with linear interpolation (zero external dependencies)."""
    if not data:
        return 0.0
    if len(data) == 1:
        return round(float(data[0]), 3)

    sorted_data = sorted(data)
    k = (len(sorted_data) - 1) * (percentile / 100.0)
    floor_k = math.floor(k)
    ceil_k = math.ceil(k)

    if floor_k == ceil_k:
        return round(float(sorted_data[int(k)]), 3)

    d0 = sorted_data[int(floor_k)] * (ceil_k - k)
    d1 = sorted_data[int(ceil_k)] * (k - floor_k)
    return round(float(d0 + d1), 3)


def record_job_metric(
    job,
    audio_duration_sec: float = 0.0,
    error_message: str = "",
) -> OperationalMetric:
    """
    Record an immutable telemetry point for a finished or failed GenerationJob.
    Guarantees privacy: No text prompts or audio binaries are saved.
    """
    queue_ms = 0.0
    compute_ms = 0.0
    total_ms = 0.0
    rtf: float | None = None

    if job.started_at and job.created_at:
        queue_ms = max(0.0, (job.started_at - job.created_at).total_seconds() * 1000.0)

    if job.completed_at and job.started_at:
        compute_ms = max(0.0, (job.completed_at - job.started_at).total_seconds() * 1000.0)

    if job.completed_at and job.created_at:
        total_ms = max(0.0, (job.completed_at - job.created_at).total_seconds() * 1000.0)
    elif compute_ms > 0:
        total_ms = queue_ms + compute_ms

    if audio_duration_sec > 0 and compute_ms > 0:
        # RTF = compute_time_seconds / audio_duration_seconds
        # Lower RTF is faster (< 1.0 is faster than real time)
        rtf = round((compute_ms / 1000.0) / audio_duration_sec, 4)

    err = error_message or job.error_message
    err_cat = categorize_error(err) if job.status != "SUCCEEDED" else "NONE"
    char_count = len(job.input_text) if hasattr(job, "input_text") and job.input_text else 0

    return OperationalMetric.objects.create(
        job_id=job.id,
        user_id=getattr(job, "user_id", None),
        model_id=job.model_id,
        language=job.language,
        status=job.status,
        char_count=char_count,
        audio_duration_sec=round(float(audio_duration_sec), 3),
        queue_latency_ms=round(queue_ms, 2),
        compute_latency_ms=round(compute_ms, 2),
        total_latency_ms=round(total_ms, 2),
        rtf=rtf,
        error_category=err_cat,
    )


def get_beta_analytics_summary(period: str = "all") -> dict[str, Any]:
    """
    Aggregate operational metrics: success rates, p50/p95 latency, RTF,
    language/model breakdown, and error categories.
    """
    qs = OperationalMetric.objects.all()

    now = timezone.now()
    if period == "24h":
        qs = qs.filter(created_at__gte=now - timedelta(hours=24))
    elif period == "7d":
        qs = qs.filter(created_at__gte=now - timedelta(days=7))
    elif period == "30d":
        qs = qs.filter(created_at__gte=now - timedelta(days=30))

    metrics_list = list(qs)

    # If OperationalMetric is empty, fallback to querying GenerationJob history
    if not metrics_list:
        from apps.generations.models import GenerationJob

        job_qs = GenerationJob.objects.all()
        if period == "24h":
            job_qs = job_qs.filter(created_at__gte=now - timedelta(hours=24))
        elif period == "7d":
            job_qs = job_qs.filter(created_at__gte=now - timedelta(days=7))
        elif period == "30d":
            job_qs = job_qs.filter(created_at__gte=now - timedelta(days=30))

        # Backfill or calculate directly
        total = job_qs.count()
        succeeded = job_qs.filter(status=GenerationJob.STATUS_SUCCEEDED).count()
        failed = job_qs.filter(status=GenerationJob.STATUS_FAILED).count()
        cancelled = job_qs.filter(status=GenerationJob.STATUS_CANCELLED).count()

        lang_counts: dict[str, int] = {}
        model_counts: dict[str, int] = {}
        for item in job_qs.values("language", "model_id"):
            lang = item["language"]
            mod = item["model_id"]
            lang_counts[lang] = lang_counts.get(lang, 0) + 1
            model_counts[mod] = model_counts.get(mod, 0) + 1

        success_rate = round((succeeded / total) * 100.0, 1) if total > 0 else 0.0
        failure_rate = round((failed / total) * 100.0, 1) if total > 0 else 0.0

        return {
            "period": period,
            "total_jobs": total,
            "succeeded_jobs": succeeded,
            "failed_jobs": failed,
            "cancelled_jobs": cancelled,
            "success_rate_percent": success_rate,
            "failure_rate_percent": failure_rate,
            "latency_ms": {
                "p50_total": 0.0,
                "p95_total": 0.0,
                "p50_compute": 0.0,
                "p95_compute": 0.0,
                "avg_total": 0.0,
                "avg_compute": 0.0,
                "avg_queue": 0.0,
            },
            "rtf": {
                "avg_rtf": 0.0,
                "p50_rtf": 0.0,
                "p95_rtf": 0.0,
                "samples_count": 0,
            },
            "by_language": lang_counts,
            "by_model": model_counts,
            "by_error_category": {},
            "total_audio_duration_sec": 0.0,
            "privacy_compliance": {
                "speech_content_logged": False,
                "pii_logged": False,
                "scope": "operational_telemetry_only",
            },
        }

    total_count = len(metrics_list)
    succeeded_count = sum(1 for m in metrics_list if m.status == "SUCCEEDED")
    failed_count = sum(1 for m in metrics_list if m.status == "FAILED")
    cancelled_count = sum(1 for m in metrics_list if m.status == "CANCELLED")

    total_latencies = [m.total_latency_ms for m in metrics_list if m.total_latency_ms > 0]
    compute_latencies = [m.compute_latency_ms for m in metrics_list if m.compute_latency_ms > 0]
    queue_latencies = [m.queue_latency_ms for m in metrics_list if m.queue_latency_ms > 0]

    rtf_values = [m.rtf for m in metrics_list if m.rtf is not None and m.rtf > 0]

    by_lang: dict[str, int] = {}
    by_model: dict[str, int] = {}
    by_error: dict[str, int] = {}
    total_audio_sec = 0.0

    for m in metrics_list:
        by_lang[m.language] = by_lang.get(m.language, 0) + 1
        by_model[m.model_id] = by_model.get(m.model_id, 0) + 1
        if m.error_category and m.error_category != "NONE":
            by_error[m.error_category] = by_error.get(m.error_category, 0) + 1
        total_audio_sec += m.audio_duration_sec

    avg_total = sum(total_latencies) / len(total_latencies) if total_latencies else 0.0
    avg_compute = sum(compute_latencies) / len(compute_latencies) if compute_latencies else 0.0
    avg_queue = sum(queue_latencies) / len(queue_latencies) if queue_latencies else 0.0
    avg_rtf = sum(rtf_values) / len(rtf_values) if rtf_values else 0.0

    success_rate = round((succeeded_count / total_count) * 100.0, 1) if total_count > 0 else 0.0
    failure_rate = round((failed_count / total_count) * 100.0, 1) if total_count > 0 else 0.0

    return {
        "period": period,
        "total_jobs": total_count,
        "succeeded_jobs": succeeded_count,
        "failed_jobs": failed_count,
        "cancelled_jobs": cancelled_count,
        "success_rate_percent": success_rate,
        "failure_rate_percent": failure_rate,
        "latency_ms": {
            "p50_total": calculate_percentile(total_latencies, 50.0),
            "p95_total": calculate_percentile(total_latencies, 95.0),
            "p50_compute": calculate_percentile(compute_latencies, 50.0),
            "p95_compute": calculate_percentile(compute_latencies, 95.0),
            "avg_total": round(avg_total, 2),
            "avg_compute": round(avg_compute, 2),
            "avg_queue": round(avg_queue, 2),
        },
        "rtf": {
            "avg_rtf": round(avg_rtf, 4),
            "p50_rtf": calculate_percentile(rtf_values, 50.0),
            "p95_rtf": calculate_percentile(rtf_values, 95.0),
            "samples_count": len(rtf_values),
        },
        "by_language": by_lang,
        "by_model": by_model,
        "by_error_category": by_error,
        "total_audio_duration_sec": round(total_audio_sec, 2),
        "privacy_compliance": {
            "speech_content_logged": False,
            "pii_logged": False,
            "scope": "operational_telemetry_only",
        },
    }


def calculate_unit_economics(
    period: str = "all",
    gpu_hourly_cost_usd: float = 0.35,
    storage_gb_monthly_usd: float = 0.023,
    usd_uzs_rate: float = 12650.0,
) -> dict[str, Any]:
    """
    Compute unit economics and COGS for speech synthesis workloads (VC-094).

    Inputs:
    - gpu_hourly_cost_usd: Cloud GPU hourly cost (default $0.35 for NVIDIA T4/RTX instance).
    - storage_gb_monthly_usd: Object/SSD storage cost per GB-month (default $0.023).
    - usd_uzs_rate: USD to UZS conversion rate.
    """
    qs = OperationalMetric.objects.all()
    now = timezone.now()
    if period == "24h":
        qs = qs.filter(created_at__gte=now - timedelta(hours=24))
    elif period == "7d":
        qs = qs.filter(created_at__gte=now - timedelta(days=7))
    elif period == "30d":
        qs = qs.filter(created_at__gte=now - timedelta(days=30))

    metrics = list(qs)

    total_jobs = len(metrics)
    total_audio_sec = sum(m.audio_duration_sec for m in metrics)
    total_compute_ms = sum(m.compute_latency_ms for m in metrics if m.compute_latency_ms > 0)
    total_compute_sec = total_compute_ms / 1000.0

    total_audio_min = total_audio_sec / 60.0
    rtf_values = [m.rtf for m in metrics if m.rtf is not None and m.rtf > 0]
    avg_rtf = (
        sum(rtf_values) / len(rtf_values)
        if rtf_values
        else (total_compute_sec / total_audio_sec if total_audio_sec > 0 else 0.38)
    )

    # 1. Compute Cost
    gpu_cost_per_sec_usd = gpu_hourly_cost_usd / 3600.0
    compute_cost_usd = total_compute_sec * gpu_cost_per_sec_usd
    compute_cost_uzs = compute_cost_usd * usd_uzs_rate

    # 2. Storage Cost (assuming 24kHz 16-bit mono WAV ~ 48,000 bytes/sec, 7 days retention)
    est_bytes = total_audio_sec * 48_000
    est_gb = est_bytes / (1024.0**3)
    storage_cost_usd = est_gb * (storage_gb_monthly_usd * (7.0 / 30.0))
    storage_cost_uzs = storage_cost_usd * usd_uzs_rate

    # 3. Total COGS
    total_cogs_usd = compute_cost_usd + storage_cost_usd
    total_cogs_uzs = compute_cost_uzs + storage_cost_uzs

    # Unit Cost per Minute of Audio
    cogs_per_minute_usd = (
        (total_cogs_usd / total_audio_min)
        if total_audio_min > 0
        else (60.0 * avg_rtf * gpu_cost_per_sec_usd)
    )
    cogs_per_minute_uzs = cogs_per_minute_usd * usd_uzs_rate

    # Commercial Revenue benchmarks (from VC-093)
    price_per_min_creator = 2633.0
    price_per_min_pro = 1658.0
    price_per_min_payg = 1500.0

    margin_creator_pct = (
        round(((price_per_min_creator - cogs_per_minute_uzs) / price_per_min_creator) * 100.0, 1)
        if price_per_min_creator > 0
        else 0.0
    )
    margin_pro_pct = (
        round(((price_per_min_pro - cogs_per_minute_uzs) / price_per_min_pro) * 100.0, 1)
        if price_per_min_pro > 0
        else 0.0
    )
    margin_payg_pct = (
        round(((price_per_min_payg - cogs_per_minute_uzs) / price_per_min_payg) * 100.0, 1)
        if price_per_min_payg > 0
        else 0.0
    )

    return {
        "period": period,
        "workload": {
            "total_jobs": total_jobs,
            "total_audio_seconds": round(total_audio_sec, 2),
            "total_audio_minutes": round(total_audio_min, 2),
            "total_compute_seconds": round(total_compute_sec, 2),
            "average_rtf": round(avg_rtf, 4),
            "estimated_storage_mb": round(est_bytes / (1024.0**2), 2),
        },
        "rates": {
            "gpu_hourly_usd": gpu_hourly_cost_usd,
            "storage_gb_monthly_usd": storage_gb_monthly_usd,
            "usd_uzs_rate": usd_uzs_rate,
        },
        "costs": {
            "compute_cost_usd": round(compute_cost_usd, 4),
            "compute_cost_uzs": round(compute_cost_uzs, 2),
            "storage_cost_usd": round(storage_cost_usd, 6),
            "storage_cost_uzs": round(storage_cost_uzs, 2),
            "total_cogs_usd": round(total_cogs_usd, 4),
            "total_cogs_uzs": round(total_cogs_uzs, 2),
            "cogs_per_minute_audio_usd": round(cogs_per_minute_usd, 5),
            "cogs_per_minute_audio_uzs": round(cogs_per_minute_uzs, 2),
        },
        "profitability_margins": {
            "creator_tier_margin_percent": margin_creator_pct,
            "pro_tier_margin_percent": margin_pro_pct,
            "payg_margin_percent": margin_payg_pct,
        },
    }

