"""Comprehensive test suite for notes tools."""

import pytest
import json
from unittest.mock import patch
from qontak_mcp.tools.notes import register_note_tools_lazy, register_note_tools


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

class TestNoteToolsBasicInvocation:
    """Test basic invocation of all note tools."""
    
    @pytest.mark.asyncio
    async def test_list_notes_basic(self, mock_mcp, mock_client_factory, client, mock_note_list_response):
        """Test list_notes basic invocation."""
        register_note_tools_lazy(mock_mcp, mock_client_factory)
        tool = mock_mcp.tools["list_notes"]
        
        with patch.object(client, 'list_notes', return_value=mock_note_list_response):
            result_json = await tool()
            result = json.loads(result_json)
            
            assert result["success"] is True
            assert "data" in result
    
    @pytest.mark.asyncio
    async def test_get_note_basic(self, mock_mcp, mock_client_factory, client, mock_note_get_response):
        """Test get_note basic invocation."""
        register_note_tools_lazy(mock_mcp, mock_client_factory)
        tool = mock_mcp.tools["get_note"]
        
        with patch.object(client, 'get_note', return_value=mock_note_get_response):
            result_json = await tool(note_id=1)
            result = json.loads(result_json)
            
            assert result["success"] is True
    
    @pytest.mark.asyncio
    async def test_create_note_basic(self, mock_mcp, mock_client_factory, client, mock_note_create_response):
        """Test create_note basic invocation."""
        register_note_tools_lazy(mock_mcp, mock_client_factory)
        tool = mock_mcp.tools["create_note"]
        
        with patch.object(client, 'create_note', return_value=mock_note_create_response):
            result_json = await tool(title="Test Note", content="Test content")
            result = json.loads(result_json)
            
            assert result["success"] is True
    
    @pytest.mark.asyncio
    async def test_update_note_basic(self, mock_mcp, mock_client_factory, client, mock_note_update_response):
        """Test update_note basic invocation."""
        register_note_tools_lazy(mock_mcp, mock_client_factory)
        tool = mock_mcp.tools["update_note"]
        
        with patch.object(client, 'update_note', return_value=mock_note_update_response):
            result_json = await tool(note_id=1, title="Updated")
            result = json.loads(result_json)
            
            assert result["success"] is True
    
    @pytest.mark.asyncio
    async def test_delete_note_basic(self, mock_mcp, mock_client_factory, client, mock_note_delete_response):
        """Test delete_note basic invocation."""
        register_note_tools_lazy(mock_mcp, mock_client_factory)
        tool = mock_mcp.tools["delete_note"]
        
        with patch.object(client, 'delete_note', return_value=mock_note_delete_response):
            result_json = await tool(note_id=1)
            result = json.loads(result_json)
            
            assert result["success"] is True


# ============================================================================
# Registration Tests
# ============================================================================

class TestNoteToolsRegisterWrapper:
    """Test tool registration."""
    
    @pytest.mark.asyncio
    async def test_all_tools_registered(self, mock_mcp, mock_client_factory):
        """Test that all 5 note tools are registered."""
        register_note_tools_lazy(mock_mcp, mock_client_factory)
        
        expected_tools = [
            "list_notes",
            "get_note",
            "create_note",
            "update_note",
            "delete_note",
        ]
        
        assert len(mock_mcp.tools) == 5
        for tool_name in expected_tools:
            assert tool_name in mock_mcp.tools
    
    @pytest.mark.asyncio
    async def test_register_note_tools_non_lazy_wrapper(self, mock_mcp, client):
        """Test the non-lazy register_note_tools wrapper function."""
        register_note_tools(mock_mcp, client)
        
        assert "list_notes" in mock_mcp.tools
        assert len(mock_mcp.tools) == 5


# ============================================================================
# Multi-tenant (user_id) Tests
# ============================================================================

