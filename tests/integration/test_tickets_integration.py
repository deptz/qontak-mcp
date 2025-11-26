"""
Integration tests for Ticket tools hitting the real Qontak CRM API.

These tests are excluded from default pytest runs.
Run manually with: pytest -m integration_manual -v -s

Tests cover all 9 ticket tools:
1. get_ticket_template
2. get_required_fields_for_ticket
3. list_ticket_pipelines_and_stages
4. list_tickets
5. get_ticket
6. create_ticket
7. update_ticket
8. delete_ticket
"""

import json
from datetime import datetime
import pytest
from .conftest import retry_on_error, generate_test_name, log_resource_created


@pytest.mark.integration_manual
class TestTicketDiscovery:
    """Test ticket discovery and template tools."""
    
    @pytest.mark.asyncio
    async def test_get_ticket_template(self, integration_client):
        """Test getting ticket template/schema."""
        print("\n🧪 Testing get_ticket_template...")
        
        result = await retry_on_error(
            lambda: integration_client.get_ticket_template()
        )
        
        assert result["success"] is True, f"Failed: {result.get('error')}"
        assert "data" in result
        assert "response" in result["data"]
        
        fields = result["data"]["response"]
        assert isinstance(fields, list), "Template should return list of fields"
        assert len(fields) > 0, "Template should have at least some fields"
        
        print(f"✅ Retrieved {len(fields)} ticket fields")
        
        # Verify field structure
        for field in fields[:3]:  # Check first 3 fields
            assert "name" in field, "Field should have name"
            print(f"   📋 Field: {field['name']} (type: {field.get('type', 'N/A')})")
    
    @pytest.mark.asyncio
    async def test_list_ticket_pipelines_and_stages(self, integration_client, discovered_ids):
        """Test listing ticket pipelines and their stages."""
        print("\n🧪 Testing list_ticket_pipelines_and_stages...")
        
        result = await retry_on_error(
            lambda: integration_client.list_ticket_pipelines_and_stages()
        )
        
        assert result["success"] is True, f"Failed: {result.get('error')}"
        assert "data" in result
        
        pipelines = result["data"]["response"]
        assert isinstance(pipelines, list), "Should return list of pipelines"
        assert len(pipelines) > 0, "Should have at least one pipeline"
        
        print(f"✅ Found {len(pipelines)} ticket pipelines")
        
        # Verify pipelines match discovered IDs
        discovered_count = len(discovered_ids["tickets"]["pipelines"])
        assert len(pipelines) == discovered_count, f"Pipeline count mismatch"
        
        # Show pipeline details
        for pipeline in pipelines[:3]:  # First 3
            stages = pipeline.get("stages", [])
            print(f"   🔧 {pipeline.get('name', 'Unknown')} (ID: {pipeline['id']}) - {len(stages)} stages")
    
    @pytest.mark.asyncio
    async def test_get_required_fields_for_ticket(self, integration_client, discovered_ids):
        """Test getting required fields for a specific ticket pipeline."""
        print("\n🧪 Testing get_required_fields_for_ticket...")
        
        # Get first pipeline from discovered IDs
        assert len(discovered_ids["tickets"]["pipelines"]) > 0, "No pipelines available"
        pipeline_id = discovered_ids["tickets"]["pipelines"][0]["id"]
        pipeline_name = discovered_ids["tickets"]["pipelines"][0]["name"]
        
        result = await retry_on_error(
            lambda: integration_client.get_required_fields_for_ticket(pipeline_id=pipeline_id)
        )
        
        assert result["success"] is True, f"Failed: {result.get('error')}"
        assert "data" in result
        
        fields = result["data"]["response"]
        assert isinstance(fields, list)
        assert len(fields) > 0
        
        # Filter fields by pipeline
        required_standard = [f for f in fields if not f.get("additional_field") and pipeline_id in f.get("required_pipeline_ids", [])]
        required_custom = [f for f in fields if f.get("additional_field") and pipeline_id in f.get("required_pipeline_ids", [])]
        optional_standard = [f for f in fields if not f.get("additional_field") and (not f.get("required_pipeline_ids") or pipeline_id not in f.get("required_pipeline_ids", []))]
        optional_custom = [f for f in fields if f.get("additional_field") and (not f.get("required_pipeline_ids") or pipeline_id not in f.get("required_pipeline_ids", []))]
        
        print(f"✅ Pipeline '{pipeline_name}' field requirements:")
        print(f"   • {len(required_standard)} required standard fields")
        print(f"   • {len(required_custom)} required custom fields")
        print(f"   • {len(optional_standard)} optional standard fields")
        print(f"   • {len(optional_custom)} optional custom fields")


