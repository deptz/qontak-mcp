"""
Proof of Concept Tests for All MCP Tools

This test suite validates that all tools work correctly after recent changes,
particularly around custom field handling and parameter naming.

Tests cover:
- Deals: list, create, get, update, templates, timelines, stage history, pipelines
- Tasks: list, create, get, update, categories, required fields
- Tickets: list, create, get, update, pipelines, required fields
"""

import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from qontak_mcp.tools.deals import register_deal_tools_lazy
from qontak_mcp.tools.tasks import register_task_tools_lazy
from qontak_mcp.tools.tickets import register_ticket_tools_lazy


class MockFastMCP:
    """Mock FastMCP for testing."""
    def __init__(self):
        self.tools = {}
    
    def tool(self):
        def decorator(func):
            self.tools[func.__name__] = func
            return func
        return decorator


@pytest.fixture
def mock_mcp():
    """Create mock MCP instance."""
    return MockFastMCP()


@pytest.fixture
def mock_client():
    """Create mock Qontak client."""
    return MagicMock()


@pytest.fixture
def mock_client_factory(mock_client):
    """Create mock client factory."""
    return lambda: mock_client


class TestDealsToolsPoC:
    """Proof of Concept tests for all Deal tools."""
    
    @pytest.mark.asyncio
    async def test_list_deals_workflow(self, mock_mcp, mock_client_factory, mock_client):
        """Test list_deals with filters."""
        register_deal_tools_lazy(mock_mcp, mock_client_factory)
        tool = mock_mcp.tools["list_deals"]
        
        mock_client.list_deals = AsyncMock(return_value={
            "success": True,
            "data": {
                "data": [
                    {"id": 1, "name": "Deal 1", "crm_stage_id": 5, "amount": 1000},
                    {"id": 2, "name": "Deal 2", "crm_stage_id": 5, "amount": 2000}
                ]
            }
        })
        
        result_json = await tool(page=1, per_page=10, stage_id=5, pipeline_id=1)
        result = json.loads(result_json)
        
        assert result["success"] is True
        assert len(result["data"]["data"]) == 2
        mock_client.list_deals.assert_called_once()
        call_kwargs = mock_client.list_deals.call_args.kwargs
        assert call_kwargs["stage_id"] == 5
        assert call_kwargs["pipeline_id"] == 1
    
    @pytest.mark.asyncio
    async def test_create_deal_with_custom_fields(self, mock_mcp, mock_client_factory, mock_client):
        """Test create_deal with custom fields in array format."""
        register_deal_tools_lazy(mock_mcp, mock_client_factory)
        tool = mock_mcp.tools["create_deal"]
        
        mock_client.create_deal = AsyncMock(return_value={
            "success": True,
            "data": {"data": {"id": 123, "name": "New Deal"}}
        })
        
        custom_fields_json = '{"industry": "tech", "size": "large"}'
        result_json = await tool(
            name="New Deal",
            crm_pipeline_id=1,
            crm_stage_id=2,
            contact_id=100,
            company_id=200,
            amount=50000.00,
            expected_close_date="2025-12-31",
            description="Important deal",
            custom_fields=custom_fields_json
        )
        result = json.loads(result_json)
        
        assert result["success"] is True
        assert result["data"]["data"]["id"] == 123
        mock_client.create_deal.assert_called_once()
        
        # Verify custom_fields parsed correctly
        call_kwargs = mock_client.create_deal.call_args.kwargs
        deal_data = call_kwargs["deal_data"]
        assert deal_data["custom_fields"] == {"industry": "tech", "size": "large"}
    
    @pytest.mark.asyncio
    async def test_get_deal_details(self, mock_mcp, mock_client_factory, mock_client):
        """Test get_deal retrieves deal details."""
        register_deal_tools_lazy(mock_mcp, mock_client_factory)
        tool = mock_mcp.tools["get_deal"]
        
        mock_client.get_deal = AsyncMock(return_value={
            "success": True,
            "data": {"data": {"id": 123, "name": "Deal 123", "amount": 50000}}
        })
        
        result_json = await tool(deal_id=123)
        result = json.loads(result_json)
        
        assert result["success"] is True
        assert result["data"]["data"]["id"] == 123
        mock_client.get_deal.assert_called_once_with(deal_id=123, user_id=None)
    
    @pytest.mark.asyncio
    async def test_update_deal_partial_fields(self, mock_mcp, mock_client_factory, mock_client):
        """Test update_deal with partial field updates."""
        register_deal_tools_lazy(mock_mcp, mock_client_factory)
        tool = mock_mcp.tools["update_deal"]
        
        mock_client.update_deal = AsyncMock(return_value={
            "success": True,
            "data": {"data": {"id": 123, "name": "Updated Deal"}}
        })
        
        result_json = await tool(
            deal_id=123,
            name="Updated Deal",
            crm_stage_id=3,
            amount=75000.00,
            custom_fields='{"industry": "healthcare"}'
        )
        result = json.loads(result_json)
        
        assert result["success"] is True
        mock_client.update_deal.assert_called_once()
        
        # Verify only specified fields are in deal_data
        call_kwargs = mock_client.update_deal.call_args.kwargs
        deal_data = call_kwargs["deal_data"]
        assert deal_data["name"] == "Updated Deal"
        assert deal_data["crm_stage_id"] == 3
        assert deal_data["amount"] == 75000.00
        assert "contact_id" not in deal_data  # Not specified, shouldn't be in update
    
    @pytest.mark.asyncio
    async def test_get_deal_template(self, mock_mcp, mock_client_factory, mock_client):
        """Test get_deal_template retrieves pipeline templates."""
        register_deal_tools_lazy(mock_mcp, mock_client_factory)
        tool = mock_mcp.tools["get_deal_template"]
        
        mock_client.get_deal_template = AsyncMock(return_value={
            "success": True,
            "data": {"data": [{"id": 1, "name": "Standard Pipeline"}]}
        })
        
        result_json = await tool()
        result = json.loads(result_json)
        
        assert result["success"] is True
        mock_client.get_deal_template.assert_called_once_with(user_id=None)
    
    @pytest.mark.asyncio
    async def test_get_deal_timeline(self, mock_mcp, mock_client_factory, mock_client):
        """Test get_deal_timeline retrieves activity history."""
        register_deal_tools_lazy(mock_mcp, mock_client_factory)
        tool = mock_mcp.tools["get_deal_timeline"]
        
        mock_client.get_deal_timeline = AsyncMock(return_value={
            "success": True,
            "data": {"data": [{"id": 1, "action": "created"}]}
        })
        
        result_json = await tool(deal_id=123, page=1, per_page=20)
        result = json.loads(result_json)
        
        assert result["success"] is True
        mock_client.get_deal_timeline.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_deal_stage_history(self, mock_mcp, mock_client_factory, mock_client):
        """Test get_deal_stage_history retrieves stage changes."""
        register_deal_tools_lazy(mock_mcp, mock_client_factory)
        tool = mock_mcp.tools["get_deal_stage_history"]
        
        mock_client.get_deal_stage_history = AsyncMock(return_value={
            "success": True,
            "data": {"data": [{"from_stage": 1, "to_stage": 2}]}
        })
        
        result_json = await tool(deal_id=123)
        result = json.loads(result_json)
        
        assert result["success"] is True
        mock_client.get_deal_stage_history.assert_called_once_with(deal_id=123, page=1, per_page=25, user_id=None)
    
    # Note: get_deal_pipelines tool doesn't exist - pipelines are part of get_deal_template


