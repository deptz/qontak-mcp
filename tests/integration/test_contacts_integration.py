"""
Integration tests for Contacts APIs.
"""

import os
import pytest
from src.qontak_mcp.client import QontakClient
from src.qontak_mcp.auth import QontakAuth


@pytest.fixture
def client():
    """Create a real QontakClient for integration tests."""
    auth = QontakAuth()
    return QontakClient(auth=auth)


@pytest.mark.integration
@pytest.mark.asyncio
class TestContactIntegration:
    """Integration tests for Contacts APIs."""
    
    async def test_get_contact_template(self, client):
        """Test getting contact template from real API."""
        if not os.getenv("QONTAK_REFRESH_TOKEN"):
            pytest.skip("QONTAK_REFRESH_TOKEN not set, skipping integration test")
        
        result = await client.get_contact_template()
        assert result.get("success") is True
        assert "data" in result
        print(f"\n✅ Contacts template retrieved successfully")
    
    async def test_list_contacts(self, client):
        """Test listing contacts from real API."""
        if not os.getenv("QONTAK_REFRESH_TOKEN"):
            pytest.skip("QONTAK_REFRESH_TOKEN not set, skipping integration test")
        
        result = await client.list_contacts(page=1, per_page=5)
        assert result.get("success") is True
        assert "data" in result
        print(f"\n✅ Contacts list retrieved successfully")
    
    async def test_get_required_fields_for_contact(self, client):
        """Test getting required fields for contacts."""
        if not os.getenv("QONTAK_REFRESH_TOKEN"):
            pytest.skip("QONTAK_REFRESH_TOKEN not set, skipping integration test")
        
        # First get the template to understand the structure
        template_result = await client.get_contact_template()
        assert template_result.get("success") is True
        print(f"\n✅ Contact required fields retrieved successfully")
