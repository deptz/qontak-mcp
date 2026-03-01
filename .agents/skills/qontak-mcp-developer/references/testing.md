# Testing Patterns

## Test Organization

```
tests/
├── conftest.py              # Shared fixtures
├── test_auth.py             # Authentication tests
├── test_client.py           # Client/HTTP tests
├── test_models.py           # Pydantic model tests
├── test_validation.py       # Validation function tests
├── test_server.py           # Server/lifespan tests
├── stores/
│   ├── test_env.py
│   ├── test_redis.py
│   └── test_stores_init.py
├── tools/
│   ├── conftest.py          # Tool fixtures
│   ├── test_deals.py        # Deal tool tests
│   ├── test_contacts.py     # Contact tool tests
│   └── ...
└── integration/
    ├── conftest.py          # Integration config
    └── test_*_integration.py # Real API tests
```

## Fixtures

### Mock Client Fixture

```python
# tests/conftest.py
import pytest
from unittest.mock import AsyncMock, MagicMock


@pytest.fixture
def mock_auth():
    """Create mock QontakAuth."""
    auth = MagicMock()
    auth.get_auth_headers = AsyncMock(return_value={"Authorization": "Bearer test"})
    return auth


@pytest.fixture
def mock_client(mock_auth):
    """Create mock QontakClient."""
    from qontak_mcp.client import QontakClient
    
    client = QontakClient(auth=mock_auth)
    client._request = AsyncMock()
    return client


@pytest.fixture
def mock_http_response():
    """Factory for mock HTTP responses."""
    def _make_response(status_code=200, json_data=None, text=""):
        response = MagicMock()
        response.status_code = status_code
        response.json = AsyncMock(return_value=json_data or {})
        response.text = text
        return response
    return _make_response
```

### Tool Fixtures

```python
# tests/tools/conftest.py
import pytest
from unittest.mock import MagicMock


@pytest.fixture
def mock_get_client():
    """Factory for mock get_client function."""
    def _make_client(mock_response=None):
        client = MagicMock()
        
        # Set up all async methods to return mock_response
        for method in [
            'get_deal', 'list_deals', 'create_deal', 'update_deal',
            'get_contact', 'list_contacts', 'create_contact',
            # ... all client methods
        ]:
            setattr(client, method, AsyncMock(return_value=mock_response or {
                "success": True,
                "data": {}
            }))
        
        return lambda: client
    return _make_client
```

## Unit Test Patterns

### Testing Client Methods

```python
# tests/test_client.py
import pytest
from qontak_mcp.client import QontakClient


class TestDealOperations:
    @pytest.mark.asyncio
    async def test_list_deals_success(self, mock_auth, mock_http_response):
        """Test successful deal listing."""
        client = QontakClient(auth=mock_auth)
        
        mock_response = mock_http_response(
            status_code=200,
            json_data={"response": [{"id": 1, "name": "Deal 1"}]}
        )
        client._http_client = MagicMock()
        client._http_client.request = AsyncMock(return_value=mock_response)
        
        result = await client.list_deals(page=1, per_page=25)
        
        assert result["success"] is True
        assert len(result["data"]["response"]) == 1
    
    @pytest.mark.asyncio
    async def test_list_deals_validation_error(self, mock_auth):
        """Test validation of invalid pagination."""
        client = QontakClient(auth=mock_auth)
        
        result = await client.list_deals(page=0, per_page=25)  # Invalid page
        
        assert result["success"] is False
        assert "page" in result["error"].lower()
    
    @pytest.mark.asyncio
    async def test_get_deal_api_error(self, mock_auth, mock_http_response):
        """Test handling of API error response."""
        client = QontakClient(auth=mock_auth)
        
        mock_response = mock_http_response(
            status_code=404,
            json_data={"message": "Deal not found"}
        )
        client._http_client = MagicMock()
        client._http_client.request = AsyncMock(return_value=mock_response)
        
        result = await client.get_deal(deal_id=999)
        
        assert result["success"] is False
        assert result["status_code"] == 404
```

### Testing Tools

