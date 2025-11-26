"""
Pytest configuration and fixtures for integration tests.

These fixtures provide:
- Real QontakClient with actual API authentication
- Dynamic discovery of pipeline/stage/category IDs
- Resource tracking for cleanup and logging
- Retry logic with exponential backoff
"""

import os
import json
import time
import asyncio
from datetime import datetime
from typing import Dict, Any, Optional
from uuid import uuid4

import pytest
from dotenv import load_dotenv
from qontak_mcp.client import QontakClient
from qontak_mcp.auth import QontakAuth
from qontak_mcp.stores.redis import RedisTokenStore

# Load environment variables from .env file
load_dotenv()


# =============================================================================
# Module-level variable to store created resources for session finish hook
# =============================================================================
_session_created_resources = None


# =============================================================================
# Pytest-asyncio configuration for session-scoped async fixtures
# =============================================================================
@pytest.fixture(scope="session")
def event_loop():
    """Create an event loop for the test session."""
    import asyncio
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# =============================================================================
# Session-scoped fixtures for integration tests
# =============================================================================

@pytest.fixture(scope="session")
async def integration_client(event_loop):
    """
    Create a real QontakClient for integration tests.
    
    This client uses actual authentication with the Qontak API and Redis for token caching.
    
    Required environment variables:
    - QONTAK_REFRESH_TOKEN: Your refresh token from Qontak CRM
    
    Optional environment variables (for Redis):
    - REDIS_URL: Redis connection URL (default: redis://localhost:6379/0)
    - REDIS_KEY_PREFIX: Key prefix (default: qontak:tokens:)
    
    Redis is used to cache access tokens, so they're only refreshed when expired (every 6 hours),
    not on every test run. This is much more efficient than refreshing on every request.
    
    If Redis already has cached tokens, they will be used (even if QONTAK_REFRESH_TOKEN is set).
    This prevents overwriting working cached tokens with potentially stale environment variables.
    """
    # Use Redis token store for efficient token caching
    # This will store access tokens and only refresh when they expire
    token_store = RedisTokenStore(
        redis_url=os.getenv("REDIS_URL", "redis://localhost:6379/0"),
        key_prefix=os.getenv("REDIS_KEY_PREFIX", "qontak:test:tokens:"),
        token_ttl=21600  # 6 hours (same as Qontak token expiry)
    )
    
    # Prioritize Redis cached tokens over environment variables
    from qontak_mcp.stores.base import TokenData
    
    # First, check if Redis already has tokens cached
    existing_token = token_store.get(user_id=None)
    
    if existing_token is not None:
        # Redis has cached tokens - use them (prioritize cache)
        print(f"🔑 Using cached tokens from Redis (refresh_token: ...{existing_token.refresh_token[-8:] if existing_token.refresh_token else 'None'})")
    else:
        # No cached tokens - seed from environment variable
        refresh_token = os.environ.get("QONTAK_REFRESH_TOKEN")
        
        if not refresh_token:
            pytest.skip("QONTAK_REFRESH_TOKEN not set - skipping integration tests")
        
        initial_token_data = TokenData(
            refresh_token=refresh_token,
            access_token=None,  # Will be fetched on first use
            expires_at=None  # Will be set after first refresh
        )
        token_store.save(initial_token_data, user_id=None)
        print(f"🔑 Initialized Redis with refresh token from environment")
    
    # Create client with real auth and Redis caching
    auth = QontakAuth(store=token_store)
    client = QontakClient(auth=auth)
    
    print(f"🔧 Using Redis for token caching at: {token_store._redis_url}")
    
    yield client
    
    # Cleanup: close client connections
    await client.close()


