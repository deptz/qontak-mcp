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
    async def test_create_deal_with_size_and_currency(self, mock_mcp, mock_client_factory, client):
        """Test create_deal with size and currency fields."""
        register_deal_tools_lazy(mock_mcp, mock_client_factory)
        tool = mock_mcp.tools["create_deal"]
        
        with patch.object(client, 'create_deal', return_value={"success": True, "data": {"data": {"id": 1}}}) as mock:
            result_json = await tool(
                name="Big Deal",
                crm_pipeline_id=1,
                crm_stage_id=1,
                size=100000.50,
                currency="USD"
            )
            result = json.loads(result_json)
            
            assert result["success"] is True
            call_kwargs = mock.call_args.kwargs
            deal_data = call_kwargs['deal_data']
            assert deal_data['size'] == 100000.50
            assert deal_data['currency'] == "USD"
    
    @pytest.mark.asyncio
    async def test_create_deal_with_additional_fields_array(self, mock_mcp, mock_client_factory, client):
        """Test create_deal with additional_fields as JSON array."""
        register_deal_tools_lazy(mock_mcp, mock_client_factory)
        tool = mock_mcp.tools["create_deal"]
        
        additional_fields_json = '[{"id": 123, "name": "industry", "value": "Technology"}]'
        
        with patch.object(client, 'create_deal', return_value={"success": True, "data": {"data": {"id": 1}}}) as mock:
            result_json = await tool(
                name="Deal with Custom Fields",
                crm_pipeline_id=1,
                crm_stage_id=1,
                additional_fields=additional_fields_json
            )
            result = json.loads(result_json)
            
            assert result["success"] is True
            call_kwargs = mock.call_args.kwargs
            deal_data = call_kwargs['deal_data']
            assert 'additional_fields' in deal_data
            assert len(deal_data['additional_fields']) == 1
            assert deal_data['additional_fields'][0]['name'] == "industry"
    
    @pytest.mark.asyncio
    async def test_create_deal_with_invalid_additional_fields_not_array(self, mock_mcp, mock_client_factory, client):
        """Test create_deal with additional_fields that is not an array."""
        register_deal_tools_lazy(mock_mcp, mock_client_factory)
        tool = mock_mcp.tools["create_deal"]
        
        # Pass object instead of array
        result_json = await tool(
            name="Test Deal",
            crm_pipeline_id=1,
            crm_stage_id=1,
            additional_fields='{"key": "value"}'
        )
        result = json.loads(result_json)
        
        assert result["success"] is False
        assert "must be a JSON array" in result["error"]
    
    @pytest.mark.asyncio
    async def test_create_deal_with_invalid_additional_fields_json(self, mock_mcp, mock_client_factory, client):
        """Test create_deal with invalid JSON in additional_fields."""
        register_deal_tools_lazy(mock_mcp, mock_client_factory)
        tool = mock_mcp.tools["create_deal"]
        
        result_json = await tool(
            name="Test Deal",
            crm_pipeline_id=1,
            crm_stage_id=1,
            additional_fields="not valid json ["
        )
        result = json.loads(result_json)
        
        assert result["success"] is False
        assert "Invalid JSON format in additional_fields" in result["error"]
    
    @pytest.mark.asyncio
    async def test_create_deal_with_empty_additional_fields(self, mock_mcp, mock_client_factory, client):
        """Test create_deal without additional_fields defaults to empty array."""
        register_deal_tools_lazy(mock_mcp, mock_client_factory)
        tool = mock_mcp.tools["create_deal"]
        
        with patch.object(client, 'create_deal', return_value={"success": True, "data": {"data": {"id": 1}}}) as mock:
            result_json = await tool(
                name="Simple Deal",
                crm_pipeline_id=1,
                crm_stage_id=1
            )
            result = json.loads(result_json)
            
            assert result["success"] is True
            call_kwargs = mock.call_args.kwargs
            deal_data = call_kwargs['deal_data']
            assert deal_data['additional_fields'] == []
    
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
    async def test_update_deal_with_pipeline_id(self, mock_mcp, mock_client_factory, client):
        """Test update_deal with crm_pipeline_id."""
        register_deal_tools_lazy(mock_mcp, mock_client_factory)
        tool = mock_mcp.tools["update_deal"]
        
        with patch.object(client, 'update_deal', return_value={"success": True, "data": {"data": {"id": 1}}}) as mock:
            result_json = await tool(
                deal_id=1,
                crm_pipeline_id=3,
                crm_stage_id=5
            )
            result = json.loads(result_json)
            
            assert result["success"] is True
            call_kwargs = mock.call_args.kwargs
            deal_data = call_kwargs['deal_data']
            assert deal_data['crm_pipeline_id'] == 3
            assert deal_data['crm_stage_id'] == 5
    
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


