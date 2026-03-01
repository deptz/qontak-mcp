# Qontak MCP Usage Guide

## Overview

This guide covers how to use the Qontak MCP server as an end user - the workflows, patterns, and best practices for managing CRM data through the 61 available tools.

## Getting Started

### Available Tool Categories

| Category | Tools | Purpose |
|----------|-------|---------|
| **Contacts** | 10 | Manage people/individuals |
| **Companies** | 8 | Manage organizations |
| **Deals** | 14 | Manage sales opportunities |
| **Tickets** | 7 | Manage support tickets |
| **Tasks** | 8 | Manage to-do items |
| **Notes** | 5 | Add notes to any entity |
| **Products** | 5 | Manage product catalog |
| **Products Association** | 5 | Link products to deals/contacts/companies |

### General Workflow Pattern

Almost all resources follow this pattern:

1. **Get Template** → Understand available fields
2. **List** → See existing records
3. **Create** → Add new records
4. **Update** → Modify existing records

## Working with Contacts

### Finding a Contact

```
1. Search by listing all contacts
   → list_contacts(page=1, per_page=25)

2. Get specific contact details
   → get_contact(contact_id=67890)
```

### Creating a New Contact

```
Step 1: Check what fields are available (optional but recommended)
→ get_contact_template()

Step 2: Create the contact
→ create_contact(
    first_name="John",
    last_name="Doe",
    email="john@example.com",
    telephone="+1234567890",
    job_title="CTO",
    crm_company_id=11111  # Link to existing company
)
```

### Updating Contact Information

```
→ update_contact(
    contact_id=67890,
    email="newemail@example.com",
    job_title="VP Engineering"
)
```

### Viewing Contact History

```
→ get_contact_timeline(contact_id=67890)
→ get_contact_chat_history(contact_id=67890)
```

## Working with Deals

### Understanding Deal Pipelines

Deals exist in pipelines with stages. Each pipeline/stage can have different required fields.

```
Step 1: Get deal template to see field definitions
→ get_deal_template()

Step 2: Check required fields for your pipeline/stage
→ get_required_fields_for_deal(pipeline_id=100, stage_id=200)
```

### Creating a Deal

```
Step 1: Get required fields for target pipeline/stage
→ get_required_fields_for_deal(pipeline_id=100, stage_id=200)

Step 2: Create deal with all required fields
→ create_deal(
    name="Big Corp Opportunity",
    crm_pipeline_id=100,
    crm_stage_id=200,
    size=50000,
    expected_close_date="2025-06-30",
    contact_id=67890,
    company_id=11111
)
```

### Moving Deal to Next Stage

```
→ update_deal(
    deal_id=12345,
    crm_stage_id=300  # New stage ID
)
```

### Tracking Deal Progress

```
→ get_deal_timeline(deal_id=12345)
→ get_deal_stage_history(deal_id=12345)
```

## Working with Custom Fields (Dynamic Fields)

Many resources support custom fields. These are handled via `additional_fields`.

### Understanding Custom Fields

```
Step 1: Get template to see custom field definitions
→ get_deal_template()  # or get_contact_template(), etc.

Response includes:
{
  "id": 14840254,
  "name": "deal_source",
  "type": "Dropdown select",
  "required": true,
  "dropdown": [
    {"id": 1, "name": "Website"},
    {"id": 2, "name": "Referral"}
  ]
}
```

### Creating with Custom Fields

```
→ create_deal(
    name="New Deal",
    crm_pipeline_id=100,
    crm_stage_id=200,
    additional_fields=[
        {
            "id": 14840254,
            "name": "deal_source",
            "value": 1,  # ID from dropdown
            "value_name": null
        },
        {
            "id": 14840255,
            "name": "custom_text",
            "value": "Custom value",
            "value_name": null
        }
    ]
)
```

### Field Type Reference

| Type | Format | Example Value |
|------|--------|---------------|
| Single-line text | String | `"Some text"` |
| Text Area | String | `"Multi-line\ntext"` |
| Number | Number | `123.45` |
| Date | "YYYY-MM-DD" | `"2025-06-30"` |
| Date time | "YYYY-MM-DD HH:MM:SS" | `"2025-06-30 14:30:00"` |
| Dropdown select | Option ID | `1` |
| Multiple select | Array of IDs | `[1, 2, 3]` |
| Percentage | Number 0-100 | `75` |
| Checklist | Boolean | `true` or `false` |
| URL | String | `"https://example.com"` |

## Working with Tickets

### Ticket Workflow

Tickets are similar to deals but for support/customer service.

```
Step 1: Get ticket template
→ get_ticket_template()

Step 2: Check pipelines and stages
→ get_ticket_pipelines()

Step 3: Create ticket
→ create_ticket(
    name="Support Request",
    ticket_stage_id=100,
    priority="high",
    crm_lead_ids=[67890]  # Associated contacts
)
```

### Ticket Priorities

