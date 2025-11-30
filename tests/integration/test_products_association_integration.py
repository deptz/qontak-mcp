"""
Integration tests for Products Associations APIs.
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
class TestProductsAssociationIntegration:
    """Integration tests for Products Association APIs."""
    
    async def test_get_products_association_template(self, client):
        """Test getting products_association template (returns simple structure)."""
        if not os.getenv("QONTAK_REFRESH_TOKEN"):
            pytest.skip("QONTAK_REFRESH_TOKEN not set, skipping integration test")
        
        result = await client.get_products_association_template()
        assert result.get("success") is True
        assert "data" in result
        print(f"\n✅ Products Association template structure retrieved successfully")
    
    async def test_list_products_associations(self, client):
        """Test listing products_associations from real API."""
        if not os.getenv("QONTAK_REFRESH_TOKEN"):
            pytest.skip("QONTAK_REFRESH_TOKEN not set, skipping integration test")
        
        result = await client.list_products_associations(page=1, per_page=5)
        assert result.get("success") is True
        assert "data" in result
        print(f"\n✅ Products Associations list retrieved successfully")
    
    async def test_products_association_pagination(self, client):
        """Test products associations pagination."""
        if not os.getenv("QONTAK_REFRESH_TOKEN"):
            pytest.skip("QONTAK_REFRESH_TOKEN not set, skipping integration test")
        
        # Test different page sizes
        result = await client.list_products_associations(page=1, per_page=10)
        assert result.get("success") is True
        print(f"\n✅ Products associations pagination test completed")
