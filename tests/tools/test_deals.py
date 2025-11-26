import pytest
import json
import httpx
from unittest.mock import MagicMock, patch
from pydantic import ValidationError as PydanticValidationError
from qontak_mcp.tools.deals import register_deal_tools_lazy, register_deal_tools

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
async def test_list_deals_tool(mock_mcp, mock_client_factory, client):
    """Test list_deals tool."""
    register_deal_tools_lazy(mock_mcp, mock_client_factory)
    
    tool = mock_mcp.tools["list_deals"]
    
    # Mock client method
    with patch.object(client, 'list_deals', return_value={"success": True, "data": {"data": []}}):
        result_json = await tool(page=1, per_page=10)
        result = json.loads(result_json)
    
    assert result["success"] is True
    assert result["data"] == {"data": []}

@pytest.mark.asyncio
async def test_list_deals_tool_error(mock_mcp, mock_client_factory, client):
    """Test list_deals tool error handling."""
    register_deal_tools_lazy(mock_mcp, mock_client_factory)
    tool = mock_mcp.tools["list_deals"]
    
    # Force validation error by passing invalid type (if pydantic checks it)
    # Or mock client to raise exception
    
    with patch.object(client, "list_deals", side_effect=Exception("Boom")):
        result_json = await tool()
        result = json.loads(result_json)

        assert result["success"] is False
        assert "An unexpected error occurred" in result["error"]

@pytest.mark.asyncio
async def test_create_deal_tool(mock_mcp, mock_client_factory, client):
    """Test create_deal tool."""
    register_deal_tools_lazy(mock_mcp, mock_client_factory)
    tool = mock_mcp.tools["create_deal"]
    
    with patch.object(client, 'create_deal', return_value={"success": True, "data": {"data": {"id": 1}}}):
        result_json = await tool(name="New Deal", crm_pipeline_id=2, crm_stage_id=1, amount=100)
        result = json.loads(result_json)
    
    assert result["success"] is True
    assert result["data"]["data"]["id"] == 1

@pytest.mark.asyncio
async def test_get_deal_tool(mock_mcp, mock_client_factory, client):
    """Test get_deal tool."""
    register_deal_tools_lazy(mock_mcp, mock_client_factory)
    tool = mock_mcp.tools["get_deal"]
    
    with patch.object(client, 'get_deal', return_value={"success": True, "data": {"data": {"id": 1, "name": "Deal 1"}}}):
        result_json = await tool(deal_id=1)
        result = json.loads(result_json)
    
    assert result["success"] is True
    assert result["data"]["data"]["id"] == 1

@pytest.mark.asyncio
async def test_update_deal_tool(mock_mcp, mock_client_factory, client):
    """Test update_deal tool."""
    register_deal_tools_lazy(mock_mcp, mock_client_factory)
    tool = mock_mcp.tools["update_deal"]
    
    with patch.object(client, 'update_deal', return_value={"success": True, "data": {"data": {"id": 1, "name": "Updated Deal"}}}):
        result_json = await tool(deal_id=1, name="Updated Deal")
        result = json.loads(result_json)
    
    assert result["success"] is True
    assert result["data"]["data"]["name"] == "Updated Deal"

@pytest.mark.asyncio
async def test_get_deal_template_tool(mock_mcp, mock_client_factory, client):
    """Test get_deal_template tool."""
    register_deal_tools_lazy(mock_mcp, mock_client_factory)
    tool = mock_mcp.tools["get_deal_template"]
    
    with patch.object(client, 'get_deal_template', return_value={"success": True, "data": {"data": {"fields": []}}}):
        result_json = await tool()
        result = json.loads(result_json)
    
    assert result["success"] is True
    assert "fields" in result["data"]["data"]

@pytest.mark.asyncio
async def test_get_deal_timeline_tool(mock_mcp, mock_client_factory, client):
    """Test get_deal_timeline tool."""
    register_deal_tools_lazy(mock_mcp, mock_client_factory)
    tool = mock_mcp.tools["get_deal_timeline"]
    
    with patch.object(client, 'get_deal_timeline', return_value={"success": True, "data": {"data": [{"activity": "Created"}]}}):
        result_json = await tool(deal_id=1)
        result = json.loads(result_json)
    
    assert result["success"] is True
    assert len(result["data"]["data"]) > 0

