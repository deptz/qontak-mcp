# Pydantic Models Guide

## Base Models

### SecureBaseModel

Foundation for all models with security settings:

```python
class SecureBaseModel(BaseModel):
    model_config = ConfigDict(
        extra='forbid',           # Prevent mass assignment attacks
        str_strip_whitespace=True,
        validate_default=True,
        use_enum_values=True,
    )
```

### TenantMixin

Adds multi-tenant support with user_id validation:

```python
class TenantMixin(BaseModel):
    user_id: Optional[str] = Field(
        default=None,
        description="User/tenant identifier",
        max_length=128,
    )
    
    @field_validator('user_id')
    @classmethod
    def validate_user_id(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        
        v = v.strip()
        if not v:
            return None
        
        # Pattern: alphanumeric, hyphens, underscores
        if not USER_ID_PATTERN.match(v):
            raise ValueError('Invalid user_id format')
        
        # Injection protection
        dangerous = ['..', '/', '\', ';', '|', '&', '`', '${', '#{', '{{']
        for pattern in dangerous:
            if pattern in v:
                raise ValueError('Invalid characters in user_id')
        
        return v
```

### PaginationMixin

Standard pagination parameters:

```python
class PaginationMixin(BaseModel):
    page: int = Field(default=1, ge=1, le=10000)
    per_page: int = Field(default=25, ge=1, le=100)
```

## Creating New Models

### Step 1: Inherit from SecureBaseModel

```python
class MyResourceParams(SecureBaseModel):
    """Parameters for my resource operation."""
    pass
```

### Step 2: Add Mixins as Needed

```python
class MyResourceListParams(SecureBaseModel, TenantMixin, PaginationMixin):
    """Parameters for listing with pagination and tenant isolation."""
    pass

class MyResourceCreateParams(SecureBaseModel, TenantMixin):
    """Parameters for creating a resource."""
    name: str = Field(min_length=1, max_length=MAX_NAME_LENGTH)
```

### Step 3: Define Fields with Validation

```python
class DealCreateParams(SecureBaseModel, TenantMixin):
    # Required fields
    name: str = Field(
        min_length=1,
        max_length=MAX_NAME_LENGTH,
        description="Deal name"
    )
    crm_pipeline_id: PositiveInt = Field(description="Pipeline ID")
    
    # Optional fields
    description: Optional[str] = Field(
        default=None,
        max_length=MAX_DESCRIPTION_LENGTH
    )
    expected_close_date: Optional[str] = Field(default=None)
    
    # Custom fields
    additional_fields: Optional[list[dict[str, Any]]] = Field(
        default=None,
        description="Custom field values"
    )
    
    @field_validator('expected_close_date')
    @classmethod
    def validate_date(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        if not DATE_PATTERN.match(v):
            raise ValueError('Date must be YYYY-MM-DD')
        return v
```

## Field Types

### Standard Types

```python
from typing import Optional, Annotated
from pydantic import Field

# Positive integer (for IDs)
PositiveInt = Annotated[int, Field(gt=0, lt=2**53)]

# String with constraints
name: str = Field(min_length=1, max_length=500)

# Enum pattern
from typing import Literal
priority: Literal["low", "medium", "high", "urgent"]

# Optional with default
optional_field: Optional[str] = Field(default=None, max_length=255)
```

### Custom Validators

```python
@field_validator('field_name')
@classmethod
def validate_field(cls, v: str) -> str:
    """Validate and transform field value."""
    if not v:
        raise ValueError('Field cannot be empty')
    return v.strip().lower()

@field_validator('date_field')
@classmethod
def validate_date(cls, v: Optional[str]) -> Optional[str]:
    """Validate date format."""
    if v is None:
        return None
    if not DATE_PATTERN.match(v):
        raise ValueError('Invalid date format')
    return v
```

### Model Validators

```python
@model_validator(mode='after')
def check_at_least_one_field(self) -> 'UpdateParams':
    """Ensure at least one update field provided."""
    update_fields = ['name', 'description', 'status']
    if not any(getattr(self, f, None) is not None for f in update_fields):
        raise ValueError('At least one field must be provided')
    return self

@model_validator(mode='after')
def check_dates_consistent(self) -> 'DateRangeParams':
    """Ensure start_date <= end_date."""
    if self.start_date and self.end_date:
        if self.start_date > self.end_date:
            raise ValueError('start_date must be before end_date')
    return self
```

## Model Categories

### List Parameters

```python
class ResourceListParams(SecureBaseModel, TenantMixin, PaginationMixin):
    """Parameters for listing resources."""
    
    # Optional filters
    status_id: Optional[PositiveInt] = Field(default=None)
    category_id: Optional[PositiveInt] = Field(default=None)
```

### Get Parameters

```python
class ResourceGetParams(SecureBaseModel, TenantMixin):
    """Parameters for getting a single resource."""
    
    resource_id: PositiveInt = Field(description="The resource ID")
```

### Create Parameters

```python
class ResourceCreateParams(SecureBaseModel, TenantMixin):
    """Parameters for creating a resource."""
    
    # Required
    name: str = Field(min_length=1, max_length=MAX_NAME_LENGTH)
    
    # Optional with defaults
    description: Optional[str] = Field(default=None)
    status: str = Field(default="active")
    
    # Related IDs
    parent_id: Optional[PositiveInt] = Field(default=None)
    
    # Custom fields
    additional_fields: Optional[list[dict[str, Any]]] = Field(default=None)
```

### Update Parameters

```python
class ResourceUpdateParams(SecureBaseModel, TenantMixin):
    """Parameters for updating a resource."""
    
    resource_id: PositiveInt = Field(description="Resource to update")
    
    # All optional for partial update
    name: Optional[str] = Field(default=None, min_length=1)
    description: Optional[str] = Field(default=None)
    status: Optional[str] = Field(default=None)
    
    @model_validator(mode='after')
    def check_at_least_one_field(self) -> 'ResourceUpdateParams':
        update_fields = ['name', 'description', 'status']
        if not any(getattr(self, f, None) is not None for f in update_fields):
            raise ValueError('At least one field required')
        return self
```

## Common Validation Patterns

### Date Validation

```python
DATE_PATTERN = re.compile(r'^\d{4}-\d{2}-\d{2}$')
DATETIME_PATTERN = re.compile(r'^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$')

@field_validator('date_field')
@classmethod
def validate_date(cls, v: Optional[str]) -> Optional[str]:
    if v is None:
        return None
    if DATE_PATTERN.match(v):
        return v
    raise ValueError('Date must be YYYY-MM-DD')
```

### Color Validation

```python
COLOR_PATTERN = re.compile(r'^#[0-9A-Fa-f]{6}$|^[a-zA-Z]{1,20}$')

@field_validator('color')
@classmethod
def validate_color(cls, v: Optional[str]) -> Optional[str]:
    if v is None:
        return None
    if not COLOR_PATTERN.match(v):
        raise ValueError('Color must be hex (#RRGGBB) or name')
    return v
```

### Custom Fields Validation

```python
@field_validator('custom_fields')
@classmethod
def validate_custom_fields(cls, v: Optional[dict]) -> Optional[dict]:
    if v is None:
        return None
    
    if len(v) > MAX_CUSTOM_FIELDS:
        raise ValueError(f'Max {MAX_CUSTOM_FIELDS} custom fields')
    
    for key in v.keys():
        if not isinstance(key, str):
            raise ValueError('Custom field keys must be strings')
        
        if len(key) > 256:
            raise ValueError('Key too long')
        
        # Injection check
        if any(c in key for c in ['$', '{', '}', ';', '|']):
            raise ValueError('Invalid characters in key')
    
    return v
```

### Email Validation

```python
from pydantic import EmailStr

class ContactCreateParams(SecureBaseModel, TenantMixin):
    email: Optional[EmailStr] = Field(default=None)
```

## Testing Models

### Valid Data Tests

```python
def test_valid_creation():
    """Test model accepts valid data."""
    params = DealCreateParams(
        name="Test Deal",
        crm_pipeline_id=123,
        crm_stage_id=456
    )
    assert params.name == "Test Deal"
    assert params.user_id is None
```

### Invalid Data Tests

```python
def test_name_required():
    """Test name cannot be empty."""
    with pytest.raises(ValidationError) as exc:
        DealCreateParams(
            name="",
            crm_pipeline_id=123,
            crm_stage_id=456
        )
    assert "name" in str(exc.value)
```

### Custom Validator Tests

```python
def test_date_format_validation():
    """Test date format validation."""
    # Valid
    params = DealCreateParams(
        name="Test",
        crm_pipeline_id=1,
        crm_stage_id=1,
        expected_close_date="2025-12-31"
    )
    assert params.expected_close_date == "2025-12-31"
    
    # Invalid
    with pytest.raises(ValidationError) as exc:
        DealCreateParams(
            name="Test",
            crm_pipeline_id=1,
            crm_stage_id=1,
            expected_close_date="31/12/2025"
        )
    assert "expected_close_date" in str(exc.value)
```

### Model Validator Tests

```python
def test_update_requires_one_field():
    """Test update requires at least one field."""
    with pytest.raises(ValidationError) as exc:
        DealUpdateParams(deal_id=123)  # No fields to update
    
    assert "at least one field" in str(exc.value).lower()
```

## Constants Reference

```python
# Field limits
MAX_NAME_LENGTH = 500
MAX_DESCRIPTION_LENGTH = 10000
MAX_CUSTOM_FIELDS = 100

# Patterns
USER_ID_PATTERN = re.compile(r'^[a-zA-Z0-9_-]{1,128}$')
DATE_PATTERN = re.compile(r'^\d{4}-\d{2}-\d{2}$')
DATETIME_PATTERN = re.compile(r'^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$')
COLOR_PATTERN = re.compile(r'^#[0-9A-Fa-f]{6}$|^[a-zA-Z]{1,20}$')

# Pagination
MAX_PAGE = 10000
MAX_PER_PAGE = 100

# Resource IDs
MAX_RESOURCE_ID = 2**53  # JavaScript safe integer
```
