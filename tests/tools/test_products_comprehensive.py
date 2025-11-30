"""Comprehensive test suite for products tools."""

import pytest
import json
from unittest.mock import patch
from qontak_mcp.tools.products import register_product_tools_lazy, register_product_tools


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

class TestProductToolsBasicInvocation:
    """Test basic invocation of all product tools."""
    
    @pytest.mark.asyncio
    async def test_list_products_basic(self, mock_mcp, mock_client_factory, client, mock_product_list_response):
        """Test list_products basic invocation."""
        register_product_tools_lazy(mock_mcp, mock_client_factory)
        tool = mock_mcp.tools["list_products"]
        
        with patch.object(client, 'list_products', return_value=mock_product_list_response):
            result_json = await tool()
            result = json.loads(result_json)
            
            assert result["success"] is True
            assert "data" in result
    
    @pytest.mark.asyncio
    async def test_get_product_basic(self, mock_mcp, mock_client_factory, client, mock_product_get_response):
        """Test get_product basic invocation."""
        register_product_tools_lazy(mock_mcp, mock_client_factory)
        tool = mock_mcp.tools["get_product"]
        
        with patch.object(client, 'get_product', return_value=mock_product_get_response):
            result_json = await tool(product_id=1)
            result = json.loads(result_json)
            
            assert result["success"] is True
    
    @pytest.mark.asyncio
    async def test_create_product_basic(self, mock_mcp, mock_client_factory, client, mock_product_create_response):
        """Test create_product basic invocation."""
        register_product_tools_lazy(mock_mcp, mock_client_factory)
        tool = mock_mcp.tools["create_product"]
        
        with patch.object(client, 'create_product', return_value=mock_product_create_response):
            result_json = await tool(name="Test Product")
            result = json.loads(result_json)
            
            assert result["success"] is True
    
    @pytest.mark.asyncio
    async def test_update_product_basic(self, mock_mcp, mock_client_factory, client, mock_product_update_response):
        """Test update_product basic invocation."""
        register_product_tools_lazy(mock_mcp, mock_client_factory)
        tool = mock_mcp.tools["update_product"]
        
        with patch.object(client, 'update_product', return_value=mock_product_update_response):
            result_json = await tool(product_id=1, name="Updated Product")
            result = json.loads(result_json)
            
            assert result["success"] is True
    
    @pytest.mark.asyncio
    async def test_delete_product_basic(self, mock_mcp, mock_client_factory, client, mock_product_delete_response):
        """Test delete_product basic invocation."""
        register_product_tools_lazy(mock_mcp, mock_client_factory)
        tool = mock_mcp.tools["delete_product"]
        
        with patch.object(client, 'delete_product', return_value=mock_product_delete_response):
            result_json = await tool(product_id=1)
            result = json.loads(result_json)
            
            assert result["success"] is True


# ============================================================================
# Registration Tests
# ============================================================================

class TestProductToolsRegisterWrapper:
    """Test tool registration."""
    
    @pytest.mark.asyncio
    async def test_all_tools_registered(self, mock_mcp, mock_client_factory):
        """Test that all 5 product tools are registered."""
        register_product_tools_lazy(mock_mcp, mock_client_factory)
        
        expected_tools = [
            "list_products",
            "get_product",
            "create_product",
            "update_product",
            "delete_product",
        ]
        
        assert len(mock_mcp.tools) == 5
        for tool_name in expected_tools:
            assert tool_name in mock_mcp.tools
    
    @pytest.mark.asyncio
    async def test_register_product_tools_non_lazy_wrapper(self, mock_mcp, client):
        """Test the non-lazy register_product_tools wrapper function."""
        register_product_tools(mock_mcp, client)
        
        assert "list_products" in mock_mcp.tools
        assert len(mock_mcp.tools) == 5


# ============================================================================
# Multi-tenant (user_id) Tests
# ============================================================================

