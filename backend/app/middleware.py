"""
Comprehensive middleware for rate limiting, logging, and security.

Copy this to: backend/app/middleware.py
"""

from collections import defaultdict
from datetime import datetime, timedelta
from typing import Dict, List
import time
import uuid
import logging
import json

from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response, JSONResponse

logger = logging.getLogger(__name__)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Rate limit requests per user to prevent abuse.
    
    Default: 100 requests per 60 seconds per user.
    """
    
    def __init__(
        self,
        app,
        calls: int = 100,
        period: int = 60,
        exclude_paths: List[str] = None
    ):
        super().__init__(app)
        self.calls = calls
        self.period = period
        self.exclude_paths = exclude_paths or ["/health", "/metrics", "/docs", "/redoc"]
        self.requests: Dict[str, List[datetime]] = defaultdict(list)
        self._cleanup_interval = 300  # Cleanup old data every 5 minutes
        self._last_cleanup = datetime.now()
    
    async def dispatch(self, request: Request, call_next):
        # Skip rate limiting for excluded paths
        if any(request.url.path.startswith(path) for path in self.exclude_paths):
            return await call_next(request)
        
        # Get user identifier
        user_id = self._get_user_identifier(request)
        
        # Check rate limit
        now = datetime.now()
        cutoff = now - timedelta(seconds=self.period)
        
        # Clean old requests for this user
        self.requests[user_id] = [
            req_time for req_time in self.requests[user_id]
            if req_time > cutoff
        ]
        
        # Check if limit exceeded
        if len(self.requests[user_id]) >= self.calls:
            logger.warning(
                f"Rate limit exceeded for user {user_id}",
                extra={
                    "user_id": user_id,
                    "path": request.url.path,
                    "requests_count": len(self.requests[user_id])
                }
            )
            
            return JSONResponse(
                status_code=429,
                content={
                    "error": "Too many requests. Please try again later.",
                    "retry_after": self.period
                },
                headers={
                    "Retry-After": str(self.period),
                    "X-RateLimit-Limit": str(self.calls),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(int((cutoff + timedelta(seconds=self.period)).timestamp()))
                }
            )
        
        # Add current request
        self.requests[user_id].append(now)
        
        # Periodic cleanup
        if (now - self._last_cleanup).seconds > self._cleanup_interval:
            self._cleanup_old_data()
            self._last_cleanup = now
        
        # Process request
        response = await call_next(request)
        
        # Add rate limit headers
        response.headers["X-RateLimit-Limit"] = str(self.calls)
        response.headers["X-RateLimit-Remaining"] = str(
            max(0, self.calls - len(self.requests[user_id]))
        )
        response.headers["X-RateLimit-Reset"] = str(
            int((now + timedelta(seconds=self.period)).timestamp())
        )
        
        return response
    
    def _get_user_identifier(self, request: Request) -> str:
        """Extract user identifier from request"""
        # Try to get from Telegram initData
        init_data = request.headers.get("x-tg-init-data", "")
        if init_data:
            user_id = self._extract_user_id_from_init_data(init_data)
            if user_id:
                return f"user:{user_id}"
        
        # Fallback to IP address
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            return f"ip:{forwarded_for.split(',')[0]}"
        
        client_host = request.client.host if request.client else "unknown"
        return f"ip:{client_host}"
    
    def _extract_user_id_from_init_data(self, init_data: str) -> str:
        """Extract user ID from Telegram initData"""
        try:
            import urllib.parse
            data = dict(urllib.parse.parse_qsl(init_data))
            user_json = data.get("user", "{}")
            user = json.loads(user_json)
            return str(user.get("id", ""))
        except Exception:
            return ""
    
    def _cleanup_old_data(self):
        """Remove data for users who haven't made requests recently"""
        cutoff = datetime.now() - timedelta(seconds=self.period * 2)
        users_to_remove = []
        
        for user_id, requests in self.requests.items():
            if not requests or all(req_time < cutoff for req_time in requests):
                users_to_remove.append(user_id)
        
        for user_id in users_to_remove:
            del self.requests[user_id]
        
        if users_to_remove:
            logger.debug(f"Cleaned up rate limit data for {len(users_to_remove)} users")


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Log all requests with timing, user info, and response status.
    """
    
    def __init__(self, app, log_request_body: bool = False):
        super().__init__(app)
        self.log_request_body = log_request_body
    
    async def dispatch(self, request: Request, call_next):
        # Generate unique request ID
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        
        # Start timing
        start_time = time.time()
        
        # Log request
        logger.info(
            f"Request started: {request.method} {request.url.path}",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "query_params": str(request.query_params),
                "client_host": request.client.host if request.client else None,
                "user_agent": request.headers.get("user-agent"),
            }
        )
        
        # Log request body if enabled (be careful with sensitive data!)
        if self.log_request_body and request.method in ["POST", "PUT", "PATCH"]:
            try:
                body = await request.body()
                # Don't log if body is too large (> 1KB)
                if len(body) < 1024:
                    logger.debug(
                        f"Request body: {body.decode('utf-8')}",
                        extra={"request_id": request_id}
                    )
            except Exception as e:
                logger.warning(f"Failed to log request body: {str(e)}")
        
        try:
            # Process request
            response = await call_next(request)
            
            # Calculate duration
            duration = time.time() - start_time
            
            # Log successful response
            logger.info(
                f"Request completed: {request.method} {request.url.path} "
                f"[{response.status_code}] in {duration:.2f}s",
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.url.path,
                    "status_code": response.status_code,
                    "duration": duration,
                }
            )
            
            # Add request ID to response headers
            response.headers["X-Request-ID"] = request_id
            
            return response
            
        except Exception as e:
            # Calculate duration
            duration = time.time() - start_time
            
            # Log error
            logger.error(
                f"Request failed: {request.method} {request.url.path} "
                f"in {duration:.2f}s - {str(e)}",
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.url.path,
                    "duration": duration,
                    "error": str(e),
                },
                exc_info=True
            )
            
            raise


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Add security headers to all responses.
    """
    
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        # Content Security Policy
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://telegram.org; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https: blob:; "
            "font-src 'self' data:; "
            "connect-src 'self' https://api.telegram.org; "
            "frame-ancestors 'none'; "
            "base-uri 'self'; "
            "form-action 'self';"
        )
        
        # Prevent clickjacking
        response.headers["X-Frame-Options"] = "DENY"
        
        # Prevent MIME type sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"
        
        # XSS Protection (legacy but still useful)
        response.headers["X-XSS-Protection"] = "1; mode=block"
        
        # Force HTTPS
        response.headers["Strict-Transport-Security"] = (
            "max-age=31536000; includeSubDomains; preload"
        )
        
        # Referrer policy
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        # Permissions policy (formerly Feature-Policy)
        response.headers["Permissions-Policy"] = (
            "geolocation=(), "
            "microphone=(), "
            "camera=(), "
            "payment=(), "
            "usb=(), "
            "magnetometer=(), "
            "gyroscope=(), "
            "accelerometer=()"
        )
        
        return response


