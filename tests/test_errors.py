import pytest
import httpx
from pydantic import ValidationError as PydanticValidationError
from qontak_mcp.errors import (
    ErrorCategory,
    ClassifiedError,
    classify_error,
    safe_error_response,
    internal_error_response,
)
from qontak_mcp.validation import ValidationError


def test_error_category_values():
    """Test error category enum values."""
    assert ErrorCategory.VALIDATION == "validation"
    assert ErrorCategory.AUTHENTICATION == "authentication"
    assert ErrorCategory.NOT_FOUND == "not_found"
    assert ErrorCategory.INTERNAL == "internal"


def test_classified_error_to_response():
    """Test ClassifiedError to_response conversion."""
    err = ClassifiedError(
        category=ErrorCategory.VALIDATION,
        user_message="Invalid input",
        details="Field 'name' is required",
        status_code=400
    )
    
    response = err.to_response()
    assert response["success"] is False
    assert response["error"] == "Invalid input"
    assert response["error_code"] == "validation"
    assert response["details"] == "Field 'name' is required"


def test_classified_error_to_response_no_details():
    """Test ClassifiedError to_response without details."""
    err = ClassifiedError(
        category=ErrorCategory.INTERNAL,
        user_message="Internal error",
        status_code=500
    )
    
    response = err.to_response()
    assert response["success"] is False
    assert response["error"] == "Internal error"
    assert "details" not in response


def test_classify_error_http_404():
    """Test classification of 404 HTTP error."""
    error = httpx.HTTPStatusError(
        "Not found",
        request=httpx.Request("GET", "https://example.com"),
        response=httpx.Response(404)
    )
    
    classified = classify_error(error)
    assert classified.category == ErrorCategory.NOT_FOUND
    assert classified.status_code == 404


def test_classify_error_http_401():
    """Test classification of 401 HTTP error."""
    error = httpx.HTTPStatusError(
        "Unauthorized",
        request=httpx.Request("GET", "https://example.com"),
        response=httpx.Response(401)
    )
    
    classified = classify_error(error)
    assert classified.category == ErrorCategory.AUTHENTICATION
    assert classified.status_code == 401


def test_classify_error_http_429():
    """Test classification of 429 rate limit error."""
    error = httpx.HTTPStatusError(
        "Too many requests",
        request=httpx.Request("GET", "https://example.com"),
        response=httpx.Response(429)
    )
    
    classified = classify_error(error)
    assert classified.category == ErrorCategory.RATE_LIMITED
    assert classified.status_code == 429


def test_classify_error_http_500():
    """Test classification of 500 HTTP error."""
    error = httpx.HTTPStatusError(
        "Internal server error",
        request=httpx.Request("GET", "https://example.com"),
        response=httpx.Response(500)
    )
    
    classified = classify_error(error)
    assert classified.category == ErrorCategory.SERVICE_UNAVAILABLE
    assert classified.status_code == 500


def test_classify_error_timeout():
    """Test classification of timeout error."""
    error = httpx.TimeoutException("Request timed out")
    
    classified = classify_error(error)
    assert classified.category == ErrorCategory.TIMEOUT
    assert classified.status_code == 504


def test_classify_error_connect():
    """Test classification of connection error."""
    error = httpx.ConnectError("Connection failed")
    
    classified = classify_error(error)
    assert classified.category == ErrorCategory.SERVICE_UNAVAILABLE


def test_classify_error_validation():
    """Test classification of ValidationError."""
    error = ValidationError("test_field", "Invalid value")
    
    classified = classify_error(error)
    assert classified.category == ErrorCategory.VALIDATION


def test_classify_error_generic():
    """Test classification of generic exception."""
    error = Exception("Something went wrong")
    
    classified = classify_error(error)
    assert classified.category == ErrorCategory.UNKNOWN


def test_safe_error_response_with_exception():
    """Test safe_error_response with exception."""
    error = ValueError("Invalid value")
    response = safe_error_response(error)
    
    assert response["success"] is False
    assert "error" in response
    # ValueError gets classified as BAD_REQUEST
    assert response["error_code"] == "bad_request"


def test_safe_error_response_validation_error():
    """Test safe_error_response with ValidationError."""
    from qontak_mcp.validation import ValidationError
    error = ValidationError("test_field", "Test error message")
    response = safe_error_response(error, include_details=True)
    
    assert response["success"] is False
    assert response["error_code"] == "validation"
    assert "details" in response


def test_internal_error_response():
    """Test internal_error_response."""
    response = internal_error_response()
    
    assert response["success"] is False
    assert "error" in response
    assert response["error_code"] == "internal"
    assert "An internal error occurred" in response["error"]


def test_validation_error_response():
    """Test validation_error_response helper."""
    from qontak_mcp.errors import validation_error_response
    response = validation_error_response("name", "Required field")
    
    assert response["success"] is False
    assert response["error_code"] == "validation"
    assert "name" in response["details"]


def test_auth_error_response():
    """Test auth_error_response helper."""
    from qontak_mcp.errors import auth_error_response
    response = auth_error_response()
    
    assert response["success"] is False
    assert response["error_code"] == "authentication"


def test_rate_limit_error_response():
    """Test rate_limit_error_response helper."""
    from qontak_mcp.errors import rate_limit_error_response
    response = rate_limit_error_response(retry_after=60)
    
    assert response["success"] is False
    assert response["error_code"] == "rate_limited"
    assert response["retry_after"] == 60


def test_not_found_error_response():
    """Test not_found_error_response helper."""
    from qontak_mcp.errors import not_found_error_response
    response = not_found_error_response("deal")
    
    assert response["success"] is False
    assert response["error_code"] == "not_found"
    assert "deal" in response["error"]


class TestFormatValidationErrors:
    """Test format_validation_errors helper function."""
    
    def test_single_error(self):
        """Test formatting a single validation error."""
        from qontak_mcp.errors import format_validation_errors
        
        errors = [
            {"loc": ("body", "name"), "msg": "Field required"}
        ]
        result = format_validation_errors(errors)
        assert result == "name: Field required"
    
    def test_multiple_errors(self):
        """Test formatting multiple validation errors."""
        from qontak_mcp.errors import format_validation_errors
        
        errors = [
            {"loc": ("body", "name"), "msg": "Field required"},
            {"loc": ("body", "email"), "msg": "Invalid email format"}
        ]
        result = format_validation_errors(errors)
        assert "name: Field required" in result
        assert "email: Invalid email format" in result
        assert "; " in result  # Multiple errors joined by semicolon
    
    def test_error_without_location(self):
        """Test formatting error with empty location."""
        from qontak_mcp.errors import format_validation_errors
        
        errors = [
            {"loc": (), "msg": "General error"}
        ]
        result = format_validation_errors(errors)
        assert result == "unknown: General error"
    
    def test_error_without_message(self):
        """Test formatting error with default message."""
        from qontak_mcp.errors import format_validation_errors
        
        errors = [
            {"loc": ("field",)}
        ]
        result = format_validation_errors(errors)
        assert "field: invalid value" in result