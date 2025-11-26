"""
Integration tests for Task tools hitting the real Qontak CRM API.

These tests are excluded from default pytest runs.
Run manually with: pytest -m integration_manual -v -s

Tests cover all 9 task tools:
1. get_task_template
2. get_required_fields_for_task
3. list_task_categories
4. create_task_category
5. delete_task_category
6. list_tasks
7. get_task
8. create_task
9. update_task
10. delete_task
"""

import json
from datetime import datetime, timedelta
import pytest
from .conftest import retry_on_error, generate_test_name, log_resource_created


@pytest.mark.integration_manual
class TestTaskDiscovery:
    """Test task discovery and template tools."""
    
    @pytest.mark.asyncio
    async def test_get_task_template(self, integration_client):
        """Test getting task template/schema."""
        print("\n🧪 Testing get_task_template...")
        
        result = await retry_on_error(
            lambda: integration_client.get_task_template()
        )
        
        assert result["success"] is True, f"Failed: {result.get('error')}"
        assert "data" in result
        assert "response" in result["data"]
        
        fields = result["data"]["response"]
        assert isinstance(fields, list), "Template should return list of fields"
        assert len(fields) > 0, "Template should have at least some fields"
        
        print(f"✅ Retrieved {len(fields)} task fields")
        
        # Verify field structure
        for field in fields[:3]:  # Check first 3 fields
            assert "name" in field, "Field should have name"
            print(f"   📋 Field: {field['name']} (type: {field.get('type', 'N/A')})")
    
    @pytest.mark.asyncio
    async def test_get_required_fields_for_task(self, integration_client):
        """Test getting required fields for tasks."""
        print("\n🧪 Testing get_required_fields_for_task...")
        
        result = await retry_on_error(
            lambda: integration_client.get_required_fields_for_task()
        )
        
        assert result["success"] is True, f"Failed: {result.get('error')}"
        assert "data" in result
        assert "response" in result["data"]
        
        all_fields = result["data"]["response"]
        assert isinstance(all_fields, list), "Should return list of fields"
        assert len(all_fields) > 0, "Should have at least some fields"
        
        # Separate standard and custom fields
        standard_fields = [f for f in all_fields if not f.get("additional_field")]
        custom_fields = [f for f in all_fields if f.get("additional_field")]
        
        print(f"✅ Found {len(standard_fields)} standard fields")
        print(f"✅ Found {len(custom_fields)} custom fields")
        
        # Check for special field types
        
        gps_fields = [f for f in all_fields if f.get('type') == 'checkin']
        checklist_fields = [f for f in all_fields if f.get('type') == 'Checklist']
        
        if gps_fields:
            print(f"   📍 Found {len(gps_fields)} GPS/location fields")
        if checklist_fields:
            print(f"   ☑️  Found {len(checklist_fields)} checklist fields")
    
    @pytest.mark.asyncio
    async def test_list_task_categories(self, integration_client, discovered_ids):
        """Test listing task categories."""
        print("\n🧪 Testing list_task_categories...")
        
        result = await retry_on_error(
            lambda: integration_client.list_task_categories()
        )
        
        assert result["success"] is True, f"Failed: {result.get('error')}"
        assert "data" in result
        
        categories = result["data"]["response"]
        assert isinstance(categories, list), "Should return list of categories"
        
        print(f"✅ Found {len(categories)} task categories")
        
        # Verify categories match discovered IDs
        discovered_count = len(discovered_ids["tasks"]["categories"])
        assert len(categories) == discovered_count, f"Category count mismatch"
        
        for cat in categories[:5]:  # Show first 5
            print(f"   📁 {cat.get('name', 'Unknown')} (ID: {cat['id']})")


