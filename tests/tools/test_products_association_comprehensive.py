"""Comprehensive test suite for products association tools."""

import pytest
import json
from unittest.mock import patch
from qontak_mcp.tools.products_association import register_products_association_tools_lazy, register_products_association_tools


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

class TestProductsAssociationToolsBasicInvocation:
    """Test basic invocation of all products association tools."""
    
    @pytest.mark.asyncio
    async def test_list_products_associations_basic(self, mock_mcp, mock_client_factory, client, mock_product_association_list_response):
        """Test list_products_associations basic invocation."""
        register_products_association_tools_lazy(mock_mcp, mock_client_factory)
        tool = mock_mcp.tools["list_products_associations"]
        
        with patch.object(client, 'list_products_associations', return_value=mock_product_association_list_response):
            result_json = await tool()
            result = json.loads(result_json)
            
            assert result["success"] is True
            assert "data" in result
    
    @pytest.mark.asyncio
    async def test_get_products_association_basic(self, mock_mcp, mock_client_factory, client, mock_product_association_get_response):
        """Test get_products_association basic invocation."""
        register_products_association_tools_lazy(mock_mcp, mock_client_factory)
        tool = mock_mcp.tools["get_products_association"]
        
        with patch.object(client, 'get_products_association', return_value=mock_product_association_get_response):
            result_json = await tool(association_id=1)
            result = json.loads(result_json)
            
            assert result["success"] is True
    
    @pytest.mark.asyncio
    async def test_create_products_association_basic(self, mock_mcp, mock_client_factory, client, mock_product_association_create_response):
        """Test create_products_association basic invocation."""
        register_products_association_tools_lazy(mock_mcp, mock_client_factory)
        tool = mock_mcp.tools["create_products_association"]
        
        with patch.object(client, 'create_products_association', return_value=mock_product_association_create_response):
            result_json = await tool(product_id=100)
            result = json.loads(result_json)
            
            assert result["success"] is True
    
    @pytest.mark.asyncio
    async def test_update_products_association_basic(self, mock_mcp, mock_client_factory, client, mock_product_association_update_response):
        """Test update_products_association basic invocation."""
        register_products_association_tools_lazy(mock_mcp, mock_client_factory)
        tool = mock_mcp.tools["update_products_association"]
        
        with patch.object(client, 'update_products_association', return_value=mock_product_association_update_response):
            result_json = await tool(association_id=1, quantity=5)
            result = json.loads(result_json)
            
            assert result["success"] is True
    
    @pytest.mark.asyncio
    async def test_delete_products_association_basic(self, mock_mcp, mock_client_factory, client, mock_product_association_delete_response):
        """Test delete_products_association basic invocation."""
        register_products_association_tools_lazy(mock_mcp, mock_client_factory)
        tool = mock_mcp.tools["delete_products_association"]
        
        with patch.object(client, 'delete_products_association', return_value=mock_product_association_delete_response):
            result_json = await tool(association_id=1)
            result = json.loads(result_json)
            
            assert result["success"] is True


# ============================================================================
# Registration Tests
# ============================================================================

class TestProductsAssociationToolsRegisterWrapper:
    """Test tool registration."""
    
    @pytest.mark.asyncio
    async def test_all_tools_registered(self, mock_mcp, mock_client_factory):
        """Test that all 5 products association tools are registered."""
        register_products_association_tools_lazy(mock_mcp, mock_client_factory)
        
        expected_tools = [
            "list_products_associations",
            "get_products_association",
            "create_products_association",
            "update_products_association",
            "delete_products_association",
        ]
        
        assert len(mock_mcp.tools) == 5
        for tool_name in expected_tools:
            assert tool_name in mock_mcp.tools
    
    @pytest.mark.asyncio
    async def test_register_products_association_tools_non_lazy_wrapper(self, mock_mcp, client):
        """Test the non-lazy register_products_association_tools wrapper function."""
        register_products_association_tools(mock_mcp, client)
        
        assert "list_products_associations" in mock_mcp.tools
        assert len(mock_mcp.tools) == 5


# ============================================================================
# Multi-tenant (user_id) Tests
# ============================================================================

