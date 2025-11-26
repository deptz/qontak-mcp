# Qontak CRM API Field Limitations

## Overview
This document describes known limitations and special handling requirements for certain field types in the Qontak CRM API.

## File Upload Fields

### Affected Fields
- **Tasks**: `crm_task_attachment` (Lampiran/Attachment)
- **Tickets**: Similar attachment fields
- **Deals**: Document/file upload fields

### Limitation
File upload fields **cannot be set via the standard JSON API endpoints**. These fields require multipart/form-data requests with actual file uploads.

### Workaround
1. Create the task/ticket/deal first without the file attachment
2. Use a separate file upload endpoint or UI to attach files
3. The API currently does not support direct file uploads through JSON payload

### Example
```json
{
  "name": "Task with attachment",
  "due_date": "2024-12-31",
  // ❌ Cannot include: "crm_task_attachment": "file.pdf"
}
```

**Note**: To attach files, you must use the Qontak CRM web interface or a dedicated file upload API endpoint (if available).

---

## Checklist Fields

### Affected Fields
- **Tasks**: Custom fields of type "Checklist" (e.g., `my_checklist`)
- **Tickets**: Custom fields of type "Checklist"

### Implementation
Checklist fields are custom/additional fields with `type: "Checklist"` and have a special `checklist_details_attributes` structure.

### Structure
```json
{
  "id": 272681,
  "name": "my_checklist",
  "name_alias": "My Checklist",
  "additional_field": true,
  "type": "Checklist",
  "checklist_details_attributes": [
    {
      "crm_additional_option_id": 91767,
      "name": "Item 1",
      "completed": false,
      "due_date": "2024-12-31",
      "checklist_due_time": "14:00:00",
      "reminder": "2024-12-30 10:00:00",
      "user_ids": [123, 456]
    }
  ]
}
```

### Usage in API Calls

#### Getting Checklist Structure
1. Call `get_required_fields_for_task()` or `get_required_fields_for_ticket()`
2. Look for custom fields with `type: "Checklist"`
3. Review the `checklist_details_attributes` array for available options
4. Note the field `id` - you'll need this for the array format

#### Creating/Updating with Checklist Items
**IMPORTANT**: Both Tasks and Tickets use the **array format** for `additional_fields`:

```python
# Array format with id, name, value structure
additional_fields = [
    {
        "id": 16111169,  # Field ID from template
        "name": "task_checklist",  # Field name from template
        "value": json.dumps({  # Checklist value as JSON string
            "checklist_details_attributes": [
                {
                    "crm_additional_option_id": 91767,  # Required: ID of the checklist option
                    "name": "Complete documentation",   # Required: Item name
                    "completed": false,                 # Optional: Completion status
                    "due_date": "2024-12-31",          # Optional: Due date
                    "checklist_due_time": "17:00:00",  # Optional: Time
                    "reminder": "2024-12-30 10:00:00", # Optional: Reminder datetime
                    "user_ids": [123, 456]             # Optional: Assigned users
                }
            ]
        })
    }
]

# Convert to JSON string for the API call
additional_fields_json = json.dumps(additional_fields)

# Call the tool
create_task(
    name="Task with checklist",
    due_date="2024-12-31",
    additional_fields=additional_fields_json
)
```

### Important Notes
1. **`crm_additional_option_id` is required** for each checklist item
2. The checklist options are pre-defined in the custom field configuration
3. Get the available `crm_additional_option_id` values from `get_required_fields_for_task()` or `get_required_fields_for_ticket()`
4. You can only use checklist items that are defined in the field template
5. Multiple checklist items can be included in the array

### LLM Workflow for Checklist Fields
1. Call `get_required_fields_for_task()` to discover checklist fields
2. Present checklist options to the user (from `checklist_details_attributes`)
3. Ask which items to include and their details (due date, assignees, etc.)
4. Build the `additional_fields` JSON with proper structure
5. Call `create_task()` or `update_task()` with the `additional_fields` parameter

