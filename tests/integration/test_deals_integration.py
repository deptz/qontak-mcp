"""
Integration tests for Deal tools hitting the real Qontak CRM API.

These tests are excluded from default pytest runs.
Run manually with: pytest -m integration_manual -v -s

Tests cover all 11 deal tools:
1. get_deal_template
2. get_required_fields_for_deal
3. list_pipelines
4. get_pipeline
5. list_pipeline_stages
6. list_deals
7. get_deal
8. create_deal
9. update_deal
10. get_deal_timeline
11. get_deal_stage_history
"""

import json
import pytest
from .conftest import retry_on_error, generate_test_name, log_resource_created


@pytest.mark.integration_manual
class TestDealDiscovery:
    """Test deal discovery and template tools."""
    
    @pytest.mark.asyncio
    async def test_get_deal_template(self, integration_client):
        """Test getting deal template/schema."""
        print("\n🧪 Testing get_deal_template...")
        
        result = await retry_on_error(
            lambda: integration_client.get_deal_template()
        )
        
        assert result["success"] is True, f"Failed: {result.get('error')}"
        assert "data" in result
        assert "response" in result["data"]
        
        fields = result["data"]["response"]
        assert isinstance(fields, list), "Template should return list of fields"
        assert len(fields) > 0, "Template should have at least some fields"
        
        print(f"✅ Retrieved {len(fields)} deal fields")
        
        # Verify field structure
        for field in fields[:3]:  # Check first 3 fields
            assert "name" in field, "Field should have name"
            assert "type" in field, "Field should have type"
            print(f"   📋 Field: {field['name']} (type: {field['type']})")
    
    @pytest.mark.asyncio
    async def test_list_pipelines(self, integration_client, discovered_ids):
        """Test listing deal pipelines."""
        print("\n🧪 Testing list_pipelines...")
        
        result = await retry_on_error(
            lambda: integration_client.list_pipelines()
        )
        
        assert result["success"] is True, f"Failed: {result.get('error')}"
        assert "data" in result
        
        pipelines = result["data"]["response"]
        assert isinstance(pipelines, list), "Should return list of pipelines"
        assert len(pipelines) > 0, "Should have at least one pipeline"
        
        print(f"✅ Found {len(pipelines)} pipelines")
        
        # Verify pipelines match discovered IDs
        discovered_count = len(discovered_ids["deals"]["pipelines"])
        assert len(pipelines) == discovered_count, f"Pipeline count mismatch"
    
    @pytest.mark.asyncio
    async def test_get_pipeline(self, integration_client, discovered_ids):
        """Test getting a specific pipeline."""
        print("\n🧪 Testing get_pipeline...")
        
        # Get first pipeline from discovered IDs
        assert len(discovered_ids["deals"]["pipelines"]) > 0, "No pipelines available"
        pipeline_id = discovered_ids["deals"]["pipelines"][0]["id"]
        
        result = await retry_on_error(
            lambda: integration_client.get_pipeline(pipeline_id=pipeline_id)
        )
        
        assert result["success"] is True, f"Failed: {result.get('error')}"
        assert "data" in result
        
        pipeline = result["data"]["response"]
        assert pipeline["id"] == pipeline_id, "Should return requested pipeline"
        assert "name" in pipeline, "Pipeline should have name"
        
        print(f"✅ Retrieved pipeline: {pipeline['name']} (ID: {pipeline_id})")
    
    @pytest.mark.asyncio
    async def test_list_pipeline_stages(self, integration_client, discovered_ids):
        """Test listing stages for a pipeline."""
        print("\n🧪 Testing list_pipeline_stages...")
        
        # Get first pipeline from discovered IDs
        assert len(discovered_ids["deals"]["pipelines"]) > 0, "No pipelines available"
        pipeline_id = discovered_ids["deals"]["pipelines"][0]["id"]
        pipeline_name = discovered_ids["deals"]["pipelines"][0]["name"]
        
        result = await retry_on_error(
            lambda: integration_client.list_pipeline_stages(pipeline_id=pipeline_id)
        )
        
        assert result["success"] is True, f"Failed: {result.get('error')}"
        assert "data" in result
        
        stages = result["data"]["response"]
        assert isinstance(stages, list), "Should return list of stages"
        assert len(stages) > 0, f"Pipeline {pipeline_name} should have at least one stage"
        
        print(f"✅ Found {len(stages)} stages for pipeline '{pipeline_name}'")
        
        # Verify stages match discovered IDs
        discovered_stages = discovered_ids["deals"]["stages"].get(pipeline_id, [])
        assert len(stages) == len(discovered_stages), "Stage count mismatch"
    
    @pytest.mark.asyncio
    async def test_get_required_fields_for_deal(self, integration_client, discovered_ids):
        """Test getting required fields for a specific pipeline and stage."""
        print("\n🧪 Testing get_required_fields_for_deal...")
        
        # Get first pipeline and stage from discovered IDs
        assert len(discovered_ids["deals"]["pipelines"]) > 0, "No pipelines available"
        pipeline_id = discovered_ids["deals"]["pipelines"][0]["id"]
        
        assert pipeline_id in discovered_ids["deals"]["stages"], "No stages for pipeline"
        stages = discovered_ids["deals"]["stages"][pipeline_id]
        assert len(stages) > 0, "No stages available"
        stage_id = stages[0]["id"]
        
        result = await retry_on_error(
            lambda: integration_client.get_required_fields_for_deal(
                pipeline_id=pipeline_id,
                stage_id=stage_id
            )
        )
        
        assert result["success"] is True, f"Failed: {result.get('error')}"
        assert "data" in result
        
        fields = result["data"]["response"]
        assert isinstance(fields, list)
        assert len(fields) > 0
        
        # Filter fields by pipeline and stage
        required_standard = [f for f in fields if not f.get("additional_field") and pipeline_id in f.get("required_pipeline_ids", []) and stage_id in f.get("required_stage_ids", [])]
        required_custom = [f for f in fields if f.get("additional_field") and pipeline_id in f.get("required_pipeline_ids", []) and stage_id in f.get("required_stage_ids", [])]
        optional_standard = [f for f in fields if not f.get("additional_field") and (not f.get("required_pipeline_ids") or pipeline_id not in f.get("required_pipeline_ids", []))]
        optional_custom = [f for f in fields if f.get("additional_field") and (not f.get("required_pipeline_ids") or pipeline_id not in f.get("required_pipeline_ids", []))]
        
        print(f"✅ Found {len(required_standard)} required standard fields")
        print(f"✅ Found {len(required_custom)} required custom fields")
        print(f"✅ Found {len(optional_standard)} optional standard fields")
        print(f"✅ Found {len(optional_custom)} optional custom fields")


