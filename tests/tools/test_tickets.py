import pytest
import json
import httpx
from unittest.mock import MagicMock, patch
from qontak_mcp.tools.tickets import register_ticket_tools_lazy, register_ticket_tools

class MockFastMCP:
    def __init__(self):
        self.tools = {}

    def tool(self, name=None):
        def decorator(func):
            tool_name = name or func.__name__
            self.tools[tool_name] = func
            return func
        return decorator

@pytest.fixture
def mock_mcp():
    return MockFastMCP()

@pytest.fixture
def mock_client_factory(client):
    return lambda: client

@pytest.mark.asyncio
async def test_list_tickets_tool(mock_mcp, mock_client_factory, client):
    """Test list_tickets tool."""
    register_ticket_tools_lazy(mock_mcp, mock_client_factory)
    
    tool = mock_mcp.tools["list_tickets"]
    
    with patch.object(client, 'list_tickets', return_value={"success": True, "data": {"data": []}}):
        result_json = await tool(page=1, per_page=10)
        result = json.loads(result_json)
    
    assert result["success"] is True
    assert result["data"] == {"data": []}

@pytest.mark.asyncio
async def test_create_ticket_tool(mock_mcp, mock_client_factory, client):
    """Test create_ticket tool."""
    register_ticket_tools_lazy(mock_mcp, mock_client_factory)
    tool = mock_mcp.tools["create_ticket"]
    
    with patch.object(client, 'create_ticket', return_value={"success": True, "data": {"data": {"id": 1}}}):
        result_json = await tool(name="New Ticket", ticket_stage_id=1, priority="high")
        result = json.loads(result_json)
    
    assert result["success"] is True
    assert result["data"]["data"]["id"] == 1

@pytest.mark.asyncio
async def test_get_ticket_tool(mock_mcp, mock_client_factory, client):
    """Test get_ticket tool."""
    register_ticket_tools_lazy(mock_mcp, mock_client_factory)
    tool = mock_mcp.tools["get_ticket"]
    
    with patch.object(client, 'get_ticket', return_value={"success": True, "data": {"data": {"id": 1, "subject": "Ticket 1"}}}):
        result_json = await tool(ticket_id=1)
        result = json.loads(result_json)
    
    assert result["success"] is True
    assert result["data"]["data"]["id"] == 1

@pytest.mark.asyncio
async def test_update_ticket_tool(mock_mcp, mock_client_factory, client):
    """Test update_ticket tool."""
    register_ticket_tools_lazy(mock_mcp, mock_client_factory)
    tool = mock_mcp.tools["update_ticket"]
    
    with patch.object(client, 'update_ticket', return_value={"success": True, "data": {"data": {"id": 1, "subject": "Updated Ticket"}}}):
        result_json = await tool(ticket_id=1, name="Updated Ticket")
        result = json.loads(result_json)
    
    assert result["success"] is True
    assert result["data"]["data"]["subject"] == "Updated Ticket"

@pytest.mark.asyncio
async def test_get_ticket_template_tool(mock_mcp, mock_client_factory, client):
    """Test get_ticket_template tool."""
    register_ticket_tools_lazy(mock_mcp, mock_client_factory)
    tool = mock_mcp.tools["get_ticket_template"]
    
    with patch.object(client, 'get_ticket_template', return_value={"success": True, "data": {"data": {"fields": []}}}):
        result_json = await tool()
        result = json.loads(result_json)
    
    assert result["success"] is True
    assert "fields" in result["data"]["data"]

@pytest.mark.asyncio
async def test_get_ticket_pipelines_tool(mock_mcp, mock_client_factory, client):
    """Test get_ticket_pipelines tool."""
    register_ticket_tools_lazy(mock_mcp, mock_client_factory)
    tool = mock_mcp.tools["get_ticket_pipelines"]
    
    with patch.object(client, 'get_ticket_pipelines', return_value={"success": True, "data": {"data": [{"id": 1, "name": "Pipeline 1"}]}}):
        result_json = await tool()
        result = json.loads(result_json)
    
    assert result["success"] is True
    assert len(result["data"]["data"]) > 0


