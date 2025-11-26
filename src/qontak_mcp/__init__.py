"""
Qontak MCP - Manage Deals, Tickets, and Tasks in Qontak CRM

Security Features:
- Pydantic input validation
- User ID validation for tenant isolation
- Rate limiting with token bucket
- Structured security logging
- Safe error handling (no information disclosure)
"""

__version__ = "0.1.0"

# Validation
from .validation import (
    ValidationError,
    ValidationResult,
    validate_user_id,
    validate_resource_id,
    validate_pagination,
    validate_string,
    validate_date,
    validate_custom_fields,
    require_valid_user_id,
    require_valid_resource_id,
)

# Rate limiting
from .rate_limit import (
    RateLimiter,
    RateLimitConfig,
    TokenBucket,
    get_rate_limiter,
    configure_rate_limiter,
)

# Logging
from .logging import (
    SecurityLogger,
    SecurityEventType,
    get_logger,
    configure_logger,
    log_operation,
)

# Error handling
from .errors import (
    ErrorCategory,
    ClassifiedError,
    classify_error,
    safe_error_response,
    validation_error_response,
    auth_error_response,
    rate_limit_error_response,
    not_found_error_response,
    internal_error_response,
)

__all__ = [
    # Version
    "__version__",
    
    # Validation
    "ValidationError",
    "ValidationResult", 
    "validate_user_id",
    "validate_resource_id",
    "validate_pagination",
    "validate_string",
    "validate_date",
    "validate_custom_fields",
    "require_valid_user_id",
    "require_valid_resource_id",
    
    # Rate limiting
    "RateLimiter",
    "RateLimitConfig",
    "TokenBucket",
    "get_rate_limiter",
    "configure_rate_limiter",
    
    # Logging
    "SecurityLogger",
    "SecurityEventType",
    "get_logger",
    "configure_logger",
    "log_operation",
    
    # Error handling
    "ErrorCategory",
    "ClassifiedError",
    "classify_error",
    "safe_error_response",
    "validation_error_response",
    "auth_error_response",
    "rate_limit_error_response",
    "not_found_error_response",
    "internal_error_response",
]