@pytest.mark.asyncio
async def test_get_deal_stage_history_tool(mock_mcp, mock_client_factory, client):
    """Test get_deal_stage_history tool."""
    register_deal_tools_lazy(mock_mcp, mock_client_factory)
    tool = mock_mcp.tools["get_deal_stage_history"]
    
    with patch.object(client, 'get_deal_stage_history', return_value={"success": True, "data": {"data": [{"stage": "New"}]}}):
        result_json = await tool(deal_id=1)
        result = json.loads(result_json)
    
    assert result["success"] is True
    assert len(result["data"]["data"]) > 0


class TestDealToolsRegisterWrapper:
    """Test the register_deal_tools wrapper function."""
    
    @pytest.mark.asyncio
    async def test_register_deal_tools_wrapper(self, mock_mcp, client):
        """Test the register_deal_tools uses lazy registration internally."""
        register_deal_tools(mock_mcp, client)
        
        # Should have registered all tools
        assert "list_deals" in mock_mcp.tools
        assert "get_deal" in mock_mcp.tools
        assert "create_deal" in mock_mcp.tools
        assert "update_deal" in mock_mcp.tools
        assert "get_deal_template" in mock_mcp.tools


class TestDealListToolParameters:
    """Test list_deals with various parameter combinations."""
    
    @pytest.mark.asyncio
    async def test_list_deals_with_stage_filter(self, mock_mcp, mock_client_factory, client):
        """Test list_deals with stage_id filter."""
        register_deal_tools_lazy(mock_mcp, mock_client_factory)
        tool = mock_mcp.tools["list_deals"]
        
        with patch.object(client, 'list_deals', return_value={"success": True, "data": {"data": []}}) as mock:
            await tool(page=1, per_page=10, stage_id=5)
            mock.assert_called_once()
            call_kwargs = mock.call_args.kwargs
            assert call_kwargs['stage_id'] == 5
    
    @pytest.mark.asyncio
    async def test_list_deals_with_pipeline_filter(self, mock_mcp, mock_client_factory, client):
        """Test list_deals with pipeline_id filter."""
        register_deal_tools_lazy(mock_mcp, mock_client_factory)
        tool = mock_mcp.tools["list_deals"]
        
        with patch.object(client, 'list_deals', return_value={"success": True, "data": {"data": []}}) as mock:
            await tool(page=1, per_page=10, pipeline_id=3)
            mock.assert_called_once()
            call_kwargs = mock.call_args.kwargs
            assert call_kwargs['pipeline_id'] == 3
    
    @pytest.mark.asyncio
    async def test_list_deals_with_user_id(self, mock_mcp, mock_client_factory, client):
        """Test list_deals with user_id for multi-tenant."""
        register_deal_tools_lazy(mock_mcp, mock_client_factory)
        tool = mock_mcp.tools["list_deals"]
        
        with patch.object(client, 'list_deals', return_value={"success": True, "data": {"data": []}}) as mock:
            await tool(page=1, per_page=10, user_id="tenant_123")
            mock.assert_called_once()
            call_kwargs = mock.call_args.kwargs
            assert call_kwargs['user_id'] == "tenant_123"
    
    @pytest.mark.asyncio
    async def test_list_deals_pydantic_validation_error(self, mock_mcp, mock_client_factory, client):
        """Test list_deals handles PydanticValidationError."""
        register_deal_tools_lazy(mock_mcp, mock_client_factory)
        tool = mock_mcp.tools["list_deals"]
        
        # Pass invalid page number (negative)
        result_json = await tool(page=-1, per_page=10)
        result = json.loads(result_json)
        
        assert result["success"] is False
        assert "error" in result


