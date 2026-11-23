"""Validation Performance Profiler.

This module provides operational execution profiling for validation tiers and individual validators.
"""

from contextlib import contextmanager
import time
from typing import Dict, Generator, Optional


class ValidationPerformanceProfiler:
    """Optional, low-overhead performance profiler measuring tier and validator latency."""

    def __init__(self, enabled: bool = False) -> None:
        self.enabled = enabled
        self.tier_durations_ms: Dict[str, float] = {}
        self.validator_durations_ms: Dict[str, float] = {}
        self.total_duration_ms: float = 0.0
        self._start_time: Optional[float] = None

    def start(self) -> None:
        if self.enabled:
            self._start_time = time.perf_counter()

    def stop(self) -> float:
        if self.enabled and self._start_time is not None:
            self.total_duration_ms = (time.perf_counter() - self._start_time) * 1000.0
            return self.total_duration_ms
        return 0.0

    @contextmanager
    def profile_tier(self, tier_name: str) -> Generator[None, None, None]:
        if not self.enabled:
            yield
            return
        t0 = time.perf_counter()
        try:
            yield
        finally:
            dur = (time.perf_counter() - t0) * 1000.0
            self.tier_durations_ms[tier_name] = self.tier_durations_ms.get(tier_name, 0.0) + dur

    @contextmanager
    def profile_validator(self, rule_id: str) -> Generator[None, None, None]:
        if not self.enabled:
            yield
            return
        t0 = time.perf_counter()
        try:
            yield
        finally:
            dur = (time.perf_counter() - t0) * 1000.0
            self.validator_durations_ms[rule_id] = self.validator_durations_ms.get(rule_id, 0.0) + dur
