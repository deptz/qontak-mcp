import pytest
import json
import httpx
from unittest.mock import MagicMock, patch
from qontak_mcp.tools.tasks import register_task_tools_lazy, register_task_tools

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
async def test_list_tasks_tool(mock_mcp, mock_client_factory, client):
    """Test list_tasks tool."""
    register_task_tools_lazy(mock_mcp, mock_client_factory)
    
    tool = mock_mcp.tools["list_tasks"]
    
    with patch.object(client, 'list_tasks', return_value={"success": True, "data": {"data": []}}):
        result_json = await tool(page=1, per_page=10)
        result = json.loads(result_json)
    
    assert result["success"] is True
    assert result["data"] == {"data": []}

@pytest.mark.asyncio
async def test_create_task_tool(mock_mcp, mock_client_factory, client):
    """Test create_task tool."""
    register_task_tools_lazy(mock_mcp, mock_client_factory)
    tool = mock_mcp.tools["create_task"]
    
    with patch.object(client, 'create_task', return_value={"success": True, "data": {"data": {"id": 1}}}):
        result_json = await tool(name="New Task", due_date="2025-12-31")
        result = json.loads(result_json)
    
    assert result["success"] is True
    assert result["data"]["data"]["id"] == 1

@pytest.mark.asyncio
async def test_get_task_tool(mock_mcp, mock_client_factory, client):
    """Test get_task tool."""
    register_task_tools_lazy(mock_mcp, mock_client_factory)
    tool = mock_mcp.tools["get_task"]
    
    with patch.object(client, 'get_task', return_value={"success": True, "data": {"data": {"id": 1, "title": "Task 1"}}}):
        result_json = await tool(task_id=1)
        result = json.loads(result_json)
    
    assert result["success"] is True
    assert result["data"]["data"]["id"] == 1

@pytest.mark.asyncio
async def test_update_task_tool(mock_mcp, mock_client_factory, client):
    """Test update_task tool."""
    register_task_tools_lazy(mock_mcp, mock_client_factory)
    tool = mock_mcp.tools["update_task"]
    
    with patch.object(client, 'update_task', return_value={"success": True, "data": {"data": {"id": 1, "title": "Updated Task"}}}):
        result_json = await tool(task_id=1, name="Updated Task")
        result = json.loads(result_json)
    
    assert result["success"] is True
    assert result["data"]["data"]["title"] == "Updated Task"

@pytest.mark.asyncio
async def test_get_task_template_tool(mock_mcp, mock_client_factory, client):
    """Test get_task_template tool."""
    register_task_tools_lazy(mock_mcp, mock_client_factory)
    tool = mock_mcp.tools["get_task_template"]
    
    with patch.object(client, 'get_task_template', return_value={"success": True, "data": {"data": {"fields": []}}}):
        result_json = await tool()
        result = json.loads(result_json)
    
    assert result["success"] is True
    assert "fields" in result["data"]["data"]

@pytest.mark.asyncio
async def test_list_task_categories_tool(mock_mcp, mock_client_factory, client):
    """Test list_task_categories tool."""
    register_task_tools_lazy(mock_mcp, mock_client_factory)
    tool = mock_mcp.tools["list_task_categories"]
    
    with patch.object(client, 'list_task_categories', return_value={"success": True, "data": {"data": [{"id": 1, "name": "Category 1"}]}}):
        result_json = await tool()
        result = json.loads(result_json)
    
    assert result["success"] is True
    assert len(result["data"]["data"]) > 0

@pytest.mark.asyncio
async def test_create_task_category_tool(mock_mcp, mock_client_factory, client):
    """Test create_task_category tool."""
    register_task_tools_lazy(mock_mcp, mock_client_factory)
    tool = mock_mcp.tools["create_task_category"]
    
    with patch.object(client, 'create_task_category', return_value={"success": True, "data": {"data": {"id": 2, "name": "New Category"}}}):
        result_json = await tool(name="New Category")
        result = json.loads(result_json)
    
    assert result["success"] is True
    assert result["data"]["data"]["name"] == "New Category"


