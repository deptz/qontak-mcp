---
name: qontak-mcp-developer
description: Develop and extend the Qontak MCP server - add new tools, create token store backends, implement dynamic field discovery, and maintain the 61-tool CRM integration. Use when working with qontak-mcp codebase for feature development, tool additions, architecture changes, testing, or debugging CRM integration issues.
---

# Qontak MCP Developer Skill

Guide for developing and extending the Qontak MCP server.

## Quick Reference

### Project Structure

```
src/qontak_mcp/
├── server.py          # MCP server entry point
├── client.py          # Qontak API HTTP client
├── auth.py            # OAuth with lazy token refresh
├── models.py          # Pydantic validation models
├── validation.py      # Input validation utilities
├── tools/             # 61 MCP tools (8 modules)
│   ├── contacts.py    # 10 tools
│   ├── companies.py   # 8 tools
│   ├── deals.py       # 14 tools
│   ├── tickets.py     # 7 tools
│   ├── tasks.py       # 8 tools
│   ├── notes.py       # 5 tools
│   ├── products.py    # 5 tools
│   └── products_association.py  # 5 tools
└── stores/            # Token storage backends
    ├── base.py        # TokenStore protocol
    ├── env.py         # Environment variable store
    ├── redis.py       # Redis token cache
    └── vault.py       # HashiCorp Vault store
```

### Documentation Index

