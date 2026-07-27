from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Callable


class CircuitOpenError(RuntimeError):
    """The source is temporarily disabled after repeated failures."""


@dataclass
class RateLimiter:
    min_interval_seconds: float = 0.0
    clock: Callable[[], float] = time.monotonic
    sleeper: Callable[[float], None] = time.sleep
    _last_request_at: float | None = field(default=None, init=False)

    def wait(self) -> None:
        now = self.clock()
        if self._last_request_at is not None:
            remaining = self.min_interval_seconds - (now - self._last_request_at)
            if remaining > 0:
                self.sleeper(remaining)
        self._last_request_at = self.clock()


@dataclass
class CircuitBreaker:
    failure_threshold: int = 3
    recovery_seconds: float = 60.0
    clock: Callable[[], float] = time.monotonic
    _failures: int = field(default=0, init=False)
    _opened_at: float | None = field(default=None, init=False)

    def before_call(self) -> None:
        if self._opened_at is None:
            return
        if self.clock() - self._opened_at < self.recovery_seconds:
            raise CircuitOpenError("source circuit is open")
        self._opened_at = None
        self._failures = 0

    def record_success(self) -> None:
        self._failures = 0
        self._opened_at = None

    def record_failure(self) -> None:
        self._failures += 1
        if self._failures >= self.failure_threshold:
            self._opened_at = self.clock()
