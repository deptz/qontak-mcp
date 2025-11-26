"""
Input validation utilities for Qontak MCP Server.

This module provides validation functions to ensure:
- Tenant isolation through user_id validation
- Input sanitization to prevent injection attacks
- Type and format validation for API parameters
"""

import re
from typing import Optional, Any
from dataclasses import dataclass


# =============================================================================
# Validation Configuration
# =============================================================================

# User ID validation pattern:
# - Alphanumeric, hyphens, underscores only
# - 1-128 characters
# - No path traversal characters
USER_ID_PATTERN = re.compile(r'^[a-zA-Z0-9_-]{1,128}$')

# Maximum pagination limits
MAX_PAGE = 10000
MAX_PER_PAGE = 100

# ID validation (positive integers with reasonable bounds)
MAX_RESOURCE_ID = 2**53  # JavaScript safe integer limit


# =============================================================================
# Validation Errors
# =============================================================================

class ValidationError(Exception):
    """Raised when input validation fails."""
    
    def __init__(self, field: str, message: str) -> None:
        self.field = field
        self.message = message
        super().__init__(f"Validation error on '{field}': {message}")


# =============================================================================
# Validation Result
# =============================================================================

@dataclass
class ValidationResult:
    """Result of a validation operation."""
    is_valid: bool
    error: Optional[str] = None
    sanitized_value: Any = None


# =============================================================================
# User ID Validation (Critical for Tenant Isolation)
# =============================================================================

def validate_user_id(user_id: Optional[str]) -> ValidationResult:
    """
    Validate and sanitize user_id for tenant isolation.
    
    This is CRITICAL for multi-tenant security. The user_id:
    - Must match allowed pattern (alphanumeric, hyphens, underscores)
    - Must be within length limits
    - Cannot contain path traversal characters
    - Cannot contain SQL/NoSQL injection patterns
    
    Args:
        user_id: The user/tenant identifier to validate
        
    Returns:
        ValidationResult with sanitized value or error
    """
    # None is valid (single-tenant mode)
    if user_id is None:
        return ValidationResult(is_valid=True, sanitized_value=None)
    
    # Must be a string
    if not isinstance(user_id, str):
        return ValidationResult(
            is_valid=False,
            error="user_id must be a string"
        )
    
    # Strip whitespace
    user_id = user_id.strip()
    
    # Empty after strip means None
    if not user_id:
        return ValidationResult(is_valid=True, sanitized_value=None)
    
    # Check pattern
    if not USER_ID_PATTERN.match(user_id):
        return ValidationResult(
            is_valid=False,
            error="user_id must contain only alphanumeric characters, hyphens, and underscores (1-128 chars)"
        )
    
    # Check for path traversal attempts
    if '..' in user_id or '/' in user_id or '\\' in user_id:
        return ValidationResult(
            is_valid=False,
            error="user_id contains invalid characters"
        )
    
    # Check for common injection patterns
    injection_patterns = [
        '__', '${', '#{', '{{',  # Template injection
        ';', '|', '&', '`',       # Command injection
        '\x00', '\n', '\r',       # Null/newline injection
    ]
    for pattern in injection_patterns:
        if pattern in user_id:
            return ValidationResult(
                is_valid=False,
                error="user_id contains invalid characters"
            )
    
    return ValidationResult(is_valid=True, sanitized_value=user_id)


def require_valid_user_id(user_id: Optional[str]) -> Optional[str]:
    """
    Validate user_id and return sanitized value or raise ValidationError.
    
    Use this in functions that require a validated user_id.
    
    Args:
        user_id: The user/tenant identifier to validate
        
    Returns:
        Sanitized user_id (or None)
        
    Raises:
        ValidationError: If validation fails
    """
    result = validate_user_id(user_id)
    if not result.is_valid:
        raise ValidationError("user_id", result.error or "Invalid user_id")
    return result.sanitized_value