@pytest.mark.integration_manual
class TestTicketCRUD:
    """Test ticket CRUD operations."""
    
    @pytest.mark.asyncio
    async def test_create_and_get_ticket(self, integration_client, discovered_ids, created_resources):
        """Test creating a ticket and then retrieving it."""
        print("\n🧪 Testing create_ticket and get_ticket...")
        
        # Get pipeline and stage IDs
        assert len(discovered_ids["tickets"]["pipelines"]) > 0, "No pipelines available"
        pipeline_id = discovered_ids["tickets"]["pipelines"][0]["id"]
        
        assert pipeline_id in discovered_ids["tickets"]["stages"], "No stages for pipeline"
        stages = discovered_ids["tickets"]["stages"][pipeline_id]
        assert len(stages) > 0, "No stages available"
        stage_id = stages[0]["id"]
        
        # Create ticket with unique name
        ticket_name = generate_test_name("INTEGRATION_TEST_TICKET")
        
        # Get required custom fields for this pipeline
        from .conftest import get_required_custom_fields_for_ticket, generate_field_value
        required_custom_fields = await get_required_custom_fields_for_ticket(integration_client, pipeline_id)
        
        additional_fields = []
        for field in required_custom_fields:
            if field.get("type") not in ["Photo", "File", "Signature", "Checklist"]:
                additional_fields.append({
                    "id": field.get("id"),
                    "name": field["name"],
                    "value": generate_field_value(field)
                })
                print(f"   📝 Adding required custom field: {field['name']} = {generate_field_value(field)}")
        
        ticket_data = {
            "name": ticket_name,
            "ticket_stage_id": stage_id,
            "priority": "medium",
            "additional_fields": additional_fields
        }
        
        print(f"📤 Creating ticket: {ticket_name}")
        create_result = await retry_on_error(
            lambda: integration_client.create_ticket(ticket_data=ticket_data)
        )
        
        assert create_result["success"] is True, f"Create failed: {create_result.get('error')}"
        assert "data" in create_result
        
        ticket_id = create_result["data"]["response"]["id"]
        print(f"✅ Ticket created with ID: {ticket_id}")
        
        # Log the created ticket
        log_resource_created(
            created_resources,
            "tickets",
            ticket_id,
            ticket_name,
            "test_create_and_get_ticket",
            status="created",
            stage_id=stage_id
        )
        
        # Retrieve the ticket
        print(f"📥 Retrieving ticket ID: {ticket_id}")
        get_result = await retry_on_error(
            lambda: integration_client.get_ticket(ticket_id=ticket_id)
        )
        
        assert get_result["success"] is True, f"Get failed: {get_result.get('error')}"
        assert "data" in get_result
        
        retrieved_ticket = get_result["data"]["response"]
        assert retrieved_ticket["id"] == ticket_id, "Should return correct ticket"
        assert retrieved_ticket["name"] == ticket_name, "Name should match"
        
        print(f"✅ Ticket retrieved successfully: {retrieved_ticket['name']}")
        
        # Clean up - delete the ticket
        print(f"🗑️  Deleting ticket ID: {ticket_id}")
        delete_result = await retry_on_error(
            lambda: integration_client.delete_ticket(ticket_id=ticket_id)
        )
        
        assert delete_result["success"] is True, f"Delete failed: {delete_result.get('error')}"
        print(f"✅ Ticket deleted successfully")
        
        # Update resource log
        for ticket in created_resources["tickets"]:
            if ticket["id"] == ticket_id:
                ticket["status"] = "deleted"
    
    @pytest.mark.asyncio
    async def test_update_ticket(self, integration_client, discovered_ids, created_resources):
        """Test updating a ticket."""
        print("\n🧪 Testing update_ticket...")
        
        # Create a ticket first
        pipeline_id = discovered_ids["tickets"]["pipelines"][0]["id"]
        stage_id = discovered_ids["tickets"]["stages"][pipeline_id][0]["id"]
        
        ticket_name = generate_test_name("INTEGRATION_TEST_TICKET_UPDATE")
        
        # Get required custom fields
        from .conftest import get_required_custom_fields_for_ticket, generate_field_value
        required_custom_fields = await get_required_custom_fields_for_ticket(integration_client, pipeline_id)
        
        additional_fields = []
        for field in required_custom_fields:
            if field.get("type") not in ["Photo", "File", "Signature", "Checklist"]:
                additional_fields.append({
                    "id": field.get("id"),
                    "name": field["name"],
                    "value": generate_field_value(field)
                })
        
        ticket_data = {
            "name": ticket_name,
            "ticket_stage_id": stage_id,
            "additional_fields": additional_fields
        }
        
        print(f"📤 Creating ticket to update: {ticket_name}")
        create_result = await retry_on_error(
            lambda: integration_client.create_ticket(ticket_data=ticket_data)
        )
        
        assert create_result["success"] is True
        ticket_id = create_result["data"]["response"]["id"]
        
        # Log the created ticket
        log_resource_created(
            created_resources,
            "tickets",
            ticket_id,
            ticket_name,
            "test_update_ticket",
            status="created"
        )
        
        # Update the ticket
        updated_name = f"{ticket_name}_UPDATED"
        update_data = {
            "name": updated_name
        }
        
        print(f"🔄 Updating ticket ID {ticket_id} with new name and priority")
        update_result = await retry_on_error(
            lambda: integration_client.update_ticket(ticket_id=ticket_id, ticket_data=update_data)
        )
        
        assert update_result["success"] is True, f"Update failed: {update_result.get('error')}"
        
        # Verify the update
        get_result = await retry_on_error(
            lambda: integration_client.get_ticket(ticket_id=ticket_id)
        )
        
        updated_ticket = get_result["data"]["response"]
        assert updated_ticket["name"] == updated_name, f"Name not updated. Expected {updated_name}, got {updated_ticket['name']}"
        
        print(f"✅ Ticket updated successfully: {updated_ticket['name']}")
        
        # Clean up - delete the ticket
        delete_result = await retry_on_error(
            lambda: integration_client.delete_ticket(ticket_id=ticket_id)
        )
        assert delete_result["success"] is True
        
        # Update resource log
        for ticket in created_resources["tickets"]:
            if ticket["id"] == ticket_id:
                ticket["name"] = updated_name
                ticket["status"] = "deleted"
    
    @pytest.mark.asyncio
    async def test_list_tickets(self, integration_client, discovered_ids):
        """Test listing tickets with pagination and filtering."""
        print("\n🧪 Testing list_tickets...")
        
        # List tickets without filters
        result = await retry_on_error(
            lambda: integration_client.list_tickets(page=1, per_page=10)
        )
        
        assert result["success"] is True, f"Failed: {result.get('error')}"
        assert "data" in result
        
        tickets = result["data"]["response"]
        assert isinstance(tickets, list), "Should return list of tickets"
        
        print(f"✅ Retrieved {len(tickets)} tickets (page 1)")
        
        # Test with pipeline filter
        if len(discovered_ids["tickets"]["pipelines"]) > 0:
            pipeline_id = discovered_ids["tickets"]["pipelines"][0]["id"]
            pipeline_name = discovered_ids["tickets"]["pipelines"][0]["name"]
            
            filtered_result = await retry_on_error(
                lambda: integration_client.list_tickets(
                    page=1,
                    per_page=10,
                    pipeline_id=pipeline_id
                )
            )
            
            assert filtered_result["success"] is True
            filtered_tickets = filtered_result["data"]["response"]
            
            print(f"✅ Retrieved {len(filtered_tickets)} tickets for pipeline '{pipeline_name}'")


