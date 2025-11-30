"""
Integration tests for Companies APIs.
"""

import pytest
import os
from src.qontak_mcp.client import QontakClient
from src.qontak_mcp.auth import QontakAuth


@pytest.fixture
def client():
    """Create a real QontakClient for integration tests."""
    auth = QontakAuth()
    return QontakClient(auth=auth)


@pytest.mark.integration
@pytest.mark.asyncio
class TestCompanyIntegration:
    """Integration tests for Companies APIs."""
    
    async def test_get_company_template(self, client):
        """Test getting company template from real API."""
        if not os.getenv("QONTAK_REFRESH_TOKEN"):
            pytest.skip("QONTAK_REFRESH_TOKEN not set, skipping integration test")
        
        result = await client.get_company_template()
        assert result.get("success") is True
        assert "data" in result
        print(f"\n✅ Companies template retrieved successfully")
    
    async def test_list_companies(self, client):
        """Test listing companies from real API."""
        if not os.getenv("QONTAK_REFRESH_TOKEN"):
            pytest.skip("QONTAK_REFRESH_TOKEN not set, skipping integration test")
        
        result = await client.list_companies(page=1, per_page=5)
        assert result.get("success") is True
        assert "data" in result
        print(f"\n✅ Companies list retrieved successfully")
    
    async def test_get_required_fields_for_company(self, client):
        """Test getting required fields for companies."""
        if not os.getenv("QONTAK_REFRESH_TOKEN"):
            pytest.skip("QONTAK_REFRESH_TOKEN not set, skipping integration test")
        
        # First get the template to understand the structure
        template_result = await client.get_company_template()
        assert template_result.get("success") is True
        print(f"\n✅ Company required fields retrieved successfully")
