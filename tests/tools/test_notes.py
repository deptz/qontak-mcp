import pytest
import json
from unittest.mock import patch
from qontak_mcp.tools.notes import register_note_tools_lazy

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

class TestNotesTools:
    @pytest.mark.asyncio
    async def test_tools_registered(self, mock_mcp, mock_client_factory):
        """Test that notes tools are registered."""
        register_note_tools_lazy(mock_mcp, mock_client_factory)
        
        expected_tools = [
            "list_notes",
            "get_note",
            "create_note",
            "update_note",
            "delete_note"
        ]
        
        for tool_name in expected_tools:
            assert tool_name in mock_mcp.tools, f"Tool {{tool_name}} not registered"

    @pytest.mark.asyncio
    async def test_list_notes(self, mock_mcp, mock_client_factory, client):
        """Test list_notes tool."""
        register_note_tools_lazy(mock_mcp, mock_client_factory)
        tool = mock_mcp.tools["list_notes"]
        
        with patch.object(client, 'list_notes', return_value={"success": True, "data": {"data": []}}):
            result_json = await tool()
            result = json.loads(result_json)
        
        assert result["success"] is True
