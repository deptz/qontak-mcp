# Contributing to Qontak MCP

First off, thank you for considering contributing to this project! 🎉

## Code of Conduct

This project and everyone participating in it is governed by our [Code of Conduct](CODE_OF_CONDUCT.md). By participating, you are expected to uphold this code.

## How Can I Contribute?

### Reporting Bugs

Before creating bug reports, please check the existing issues to avoid duplicates. When you create a bug report, include as many details as possible:

- **Use a clear and descriptive title**
- **Describe the exact steps to reproduce the problem**
- **Provide specific examples** (code snippets, configuration, etc.)
- **Describe the behavior you observed and what you expected**
- **Include your environment details** (Python version, OS, etc.)

### Suggesting Enhancements

Enhancement suggestions are tracked as GitHub issues. When creating an enhancement suggestion:

- **Use a clear and descriptive title**
- **Provide a detailed description of the proposed enhancement**
- **Explain why this enhancement would be useful**
- **List any alternatives you've considered**

### Pull Requests

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run tests and linting (see below)
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to your branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

## Development Setup

### Prerequisites

- Python 3.10+
- Git

### Installation

```bash
# Clone your fork
git clone https://github.com/YOUR_USERNAME/qontak-mcp.git
cd qontak-mcp

# Create virtual environment
python -m venv venv
source venv/bin/activate  # macOS/Linux
# or .\venv\Scripts\activate on Windows

# Install development dependencies
pip install -e ".[dev,all]"

# Install pre-commit hooks
pre-commit install
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src/qontak_mcp

# Run specific test file
pytest tests/test_client.py
```

### Code Quality

We use several tools to maintain code quality:

```bash
# Type checking
mypy src/

# Linting and formatting
ruff check src/
ruff format src/

# Security audit
pip-audit
```

### Pre-commit Checks

We use `pre-commit` to ensure code quality. Before committing, the configured hooks will run automatically.

You can also run them manually:

```bash
pre-commit run --all-files
```

Before committing, ensure:

1. ✅ All tests pass
2. ✅ No type errors (`mypy src/`)
3. ✅ No linting errors (`ruff check src/`)
4. ✅ Code is formatted (`ruff format src/`)
5. ✅ No security vulnerabilities (`pip-audit`)

## Style Guidelines

### Python Code Style

- Follow [PEP 8](https://pep8.org/)
- Use type hints for all function signatures
- Maximum line length: 100 characters
- Use docstrings for all public functions and classes

### Commit Messages

- Use the present tense ("Add feature" not "Added feature")
- Use the imperative mood ("Move cursor to..." not "Moves cursor to...")
- Limit the first line to 72 characters
- Reference issues and pull requests when relevant

Examples:
```
Add support for custom deal fields
Fix token refresh race condition (#123)
Update documentation for Redis configuration
```

### Documentation

- Keep README.md up to date with any changes
- Document all public APIs
- Include examples for new features

## Project Structure

```
qontak-mcp/
├── src/qontak_mcp/         # Main package
│   ├── __init__.py         # Package exports
│   ├── auth.py             # Authentication logic
│   ├── client.py           # HTTP client
│   ├── errors.py           # Error handling
│   ├── logging.py          # Structured logging
│   ├── models.py           # Pydantic models
│   ├── rate_limit.py       # Rate limiting
│   ├── server.py           # MCP server entry point
│   ├── validation.py       # Input validation
│   ├── stores/             # Token storage backends
│   │   ├── base.py         # Protocol definition
│   │   ├── env.py          # Environment store
│   │   ├── redis.py        # Redis store
│   │   └── vault.py        # Vault store
│   └── tools/              # MCP tool implementations
│       ├── deals.py        # Deal operations
│       ├── tasks.py        # Task operations
│       └── tickets.py      # Ticket operations
├── tests/                  # Test files
├── pyproject.toml          # Project configuration
└── README.md               # Documentation
```

## Security

- Never commit credentials or secrets
- Report security vulnerabilities privately (see [SECURITY.md](SECURITY.md))
- Follow secure coding practices
- Use environment variables for configuration

## Questions?

Feel free to open an issue with the "question" label if you have any questions about contributing.

Thank you for contributing! 🙏
