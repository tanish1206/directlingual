import time
from collections import defaultdict
import threading

class RateLimiter:
    def __init__(self, requests_limit: int = 20, window_seconds: int = 60):
        self.requests_limit = requests_limit
        self.window_seconds = window_seconds
        self.requests = defaultdict(list)
        self.lock = threading.Lock()

    def is_allowed(self, client_id: str) -> bool:
        """
        Thread-safe sliding window rate limiting check.
        Returns True if request is allowed, False otherwise.
        """
        now = time.time()
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
global_rate_limiter = RateLimiter(requests_limit=15, window_seconds=60)