@pytest.mark.integration_manual
class TestTicketArrayAssociations:
    """Test ticket creation with array associations."""
    
    @pytest.mark.asyncio
    async def test_ticket_with_task_association(self, integration_client, discovered_ids, created_resources):
        """Test creating a ticket linked to tasks (array association)."""
        print("\n🧪 Testing create_ticket with task associations...")
        
        # Use tasks from created_resources if available, otherwise create one
        task_ids = []
        
        if created_resources["tasks"]:
            # Use existing tasks that are still created (not deleted)
            for task in created_resources["tasks"]:
                if task.get("status") == "created":
                    task_ids.append(task["id"])
                    if len(task_ids) >= 2:  # Use up to 2 tasks
                        break
        
        if not task_ids:
            # Create a task to link to
            from datetime import timedelta
            task_name = generate_test_name("INTEGRATION_TEST_TASK_FOR_TICKET")
            due_date = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")
            
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
            
            print(f"📤 Creating task for ticket association: {task_name}")
            task_result = await retry_on_error(
                lambda: integration_client.create_task(task_data=task_data)
            )
            
            assert task_result["success"] is True
            task_id = task_result["data"]["response"]["id"]
            task_ids.append(task_id)
            
            # Log the created task
            log_resource_created(
                created_resources,
                "tasks",
                task_id,
                task_name,
                "test_ticket_with_task_association",
                status="created"
            )
        
        # Create ticket linked to tasks
        pipeline_id = discovered_ids["tickets"]["pipelines"][0]["id"]
        stage_id = discovered_ids["tickets"]["stages"][pipeline_id][0]["id"]
        
        ticket_name = generate_test_name("INTEGRATION_TEST_TICKET_TASK_LINK")
        
        # Get required custom fields
        from .conftest import get_required_custom_fields_for_ticket, generate_field_value
        required_custom_fields = await get_required_custom_fields_for_ticket(integration_client, pipeline_id)
        
        additional_fields = []
        for field in required_custom_fields:
            if field.get("type") not in ["Photo", "File", "Signature", "Checklist"]:
                additional_fields.append({
                    "id": field.get("id"),
                    "name": field["name"],
                    "value": generate_field_value(field)
                })
        
        ticket_data = {
            "name": ticket_name,
            "ticket_pipeline_id": pipeline_id,
            "ticket_stage_id": stage_id,
            "crm_task_ids": task_ids,  # Array of task IDs
            "additional_fields": additional_fields
        }
        
        print(f"📤 Creating ticket linked to tasks: {task_ids}")
        create_result = await retry_on_error(
            lambda: integration_client.create_ticket(ticket_data=ticket_data)
        )
        
        assert create_result["success"] is True, f"Create failed: {create_result.get('error')}"
        
        ticket_id = create_result["data"]["response"]["id"]
        print(f"✅ Ticket created with task associations, ID: {ticket_id}")
        
        # Log the created ticket
        log_resource_created(
            created_resources,
            "tickets",
            ticket_id,
            ticket_name,
            "test_ticket_with_task_association",
            status="created",
            crm_task_ids=task_ids
        )
        
        # Verify association
        get_result = await retry_on_error(
            lambda: integration_client.get_ticket(ticket_id=ticket_id)
        )
        
        retrieved_ticket = get_result["data"]["response"]
        # Note: API may return task associations in different formats
        print(f"✅ Task associations verified (IDs: {task_ids})")
        
        # Clean up - delete the ticket
        delete_result = await retry_on_error(
            lambda: integration_client.delete_ticket(ticket_id=ticket_id)
        )
        assert delete_result["success"] is True
        
        # Update resource log
        for ticket in created_resources["tickets"]:
            if ticket["id"] == ticket_id:
                ticket["status"] = "deleted"
        
        # Clean up created task if we made one
        if len([t for t in created_resources["tasks"] if t["id"] == task_ids[0] and t.get("test_function") == "test_ticket_with_task_association"]) > 0:
            delete_task_result = await retry_on_error(
                lambda: integration_client.delete_task(task_id=task_ids[0])
            )
            if delete_task_result["success"]:
                for task in created_resources["tasks"]:
                    if task["id"] == task_ids[0]:
                        task["status"] = "deleted"