@pytest.fixture(scope="session")
async def discovered_ids(integration_client):
    """
    Discover and cache valid IDs for use in tests.
    
    This fixture runs once at session start and discovers:
    - Deal pipeline IDs and stage IDs
    - Ticket pipeline IDs and stage IDs
    - Task category IDs (if any exist)
    
    Returns a dict with the discovered IDs.
    """
    ids = {
        "deals": {"pipelines": [], "stages": {}},
        "tickets": {"pipelines": [], "stages": {}},
        "tasks": {"categories": []},
    }
    
    try:
        # Discover deal pipelines and stages
        print("\n🔍 Discovering deal pipelines and stages...")
        pipelines_result = await integration_client.list_pipelines()
        if pipelines_result.get("success") and pipelines_result.get("data", {}).get("response"):
            pipelines = pipelines_result["data"]["response"]
            for pipeline in pipelines:
                pipeline_id = pipeline["id"]
                ids["deals"]["pipelines"].append({
                    "id": pipeline_id,
                    "name": pipeline.get("name", "Unknown"),
                })
                
                # Get stages for this pipeline
                stages_result = await integration_client.list_pipeline_stages(pipeline_id=pipeline_id)
                if stages_result.get("success") and stages_result.get("data", {}).get("response"):
                    stages = stages_result["data"]["response"]
                    ids["deals"]["stages"][pipeline_id] = [
                        {"id": stage["id"], "name": stage.get("name", "Unknown")}
                        for stage in stages
                    ]
        
        print(f"✅ Found {len(ids['deals']['pipelines'])} deal pipelines")
        
        # Discover ticket pipelines and stages from ticket template
        print("🔍 Discovering ticket pipelines and stages...")
        ticket_template_result = await integration_client.get_ticket_template()
        if ticket_template_result.get("success") and ticket_template_result.get("data", {}).get("response"):
            fields = ticket_template_result["data"]["response"]
            
            # Extract pipeline info from ticket_pipeline_id field
            for field in fields:
                if field.get("name") == "ticket_pipeline_id" and "dropdown" in field:
                    for pipeline in field["dropdown"]:
                        ids["tickets"]["pipelines"].append({
                            "id": pipeline["id"],
                            "name": pipeline.get("name", "Unknown"),
                        })
                
                # Extract stage info from ticket_stage_id field
                if field.get("name") == "ticket_stage_id" and "dropdown" in field:
                    # Group stages by pipeline
                    for stage in field["dropdown"]:
                        pipeline_id = stage.get("ticket_pipeline_id")
                        if pipeline_id:
                            if pipeline_id not in ids["tickets"]["stages"]:
                                ids["tickets"]["stages"][pipeline_id] = []
                            ids["tickets"]["stages"][pipeline_id].append({
                                "id": stage["id"],
                                "name": stage.get("name", "Unknown")
                            })
        
        print(f"✅ Found {len(ids['tickets']['pipelines'])} ticket pipelines")
        
        # Discover task categories
        print("🔍 Discovering task categories...")
        categories_result = await integration_client.list_task_categories()
        if categories_result.get("success") and categories_result.get("data", {}).get("response"):
            categories = categories_result["data"]["response"]
            ids["tasks"]["categories"] = [
                {"id": cat["id"], "name": cat.get("name", "Unknown")}
                for cat in categories
            ]
        
        print(f"✅ Found {len(ids['tasks']['categories'])} task categories")
        
    except Exception as e:
        print(f"⚠️  Error discovering IDs: {e}")
        # Continue with empty IDs - tests will handle missing data
    
    return ids


@pytest.fixture(scope="session")
def created_resources():
    """
    Track all resources created during integration tests.
    
    Structure:
    {
        "deals": [{"id": 123, "name": "...", "test": "...", "timestamp": "...", "status": "created"}],
        "tasks": [{"id": 456, "name": "...", "test": "...", "timestamp": "...", "status": "deleted"}],
        "tickets": [{"id": 789, "name": "...", "test": "...", "timestamp": "...", "status": "deleted"}],
        "categories": [{"id": 10, "name": "...", "test": "...", "timestamp": "...", "status": "deleted"}],
        "workflows": [{"name": "...", "deal_id": 123, "task_id": 456, "ticket_id": 789, ...}]
    }
    """
    global _session_created_resources
    resources = {
        "deals": [],
        "tasks": [],
        "tickets": [],
        "categories": [],
        "workflows": [],
        "metadata": {
            "test_session_start": datetime.now().isoformat(),
            "test_session_end": None,
            "total_tests_run": 0,
            "total_resources_created": 0,
        }
    }
    _session_created_resources = resources
    return resources


def pytest_sessionfinish(session, exitstatus):
    """
    Hook that runs after all tests complete.
    
    Writes comprehensive resource log to integration_test_resources.json
    even if tests failed partially.
    """
    global _session_created_resources
    
    # Use the module-level variable set by the fixture
    created_resources = _session_created_resources
    
    if not created_resources:
        # Fallback if fixture wasn't used
        created_resources = {
            "metadata": {
                "note": "No integration tests were run or fixture not initialized",
                "test_session_end": datetime.now().isoformat(),
                "exit_status": exitstatus,
            }
        }
    
    # Update metadata
    if "metadata" in created_resources:
        created_resources["metadata"]["test_session_end"] = datetime.now().isoformat()
        created_resources["metadata"]["exit_status"] = exitstatus
        created_resources["metadata"]["total_resources_created"] = (
            len(created_resources.get("deals", [])) +
            len(created_resources.get("tasks", [])) +
            len(created_resources.get("tickets", [])) +
            len(created_resources.get("categories", []))
        )
        
    # Write to JSON file
    output_file = "integration_test_resources.json"
    try:
        with open(output_file, "w") as f:
            json.dump(created_resources, f, indent=2)
        print(f"\n📄 Integration test resources logged to: {output_file}")
        
        # Print summary
        if "deals" in created_resources:
            deals_left = len([d for d in created_resources["deals"] if d.get("status") == "created"])
            if deals_left > 0:
                print(f"⚠️  {deals_left} deal(s) left in CRM (no delete endpoint available)")
        
        tasks_deleted = len([t for t in created_resources.get("tasks", []) if t.get("status") == "deleted"])
        tickets_deleted = len([t for t in created_resources.get("tickets", []) if t.get("status") == "deleted"])
        print(f"✅ {tasks_deleted} task(s) and {tickets_deleted} ticket(s) cleaned up")
        
    except Exception as e:
        print(f"⚠️  Failed to write resource log: {e}")