class TestTaskToolsRegisterWrapper:
    """Test the register_task_tools wrapper function."""
    
    @pytest.mark.asyncio
    async def test_register_task_tools_wrapper(self, mock_mcp, client):
        """Test register_task_tools uses lazy registration internally."""
        register_task_tools(mock_mcp, client)
        
        # Should have registered all tools
        assert "list_tasks" in mock_mcp.tools
        assert "get_task" in mock_mcp.tools
        assert "create_task" in mock_mcp.tools
        assert "update_task" in mock_mcp.tools


class TestListTasksToolParameters:
    """Test list_tasks with various parameter combinations."""
    
    @pytest.mark.asyncio
    async def test_list_tasks_with_all_filters(self, mock_mcp, mock_client_factory, client):
        """Test list_tasks with category and user filters."""
        register_task_tools_lazy(mock_mcp, mock_client_factory)
        tool = mock_mcp.tools["list_tasks"]
        
        with patch.object(client, 'list_tasks', return_value={"success": True, "data": {"data": []}}) as mock:
            await tool(page=1, per_page=10, category_id=3, user_id="tenant_123")
            mock.assert_called_once()
            call_kwargs = mock.call_args.kwargs
            assert call_kwargs['category_id'] == 3
            assert call_kwargs['user_id'] == "tenant_123"
    
    @pytest.mark.asyncio
    async def test_list_tasks_with_category_filter(self, mock_mcp, mock_client_factory, client):
        """Test list_tasks with category_id filter."""
        register_task_tools_lazy(mock_mcp, mock_client_factory)
        tool = mock_mcp.tools["list_tasks"]
        
        with patch.object(client, 'list_tasks', return_value={"success": True, "data": {"data": []}}) as mock:
            await tool(page=1, per_page=10, category_id=3)
            mock.assert_called_once()
            call_kwargs = mock.call_args.kwargs
            assert call_kwargs['category_id'] == 3
    
    @pytest.mark.asyncio
    async def test_list_tasks_with_user_id(self, mock_mcp, mock_client_factory, client):
        """Test list_tasks with user_id for multi-tenant."""
        register_task_tools_lazy(mock_mcp, mock_client_factory)
        tool = mock_mcp.tools["list_tasks"]
        
        with patch.object(client, 'list_tasks', return_value={"success": True, "data": {"data": []}}) as mock:
            await tool(page=1, per_page=10, user_id="tenant_123")
            mock.assert_called_once()
            call_kwargs = mock.call_args.kwargs
            assert call_kwargs['user_id'] == "tenant_123"
    
    @pytest.mark.asyncio
    async def test_list_tasks_pydantic_validation_error(self, mock_mcp, mock_client_factory, client):
        """Test list_tasks handles PydanticValidationError."""
        register_task_tools_lazy(mock_mcp, mock_client_factory)
        tool = mock_mcp.tools["list_tasks"]
        
        # Pass invalid page number (negative)
        result_json = await tool(page=-1, per_page=10)
        result = json.loads(result_json)
        
        assert result["success"] is False
        assert "error" in result
    
    @pytest.mark.asyncio
    async def test_list_tasks_client_exception(self, mock_mcp, mock_client_factory, client):
        """Test list_tasks handles client exceptions."""
        register_task_tools_lazy(mock_mcp, mock_client_factory)
        tool = mock_mcp.tools["list_tasks"]
        
        with patch.object(client, 'list_tasks', side_effect=Exception("Network error")):
            result_json = await tool(page=1, per_page=10)
            result = json.loads(result_json)
            
            assert result["success"] is False
            assert "error" in result