class TestProductToolsWithUserId:
    """Test tools with user_id parameter."""
    
    @pytest.mark.asyncio
    async def test_list_products_with_user_id(self, mock_mcp, mock_client_factory, client, mock_product_list_response):
        """Test list_products passes user_id correctly."""
        register_product_tools_lazy(mock_mcp, mock_client_factory)
        tool = mock_mcp.tools["list_products"]
        
        with patch.object(client, 'list_products', return_value=mock_product_list_response) as mock:
            await tool(user_id="tenant123")
            assert mock.call_args.kwargs["user_id"] == "tenant123"
    
    @pytest.mark.asyncio
    async def test_get_product_with_user_id(self, mock_mcp, mock_client_factory, client, mock_product_get_response):
        """Test get_product passes user_id correctly."""
        register_product_tools_lazy(mock_mcp, mock_client_factory)
        tool = mock_mcp.tools["get_product"]
        
        with patch.object(client, 'get_product', return_value=mock_product_get_response) as mock:
            await tool(product_id=1, user_id="tenant123")
            assert mock.call_args.kwargs["user_id"] == "tenant123"
    
    @pytest.mark.asyncio
    async def test_create_product_with_user_id(self, mock_mcp, mock_client_factory, client, mock_product_create_response):
        """Test create_product passes user_id correctly."""
        register_product_tools_lazy(mock_mcp, mock_client_factory)
        tool = mock_mcp.tools["create_product"]
        
        with patch.object(client, 'create_product', return_value=mock_product_create_response) as mock:
            await tool(name="Test", user_id="tenant123")
            assert mock.call_args.kwargs["user_id"] == "tenant123"


# ============================================================================
# Validation Error Tests
# ============================================================================

class TestProductToolsValidationErrors:
    """Test Pydantic validation error handling."""
    
    @pytest.mark.asyncio
    async def test_list_products_invalid_page(self, mock_mcp, mock_client_factory, client):
        """Test list_products with invalid page number."""
        register_product_tools_lazy(mock_mcp, mock_client_factory)
        tool = mock_mcp.tools["list_products"]
        
        result_json = await tool(page=-1)
        result = json.loads(result_json)
        
        assert result["success"] is False
        assert "error" in result
    
    @pytest.mark.asyncio
    async def test_list_products_invalid_per_page(self, mock_mcp, mock_client_factory, client):
        """Test list_products with invalid per_page."""
        register_product_tools_lazy(mock_mcp, mock_client_factory)
        tool = mock_mcp.tools["list_products"]
        
        result_json = await tool(per_page=0)
        result = json.loads(result_json)
        
        assert result["success"] is False
        assert "error" in result
    
    @pytest.mark.asyncio
    async def test_create_product_empty_name(self, mock_mcp, mock_client_factory, client):
        """Test create_product with empty name."""
        register_product_tools_lazy(mock_mcp, mock_client_factory)
        tool = mock_mcp.tools["create_product"]
        
        result_json = await tool(name="")
        result = json.loads(result_json)
        
        assert result["success"] is False
        assert "error" in result
    
    @pytest.mark.asyncio
    async def test_create_product_negative_price(self, mock_mcp, mock_client_factory, client):
        """Test create_product with negative price."""
        register_product_tools_lazy(mock_mcp, mock_client_factory)
        tool = mock_mcp.tools["create_product"]
        
        result_json = await tool(name="Test", price=-10.0)
        result = json.loads(result_json)
        
        assert result["success"] is False
        assert "error" in result


# ============================================================================
# Client Exception Tests
# ============================================================================

