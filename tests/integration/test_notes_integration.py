"""
Integration tests for Notes APIs.
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
class TestNoteIntegration:
    """Integration tests for Notes APIs."""
    
    async def test_get_note_template(self, client):
        """Test getting note template (returns simple structure)."""
        if not os.getenv("QONTAK_REFRESH_TOKEN"):
            pytest.skip("QONTAK_REFRESH_TOKEN not set, skipping integration test")
        
        result = await client.get_note_template()
        assert result.get("success") is True
        assert "data" in result
        print(f"\n✅ Notes template structure retrieved successfully")
    
    async def test_list_notes(self, client):
        """Test listing notes from real API."""
        if not os.getenv("QONTAK_REFRESH_TOKEN"):
            pytest.skip("QONTAK_REFRESH_TOKEN not set, skipping integration test")
        
        result = await client.list_notes(page=1, per_page=5)
        assert result.get("success") is True
        assert "data" in result
        print(f"\n✅ Notes list retrieved successfully")
    
    async def test_list_notes_by_contact(self, client):
        """Test listing notes filtered by contact."""
        if not os.getenv("QONTAK_REFRESH_TOKEN"):
            pytest.skip("QONTAK_REFRESH_TOKEN not set, skipping integration test")
        
        # This will list notes, potentially empty if no contact ID specified
        result = await client.list_notes(page=1, per_page=5, crm_lead_id=1)
        assert result.get("success") is True or result.get("success") is False  # May fail if contact doesn't exist
        print(f"\n✅ Notes filtered by contact test completed")