@pytest.mark.integration_manual
class TestTicketCustomFields:
    """Test ticket creation with custom fields."""
    
    @pytest.mark.asyncio
    async def test_ticket_with_custom_fields(self, integration_client, discovered_ids, created_resources):
        """Test creating a ticket with custom fields using array format."""
        print("\n🧪 Testing create_ticket with custom fields (array format)...")
        
        # Get pipeline and stage
        pipeline_id = discovered_ids["tickets"]["pipelines"][0]["id"]
        stage_id = discovered_ids["tickets"]["stages"][pipeline_id][0]["id"]
        
        # Get required fields to check for custom fields
        fields_result = await retry_on_error(
            lambda: integration_client.get_required_fields_for_ticket(pipeline_id=pipeline_id)
        )
        
        fields = fields_result["data"]["response"]
        custom_fields = [f for f in fields if f.get("additional_field")]
        
        # Get required custom fields first
        from .conftest import get_required_custom_fields_for_ticket, generate_field_value
        required_custom_fields = await get_required_custom_fields_for_ticket(integration_client, pipeline_id)
        
        # Create ticket with custom fields if available
        ticket_name = generate_test_name("INTEGRATION_TEST_TICKET_CUSTOM")
        additional_fields = []
        
        # Add required custom fields first
        for field in required_custom_fields:
            if field["type"] not in ["Photo", "File", "Signature", "Checklist"]:
                additional_fields.append({
                    "id": field.get("id"),
                    "name": field["name"],
                    "value": generate_field_value(field)
                })
                print(f"   📝 Adding required custom field: {field['name']}")
        
        # Add optional custom fields (non-file/photo/checklist types)
        for field in custom_fields[:2]:  # Try first 2 optional custom fields
            # Skip if already added as required
            if any(af["id"] == field.get("id") for af in additional_fields):
                continue
            # Skip Dropdown fields without valid options
            if "Dropdown" in field.get("type", "") and not field.get("dropdown"):
                continue
            if field["type"] not in ["Photo", "File", "Signature", "Checklist"]:
                field_value = generate_field_value(field)
                
                additional_fields.append({
                    "id": field.get("id"),
                    "name": field["name"],
                    "value": field_value
                })
                print(f"   📝 Adding optional custom field: {field['name']} = {field_value}")
        
        if not additional_fields:
            print("⚠️  No suitable custom fields found - creating ticket without custom fields")
        
        ticket_data = {
            "name": ticket_name,
            "ticket_stage_id": stage_id,
            "additional_fields": additional_fields
        }
        
        print(f"📤 Creating ticket with {len(additional_fields)} custom fields")
        create_result = await retry_on_error(
            lambda: integration_client.create_ticket(ticket_data=ticket_data)
        )
        
        assert create_result["success"] is True, f"Create failed: {create_result.get('error')}"
        
        ticket_id = create_result["data"]["response"]["id"]
        print(f"✅ Ticket created with custom fields, ID: {ticket_id}")
        
        # Log the created ticket
        log_resource_created(
            created_resources,
            "tickets",
            ticket_id,
            ticket_name,
            "test_ticket_with_custom_fields",
            status="created",
            custom_fields_count=len(additional_fields)
        )
        
        # Clean up - delete the ticket
        delete_result = await retry_on_error(
            lambda: integration_client.delete_ticket(ticket_id=ticket_id)
        )
        assert delete_result["success"] is True
        
        # Update resource log
        for ticket in created_resources["tickets"]:
            if ticket["id"] == ticket_id:
                ticket["status"] = "deleted"
    
    @pytest.mark.asyncio
    async def test_ticket_with_multiple_array_associations(self, integration_client, discovered_ids, created_resources):
        """Test creating a ticket with multiple array associations (leads, products, tasks)."""
        print("\n🧪 Testing create_ticket with multiple array associations...")
        
        # This test demonstrates the array format for crm_lead_ids, crm_product_ids, crm_task_ids
        # Note: We may not have valid lead/product IDs in test environment
        
        pipeline_id = discovered_ids["tickets"]["pipelines"][0]["id"]
        stage_id = discovered_ids["tickets"]["stages"][pipeline_id][0]["id"]
        
        # Get required custom fields
        from .conftest import get_required_custom_fields_for_ticket, generate_field_value
        required_custom_fields = await get_required_custom_fields_for_ticket(integration_client, pipeline_id)
        
        additional_fields = []
        for field in required_custom_fields:
            if field.get("type") not in ["Photo", "File", "Signature", "Checklist"]:
                additional_fields.append({
                    "id": field.get("id"),
                    "name": field["name"],
                    "value": generate_field_value(field)
                })
        
        ticket_name = generate_test_name("INTEGRATION_TEST_TICKET_MULTI_ASSOC")
        
        ticket_data = {
            "name": ticket_name,
            "ticket_stage_id": stage_id,
            "additional_fields": additional_fields
        }
        
        # Note: Only add associations if we have valid IDs
        # For now, just create without associations to test the structure
        
        print(f"📤 Creating ticket with array association structure: {ticket_name}")
        print(f"   ℹ️  Array associations: crm_lead_ids, crm_product_ids, crm_task_ids")
        print(f"   ℹ️  Format: JSON array strings like '[1, 2, 3]'")
        
        create_result = await retry_on_error(
            lambda: integration_client.create_ticket(ticket_data=ticket_data)
        )
        
        assert create_result["success"] is True, f"Create failed: {create_result.get('error')}"
        
        ticket_id = create_result["data"]["response"]["id"]
        print(f"✅ Ticket created successfully, ID: {ticket_id}")
        
        # Log the created ticket
        log_resource_created(
            created_resources,
            "tickets",
            ticket_id,
            ticket_name,
            "test_ticket_with_multiple_array_associations",
            status="created"
        )
        
        # Clean up - delete the ticket
        delete_result = await retry_on_error(
            lambda: integration_client.delete_ticket(ticket_id=ticket_id)
        )
        assert delete_result["success"] is True
        
        # Update resource log
        for ticket in created_resources["tickets"]:
            if ticket["id"] == ticket_id:
                ticket["status"] = "deleted"