class TestCreateTaskToolParameters:
    """Test create_task with various parameter combinations."""
    
    @pytest.mark.asyncio
    async def test_create_task_with_all_optional_fields(self, mock_mcp, mock_client_factory, client):
        """Test create_task with all optional fields."""
        register_task_tools_lazy(mock_mcp, mock_client_factory)
        tool = mock_mcp.tools["create_task"]
        
        with patch.object(client, 'create_task', return_value={"success": True, "data": {"data": {"id": 1}}}) as mock:
            result_json = await tool(
                name="Test Task",
                due_date="2024-12-31",
                category_id=5,
                crm_person_id=100,
                crm_company_id=200,
                crm_deal_id=300,
                priority="high",
                description="Test description",
                additional_fields='[{"id": 123, "name": "field_1", "value": "value1"}]'
            )
            result = json.loads(result_json)
            
            assert result["success"] is True
            call_kwargs = mock.call_args.kwargs
            task_data = call_kwargs['task_data']
            assert task_data['name'] == "Test Task"
            assert task_data['due_date'] == "2024-12-31"
            assert task_data['category_id'] == 5
            assert task_data['crm_person_id'] == 100
            assert task_data['crm_company_id'] == 200
            assert task_data['crm_deal_id'] == 300
            assert task_data['priority'] == "high"
            assert task_data['description'] == "Test description"
            assert task_data['additional_fields'] == [{"id": 123, "name": "field_1", "value": "value1"}]
    
    @pytest.mark.asyncio
    async def test_create_task_invalid_custom_fields_json(self, mock_mcp, mock_client_factory, client):
        """Test create_task with invalid JSON in custom_fields."""
        register_task_tools_lazy(mock_mcp, mock_client_factory)
        tool = mock_mcp.tools["create_task"]
        
        result_json = await tool(
            name="Test Task",
            due_date="2024-12-31",
            additional_fields="not valid json {{"
        )
        result = json.loads(result_json)
        
        assert result["success"] is False
        assert "Invalid JSON format" in result["error"]
    
    @pytest.mark.asyncio
    async def test_create_task_pydantic_validation_error(self, mock_mcp, mock_client_factory, client):
        """Test create_task handles PydanticValidationError."""
        register_task_tools_lazy(mock_mcp, mock_client_factory)
        tool = mock_mcp.tools["create_task"]
        
        # Pass empty name (invalid)
        result_json = await tool(name="", due_date="2024-12-31")
        result = json.loads(result_json)
        
        assert result["success"] is False
        assert "error" in result
    
    @pytest.mark.asyncio
    async def test_create_task_client_exception(self, mock_mcp, mock_client_factory, client):
        """Test create_task handles client exceptions."""
        register_task_tools_lazy(mock_mcp, mock_client_factory)
        tool = mock_mcp.tools["create_task"]
        
        with patch.object(client, 'create_task', side_effect=Exception("Network error")):
            result_json = await tool(name="Test Task", due_date="2024-12-31")
            result = json.loads(result_json)
            
            assert result["success"] is False
            assert "error" in result