class TestNoteToolsWithUserId:
    """Test tools with user_id parameter."""
    
    @pytest.mark.asyncio
    async def test_list_notes_with_user_id(self, mock_mcp, mock_client_factory, client, mock_note_list_response):
        """Test list_notes passes user_id correctly."""
        register_note_tools_lazy(mock_mcp, mock_client_factory)
        tool = mock_mcp.tools["list_notes"]
        
        with patch.object(client, 'list_notes', return_value=mock_note_list_response) as mock:
            await tool(user_id="tenant123")
            assert mock.call_args.kwargs["user_id"] == "tenant123"
    
    @pytest.mark.asyncio
    async def test_get_note_with_user_id(self, mock_mcp, mock_client_factory, client, mock_note_get_response):
        """Test get_note passes user_id correctly."""
        register_note_tools_lazy(mock_mcp, mock_client_factory)
        tool = mock_mcp.tools["get_note"]
        
        with patch.object(client, 'get_note', return_value=mock_note_get_response) as mock:
            await tool(note_id=1, user_id="tenant123")
            assert mock.call_args.kwargs["user_id"] == "tenant123"
    
    @pytest.mark.asyncio
    async def test_create_note_with_user_id(self, mock_mcp, mock_client_factory, client, mock_note_create_response):
        """Test create_note passes user_id correctly."""
        register_note_tools_lazy(mock_mcp, mock_client_factory)
        tool = mock_mcp.tools["create_note"]
        
        with patch.object(client, 'create_note', return_value=mock_note_create_response) as mock:
            await tool(title="Test", content="Content", user_id="tenant123")
            assert mock.call_args.kwargs["user_id"] == "tenant123"


# ============================================================================
# Validation Error Tests
# ============================================================================

class TestNoteToolsValidationErrors:
    """Test Pydantic validation error handling."""
    
    @pytest.mark.asyncio
    async def test_list_notes_invalid_page(self, mock_mcp, mock_client_factory, client):
        """Test list_notes with invalid page number."""
        register_note_tools_lazy(mock_mcp, mock_client_factory)
        tool = mock_mcp.tools["list_notes"]
        
        result_json = await tool(page=-1)
        result = json.loads(result_json)
        
        assert result["success"] is False
        assert "error" in result
    
    @pytest.mark.asyncio
    async def test_list_notes_invalid_per_page(self, mock_mcp, mock_client_factory, client):
        """Test list_notes with invalid per_page."""
        register_note_tools_lazy(mock_mcp, mock_client_factory)
        tool = mock_mcp.tools["list_notes"]
        
        result_json = await tool(per_page=0)
        result = json.loads(result_json)
        
        assert result["success"] is False
        assert "error" in result
    
    @pytest.mark.asyncio
    async def test_create_note_empty_title(self, mock_mcp, mock_client_factory, client):
        """Test create_note with empty title."""
        register_note_tools_lazy(mock_mcp, mock_client_factory)
        tool = mock_mcp.tools["create_note"]
        
        result_json = await tool(title="", content="Test")
        result = json.loads(result_json)
        
        assert result["success"] is False
        assert "error" in result
    
    @pytest.mark.asyncio
    async def test_create_note_empty_content(self, mock_mcp, mock_client_factory, client):
        """Test create_note with empty content."""
        register_note_tools_lazy(mock_mcp, mock_client_factory)
        tool = mock_mcp.tools["create_note"]
        
        result_json = await tool(title="Test", content="")
        result = json.loads(result_json)
        
        assert result["success"] is False
        assert "error" in result


# ============================================================================
# Client Exception Tests
# ============================================================================

