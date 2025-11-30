"""
Pydantic models for input validation.

This module provides strict input validation using Pydantic models to ensure:
- Type safety for all API inputs
- Field-level validation with clear error messages
- Protection against injection attacks
- Consistent data formats
"""

import re
from typing import Optional, Any, Annotated
from pydantic import BaseModel, Field, field_validator, model_validator, ConfigDict


# =============================================================================
# Validation Constants
# =============================================================================

USER_ID_PATTERN = re.compile(r'^[a-zA-Z0-9_-]{1,128}$')
COLOR_PATTERN = re.compile(r'^#[0-9A-Fa-f]{6}$|^[a-zA-Z]{1,20}$')
DATE_PATTERN = re.compile(r'^\d{4}-\d{2}-\d{2}$')
DATETIME_PATTERN = re.compile(r'^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$')

# Field limits
MAX_NAME_LENGTH = 500
MAX_DESCRIPTION_LENGTH = 10000
MAX_CUSTOM_FIELDS = 100


# =============================================================================
# Base Models
# =============================================================================

class SecureBaseModel(BaseModel):
    """Base model with security-focused configuration."""
    
    model_config = ConfigDict(
        # Forbid extra fields to prevent mass assignment attacks
        extra='forbid',
        # Strip whitespace from strings
        str_strip_whitespace=True,
        # Validate default values
        validate_default=True,
        # Use enum values
        use_enum_values=True,
    )


