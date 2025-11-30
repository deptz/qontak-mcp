"""
Comprehensive tests for contact tools.

Achieves 100% code coverage for src/qontak_mcp/tools/contacts.py
"""

import pytest
import json
import httpx
from unittest.mock import MagicMock, patch
from qontak_mcp.tools.contacts import register_contact_tools_lazy, register_contact_tools

# Import fixtures
from tests.tools.contact_fixtures import (
    mock_contact_data,
    mock_contact_list_response,
    mock_contact_get_response,
    mock_contact_create_response,
    mock_contact_update_response,
    mock_contact_delete_response,
    mock_contact_template_response,
    mock_contact_required_fields_response,
    mock_contact_timeline_response,
    mock_contact_chat_history_response,
    mock_contact_owner_update_response,
    mock_contact_additional_fields,
    invalid_contact_additional_fields,
    mock_api_error_401,
    mock_api_error_403,
    mock_api_error_404,
    mock_api_error_422,
    mock_api_error_429,
    mock_api_error_500,
)


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


# ============================================================================
# BASIC TOOL INVOCATION TESTS (Happy Path)
# ============================================================================

@pytest.mark.asyncio
async def test_get_contact_template_tool(mock_mcp, mock_client_factory, client, mock_contact_template_response):
    """Test get_contact_template tool - happy path."""
    register_contact_tools_lazy(mock_mcp, mock_client_factory)
    tool = mock_mcp.tools["get_contact_template"]
    
    with patch.object(client, 'get_contact_template', return_value=mock_contact_template_response):
        result_json = await tool()
        result = json.loads(result_json)
    
    assert result["success"] is True
    assert "data" in result


@pytest.mark.asyncio
async def test_list_contacts_tool(mock_mcp, mock_client_factory, client, mock_contact_list_response):
    """Test list_contacts tool - happy path."""
    register_contact_tools_lazy(mock_mcp, mock_client_factory)
    tool = mock_mcp.tools["list_contacts"]
    
    with patch.object(client, 'list_contacts', return_value=mock_contact_list_response):
        result_json = await tool(page=1, per_page=25)
        result = json.loads(result_json)
    
    assert result["success"] is True
    assert "data" in result
    assert len(result["data"]["data"]) > 0


@pytest.mark.asyncio
async def test_get_contact_tool(mock_mcp, mock_client_factory, client, mock_contact_get_response):
    """Test get_contact tool - happy path."""
    register_contact_tools_lazy(mock_mcp, mock_client_factory)
    tool = mock_mcp.tools["get_contact"]
    
    with patch.object(client, 'get_contact', return_value=mock_contact_get_response):
        result_json = await tool(contact_id=12345)
        result = json.loads(result_json)
    
    assert result["success"] is True
    assert result["data"]["data"]["id"] == 12345


@pytest.mark.asyncio
async def test_create_contact_tool(mock_mcp, mock_client_factory, client, mock_contact_create_response):
    """Test create_contact tool - happy path."""
    register_contact_tools_lazy(mock_mcp, mock_client_factory)
    tool = mock_mcp.tools["create_contact"]
    
    with patch.object(client, 'create_contact', return_value=mock_contact_create_response):
        result_json = await tool(first_name="John")
        result = json.loads(result_json)
    
    assert result["success"] is True
    assert result["data"]["data"]["first_name"] == "John"


@pytest.mark.asyncio
async def test_update_contact_tool(mock_mcp, mock_client_factory, client, mock_contact_update_response):
    """Test update_contact tool - happy path."""
    register_contact_tools_lazy(mock_mcp, mock_client_factory)
    tool = mock_mcp.tools["update_contact"]
    
    with patch.object(client, 'update_contact', return_value=mock_contact_update_response):
        result_json = await tool(contact_id=12345, first_name="Updated John")
        result = json.loads(result_json)
    
    assert result["success"] is True


@pytest.mark.asyncio
async def test_delete_contact_tool(mock_mcp, mock_client_factory, client, mock_contact_delete_response):
    """Test delete_contact tool - happy path."""
    register_contact_tools_lazy(mock_mcp, mock_client_factory)
    tool = mock_mcp.tools["delete_contact"]
    
    with patch.object(client, 'delete_contact', return_value=mock_contact_delete_response):
        result_json = await tool(contact_id=12345)
        result = json.loads(result_json)
    
    assert result["success"] is True


