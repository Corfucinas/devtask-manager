"""Retry mechanism with exponential backoff."""
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional
import time as time_module
import random as random_module


@dataclass
class RetryPolicy:
    """Configuration for retries."""
    max_attempts: int = 3
    initial_delay: float = 1.0     # seconds
    backoff_multiplier: float = 2.0
    max_delay: float = 60.0
    jitter: bool = True


class RetryResult:
    """Outcome of a retried operation."""
    def __init__(self, succeeded: bool, attempts: int, result=None, last_error=None):
        self.succeeded = succeeded
        self.attempts = attempts
        self.result = result
        self.last_error = last_error

    def __repr__(self):
        return (f"RetryResult(succeeded={self.succeeded}, "
                f"attempts={self.attempts}, error={self.last_error})")


class Retry:
    """Executes operations with retry and exponential backoff."""
    def __init__(self, policy: RetryPolicy = None):
        self._policy = policy or RetryPolicy()
        self._history: List[Dict] = []

    @property
    def policy(self) -> RetryPolicy:
        return self._policy

    def set_policy(self, policy: RetryPolicy):
        self._policy = policy
        return self

    def _delay_for(self, attempt: int) -> float:
        """Compute delay before the given attempt (1-indexed)."""
        delay = self._policy.initial_delay * (self._policy.backoff_multiplier ** (attempt - 1))
        delay = min(delay, self._policy.max_delay)
        if self._policy.jitter and delay > 0:
            delay *= 0.5 + random_module.random() * 0.5
        return delay

    def execute(self, func: Callable, *args, sleep: bool = False, **kwargs) -> RetryResult:
        """Run func with retries. sleep=False skips real waiting (testable)."""
        attempts = 0
        last_error = None
        while attempts < self._policy.max_attempts:
            attempts += 1
            try:
                result = func(*args, **kwargs)
                self._history.append({"attempts": attempts, "succeeded": True})
                return RetryResult(succeeded=True, attempts=attempts, result=result)
            except Exception as e:
                last_error = str(e)
                self._history.append({"attempts": attempts, "succeeded": False,
                                      "error": last_error})
                if attempts < self._policy.max_attempts and sleep:
                    time_module.sleep(self._delay_for(attempts))
        return RetryResult(succeeded=False, attempts=attempts, last_error=last_error)

    def history(self) -> List[Dict]:
        return list(self._history)

    def success_rate(self) -> float:
        if not self._history:
            return 0.0
        ok = sum(1 for h in self._history if h.get("succeeded"))
        return round(ok / len(self._history) * 100, 1)


def default_retry() -> Retry:
    return Retry(RetryPolicy())


def retry_on_exception(func, exceptions=(Exception,), policy: RetryPolicy = None,
                       sleep: bool = False, *args, **kwargs) -> RetryResult:
    """Convenience: retry only on specific exception types."""
    r = Retry(policy or RetryPolicy())
    attempts = 0
    last_error = None
    while attempts < r.policy.max_attempts:
        attempts += 1
        try:
            result = func(*args, **kwargs)
            return RetryResult(succeeded=True, attempts=attempts, result=result)
        except exceptions as e:
            last_error = str(e)
            if attempts < r.policy.max_attempts and sleep:
                time_module.sleep(r._delay_for(attempts))
        except Exception as e:
            return RetryResult(succeeded=False, attempts=attempts, last_error=str(e))
    return RetryResult(succeeded=False, attempts=attempts, last_error=last_error)
