"""
Structured logging for security and audit purposes.

This module provides:
- Structured JSON logging for easy parsing
- Security event logging
- Audit trail for API operations
- Sensitive data redaction
"""

import logging
import json
import re
import sys
import os
import time
import uuid
from typing import Optional, Any
from datetime import datetime, timezone
from dataclasses import dataclass, asdict
from enum import Enum
from functools import wraps


# =============================================================================
# Log Levels and Event Types
# =============================================================================

class SecurityEventType(str, Enum):
    """Types of security-relevant events."""
    
    # Authentication events
    AUTH_SUCCESS = "auth.success"
    AUTH_FAILURE = "auth.failure"
    AUTH_TOKEN_REFRESH = "auth.token_refresh"
    AUTH_TOKEN_EXPIRED = "auth.token_expired"
    
    # Authorization events
    AUTHZ_DENIED = "authz.denied"
    AUTHZ_GRANTED = "authz.granted"
    
    # Validation events
    VALIDATION_FAILURE = "validation.failure"
    VALIDATION_INJECTION_ATTEMPT = "validation.injection_attempt"
    
    # Rate limiting events
    RATE_LIMIT_EXCEEDED = "rate_limit.exceeded"
    RATE_LIMIT_WARNING = "rate_limit.warning"
    
    # API events
    API_REQUEST = "api.request"
    API_RESPONSE = "api.response"
    API_ERROR = "api.error"
    
    # System events
    SYSTEM_STARTUP = "system.startup"
    SYSTEM_SHUTDOWN = "system.shutdown"
    SYSTEM_ERROR = "system.error"


class LogLevel(str, Enum):
    """Log levels."""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


# =============================================================================
# Sensitive Data Patterns
# =============================================================================

# Fields that should be redacted in logs
SENSITIVE_FIELDS = {
    'password', 'token', 'access_token', 'refresh_token', 
    'api_key', 'secret', 'authorization', 'credential',
    'credit_card', 'ssn', 'social_security',
}

# Patterns that look like secrets (for header values, etc.)
SECRET_PATTERNS = [
    r'Bearer\s+[A-Za-z0-9\-_]+',
    r'[A-Za-z0-9]{32,}',  # Long alphanumeric strings
]

# Patterns in string content that should be redacted
# These are compiled for performance
CONTENT_REDACT_PATTERNS = [
    # Connection strings with credentials
    re.compile(r'(postgres|mysql|mongodb|redis|amqp|mssql)://[^@]+:[^@]+@[^\s]+', re.IGNORECASE),
    # Bearer tokens
    re.compile(r'Bearer\s+[A-Za-z0-9\-_\.]+', re.IGNORECASE),
    # API keys in various formats
    re.compile(r'(api[_-]?key|apikey|api_secret|secret_key)[=:]\s*["\']?[A-Za-z0-9\-_]+["\']?', re.IGNORECASE),
    # AWS-style keys
    re.compile(r'AKIA[A-Z0-9]{16}'),
    # Generic secrets in key=value format
    re.compile(r'(password|passwd|pwd|secret|token)[=:]\s*["\']?[^\s"\']+["\']?', re.IGNORECASE),
]


# =============================================================================
# Structured Log Entry
# =============================================================================

@dataclass
class LogEntry:
    """Structured log entry."""
    
    timestamp: str
    level: str
    event_type: str
    message: str
    
    # Context
    request_id: Optional[str] = None
    user_id: Optional[str] = None
    
    # Additional data
    data: Optional[dict] = None
    
    # Error information
    error_type: Optional[str] = None
    error_message: Optional[str] = None
    
    # Performance
    duration_ms: Optional[float] = None
    
    def to_dict(self) -> dict:
        """Convert to dictionary, excluding None values."""
        result = {}
        for key, value in asdict(self).items():
            if value is not None:
                result[key] = value
        return result
    
    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), default=str)


# =============================================================================
# JSON Log Formatter
# =============================================================================

class StructuredFormatter(logging.Formatter):
    """JSON formatter for structured logging."""
    
    def __init__(self, redact_sensitive: bool = True):
        super().__init__()
        self.redact_sensitive = redact_sensitive
    
    def format(self, record: logging.LogRecord) -> str:
        # Build base log entry
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        
        # Add extra fields from record
        for key in ['event_type', 'request_id', 'user_id', 'data', 
                    'error_type', 'error_message', 'duration_ms']:
            if hasattr(record, key):
                value = getattr(record, key)
                if value is not None:
                    entry[key] = value
        
        # Add exception info if present
        if record.exc_info:
            entry['exception'] = self.formatException(record.exc_info)
        
        # Redact sensitive data
        if self.redact_sensitive:
            entry = self._redact_sensitive(entry)
        
        return json.dumps(entry, default=str)
    
    def _redact_sensitive(self, data: Any, path: str = "") -> Any:
        """Recursively redact sensitive fields."""
        if isinstance(data, dict):
            result = {}
            for key, value in data.items():
                key_lower = key.lower()
                if any(s in key_lower for s in SENSITIVE_FIELDS):
                    result[key] = "[REDACTED]"
                else:
                    result[key] = self._redact_sensitive(value, f"{path}.{key}")
            return result
        elif isinstance(data, list):
            return [self._redact_sensitive(item, f"{path}[]") for item in data]
        elif isinstance(data, str):
            # Redact strings that look like tokens (long alphanumeric)
            if len(data) > 30 and data.isalnum():
                return "[REDACTED]"
            
            # Redact sensitive patterns in string content
            redacted = data
            for pattern in CONTENT_REDACT_PATTERNS:
                redacted = pattern.sub("[REDACTED]", redacted)
            return redacted
        return data


