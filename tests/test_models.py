"""
Comprehensive tests for Pydantic models module.

Tests input validation, field constraints, security features,
and edge cases for all model classes.
"""

import pytest
from pydantic import ValidationError
from qontak_mcp.models import (
    SecureBaseModel,
    TenantMixin,
    PaginationMixin,
    ResourceId,
    DealListParams,
    DealGetParams,
    DealCreateParams,
    DealUpdateParams,
    DealTimelineParams,
    TicketListParams,
    TicketGetParams,
    TicketCreateParams,
    TicketUpdateParams,
    TicketPipelinesParams,
    TaskListParams,
    TaskGetParams,
    TaskCreateParams,
    TaskUpdateParams,
    TaskCategoryCreateParams,
    TaskCategoryListParams,
)


class TestSecureBaseModel:
    """Test SecureBaseModel security configurations."""
    
    def test_forbid_extra_fields(self):
        """Test that extra fields are forbidden to prevent mass assignment."""
        with pytest.raises(ValidationError) as exc_info:
            DealGetParams(deal_id=1, extra_field="should fail")
        
        assert "extra_field" in str(exc_info.value).lower()
    
    def test_string_whitespace_stripping(self):
        """Test that whitespace is stripped from strings."""
        deal = DealCreateParams(
            name="  Deal Name  ",
            crm_pipeline_id=1,
            crm_stage_id=1
        )
        assert deal.name == "Deal Name"


class TestTenantMixin:
    """Test TenantMixin validation."""
    
    def test_valid_user_id(self):
        """Test valid user_id formats."""
        params = DealGetParams(deal_id=1, user_id="user-123_test")
        assert params.user_id == "user-123_test"
    
    def test_user_id_none(self):
        """Test that user_id can be None."""
        params = DealGetParams(deal_id=1, user_id=None)
        assert params.user_id is None
    
    def test_user_id_empty_string_becomes_none(self):
        """Test that empty string user_id becomes None."""
        params = DealGetParams(deal_id=1, user_id="   ")
        assert params.user_id is None
    
    def test_user_id_invalid_characters(self):
        """Test that invalid characters in user_id are rejected."""
        with pytest.raises(ValidationError) as exc_info:
            DealGetParams(deal_id=1, user_id="user@invalid")
        assert "alphanumeric" in str(exc_info.value).lower()
    
    def test_user_id_path_traversal_rejected(self):
        """Test that path traversal attempts are rejected."""
        with pytest.raises(ValidationError):
            DealGetParams(deal_id=1, user_id="../etc/passwd")
        
        with pytest.raises(ValidationError):
            DealGetParams(deal_id=1, user_id="user/admin")
        
        with pytest.raises(ValidationError):
            DealGetParams(deal_id=1, user_id="user\\admin")
    
    def test_user_id_injection_patterns_rejected(self):
        """Test that injection patterns are rejected."""
        # Command injection
        with pytest.raises(ValidationError):
            DealGetParams(deal_id=1, user_id="user;rm -rf")
        
        # Template injection
        with pytest.raises(ValidationError):
            DealGetParams(deal_id=1, user_id="user${cmd}")
        
        # NoSQL injection
        with pytest.raises(ValidationError):
            DealGetParams(deal_id=1, user_id="user{{var}}")
    
    def test_user_id_too_long(self):
        """Test that user_id over 128 chars is rejected."""
        long_user_id = "a" * 129
        with pytest.raises(ValidationError):
            DealGetParams(deal_id=1, user_id=long_user_id)
    
    def test_user_id_whitespace_stripping(self):
        """Test that whitespace is stripped from user_id."""
        params = DealGetParams(deal_id=1, user_id="  user123  ")
        assert params.user_id == "user123"


class TestPaginationMixin:
    """Test PaginationMixin validation."""
    
    def test_default_values(self):
        """Test default pagination values."""
        params = DealListParams()
        assert params.page == 1
        assert params.per_page == 25
    
    def test_valid_pagination(self):
        """Test valid pagination values."""
        params = DealListParams(page=5, per_page=50)
        assert params.page == 5
        assert params.per_page == 50
    
    def test_page_min_value(self):
        """Test page must be at least 1."""
        with pytest.raises(ValidationError) as exc_info:
            DealListParams(page=0)
        assert "greater than or equal to 1" in str(exc_info.value).lower()
    
    def test_page_max_value(self):
        """Test page maximum value."""
        with pytest.raises(ValidationError):
            DealListParams(page=10001)
    
    def test_per_page_min_value(self):
        """Test per_page must be at least 1."""
        with pytest.raises(ValidationError):
            DealListParams(per_page=0)
    
    def test_per_page_max_value(self):
        """Test per_page maximum is 100."""
        with pytest.raises(ValidationError):
            DealListParams(per_page=101)
    
    def test_per_page_boundary(self):
        """Test per_page at boundary value 100."""
        params = DealListParams(per_page=100)
        assert params.per_page == 100