class TestProductToolsClientExceptions:
    """Test client exception handling."""
    
    @pytest.mark.asyncio
    async def test_list_products_exception(self, mock_mcp, mock_client_factory, client):
        """Test list_products with client exception."""
        register_product_tools_lazy(mock_mcp, mock_client_factory)
        tool = mock_mcp.tools["list_products"]
        
        with patch.object(client, 'list_products', side_effect=Exception("Network error")):
            result_json = await tool()
            result = json.loads(result_json)
            
            assert result["success"] is False
            assert "error" in result
    
    @pytest.mark.asyncio
    async def test_get_product_exception(self, mock_mcp, mock_client_factory, client):
        """Test get_product with client exception."""
        register_product_tools_lazy(mock_mcp, mock_client_factory)
        tool = mock_mcp.tools["get_product"]
        
        with patch.object(client, 'get_product', side_effect=Exception("Not found")):
            result_json = await tool(product_id=1)
            result = json.loads(result_json)
            
            assert result["success"] is False
            assert "error" in result
    
    @pytest.mark.asyncio
    async def test_create_product_exception(self, mock_mcp, mock_client_factory, client):
        """Test create_product with client exception."""
        register_product_tools_lazy(mock_mcp, mock_client_factory)
        tool = mock_mcp.tools["create_product"]
        
        with patch.object(client, 'create_product', side_effect=Exception("Create failed")):
            result_json = await tool(name="Test")
            result = json.loads(result_json)
            
            assert result["success"] is False
            assert "error" in result
    
    @pytest.mark.asyncio
    async def test_update_product_exception(self, mock_mcp, mock_client_factory, client):
        """Test update_product with client exception."""
        register_product_tools_lazy(mock_mcp, mock_client_factory)
        tool = mock_mcp.tools["update_product"]
        
        with patch.object(client, 'update_product', side_effect=Exception("Update failed")):
            result_json = await tool(product_id=1, name="Test")
            result = json.loads(result_json)
            
            assert result["success"] is False
            assert "error" in result
    
    @pytest.mark.asyncio
    async def test_delete_product_exception(self, mock_mcp, mock_client_factory, client):
        """Test delete_product with client exception."""
        register_product_tools_lazy(mock_mcp, mock_client_factory)
        tool = mock_mcp.tools["delete_product"]
        
        with patch.object(client, 'delete_product', side_effect=Exception("Delete failed")):
            result_json = await tool(product_id=1)
            result = json.loads(result_json)
            
            assert result["success"] is False
            assert "error" in result


# ============================================================================
# Comprehensive Parameter Tests
# ============================================================================

class TestCreateProductComprehensive:
    """Comprehensive tests for create_product."""
    
    @pytest.mark.asyncio
    async def test_create_product_with_all_fields(self, mock_mcp, mock_client_factory, client, mock_product_create_response):
        """Test create_product with all optional fields."""
        register_product_tools_lazy(mock_mcp, mock_client_factory)
        tool = mock_mcp.tools["create_product"]
        
        with patch.object(client, 'create_product', return_value=mock_product_create_response) as mock:
            await tool(
                name="Test Product",
                price=99.99,
                sku="TEST-SKU-001",
                description="Test description",
                category="Electronics"
            )
            product_data = mock.call_args.kwargs["product_data"]
            assert product_data["name"] == "Test Product"
            assert product_data["price"] == 99.99
            assert product_data["sku"] == "TEST-SKU-001"
            assert product_data["description"] == "Test description"
            assert product_data["category"] == "Electronics"
    
    @pytest.mark.asyncio
    async def test_create_product_name_only(self, mock_mcp, mock_client_factory, client, mock_product_create_response):
        """Test create_product with only required name field."""
        register_product_tools_lazy(mock_mcp, mock_client_factory)
        tool = mock_mcp.tools["create_product"]
        
        with patch.object(client, 'create_product', return_value=mock_product_create_response) as mock:
            await tool(name="Test Product")
            product_data = mock.call_args.kwargs["product_data"]
            assert product_data == {"name": "Test Product"}
    
    @pytest.mark.asyncio
    async def test_create_product_with_zero_price(self, mock_mcp, mock_client_factory, client, mock_product_create_response):
        """Test create_product with price=0."""
        register_product_tools_lazy(mock_mcp, mock_client_factory)
        tool = mock_mcp.tools["create_product"]
        
        with patch.object(client, 'create_product', return_value=mock_product_create_response) as mock:
            await tool(name="Free Product", price=0.0)
            product_data = mock.call_args.kwargs["product_data"]
            assert product_data["price"] == 0.0