class TestTasksToolsPoC:
    """Proof of Concept tests for all Task tools."""
    
    @pytest.mark.asyncio
    async def test_list_tasks_workflow(self, mock_mcp, mock_client_factory, mock_client):
        """Test list_tasks with pagination."""
        register_task_tools_lazy(mock_mcp, mock_client_factory)
        tool = mock_mcp.tools["list_tasks"]
        
        mock_client.list_tasks = AsyncMock(return_value={
            "success": True,
            "data": {
                "data": [
                    {"id": 1, "name": "Task 1", "status": "pending"},
                    {"id": 2, "name": "Task 2", "status": "completed"}
                ]
            }
        })
        
        result_json = await tool(page=1, per_page=10)
        result = json.loads(result_json)
        
        assert result["success"] is True
        assert len(result["data"]["data"]) == 2
        mock_client.list_tasks.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_create_task_with_additional_fields(self, mock_mcp, mock_client_factory, mock_client):
        """Test create_task with additional_fields in array format."""
        register_task_tools_lazy(mock_mcp, mock_client_factory)
        tool = mock_mcp.tools["create_task"]
        
        mock_client.create_task = AsyncMock(return_value={
            "success": True,
            "data": {"data": {"id": 456, "name": "New Task"}}
        })
        
        # Test with array format for additional_fields
        additional_fields_json = '[{"id": 185967, "name": "photo", "value": "https://example.com/photo.jpg"}]'
        result_json = await tool(
            name="New Task",
            due_date="2025-12-31",
            category_id=5,
            crm_person_id=100,
            crm_company_id=200,
            crm_deal_id=300,
            priority="high",
            description="Important task",
            additional_fields=additional_fields_json
        )
        result = json.loads(result_json)
        
        assert result["success"] is True
        assert result["data"]["data"]["id"] == 456
        mock_client.create_task.assert_called_once()
        
        # Verify additional_fields are in correct format
        call_kwargs = mock_client.create_task.call_args.kwargs
        task_data = call_kwargs["task_data"]
        assert isinstance(task_data["additional_fields"], list)
        assert task_data["additional_fields"][0]["name"] == "photo"
    
    @pytest.mark.asyncio
    async def test_get_task_details(self, mock_mcp, mock_client_factory, mock_client):
        """Test get_task retrieves task details."""
        register_task_tools_lazy(mock_mcp, mock_client_factory)
        tool = mock_mcp.tools["get_task"]
        
        mock_client.get_task = AsyncMock(return_value={
            "success": True,
            "data": {"data": {"id": 456, "name": "Task 456"}}
        })
        
        result_json = await tool(task_id=456)
        result = json.loads(result_json)
        
        assert result["success"] is True
        assert result["data"]["data"]["id"] == 456
        mock_client.get_task.assert_called_once_with(task_id=456, user_id=None)
    
    @pytest.mark.asyncio
    async def test_update_task_with_simplified_names(self, mock_mcp, mock_client_factory, mock_client):
        """Test update_task using simplified parameter names."""
        register_task_tools_lazy(mock_mcp, mock_client_factory)
        tool = mock_mcp.tools["update_task"]
        
        mock_client.update_task = AsyncMock(return_value={
            "success": True,
            "data": {"data": {"id": 456, "name": "Updated Task"}}
        })
        
        # Use simplified names: contact_id, company_id, deal_id, custom_fields
        result_json = await tool(
            task_id=456,
            name="Updated Task",
            contact_id=150,
            company_id=250,
            deal_id=350,
            status="completed",
            custom_fields='{"custom_field": "value"}'
        )
        result = json.loads(result_json)
        
        assert result["success"] is True
        mock_client.update_task.assert_called_once()
        
        # Verify simplified names are mapped to API names
        call_kwargs = mock_client.update_task.call_args.kwargs
        task_data = call_kwargs["task_data"]
        assert task_data["contact_id"] == 150  # Mapped from contact_id
        assert task_data["company_id"] == 250  # Mapped from company_id
        assert task_data["deal_id"] == 350     # Mapped from deal_id
    
    @pytest.mark.asyncio
    async def test_list_task_categories(self, mock_mcp, mock_client_factory, mock_client):
        """Test list_task_categories retrieves available categories."""
        register_task_tools_lazy(mock_mcp, mock_client_factory)
        tool = mock_mcp.tools["list_task_categories"]
        
        mock_client.list_task_categories = AsyncMock(return_value={
            "success": True,
            "data": {"data": [
                {"id": 1, "name": "Follow-up"},
                {"id": 2, "name": "Meeting"}
            ]}
        })
        
        result_json = await tool()
        result = json.loads(result_json)
        
        assert result["success"] is True
        assert len(result["data"]["data"]) == 2
        mock_client.list_task_categories.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_required_fields_for_task(self, mock_mcp, mock_client_factory, mock_client):
        """Test get_required_fields_for_task retrieves field definitions."""
        register_task_tools_lazy(mock_mcp, mock_client_factory)
        tool = mock_mcp.tools["get_required_fields_for_task"]
        
        mock_client.get_task_template = AsyncMock(return_value={
            "success": True,
            "data": {"response": [
                {"id": 185967, "name": "photo", "type": "text", "required": False}
            ]}
        })
        
        result_json = await tool()
        result = json.loads(result_json)
        
        assert result["success"] is True
        # Tool now returns required_* and optional_* categorized fields
        assert "required_standard_fields" in result
        assert "required_custom_fields" in result
        assert "optional_standard_fields" in result
        assert "optional_custom_fields" in result
        assert isinstance(result["optional_custom_fields"], list)
        mock_client.get_task_template.assert_called_once()