class TestTicketToolsRegisterWrapper:
    """Test the register_ticket_tools wrapper function."""
    
    @pytest.mark.asyncio
    async def test_register_ticket_tools_wrapper(self, mock_mcp, client):
        """Test register_ticket_tools uses lazy registration internally."""
        register_ticket_tools(mock_mcp, client)
        
        # Should have registered all tools
        assert "list_tickets" in mock_mcp.tools
        assert "get_ticket" in mock_mcp.tools
        assert "create_ticket" in mock_mcp.tools
        assert "update_ticket" in mock_mcp.tools


class TestListTicketsToolParameters:
    """Test list_tickets with various parameter combinations."""
    
    @pytest.mark.asyncio
    async def test_list_tickets_with_all_filters(self, mock_mcp, mock_client_factory, client):
        """Test list_tickets with pipeline and user filters."""
        register_ticket_tools_lazy(mock_mcp, mock_client_factory)
        tool = mock_mcp.tools["list_tickets"]
        
        with patch.object(client, 'list_tickets', return_value={"success": True, "data": {"data": []}}) as mock:
            await tool(page=1, per_page=10, pipeline_id=5, user_id="tenant_123")
            mock.assert_called_once()
            call_kwargs = mock.call_args.kwargs
            assert call_kwargs['pipeline_id'] == 5
            assert call_kwargs['user_id'] == "tenant_123"
    
    @pytest.mark.asyncio
    async def test_list_tickets_with_pipeline_filter(self, mock_mcp, mock_client_factory, client):
        """Test list_tickets with pipeline_id filter."""
        register_ticket_tools_lazy(mock_mcp, mock_client_factory)
        tool = mock_mcp.tools["list_tickets"]
        
        with patch.object(client, 'list_tickets', return_value={"success": True, "data": {"data": []}}) as mock:
            await tool(page=1, per_page=10, pipeline_id=5)
            mock.assert_called_once()
            call_kwargs = mock.call_args.kwargs
            assert call_kwargs['pipeline_id'] == 5
    
    @pytest.mark.asyncio
    async def test_list_tickets_with_user_id(self, mock_mcp, mock_client_factory, client):
        """Test list_tickets with user_id for multi-tenant."""
        register_ticket_tools_lazy(mock_mcp, mock_client_factory)
        tool = mock_mcp.tools["list_tickets"]
        
        with patch.object(client, 'list_tickets', return_value={"success": True, "data": {"data": []}}) as mock:
            await tool(page=1, per_page=10, user_id="tenant_123")
            mock.assert_called_once()
            call_kwargs = mock.call_args.kwargs
            assert call_kwargs['user_id'] == "tenant_123"
    
    @pytest.mark.asyncio
    async def test_list_tickets_pydantic_validation_error(self, mock_mcp, mock_client_factory, client):
        """Test list_tickets handles PydanticValidationError."""
        register_ticket_tools_lazy(mock_mcp, mock_client_factory)
        tool = mock_mcp.tools["list_tickets"]
        
        # Pass invalid page number (negative)
        result_json = await tool(page=-1, per_page=10)
        result = json.loads(result_json)
        
        assert result["success"] is False
        assert "error" in result
    
    @pytest.mark.asyncio
    async def test_list_tickets_client_exception(self, mock_mcp, mock_client_factory, client):
        """Test list_tickets handles client exceptions."""
        register_ticket_tools_lazy(mock_mcp, mock_client_factory)
        tool = mock_mcp.tools["list_tickets"]
        
        with patch.object(client, 'list_tickets', side_effect=Exception("Network error")):
            result_json = await tool(page=1, per_page=10)
            result = json.loads(result_json)
            
            assert result["success"] is False
            assert "error" in result


