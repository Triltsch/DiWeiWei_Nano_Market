"""Rate limiting primitives for API abuse protection."""

from __future__ import annotations

import asyncio
import time
from collections import deque


class SlidingWindowRateLimiter:
    """In-memory sliding-window rate limiter.

    Each key maintains a rolling deque of hit timestamps.  On every check the
    deque is pruned to the current ``window_seconds`` interval so the visible
    request count always reflects a true sliding window rather than a discrete
    epoch boundary.  Keys should be endpoint-scoped and identity-scoped.
    """

    def __init__(self, max_requests: int, window_seconds: int) -> None:
        if max_requests <= 0:
            raise ValueError("max_requests must be greater than zero")
        if window_seconds <= 0:
            raise ValueError("window_seconds must be greater than zero")

        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._hits: dict[str, deque[float]] = {}
        self._violations: dict[str, deque[float]] = {}
        self._lock = asyncio.Lock()

    async def check(self, key: str) -> tuple[bool, int]:
        """Check whether a request for ``key`` is allowed.

        Returns:
            Tuple of (allowed, retry_after_seconds). When allowed is True,
            retry_after_seconds is always 0.
        """
        now = time.monotonic()

        async with self._lock:
            bucket = self._hits.setdefault(key, deque())
            violation_bucket = self._violations.setdefault(key, deque())
            cutoff = now - self.window_seconds

            while bucket and bucket[0] <= cutoff:
                bucket.popleft()
            while violation_bucket and violation_bucket[0] <= cutoff:
                violation_bucket.popleft()

            # Evict the key when the bucket is empty to prevent the _hits dict
            # from growing without bound across many distinct client keys.
            if not bucket:
                del self._hits[key]
            if not violation_bucket:
                self._violations.pop(key, None)

            if len(bucket) >= self.max_requests:
                violation_bucket = self._violations.setdefault(key, deque())
                violation_bucket.append(now)

                base_retry_after_seconds = max(1, int(self.window_seconds - (now - bucket[0])))
                # Apply a linear penalty on repeated violations for this key.
                linear_penalty_seconds = len(violation_bucket)
                retry_after_seconds = max(base_retry_after_seconds, linear_penalty_seconds)
                return False, retry_after_seconds

            bucket = self._hits.setdefault(key, deque())
            bucket.append(now)
            self._violations.pop(key, None)
            return True, 0

    def reset(self) -> None:
        """Clear all counters (primarily for tests)."""
        self._hits.clear()
        self._violations.clear()