# =============================================================================
# Helper functions
# =============================================================================

async def retry_on_error(func, max_retries: int = 3, initial_delay: float = 1.0):
    """
    Retry a function with exponential backoff.
    
    Retries on:
    - 429 (rate limit)
    - 5xx (server errors)
    
    Fails fast on:
    - 401 (auth errors - configuration issue)
    - 4xx (other client errors - bad request)
    
    Args:
        func: Async function to retry
        max_retries: Maximum number of retry attempts (default: 3)
        initial_delay: Initial delay in seconds (default: 1.0)
    
    Returns:
        Result from the function
    
    Raises:
        Exception if all retries fail or on non-retryable errors
    """
    last_exception = None
    delay = initial_delay
    
    for attempt in range(max_retries + 1):
        try:
            result = await func()
            
            # Check if result indicates an error that should be retried
            if isinstance(result, dict):
                # Check for rate limit in response
                if not result.get("success"):
                    error_msg = result.get("error", "").lower()
                    
                    # Fail fast on auth errors
                    if "401" in error_msg or "unauthorized" in error_msg or "authentication" in error_msg:
                        raise Exception(f"Authentication error (fail fast): {result.get('error')}")
                    
                    # Fail fast on other 4xx errors (except 429)
                    if "400" in error_msg or "404" in error_msg or "403" in error_msg:
                        raise Exception(f"Client error (fail fast): {result.get('error')}")
                    
                    # Retry on rate limit or server errors
                    if "429" in error_msg or "rate limit" in error_msg or "500" in error_msg or "502" in error_msg or "503" in error_msg:
                        if attempt < max_retries:
                            print(f"⏳ Retryable error (attempt {attempt + 1}/{max_retries}): {result.get('error')}")
                            await asyncio.sleep(delay)
                            delay *= 2  # Exponential backoff
                            continue
                        else:
                            raise Exception(f"Max retries exceeded: {result.get('error')}")
            
            return result
            
        except Exception as e:
            last_exception = e
            error_msg = str(e).lower()
            
            # Fail fast on auth errors
            if "401" in error_msg or "unauthorized" in error_msg or "authentication" in error_msg:
                raise
            
            # Retry on rate limit or server errors
            if ("429" in error_msg or "rate limit" in error_msg or 
                "500" in error_msg or "502" in error_msg or "503" in error_msg or
                "timeout" in error_msg or "connection" in error_msg):
                if attempt < max_retries:
                    print(f"⏳ Retrying after error (attempt {attempt + 1}/{max_retries}): {e}")
                    await asyncio.sleep(delay)
                    delay *= 2  # Exponential backoff
                    continue
            
            # Fail fast on other errors
            raise
    
    # If we get here, all retries failed
    if last_exception:
        raise last_exception