class TestTicketsToolsPoC:
    """Proof of Concept tests for all Ticket tools."""
    
    @pytest.mark.asyncio
    async def test_list_tickets_workflow(self, mock_mcp, mock_client_factory, mock_client):
        """Test list_tickets with pagination."""
        register_ticket_tools_lazy(mock_mcp, mock_client_factory)
        tool = mock_mcp.tools["list_tickets"]
        
        mock_client.list_tickets = AsyncMock(return_value={
            "success": True,
            "data": {
                "data": [
                    {"id": 1, "name": "Ticket 1", "priority": "high"},
                    {"id": 2, "name": "Ticket 2", "priority": "medium"}
                ]
            }
        })
        
        result_json = await tool(page=1, per_page=10)
        result = json.loads(result_json)
        
        assert result["success"] is True
        assert len(result["data"]["data"]) == 2
        mock_client.list_tickets.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_create_ticket_with_additional_fields(self, mock_mcp, mock_client_factory, mock_client):
        """Test create_ticket with additional_fields in array format."""
        register_ticket_tools_lazy(mock_mcp, mock_client_factory)
        tool = mock_mcp.tools["create_ticket"]
        
        mock_client.create_ticket = AsyncMock(return_value={
            "success": True,
            "data": {"data": {"id": 789, "name": "New Ticket"}}
        })
        
        # Test with array format for additional_fields
        additional_fields_json = '[{"id": 17078476, "name": "score", "value": "100", "value_name": null}]'
        result_json = await tool(
            name="New Ticket",
            ticket_stage_id=1,
            crm_lead_ids="[100, 101]",
            crm_company_id=200,
            priority="urgent",
            description="Critical issue",
            additional_fields=additional_fields_json
        )
        result = json.loads(result_json)
        
        assert result["success"] is True
        assert result["data"]["data"]["id"] == 789
        mock_client.create_ticket.assert_called_once()
        
        # Verify additional_fields are in correct format
        call_kwargs = mock_client.create_ticket.call_args.kwargs
        ticket_data = call_kwargs["ticket_data"]
        assert isinstance(ticket_data["additional_fields"], list)
        assert ticket_data["crm_lead_ids"] == [100, 101]
    
    @pytest.mark.asyncio
    async def test_get_ticket_details(self, mock_mcp, mock_client_factory, mock_client):
        """Test get_ticket retrieves ticket details."""
        register_ticket_tools_lazy(mock_mcp, mock_client_factory)
        tool = mock_mcp.tools["get_ticket"]
        
        mock_client.get_ticket = AsyncMock(return_value={
            "success": True,
            "data": {"data": {"id": 789, "name": "Ticket 789"}}
        })
        
        result_json = await tool(ticket_id=789)
        result = json.loads(result_json)
        
        assert result["success"] is True
        assert result["data"]["data"]["id"] == 789
        mock_client.get_ticket.assert_called_once_with(ticket_id=789, user_id=None)
    
    @pytest.mark.asyncio
    async def test_update_ticket_with_simplified_names(self, mock_mcp, mock_client_factory, mock_client):
        """Test update_ticket using simplified parameter names."""
        register_ticket_tools_lazy(mock_mcp, mock_client_factory)
        tool = mock_mcp.tools["update_ticket"]
        
        mock_client.update_ticket = AsyncMock(return_value={
            "success": True,
            "data": {"data": {"id": 789, "name": "Updated Ticket"}}
        })
        
        # Use simplified names: stage_id, contact_id, company_id, custom_fields
        result_json = await tool(
            ticket_id=789,
            name="Updated Ticket",
            stage_id=2,
            contact_id=150,
            company_id=250,
            priority="low",
            custom_fields='{"resolution": "solved"}'
        )
        result = json.loads(result_json)
        
        assert result["success"] is True
        mock_client.update_ticket.assert_called_once()
        
        # Verify simplified names are mapped to API names
        call_kwargs = mock_client.update_ticket.call_args.kwargs
        ticket_data = call_kwargs["ticket_data"]
        assert ticket_data["ticket_stage_id"] == 2  # Mapped from stage_id
        assert ticket_data["contact_id"] == 150     # Mapped from contact_id (as first element of array)
        assert ticket_data["company_id"] == 250     # Mapped from company_id
    
    @pytest.mark.asyncio
    async def test_get_ticket_pipelines(self, mock_mcp, mock_client_factory, mock_client):
        """Test get_ticket_pipelines retrieves available pipelines."""
        register_ticket_tools_lazy(mock_mcp, mock_client_factory)
        tool = mock_mcp.tools["get_ticket_pipelines"]
        
        mock_client.get_ticket_pipelines = AsyncMock(return_value={
            "success": True,
            "data": {"data": [
                {"id": 1, "name": "Support Pipeline", "stages": []}
            ]}
        })
        
        result_json = await tool()
        result = json.loads(result_json)
        
        assert result["success"] is True
        assert len(result["data"]["data"]) == 1
        mock_client.get_ticket_pipelines.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_required_fields_for_ticket(self, mock_mcp, mock_client_factory, mock_client):
        """Test get_required_fields_for_ticket retrieves field definitions."""
        register_ticket_tools_lazy(mock_mcp, mock_client_factory)
        tool = mock_mcp.tools["get_required_fields_for_ticket"]
        
        mock_client.get_ticket_template = AsyncMock(return_value={
            "success": True,
            "data": {"response": [
                {"id": 17078476, "name": "score", "type": "number", "required": False}
            ]}
        })
        
        result_json = await tool(pipeline_id=1)
        result = json.loads(result_json)
        
        assert result["success"] is True
        # Ticket tool returns required/optional fields split by standard/custom
        assert "optional_custom_fields" in result
        assert "required_custom_fields" in result
        assert isinstance(result["optional_custom_fields"], list)
        mock_client.get_ticket_template.assert_called_once()


