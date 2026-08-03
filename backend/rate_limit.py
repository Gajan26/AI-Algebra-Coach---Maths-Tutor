"""Minimal in-memory per-IP sliding-window rate limiter.

Single-process only: counts reset on redeploy and are not shared across
replicas. That's fine for a single-instance deployment; swap in a
Redis-backed limiter if this ever runs with more than one replica.
"""

from __future__ import annotations

import time
from collections import defaultdict, deque

_hits: dict[tuple[str, str], deque[float]] = defaultdict(deque)


def check(ip: str, bucket: str, limit: int, window_seconds: int) -> bool:
    """Record a hit for (ip, bucket) and return True if still within limit."""
    now = time.monotonic()
    window = _hits[(ip, bucket)]
    while window and now - window[0] > window_seconds:
        window.popleft()
    if len(window) >= limit:
        return False
    window.append(now)
    return True
