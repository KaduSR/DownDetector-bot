"""Rate limiting middleware for API protection."""

from collections import defaultdict
from datetime import datetime, timedelta
from typing import Dict, List
from fastapi import Request, HTTPException


class RateLimiter:
    """Simple in-memory rate limiter."""

    def __init__(self, requests_per_minute: int = 100):
        """
        Initialize rate limiter.

        Args:
            requests_per_minute: Maximum requests allowed per minute per IP
        """
        self.requests_per_minute = requests_per_minute
        self.requests: Dict[str, List[datetime]] = defaultdict(list)

    async def check_rate_limit(self, request: Request) -> None:
        """
        Check if request exceeds rate limit.

        Args:
            request: FastAPI request object

        Raises:
            HTTPException: If rate limit is exceeded
        """
        # Get client IP
        client_ip = self._get_client_ip(request)

        # Clean old requests
        cutoff_time = datetime.now() - timedelta(minutes=1)
        self.requests[client_ip] = [
            req_time for req_time in self.requests[client_ip]
            if req_time > cutoff_time
        ]

        # Check limit
        if len(self.requests[client_ip]) >= self.requests_per_minute:
            raise HTTPException(
                status_code=429,
                detail={
                    "error": {
                        "code": "RATE_LIMIT_EXCEEDED",
                        "message": "Rate limit exceeded. Please try again later.",
                        "retry_after_seconds": 60,
                    }
                }
            )

        # Add current request
        self.requests[client_ip].append(datetime.now())

    def _get_client_ip(self, request: Request) -> str:
        """Get client IP address from request."""
        # Check for forwarded headers
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()

        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip

        return request.client.host if request.client else "unknown"

    def reset(self) -> None:
        """Reset all rate limit counters."""
        self.requests.clear()

    def get_remaining(self, client_ip: str) -> int:
        """Get remaining requests for a client."""
        cutoff_time = datetime.now() - timedelta(minutes=1)
        recent_requests = [
            req_time for req_time in self.requests.get(client_ip, [])
            if req_time > cutoff_time
        ]
        return max(0, self.requests_per_minute - len(recent_requests))