class TestCreateDealToolParameters:
    """Test create_deal with various parameter combinations."""
    
    @pytest.mark.asyncio
    async def test_create_deal_with_all_optional_fields(self, mock_mcp, mock_client_factory, client):
        """Test create_deal with all optional fields."""
        register_deal_tools_lazy(mock_mcp, mock_client_factory)
        tool = mock_mcp.tools["create_deal"]
        
        with patch.object(client, 'create_deal', return_value={"success": True, "data": {"data": {"id": 1}}}) as mock:
            result_json = await tool(
                name="Test Deal",
                crm_pipeline_id=1,
                crm_stage_id=1,
                contact_id=100,
                company_id=200,
                amount=5000.50,
                expected_close_date="2024-12-31",
                description="Test description",
                custom_fields='{"field_1": "value1"}'
            )
            result = json.loads(result_json)
            
            assert result["success"] is True
            call_kwargs = mock.call_args.kwargs
            deal_data = call_kwargs['deal_data']
            assert deal_data['contact_id'] == 100
            assert deal_data['company_id'] == 200
            assert deal_data['amount'] == 5000.50
            assert deal_data['expected_close_date'] == "2024-12-31"
            assert deal_data['description'] == "Test description"
            assert deal_data['custom_fields'] == {"field_1": "value1"}
    
    @pytest.mark.asyncio
    async def test_create_deal_invalid_custom_fields_json(self, mock_mcp, mock_client_factory, client):
        """Test create_deal with invalid JSON in custom_fields."""
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
        assert "Invalid JSON format in custom_fields" in result["error"]
    
    @pytest.mark.asyncio
    async def test_create_deal_pydantic_validation_error(self, mock_mcp, mock_client_factory, client):
        """Test create_deal handles PydanticValidationError."""
        register_deal_tools_lazy(mock_mcp, mock_client_factory)
        tool = mock_mcp.tools["create_deal"]
        
        # Pass invalid stage_id (negative)
        result_json = await tool(name="Test", crm_pipeline_id=1, crm_stage_id=-1)
        result = json.loads(result_json)
        
        assert result["success"] is False
        assert "error" in result
    
    @pytest.mark.asyncio
    async def test_create_deal_client_exception(self, mock_mcp, mock_client_factory, client):
        """Test create_deal handles client exceptions."""
        register_deal_tools_lazy(mock_mcp, mock_client_factory)
        tool = mock_mcp.tools["create_deal"]
        
        with patch.object(client, 'create_deal', side_effect=Exception("Network error")):
            result_json = await tool(name="Test Deal", crm_pipeline_id=1, crm_stage_id=1)
            result = json.loads(result_json)
            
            assert result["success"] is False
            assert "error" in result


class TestUpdateDealToolParameters:
    """Test update_deal with various parameter combinations."""
    
    @pytest.mark.asyncio
    async def test_update_deal_with_all_optional_fields(self, mock_mcp, mock_client_factory, client):
        """Test update_deal with all optional fields."""
        register_deal_tools_lazy(mock_mcp, mock_client_factory)
        tool = mock_mcp.tools["update_deal"]
        
        with patch.object(client, 'update_deal', return_value={"success": True, "data": {"data": {"id": 1}}}) as mock:
            result_json = await tool(
                deal_id=1,
                name="Updated Deal",
                crm_stage_id=2,
                contact_id=100,
                company_id=200,
                amount=10000.00,
                expected_close_date="2025-01-15",
                description="Updated description",
                custom_fields='{"field_2": "value2"}'
            )
            result = json.loads(result_json)
            
            assert result["success"] is True
            call_kwargs = mock.call_args.kwargs
            deal_data = call_kwargs['deal_data']
            assert deal_data['name'] == "Updated Deal"
            assert deal_data['crm_stage_id'] == 2
            assert deal_data['contact_id'] == 100
            assert deal_data['company_id'] == 200
            assert deal_data['amount'] == 10000.00
            assert deal_data['custom_fields'] == {"field_2": "value2"}
    
    @pytest.mark.asyncio
    async def test_update_deal_invalid_custom_fields_json(self, mock_mcp, mock_client_factory, client):
        """Test update_deal with invalid JSON in custom_fields."""
        register_deal_tools_lazy(mock_mcp, mock_client_factory)
        tool = mock_mcp.tools["update_deal"]
        
        result_json = await tool(
            deal_id=1,
            custom_fields="invalid json here"
        )
        result = json.loads(result_json)
        
        assert result["success"] is False
        assert "Invalid JSON format in custom_fields" in result["error"]
    
    @pytest.mark.asyncio
    async def test_update_deal_pydantic_validation_error(self, mock_mcp, mock_client_factory, client):
        """Test update_deal handles PydanticValidationError."""
        register_deal_tools_lazy(mock_mcp, mock_client_factory)
        tool = mock_mcp.tools["update_deal"]
        
        # Pass invalid deal_id (negative)
        result_json = await tool(deal_id=-1, name="Updated")
        result = json.loads(result_json)
        
        assert result["success"] is False
        assert "error" in result
    
    @pytest.mark.asyncio
    async def test_update_deal_client_exception(self, mock_mcp, mock_client_factory, client):
        """Test update_deal handles client exceptions."""
        register_deal_tools_lazy(mock_mcp, mock_client_factory)
        tool = mock_mcp.tools["update_deal"]
        
        with patch.object(client, 'update_deal', side_effect=Exception("Timeout")):
            result_json = await tool(deal_id=1, name="Test")
            result = json.loads(result_json)
            
            assert result["success"] is False
            assert "error" in result


