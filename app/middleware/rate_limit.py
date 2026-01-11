"""
Rate limiting middleware for API endpoints
"""

from __future__ import annotations

import time
from collections import defaultdict
from typing import Callable

from fastapi import Request, Response, status
from starlette.middleware.base import BaseHTTPMiddleware

from app.config import get_settings


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Simple in-memory rate limiting middleware
    
    Note: For production with multiple instances, use Redis-based rate limiting
    """
    
    def __init__(self, app, requests_per_window: int = 100, window_seconds: int = 60):
        super().__init__(app)
        self.requests_per_window = requests_per_window
        self.window_seconds = window_seconds
        # Store request timestamps per IP
        self.request_times: dict[str, list[float]] = defaultdict(list)
        self._cleanup_interval = 300  # Clean up old entries every 5 minutes
        self._last_cleanup = time.time()
    
    def _cleanup_old_entries(self) -> None:
        """Remove old entries to prevent memory leak"""
        current_time = time.time()
        if current_time - self._last_cleanup < self._cleanup_interval:
            return
        
        cutoff_time = current_time - self.window_seconds
        for ip in list(self.request_times.keys()):
            # Keep only recent requests
            self.request_times[ip] = [
                t for t in self.request_times[ip] if t > cutoff_time
            ]
            # Remove empty entries
            if not self.request_times[ip]:
                del self.request_times[ip]
        
        self._last_cleanup = current_time
    
    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP from request"""
        # Check for forwarded IP (from proxy/load balancer)
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        # Fallback to direct client IP
        if request.client:
            return request.client.host
        
        return "unknown"
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Check rate limit before processing request"""
        
        # Skip rate limiting for health/ready/debug endpoints
        if request.url.path in ["/health", "/ready", "/debug", "/", "/docs", "/openapi.json"]:
            return await call_next(request)
        
        # Get client IP
        client_ip = self._get_client_ip(request)
        
        # Cleanup old entries periodically
        self._cleanup_old_entries()
        
        # Get current time
        current_time = time.time()
        cutoff_time = current_time - self.window_seconds
        
        # Get request times for this IP
        request_times = self.request_times[client_ip]
        
        # Remove old requests outside the window
        request_times[:] = [t for t in request_times if t > cutoff_time]
        
        # Check if limit exceeded
        if len(request_times) >= self.requests_per_window:
            return Response(
                content='{"detail": "Rate limit exceeded. Please try again later."}',
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                media_type="application/json",
                headers={
                    "Retry-After": str(self.window_seconds),
                    "X-RateLimit-Limit": str(self.requests_per_window),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(int(current_time + self.window_seconds)),
                }
            )
        
        # Add current request
        request_times.append(current_time)
        
        # Process request
        response = await call_next(request)
        
        # Add rate limit headers
        remaining = max(0, self.requests_per_window - len(request_times))
        response.headers["X-RateLimit-Limit"] = str(self.requests_per_window)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(int(current_time + self.window_seconds))
        
        return response



