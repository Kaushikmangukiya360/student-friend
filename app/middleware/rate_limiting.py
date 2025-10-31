from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
import time
import logging
from collections import defaultdict
from typing import Dict, Tuple
import os

logger = logging.getLogger(__name__)

class RateLimiter:
    """Simple in-memory rate limiter"""

    def __init__(self):
        self.requests: Dict[str, list] = defaultdict(list)
        self.rate_limits = {
            "auth": (5, 60),  # 5 requests per minute for auth endpoints
            "api": (100, 60),  # 100 requests per minute for general API
            "webhook": (10, 60),  # 10 requests per minute for webhooks
            "ai": (50, 60),  # 50 requests per minute for AI endpoints
        }

    def is_allowed(self, key: str, limit_type: str = "api") -> bool:
        """Check if request is allowed under rate limit"""
        now = time.time()
        limit, window = self.rate_limits.get(limit_type, (100, 60))

        # Clean old requests
        self.requests[key] = [req_time for req_time in self.requests[key]
                            if now - req_time < window]

        # Check if under limit
        if len(self.requests[key]) >= limit:
            return False

        # Add current request
        self.requests[key].append(now)
        return True

# Global rate limiter instance
rate_limiter = RateLimiter()

async def rate_limiting_middleware(request: Request, call_next):
    """Rate limiting middleware"""
    # Get client identifier (IP address)
    client_ip = request.client.host if request.client else "unknown"

    # Determine rate limit type based on path
    path = request.url.path
    if path.startswith("/auth"):
        limit_type = "auth"
    elif path.startswith("/payment/webhook"):
        limit_type = "webhook"
    elif path.startswith("/ai"):
        limit_type = "ai"
    else:
        limit_type = "api"

    # Check rate limit
    if not rate_limiter.is_allowed(client_ip, limit_type):
        logger.warning(f"Rate limit exceeded for {client_ip} on {path}")
        return JSONResponse(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            content={
                "success": False,
                "message": "Too many requests. Please try again later.",
                "error_code": "RATE_LIMIT_EXCEEDED"
            }
        )

    # Continue with request
    response = await call_next(request)
    return response

async def logging_middleware(request: Request, call_next):
    """Request logging middleware"""
    start_time = time.time()

    # Log request
    logger.info(f"{request.method} {request.url.path} - Client: {request.client.host if request.client else 'unknown'}")

    try:
        response = await call_next(request)

        # Log response
        process_time = time.time() - start_time
        logger.info(".2f")

        return response

    except Exception as e:
        # Log error
        process_time = time.time() - start_time
        logger.error(".2f")
        raise

async def validation_middleware(request: Request, call_next):
    """Input validation and sanitization middleware"""
    # Basic input validation for common attacks
    if request.method in ["POST", "PUT", "PATCH"]:
        try:
            body = await request.body()

            # Check for suspicious patterns (basic XSS/SQL injection detection)
            suspicious_patterns = [
                "<script", "javascript:", "onload=", "onerror=",
                "SELECT ", "INSERT ", "UPDATE ", "DELETE ", "DROP ",
                "../../../", "..\\"
            ]

            body_str = body.decode('utf-8', errors='ignore').lower()
            for pattern in suspicious_patterns:
                if pattern.lower() in body_str:
                    logger.warning(f"Suspicious input detected from {request.client.host if request.client else 'unknown'}: {pattern}")
                    return JSONResponse(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        content={
                            "success": False,
                            "message": "Invalid input detected",
                            "error_code": "INVALID_INPUT"
                        }
                    )
        except:
            pass  # If we can't read body, continue

    response = await call_next(request)
    return response

async def security_headers_middleware(request: Request, call_next):
    """Add security headers to responses"""
    response = await call_next(request)

    # Add security headers
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["Content-Security-Policy"] = "default-src 'self'"

    # Remove server header for security
    if "server" in response.headers:
        del response.headers["server"]

    return response