@pytest.mark.integration_manual
class TestDealCRUD:
    """Test deal CRUD operations."""
    
    @pytest.mark.asyncio
    async def test_create_and_get_deal(self, integration_client, discovered_ids, created_resources):
        """Test creating a deal and then retrieving it."""
        print("\n🧪 Testing create_deal and get_deal...")
        
        # Get pipeline and stage IDs
        assert len(discovered_ids["deals"]["pipelines"]) > 0, "No pipelines available"
        pipeline_id = discovered_ids["deals"]["pipelines"][0]["id"]
        
        assert pipeline_id in discovered_ids["deals"]["stages"], "No stages for pipeline"
        stages = discovered_ids["deals"]["stages"][pipeline_id]
        assert len(stages) > 0, "No stages available"
        stage_id = stages[0]["id"]
        
        # Create deal with unique name
        deal_name = generate_test_name("INTEGRATION_TEST_DEAL")
        
        # Get required fields for this pipeline/stage
        from .conftest import get_required_fields_for_deal
        required = await get_required_fields_for_deal(integration_client, pipeline_id, stage_id)
        
        deal_data = {
            "name": deal_name,
            "crm_pipeline_id": pipeline_id,
            "crm_stage_id": stage_id,
            **required["standard_fields"],  # Add dynamically discovered required fields
            "additional_fields": []  # Use array format (preferred)
        }
        
        print(f"📤 Creating deal: {deal_name}")
        if required["standard_fields"]:
            print(f"   📝 Including required fields: {list(required['standard_fields'].keys())}")
        create_result = await retry_on_error(
            lambda: integration_client.create_deal(deal_data=deal_data)
        )
        
        assert create_result["success"] is True, f"Create failed: {create_result.get('error')}"
        assert "data" in create_result
        
        deal_id = create_result["data"]["response"]["id"]
        print(f"✅ Deal created with ID: {deal_id}")
        
        # Log the created deal
        log_resource_created(
            created_resources,
            "deals",
            deal_id,
            deal_name,
            "test_create_and_get_deal",
            status="created",
            pipeline_id=pipeline_id,
            stage_id=stage_id
        )
        
        # Retrieve the deal
        print(f"📥 Retrieving deal ID: {deal_id}")
        get_result = await retry_on_error(
            lambda: integration_client.get_deal(deal_id=deal_id)
        )
        
        assert get_result["success"] is True, f"Get failed: {get_result.get('error')}"
        assert "data" in get_result
        
        retrieved_deal = get_result["data"]["response"]
        assert retrieved_deal["id"] == deal_id, "Should return correct deal"
        assert retrieved_deal["name"] == deal_name, "Name should match"
        assert retrieved_deal["crm_pipeline_id"] == pipeline_id, "Pipeline should match"
        assert retrieved_deal["crm_stage_id"] == stage_id, "Stage should match"
        
        print(f"✅ Deal retrieved successfully: {retrieved_deal['name']}")
    
    @pytest.mark.asyncio
    async def test_update_deal(self, integration_client, discovered_ids, created_resources):
        """Test updating a deal."""
        print("\n🧪 Testing update_deal...")
        
        # Create a deal first
        pipeline_id = discovered_ids["deals"]["pipelines"][0]["id"]
        stage_id = discovered_ids["deals"]["stages"][pipeline_id][0]["id"]
        
        deal_name = generate_test_name("INTEGRATION_TEST_DEAL_UPDATE")
        
        # Get required fields for this pipeline/stage
        from .conftest import get_required_fields_for_deal
        required = await get_required_fields_for_deal(integration_client, pipeline_id, stage_id)
        
        deal_data = {
            "name": deal_name,
            "crm_pipeline_id": pipeline_id,
            "crm_stage_id": stage_id,
            **required["standard_fields"],
            "additional_fields": []
        }
        
        print(f"📤 Creating deal to update: {deal_name}")
        create_result = await retry_on_error(
            lambda: integration_client.create_deal(deal_data=deal_data)
        )
        
        assert create_result["success"] is True
        deal_id = create_result["data"]["response"]["id"]
        
        # Log the created deal
        log_resource_created(
            created_resources,
            "deals",
            deal_id,
            deal_name,
            "test_update_deal",
            status="created",
            pipeline_id=pipeline_id,
            stage_id=stage_id
        )
        
        # Update the deal
        updated_name = f"{deal_name}_UPDATED"
        update_data = {
            "name": updated_name,
        }
        
        print(f"🔄 Updating deal ID {deal_id} with new name")
        update_result = await retry_on_error(
            lambda: integration_client.update_deal(deal_id=deal_id, deal_data=update_data)
        )
        
        assert update_result["success"] is True, f"Update failed: {update_result.get('error')}"
        
        # Verify the update
        get_result = await retry_on_error(
            lambda: integration_client.get_deal(deal_id=deal_id)
        )
        
        updated_deal = get_result["data"]["response"]
        assert updated_deal["name"] == updated_name, f"Name not updated. Expected {updated_name}, got {updated_deal['name']}"
        
        print(f"✅ Deal updated successfully: {updated_deal['name']}")
        
        # Update resource log
        for deal in created_resources["deals"]:
            if deal["id"] == deal_id:
                deal["name"] = updated_name
                deal["status"] = "updated"
    
    @pytest.mark.asyncio
    async def test_list_deals(self, integration_client, discovered_ids):
        """Test listing deals with pagination."""
        print("\n🧪 Testing list_deals...")
        
        # List deals without filters
        result = await retry_on_error(
            lambda: integration_client.list_deals(page=1, per_page=10)
        )
        
        assert result["success"] is True, f"Failed: {result.get('error')}"
        assert "data" in result
        
        deals = result["data"]["response"]
        assert isinstance(deals, list), "Should return list of deals"
        
        print(f"✅ Retrieved {len(deals)} deals (page 1)")
        
        # Test with pipeline filter
        if len(discovered_ids["deals"]["pipelines"]) > 0:
            pipeline_id = discovered_ids["deals"]["pipelines"][0]["id"]
            pipeline_name = discovered_ids["deals"]["pipelines"][0]["name"]
            
            filtered_result = await retry_on_error(
                lambda: integration_client.list_deals(
                    page=1,
                    per_page=10,
                    pipeline_id=pipeline_id
                )
            )
            
            assert filtered_result["success"] is True
            filtered_deals = filtered_result["data"]["response"]
            
            print(f"✅ Retrieved {len(filtered_deals)} deals for pipeline '{pipeline_name}'")