@pytest.mark.asyncio
async def test_get_contact_timeline_tool(mock_mcp, mock_client_factory, client, mock_contact_timeline_response):
    """Test get_contact_timeline tool - happy path."""
    register_contact_tools_lazy(mock_mcp, mock_client_factory)
    tool = mock_mcp.tools["get_contact_timeline"]
    
    with patch.object(client, 'get_contact_timeline', return_value=mock_contact_timeline_response):
        result_json = await tool(contact_id=12345)
        result = json.loads(result_json)
    
    assert result["success"] is True
    assert len(result["data"]["data"]) > 0


@pytest.mark.asyncio
async def test_get_contact_chat_history_tool(mock_mcp, mock_client_factory, client, mock_contact_chat_history_response):
    """Test get_contact_chat_history tool - happy path."""
    register_contact_tools_lazy(mock_mcp, mock_client_factory)
    tool = mock_mcp.tools["get_contact_chat_history"]
    
    with patch.object(client, 'get_contact_chat_history', return_value=mock_contact_chat_history_response):
        result_json = await tool(contact_id=12345)
        result = json.loads(result_json)
    
    assert result["success"] is True
    assert len(result["data"]["data"]) > 0


@pytest.mark.asyncio
async def test_update_contact_owner_tool(mock_mcp, mock_client_factory, client, mock_contact_owner_update_response):
    """Test update_contact_owner tool - happy path."""
    register_contact_tools_lazy(mock_mcp, mock_client_factory)
    tool = mock_mcp.tools["update_contact_owner"]
    
    with patch.object(client, 'update_contact_owner', return_value=mock_contact_owner_update_response):
        result_json = await tool(contact_id=12345, creator_id=999)
        result = json.loads(result_json)
    
    assert result["success"] is True


@pytest.mark.asyncio
async def test_get_required_fields_for_contact_tool(mock_mcp, mock_client_factory, client):
    """Test get_required_fields_for_contact tool - happy path."""
    register_contact_tools_lazy(mock_mcp, mock_client_factory)
    tool = mock_mcp.tools["get_required_fields_for_contact"]
    
    template_response = {
        "success": True,
        "data": {
            "response": [
                {
                    "id": 1,
                    "name": "first_name",
                    "name_alias": "First Name",
                    "type": "text",
                    "required": True,
                    "additional_field": False,
                    "dropdown": []
                }
            ]
        }
    }
    
    with patch.object(client, 'get_contact_template', return_value=template_response):
        result_json = await tool()
        result = json.loads(result_json)
    
    assert result["success"] is True
    assert "required_standard_fields" in result


# ============================================================================
# REGISTRATION TESTS
# ============================================================================

class TestContactToolsRegisterWrapper:
    """Test the register_contact_tools wrapper function."""
    
    @pytest.mark.asyncio
    async def test_register_contact_tools_wrapper(self, mock_mcp, client):
        """Test register_contact_tools uses lazy registration internally."""
        register_contact_tools(mock_mcp, client)
        
        # Should have registered all 10 tools
        assert "get_contact_template" in mock_mcp.tools
        assert "list_contacts" in mock_mcp.tools
        assert "get_contact" in mock_mcp.tools
        assert "create_contact" in mock_mcp.tools
        assert "update_contact" in mock_mcp.tools
        assert "delete_contact" in mock_mcp.tools
        assert "get_contact_timeline" in mock_mcp.tools
        assert "get_contact_chat_history" in mock_mcp.tools
        assert "update_contact_owner" in mock_mcp.tools
        assert "get_required_fields_for_contact" in mock_mcp.tools


# ============================================================================
# PARAMETER TESTS WITH USER_ID
# ============================================================================

class TestContactToolsWithUserId:
    """Test all tools with user_id for multi-tenant scenarios."""
    
    @pytest.mark.asyncio
    async def test_get_contact_template_with_user_id(self, mock_mcp, mock_client_factory, client, mock_contact_template_response):
        """Test get_contact_template with user_id."""
        register_contact_tools_lazy(mock_mcp, mock_client_factory)
        tool = mock_mcp.tools["get_contact_template"]
        
        with patch.object(client, 'get_contact_template', return_value=mock_contact_template_response) as mock:
            await tool(user_id="tenant_123")
            mock.assert_called_once_with(user_id="tenant_123")
    
    @pytest.mark.asyncio
    async def test_list_contacts_with_user_id(self, mock_mcp, mock_client_factory, client, mock_contact_list_response):
        """Test list_contacts with user_id."""
        register_contact_tools_lazy(mock_mcp, mock_client_factory)
        tool = mock_mcp.tools["list_contacts"]
        
        with patch.object(client, 'list_contacts', return_value=mock_contact_list_response) as mock:
            await tool(page=1, per_page=25, user_id="tenant_123")
            call_kwargs = mock.call_args.kwargs
            assert call_kwargs['user_id'] == "tenant_123"
    
    @pytest.mark.asyncio
    async def test_get_contact_with_user_id(self, mock_mcp, mock_client_factory, client, mock_contact_get_response):
        """Test get_contact with user_id."""
        register_contact_tools_lazy(mock_mcp, mock_client_factory)
        tool = mock_mcp.tools["get_contact"]
        
        with patch.object(client, 'get_contact', return_value=mock_contact_get_response) as mock:
            await tool(contact_id=12345, user_id="tenant_123")
            call_kwargs = mock.call_args.kwargs
            assert call_kwargs['user_id'] == "tenant_123"