class TestCreateTicketToolParameters:
    """Test create_ticket with various parameter combinations."""
    
    @pytest.mark.asyncio
    async def test_create_ticket_with_all_optional_fields(self, mock_mcp, mock_client_factory, client):
        """Test create_ticket with all optional fields."""
        register_ticket_tools_lazy(mock_mcp, mock_client_factory)
        tool = mock_mcp.tools["create_ticket"]
        
        with patch.object(client, 'create_ticket', return_value={"success": True, "data": {"data": {"id": 1}}}) as mock:
            result_json = await tool(
                name="Test Ticket",
                ticket_stage_id=1,
                priority="high",
                crm_lead_ids="[100]",
                crm_company_id=200,
                description="Test description",
                additional_fields='[{"id": 456, "name": "field_1", "value": "value1", "value_name": null}]'
            )
            result = json.loads(result_json)
            
            assert result["success"] is True
            call_kwargs = mock.call_args.kwargs
            ticket_data = call_kwargs['ticket_data']
            assert ticket_data['priority'] == "high"
            assert ticket_data['crm_lead_ids'] == [100]
            assert ticket_data['crm_company_id'] == 200
            assert ticket_data['description'] == "Test description"
            assert ticket_data['additional_fields'] == [{"id": 456, "name": "field_1", "value": "value1", "value_name": None}]
    
    @pytest.mark.asyncio
    async def test_create_ticket_invalid_custom_fields_json(self, mock_mcp, mock_client_factory, client):
        """Test create_ticket with invalid JSON in custom_fields."""
        register_ticket_tools_lazy(mock_mcp, mock_client_factory)
        tool = mock_mcp.tools["create_ticket"]
        
        result_json = await tool(
            name="Test Ticket",
            ticket_stage_id=1,
            priority="high",
            additional_fields="not valid json {{"
        )
        result = json.loads(result_json)
        
        assert result["success"] is False
        assert "Invalid JSON format" in result["error"]
    
    @pytest.mark.asyncio
    async def test_create_ticket_pydantic_validation_error(self, mock_mcp, mock_client_factory, client):
        """Test create_ticket handles PydanticValidationError."""
        register_ticket_tools_lazy(mock_mcp, mock_client_factory)
        tool = mock_mcp.tools["create_ticket"]
        
        # Pass invalid stage_id (negative)
        result_json = await tool(name="Test", ticket_stage_id=-1, priority="high")
        result = json.loads(result_json)
        
        assert result["success"] is False
        assert "error" in result
    
    @pytest.mark.asyncio
    async def test_create_ticket_client_exception(self, mock_mcp, mock_client_factory, client):
        """Test create_ticket handles client exceptions."""
        register_ticket_tools_lazy(mock_mcp, mock_client_factory)
        tool = mock_mcp.tools["create_ticket"]
        
        with patch.object(client, 'create_ticket', side_effect=Exception("Network error")):
            result_json = await tool(name="Test Ticket", ticket_stage_id=1, priority="high")
            result = json.loads(result_json)
            
            assert result["success"] is False
            assert "error" in result


