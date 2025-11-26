"""
MCP Tools for Qontak CRM Tasks.

Security features:
- Pydantic validation for all inputs
- Lazy client initialization
- Safe error responses
"""

import json
from typing import Optional, Any, Callable

from mcp.server.fastmcp import FastMCP
from pydantic import ValidationError as PydanticValidationError

from ..client import QontakClient
from ..models import (
    TaskListParams,
    TaskGetParams,
    TaskCreateParams,
    TaskUpdateParams,
    TaskCategoryListParams,
    TaskCategoryCreateParams,
)
from ..errors import safe_error_response


def register_task_tools(mcp: FastMCP, client: QontakClient) -> None:
    """
    Register all task-related MCP tools.
    
    Args:
        mcp: The FastMCP server instance
        client: The QontakClient instance
    """
    # Use the lazy version internally
    register_task_tools_lazy(mcp, lambda: client)


def register_task_tools_lazy(
    mcp: FastMCP,
    get_client: Callable[[], QontakClient]
) -> None:
    """
    Register all task-related MCP tools with lazy client access.
    
    This version defers client access until the tool is called,
    avoiding the security issue of creating clients at import time.
    
    Args:
        mcp: The FastMCP server instance
        get_client: Function that returns the QontakClient instance
    """
    
    @mcp.tool()
    async def get_task_template(user_id: Optional[str] = None) -> str:
        """
        Get the task field template/schema.
        
        Returns the available fields, their types, and options for creating/updating tasks.
        Use this to understand what data is required when creating a new task.
        
        Args:
            user_id: Optional user/tenant identifier for multi-tenant scenarios
        
        Returns:
            JSON string with task template fields and options
        """
        try:
            client = get_client()
            result = await client.get_task_template(user_id=user_id)
            return json.dumps(result, indent=2)
        except Exception as e:
            return json.dumps(safe_error_response(e, "get_task_template"), indent=2)
    
    @mcp.tool()
    async def list_tasks(
        page: int = 1,
        per_page: int = 25,
        category_id: Optional[int] = None,
        user_id: Optional[str] = None,
    ) -> str:
        """
        List tasks with optional filtering.
        
        Retrieves a paginated list of tasks from Qontak CRM.
        
        Args:
            page: Page number (default: 1)
            per_page: Number of tasks per page (default: 25, max: 100)
            category_id: Optional filter by category ID
            user_id: Optional user/tenant identifier for multi-tenant scenarios
        
        Returns:
            JSON string with list of tasks and pagination info
        """
        try:
            # Validate inputs with Pydantic
            params = TaskListParams(
                page=page,
                per_page=per_page,
                category_id=category_id,
                user_id=user_id,
            )
            
            client = get_client()
            result = await client.list_tasks(
                page=params.page,
                per_page=params.per_page,
                category_id=params.category_id,
                user_id=params.user_id,
            )
            return json.dumps(result, indent=2)
        except PydanticValidationError as e:
            return json.dumps(safe_error_response(e, "list_tasks"), indent=2)
        except Exception as e:
            return json.dumps(safe_error_response(e, "list_tasks"), indent=2)
    
    @mcp.tool()
    async def get_task(task_id: int, user_id: Optional[str] = None) -> str:
        """
        Get a single task by ID.
        
        Retrieves detailed information about a specific task.
        
        Args:
            task_id: The ID of the task to retrieve
            user_id: Optional user/tenant identifier for multi-tenant scenarios
        
        Returns:
            JSON string with task details
        """
        try:
            # Validate inputs
            params = TaskGetParams(task_id=task_id, user_id=user_id)
            
            client = get_client()
            result = await client.get_task(task_id=params.task_id, user_id=params.user_id)
            return json.dumps(result, indent=2)
        except PydanticValidationError as e:
            return json.dumps(safe_error_response(e, "get_task"), indent=2)
        except Exception as e:
            return json.dumps(safe_error_response(e, "get_task"), indent=2)
    
    @mcp.tool()
    async def create_task(
        name: str,
        due_date: str,
        crm_task_status_id: Optional[int] = None,
        detail: Optional[str] = None,
        next_step: Optional[str] = None,
        category_id: Optional[int] = None,
        crm_person_id: Optional[int] = None,
        crm_company_id: Optional[int] = None,
        crm_deal_id: Optional[int] = None,
        priority: Optional[str] = None,
        description: Optional[str] = None,
        additional_fields: Optional[str] = None,
        user_id: Optional[str] = None,
    ) -> str:
        """
        Create a new task.
        
        Creates a new task in Qontak CRM with the specified data.
        
        CRITICAL WORKFLOW FOR LLMs:
        1. Call get_required_fields_for_task() FIRST to discover required fields dynamically
        2. Review the required_standard_fields and required_custom_fields from the response
        3. For dropdown fields (like crm_task_status_id), present the available options to the user
        4. Collect values for ALL required fields before calling this tool
        5. Call this tool with standard required fields as direct parameters
        6. Pass custom required fields in the additional_fields JSON array
        
        IMPORTANT: Required fields (like crm_task_status_id, detail, next_step) are discovered 
        dynamically from the template - NEVER hardcode these values
        
        Args:
            name: Task name/title (always required)
            due_date: Task due date (always required, format: YYYY-MM-DD or YYYY-MM-DD HH:MM:SS)
            crm_task_status_id: Task status ID. USUALLY REQUIRED - check get_required_fields_for_task(). Common values: 1=Not Started, 2=In Progress, 3=Waiting, 4=Completed, 5=Deferred
            detail: Task details/plan. USUALLY REQUIRED - check get_required_fields_for_task(). Provide descriptive text about the task.
            next_step: Next steps/results. USUALLY REQUIRED - check get_required_fields_for_task(). Describe the expected next action or outcome.
            category_id: Task category ID. May be required - check template. Use list_task_categories to see options.
            crm_person_id: Associated contact/person ID. May be required - check template.
            crm_company_id: Associated company ID. May be required - check template.
            crm_deal_id: Associated deal ID. May be required - check template.
            priority: Priority level. May be required - check template (e.g., "low", "medium", "high")
            description: Task description. May be required - check template.
            additional_fields: JSON array of custom/additional required and optional fields. Format: '[{"id": 123, "name": "field_name", "value": "value"}]'. MUST include all required custom fields from get_required_fields_for_task().
            user_id: Optional user/tenant identifier for multi-tenant scenarios
        
        Returns:
            JSON string with the created task details
        """
        try:
            # Parse additional_fields JSON if provided (should be array format)
            parsed_additional_fields = None
            if additional_fields is not None:
                try:
                    parsed_additional_fields = json.loads(additional_fields)
                    if not isinstance(parsed_additional_fields, list):
                        return json.dumps({
                            "success": False,
                            "error": "additional_fields must be a JSON array of objects with id, name, value structure"
                        }, indent=2)
                except json.JSONDecodeError:
                    return json.dumps({
                        "success": False,
                        "error": "Invalid JSON format in additional_fields"
                    }, indent=2)
            
            # Validate with Pydantic
            params = TaskCreateParams(
                name=name,
                due_date=due_date,
                crm_task_status_id=crm_task_status_id,
                detail=detail,
                next_step=next_step,
                category_id=category_id,
                crm_person_id=crm_person_id,
                crm_company_id=crm_company_id,
                crm_deal_id=crm_deal_id,
                priority=priority,
                description=description,
                additional_fields=parsed_additional_fields,
                user_id=user_id,
            )
            
            # Build task data with correct API field names
            task_data: dict[str, Any] = {
                "name": params.name,
                "due_date": params.due_date,
            }
            
            if params.crm_task_status_id is not None:
                task_data["crm_task_status_id"] = params.crm_task_status_id
            if params.detail is not None:
                task_data["detail"] = params.detail
            if params.next_step is not None:
                task_data["next_step"] = params.next_step
            if params.category_id is not None:
                task_data["category_id"] = params.category_id
            if params.crm_person_id is not None:
                task_data["crm_person_id"] = params.crm_person_id
            if params.crm_company_id is not None:
                task_data["crm_company_id"] = params.crm_company_id
            if params.crm_deal_id is not None:
                task_data["crm_deal_id"] = params.crm_deal_id
            if params.priority is not None:
                task_data["priority"] = params.priority
            if params.description is not None:
                task_data["description"] = params.description
            
            # Add additional_fields array (required by API, empty array if not provided)
            if parsed_additional_fields:
                task_data["additional_fields"] = parsed_additional_fields
            else:
                task_data["additional_fields"] = []
            
            client = get_client()
            result = await client.create_task(task_data=task_data, user_id=params.user_id)
            return json.dumps(result, indent=2)
        except PydanticValidationError as e:
            return json.dumps(safe_error_response(e, "create_task"), indent=2)
        except Exception as e:
            return json.dumps(safe_error_response(e, "create_task"), indent=2)
    
    @mcp.tool()
    async def update_task(
        task_id: int,
        name: Optional[str] = None,
        due_date: Optional[str] = None,
        category_id: Optional[int] = None,
        contact_id: Optional[int] = None,
        company_id: Optional[int] = None,
        deal_id: Optional[int] = None,
        priority: Optional[str] = None,
        description: Optional[str] = None,
        status: Optional[str] = None,
        custom_fields: Optional[str] = None,
        user_id: Optional[str] = None,
    ) -> str:
        """
        Update an existing task.
        
        Updates a task in Qontak CRM. Only provided fields will be updated.
        
        Args:
            task_id: The ID of the task to update (required)
            name: Optional new task name
            due_date: Optional new due date (format: YYYY-MM-DD or YYYY-MM-DD HH:MM:SS)
            category_id: Optional new category ID
            contact_id: Optional new associated contact ID
            company_id: Optional new associated company ID
            deal_id: Optional new associated deal ID
            priority: Optional new priority level
            description: Optional new task description
            status: Optional new status (e.g., "pending", "completed")
            custom_fields: Optional JSON string of custom field values to update
            user_id: Optional user/tenant identifier for multi-tenant scenarios
        
        Returns:
            JSON string with the updated task details
        """
        try:
            # Parse custom_fields JSON if provided
            parsed_custom_fields = None
            if custom_fields is not None:
                try:
                    parsed_custom_fields = json.loads(custom_fields)
                except json.JSONDecodeError:
                    return json.dumps({
                        "success": False,
                        "error": "Invalid JSON format in custom_fields"
                    }, indent=2)
            
            # Validate with Pydantic (map simplified names to API field names)
            params = TaskUpdateParams(
                task_id=task_id,
                name=name,
                due_date=due_date,
                category_id=category_id,
                crm_person_id=contact_id,
                crm_company_id=company_id,
                crm_deal_id=deal_id,
                priority=priority,
                description=description,
                status=status,
                custom_fields=parsed_custom_fields,
                user_id=user_id,
            )
            
            # Build update data
            task_data: dict[str, Any] = {}
            
            if params.name is not None:
                task_data["name"] = params.name
            if params.due_date is not None:
                task_data["due_date"] = params.due_date
            if params.category_id is not None:
                task_data["category_id"] = params.category_id
            if params.crm_person_id is not None:
                task_data["contact_id"] = params.crm_person_id
            if params.crm_company_id is not None:
                task_data["company_id"] = params.crm_company_id
            if params.crm_deal_id is not None:
                task_data["deal_id"] = params.crm_deal_id
            if params.priority is not None:
                task_data["priority"] = params.priority
            if params.description is not None:
                task_data["description"] = params.description
            if params.status is not None:
                task_data["status"] = params.status
            if params.custom_fields is not None:
                task_data["custom_fields"] = params.custom_fields
            
            client = get_client()
            result = await client.update_task(
                task_id=params.task_id, task_data=task_data, user_id=params.user_id
            )
            return json.dumps(result, indent=2)
        except PydanticValidationError as e:
            return json.dumps(safe_error_response(e, "update_task"), indent=2)
        except Exception as e:
            return json.dumps(safe_error_response(e, "update_task"), indent=2)
    
    @mcp.tool()
    async def list_task_categories(
        page: int = 1,
        per_page: int = 25,
        user_id: Optional[str] = None,
    ) -> str:
        """
        List available task categories.
        
        Retrieves all task categories. Use this to get valid category_id values
        for creating/updating tasks.
        
        Args:
            page: Page number (default: 1)
            per_page: Number of categories per page (default: 25)
            user_id: Optional user/tenant identifier for multi-tenant scenarios
        
        Returns:
            JSON string with list of task categories
        """
        try:
            # Validate inputs
            params = TaskCategoryListParams(
                page=page,
                per_page=per_page,
                user_id=user_id,
            )
            
            client = get_client()
            result = await client.list_task_categories(
                page=params.page, per_page=params.per_page, user_id=params.user_id
            )
            return json.dumps(result, indent=2)
        except PydanticValidationError as e:
            return json.dumps(safe_error_response(e, "list_task_categories"), indent=2)
        except Exception as e:
            return json.dumps(safe_error_response(e, "list_task_categories"), indent=2)
    
    @mcp.tool()
    async def create_task_category(
        name: str,
        color: Optional[str] = None,
        user_id: Optional[str] = None,
    ) -> str:
        """
        Create a new task category.
        
        Creates a new category for organizing tasks.
        
        Args:
            name: Category name (required)
            color: Optional color for the category (e.g., "#FF5733" or "red")
            user_id: Optional user/tenant identifier for multi-tenant scenarios
        
        Returns:
            JSON string with the created category details
        """
        try:
            # Validate inputs
            params = TaskCategoryCreateParams(
                name=name,
                color=color,
                user_id=user_id,
            )
            
            client = get_client()
            result = await client.create_task_category(
                name=params.name, color=params.color, user_id=params.user_id
            )
            return json.dumps(result, indent=2)
        except PydanticValidationError as e:
            return json.dumps(safe_error_response(e, "create_task_category"), indent=2)
        except Exception as e:
            return json.dumps(safe_error_response(e, "create_task_category"), indent=2)
    
    @mcp.tool()
    async def delete_task(
        task_id: int,
        user_id: Optional[str] = None,
    ) -> str:
        """
        Delete a task.
        
        Permanently deletes a task by its ID.
        
        Args:
            task_id: The ID of the task to delete (required)
            user_id: Optional user/tenant identifier for multi-tenant scenarios
        
        Returns:
            JSON string confirming the deletion
        """
        try:
            # Validate inputs
            params = TaskGetParams(task_id=task_id, user_id=user_id)
            
            client = get_client()
            result = await client.delete_task(task_id=params.task_id, user_id=params.user_id)
            return json.dumps(result, indent=2)
        except PydanticValidationError as e:
            return json.dumps(safe_error_response(e, "delete_task"), indent=2)
        except Exception as e:
            return json.dumps(safe_error_response(e, "delete_task"), indent=2)
    
    @mcp.tool()
    async def delete_task_category(
        category_id: int,
        user_id: Optional[str] = None,
    ) -> str:
        """
        Delete a task category.
        
        Permanently deletes a task category by its ID.
        Note: Tasks using this category will need to be reassigned to another category.
        
        Args:
            category_id: The ID of the category to delete (required)
            user_id: Optional user/tenant identifier for multi-tenant scenarios
        
        Returns:
            JSON string confirming the deletion
        """
        try:
            client = get_client()
            result = await client.delete_task_category(category_id=category_id, user_id=user_id)
            return json.dumps(result, indent=2)
        except Exception as e:
            return json.dumps(safe_error_response(e, "delete_task_category"), indent=2)
    
    @mcp.tool()
    async def get_required_fields_for_task(user_id: Optional[str] = None) -> str:
        """
        Get comprehensive task field information from template.
        
        Returns detailed information about all available task fields including:
        - Field names and human-readable labels (name_alias)
        - Field types (Single-line text, Dropdown select, Date time, etc.)
        - Dropdown options with IDs and names (where applicable)
        - Whether field is a standard or custom/additional field
        
        WORKFLOW FOR LLMs:
        1. Call this tool to discover all available task fields
        2. Review the field types and dropdown options
        3. Ask the user for values for required fields (name, status, priority, category, user_id)
        4. For dropdown fields, present the available options to the user
        5. Call create_task() with all necessary field values
        
        IMPORTANT NOTES:
        - Task Status has 5 options: Not Started, In Progress, Waiting, Completed, Deferred
        - Task Priority has 5 levels: None, Low, Normal, High, Urgent
        - Categories are user-defined (use list_task_categories to get valid IDs)
        - Associations: crm_person_id (contact), crm_company_id, crm_deal_id
        - Date fields: due_date, end_due_date, reminder_date (use ISO format or DD/MM/YYYY)
        - Custom fields use additional_fields array format
        
        Args:
            user_id: Optional user/tenant identifier for multi-tenant scenarios
        
        Returns:
            JSON string with comprehensive field information including standard and custom fields
        """
        try:
            client = get_client()
            template = await client.get_task_template(user_id=user_id)
            
            if not template.get("success"):
                return json.dumps(template, indent=2)
            
            fields = template.get("data", {}).get("response", [])
            
            required_standard_fields = []
            required_custom_fields = []
            optional_standard_fields = []
            optional_custom_fields = []
            
            for field in fields:
                field_name = field.get("name", "")
                field_id = field.get("id")
                field_type = field.get("type", "unknown")
                field_alias = field.get("name_alias", field_name)
                is_additional = field.get("additional_field", False)
                is_required = field.get("required", False)
                dropdown = field.get("dropdown", [])
                
                field_info: dict[str, Any] = {
                    "name": field_name,
                    "name_alias": field_alias,
                    "type": field_type,
                    "required": is_required,
                    "has_dropdown": len(dropdown) > 0 if dropdown else False,
                }
                
                if field_id is not None:
                    field_info["id"] = field_id
                
                if dropdown and len(dropdown) > 0:
                    field_info["dropdown_options"] = [
                        {
                            "id": opt.get("id"),
                            "name": opt.get("name"),
                            "email": opt.get("email") if "email" in opt else None
                        }
                        for opt in dropdown
                    ]
                
                # Categorize fields by required status and type
                if is_required:
                    if is_additional:
                        required_custom_fields.append(field_info)
                    else:
                        required_standard_fields.append(field_info)
                else:
                    if is_additional:
                        optional_custom_fields.append(field_info)
                    else:
                        optional_standard_fields.append(field_info)
            
            result = {
                "success": True,
                "required_standard_fields": required_standard_fields,
                "required_custom_fields": required_custom_fields,
                "optional_standard_fields": optional_standard_fields,
                "optional_custom_fields": optional_custom_fields,
                "summary": {
                    "total_fields": len(fields),
                    "total_required": len(required_standard_fields) + len(required_custom_fields),
                    "required_standard": len(required_standard_fields),
                    "required_custom": len(required_custom_fields),
                    "total_optional": len(optional_standard_fields) + len(optional_custom_fields),
                    "note": "Use this information to ask the user for field values for all required fields. For dropdown fields, present the available options."
                }
            }
            
            return json.dumps(result, indent=2)
        except Exception as e:
            return json.dumps(safe_error_response(e, "get_required_fields_for_task"), indent=2)