def generate_test_name(prefix: str = "INTEGRATION_TEST") -> str:
    """
    Generate a unique test resource name.
    
    Format: {prefix}_{timestamp}_{uuid}
    Example: INTEGRATION_TEST_20251126_143022_a3b4c5d6
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    unique_id = uuid4().hex[:8]
    return f"{prefix}_{timestamp}_{unique_id}"


def log_resource_created(
    created_resources: Dict[str, Any],
    resource_type: str,
    resource_id: int,
    resource_name: str,
    test_function: str,
    status: str = "created",
    **extra_fields
):
    """
    Log a created resource with full details.
    
    Args:
        created_resources: The created_resources fixture dict
        resource_type: Type of resource ("deals", "tasks", "tickets", "categories")
        resource_id: The resource ID
        resource_name: The resource name
        test_function: Name of the test function that created it
        status: Status of the resource ("created", "deleted", "error")
        **extra_fields: Additional fields to log
    """
    if resource_type not in created_resources:
        created_resources[resource_type] = []
    
    resource_entry = {
        "id": resource_id,
        "name": resource_name,
        "test_function": test_function,
        "timestamp": datetime.now().isoformat(),
        "status": status,
        **extra_fields
    }
    
    created_resources[resource_type].append(resource_entry)
    print(f"📝 Logged {resource_type[:-1]}: {resource_name} (ID: {resource_id}) - {status}")


def log_workflow(
    created_resources: Dict[str, Any],
    workflow_name: str,
    test_function: str,
    **workflow_data
):
    """
    Log a complete workflow with relationships.
    
    Args:
        created_resources: The created_resources fixture dict
        workflow_name: Name of the workflow
        test_function: Name of the test function
        **workflow_data: Workflow data (deal_id, task_id, ticket_id, etc.)
    """
    workflow_entry = {
        "name": workflow_name,
        "test_function": test_function,
        "timestamp": datetime.now().isoformat(),
        **workflow_data
    }
    
    created_resources["workflows"].append(workflow_entry)
    print(f"📝 Logged workflow: {workflow_name}")


async def get_required_custom_fields_for_ticket(client, pipeline_id: int) -> list:
    """
    Get required custom fields for a ticket pipeline.
    
    Returns list of field definitions that are required custom fields.
    """
    template_result = await client.get_ticket_template()
    if not template_result.get("success"):
        return []
    
    fields = template_result["data"]["response"]
    required_fields = []
    
    for field in fields:
        if field.get("additional_field") and pipeline_id in field.get("required_pipeline_ids", []):
            required_fields.append(field)
    
    return required_fields


def generate_field_value(field: dict) -> str:
    """Generate a suitable test value for a field based on its type."""
    field_type = field.get("type", "")
    
    if field_type == "Number":
        return "100"
    elif field_type == "Date":
        return "2025-12-31"
    elif "Dropdown" in field_type and field.get("dropdown"):
        # Use first dropdown option if available (handles "Dropdown", "Dropdown select", etc.)
        if len(field["dropdown"]) > 0:
            return str(field["dropdown"][0]["id"])
        return ""
    else:
        return "Test Value"


async def get_required_fields_for_deal(client, pipeline_id: int, stage_id: int) -> dict:
    """
    Get required standard and custom fields for a deal pipeline/stage.
    
    Returns dict with:
    - standard_fields: dict of required standard field names and values
    - custom_fields: list of required custom field definitions
    
    Note: Excludes common fields that are set by the test (name, crm_pipeline_id, crm_stage_id)
    """
    template_result = await client.get_deal_template()
    if not template_result.get("success"):
        return {"standard_fields": {}, "custom_fields": []}
    
    fields = template_result["data"]["response"]
    standard_fields = {}
    custom_fields = []
    
    # Fields that are set by the test itself - don't auto-fill these
    excluded_fields = {"name", "crm_pipeline_id", "crm_stage_id"}
    
    for field in fields:
        field_name = field.get("name", field.get("field_name"))
        is_custom = field.get("additional_field", False)
        
        # Skip excluded fields
        if field_name in excluded_fields:
            continue
        
        # Check if required for this pipeline/stage
        required_for_pipeline = pipeline_id in field.get("required_pipeline_ids", [])
        required_for_stage = stage_id in field.get("required_stage_ids", [])
        
        if required_for_pipeline or required_for_stage:
            if is_custom:
                custom_fields.append(field)
            else:
                # Standard field - generate value
                value = generate_field_value(field)
                standard_fields[field_name] = value
    
    return {"standard_fields": standard_fields, "custom_fields": custom_fields}


async def get_required_fields_for_task(client) -> dict:
    """
    Get required standard and custom fields for a task.
    
    Returns dict with:
    - standard_fields: dict of required standard field names and values
    - custom_fields: list of required custom field definitions
    
    Note: Tasks don't have pipeline/stage concept, so we check if any field is required
    Note: Excludes common fields that are set by the test (name, due_date)
    """
    template_result = await client.get_required_fields_for_task()
    if not template_result.get("success"):
        return {"standard_fields": {}, "custom_fields": []}
    
    fields = template_result["data"]["response"]
    standard_fields = {}
    custom_fields = []
    
    # Fields that are set by the test itself - don't auto-fill these
    excluded_fields = {"name", "due_date"}
    
    for field in fields:
        field_name = field.get("name", field.get("field_name"))
        is_custom = field.get("additional_field", False)
        
        # Skip excluded fields
        if field_name in excluded_fields:
            continue
        
        # Check if field is required
        # For tasks, use the "required" field directly (not pipeline/stage specific)
        is_required = field.get("required", False)
        
        if is_required:
            if is_custom:
                custom_fields.append(field)
            else:
                # Standard field - generate value
                value = generate_field_value(field)
                standard_fields[field_name] = value
    
    return {"standard_fields": standard_fields, "custom_fields": custom_fields}