class TestResourceId:
    """Test ResourceId model."""
    
    def test_valid_resource_id(self):
        """Test valid resource IDs."""
        res = ResourceId(id=123)
        assert res.id == 123
    
    def test_zero_id_rejected(self):
        """Test that zero ID is rejected."""
        with pytest.raises(ValidationError):
            ResourceId(id=0)
    
    def test_negative_id_rejected(self):
        """Test that negative ID is rejected."""
        with pytest.raises(ValidationError):
            ResourceId(id=-1)
    
    def test_very_large_id(self):
        """Test JavaScript safe integer limit."""
        # Just below 2^53
        res = ResourceId(id=9007199254740990)
        assert res.id == 9007199254740990
        
        # At or above 2^53 should fail
        with pytest.raises(ValidationError):
            ResourceId(id=2**53)


class TestDealModels:
    """Test Deal-related models."""
    
    def test_deal_list_params(self):
        """Test DealListParams validation."""
        params = DealListParams(
            stage_id=123,
            pipeline_id=456,
            page=2,
            per_page=50,
            user_id="user1"
        )
        assert params.stage_id == 123
        assert params.pipeline_id == 456
    
    def test_deal_get_params(self):
        """Test DealGetParams validation."""
        params = DealGetParams(deal_id=789, user_id="user1")
        assert params.deal_id == 789
    
    def test_deal_create_params_minimal(self):
        """Test DealCreateParams with minimal fields."""
        params = DealCreateParams(name="Test Deal", crm_pipeline_id=1, crm_stage_id=1)
        assert params.name == "Test Deal"
        assert params.crm_stage_id == 1
        assert params.contact_id is None
        assert params.amount is None
    
    def test_deal_create_params_full(self):
        """Test DealCreateParams with all fields."""
        params = DealCreateParams(
            name="Full Deal",
            crm_pipeline_id=1,
            crm_stage_id=1,
            contact_id=100,
            company_id=200,
            amount=1500.50,
            expected_close_date="2024-12-31",
            description="Deal description",
            custom_fields={"field1": "value1"},
            user_id="user1"
        )
        assert params.amount == 1500.50
        assert params.expected_close_date == "2024-12-31"
        assert params.custom_fields == {"field1": "value1"}
    
    def test_deal_name_too_short(self):
        """Test that deal name must have at least 1 character."""
        with pytest.raises(ValidationError):
            DealCreateParams(name="", crm_pipeline_id=1, crm_stage_id=1)
    
    def test_deal_name_too_long(self):
        """Test that deal name has maximum length."""
        long_name = "a" * 501
        with pytest.raises(ValidationError) as exc_info:
            DealCreateParams(name=long_name, crm_stage_id=1)
        assert "500" in str(exc_info.value)
    
    def test_deal_description_max_length(self):
        """Test deal description maximum length."""
        long_desc = "a" * 10001
        with pytest.raises(ValidationError):
            DealCreateParams(name="Deal", crm_pipeline_id=1, crm_stage_id=1, description=long_desc)
    
    def test_deal_amount_negative_rejected(self):
        """Test that negative amount is rejected."""
        with pytest.raises(ValidationError):
            DealCreateParams(name="Deal", crm_pipeline_id=1, crm_stage_id=1, amount=-100.0)
    
    def test_deal_amount_zero_accepted(self):
        """Test that zero amount is accepted."""
        params = DealCreateParams(name="Deal", crm_pipeline_id=1, crm_stage_id=1, amount=0.0)
        assert params.amount == 0.0
    
    def test_deal_invalid_date_format(self):
        """Test that invalid date format is rejected."""
        with pytest.raises(ValidationError):
            DealCreateParams(
                name="Deal",
                stage_id=1,
                expected_close_date="12/31/2024"
            )
    
    def test_deal_custom_fields_too_many(self):
        """Test that too many custom fields are rejected."""
        many_fields = {f"field{i}": f"value{i}" for i in range(101)}
        with pytest.raises(ValidationError) as exc_info:
            DealCreateParams(name="Deal", crm_pipeline_id=1, crm_stage_id=1, custom_fields=many_fields)
        assert "100" in str(exc_info.value)
    
    def test_deal_custom_fields_key_too_long(self):
        """Test that custom field key too long is rejected."""
        long_key = "a" * 257
        with pytest.raises(ValidationError):
            DealCreateParams(
                name="Deal",
                stage_id=1,
                custom_fields={long_key: "value"}
            )
    
    def test_deal_custom_fields_injection_rejected(self):
        """Test that custom field keys with injection patterns are rejected."""
        with pytest.raises(ValidationError):
            DealCreateParams(
                name="Deal",
                stage_id=1,
                custom_fields={"field$injection": "value"}
            )
        
        with pytest.raises(ValidationError):
            DealCreateParams(
                name="Deal",
                stage_id=1,
                custom_fields={"field;drop": "value"}
            )
    
    def test_deal_update_params(self):
        """Test DealUpdateParams validation."""
        params = DealUpdateParams(
            deal_id=123,
            name="Updated Deal",
            user_id="user1"
        )
        assert params.deal_id == 123
        assert params.name == "Updated Deal"
    
    def test_deal_update_requires_at_least_one_field(self):
        """Test DealUpdateParams requires at least one update field."""
        # Should fail with no update fields
        with pytest.raises(ValidationError) as exc_info:
            DealUpdateParams(deal_id=123, user_id="user1")
        assert "at least one field" in str(exc_info.value).lower()
        
        # Should succeed with at least one field
        params = DealUpdateParams(deal_id=123, name="Updated")
        assert params.name == "Updated"
    
    def test_deal_timeline_params(self):
        """Test DealTimelineParams validation."""
        params = DealTimelineParams(deal_id=123, page=1, per_page=25)
        assert params.deal_id == 123


