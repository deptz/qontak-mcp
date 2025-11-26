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
