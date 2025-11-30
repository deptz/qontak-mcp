"""
Fixtures for note-related tests.

Provides reusable mock data and error scenarios for note tool testing.
"""

import pytest
from typing import Dict, Any


@pytest.fixture
def mock_note_data() -> Dict[str, Any]:
    """Valid note data for testing."""
    return {
        "id": 11111,
        "content": "Follow up with customer next week",
        "contact_id": 12345,
        "company_id": None,
        "deal_id": None,
        "created_at": "2025-01-01T10:00:00Z",
        "updated_at": "2025-01-01T10:00:00Z",
        "created_by": "user@example.com",
    }


@pytest.fixture
def mock_note_list_response() -> Dict[str, Any]:
    """Mock response for list_notes."""
    return {
        "success": True,
        "data": {
            "data": [
                {
                    "id": 11111,
                    "content": "Follow up with customer next week",
                    "contact_id": 12345,
                },
                {
                    "id": 11112,
                    "content": "Customer interested in premium plan",
                    "contact_id": 12345,
                },
            ],
            "meta": {
                "current_page": 1,
                "per_page": 25,
                "total": 2,
            }
        }
    }


@pytest.fixture
def mock_note_get_response(mock_note_data) -> Dict[str, Any]:
    """Mock response for get_note."""
    return {
        "success": True,
        "data": {
            "data": mock_note_data
        }
    }


@pytest.fixture
def mock_note_create_response(mock_note_data) -> Dict[str, Any]:
    """Mock response for create_note."""
    return {
        "success": True,
        "data": {
            "data": mock_note_data
        }
    }


@pytest.fixture
def mock_note_update_response(mock_note_data) -> Dict[str, Any]:
    """Mock response for update_note."""
    updated_data = mock_note_data.copy()
    updated_data["content"] = "Updated: Follow up with customer tomorrow"
    return {
        "success": True,
        "data": {
            "data": updated_data
        }
    }


@pytest.fixture
def mock_note_delete_response() -> Dict[str, Any]:
    """Mock response for delete_note."""
    return {
        "success": True,
        "data": {
            "message": "Note deleted successfully"
        }
    }


@pytest.fixture
def mock_note_with_company() -> Dict[str, Any]:
    """Note associated with a company."""
    return {
        "id": 11113,
        "content": "Company meeting notes",
        "contact_id": None,
        "company_id": 54321,
        "deal_id": None,
    }


@pytest.fixture
def mock_note_with_deal() -> Dict[str, Any]:
    """Note associated with a deal."""
    return {
        "id": 11114,
        "content": "Deal negotiation notes",
        "contact_id": None,
        "company_id": None,
        "deal_id": 98765,
    }


@pytest.fixture
def mock_note_with_all_associations() -> Dict[str, Any]:
    """Note associated with contact, company, and deal."""
    return {
        "id": 11115,
        "content": "Comprehensive meeting notes",
        "contact_id": 12345,
        "company_id": 54321,
        "deal_id": 98765,
    }