class TenantMixin(BaseModel):
    """Mixin for multi-tenant support with user_id validation."""
    
    user_id: Optional[str] = Field(
        default=None,
        description="User/tenant identifier for multi-tenant scenarios",
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
            
        if not USER_ID_PATTERN.match(v):
            raise ValueError(
                'user_id must contain only alphanumeric characters, '
                'hyphens, and underscores (1-128 chars)'
            )
        
        # Check for injection patterns
        dangerous_patterns = ['..', '/', '\\', ';', '|', '&', '`', '${', '#{', '{{']
        for pattern in dangerous_patterns:
            if pattern in v:
                raise ValueError('user_id contains invalid characters')
        
        return v


class PaginationMixin(BaseModel):
    """Mixin for pagination parameters."""
    
    page: int = Field(
        default=1,
        ge=1,
        le=10000,
        description="Page number (1-indexed)"
    )
    per_page: int = Field(
        default=25,
        ge=1,
        le=100,
        description="Number of items per page (max 100)"
    )


# =============================================================================
# Resource ID Types
# =============================================================================

PositiveInt = Annotated[int, Field(gt=0, lt=2**53)]


class ResourceId(SecureBaseModel):
    """Validated resource ID."""
    
    id: PositiveInt = Field(description="Resource ID (positive integer)")


# =============================================================================
# Deal Models
# =============================================================================

class DealListParams(SecureBaseModel, TenantMixin, PaginationMixin):
    """Parameters for listing deals."""
    
    stage_id: Optional[PositiveInt] = Field(
        default=None,
        description="Filter by stage ID"
    )
    pipeline_id: Optional[PositiveInt] = Field(
        default=None,
        description="Filter by pipeline ID"
    )


class DealGetParams(SecureBaseModel, TenantMixin):
    """Parameters for getting a single deal."""
    
    deal_id: PositiveInt = Field(description="The deal ID to retrieve")


class DealCreateParams(SecureBaseModel, TenantMixin):
    """Parameters for creating a deal."""
    
    name: str = Field(
        min_length=1,
        max_length=MAX_NAME_LENGTH,
        description="Deal name/title"
    )
    crm_pipeline_id: PositiveInt = Field(description="CRM pipeline ID (required)")
    crm_stage_id: PositiveInt = Field(description="CRM pipeline stage ID (required)")
    size: Optional[float] = Field(
        default=None,
        ge=0,
        description="Deal size/value (may be required depending on pipeline configuration)"
    )
    contact_id: Optional[PositiveInt] = Field(
        default=None,
        description="Associated contact ID"
    )
    company_id: Optional[PositiveInt] = Field(
        default=None,
        description="Associated company ID"
    )
    amount: Optional[float] = Field(
        default=None,
        ge=0,
        description="Deal value/amount"
    )
    expected_close_date: Optional[str] = Field(
        default=None,
        description="Expected close date (YYYY-MM-DD)"
    )
    description: Optional[str] = Field(
        default=None,
        max_length=MAX_DESCRIPTION_LENGTH,
        description="Deal description"
    )
    custom_fields: Optional[dict[str, Any]] = Field(
        default=None,
        description="Custom field values"
    )
    
    @field_validator('expected_close_date')
    @classmethod
    def validate_date(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        if not DATE_PATTERN.match(v):
            raise ValueError('Date must be in YYYY-MM-DD format')
        return v
    
    @field_validator('custom_fields')
    @classmethod
    def validate_custom_fields(cls, v: Optional[dict]) -> Optional[dict]:
        if v is None:
            return None
        if len(v) > MAX_CUSTOM_FIELDS:
            raise ValueError(f'Maximum {MAX_CUSTOM_FIELDS} custom fields allowed')
        
        for key in v.keys():
            if not isinstance(key, str):
                raise ValueError('Custom field keys must be strings')
            if len(key) > 256:
                raise ValueError('Custom field key too long (max 256 chars)')
            # Check for injection in keys
            if any(c in key for c in ['$', '{', '}', ';', '|']):
                raise ValueError('Custom field key contains invalid characters')
        
        return v


class DealUpdateParams(SecureBaseModel, TenantMixin):
    """Parameters for updating a deal."""
    
    deal_id: PositiveInt = Field(description="The deal ID to update")
    name: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=MAX_NAME_LENGTH,
        description="New deal name"
    )
    crm_pipeline_id: Optional[PositiveInt] = Field(
        default=None,
        description="New CRM pipeline ID"
    )
    crm_stage_id: Optional[PositiveInt] = Field(
        default=None,
        description="New CRM stage ID"
    )
    contact_id: Optional[PositiveInt] = Field(
        default=None,
        description="New contact ID"
    )
    company_id: Optional[PositiveInt] = Field(
        default=None,
        description="New company ID"
    )
    amount: Optional[float] = Field(
        default=None,
        ge=0,
        description="New deal amount"
    )
    expected_close_date: Optional[str] = Field(
        default=None,
        description="New expected close date (YYYY-MM-DD)"
    )
    description: Optional[str] = Field(
        default=None,
        max_length=MAX_DESCRIPTION_LENGTH,
        description="New description"
    )
    custom_fields: Optional[dict[str, Any]] = Field(
        default=None,
        description="Custom field values to update"
    )
    
    @field_validator('expected_close_date')
    @classmethod
    def validate_date(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        if not DATE_PATTERN.match(v):
            raise ValueError('Date must be in YYYY-MM-DD format')
        return v
    
    @model_validator(mode='after')
    def check_at_least_one_field(self) -> 'DealUpdateParams':
        update_fields = ['name', 'crm_pipeline_id', 'crm_stage_id', 'contact_id', 'company_id', 
                        'amount', 'expected_close_date', 'description', 'custom_fields', 'additional_fields']
        if not any(getattr(self, f, None) is not None for f in update_fields):
            raise ValueError('At least one field must be provided for update')
        return self


class DealTimelineParams(SecureBaseModel, TenantMixin, PaginationMixin):
    """Parameters for getting deal timeline."""
    
    deal_id: PositiveInt = Field(description="The deal ID")


# =============================================================================
# Ticket Models
# =============================================================================

class TicketListParams(SecureBaseModel, TenantMixin, PaginationMixin):
    """Parameters for listing tickets."""
    
    pipeline_id: Optional[PositiveInt] = Field(
        default=None,
        description="Filter by pipeline ID"
    )


class TicketGetParams(SecureBaseModel, TenantMixin):
    """Parameters for getting a single ticket."""
    
    ticket_id: PositiveInt = Field(description="The ticket ID to retrieve")


class TicketCreateParams(SecureBaseModel, TenantMixin):
    """Parameters for creating a ticket."""
    
    name: str = Field(
        min_length=1,
        max_length=MAX_NAME_LENGTH,
        description="Ticket name/title"
    )
    ticket_stage_id: PositiveInt = Field(description="Pipeline stage ID (API field name: ticket_stage_id)")
    crm_lead_ids: Optional[list[PositiveInt]] = Field(
        default=None,
        description="Associated contact/lead IDs as array (API field name: crm_lead_ids)"
    )
    crm_company_id: Optional[PositiveInt] = Field(
        default=None,
        description="Associated company ID (API field name: crm_company_id)"
    )
    crm_product_ids: Optional[list[PositiveInt]] = Field(
        default=None,
        description="Associated product IDs as array (API field name: crm_product_ids)"
    )
    crm_task_ids: Optional[list[PositiveInt]] = Field(
        default=None,
        description="Associated task IDs as array (API field name: crm_task_ids)"
    )
    priority: Optional[str] = Field(
        default=None,
        pattern=r'^(low|medium|high|urgent)$',
        description="Priority level"
    )
    description: Optional[str] = Field(
        default=None,
        max_length=MAX_DESCRIPTION_LENGTH,
        description="Ticket description"
    )
    additional_fields: Optional[list[dict[str, Any]]] = Field(
        default=None,
        description="Additional/custom field values as array"
    )


class TicketUpdateParams(SecureBaseModel, TenantMixin):
    """Parameters for updating a ticket."""
    
    ticket_id: PositiveInt = Field(description="The ticket ID to update")
    name: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=MAX_NAME_LENGTH,
        description="New ticket name"
    )
    ticket_stage_id: Optional[PositiveInt] = Field(
        default=None,
        description="New stage ID (API field name: ticket_stage_id)"
    )
    crm_lead_ids: Optional[list[PositiveInt]] = Field(
        default=None,
        description="New contact/lead IDs as array (API field name: crm_lead_ids)"
    )
    crm_company_id: Optional[PositiveInt] = Field(
        default=None,
        description="New company ID (API field name: crm_company_id)"
    )
    crm_product_ids: Optional[list[PositiveInt]] = Field(
        default=None,
        description="New product IDs as array (API field name: crm_product_ids)"
    )
    crm_task_ids: Optional[list[PositiveInt]] = Field(
        default=None,
        description="New task IDs as array (API field name: crm_task_ids)"
    )
    priority: Optional[str] = Field(
        default=None,
        pattern=r'^(low|medium|high|urgent)$',
        description="New priority level"
    )
    description: Optional[str] = Field(
        default=None,
        max_length=MAX_DESCRIPTION_LENGTH,
        description="New description"
    )
    custom_fields: Optional[dict[str, Any]] = Field(
        default=None,
        description="Custom field values to update"
    )
    
    @model_validator(mode='after')
    def check_at_least_one_field(self) -> 'TicketUpdateParams':
        update_fields = ['name', 'ticket_stage_id', 'crm_lead_ids', 'crm_company_id',
                        'crm_product_ids', 'crm_task_ids', 'priority', 'description', 'custom_fields']
        if not any(getattr(self, f) is not None for f in update_fields):
            raise ValueError('At least one field must be provided for update')
        return self


class TicketPipelinesParams(SecureBaseModel, TenantMixin, PaginationMixin):
    """Parameters for getting ticket pipelines."""
    pass


# =============================================================================
# Task Models
# =============================================================================

class TaskListParams(SecureBaseModel, TenantMixin, PaginationMixin):
    """Parameters for listing tasks."""
    
    category_id: Optional[PositiveInt] = Field(
        default=None,
        description="Filter by category ID"
    )


class TaskGetParams(SecureBaseModel, TenantMixin):
    """Parameters for getting a single task."""
    
    task_id: PositiveInt = Field(description="The task ID to retrieve")


class TaskCreateParams(SecureBaseModel, TenantMixin):
    """Parameters for creating a task."""
    
    name: str = Field(
        min_length=1,
        max_length=MAX_NAME_LENGTH,
        description="Task name/title"
    )
    due_date: str = Field(
        description="Due date (YYYY-MM-DD or YYYY-MM-DD HH:MM:SS)"
    )
    crm_task_status_id: Optional[PositiveInt] = Field(
        default=None,
        description="Task status ID (usually required - check template)"
    )
    detail: Optional[str] = Field(
        default=None,
        max_length=MAX_DESCRIPTION_LENGTH,
        description="Task details/plan (usually required - check template)"
    )
    next_step: Optional[str] = Field(
        default=None,
        max_length=MAX_DESCRIPTION_LENGTH,
        description="Next steps/results (usually required - check template)"
    )
    category_id: Optional[PositiveInt] = Field(
        default=None,
        description="Task category ID"
    )
    crm_person_id: Optional[PositiveInt] = Field(
        default=None,
        description="Associated contact/person ID (API field name: crm_person_id)"
    )
    crm_company_id: Optional[PositiveInt] = Field(
        default=None,
        description="Associated company ID (API field name: crm_company_id)"
    )
    crm_deal_id: Optional[PositiveInt] = Field(
        default=None,
        description="Associated deal ID (API field name: crm_deal_id)"
    )
    priority: Optional[str] = Field(
        default=None,
        pattern=r'^(low|medium|high)$',
        description="Priority level"
    )
    description: Optional[str] = Field(
        default=None,
        max_length=MAX_DESCRIPTION_LENGTH,
        description="Task description"
    )
    additional_fields: Optional[list[dict[str, Any]]] = Field(
        default=None,
        description="Additional/custom field values as array"
    )
    
    @field_validator('due_date')
    @classmethod
    def validate_due_date(cls, v: str) -> str:
        if DATE_PATTERN.match(v) or DATETIME_PATTERN.match(v):
            return v
        raise ValueError('due_date must be in YYYY-MM-DD or YYYY-MM-DD HH:MM:SS format')


class TaskUpdateParams(SecureBaseModel, TenantMixin):
    """Parameters for updating a task."""
    
    task_id: PositiveInt = Field(description="The task ID to update")
    name: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=MAX_NAME_LENGTH,
        description="New task name"
    )
    due_date: Optional[str] = Field(
        default=None,
        description="New due date"
    )
    category_id: Optional[PositiveInt] = Field(
        default=None,
        description="New category ID"
    )
    crm_person_id: Optional[PositiveInt] = Field(
        default=None,
        description="New contact/person ID (API field name: crm_person_id)"
    )
    crm_company_id: Optional[PositiveInt] = Field(
        default=None,
        description="New company ID (API field name: crm_company_id)"
    )
    crm_deal_id: Optional[PositiveInt] = Field(
        default=None,
        description="New deal ID (API field name: crm_deal_id)"
    )
    priority: Optional[str] = Field(
        default=None,
        pattern=r'^(low|medium|high)$',
        description="New priority level"
    )
    description: Optional[str] = Field(
        default=None,
        max_length=MAX_DESCRIPTION_LENGTH,
        description="New description"
    )
    status: Optional[str] = Field(
        default=None,
        pattern=r'^(pending|completed)$',
        description="New status"
    )
    custom_fields: Optional[dict[str, Any]] = Field(
        default=None,
        description="Custom field values to update"
    )
    
    @field_validator('due_date')
    @classmethod
    def validate_due_date(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        if DATE_PATTERN.match(v) or DATETIME_PATTERN.match(v):
            return v
        raise ValueError('due_date must be in YYYY-MM-DD or YYYY-MM-DD HH:MM:SS format')
    
    @model_validator(mode='after')
    def check_at_least_one_field(self) -> 'TaskUpdateParams':
        update_fields = ['name', 'due_date', 'category_id', 'crm_person_id', 'crm_company_id',
                        'crm_deal_id', 'priority', 'description', 'status', 'custom_fields']
        if not any(getattr(self, f) is not None for f in update_fields):
            raise ValueError('At least one field must be provided for update')
        return self


class TaskCategoryCreateParams(SecureBaseModel, TenantMixin):
    """Parameters for creating a task category."""
    
    name: str = Field(
        min_length=1,
        max_length=100,
        description="Category name"
    )
    color: Optional[str] = Field(
        default=None,
        description="Category color (hex code like #FF5733 or color name)"
    )
    
    @field_validator('color')
    @classmethod
    def validate_color(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        if not COLOR_PATTERN.match(v):
            raise ValueError('Color must be a hex code (#RRGGBB) or color name')
        return v


class TaskCategoryListParams(SecureBaseModel, TenantMixin, PaginationMixin):
    """Parameters for listing task categories."""
    pass


# =============================================================================
# Contact Models
# =============================================================================

class ContactListParams(SecureBaseModel, TenantMixin, PaginationMixin):
    """Parameters for listing contacts."""
    pass


class ContactGetParams(SecureBaseModel, TenantMixin):
    """Parameters for getting a single contact."""
    
    contact_id: PositiveInt = Field(description="The contact ID to retrieve")


class ContactCreateParams(SecureBaseModel, TenantMixin):
    """Parameters for creating a contact."""
    
    first_name: str = Field(
        min_length=1,
        max_length=MAX_NAME_LENGTH,
        description="Contact first name"
    )
    last_name: Optional[str] = Field(
        default=None,
        max_length=MAX_NAME_LENGTH,
        description="Contact last name"
    )
    email: Optional[str] = Field(
        default=None,
        max_length=255,
        description="Email address"
    )
    telephone: Optional[str] = Field(
        default=None,
        max_length=50,
        description="Phone number"
    )
    job_title: Optional[str] = Field(
        default=None,
        max_length=255,
        description="Job title"
    )
    crm_status_id: Optional[PositiveInt] = Field(
        default=None,
        description="CRM status ID"
    )
    crm_company_id: Optional[PositiveInt] = Field(
        default=None,
        description="Associated company ID"
    )
    address: Optional[str] = Field(
        default=None,
        max_length=500,
        description="Street address"
    )
    city: Optional[str] = Field(
        default=None,
        max_length=100,
        description="City"
    )
    province: Optional[str] = Field(
        default=None,
        max_length=100,
        description="Province/State"
    )
    country: Optional[str] = Field(
        default=None,
        max_length=100,
        description="Country"
    )
    zipcode: Optional[str] = Field(
        default=None,
        max_length=20,
        description="ZIP/Postal code"
    )
    date_of_birth: Optional[str] = Field(
        default=None,
        description="Date of birth (YYYY-MM-DD)"
    )
    additional_fields: Optional[list[dict[str, Any]]] = Field(
        default=None,
        description="Additional/custom field values as array"
    )
    
    @field_validator('date_of_birth')
    @classmethod
    def validate_date(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        if not DATE_PATTERN.match(v):
            raise ValueError('Date must be in YYYY-MM-DD format')
        return v


class ContactUpdateParams(SecureBaseModel, TenantMixin):
    """Parameters for updating a contact."""
    
    contact_id: PositiveInt = Field(description="The contact ID to update")
    first_name: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=MAX_NAME_LENGTH,
        description="New first name"
    )
    last_name: Optional[str] = Field(
        default=None,
        max_length=MAX_NAME_LENGTH,
        description="New last name"
    )
    email: Optional[str] = Field(
        default=None,
        max_length=255,
        description="New email address"
    )
    telephone: Optional[str] = Field(
        default=None,
        max_length=50,
        description="New phone number"
    )
    job_title: Optional[str] = Field(
        default=None,
        max_length=255,
        description="New job title"
    )
    crm_status_id: Optional[PositiveInt] = Field(
        default=None,
        description="New CRM status ID"
    )
    crm_company_id: Optional[PositiveInt] = Field(
        default=None,
        description="New associated company ID"
    )
    address: Optional[str] = Field(
        default=None,
        max_length=500,
        description="New street address"
    )
    city: Optional[str] = Field(
        default=None,
        max_length=100,
        description="New city"
    )
    province: Optional[str] = Field(
        default=None,
        max_length=100,
        description="New province/state"
    )
    country: Optional[str] = Field(
        default=None,
        max_length=100,
        description="New country"
    )
    zipcode: Optional[str] = Field(
        default=None,
        max_length=20,
        description="New ZIP/Postal code"
    )
    date_of_birth: Optional[str] = Field(
        default=None,
        description="New date of birth (YYYY-MM-DD)"
    )
    additional_fields: Optional[list[dict[str, Any]]] = Field(
        default=None,
        description="Additional/custom fields to update"
    )
    
    @field_validator('date_of_birth')
    @classmethod
    def validate_date(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        if not DATE_PATTERN.match(v):
            raise ValueError('Date must be in YYYY-MM-DD format')
        return v
    
    @model_validator(mode='after')
    def check_at_least_one_field(self) -> 'ContactUpdateParams':
        update_fields = ['first_name', 'last_name', 'email', 'telephone', 'job_title',
                        'crm_status_id', 'crm_company_id', 'address', 'city', 'province',
                        'country', 'zipcode', 'date_of_birth', 'additional_fields']
        if not any(getattr(self, f) is not None for f in update_fields):
            raise ValueError('At least one field must be provided for update')
        return self


class ContactTimelineParams(SecureBaseModel, TenantMixin, PaginationMixin):
    """Parameters for getting contact timeline."""
    
    contact_id: PositiveInt = Field(description="The contact ID")


# =============================================================================
# Company Models
# =============================================================================

class CompanyListParams(SecureBaseModel, TenantMixin, PaginationMixin):
    """Parameters for listing companies."""
    pass


class CompanyGetParams(SecureBaseModel, TenantMixin):
    """Parameters for getting a single company."""
    
    company_id: PositiveInt = Field(description="The company ID to retrieve")


class CompanyCreateParams(SecureBaseModel, TenantMixin):
    """Parameters for creating a company."""
    
    name: str = Field(
        min_length=1,
        max_length=MAX_NAME_LENGTH,
        description="Company name"
    )
    crm_status_id: Optional[PositiveInt] = Field(
        default=None,
        description="CRM status ID"
    )
    address: Optional[str] = Field(
        default=None,
        max_length=500,
        description="Street address"
    )
    city: Optional[str] = Field(
        default=None,
        max_length=100,
        description="City"
    )
    province: Optional[str] = Field(
        default=None,
        max_length=100,
        description="Province/State"
    )
    country: Optional[str] = Field(
        default=None,
        max_length=100,
        description="Country"
    )
    zipcode: Optional[str] = Field(
        default=None,
        max_length=20,
        description="ZIP/Postal code"
    )
    telephone: Optional[str] = Field(
        default=None,
        max_length=50,
        description="Phone number"
    )
    email: Optional[str] = Field(
        default=None,
        max_length=255,
        description="Email address"
    )
    website: Optional[str] = Field(
        default=None,
        max_length=500,
        description="Website URL"
    )
    additional_fields: Optional[list[dict[str, Any]]] = Field(
        default=None,
        description="Additional/custom field values as array"
    )


class CompanyUpdateParams(SecureBaseModel, TenantMixin):
    """Parameters for updating a company."""
    
    company_id: PositiveInt = Field(description="The company ID to update")
    name: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=MAX_NAME_LENGTH,
        description="New company name"
    )
    crm_status_id: Optional[PositiveInt] = Field(
        default=None,
        description="New CRM status ID"
    )
    address: Optional[str] = Field(
        default=None,
        max_length=500,
        description="New street address"
    )
    city: Optional[str] = Field(
        default=None,
        max_length=100,
        description="New city"
    )
    province: Optional[str] = Field(
        default=None,
        max_length=100,
        description="New province/state"
    )
    country: Optional[str] = Field(
        default=None,
        max_length=100,
        description="New country"
    )
    zipcode: Optional[str] = Field(
        default=None,
        max_length=20,
        description="New ZIP/Postal code"
    )
    telephone: Optional[str] = Field(
        default=None,
        max_length=50,
        description="New phone number"
    )
    email: Optional[str] = Field(
        default=None,
        max_length=255,
        description="New email address"
    )
    website: Optional[str] = Field(
        default=None,
        max_length=500,
        description="New website URL"
    )
    additional_fields: Optional[list[dict[str, Any]]] = Field(
        default=None,
        description="Additional/custom fields to update"
    )
    
    @model_validator(mode='after')
    def check_at_least_one_field(self) -> 'CompanyUpdateParams':
        update_fields = ['name', 'crm_status_id', 'address', 'city', 'province',
                        'country', 'zipcode', 'telephone', 'email', 'website',
                        'additional_fields']
        if not any(getattr(self, f) is not None for f in update_fields):
            raise ValueError('At least one field must be provided for update')
        return self


class CompanyTimelineParams(SecureBaseModel, TenantMixin, PaginationMixin):
    """Parameters for getting company timeline."""
    
    company_id: PositiveInt = Field(description="The company ID")


# =============================================================================
# Note Models
# =============================================================================

class NoteListParams(SecureBaseModel, TenantMixin, PaginationMixin):
    """Parameters for listing notes."""
    
    crm_lead_id: Optional[PositiveInt] = Field(
        default=None,
        description="Filter by associated contact/lead ID"
    )
    crm_company_id: Optional[PositiveInt] = Field(
        default=None,
        description="Filter by associated company ID"
    )
    crm_deal_id: Optional[PositiveInt] = Field(
        default=None,
        description="Filter by associated deal ID"
    )


class NoteGetParams(SecureBaseModel, TenantMixin):
    """Parameters for getting a single note."""
    
    note_id: PositiveInt = Field(description="The note ID to retrieve")


class NoteCreateParams(SecureBaseModel, TenantMixin):
    """Parameters for creating a note."""
    
    title: str = Field(
        min_length=1,
        max_length=MAX_NAME_LENGTH,
        description="Note title"
    )
    content: str = Field(
        min_length=1,
        max_length=MAX_DESCRIPTION_LENGTH,
        description="Note content/body"
    )
    crm_lead_id: Optional[PositiveInt] = Field(
        default=None,
        description="Associated contact/lead ID"
    )
    crm_company_id: Optional[PositiveInt] = Field(
        default=None,
        description="Associated company ID"
    )
    crm_deal_id: Optional[PositiveInt] = Field(
        default=None,
        description="Associated deal ID"
    )


class NoteUpdateParams(SecureBaseModel, TenantMixin):
    """Parameters for updating a note."""
    
    note_id: PositiveInt = Field(description="The note ID to update")
    title: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=MAX_NAME_LENGTH,
        description="New note title"
    )
    content: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=MAX_DESCRIPTION_LENGTH,
        description="New note content/body"
    )
    
    @model_validator(mode='after')
    def check_at_least_one_field(self) -> 'NoteUpdateParams':
        if self.title is None and self.content is None:
            raise ValueError('At least one field (title or content) must be provided for update')
        return self


