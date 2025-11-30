"""Comprehensive test suite for companies tools."""

import pytest
import json
from unittest.mock import patch, MagicMock
from qontak_mcp.tools.companies import register_company_tools_lazy
from pydantic import ValidationError as PydanticValidationError


class MockFastMCP:
    """Mock FastMCP server for testing."""
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
    """Provide a mock FastMCP instance."""
    return MockFastMCP()


@pytest.fixture
def mock_client_factory(client):
    """Provide a client factory."""
    return lambda: client


# ============================================================================
# Basic Tool Invocation Tests
# ============================================================================

class TestCompanyToolsBasicInvocation:
    """Test basic invocation of all company tools."""
    
    @pytest.mark.asyncio
    async def test_get_company_template_basic(self, mock_mcp, mock_client_factory, client, mock_company_template_response):
        """Test get_company_template basic invocation."""
        register_company_tools_lazy(mock_mcp, mock_client_factory)
        tool = mock_mcp.tools["get_company_template"]
        
        with patch.object(client, 'get_company_template', return_value=mock_company_template_response):
            result_json = await tool()
            result = json.loads(result_json)
            
            assert result["success"] is True
            assert "data" in result
    
    @pytest.mark.asyncio
    async def test_list_companies_basic(self, mock_mcp, mock_client_factory, client, mock_company_list_response):
        """Test list_companies basic invocation."""
        register_company_tools_lazy(mock_mcp, mock_client_factory)
        tool = mock_mcp.tools["list_companies"]
        
        with patch.object(client, 'list_companies', return_value=mock_company_list_response):
            result_json = await tool()
            result = json.loads(result_json)
            
            assert result["success"] is True
            assert "data" in result
    
    @pytest.mark.asyncio
    async def test_get_company_basic(self, mock_mcp, mock_client_factory, client, mock_company_get_response):
        """Test get_company basic invocation."""
        register_company_tools_lazy(mock_mcp, mock_client_factory)
        tool = mock_mcp.tools["get_company"]
        
        with patch.object(client, 'get_company', return_value=mock_company_get_response):
            result_json = await tool(company_id=1)
            result = json.loads(result_json)
            
            assert result["success"] is True
    
    @pytest.mark.asyncio
    async def test_create_company_basic(self, mock_mcp, mock_client_factory, client, mock_company_create_response):
        """Test create_company basic invocation."""
        register_company_tools_lazy(mock_mcp, mock_client_factory)
        tool = mock_mcp.tools["create_company"]
        
        with patch.object(client, 'create_company', return_value=mock_company_create_response):
            result_json = await tool(name="Test Company")
            result = json.loads(result_json)
            
            assert result["success"] is True
    
    @pytest.mark.asyncio
    async def test_update_company_basic(self, mock_mcp, mock_client_factory, client, mock_company_update_response):
        """Test update_company basic invocation."""
        register_company_tools_lazy(mock_mcp, mock_client_factory)
        tool = mock_mcp.tools["update_company"]
        
        with patch.object(client, 'update_company', return_value=mock_company_update_response):
            result_json = await tool(company_id=1, name="Updated Company")
            result = json.loads(result_json)
            
            assert result["success"] is True
    
    @pytest.mark.asyncio
    async def test_delete_company_basic(self, mock_mcp, mock_client_factory, client, mock_company_delete_response):
        """Test delete_company basic invocation."""
        register_company_tools_lazy(mock_mcp, mock_client_factory)
        tool = mock_mcp.tools["delete_company"]
        
        with patch.object(client, 'delete_company', return_value=mock_company_delete_response):
            result_json = await tool(company_id=1)
            result = json.loads(result_json)
            
            assert result["success"] is True
    
    @pytest.mark.asyncio
    async def test_get_company_timeline_basic(self, mock_mcp, mock_client_factory, client, mock_company_timeline_response):
        """Test get_company_timeline basic invocation."""
        register_company_tools_lazy(mock_mcp, mock_client_factory)
        tool = mock_mcp.tools["get_company_timeline"]
        
        with patch.object(client, 'get_company_timeline', return_value=mock_company_timeline_response):
            result_json = await tool(company_id=1)
            result = json.loads(result_json)
            
            assert result["success"] is True
    
    @pytest.mark.asyncio
    async def test_get_required_fields_basic(self, mock_mcp, mock_client_factory, client, mock_company_template_response):
        """Test get_required_fields_for_company basic invocation."""
        register_company_tools_lazy(mock_mcp, mock_client_factory)
        tool = mock_mcp.tools["get_required_fields_for_company"]
        
        with patch.object(client, 'get_company_template', return_value=mock_company_template_response):
            result_json = await tool()
            result = json.loads(result_json)
            
            assert result["success"] is True


