# Dynamic Field Discovery Patterns

## Overview

Qontak CRM uses dynamic fields that vary by:
- **Pipeline** (for deals, tickets)
- **Stage** (for deals)
- **Custom field configurations**

The MCP server discovers these at runtime via template endpoints.

## Template Endpoints

| Resource | Endpoint | Description |
|----------|----------|-------------|
| Deals | `/deals/info` | Fields with pipeline/stage requirements |
| Tickets | `/tickets/info` | Fields with pipeline requirements |
| Tasks | `/tasks/info` | Fields with status/detail/next_step |
| Contacts | `/contacts/info` | Contact field definitions |
| Companies | `/companies/info` | Company field definitions |

## Field Structure

```json
{
  "id": 14840254,
  "name": "field_name",
  "type": "Single-line text",
  "required": false,
  "required_pipeline_ids": [123, 456],
  "required_stage_ids": [789, 101112],
  "dropdown": [
    {"id": 1, "name": "Option 1"}
  ],
  "max_length": 255
}
```

### Field Types

| Type | Format | Notes |
|------|--------|-------|
| Single-line text | Plain string | max_length may apply |
| Text Area | Plain string | Multi-line text |
| Number | Numeric | Integer or decimal |
| Date | "YYYY-MM-DD" | ISO 8601 format |
| Date time | "YYYY-MM-DD HH:MM:SS" | 24-hour format |
| Dropdown select | Option ID | Use dropdown array for options |
| Multiple select | Array of IDs | Multiple selections allowed |
| Percentage | Number 0-100 | Stored as number |
| Checklist | Boolean | true/false |
| URL | String | Must be valid URL format |

### Field Types Requiring Special Handling

| Type | Challenge | Solution |
|------|-----------|----------|
| Photo | Requires file upload | Separate upload mechanism |
| Signature | Requires file upload | Separate upload mechanism |
| File upload | Binary data | Pre-signed URL flow |
| GPS | Lat/long coordinates | Special format validation |

## Implementation Patterns

### Pattern 1: Basic Template Retrieval

```python
async def get_deal_template(self, user_id: Optional[str] = None) -> dict:
    """Get deal template with all fields."""
    return await self._request("GET", "/deals/info", user_id=user_id)
```

### Pattern 2: Context-Aware Required Fields

```python
async def get_required_fields_for_deal(
    self,
    pipeline_id: int,
    stage_id: int,
    user_id: Optional[str] = None
) -> dict:
    """Get fields required for specific pipeline/stage combination."""
    template = await self.get_deal_template(user_id=user_id)
    
    if not template.get("success"):
        return template
    
    fields = template.get("data", {}).get("response", [])
    required_fields = []
    
    for field in fields:
        is_required = False
        
        # Check global required flag
        if field.get("required"):
            is_required = True
        
        # Check pipeline-specific requirements
        required_pipelines = field.get("required_pipeline_ids", [])
        if required_pipelines and pipeline_id in required_pipelines:
            is_required = True
        
        # Check stage-specific requirements (refines pipeline)
        required_stages = field.get("required_stage_ids", [])
        if required_stages:
            if stage_id in required_stages:
                is_required = True
            else:
                is_required = False
        
        if is_required:
            required_fields.append({
                "id": field["id"],
                "name": field["name"],
                "type": field["type"],
                "dropdown": field.get("dropdown"),
            })
    
    return {
        "success": True,
        "data": {
            "pipeline_id": pipeline_id,
            "stage_id": stage_id,
            "required_fields": required_fields
        }
    }
```

### Pattern 3: Extract Dropdown Options

```python
def _extract_dropdown_options(field: dict) -> list[dict]:
    """Extract dropdown options from a field."""
    dropdown = field.get("dropdown", [])
    return [
        {"id": opt["id"], "name": opt["name"]}
        for opt in dropdown
    ]

# In template parsing:
for field in fields:
    if field["type"] in ["Dropdown select", "Multiple select"]:
        options = self._extract_dropdown_options(field)
        # Present options to user
```

### Pattern 4: Build additional_fields Array