@pytest.mark.asyncio
async def test_get_deal_chat_history(mock_mcp, mock_client_factory, client):
    """Test get_deal_chat_history tool."""
    register_deal_tools_lazy(mock_mcp, mock_client_factory)
    tool = mock_mcp.tools["get_deal_chat_history"]
    
    with patch.object(client, 'get_deal_chat_history', return_value={"success": True, "data": {"response": []}}):
        result_json = await tool(deal_id=123)
        result = json.loads(result_json)
    
    assert result["success"] is True

@pytest.mark.asyncio
async def test_get_deal_real_creator(mock_mcp, mock_client_factory, client):
    """Test get_deal_real_creator tool."""
    register_deal_tools_lazy(mock_mcp, mock_client_factory)
    tool = mock_mcp.tools["get_deal_real_creator"]
    
    with patch.object(client, 'get_deal_real_creator', return_value={"success": True, "data": {"user_id": 1, "name": "Test Creator"}}):
        result_json = await tool(deal_id=123)
        result = json.loads(result_json)
    
    assert result["success"] is True

@pytest.mark.asyncio
async def test_get_deal_full_field(mock_mcp, mock_client_factory, client):
    """Test get_deal_full_field tool."""
    register_deal_tools_lazy(mock_mcp, mock_client_factory)
    tool = mock_mcp.tools["get_deal_full_field"]
    
    with patch.object(client, 'get_deal_full_field', return_value={"success": True, "data": {"deal_id": 123, "fields": {}}}):
        result_json = await tool(deal_id=123)
        result = json.loads(result_json)
    
    assert result["success"] is True

@pytest.mark.asyncio
async def test_get_deal_permissions(mock_mcp, mock_client_factory, client):
    """Test get_deal_permissions tool."""
    register_deal_tools_lazy(mock_mcp, mock_client_factory)
    tool = mock_mcp.tools["get_deal_permissions"]
    
    with patch.object(client, 'get_deal_permissions', return_value={"success": True, "data": {"permissions": []}}):
        result_json = await tool(deal_id=123)
        result = json.loads(result_json)
    
    assert result["success"] is True

@pytest.mark.asyncio
async def test_update_deal_owner(mock_mcp, mock_client_factory, client):
    """Test update_deal_owner tool."""
    register_deal_tools_lazy(mock_mcp, mock_client_factory)
    tool = mock_mcp.tools["update_deal_owner"]
    
    with patch.object(client, 'update_deal_owner', return_value={"success": True, "data": {"deal_id": 123, "creator_id": 456}}):
        result_json = await tool(deal_id=123, creator_id=456)
        result = json.loads(result_json)
    
    assert result["success"] is True