# ============================================================================
# Registration Tests
# ============================================================================

class TestCompanyToolsRegisterWrapper:
    """Test tool registration."""
    
    @pytest.mark.asyncio
    async def test_all_tools_registered(self, mock_mcp, mock_client_factory):
        """Test that all 8 company tools are registered."""
        register_company_tools_lazy(mock_mcp, mock_client_factory)
        
        expected_tools = [
            "get_company_template",
            "list_companies",
            "get_company",
            "create_company",
            "update_company",
            "delete_company",
            "get_company_timeline",
            "get_required_fields_for_company",
        ]
        
        assert len(mock_mcp.tools) == 8
        for tool_name in expected_tools:
            assert tool_name in mock_mcp.tools


# ============================================================================
# Multi-tenant (user_id) Tests
# ============================================================================

class TestCompanyToolsWithUserId:
    """Test tools with user_id parameter."""
    
    @pytest.mark.asyncio
    async def test_get_company_template_with_user_id(self, mock_mcp, mock_client_factory, client, mock_company_template_response):
        """Test get_company_template passes user_id correctly."""
        register_company_tools_lazy(mock_mcp, mock_client_factory)
        tool = mock_mcp.tools["get_company_template"]
        
        with patch.object(client, 'get_company_template', return_value=mock_company_template_response) as mock:
            await tool(user_id="tenant123")
            mock.assert_called_once_with(user_id="tenant123")
    
    @pytest.mark.asyncio
    async def test_list_companies_with_user_id(self, mock_mcp, mock_client_factory, client, mock_company_list_response):
        """Test list_companies passes user_id correctly."""
        register_company_tools_lazy(mock_mcp, mock_client_factory)
        tool = mock_mcp.tools["list_companies"]
        
        with patch.object(client, 'list_companies', return_value=mock_company_list_response) as mock:
            await tool(user_id="tenant123")
            assert mock.call_args.kwargs["user_id"] == "tenant123"
    
    @pytest.mark.asyncio
    async def test_get_company_with_user_id(self, mock_mcp, mock_client_factory, client, mock_company_get_response):
        """Test get_company passes user_id correctly."""
        register_company_tools_lazy(mock_mcp, mock_client_factory)
        tool = mock_mcp.tools["get_company"]
        
        with patch.object(client, 'get_company', return_value=mock_company_get_response) as mock:
            await tool(company_id=1, user_id="tenant123")
            assert mock.call_args.kwargs["user_id"] == "tenant123"


# ============================================================================
# Validation Error Tests
# ============================================================================

class TestCompanyToolsValidationErrors:
    """Test Pydantic validation error handling."""
    
    @pytest.mark.asyncio
    async def test_list_companies_invalid_page(self, mock_mcp, mock_client_factory, client):
        """Test list_companies with invalid page number."""
        register_company_tools_lazy(mock_mcp, mock_client_factory)
        tool = mock_mcp.tools["list_companies"]
        
        result_json = await tool(page=-1)
        result = json.loads(result_json)
        
        assert result["success"] is False
        assert "error" in result
    
    @pytest.mark.asyncio
    async def test_list_companies_invalid_per_page(self, mock_mcp, mock_client_factory, client):
        """Test list_companies with invalid per_page."""
        register_company_tools_lazy(mock_mcp, mock_client_factory)
        tool = mock_mcp.tools["list_companies"]
        
        result_json = await tool(per_page=0)
        result = json.loads(result_json)
        
        assert result["success"] is False
        assert "error" in result
    
    @pytest.mark.asyncio
    async def test_get_company_timeline_invalid_page(self, mock_mcp, mock_client_factory, client):
        """Test get_company_timeline with invalid page."""
        register_company_tools_lazy(mock_mcp, mock_client_factory)
        tool = mock_mcp.tools["get_company_timeline"]
        
        result_json = await tool(company_id=1, page=-1)
        result = json.loads(result_json)
        
        assert result["success"] is False
        assert "error" in result
    
    @pytest.mark.asyncio
    async def test_create_company_empty_name(self, mock_mcp, mock_client_factory, client):
        """Test create_company with empty name."""
        register_company_tools_lazy(mock_mcp, mock_client_factory)
        tool = mock_mcp.tools["create_company"]
        
        result_json = await tool(name="")
        result = json.loads(result_json)
        
        assert result["success"] is False
        assert "error" in result