```python
def build_additional_fields(
    self,
    field_values: dict[int, Any],  # field_id -> value
    template_fields: list[dict]
) -> list[dict]:
    """
    Build additional_fields array from field values.
    
    Args:
        field_values: Dict mapping field_id to value
        template_fields: Fields from template
    
    Returns:
        Array formatted for API
    """
    additional_fields = []
    
    for field_id, value in field_values.items():
        # Find field in template
        field_def = next(
            (f for f in template_fields if f["id"] == field_id),
            None
        )
        if not field_def:
            continue
        
        # Format value based on type
        formatted_value = self._format_field_value(value, field_def)
        
        additional_fields.append({
            "id": field_id,
            "name": field_def["name"],
            "value": formatted_value,
            "value_name": None  # Set if using dropdown
        })
    
    return additional_fields

def _format_field_value(self, value: Any, field_def: dict) -> Any:
    """Format value based on field type."""
    field_type = field_def["type"]
    
    if field_type == "Date":
        return str(value)  # Ensure YYYY-MM-DD
    elif field_type == "Date time":
        return str(value)  # Ensure YYYY-MM-DD HH:MM:SS
    elif field_type == "Percentage":
        return float(value)
    elif field_type == "Checklist":
        return bool(value)
    else:
        return value
```

### Pattern 5: Validate Custom Fields Against Template

```python
def validate_custom_fields(
    self,
    custom_fields: list[dict],
    template_fields: list[dict]
) -> tuple[bool, Optional[str]]:
    """
    Validate custom fields against template.
    
    Returns:
        (is_valid, error_message)
    """
    valid_field_ids = {f["id"] for f in template_fields}
    
    for cf in custom_fields:
        field_id = cf.get("id")
        
        if field_id not in valid_field_ids:
            return False, f"Invalid field ID: {field_id}"
        
        field_def = next(f for f in template_fields if f["id"] == field_id)
        
        # Validate type
        value = cf.get("value")
        field_type = field_def["type"]
        
        if field_type == "Dropdown select":
            valid_ids = {opt["id"] for opt in field_def.get("dropdown", [])}
            if value not in valid_ids:
                return False, f"Invalid option for {field_def['name']}"
        
        elif field_type == "Number":
            try:
                float(value)
            except (TypeError, ValueError):
                return False, f"{field_def['name']} must be a number"
    
    return True, None
```

## Resource-Specific Patterns

### Deals: Pipeline + Stage Requirements

Deals can have different required fields based on BOTH pipeline and stage:

```python
# Pipeline 1 might require "deal_size"
# Stage "Closed Won" in Pipeline 1 might require "close_reason"

is_required = False

# Global requirement
if field.get("required"):
    is_required = True

# Pipeline requirement
if pipeline_id in field.get("required_pipeline_ids", []):
    is_required = True

# Stage requirement (overrides)
required_stages = field.get("required_stage_ids", [])
if required_stages:
    is_required = stage_id in required_stages
```

### Tickets: Pipeline-Only Requirements

Tickets only use pipeline-level requirements:

```python
is_required = (
    field.get("required") or
    pipeline_id in field.get("required_pipeline_ids", [])
)
```

### Tasks: Static Requirements

Tasks have consistent requirements (status, detail, next_step):

```python
# Always check template for current requirements
# Fields often required:
# - crm_task_status_id
# - detail
# - next_step
```

## Error Handling

### Template Unavailable
```python
result = await client.get_deal_template()
if not result.get("success"):
    return {
        "success": False,
        "error": "Cannot retrieve field template. " + result.get("error", "")
    }
```

### Missing Required Fields
```python
required = get_required_fields(template, pipeline_id, stage_id)
provided = {f["id"] for f in additional_fields}

missing = [f for f in required if f["id"] not in provided]
if missing:
    return {
        "success": False,
        "error": f"Missing required fields: {[f['name'] for f in missing]}"
    }
```

## Testing Dynamic Fields

### Mock Template Response
```python
mock_template = {
    "success": True,
    "data": {
        "response": [
            {
                "id": 1,
                "name": "deal_size",
                "type": "Number",
                "required": False,
                "required_pipeline_ids": [100],
                "required_stage_ids": []
            },
            {
                "id": 2,
                "name": "priority",
                "type": "Dropdown select",
                "required": True,
                "dropdown": [
                    {"id": 10, "name": "High"},
                    {"id": 11, "name": "Low"}
                ]
            }
        ]
    }
}
```

### Test Field Discovery
```python
@pytest.mark.asyncio
async def test_required_fields_filtered_by_pipeline():
    client = QontakClient(mock_auth)
    client._request = AsyncMock(return_value=mock_template)
    
    result = await client.get_required_fields_for_deal(
        pipeline_id=100,  # Requires deal_size
        stage_id=1
    )
    
    field_names = [f["name"] for f in result["data"]["required_fields"]]
    assert "deal_size" in field_names
```
