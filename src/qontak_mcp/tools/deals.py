"""
MCP Tools for Qontak CRM Deals.

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
    DealListParams,
    DealGetParams,
    DealCreateParams,
    DealUpdateParams,
    DealTimelineParams,
)
from ..errors import safe_error_response


def register_deal_tools(mcp: FastMCP, client: QontakClient) -> None:
    """
    Register all deal-related MCP tools.
    
    Args:
        mcp: The FastMCP server instance
        client: The QontakClient instance
    """
    # Use the lazy version internally
    register_deal_tools_lazy(mcp, lambda: client)


def register_deal_tools_lazy(
    mcp: FastMCP,
    get_client: Callable[[], QontakClient]
) -> None:
    """
    Register all deal-related MCP tools with lazy client access.
    
    This version defers client access until the tool is called,
    avoiding the security issue of creating clients at import time.
    
    Args:
        mcp: The FastMCP server instance
        get_client: Function that returns the QontakClient instance
    """
    
    @mcp.tool()
    async def get_deal_template(user_id: Optional[str] = None) -> str:
        """
        Get the deal field template/schema.
        
        Returns the available fields, their types, and required field information for 
        creating/updating deals. Each field shows:
        - required_pipeline_ids: List of pipeline IDs where this field is required
        - required_stage_ids: List of stage IDs where this field is required
        
        IMPORTANT: Use this tool BEFORE creating a deal to check which fields are 
        required for your specific pipeline and stage combination.
        
        Args:
            user_id: Optional user/tenant identifier for multi-tenant scenarios
        
        Returns:
            JSON string with deal template fields, dropdown options, and requirement rules
        """
        try:
            client = get_client()
            result = await client.get_deal_template(user_id=user_id)
            return json.dumps(result, indent=2)
        except Exception as e:
            return json.dumps(safe_error_response(e, "get_deal_template"), indent=2)
    
    @mcp.tool()
    async def list_deals(
        page: int = 1,
        per_page: int = 25,
        stage_id: Optional[int] = None,
        pipeline_id: Optional[int] = None,
        user_id: Optional[str] = None,
    ) -> str:
        """
        List deals with optional filtering.
        
        Retrieves a paginated list of deals from Qontak CRM.
        
        Args:
            page: Page number (default: 1)
            per_page: Number of deals per page (default: 25, max: 100)
            stage_id: Optional filter by stage ID
            pipeline_id: Optional filter by pipeline ID
            user_id: Optional user/tenant identifier for multi-tenant scenarios
        
        Returns:
            JSON string with list of deals and pagination info
        """
        try:
            # Validate inputs with Pydantic
            params = DealListParams(
                page=page,
                per_page=per_page,
                stage_id=stage_id,
                pipeline_id=pipeline_id,
                user_id=user_id,
            )
            
            client = get_client()
            result = await client.list_deals(
                page=params.page,
                per_page=params.per_page,
                stage_id=params.stage_id,
                pipeline_id=params.pipeline_id,
                user_id=params.user_id,
            )
            return json.dumps(result, indent=2)
        except PydanticValidationError as e:
            return json.dumps(safe_error_response(e, "list_deals"), indent=2)
        except Exception as e:
            return json.dumps(safe_error_response(e, "list_deals"), indent=2)
    
    @mcp.tool()
    async def get_deal(deal_id: int, user_id: Optional[str] = None) -> str:
        """
        Get a single deal by ID.
        
        Retrieves detailed information about a specific deal.
        
        Args:
            deal_id: The ID of the deal to retrieve
            user_id: Optional user/tenant identifier for multi-tenant scenarios
        
        Returns:
            JSON string with deal details
        """
        try:
            # Validate inputs
            params = DealGetParams(deal_id=deal_id, user_id=user_id)
            
            client = get_client()
            result = await client.get_deal(deal_id=params.deal_id, user_id=params.user_id)
            return json.dumps(result, indent=2)
        except PydanticValidationError as e:
            return json.dumps(safe_error_response(e, "get_deal"), indent=2)
        except Exception as e:
            return json.dumps(safe_error_response(e, "get_deal"), indent=2)
    
    @mcp.tool()
    async def create_deal(
        name: str,
        crm_pipeline_id: int,
        crm_stage_id: int,
        size: Optional[float] = None,
        currency: Optional[str] = None,
        contact_id: Optional[int] = None,
        company_id: Optional[int] = None,
        amount: Optional[float] = None,
        expected_close_date: Optional[str] = None,
        description: Optional[str] = None,
        custom_fields: Optional[str] = None,
        additional_fields: Optional[str] = None,
        user_id: Optional[str] = None,
    ) -> str:
        """
        Create a new deal in Qontak CRM.
        
        WORKFLOW:
        1. Call get_required_fields_for_deal(crm_pipeline_id, crm_stage_id) first
        2. Ask the user for values for all required fields shown in the response
        3. For dropdown fields, present the available options to the user
        4. Call this tool with all required field values
        
        IMPORTANT NOTES:
        - Required fields vary by pipeline and stage configuration
        - Standard fields (like size, currency) are passed as direct parameters
        - Custom/additional fields must be passed in the additional_fields JSON parameter
        - For dropdown fields, use the exact ID or name from dropdown_options
        
        Args:
            name: Deal name/title (required)
            crm_pipeline_id: CRM pipeline ID (required)
            crm_stage_id: CRM pipeline stage ID (required)
            size: Deal size/value (may be required - check with get_required_fields_for_deal)
            currency: Currency code (may be required - check with get_required_fields_for_deal)
            contact_id: Optional associated contact ID
            company_id: Optional associated company ID
            amount: Optional deal value/amount
            expected_close_date: Optional expected close date (format: YYYY-MM-DD)
            description: Optional deal description
            custom_fields: DEPRECATED - Use additional_fields instead
            additional_fields: JSON array of custom field objects. Format: '[{"id": 123, "name": "field_name", "value": "field_value"}]'
                              For dropdown fields, value should be the option ID or name from the template
            user_id: Optional user/tenant identifier for multi-tenant scenarios
        
        Returns:
            JSON string with the created deal details including ID, slug, and all field values
        
        Example additional_fields:
            '[{"id": 123, "name": "industry", "value": "Technology"}, {"id": 124, "name": "budget", "value": 50000}]'
        """
        try:
            # Parse custom_fields JSON if provided (deprecated, use additional_fields)
            parsed_custom_fields = None
            if custom_fields is not None:
                try:
                    parsed_custom_fields = json.loads(custom_fields)
                except json.JSONDecodeError:
                    return json.dumps({
                        "success": False,
                        "error": "Invalid JSON format in custom_fields"
                    }, indent=2)
            
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
            params = DealCreateParams(
                name=name,
                crm_pipeline_id=crm_pipeline_id,
                crm_stage_id=crm_stage_id,
                size=size,
                contact_id=contact_id,
                company_id=company_id,
                amount=amount,
                expected_close_date=expected_close_date,
                description=description,
                custom_fields=parsed_custom_fields,
                user_id=user_id,
            )
            
            # Build deal data
            deal_data: dict[str, Any] = {
                "name": params.name,
                "crm_pipeline_id": params.crm_pipeline_id,
                "crm_stage_id": params.crm_stage_id,
            }
            
            if params.size is not None:
                deal_data["size"] = params.size
            if currency is not None:
                deal_data["currency"] = currency
            if params.contact_id is not None:
                deal_data["contact_id"] = params.contact_id
            if params.company_id is not None:
                deal_data["company_id"] = params.company_id
            if params.amount is not None:
                deal_data["amount"] = params.amount
            if params.expected_close_date is not None:
                deal_data["expected_close_date"] = params.expected_close_date
            if params.description is not None:
                deal_data["description"] = params.description
            
            # Add additional_fields array (required by API, empty array if not provided)
            if parsed_additional_fields is not None:
                deal_data["additional_fields"] = parsed_additional_fields
            elif params.custom_fields is not None:
                # Fallback for deprecated custom_fields - convert to array if needed
                deal_data["custom_fields"] = params.custom_fields
            else:
                deal_data["additional_fields"] = []
            
            client = get_client()
            result = await client.create_deal(deal_data=deal_data, user_id=params.user_id)
            return json.dumps(result, indent=2)
        except PydanticValidationError as e:
            return json.dumps(safe_error_response(e, "create_deal"), indent=2)
        except Exception as e:
            return json.dumps(safe_error_response(e, "create_deal"), indent=2)
    
    @mcp.tool()
    async def update_deal(
        deal_id: int,
        name: Optional[str] = None,
        crm_pipeline_id: Optional[int] = None,
        crm_stage_id: Optional[int] = None,
        contact_id: Optional[int] = None,
        company_id: Optional[int] = None,
        amount: Optional[float] = None,
        expected_close_date: Optional[str] = None,
        description: Optional[str] = None,
        custom_fields: Optional[str] = None,
        user_id: Optional[str] = None,
    ) -> str:
        """
        Update an existing deal.
        
        Updates a deal in Qontak CRM. Only provided fields will be updated.
        
        Args:
            deal_id: The ID of the deal to update (required)
            name: Optional new deal name
            crm_pipeline_id: Optional new CRM pipeline ID
            crm_stage_id: Optional new CRM stage ID
            contact_id: Optional new associated contact ID
            company_id: Optional new associated company ID
            amount: Optional new deal value/amount
            expected_close_date: Optional new expected close date (format: YYYY-MM-DD)
            description: Optional new deal description
            custom_fields: Optional JSON string of custom field values to update
            user_id: Optional user/tenant identifier for multi-tenant scenarios
        
        Returns:
            JSON string with the updated deal details
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
            
            # Validate with Pydantic
            params = DealUpdateParams(
                deal_id=deal_id,
                name=name,
                crm_pipeline_id=crm_pipeline_id,
                crm_stage_id=crm_stage_id,
                contact_id=contact_id,
                company_id=company_id,
                amount=amount,
                expected_close_date=expected_close_date,
                description=description,
                custom_fields=parsed_custom_fields,
                user_id=user_id,
            )
            
            # Build update data
            deal_data: dict[str, Any] = {}
            
            if params.name is not None:
                deal_data["name"] = params.name
            if params.crm_pipeline_id is not None:
                deal_data["crm_pipeline_id"] = params.crm_pipeline_id
            if params.crm_stage_id is not None:
                deal_data["crm_stage_id"] = params.crm_stage_id
            if params.contact_id is not None:
                deal_data["contact_id"] = params.contact_id
            if params.company_id is not None:
                deal_data["company_id"] = params.company_id
            if params.amount is not None:
                deal_data["amount"] = params.amount
            if params.expected_close_date is not None:
                deal_data["expected_close_date"] = params.expected_close_date
            if params.description is not None:
                deal_data["description"] = params.description
            if params.custom_fields is not None:
                deal_data["custom_fields"] = params.custom_fields
            
            client = get_client()
            result = await client.update_deal(
                deal_id=params.deal_id, deal_data=deal_data, user_id=params.user_id
            )
            return json.dumps(result, indent=2)
        except PydanticValidationError as e:
            return json.dumps(safe_error_response(e, "update_deal"), indent=2)
        except Exception as e:
            return json.dumps(safe_error_response(e, "update_deal"), indent=2)
    
    @mcp.tool()
    async def get_deal_timeline(
        deal_id: int,
        page: int = 1,
        per_page: int = 25,
        user_id: Optional[str] = None,
    ) -> str:
        """
        Get the activity timeline for a deal.
        
        Retrieves the chronological activity history for a specific deal,
        including notes, calls, emails, and other interactions.
        
        Args:
            deal_id: The ID of the deal
            page: Page number (default: 1)
            per_page: Number of activities per page (default: 25)
            user_id: Optional user/tenant identifier for multi-tenant scenarios
        
        Returns:
            JSON string with deal timeline activities
        """
        try:
            # Validate inputs
            params = DealTimelineParams(
                deal_id=deal_id,
                page=page,
                per_page=per_page,
                user_id=user_id,
            )
            
            client = get_client()
            result = await client.get_deal_timeline(
                deal_id=params.deal_id,
                page=params.page,
                per_page=params.per_page,
                user_id=params.user_id,
            )
            return json.dumps(result, indent=2)
        except PydanticValidationError as e:
            return json.dumps(safe_error_response(e, "get_deal_timeline"), indent=2)
        except Exception as e:
            return json.dumps(safe_error_response(e, "get_deal_timeline"), indent=2)
    
    @mcp.tool()
    async def get_deal_stage_history(
        deal_id: int,
        page: int = 1,
        per_page: int = 25,
        user_id: Optional[str] = None,
    ) -> str:
        """
        Get the stage change history for a deal.
        
        Retrieves the history of pipeline stage changes for a specific deal,
        showing when and how the deal moved through the sales pipeline.
        
        Args:
            deal_id: The ID of the deal
            page: Page number (default: 1)
            per_page: Number of entries per page (default: 25)
            user_id: Optional user/tenant identifier for multi-tenant scenarios
        
        Returns:
            JSON string with deal stage history
        """
        try:
            # Validate inputs
            params = DealTimelineParams(
                deal_id=deal_id,
                page=page,
                per_page=per_page,
                user_id=user_id,
            )
            
            client = get_client()
            result = await client.get_deal_stage_history(
                deal_id=params.deal_id,
                page=params.page,
                per_page=params.per_page,
                user_id=params.user_id,
            )
            return json.dumps(result, indent=2)
        except PydanticValidationError as e:
            return json.dumps(safe_error_response(e, "get_deal_stage_history"), indent=2)
        except Exception as e:
            return json.dumps(safe_error_response(e, "get_deal_stage_history"), indent=2)
    
    @mcp.tool()
    async def list_pipelines(user_id: Optional[str] = None) -> str:
        """
        List all available pipelines.
        
        Retrieves a list of all pipelines in the CRM. Use this to get the 
        crm_pipeline_id values needed when creating or updating deals.
        Each pipeline contains multiple stages that deals progress through.
        
        Args:
            user_id: Optional user/tenant identifier for multi-tenant scenarios
        
        Returns:
            JSON string with list of pipelines, including their IDs and names
        """
        try:
            client = get_client()
            result = await client.list_pipelines(user_id=user_id)
            return json.dumps(result, indent=2)
        except Exception as e:
            return json.dumps(safe_error_response(e, "list_pipelines"), indent=2)
    
    @mcp.tool()
    async def get_pipeline(
        pipeline_id: int, 
        user_id: Optional[str] = None
    ) -> str:
        """
        Get details of a specific pipeline.
        
        Retrieves detailed information about a single pipeline by its ID.
        
        Args:
            pipeline_id: The ID of the pipeline to retrieve
            user_id: Optional user/tenant identifier for multi-tenant scenarios
        
        Returns:
            JSON string with pipeline details
        """
        try:
            client = get_client()
            result = await client.get_pipeline(pipeline_id=pipeline_id, user_id=user_id)
            return json.dumps(result, indent=2)
        except Exception as e:
            return json.dumps(safe_error_response(e, "get_pipeline"), indent=2)
    
    @mcp.tool()
    async def list_pipeline_stages(
        pipeline_id: int,
        user_id: Optional[str] = None
    ) -> str:
        """
        List all stages for a specific pipeline.
        
        Retrieves all stages within a pipeline. Use this to get the crm_stage_id 
        values needed when creating or updating deals. Each stage represents a 
        step in the sales process (e.g., "New", "Qualified", "Proposal", "Won").
        
        Args:
            pipeline_id: The ID of the pipeline to get stages from
            user_id: Optional user/tenant identifier for multi-tenant scenarios
        
        Returns:
            JSON string with list of stages, including their IDs, names, and order
        """
        try:
            client = get_client()
            result = await client.list_pipeline_stages(
                pipeline_id=pipeline_id, 
                user_id=user_id
            )
            return json.dumps(result, indent=2)
        except Exception as e:
            return json.dumps(safe_error_response(e, "list_pipeline_stages"), indent=2)
    
    @mcp.tool()
    async def get_required_fields_for_deal(
        crm_pipeline_id: int,
        crm_stage_id: int,
        user_id: Optional[str] = None
    ) -> str:
        """
        Get required and optional fields for creating a deal in a specific pipeline and stage.
        
        This tool analyzes the deal template and returns detailed information about which 
        fields are required and optional for the given pipeline/stage combination. 
        
        IMPORTANT: Use this tool BEFORE creating a deal to:
        1. Know which fields are required (must be provided)
        2. Get dropdown options for fields that have predefined values
        3. Understand field types and constraints
        
        The LLM should use this information to ask the user for required field values.
        
        Args:
            crm_pipeline_id: The CRM pipeline ID
            crm_stage_id: The CRM stage ID within the pipeline
            user_id: Optional user/tenant identifier for multi-tenant scenarios
        
        Returns:
            JSON string with detailed field information:
            - required_standard_fields: Standard required fields with types and options
            - required_custom_fields: Custom required fields with types and options
            - optional_standard_fields: Standard optional fields
            - optional_custom_fields: Custom optional fields
            - Each field includes:
              * name: Field API name
              * name_alias: Human-readable field name
              * type: Field type (Single-line text, Number, Dropdown select, etc.)
              * dropdown_options: Available options for dropdown fields (if applicable)
              * id: Field ID (for custom fields)
        """
        try:
            client = get_client()
            template_result = await client.get_deal_template(user_id=user_id)
            
            if not template_result.get("success"):
                return json.dumps(template_result, indent=2)
            
            fields = template_result.get("data", {}).get("response", [])
            
            required_standard = []
            required_custom = []
            optional_standard = []
            optional_custom = []
            
            for field in fields:
                name = field.get("name")
                field_type = field.get("type")
                is_additional = field.get("additional_field", False)
                req_pipelines = field.get("required_pipeline_ids", [])
                req_stages = field.get("required_stage_ids", [])
                dropdown = field.get("dropdown")
                field_id = field.get("id")
                
                # Check if required for this pipeline/stage
                is_required = (
                    crm_pipeline_id in req_pipelines or 
                    crm_stage_id in req_stages
                )
                
                field_info = {
                    "name": name,
                    "name_alias": field.get("name_alias"),
                    "type": field_type,
                }
                
                # Add field ID for custom fields
                if field_id is not None:
                    field_info["id"] = field_id
                
                # Add dropdown options if available
                if dropdown:
                    field_info["dropdown_options"] = dropdown
                    field_info["has_dropdown"] = True
                else:
                    field_info["has_dropdown"] = False
                
                # Add field description based on type
                if field_type == "Single-line text":
                    field_info["description"] = "Text input, single line"
                elif field_type == "Text Area":
                    field_info["description"] = "Text input, multiple lines"
                elif field_type == "Number":
                    field_info["description"] = "Numeric value"
                elif field_type == "Date":
                    field_info["description"] = "Date value (format: YYYY-MM-DD)"
                elif field_type == "Dropdown select":
                    if dropdown:
                        option_count = len(dropdown)
                        field_info["description"] = f"Select one option from {option_count} available choices"
                    else:
                        field_info["description"] = "Select one option from available choices"
                
                # Categorize the field
                if is_required:
                    if is_additional:
                        required_custom.append(field_info)
                    else:
                        required_standard.append(field_info)
                else:
                    if is_additional:
                        optional_custom.append(field_info)
                    else:
                        optional_standard.append(field_info)
            
            result = {
                "success": True,
                "pipeline_id": crm_pipeline_id,
                "stage_id": crm_stage_id,
                "required_standard_fields": required_standard,
                "required_custom_fields": required_custom,
                "optional_standard_fields": optional_standard[:10],  # Limit to first 10
                "optional_custom_fields": optional_custom[:10],  # Limit to first 10
                "summary": {
                    "total_required": len(required_standard) + len(required_custom),
                    "required_standard_count": len(required_standard),
                    "required_custom_count": len(required_custom),
                    "note": "The LLM should ask the user for values for all required fields. For dropdown fields, present the available options to the user."
                }
            }
            
            return json.dumps(result, indent=2)
        except Exception as e:
            return json.dumps(safe_error_response(e, "get_required_fields_for_deal"), indent=2)
    
    @mcp.tool()
    async def get_deal_chat_history(
        deal_id: int,
        page: int = 1,
        per_page: int = 25,
        user_id: Optional[str] = None,
    ) -> str:
        """
        Get the chat history for a deal.
        
        Retrieves chat conversations associated with this deal.
        Requires CRM integration with chat panel.
        
        Args:
            deal_id: The ID of the deal
            page: Page number (default: 1)
            per_page: Number of messages per page (default: 25)
            user_id: Optional user/tenant identifier
        
        Returns:
            JSON string with deal chat history
        """
        try:
            params = DealTimelineParams(deal_id=deal_id, page=page, per_page=per_page, user_id=user_id)
            client = get_client()
            result = await client.get_deal_chat_history(
                deal_id=params.deal_id, page=params.page, per_page=params.per_page, user_id=params.user_id
            )
            return json.dumps(result, indent=2)
        except Exception as e:
            return json.dumps(safe_error_response(e, "get_deal_chat_history"), indent=2)
    
    @mcp.tool()
    async def get_deal_real_creator(deal_id: int, user_id: Optional[str] = None) -> str:
        """
        Get the real creator (original creator) of a deal.
        
        Returns information about who originally created the deal.
        
        Args:
            deal_id: The ID of the deal
            user_id: Optional user/tenant identifier
        
        Returns:
            JSON string with creator information
        """
        try:
            params = DealGetParams(deal_id=deal_id, user_id=user_id)
            client = get_client()
            result = await client.get_deal_real_creator(deal_id=params.deal_id, user_id=params.user_id)
            return json.dumps(result, indent=2)
        except Exception as e:
            return json.dumps(safe_error_response(e, "get_deal_real_creator"), indent=2)
    
    @mcp.tool()
    async def get_deal_full_field(deal_id: int, user_id: Optional[str] = None) -> str:
        """
        Get deal with complete field information.
        
        Returns a deal with download-like fields and complete details.
        
        Args:
            deal_id: The ID of the deal
            user_id: Optional user/tenant identifier
        
        Returns:
            JSON string with complete deal field information
        """
        try:
            params = DealGetParams(deal_id=deal_id, user_id=user_id)
            client = get_client()
            result = await client.get_deal_full_field(deal_id=params.deal_id, user_id=params.user_id)
            return json.dumps(result, indent=2)
        except Exception as e:
            return json.dumps(safe_error_response(e, "get_deal_full_field"), indent=2)
    
    @mcp.tool()
    async def get_deal_permissions(deal_id: int, user_id: Optional[str] = None) -> str:
        """
        Get permissions for a deal.
        
        Returns the permission settings for the specified deal including
        who has access and what operations they can perform.
        
        Args:
            deal_id: The ID of the deal
            user_id: Optional user/tenant identifier
        
        Returns:
            JSON string with deal permissions information
        """
        try:
            params = DealGetParams(deal_id=deal_id, user_id=user_id)
            client = get_client()
            result = await client.get_deal_permissions(deal_id=params.deal_id, user_id=params.user_id)
            return json.dumps(result, indent=2)
        except Exception as e:
            return json.dumps(safe_error_response(e, "get_deal_permissions"), indent=2)
    
    @mcp.tool()
    async def update_deal_owner(
        deal_id: int,
        creator_id: int,
        user_id: Optional[str] = None,
    ) -> str:
        """
        Update the owner of a deal.
        
        Changes the user who owns/manages this deal.
        
        Args:
            deal_id: The ID of the deal to update (required)
            creator_id: The ID of the new owner/user (required)
            user_id: Optional user/tenant identifier
        
        Returns:
            JSON string with the updated deal details
        """
        try:
            params = DealGetParams(deal_id=deal_id, user_id=user_id)
            client = get_client()
            result = await client.update_deal_owner(
                deal_id=params.deal_id, creator_id=creator_id, user_id=params.user_id
            )
            return json.dumps(result, indent=2)
        except Exception as e:
            return json.dumps(safe_error_response(e, "update_deal_owner"), indent=2)