@pytest.mark.integration_manual
class TestTaskCategories:
    """Test task category management."""
    
    @pytest.mark.asyncio
    async def test_create_and_delete_task_category(self, integration_client, created_resources):
        """Test creating and deleting a task category."""
        print("\n🧪 Testing create_task_category and delete_task_category...")
        
        # Create category
        category_name = generate_test_name("INTEGRATION_TEST_CATEGORY")
        
        print(f"📤 Creating task category: {category_name}")
        create_result = await retry_on_error(
            lambda: integration_client.create_task_category(name=category_name)
        )
        
        assert create_result["success"] is True, f"Create failed: {create_result.get('error')}"
        assert "data" in create_result
        
        category_id = create_result["data"]["response"]["id"]
        print(f"✅ Category created with ID: {category_id}")
        
        # Log the created category
        log_resource_created(
            created_resources,
            "categories",
            category_id,
            category_name,
            "test_create_and_delete_task_category",
            status="created"
        )
        
        # Delete category
        print(f"🗑️  Deleting task category ID: {category_id}")
        delete_result = await retry_on_error(
            lambda: integration_client.delete_task_category(category_id=category_id)
        )
        
        assert delete_result["success"] is True, f"Delete failed: {delete_result.get('error')}"
        print(f"✅ Category deleted successfully")
        
        # Update resource log
        for cat in created_resources["categories"]:
            if cat["id"] == category_id:
                cat["status"] = "deleted"