class TestPipelineTools:
    """Test pipeline-related tools."""
    
    @pytest.mark.asyncio
    async def test_list_pipelines(self, mock_mcp, mock_client_factory, client):
        """Test list_pipelines tool."""
        register_deal_tools_lazy(mock_mcp, mock_client_factory)
        tool = mock_mcp.tools["list_pipelines"]
        
        with patch.object(client, 'list_pipelines', return_value={"success": True, "data": [{"id": 1, "name": "Sales"}]}):
            result_json = await tool()
            result = json.loads(result_json)
        
        assert result["success"] is True
        assert len(result["data"]) > 0
    
    @pytest.mark.asyncio
    async def test_list_pipelines_with_user_id(self, mock_mcp, mock_client_factory, client):
        """Test list_pipelines with user_id."""
        register_deal_tools_lazy(mock_mcp, mock_client_factory)
        tool = mock_mcp.tools["list_pipelines"]
        
        with patch.object(client, 'list_pipelines', return_value={"success": True, "data": []}) as mock:
            await tool(user_id="tenant_123")
            call_kwargs = mock.call_args.kwargs
            assert call_kwargs['user_id'] == "tenant_123"
    
    @pytest.mark.asyncio
    async def test_list_pipelines_exception(self, mock_mcp, mock_client_factory, client):
        """Test list_pipelines handles exceptions."""
        register_deal_tools_lazy(mock_mcp, mock_client_factory)
        tool = mock_mcp.tools["list_pipelines"]
        
        with patch.object(client, 'list_pipelines', side_effect=Exception("Pipeline error")):
            result_json = await tool()
            result = json.loads(result_json)
            
            assert result["success"] is False
            assert "error" in result
    
    @pytest.mark.asyncio
    async def test_get_pipeline(self, mock_mcp, mock_client_factory, client):
        """Test get_pipeline tool."""
        register_deal_tools_lazy(mock_mcp, mock_client_factory)
        tool = mock_mcp.tools["get_pipeline"]
        
        with patch.object(client, 'get_pipeline', return_value={"success": True, "data": {"id": 1, "name": "Sales"}}):
            result_json = await tool(pipeline_id=1)
            result = json.loads(result_json)
        
        assert result["success"] is True
        assert result["data"]["id"] == 1
    
    @pytest.mark.asyncio
    async def test_get_pipeline_with_user_id(self, mock_mcp, mock_client_factory, client):
        """Test get_pipeline with user_id."""
        register_deal_tools_lazy(mock_mcp, mock_client_factory)
        tool = mock_mcp.tools["get_pipeline"]
        
        with patch.object(client, 'get_pipeline', return_value={"success": True, "data": {}}) as mock:
            await tool(pipeline_id=1, user_id="tenant_456")
            call_kwargs = mock.call_args.kwargs
            assert call_kwargs['pipeline_id'] == 1
            assert call_kwargs['user_id'] == "tenant_456"
    
    @pytest.mark.asyncio
    async def test_get_pipeline_exception(self, mock_mcp, mock_client_factory, client):
        """Test get_pipeline handles exceptions."""
        register_deal_tools_lazy(mock_mcp, mock_client_factory)
        tool = mock_mcp.tools["get_pipeline"]
        
        with patch.object(client, 'get_pipeline', side_effect=Exception("Not found")):
            result_json = await tool(pipeline_id=1)
            result = json.loads(result_json)
            
            assert result["success"] is False
            assert "error" in result
    
    @pytest.mark.asyncio
    async def test_list_pipeline_stages(self, mock_mcp, mock_client_factory, client):
        """Test list_pipeline_stages tool."""
        register_deal_tools_lazy(mock_mcp, mock_client_factory)
        tool = mock_mcp.tools["list_pipeline_stages"]
        
        with patch.object(client, 'list_pipeline_stages', return_value={"success": True, "data": [{"id": 1, "name": "New"}]}):
            result_json = await tool(pipeline_id=1)
            result = json.loads(result_json)
        
        assert result["success"] is True
        assert len(result["data"]) > 0
    
    @pytest.mark.asyncio
    async def test_list_pipeline_stages_with_user_id(self, mock_mcp, mock_client_factory, client):
        """Test list_pipeline_stages with user_id."""
        register_deal_tools_lazy(mock_mcp, mock_client_factory)
        tool = mock_mcp.tools["list_pipeline_stages"]
        
        with patch.object(client, 'list_pipeline_stages', return_value={"success": True, "data": []}) as mock:
            await tool(pipeline_id=1, user_id="tenant_789")
            call_kwargs = mock.call_args.kwargs
            assert call_kwargs['pipeline_id'] == 1
            assert call_kwargs['user_id'] == "tenant_789"
    
    @pytest.mark.asyncio
    async def test_list_pipeline_stages_exception(self, mock_mcp, mock_client_factory, client):
        """Test list_pipeline_stages handles exceptions."""
        register_deal_tools_lazy(mock_mcp, mock_client_factory)
        tool = mock_mcp.tools["list_pipeline_stages"]
        
        with patch.object(client, 'list_pipeline_stages', side_effect=Exception("Stages error")):
            result_json = await tool(pipeline_id=1)
            result = json.loads(result_json)
            
            assert result["success"] is False
            assert "error" in result


