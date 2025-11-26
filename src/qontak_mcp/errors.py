"""
Secure error handling to prevent information disclosure.

This module provides:
- Safe error responses that don't leak internal details
- Error classification and mapping
- Consistent error response format
"""

import traceback
from typing import Optional, Any
from enum import Enum
from dataclasses import dataclass

from .logging import get_logger, SecurityEventType


# =============================================================================
# Error Categories
# =============================================================================

class ErrorCategory(str, Enum):
    """Categories of errors with appropriate user messages."""
    
    # Client errors (4xx)
    VALIDATION = "validation"
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    NOT_FOUND = "not_found"
    RATE_LIMITED = "rate_limited"
    BAD_REQUEST = "bad_request"
    
    # Server errors (5xx)
    INTERNAL = "internal"
    SERVICE_UNAVAILABLE = "service_unavailable"
    TIMEOUT = "timeout"
    
    # Unknown
    UNKNOWN = "unknown"


# =============================================================================
# Safe Error Messages
# =============================================================================

# User-facing error messages that don't reveal internals
SAFE_ERROR_MESSAGES = {
    ErrorCategory.VALIDATION: "The request contains invalid data. Please check your input.",
    ErrorCategory.AUTHENTICATION: "Authentication failed. Please check your credentials.",
    ErrorCategory.AUTHORIZATION: "You don't have permission to perform this action.",
    ErrorCategory.NOT_FOUND: "The requested resource was not found.",
    ErrorCategory.RATE_LIMITED: "Too many requests. Please wait and try again.",
    ErrorCategory.BAD_REQUEST: "Invalid request. Please check your input.",
    ErrorCategory.INTERNAL: "An internal error occurred. Please try again later.",
    ErrorCategory.SERVICE_UNAVAILABLE: "The service is temporarily unavailable. Please try again later.",
    ErrorCategory.TIMEOUT: "The request timed out. Please try again.",
    ErrorCategory.UNKNOWN: "An unexpected error occurred. Please try again later.",
}


# =============================================================================
# Error Classification
# =============================================================================

@dataclass
class ClassifiedError:
    """A classified error with safe user message."""
    
    category: ErrorCategory
    user_message: str
    details: Optional[str] = None  # Safe details to show user
    internal_message: Optional[str] = None  # For logging only
    status_code: int = 500
    
    def to_response(self, include_details: bool = True) -> dict[str, Any]:
        """Convert to API response format."""
        response = {
            "success": False,
            "error": self.user_message,
            "error_code": self.category.value,
        }
        if include_details and self.details:
            response["details"] = self.details
        return response


def classify_error(error: Exception, context: str = "") -> ClassifiedError:
    """
    Classify an exception into a safe error category.
    
    Args:
        error: The exception to classify
        context: Optional context about where the error occurred
        
    Returns:
        ClassifiedError with safe user message
    """
    import httpx
    from pydantic import ValidationError as PydanticValidationError
    
    error_type = type(error).__name__
    error_msg = str(error)
    
    # Log the full error internally
    logger = get_logger()
    
    # Validation errors (from Pydantic)
    if isinstance(error, PydanticValidationError):
        # Extract safe field names from validation errors
        fields = []
        for err in error.errors():
            loc = err.get('loc', ())
            if loc:
                fields.append(str(loc[-1]))
        
        safe_details = f"Invalid fields: {', '.join(fields)}" if fields else None
        
        logger.validation_failure(
            field=", ".join(fields) if fields else "unknown",
            reason=error_msg,
        )
        
        return ClassifiedError(
            category=ErrorCategory.VALIDATION,
            user_message=SAFE_ERROR_MESSAGES[ErrorCategory.VALIDATION],
            details=safe_details,
            internal_message=error_msg,
            status_code=400,
        )
    
    # Our custom validation errors
    from .validation import ValidationError as CustomValidationError
    if isinstance(error, CustomValidationError):
        logger.validation_failure(
            field=error.field,
            reason=error.message,
        )
        
        return ClassifiedError(
            category=ErrorCategory.VALIDATION,
            user_message=SAFE_ERROR_MESSAGES[ErrorCategory.VALIDATION],
            details=f"Invalid field: {error.field}",
            internal_message=error_msg,
            status_code=400,
        )
    
    # HTTP errors
    if isinstance(error, httpx.TimeoutException):
        logger.api_error("", "", error)
        return ClassifiedError(
            category=ErrorCategory.TIMEOUT,
            user_message=SAFE_ERROR_MESSAGES[ErrorCategory.TIMEOUT],
            internal_message=error_msg,
            status_code=504,
        )
    
    if isinstance(error, httpx.ConnectError):
        logger.api_error("", "", error)
        return ClassifiedError(
            category=ErrorCategory.SERVICE_UNAVAILABLE,
            user_message=SAFE_ERROR_MESSAGES[ErrorCategory.SERVICE_UNAVAILABLE],
            internal_message=error_msg,
            status_code=503,
        )
    
    if isinstance(error, httpx.HTTPStatusError):
        status = error.response.status_code
        
        if status == 401:
            return ClassifiedError(
                category=ErrorCategory.AUTHENTICATION,
                user_message=SAFE_ERROR_MESSAGES[ErrorCategory.AUTHENTICATION],
                internal_message=error_msg,
                status_code=401,
            )
        elif status == 403:
            return ClassifiedError(
                category=ErrorCategory.AUTHORIZATION,
                user_message=SAFE_ERROR_MESSAGES[ErrorCategory.AUTHORIZATION],
                internal_message=error_msg,
                status_code=403,
            )
        elif status == 404:
            return ClassifiedError(
                category=ErrorCategory.NOT_FOUND,
                user_message=SAFE_ERROR_MESSAGES[ErrorCategory.NOT_FOUND],
                internal_message=error_msg,
                status_code=404,
            )
        elif status == 429:
            return ClassifiedError(
                category=ErrorCategory.RATE_LIMITED,
                user_message=SAFE_ERROR_MESSAGES[ErrorCategory.RATE_LIMITED],
                internal_message=error_msg,
                status_code=429,
            )
        elif status >= 500:
            return ClassifiedError(
                category=ErrorCategory.SERVICE_UNAVAILABLE,
                user_message=SAFE_ERROR_MESSAGES[ErrorCategory.SERVICE_UNAVAILABLE],
                internal_message=error_msg,
                status_code=status,
            )
    
    # Value errors (often from our validation)
    if isinstance(error, ValueError):
        return ClassifiedError(
            category=ErrorCategory.BAD_REQUEST,
            user_message=SAFE_ERROR_MESSAGES[ErrorCategory.BAD_REQUEST],
            internal_message=error_msg,
            status_code=400,
        )
    
    # Runtime errors
    if isinstance(error, RuntimeError):
        logger.system_error(error, context)
        return ClassifiedError(
            category=ErrorCategory.INTERNAL,
            user_message=SAFE_ERROR_MESSAGES[ErrorCategory.INTERNAL],
            internal_message=error_msg,
            status_code=500,
        )
    
    # Default: unknown error
    logger.system_error(error, context)
    return ClassifiedError(
        category=ErrorCategory.UNKNOWN,
        user_message=SAFE_ERROR_MESSAGES[ErrorCategory.UNKNOWN],
        internal_message=f"{error_type}: {error_msg}",
        status_code=500,
    )


