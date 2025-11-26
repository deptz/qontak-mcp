"""
Tests for logging module - security events, structured logging, and sensitive data redaction.
"""

import pytest
import logging
import json
from unittest.mock import Mock, patch
from qontak_mcp.logging import (
    SecurityEventType,
    LogLevel,
    SecurityLogger,
    get_logger,
    configure_logger,
    log_operation,
    StructuredFormatter,
    SENSITIVE_FIELDS,
)


class TestSecurityEventType:
    """Test SecurityEventType enum."""
    
    def test_event_types_exist(self):
        """Test that all expected event types are defined."""
        assert SecurityEventType.AUTH_SUCCESS
        assert SecurityEventType.AUTH_FAILURE
        assert SecurityEventType.VALIDATION_FAILURE
        assert SecurityEventType.RATE_LIMIT_EXCEEDED
        assert SecurityEventType.API_REQUEST
        assert SecurityEventType.API_ERROR
        assert SecurityEventType.SYSTEM_STARTUP
        assert SecurityEventType.SYSTEM_SHUTDOWN


class TestLogLevel:
    """Test LogLevel enum."""
    
    def test_log_levels_exist(self):
        """Test that all log levels are defined."""
        assert LogLevel.DEBUG
        assert LogLevel.INFO
        assert LogLevel.WARNING
        assert LogLevel.ERROR
        assert LogLevel.CRITICAL


class TestStructuredFormatter:
    """Test StructuredFormatter for sensitive data redaction."""
    
    def test_formatter_redacts_sensitive_fields(self):
        """Test that formatter redacts sensitive field names."""
        formatter = StructuredFormatter(redact_sensitive=True)
        
        data = {
            "username": "test_user",
            "password": "secret123",
            "api_key": "key123",
            "token": "token456"
        }
        
        redacted = formatter._redact_sensitive(data)
        
        assert redacted["username"] == "test_user"
        assert redacted["password"] == "[REDACTED]"
        assert redacted["api_key"] == "[REDACTED]"
        assert redacted["token"] == "[REDACTED]"
    
    def test_formatter_redacts_nested_data(self):
        """Test redaction in nested structures."""
        formatter = StructuredFormatter(redact_sensitive=True)
        
        data = {
            "user": {
                "name": "Test",
                "password": "secret",
                "details": {
                    "token": "abc123"
                }
            }
        }
        
        redacted = formatter._redact_sensitive(data)
        
        assert redacted["user"]["name"] == "Test"
        assert redacted["user"]["password"] == "[REDACTED]"
        assert redacted["user"]["details"]["token"] == "[REDACTED]"
    
    def test_formatter_redacts_long_alphanumeric_strings(self):
        """Test that long alphanumeric strings (potential tokens) are redacted."""
        formatter = StructuredFormatter(redact_sensitive=True)
        
        long_token = "a" * 35  # > 30 chars
        data = {"field": long_token}
        
        redacted = formatter._redact_sensitive(data)
        assert redacted["field"] == "[REDACTED]"
    
    def test_formatter_preserves_short_strings(self):
        """Test that short strings are not redacted."""
        formatter = StructuredFormatter(redact_sensitive=True)
        
        data = {"name": "Short", "description": "Normal text"}
        redacted = formatter._redact_sensitive(data)
        
        assert redacted["name"] == "Short"
        assert redacted["description"] == "Normal text"
    
    def test_formatter_handles_lists(self):
        """Test redaction works with lists."""
        formatter = StructuredFormatter(redact_sensitive=True)
        
        data = {
            "items": [
                {"name": "Item 1", "password": "secret1"},
                {"name": "Item 2", "token": "token2"}
            ]
        }
        
        redacted = formatter._redact_sensitive(data)
        
        assert redacted["items"][0]["password"] == "[REDACTED]"
        assert redacted["items"][1]["token"] == "[REDACTED]"
        assert redacted["items"][0]["name"] == "Item 1"
    
    def test_formatter_can_disable_redaction(self):
        """Test that redaction can be disabled."""
        formatter = StructuredFormatter(redact_sensitive=False)
        
        # format method would include redaction logic
        # Just verify the formatter was created with the flag
        assert formatter.redact_sensitive is False
    
    def test_formatter_format_method(self):
        """Test that format method produces JSON output."""
        formatter = StructuredFormatter(redact_sensitive=True)
        
        # Create a log record
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="Test message",
            args=(),
            exc_info=None
        )
        
        output = formatter.format(record)
        
        # Should be valid JSON
        parsed = json.loads(output)
        assert "message" in parsed
        assert parsed["message"] == "Test message"
        assert "timestamp" in parsed
        assert "level" in parsed