# =============================================================================
# Resource ID Validation
# =============================================================================

def validate_resource_id(resource_id: int, field_name: str = "id") -> ValidationResult:
    """
    Validate a resource ID (deal_id, ticket_id, task_id, etc.).
    
    Args:
        resource_id: The ID to validate
        field_name: Name of the field for error messages
        
    Returns:
        ValidationResult with sanitized value or error
    """
    if not isinstance(resource_id, int):
        return ValidationResult(
            is_valid=False,
            error=f"{field_name} must be an integer"
        )
    
    if resource_id <= 0:
        return ValidationResult(
            is_valid=False,
            error=f"{field_name} must be a positive integer"
        )
    
    if resource_id > MAX_RESOURCE_ID:
        return ValidationResult(
            is_valid=False,
            error=f"{field_name} exceeds maximum allowed value"
        )
    
    return ValidationResult(is_valid=True, sanitized_value=resource_id)


def require_valid_resource_id(resource_id: int, field_name: str = "id") -> int:
    """
    Validate resource ID and return value or raise ValidationError.
    
    Args:
        resource_id: The ID to validate
        field_name: Name of the field for error messages
        
    Returns:
        Validated resource ID
        
    Raises:
        ValidationError: If validation fails
    """
    result = validate_resource_id(resource_id, field_name)
    if not result.is_valid:
        raise ValidationError(field_name, result.error or "Invalid ID")
    return result.sanitized_value


# =============================================================================
# Pagination Validation
# =============================================================================

def validate_pagination(
    page: int = 1,
    per_page: int = 25
) -> ValidationResult:
    """
    Validate pagination parameters.
    
    Args:
        page: Page number (1-indexed)
        per_page: Number of items per page
        
    Returns:
        ValidationResult with dict of sanitized values or error
    """
    # Validate page
    if not isinstance(page, int) or page < 1:
        return ValidationResult(
            is_valid=False,
            error="page must be a positive integer"
        )
    
    if page > MAX_PAGE:
        return ValidationResult(
            is_valid=False,
            error=f"page cannot exceed {MAX_PAGE}"
        )
    
    # Validate per_page
    if not isinstance(per_page, int) or per_page < 1:
        return ValidationResult(
            is_valid=False,
            error="per_page must be a positive integer"
        )
    
    if per_page > MAX_PER_PAGE:
        return ValidationResult(
            is_valid=False,
            error=f"per_page cannot exceed {MAX_PER_PAGE}"
        )
    
    return ValidationResult(
        is_valid=True,
        sanitized_value={"page": page, "per_page": per_page}
    )


# =============================================================================
# String Validation
# =============================================================================

def validate_string(
    value: Optional[str],
    field_name: str,
    required: bool = False,
    min_length: int = 0,
    max_length: int = 10000,
    pattern: Optional[re.Pattern] = None
) -> ValidationResult:
    """
    Validate a string parameter.
    
    Args:
        value: The string to validate
        field_name: Name of the field for error messages
        required: Whether the field is required
        min_length: Minimum length
        max_length: Maximum length
        pattern: Optional regex pattern to match
        
    Returns:
        ValidationResult with sanitized value or error
    """
    if value is None:
        if required:
            return ValidationResult(
                is_valid=False,
                error=f"{field_name} is required"
            )
        return ValidationResult(is_valid=True, sanitized_value=None)
    
    if not isinstance(value, str):
        return ValidationResult(
            is_valid=False,
            error=f"{field_name} must be a string"
        )
    
    # Strip whitespace
    value = value.strip()
    
    if not value and required:
        return ValidationResult(
            is_valid=False,
            error=f"{field_name} cannot be empty"
        )
    
    if len(value) < min_length:
        return ValidationResult(
            is_valid=False,
            error=f"{field_name} must be at least {min_length} characters"
        )
    
    if len(value) > max_length:
        return ValidationResult(
            is_valid=False,
            error=f"{field_name} cannot exceed {max_length} characters"
        )
    
    if pattern and not pattern.match(value):
        return ValidationResult(
            is_valid=False,
            error=f"{field_name} format is invalid"
        )
    
    return ValidationResult(is_valid=True, sanitized_value=value)


