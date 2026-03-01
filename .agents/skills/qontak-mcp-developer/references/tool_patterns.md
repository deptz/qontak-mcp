# Tool Implementation Patterns

## Tool Structure Template

```python
@mcp.tool()
async def tool_name(
    required_param: str,
    optional_param: Optional[int] = None,
    user_id: Optional[str] = None,
) -> str:
    """
    Clear description of what the tool does.
    
    Explain when to use this tool and what it returns.
    Mention any important limitations or prerequisites.
    
    Args:
        required_param: Description of parameter
        optional_param: Description (default: None)
        user_id: Optional user/tenant identifier for multi-tenant scenarios
    
    Returns:
        JSON string with result or error
    """
    try:
        client = get_client()
        result = await client.client_method(required_param, optional_param, user_id=user_id)
        return json.dumps(result, indent=2)
    except PydanticValidationError as e:
        return json.dumps({
            "success": False,
            "error": "Validation error",
            "details": e.errors()
        }, indent=2)
    except Exception as e:
        return json.dumps(safe_error_response(e, "tool_name"), indent=2)
```

## Tool Categories

### 1. List Operations

```python
@mcp.tool()
async def list_resources(
    page: int = 1,
    per_page: int = 25,
    filter_id: Optional[int] = None,
    user_id: Optional[str] = None,
) -> str:
    """List resources with pagination and optional filtering."""
    try:
        client = get_client()
        result = await client.list_resources(
            page=page,
            per_page=per_page,
            filter_id=filter_id,
            user_id=user_id
        )
        return json.dumps(result, indent=2)
    except Exception as e:
        return json.dumps(safe_error_response(e, "list_resources"), indent=2)
```

**Key points:**
- Always include pagination (page, per_page)
- Default per_page: 25
- Max per_page: 100

### 2. Get Single Resource

```python
@mcp.tool()
async def get_resource(
    resource_id: int,
    user_id: Optional[str] = None,
) -> str:
    """Get a single resource by ID."""
    try:
        # Pydantic model validates resource_id > 0
        params = ResourceGetParams(resource_id=resource_id, user_id=user_id)
        
        client = get_client()
        result = await client.get_resource(params.resource_id, user_id=params.user_id)
        return json.dumps(result, indent=2)
    except PydanticValidationError as e:
        return json.dumps({"success": False, "error": str(e)}, indent=2)
    except Exception as e:
        return json.dumps(safe_error_response(e, "get_resource"), indent=2)
```

### 3. Create Resource

```python
@mcp.tool()
async def create_resource(
    name: str,
    required_field: int,
    optional_field: Optional[str] = None,
    additional_fields: Optional[str] = None,  # JSON string
    user_id: Optional[str] = None,
) -> str:
    """Create a new resource."""
    try:
        # Parse additional_fields JSON
        additional = json.loads(additional_fields) if additional_fields else None
        
        # Build data dict
        resource_data = {
            "name": name,
            "required_field": required_field,
        }
        if optional_field:
            resource_data["optional_field"] = optional_field
        if additional:
            resource_data["additional_fields"] = additional
        
        client = get_client()
        result = await client.create_resource(resource_data, user_id=user_id)
        return json.dumps(result, indent=2)
    except json.JSONDecodeError:
        return json.dumps({
            "success": False, 
            "error": "additional_fields must be valid JSON"
        }, indent=2)
    except Exception as e:
        return json.dumps(safe_error_response(e, "create_resource"), indent=2)
```

### 4. Update Resource

```python
@mcp.tool()
async def update_resource(
    resource_id: int,
    name: Optional[str] = None,
    field: Optional[str] = None,
    user_id: Optional[str] = None,
) -> str:
    """Update an existing resource."""
    try:
        # At least one field required
        if not any([name, field]):
            return json.dumps({
                "success": False,
                "error": "At least one field must be provided for update"
            }, indent=2)
        
        resource_data = {}
        if name:
            resource_data["name"] = name
        if field:
            resource_data["field"] = field
        
        client = get_client()
        result = await client.update_resource(resource_id, resource_data, user_id=user_id)
        return json.dumps(result, indent=2)
    except Exception as e:
        return json.dumps(safe_error_response(e, "update_resource"), indent=2)
```

### 5. Template/Schema Operations

```python
@mcp.tool()
async def get_resource_template(user_id: Optional[str] = None) -> str:
    """
    Get the resource field template/schema.
    
    IMPORTANT: Use this BEFORE creating/updating to check required fields.
    """
    try:
        client = get_client()
        result = await client.get_resource_template(user_id=user_id)
        return json.dumps(result, indent=2)
    except Exception as e:
        return json.dumps(safe_error_response(e, "get_resource_template"), indent=2)
```

### 6. Dynamic Field Discovery

