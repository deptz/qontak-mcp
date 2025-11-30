"""
MCP Tools for Qontak CRM Contacts.

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
    ContactListParams,
    ContactGetParams,
    ContactCreateParams,
    ContactUpdateParams,
    ContactTimelineParams,
)
from ..errors import safe_error_response


def register_contact_tools(mcp: FastMCP, client: QontakClient) -> None:
    """
    Register all contact-related MCP tools.
    
    Args:
        mcp: The FastMCP server instance
        client: The QontakClient instance
    """
    register_contact_tools_lazy(mcp, lambda: client)


def register_contact_tools_lazy(
    mcp: FastMCP,
    get_client: Callable[[], QontakClient]
) -> None:
    """
    Register all contact-related MCP tools with lazy client access.
    
    Args:
        mcp: The FastMCP server instance
        get_client: Function that returns the QontakClient instance
    """
    
    @mcp.tool()
    async def get_contact_template(user_id: Optional[str] = None) -> str:
        """
        Get the contact field template/schema.
        
        Returns the available fields, their types, and required field information for 
        creating/updating contacts. Use this to understand what data is required/optional.
        
        Args:
            user_id: Optional user/tenant identifier for multi-tenant scenarios
        
        Returns:
            JSON string with contact template fields, dropdown options, and validation rules
        """
        try:
            client = get_client()
            result = await client.get_contact_template(user_id=user_id)
            return json.dumps(result, indent=2)
        except Exception as e:
            return json.dumps(safe_error_response(e, "get_contact_template"), indent=2)
    
    @mcp.tool()
    async def list_contacts(
        page: int = 1,
        per_page: int = 25,
        user_id: Optional[str] = None,
    ) -> str:
        """
        List contacts with optional filtering and pagination.
        
        Retrieves a paginated list of contacts from Qontak CRM.
        
        Args:
            page: Page number (default: 1)
            per_page: Number of contacts per page (default: 25, max: 100)
            user_id: Optional user/tenant identifier for multi-tenant scenarios
        
        Returns:
            JSON string with list of contacts and pagination info
        """
        try:
            params = ContactListParams(
                page=page,
                per_page=per_page,
                user_id=user_id,
            )
            
            client = get_client()
            result = await client.list_contacts(
                page=params.page,
                per_page=params.per_page,
                user_id=params.user_id,
            )
            return json.dumps(result, indent=2)
        except PydanticValidationError as e:
            return json.dumps(safe_error_response(e, "list_contacts"), indent=2)
        except Exception as e:
            return json.dumps(safe_error_response(e, "list_contacts"), indent=2)
    
    @mcp.tool()
    async def get_contact(contact_id: int, user_id: Optional[str] = None) -> str:
        """
        Get a single contact by ID.
        
        Retrieves detailed information about a specific contact including all fields.
        
        Args:
            contact_id: The ID of the contact to retrieve
            user_id: Optional user/tenant identifier for multi-tenant scenarios
        
        Returns:
            JSON string with contact details
        """
        try:
            params = ContactGetParams(contact_id=contact_id, user_id=user_id)
            
            client = get_client()
            result = await client.get_contact(
                contact_id=params.contact_id, user_id=params.user_id
            )
            return json.dumps(result, indent=2)
        except PydanticValidationError as e:
            return json.dumps(safe_error_response(e, "get_contact"), indent=2)
        except Exception as e:
            return json.dumps(safe_error_response(e, "get_contact"), indent=2)
    
    @mcp.tool()
    async def create_contact(
        first_name: str,
        last_name: Optional[str] = None,
        email: Optional[str] = None,
        telephone: Optional[str] = None,
        job_title: Optional[str] = None,
        crm_status_id: Optional[int] = None,
        crm_company_id: Optional[int] = None,
        address: Optional[str] = None,
        city: Optional[str] = None,
        province: Optional[str] = None,
        country: Optional[str] = None,
        zipcode: Optional[str] = None,
        date_of_birth: Optional[str] = None,
        additional_fields: Optional[str] = None,
        user_id: Optional[str] = None,
    ) -> str:
        """
        Create a new contact in Qontak CRM.
        
        WORKFLOW:
        1. Call get_required_fields_for_contact() first to discover required fields
        2. Ask the user for values for all required fields
        3. For dropdown fields, present the available options
        4. Call this tool with all required field values
        
        Args:
            first_name: Contact first name (required)
            last_name: Optional last name
            email: Optional email address
            telephone: Optional phone number
            job_title: Optional job title
            crm_status_id: Optional status ID (check template for valid values)
            crm_company_id: Optional associated company ID
            address: Optional street address
            city: Optional city
            province: Optional province/state
            country: Optional country
            zipcode: Optional ZIP/postal code
            date_of_birth: Optional date of birth (format: YYYY-MM-DD)
            additional_fields: Optional JSON array of custom fields. Format: '[{"id": 123, "name": "field_name", "value": "value"}]'
            user_id: Optional user/tenant identifier for multi-tenant scenarios
        
        Returns:
            JSON string with the created contact details including ID
        """
        try:
            parsed_additional_fields = None
            if additional_fields is not None:
                try:
                    parsed_additional_fields = json.loads(additional_fields)
                    if not isinstance(parsed_additional_fields, list):
                        return json.dumps({
                            "success": False,
                            "error": "additional_fields must be a JSON array"
                        }, indent=2)
                except json.JSONDecodeError:
                    return json.dumps({
                        "success": False,
                        "error": "Invalid JSON format in additional_fields"
                    }, indent=2)
            
            params = ContactCreateParams(
                first_name=first_name,
                last_name=last_name,
                email=email,
                telephone=telephone,
                job_title=job_title,
                crm_status_id=crm_status_id,
                crm_company_id=crm_company_id,
                address=address,
                city=city,
                province=province,
                country=country,
                zipcode=zipcode,
                date_of_birth=date_of_birth,
                additional_fields=parsed_additional_fields,
                user_id=user_id,
            )
            
            contact_data: dict[str, Any] = {
                "first_name": params.first_name,
            }
            
            if params.last_name is not None:
                contact_data["last_name"] = params.last_name
            if params.email is not None:
                contact_data["email"] = params.email
            if params.telephone is not None:
                contact_data["telephone"] = params.telephone
            if params.job_title is not None:
                contact_data["job_title"] = params.job_title
            if params.crm_status_id is not None:
                contact_data["crm_status_id"] = params.crm_status_id
            if params.crm_company_id is not None:
                contact_data["crm_company_id"] = params.crm_company_id
            if params.address is not None:
                contact_data["address"] = params.address
            if params.city is not None:
                contact_data["city"] = params.city
            if params.province is not None:
                contact_data["province"] = params.province
            if params.country is not None:
                contact_data["country"] = params.country
            if params.zipcode is not None:
                contact_data["zipcode"] = params.zipcode
            if params.date_of_birth is not None:
                contact_data["date_of_birth"] = params.date_of_birth
            
            if parsed_additional_fields:
                contact_data["additional_fields"] = parsed_additional_fields
            else:
                contact_data["additional_fields"] = []
            
            client = get_client()
            result = await client.create_contact(
                contact_data=contact_data, user_id=params.user_id
            )
            return json.dumps(result, indent=2)
        except PydanticValidationError as e:
            return json.dumps(safe_error_response(e, "create_contact"), indent=2)
        except Exception as e:
            return json.dumps(safe_error_response(e, "create_contact"), indent=2)
    
    @mcp.tool()
    async def update_contact(
        contact_id: int,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        email: Optional[str] = None,
        telephone: Optional[str] = None,
        job_title: Optional[str] = None,
        crm_status_id: Optional[int] = None,
        crm_company_id: Optional[int] = None,
        address: Optional[str] = None,
        city: Optional[str] = None,
        province: Optional[str] = None,
        country: Optional[str] = None,
        zipcode: Optional[str] = None,
        date_of_birth: Optional[str] = None,
        additional_fields: Optional[str] = None,
        user_id: Optional[str] = None,
    ) -> str:
        """
        Update an existing contact.
        
        Updates a contact in Qontak CRM. Only provided fields will be updated.
        
        Args:
            contact_id: The ID of the contact to update (required)
            first_name: Optional new first name
            last_name: Optional new last name
            email: Optional new email address
            telephone: Optional new phone number
            job_title: Optional new job title
            crm_status_id: Optional new status ID
            crm_company_id: Optional new associated company ID
            address: Optional new street address
            city: Optional new city
            province: Optional new province/state
            country: Optional new country
            zipcode: Optional new ZIP/postal code
            date_of_birth: Optional new date of birth (format: YYYY-MM-DD)
            additional_fields: Optional JSON array of custom fields to update
            user_id: Optional user/tenant identifier for multi-tenant scenarios
        
        Returns:
            JSON string with the updated contact details
        """
        try:
            parsed_additional_fields = None
            if additional_fields is not None:
                try:
                    parsed_additional_fields = json.loads(additional_fields)
                except json.JSONDecodeError:
                    return json.dumps({
                        "success": False,
                        "error": "Invalid JSON format in additional_fields"
                    }, indent=2)
            
            params = ContactUpdateParams(
                contact_id=contact_id,
                first_name=first_name,
                last_name=last_name,
                email=email,
                telephone=telephone,
                job_title=job_title,
                crm_status_id=crm_status_id,
                crm_company_id=crm_company_id,
                address=address,
                city=city,
                province=province,
                country=country,
                zipcode=zipcode,
                date_of_birth=date_of_birth,
                additional_fields=parsed_additional_fields,
                user_id=user_id,
            )
            
            contact_data: dict[str, Any] = {}
            
            if params.first_name is not None:
                contact_data["first_name"] = params.first_name
            if params.last_name is not None:
                contact_data["last_name"] = params.last_name
            if params.email is not None:
                contact_data["email"] = params.email
            if params.telephone is not None:
                contact_data["telephone"] = params.telephone
            if params.job_title is not None:
                contact_data["job_title"] = params.job_title
            if params.crm_status_id is not None:
                contact_data["crm_status_id"] = params.crm_status_id
            if params.crm_company_id is not None:
                contact_data["crm_company_id"] = params.crm_company_id
            if params.address is not None:
                contact_data["address"] = params.address
            if params.city is not None:
                contact_data["city"] = params.city
            if params.province is not None:
                contact_data["province"] = params.province
            if params.country is not None:
                contact_data["country"] = params.country
            if params.zipcode is not None:
                contact_data["zipcode"] = params.zipcode
            if params.date_of_birth is not None:
                contact_data["date_of_birth"] = params.date_of_birth
            if params.additional_fields is not None:
                contact_data["additional_fields"] = params.additional_fields
            
            client = get_client()
            result = await client.update_contact(
                contact_id=params.contact_id,
                contact_data=contact_data,
                user_id=params.user_id
            )
            return json.dumps(result, indent=2)
        except PydanticValidationError as e:
            return json.dumps(safe_error_response(e, "update_contact"), indent=2)
        except Exception as e:
            return json.dumps(safe_error_response(e, "update_contact"), indent=2)
    
    @mcp.tool()
    async def delete_contact(
        contact_id: int,
        user_id: Optional[str] = None,
    ) -> str:
        """
        Delete a contact.
        
        Permanently deletes a contact by its ID.
        
        Args:
            contact_id: The ID of the contact to delete (required)
            user_id: Optional user/tenant identifier for multi-tenant scenarios
        
        Returns:
            JSON string confirming the deletion
        """
        try:
            params = ContactGetParams(contact_id=contact_id, user_id=user_id)
            
            client = get_client()
            result = await client.delete_contact(
                contact_id=params.contact_id, user_id=params.user_id
            )
            return json.dumps(result, indent=2)
        except PydanticValidationError as e:
            return json.dumps(safe_error_response(e, "delete_contact"), indent=2)
        except Exception as e:
            return json.dumps(safe_error_response(e, "delete_contact"), indent=2)
    
    @mcp.tool()
    async def get_contact_timeline(
        contact_id: int,
        page: int = 1,
        per_page: int = 25,
        user_id: Optional[str] = None,
    ) -> str:
        """
        Get the activity timeline for a contact.
        
        Retrieves the chronological activity history for a specific contact,
        including notes, calls, emails, and other interactions.
        
        Args:
            contact_id: The ID of the contact
            page: Page number (default: 1)
            per_page: Number of activities per page (default: 25)
            user_id: Optional user/tenant identifier for multi-tenant scenarios
        
        Returns:
            JSON string with contact timeline activities
        """
        try:
            params = ContactTimelineParams(
                contact_id=contact_id,
                page=page,
                per_page=per_page,
                user_id=user_id,
            )
            
            client = get_client()
            result = await client.get_contact_timeline(
                contact_id=params.contact_id,
                page=params.page,
                per_page=params.per_page,
                user_id=params.user_id,
            )
            return json.dumps(result, indent=2)
        except PydanticValidationError as e:
            return json.dumps(safe_error_response(e, "get_contact_timeline"), indent=2)
        except Exception as e:
            return json.dumps(safe_error_response(e, "get_contact_timeline"), indent=2)
    
    @mcp.tool()
    async def get_contact_chat_history(
        contact_id: int,
        page: int = 1,
        per_page: int = 25,
        user_id: Optional[str] = None,
    ) -> str:
        """
        Get the chat history for a contact.
        
        Retrieves chat conversations and messages associated with this contact.
        Requires CRM integration with chat panel.
        
        Args:
            contact_id: The ID of the contact
            page: Page number (default: 1)
            per_page: Number of messages per page (default: 25)
            user_id: Optional user/tenant identifier for multi-tenant scenarios
        
        Returns:
            JSON string with contact chat history
        """
        try:
            params = ContactTimelineParams(
                contact_id=contact_id,
                page=page,
                per_page=per_page,
                user_id=user_id,
            )
            
            client = get_client()
            result = await client.get_contact_chat_history(
                contact_id=params.contact_id,
                page=params.page,
                per_page=params.per_page,
                user_id=params.user_id,
            )
            return json.dumps(result, indent=2)
        except PydanticValidationError as e:
            return json.dumps(safe_error_response(e, "get_contact_chat_history"), indent=2)
        except Exception as e:
            return json.dumps(safe_error_response(e, "get_contact_chat_history"), indent=2)
    
    @mcp.tool()
    async def update_contact_owner(
        contact_id: int,
        creator_id: int,
        user_id: Optional[str] = None,
    ) -> str:
        """
        Update the owner of a contact.
        
        Changes the user who owns/manages this contact.
        
        Args:
            contact_id: The ID of the contact to update (required)
            creator_id: The ID of the new owner/user (required)
            user_id: Optional user/tenant identifier for multi-tenant scenarios
        
        Returns:
            JSON string with the updated contact details
        """
        try:
            params = ContactGetParams(contact_id=contact_id, user_id=user_id)
            
            client = get_client()
            result = await client.update_contact_owner(
                contact_id=params.contact_id,
                creator_id=creator_id,
                user_id=params.user_id
            )
            return json.dumps(result, indent=2)
        except PydanticValidationError as e:
            return json.dumps(safe_error_response(e, "update_contact_owner"), indent=2)
        except Exception as e:
            return json.dumps(safe_error_response(e, "update_contact_owner"), indent=2)
    
    @mcp.tool()
    async def get_required_fields_for_contact(user_id: Optional[str] = None) -> str:
        """
        Get required and optional fields for creating/updating contacts.
        
        Analyzes the contact template to determine which fields are required and optional.
        Returns detailed information about field types, dropdown options, and constraints.
        
        WORKFLOW FOR LLMs:
        1. Call this tool to discover all available contact fields
        2. Review the required_standard_fields and required_custom_fields
        3. Ask the user for values for all required fields
        4. For dropdown fields, present the available options to the user
        5. Call create_contact() with all required field values
        
        Args:
            user_id: Optional user/tenant identifier for multi-tenant scenarios
        
        Returns:
            JSON string with comprehensive field information including:
            - required_standard_fields: Standard required fields
            - required_custom_fields: Custom required fields
            - optional_standard_fields: Standard optional fields
            - optional_custom_fields: Custom optional fields
            Each field includes: name, name_alias, type, dropdown_options (if applicable)
        """
        try:
            client = get_client()
            template = await client.get_contact_template(user_id=user_id)
            
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
                "required_standard_fields": required_standard_fields,
                "required_custom_fields": required_custom_fields,
                "optional_standard_fields": optional_standard_fields,
                "optional_custom_fields": optional_custom_fields,
                "summary": {
                    "total_fields": len(fields),
                    "total_required": len(required_standard_fields) + len(required_custom_fields),
                    "required_standard": len(required_standard_fields),
                    "required_custom": len(required_custom_fields),
                    "note": "Use this information to ask the user for required field values. For dropdown fields, present the available options."
                }
            }
            
            return json.dumps(result, indent=2)
        except Exception as e:
            return json.dumps(safe_error_response(e, "get_required_fields_for_contact"), indent=2)