class TestUpdateProductComprehensive:
    """Comprehensive tests for update_product."""
    
    @pytest.mark.asyncio
    async def test_update_product_with_all_fields(self, mock_mcp, mock_client_factory, client, mock_product_update_response):
        """Test update_product with all optional fields."""
        register_product_tools_lazy(mock_mcp, mock_client_factory)
        tool = mock_mcp.tools["update_product"]
        
        with patch.object(client, 'update_product', return_value=mock_product_update_response) as mock:
            await tool(
                product_id=1,
                name="Updated Product",
                price=149.99,
                sku="UPD-SKU-001",
                description="Updated description",
                category="Software"
            )
            product_data = mock.call_args.kwargs["product_data"]
            assert "name" in product_data
            assert "price" in product_data
            assert "sku" in product_data
            assert "description" in product_data
            assert "category" in product_data
    
    @pytest.mark.asyncio
    async def test_update_product_name_only(self, mock_mcp, mock_client_factory, client, mock_product_update_response):
        """Test update_product with only name."""
        register_product_tools_lazy(mock_mcp, mock_client_factory)
        tool = mock_mcp.tools["update_product"]
        
        with patch.object(client, 'update_product', return_value=mock_product_update_response) as mock:
            await tool(product_id=1, name="New Name")
            product_data = mock.call_args.kwargs["product_data"]
            assert product_data == {"name": "New Name"}
    
    @pytest.mark.asyncio
    async def test_update_product_price_only(self, mock_mcp, mock_client_factory, client, mock_product_update_response):
        """Test update_product with only price."""
        register_product_tools_lazy(mock_mcp, mock_client_factory)
        tool = mock_mcp.tools["update_product"]
        
        with patch.object(client, 'update_product', return_value=mock_product_update_response) as mock:
            await tool(product_id=1, price=199.99)
            product_data = mock.call_args.kwargs["product_data"]
            assert product_data == {"price": 199.99}
    
    @pytest.mark.asyncio
    async def test_update_product_with_zero_price(self, mock_mcp, mock_client_factory, client, mock_product_update_response):
        """Test update_product with price=0."""
        register_product_tools_lazy(mock_mcp, mock_client_factory)
        tool = mock_mcp.tools["update_product"]
        
        with patch.object(client, 'update_product', return_value=mock_product_update_response) as mock:
            await tool(product_id=1, price=0.0)
            product_data = mock.call_args.kwargs["product_data"]
            assert product_data["price"] == 0.0


# ============================================================================
# Pagination Tests
# ============================================================================

class TestProductToolsPagination:
    """Test pagination parameters."""
    
    @pytest.mark.asyncio
    async def test_list_products_with_pagination(self, mock_mcp, mock_client_factory, client, mock_product_list_response):
        """Test list_products with pagination parameters."""
        register_product_tools_lazy(mock_mcp, mock_client_factory)
        tool = mock_mcp.tools["list_products"]
        
        with patch.object(client, 'list_products', return_value=mock_product_list_response) as mock:
            await tool(page=2, per_page=50)
            assert mock.call_args.kwargs["page"] == 2
            assert mock.call_args.kwargs["per_page"] == 50
    
    @pytest.mark.asyncio
    async def test_list_products_default_pagination(self, mock_mcp, mock_client_factory, client, mock_product_list_response):
        """Test list_products with default pagination."""
        register_product_tools_lazy(mock_mcp, mock_client_factory)
        tool = mock_mcp.tools["list_products"]
        
        with patch.object(client, 'list_products', return_value=mock_product_list_response) as mock:
            await tool()
            assert mock.call_args.kwargs["page"] == 1
            assert mock.call_args.kwargs["per_page"] == 25
