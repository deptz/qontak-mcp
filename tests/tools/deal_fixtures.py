"""
Fixtures for deal-related tests.

Provides reusable mock data and error scenarios for deal tool testing.
"""

import pytest
from typing import Dict, Any


@pytest.fixture
def mock_deal_data() -> Dict[str, Any]:
    """Valid deal data for testing."""
    return {
        "id": 98765,
        "name": "Enterprise Software Deal",
        "amount": 50000.00,
        "pipeline_id": 1,
        "stage_id": 2,
        "contact_id": 12345,
        "company_id": 54321,
        "expected_close_date": "2025-12-31",
        "probability": 75,
        "owner_id": 100,
    }


@pytest.fixture
def mock_deal_list_response() -> Dict[str, Any]:
    """Mock response for list_deals."""
    return {
        "success": True,
        "data": {
            "data": [
                {
                    "id": 98765,
                    "name": "Enterprise Software Deal",
                    "amount": 50000.00,
                    "pipeline_id": 1,
                    "stage_id": 2,
                },
                {
                    "id": 98766,
                    "name": "Consulting Services Deal",
                    "amount": 25000.00,
                    "pipeline_id": 1,
                    "stage_id": 3,
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
def mock_deal_get_response(mock_deal_data) -> Dict[str, Any]:
    """Mock response for get_deal."""
    return {
        "success": True,
        "data": {
            "data": mock_deal_data
        }
    }


@pytest.fixture
def mock_deal_create_response(mock_deal_data) -> Dict[str, Any]:
    """Mock response for create_deal."""
    return {
        "success": True,
        "data": {
            "data": mock_deal_data
        }
    }


@pytest.fixture
def mock_deal_update_response(mock_deal_data) -> Dict[str, Any]:
    """Mock response for update_deal."""
    updated_data = mock_deal_data.copy()
    updated_data["name"] = "Updated Enterprise Deal"
    updated_data["stage_id"] = 3
    return {
        "success": True,
        "data": {
            "data": updated_data
        }
    }


@pytest.fixture
def mock_deal_delete_response() -> Dict[str, Any]:
    """Mock response for delete_deal."""
    return {
        "success": True,
        "data": {
            "message": "Deal deleted successfully"
        }
    }


@pytest.fixture
def mock_deal_template_response() -> Dict[str, Any]:
    """Mock response for get_deal_template."""
    return {
        "success": True,
        "data": {
            "data": {
                "fields": [
                    {
                        "id": 1,
                        "name": "name",
                        "type": "text",
                        "required": True,
                    },
                    {
                        "id": 2,
                        "name": "amount",
                        "type": "number",
                        "required": True,
                    },
                    {
                        "id": 3,
                        "name": "pipeline_id",
                        "type": "dropdown",
                        "required": True,
                    },
                    {
                        "id": 4,
                        "name": "stage_id",
                        "type": "dropdown",
                        "required": True,
                    },
                ],
                "pipelines": [
                    {
                        "id": 1,
                        "name": "Sales Pipeline",
                        "stages": [
                            {"id": 1, "name": "Qualification"},
                            {"id": 2, "name": "Proposal"},
                            {"id": 3, "name": "Negotiation"},
                        ]
                    }
                ]
            }
        }
    }


@pytest.fixture
def mock_deal_required_fields_response() -> Dict[str, Any]:
    """Mock response for get_required_fields_for_deal."""
    return {
        "success": True,
        "data": {
            "required_fields": ["name", "amount", "pipeline_id", "stage_id"],
            "optional_fields": ["contact_id", "company_id", "expected_close_date"],
            "stage_specific_required": ["probability"],
            "all_fields": [
                {
                    "id": 1,
                    "name": "name",
                    "type": "text",
                    "required": True,
                },
                {
                    "id": 2,
                    "name": "amount",
                    "type": "number",
                    "required": True,
                },
            ]
        }
    }


@pytest.fixture
def mock_deal_timeline_response() -> Dict[str, Any]:
    """Mock response for get_deal_timeline."""
    return {
        "success": True,
        "data": {
            "data": [
                {
                    "id": 1,
                    "event_type": "created",
                    "description": "Deal created",
                    "created_at": "2025-01-01T10:00:00Z",
                },
                {
                    "id": 2,
                    "event_type": "stage_changed",
                    "description": "Moved to Proposal stage",
                    "created_at": "2025-01-10T15:00:00Z",
                },
            ]
        }
    }


@pytest.fixture
def mock_deal_stage_history_response() -> Dict[str, Any]:
    """Mock response for get_deal_stage_history."""
    return {
        "success": True,
        "data": {
            "data": [
                {
                    "id": 1,
                    "stage_id": 1,
                    "stage_name": "Qualification",
                    "entered_at": "2025-01-01T10:00:00Z",
                    "exited_at": "2025-01-10T15:00:00Z",
                },
                {
                    "id": 2,
                    "stage_id": 2,
                    "stage_name": "Proposal",
                    "entered_at": "2025-01-10T15:00:00Z",
                    "exited_at": None,
                },
            ]
        }
    }


@pytest.fixture
def mock_deal_chat_history_response() -> Dict[str, Any]:
    """Mock response for get_deal_chat_history."""
    return {
        "success": True,
        "data": {
            "data": [
                {
                    "id": 1,
                    "message": "Discussed pricing options",
                    "sender": "agent",
                    "timestamp": "2025-01-05T10:00:00Z",
                },
            ]
        }
    }


@pytest.fixture
def mock_deal_real_creator_response() -> Dict[str, Any]:
    """Mock response for get_deal_real_creator."""
    return {
        "success": True,
        "data": {
            "creator_id": 100,
            "creator_name": "John Doe",
            "creator_email": "john.doe@example.com",
        }
    }


@pytest.fixture
def mock_deal_full_field_response(mock_deal_data) -> Dict[str, Any]:
    """Mock response for get_deal_full_field."""
    full_data = mock_deal_data.copy()
    full_data["additional_fields"] = [
        {"id": 14840254, "name": "custom_field", "value": "custom_value"}
    ]
    return {
        "success": True,
        "data": {
            "data": full_data
        }
    }


@pytest.fixture
def mock_deal_permissions_response() -> Dict[str, Any]:
    """Mock response for get_deal_permissions."""
    return {
        "success": True,
        "data": {
            "can_view": True,
            "can_edit": True,
            "can_delete": False,
            "can_change_owner": True,
        }
    }


@pytest.fixture
def mock_deal_owner_update_response(mock_deal_data) -> Dict[str, Any]:
    """Mock response for update_deal_owner."""
    updated_data = mock_deal_data.copy()
    updated_data["owner_id"] = 999
    return {
        "success": True,
        "data": {
            "data": updated_data
        }
    }


@pytest.fixture
def mock_deal_additional_fields() -> str:
    """Valid JSON string for additional_fields."""
    return '[{"id": 14840254, "name": "custom_deal_field", "value": "deal_value"}]'


@pytest.fixture
def invalid_deal_additional_fields() -> str:
    """Invalid JSON string for additional_fields."""
    return '["incomplete": array'