```python
# tests/tools/test_deals.py
import pytest
import json
from qontak_mcp.tools.deals import register_deal_tools_lazy


class TestGetDealTemplate:
    @pytest.mark.asyncio
    async def test_returns_json_string(self, mock_get_client):
        """Tool must return JSON string."""
        mock_response = {
            "success": True,
            "data": {"fields": []}
        }
        get_client = mock_get_client(mock_response)
        
        # Create minimal MCP for registration
        mcp = MagicMock()
        tools = {}
        mcp.tool = lambda: lambda f: tools.update({f.__name__: f})
        
        register_deal_tools_lazy(mcp, get_client)
        
        result = await tools["get_deal_template"]()
        parsed = json.loads(result)
        
        assert "success" in parsed
        assert parsed["success"] is True
    
    @pytest.mark.asyncio
    async def test_handles_exception(self, mock_get_client):
        """Tool must handle exceptions gracefully."""
        def failing_client():
            raise RuntimeError("Connection failed")
        
        mcp = MagicMock()
        tools = {}
        mcp.tool = lambda: lambda f: tools.update({f.__name__: f})
        
        register_deal_tools_lazy(mcp, failing_client)
        
        result = await tools["get_deal_template"]()
        parsed = json.loads(result)
        
        assert parsed["success"] is False
        assert "error" in parsed
```

### Testing Models

```python
# tests/test_models.py
import pytest
from pydantic import ValidationError
from qontak_mcp.models import DealCreateParams, ContactUpdateParams


class TestDealCreateParams:
    def test_valid_creation(self):
        """Test valid parameter creation."""
        params = DealCreateParams(
            name="Test Deal",
            crm_pipeline_id=123,
            crm_stage_id=456
        )
        assert params.name == "Test Deal"
        assert params.crm_pipeline_id == 123
    
    def test_name_required(self):
        """Test name is required."""
        with pytest.raises(ValidationError) as exc:
            DealCreateParams(
                name="",  # Empty name
                crm_pipeline_id=123,
                crm_stage_id=456
            )
        assert "name" in str(exc.value)
    
    def test_date_validation(self):
        """Test date format validation."""
        with pytest.raises(ValidationError) as exc:
            DealCreateParams(
                name="Test Deal",
                crm_pipeline_id=123,
                crm_stage_id=456,
                expected_close_date="invalid-date"
            )
        assert "expected_close_date" in str(exc.value)
    
    def test_user_id_sanitization(self):
        """Test user_id validation."""
        # Valid user_id
        params = DealCreateParams(
            name="Test",
            crm_pipeline_id=1,
            crm_stage_id=1,
            user_id="user_123-abc"
        )
        assert params.user_id == "user_123-abc"
        
        # Invalid user_id
        with pytest.raises(ValidationError):
            DealCreateParams(
                name="Test",
                crm_pipeline_id=1,
                crm_stage_id=1,
                user_id="user@example.com"  # Invalid chars
            )
```

### Testing Validation Functions

```python
# tests/test_validation.py
import pytest
from qontak_mcp.validation import (
    validate_user_id,
    validate_resource_id,
    validate_pagination,
    ValidationResult
)


class TestValidateUserId:
    def test_none_is_valid(self):
        """None user_id is valid (single-tenant)."""
        result = validate_user_id(None)
        assert result.is_valid is True
        assert result.sanitized_value is None
    
    def test_valid_user_id(self):
        """Valid alphanumeric user_id."""
        result = validate_user_id("user_123")
        assert result.is_valid is True
        assert result.sanitized_value == "user_123"
    
    def test_path_trajection_rejected(self):
        """Reject path traversal attempts."""
        result = validate_user_id("../etc/passwd")
        assert result.is_valid is False
    
    def test_sql_injection_rejected(self):
        """Reject SQL injection patterns."""
        result = validate_user_id("user'; DROP TABLE users--")
        assert result.is_valid is False


class TestValidateResourceId:
    def test_positive_integer(self):
        """Valid positive integer."""
        result = validate_resource_id(123, "deal_id")
        assert result.is_valid is True
        assert result.sanitized_value == 123
    
    def test_zero_rejected(self):
        """Zero is invalid."""
        result = validate_resource_id(0, "deal_id")
        assert result.is_valid is False
    
    def test_negative_rejected(self):
        """Negative numbers invalid."""
        result = validate_resource_id(-1, "deal_id")
        assert result.is_valid is False


class TestValidatePagination:
    def test_defaults_valid(self):
        """Default pagination is valid."""
        result = validate_pagination()
        assert result.is_valid is True
        assert result.sanitized_value == {"page": 1, "per_page": 25}
    
    def test_per_page_max(self):
        """Per page cannot exceed 100."""
        result = validate_pagination(per_page=200)
        assert result.is_valid is False
```