# ============================================================================
# VALIDATION ERROR TESTS
# ============================================================================

class TestContactToolsValidationErrors:
    """Test Pydantic validation errors for all tools."""
    
    @pytest.mark.asyncio
    async def test_list_contacts_negative_page(self, mock_mcp, mock_client_factory, client):
        """Test list_contacts with negative page number."""
        register_contact_tools_lazy(mock_mcp, mock_client_factory)
        tool = mock_mcp.tools["list_contacts"]
        
        result_json = await tool(page=-1, per_page=25)
        result = json.loads(result_json)
        
        assert result["success"] is False
        assert "error" in result
    
    @pytest.mark.asyncio
    async def test_get_contact_negative_id(self, mock_mcp, mock_client_factory, client):
        """Test get_contact with negative ID."""
        register_contact_tools_lazy(mock_mcp, mock_client_factory)
        tool = mock_mcp.tools["get_contact"]
        
        result_json = await tool(contact_id=-1)
        result = json.loads(result_json)
        
        assert result["success"] is False
        assert "error" in result
    
    @pytest.mark.asyncio
    async def test_create_contact_empty_first_name(self, mock_mcp, mock_client_factory, client):
        """Test create_contact with empty first_name."""
        register_contact_tools_lazy(mock_mcp, mock_client_factory)
        tool = mock_mcp.tools["create_contact"]
        
        result_json = await tool(first_name="")
        result = json.loads(result_json)
        
        assert result["success"] is False
        assert "error" in result
    
    @pytest.mark.asyncio
    async def test_delete_contact_negative_id(self, mock_mcp, mock_client_factory, client):
        """Test delete_contact with negative ID."""
        register_contact_tools_lazy(mock_mcp, mock_client_factory)
        tool = mock_mcp.tools["delete_contact"]
        
        result_json = await tool(contact_id=-1)
        result = json.loads(result_json)
        
        assert result["success"] is False
        assert "error" in result


# ============================================================================
# JSON PARSING ERROR TESTS
# ============================================================================

class TestContactToolsJsonErrors:
    """Test JSON parsing errors for additional_fields."""
    
    @pytest.mark.asyncio
    async def test_create_contact_invalid_json(self, mock_mcp, mock_client_factory, client, invalid_contact_additional_fields):
        """Test create_contact with invalid JSON."""
        register_contact_tools_lazy(mock_mcp, mock_client_factory)
        tool = mock_mcp.tools["create_contact"]
        
        result_json = await tool(first_name="John", additional_fields=invalid_contact_additional_fields)
        result = json.loads(result_json)
        
        assert result["success"] is False
        assert "Invalid JSON format" in result["error"]
    
    @pytest.mark.asyncio
    async def test_create_contact_additional_fields_not_array(self, mock_mcp, mock_client_factory, client):
        """Test create_contact when additional_fields is not an array."""
        register_contact_tools_lazy(mock_mcp, mock_client_factory)
        tool = mock_mcp.tools["create_contact"]
        
        result_json = await tool(first_name="John", additional_fields='{"key": "value"}')
        result = json.loads(result_json)
        
        assert result["success"] is False
        assert "must be a JSON array" in result["error"]
    
    @pytest.mark.asyncio
    async def test_update_contact_invalid_json(self, mock_mcp, mock_client_factory, client, invalid_contact_additional_fields):
        """Test update_contact with invalid JSON."""
        register_contact_tools_lazy(mock_mcp, mock_client_factory)
        tool = mock_mcp.tools["update_contact"]
        
        result_json = await tool(contact_id=12345, additional_fields=invalid_contact_additional_fields)
        result = json.loads(result_json)
        
        assert result["success"] is False
        assert "Invalid JSON format" in result["error"]