def safe_error_response(
    error: Exception,
    context: str = "",
    include_details: bool = True,
) -> dict[str, Any]:
    """
    Create a safe error response from an exception.
    
    This function ensures no internal details are leaked to the user.
    
    Args:
        error: The exception that occurred
        context: Optional context about where the error occurred
        include_details: Whether to include safe details
        
    Returns:
        Dict suitable for API response
    """
    classified = classify_error(error, context)
    return classified.to_response(include_details)


def format_validation_errors(errors: list[dict]) -> str:
    """
    Format Pydantic validation errors into a safe, user-friendly message.
    
    Args:
        errors: List of error dicts from Pydantic
        
    Returns:
        User-friendly error message
    """
    messages = []
    for err in errors:
        loc = err.get('loc', ())
        field = str(loc[-1]) if loc else 'unknown'
        msg = err.get('msg', 'invalid value')
        messages.append(f"{field}: {msg}")
    
    if len(messages) == 1:
        return messages[0]
    return "; ".join(messages)


# =============================================================================
# Error Response Helpers
# =============================================================================

def validation_error_response(
    field: str,
    message: str,
) -> dict[str, Any]:
    """Create a validation error response."""
    return {
        "success": False,
        "error": SAFE_ERROR_MESSAGES[ErrorCategory.VALIDATION],
        "error_code": ErrorCategory.VALIDATION.value,
        "details": f"Invalid field '{field}': {message}",
    }


def auth_error_response() -> dict[str, Any]:
    """Create an authentication error response."""
    return {
        "success": False,
        "error": SAFE_ERROR_MESSAGES[ErrorCategory.AUTHENTICATION],
        "error_code": ErrorCategory.AUTHENTICATION.value,
    }


def rate_limit_error_response(retry_after: Optional[int] = None) -> dict[str, Any]:
    """Create a rate limit error response."""
    response = {
        "success": False,
        "error": SAFE_ERROR_MESSAGES[ErrorCategory.RATE_LIMITED],
        "error_code": ErrorCategory.RATE_LIMITED.value,
    }
    if retry_after:
        response["retry_after"] = retry_after
    return response


def not_found_error_response(resource: str = "resource") -> dict[str, Any]:
    """Create a not found error response."""
    return {
        "success": False,
        "error": f"The requested {resource} was not found.",
        "error_code": ErrorCategory.NOT_FOUND.value,
    }


def internal_error_response() -> dict[str, Any]:
    """Create an internal error response (never expose details)."""
    return {
        "success": False,
        "error": SAFE_ERROR_MESSAGES[ErrorCategory.INTERNAL],
        "error_code": ErrorCategory.INTERNAL.value,
    }