# =============================================================================
# Product Models
# =============================================================================

class ProductListParams(SecureBaseModel, TenantMixin, PaginationMixin):
    """Parameters for listing products."""
    pass


class ProductGetParams(SecureBaseModel, TenantMixin):
    """Parameters for getting a single product."""
    
    product_id: PositiveInt = Field(description="The product ID to retrieve")


class ProductCreateParams(SecureBaseModel, TenantMixin):
    """Parameters for creating a product."""
    
    name: str = Field(
        min_length=1,
        max_length=MAX_NAME_LENGTH,
        description="Product name"
    )
    price: Optional[float] = Field(
        default=None,
        ge=0,
        description="Product price"
    )
    sku: Optional[str] = Field(
        default=None,
        max_length=100,
        description="SKU/Product code"
    )
    description: Optional[str] = Field(
        default=None,
        max_length=MAX_DESCRIPTION_LENGTH,
        description="Product description"
    )
    category: Optional[str] = Field(
        default=None,
        max_length=100,
        description="Product category"
    )


class ProductUpdateParams(SecureBaseModel, TenantMixin):
    """Parameters for updating a product."""
    
    product_id: PositiveInt = Field(description="The product ID to update")
    name: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=MAX_NAME_LENGTH,
        description="New product name"
    )
    price: Optional[float] = Field(
        default=None,
        ge=0,
        description="New product price"
    )
    sku: Optional[str] = Field(
        default=None,
        max_length=100,
        description="New SKU/Product code"
    )
    description: Optional[str] = Field(
        default=None,
        max_length=MAX_DESCRIPTION_LENGTH,
        description="New product description"
    )
    category: Optional[str] = Field(
        default=None,
        max_length=100,
        description="New product category"
    )
    
    @model_validator(mode='after')
    def check_at_least_one_field(self) -> 'ProductUpdateParams':
        update_fields = ['name', 'price', 'sku', 'description', 'category']
        if not any(getattr(self, f) is not None for f in update_fields):
            raise ValueError('At least one field must be provided for update')
        return self