class TestProductsAssociationToolsWithUserId:
    """Test tools with user_id parameter."""
    
    @pytest.mark.asyncio
    async def test_list_products_associations_with_user_id(self, mock_mcp, mock_client_factory, client, mock_product_association_list_response):
        """Test list_products_associations passes user_id correctly."""
        register_products_association_tools_lazy(mock_mcp, mock_client_factory)
        tool = mock_mcp.tools["list_products_associations"]
        
        with patch.object(client, 'list_products_associations', return_value=mock_product_association_list_response) as mock:
            await tool(user_id="tenant123")
            assert mock.call_args.kwargs["user_id"] == "tenant123"
    
    @pytest.mark.asyncio
    async def test_get_products_association_with_user_id(self, mock_mcp, mock_client_factory, client, mock_product_association_get_response):
        """Test get_products_association passes user_id correctly."""
        register_products_association_tools_lazy(mock_mcp, mock_client_factory)
        tool = mock_mcp.tools["get_products_association"]
        
        with patch.object(client, 'get_products_association', return_value=mock_product_association_get_response) as mock:
            await tool(association_id=1, user_id="tenant123")
            assert mock.call_args.kwargs["user_id"] == "tenant123"
    
    @pytest.mark.asyncio
    async def test_create_products_association_with_user_id(self, mock_mcp, mock_client_factory, client, mock_product_association_create_response):
        """Test create_products_association passes user_id correctly."""
        register_products_association_tools_lazy(mock_mcp, mock_client_factory)
        tool = mock_mcp.tools["create_products_association"]
        
        with patch.object(client, 'create_products_association', return_value=mock_product_association_create_response) as mock:
            await tool(product_id=100, user_id="tenant123")
            assert mock.call_args.kwargs["user_id"] == "tenant123"


# ============================================================================
# Validation Error Tests
# ============================================================================

class TestProductsAssociationToolsValidationErrors:
    """Test Pydantic validation error handling."""
    
    @pytest.mark.asyncio
    async def test_list_products_associations_invalid_page(self, mock_mcp, mock_client_factory, client):
        """Test list_products_associations with invalid page number."""
        register_products_association_tools_lazy(mock_mcp, mock_client_factory)
        tool = mock_mcp.tools["list_products_associations"]
        
        result_json = await tool(page=-1)
        result = json.loads(result_json)
        
        assert result["success"] is False
        assert "error" in result
    
    @pytest.mark.asyncio
    async def test_list_products_associations_invalid_per_page(self, mock_mcp, mock_client_factory, client):
        """Test list_products_associations with invalid per_page."""
        register_products_association_tools_lazy(mock_mcp, mock_client_factory)
        tool = mock_mcp.tools["list_products_associations"]
        
        result_json = await tool(per_page=0)
        result = json.loads(result_json)
        
        assert result["success"] is False
        assert "error" in result
    
    @pytest.mark.asyncio
    async def test_create_products_association_negative_quantity(self, mock_mcp, mock_client_factory, client):
        """Test create_products_association with negative quantity."""
        register_products_association_tools_lazy(mock_mcp, mock_client_factory)
        tool = mock_mcp.tools["create_products_association"]
        
        result_json = await tool(product_id=100, quantity=-1)
        result = json.loads(result_json)
        
        assert result["success"] is False
        assert "error" in result
    
    @pytest.mark.asyncio
    async def test_create_products_association_negative_price(self, mock_mcp, mock_client_factory, client):
        """Test create_products_association with negative price."""
        register_products_association_tools_lazy(mock_mcp, mock_client_factory)
        tool = mock_mcp.tools["create_products_association"]
        
        result_json = await tool(product_id=100, price=-10.0)
        result = json.loads(result_json)
        
        assert result["success"] is False
        assert "error" in result


# ============================================================================
# Client Exception Tests
# ============================================================================