# ============================================================================
# CLIENT EXCEPTION TESTS
# ============================================================================

class TestContactToolsClientExceptions:
    """Test client exception handling for all tools."""
    
    @pytest.mark.asyncio
    async def test_get_contact_template_exception(self, mock_mcp, mock_client_factory, client):
        """Test get_contact_template handles exceptions."""
        register_contact_tools_lazy(mock_mcp, mock_client_factory)
        tool = mock_mcp.tools["get_contact_template"]
        
        with patch.object(client, 'get_contact_template', side_effect=Exception("Network error")):
            result_json = await tool()
            result = json.loads(result_json)
            
            assert result["success"] is False
            assert "error" in result
    
    @pytest.mark.asyncio
    async def test_list_contacts_exception(self, mock_mcp, mock_client_factory, client):
        """Test list_contacts handles exceptions."""
        register_contact_tools_lazy(mock_mcp, mock_client_factory)
        tool = mock_mcp.tools["list_contacts"]
        
        with patch.object(client, 'list_contacts', side_effect=Exception("Network error")):
            result_json = await tool(page=1, per_page=25)
            result = json.loads(result_json)
            
            assert result["success"] is False
            assert "error" in result
    
    @pytest.mark.asyncio
    async def test_create_contact_exception(self, mock_mcp, mock_client_factory, client):
        """Test create_contact handles exceptions."""
        register_contact_tools_lazy(mock_mcp, mock_client_factory)
        tool = mock_mcp.tools["create_contact"]
        
        with patch.object(client, 'create_contact', side_effect=Exception("Network error")):
            result_json = await tool(first_name="John")
            result = json.loads(result_json)
            
            assert result["success"] is False
            assert "error" in result


# ============================================================================
# CREATE CONTACT COMPREHENSIVE TESTS
# ============================================================================

class TestCreateContactComprehensive:
    """Comprehensive tests for create_contact tool."""
    
    @pytest.mark.asyncio
    async def test_create_contact_all_fields(self, mock_mcp, mock_client_factory, client, mock_contact_create_response):
        """Test create_contact with all optional fields."""
        register_contact_tools_lazy(mock_mcp, mock_client_factory)
        tool = mock_mcp.tools["create_contact"]
        
        with patch.object(client, 'create_contact', return_value=mock_contact_create_response) as mock:
            await tool(
                first_name="John",
                last_name="Doe",
                email="john@example.com",
                telephone="+1234567890",
                job_title="Engineer",
                crm_status_id=1,
                crm_company_id=100,
                address="123 St",
                city="City",
                province="Province",
                country="Country",
                zipcode="12345",
                date_of_birth="1990-01-01",
                user_id="tenant_123"
            )
            call_kwargs = mock.call_args.kwargs
            assert call_kwargs['contact_data']['first_name'] == "John"
            assert call_kwargs['contact_data']['email'] == "john@example.com"
            assert call_kwargs['user_id'] == "tenant_123"
    
    @pytest.mark.asyncio
    async def test_create_contact_with_additional_fields(self, mock_mcp, mock_client_factory, client, mock_contact_create_response, mock_contact_additional_fields):
        """Test create_contact with valid additional_fields."""
        register_contact_tools_lazy(mock_mcp, mock_client_factory)
        tool = mock_mcp.tools["create_contact"]
        
        with patch.object(client, 'create_contact', return_value=mock_contact_create_response) as mock:
            await tool(first_name="John", additional_fields=mock_contact_additional_fields)
            call_kwargs = mock.call_args.kwargs
            assert 'additional_fields' in call_kwargs['contact_data']
            assert isinstance(call_kwargs['contact_data']['additional_fields'], list)
    
    @pytest.mark.asyncio
    async def test_create_contact_empty_additional_fields(self, mock_mcp, mock_client_factory, client, mock_contact_create_response):
        """Test create_contact with empty additional_fields array."""
        register_contact_tools_lazy(mock_mcp, mock_client_factory)
        tool = mock_mcp.tools["create_contact"]
        
        with patch.object(client, 'create_contact', return_value=mock_contact_create_response) as mock:
            await tool(first_name="John", additional_fields='[]')
            call_kwargs = mock.call_args.kwargs
            assert call_kwargs['contact_data']['additional_fields'] == []
    
    @pytest.mark.asyncio
    async def test_create_contact_none_additional_fields(self, mock_mcp, mock_client_factory, client, mock_contact_create_response):
        """Test create_contact when additional_fields is None."""
        register_contact_tools_lazy(mock_mcp, mock_client_factory)
        tool = mock_mcp.tools["create_contact"]
        
        with patch.object(client, 'create_contact', return_value=mock_contact_create_response) as mock:
            await tool(first_name="John")
            call_kwargs = mock.call_args.kwargs
            assert call_kwargs['contact_data']['additional_fields'] == []


