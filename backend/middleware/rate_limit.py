"""MedicoAssist.it — Rate Limiter Middleware"""

from fastapi import Request, HTTPException
from collections import defaultdict
import time
import logging

logger = logging.getLogger(__name__)


class RateLimiter:
    def __init__(self, max_requests: int = 60, window: int = 60):
        """
        Initialize RateLimiter.
        
        Args:
            max_requests: Maximum number of requests allowed in the window.
            window: Time window in seconds.
        """
        self.requests = defaultdict(list)
        self.max_requests = max_requests
        self.window = window

    async def check(self, request: Request):
        """Check if the request exceeds the rate limit."""
        client_ip = request.client.host if request.client else "unknown"
        now = time.time()

        # Clean old requests
        self.requests[client_ip] = [
            req_time for req_time in self.requests[client_ip]
            if now - req_time < self.window
        ]

        # Check limit
        if len(self.requests[client_ip]) >= self.max_requests:
            logger.warning(f"Rate limit superato per IP: {client_ip}")
            raise HTTPException(status_code=429, detail="Limite di richieste superato")

        # Add current request
        self.requests[client_ip].append(now)


# Global rate limiter (30 requests/minute for sensitive endpoints)
sensitive_limiter = RateLimiter(max_requests=30, window=60)
