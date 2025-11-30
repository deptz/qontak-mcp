"""
MCP Tools for Qontak CRM Products Association.
"""

import json
from typing import Optional, Any, Callable
from mcp.server.fastmcp import FastMCP
from ..client import QontakClient
from ..models import ProductsAssociationListParams, ProductsAssociationGetParams, ProductsAssociationCreateParams, ProductsAssociationUpdateParams
from ..errors import safe_error_response


def register_products_association_tools(mcp: FastMCP, client: QontakClient) -> None:
    """Register all product association-related MCP tools."""
    register_products_association_tools_lazy(mcp, lambda: client)


def register_products_association_tools_lazy(mcp: FastMCP, get_client: Callable[[], QontakClient]) -> None:
    """Register all product association-related MCP tools with lazy client access."""
    
    @mcp.tool()
    async def list_products_associations(page: int = 1, per_page: int = 25, user_id: Optional[str] = None) -> str:
        """List product associations with pagination."""
        try:
            params = ProductsAssociationListParams(page=page, per_page=per_page, user_id=user_id)
            client = get_client()
            result = await client.list_products_associations(page=params.page, per_page=params.per_page, user_id=params.user_id)
            return json.dumps(result, indent=2)
        except Exception as e:
            return json.dumps(safe_error_response(e, "list_products_associations"), indent=2)
    
    @mcp.tool()
    async def get_products_association(association_id: int, user_id: Optional[str] = None) -> str:
        """Get a single product association by ID."""
        try:
            params = ProductsAssociationGetParams(association_id=association_id, user_id=user_id)
            client = get_client()
            result = await client.get_products_association(association_id=params.association_id, user_id=params.user_id)
            return json.dumps(result, indent=2)
        except Exception as e:
            return json.dumps(safe_error_response(e, "get_products_association"), indent=2)
    
    @mcp.tool()
    async def create_products_association(
        product_id: int,
        crm_deal_id: Optional[int] = None,
        crm_lead_id: Optional[int] = None,
        crm_company_id: Optional[int] = None,
        quantity: Optional[int] = None,
        price: Optional[float] = None,
        user_id: Optional[str] = None,
    ) -> str:
        """Create a new product association (link product to deal/contact/company)."""
        try:
            params = ProductsAssociationCreateParams(product_id=product_id, crm_deal_id=crm_deal_id, crm_lead_id=crm_lead_id,
                                                     crm_company_id=crm_company_id, quantity=quantity, price=price, user_id=user_id)
            assoc_data: dict[str, Any] = {"product_id": params.product_id}
            if params.crm_deal_id: assoc_data["crm_deal_id"] = params.crm_deal_id
            if params.crm_lead_id: assoc_data["crm_lead_id"] = params.crm_lead_id
            if params.crm_company_id: assoc_data["crm_company_id"] = params.crm_company_id
            if params.quantity: assoc_data["quantity"] = params.quantity
            if params.price is not None: assoc_data["price"] = params.price
            
            client = get_client()
            result = await client.create_products_association(association_data=assoc_data, user_id=params.user_id)
            return json.dumps(result, indent=2)
        except Exception as e:
            return json.dumps(safe_error_response(e, "create_products_association"), indent=2)
    
    @mcp.tool()
    async def update_products_association(
        association_id: int,
        quantity: Optional[int] = None,
        price: Optional[float] = None,
        user_id: Optional[str] = None,
    ) -> str:
        """Update an existing product association."""
        try:
            params = ProductsAssociationUpdateParams(association_id=association_id, quantity=quantity, price=price, user_id=user_id)
            assoc_data: dict[str, Any] = {}
            if params.quantity: assoc_data["quantity"] = params.quantity
            if params.price is not None: assoc_data["price"] = params.price
            
            client = get_client()
            result = await client.update_products_association(association_id=params.association_id, association_data=assoc_data, user_id=params.user_id)
            return json.dumps(result, indent=2)
        except Exception as e:
            return json.dumps(safe_error_response(e, "update_products_association"), indent=2)
    
    @mcp.tool()
    async def delete_products_association(association_id: int, user_id: Optional[str] = None) -> str:
        """Delete a product association."""
        try:
            params = ProductsAssociationGetParams(association_id=association_id, user_id=user_id)
            client = get_client()
            result = await client.delete_products_association(association_id=params.association_id, user_id=params.user_id)
            return json.dumps(result, indent=2)
        except Exception as e:
            return json.dumps(safe_error_response(e, "delete_products_association"), indent=2)