# ============================================================================
# UPDATE CONTACT COMPREHENSIVE TESTS
# ============================================================================

class TestUpdateContactComprehensive:
    """Comprehensive tests for update_contact tool."""
    
    @pytest.mark.asyncio
    async def test_update_contact_single_field(self, mock_mcp, mock_client_factory, client, mock_contact_update_response):
        """Test update_contact with single field."""
        register_contact_tools_lazy(mock_mcp, mock_client_factory)
        tool = mock_mcp.tools["update_contact"]
        
        with patch.object(client, 'update_contact', return_value=mock_contact_update_response) as mock:
            await tool(contact_id=12345, email="new@example.com")
            call_kwargs = mock.call_args.kwargs
            assert call_kwargs['contact_data']['email'] == "new@example.com"
            assert 'first_name' not in call_kwargs['contact_data']
    
    @pytest.mark.asyncio
    async def test_update_contact_empty_data(self, mock_mcp, mock_client_factory, client):
        """Test update_contact with no fields to update - should fail validation."""
        register_contact_tools_lazy(mock_mcp, mock_client_factory)
        tool = mock_mcp.tools["update_contact"]
        
        # Should fail validation when no fields provided
        result_json = await tool(contact_id=12345)
        result = json.loads(result_json)
        assert result["success"] is False
        assert "error" in result
    
    @pytest.mark.asyncio
    async def test_update_contact_with_additional_fields(self, mock_mcp, mock_client_factory, client, mock_contact_update_response, mock_contact_additional_fields):
        """Test update_contact with additional_fields."""
        register_contact_tools_lazy(mock_mcp, mock_client_factory)
        tool = mock_mcp.tools["update_contact"]
        
        with patch.object(client, 'update_contact', return_value=mock_contact_update_response) as mock:
            await tool(contact_id=12345, additional_fields=mock_contact_additional_fields)
            call_kwargs = mock.call_args.kwargs
            assert 'additional_fields' in call_kwargs['contact_data']


# ============================================================================
# GET REQUIRED FIELDS COMPREHENSIVE TESTS
# ============================================================================

class TestGetRequiredFieldsComprehensive:
    """Comprehensive tests for get_required_fields_for_contact tool."""
    
    @pytest.mark.asyncio
    async def test_get_required_fields_with_custom_fields(self, mock_mcp, mock_client_factory, client):
        """Test get_required_fields with custom fields."""
        register_contact_tools_lazy(mock_mcp, mock_client_factory)
        tool = mock_mcp.tools["get_required_fields_for_contact"]
        
        template_response = {
            "success": True,
            "data": {
                "response": [
                    {
                        "id": 1,
                        "name": "first_name",
                        "name_alias": "First Name",
                        "type": "text",
                        "required": True,
                        "additional_field": False,
                        "dropdown": []
                    },
                    {
                        "id": 14840254,
                        "name": "custom_field",
                        "name_alias": "Custom Field",
                        "type": "text",
                        "required": True,
                        "additional_field": True,
                        "dropdown": []
                    }
                ]
            }
        }
        
        with patch.object(client, 'get_contact_template', return_value=template_response):
            result_json = await tool()
            result = json.loads(result_json)
            
            assert result["success"] is True
            assert len(result["required_custom_fields"]) > 0
            assert result["summary"]["required_custom"] == 1
    
    @pytest.mark.asyncio
    async def test_get_required_fields_with_dropdown(self, mock_mcp, mock_client_factory, client):
        """Test get_required_fields with dropdown options."""
        register_contact_tools_lazy(mock_mcp, mock_client_factory)
        tool = mock_mcp.tools["get_required_fields_for_contact"]
        
        template_response = {
            "success": True,
            "data": {
                "response": [
                    {
                        "id": 1,
                        "name": "status",
                        "name_alias": "Status",
                        "type": "dropdown",
                        "required": True,
                        "additional_field": False,
                        "dropdown": [
                            {"id": 1, "name": "Active", "email": "test@example.com"},
                            {"id": 2, "name": "Inactive"}
                        ]
                    }
                ]
            }
        }
        
        with patch.object(client, 'get_contact_template', return_value=template_response):
            result_json = await tool()
            result = json.loads(result_json)
            
            assert result["success"] is True
            field = result["required_standard_fields"][0]
            assert field["has_dropdown"] is True
            assert len(field["dropdown_options"]) == 2
            assert field["dropdown_options"][0]["email"] == "test@example.com"
    
    @pytest.mark.asyncio
    async def test_get_required_fields_template_failure(self, mock_mcp, mock_client_factory, client):
        """Test get_required_fields when template fetch fails."""
        register_contact_tools_lazy(mock_mcp, mock_client_factory)
        tool = mock_mcp.tools["get_required_fields_for_contact"]
        
        template_response = {"success": False, "error": "Failed"}
        
        with patch.object(client, 'get_contact_template', return_value=template_response):
            result_json = await tool()
            result = json.loads(result_json)
            
            assert result["success"] is False
    
    @pytest.mark.asyncio
    async def test_get_required_fields_null_dropdown(self, mock_mcp, mock_client_factory, client):
        """Test get_required_fields when dropdown is null."""
        register_contact_tools_lazy(mock_mcp, mock_client_factory)
        tool = mock_mcp.tools["get_required_fields_for_contact"]
        
        template_response = {
            "success": True,
            "data": {
                "response": [
                    {
                        "id": 1,
                        "name": "first_name",
                        "name_alias": "First Name",
                        "type": "text",
                        "required": True,
                        "additional_field": False,
                        "dropdown": None
                    }
                ]
            }
        }
        
        with patch.object(client, 'get_contact_template', return_value=template_response):
            result_json = await tool()
            result = json.loads(result_json)
            
            assert result["success"] is True
            field = result["required_standard_fields"][0]
            assert field["has_dropdown"] is False