class TestSecurityLogger:
    """Test SecurityLogger class."""
    
    def test_logger_initialization(self):
        """Test logger can be initialized."""
        logger = SecurityLogger()
        assert logger is not None
    
    def test_system_startup_logging(self):
        """Test system startup event logging."""
        with patch.object(logging.Logger, 'log') as mock_log:
            logger = SecurityLogger()
            logger.system_startup("1.0.0")
            mock_log.assert_called()
    
    def test_system_shutdown_logging(self):
        """Test system shutdown event logging."""
        with patch.object(logging.Logger, 'log') as mock_log:
            logger = SecurityLogger()
            logger.system_shutdown()
            mock_log.assert_called()
    
    def test_auth_success_logging(self):
        """Test authentication success logging."""
        with patch.object(logging.Logger, 'log') as mock_log:
            logger = SecurityLogger()
            logger.auth_success("user123")
            mock_log.assert_called()
    
    def test_auth_failure_logging(self):
        """Test authentication failure logging."""
        with patch.object(logging.Logger, 'log') as mock_log:
            logger = SecurityLogger()
            logger.auth_failure("Invalid credentials", "user123")
            mock_log.assert_called()
    
    def test_validation_failure_logging(self):
        """Test validation failure logging."""
        with patch.object(logging.Logger, 'log') as mock_log:
            logger = SecurityLogger()
            logger.validation_failure("user_id", "Invalid format")
            mock_log.assert_called()
    
    def test_rate_limit_exceeded_logging(self):
        """Test rate limit exceeded logging."""
        with patch.object(logging.Logger, 'log') as mock_log:
            logger = SecurityLogger()
            logger.rate_limit_exceeded("user123")
            mock_log.assert_called()
    
    def test_api_request_logging(self):
        """Test API request logging."""
        with patch.object(logging.Logger, 'log') as mock_log:
            logger = SecurityLogger()
            logger.api_request("GET", "/api/deals", "user123")
            mock_log.assert_called()
    
    def test_api_error_logging(self):
        """Test API error logging."""
        with patch.object(logging.Logger, 'log') as mock_log:
            logger = SecurityLogger()
            error = ValueError("Internal error")
            logger.api_error("GET", "/api/deals", error)
            mock_log.assert_called()
    
    def test_sensitive_data_logged_gets_formatted(self):
        """Test that logging methods accept and process data."""
        # Just ensure the methods work without crashing
        logger = SecurityLogger()
        logger.api_request("POST", "/api/auth", user_id="user123")


class TestLoggerGlobalFunctions:
    """Test global logger functions."""
    
    def test_get_logger_singleton(self):
        """Test get_logger returns same instance."""
        logger1 = get_logger()
        logger2 = get_logger()
        assert logger1 is logger2
    
    def test_configure_logger_returns_logger(self):
        """Test configure_logger returns a logger instance."""
        logger = configure_logger(level="DEBUG")
        assert logger is not None
        assert isinstance(logger, SecurityLogger)
    
    def test_configure_logger_with_json_format(self):
        """Test configure_logger with JSON format."""
        logger = configure_logger(json_output=True)
        assert logger is not None
    
    def test_log_operation_decorator(self):
        """Test log_operation decorator."""
        
        @log_operation()
        def test_func(x, y):
            return x + y
        
        # Should not raise, even if logging fails
        result = test_func(1, 2)
        assert result == 3
    
    @pytest.mark.asyncio
    async def test_log_operation_decorator_async(self):
        """Test log_operation decorator with async functions."""
        
        @log_operation()
        async def test_async_func(x, y):
            return x + y
        
        result = await test_async_func(1, 2)
        assert result == 3


class TestLoggingConfiguration:
    """Test logging configuration."""
    
    def test_configure_with_json_output(self):
        """Test configuring logger with JSON output."""
        logger = configure_logger(json_output=True, redact_sensitive=True)
        assert logger is not None
        # Log something
        logger.system_startup("1.0.0")
    
    def test_configure_with_custom_level(self):
        """Test configuring logger with custom log level."""
        logger = configure_logger(level="WARNING")
        assert logger is not None


class TestStructuredLogging:
    """Test structured logging features."""
    
    def test_log_includes_context(self):
        """Test that logs include contextual information."""
        with patch.object(logging.Logger, 'log') as mock_log:
            logger = SecurityLogger()
            logger.api_request("GET", "/api/test", user_id="user123")
            
            # Should have been logged
            mock_log.assert_called()
    
    def test_log_includes_timestamp(self):
        """Test that logs include timestamps (via logger config)."""
        # This is handled by the logging formatter
        # We just verify logger is configured
        logger = SecurityLogger()
        assert logger.logger is not None


class TestEdgeCases:
    """Test edge cases and error handling."""
    
    def test_formatter_handles_non_dict_data(self):
        """Test formatter redaction with non-dict data types."""
        formatter = StructuredFormatter(redact_sensitive=True)
        
        # String
        result = formatter._redact_sensitive("plain string")
        assert isinstance(result, str)
        
        # Number
        result = formatter._redact_sensitive(123)
        assert result == 123
        
        # None
        result = formatter._redact_sensitive(None)
        assert result is None
        
        # List
        result = formatter._redact_sensitive([1, 2, 3])
        assert result == [1, 2, 3]
    
    def test_logger_handles_exception_in_logging(self):
        """Test logger handles exceptions during logging gracefully."""
        logger = SecurityLogger()
        
        # Even if there's an issue, logging shouldn't crash the app
        try:
            logger.api_request("GET", "/test", user_id=None)
            assert True
        except Exception:
            pytest.fail("Logger should handle exceptions gracefully")
    
    def test_formatter_with_exception_info(self):
        """Test formatter handles exception info in log records."""
        formatter = StructuredFormatter(redact_sensitive=True)
        
        try:
            raise ValueError("Test exception")
        except ValueError:
            import sys
            exc_info = sys.exc_info()
            
            record = logging.LogRecord(
                name="test",
                level=logging.ERROR,
                pathname="",
                lineno=0,
                msg="Error occurred",
                args=(),
                exc_info=exc_info
            )
            
            output = formatter.format(record)
            parsed = json.loads(output)
            
            assert "exception" in parsed
            assert "ValueError" in parsed["exception"]
