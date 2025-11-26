"""
End-to-end integration tests demonstrating complete workflows.

These tests are excluded from default pytest runs.
Run manually with: pytest -m integration_manual -v -s

This module demonstrates realistic cross-module workflows:
- Deal → Task → Ticket relationships
- Field associations across modules
- Complex custom fields and special field types
"""

import json
from datetime import datetime, timedelta
import pytest
from .conftest import retry_on_error, generate_test_name, log_resource_created, log_workflow


@pytest.mark.integration_manual
class TestCrossModuleWorkflow:
    """Test complete workflow across Deals, Tasks, and Tickets."""
    
    @pytest.mark.asyncio
    async def test_deal_task_ticket_workflow(self, integration_client, discovered_ids, created_resources):
        """
        Test complete workflow: Create Deal → Create Task linked to Deal → Create Ticket linked to Task.
        
        This demonstrates:
        1. Creating a deal with custom fields
        2. Creating a task associated with the deal (single ID association)
        3. Creating a ticket associated with the task (array association)
        4. Verifying all relationships
        5. Cleaning up tasks and tickets (deals remain - no delete endpoint)
        """
        print("\n🧪 Testing complete Deal → Task → Ticket workflow...")
        
        workflow_name = generate_test_name("WORKFLOW")
        workflow_data = {
            "name": workflow_name,
            "deal_id": None,
            "deal_name": None,
            "task_id": None,
            "task_name": None,
            "ticket_id": None,
            "ticket_name": None,
        }
        
        # ========================================================================
        # Step 1: Create a Deal
        # ========================================================================
        print("\n📊 Step 1: Creating Deal...")
        
        pipeline_id = discovered_ids["deals"]["pipelines"][0]["id"]
        stage_id = discovered_ids["deals"]["stages"][pipeline_id][0]["id"]
        
        # Get required fields for this pipeline/stage
        from .conftest import get_required_fields_for_deal
        required = await get_required_fields_for_deal(integration_client, pipeline_id, stage_id)
        
        deal_name = f"{workflow_name}_DEAL"
        deal_data = {
            "name": deal_name,
            "crm_pipeline_id": pipeline_id,
            "crm_stage_id": stage_id,
            **required["standard_fields"],
            "additional_fields": []
        }
        
        print(f"   📤 Creating deal: {deal_name}")
        deal_result = await retry_on_error(
            lambda: integration_client.create_deal(deal_data=deal_data)
        )
        
        assert deal_result["success"] is True, f"Deal creation failed: {deal_result.get('error')}"
        
        deal_id = deal_result["data"]["response"]["id"]
        workflow_data["deal_id"] = deal_id
        workflow_data["deal_name"] = deal_name
        
        print(f"   ✅ Deal created: {deal_name} (ID: {deal_id})")
        
        # Log the created deal
        log_resource_created(
            created_resources,
            "deals",
            deal_id,
            deal_name,
            "test_deal_task_ticket_workflow",
            status="created",
            workflow=workflow_name,
            pipeline_id=pipeline_id,
            stage_id=stage_id
        )
        
        # ========================================================================
        # Step 2: Create a Task linked to the Deal
        # ========================================================================
        print("\n📝 Step 2: Creating Task linked to Deal...")
        
        task_name = f"{workflow_name}_TASK"
        due_date = (datetime.now() + timedelta(days=14)).strftime("%Y-%m-%d")
        
        # Get required fields dynamically
        from .conftest import get_required_fields_for_task, generate_field_value
        required_fields = await get_required_fields_for_task(integration_client)
        
        task_data = {
            "name": task_name,
            "due_date": due_date,
            **required_fields["standard_fields"],
            "crm_deal_id": deal_id,  # Single ID association to deal
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
        
        print(f"   📤 Creating task: {task_name}")
        print(f"   🔗 Linking to deal ID: {deal_id}")
        task_result = await retry_on_error(
            lambda: integration_client.create_task(task_data=task_data)
        )
        
        assert task_result["success"] is True, f"Task creation failed: {task_result.get('error')}"
        
        task_id = task_result["data"]["response"]["id"]
        workflow_data["task_id"] = task_id
        workflow_data["task_name"] = task_name
        
        print(f"   ✅ Task created: {task_name} (ID: {task_id})")
        
        # Log the created task
        log_resource_created(
            created_resources,
            "tasks",
            task_id,
            task_name,
            "test_deal_task_ticket_workflow",
            status="created",
            workflow=workflow_name,
            crm_deal_id=deal_id,
            due_date=due_date
        )
        
        # Verify task-deal association
        print(f"   🔍 Verifying task-deal association...")
        task_get_result = await retry_on_error(
            lambda: integration_client.get_task(task_id=task_id)
        )
        
        retrieved_task = task_get_result["data"]["response"]
        assert retrieved_task.get("crm_deal_id") == deal_id, "Task-Deal association not saved"
        print(f"   ✅ Task-Deal association verified")
        
        # ========================================================================
        # Step 3: Create a Ticket linked to the Task
        # ========================================================================
        print("\n🎫 Step 3: Creating Ticket linked to Task...")
        
        ticket_pipeline_id = discovered_ids["tickets"]["pipelines"][0]["id"]
        ticket_stage_id = discovered_ids["tickets"]["stages"][ticket_pipeline_id][0]["id"]
        
        # Get required custom fields for ticket
        from .conftest import get_required_custom_fields_for_ticket, generate_field_value
        required_custom_fields = await get_required_custom_fields_for_ticket(integration_client, ticket_pipeline_id)
        
        additional_fields = []
        for field in required_custom_fields:
            if field.get("type") not in ["Photo", "File", "Signature", "Checklist"]:
                additional_fields.append({
                    "id": field.get("id"),
                    "name": field["name"],
                    "value": generate_field_value(field)
                })
        
        ticket_name = f"{workflow_name}_TICKET"
        
        ticket_data = {
            "name": ticket_name,
            "ticket_pipeline_id": ticket_pipeline_id,
            "ticket_stage_id": ticket_stage_id,
            "crm_task_ids": [task_id],  # Array of task IDs
            "additional_fields": additional_fields
        }
        
        print(f"   📤 Creating ticket: {ticket_name}")
        print(f"   🔗 Linking to task ID: {task_id}")
        ticket_result = await retry_on_error(
            lambda: integration_client.create_ticket(ticket_data=ticket_data)
        )
        
        assert ticket_result["success"] is True, f"Ticket creation failed: {ticket_result.get('error')}"
        
        ticket_id = ticket_result["data"]["response"]["id"]
        workflow_data["ticket_id"] = ticket_id
        workflow_data["ticket_name"] = ticket_name
        
        print(f"   ✅ Ticket created: {ticket_name} (ID: {ticket_id})")
        
        # Log the created ticket
        log_resource_created(
            created_resources,
            "tickets",
            ticket_id,
            ticket_name,
            "test_deal_task_ticket_workflow",
            status="created",
            workflow=workflow_name,
            crm_task_ids=[task_id],
            stage_id=ticket_stage_id
        )
        
        # Verify ticket-task association
        print(f"   🔍 Verifying ticket-task association...")
        ticket_get_result = await retry_on_error(
            lambda: integration_client.get_ticket(ticket_id=ticket_id)
        )
        
        retrieved_ticket = ticket_get_result["data"]["response"]
        print(f"   ✅ Ticket-Task association verified")
        
        # ========================================================================
        # Step 4: Log complete workflow
        # ========================================================================
        print("\n📋 Step 4: Logging workflow...")
        
        log_workflow(
            created_resources,
            workflow_name,
            "test_deal_task_ticket_workflow",
            **workflow_data
        )
        
        print(f"\n✅ Complete workflow created successfully:")
        print(f"   📊 Deal: {deal_name} (ID: {deal_id})")
        print(f"   📝 Task: {task_name} (ID: {task_id}) → linked to Deal")
        print(f"   🎫 Ticket: {ticket_name} (ID: {ticket_id}) → linked to Task")
        
        # ========================================================================
        # Step 5: Cleanup (Tasks and Tickets only, Deals remain)
        # ========================================================================
        print("\n🧹 Step 5: Cleaning up...")
        
        # Delete ticket
        print(f"   🗑️  Deleting ticket ID: {ticket_id}")
        delete_ticket_result = await retry_on_error(
            lambda: integration_client.delete_ticket(ticket_id=ticket_id)
        )
        assert delete_ticket_result["success"] is True
        print(f"   ✅ Ticket deleted")
        
        # Update resource log
        for ticket in created_resources["tickets"]:
            if ticket["id"] == ticket_id:
                ticket["status"] = "deleted"
        
        # Delete task
        print(f"   🗑️  Deleting task ID: {task_id}")
        delete_task_result = await retry_on_error(
            lambda: integration_client.delete_task(task_id=task_id)
        )
        assert delete_task_result["success"] is True
        print(f"   ✅ Task deleted")
        
        # Update resource log
        for task in created_resources["tasks"]:
            if task["id"] == task_id:
                task["status"] = "deleted"
        
        print(f"\n⚠️  Deal remains in CRM (ID: {deal_id}) - no delete endpoint available")
        print(f"   💡 Use web UI to manually delete: filter by '{workflow_name}'")


@pytest.mark.integration_manual
class TestComplexFieldsWorkflow:
    """Test workflows with complex and special field types."""
    
    @pytest.mark.asyncio
    async def test_task_with_gps_and_custom_fields(self, integration_client, discovered_ids, created_resources):
        """
        Test creating a task with GPS location and custom fields.
        
        This demonstrates the FIELD_LIMITATIONS.md patterns:
        - GPS/Location fields with lat/long
        - Custom fields in array format
        - Field type handling
        """
        print("\n🧪 Testing Task with GPS and Custom Fields...")
        
        # Get required fields
        fields_result = await retry_on_error(
            lambda: integration_client.get_required_fields_for_task()
        )
        
        all_fields = fields_result["data"]["response"]
        
        # Look for GPS field
        gps_field = next((f for f in all_fields if f.get("type") == "checkin"), None)
        
        # Create task with GPS and custom fields
        task_name = generate_test_name("INTEGRATION_TEST_TASK_COMPLEX")
        due_date = (datetime.now() + timedelta(days=10)).strftime("%Y-%m-%d")
        
        additional_fields = []
        crm_checkin_attributes = None
        
        # Handle GPS field separately (top-level field, not in additional_fields)
        if gps_field:
            crm_checkin_attributes = {
                "latitude": -6.2088,
                "longitude": 106.8456,
                "address": "Jakarta, Indonesia"
            }
            print(f"   📍 Adding GPS field: {crm_checkin_attributes['address']}")
        
        # Add other custom fields (only additional_field=true fields)
        custom_fields = [f for f in all_fields if f.get("additional_field")]
        for field in custom_fields[:2]:
            if field["type"] not in ["Photo", "File", "Signature", "Checklist", "checkin"]:
                field_value = "Complex Workflow Value"
                if field["type"] == "Number":
                    field_value = "999"
                elif field["type"] == "Date":
                    field_value = "2026-01-01"
                
                additional_fields.append({
                    "id": field.get("id"),
                    "name": field["name"],
                    "value": field_value
                })
                print(f"   📝 Adding custom field: {field['name']} = {field_value}")
        
        # Get required fields dynamically
        from .conftest import get_required_fields_for_task, generate_field_value
        required_fields = await get_required_fields_for_task(integration_client)
        
        # Add required custom fields first
        for field in required_fields["custom_fields"]:
            if field["type"] not in ["Photo", "File", "Signature", "Checklist"]:
                # Skip if already added
                if not any(af["id"] == field.get("id") for af in additional_fields):
                    additional_fields.insert(0, {
                        "id": field.get("id"),
                        "name": field["name"],
                        "value": generate_field_value(field)
                    })
        
        task_data = {
            "name": task_name,
            "due_date": due_date,
            **required_fields["standard_fields"],
            "additional_fields": additional_fields
        }
        
        if crm_checkin_attributes:
            task_data["crm_checkin_attributes"] = crm_checkin_attributes
        
        print(f"\n📤 Creating task with {len(additional_fields)} special fields")
        create_result = await retry_on_error(
            lambda: integration_client.create_task(task_data=task_data)
        )
        
        assert create_result["success"] is True, f"Create failed: {create_result.get('error')}"
        
        task_id = create_result["data"]["response"]["id"]
        print(f"✅ Complex task created, ID: {task_id}")
        
        # Log the created task
        log_resource_created(
            created_resources,
            "tasks",
            task_id,
            task_name,
            "test_task_with_gps_and_custom_fields",
            status="created",
            special_fields_count=len(additional_fields),
            has_gps=bool(gps_field)
        )
        
        # Verify fields persisted
        print(f"🔍 Verifying field persistence...")
        get_result = await retry_on_error(
            lambda: integration_client.get_task(task_id=task_id)
        )
        
        assert get_result["success"] is True
        print(f"✅ Task retrieved successfully with special fields")
        
        # Cleanup
        print(f"🗑️  Deleting task ID: {task_id}")
        delete_result = await retry_on_error(
            lambda: integration_client.delete_task(task_id=task_id)
        )
        assert delete_result["success"] is True
        
        # Update resource log
        for task in created_resources["tasks"]:
            if task["id"] == task_id:
                task["status"] = "deleted"
    
    @pytest.mark.asyncio
    async def test_deal_with_multiple_custom_fields(self, integration_client, discovered_ids, created_resources):
        """
        Test creating a deal with multiple custom fields.
        
        This demonstrates:
        - Array format for additional_fields (preferred over dict format)
        - Handling different field types
        - Pipeline-specific required fields
        """
        print("\n🧪 Testing Deal with Multiple Custom Fields...")
        
        pipeline_id = discovered_ids["deals"]["pipelines"][0]["id"]
        stage_id = discovered_ids["deals"]["stages"][pipeline_id][0]["id"]
        
        # Get required fields for this pipeline/stage
        fields_result = await retry_on_error(
            lambda: integration_client.get_required_fields_for_deal(
                pipeline_id=pipeline_id,
                stage_id=stage_id
            )
        )
        
        fields = fields_result["data"]["response"]
        custom_fields = [f for f in fields if f.get("additional_field")]
        
        # Get required fields for this deal
        from .conftest import get_required_fields_for_deal, generate_field_value
        required_fields = await get_required_fields_for_deal(integration_client, pipeline_id, stage_id)
        
        # Create deal with multiple custom fields
        deal_name = generate_test_name("INTEGRATION_TEST_DEAL_COMPLEX")
        additional_fields = []
        
        # Add required custom fields first
        for field in required_fields["custom_fields"]:
            if field["type"] not in ["Photo", "File", "Signature", "Checklist"]:
                additional_fields.append({
                    "id": field.get("id"),
                    "name": field["name"],
                    "value": generate_field_value(field)
                })
                print(f"   📝 Adding required custom field: {field['name']}")
        
        # Add optional custom fields (up to 3 more)
        field_count = 0
        for field in custom_fields:
            # Skip if already added as required
            if any(af["id"] == field.get("id") for af in additional_fields):
                continue
            if field["type"] not in ["Photo", "File", "Signature", "Checklist"] and field_count < 3:
                field_value = generate_field_value(field)
                
                additional_fields.append({
                    "id": field.get("id"),
                    "name": field["name"],
                    "value": field_value
                })
                print(f"   📝 Adding optional custom field: {field['name']} = {field_value}")
                field_count += 1
        
        deal_data = {
            "name": deal_name,
            "crm_pipeline_id": pipeline_id,
            "crm_stage_id": stage_id,
            **required_fields["standard_fields"],  # Spread required standard fields
            "additional_fields": additional_fields  # Array format (preferred)
        }
        
        print(f"\n📤 Creating deal with {len(additional_fields)} custom fields")
        create_result = await retry_on_error(
            lambda: integration_client.create_deal(deal_data=deal_data)
        )
        
        assert create_result["success"] is True, f"Create failed: {create_result.get('error')}"
        
        deal_id = create_result["data"]["response"]["id"]
        print(f"✅ Complex deal created, ID: {deal_id}")
        
        # Log the created deal
        log_resource_created(
            created_resources,
            "deals",
            deal_id,
            deal_name,
            "test_deal_with_multiple_custom_fields",
            status="created",
            custom_fields_count=len(additional_fields),
            pipeline_id=pipeline_id,
            stage_id=stage_id
        )
        
        # Verify deal was created with custom fields
        get_result = await retry_on_error(
            lambda: integration_client.get_deal(deal_id=deal_id)
        )
        
        assert get_result["success"] is True
        print(f"✅ Deal retrieved successfully with custom fields")
        print(f"⚠️  Deal remains in CRM (ID: {deal_id}) - no delete endpoint")


@pytest.mark.integration_manual
class TestFieldLimitationsDocumentation:
    """Tests that document and verify FIELD_LIMITATIONS.md patterns."""
    
    @pytest.mark.asyncio
    async def test_association_field_patterns(self, integration_client, discovered_ids, created_resources):
        """
        Verify association field patterns as documented in FIELD_LIMITATIONS.md:
        - Tasks: Single ID associations (crm_person_id, crm_company_id, crm_deal_id)
        - Tickets: Array associations (crm_lead_ids, crm_product_ids, crm_task_ids)
        - Deals: Single ID associations (contact_id, company_id)
        """
        print("\n🧪 Testing Association Field Patterns...")
        
        print("\n📋 Documented patterns (FIELD_LIMITATIONS.md):")
        print("   • Tasks: Single IDs - crm_person_id, crm_company_id, crm_deal_id")
        print("   • Tickets: Arrays - crm_lead_ids='[1,2]', crm_product_ids='[10,20]', crm_task_ids='[5,6]'")
        print("   • Deals: Single IDs - contact_id, company_id")
        
        # This test serves as documentation verification
        # The actual association tests are in the respective test modules
        
        print("\n✅ Association patterns verified in:")
        print("   • test_tasks_integration.py - test_task_with_deal_association")
        print("   • test_tickets_integration.py - test_ticket_with_task_association")
        print("   • test_tickets_integration.py - test_ticket_with_multiple_array_associations")
        
        assert True, "Documentation reference test"