class TestTicketModels:
    """Test Ticket-related models."""
    
    def test_ticket_create_params_minimal(self):
        """Test TicketCreateParams with minimal fields."""
        params = TicketCreateParams(
            name="Test Ticket",
            ticket_stage_id=1
        )
        assert params.name == "Test Ticket"
        assert params.ticket_stage_id == 1
    
    def test_ticket_name_validation(self):
        """Test ticket name validation."""
        # Too short
        with pytest.raises(ValidationError):
            TicketCreateParams(name="", crm_stage_id=1)
        
        # Too long
        long_name = "a" * 501
        with pytest.raises(ValidationError):
            TicketCreateParams(name=long_name, crm_stage_id=1)
    
    def test_ticket_priority_validation(self):
        """Test ticket priority validation."""
        # Valid priorities
        params = TicketCreateParams(name="Ticket", ticket_stage_id=1, priority="high")
        assert params.priority == "high"
        
        params = TicketCreateParams(name="Ticket", ticket_stage_id=1, priority="low")
        assert params.priority == "low"
        
        # Invalid priority
        with pytest.raises(ValidationError):
            TicketCreateParams(name="Ticket", ticket_stage_id=1, priority="invalid")
    
    def test_ticket_list_params(self):
        """Test TicketListParams validation."""
        params = TicketListParams(
            pipeline_id=10,
            page=1,
            per_page=25
        )
        assert params.pipeline_id == 10
    
    def test_ticket_update_params(self):
        """Test TicketUpdateParams validation."""
        params = TicketUpdateParams(
            ticket_id=456,
            name="Updated Ticket",
            priority="urgent"
        )
        assert params.ticket_id == 456
        assert params.priority == "urgent"
    
    def test_ticket_update_requires_at_least_one_field(self):
        """Test TicketUpdateParams requires at least one update field."""
        with pytest.raises(ValidationError) as exc_info:
            TicketUpdateParams(ticket_id=456)
        assert "at least one field" in str(exc_info.value).lower()
    
    def test_ticket_pipelines_params(self):
        """Test TicketPipelinesParams validation."""
        params = TicketPipelinesParams(page=1, per_page=50)
        assert params.page == 1