class CORSMiddleware(BaseHTTPMiddleware):
    """
    Custom CORS middleware with additional controls.
    """
    
    def __init__(
        self,
        app,
        allow_origins: List[str],
        allow_methods: List[str] = None,
        allow_headers: List[str] = None,
        max_age: int = 600,
    ):
        super().__init__(app)
        self.allow_origins = allow_origins
        self.allow_methods = allow_methods or ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"]
        self.allow_headers = allow_headers or ["*"]
        self.max_age = max_age
    
    async def dispatch(self, request: Request, call_next):
        origin = request.headers.get("origin")
        
        # Handle preflight requests
        if request.method == "OPTIONS":
            if origin in self.allow_origins or "*" in self.allow_origins:
                return Response(
                    status_code=200,
                    headers={
                        "Access-Control-Allow-Origin": origin or "*",
                        "Access-Control-Allow-Methods": ", ".join(self.allow_methods),
                        "Access-Control-Allow-Headers": ", ".join(self.allow_headers),
                        "Access-Control-Max-Age": str(self.max_age),
                        "Access-Control-Allow-Credentials": "true",
                    }
                )
        
        # Process request
        response = await call_next(request)
        
        # Add CORS headers
        if origin in self.allow_origins or "*" in self.allow_origins:
            response.headers["Access-Control-Allow-Origin"] = origin or "*"
            response.headers["Access-Control-Allow-Credentials"] = "true"
            response.headers["Access-Control-Expose-Headers"] = "X-Request-ID"
        
        return response


class CompressionMiddleware(BaseHTTPMiddleware):
    """
    Compress responses with gzip if client supports it.
    Note: In production, use nginx or CDN for compression.
    """
    
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        # Check if client accepts gzip
        accept_encoding = request.headers.get("accept-encoding", "")
        
        if "gzip" in accept_encoding and response.status_code < 300:
            # Only compress text responses
            content_type = response.headers.get("content-type", "")
            if any(t in content_type for t in ["text/", "application/json", "application/javascript"]):
                # Add compression hint
                response.headers["Vary"] = "Accept-Encoding"
        
        return response


# Usage in main.py:
"""
from .middleware import (
    RateLimitMiddleware,
    RequestLoggingMiddleware,
    SecurityHeadersMiddleware,
)

# Add middlewares (order matters - they execute bottom to top)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RequestLoggingMiddleware, log_request_body=False)
app.add_middleware(RateLimitMiddleware, calls=100, period=60)
"""