---

## GPS/Location Fields

### Affected Fields
- **Tasks**: `crm_checkin_attributes` (Lokasi GPS/GPS Location)

### Structure
```json
{
  "name": "crm_checkin_attributes",
  "name_alias": "Lokasi GPS",
  "type": "checkin"
}
```

### Usage
GPS location fields require latitude and longitude coordinates in array format:

```python
# Tasks and Tickets use array format for additional_fields
additional_fields = [
    {
        "id": null,  # This field typically doesn't have an ID in template
        "name": "crm_checkin_attributes",
        "value": json.dumps({
            "latitude": -6.2088,
            "longitude": 106.8456,
            "address": "Jakarta, Indonesia"  # Optional
        })
    }
]
```

---

## Photo and Signature Fields

### Affected Fields
- **Tasks**: Custom fields with `type: "Photo"` or `type: "Signature"`

### Limitation
Similar to file uploads, photo and signature fields typically require:
1. Multipart/form-data upload
2. Base64 encoded image data
3. Specific image format requirements

### Workaround
These fields may need to be handled through:
- The Qontak CRM web interface
- Mobile app for on-site photo/signature capture
- Separate API endpoints designed for image uploads

---

## Association Fields (Arrays)

### Tickets Only
Ticket associations support **arrays** of IDs:
- `crm_lead_ids`: Array of contact/lead IDs - `[1, 2, 3]`
- `crm_product_ids`: Array of product IDs - `[10, 20]`
- `crm_task_ids`: Array of task IDs - `[5, 6]`

### Tasks
Task associations support **single IDs** only:
- `crm_person_id`: Single contact ID - `123`
- `crm_company_id`: Single company ID - `456`
- `crm_deal_id`: Single deal ID - `789`

### Deals
Deal associations support **single IDs** only:
- `contact_id`: Single contact ID
- `company_id`: Single company ID

---

## Best Practices

### 1. Always Check Field Requirements First
```python
# For tasks
fields_info = get_required_fields_for_task()

# For tickets
fields_info = get_required_fields_for_ticket(pipeline_id=123)

# For deals
fields_info = get_required_fields_for_deal(pipeline_id=456)
```

### 2. Handle Special Fields Appropriately
- Use `additional_fields` parameter for custom fields - **ARRAY FORMAT for both Tasks and Tickets**
- Format: `[{"id": field_id, "name": "field_name", "value": "value"}]`
- Skip file upload fields in API calls (handle separately)
- Build checklist structures carefully with valid option IDs
- Use arrays for ticket associations, single IDs for tasks/deals

### 3. Provide Clear User Guidance
When implementing LLM workflows:
1. Inform users about file upload limitations
2. Show available checklist options before asking for selections
3. Validate association IDs exist before submission
4. Explain that some fields require web interface or mobile app

---

## Summary Table

| Field Type | API Support | Notes |
|------------|-------------|-------|
| Standard text/number | ✅ Full | Direct parameter or additional_fields |
| Dropdown fields | ✅ Full | Use ID from dropdown options |
| Date/DateTime | ✅ Full | Use ISO format or DD/MM/YYYY |
| File uploads | ❌ Limited | Requires separate upload mechanism |
| Photos | ❌ Limited | Requires image upload endpoint |
| Signatures | ❌ Limited | Requires image upload endpoint |
| Checklists | ✅ Full | Via additional_fields with proper structure |
| GPS/Location | ✅ Full | Via additional_fields with lat/long |
| Associations (single) | ✅ Full | Tasks and Deals |
| Associations (array) | ✅ Full | Tickets only |

---

## Related Documentation
- See `get_required_fields_for_task()` tool for field discovery
- See `get_required_fields_for_ticket()` tool for pipeline-specific fields
- See `get_required_fields_for_deal()` tool for pipeline-specific requirements
- Check tool signatures for correct parameter names and types