## Integration Tests

### Marking Integration Tests

```python
# tests/integration/test_deals_integration.py
import pytest

pytestmark = pytest.mark.integration_manual


class TestDealIntegration:
    """Tests requiring real Qontak API access."""
    
    @pytest.mark.asyncio
    async def test_create_and_delete_deal(self, real_client):
        """Test full deal lifecycle."""
        # Create
        create_result = await real_client.create_deal({
            "name": "Integration Test Deal",
            "crm_pipeline_id": 123,
            "crm_stage_id": 456
        })
        
        assert create_result["success"] is True
        deal_id = create_result["data"]["response"]["id"]
        
        try:
            # Read
            get_result = await real_client.get_deal(deal_id)
            assert get_result["success"] is True
            
            # Update
            update_result = await real_client.update_deal(
                deal_id,
                {"name": "Updated Deal"}
            )
            assert update_result["success"] is True
        finally:
            # Cleanup
            await real_client.delete_deal(deal_id)
```

### Integration Fixtures

```python
# tests/integration/conftest.py
import pytest
import os
from qontak_mcp.client import QontakClient
from qontak_mcp.auth import QontakAuth
from qontak_mcp.stores import get_token_store


@pytest.fixture(scope="session")
async def real_client():
    """Create real client for integration tests."""
    if not os.getenv("QONTAK_REFRESH_TOKEN"):
        pytest.skip("QONTAK_REFRESH_TOKEN not set")
    
    store = get_token_store()
    auth = QontakAuth(store=store)
    client = QontakClient(auth=auth)
    
    yield client
    
    await client.close()
```

## Coverage Configuration

```toml
# pyproject.toml
[tool.coverage.run]
source = ["src/qontak_mcp"]
omit = [
    "tests/*",
    "**/__init__.py",
    "src/qontak_mcp/stores/vault.py",  # Optional
]

[tool.coverage.report]
exclude_lines = [
    "pragma: no cover",
    "def __repr__",
    "if self.debug:",
    "if __name__ == .__main__.:",
    "raise NotImplementedError",
    "if TYPE_CHECKING:",
    "except ImportError:",
]
```

## Running Tests

```bash
# All tests
pytest

# With coverage
pytest --cov=src/qontak_mcp --cov-report=term-missing

# HTML report
pytest --cov=src/qontak_mcp --cov-report=html

# Specific module
pytest tests/tools/test_deals.py -v

# Integration tests only (requires API)
pytest -m integration_manual

# Exclude integration tests
pytest -m "not integration_manual"

# Parallel execution
pytest -n auto
```

## Test Naming Conventions

| Pattern | Example | Purpose |
|---------|---------|---------|
| `test_{action}_success` | `test_create_deal_success` | Happy path |
| `test_{action}_{error}` | `test_create_deal_validation_error` | Error cases |
| `test_{condition}_handles_{outcome}` | `test_empty_name_handles_validation` | Edge cases |
| `test_{resource}_{operation}` | `test_deal_timeline_pagination` | Specific features |

## Mocking HTTP with respx

```python
import respx
from httpx import Response


@respx.mock
async def test_api_call():
    """Mock HTTP request."""
    route = respx.post("https://app.qontak.com/api/v3.1/deals").mock(
        return_value=Response(200, json={"response": {"id": 1}})
    )
    
    result = await client.create_deal({"name": "Test"})
    
    assert route.called
    assert result["success"] is True
```