class TestUpdateTaskToolParameters:
    """Test update_task with various parameter combinations."""
    
    @pytest.mark.asyncio
    async def test_update_task_with_all_optional_fields(self, mock_mcp, mock_client_factory, client):
        """Test update_task with all optional fields."""
        register_task_tools_lazy(mock_mcp, mock_client_factory)
        tool = mock_mcp.tools["update_task"]
        
        with patch.object(client, 'update_task', return_value={"success": True, "data": {"data": {"id": 1}}}) as mock:
            result_json = await tool(
                task_id=1,
                name="Updated Task",
                due_date="2025-01-15",
                status="completed",
                category_id=7,
                contact_id=100,
                company_id=200,
                deal_id=300,
                priority="high",
                description="Updated description",
                custom_fields='{"field_2": "value2"}'
            )
            result = json.loads(result_json)
            
            assert result["success"] is True
            call_kwargs = mock.call_args.kwargs
            task_data = call_kwargs['task_data']
            assert task_data['name'] == "Updated Task"
            assert task_data['due_date'] == "2025-01-15"
            assert task_data['status'] == "completed"
            assert task_data['category_id'] == 7
            assert task_data['contact_id'] == 100
            assert task_data['company_id'] == 200
            assert task_data['deal_id'] == 300
            assert task_data['priority'] == "high"
            assert task_data['description'] == "Updated description"
            assert task_data['custom_fields'] == {"field_2": "value2"}
    
    @pytest.mark.asyncio
    async def test_update_task_invalid_custom_fields_json(self, mock_mcp, mock_client_factory, client):
        """Test update_task with invalid JSON in custom_fields."""
        register_task_tools_lazy(mock_mcp, mock_client_factory)
        tool = mock_mcp.tools["update_task"]
        
        result_json = await tool(
            task_id=1,
            custom_fields="invalid json here"
        )
        result = json.loads(result_json)
        
        assert result["success"] is False
        assert "Invalid JSON format" in result["error"]
    
    @pytest.mark.asyncio
    async def test_update_task_pydantic_validation_error(self, mock_mcp, mock_client_factory, client):
        """Test update_task handles PydanticValidationError."""
        register_task_tools_lazy(mock_mcp, mock_client_factory)
        tool = mock_mcp.tools["update_task"]
        
        # Pass invalid task_id (negative)
        result_json = await tool(task_id=-1, name="Updated")
        result = json.loads(result_json)
        
        assert result["success"] is False
        assert "error" in result
    
    @pytest.mark.asyncio
    async def test_update_task_client_exception(self, mock_mcp, mock_client_factory, client):
        """Test update_task handles client exceptions."""
        register_task_tools_lazy(mock_mcp, mock_client_factory)
        tool = mock_mcp.tools["update_task"]
        
        with patch.object(client, 'update_task', side_effect=Exception("Timeout")):
            result_json = await tool(task_id=1, name="Test")
            result = json.loads(result_json)
            
            assert result["success"] is False
            assert "error" in result


class TestGetTaskToolParameters:
    """Test get_task with various parameter combinations."""
    
    @pytest.mark.asyncio
    async def test_get_task_with_user_id(self, mock_mcp, mock_client_factory, client):
        """Test get_task with user_id for multi-tenant."""
        register_task_tools_lazy(mock_mcp, mock_client_factory)
        tool = mock_mcp.tools["get_task"]
        
        with patch.object(client, 'get_task', return_value={"success": True, "data": {"data": {"id": 1}}}) as mock:
            await tool(task_id=1, user_id="tenant_456")
            call_kwargs = mock.call_args.kwargs
            assert call_kwargs['user_id'] == "tenant_456"
    
    @pytest.mark.asyncio
    async def test_get_task_pydantic_validation_error(self, mock_mcp, mock_client_factory, client):
        """Test get_task handles PydanticValidationError."""
        register_task_tools_lazy(mock_mcp, mock_client_factory)
        tool = mock_mcp.tools["get_task"]
        
        # Pass invalid task_id (negative)
        result_json = await tool(task_id=-1)
        result = json.loads(result_json)
        
        assert result["success"] is False
        assert "error" in result
    
    @pytest.mark.asyncio
    async def test_get_task_client_exception(self, mock_mcp, mock_client_factory, client):
        """Test get_task handles client exceptions."""
        register_task_tools_lazy(mock_mcp, mock_client_factory)
        tool = mock_mcp.tools["get_task"]
        
        with patch.object(client, 'get_task', side_effect=Exception("Not found")):
            result_json = await tool(task_id=1)
            result = json.loads(result_json)
            
            assert result["success"] is False
            assert "error" in result


class TestGetTaskTemplateToolParameters:
    """Test get_task_template with various parameters."""
    
    @pytest.mark.asyncio
    async def test_get_task_template_with_user_id(self, mock_mcp, mock_client_factory, client):
        """Test get_task_template with user_id for multi-tenant."""
        register_task_tools_lazy(mock_mcp, mock_client_factory)
        tool = mock_mcp.tools["get_task_template"]
        
        with patch.object(client, 'get_task_template', return_value={"success": True, "data": {"data": {"fields": []}}}) as mock:
            await tool(user_id="tenant_789")
            call_kwargs = mock.call_args.kwargs
            assert call_kwargs['user_id'] == "tenant_789"
    
    @pytest.mark.asyncio
    async def test_get_task_template_client_exception(self, mock_mcp, mock_client_factory, client):
        """Test get_task_template handles client exceptions."""
        register_task_tools_lazy(mock_mcp, mock_client_factory)
        tool = mock_mcp.tools["get_task_template"]
        
        with patch.object(client, 'get_task_template', side_effect=Exception("Template error")):
            result_json = await tool()
            result = json.loads(result_json)
            
            assert result["success"] is False
            assert "error" in result