class TestNoteToolsClientExceptions:
    """Test client exception handling."""
    
    @pytest.mark.asyncio
    async def test_list_notes_exception(self, mock_mcp, mock_client_factory, client):
        """Test list_notes with client exception."""
        register_note_tools_lazy(mock_mcp, mock_client_factory)
        tool = mock_mcp.tools["list_notes"]
        
        with patch.object(client, 'list_notes', side_effect=Exception("Network error")):
            result_json = await tool()
            result = json.loads(result_json)
            
            assert result["success"] is False
            assert "error" in result
    
    @pytest.mark.asyncio
    async def test_get_note_exception(self, mock_mcp, mock_client_factory, client):
        """Test get_note with client exception."""
        register_note_tools_lazy(mock_mcp, mock_client_factory)
        tool = mock_mcp.tools["get_note"]
        
        with patch.object(client, 'get_note', side_effect=Exception("Not found")):
            result_json = await tool(note_id=1)
            result = json.loads(result_json)
            
            assert result["success"] is False
            assert "error" in result
    
    @pytest.mark.asyncio
    async def test_create_note_exception(self, mock_mcp, mock_client_factory, client):
        """Test create_note with client exception."""
        register_note_tools_lazy(mock_mcp, mock_client_factory)
        tool = mock_mcp.tools["create_note"]
        
        with patch.object(client, 'create_note', side_effect=Exception("Create failed")):
            result_json = await tool(title="Test", content="Content")
            result = json.loads(result_json)
            
            assert result["success"] is False
            assert "error" in result
    
    @pytest.mark.asyncio
    async def test_update_note_exception(self, mock_mcp, mock_client_factory, client):
        """Test update_note with client exception."""
        register_note_tools_lazy(mock_mcp, mock_client_factory)
        tool = mock_mcp.tools["update_note"]
        
        with patch.object(client, 'update_note', side_effect=Exception("Update failed")):
            result_json = await tool(note_id=1, title="Test")
            result = json.loads(result_json)
            
            assert result["success"] is False
            assert "error" in result
    
    @pytest.mark.asyncio
    async def test_delete_note_exception(self, mock_mcp, mock_client_factory, client):
        """Test delete_note with client exception."""
        register_note_tools_lazy(mock_mcp, mock_client_factory)
        tool = mock_mcp.tools["delete_note"]
        
        with patch.object(client, 'delete_note', side_effect=Exception("Delete failed")):
            result_json = await tool(note_id=1)
            result = json.loads(result_json)
            
            assert result["success"] is False
            assert "error" in result


# ============================================================================
# Association Tests (contact, company, deal)
# ============================================================================

class TestNoteAssociations:
    """Test note associations with contact, company, and deal."""
    
    @pytest.mark.asyncio
    async def test_create_note_with_contact(self, mock_mcp, mock_client_factory, client, mock_note_create_response):
        """Test create_note with crm_lead_id."""
        register_note_tools_lazy(mock_mcp, mock_client_factory)
        tool = mock_mcp.tools["create_note"]
        
        with patch.object(client, 'create_note', return_value=mock_note_create_response) as mock:
            await tool(title="Test", content="Content", crm_lead_id=123)
            note_data = mock.call_args.kwargs["note_data"]
            assert note_data["crm_lead_id"] == 123
    
    @pytest.mark.asyncio
    async def test_create_note_with_company(self, mock_mcp, mock_client_factory, client, mock_note_create_response):
        """Test create_note with crm_company_id."""
        register_note_tools_lazy(mock_mcp, mock_client_factory)
        tool = mock_mcp.tools["create_note"]
        
        with patch.object(client, 'create_note', return_value=mock_note_create_response) as mock:
            await tool(title="Test", content="Content", crm_company_id=456)
            note_data = mock.call_args.kwargs["note_data"]
            assert note_data["crm_company_id"] == 456
    
    @pytest.mark.asyncio
    async def test_create_note_with_deal(self, mock_mcp, mock_client_factory, client, mock_note_create_response):
        """Test create_note with crm_deal_id."""
        register_note_tools_lazy(mock_mcp, mock_client_factory)
        tool = mock_mcp.tools["create_note"]
        
        with patch.object(client, 'create_note', return_value=mock_note_create_response) as mock:
            await tool(title="Test", content="Content", crm_deal_id=789)
            note_data = mock.call_args.kwargs["note_data"]
            assert note_data["crm_deal_id"] == 789
    
    @pytest.mark.asyncio
    async def test_create_note_with_all_associations(self, mock_mcp, mock_client_factory, client, mock_note_create_response):
        """Test create_note with all associations."""
        register_note_tools_lazy(mock_mcp, mock_client_factory)
        tool = mock_mcp.tools["create_note"]
        
        with patch.object(client, 'create_note', return_value=mock_note_create_response) as mock:
            await tool(
                title="Test",
                content="Content",
                crm_lead_id=123,
                crm_company_id=456,
                crm_deal_id=789
            )
            note_data = mock.call_args.kwargs["note_data"]
            assert note_data["crm_lead_id"] == 123
            assert note_data["crm_company_id"] == 456
            assert note_data["crm_deal_id"] == 789
    
    @pytest.mark.asyncio
    async def test_list_notes_filter_by_contact(self, mock_mcp, mock_client_factory, client, mock_note_list_response):
        """Test list_notes filtering by crm_lead_id."""
        register_note_tools_lazy(mock_mcp, mock_client_factory)
        tool = mock_mcp.tools["list_notes"]
        
        with patch.object(client, 'list_notes', return_value=mock_note_list_response) as mock:
            await tool(crm_lead_id=123)
            assert mock.call_args.kwargs["crm_lead_id"] == 123
    
    @pytest.mark.asyncio
    async def test_list_notes_filter_by_company(self, mock_mcp, mock_client_factory, client, mock_note_list_response):
        """Test list_notes filtering by crm_company_id."""
        register_note_tools_lazy(mock_mcp, mock_client_factory)
        tool = mock_mcp.tools["list_notes"]
        
        with patch.object(client, 'list_notes', return_value=mock_note_list_response) as mock:
            await tool(crm_company_id=456)
            assert mock.call_args.kwargs["crm_company_id"] == 456
    
    @pytest.mark.asyncio
    async def test_list_notes_filter_by_deal(self, mock_mcp, mock_client_factory, client, mock_note_list_response):
        """Test list_notes filtering by crm_deal_id."""
        register_note_tools_lazy(mock_mcp, mock_client_factory)
        tool = mock_mcp.tools["list_notes"]
        
        with patch.object(client, 'list_notes', return_value=mock_note_list_response) as mock:
            await tool(crm_deal_id=789)
            assert mock.call_args.kwargs["crm_deal_id"] == 789