class TestCustomFieldsIntegration:
    """Integration tests for custom fields across all modules."""
    
    @pytest.mark.asyncio
    async def test_deal_custom_fields_dict_format(self, mock_mcp, mock_client_factory, mock_client):
        """Test deals accept custom_fields as dict (key-value pairs)."""
        register_deal_tools_lazy(mock_mcp, mock_client_factory)
        tool = mock_mcp.tools["create_deal"]
        
        mock_client.create_deal = AsyncMock(return_value={
            "success": True,
            "data": {"data": {"id": 1}}
        })
        
        # Deals use dict format (key-value pairs)
        custom_fields_json = '{"industry": "tech", "size": "enterprise"}'
        result_json = await tool(
            name="Test Deal",
            crm_pipeline_id=1,
            crm_stage_id=1,
            custom_fields=custom_fields_json
        )
        result = json.loads(result_json)
        
        assert result["success"] is True
        call_kwargs = mock_client.create_deal.call_args.kwargs
        assert "custom_fields" in call_kwargs["deal_data"]
        # Should be converted to dict format
        assert isinstance(call_kwargs["deal_data"]["custom_fields"], dict)
    
    @pytest.mark.asyncio
    async def test_task_additional_fields_array_format(self, mock_mcp, mock_client_factory, mock_client):
        """Test tasks accept additional_fields as array."""
        register_task_tools_lazy(mock_mcp, mock_client_factory)
        tool = mock_mcp.tools["create_task"]
        
        mock_client.create_task = AsyncMock(return_value={
            "success": True,
            "data": {"data": {"id": 1}}
        })
        
        # Tasks use array format
        additional_fields_json = '[{"id": 123, "name": "field_1", "value": "value1"}]'
        result_json = await tool(
            name="Test Task",
            due_date="2025-12-31",
            additional_fields=additional_fields_json
        )
        result = json.loads(result_json)
        
        assert result["success"] is True
        call_kwargs = mock_client.create_task.call_args.kwargs
        assert "additional_fields" in call_kwargs["task_data"]
        # Should remain as array
        assert isinstance(call_kwargs["task_data"]["additional_fields"], list)
    
    @pytest.mark.asyncio
    async def test_ticket_additional_fields_array_format(self, mock_mcp, mock_client_factory, mock_client):
        """Test tickets accept additional_fields as array."""
        register_ticket_tools_lazy(mock_mcp, mock_client_factory)
        tool = mock_mcp.tools["create_ticket"]
        
        mock_client.create_ticket = AsyncMock(return_value={
            "success": True,
            "data": {"data": {"id": 1}}
        })
        
        # Tickets use array format with value_name
        additional_fields_json = '[{"id": 456, "name": "field_1", "value": "value1", "value_name": null}]'
        result_json = await tool(
            name="Test Ticket",
            ticket_stage_id=1,
            additional_fields=additional_fields_json
        )
        result = json.loads(result_json)
        
        assert result["success"] is True
        call_kwargs = mock_client.create_ticket.call_args.kwargs
        assert "additional_fields" in call_kwargs["ticket_data"]
        # Should remain as array
        assert isinstance(call_kwargs["ticket_data"]["additional_fields"], list)