# ============================================================================
# JSON Parsing Error Tests
# ============================================================================

class TestCompanyToolsJsonErrors:
    """Test JSON parsing error handling."""
    
    @pytest.mark.asyncio
    async def test_create_company_invalid_additional_fields_json(self, mock_mcp, mock_client_factory, client):
        """Test create_company with invalid additional_fields JSON."""
        register_company_tools_lazy(mock_mcp, mock_client_factory)
        tool = mock_mcp.tools["create_company"]
        
        result_json = await tool(name="Test", additional_fields="{bad json}")
        result = json.loads(result_json)
        
        assert result["success"] is False
        assert "error" in result
    
    @pytest.mark.asyncio
    async def test_update_company_invalid_additional_fields_json(self, mock_mcp, mock_client_factory, client):
        """Test update_company with invalid additional_fields JSON."""
        register_company_tools_lazy(mock_mcp, mock_client_factory)
        tool = mock_mcp.tools["update_company"]
        
        result_json = await tool(company_id=1, additional_fields="{bad json}")
        result = json.loads(result_json)
        
        assert result["success"] is False
        assert "error" in result


# ============================================================================
# Client Exception Tests
# ============================================================================

class TestCompanyToolsClientExceptions:
    """Test client exception handling."""
    
    @pytest.mark.asyncio
    async def test_get_company_exception(self, mock_mcp, mock_client_factory, client):
        """Test get_company with client exception."""
        register_company_tools_lazy(mock_mcp, mock_client_factory)
        tool = mock_mcp.tools["get_company"]
        
        with patch.object(client, 'get_company', side_effect=Exception("Network error")):
            result_json = await tool(company_id=1)
            result = json.loads(result_json)
            
            assert result["success"] is False
            assert "error" in result
    
    @pytest.mark.asyncio
    async def test_update_company_exception(self, mock_mcp, mock_client_factory, client):
        """Test update_company with client exception."""
        register_company_tools_lazy(mock_mcp, mock_client_factory)
        tool = mock_mcp.tools["update_company"]
        
        with patch.object(client, 'update_company', side_effect=Exception("Update failed")):
            result_json = await tool(company_id=1, name="Test")
            result = json.loads(result_json)
            
            assert result["success"] is False
            assert "error" in result
    
    @pytest.mark.asyncio
    async def test_delete_company_exception(self, mock_mcp, mock_client_factory, client):
        """Test delete_company with client exception."""
        register_company_tools_lazy(mock_mcp, mock_client_factory)
        tool = mock_mcp.tools["delete_company"]
        
        with patch.object(client, 'delete_company', side_effect=Exception("Delete failed")):
            result_json = await tool(company_id=1)
            result = json.loads(result_json)
            
            assert result["success"] is False
            assert "error" in result


# ============================================================================
# Comprehensive Parameter Tests
# ============================================================================