class TestProductsAssociationToolsClientExceptions:
    """Test client exception handling."""
    
    @pytest.mark.asyncio
    async def test_list_products_associations_exception(self, mock_mcp, mock_client_factory, client):
        """Test list_products_associations with client exception."""
        register_products_association_tools_lazy(mock_mcp, mock_client_factory)
        tool = mock_mcp.tools["list_products_associations"]
        
        with patch.object(client, 'list_products_associations', side_effect=Exception("Network error")):
            result_json = await tool()
            result = json.loads(result_json)
            
            assert result["success"] is False
            assert "error" in result
    
    @pytest.mark.asyncio
    async def test_get_products_association_exception(self, mock_mcp, mock_client_factory, client):
        """Test get_products_association with client exception."""
        register_products_association_tools_lazy(mock_mcp, mock_client_factory)
        tool = mock_mcp.tools["get_products_association"]
        
        with patch.object(client, 'get_products_association', side_effect=Exception("Not found")):
            result_json = await tool(association_id=1)
            result = json.loads(result_json)
            
            assert result["success"] is False
            assert "error" in result
    
    @pytest.mark.asyncio
    async def test_create_products_association_exception(self, mock_mcp, mock_client_factory, client):
        """Test create_products_association with client exception."""
        register_products_association_tools_lazy(mock_mcp, mock_client_factory)
        tool = mock_mcp.tools["create_products_association"]
        
        with patch.object(client, 'create_products_association', side_effect=Exception("Create failed")):
            result_json = await tool(product_id=100)
            result = json.loads(result_json)
            
            assert result["success"] is False
            assert "error" in result
    
    @pytest.mark.asyncio
    async def test_update_products_association_exception(self, mock_mcp, mock_client_factory, client):
        """Test update_products_association with client exception."""
        register_products_association_tools_lazy(mock_mcp, mock_client_factory)
        tool = mock_mcp.tools["update_products_association"]
        
        with patch.object(client, 'update_products_association', side_effect=Exception("Update failed")):
            result_json = await tool(association_id=1, quantity=5)
            result = json.loads(result_json)
            
            assert result["success"] is False
            assert "error" in result
    
    @pytest.mark.asyncio
    async def test_delete_products_association_exception(self, mock_mcp, mock_client_factory, client):
        """Test delete_products_association with client exception."""
        register_products_association_tools_lazy(mock_mcp, mock_client_factory)
        tool = mock_mcp.tools["delete_products_association"]
        
        with patch.object(client, 'delete_products_association', side_effect=Exception("Delete failed")):
            result_json = await tool(association_id=1)
            result = json.loads(result_json)
            
            assert result["success"] is False
            assert "error" in result


# ============================================================================
# Association Tests (contact, company, deal)
# ============================================================================

class TestProductsAssociationLinking:
    """Test product associations with contact, company, and deal."""
    
    @pytest.mark.asyncio
    async def test_create_association_with_deal(self, mock_mcp, mock_client_factory, client, mock_product_association_create_response):
        """Test create_products_association with crm_deal_id."""
        register_products_association_tools_lazy(mock_mcp, mock_client_factory)
        tool = mock_mcp.tools["create_products_association"]
        
        with patch.object(client, 'create_products_association', return_value=mock_product_association_create_response) as mock:
            await tool(product_id=100, crm_deal_id=789)
            assoc_data = mock.call_args.kwargs["association_data"]
            assert assoc_data["product_id"] == 100
            assert assoc_data["crm_deal_id"] == 789
    
    @pytest.mark.asyncio
    async def test_create_association_with_contact(self, mock_mcp, mock_client_factory, client, mock_product_association_create_response):
        """Test create_products_association with crm_lead_id."""
        register_products_association_tools_lazy(mock_mcp, mock_client_factory)
        tool = mock_mcp.tools["create_products_association"]
        
        with patch.object(client, 'create_products_association', return_value=mock_product_association_create_response) as mock:
            await tool(product_id=100, crm_lead_id=123)
            assoc_data = mock.call_args.kwargs["association_data"]
            assert assoc_data["crm_lead_id"] == 123
    
    @pytest.mark.asyncio
    async def test_create_association_with_company(self, mock_mcp, mock_client_factory, client, mock_product_association_create_response):
        """Test create_products_association with crm_company_id."""
        register_products_association_tools_lazy(mock_mcp, mock_client_factory)
        tool = mock_mcp.tools["create_products_association"]
        
        with patch.object(client, 'create_products_association', return_value=mock_product_association_create_response) as mock:
            await tool(product_id=100, crm_company_id=456)
            assoc_data = mock.call_args.kwargs["association_data"]
            assert assoc_data["crm_company_id"] == 456
    
    @pytest.mark.asyncio
    async def test_create_association_with_quantity_and_price(self, mock_mcp, mock_client_factory, client, mock_product_association_create_response):
        """Test create_products_association with quantity and price."""
        register_products_association_tools_lazy(mock_mcp, mock_client_factory)
        tool = mock_mcp.tools["create_products_association"]
        
        with patch.object(client, 'create_products_association', return_value=mock_product_association_create_response) as mock:
            await tool(product_id=100, quantity=10, price=99.99)
            assoc_data = mock.call_args.kwargs["association_data"]
            assert assoc_data["quantity"] == 10
            assert assoc_data["price"] == 99.99
    
    @pytest.mark.asyncio
    async def test_create_association_with_zero_price(self, mock_mcp, mock_client_factory, client, mock_product_association_create_response):
        """Test create_products_association with price=0."""
        register_products_association_tools_lazy(mock_mcp, mock_client_factory)
        tool = mock_mcp.tools["create_products_association"]
        
        with patch.object(client, 'create_products_association', return_value=mock_product_association_create_response) as mock:
            await tool(product_id=100, price=0.0)
            assoc_data = mock.call_args.kwargs["association_data"]
            assert assoc_data["price"] == 0.0