# =============================================================================
# Security Logger
# =============================================================================

class SecurityLogger:
    """
    Security-focused structured logger.
    
    Provides methods for logging security-relevant events with
    proper context and sensitive data redaction.
    """
    
    def __init__(
        self,
        name: str = "qontak_mcp",
        level: str = "INFO",
        json_output: bool = True,
        redact_sensitive: bool = True,
    ):
        """
        Initialize the security logger.
        
        Args:
            name: Logger name
            level: Minimum log level
            json_output: Whether to use JSON formatting
            redact_sensitive: Whether to redact sensitive data
        """
        self.logger = logging.getLogger(name)
        self.logger.setLevel(getattr(logging, level.upper()))
        
        # Remove existing handlers
        self.logger.handlers.clear()
        
        # Add handler with appropriate formatter
        handler = logging.StreamHandler(sys.stderr)
        if json_output:
            handler.setFormatter(StructuredFormatter(redact_sensitive))
        else:
            handler.setFormatter(logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            ))
        self.logger.addHandler(handler)
        
        # Request context
        self._request_id: Optional[str] = None
        self._user_id: Optional[str] = None
    
    def set_context(
        self,
        request_id: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> None:
        """Set context for subsequent log entries."""
        self._request_id = request_id
        self._user_id = user_id
    
    def clear_context(self) -> None:
        """Clear the current context."""
        self._request_id = None
        self._user_id = None
    
    def generate_request_id(self) -> str:
        """Generate a new unique request ID."""
        return str(uuid.uuid4())[:8]
    
    def _log(
        self,
        level: int,
        event_type: SecurityEventType,
        message: str,
        data: Optional[dict] = None,
        error: Optional[Exception] = None,
        duration_ms: Optional[float] = None,
        user_id: Optional[str] = None,
    ) -> None:
        """Internal logging method."""
        extra = {
            'event_type': event_type.value,
            'request_id': self._request_id,
            'user_id': user_id or self._user_id,
            'data': data,
            'duration_ms': duration_ms,
        }
        
        if error:
            extra['error_type'] = type(error).__name__
            extra['error_message'] = str(error)
        
        self.logger.log(level, message, extra=extra, exc_info=error if level >= logging.ERROR else None)
    
    # =========================================================================
    # Authentication Events
    # =========================================================================
    
    def auth_success(self, user_id: str, method: str = "token") -> None:
        """Log successful authentication."""
        self._log(
            logging.INFO,
            SecurityEventType.AUTH_SUCCESS,
            f"Authentication successful via {method}",
            data={"method": method},
            user_id=user_id,
        )
    
    def auth_failure(self, reason: str, user_id: Optional[str] = None) -> None:
        """Log authentication failure."""
        self._log(
            logging.WARNING,
            SecurityEventType.AUTH_FAILURE,
            f"Authentication failed: {reason}",
            data={"reason": reason},
            user_id=user_id,
        )
    
    def token_refresh(self, user_id: Optional[str] = None) -> None:
        """Log token refresh."""
        self._log(
            logging.INFO,
            SecurityEventType.AUTH_TOKEN_REFRESH,
            "Access token refreshed",
            user_id=user_id,
        )
    
    # =========================================================================
    # Validation Events
    # =========================================================================
    
    def validation_failure(
        self,
        field: str,
        reason: str,
        value_type: str = "unknown",
        user_id: Optional[str] = None,
    ) -> None:
        """Log validation failure."""
        self._log(
            logging.WARNING,
            SecurityEventType.VALIDATION_FAILURE,
            f"Validation failed for field '{field}': {reason}",
            data={"field": field, "reason": reason, "value_type": value_type},
            user_id=user_id,
        )
    
    def injection_attempt(
        self,
        field: str,
        pattern: str,
        user_id: Optional[str] = None,
    ) -> None:
        """Log potential injection attempt (HIGH SEVERITY)."""
        self._log(
            logging.ERROR,
            SecurityEventType.VALIDATION_INJECTION_ATTEMPT,
            f"Potential injection attempt detected in field '{field}'",
            data={"field": field, "pattern": pattern},
            user_id=user_id,
        )
    
    # =========================================================================
    # Rate Limiting Events
    # =========================================================================
    
    def rate_limit_exceeded(self, user_id: Optional[str] = None) -> None:
        """Log rate limit exceeded."""
        self._log(
            logging.WARNING,
            SecurityEventType.RATE_LIMIT_EXCEEDED,
            "Rate limit exceeded",
            user_id=user_id,
        )
    
    def rate_limit_warning(
        self,
        remaining: float,
        user_id: Optional[str] = None,
    ) -> None:
        """Log rate limit warning (approaching limit)."""
        self._log(
            logging.INFO,
            SecurityEventType.RATE_LIMIT_WARNING,
            f"Rate limit warning: {remaining:.1f} tokens remaining",
            data={"remaining_tokens": remaining},
            user_id=user_id,
        )
    
    # =========================================================================
    # API Events
    # =========================================================================
    
    def api_request(
        self,
        method: str,
        path: str,
        user_id: Optional[str] = None,
    ) -> None:
        """Log API request."""
        self._log(
            logging.DEBUG,
            SecurityEventType.API_REQUEST,
            f"API request: {method} {path}",
            data={"method": method, "path": path},
            user_id=user_id,
        )
    
    def api_response(
        self,
        method: str,
        path: str,
        status_code: int,
        duration_ms: float,
        user_id: Optional[str] = None,
    ) -> None:
        """Log API response."""
        level = logging.DEBUG if status_code < 400 else logging.WARNING
        self._log(
            level,
            SecurityEventType.API_RESPONSE,
            f"API response: {method} {path} -> {status_code} ({duration_ms:.1f}ms)",
            data={"method": method, "path": path, "status_code": status_code},
            duration_ms=duration_ms,
            user_id=user_id,
        )
    
    def api_error(
        self,
        method: str,
        path: str,
        error: Exception,
        user_id: Optional[str] = None,
    ) -> None:
        """Log API error."""
        self._log(
            logging.ERROR,
            SecurityEventType.API_ERROR,
            f"API error: {method} {path} - {type(error).__name__}",
            data={"method": method, "path": path},
            error=error,
            user_id=user_id,
        )
    
    # =========================================================================
    # System Events
    # =========================================================================
    
    def system_startup(self, version: str) -> None:
        """Log system startup."""
        self._log(
            logging.INFO,
            SecurityEventType.SYSTEM_STARTUP,
            f"MCP server starting (version {version})",
            data={"version": version},
        )
    
    def system_shutdown(self) -> None:
        """Log system shutdown."""
        self._log(
            logging.INFO,
            SecurityEventType.SYSTEM_SHUTDOWN,
            "MCP server shutting down",
        )
    
    def system_error(self, error: Exception, context: str = "") -> None:
        """Log system error."""
        self._log(
            logging.ERROR,
            SecurityEventType.SYSTEM_ERROR,
            f"System error{': ' + context if context else ''}",
            error=error,
        )


# =============================================================================
# Global Logger Instance
# =============================================================================

_logger: Optional[SecurityLogger] = None


def get_logger() -> SecurityLogger:
    """Get or create the global security logger."""
    global _logger
    if _logger is None:
        # Read config from environment
        log_level = os.getenv("LOG_LEVEL", "INFO")
        json_output = os.getenv("LOG_FORMAT", "json").lower() == "json"
        redact = os.getenv("LOG_REDACT_SENSITIVE", "true").lower() == "true"
        
        _logger = SecurityLogger(
            level=log_level,
            json_output=json_output,
            redact_sensitive=redact,
        )
    return _logger


def configure_logger(
    level: str = "INFO",
    json_output: bool = True,
    redact_sensitive: bool = True,
) -> SecurityLogger:
    """Configure and return the global logger."""
    global _logger
    _logger = SecurityLogger(
        level=level,
        json_output=json_output,
        redact_sensitive=redact_sensitive,
    )
    return _logger


# =============================================================================
# Logging Decorator
# =============================================================================

def log_operation(event_type: SecurityEventType = SecurityEventType.API_REQUEST):
    """Decorator to log function execution with timing."""
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            logger = get_logger()
            start_time = time.monotonic()
            
            try:
                result = await func(*args, **kwargs)
                duration_ms = (time.monotonic() - start_time) * 1000
                logger._log(
                    logging.DEBUG,
                    event_type,
                    f"Operation completed: {func.__name__}",
                    duration_ms=duration_ms,
                )
                return result
            except Exception as e:
                duration_ms = (time.monotonic() - start_time) * 1000
                logger._log(
                    logging.ERROR,
                    SecurityEventType.API_ERROR,
                    f"Operation failed: {func.__name__}",
                    error=e,
                    duration_ms=duration_ms,
                )
                raise
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            logger = get_logger()
            start_time = time.monotonic()
            
            try:
                result = func(*args, **kwargs)
                duration_ms = (time.monotonic() - start_time) * 1000
                logger._log(
                    logging.DEBUG,
                    event_type,
                    f"Operation completed: {func.__name__}",
                    duration_ms=duration_ms,
                )
                return result
            except Exception as e:
                duration_ms = (time.monotonic() - start_time) * 1000
                logger._log(
                    logging.ERROR,
                    SecurityEventType.API_ERROR,
                    f"Operation failed: {func.__name__}",
                    error=e,
                    duration_ms=duration_ms,
                )
                raise
        
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper
    
    return decorator