| Document | Purpose |
|----------|---------|
| [usage_guide.md](references/usage_guide.md) | **End-user guide** - How to use the 61 MCP tools |
| [architecture.md](references/architecture.md) | System architecture and data flow |
| [tool_patterns.md](references/tool_patterns.md) | Tool implementation patterns |
| [dynamic_fields.md](references/dynamic_fields.md) | Custom field discovery patterns |
| [token_stores.md](references/token_stores.md) | Adding new token backends |
| [testing.md](references/testing.md) | Testing patterns and fixtures |
| [models.md](references/models.md) | Pydantic model patterns |
| [domains/*.md](references/domains/) | Resource-specific details |

## Using the Qontak MCP

### For End Users

The Qontak MCP provides **61 tools** across 8 CRM domains. Common usage patterns:

**Basic CRM Workflow:**
```
1. Get template → Understand available fields
   → get_contact_template(), get_deal_template(), etc.

2. List → See existing records
   → list_contacts(), list_deals(), etc.

3. Create → Add new records with required fields
   → create_contact(), create_deal(), etc.

4. Update → Modify existing records
   → update_contact(), update_deal(), etc.
```

**Working with Custom Fields:**
```
1. Check template for field definitions
   → get_deal_template()

2. Build additional_fields array
   [{"id": field_id, "name": field_name, "value": value, "value_name": null}]

3. Include in create/update calls
   → create_deal(..., additional_fields=[...])
```

**Key Resources:**
- **[usage_guide.md](references/usage_guide.md)** - Complete usage guide with workflows, examples, and best practices
- **[dynamic_fields.md](references/dynamic_fields.md)** - Working with custom fields and dynamic field discovery
- **[domains/](references/domains/)** - Resource-specific usage patterns

### Common User Questions

| Question | Answer |
|----------|--------|
| "How do I create a deal?" | See usage_guide.md → Working with Deals |
| "What fields are required?" | Use get_*_template() or get_required_fields_for_*() tools |
| "How do I add custom fields?" | See usage_guide.md → Working with Custom Fields |
| "Can I link a contact to a company?" | Yes, use crm_company_id in create/update_contact |
| "How do I track deal progress?" | Use get_deal_timeline() and get_deal_stage_history() |

## Developing the MCP

### 1. Add a New Tool

**Step 1:** Determine the domain (deals, contacts, tickets, tasks, notes, companies, products, products_association)

**Step 2:** Check reference for domain-specific patterns:
- See [references/domains/](references/domains/) for domain-specific implementation details

**Step 3:** Add client method in `src/qontak_mcp/client.py`:
```python
async def new_operation(
    self,
    param: str,
    user_id: Optional[str] = None
) -> dict[str, Any]:
    """Description of operation."""
    # Validate inputs using validation.py functions
    result = validate_something(param)
    if not result.is_valid:
        return {"success": False, "error": result.error}
    
    return await self._request("METHOD", "/endpoint", user_id=user_id)
```

**Step 4:** Add Pydantic model in `src/qontak_mcp/models.py` (if needed):
```python
class NewOperationParams(SecureBaseModel, TenantMixin):
    """Parameters for new operation."""
    param: str = Field(min_length=1, max_length=MAX_NAME_LENGTH)
```

**Step 5:** Register tool in `src/qontak_mcp/tools/{domain}.py`:
```python
@mcp.tool()
async def new_tool_name(
    param: str,
    user_id: Optional[str] = None
) -> str:
    """Tool description for LLM."""
    try:
        client = get_client()
        result = await client.new_operation(param, user_id=user_id)
        return json.dumps(result, indent=2)
    except Exception as e:
        return json.dumps(safe_error_response(e, "new_tool_name"), indent=2)
```

**Step 6:** Add tests in `tests/tools/test_{domain}.py`

### 2. Add a New Token Store Backend

See [references/token_stores.md](references/token_stores.md) for complete guide.

Quick pattern:
```python
# src/qontak_mcp/stores/new_store.py
class NewTokenStore:
    """Token store using NewBackend."""
    
    def get(self, user_id: Optional[str] = None) -> Optional[TokenData]:
        # Retrieve token data
        pass
    
    def save(self, token_data: TokenData, user_id: Optional[str] = None) -> None:
        # Store token data
        pass
```

### 3. Implement Dynamic Field Discovery

See [references/dynamic_fields.md](references/dynamic_fields.md) for patterns.

Key principle: Call `{resource}/info` endpoint to get template, parse fields to identify required vs optional based on pipeline/stage context.

### 4. Run Tests

```bash
# All tests
pytest

# Specific module
pytest tests/tools/test_deals.py -v

# With coverage
pytest --cov=src/qontak_mcp --cov-report=term-missing

# Integration tests (requires real API)
pytest -m integration_manual
```

## Architecture Principles

1. **Lazy Initialization**: Never create client at import time - use `get_client()` factory
2. **Validation First**: All inputs validated via Pydantic models or validation functions
3. **Security**: Rate limiting, audit logging, input sanitization
4. **Multi-tenancy**: All tools accept optional `user_id` parameter
5. **Error Safety**: Never expose internal details - use `safe_error_response()`

## Domain-Specific References

| Domain | File | Tools Count |
|--------|------|-------------|
| Contacts | [references/domains/contacts.md](references/domains/contacts.md) | 10 |
| Companies | [references/domains/companies.md](references/domains/companies.md) | 8 |
| Deals | [references/domains/deals.md](references/domains/deals.md) | 14 |
| Tickets | [references/domains/tickets.md](references/domains/tickets.md) | 7 |
| Tasks | [references/domains/tasks.md](references/domains/tasks.md) | 8 |
| Notes | [references/domains/notes.md](references/domains/notes.md) | 5 |
| Products | [references/domains/products.md](references/domains/products.md) | 5 |
| Products Association | [references/domains/products_association.md](references/domains/products_association.md) | 5 |

## Common Tasks

### Fix Tool Registration Issues
- Check lazy registration pattern in `tools/__init__.py`
- Ensure `register_{domain}_tools_lazy(mcp, get_client)` is called in `server.py`

### Update Validation Rules
- Modify `src/qontak_mcp/validation.py` for low-level validation
- Modify `src/qontak_mcp/models.py` for Pydantic model validation
- Update both for consistency

### Add Custom Field Support
1. Update model to accept `additional_fields: Optional[list[dict[str, Any]]]`
2. Add field validator for custom fields
3. Document in tool docstring

### Debug API Issues
1. Check logs for sanitized error messages
2. Run integration test with real API
3. Verify token store has valid refresh token
