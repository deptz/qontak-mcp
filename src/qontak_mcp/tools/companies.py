"""
MCP Tools for Qontak CRM Companies.

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
    CompanyListParams,
    CompanyGetParams,
    CompanyCreateParams,
    CompanyUpdateParams,
    CompanyTimelineParams,
)
from ..errors import safe_error_response


def register_company_tools(mcp: FastMCP, client: QontakClient) -> None:
    """Register all company-related MCP tools."""
    register_company_tools_lazy(mcp, lambda: client)


def register_company_tools_lazy(
    mcp: FastMCP,
    get_client: Callable[[], QontakClient]
) -> None:
    """Register all company-related MCP tools with lazy client access."""
    
    @mcp.tool()
    async def get_company_template(user_id: Optional[str] = None) -> str:
        """
        Get the company field template/schema.
        
        Returns the available fields, their types, and required field information.
        
        Args:
            user_id: Optional user/tenant identifier
        
        Returns:
            JSON string with company template fields
        """
        try:
            client = get_client()
            result = await client.get_company_template(user_id=user_id)
            return json.dumps(result, indent=2)
        except Exception as e:
            return json.dumps(safe_error_response(e, "get_company_template"), indent=2)
    
    @mcp.tool()
    async def list_companies(
        page: int = 1,
        per_page: int = 25,
        user_id: Optional[str] = None,
    ) -> str:
        """
        List companies with pagination.
        
        Args:
            page: Page number (default: 1)
            per_page: Number per page (default: 25, max: 100)
            user_id: Optional user/tenant identifier
        
        Returns:
            JSON string with list of companies
        """
        try:
            params = CompanyListParams(page=page, per_page=per_page, user_id=user_id)
            client = get_client()
            result = await client.list_companies(page=params.page, per_page=params.per_page, user_id=params.user_id)
            return json.dumps(result, indent=2)
        except Exception as e:
            return json.dumps(safe_error_response(e, "list_companies"), indent=2)
    
    @mcp.tool()
    async def get_company(company_id: int, user_id: Optional[str] = None) -> str:
        """Get a single company by ID."""
        try:
            params = CompanyGetParams(company_id=company_id, user_id=user_id)
            client = get_client()
            result = await client.get_company(company_id=params.company_id, user_id=params.user_id)
            return json.dumps(result, indent=2)
        except Exception as e:
            return json.dumps(safe_error_response(e, "get_company"), indent=2)
    
    @mcp.tool()
    async def create_company(
        name: str,
        crm_status_id: Optional[int] = None,
        address: Optional[str] = None,
        city: Optional[str] = None,
        province: Optional[str] = None,
        country: Optional[str] = None,
        zipcode: Optional[str] = None,
        telephone: Optional[str] = None,
        email: Optional[str] = None,
        website: Optional[str] = None,
        additional_fields: Optional[str] = None,
        user_id: Optional[str] = None,
    ) -> str:
        """Create a new company."""
        try:
            parsed_additional = None
            if additional_fields:
                parsed_additional = json.loads(additional_fields)
            
            params = CompanyCreateParams(
                name=name, crm_status_id=crm_status_id, address=address,
                city=city, province=province, country=country, zipcode=zipcode,
                telephone=telephone, email=email, website=website,
                additional_fields=parsed_additional, user_id=user_id
            )
            
            company_data: dict[str, Any] = {"name": params.name}
            if params.crm_status_id: company_data["crm_status_id"] = params.crm_status_id
            if params.address: company_data["address"] = params.address
            if params.city: company_data["city"] = params.city
            if params.province: company_data["province"] = params.province
            if params.country: company_data["country"] = params.country
            if params.zipcode: company_data["zipcode"] = params.zipcode
            if params.telephone: company_data["telephone"] = params.telephone
            if params.email: company_data["email"] = params.email
            if params.website: company_data["website"] = params.website
            company_data["additional_fields"] = parsed_additional or []
            
            client = get_client()
            result = await client.create_company(company_data=company_data, user_id=params.user_id)
            return json.dumps(result, indent=2)
        except Exception as e:
            return json.dumps(safe_error_response(e, "create_company"), indent=2)
    
    @mcp.tool()
    async def update_company(
        company_id: int,
        name: Optional[str] = None,
        crm_status_id: Optional[int] = None,
        address: Optional[str] = None,
        city: Optional[str] = None,
        province: Optional[str] = None,
        country: Optional[str] = None,
        zipcode: Optional[str] = None,
        telephone: Optional[str] = None,
        email: Optional[str] = None,
        website: Optional[str] = None,
        additional_fields: Optional[str] = None,
        user_id: Optional[str] = None,
    ) -> str:
        """Update an existing company."""
        try:
            parsed_additional = None
            if additional_fields:
                parsed_additional = json.loads(additional_fields)
            
            params = CompanyUpdateParams(
                company_id=company_id, name=name, crm_status_id=crm_status_id,
                address=address, city=city, province=province, country=country,
                zipcode=zipcode, telephone=telephone, email=email, website=website,
                additional_fields=parsed_additional, user_id=user_id
            )
            
            company_data: dict[str, Any] = {}
            if params.name: company_data["name"] = params.name
            if params.crm_status_id: company_data["crm_status_id"] = params.crm_status_id
            if params.address: company_data["address"] = params.address
            if params.city: company_data["city"] = params.city
            if params.province: company_data["province"] = params.province
            if params.country: company_data["country"] = params.country
            if params.zipcode: company_data["zipcode"] = params.zipcode
            if params.telephone: company_data["telephone"] = params.telephone
            if params.email: company_data["email"] = params.email
            if params.website: company_data["website"] = params.website
            if params.additional_fields: company_data["additional_fields"] = params.additional_fields
            
            client = get_client()
            result = await client.update_company(company_id=params.company_id, company_data=company_data, user_id=params.user_id)
            return json.dumps(result, indent=2)
        except Exception as e:
            return json.dumps(safe_error_response(e, "update_company"), indent=2)
    
    @mcp.tool()
    async def delete_company(company_id: int, user_id: Optional[str] = None) -> str:
        """Delete a company."""
        try:
            params = CompanyGetParams(company_id=company_id, user_id=user_id)
            client = get_client()
            result = await client.delete_company(company_id=params.company_id, user_id=params.user_id)
            return json.dumps(result, indent=2)
        except Exception as e:
            return json.dumps(safe_error_response(e, "delete_company"), indent=2)
    
    @mcp.tool()
    async def get_company_timeline(
        company_id: int,
        page: int = 1,
        per_page: int = 25,
        user_id: Optional[str] = None,
    ) -> str:
        """Get the activity timeline for a company."""
        try:
            params = CompanyTimelineParams(company_id=company_id, page=page, per_page=per_page, user_id=user_id)
            client = get_client()
            result = await client.get_company_timeline(company_id=params.company_id, page=params.page, per_page=params.per_page, user_id=params.user_id)
            return json.dumps(result, indent=2)
        except Exception as e:
            return json.dumps(safe_error_response(e, "get_company_timeline"), indent=2)
    
    @mcp.tool()
    async def get_required_fields_for_company(user_id: Optional[str] = None) -> str:
        """Get required and optional fields for creating/updating companies."""
        try:
            client = get_client()
            template = await client.get_company_template(user_id=user_id)
            if not template.get("success"):
                return json.dumps(template, indent=2)
            
            fields = template.get("data", {}).get("response", [])
            required_standard = []
            required_custom = []
            optional_standard = []
            optional_custom = []
            
            for field in fields:
                field_info = {
                    "name": field.get("name", ""),
                    "name_alias": field.get("name_alias", ""),
                    "type": field.get("type", ""),
                    "required": field.get("required", False),
                    "has_dropdown": bool(field.get("dropdown")),
                }
                if field.get("id"): field_info["id"] = field["id"]
                if field.get("dropdown"): field_info["dropdown_options"] = field["dropdown"]
                
                is_required = field.get("required", False)
                is_additional = field.get("additional_field", False)
                
                if is_required:
                    (required_custom if is_additional else required_standard).append(field_info)
                else:
                    (optional_custom if is_additional else optional_standard).append(field_info)
            
            result = {
                "success": True,
                "required_standard_fields": required_standard,
                "required_custom_fields": required_custom,
                "optional_standard_fields": optional_standard,
                "optional_custom_fields": optional_custom,
                "summary": {
                    "total_required": len(required_standard) + len(required_custom),
                    "required_standard": len(required_standard),
                    "required_custom": len(required_custom),
                }
            }
            return json.dumps(result, indent=2)
        except Exception as e:
            return json.dumps(safe_error_response(e, "get_required_fields_for_company"), indent=2)