# ============================================================================
# Update Tests
# ============================================================================

class TestUpdateProductsAssociationComprehensive:
    """Comprehensive tests for update_products_association."""
    
    @pytest.mark.asyncio
    async def test_update_association_quantity_only(self, mock_mcp, mock_client_factory, client, mock_product_association_update_response):
        """Test update_products_association with only quantity."""
        register_products_association_tools_lazy(mock_mcp, mock_client_factory)
        tool = mock_mcp.tools["update_products_association"]
        
        with patch.object(client, 'update_products_association', return_value=mock_product_association_update_response) as mock:
            await tool(association_id=1, quantity=20)
            assoc_data = mock.call_args.kwargs["association_data"]
            assert "quantity" in assoc_data
            assert "price" not in assoc_data
    
    @pytest.mark.asyncio
    async def test_update_association_price_only(self, mock_mcp, mock_client_factory, client, mock_product_association_update_response):
        """Test update_products_association with only price."""
        register_products_association_tools_lazy(mock_mcp, mock_client_factory)
        tool = mock_mcp.tools["update_products_association"]
        
        with patch.object(client, 'update_products_association', return_value=mock_product_association_update_response) as mock:
            await tool(association_id=1, price=149.99)
            assoc_data = mock.call_args.kwargs["association_data"]
            assert "price" in assoc_data
            assert "quantity" not in assoc_data
    
    @pytest.mark.asyncio
    async def test_update_association_both_fields(self, mock_mcp, mock_client_factory, client, mock_product_association_update_response):
        """Test update_products_association with both quantity and price."""
        register_products_association_tools_lazy(mock_mcp, mock_client_factory)
        tool = mock_mcp.tools["update_products_association"]
        
        with patch.object(client, 'update_products_association', return_value=mock_product_association_update_response) as mock:
            await tool(association_id=1, quantity=30, price=199.99)
            assoc_data = mock.call_args.kwargs["association_data"]
            assert "quantity" in assoc_data
            assert "price" in assoc_data
    
    @pytest.mark.asyncio
    async def test_update_association_with_zero_price(self, mock_mcp, mock_client_factory, client, mock_product_association_update_response):
        """Test update_products_association with price=0."""
        register_products_association_tools_lazy(mock_mcp, mock_client_factory)
        tool = mock_mcp.tools["update_products_association"]
        
        with patch.object(client, 'update_products_association', return_value=mock_product_association_update_response) as mock:
            await tool(association_id=1, price=0.0)
            assoc_data = mock.call_args.kwargs["association_data"]
            assert assoc_data["price"] == 0.0


# ============================================================================
# Pagination Tests
# ============================================================================

class TestProductsAssociationToolsPagination:
    """Test pagination parameters."""
    
    @pytest.mark.asyncio
    async def test_list_products_associations_with_pagination(self, mock_mcp, mock_client_factory, client, mock_product_association_list_response):
        """Test list_products_associations with pagination parameters."""
        register_products_association_tools_lazy(mock_mcp, mock_client_factory)
        tool = mock_mcp.tools["list_products_associations"]
        
        with patch.object(client, 'list_products_associations', return_value=mock_product_association_list_response) as mock:
            await tool(page=2, per_page=50)
            assert mock.call_args.kwargs["page"] == 2
            assert mock.call_args.kwargs["per_page"] == 50
    
    @pytest.mark.asyncio
    async def test_list_products_associations_default_pagination(self, mock_mcp, mock_client_factory, client, mock_product_association_list_response):
        """Test list_products_associations with default pagination."""
        register_products_association_tools_lazy(mock_mcp, mock_client_factory)
        tool = mock_mcp.tools["list_products_associations"]
        
        with patch.object(client, 'list_products_associations', return_value=mock_product_association_list_response) as mock:
            await tool()
            assert mock.call_args.kwargs["page"] == 1
            assert mock.call_args.kwargs["per_page"] == 25
