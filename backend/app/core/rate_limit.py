from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from app.core.config import settings

# Create limiter instance
limiter = Limiter(key_func=get_remote_address)

# Rate limit error handler
async def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded) -> Response:
    """Handle rate limit exceeded errors."""
    return JSONResponse(
        status_code=429,
        content={
            "error": "Rate limit exceeded",
            "detail": f"Too many requests. Try again in {exc.retry_after} seconds.",
            "retry_after": exc.retry_after
        }
    )

# Default rate limits
DEFAULT_RATE_LIMIT = "100/hour"
CHAT_RATE_LIMIT = "10/minute"
MODEL_RATE_LIMIT = "30/minute"
WEBSOCKET_RATE_LIMIT = "60/minute"

# Rate limit decorators
def default_rate_limit():
    """Default rate limit decorator."""
    return limiter.limit(DEFAULT_RATE_LIMIT)

def chat_rate_limit():
    """Chat rate limit decorator."""
    return limiter.limit(CHAT_RATE_LIMIT)

def model_rate_limit():
    """Model rate limit decorator."""
    return limiter.limit(MODEL_RATE_LIMIT)

def websocket_rate_limit():
    """WebSocket rate limit decorator."""
    return limiter.limit(WEBSOCKET_RATE_LIMIT) 