class TestAdditionalDealTools:
    """Test additional deal tools not covered in basic tests."""
    
    @pytest.mark.asyncio
    async def test_get_deal_chat_history_with_pagination(self, mock_mcp, mock_client_factory, client):
        """Test get_deal_chat_history with pagination."""
        register_deal_tools_lazy(mock_mcp, mock_client_factory)
        tool = mock_mcp.tools["get_deal_chat_history"]
        
        with patch.object(client, 'get_deal_chat_history', return_value={"success": True, "data": []}) as mock:
            await tool(deal_id=123, page=2, per_page=50, user_id="tenant_abc")
            call_kwargs = mock.call_args.kwargs
            assert call_kwargs['page'] == 2
            assert call_kwargs['per_page'] == 50
    
    @pytest.mark.asyncio
    async def test_get_deal_chat_history_exception(self, mock_mcp, mock_client_factory, client):
        """Test get_deal_chat_history handles exceptions."""
        register_deal_tools_lazy(mock_mcp, mock_client_factory)
        tool = mock_mcp.tools["get_deal_chat_history"]
        
        with patch.object(client, 'get_deal_chat_history', side_effect=Exception("Chat error")):
            result_json = await tool(deal_id=123)
            result = json.loads(result_json)
            
            assert result["success"] is False
            assert "error" in result
    
    @pytest.mark.asyncio
    async def test_get_deal_real_creator_with_user_id(self, mock_mcp, mock_client_factory, client):
        """Test get_deal_real_creator with user_id."""
        register_deal_tools_lazy(mock_mcp, mock_client_factory)
        tool = mock_mcp.tools["get_deal_real_creator"]
        
        with patch.object(client, 'get_deal_real_creator', return_value={"success": True, "data": {}}) as mock:
            await tool(deal_id=123, user_id="tenant_xyz")
            call_kwargs = mock.call_args.kwargs
            assert call_kwargs['user_id'] == "tenant_xyz"
    
    @pytest.mark.asyncio
    async def test_get_deal_real_creator_exception(self, mock_mcp, mock_client_factory, client):
        """Test get_deal_real_creator handles exceptions."""
        register_deal_tools_lazy(mock_mcp, mock_client_factory)
        tool = mock_mcp.tools["get_deal_real_creator"]
        
        with patch.object(client, 'get_deal_real_creator', side_effect=Exception("Creator error")):
            result_json = await tool(deal_id=123)
            result = json.loads(result_json)
            
            assert result["success"] is False
            assert "error" in result
    
    @pytest.mark.asyncio
    async def test_get_deal_full_field_with_user_id(self, mock_mcp, mock_client_factory, client):
        """Test get_deal_full_field with user_id."""
        register_deal_tools_lazy(mock_mcp, mock_client_factory)
        tool = mock_mcp.tools["get_deal_full_field"]
        
        with patch.object(client, 'get_deal_full_field', return_value={"success": True, "data": {}}) as mock:
            await tool(deal_id=123, user_id="tenant_abc")
            call_kwargs = mock.call_args.kwargs
            assert call_kwargs['user_id'] == "tenant_abc"
    
    @pytest.mark.asyncio
    async def test_get_deal_full_field_exception(self, mock_mcp, mock_client_factory, client):
        """Test get_deal_full_field handles exceptions."""
        register_deal_tools_lazy(mock_mcp, mock_client_factory)
        tool = mock_mcp.tools["get_deal_full_field"]
        
        with patch.object(client, 'get_deal_full_field', side_effect=Exception("Field error")):
            result_json = await tool(deal_id=123)
            result = json.loads(result_json)
            
            assert result["success"] is False
            assert "error" in result
    
    @pytest.mark.asyncio
    async def test_get_deal_permissions_with_user_id(self, mock_mcp, mock_client_factory, client):
        """Test get_deal_permissions with user_id."""
        register_deal_tools_lazy(mock_mcp, mock_client_factory)
        tool = mock_mcp.tools["get_deal_permissions"]
        
        with patch.object(client, 'get_deal_permissions', return_value={"success": True, "data": {}}) as mock:
            await tool(deal_id=123, user_id="tenant_xyz")
            call_kwargs = mock.call_args.kwargs
            assert call_kwargs['user_id'] == "tenant_xyz"
    
    @pytest.mark.asyncio
    async def test_get_deal_permissions_exception(self, mock_mcp, mock_client_factory, client):
        """Test get_deal_permissions handles exceptions."""
        register_deal_tools_lazy(mock_mcp, mock_client_factory)
        tool = mock_mcp.tools["get_deal_permissions"]
        
        with patch.object(client, 'get_deal_permissions', side_effect=Exception("Permissions error")):
            result_json = await tool(deal_id=123)
            result = json.loads(result_json)
            
            assert result["success"] is False
            assert "error" in result
    
    @pytest.mark.asyncio
    async def test_update_deal_owner_with_user_id(self, mock_mcp, mock_client_factory, client):
        """Test update_deal_owner with user_id."""
        register_deal_tools_lazy(mock_mcp, mock_client_factory)
        tool = mock_mcp.tools["update_deal_owner"]
        
        with patch.object(client, 'update_deal_owner', return_value={"success": True, "data": {}}) as mock:
            await tool(deal_id=123, creator_id=456, user_id="tenant_abc")
            call_kwargs = mock.call_args.kwargs
            assert call_kwargs['creator_id'] == 456
            assert call_kwargs['user_id'] == "tenant_abc"
    
    @pytest.mark.asyncio
    async def test_update_deal_owner_exception(self, mock_mcp, mock_client_factory, client):
        """Test update_deal_owner handles exceptions."""
        register_deal_tools_lazy(mock_mcp, mock_client_factory)
        tool = mock_mcp.tools["update_deal_owner"]
        
        with patch.object(client, 'update_deal_owner', side_effect=Exception("Owner update error")):
            result_json = await tool(deal_id=123, creator_id=456)
            result = json.loads(result_json)
            
            assert result["success"] is False
            assert "error" in result