# =============================================================================
# Products Association Models
# =============================================================================

class ProductsAssociationListParams(SecureBaseModel, TenantMixin, PaginationMixin):
    """Parameters for listing product associations."""
    pass


class ProductsAssociationGetParams(SecureBaseModel, TenantMixin):
    """Parameters for getting a single product association."""
    
    association_id: PositiveInt = Field(description="The product association ID to retrieve")


class ProductsAssociationCreateParams(SecureBaseModel, TenantMixin):
    """Parameters for creating a product association."""
    
    product_id: PositiveInt = Field(description="Product ID to associate")
    crm_deal_id: Optional[PositiveInt] = Field(
        default=None,
        description="Deal ID to associate with"
    )
    crm_lead_id: Optional[PositiveInt] = Field(
        default=None,
        description="Contact/Lead ID to associate with"
    )
    crm_company_id: Optional[PositiveInt] = Field(
        default=None,
        description="Company ID to associate with"
    )
    quantity: Optional[int] = Field(
        default=None,
        ge=1,
        description="Quantity of product"
    )
    price: Optional[float] = Field(
        default=None,
        ge=0,
        description="Price for this association"
    )


class ProductsAssociationUpdateParams(SecureBaseModel, TenantMixin):
    """Parameters for updating a product association."""
    
    association_id: PositiveInt = Field(description="The product association ID to update")
    quantity: Optional[int] = Field(
        default=None,
        ge=1,
        description="New quantity"
    )
    price: Optional[float] = Field(
        default=None,
        ge=0,
        description="New price"
    )
    
    @model_validator(mode='after')
    def check_at_least_one_field(self) -> 'ProductsAssociationUpdateParams':
        if self.quantity is None and self.price is None:
            raise ValueError('At least one field (quantity or price) must be provided for update')
        return self
