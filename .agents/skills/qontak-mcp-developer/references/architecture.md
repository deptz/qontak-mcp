# Qontak MCP Architecture

## System Overview

```
┌─────────────────────────────────────────┐
│           MCP Tools (61)                │
│   FastMCP decorators + lazy client      │
└─────────────────┬───────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────┐
│          QontakClient                   │
│   Async HTTP + validation + rate limit  │
│   Returns: {"success": bool, ...}       │
└─────────────────┬───────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────┐
│           QontakAuth                    │
│   Lazy token refresh (6h caching)       │
└─────────────────┬───────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────┐
│         TokenStore (Protocol)           │
│   env | redis | vault                   │
└─────────────────────────────────────────┘
```

## Key Components

### 1. Server (`server.py`)

Entry point with lifespan management:
```python
@asynccontextmanager
async def lifespan(mcp: FastMCP) -> AsyncIterator[None]:
    # Load env, configure logging
    # Initialize token store
    # Create client with auth
    yield
    # Cleanup

mcp = FastMCP(name="Qontak CRM", lifespan=lifespan)
```

**Critical**: Client is NOT created at import time. It's initialized in lifespan and accessed via `get_client()`.

### 2. Client (`client.py`)

- Async HTTP client using `httpx`
- All methods return `dict[str, Any]` with `{"success": bool, ...}`
- Input validation before API calls
- Rate limiting integration

Pattern:
```python
async def operation(self, resource_id: int, user_id: Optional[str] = None) -> dict:
    # Validate
    id_result = validate_resource_id(resource_id, "resource_id")
    if not id_result.is_valid:
        return {"success": False, "error": id_result.error}
    
    # Call API
    return await self._request("GET", f"/resources/{resource_id}", user_id=user_id)
```

### 3. Authentication (`auth.py`)

- Lazy token refresh (only when needed)
- Token rotation support (new refresh_token may be returned)
- 6-hour token lifetime with 5-minute buffer

```python
async def get_access_token(self, user_id: Optional[str] = None) -> str:
    token_data = self._store.get(user_id)
    
    if token_data.is_access_token_valid(REFRESH_BUFFER_SECONDS):
        return token_data.access_token
    
    # Refresh
    result = await self._refresh_token(token_data.refresh_token)
    # Save new tokens
    return result["access_token"]
```

### 4. Token Stores (`stores/`)

Protocol-based for pluggability:
```python
class TokenStore(Protocol):
    def get(self, user_id: Optional[str] = None) -> Optional[TokenData]: ...
    def save(self, token_data: TokenData, user_id: Optional[str] = None) -> None: ...
```

Implementations:
- **EnvTokenStore**: Reads from `QONTAK_REFRESH_TOKEN` env var
- **RedisTokenStore**: Caches tokens with TTL
- **VaultTokenStore**: Production-grade with encryption at rest

### 5. Tools (`tools/`)

Each domain has its own module. Tool registration uses lazy pattern:

```python
def register_domain_tools_lazy(mcp: FastMCP, get_client: Callable) -> None:
    @mcp.tool()
    async def tool_name(param: str, user_id: Optional[str] = None) -> str:
        client = get_client()  # Deferred!
        result = await client.operation(param, user_id=user_id)
        return json.dumps(result, indent=2)
```

### 6. Models (`models.py`)

Pydantic v2 models with security focus:
```python
class SecureBaseModel(BaseModel):
    model_config = ConfigDict(
        extra='forbid',           # Prevent mass assignment
        str_strip_whitespace=True,
        validate_default=True,
    )

class TenantMixin(BaseModel):
    user_id: Optional[str] = Field(default=None, max_length=128)
    
    @field_validator('user_id')
    @classmethod
    def validate_user_id(cls, v: Optional[str]) -> Optional[str]:
        # Pattern validation + injection checks
        ...
```

### 7. Validation (`validation.py`)

Low-level validation functions (used by client when Pydantic not applicable):
```python
def validate_user_id(user_id: Optional[str]) -> ValidationResult:
def validate_resource_id(resource_id: int, field_name: str) -> ValidationResult:
def validate_pagination(page: int, per_page: int) -> ValidationResult:
```

## Data Flow

```
1. LLM calls tool via MCP
   ↓
2. Tool function validates with Pydantic model
   ↓
3. Tool calls client method
   ↓
4. Client validates inputs (validation.py)
   ↓
5. Client checks rate limiter
   ↓
6. Client gets auth headers (triggers token refresh if needed)
   ↓
7. HTTP request to Qontak API
   ↓
8. Response formatted as JSON string for LLM
```

## Security Layers

| Layer | Implementation |
|-------|----------------|
| Input validation | Pydantic models + validation functions |
| Tenant isolation | user_id validation with pattern matching |
| Rate limiting | Token bucket algorithm per user |
| Auth | OAuth 2.0 with lazy refresh |
| Token storage | Pluggable stores (env/redis/vault) |
| Audit logging | Structured logs with sensitive data redaction |
| Error handling | Safe error responses (no internal details) |

## Testing Architecture

```
tests/
├── conftest.py              # Shared fixtures
├── test_*.py                # Unit tests (auth, client, models, etc.)
├── stores/
│   ├── test_env.py
│   ├── test_redis.py
│   └── test_stores_init.py
├── tools/
│   ├── conftest.py          # Tool-specific fixtures
│   ├── test_deals.py        # Basic tool tests
│   ├── test_deals_comprehensive.py  # Edge cases
│   └── *_fixtures.py        # Domain fixtures
└── integration/
    ├── conftest.py          # Integration test config
    └── test_*_integration.py # Real API tests
```

## Code Organization Rules

1. **One domain per file** in `tools/`
2. **Client methods grouped by domain** in `client.py`
3. **Models grouped by domain** in `models.py`
4. **Tests mirror source structure**
5. **Fixtures separate** for reusability
