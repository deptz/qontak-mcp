"""
MCP Tools for Qontak CRM Products.
"""

import json
from typing import Optional, Any, Callable
from mcp.server.fastmcp import FastMCP
from ..client import QontakClient
from ..models import ProductListParams, ProductGetParams, ProductCreateParams, ProductUpdateParams
from ..errors import safe_error_response


def register_product_tools(mcp: FastMCP, client: QontakClient) -> None:
    """Register all product-related MCP tools."""
    register_product_tools_lazy(mcp, lambda: client)


def register_product_tools_lazy(mcp: FastMCP, get_client: Callable[[], QontakClient]) -> None:
    """Register all product-related MCP tools with lazy client access."""
    
    @mcp.tool()
    async def list_products(page: int = 1, per_page: int = 25, user_id: Optional[str] = None) -> str:
        """List products with pagination."""
        try:
            params = ProductListParams(page=page, per_page=per_page, user_id=user_id)
            client = get_client()
            result = await client.list_products(page=params.page, per_page=params.per_page, user_id=params.user_id)
            return json.dumps(result, indent=2)
        except Exception as e:
            return json.dumps(safe_error_response(e, "list_products"), indent=2)
    
    @mcp.tool()
    async def get_product(product_id: int, user_id: Optional[str] = None) -> str:
        """Get a single product by ID."""
        try:
            params = ProductGetParams(product_id=product_id, user_id=user_id)
            client = get_client()
            result = await client.get_product(product_id=params.product_id, user_id=params.user_id)
            return json.dumps(result, indent=2)
        except Exception as e:
            return json.dumps(safe_error_response(e, "get_product"), indent=2)
    
    @mcp.tool()
    async def create_product(
        name: str,
        price: Optional[float] = None,
        sku: Optional[str] = None,
        description: Optional[str] = None,
        category: Optional[str] = None,
        user_id: Optional[str] = None,
    ) -> str:
        """Create a new product."""
        try:
            params = ProductCreateParams(name=name, price=price, sku=sku, description=description, category=category, user_id=user_id)
            product_data: dict[str, Any] = {"name": params.name}
            if params.price is not None: product_data["price"] = params.price
            if params.sku: product_data["sku"] = params.sku
            if params.description: product_data["description"] = params.description
            if params.category: product_data["category"] = params.category
            
            client = get_client()
            result = await client.create_product(product_data=product_data, user_id=params.user_id)
            return json.dumps(result, indent=2)
        except Exception as e:
            return json.dumps(safe_error_response(e, "create_product"), indent=2)
    
    @mcp.tool()
    async def update_product(
        product_id: int,
        name: Optional[str] = None,
        price: Optional[float] = None,
        sku: Optional[str] = None,
        description: Optional[str] = None,
        category: Optional[str] = None,
        user_id: Optional[str] = None,
    ) -> str:
        """Update an existing product."""
        try:
            params = ProductUpdateParams(product_id=product_id, name=name, price=price, sku=sku, description=description, category=category, user_id=user_id)
            product_data: dict[str, Any] = {}
            if params.name: product_data["name"] = params.name
            if params.price is not None: product_data["price"] = params.price
            if params.sku: product_data["sku"] = params.sku
            if params.description: product_data["description"] = params.description
            if params.category: product_data["category"] = params.category
            
            client = get_client()
            result = await client.update_product(product_id=params.product_id, product_data=product_data, user_id=params.user_id)
            return json.dumps(result, indent=2)
        except Exception as e:
            return json.dumps(safe_error_response(e, "update_product"), indent=2)
    
    @mcp.tool()
    async def delete_product(product_id: int, user_id: Optional[str] = None) -> str:
        """Delete a product."""
        try:
            params = ProductGetParams(product_id=product_id, user_id=user_id)
            client = get_client()
            result = await client.delete_product(product_id=params.product_id, user_id=params.user_id)
            return json.dumps(result, indent=2)
        except Exception as e:
            return json.dumps(safe_error_response(e, "delete_product"), indent=2)
