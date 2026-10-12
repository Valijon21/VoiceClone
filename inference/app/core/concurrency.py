"""Bounded concurrency and memory cleanup manager for GPU/CPU inference."""

import asyncio
import gc
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from inference.app.core.exceptions import ConcurrencyLimitExceededError


class BoundedInferenceLock:
    """Manages strictly bounded concurrency (default 1) to protect GPU VRAM from OOM."""

    def __init__(self, max_concurrent_jobs: int = 1, timeout_seconds: float = 30.0):
        self._semaphore = asyncio.Semaphore(max_concurrent_jobs)
        self._max_jobs = max_concurrent_jobs
        self._timeout = timeout_seconds

    @asynccontextmanager
    async def acquire(self) -> AsyncIterator[None]:
        """Acquire execution lease within bounded timeout or raise ConcurrencyLimitExceededError."""
        acquired = False
        try:
            try:
                await asyncio.wait_for(self._semaphore.acquire(), timeout=self._timeout)
                acquired = True
            except TimeoutError as err:
                raise ConcurrencyLimitExceededError(
                    f"Inference queue saturated: could not acquire slot within {self._timeout}s."
                ) from err

            yield

        finally:
            if acquired:
                self._semaphore.release()
                # Run deterministic garbage collection and GPU cache cleanup
                gc.collect()
                try:
                    import torch

                    if torch.cuda.is_available():
                        torch.cuda.empty_cache()
                except ImportError:
                    pass