# =============================================================================
# Date Validation
# =============================================================================

DATE_PATTERN = re.compile(r'^\d{4}-\d{2}-\d{2}$')
DATETIME_PATTERN = re.compile(r'^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$')


def validate_date(
    value: Optional[str],
    field_name: str,
    required: bool = False,
    allow_datetime: bool = True
) -> ValidationResult:
    """
    Validate a date or datetime string.
    
    Args:
        value: The date string to validate (YYYY-MM-DD or YYYY-MM-DD HH:MM:SS)
        field_name: Name of the field for error messages
        required: Whether the field is required
        allow_datetime: Whether to allow datetime format
        
    Returns:
        ValidationResult with sanitized value or error
    """
    if value is None:
        if required:
            return ValidationResult(
                is_valid=False,
                error=f"{field_name} is required"
            )
        return ValidationResult(is_valid=True, sanitized_value=None)
    
    if not isinstance(value, str):
        return ValidationResult(
            is_valid=False,
            error=f"{field_name} must be a string"
        )
    
    value = value.strip()
    
    # Check format
    if DATE_PATTERN.match(value):
        return ValidationResult(is_valid=True, sanitized_value=value)
    
    if allow_datetime and DATETIME_PATTERN.match(value):
        return ValidationResult(is_valid=True, sanitized_value=value)
    
    expected = "YYYY-MM-DD" + (" or YYYY-MM-DD HH:MM:SS" if allow_datetime else "")
    return ValidationResult(
        is_valid=False,
        error=f"{field_name} must be in format {expected}"
    )


# =============================================================================
# JSON Custom Fields Validation
# =============================================================================

def validate_custom_fields(
    value: Optional[str],
    max_fields: int = 100,
    max_value_length: int = 10000
) -> ValidationResult:
    """
    Validate custom_fields JSON string.
    
    Args:
        value: JSON string of custom fields
        max_fields: Maximum number of fields allowed
        max_value_length: Maximum length for string values
        
    Returns:
        ValidationResult with parsed dict or error
    """
    import json
    
    if value is None:
        return ValidationResult(is_valid=True, sanitized_value=None)
    
    if not isinstance(value, str):
        return ValidationResult(
            is_valid=False,
            error="custom_fields must be a JSON string"
        )
    
    value = value.strip()
    if not value:
        return ValidationResult(is_valid=True, sanitized_value=None)
    
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError:
        return ValidationResult(
            is_valid=False,
            error="custom_fields is not valid JSON"
        )
    
    if not isinstance(parsed, dict):
        return ValidationResult(
            is_valid=False,
            error="custom_fields must be a JSON object"
        )
    
    if len(parsed) > max_fields:
        return ValidationResult(
            is_valid=False,
            error=f"custom_fields cannot have more than {max_fields} fields"
        )
    
    # Validate keys and values
    for key, val in parsed.items():
        if not isinstance(key, str):
            return ValidationResult(
                is_valid=False,
                error="custom_fields keys must be strings"
            )
        
        if len(key) > 256:
            return ValidationResult(
                is_valid=False,
                error=f"custom_fields key '{key[:50]}...' is too long"
            )
        
        # Check for injection in keys
        if any(c in key for c in ['$', '{', '}', '[', ']', ';', '|']):
            return ValidationResult(
                is_valid=False,
                error=f"custom_fields key contains invalid characters"
            )
        
        # Validate string values length
        if isinstance(val, str) and len(val) > max_value_length:
            return ValidationResult(
                is_valid=False,
                error=f"custom_fields value for '{key}' is too long"
            )
    
    return ValidationResult(is_valid=True, sanitized_value=parsed)