class TestGetDealToolParameters:
    """Test get_deal with various parameter combinations."""
    
    @pytest.mark.asyncio
    async def test_get_deal_with_user_id(self, mock_mcp, mock_client_factory, client):
        """Test get_deal with user_id for multi-tenant."""
        register_deal_tools_lazy(mock_mcp, mock_client_factory)
        tool = mock_mcp.tools["get_deal"]
        
        with patch.object(client, 'get_deal', return_value={"success": True, "data": {"data": {"id": 1}}}) as mock:
            await tool(deal_id=1, user_id="tenant_456")
            call_kwargs = mock.call_args.kwargs
            assert call_kwargs['user_id'] == "tenant_456"
    
    @pytest.mark.asyncio
    async def test_get_deal_pydantic_validation_error(self, mock_mcp, mock_client_factory, client):
        """Test get_deal handles PydanticValidationError."""
        register_deal_tools_lazy(mock_mcp, mock_client_factory)
        tool = mock_mcp.tools["get_deal"]
        
        # Pass invalid deal_id (negative)
        result_json = await tool(deal_id=-1)
        result = json.loads(result_json)
        
        assert result["success"] is False
        assert "error" in result
    
    @pytest.mark.asyncio
    async def test_get_deal_client_exception(self, mock_mcp, mock_client_factory, client):
        """Test get_deal handles client exceptions."""
        register_deal_tools_lazy(mock_mcp, mock_client_factory)
        tool = mock_mcp.tools["get_deal"]
        
        with patch.object(client, 'get_deal', side_effect=Exception("Not found")):
            result_json = await tool(deal_id=1)
            result = json.loads(result_json)
            
            assert result["success"] is False
            assert "error" in result


class TestGetDealTemplateToolParameters:
    """Test get_deal_template with various parameters."""
    
    @pytest.mark.asyncio
    async def test_get_deal_template_with_user_id(self, mock_mcp, mock_client_factory, client):
        """Test get_deal_template with user_id for multi-tenant."""
        register_deal_tools_lazy(mock_mcp, mock_client_factory)
        tool = mock_mcp.tools["get_deal_template"]
        
        with patch.object(client, 'get_deal_template', return_value={"success": True, "data": {"data": {"fields": []}}}) as mock:
            await tool(user_id="tenant_789")
            call_kwargs = mock.call_args.kwargs
            assert call_kwargs['user_id'] == "tenant_789"
    
    @pytest.mark.asyncio
    async def test_get_deal_template_client_exception(self, mock_mcp, mock_client_factory, client):
        """Test get_deal_template handles client exceptions."""
        register_deal_tools_lazy(mock_mcp, mock_client_factory)
        tool = mock_mcp.tools["get_deal_template"]
        
        with patch.object(client, 'get_deal_template', side_effect=Exception("Template error")):
            result_json = await tool()
            result = json.loads(result_json)
            
            assert result["success"] is False
            assert "error" in result