class TestGetRequiredFieldsForDeal:
    """Test get_required_fields_for_deal tool comprehensively."""
    
    @pytest.mark.asyncio
    async def test_get_required_fields_basic(self, mock_mcp, mock_client_factory, client):
        """Test get_required_fields_for_deal basic functionality."""
        register_deal_tools_lazy(mock_mcp, mock_client_factory)
        tool = mock_mcp.tools["get_required_fields_for_deal"]
        
        template_response = {
            "success": True,
            "data": {
                "response": [
                    {
                        "name": "name",
                        "name_alias": "Deal Name",
                        "type": "Single-line text",
                        "additional_field": False,
                        "required_pipeline_ids": [1],
                        "required_stage_ids": [2],
                        "dropdown": None,
                        "id": None
                    },
                    {
                        "name": "industry",
                        "name_alias": "Industry",
                        "type": "Dropdown select",
                        "additional_field": True,
                        "required_pipeline_ids": [1],
                        "required_stage_ids": [],
                        "dropdown": [{"id": 1, "value": "Tech"}, {"id": 2, "value": "Finance"}],
                        "id": 100
                    }
                ]
            }
        }
        
        with patch.object(client, 'get_deal_template', return_value=template_response):
            result_json = await tool(crm_pipeline_id=1, crm_stage_id=2)
            result = json.loads(result_json)
        
        assert result["success"] is True
        assert result["pipeline_id"] == 1
        assert result["stage_id"] == 2
        assert "required_standard_fields" in result
        assert "required_custom_fields" in result
        assert len(result["required_standard_fields"]) > 0
        assert len(result["required_custom_fields"]) > 0
    
    @pytest.mark.asyncio
    async def test_get_required_fields_with_dropdown_options(self, mock_mcp, mock_client_factory, client):
        """Test get_required_fields_for_deal includes dropdown options."""
        register_deal_tools_lazy(mock_mcp, mock_client_factory)
        tool = mock_mcp.tools["get_required_fields_for_deal"]
        
        template_response = {
            "success": True,
            "data": {
                "response": [
                    {
                        "name": "status",
                        "name_alias": "Status",
                        "type": "Dropdown select",
                        "additional_field": False,
                        "required_pipeline_ids": [5],
                        "required_stage_ids": [],
                        "dropdown": [{"id": 1, "value": "Active"}, {"id": 2, "value": "Inactive"}],
                        "id": None
                    }
                ]
            }
        }
        
        with patch.object(client, 'get_deal_template', return_value=template_response):
            result_json = await tool(crm_pipeline_id=5, crm_stage_id=1)
            result = json.loads(result_json)
        
        assert result["success"] is True
        required_field = result["required_standard_fields"][0]
        assert required_field["has_dropdown"] is True
        assert len(required_field["dropdown_options"]) == 2
        assert "description" in required_field
    
    @pytest.mark.asyncio
    async def test_get_required_fields_separates_standard_and_custom(self, mock_mcp, mock_client_factory, client):
        """Test get_required_fields_for_deal separates standard and custom fields."""
        register_deal_tools_lazy(mock_mcp, mock_client_factory)
        tool = mock_mcp.tools["get_required_fields_for_deal"]
        
        template_response = {
            "success": True,
            "data": {
                "response": [
                    {
                        "name": "name",
                        "name_alias": "Name",
                        "type": "Single-line text",
                        "additional_field": False,
                        "required_pipeline_ids": [1],
                        "required_stage_ids": [],
                        "dropdown": None,
                        "id": None
                    },
                    {
                        "name": "custom_field",
                        "name_alias": "Custom Field",
                        "type": "Number",
                        "additional_field": True,
                        "required_pipeline_ids": [1],
                        "required_stage_ids": [],
                        "dropdown": None,
                        "id": 200
                    },
                    {
                        "name": "optional_field",
                        "name_alias": "Optional",
                        "type": "Text Area",
                        "additional_field": False,
                        "required_pipeline_ids": [],
                        "required_stage_ids": [],
                        "dropdown": None,
                        "id": None
                    }
                ]
            }
        }
        
        with patch.object(client, 'get_deal_template', return_value=template_response):
            result_json = await tool(crm_pipeline_id=1, crm_stage_id=1)
            result = json.loads(result_json)
        
        assert result["success"] is True
        assert len(result["required_standard_fields"]) == 1
        assert len(result["required_custom_fields"]) == 1
        assert result["required_custom_fields"][0]["id"] == 200
        assert "optional_standard_fields" in result
    
    @pytest.mark.asyncio
    async def test_get_required_fields_by_stage_id(self, mock_mcp, mock_client_factory, client):
        """Test get_required_fields_for_deal filters by stage_id."""
        register_deal_tools_lazy(mock_mcp, mock_client_factory)
        tool = mock_mcp.tools["get_required_fields_for_deal"]
        
        template_response = {
            "success": True,
            "data": {
                "response": [
                    {
                        "name": "field_required_for_stage",
                        "name_alias": "Stage Required Field",
                        "type": "Date",
                        "additional_field": False,
                        "required_pipeline_ids": [],
                        "required_stage_ids": [10],
                        "dropdown": None,
                        "id": None
                    }
                ]
            }
        }
        
        with patch.object(client, 'get_deal_template', return_value=template_response):
            result_json = await tool(crm_pipeline_id=1, crm_stage_id=10)
            result = json.loads(result_json)
        
        assert result["success"] is True
        assert len(result["required_standard_fields"]) == 1
        assert result["required_standard_fields"][0]["name"] == "field_required_for_stage"
    
    @pytest.mark.asyncio
    async def test_get_required_fields_with_field_types(self, mock_mcp, mock_client_factory, client):
        """Test get_required_fields_for_deal includes field type descriptions."""
        register_deal_tools_lazy(mock_mcp, mock_client_factory)
        tool = mock_mcp.tools["get_required_fields_for_deal"]
        
        template_response = {
            "success": True,
            "data": {
                "response": [
                    {"name": "text", "name_alias": "Text", "type": "Single-line text", "additional_field": False, 
                     "required_pipeline_ids": [1], "required_stage_ids": [], "dropdown": None, "id": None},
                    {"name": "textarea", "name_alias": "TextArea", "type": "Text Area", "additional_field": False,
                     "required_pipeline_ids": [1], "required_stage_ids": [], "dropdown": None, "id": None},
                    {"name": "number", "name_alias": "Number", "type": "Number", "additional_field": False,
                     "required_pipeline_ids": [1], "required_stage_ids": [], "dropdown": None, "id": None},
                    {"name": "date", "name_alias": "Date", "type": "Date", "additional_field": False,
                     "required_pipeline_ids": [1], "required_stage_ids": [], "dropdown": None, "id": None}
                ]
            }
        }
        
        with patch.object(client, 'get_deal_template', return_value=template_response):
            result_json = await tool(crm_pipeline_id=1, crm_stage_id=1)
            result = json.loads(result_json)
        
        assert result["success"] is True
        fields = result["required_standard_fields"]
        assert any("Text input, single line" in f["description"] for f in fields)
        assert any("Text input, multiple lines" in f["description"] for f in fields)
        assert any("Numeric value" in f["description"] for f in fields)
        assert any("Date value" in f["description"] for f in fields)
    
    @pytest.mark.asyncio
    async def test_get_required_fields_limits_optional_fields(self, mock_mcp, mock_client_factory, client):
        """Test get_required_fields_for_deal limits optional fields to 10."""
        register_deal_tools_lazy(mock_mcp, mock_client_factory)
        tool = mock_mcp.tools["get_required_fields_for_deal"]
        
        # Create 15 optional fields
        optional_fields = [
            {
                "name": f"optional_{i}",
                "name_alias": f"Optional {i}",
                "type": "Single-line text",
                "additional_field": False,
                "required_pipeline_ids": [],
                "required_stage_ids": [],
                "dropdown": None,
                "id": None
            }
            for i in range(15)
        ]
        
        template_response = {
            "success": True,
            "data": {"response": optional_fields}
        }
        
        with patch.object(client, 'get_deal_template', return_value=template_response):
            result_json = await tool(crm_pipeline_id=1, crm_stage_id=1)
            result = json.loads(result_json)
        
        assert result["success"] is True
        assert len(result["optional_standard_fields"]) == 10
    
    @pytest.mark.asyncio
    async def test_get_required_fields_with_user_id(self, mock_mcp, mock_client_factory, client):
        """Test get_required_fields_for_deal with user_id."""
        register_deal_tools_lazy(mock_mcp, mock_client_factory)
        tool = mock_mcp.tools["get_required_fields_for_deal"]
        
        template_response = {
            "success": True,
            "data": {"response": []}
        }
        
        with patch.object(client, 'get_deal_template', return_value=template_response) as mock:
            await tool(crm_pipeline_id=1, crm_stage_id=1, user_id="tenant_xyz")
            call_kwargs = mock.call_args.kwargs
            assert call_kwargs['user_id'] == "tenant_xyz"
    
    @pytest.mark.asyncio
    async def test_get_required_fields_template_error(self, mock_mcp, mock_client_factory, client):
        """Test get_required_fields_for_deal when template returns error."""
        register_deal_tools_lazy(mock_mcp, mock_client_factory)
        tool = mock_mcp.tools["get_required_fields_for_deal"]
        
        template_response = {
            "success": False,
            "error": "Template not found"
        }
        
        with patch.object(client, 'get_deal_template', return_value=template_response):
            result_json = await tool(crm_pipeline_id=1, crm_stage_id=1)
            result = json.loads(result_json)
        
        assert result["success"] is False
    
    @pytest.mark.asyncio
    async def test_get_required_fields_dropdown_without_options(self, mock_mcp, mock_client_factory, client):
        """Test get_required_fields_for_deal with dropdown field but no options."""
        register_deal_tools_lazy(mock_mcp, mock_client_factory)
        tool = mock_mcp.tools["get_required_fields_for_deal"]
        
        template_response = {
            "success": True,
            "data": {
                "response": [
                    {
                        "name": "dropdown_no_options",
                        "name_alias": "Dropdown No Options",
                        "type": "Dropdown select",
                        "additional_field": False,
                        "required_pipeline_ids": [1],
                        "required_stage_ids": [],
                        "dropdown": None,
                        "id": None
                    }
                ]
            }
        }
        
        with patch.object(client, 'get_deal_template', return_value=template_response):
            result_json = await tool(crm_pipeline_id=1, crm_stage_id=1)
            result = json.loads(result_json)
        
        assert result["success"] is True
        field = result["required_standard_fields"][0]
        assert "Select one option from available choices" in field["description"]
        assert field["has_dropdown"] is False
    
    @pytest.mark.asyncio
    async def test_get_required_fields_optional_custom_fields(self, mock_mcp, mock_client_factory, client):
        """Test get_required_fields_for_deal includes optional custom fields."""
        register_deal_tools_lazy(mock_mcp, mock_client_factory)
        tool = mock_mcp.tools["get_required_fields_for_deal"]
        
        template_response = {
            "success": True,
            "data": {
                "response": [
                    {
                        "name": "optional_custom",
                        "name_alias": "Optional Custom Field",
                        "type": "Number",
                        "additional_field": True,
                        "required_pipeline_ids": [],
                        "required_stage_ids": [],
                        "dropdown": None,
                        "id": 500
                    }
                ]
            }
        }
        
        with patch.object(client, 'get_deal_template', return_value=template_response):
            result_json = await tool(crm_pipeline_id=1, crm_stage_id=1)
            result = json.loads(result_json)
        
        assert result["success"] is True
        assert len(result["optional_custom_fields"]) == 1
        assert result["optional_custom_fields"][0]["id"] == 500
    
    @pytest.mark.asyncio
    async def test_get_required_fields_exception(self, mock_mcp, mock_client_factory, client):
        """Test get_required_fields_for_deal handles exceptions."""
        register_deal_tools_lazy(mock_mcp, mock_client_factory)
        tool = mock_mcp.tools["get_required_fields_for_deal"]
        
        with patch.object(client, 'get_deal_template', side_effect=Exception("Template error")):
            result_json = await tool(crm_pipeline_id=1, crm_stage_id=1)
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