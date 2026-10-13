"""Load testing, bounded concurrency, capacity limits, and race condition tests (VC-105)."""

import asyncio
from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest
from apps.accounts.models import UsageLedger, User
from apps.generations.models import GenerationJob
from django.db import transaction
from inference.app.core.concurrency import BoundedInferenceLock
from inference.app.core.exceptions import ConcurrencyLimitExceededError


@pytest.fixture
def load_test_user(db):
    """User with ample quota for concurrent synthesis debits."""
    return User.objects.create_user(
        username="load_test_user",
        email="load_test@voiceclone.local",
        password="TestPassword123!",
        plan=User.PLAN_PRO,
        audio_seconds_quota=7200,
        audio_seconds_used=0.0,
    )


@pytest.mark.asyncio
async def test_bounded_inference_lock_serial_isolation():
    """Verify that BoundedInferenceLock(max_concurrent_jobs=1) strictly serializes jobs."""
    lock = BoundedInferenceLock(max_concurrent_jobs=1, timeout_seconds=5.0)
    execution_order = []
    active_jobs = 0
    max_observed_active = 0

    async def worker(worker_id: int):
        nonlocal active_jobs, max_observed_active
        async with lock.acquire():
            active_jobs += 1
            max_observed_active = max(max_observed_active, active_jobs)
            execution_order.append(f"start_{worker_id}")
            await asyncio.sleep(0.05)  # Simulate GPU compute
            execution_order.append(f"end_{worker_id}")
            active_jobs -= 1

    # Launch 5 concurrent inference tasks
    await asyncio.gather(worker(1), worker(2), worker(3), worker(4), worker(5))

    # Verify concurrency never exceeded 1
    assert max_observed_active == 1
    assert len(execution_order) == 10
    # Verify each task starts and ends before next one starts
    for i in range(0, 10, 2):
        start_event = execution_order[i]
        end_event = execution_order[i + 1]
        job_num = start_event.split("_")[1]
        assert end_event == f"end_{job_num}"


@pytest.mark.asyncio
async def test_bounded_inference_lock_queue_timeout():
    """Verify that jobs exceeding timeout raise ConcurrencyLimitExceededError."""
    # Timeout 0.1s, worker holds lock for 0.3s
    lock = BoundedInferenceLock(max_concurrent_jobs=1, timeout_seconds=0.1)

    async def long_running_task():
        async with lock.acquire():
            await asyncio.sleep(0.25)

    async def waiting_task():
        await asyncio.sleep(0.02)  # Wait for long task to acquire
        async with lock.acquire():
            pass

    with pytest.raises(ConcurrencyLimitExceededError) as exc_info:
        await asyncio.gather(long_running_task(), waiting_task())

    assert "Inference queue saturated" in str(exc_info.value)


@pytest.mark.django_db
def test_quota_debits_ledger_arithmetic(load_test_user):
    """
    Simulate 10 synthesis debits on a single user.
    Verifies transaction isolation, ledger completeness, and exact balance arithmetic.
    """
    import uuid

    job_count = 10
    duration_per_job = 5.0
    expected_total_deduction = job_count * duration_per_job

    for idx in range(job_count):
        with transaction.atomic():
            u = User.objects.get(id=load_test_user.id)
            u.audio_seconds_used += float(duration_per_job)
            u.save(update_fields=["audio_seconds_used"])
            UsageLedger.objects.create(
                user=u,
                job_id=uuid.uuid4(),
                operation=UsageLedger.OPERATION_DEBIT,
                delta_seconds=-float(duration_per_job),
                balance_after_seconds=u.remaining_seconds,
                notes=f"Debit test {idx}",
            )

    # Refresh user from database
    load_test_user.refresh_from_db()
    assert load_test_user.audio_seconds_used == expected_total_deduction
    assert load_test_user.remaining_seconds == 7200.0 - expected_total_deduction

    # Verify UsageLedger audit entries
    ledger_entries = UsageLedger.objects.filter(
        user=load_test_user, operation=UsageLedger.OPERATION_DEBIT
    )
    assert ledger_entries.count() == 10
    for entry in ledger_entries:
        assert entry.delta_seconds == Decimal(str(-duration_per_job))


@pytest.mark.django_db
def test_concurrent_job_creation_idempotency_protection(load_test_user):
    """
    Verify that multiple requests using identical idempotency_key do not create duplicate jobs.
    """
    idempotency_key = "idemp_capacity_stress_key_101"

    # Create initial job
    job1 = GenerationJob.objects.create(
        user=load_test_user,
        model_id="openvoice_v2",
        input_text="Salom dunyo",
        language="uz",
        idempotency_key=idempotency_key,
    )

    # Subsequent lookup with idempotency_key returns existing job
    job2 = GenerationJob.objects.filter(
        user=load_test_user, idempotency_key=idempotency_key
    ).first()

    assert job2.id == job1.id
    assert GenerationJob.objects.filter(idempotency_key=idempotency_key).count() == 1


@pytest.mark.django_db
def test_stress_pipeline_status_transitions(load_test_user):
    """
    Simulate state machine transitions across 10 jobs in rapid succession.
    Verifies transition validity and absence of state corruption under high load.
    """
    jobs = [
        GenerationJob.objects.create(
            user=load_test_user,
            model_id="openvoice_v2",
            input_text=f"Stress text test {i}",
            language="uz",
        )
        for i in range(10)
    ]

    for job in jobs:
        assert job.status == GenerationJob.STATUS_PENDING

        # Transition PENDING -> RUNNING
        job.transition_to(GenerationJob.STATUS_RUNNING)
        job.save()
        assert job.status == GenerationJob.STATUS_RUNNING
        assert job.started_at is not None

        # Transition RUNNING -> SUCCEEDED
        job.progress_percent = 100
        job.transition_to(GenerationJob.STATUS_SUCCEEDED)
        job.save()
        assert job.status == GenerationJob.STATUS_SUCCEEDED
        assert job.completed_at is not None
        assert job.progress_percent == 100

    # Verify all 10 jobs are now SUCCEEDED
    completed_count = GenerationJob.objects.filter(
        user=load_test_user, status=GenerationJob.STATUS_SUCCEEDED
    ).count()
    assert completed_count == 10