@pytest.mark.integration_manual
class TestTaskCRUD:
    """Test task CRUD operations."""
    
    @pytest.mark.asyncio
    async def test_create_and_get_task(self, integration_client, discovered_ids, created_resources):
        """Test creating a task and then retrieving it."""
        print("\n🧪 Testing create_task and get_task...")
        
        # Create task with unique name
        task_name = generate_test_name("INTEGRATION_TEST_TASK")
        due_date = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")
        
        # Get required fields dynamically from template
        from .conftest import get_required_fields_for_task, generate_field_value
        required_fields = await get_required_fields_for_task(integration_client)
        
        # Build task data with required fields
        task_data = {
            "name": task_name,
            "due_date": due_date,
            **required_fields["standard_fields"],  # Spread required standard fields
            "additional_fields": []  # Array format
        }
        
        # Add required custom fields
        for field in required_fields["custom_fields"]:
            if field["type"] not in ["Photo", "File", "Signature", "Checklist"]:
                task_data["additional_fields"].append({
                    "id": field.get("id"),
                    "name": field["name"],
                    "value": generate_field_value(field)
                })
        
        # Add category if available
        if len(discovered_ids["tasks"]["categories"]) > 0:
            category_id = discovered_ids["tasks"]["categories"][0]["id"]
            task_data["category_id"] = category_id
            print(f"   📁 Using category ID: {category_id}")
        
        print(f"📤 Creating task: {task_name}")
        create_result = await retry_on_error(
            lambda: integration_client.create_task(task_data=task_data)
        )
        
        assert create_result["success"] is True, f"Create failed: {create_result.get('error')}"
        assert "data" in create_result
        
        task_id = create_result["data"]["response"]["id"]
        print(f"✅ Task created with ID: {task_id}")
        
        # Log the created task
        log_resource_created(
            created_resources,
            "tasks",
            task_id,
            task_name,
            "test_create_and_get_task",
            status="created",
            due_date=due_date
        )
        
        # Retrieve the task
        print(f"📥 Retrieving task ID: {task_id}")
        get_result = await retry_on_error(
            lambda: integration_client.get_task(task_id=task_id)
        )
        
        assert get_result["success"] is True, f"Get failed: {get_result.get('error')}"
        assert "data" in get_result
        
        retrieved_task = get_result["data"]["response"]
        assert retrieved_task["id"] == task_id, "Should return correct task"
        assert retrieved_task["name"] == task_name, "Name should match"
        
        print(f"✅ Task retrieved successfully: {retrieved_task['name']}")
        
        # Clean up - delete the task
        print(f"🗑️  Deleting task ID: {task_id}")
        delete_result = await retry_on_error(
            lambda: integration_client.delete_task(task_id=task_id)
        )
        
        assert delete_result["success"] is True, f"Delete failed: {delete_result.get('error')}"
        print(f"✅ Task deleted successfully")
        
        # Update resource log
        for task in created_resources["tasks"]:
            if task["id"] == task_id:
                task["status"] = "deleted"
    
    @pytest.mark.asyncio
    async def test_update_task(self, integration_client, created_resources):
        """Test updating a task."""
        print("\n🧪 Testing update_task...")
        
        # Create task to update
        task_name = generate_test_name("INTEGRATION_TEST_TASK_UPDATE")
        due_date = (datetime.now() + timedelta(days=5)).strftime("%Y-%m-%d")
        
        # Get required fields dynamically
        from .conftest import get_required_fields_for_task, generate_field_value
        required_fields = await get_required_fields_for_task(integration_client)
        
        task_data = {
            "name": task_name,
            "due_date": due_date,
            **required_fields["standard_fields"],
            "additional_fields": []
        }
        
        # Add required custom fields
        for field in required_fields["custom_fields"]:
            if field["type"] not in ["Photo", "File", "Signature", "Checklist"]:
                task_data["additional_fields"].append({
                    "id": field.get("id"),
                    "name": field["name"],
                    "value": generate_field_value(field)
                })
        
        print(f"📤 Creating task to update: {task_name}")
        create_result = await retry_on_error(
            lambda: integration_client.create_task(task_data=task_data)
        )
        
        assert create_result["success"] is True
        task_id = create_result["data"]["response"]["id"]
        
        # Log the created task
        log_resource_created(
            created_resources,
            "tasks",
            task_id,
            task_name,
            "test_update_task",
            status="created"
        )
        
        # Update the task
        updated_name = f"{task_name}_UPDATED"
        update_data = {
            "name": updated_name,
            "priority": "high"
        }
        
        print(f"🔄 Updating task ID {task_id} with new name and priority")
        update_result = await retry_on_error(
            lambda: integration_client.update_task(task_id=task_id, task_data=update_data)
        )
        
        assert update_result["success"] is True, f"Update failed: {update_result.get('error')}"
        
        # Verify the update
        get_result = await retry_on_error(
            lambda: integration_client.get_task(task_id=task_id)
        )
        
        updated_task = get_result["data"]["response"]
        assert updated_task["name"] == updated_name, f"Name not updated. Expected {updated_name}, got {updated_task['name']}"
        # Note: API may not return priority field directly, check if it exists
        if "priority" in updated_task:
            assert updated_task["priority"] == "high", "Priority not updated"
            print(f"✅ Task updated successfully: {updated_task['name']} (Priority: {updated_task['priority']})")
        else:
            print(f"✅ Task updated successfully: {updated_task['name']}")
        
        # Clean up - delete the task
        delete_result = await retry_on_error(
            lambda: integration_client.delete_task(task_id=task_id)
        )
        assert delete_result["success"] is True
        
        # Update resource log
        for task in created_resources["tasks"]:
            if task["id"] == task_id:
                task["name"] = updated_name
                task["status"] = "deleted"
    
    @pytest.mark.asyncio
    async def test_list_tasks(self, integration_client):
        """Test listing tasks with pagination."""
        print("\n🧪 Testing list_tasks...")
        
        # List tasks without filters
        result = await retry_on_error(
            lambda: integration_client.list_tasks(page=1, per_page=10)
        )
        
        assert result["success"] is True, f"Failed: {result.get('error')}"
        assert "data" in result
        
        tasks = result["data"]["response"]
        assert isinstance(tasks, list), "Should return list of tasks"
        
        print(f"✅ Retrieved {len(tasks)} tasks (page 1)")