class TestGetDealTimelineToolParameters:
    """Test get_deal_timeline with various parameters."""
    
    @pytest.mark.asyncio
    async def test_get_deal_timeline_with_pagination(self, mock_mcp, mock_client_factory, client):
        """Test get_deal_timeline with pagination parameters."""
        register_deal_tools_lazy(mock_mcp, mock_client_factory)
        tool = mock_mcp.tools["get_deal_timeline"]
        
        with patch.object(client, 'get_deal_timeline', return_value={"success": True, "data": {"data": []}}) as mock:
            await tool(deal_id=1, page=2, per_page=50, user_id="tenant_abc")
            call_kwargs = mock.call_args.kwargs
            assert call_kwargs['page'] == 2
            assert call_kwargs['per_page'] == 50
            assert call_kwargs['user_id'] == "tenant_abc"
    
    @pytest.mark.asyncio
    async def test_get_deal_timeline_pydantic_validation_error(self, mock_mcp, mock_client_factory, client):
        """Test get_deal_timeline handles PydanticValidationError."""
        register_deal_tools_lazy(mock_mcp, mock_client_factory)
        tool = mock_mcp.tools["get_deal_timeline"]
        
        # Pass invalid deal_id (negative)
        result_json = await tool(deal_id=-1)
        result = json.loads(result_json)
        
        assert result["success"] is False
        assert "error" in result
    
    @pytest.mark.asyncio
    async def test_get_deal_timeline_client_exception(self, mock_mcp, mock_client_factory, client):
        """Test get_deal_timeline handles client exceptions."""
        register_deal_tools_lazy(mock_mcp, mock_client_factory)
        tool = mock_mcp.tools["get_deal_timeline"]
        
        with patch.object(client, 'get_deal_timeline', side_effect=Exception("Timeline error")):
            result_json = await tool(deal_id=1)
            result = json.loads(result_json)
            
            assert result["success"] is False
            assert "error" in result


class TestGetDealStageHistoryToolParameters:
    """Test get_deal_stage_history with various parameters."""
    
    @pytest.mark.asyncio
    async def test_get_deal_stage_history_with_user_id(self, mock_mcp, mock_client_factory, client):
        """Test get_deal_stage_history with user_id for multi-tenant."""
        register_deal_tools_lazy(mock_mcp, mock_client_factory)
        tool = mock_mcp.tools["get_deal_stage_history"]
        
        with patch.object(client, 'get_deal_stage_history', return_value={"success": True, "data": {"data": []}}) as mock:
            await tool(deal_id=1, user_id="tenant_xyz")
            call_kwargs = mock.call_args.kwargs
            assert call_kwargs['user_id'] == "tenant_xyz"
    
    @pytest.mark.asyncio
    async def test_get_deal_stage_history_pydantic_validation_error(self, mock_mcp, mock_client_factory, client):
        """Test get_deal_stage_history handles PydanticValidationError."""
        register_deal_tools_lazy(mock_mcp, mock_client_factory)
        tool = mock_mcp.tools["get_deal_stage_history"]
        
        # Pass invalid deal_id (negative)
        result_json = await tool(deal_id=-1)
        result = json.loads(result_json)
        
        assert result["success"] is False
        assert "error" in result
    
    @pytest.mark.asyncio
    async def test_get_deal_stage_history_client_exception(self, mock_mcp, mock_client_factory, client):
        """Test get_deal_stage_history handles client exceptions."""
        register_deal_tools_lazy(mock_mcp, mock_client_factory)
        tool = mock_mcp.tools["get_deal_stage_history"]
        
        with patch.object(client, 'get_deal_stage_history', side_effect=Exception("History error")):
            result_json = await tool(deal_id=1)
            result = json.loads(result_json)
            
            assert result["success"] is False
            assert "error" in result