class TestCreateCompanyComprehensive:
    """Comprehensive tests for create_company."""
    
    @pytest.mark.asyncio
    async def test_create_company_with_all_optional_fields(self, mock_mcp, mock_client_factory, client, mock_company_create_response):
        """Test create_company with all optional fields."""
        register_company_tools_lazy(mock_mcp, mock_client_factory)
        tool = mock_mcp.tools["create_company"]
        
        with patch.object(client, 'create_company', return_value=mock_company_create_response) as mock:
            await tool(
                name="Test Company",
                crm_status_id=5,
                email="test@example.com",
                telephone="+1234567890",
                address="123 Main St",
                city="City",
                province="Province",
                country="Country",
                zipcode="12345",
                website="https://example.com",
                additional_fields='[{"id": 10, "value": "custom"}]',
                user_id="tenant123"
            )
            call_kwargs = mock.call_args.kwargs
            assert call_kwargs["company_data"]["email"] == "test@example.com"
            assert call_kwargs["company_data"]["telephone"] == "+1234567890"
            assert call_kwargs["company_data"]["address"] == "123 Main St"
            assert call_kwargs["company_data"]["website"] == "https://example.com"
            assert call_kwargs["user_id"] == "tenant123"
    
    @pytest.mark.asyncio
    async def test_create_company_builds_additional_fields_list(self, mock_mcp, mock_client_factory, client, mock_company_create_response):
        """Test create_company parses additional_fields JSON list."""
        register_company_tools_lazy(mock_mcp, mock_client_factory)
        tool = mock_mcp.tools["create_company"]
        
        with patch.object(client, 'create_company', return_value=mock_company_create_response):
            result_json = await tool(
                name="Test",
                additional_fields='[{"id": 1, "value": "test"}]'
            )
            result = json.loads(result_json)
            assert result["success"] is True
    
    @pytest.mark.asyncio
    async def test_create_company_without_additional_fields(self, mock_mcp, mock_client_factory, client, mock_company_create_response):
        """Test create_company without additional_fields (should default to empty list)."""
        register_company_tools_lazy(mock_mcp, mock_client_factory)
        tool = mock_mcp.tools["create_company"]
        
        with patch.object(client, 'create_company', return_value=mock_company_create_response) as mock:
            await tool(name="Test Company")
            # additional_fields defaults to [] when not provided
            assert mock.call_args.kwargs["company_data"]["additional_fields"] == []
    
    @pytest.mark.asyncio
    async def test_create_company_omits_none_values(self, mock_mcp, mock_client_factory, client, mock_company_create_response):
        """Test create_company omits None values from company_data."""
        register_company_tools_lazy(mock_mcp, mock_client_factory)
        tool = mock_mcp.tools["create_company"]
        
        with patch.object(client, 'create_company', return_value=mock_company_create_response) as mock:
            await tool(name="Test", email=None, telephone=None)
            company_data = mock.call_args.kwargs["company_data"]
            assert "email" not in company_data
            assert "telephone" not in company_data


class TestUpdateCompanyComprehensive:
    """Comprehensive tests for update_company."""
    
    @pytest.mark.asyncio
    async def test_update_company_with_all_optional_fields(self, mock_mcp, mock_client_factory, client, mock_company_update_response):
        """Test update_company with all optional fields."""
        register_company_tools_lazy(mock_mcp, mock_client_factory)
        tool = mock_mcp.tools["update_company"]
        
        with patch.object(client, 'update_company', return_value=mock_company_update_response) as mock:
            await tool(
                company_id=1,
                name="Updated",
                crm_status_id=10,
                email="updated@example.com",
                telephone="+9876543210",
                address="456 Oak St",
                city="New City",
                province="New Province",
                country="New Country",
                zipcode="54321",
                website="https://newsite.com",
                additional_fields='[{"id": 20, "value": "updated"}]'
            )
            call_kwargs = mock.call_args.kwargs
            assert "name" in call_kwargs["company_data"]
            assert "email" in call_kwargs["company_data"]
            assert "website" in call_kwargs["company_data"]
    
    @pytest.mark.asyncio
    async def test_update_company_builds_company_data_dict(self, mock_mcp, mock_client_factory, client, mock_company_update_response):
        """Test update_company builds company_data dict from parameters."""
        register_company_tools_lazy(mock_mcp, mock_client_factory)
        tool = mock_mcp.tools["update_company"]
        
        with patch.object(client, 'update_company', return_value=mock_company_update_response) as mock:
            await tool(company_id=1, name="Test", email="test@example.com")
            company_data = mock.call_args.kwargs["company_data"]
            assert isinstance(company_data, dict)
            assert company_data["name"] == "Test"
            assert company_data["email"] == "test@example.com"
    
    @pytest.mark.asyncio
    async def test_update_company_omits_none_values(self, mock_mcp, mock_client_factory, client, mock_company_update_response):
        """Test update_company omits None values."""
        register_company_tools_lazy(mock_mcp, mock_client_factory)
        tool = mock_mcp.tools["update_company"]
        
        with patch.object(client, 'update_company', return_value=mock_company_update_response) as mock:
            await tool(company_id=1, name="Test", email=None, telephone=None)
            company_data = mock.call_args.kwargs["company_data"]
            assert "email" not in company_data
            assert "telephone" not in company_data


