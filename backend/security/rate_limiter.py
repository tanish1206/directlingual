import time
from collections import defaultdict
import threading
from typing import Dict, List
from backend.config import API_RATE_LIMIT_REQUESTS, API_RATE_LIMIT_WINDOW


# pylint: disable=too-few-public-methods
class RateLimiter:
    """Thread-safe sliding window rate limiter to prevent API abuse."""

    def __init__(
        self,
        requests_limit: int = API_RATE_LIMIT_REQUESTS,
        window_seconds: int = API_RATE_LIMIT_WINDOW
    ) -> None:
        """Initializes the RateLimiter.

        Args:
            requests_limit: Maximum requests allowed in the time window.
            window_seconds: Time window duration in seconds.
        """
        self.requests_limit: int = requests_limit
        self.window_seconds: int = window_seconds
        self.requests: Dict[str, List[float]] = defaultdict(list)
        self.lock: threading.Lock = threading.Lock()

    def is_allowed(self, client_id: str) -> bool:
        """Checks if a request from the given client is allowed.

        Args:
            client_id: Unique identifier for the client (typically IP address).

        Returns:
            True if the request is within limits and allowed, False otherwise.
        """
        now: float = time.time()
        with self.lock:
            history = self.requests[client_id]
            # Keep only requests within the active window
            history = [t for t in history if now - t < self.window_seconds]
            self.requests[client_id] = history

            if len(history) >= self.requests_limit:
                return False

            self.requests[client_id].append(now)
            return True


# Global rate limiter instance for API use
global_rate_limiter: RateLimiter = RateLimiter(
    requests_limit=API_RATE_LIMIT_REQUESTS,
    window_seconds=API_RATE_LIMIT_WINDOW
)
