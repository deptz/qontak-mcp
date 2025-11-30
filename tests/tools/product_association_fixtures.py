"""
Fixtures for product association-related tests.

Provides reusable mock data and error scenarios for product association tool testing.
"""

import pytest
from typing import Dict, Any


@pytest.fixture
def mock_product_association_data() -> Dict[str, Any]:
    """Valid product association data for testing."""
    return {
        "id": 88888,
        "product_id": 77777,
        "entity_type": "deal",
        "entity_id": 98765,
        "quantity": 5,
        "discount": 10.0,
        "total_price": 4499.95,
        "created_at": "2025-01-01T10:00:00Z",
    }


@pytest.fixture
def mock_product_association_list_response() -> Dict[str, Any]:
    """Mock response for list_products_associations."""
    return {
        "success": True,
        "data": {
            "data": [
                {
                    "id": 88888,
                    "product_id": 77777,
                    "entity_type": "deal",
                    "entity_id": 98765,
                    "quantity": 5,
                },
                {
                    "id": 88889,
                    "product_id": 77778,
                    "entity_type": "contact",
                    "entity_id": 12345,
                    "quantity": 1,
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
def mock_product_association_get_response(mock_product_association_data) -> Dict[str, Any]:
    """Mock response for get_products_association."""
    return {
        "success": True,
        "data": {
            "data": mock_product_association_data
        }
    }


@pytest.fixture
def mock_product_association_create_response(mock_product_association_data) -> Dict[str, Any]:
    """Mock response for create_products_association."""
    return {
        "success": True,
        "data": {
            "data": mock_product_association_data
        }
    }


@pytest.fixture
def mock_product_association_update_response(mock_product_association_data) -> Dict[str, Any]:
    """Mock response for update_products_association."""
    updated_data = mock_product_association_data.copy()
    updated_data["quantity"] = 10
    updated_data["total_price"] = 8999.90
    return {
        "success": True,
        "data": {
            "data": updated_data
        }
    }


@pytest.fixture
def mock_product_association_delete_response() -> Dict[str, Any]:
    """Mock response for delete_products_association."""
    return {
        "success": True,
        "data": {
            "message": "Product association deleted successfully"
        }
    }


@pytest.fixture
def mock_product_association_with_contact() -> Dict[str, Any]:
    """Product association with a contact."""
    return {
        "id": 88890,
        "product_id": 77777,
        "entity_type": "contact",
        "entity_id": 12345,
        "quantity": 2,
    }


@pytest.fixture
def mock_product_association_with_company() -> Dict[str, Any]:
    """Product association with a company."""
    return {
        "id": 88891,
        "product_id": 77778,
        "entity_type": "company",
        "entity_id": 54321,
        "quantity": 100,
    }


@pytest.fixture
def mock_product_association_with_discount() -> Dict[str, Any]:
    """Product association with discount."""
    return {
        "id": 88892,
        "product_id": 77777,
        "entity_type": "deal",
        "entity_id": 98765,
        "quantity": 10,
        "discount": 25.0,
        "total_price": 7499.93,
    }


@pytest.fixture
def mock_product_association_zero_discount() -> Dict[str, Any]:
    """Product association with zero discount."""
    return {
        "id": 88893,
        "product_id": 77777,
        "entity_type": "deal",
        "entity_id": 98766,
        "quantity": 1,
        "discount": 0.0,
        "total_price": 999.99,
    }