class TestGetRequiredFieldsComprehensive:
    """Comprehensive tests for get_required_fields_for_company."""
    
    @pytest.mark.asyncio
    async def test_get_required_fields_parses_template(self, mock_mcp, mock_client_factory, client, mock_company_template_response):
        """Test get_required_fields_for_company parses template."""
        register_company_tools_lazy(mock_mcp, mock_client_factory)
        tool = mock_mcp.tools["get_required_fields_for_company"]
        
        with patch.object(client, 'get_company_template', return_value=mock_company_template_response):
            result_json = await tool()
            result = json.loads(result_json)
            
            assert result["success"] is True
            assert "required_standard_fields" in result
            assert "optional_standard_fields" in result
    
    @pytest.mark.asyncio
    async def test_get_required_fields_categorizes_fields(self, mock_mcp, mock_client_factory, client, mock_company_template_with_custom_fields):
        """Test get_required_fields_for_company categorizes fields correctly."""
        register_company_tools_lazy(mock_mcp, mock_client_factory)
        tool = mock_mcp.tools["get_required_fields_for_company"]
        
        with patch.object(client, 'get_company_template', return_value=mock_company_template_with_custom_fields):
            result_json = await tool()
            result = json.loads(result_json)
            
            assert "required_custom_fields" in result
            assert "optional_custom_fields" in result
            assert len(result["optional_custom_fields"]) == 2
    
    @pytest.mark.asyncio
    async def test_get_required_fields_handles_dropdown(self, mock_mcp, mock_client_factory, client, mock_company_template_with_dropdown):
        """Test get_required_fields_for_company handles dropdown fields."""
        register_company_tools_lazy(mock_mcp, mock_client_factory)
        tool = mock_mcp.tools["get_required_fields_for_company"]
        
        with patch.object(client, 'get_company_template', return_value=mock_company_template_with_dropdown):
            result_json = await tool()
            result = json.loads(result_json)
            
            assert result["success"] is True
            # Check if any field has dropdown_options
            all_fields = (result.get("required_standard_fields", []) + 
                         result.get("optional_standard_fields", []))
            dropdown_fields = [f for f in all_fields if f.get("has_dropdown")]
            assert len(dropdown_fields) > 0
    
    @pytest.mark.asyncio
    async def test_get_required_fields_exception_handling(self, mock_mcp, mock_client_factory, client):
        """Test get_required_fields_for_company exception handling."""
        register_company_tools_lazy(mock_mcp, mock_client_factory)
        tool = mock_mcp.tools["get_required_fields_for_company"]
        
        with patch.object(client, 'get_company_template', side_effect=Exception("Network error")):
            result_json = await tool()
            result = json.loads(result_json)
            
            assert result["success"] is False
            assert "error" in result


# ============================================================================
# Pagination Tests
# ============================================================================

class TestCompanyToolsPagination:
    """Test pagination parameters."""
    
    @pytest.mark.asyncio
    async def test_list_companies_with_pagination(self, mock_mcp, mock_client_factory, client, mock_company_list_response):
        """Test list_companies with pagination parameters."""
        register_company_tools_lazy(mock_mcp, mock_client_factory)
        tool = mock_mcp.tools["list_companies"]
        
        with patch.object(client, 'list_companies', return_value=mock_company_list_response) as mock:
            await tool(page=2, per_page=50)
            assert mock.call_args.kwargs["page"] == 2
            assert mock.call_args.kwargs["per_page"] == 50
    
    @pytest.mark.asyncio
    async def test_get_company_timeline_with_pagination(self, mock_mcp, mock_client_factory, client, mock_company_timeline_response):
        """Test get_company_timeline with pagination."""
        register_company_tools_lazy(mock_mcp, mock_client_factory)
        tool = mock_mcp.tools["get_company_timeline"]
        
        with patch.object(client, 'get_company_timeline', return_value=mock_company_timeline_response) as mock:
            await tool(company_id=1, page=3, per_page=25)
            assert mock.call_args.kwargs["page"] == 3
            assert mock.call_args.kwargs["per_page"] == 25
    
    @pytest.mark.asyncio
    async def test_list_companies_default_parameters(self, mock_mcp, mock_client_factory, client, mock_company_list_response):
        """Test list_companies with default parameters."""
        register_company_tools_lazy(mock_mcp, mock_client_factory)
        tool = mock_mcp.tools["list_companies"]
        
        with patch.object(client, 'list_companies', return_value=mock_company_list_response) as mock:
            await tool()
            assert mock.call_args.kwargs["page"] == 1
            assert mock.call_args.kwargs["per_page"] == 25


