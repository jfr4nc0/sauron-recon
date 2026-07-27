import pytest

from sauron_recon.adapters.resilience import CircuitBreaker, CircuitOpenError, RateLimiter


def test_rate_limiter_waits_only_after_first_request():
    now = [0.0]
    sleeps = []
    limiter = RateLimiter(min_interval_seconds=5, clock=lambda: now[0], sleeper=sleeps.append)
    limiter.wait()
    now[0] = 1
    limiter.wait()
    assert sleeps == [4]


def test_circuit_breaker_opens_and_recovers():
    now = [0.0]
    breaker = CircuitBreaker(failure_threshold=2, recovery_seconds=10, clock=lambda: now[0])
    breaker.record_failure()
    breaker.before_call()
    breaker.record_failure()
    with pytest.raises(CircuitOpenError):
        breaker.before_call()
    now[0] = 11
    breaker.before_call()
    breaker.record_success()
    breaker.before_call()