@pytest.mark.integration_manual
class TestDealTimeline:
    """Test deal timeline and history features."""
    
    @pytest.mark.asyncio
    async def test_deal_timeline(self, integration_client, created_resources):
        """Test getting deal timeline/activity history."""
        print("\n🧪 Testing get_deal_timeline...")
        
        # Use a deal from created_resources if available, otherwise skip
        if not created_resources["deals"]:
            pytest.skip("No deals created yet - run create tests first")
        
        deal_id = created_resources["deals"][0]["id"]
        deal_name = created_resources["deals"][0]["name"]
        
        print(f"📊 Getting timeline for deal: {deal_name} (ID: {deal_id})")
        result = await retry_on_error(
            lambda: integration_client.get_deal_timeline(deal_id=deal_id)
        )
        
        assert result["success"] is True, f"Failed: {result.get('error')}"
        assert "data" in result
        
        timeline = result["data"]["response"]
        assert isinstance(timeline, list), "Timeline should be a list"
        
        print(f"✅ Retrieved {len(timeline)} timeline entries")
        
        if len(timeline) > 0:
            # Show first few entries
            for entry in timeline[:3]:
                print(f"   📌 {entry.get('action', 'Unknown action')} - {entry.get('created_at', 'No timestamp')}")
    
    @pytest.mark.asyncio
    async def test_deal_stage_history(self, integration_client, created_resources):
        """Test getting deal stage change history."""
        print("\n🧪 Testing get_deal_stage_history...")
        
        # Use a deal from created_resources if available, otherwise skip
        if not created_resources["deals"]:
            pytest.skip("No deals created yet - run create tests first")
        
        deal_id = created_resources["deals"][0]["id"]
        deal_name = created_resources["deals"][0]["name"]
        
        print(f"📊 Getting stage history for deal: {deal_name} (ID: {deal_id})")
        result = await retry_on_error(
            lambda: integration_client.get_deal_stage_history(deal_id=deal_id)
        )
        
        assert result["success"] is True, f"Failed: {result.get('error')}"
        assert "data" in result
        
        history = result["data"]["response"]
        assert isinstance(history, list), "Stage history should be a list"
        
        print(f"✅ Retrieved {len(history)} stage change entries")
        
        if len(history) > 0:
            # Show stage changes
            for entry in history[:3]:
                print(f"   📍 Stage: {entry.get('stage_name', 'Unknown')} - {entry.get('created_at', 'No timestamp')}")


