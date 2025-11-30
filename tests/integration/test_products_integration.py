"""
Integration tests for Products APIs.
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
class TestProductIntegration:
    """Integration tests for Products APIs."""
    
    async def test_get_product_template(self, client):
        """Test getting product template (returns simple structure)."""
        if not os.getenv("QONTAK_REFRESH_TOKEN"):
            pytest.skip("QONTAK_REFRESH_TOKEN not set, skipping integration test")
        
        result = await client.get_product_template()
        assert result.get("success") is True
        assert "data" in result
        print(f"\n✅ Products template structure retrieved successfully")
    
    async def test_list_products(self, client):
        """Test listing products from real API."""
        if not os.getenv("QONTAK_REFRESH_TOKEN"):
            pytest.skip("QONTAK_REFRESH_TOKEN not set, skipping integration test")
        
        result = await client.list_products(page=1, per_page=5)
        assert result.get("success") is True
        assert "data" in result
        print(f"\n✅ Products list retrieved successfully")
    
    async def test_product_pagination(self, client):
        """Test products pagination."""
        if not os.getenv("QONTAK_REFRESH_TOKEN"):
            pytest.skip("QONTAK_REFRESH_TOKEN not set, skipping integration test")
        
        # Test different page sizes
        result = await client.list_products(page=1, per_page=10)
        assert result.get("success") is True
        print(f"\n✅ Products pagination test completed")