# ============================================================================
# PAGINATION TESTS
# ============================================================================

class TestContactToolsPagination:
    """Test pagination parameters for list and timeline tools."""
    
    @pytest.mark.asyncio
    async def test_list_contacts_custom_pagination(self, mock_mcp, mock_client_factory, client, mock_contact_list_response):
        """Test list_contacts with custom page and per_page."""
        register_contact_tools_lazy(mock_mcp, mock_client_factory)
        tool = mock_mcp.tools["list_contacts"]
        
        with patch.object(client, 'list_contacts', return_value=mock_contact_list_response) as mock:
            await tool(page=2, per_page=50)
            call_kwargs = mock.call_args.kwargs
            assert call_kwargs['page'] == 2
            assert call_kwargs['per_page'] == 50
    
    @pytest.mark.asyncio
    async def test_get_contact_timeline_pagination(self, mock_mcp, mock_client_factory, client, mock_contact_timeline_response):
        """Test get_contact_timeline with pagination."""
        register_contact_tools_lazy(mock_mcp, mock_client_factory)
        tool = mock_mcp.tools["get_contact_timeline"]
        
        with patch.object(client, 'get_contact_timeline', return_value=mock_contact_timeline_response) as mock:
            await tool(contact_id=12345, page=3, per_page=100)
            call_kwargs = mock.call_args.kwargs
            assert call_kwargs['page'] == 3
            assert call_kwargs['per_page'] == 100
    
    @pytest.mark.asyncio
    async def test_get_contact_chat_history_pagination(self, mock_mcp, mock_client_factory, client, mock_contact_chat_history_response):
        """Test get_contact_chat_history with pagination."""
        register_contact_tools_lazy(mock_mcp, mock_client_factory)
        tool = mock_mcp.tools["get_contact_chat_history"]
        
        with patch.object(client, 'get_contact_chat_history', return_value=mock_contact_chat_history_response) as mock:
            await tool(contact_id=12345, page=2, per_page=75)
            call_kwargs = mock.call_args.kwargs
            assert call_kwargs['page'] == 2
            assert call_kwargs['per_page'] == 75


# ============================================================================
# ADDITIONAL COVERAGE TESTS
# ============================================================================