@pytest.mark.integration_manual
class TestTaskAssociations:
    """Test task creation with associations."""
    
    @pytest.mark.asyncio
    async def test_task_with_deal_association(self, integration_client, created_resources):
        """Test creating a task linked to a deal."""
        print("\n🧪 Testing create_task with deal association...")
        
        # Use a deal from created_resources if available
        if not created_resources["deals"]:
            pytest.skip("No deals created yet - run deal tests first")
        
        deal_id = created_resources["deals"][0]["id"]
        deal_name = created_resources["deals"][0]["name"]
        
        # Create task linked to deal
        task_name = generate_test_name("INTEGRATION_TEST_TASK_DEAL_LINK")
        due_date = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")
        
        # Get required fields dynamically
        from .conftest import get_required_fields_for_task, generate_field_value
        required_fields = await get_required_fields_for_task(integration_client)
        
        task_data = {
            "name": task_name,
            "due_date": due_date,
            **required_fields["standard_fields"],
            "crm_deal_id": deal_id,  # Single ID association
            "additional_fields": []
        }
        
        # Add required custom fields
        for field in required_fields["custom_fields"]:
            if field["type"] not in ["Photo", "File", "Signature", "Checklist"]:
                task_data["additional_fields"].append({
                    "id": field.get("id"),
                    "name": field["name"],
                    "value": generate_field_value(field)
                })
        
        print(f"📤 Creating task linked to deal '{deal_name}' (ID: {deal_id})")
        create_result = await retry_on_error(
            lambda: integration_client.create_task(task_data=task_data)
        )
        
        assert create_result["success"] is True, f"Create failed: {create_result.get('error')}"
        
        task_id = create_result["data"]["response"]["id"]
        print(f"✅ Task created with deal association, ID: {task_id}")
        
        # Log the created task
        log_resource_created(
            created_resources,
            "tasks",
            task_id,
            task_name,
            "test_task_with_deal_association",
            status="created",
            crm_deal_id=deal_id
        )
        
        # Verify association
        get_result = await retry_on_error(
            lambda: integration_client.get_task(task_id=task_id)
        )
        
        retrieved_task = get_result["data"]["response"]
        assert retrieved_task.get("crm_deal_id") == deal_id, "Deal association not saved"
        
        print(f"✅ Deal association verified")
        
        # Clean up - delete the task
        delete_result = await retry_on_error(
            lambda: integration_client.delete_task(task_id=task_id)
        )
        assert delete_result["success"] is True
        
        # Update resource log
        for task in created_resources["tasks"]:
            if task["id"] == task_id:
                task["status"] = "deleted"


