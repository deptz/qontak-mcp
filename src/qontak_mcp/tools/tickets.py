"""
MCP Tools for Qontak CRM Tickets.

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
    TicketListParams,
    TicketGetParams,
    TicketCreateParams,
    TicketUpdateParams,
    TicketPipelinesParams,
)
from ..errors import safe_error_response


def register_ticket_tools(mcp: FastMCP, client: QontakClient) -> None:
    """
    Register all ticket-related MCP tools.
    
    Args:
        mcp: The FastMCP server instance
        client: The QontakClient instance
    """
    # Use the lazy version internally
    register_ticket_tools_lazy(mcp, lambda: client)


def register_ticket_tools_lazy(
    mcp: FastMCP,
    get_client: Callable[[], QontakClient]
) -> None:
    """
    Register all ticket-related MCP tools with lazy client access.
    
    This version defers client access until the tool is called,
    avoiding the security issue of creating clients at import time.
    
    Args:
        mcp: The FastMCP server instance
        get_client: Function that returns the QontakClient instance
    """
    
    @mcp.tool()
    async def get_ticket_template(user_id: Optional[str] = None) -> str:
        """
        Get the ticket field template/schema.
        
        Returns the available fields, their types, and options for creating/updating tickets.
        Use this to understand what data is required when creating a new ticket.
        
        Args:
            user_id: Optional user/tenant identifier for multi-tenant scenarios
        
        Returns:
            JSON string with ticket template fields and options
        """
        try:
            client = get_client()
            result = await client.get_ticket_template(user_id=user_id)
            return json.dumps(result, indent=2)
        except Exception as e:
            return json.dumps(safe_error_response(e, "get_ticket_template"), indent=2)
    
    @mcp.tool()
    async def list_tickets(
        page: int = 1,
        per_page: int = 25,
        pipeline_id: Optional[int] = None,
        user_id: Optional[str] = None,
    ) -> str:
        """
        List tickets with optional filtering.
        
        Retrieves a paginated list of tickets from Qontak CRM.
        
        Args:
            page: Page number (default: 1)
            per_page: Number of tickets per page (default: 25, max: 100)
            pipeline_id: Optional filter by pipeline ID
            user_id: Optional user/tenant identifier for multi-tenant scenarios
        
        Returns:
            JSON string with list of tickets and pagination info
        """
        try:
            # Validate inputs with Pydantic
            params = TicketListParams(
                page=page,
                per_page=per_page,
                pipeline_id=pipeline_id,
                user_id=user_id,
            )
            
            client = get_client()
            result = await client.list_tickets(
                page=params.page,
                per_page=params.per_page,
                pipeline_id=params.pipeline_id,
                user_id=params.user_id,
            )
            return json.dumps(result, indent=2)
        except PydanticValidationError as e:
            return json.dumps(safe_error_response(e, "list_tickets"), indent=2)
        except Exception as e:
            return json.dumps(safe_error_response(e, "list_tickets"), indent=2)
    
    @mcp.tool()
    async def get_ticket(ticket_id: int, user_id: Optional[str] = None) -> str:
        """
        Get a single ticket by ID.
        
        Retrieves detailed information about a specific ticket.
        
        Args:
            ticket_id: The ID of the ticket to retrieve
            user_id: Optional user/tenant identifier for multi-tenant scenarios
        
        Returns:
            JSON string with ticket details
        """
        try:
            # Validate inputs
            params = TicketGetParams(ticket_id=ticket_id, user_id=user_id)
            
            client = get_client()
            result = await client.get_ticket(ticket_id=params.ticket_id, user_id=params.user_id)
            return json.dumps(result, indent=2)
        except PydanticValidationError as e:
            return json.dumps(safe_error_response(e, "get_ticket"), indent=2)
        except Exception as e:
            return json.dumps(safe_error_response(e, "get_ticket"), indent=2)
    
    @mcp.tool()
    async def create_ticket(
        name: str,
        ticket_stage_id: int,
        crm_lead_ids: Optional[str] = None,
        crm_company_id: Optional[int] = None,
        crm_product_ids: Optional[str] = None,
        crm_task_ids: Optional[str] = None,
        priority: Optional[str] = None,
        description: Optional[str] = None,
        additional_fields: Optional[str] = None,
        user_id: Optional[str] = None,
    ) -> str:
        """
        Create a new ticket.
        
        Creates a new ticket in Qontak CRM with the specified data.
        
        WORKFLOW FOR LLMs:
        1. Call get_ticket_pipelines() to see available pipelines and stages
        2. Call get_required_fields_for_ticket(pipeline_id) to discover required fields for that pipeline
        3. For dropdown fields, present the available options to the user
        4. Collect values for all required fields and desired optional fields
        5. Call this tool with standard fields as parameters and custom fields in additional_fields
        
        Args:
            name: Ticket name/title (required)
            ticket_stage_id: Pipeline stage ID (required, API field name: ticket_stage_id). Use get_ticket_pipelines to see available stages.
            crm_lead_ids: Optional JSON array string of associated contact/lead IDs (API field name: crm_lead_ids). Example: '[1, 2, 3]'
            crm_company_id: Optional associated company ID (API field name: crm_company_id)
            crm_product_ids: Optional JSON array string of associated product IDs (API field name: crm_product_ids). Example: '[10, 20]'
            crm_task_ids: Optional JSON array string of associated task IDs (API field name: crm_task_ids). Example: '[5, 6]'
            priority: Optional priority level (e.g., "low", "medium", "high", "urgent")
            description: Optional ticket description
            additional_fields: Optional JSON string of additional/custom fields array. Format: '[{"id": 123, "name": "field_name", "value": "value", "value_name": null}]'. Get field IDs from get_required_fields_for_ticket(). Example: '[{"id": 17078476, "name": "score", "value": "100", "value_name": null}]'
            user_id: Optional user/tenant identifier for multi-tenant scenarios
        
        Returns:
            JSON string with the created ticket details
        """
        try:
            # Parse array fields
            parsed_lead_ids = None
            if crm_lead_ids is not None:
                try:
                    parsed_lead_ids = json.loads(crm_lead_ids)
                    if not isinstance(parsed_lead_ids, list):
                        return json.dumps({"success": False, "error": "crm_lead_ids must be a JSON array"}, indent=2)
                except json.JSONDecodeError:
                    return json.dumps({"success": False, "error": "Invalid JSON format in crm_lead_ids"}, indent=2)
            
            parsed_product_ids = None
            if crm_product_ids is not None:
                try:
                    parsed_product_ids = json.loads(crm_product_ids)
                    if not isinstance(parsed_product_ids, list):
                        return json.dumps({"success": False, "error": "crm_product_ids must be a JSON array"}, indent=2)
                except json.JSONDecodeError:
                    return json.dumps({"success": False, "error": "Invalid JSON format in crm_product_ids"}, indent=2)
            
            parsed_task_ids = None
            if crm_task_ids is not None:
                try:
                    parsed_task_ids = json.loads(crm_task_ids)
                    if not isinstance(parsed_task_ids, list):
                        return json.dumps({"success": False, "error": "crm_task_ids must be a JSON array"}, indent=2)
                except json.JSONDecodeError:
                    return json.dumps({"success": False, "error": "Invalid JSON format in crm_task_ids"}, indent=2)
            
            # Parse additional_fields JSON if provided (should be array format)
            parsed_additional_fields = None
            if additional_fields is not None:
                try:
                    parsed_additional_fields = json.loads(additional_fields)
                    if not isinstance(parsed_additional_fields, list):
                        return json.dumps({"success": False, "error": "additional_fields must be a JSON array of objects with id, name, value structure"}, indent=2)
                except json.JSONDecodeError:
                    return json.dumps({"success": False, "error": "Invalid JSON format in additional_fields"}, indent=2)
            
            # Validate with Pydantic
            params = TicketCreateParams(
                name=name,
                ticket_stage_id=ticket_stage_id,
                crm_lead_ids=parsed_lead_ids,
                crm_company_id=crm_company_id,
                crm_product_ids=parsed_product_ids,
                crm_task_ids=parsed_task_ids,
                priority=priority,
                description=description,
                additional_fields=parsed_additional_fields,
                user_id=user_id,
            )
            
            # Build ticket data with correct API field names
            ticket_data: dict[str, Any] = {
                "name": params.name,
                "ticket_stage_id": params.ticket_stage_id,
            }
            
            if params.crm_lead_ids is not None:
                ticket_data["crm_lead_ids"] = params.crm_lead_ids
            if params.crm_company_id is not None:
                ticket_data["crm_company_id"] = params.crm_company_id
            if params.crm_product_ids is not None:
                ticket_data["crm_product_ids"] = params.crm_product_ids
            if params.crm_task_ids is not None:
                ticket_data["crm_task_ids"] = params.crm_task_ids
            if params.priority is not None:
                ticket_data["priority"] = params.priority
            if params.description is not None:
                ticket_data["description"] = params.description
            
            # Add additional_fields array (required by API, empty array if not provided)
            if parsed_additional_fields:
                ticket_data["additional_fields"] = parsed_additional_fields
            else:
                ticket_data["additional_fields"] = []
            
            client = get_client()
            result = await client.create_ticket(ticket_data=ticket_data, user_id=params.user_id)
            return json.dumps(result, indent=2)
        except PydanticValidationError as e:
            return json.dumps(safe_error_response(e, "create_ticket"), indent=2)
        except Exception as e:
            return json.dumps(safe_error_response(e, "create_ticket"), indent=2)
    
    @mcp.tool()
    async def update_ticket(
        ticket_id: int,
        name: Optional[str] = None,
        stage_id: Optional[int] = None,
        contact_id: Optional[int] = None,
        company_id: Optional[int] = None,
        priority: Optional[str] = None,
        description: Optional[str] = None,
        custom_fields: Optional[str] = None,
        user_id: Optional[str] = None,
    ) -> str:
        """
        Update an existing ticket.
        
        Updates a ticket in Qontak CRM. Only provided fields will be updated.
        
        Args:
            ticket_id: The ID of the ticket to update (required)
            name: Optional new ticket name
            stage_id: Optional new stage ID
            contact_id: Optional new associated contact ID
            company_id: Optional new associated company ID
            priority: Optional new priority level
            description: Optional new ticket description
            custom_fields: Optional JSON string of custom field values to update
            user_id: Optional user/tenant identifier for multi-tenant scenarios
        
        Returns:
            JSON string with the updated ticket details
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
            # Convert contact_id to list format for crm_lead_ids
            crm_lead_ids_list = [contact_id] if contact_id is not None else None
            
            params = TicketUpdateParams(
                ticket_id=ticket_id,
                name=name,
                ticket_stage_id=stage_id,
                crm_lead_ids=crm_lead_ids_list,
                crm_company_id=company_id,
                priority=priority,
                description=description,
                custom_fields=parsed_custom_fields,
                user_id=user_id,
            )
            
            # Build update data
            ticket_data: dict[str, Any] = {}
            
            if params.name is not None:
                ticket_data["name"] = params.name
            if params.ticket_stage_id is not None:
                ticket_data["ticket_stage_id"] = params.ticket_stage_id
            if params.crm_lead_ids is not None:
                # Convert list to the first ID for simplified API (contact_id)
                ticket_data["contact_id"] = params.crm_lead_ids[0] if params.crm_lead_ids else None
            if params.crm_company_id is not None:
                ticket_data["company_id"] = params.crm_company_id
            if params.priority is not None:
                ticket_data["priority"] = params.priority
            if params.description is not None:
                ticket_data["description"] = params.description
            if params.custom_fields is not None:
                ticket_data["custom_fields"] = params.custom_fields
            
            client = get_client()
            result = await client.update_ticket(
                ticket_id=params.ticket_id, ticket_data=ticket_data, user_id=params.user_id
            )
            return json.dumps(result, indent=2)
        except PydanticValidationError as e:
            return json.dumps(safe_error_response(e, "update_ticket"), indent=2)
        except Exception as e:
            return json.dumps(safe_error_response(e, "update_ticket"), indent=2)
    
    @mcp.tool()
    async def get_ticket_pipelines(
        page: int = 1,
        per_page: int = 25,
        user_id: Optional[str] = None,
    ) -> str:
        """
        Get available ticket pipelines and stages.
        
        Retrieves all ticket pipelines with their stages. Use this to get
        valid stage_id values for creating/updating tickets.
        
        Args:
            page: Page number (default: 1)
            per_page: Number of pipelines per page (default: 25)
            user_id: Optional user/tenant identifier for multi-tenant scenarios
        
        Returns:
            JSON string with pipelines and their stages
        """
        try:
            # Validate inputs
            params = TicketPipelinesParams(
                page=page,
                per_page=per_page,
                user_id=user_id,
            )
            
            client = get_client()
            result = await client.get_ticket_pipelines(
                page=params.page, per_page=params.per_page, user_id=params.user_id
            )
            return json.dumps(result, indent=2)
        except PydanticValidationError as e:
            return json.dumps(safe_error_response(e, "get_ticket_pipelines"), indent=2)
        except Exception as e:
            return json.dumps(safe_error_response(e, "get_ticket_pipelines"), indent=2)
    
    @mcp.tool()
    async def delete_ticket(
        ticket_id: int,
        user_id: Optional[str] = None,
    ) -> str:
        """
        Delete a ticket.
        
        Permanently deletes a ticket by its ID.
        
        Args:
            ticket_id: The ID of the ticket to delete (required)
            user_id: Optional user/tenant identifier for multi-tenant scenarios
        
        Returns:
            JSON string confirming the deletion
        """
        try:
            # Validate inputs
            params = TicketGetParams(ticket_id=ticket_id, user_id=user_id)
            
            client = get_client()
            result = await client.delete_ticket(ticket_id=params.ticket_id, user_id=params.user_id)
            return json.dumps(result, indent=2)
        except PydanticValidationError as e:
            return json.dumps(safe_error_response(e, "delete_ticket"), indent=2)
        except Exception as e:
            return json.dumps(safe_error_response(e, "delete_ticket"), indent=2)
    
    @mcp.tool()
    async def get_required_fields_for_ticket(
        pipeline_id: int,
        user_id: Optional[str] = None,
    ) -> str:
        """
        Get comprehensive ticket field information with pipeline-specific requirements.
        
        Analyzes the ticket template to determine which fields are required for a specific
        pipeline. Returns detailed information about all fields including:
        - Field names and human-readable labels (name_alias)
        - Field types (Single-line text, Dropdown select, Number, Text Area, etc.)
        - Dropdown options with IDs and names (where applicable)
        - Whether field is required for the specified pipeline
        - Whether field is a standard or custom/additional field
        
        WORKFLOW FOR LLMs:
        1. Call get_ticket_pipelines() to show available pipelines
        2. Call this tool with the selected pipeline_id
        3. Review required fields and dropdown options
        4. Ask the user for values for all required fields
        5. For dropdown fields, present the available options to the user
        6. Call create_ticket() with all required field values
        
        IMPORTANT NOTES:
        - Required fields vary by pipeline (check required_pipeline_ids array)
        - Tickets MUST have: name, ticket_stage_id (from selected pipeline)
        - user_id is the assigned user (get valid IDs from template dropdown_options)
        - Date fields accept formats: DD-MM-YYYY or ISO format
        - Custom/additional fields (where id is not null) must be passed in additional_fields parameter
        - Format: {"crm_additional_field_{id}": "value"} for custom fields with IDs
        - Example: If custom field "score" has id 17078476, use: {"crm_additional_field_17078476": "85"}
        - Associations support arrays: crm_lead_ids (contacts), crm_product_ids, crm_task_ids
        - File uploads: Photo/signature/attachment fields require separate upload mechanism
        
        Args:
            pipeline_id: The pipeline ID to check requirements for (required)
            user_id: Optional user/tenant identifier for multi-tenant scenarios
        
        Returns:
            JSON string with comprehensive field information including required fields for the pipeline
        """
        try:
            client = get_client()
            template = await client.get_ticket_template(user_id=user_id)
            
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
                dropdown = field.get("dropdown", [])
                required_pipeline_ids = field.get("required_pipeline_ids", [])
                show_pipeline_ids = field.get("show_pipeline_ids", [])
                
                is_required = pipeline_id in required_pipeline_ids
                is_visible = pipeline_id in show_pipeline_ids or not show_pipeline_ids
                
                field_info: dict[str, Any] = {
                    "name": field_name,
                    "name_alias": field_alias,
                    "type": field_type,
                    "has_dropdown": len(dropdown) > 0 if dropdown else False,
                    "required_for_pipeline": is_required,
                    "visible_for_pipeline": is_visible,
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
                
                # Categorize fields
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
                "pipeline_id": pipeline_id,
                "required_standard_fields": required_standard_fields,
                "required_custom_fields": required_custom_fields,
                "optional_standard_fields": optional_standard_fields,
                "optional_custom_fields": optional_custom_fields,
                "summary": {
                    "total_required": len(required_standard_fields) + len(required_custom_fields),
                    "required_standard": len(required_standard_fields),
                    "required_custom": len(required_custom_fields),
                    "total_optional": len(optional_standard_fields) + len(optional_custom_fields),
                    "note": "Use this information to ask the user for required field values. For dropdown fields, present the available options."
                }
            }
            
            return json.dumps(result, indent=2)
        except Exception as e:
            return json.dumps(safe_error_response(e, "get_required_fields_for_ticket"), indent=2)