class TestListTaskCategoriesToolParameters:
    """Test list_task_categories with various parameters."""
    
    @pytest.mark.asyncio
    async def test_list_task_categories_with_pagination(self, mock_mcp, mock_client_factory, client):
        """Test list_task_categories with pagination parameters."""
        register_task_tools_lazy(mock_mcp, mock_client_factory)
        tool = mock_mcp.tools["list_task_categories"]
        
        with patch.object(client, 'list_task_categories', return_value={"success": True, "data": {"data": []}}) as mock:
            await tool(page=2, per_page=50, user_id="tenant_abc")
            call_kwargs = mock.call_args.kwargs
            assert call_kwargs['page'] == 2
            assert call_kwargs['per_page'] == 50
            assert call_kwargs['user_id'] == "tenant_abc"
    
    @pytest.mark.asyncio
    async def test_list_task_categories_pydantic_validation_error(self, mock_mcp, mock_client_factory, client):
        """Test list_task_categories handles PydanticValidationError."""
        register_task_tools_lazy(mock_mcp, mock_client_factory)
        tool = mock_mcp.tools["list_task_categories"]
        
        # Pass invalid page (negative)
        result_json = await tool(page=-1)
        result = json.loads(result_json)
        
        assert result["success"] is False
        assert "error" in result
    
    @pytest.mark.asyncio
    async def test_list_task_categories_client_exception(self, mock_mcp, mock_client_factory, client):
        """Test list_task_categories handles client exceptions."""
        register_task_tools_lazy(mock_mcp, mock_client_factory)
        tool = mock_mcp.tools["list_task_categories"]
        
        with patch.object(client, 'list_task_categories', side_effect=Exception("Category error")):
            result_json = await tool()
            result = json.loads(result_json)
            
            assert result["success"] is False
            assert "error" in result


class TestCreateTaskCategoryToolParameters:
    """Test create_task_category with various parameters."""
    
    @pytest.mark.asyncio
    async def test_create_task_category_with_user_id(self, mock_mcp, mock_client_factory, client):
        """Test create_task_category with user_id for multi-tenant."""
        register_task_tools_lazy(mock_mcp, mock_client_factory)
        tool = mock_mcp.tools["create_task_category"]
        
        with patch.object(client, 'create_task_category', return_value={"success": True, "data": {"data": {"id": 1}}}) as mock:
            await tool(name="Test Category", user_id="tenant_xyz")
            call_kwargs = mock.call_args.kwargs
            assert call_kwargs['user_id'] == "tenant_xyz"
    
    @pytest.mark.asyncio
    async def test_create_task_category_pydantic_validation_error(self, mock_mcp, mock_client_factory, client):
        """Test create_task_category handles PydanticValidationError."""
        register_task_tools_lazy(mock_mcp, mock_client_factory)
        tool = mock_mcp.tools["create_task_category"]
        
        # Pass empty name (invalid)
        result_json = await tool(name="")
        result = json.loads(result_json)
        
        assert result["success"] is False
        assert "error" in result
    
    @pytest.mark.asyncio
    async def test_create_task_category_client_exception(self, mock_mcp, mock_client_factory, client):
        """Test create_task_category handles client exceptions."""
        register_task_tools_lazy(mock_mcp, mock_client_factory)
        tool = mock_mcp.tools["create_task_category"]
        
        with patch.object(client, 'create_task_category', side_effect=Exception("Create error")):
            result_json = await tool(name="Test Category")
            result = json.loads(result_json)
            
            assert result["success"] is False
            assert "error" in result