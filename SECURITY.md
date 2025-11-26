# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 0.1.x   | :white_check_mark: |

## Reporting a Vulnerability

We take the security of Qontak MCP seriously. If you have discovered a security vulnerability, please report it responsibly.

### How to Report

**Please do NOT report security vulnerabilities through public GitHub issues.**

Instead, please send an email to the maintainers with:

1. **Description**: A clear description of the vulnerability
2. **Steps to Reproduce**: Detailed steps to reproduce the issue
3. **Impact**: Your assessment of the potential impact
4. **Affected Versions**: Which versions are affected
5. **Suggested Fix**: If you have one (optional)

### What to Expect

- **Acknowledgment**: We will acknowledge receipt within 48 hours
- **Initial Assessment**: We will provide an initial assessment within 7 days
- **Regular Updates**: We will keep you informed of our progress
- **Credit**: We will credit you in the security advisory (unless you prefer to remain anonymous)

### Disclosure Policy

- We follow coordinated disclosure practices
- We aim to fix critical vulnerabilities within 30 days
- We will publish a security advisory after the fix is released

## Security Best Practices

When using this MCP server, please follow these security practices:

### Token Storage

| Environment | Recommended Store | Notes |
|-------------|-------------------|-------|
| Development | `env` or `redis` | Never use real production credentials |
| Staging | `redis` | Use separate credentials from production |
| Production | `vault` | **Required** for production deployments |

### Configuration

1. **Never commit credentials** to version control
2. **Use `.env` files** only for local development
3. **Rotate tokens regularly** in production
4. **Use least-privilege access** for Vault tokens
5. **Enable audit logging** in production environments

### Network Security

1. Use HTTPS for all Vault and Redis connections in production
2. Configure proper firewall rules
3. Use private networks where possible
4. Enable TLS for Redis connections

### Audit Logging

The server includes structured security logging. Enable and monitor:

```python
from qontak_mcp.logging import configure_logger, SecurityEventType

configure_logger(
    level="INFO",
    enable_security_events=True
)
```

## Known Security Considerations

### Token Storage

- **Environment Store**: Tokens are stored in memory only. Suitable for development.
- **Redis Store**: Tokens are stored in plain text. Use only in trusted networks.
- **Vault Store**: Tokens are encrypted at rest with audit logging. Recommended for production.

### API Rate Limiting

The server includes built-in rate limiting to prevent API abuse. Default configuration:

- 120 requests per minute per user
- Configurable via `RateLimitConfig`

### Input Validation

All inputs are validated using Pydantic models to prevent:

- Injection attacks
- Invalid data types
- Resource enumeration

## Vulnerability Disclosure Timeline

1. **Day 0**: Vulnerability reported
2. **Day 2**: Acknowledgment sent
3. **Day 7**: Initial assessment completed
4. **Day 14**: Fix developed and tested
5. **Day 21**: Fix released (for critical issues)
6. **Day 28**: Security advisory published

For non-critical issues, the timeline may be extended.

## Security Updates

Security updates will be released as patch versions (e.g., 0.1.1, 0.1.2).

To stay informed:
- Watch the repository for releases
- Check the CHANGELOG.md for security-related updates
- Subscribe to security advisories (when available)

## Dependencies

We regularly audit our dependencies for known vulnerabilities:

```bash
# Run security audit
pip-audit
```

Dependencies are pinned to specific versions to ensure reproducibility and security.
