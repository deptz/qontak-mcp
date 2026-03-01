#!/usr/bin/env python3
"""
Generate boilerplate for a new MCP tool.

Usage:
    python add_tool.py <domain> <tool_name> <client_method>

Example:
    python add_tool.py deals get_deal_tags get_deal_tags
"""

import sys
from pathlib import Path


def generate_tool_code(domain: str, tool_name: str, client_method: str) -> str:
    """Generate tool function boilerplate."""
    
    template = f'''@mcp.tool()
async def {tool_name}(
    resource_id: int,
    user_id: Optional[str] = None,
) -> str:
    """
    TODO: Add tool description.
    
    Args:
        resource_id: The resource ID
        user_id: Optional user/tenant identifier
    
    Returns:
        JSON string with result
    """
    try:
        # Validate parameters
        params = ResourceGetParams(resource_id=resource_id, user_id=user_id)
        
        client = get_client()
        result = await client.{client_method}(params.resource_id, user_id=params.user_id)
        return json.dumps(result, indent=2)
    except PydanticValidationError as e:
        return json.dumps({{
            "success": False,
            "error": "Validation error",
            "details": e.errors()
        }}, indent=2)
    except Exception as e:
        return json.dumps(safe_error_response(e, "{tool_name}"), indent=2)
'''
    return template


def generate_client_code(method_name: str, endpoint: str, http_method: str = "GET") -> str:
    """Generate client method boilerplate."""
    
    template = f'''
    async def {method_name}(
        self,
        resource_id: int,
        user_id: Optional[str] = None
    ) -> dict[str, Any]:
        """TODO: Add description."""
        # Validate resource_id
        id_result = validate_resource_id(resource_id, "resource_id")
        if not id_result.is_valid:
            return {{"success": False, "error": id_result.error}}
        
        return await self._request("{http_method}", f"{endpoint}/{{resource_id}}", user_id=user_id)
'''
    return template


def generate_test_code(domain: str, tool_name: str) -> str:
    """Generate test boilerplate."""
    
    template = f'''
class Test{tool_name.replace('_', ' ').title().replace(' ', '')}:
    @pytest.mark.asyncio
    async def test_{tool_name}_success(self, mock_get_client):
        """Test successful execution."""
        mock_response = {{"success": True, "data": {{}}}}
        get_client = mock_get_client(mock_response)
        
        # Register and call tool
        from qontak_mcp.tools.{domain} import register_{domain}_tools_lazy
        mcp = MagicMock()
        tools = {{}}
        mcp.tool = lambda: lambda f: tools.update({{f.__name__: f}})
        
        register_{domain}_tools_lazy(mcp, get_client)
        
        result = await tools["{tool_name}"](resource_id=123)
        parsed = json.loads(result)
        
        assert parsed["success"] is True
    
    @pytest.mark.asyncio
    async def test_{tool_name}_validation_error(self):
        """Test validation failure."""
        # Test with invalid resource_id
        result = await {tool_name}(resource_id=-1)
        parsed = json.loads(result)
        
        assert parsed["success"] is False
        assert "error" in parsed
'''
    return template


def main():
    if len(sys.argv) != 4:
        print("Usage: python add_tool.py <domain> <tool_name> <client_method>")
        print("\nDomains: deals, contacts, companies, tickets, tasks, notes, products, products_association")
        print("\nExample:")
        print('  python add_tool.py deals get_deal_tags get_deal_tags')
        sys.exit(1)
    
    domain = sys.argv[1]
    tool_name = sys.argv[2]
    client_method = sys.argv[3]
    
    print(f"\n{'='*60}")
    print(f"Generating code for: {tool_name}")
    print(f"Domain: {domain}")
    print(f"{'='*60}\n")
    
    # Generate code
    tool_code = generate_tool_code(domain, tool_name, client_method)
    client_code = generate_client_code(client_method, f"/{domain}")
    test_code = generate_test_code(domain, tool_name)
    
    print("1. ADD TOOL CODE to src/qontak_mcp/tools/{}.py:".format(domain))
    print("-" * 60)
    print(tool_code)
    
    print("\n2. ADD CLIENT METHOD to src/qontak_mcp/client.py:")
    print("-" * 60)
    print(client_code)
    
    print("\n3. ADD TEST to tests/tools/test_{}.py:".format(domain))
    print("-" * 60)
    print(test_code)
    
    print("\n4. UPDATE MODELS (if needed) in src/qontak_mcp/models.py")
    print("-" * 60)
    print("Add Pydantic model for parameters if needed.")
    
    print("\n" + "="*60)
    print("Remember to:")
    print("  - Fill in TODO descriptions")
    print("  - Update the endpoint path in client method")
    print("  - Add any additional parameters")
    print("  - Run tests: pytest tests/tools/test_{}.py -v".format(domain))
    print("="*60 + "\n")


if __name__ == "__main__":
    main()
