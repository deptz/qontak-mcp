# Contacts Domain

## Overview

Contacts represent people/individuals in the CRM. They support:
- Person data (name, email, phone)
- Address information
- Custom fields
- Timeline tracking
- Chat history
- Company association

## Tools Reference

| Tool | Client Method | Description |
|------|---------------|-------------|
| `get_contact_template` | `get_contact_template()` | Get field definitions |
| `get_required_fields_for_contact` | `get_contact_template()` + filter | Discover required fields |
| `list_contacts` | `list_contacts(page, per_page)` | List all contacts |
| `get_contact` | `get_contact(contact_id)` | Single contact |
| `create_contact` | `create_contact(contact_data)` | Create new |
| `update_contact` | `update_contact(contact_id, contact_data)` | Update existing |
| `delete_contact` | `delete_contact(contact_id)` | Delete contact |
| `get_contact_timeline` | `get_contact_timeline(contact_id, page, per_page)` | Activity history |
| `get_contact_chat_history` | `get_contact_chat_history(contact_id, page, per_page)` | Chat messages |
| `update_contact_owner` | `update_contact_owner(contact_id, creator_id)` | Change owner |

## Contact Data Structure

```json
{
  "id": 67890,
  "first_name": "John",
  "last_name": "Doe",
  "email": "john@example.com",
  "telephone": "+1234567890",
  "job_title": "CEO",
  "crm_status_id": 100,
  "crm_company_id": 11111,
  "address": "123 Main St",
  "city": "Jakarta",
  "province": "DKI Jakarta",
  "country": "Indonesia",
  "zipcode": "12345",
  "date_of_birth": "1990-01-15",
  "additional_fields": [
    {
      "id": 20001,
      "name": "lead_source",
      "value": "Website",
      "value_name": null
    }
  ],
  "created_at": "2025-01-10T08:00:00Z",
  "updated_at": "2025-01-20T16:30:00Z"
}
```

## Key Fields

| Field | Required | Type | Notes |
|-------|----------|------|-------|
| first_name | Yes | string | Primary identifier |
| last_name | No | string | Optional surname |
| email | No | string | Must be valid format |
| telephone | No | string | Phone number |
| job_title | No | string | Position |
| crm_status_id | No | integer | Contact status |
| crm_company_id | No | integer | Parent company |
| address | No | string | Street address |
| city | No | string | City name |
| province | No | string | State/Province |
| country | No | string | Country name |
| zipcode | No | string | Postal code |
| date_of_birth | No | date | YYYY-MM-DD |

## Creating a Contact

### Minimal Creation

```python
contact_data = {
    "first_name": "Jane"
}
result = await client.create_contact(contact_data)
```

### Full Creation

```python
contact_data = {
    "first_name": "Jane",
    "last_name": "Smith",
    "email": "jane@company.com",
    "telephone": "+6281234567890",
    "job_title": "CTO",
    "crm_status_id": 100,
    "crm_company_id": 11111,
    "address": "456 Oak Ave",
    "city": "Surabaya",
    "province": "East Java",
    "country": "Indonesia",
    "zipcode": "60241",
    "date_of_birth": "1985-03-20",
    "additional_fields": [
        {
            "id": 20001,
            "name": "lead_source",
            "value": "Referral",
            "value_name": null
        }
    ]
}
result = await client.create_contact(contact_data)
```

## Dynamic Fields

Contact templates return field definitions with requirement info:

```python
{
  "id": 20001,
  "name": "lead_source",
  "type": "Dropdown select",
  "required": True,
  "dropdown": [
    {"id": 1, "name": "Website"},
    {"id": 2, "name": "Referral"},
    {"id": 3, "name": "Social Media"}
  ]
}
```

## Updating Contacts

### Partial Update

```python
# Update only email
result = await client.update_contact(
    contact_id=67890,
    contact_data={"email": "newemail@example.com"}
)
```

### Full Update

```python
result = await client.update_contact(
    contact_id=67890,
    contact_data={
        "first_name": "Johnny",
        "job_title": "President",
        "telephone": "+6289876543210"
    }
)
```

## Company Association

Link contact to company:

```python
# Associate with company
result = await client.update_contact(
    contact_id=67890,
    contact_data={"crm_company_id": 11111}
)

# Remove association
result = await client.update_contact(
    contact_id=67890,
    contact_data={"crm_company_id": None}
)
```

## Chat History

```python
# Get recent chat messages
chat = await client.get_contact_chat_history(
    contact_id=67890,
    page=1,
    per_page=10
)

# Messages structure
{
  "success": True,
  "data": {
    "response": [
      {
        "id": 5001,
        "message": "Hello, interested in your product",
        "direction": "incoming",  # or "outgoing"
        "channel": "whatsapp",    # or "email", "sms"
        "created_at": "2025-01-20T10:30:00Z"
      }
    ]
  }
}
```

## Timeline

```python
timeline = await client.get_contact_timeline(
    contact_id=67890,
    page=1,
    per_page=20
)

// Events include:
// - Contact created
// - Field updates
// - Deal associations
// - Note additions
// - Activity logs
```

## Owner Management

```python
# Change owner
result = await client.update_contact_owner(
    contact_id=67890,
    creator_id=999  # New owner user ID
)
```

## Testing Patterns

### Mock Contact Response

```python
mock_contact = {
    "success": True,
    "data": {
        "response": {
            "id": 67890,
            "first_name": "Test",
            "last_name": "Contact",
            "email": "test@example.com",
            "telephone": "+1234567890",
            "crm_company_id": 11111
        }
    }
}
```

### Test Contact Creation

```python
@pytest.mark.asyncio
async def test_create_contact_with_company(mock_client):
    mock_client.create_contact = AsyncMock(return_value={
        "success": True,
        "data": {"response": {"id": 123}}
    })
    
    result = await mock_client.create_contact({
        "first_name": "Test",
        "crm_company_id": 11111
    })
    
    assert result["success"] is True
    mock_client.create_contact.assert_called_once()
```

### Test Required Field Validation

```python
@pytest.mark.asyncio
async def test_create_contact_requires_first_name():
    from qontak_mcp.models import ContactCreateParams
    
    with pytest.raises(ValidationError) as exc:
        ContactCreateParams(first_name="")  # Empty
    
    assert "first_name" in str(exc.value)
```

## API Endpoints

| Operation | Method | Endpoint |
|-----------|--------|----------|
| List | GET | `/contacts` |
| Get | GET | `/contacts/{id}` |
| Create | POST | `/contacts` |
| Update | PUT | `/contacts/{id}` |
| Delete | DELETE | `/contacts/{id}` |
| Template | GET | `/contacts/info` |
| Timeline | GET | `/contacts/{id}/timeline` |
| Chat History | GET | `/contacts/{id}/chat_history` |
| Update Owner | PUT | `/contacts/{id}/owner` |

## Common Use Cases

### 1. Import Contacts from CSV

```python
for row in csv_data:
    contact_data = {
        "first_name": row["first_name"],
        "last_name": row.get("last_name"),
        "email": row.get("email"),
        "telephone": row.get("phone"),
    }
    await client.create_contact(contact_data)
```

### 2. Update Contact Status

```python
# Mark as qualified
await client.update_contact(
    contact_id=contact_id,
    contact_data={"crm_status_id": QUALIFIED_STATUS_ID}
)
```

### 3. Find Contacts by Company

```python
# List all and filter (API doesn't support direct company filter)
all_contacts = await client.list_contacts(per_page=100)
company_contacts = [
    c for c in all_contacts["data"]["response"]
    if c.get("crm_company_id") == company_id
]
```