class TestErrorHandling:
    """Test error handling for common scenarios."""
    
    @pytest.mark.asyncio
    async def test_invalid_json_in_custom_fields(self, mock_mcp, mock_client_factory, mock_client):
        """Test that invalid JSON in custom_fields returns proper error."""
        register_deal_tools_lazy(mock_mcp, mock_client_factory)
        tool = mock_mcp.tools["create_deal"]
        
        result_json = await tool(
            name="Test Deal",
            crm_pipeline_id=1,
            crm_stage_id=1,
            custom_fields="not valid json {{"
        )
        result = json.loads(result_json)
        
        assert result["success"] is False
        assert "Invalid JSON format" in result["error"]
    
    @pytest.mark.asyncio
    async def test_invalid_array_format_for_additional_fields(self, mock_mcp, mock_client_factory, mock_client):
        """Test that dict format for additional_fields returns error."""
        register_task_tools_lazy(mock_mcp, mock_client_factory)
        tool = mock_mcp.tools["create_task"]
        
        # Passing dict instead of array
        result_json = await tool(
            name="Test Task",
            due_date="2025-12-31",
            additional_fields='{"field": "value"}'
        )
        result = json.loads(result_json)
        
        assert result["success"] is False
        assert "must be a JSON array" in result["error"]
    
    @pytest.mark.asyncio
    async def test_missing_required_fields(self, mock_mcp, mock_client_factory, mock_client):
        """Test that missing required fields returns validation error."""
        register_deal_tools_lazy(mock_mcp, mock_client_factory)
        tool = mock_mcp.tools["update_deal"]
        
        # update_deal requires at least one field to update
        result_json = await tool(deal_id=123)
        result = json.loads(result_json)
        
        assert result["success"] is False
        assert "error" in result
