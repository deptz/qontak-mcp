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