- `low`
- `medium`
- `high`
- `urgent`

## Working with Tasks

### Creating a Task

```
Step 1: Get task template to see required fields
→ get_task_template()

Step 2: Get available categories (optional)
→ list_task_categories()

Step 3: Create task
→ create_task(
    name="Follow up with client",
    due_date="2025-03-15",
    crm_task_status_id=100,  # Usually required
    detail="Call to discuss proposal",
    next_step="Schedule meeting",
    crm_deal_id=12345,  # Link to deal
    crm_person_id=67890  # Link to contact
)
```

### Task Priorities

- `low`
- `medium`
- `high`

## Working with Notes

### Adding Notes to Entities

Notes can be attached to contacts, companies, or deals.

```
→ create_note(
    title="Meeting Summary",
    content="Discussed pricing and timeline...",
    crm_lead_id=67890  # Or crm_company_id, crm_deal_id
)
```

### Finding Notes

```
→ list_notes(crm_lead_id=67890)  # Notes for specific contact
→ list_notes(crm_deal_id=12345)  # Notes for specific deal
→ list_notes()  # All recent notes
```

## Working with Products

### Product Catalog Management

```
→ list_products(page=1, per_page=25)
→ create_product(
    name="Premium Plan",
    sku="PLAN-PREMIUM-001",
    price=999.99,
    description="Annual subscription"
)
```

### Associating Products

Link products to deals, contacts, or companies:

```
→ create_products_association(
    product_id=100,
    entity_type="deal",  # or "contact", "company"
    entity_id=12345,
    quantity=2,
    price=999.99
)
```

## Common Workflows

### Sales Pipeline Workflow

```
1. Create Contact
   → create_contact(first_name="John", ...)

2. Create Company (if new account)
   → create_company(name="Big Corp", ...)

3. Update Contact with Company
   → update_contact(contact_id=100, crm_company_id=200)

4. Create Deal
   → get_required_fields_for_deal(pipeline_id=1, stage_id=10)
   → create_deal(name="Big Corp Deal", crm_pipeline_id=1, ...)

5. Associate Product
   → create_products_association(
       product_id=50,
       entity_type="deal",
       entity_id=deal_id
   )

6. Add Tasks
   → create_task(name="Send proposal", crm_deal_id=deal_id, ...)

7. Add Notes
   → create_note(title="Call notes", crm_deal_id=deal_id, ...)

8. Move Deal Through Stages
   → update_deal(deal_id=deal_id, crm_stage_id=20)
   → update_deal(deal_id=deal_id, crm_stage_id=30)
```

### Support Ticket Workflow

```
1. Find Contact
   → list_contacts() or identify existing

2. Create Ticket
   → create_ticket(
       name="Issue with product",
       ticket_stage_id=100,
       priority="high",
       crm_lead_ids=[contact_id]
   )

3. Add Notes
   → create_note(title="Issue details", ...)

4. Create Task for Follow-up
   → create_task(name="Resolve ticket", ...)

5. Update Ticket Status
   → update_ticket(ticket_id=100, ticket_stage_id=200)
```

### Data Import Workflow

```
For each record in import file:

1. Check if company exists
   → list_companies() or search

2. Create/Get Company
   → create_company(...) or use existing

3. Create Contact
   → create_contact(crm_company_id=company_id, ...)

4. Optionally create deal
   → create_deal(contact_id=contact_id, company_id=company_id, ...)
```

## Pagination Best Practices

### Handling Large Result Sets

```
Page 1: list_contacts(page=1, per_page=100)
Page 2: list_contacts(page=2, per_page=100)
...
Continue until fewer than per_page results returned
```

### Default Pagination

| Parameter | Default | Max |
|-----------|---------|-----|
| page | 1 | 10,000 |
| per_page | 25 | 100 |

## Multi-Tenant Usage

All tools support an optional `user_id` parameter for multi-tenant scenarios:

```
→ list_deals(page=1, per_page=25, user_id="tenant-123")
→ create_deal(..., user_id="tenant-123")
```

## Error Handling

### Common Errors

| Error | Cause | Solution |
|-------|-------|----------|
| "Validation error" | Missing required fields | Check template for required fields |
| "Invalid date format" | Wrong date format | Use YYYY-MM-DD |
| "Resource not found" | Wrong ID | Verify ID exists |
| "Rate limit exceeded" | Too many requests | Wait and retry |

### Response Format

Success:
```json
{
  "success": true,
  "data": {
    "response": {...},
    "meta": {...}
  }
}
```

Error:
```json
{
  "success": false,
  "error": "Error message",
  "error_code": "optional_code"
}
```

## Tips and Best Practices

1. **Always check templates first** when creating resources with custom fields
2. **Use pagination** for list operations (don't assume small result sets)
3. **Handle errors gracefully** - check `success` field in responses
4. **Link related entities** (contacts to companies, deals to contacts)
5. **Add notes** to track context and history
6. **Use tasks** for follow-up items and reminders