@pytest.mark.integration_manual
class TestTaskSpecialFields:
    """Test task creation with special fields."""
    
    @pytest.mark.asyncio
    async def test_task_with_gps_location(self, integration_client, created_resources):
        """Test creating a task with GPS location field."""
        print("\n🧪 Testing create_task with GPS location...")
        
        # Get required fields to check for GPS field
        fields_result = await retry_on_error(
            lambda: integration_client.get_required_fields_for_task()
        )
        
        all_fields = fields_result["data"]["response"]
        
        gps_field = next((f for f in all_fields if f.get("type") == "checkin"), None)
        
        if not gps_field:
            print("⚠️  No GPS location field found in task template - skipping")
            pytest.skip("No GPS location field available")
        
        # Create task with GPS location
        task_name = generate_test_name("INTEGRATION_TEST_TASK_GPS")
        due_date = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")
        
        # GPS location for Jakarta, Indonesia
        gps_data = {
            "latitude": -6.2088,
            "longitude": 106.8456,
            "address": "Jakarta, Indonesia"
        }
        
        # Get required fields dynamically
        from .conftest import get_required_fields_for_task, generate_field_value
        required_fields = await get_required_fields_for_task(integration_client)
        
        task_data = {
            "name": task_name,
            "due_date": due_date,
            **required_fields["standard_fields"],
            "crm_checkin_attributes": gps_data,  # GPS as top-level field
            "additional_fields": []
        }
        
        # Add required custom fields
        for field in required_fields["custom_fields"]:
            if field["type"] not in ["Photo", "File", "Signature", "Checklist"]:
                task_data["additional_fields"].append({
                    "id": field.get("id"),
                    "name": field["name"],
                    "value": generate_field_value(field)
                })
        
        print(f"📤 Creating task with GPS location: {gps_data['address']}")
        create_result = await retry_on_error(
            lambda: integration_client.create_task(task_data=task_data)
        )
        
        assert create_result["success"] is True, f"Create failed: {create_result.get('error')}"
        
        task_id = create_result["data"]["response"]["id"]
        print(f"✅ Task created with GPS location, ID: {task_id}")
        
        # Log the created task
        log_resource_created(
            created_resources,
            "tasks",
            task_id,
            task_name,
            "test_task_with_gps_location",
            status="created",
            gps_location=gps_data
        )
        
        # Clean up - delete the task
        delete_result = await retry_on_error(
            lambda: integration_client.delete_task(task_id=task_id)
        )
        assert delete_result["success"] is True
        print(f"✅ Task with GPS location deleted")
        
        # Update resource log
        for task in created_resources["tasks"]:
            if task["id"] == task_id:
                task["status"] = "deleted"
    
    @pytest.mark.asyncio
    async def test_task_with_custom_fields(self, integration_client, created_resources):
        """Test creating a task with custom fields using array format."""
        print("\n🧪 Testing create_task with custom fields (array format)...")
        
        # Get required fields to check for custom fields
        fields_result = await retry_on_error(
            lambda: integration_client.get_required_fields_for_task()
        )
        
        fields = fields_result["data"]["response"]
        custom_fields = [f for f in fields if f.get("additional_field")]
        
        # Create task with custom fields if available
        task_name = generate_test_name("INTEGRATION_TEST_TASK_CUSTOM")
        due_date = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")
        additional_fields = []
        
        # Get required fields dynamically
        from .conftest import get_required_fields_for_task, generate_field_value
        required_fields = await get_required_fields_for_task(integration_client)
        
        # Add required custom fields first
        for field in required_fields["custom_fields"]:
            if field["type"] not in ["Photo", "File", "Signature", "Checklist"]:
                additional_fields.append({
                    "id": field.get("id"),
                    "name": field["name"],
                    "value": generate_field_value(field)
                })
                print(f"   📝 Adding required custom field: {field['name']}")
        
        # Add optional custom fields (non-file/photo/checklist types)
        for field in custom_fields[:2]:  # Try first 2 custom fields
            # Skip if already added as required
            if any(af["id"] == field.get("id") for af in additional_fields):
                continue
            if field["type"] not in ["Photo", "File", "Signature", "Checklist", "checkin"]:
                field_value = generate_field_value(field)
                
                additional_fields.append({
                    "id": field.get("id"),
                    "name": field["name"],
                    "value": field_value
                })
                print(f"   📝 Adding optional custom field: {field['name']} = {field_value}")
        
        if not additional_fields:
            print("⚠️  No suitable custom fields found - creating task without custom fields")
        
        task_data = {
            "name": task_name,
            "due_date": due_date,
            **required_fields["standard_fields"],
            "additional_fields": additional_fields
        }
        
        print(f"📤 Creating task with {len(additional_fields)} custom fields")
        create_result = await retry_on_error(
            lambda: integration_client.create_task(task_data=task_data)
        )
        
        assert create_result["success"] is True, f"Create failed: {create_result.get('error')}"
        
        task_id = create_result["data"]["response"]["id"]
        print(f"✅ Task created with custom fields, ID: {task_id}")
        
        # Log the created task
        log_resource_created(
            created_resources,
            "tasks",
            task_id,
            task_name,
            "test_task_with_custom_fields",
            status="created",
            custom_fields_count=len(additional_fields)
        )
        
        # Clean up - delete the task
        delete_result = await retry_on_error(
            lambda: integration_client.delete_task(task_id=task_id)
        )
        assert delete_result["success"] is True
        
        # Update resource log
        for task in created_resources["tasks"]:
            if task["id"] == task_id:
                task["status"] = "deleted"