class TestUpdateTicketToolParameters:
    """Test update_ticket with various parameter combinations."""
    
    @pytest.mark.asyncio
    async def test_update_ticket_with_all_optional_fields(self, mock_mcp, mock_client_factory, client):
        """Test update_ticket with all optional fields."""
        register_ticket_tools_lazy(mock_mcp, mock_client_factory)
        tool = mock_mcp.tools["update_ticket"]
        
        with patch.object(client, 'update_ticket', return_value={"success": True, "data": {"data": {"id": 1}}}) as mock:
            result_json = await tool(
                ticket_id=1,
                name="Updated Ticket",
                stage_id=2,
                priority="low",
                contact_id=100,
                company_id=200,
                description="Updated description",
                custom_fields='{"field_2": "value2"}'
            )
            result = json.loads(result_json)
            
            assert result["success"] is True
            call_kwargs = mock.call_args.kwargs
            ticket_data = call_kwargs['ticket_data']
            assert ticket_data['name'] == "Updated Ticket"
            assert ticket_data['ticket_stage_id'] == 2
            assert ticket_data['priority'] == "low"
            assert ticket_data['contact_id'] == 100
            assert ticket_data['company_id'] == 200
            assert ticket_data['description'] == "Updated description"
            assert ticket_data['custom_fields'] == {"field_2": "value2"}
    
    @pytest.mark.asyncio
    async def test_update_ticket_invalid_custom_fields_json(self, mock_mcp, mock_client_factory, client):
        """Test update_ticket with invalid JSON in custom_fields."""
        register_ticket_tools_lazy(mock_mcp, mock_client_factory)
        tool = mock_mcp.tools["update_ticket"]
        
        result_json = await tool(
            ticket_id=1,
            custom_fields="invalid json here"
        )
        result = json.loads(result_json)
        
        assert result["success"] is False
        assert "Invalid JSON format" in result["error"]
    
    @pytest.mark.asyncio
    async def test_update_ticket_pydantic_validation_error(self, mock_mcp, mock_client_factory, client):
        """Test update_ticket handles PydanticValidationError."""
        register_ticket_tools_lazy(mock_mcp, mock_client_factory)
        tool = mock_mcp.tools["update_ticket"]
        
        # Pass invalid ticket_id (negative)
        result_json = await tool(ticket_id=-1, name="Updated")
        result = json.loads(result_json)
        
        assert result["success"] is False
        assert "error" in result
    
    @pytest.mark.asyncio
    async def test_update_ticket_client_exception(self, mock_mcp, mock_client_factory, client):
        """Test update_ticket handles client exceptions."""
        register_ticket_tools_lazy(mock_mcp, mock_client_factory)
        tool = mock_mcp.tools["update_ticket"]
        
        with patch.object(client, 'update_ticket', side_effect=Exception("Timeout")):
            result_json = await tool(ticket_id=1, name="Test")
            result = json.loads(result_json)
            
            assert result["success"] is False
            assert "error" in result


class TestGetTicketToolParameters:
    """Test get_ticket with various parameter combinations."""
    
    @pytest.mark.asyncio
    async def test_get_ticket_with_user_id(self, mock_mcp, mock_client_factory, client):
        """Test get_ticket with user_id for multi-tenant."""
        register_ticket_tools_lazy(mock_mcp, mock_client_factory)
        tool = mock_mcp.tools["get_ticket"]
        
        with patch.object(client, 'get_ticket', return_value={"success": True, "data": {"data": {"id": 1}}}) as mock:
            await tool(ticket_id=1, user_id="tenant_456")
            call_kwargs = mock.call_args.kwargs
            assert call_kwargs['user_id'] == "tenant_456"
    
    @pytest.mark.asyncio
    async def test_get_ticket_pydantic_validation_error(self, mock_mcp, mock_client_factory, client):
        """Test get_ticket handles PydanticValidationError."""
        register_ticket_tools_lazy(mock_mcp, mock_client_factory)
        tool = mock_mcp.tools["get_ticket"]
        
        # Pass invalid ticket_id (negative)
        result_json = await tool(ticket_id=-1)
        result = json.loads(result_json)
        
        assert result["success"] is False
        assert "error" in result
    
    @pytest.mark.asyncio
    async def test_get_ticket_client_exception(self, mock_mcp, mock_client_factory, client):
        """Test get_ticket handles client exceptions."""
        register_ticket_tools_lazy(mock_mcp, mock_client_factory)
        tool = mock_mcp.tools["get_ticket"]
        
        with patch.object(client, 'get_ticket', side_effect=Exception("Not found")):
            result_json = await tool(ticket_id=1)
            result = json.loads(result_json)
            
            assert result["success"] is False
            assert "error" in result


