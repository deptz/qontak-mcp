"""
Fixtures for contact-related tests.

Provides reusable mock data and error scenarios for contact tool testing.
"""

import pytest
from typing import Dict, Any


@pytest.fixture
def mock_contact_data() -> Dict[str, Any]:
    """Valid contact data for testing."""
    return {
        "id": 12345,
        "first_name": "John",
        "last_name": "Doe",
        "email": "john.doe@example.com",
        "telephone": "+6281234567890",
        "job_title": "Software Engineer",
        "crm_status_id": 1,
        "crm_company_id": 100,
        "address": "123 Main St",
        "city": "Jakarta",
        "province": "DKI Jakarta",
        "country": "Indonesia",
        "zipcode": "12345",
        "date_of_birth": "1990-01-15",
    }


@pytest.fixture
def mock_contact_list_response() -> Dict[str, Any]:
    """Mock response for list_contacts."""
    return {
        "success": True,
        "data": {
            "data": [
                {
                    "id": 12345,
                    "first_name": "John",
                    "last_name": "Doe",
                    "email": "john.doe@example.com",
                },
                {
                    "id": 12346,
                    "first_name": "Jane",
                    "last_name": "Smith",
                    "email": "jane.smith@example.com",
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
def mock_contact_get_response(mock_contact_data) -> Dict[str, Any]:
    """Mock response for get_contact."""
    return {
        "success": True,
        "data": {
            "data": mock_contact_data
        }
    }


@pytest.fixture
def mock_contact_create_response(mock_contact_data) -> Dict[str, Any]:
    """Mock response for create_contact."""
    return {
        "success": True,
        "data": {
            "data": mock_contact_data
        }
    }


@pytest.fixture
def mock_contact_update_response(mock_contact_data) -> Dict[str, Any]:
    """Mock response for update_contact."""
    updated_data = mock_contact_data.copy()
    updated_data["first_name"] = "Updated John"
    return {
        "success": True,
        "data": {
            "data": updated_data
        }
    }


@pytest.fixture
def mock_contact_delete_response() -> Dict[str, Any]:
    """Mock response for delete_contact."""
    return {
        "success": True,
        "data": {
            "message": "Contact deleted successfully"
        }
    }


@pytest.fixture
def mock_contact_template_response() -> Dict[str, Any]:
    """Mock response for get_contact_template."""
    return {
        "success": True,
        "data": {
            "data": {
                "fields": [
                    {
                        "id": 1,
                        "name": "first_name",
                        "type": "text",
                        "required": True,
                    },
                    {
                        "id": 2,
                        "name": "last_name",
                        "type": "text",
                        "required": False,
                    },
                    {
                        "id": 3,
                        "name": "email",
                        "type": "email",
                        "required": False,
                    },
                    {
                        "id": 4,
                        "name": "telephone",
                        "type": "phone",
                        "required": False,
                    },
                ]
            }
        }
    }


@pytest.fixture
def mock_contact_required_fields_response() -> Dict[str, Any]:
    """Mock response for get_required_fields_for_contact."""
    return {
        "success": True,
        "data": {
            "required_fields": ["first_name"],
            "optional_fields": ["last_name", "email", "telephone", "job_title"],
            "all_fields": [
                {
                    "name": "first_name",
                    "type": "text",
                    "required": True,
                },
                {
                    "name": "last_name",
                    "type": "text",
                    "required": False,
                },
            ]
        }
    }


@pytest.fixture
def mock_contact_template_with_custom_fields() -> Dict[str, Any]:
    """Mock response for get_contact_template with optional custom fields."""
    return {
        "success": True,
        "data": {
            "response": [
                {
                    "id": 1,
                    "name": "first_name",
                    "name_alias": "First Name",
                    "type": "text",
                    "required": True,
                    "additional_field": False,
                },
                {
                    "id": 2,
                    "name": "last_name",
                    "name_alias": "Last Name",
                    "type": "text",
                    "required": False,
                    "additional_field": False,
                },
                {
                    "id": 5,
                    "name": "custom_field_1",
                    "name_alias": "Custom Field 1",
                    "type": "text",
                    "required": False,
                    "additional_field": True,
                },
                {
                    "id": 6,
                    "name": "custom_field_2",
                    "name_alias": "Custom Field 2",
                    "type": "dropdown",
                    "required": False,
                    "additional_field": True,
                    "dropdown": [
                        {"id": 1, "name": "Option 1"},
                        {"id": 2, "name": "Option 2"},
                    ]
                },
            ]
        }
    }


@pytest.fixture
def mock_contact_timeline_response() -> Dict[str, Any]:
    """Mock response for get_contact_timeline."""
    return {
        "success": True,
        "data": {
            "data": [
                {
                    "id": 1,
                    "event_type": "created",
                    "description": "Contact created",
                    "created_at": "2025-01-01T10:00:00Z",
                    "user": "admin@example.com",
                },
                {
                    "id": 2,
                    "event_type": "updated",
                    "description": "Contact updated",
                    "created_at": "2025-01-02T15:30:00Z",
                    "user": "user@example.com",
                },
            ]
        }
    }


@pytest.fixture
def mock_contact_chat_history_response() -> Dict[str, Any]:
    """Mock response for get_contact_chat_history."""
    return {
        "success": True,
        "data": {
            "data": [
                {
                    "id": 1,
                    "message": "Hello, how can I help you?",
                    "sender": "agent",
                    "timestamp": "2025-01-01T10:00:00Z",
                },
                {
                    "id": 2,
                    "message": "I need information about your product",
                    "sender": "contact",
                    "timestamp": "2025-01-01T10:01:00Z",
                },
            ]
        }
    }


@pytest.fixture
def mock_contact_owner_update_response(mock_contact_data) -> Dict[str, Any]:
    """Mock response for update_contact_owner."""
    updated_data = mock_contact_data.copy()
    updated_data["owner_id"] = 999
    return {
        "success": True,
        "data": {
            "data": updated_data
        }
    }


@pytest.fixture
def mock_contact_additional_fields() -> str:
    """Valid JSON string for additional_fields."""
    return '[{"id": 14840254, "name": "custom_field", "value": "custom_value"}]'


@pytest.fixture
def invalid_contact_additional_fields() -> str:
    """Invalid JSON string for additional_fields."""
    return '{"invalid": json}'


# Error scenario fixtures
@pytest.fixture
def mock_api_error_401() -> Dict[str, Any]:
    """Mock 401 Unauthorized error response."""
    return {
        "success": False,
        "error": "Unauthorized: Invalid authentication credentials"
    }


@pytest.fixture
def mock_api_error_403() -> Dict[str, Any]:
    """Mock 403 Forbidden error response."""
    return {
        "success": False,
        "error": "Forbidden: You don't have permission to access this resource"
    }


@pytest.fixture
def mock_api_error_404() -> Dict[str, Any]:
    """Mock 404 Not Found error response."""
    return {
        "success": False,
        "error": "Not Found: Contact not found"
    }


@pytest.fixture
def mock_api_error_422() -> Dict[str, Any]:
    """Mock 422 Validation Error response."""
    return {
        "success": False,
        "error": "Validation Error: Invalid field format"
    }


@pytest.fixture
def mock_api_error_429() -> Dict[str, Any]:
    """Mock 429 Rate Limit error response."""
    return {
        "success": False,
        "error": "Rate Limit Exceeded: Too many requests"
    }


@pytest.fixture
def mock_api_error_500() -> Dict[str, Any]:
    """Mock 500 Internal Server Error response."""
    return {
        "success": False,
        "error": "Internal Server Error: Something went wrong"
    }
