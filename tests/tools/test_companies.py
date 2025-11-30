import pytest
import json
from unittest.mock import patch
from qontak_mcp.tools.companies import register_company_tools_lazy

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

class TestCompaniesTools:
    @pytest.mark.asyncio
    async def test_tools_registered(self, mock_mcp, mock_client_factory):
        """Test that companies tools are registered."""
        register_company_tools_lazy(mock_mcp, mock_client_factory)
        
        expected_tools = [
            "get_company_template",
            "get_required_fields_for_company",
            "list_companies",
            "get_company",
            "create_company",
            "update_company",
            "delete_company",
            "get_company_timeline"
        ]
        
        for tool_name in expected_tools:
            assert tool_name in mock_mcp.tools, f"Tool {{tool_name}} not registered"

    @pytest.mark.asyncio
    async def test_get_company_template(self, mock_mcp, mock_client_factory, client):
        """Test get_company_template tool."""
        register_company_tools_lazy(mock_mcp, mock_client_factory)
        tool = mock_mcp.tools["get_company_template"]
        
        with patch.object(client, 'get_company_template', return_value={"success": True, "data": {"fields": []}}):
            result_json = await tool()
            result = json.loads(result_json)
        
        assert result["success"] is True
