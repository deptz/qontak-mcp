# Deals Domain

## Overview

Deals are the most complex resource with 14 tools, supporting:
- Pipeline/stage workflow
- Dynamic required fields per pipeline/stage
- Timeline and stage history
- Chat history integration
- Permission management

## Tools Reference

| Tool | Client Method | Description |
|------|---------------|-------------|
| `get_deal_template` | `get_deal_template()` | Get all deal fields |
| `get_required_fields_for_deal` | `get_required_fields_for_deal(pipeline_id, stage_id)` | Context-aware required fields |
| `list_deals` | `list_deals(page, per_page, stage_id, pipeline_id)` | List with filters |
| `get_deal` | `get_deal(deal_id)` | Single deal by ID |
| `create_deal` | `create_deal(deal_data)` | Create new deal |
| `update_deal` | `update_deal(deal_id, deal_data)` | Update existing |
| `delete_deal` | `delete_deal(deal_id)` | Delete deal |
| `get_deal_timeline` | `get_deal_timeline(deal_id, page, per_page)` | Activity timeline |
| `get_deal_stage_history` | `get_deal_stage_history(deal_id, page, per_page)` | Stage changes |
| `get_deal_chat_history` | `get_deal_chat_history(deal_id, page, per_page)` | Chat messages |
| `get_deal_real_creator` | `get_deal_real_creator(deal_id)` | Original creator |
| `get_deal_full_field` | `get_deal_full_field(deal_id)` | Complete field data |
| `get_deal_permissions` | `get_deal_permissions(deal_id)` | User permissions |
| `update_deal_owner` | `update_deal_owner(deal_id, creator_id)` | Change owner |

## Deal Data Structure

```json
{
  "id": 12345,
  "name": "Big Corp Deal",
  "crm_pipeline_id": 100,
  "crm_stage_id": 200,
  "size": 50000.00,
  "amount": 50000.00,
  "expected_close_date": "2025-06-30",
  "description": "Deal description",
  "contact_id": 67890,
  "company_id": 11111,
  "additional_fields": [
    {
      "id": 14840254,
      "name": "custom_field",
      "value": "custom value",
      "value_name": null
    }
  ],
  "created_at": "2025-01-15T10:30:00Z",
  "updated_at": "2025-01-20T14:45:00Z"
}
```

## Pipeline/Stage Dynamics

### Required Field Logic

```
Field is required if:
  1. field.required == true (global)
  OR
  2. pipeline_id in field.required_pipeline_ids
  
  AND stage doesn't override:
     - If field.required_stage_ids is not empty
       → stage_id MUST be in required_stage_ids
```

### Implementation

```python
async def get_required_fields_for_deal(
    self,
    pipeline_id: int,
    stage_id: int,
    user_id: Optional[str] = None
) -> dict:
    template = await self.get_deal_template(user_id=user_id)
    if not template.get("success"):
        return template
    
    fields = template.get("data", {}).get("response", [])
    required = []
    
    for field in fields:
        is_required = False
        
        # Global requirement
        if field.get("required"):
            is_required = True
        
        # Pipeline requirement
        req_pipelines = field.get("required_pipeline_ids", [])
        if req_pipelines and pipeline_id in req_pipelines:
            is_required = True
        
        # Stage refinement
        req_stages = field.get("required_stage_ids", [])
        if req_stages:
            is_required = stage_id in req_stages
        
        if is_required:
            required.append({
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
            "required_fields": required
        }
    }
```

## Creating a Deal

### Step 1: Get Template

```python
template = await client.get_deal_template()
fields = template["data"]["response"]
```

### Step 2: Check Required Fields

```python
required = await client.get_required_fields_for_deal(
    pipeline_id=selected_pipeline,
    stage_id=selected_stage
)
```

### Step 3: Build Payload

```python
deal_data = {
    "name": "Deal Name",
    "crm_pipeline_id": pipeline_id,
    "crm_stage_id": stage_id,
    "size": 10000.00,  # If required
    "additional_fields": [
        {
            "id": field_id,
            "name": field_name,
            "value": field_value,
            "value_name": None
        }
        for field_id, field_value in custom_fields.items()
    ]
}
```

### Step 4: Create

```python
result = await client.create_deal(deal_data)
```

## Common Patterns

### Moving Deal to New Stage

```python
# Update just the stage
result = await client.update_deal(
    deal_id=123,
    deal_data={"crm_stage_id": new_stage_id}
)
```

### Updating Owner

```python
result = await client.update_deal_owner(
    deal_id=123,
    creator_id=new_owner_id
)
```

### Filtering by Pipeline

```python
deals = await client.list_deals(
    pipeline_id=100,
    page=1,
    per_page=50
)
```

## Field Types

| Field | Type | Notes |
|-------|------|-------|
| name | string | Required |
| crm_pipeline_id | integer | Required |
| crm_stage_id | integer | Required |
| size | number | Monetary value |
| amount | number | Alternative to size |
| expected_close_date | date | YYYY-MM-DD |
| contact_id | integer | Associated contact |
| company_id | integer | Associated company |
| description | text | Free text |

## Testing

### Mock Template Response

```python
mock_deal_template = {
    "success": True,
    "data": {
        "response": [
            {
                "id": 1,
                "name": "deal_size",
                "type": "Number",
                "required": False,
                "required_pipeline_ids": [100],  # Required for pipeline 100
                "required_stage_ids": []
            },
            {
                "id": 2,
                "name": "close_reason",
                "type": "Dropdown select",
                "required": False,
                "required_pipeline_ids": [],
                "required_stage_ids": [500, 501],  # Required for closed stages
                "dropdown": [
                    {"id": 10, "name": "Won"},
                    {"id": 11, "name": "Lost"}
                ]
            }
        ]
    }
}
```

### Test Required Field Discovery

```python
@pytest.mark.asyncio
async def test_required_fields_pipeline_specific(mock_client):
    mock_client.get_deal_template = AsyncMock(return_value=mock_deal_template)
    
    result = await mock_client.get_required_fields_for_deal(
        pipeline_id=100,  # Requires deal_size
        stage_id=200
    )
    
    field_names = [f["name"] for f in result["data"]["required_fields"]]
    assert "deal_size" in field_names
    assert "close_reason" not in field_names  # Stage 200 not closed
```

## API Endpoints

| Operation | Method | Endpoint |
|-----------|--------|----------|
| List | GET | `/deals` |
| Get | GET | `/deals/{id}` |
| Create | POST | `/deals` |
| Update | PUT | `/deals/{id}` |
| Delete | DELETE | `/deals/{id}` |
| Template | GET | `/deals/info` |
| Timeline | GET | `/deals/{id}/timeline` |
| Stage History | GET | `/deals/{id}/stage_history` |
| Chat History | GET | `/deals/{id}/chat_history` |
| Real Creator | GET | `/deals/{id}/real_creator` |
| Full Field | GET | `/deals/{id}/full_field` |
| Permissions | GET | `/deals/{id}/permissions` |
| Update Owner | PUT | `/deals/{id}/owner` |