class TestTaskModels:
    """Test Task-related models."""
    
    def test_task_create_params_minimal(self):
        """Test TaskCreateParams with minimal fields."""
        params = TaskCreateParams(name="Test Task", due_date="2024-12-31")
        assert params.name == "Test Task"
        assert params.due_date == "2024-12-31"
    
    def test_task_name_validation(self):
        """Test task name validation."""
        # Too short
        with pytest.raises(ValidationError):
            TaskCreateParams(name="", due_date="2024-12-31")
        
        # Too long
        long_name = "a" * 501
        with pytest.raises(ValidationError):
            TaskCreateParams(name=long_name, due_date="2024-12-31")
    
    def test_task_due_date_validation(self):
        """Test task due_date validation."""
        # Valid date format
        params = TaskCreateParams(
            name="Task",
            due_date="2024-12-31"
        )
        assert params.due_date == "2024-12-31"
        
        # Valid datetime format
        params = TaskCreateParams(
            name="Task",
            due_date="2024-12-31 14:30:00"
        )
        assert params.due_date == "2024-12-31 14:30:00"
        
        # Invalid format
        with pytest.raises(ValidationError):
            TaskCreateParams(
                name="Task",
                due_date="31/12/2024"
            )
    
    def test_task_priority_validation(self):
        """Test task priority validation."""
        # Valid priorities
        params = TaskCreateParams(name="Task", due_date="2024-12-31", priority="high")
        assert params.priority == "high"
        
        # Invalid priority
        with pytest.raises(ValidationError):
            TaskCreateParams(name="Task", due_date="2024-12-31", priority="urgent")
    
    def test_task_list_params(self):
        """Test TaskListParams validation."""
        params = TaskListParams(
            category_id=5,
            page=2,
            per_page=30
        )
        assert params.category_id == 5
    
    def test_task_update_params(self):
        """Test TaskUpdateParams validation."""
        params = TaskUpdateParams(
            task_id=789,
            name="Updated Task",
            status="completed"
        )
        assert params.task_id == 789
        assert params.status == "completed"
    
    def test_task_update_requires_at_least_one_field(self):
        """Test TaskUpdateParams requires at least one update field."""
        with pytest.raises(ValidationError) as exc_info:
            TaskUpdateParams(task_id=789)
        assert "at least one field" in str(exc_info.value).lower()
    
    def test_task_update_status_validation(self):
        """Test task status validation in update."""
        # Valid statuses
        params = TaskUpdateParams(task_id=789, status="pending")
        assert params.status == "pending"
        
        params = TaskUpdateParams(task_id=789, status="completed")
        assert params.status == "completed"
        
        # Invalid status
        with pytest.raises(ValidationError):
            TaskUpdateParams(task_id=789, status="cancelled")
    
    def test_task_category_create_params(self):
        """Test TaskCategoryCreateParams validation."""
        params = TaskCategoryCreateParams(name="Work", color="#FF5733")
        assert params.name == "Work"
        assert params.color == "#FF5733"
    
    def test_task_category_color_validation(self):
        """Test task category color validation."""
        # Valid hex color
        params = TaskCategoryCreateParams(name="Cat", color="#ABC123")
        assert params.color == "#ABC123"
        
        # Valid color name
        params = TaskCategoryCreateParams(name="Cat", color="blue")
        assert params.color == "blue"
        
        # Invalid color
        with pytest.raises(ValidationError):
            TaskCategoryCreateParams(name="Cat", color="not-a-color!")
        
        # Invalid hex (too short)
        with pytest.raises(ValidationError):
            TaskCategoryCreateParams(name="Cat", color="#ABC")
    
    def test_task_category_list_params(self):
        """Test TaskCategoryListParams validation."""
        params = TaskCategoryListParams(page=1, per_page=20)
        assert params.page == 1


class TestModelSecurityFeatures:
    """Test security features across all models."""
    
    def test_models_reject_extra_fields(self):
        """Test that all models reject extra fields."""
        # This prevents mass assignment vulnerabilities
        
        with pytest.raises(ValidationError):
            DealCreateParams(name="Deal", crm_pipeline_id=1, crm_stage_id=1, extra="bad")
        
        with pytest.raises(ValidationError):
            TicketCreateParams(subject="Ticket", stage_id=1, extra="bad")
        
        with pytest.raises(ValidationError):
            TaskCreateParams(title="Task", task_category_id=1, extra="bad")
    
    def test_models_strip_whitespace(self):
        """Test that models strip whitespace from strings."""
        deal = DealCreateParams(name="  Trimmed  ", crm_pipeline_id=1, crm_stage_id=1)
        assert deal.name == "Trimmed"
        
        ticket = TicketCreateParams(name="  Trimmed  ", ticket_stage_id=1)
        assert ticket.name == "Trimmed"
        
        task = TaskCreateParams(name="  Trimmed  ", due_date="2024-12-31")
        assert task.name == "Trimmed"
    
    def test_models_validate_user_id_security(self):
        """Test that all models validate user_id for security."""
        # All should reject injection patterns
        
        with pytest.raises(ValidationError):
            DealGetParams(deal_id=1, user_id="user;inject")
        
        with pytest.raises(ValidationError):
            TicketGetParams(ticket_id=1, user_id="user${cmd}")
        
        with pytest.raises(ValidationError):
            TaskGetParams(task_id=1, user_id="../admin")