# ============================================================================
# Additional Coverage Tests
# ============================================================================

class TestCompanyToolsAdditionalCoverage:
    """Additional tests to achieve 100% coverage."""
    
    @pytest.mark.asyncio
    async def test_register_company_tools_non_lazy_wrapper(self, mock_mcp, client):
        """Test the non-lazy register_company_tools wrapper function."""
        from qontak_mcp.tools.companies import register_company_tools
        
        # Test that the wrapper function works
        register_company_tools(mock_mcp, client)
        
        # Verify tools are registered
        assert "get_company_template" in mock_mcp.tools
        assert len(mock_mcp.tools) == 8
    
    @pytest.mark.asyncio
    async def test_get_required_fields_template_not_successful(self, mock_mcp, mock_client_factory, client):
        """Test get_required_fields_for_company when template returns success=False."""
        register_company_tools_lazy(mock_mcp, mock_client_factory)
        tool = mock_mcp.tools["get_required_fields_for_company"]
        
        error_response = {"success": False, "error": "Template fetch failed"}
        with patch.object(client, 'get_company_template', return_value=error_response):
            result_json = await tool()
            result = json.loads(result_json)
            
            assert result["success"] is False
            assert "error" in result
    
    @pytest.mark.asyncio
    async def test_list_companies_exception_coverage(self, mock_mcp, mock_client_factory, client):
        """Test list_companies exception handling."""
        register_company_tools_lazy(mock_mcp, mock_client_factory)
        tool = mock_mcp.tools["list_companies"]
        
        with patch.object(client, 'list_companies', side_effect=Exception("Network error")):
            result_json = await tool()
            result = json.loads(result_json)
            
            assert result["success"] is False
            assert "error" in result
    
    @pytest.mark.asyncio
    async def test_create_company_exception_coverage(self, mock_mcp, mock_client_factory, client):
        """Test create_company exception handling."""
        register_company_tools_lazy(mock_mcp, mock_client_factory)
        tool = mock_mcp.tools["create_company"]
        
        with patch.object(client, 'create_company', side_effect=Exception("Create failed")):
            result_json = await tool(name="Test")
            result = json.loads(result_json)
            
            assert result["success"] is False
            assert "error" in result
    
    @pytest.mark.asyncio
    async def test_get_company_template_exception_coverage(self, mock_mcp, mock_client_factory, client):
        """Test get_company_template exception handling."""
        register_company_tools_lazy(mock_mcp, mock_client_factory)
        tool = mock_mcp.tools["get_company_template"]
        
        with patch.object(client, 'get_company_template', side_effect=Exception("Template error")):
            result_json = await tool()
            result = json.loads(result_json)
            
            assert result["success"] is False
            assert "error" in result
    
    @pytest.mark.asyncio
    async def test_get_company_timeline_exception_coverage(self, mock_mcp, mock_client_factory, client):
        """Test get_company_timeline exception handling."""
        register_company_tools_lazy(mock_mcp, mock_client_factory)
        tool = mock_mcp.tools["get_company_timeline"]
        
        with patch.object(client, 'get_company_timeline', side_effect=Exception("Timeline error")):
            result_json = await tool(company_id=1)
            result = json.loads(result_json)
            
            assert result["success"] is False
            assert "error" in result
    
    @pytest.mark.asyncio
    async def test_update_company_validation_error_coverage(self, mock_mcp, mock_client_factory, client):
        """Test update_company with validation error."""
        register_company_tools_lazy(mock_mcp, mock_client_factory)
        tool = mock_mcp.tools["update_company"]
        
        # Test with invalid company_id (negative number)
        result_json = await tool(company_id=-1, name="Test")
        result = json.loads(result_json)
        
        assert result["success"] is False
        assert "error" in result