@pytest.mark.integration_manual
class TestDealCustomFields:
    """Test deal creation with custom fields."""
    
    @pytest.mark.asyncio
    async def test_deal_with_custom_fields_array_format(self, integration_client, discovered_ids, created_resources):
        """Test creating a deal with custom fields using array format (preferred)."""
        print("\n🧪 Testing create_deal with custom fields (array format)...")
        
        # Get pipeline and stage
        pipeline_id = discovered_ids["deals"]["pipelines"][0]["id"]
        stage_id = discovered_ids["deals"]["stages"][pipeline_id][0]["id"]
        
        # Get required fields to check for custom fields
        fields_result = await retry_on_error(
            lambda: integration_client.get_required_fields_for_deal(
                pipeline_id=pipeline_id,
                stage_id=stage_id
            )
        )
        
        fields = fields_result["data"]["response"]
        custom_fields = [f for f in fields if f.get("additional_field")]
        
        # Get required fields for this pipeline/stage
        from .conftest import get_required_fields_for_deal, generate_field_value
        required = await get_required_fields_for_deal(integration_client, pipeline_id, stage_id)
        
        # Create deal with custom fields if available
        deal_name = generate_test_name("INTEGRATION_TEST_DEAL_CUSTOM")
        additional_fields = []
        
        # Add required custom fields first
        for field in required["custom_fields"]:
            if field["type"] not in ["Photo", "File", "Signature", "Checklist"]:
                additional_fields.append({
                    "id": field.get("id"),
                    "name": field["name"],
                    "value": generate_field_value(field)
                })
                print(f"   📝 Adding required custom field: {field['name']}")
        
        # Add optional custom field if available (non-file/photo type)
        for field in custom_fields[:2]:  # Try first 2 custom fields
            if field["type"] not in ["Photo", "File", "Signature", "Checklist"]:
                field_value = "Integration Test Value"
                if field["type"] == "Number":
                    field_value = "100"
                elif field["type"] == "Date":
                    field_value = "2025-12-31"
                
                additional_fields.append({
                    "id": field.get("id"),
                    "name": field["name"],
                    "value": field_value
                })
                print(f"   📝 Adding custom field: {field['name']} = {field_value}")
        
        deal_data = {
            "name": deal_name,
            "crm_pipeline_id": pipeline_id,
            "crm_stage_id": stage_id,
            **required["standard_fields"],
            "additional_fields": additional_fields  # Array format
        }
        
        print(f"📤 Creating deal with {len(additional_fields)} custom fields")
        create_result = await retry_on_error(
            lambda: integration_client.create_deal(deal_data=deal_data)
        )
        
        assert create_result["success"] is True, f"Create failed: {create_result.get('error')}"
        
        deal_id = create_result["data"]["response"]["id"]
        print(f"✅ Deal created with custom fields, ID: {deal_id}")
        
        # Log the created deal
        log_resource_created(
            created_resources,
            "deals",
            deal_id,
            deal_name,
            "test_deal_with_custom_fields_array_format",
            status="created",
            pipeline_id=pipeline_id,
            stage_id=stage_id,
            custom_fields_count=len(additional_fields)
        )
