"""
Fixtures for product-related tests.

Provides reusable mock data and error scenarios for product tool testing.
"""

import pytest
from typing import Dict, Any


@pytest.fixture
def mock_product_data() -> Dict[str, Any]:
    """Valid product data for testing."""
    return {
        "id": 77777,
        "name": "Premium Software License",
        "sku": "SOFT-PREM-001",
        "price": 999.99,
        "currency": "USD",
        "description": "Annual premium software license with full features",
        "category": "Software",
        "unit": "license",
        "is_active": True,
    }


@pytest.fixture
def mock_product_list_response() -> Dict[str, Any]:
    """Mock response for list_products."""
    return {
        "success": True,
        "data": {
            "data": [
                {
                    "id": 77777,
                    "name": "Premium Software License",
                    "sku": "SOFT-PREM-001",
                    "price": 999.99,
                },
                {
                    "id": 77778,
                    "name": "Basic Software License",
                    "sku": "SOFT-BASIC-001",
                    "price": 499.99,
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
def mock_product_get_response(mock_product_data) -> Dict[str, Any]:
    """Mock response for get_product."""
    return {
        "success": True,
        "data": {
            "data": mock_product_data
        }
    }


@pytest.fixture
def mock_product_create_response(mock_product_data) -> Dict[str, Any]:
    """Mock response for create_product."""
    return {
        "success": True,
        "data": {
            "data": mock_product_data
        }
    }


@pytest.fixture
def mock_product_update_response(mock_product_data) -> Dict[str, Any]:
    """Mock response for update_product."""
    updated_data = mock_product_data.copy()
    updated_data["name"] = "Updated Premium Software License"
    updated_data["price"] = 1099.99
    return {
        "success": True,
        "data": {
            "data": updated_data
        }
    }


@pytest.fixture
def mock_product_delete_response() -> Dict[str, Any]:
    """Mock response for delete_product."""
    return {
        "success": True,
        "data": {
            "message": "Product deleted successfully"
        }
    }


@pytest.fixture
def mock_product_with_zero_price() -> Dict[str, Any]:
    """Product with zero price (free product)."""
    return {
        "id": 77779,
        "name": "Free Trial License",
        "sku": "SOFT-FREE-001",
        "price": 0.00,
        "currency": "USD",
    }


@pytest.fixture
def mock_product_inactive() -> Dict[str, Any]:
    """Inactive product."""
    return {
        "id": 77780,
        "name": "Discontinued Product",
        "sku": "SOFT-DISC-001",
        "price": 299.99,
        "is_active": False,
    }
