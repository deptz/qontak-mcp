"""
Fixtures for company-related tests.

Provides reusable mock data and error scenarios for company tool testing.
"""

import pytest
from typing import Dict, Any


@pytest.fixture
def mock_company_data() -> Dict[str, Any]:
    """Valid company data for testing."""
    return {
        "id": 54321,
        "name": "Acme Corporation",
        "industry": "Technology",
        "website": "https://acme.example.com",
        "telephone": "+6281234567890",
        "address": "456 Business Ave",
        "city": "Jakarta",
        "province": "DKI Jakarta",
        "country": "Indonesia",
        "zipcode": "12345",
        "employee_count": 100,
    }


@pytest.fixture
def mock_company_list_response() -> Dict[str, Any]:
    """Mock response for list_companies."""
    return {
        "success": True,
        "data": {
            "data": [
                {
                    "id": 54321,
                    "name": "Acme Corporation",
                    "industry": "Technology",
                },
                {
                    "id": 54322,
                    "name": "Tech Industries",
                    "industry": "Manufacturing",
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
def mock_company_get_response(mock_company_data) -> Dict[str, Any]:
    """Mock response for get_company."""
    return {
        "success": True,
        "data": {
            "data": mock_company_data
        }
    }


@pytest.fixture
def mock_company_create_response(mock_company_data) -> Dict[str, Any]:
    """Mock response for create_company."""
    return {
        "success": True,
        "data": {
            "data": mock_company_data
        }
    }


@pytest.fixture
def mock_company_update_response(mock_company_data) -> Dict[str, Any]:
    """Mock response for update_company."""
    updated_data = mock_company_data.copy()
    updated_data["name"] = "Updated Acme Corporation"
    return {
        "success": True,
        "data": {
            "data": updated_data
        }
    }


@pytest.fixture
def mock_company_delete_response() -> Dict[str, Any]:
    """Mock response for delete_company."""
    return {
        "success": True,
        "data": {
            "message": "Company deleted successfully"
        }
    }


@pytest.fixture
def mock_company_template_response() -> Dict[str, Any]:
    """Mock response for get_company_template."""
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
                        "name": "industry",
                        "type": "dropdown",
                        "required": False,
                        "options": ["Technology", "Manufacturing", "Services"],
                    },
                    {
                        "id": 3,
                        "name": "website",
                        "type": "url",
                        "required": False,
                    },
                ]
            }
        }
    }


@pytest.fixture
def mock_company_required_fields_response() -> Dict[str, Any]:
    """Mock response for get_required_fields_for_company."""
    return {
        "success": True,
        "data": {
            "required_fields": ["name"],
            "optional_fields": ["industry", "website", "telephone"],
            "all_fields": [
                {
                    "name": "name",
                    "type": "text",
                    "required": True,
                },
                {
                    "name": "industry",
                    "type": "dropdown",
                    "required": False,
                },
            ]
        }
    }


@pytest.fixture
def mock_company_timeline_response() -> Dict[str, Any]:
    """Mock response for get_company_timeline."""
    return {
        "success": True,
        "data": {
            "data": [
                {
                    "id": 1,
                    "event_type": "created",
                    "description": "Company created",
                    "created_at": "2025-01-01T10:00:00Z",
                    "user": "admin@example.com",
                },
                {
                    "id": 2,
                    "event_type": "deal_created",
                    "description": "New deal associated with company",
                    "created_at": "2025-01-05T14:20:00Z",
                    "user": "sales@example.com",
                },
            ]
        }
    }


@pytest.fixture
def mock_company_additional_fields() -> str:
    """Valid JSON string for additional_fields."""
    return '[{"id": 14840255, "name": "industry_code", "value": "TECH-001"}]'


@pytest.fixture
def invalid_company_additional_fields() -> str:
    """Invalid JSON string for additional_fields."""
    return '{invalid json structure'


@pytest.fixture
def mock_company_template_with_custom_fields() -> Dict[str, Any]:
    """Mock response for get_company_template with optional custom fields."""
    return {
        "success": True,
        "data": {
            "response": [
                {
                    "id": 1,
                    "name": "name",
                    "name_alias": "Company Name",
                    "type": "text",
                    "required": True,
                    "additional_field": False,
                },
                {
                    "id": 2,
                    "name": "industry",
                    "name_alias": "Industry",
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
def mock_company_template_with_dropdown() -> Dict[str, Any]:
    """Mock response for get_company_template with dropdown fields."""
    return {
        "success": True,
        "data": {
            "response": [
                {
                    "id": 1,
                    "name": "name",
                    "name_alias": "Company Name",
                    "type": "text",
                    "required": True,
                    "additional_field": False,
                },
                {
                    "id": 2,
                    "name": "industry",
                    "name_alias": "Industry",
                    "type": "dropdown",
                    "required": False,
                    "additional_field": False,
                    "dropdown": [
                        {"id": 1, "name": "Technology"},
                        {"id": 2, "name": "Manufacturing"},
                        {"id": 3, "name": "Services"},
                    ]
                },
            ]
        }
    }