class TestContactToolsAdditionalCoverage:
    """Additional tests to achieve 100% coverage."""
    
    @pytest.mark.asyncio
    async def test_create_contact_with_all_optional_none_fields(self, mock_mcp, mock_client_factory, client, mock_contact_create_response):
        """Test create_contact building contact_data with various optional fields."""
        register_contact_tools_lazy(mock_mcp, mock_client_factory)
        tool = mock_mcp.tools["create_contact"]
        
        with patch.object(client, 'create_contact', return_value=mock_contact_create_response) as mock:
            # Test with last_name, email, telephone explicitly
            await tool(
                first_name="John",
                last_name="Doe",
                email="john@example.com",
                telephone="+1234567890",
                job_title="Engineer",
                crm_status_id=1,
                crm_company_id=100,
                address="123 St",
                city="City",
                province="Province",
                country="Country",
                zipcode="12345",
                date_of_birth="1990-01-01"
            )
            call_kwargs = mock.call_args.kwargs
            # Verify all fields are in contact_data
            assert 'last_name' in call_kwargs['contact_data']
            assert 'email' in call_kwargs['contact_data']
            assert 'telephone' in call_kwargs['contact_data']
            assert 'job_title' in call_kwargs['contact_data']
            assert 'crm_status_id' in call_kwargs['contact_data']
            assert 'crm_company_id' in call_kwargs['contact_data']
            assert 'address' in call_kwargs['contact_data']
            assert 'city' in call_kwargs['contact_data']
            assert 'province' in call_kwargs['contact_data']
            assert 'country' in call_kwargs['contact_data']
            assert 'zipcode' in call_kwargs['contact_data']
            assert 'date_of_birth' in call_kwargs['contact_data']
    
    @pytest.mark.asyncio
    async def test_update_contact_with_all_optional_fields(self, mock_mcp, mock_client_factory, client, mock_contact_update_response):
        """Test update_contact building contact_data with all optional fields."""
        register_contact_tools_lazy(mock_mcp, mock_client_factory)
        tool = mock_mcp.tools["update_contact"]
        
        with patch.object(client, 'update_contact', return_value=mock_contact_update_response) as mock:
            await tool(
                contact_id=12345,
                first_name="John",
                last_name="Doe",
                email="john@example.com",
                telephone="+1234567890",
                job_title="Engineer",
                crm_status_id=1,
                crm_company_id=100,
                address="123 St",
                city="City",
                province="Province",
                country="Country",
                zipcode="12345",
                date_of_birth="1990-01-01"
            )
            call_kwargs = mock.call_args.kwargs
            # Verify all optional fields are in contact_data
            assert 'first_name' in call_kwargs['contact_data']
            assert 'last_name' in call_kwargs['contact_data']
            assert 'email' in call_kwargs['contact_data']
            assert 'telephone' in call_kwargs['contact_data']
            assert 'job_title' in call_kwargs['contact_data']
            assert 'crm_status_id' in call_kwargs['contact_data']
            assert 'crm_company_id' in call_kwargs['contact_data']
            assert 'address' in call_kwargs['contact_data']
            assert 'city' in call_kwargs['contact_data']
            assert 'province' in call_kwargs['contact_data']
            assert 'country' in call_kwargs['contact_data']
            assert 'zipcode' in call_kwargs['contact_data']
            assert 'date_of_birth' in call_kwargs['contact_data']
    
    @pytest.mark.asyncio
    async def test_get_contact_exception_coverage(self, mock_mcp, mock_client_factory, client):
        """Test get_contact exception handling."""
        register_contact_tools_lazy(mock_mcp, mock_client_factory)
        tool = mock_mcp.tools["get_contact"]
        
        with patch.object(client, 'get_contact', side_effect=Exception("Network error")):
            result_json = await tool(contact_id=12345)
            result = json.loads(result_json)
            
            assert result["success"] is False
            assert "error" in result
    
    @pytest.mark.asyncio
    async def test_update_contact_exception_coverage(self, mock_mcp, mock_client_factory, client):
        """Test update_contact exception handling."""
        register_contact_tools_lazy(mock_mcp, mock_client_factory)
        tool = mock_mcp.tools["update_contact"]
        
        with patch.object(client, 'update_contact', side_effect=Exception("Network error")):
            result_json = await tool(contact_id=12345, first_name="John")
            result = json.loads(result_json)
            
            assert result["success"] is False
            assert "error" in result
    
    @pytest.mark.asyncio
    async def test_delete_contact_exception_coverage(self, mock_mcp, mock_client_factory, client):
        """Test delete_contact exception handling."""
        register_contact_tools_lazy(mock_mcp, mock_client_factory)
        tool = mock_mcp.tools["delete_contact"]
        
        with patch.object(client, 'delete_contact', side_effect=Exception("Network error")):
            result_json = await tool(contact_id=12345)
            result = json.loads(result_json)
            
            assert result["success"] is False
            assert "error" in result
    
    @pytest.mark.asyncio
    async def test_get_contact_timeline_exception_coverage(self, mock_mcp, mock_client_factory, client):
        """Test get_contact_timeline exception handling."""
        register_contact_tools_lazy(mock_mcp, mock_client_factory)
        tool = mock_mcp.tools["get_contact_timeline"]
        
        with patch.object(client, 'get_contact_timeline', side_effect=Exception("Network error")):
            result_json = await tool(contact_id=12345)
            result = json.loads(result_json)
            
            assert result["success"] is False
            assert "error" in result
    
    @pytest.mark.asyncio
    async def test_get_contact_chat_history_exception_coverage(self, mock_mcp, mock_client_factory, client):
        """Test get_contact_chat_history exception handling."""
        register_contact_tools_lazy(mock_mcp, mock_client_factory)
        tool = mock_mcp.tools["get_contact_chat_history"]
        
        with patch.object(client, 'get_contact_chat_history', side_effect=Exception("Network error")):
            result_json = await tool(contact_id=12345)
            result = json.loads(result_json)
            
            assert result["success"] is False
            assert "error" in result
    
    @pytest.mark.asyncio
    async def test_update_contact_owner_exception_coverage(self, mock_mcp, mock_client_factory, client):
        """Test update_contact_owner exception handling."""
        register_contact_tools_lazy(mock_mcp, mock_client_factory)
        tool = mock_mcp.tools["update_contact_owner"]
        
        with patch.object(client, 'update_contact_owner', side_effect=Exception("Network error")):
            result_json = await tool(contact_id=12345, creator_id=999)
            result = json.loads(result_json)
            
            assert result["success"] is False
            assert "error" in result
    
    @pytest.mark.asyncio
    async def test_get_contact_timeline_validation_error(self, mock_mcp, mock_client_factory, client):
        """Test get_contact_timeline with validation error."""
        register_contact_tools_lazy(mock_mcp, mock_client_factory)
        tool = mock_mcp.tools["get_contact_timeline"]
        
        result_json = await tool(contact_id=-1, page=1, per_page=25)
        result = json.loads(result_json)
        
        assert result["success"] is False
        assert "error" in result
    
    @pytest.mark.asyncio
    async def test_get_contact_chat_history_validation_error(self, mock_mcp, mock_client_factory, client):
        """Test get_contact_chat_history with validation error."""
        register_contact_tools_lazy(mock_mcp, mock_client_factory)
        tool = mock_mcp.tools["get_contact_chat_history"]
        
        result_json = await tool(contact_id=-1, page=1, per_page=25)
        result = json.loads(result_json)
        
        assert result["success"] is False
        assert "error" in result
    
    @pytest.mark.asyncio
    async def test_update_contact_owner_validation_error(self, mock_mcp, mock_client_factory, client):
        """Test update_contact_owner with validation error."""
        register_contact_tools_lazy(mock_mcp, mock_client_factory)
        tool = mock_mcp.tools["update_contact_owner"]
        
        result_json = await tool(contact_id=-1, creator_id=999)
        result = json.loads(result_json)
        
        assert result["success"] is False
        assert "error" in result
    
    @pytest.mark.asyncio
    async def test_get_required_fields_with_optional_custom_fields(self, mock_mcp, mock_client_factory, client, mock_contact_template_with_custom_fields):
        """Test get_required_fields_for_contact with optional custom fields."""
        register_contact_tools_lazy(mock_mcp, mock_client_factory)
        tool = mock_mcp.tools["get_required_fields_for_contact"]
        
        with patch.object(client, 'get_contact_template', return_value=mock_contact_template_with_custom_fields):
            result_json = await tool()
            result = json.loads(result_json)
            
            assert result["success"] is True
            assert "optional_custom_fields" in result
            assert len(result["optional_custom_fields"]) == 2
            # Verify the custom fields are categorized correctly
            custom_field_names = [f["name"] for f in result["optional_custom_fields"]]
            assert "custom_field_1" in custom_field_names
            assert "custom_field_2" in custom_field_names
    
    @pytest.mark.asyncio
    async def test_get_required_fields_exception_coverage(self, mock_mcp, mock_client_factory, client):
        """Test get_required_fields_for_contact exception handling."""
        register_contact_tools_lazy(mock_mcp, mock_client_factory)
        tool = mock_mcp.tools["get_required_fields_for_contact"]
        
        with patch.object(client, 'get_contact_template', side_effect=Exception("Network error")):
            result_json = await tool()
            result = json.loads(result_json)
            
            assert result["success"] is False
            assert "error" in result