# ============================================================================
# Update Tests
# ============================================================================

class TestUpdateNoteComprehensive:
    """Comprehensive tests for update_note."""
    
    @pytest.mark.asyncio
    async def test_update_note_title_only(self, mock_mcp, mock_client_factory, client, mock_note_update_response):
        """Test update_note with only title."""
        register_note_tools_lazy(mock_mcp, mock_client_factory)
        tool = mock_mcp.tools["update_note"]
        
        with patch.object(client, 'update_note', return_value=mock_note_update_response) as mock:
            await tool(note_id=1, title="New Title")
            note_data = mock.call_args.kwargs["note_data"]
            assert "title" in note_data
            assert "content" not in note_data
    
    @pytest.mark.asyncio
    async def test_update_note_content_only(self, mock_mcp, mock_client_factory, client, mock_note_update_response):
        """Test update_note with only content."""
        register_note_tools_lazy(mock_mcp, mock_client_factory)
        tool = mock_mcp.tools["update_note"]
        
        with patch.object(client, 'update_note', return_value=mock_note_update_response) as mock:
            await tool(note_id=1, content="New Content")
            note_data = mock.call_args.kwargs["note_data"]
            assert "content" in note_data
            assert "title" not in note_data
    
    @pytest.mark.asyncio
    async def test_update_note_both_fields(self, mock_mcp, mock_client_factory, client, mock_note_update_response):
        """Test update_note with both title and content."""
        register_note_tools_lazy(mock_mcp, mock_client_factory)
        tool = mock_mcp.tools["update_note"]
        
        with patch.object(client, 'update_note', return_value=mock_note_update_response) as mock:
            await tool(note_id=1, title="New Title", content="New Content")
            note_data = mock.call_args.kwargs["note_data"]
            assert "title" in note_data
            assert "content" in note_data


# ============================================================================
# Pagination Tests
# ============================================================================

class TestNoteToolsPagination:
    """Test pagination parameters."""
    
    @pytest.mark.asyncio
    async def test_list_notes_with_pagination(self, mock_mcp, mock_client_factory, client, mock_note_list_response):
        """Test list_notes with pagination parameters."""
        register_note_tools_lazy(mock_mcp, mock_client_factory)
        tool = mock_mcp.tools["list_notes"]
        
        with patch.object(client, 'list_notes', return_value=mock_note_list_response) as mock:
            await tool(page=2, per_page=50)
            assert mock.call_args.kwargs["page"] == 2
            assert mock.call_args.kwargs["per_page"] == 50
    
    @pytest.mark.asyncio
    async def test_list_notes_default_pagination(self, mock_mcp, mock_client_factory, client, mock_note_list_response):
        """Test list_notes with default pagination."""
        register_note_tools_lazy(mock_mcp, mock_client_factory)
        tool = mock_mcp.tools["list_notes"]
        
        with patch.object(client, 'list_notes', return_value=mock_note_list_response) as mock:
            await tool()
            assert mock.call_args.kwargs["page"] == 1
            assert mock.call_args.kwargs["per_page"] == 25