```python
@mcp.tool()
async def get_required_fields_for_resource(
    pipeline_id: int,
    stage_id: Optional[int] = None,
    user_id: Optional[str] = None,
) -> str:
    """
    Get required fields for specific context.
    
    Some resources have context-dependent required fields
    (e.g., different fields required for different pipeline/stage).
    """
    try:
        client = get_client()
        # Get template
        template = await client.get_resource_template(user_id=user_id)
        
        if not template.get("success"):
            return json.dumps(template, indent=2)
        
        # Filter fields based on context
        fields = template.get("data", {}).get("response", [])
        required_fields = []
        
        for field in fields:
            is_required = False
            
            # Check pipeline requirement
            required_pipelines = field.get("required_pipeline_ids", [])
            if required_pipelines and pipeline_id in required_pipelines:
                is_required = True
            
            # Check stage requirement
            if stage_id:
                required_stages = field.get("required_stage_ids", [])
                if required_stages and stage_id not in required_stages:
                    is_required = False
            
            if is_required:
                required_fields.append({
                    "id": field.get("id"),
                    "name": field.get("name"),
                    "type": field.get("type"),
                })
        
        return json.dumps({
            "success": True,
            "data": {
                "pipeline_id": pipeline_id,
                "stage_id": stage_id,
                "required_fields": required_fields
            }
        }, indent=2)
    except Exception as e:
        return json.dumps(safe_error_response(e, "get_required_fields"), indent=2)
```

## Error Handling Patterns

### Standard Error Response
```python
from ..errors import safe_error_response

except Exception as e:
    return json.dumps(safe_error_response(e, "tool_name"), indent=2)
```

### Validation Error Response
```python
except PydanticValidationError as e:
    return json.dumps({
        "success": False,
        "error": "Validation error",
        "details": [
            {"field": " ".join(err["loc"]), "message": err["msg"]}
            for err in e.errors()
        ]
    }, indent=2)
```

### Specific Error Response
```python
except json.JSONDecodeError:
    return json.dumps({
        "success": False,
        "error": "Invalid JSON format for custom_fields"
    }, indent=2)
```

## Client Method Patterns

### Basic CRUD Pattern
```python
async def list_resources(self, page: int, per_page: int, user_id: Optional[str]) -> dict:
    pagination_result = validate_pagination(page, per_page)
    if not pagination_result.is_valid:
        return {"success": False, "error": pagination_result.error}
    
    return await self._request("GET", "/resources", user_id=user_id, params={
        "page": page, "per_page": per_page
    })

async def get_resource(self, resource_id: int, user_id: Optional[str]) -> dict:
    id_result = validate_resource_id(resource_id, "resource_id")
    if not id_result.is_valid:
        return {"success": False, "error": id_result.error}
    
    return await self._request("GET", f"/resources/{resource_id}", user_id=user_id)

async def create_resource(self, data: dict, user_id: Optional[str]) -> dict:
    return await self._request("POST", "/resources", user_id=user_id, json=data)

async def update_resource(self, resource_id: int, data: dict, user_id: Optional[str]) -> dict:
    id_result = validate_resource_id(resource_id, "resource_id")
    if not id_result.is_valid:
        return {"success": False, "error": id_result.error}
    
    return await self._request("PUT", f"/resources/{resource_id}", user_id=user_id, json=data)

async def delete_resource(self, resource_id: int, user_id: Optional[str]) -> dict:
    id_result = validate_resource_id(resource_id, "resource_id")
    if not id_result.is_valid:
        return {"success": False, "error": id_result.error}
    
    return await self._request("DELETE", f"/resources/{resource_id}", user_id=user_id)
```

## Registration Pattern

### Lazy Registration (Required)
```python
def register_domain_tools_lazy(
    mcp: FastMCP,
    get_client: Callable[[], QontakClient]
) -> None:
    """Register domain tools with lazy client access."""
    
    @mcp.tool()
    async def tool_name(...):
        client = get_client()  # Deferred until call
        ...
```

### Backward Compatibility
```python
def register_domain_tools(mcp: FastMCP, client: QontakClient) -> None:
    """Legacy registration - delegates to lazy version."""
    register_domain_tools_lazy(mcp, lambda: client)
```

## Testing Patterns

### Tool Test Template
```python
@pytest.mark.asyncio
async def test_tool_name_success(mock_client):
    """Test successful tool execution."""
    mock_client.method.return_value = {"success": True, "data": {...}}
    
    result = await tool_name(param="value")
    result_data = json.loads(result)
    
    assert result_data["success"] is True
    mock_client.method.assert_called_once_with("value", user_id=None)

@pytest.mark.asyncio
async def test_tool_name_validation_error():
    """Test validation failure."""
    result = await tool_name(param="")  # Invalid
    result_data = json.loads(result)
    
    assert result_data["success"] is False
    assert "error" in result_data
```

## Naming Conventions

| Operation | Prefix | Example |
|-----------|--------|---------|
| List | `list_` | `list_deals` |
| Get single | `get_` | `get_deal` |
| Create | `create_` | `create_deal` |
| Update | `update_` | `update_deal` |
| Delete | `delete_` | `delete_deal` |
| Template | `get_{resource}_template` | `get_deal_template` |
| Required fields | `get_required_fields_for_{resource}` | `get_required_fields_for_deal` |
| Timeline | `get_{resource}_timeline` | `get_deal_timeline` |
| Chat history | `get_{resource}_chat_history` | `get_contact_chat_history` |
| Change owner | `update_{resource}_owner` | `update_deal_owner` |

## Response Format Standards

### Success Response
```json
{
  "success": true,
  "data": {
    "response": [...],
    "meta": {
      "total_count": 100,
      "total_pages": 4
    }
  }
}
```

### Error Response
```json
{
  "success": false,
  "error": "Human-readable error message",
  "error_code": "optional_error_code"
}
```