class TestGetTicketTemplateToolParameters:
    """Test get_ticket_template with various parameters."""
    
    @pytest.mark.asyncio
    async def test_get_ticket_template_with_user_id(self, mock_mcp, mock_client_factory, client):
        """Test get_ticket_template with user_id for multi-tenant."""
        register_ticket_tools_lazy(mock_mcp, mock_client_factory)
        tool = mock_mcp.tools["get_ticket_template"]
        
        with patch.object(client, 'get_ticket_template', return_value={"success": True, "data": {"data": {"fields": []}}}) as mock:
            await tool(user_id="tenant_789")
            call_kwargs = mock.call_args.kwargs
            assert call_kwargs['user_id'] == "tenant_789"
    
    @pytest.mark.asyncio
    async def test_get_ticket_template_client_exception(self, mock_mcp, mock_client_factory, client):
        """Test get_ticket_template handles client exceptions."""
        register_ticket_tools_lazy(mock_mcp, mock_client_factory)
        tool = mock_mcp.tools["get_ticket_template"]
        
        with patch.object(client, 'get_ticket_template', side_effect=Exception("Template error")):
            result_json = await tool()
            result = json.loads(result_json)
            
            assert result["success"] is False
            assert "error" in result


class TestGetTicketPipelinesToolParameters:
    """Test get_ticket_pipelines with various parameters."""
    
    @pytest.mark.asyncio
    async def test_get_ticket_pipelines_with_user_id(self, mock_mcp, mock_client_factory, client):
        """Test get_ticket_pipelines with user_id for multi-tenant."""
        register_ticket_tools_lazy(mock_mcp, mock_client_factory)
        tool = mock_mcp.tools["get_ticket_pipelines"]
        
        with patch.object(client, 'get_ticket_pipelines', return_value={"success": True, "data": {"data": []}}) as mock:
            await tool(user_id="tenant_abc")
            call_kwargs = mock.call_args.kwargs
            assert call_kwargs['user_id'] == "tenant_abc"
    
    @pytest.mark.asyncio
    async def test_get_ticket_pipelines_with_pagination(self, mock_mcp, mock_client_factory, client):
        """Test get_ticket_pipelines with pagination parameters."""
        register_ticket_tools_lazy(mock_mcp, mock_client_factory)
        tool = mock_mcp.tools["get_ticket_pipelines"]
        
        with patch.object(client, 'get_ticket_pipelines', return_value={"success": True, "data": {"data": []}}) as mock:
            await tool(page=2, per_page=50, user_id="tenant_abc")
            call_kwargs = mock.call_args.kwargs
            assert call_kwargs['page'] == 2
            assert call_kwargs['per_page'] == 50
            assert call_kwargs['user_id'] == "tenant_abc"
    
    @pytest.mark.asyncio
    async def test_get_ticket_pipelines_pydantic_validation_error(self, mock_mcp, mock_client_factory, client):
        """Test get_ticket_pipelines handles PydanticValidationError."""
        register_ticket_tools_lazy(mock_mcp, mock_client_factory)
        tool = mock_mcp.tools["get_ticket_pipelines"]
        
        # Pass invalid page (negative)
        result_json = await tool(page=-1)
        result = json.loads(result_json)
        
        assert result["success"] is False
        assert "error" in result
    
    @pytest.mark.asyncio
    async def test_get_ticket_pipelines_client_exception(self, mock_mcp, mock_client_factory, client):
        """Test get_ticket_pipelines handles client exceptions."""
        register_ticket_tools_lazy(mock_mcp, mock_client_factory)
        tool = mock_mcp.tools["get_ticket_pipelines"]
        
        with patch.object(client, 'get_ticket_pipelines', side_effect=Exception("Pipeline error")):
            result_json = await tool()
            result = json.loads(result_json)
            
            assert result["success"] is False
            assert "error" in result