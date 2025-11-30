"""
Async HTTP client for Qontak CRM API.

Security features:
- Input validation for all parameters
- Rate limiting integration
- Structured security logging
- Safe error handling (no information disclosure)
"""

import time
import httpx
from typing import Optional, Any

from .auth import QontakAuth
from .validation import (
    validate_user_id,
    validate_resource_id,
    validate_pagination,
    ValidationError,
)
from .rate_limit import get_rate_limiter
from .logging import get_logger
from .errors import safe_error_response, internal_error_response


# Qontak API base URL
QONTAK_API_BASE = "https://app.qontak.com/api/v3.1"


class QontakClient:
    """
    Async HTTP client for Qontak CRM API.
    
    This client handles:
    - Authentication (via QontakAuth)
    - Request/response handling with rate limiting
    - Structured logging for security events
    - Safe error handling (no information disclosure)
    
    All methods return a dict that can be used directly as MCP tool response.
    On success: {"success": True, "data": ...}
    On error: {"success": False, "error": "..."}
    """
    
    def __init__(self, auth: Optional[QontakAuth] = None) -> None:
        """
        Initialize the Qontak client.
        
        Args:
            auth: Optional QontakAuth instance. If not provided, creates default.
        """
        self._auth = auth or QontakAuth()
        self._http_client: Optional[httpx.AsyncClient] = None
        self._logger = get_logger()
        self._rate_limiter = get_rate_limiter()
    
    async def _get_http_client(self) -> httpx.AsyncClient:
        """Get or create the HTTP client."""
        if self._http_client is None or self._http_client.is_closed:
            self._http_client = httpx.AsyncClient(
                base_url=QONTAK_API_BASE,
                timeout=30.0,
                # Explicitly verify SSL certificates
                verify=True,
            )
        return self._http_client
    
    async def close(self) -> None:
        """Close the HTTP client and auth client."""
        if self._http_client and not self._http_client.is_closed:
            await self._http_client.aclose()
            self._http_client = None
        await self._auth.close()
    
    async def _request(
        self,
        method: str,
        path: str,
        user_id: Optional[str] = None,
        params: Optional[dict] = None,
        json: Optional[dict] = None,
        data: Optional[dict] = None,
    ) -> dict[str, Any]:
        """
        Make an authenticated request to the Qontak API.
        
        Args:
            method: HTTP method (GET, POST, PUT, PATCH, DELETE)
            path: API path (e.g., "/deals")
            user_id: Optional user/tenant identifier
            params: Optional query parameters
            json: Optional JSON body
            data: Optional form data
        
        Returns:
            Response dict with success/error format
        """
        start_time = time.monotonic()
        
        try:
            # Validate user_id for tenant isolation (CRITICAL)
            user_id_result = validate_user_id(user_id)
            if not user_id_result.is_valid:
                self._logger.validation_failure(
                    field="user_id",
                    reason=user_id_result.error or "Invalid format",
                    user_id=user_id,
                )
                return {
                    "success": False,
                    "error": "Invalid request parameters.",
                    "error_code": "validation"
                }
            validated_user_id = user_id_result.sanitized_value
            
            # Check rate limit
            allowed, error_msg = await self._rate_limiter.check_rate_limit(
                user_id=validated_user_id
            )
            if not allowed:
                self._logger.rate_limit_exceeded(user_id=validated_user_id)
                return {
                    "success": False,
                    "error": error_msg or "Rate limit exceeded. Please try again later.",
                    "error_code": "rate_limited"
                }
            
            # Log the request
            self._logger.api_request(method, path, user_id=validated_user_id)
            
            # Get auth headers with validated user_id
            headers = await self._auth.get_auth_headers(validated_user_id)
            
            # Get HTTP client
            client = await self._get_http_client()
            
            # Make request
            response = await client.request(
                method=method,
                url=path,
                headers=headers,
                params=params,
                json=json,
                data=data,
            )
            
            duration_ms = (time.monotonic() - start_time) * 1000
            
            # Handle error responses
            if response.status_code >= 400:
                self._logger.api_response(
                    method, path, response.status_code, duration_ms,
                    user_id=validated_user_id
                )
                
                # Parse error and return full details for debugging
                try:
                    error_data = response.json()
                    print(f"\n🔍 Qontak API Error Response:")
                    print(f"   Status: {response.status_code}")
                    print(f"   Response: {error_data}")
                    
                    # Only use safe, expected error messages from API
                    error_message = error_data.get("message", "Request failed")
                    # Sanitize the error message
                    if len(error_message) > 200:
                        error_message = error_message[:200] + "..."
                except Exception as e:
                    print(f"\n🔍 Qontak API Error (no JSON):")
                    print(f"   Status: {response.status_code}")
                    print(f"   Text: {response.text[:500]}")
                    error_message = "Request failed"
                
                return {
                    "success": False,
                    "error": error_message,
                    "status_code": response.status_code,
                    "error_data": error_data if 'error_data' in locals() else None
                }
            
            # Log successful response
            self._logger.api_response(
                method, path, response.status_code, duration_ms,
                user_id=validated_user_id
            )
            
            # Parse successful response
            try:
                response_data = response.json()
            except Exception:
                response_data = {"raw": response.text}
            
            return {
                "success": True,
                "data": response_data
            }
            
        except httpx.TimeoutException:
            duration_ms = (time.monotonic() - start_time) * 1000
            self._logger.api_response(method, path, 504, duration_ms, user_id=user_id)
            return {
                "success": False,
                "error": "Request timed out. Please try again.",
                "error_code": "timeout"
            }
        except httpx.ConnectError:
            duration_ms = (time.monotonic() - start_time) * 1000
            self._logger.api_response(method, path, 503, duration_ms, user_id=user_id)
            return {
                "success": False,
                "error": "Service temporarily unavailable. Please try again.",
                "error_code": "service_unavailable"
            }
        except ValueError as e:
            # Validation errors - safe to show field info
            self._logger.validation_failure(
                field="unknown",
                reason=str(e),
                user_id=user_id,
            )
            return {
                "success": False,
                "error": "Invalid request parameters.",
                "error_code": "validation"
            }
        except Exception as e:
            # NEVER expose internal error details
            self._logger.api_error(method, path, e, user_id=user_id)
            return internal_error_response()
    
    # ===== DEALS =====
    
    async def get_deal_template(self, user_id: Optional[str] = None) -> dict[str, Any]:
        """Get deal template/schema."""
        return await self._request("GET", "/deals/info", user_id=user_id)
    
    async def get_required_fields_for_deal(
        self, pipeline_id: int, stage_id: int, user_id: Optional[str] = None
    ) -> dict[str, Any]:
        """Get required fields for a specific pipeline and stage (alias for get_deal_template with filtering)."""
        # Note: The actual API returns all fields with required_pipeline_ids/required_stage_ids arrays
        # Callers should filter based on pipeline_id and stage_id from the template response
        return await self.get_deal_template(user_id=user_id)
    
    async def list_deals(
        self,
        page: int = 1,
        per_page: int = 25,
        stage_id: Optional[int] = None,
        pipeline_id: Optional[int] = None,
        user_id: Optional[str] = None,
    ) -> dict[str, Any]:
        """List deals with optional filters."""
        # Validate pagination
        pagination_result = validate_pagination(page, per_page)
        if not pagination_result.is_valid:
            return {"success": False, "error": pagination_result.error}
        
        params = {"page": page, "per_page": per_page}
        
        # Validate optional IDs
        if stage_id is not None:
            id_result = validate_resource_id(stage_id, "stage_id")
            if not id_result.is_valid:
                return {"success": False, "error": id_result.error}
            params["stage_id"] = stage_id
        if pipeline_id is not None:
            id_result = validate_resource_id(pipeline_id, "pipeline_id")
            if not id_result.is_valid:
                return {"success": False, "error": id_result.error}
            params["pipeline_id"] = pipeline_id
            
        return await self._request("GET", "/deals", user_id=user_id, params=params)
    
    async def get_deal(self, deal_id: int, user_id: Optional[str] = None) -> dict[str, Any]:
        """Get a single deal by ID."""
        # Validate deal_id
        id_result = validate_resource_id(deal_id, "deal_id")
        if not id_result.is_valid:
            return {"success": False, "error": id_result.error}
        return await self._request("GET", f"/deals/{deal_id}", user_id=user_id)
    
    async def create_deal(
        self,
        deal_data: dict[str, Any],
        user_id: Optional[str] = None
    ) -> dict[str, Any]:
        """Create a new deal."""
        return await self._request("POST", "/deals", user_id=user_id, json=deal_data)
    
    async def update_deal(
        self,
        deal_id: int,
        deal_data: dict[str, Any],
        user_id: Optional[str] = None
    ) -> dict[str, Any]:
        """Update an existing deal."""
        # Validate deal_id
        id_result = validate_resource_id(deal_id, "deal_id")
        if not id_result.is_valid:
            return {"success": False, "error": id_result.error}
        return await self._request("PUT", f"/deals/{deal_id}", user_id=user_id, json=deal_data)
    
    async def get_deal_timeline(
        self,
        deal_id: int,
        page: int = 1,
        per_page: int = 25,
        user_id: Optional[str] = None,
    ) -> dict[str, Any]:
        """Get deal activity timeline."""
        # Validate deal_id
        id_result = validate_resource_id(deal_id, "deal_id")
        if not id_result.is_valid:
            return {"success": False, "error": id_result.error}
        # Validate pagination
        pagination_result = validate_pagination(page, per_page)
        if not pagination_result.is_valid:
            return {"success": False, "error": pagination_result.error}
        
        params = {"page": page, "per_page": per_page}
        return await self._request(
            "GET", f"/deals/{deal_id}/timeline", user_id=user_id, params=params
        )
    
    async def get_deal_stage_history(
        self,
        deal_id: int,
        page: int = 1,
        per_page: int = 25,
        user_id: Optional[str] = None,
    ) -> dict[str, Any]:
        """Get deal stage change history."""
        # Validate deal_id
        id_result = validate_resource_id(deal_id, "deal_id")
        if not id_result.is_valid:
            return {"success": False, "error": id_result.error}
        # Validate pagination
        pagination_result = validate_pagination(page, per_page)
        if not pagination_result.is_valid:
            return {"success": False, "error": pagination_result.error}
        
        params = {"page": page, "per_page": per_page}
        return await self._request(
            "GET", f"/deals/{deal_id}/stage_history", user_id=user_id, params=params
        )
    
    # ===== PIPELINES =====
    
    async def list_pipelines(self, user_id: Optional[str] = None) -> dict[str, Any]:
        """List all pipelines."""
        return await self._request("GET", "/pipelines", user_id=user_id)
    
    async def get_pipeline(
        self, pipeline_id: int, user_id: Optional[str] = None
    ) -> dict[str, Any]:
        """Get a single pipeline by ID."""
        # Validate pipeline_id
        id_result = validate_resource_id(pipeline_id, "pipeline_id")
        if not id_result.is_valid:
            return {"success": False, "error": id_result.error}
        return await self._request("GET", f"/pipelines/{pipeline_id}", user_id=user_id)
    
    async def list_pipeline_stages(
        self, pipeline_id: int, user_id: Optional[str] = None
    ) -> dict[str, Any]:
        """List all stages for a specific pipeline."""
        # Validate pipeline_id
        id_result = validate_resource_id(pipeline_id, "pipeline_id")
        if not id_result.is_valid:
            return {"success": False, "error": id_result.error}
        return await self._request(
            "GET", f"/pipelines/{pipeline_id}/stages", user_id=user_id
        )
    
    # ===== TICKETS =====
    
    async def get_ticket_template(self, user_id: Optional[str] = None) -> dict[str, Any]:
        """Get ticket template/schema."""
        return await self._request("GET", "/tickets/info", user_id=user_id)
    
    async def get_required_fields_for_ticket(
        self, pipeline_id: int, user_id: Optional[str] = None
    ) -> dict[str, Any]:
        """Get required fields for a specific ticket pipeline (alias for get_ticket_template with filtering)."""
        # Note: The actual API returns all fields with required_pipeline_ids arrays
        # Callers should filter based on pipeline_id from the template response
        return await self.get_ticket_template(user_id=user_id)
    
    async def list_ticket_pipelines_and_stages(self, user_id: Optional[str] = None) -> dict[str, Any]:
        """List ticket pipelines and stages by parsing the ticket template."""
        # The ticket template contains pipeline and stage information in dropdown fields
        template_result = await self.get_ticket_template(user_id=user_id)
        
        if not template_result.get("success"):
            return template_result
        
        # Extract pipelines and stages from the template response
        fields = template_result.get("data", {}).get("response", [])
        pipelines = []
        stages_by_pipeline = {}
        
        for field in fields:
            if field.get("name") == "ticket_pipeline_id" and "dropdown" in field:
                pipelines = field["dropdown"]
            elif field.get("name") == "ticket_stage_id" and "dropdown" in field:
                for stage in field["dropdown"]:
                    pipeline_id = stage.get("ticket_pipeline_id")
                    if pipeline_id:
                        if pipeline_id not in stages_by_pipeline:
                            stages_by_pipeline[pipeline_id] = []
                        stages_by_pipeline[pipeline_id].append(stage)
        
        # Build response with pipelines and their stages
        result_data = []
        for pipeline in pipelines:
            pipeline_with_stages = pipeline.copy()
            pipeline_with_stages["stages"] = stages_by_pipeline.get(pipeline["id"], [])
            result_data.append(pipeline_with_stages)
        
        return {
            "success": True,
            "data": {
                "response": result_data
            }
        }
    
    async def list_tickets(
        self,
        page: int = 1,
        per_page: int = 25,
        pipeline_id: Optional[int] = None,
        user_id: Optional[str] = None,
    ) -> dict[str, Any]:
        """List tickets with optional filters."""
        # Validate pagination
        pagination_result = validate_pagination(page, per_page)
        if not pagination_result.is_valid:
            return {"success": False, "error": pagination_result.error}
        
        params = {"page": page, "per_page": per_page}
        if pipeline_id is not None:
            id_result = validate_resource_id(pipeline_id, "pipeline_id")
            if not id_result.is_valid:
                return {"success": False, "error": id_result.error}
            params["pipeline_id"] = pipeline_id
        return await self._request("GET", "/tickets", user_id=user_id, params=params)
    
    async def get_ticket(self, ticket_id: int, user_id: Optional[str] = None) -> dict[str, Any]:
        """Get a single ticket by ID."""
        # Validate ticket_id
        id_result = validate_resource_id(ticket_id, "ticket_id")
        if not id_result.is_valid:
            return {"success": False, "error": id_result.error}
        return await self._request("GET", f"/tickets/{ticket_id}", user_id=user_id)
    
    async def create_ticket(
        self,
        ticket_data: dict[str, Any],
        user_id: Optional[str] = None
    ) -> dict[str, Any]:
        """Create a new ticket."""
        return await self._request("POST", "/tickets", user_id=user_id, json=ticket_data)
    
    async def update_ticket(
        self,
        ticket_id: int,
        ticket_data: dict[str, Any],
        user_id: Optional[str] = None
    ) -> dict[str, Any]:
        """Update an existing ticket."""
        # Validate ticket_id
        id_result = validate_resource_id(ticket_id, "ticket_id")
        if not id_result.is_valid:
            return {"success": False, "error": id_result.error}
        return await self._request("PUT", f"/tickets/{ticket_id}", user_id=user_id, json=ticket_data)
    
    async def get_ticket_pipelines(
        self,
        page: int = 1,
        per_page: int = 25,
        user_id: Optional[str] = None,
    ) -> dict[str, Any]:
        """Get available ticket pipelines and stages."""
        # Validate pagination
        pagination_result = validate_pagination(page, per_page)
        if not pagination_result.is_valid:
            return {"success": False, "error": pagination_result.error}
        
        params = {"page": page, "per_page": per_page}
        return await self._request("GET", "/tickets/ticket_pipelines", user_id=user_id, params=params)
    
    # ===== TASKS =====
    
    async def get_task_template(self, user_id: Optional[str] = None) -> dict[str, Any]:
        """Get task template/schema."""
        return await self._request("GET", "/tasks/info", user_id=user_id)
    
    async def get_required_fields_for_task(self, user_id: Optional[str] = None) -> dict[str, Any]:
        """Get required fields for creating/updating tasks (alias for get_task_template)."""
        return await self.get_task_template(user_id=user_id)
    
    async def list_tasks(
        self,
        page: int = 1,
        per_page: int = 25,
        category_id: Optional[int] = None,
        user_id: Optional[str] = None,
    ) -> dict[str, Any]:
        """List tasks with optional filters."""
        # Validate pagination
        pagination_result = validate_pagination(page, per_page)
        if not pagination_result.is_valid:
            return {"success": False, "error": pagination_result.error}
        
        params = {"page": page, "per_page": per_page}
        if category_id is not None:
            id_result = validate_resource_id(category_id, "category_id")
            if not id_result.is_valid:
                return {"success": False, "error": id_result.error}
            params["category_id"] = category_id
        return await self._request("GET", "/tasks", user_id=user_id, params=params)
    
    async def get_task(self, task_id: int, user_id: Optional[str] = None) -> dict[str, Any]:
        """Get a single task by ID."""
        # Validate task_id
        id_result = validate_resource_id(task_id, "task_id")
        if not id_result.is_valid:
            return {"success": False, "error": id_result.error}
        return await self._request("GET", f"/tasks/{task_id}", user_id=user_id)
    
    async def create_task(
        self,
        task_data: dict[str, Any],
        user_id: Optional[str] = None
    ) -> dict[str, Any]:
        """Create a new task."""
        return await self._request("POST", "/tasks", user_id=user_id, json=task_data)
    
    async def update_task(
        self,
        task_id: int,
        task_data: dict[str, Any],
        user_id: Optional[str] = None
    ) -> dict[str, Any]:
        """Update an existing task."""
        # Validate task_id
        id_result = validate_resource_id(task_id, "task_id")
        if not id_result.is_valid:
            return {"success": False, "error": id_result.error}
        return await self._request("PUT", f"/tasks/{task_id}", user_id=user_id, json=task_data)
    
    async def list_task_categories(
        self,
        page: int = 1,
        per_page: int = 25,
        user_id: Optional[str] = None,
    ) -> dict[str, Any]:
        """List available task categories."""
        # Validate pagination
        pagination_result = validate_pagination(page, per_page)
        if not pagination_result.is_valid:
            return {"success": False, "error": pagination_result.error}
        
        params = {"page": page, "per_page": per_page}
        return await self._request("GET", "/tasks/category", user_id=user_id, params=params)
    
    async def create_task_category(
        self,
        name: str,
        color: Optional[str] = None,
        user_id: Optional[str] = None,
    ) -> dict[str, Any]:
        """Create a new task category."""
        category_data: dict[str, Any] = {"name": name}
        if color is not None:
            category_data["color"] = color
        return await self._request(
            "POST", "/tasks/category", user_id=user_id, json=category_data
        )
    
    async def delete_task(self, task_id: int, user_id: Optional[str] = None) -> dict[str, Any]:
        """Delete a task."""
        # Validate task_id
        id_result = validate_resource_id(task_id, "task_id")
        if not id_result.is_valid:
            return {"success": False, "error": id_result.error}
        return await self._request("DELETE", f"/tasks/{task_id}", user_id=user_id)
    
    async def delete_task_category(
        self, category_id: int, user_id: Optional[str] = None
    ) -> dict[str, Any]:
        """Delete a task category."""
        # Validate category_id
        id_result = validate_resource_id(category_id, "category_id")
        if not id_result.is_valid:
            return {"success": False, "error": id_result.error}
        return await self._request("DELETE", f"/tasks/category/{category_id}", user_id=user_id)
    
    async def delete_ticket(self, ticket_id: int, user_id: Optional[str] = None) -> dict[str, Any]:
        """Delete a ticket."""
        # Validate ticket_id
        id_result = validate_resource_id(ticket_id, "ticket_id")
        if not id_result.is_valid:
            return {"success": False, "error": id_result.error}
        return await self._request("DELETE", f"/tickets/{ticket_id}", user_id=user_id)
    
    # ===== CONTACTS =====
    
    async def get_contact_template(self, user_id: Optional[str] = None) -> dict[str, Any]:
        """Get contact template/schema."""
        return await self._request("GET", "/contacts/info", user_id=user_id)
    
    async def list_contacts(
        self,
        page: int = 1,
        per_page: int = 25,
        user_id: Optional[str] = None,
    ) -> dict[str, Any]:
        """List contacts with optional filters."""
        pagination_result = validate_pagination(page, per_page)
        if not pagination_result.is_valid:
            return {"success": False, "error": pagination_result.error}
        
        params = {"page": page, "per_page": per_page}
        return await self._request("GET", "/contacts", user_id=user_id, params=params)
    
    async def get_contact(self, contact_id: int, user_id: Optional[str] = None) -> dict[str, Any]:
        """Get a single contact by ID."""
        id_result = validate_resource_id(contact_id, "contact_id")
        if not id_result.is_valid:
            return {"success": False, "error": id_result.error}
        return await self._request("GET", f"/contacts/{contact_id}", user_id=user_id)
    
    async def create_contact(
        self,
        contact_data: dict[str, Any],
        user_id: Optional[str] = None
    ) -> dict[str, Any]:
        """Create a new contact."""
        return await self._request("POST", "/contacts", user_id=user_id, json=contact_data)
    
    async def update_contact(
        self,
        contact_id: int,
        contact_data: dict[str, Any],
        user_id: Optional[str] = None
    ) -> dict[str, Any]:
        """Update an existing contact."""
        id_result = validate_resource_id(contact_id, "contact_id")
        if not id_result.is_valid:
            return {"success": False, "error": id_result.error}
        return await self._request("PUT", f"/contacts/{contact_id}", user_id=user_id, json=contact_data)
    
    async def delete_contact(self, contact_id: int, user_id: Optional[str] = None) -> dict[str, Any]:
        """Delete a contact."""
        id_result = validate_resource_id(contact_id, "contact_id")
        if not id_result.is_valid:
            return {"success": False, "error": id_result.error}
        return await self._request("DELETE", f"/contacts/{contact_id}", user_id=user_id)
    
    async def get_contact_timeline(
        self,
        contact_id: int,
        page: int = 1,
        per_page: int = 25,
        user_id: Optional[str] = None,
    ) -> dict[str, Any]:
        """Get contact activity timeline."""
        id_result = validate_resource_id(contact_id, "contact_id")
        if not id_result.is_valid:
            return {"success": False, "error": id_result.error}
        pagination_result = validate_pagination(page, per_page)
        if not pagination_result.is_valid:
            return {"success": False, "error": pagination_result.error}
        
        params = {"page": page, "per_page": per_page}
        return await self._request("GET", f"/contacts/{contact_id}/timeline", user_id=user_id, params=params)
    
    async def get_contact_chat_history(
        self,
        contact_id: int,
        page: int = 1,
        per_page: int = 25,
        user_id: Optional[str] = None,
    ) -> dict[str, Any]:
        """Get contact chat history."""
        id_result = validate_resource_id(contact_id, "contact_id")
        if not id_result.is_valid:
            return {"success": False, "error": id_result.error}
        pagination_result = validate_pagination(page, per_page)
        if not pagination_result.is_valid:
            return {"success": False, "error": pagination_result.error}
        
        params = {"page": page, "per_page": per_page}
        return await self._request("GET", f"/contacts/{contact_id}/chat_history", user_id=user_id, params=params)
    
    async def update_contact_owner(
        self,
        contact_id: int,
        creator_id: int,
        user_id: Optional[str] = None
    ) -> dict[str, Any]:
        """Update contact owner."""
        id_result = validate_resource_id(contact_id, "contact_id")
        if not id_result.is_valid:
            return {"success": False, "error": id_result.error}
        owner_data = {"creator_id": creator_id}
        return await self._request("PUT", f"/contacts/{contact_id}/owner", user_id=user_id, json=owner_data)
    
    # ===== COMPANIES =====
    
    async def get_company_template(self, user_id: Optional[str] = None) -> dict[str, Any]:
        """Get company template/schema."""
        return await self._request("GET", "/companies/info", user_id=user_id)
    
    async def list_companies(
        self,
        page: int = 1,
        per_page: int = 25,
        user_id: Optional[str] = None,
    ) -> dict[str, Any]:
        """List companies with optional filters."""
        pagination_result = validate_pagination(page, per_page)
        if not pagination_result.is_valid:
            return {"success": False, "error": pagination_result.error}
        
        params = {"page": page, "per_page": per_page}
        return await self._request("GET", "/companies", user_id=user_id, params=params)
    
    async def get_company(self, company_id: int, user_id: Optional[str] = None) -> dict[str, Any]:
        """Get a single company by ID."""
        id_result = validate_resource_id(company_id, "company_id")
        if not id_result.is_valid:
            return {"success": False, "error": id_result.error}
        return await self._request("GET", f"/companies/{company_id}", user_id=user_id)
    
    async def create_company(
        self,
        company_data: dict[str, Any],
        user_id: Optional[str] = None
    ) -> dict[str, Any]:
        """Create a new company."""
        return await self._request("POST", "/companies", user_id=user_id, json=company_data)
    
    async def update_company(
        self,
        company_id: int,
        company_data: dict[str, Any],
        user_id: Optional[str] = None
    ) -> dict[str, Any]:
        """Update an existing company."""
        id_result = validate_resource_id(company_id, "company_id")
        if not id_result.is_valid:
            return {"success": False, "error": id_result.error}
        return await self._request("PUT", f"/companies/{company_id}", user_id=user_id, json=company_data)
    
    async def delete_company(self, company_id: int, user_id: Optional[str] = None) -> dict[str, Any]:
        """Delete a company."""
        id_result = validate_resource_id(company_id, "company_id")
        if not id_result.is_valid:
            return {"success": False, "error": id_result.error}
        return await self._request("DELETE", f"/companies/{company_id}", user_id=user_id)
    
    async def get_company_timeline(
        self,
        company_id: int,
        page: int = 1,
        per_page: int = 25,
        user_id: Optional[str] = None,
    ) -> dict[str, Any]:
        """Get company activity timeline."""
        id_result = validate_resource_id(company_id, "company_id")
        if not id_result.is_valid:
            return {"success": False, "error": id_result.error}
        pagination_result = validate_pagination(page, per_page)
        if not pagination_result.is_valid:
            return {"success": False, "error": pagination_result.error}
        
        params = {"page": page, "per_page": per_page}
        return await self._request("GET", f"/companies/{company_id}/timeline", user_id=user_id, params=params)
    
    # ===== NOTES =====
    
    async def get_note_template(self, user_id: Optional[str] = None) -> dict[str, Any]:
        """Get note field definitions and schema (notes don't have templates in API, returns empty structure)."""
        # Notes API doesn't have a template endpoint, return a simple structure
        return {
            "success": True,
            "data": {
                "message": "Notes have a simple structure: content (required), crm_lead_id, crm_company_id, or crm_deal_id"
            }
        }
    
    async def list_notes(
        self,
        page: int = 1,
        per_page: int = 25,
        crm_lead_id: Optional[int] = None,
        crm_company_id: Optional[int] = None,
        crm_deal_id: Optional[int] = None,
        user_id: Optional[str] = None,
    ) -> dict[str, Any]:
        """List notes with optional filters."""
        pagination_result = validate_pagination(page, per_page)
        if not pagination_result.is_valid:
            return {"success": False, "error": pagination_result.error}
        
        params: dict[str, Any] = {"page": page, "per_page": per_page}
        if crm_lead_id is not None:
            params["crm_lead_id"] = crm_lead_id
        if crm_company_id is not None:
            params["crm_company_id"] = crm_company_id
        if crm_deal_id is not None:
            params["crm_deal_id"] = crm_deal_id
        return await self._request("GET", "/notes", user_id=user_id, params=params)
    
    async def get_note(self, note_id: int, user_id: Optional[str] = None) -> dict[str, Any]:
        """Get a single note by ID."""
        id_result = validate_resource_id(note_id, "note_id")
        if not id_result.is_valid:
            return {"success": False, "error": id_result.error}
        return await self._request("GET", f"/notes/{note_id}", user_id=user_id)
    
    async def create_note(
        self,
        note_data: dict[str, Any],
        user_id: Optional[str] = None
    ) -> dict[str, Any]:
        """Create a new note."""
        return await self._request("POST", "/notes", user_id=user_id, json=note_data)
    
    async def update_note(
        self,
        note_id: int,
        note_data: dict[str, Any],
        user_id: Optional[str] = None
    ) -> dict[str, Any]:
        """Update an existing note."""
        id_result = validate_resource_id(note_id, "note_id")
        if not id_result.is_valid:
            return {"success": False, "error": id_result.error}
        return await self._request("PUT", f"/notes/{note_id}", user_id=user_id, json=note_data)
    
    async def delete_note(self, note_id: int, user_id: Optional[str] = None) -> dict[str, Any]:
        """Delete a note."""
        id_result = validate_resource_id(note_id, "note_id")
        if not id_result.is_valid:
            return {"success": False, "error": id_result.error}
        return await self._request("DELETE", f"/notes/{note_id}", user_id=user_id)
    
    # ===== PRODUCTS =====
    
    async def get_product_template(self, user_id: Optional[str] = None) -> dict[str, Any]:
        """Get product field definitions and schema (products don't have templates in API, returns empty structure)."""
        # Products API doesn't have a template endpoint, return a simple structure
        return {
            "success": True,
            "data": {
                "message": "Products have fields: name (required), sku, price, description, etc."
            }
        }
    
    async def list_products(
        self,
        page: int = 1,
        per_page: int = 25,
        user_id: Optional[str] = None,
    ) -> dict[str, Any]:
        """List products with optional filters."""
        pagination_result = validate_pagination(page, per_page)
        if not pagination_result.is_valid:
            return {"success": False, "error": pagination_result.error}
        
        params = {"page": page, "per_page": per_page}
        return await self._request("GET", "/products", user_id=user_id, params=params)
    
    async def get_product(self, product_id: int, user_id: Optional[str] = None) -> dict[str, Any]:
        """Get a single product by ID."""
        id_result = validate_resource_id(product_id, "product_id")
        if not id_result.is_valid:
            return {"success": False, "error": id_result.error}
        return await self._request("GET", f"/products/{product_id}", user_id=user_id)
    
    async def create_product(
        self,
        product_data: dict[str, Any],
        user_id: Optional[str] = None
    ) -> dict[str, Any]:
        """Create a new product."""
        return await self._request("POST", "/products", user_id=user_id, json=product_data)
    
    async def update_product(
        self,
        product_id: int,
        product_data: dict[str, Any],
        user_id: Optional[str] = None
    ) -> dict[str, Any]:
        """Update an existing product."""
        id_result = validate_resource_id(product_id, "product_id")
        if not id_result.is_valid:
            return {"success": False, "error": id_result.error}
        return await self._request("PUT", f"/products/{product_id}", user_id=user_id, json=product_data)
    
    async def delete_product(self, product_id: int, user_id: Optional[str] = None) -> dict[str, Any]:
        """Delete a product."""
        id_result = validate_resource_id(product_id, "product_id")
        if not id_result.is_valid:
            return {"success": False, "error": id_result.error}
        return await self._request("DELETE", f"/products/{product_id}", user_id=user_id)
    
    # ===== PRODUCTS ASSOCIATION =====
    
    async def get_products_association_template(self, user_id: Optional[str] = None) -> dict[str, Any]:
        """Get products association field definitions and schema (doesn't have templates in API, returns empty structure)."""
        # Products Association API doesn't have a template endpoint, return a simple structure
        return {
            "success": True,
            "data": {
                "message": "Products associations link products to entities: product_id, entity_type (contact/company/deal), entity_id, quantity, price"
            }
        }
    
    async def list_products_associations(
        self,
        page: int = 1,
        per_page: int = 25,
        user_id: Optional[str] = None,
    ) -> dict[str, Any]:
        """List product associations with optional filters."""
        pagination_result = validate_pagination(page, per_page)
        if not pagination_result.is_valid:
            return {"success": False, "error": pagination_result.error}
        
        params = {"page": page, "per_page": per_page}
        return await self._request("GET", "/products_association", user_id=user_id, params=params)
    
    async def get_products_association(self, association_id: int, user_id: Optional[str] = None) -> dict[str, Any]:
        """Get a single product association by ID."""
        id_result = validate_resource_id(association_id, "association_id")
        if not id_result.is_valid:
            return {"success": False, "error": id_result.error}
        return await self._request("GET", f"/products_association/{association_id}", user_id=user_id)
    
    async def create_products_association(
        self,
        association_data: dict[str, Any],
        user_id: Optional[str] = None
    ) -> dict[str, Any]:
        """Create a new product association."""
        return await self._request("POST", "/products_association", user_id=user_id, json=association_data)
    
    async def update_products_association(
        self,
        association_id: int,
        association_data: dict[str, Any],
        user_id: Optional[str] = None
    ) -> dict[str, Any]:
        """Update an existing product association."""
        id_result = validate_resource_id(association_id, "association_id")
        if not id_result.is_valid:
            return {"success": False, "error": id_result.error}
        return await self._request("PUT", f"/products_association/{association_id}", user_id=user_id, json=association_data)
    
    async def delete_products_association(self, association_id: int, user_id: Optional[str] = None) -> dict[str, Any]:
        """Delete a product association."""
        id_result = validate_resource_id(association_id, "association_id")
        if not id_result.is_valid:
            return {"success": False, "error": id_result.error}
        return await self._request("DELETE", f"/products_association/{association_id}", user_id=user_id)
    
    # ===== DEAL EXTENSIONS =====
    
    async def get_deal_chat_history(
        self,
        deal_id: int,
        page: int = 1,
        per_page: int = 25,
        user_id: Optional[str] = None,
    ) -> dict[str, Any]:
        """Get deal chat history."""
        id_result = validate_resource_id(deal_id, "deal_id")
        if not id_result.is_valid:
            return {"success": False, "error": id_result.error}
        pagination_result = validate_pagination(page, per_page)
        if not pagination_result.is_valid:
            return {"success": False, "error": pagination_result.error}
        
        params = {"page": page, "per_page": per_page}
        return await self._request("GET", f"/deals/{deal_id}/chat_history", user_id=user_id, params=params)
    
    async def get_deal_real_creator(self, deal_id: int, user_id: Optional[str] = None) -> dict[str, Any]:
        """Get the real creator of a deal."""
        id_result = validate_resource_id(deal_id, "deal_id")
        if not id_result.is_valid:
            return {"success": False, "error": id_result.error}
        return await self._request("GET", f"/deals/{deal_id}/real_creator", user_id=user_id)
    
    async def get_deal_full_field(self, deal_id: int, user_id: Optional[str] = None) -> dict[str, Any]:
        """Get deal with full field information."""
        id_result = validate_resource_id(deal_id, "deal_id")
        if not id_result.is_valid:
            return {"success": False, "error": id_result.error}
        return await self._request("GET", f"/deals/{deal_id}/full_field", user_id=user_id)
    
    async def get_deal_permissions(self, deal_id: int, user_id: Optional[str] = None) -> dict[str, Any]:
        """Get deal permissions."""
        id_result = validate_resource_id(deal_id, "deal_id")
        if not id_result.is_valid:
            return {"success": False, "error": id_result.error}
        return await self._request("GET", f"/deals/{deal_id}/permissions", user_id=user_id)
    
    async def update_deal_owner(
        self,
        deal_id: int,
        creator_id: int,
        user_id: Optional[str] = None
    ) -> dict[str, Any]:
        """Update deal owner."""
        id_result = validate_resource_id(deal_id, "deal_id")
        if not id_result.is_valid:
            return {"success": False, "error": id_result.error}
        owner_data = {"creator_id": creator_id}
        return await self._request("PUT", f"/deals/{deal_id}/owner", user_id=user_id, json=owner_data)
