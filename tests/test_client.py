import pytest
import httpx
from unittest.mock import AsyncMock, patch
from qontak_mcp.client import QontakClient

@pytest.mark.asyncio
async def test_list_deals_success(client):
    """Test listing deals successfully."""
    mock_data = {"data": [{"id": 1, "name": "Deal 1"}]}
    
    with patch.object(client, '_request', new_callable=AsyncMock) as mock_request:
        mock_request.return_value = {"success": True, "data": mock_data}
        result = await client.list_deals(page=1, per_page=10)
    
    assert result["success"] is True
    assert result["data"] == mock_data

@pytest.mark.asyncio
async def test_get_deal_success(client):
    """Test getting a single deal."""
    mock_data = {"data": {"id": 1, "name": "Deal 1"}}
    
    with patch.object(client, '_request', new_callable=AsyncMock) as mock_request:
        mock_request.return_value = {"success": True, "data": mock_data}
        result = await client.get_deal(deal_id=1)
    
    assert result["success"] is True
    assert result["data"] == mock_data

@pytest.mark.asyncio
async def test_create_deal_success(client):
    """Test creating a deal."""
    deal_data = {"name": "New Deal", "value": 1000}
    mock_response = {"data": {"id": 2, "name": "New Deal"}}
    
    with patch.object(client, '_request', new_callable=AsyncMock) as mock_request:
        mock_request.return_value = {"success": True, "data": mock_response}
        result = await client.create_deal(deal_data=deal_data)
    
    assert result["success"] is True
    assert result["data"] == mock_response

@pytest.mark.asyncio
async def test_api_error_handling(client):
    """Test handling of API errors."""
    with patch.object(client, '_request', new_callable=AsyncMock) as mock_request:
        mock_request.return_value = {"success": False, "error": "An internal error occurred: 404 Not Found"}
        result = await client.get_deal(deal_id=999)
    
    assert result["success"] is False
    assert "An internal error occurred" in result["error"]

@pytest.mark.asyncio
async def test_timeout_handling(client):
    """Test handling of timeouts."""
    with patch.object(client, '_request', new_callable=AsyncMock) as mock_request:
        mock_request.return_value = {"success": False, "error": "An internal error occurred: Request timed out"}
        result = await client.get_deal(deal_id=1)
    
    assert result["success"] is False
    assert "An internal error occurred" in result["error"]

@pytest.mark.asyncio
async def test_validation_error(client):
    """Test validation error before request."""
    # Invalid ID (string instead of int, though type hint says int, runtime check might catch it if passed as string or negative)
    # The validate_resource_id checks for positive integer.
    
    result = await client.get_deal(deal_id=-1)
    
    assert result["success"] is False
    # Validation error is caught before request, so it should be specific
    assert "must be a positive integer" in result["error"]

@pytest.mark.asyncio
async def test_list_tasks_success(client):
    """Test listing tasks successfully."""
    mock_data = {"data": [{"id": 1, "title": "Task 1"}]}
    
    with patch.object(client, '_request', new_callable=AsyncMock) as mock_request:
        mock_request.return_value = {"success": True, "data": mock_data}
        result = await client.list_tasks(page=1, per_page=10)
    
    assert result["success"] is True
    assert result["data"] == mock_data

@pytest.mark.asyncio
async def test_get_task_success(client):
    """Test getting a single task."""
    mock_data = {"data": {"id": 1, "title": "Task 1"}}
    
    with patch.object(client, '_request', new_callable=AsyncMock) as mock_request:
        mock_request.return_value = {"success": True, "data": mock_data}
        result = await client.get_task(task_id=1)
    
    assert result["success"] is True
    assert result["data"] == mock_data

@pytest.mark.asyncio
async def test_create_task_success(client):
    """Test creating a task."""
    task_data = {"title": "New Task", "user_id": 123}
    mock_response = {"data": {"id": 2, "title": "New Task"}}
    
    with patch.object(client, '_request', new_callable=AsyncMock) as mock_request:
        mock_request.return_value = {"success": True, "data": mock_response}
        result = await client.create_task(task_data=task_data)
    
    assert result["success"] is True
    assert result["data"] == mock_response

@pytest.mark.asyncio
async def test_update_task_success(client):
    """Test updating a task."""
    task_data = {"title": "Updated Task"}
    mock_response = {"data": {"id": 1, "title": "Updated Task"}}
    
    with patch.object(client, '_request', new_callable=AsyncMock) as mock_request:
        mock_request.return_value = {"success": True, "data": mock_response}
        result = await client.update_task(task_id=1, task_data=task_data)
    
    assert result["success"] is True
    assert result["data"] == mock_response



@pytest.mark.asyncio
async def test_list_tickets_success(client):
    """Test listing tickets successfully."""
    mock_data = {"data": [{"id": 1, "subject": "Ticket 1"}]}
    
    with patch.object(client, '_request', new_callable=AsyncMock) as mock_request:
        mock_request.return_value = {"success": True, "data": mock_data}
        result = await client.list_tickets(page=1, per_page=10)
    
    assert result["success"] is True
    assert result["data"] == mock_data

@pytest.mark.asyncio
async def test_get_ticket_success(client):
    """Test getting a single ticket."""
    mock_data = {"data": {"id": 1, "subject": "Ticket 1"}}
    
    with patch.object(client, '_request', new_callable=AsyncMock) as mock_request:
        mock_request.return_value = {"success": True, "data": mock_data}
        result = await client.get_ticket(ticket_id=1)
    
    assert result["success"] is True
    assert result["data"] == mock_data

@pytest.mark.asyncio
async def test_create_ticket_success(client):
    """Test creating a ticket."""
    ticket_data = {"subject": "New Ticket", "user_id": 123}
    mock_response = {"data": {"id": 2, "subject": "New Ticket"}}
    
    with patch.object(client, '_request', new_callable=AsyncMock) as mock_request:
        mock_request.return_value = {"success": True, "data": mock_response}
        result = await client.create_ticket(ticket_data=ticket_data)
    
    assert result["success"] is True
    assert result["data"] == mock_response

@pytest.mark.asyncio
async def test_update_ticket_success(client):
    """Test updating a ticket."""
    ticket_data = {"subject": "Updated Ticket"}
    mock_response = {"data": {"id": 1, "subject": "Updated Ticket"}}
    
    with patch.object(client, '_request', new_callable=AsyncMock) as mock_request:
        mock_request.return_value = {"success": True, "data": mock_response}
        result = await client.update_ticket(ticket_id=1, ticket_data=ticket_data)
    
    assert result["success"] is True
    assert result["data"] == mock_response



@pytest.mark.asyncio
async def test_update_deal_success(client):
    """Test updating a deal."""
    deal_data = {"name": "Updated Deal"}
    mock_response = {"data": {"id": 1, "name": "Updated Deal"}}
    
    with patch.object(client, '_request', new_callable=AsyncMock) as mock_request:
        mock_request.return_value = {"success": True, "data": mock_response}
        result = await client.update_deal(deal_id=1, deal_data=deal_data)
    
    assert result["success"] is True
    assert result["data"] == mock_response



@pytest.mark.asyncio
async def test_get_deal_template(client):
    """Test getting deal template."""
    mock_data = {"data": {"fields": []}}
    
    with patch.object(client, '_request', new_callable=AsyncMock) as mock_request:
        mock_request.return_value = {"success": True, "data": mock_data}
        result = await client.get_deal_template()
    
    assert result["success"] is True
    assert result["data"] == mock_data

@pytest.mark.asyncio
async def test_get_ticket_template(client):
    """Test getting ticket template."""
    mock_data = {"data": {"fields": []}}
    
    with patch.object(client, '_request', new_callable=AsyncMock) as mock_request:
        mock_request.return_value = {"success": True, "data": mock_data}
        result = await client.get_ticket_template()
    
    assert result["success"] is True
    assert result["data"] == mock_data

@pytest.mark.asyncio
async def test_get_task_template(client):
    """Test getting task template."""
    mock_data = {"data": {"fields": []}}
    
    with patch.object(client, '_request', new_callable=AsyncMock) as mock_request:
        mock_request.return_value = {"success": True, "data": mock_data}
        result = await client.get_task_template()
    
    assert result["success"] is True
    assert result["data"] == mock_data

@pytest.mark.asyncio
async def test_get_ticket_pipelines(client):
    """Test getting ticket pipelines."""
    mock_data = {"data": [{"id": 1, "name": "Pipeline 1"}]}
    
    with patch.object(client, '_request', new_callable=AsyncMock) as mock_request:
        mock_request.return_value = {"success": True, "data": mock_data}
        result = await client.get_ticket_pipelines()
    
    assert result["success"] is True
    assert result["data"] == mock_data

@pytest.mark.asyncio
async def test_list_task_categories(client):
    """Test listing task categories."""
    mock_data = {"data": [{"id": 1, "name": "Category 1"}]}
    
    with patch.object(client, '_request', new_callable=AsyncMock) as mock_request:
        mock_request.return_value = {"success": True, "data": mock_data}
        result = await client.list_task_categories()
    
    assert result["success"] is True
    assert result["data"] == mock_data

@pytest.mark.asyncio
async def test_create_task_category(client):
    """Test creating a task category."""
    mock_response = {"data": {"id": 2, "name": "New Category"}}
    
    with patch.object(client, '_request', new_callable=AsyncMock) as mock_request:
        mock_request.return_value = {"success": True, "data": mock_response}
        result = await client.create_task_category(name="New Category")
    
    assert result["success"] is True
    assert result["data"] == mock_response

@pytest.mark.asyncio
async def test_get_deal_timeline(client):
    """Test getting deal timeline."""
    mock_data = {"data": [{"id": 1, "activity": "Created"}]}
    
    with patch.object(client, '_request', new_callable=AsyncMock) as mock_request:
        mock_request.return_value = {"success": True, "data": mock_data}
        result = await client.get_deal_timeline(deal_id=1)
    
    assert result["success"] is True
    assert result["data"] == mock_data

@pytest.mark.asyncio
async def test_get_deal_stage_history(client):
    """Test getting deal stage history."""
    mock_data = {"data": [{"id": 1, "stage": "New"}]}
    
    with patch.object(client, '_request', new_callable=AsyncMock) as mock_request:
        mock_request.return_value = {"success": True, "data": mock_data}
        result = await client.get_deal_stage_history(deal_id=1)
    
    assert result["success"] is True
    assert result["data"] == mock_data

@pytest.mark.asyncio
async def test_close_client(client):
    """Test closing the client."""
    await client.close()
    assert client._http_client is None

@pytest.mark.asyncio
async def test_close_already_closed(client):
    """Test closing an already closed client."""
    await client.close()
    await client.close()  # Should not raise error
    assert client._http_client is None


# =============================================================================
# CRITICAL: Test _request method directly (the core of QontakClient)
# =============================================================================

class TestRequestMethod:
    """Test the core _request method that handles all API communication."""
    
    @pytest.mark.asyncio
    async def test_request_success(self, client):
        """Test successful API request through _request method."""
        from httpx import Response
        
        mock_response = Response(200, json={"data": [{"id": 1}]})
        
        with patch.object(client._auth, 'get_auth_headers', new_callable=AsyncMock) as mock_auth:
            mock_auth.return_value = {"Authorization": "Bearer test_token"}
            
            with patch.object(client._rate_limiter, 'check_rate_limit', new_callable=AsyncMock) as mock_rate:
                mock_rate.return_value = (True, None)
                
                # Mock the HTTP client request method
                mock_http_client = AsyncMock()
                mock_http_client.request = AsyncMock(return_value=mock_response)
                mock_http_client.is_closed = False
                
                with patch.object(client, '_get_http_client', new_callable=AsyncMock) as mock_get_client:
                    mock_get_client.return_value = mock_http_client
                    
                    result = await client._request("GET", "/deals", user_id="test-user")
        
        assert result["success"] is True
        assert result["data"] == {"data": [{"id": 1}]}
    
    @pytest.mark.asyncio
    async def test_request_invalid_user_id(self, client):
        """Test _request with invalid user_id fails validation."""
        # Use an invalid user_id format (e.g., with path traversal attempt)
        result = await client._request("GET", "/deals", user_id="../../../etc/passwd")
        
        assert result["success"] is False
        assert result["error_code"] == "validation"
    
    @pytest.mark.asyncio
    async def test_request_rate_limited(self, client):
        """Test _request returns rate limit error when rate limited."""
        with patch.object(client._rate_limiter, 'check_rate_limit', new_callable=AsyncMock) as mock_rate:
            mock_rate.return_value = (False, "Rate limit exceeded")
            
            result = await client._request("GET", "/deals", user_id="test-user")
        
        assert result["success"] is False
        assert result["error_code"] == "rate_limited"
        assert "Rate limit exceeded" in result["error"]
    
    @pytest.mark.asyncio
    async def test_request_timeout_exception(self, client):
        """Test _request handles timeout exceptions."""
        with patch.object(client._rate_limiter, 'check_rate_limit', new_callable=AsyncMock) as mock_rate:
            mock_rate.return_value = (True, None)
            
            with patch.object(client._auth, 'get_auth_headers', new_callable=AsyncMock) as mock_auth:
                mock_auth.return_value = {"Authorization": "Bearer test_token"}
                
                # Mock _get_http_client to return a client that raises timeout
                mock_http_client = AsyncMock()
                mock_http_client.request = AsyncMock(side_effect=httpx.TimeoutException("Connection timed out"))
                
                with patch.object(client, '_get_http_client', new_callable=AsyncMock) as mock_get_client:
                    mock_get_client.return_value = mock_http_client
                    
                    result = await client._request("GET", "/deals", user_id="test-user")
        
        assert result["success"] is False
        assert result["error_code"] == "timeout"
        assert "timed out" in result["error"]
    
    @pytest.mark.asyncio
    async def test_request_connect_error(self, client):
        """Test _request handles connection errors."""
        with patch.object(client._rate_limiter, 'check_rate_limit', new_callable=AsyncMock) as mock_rate:
            mock_rate.return_value = (True, None)
            
            with patch.object(client._auth, 'get_auth_headers', new_callable=AsyncMock) as mock_auth:
                mock_auth.return_value = {"Authorization": "Bearer test_token"}
                
                # Mock _get_http_client to return a client that raises connect error
                mock_http_client = AsyncMock()
                mock_http_client.request = AsyncMock(side_effect=httpx.ConnectError("Connection refused"))
                
                with patch.object(client, '_get_http_client', new_callable=AsyncMock) as mock_get_client:
                    mock_get_client.return_value = mock_http_client
                    
                    result = await client._request("GET", "/deals", user_id="test-user")
        
        assert result["success"] is False
        assert result["error_code"] == "service_unavailable"
        assert "temporarily unavailable" in result["error"]
    
    @pytest.mark.asyncio
    async def test_request_http_error_response(self, client):
        """Test _request handles HTTP error responses (4xx, 5xx)."""
        from httpx import Response
        
        mock_response = Response(404, json={"message": "Not found"})
        
        with patch.object(client._auth, 'get_auth_headers', new_callable=AsyncMock) as mock_auth:
            mock_auth.return_value = {"Authorization": "Bearer test_token"}
            
            with patch.object(client._rate_limiter, 'check_rate_limit', new_callable=AsyncMock) as mock_rate:
                mock_rate.return_value = (True, None)
                
                mock_http_client = AsyncMock()
                mock_http_client.request = AsyncMock(return_value=mock_response)
                
                with patch.object(client, '_get_http_client', new_callable=AsyncMock) as mock_get_client:
                    mock_get_client.return_value = mock_http_client
                    
                    result = await client._request("GET", "/deals", user_id="test-user")
        
        assert result["success"] is False
        assert result["status_code"] == 404
        assert "Not found" in result["error"]
    
    @pytest.mark.asyncio
    async def test_request_http_error_with_long_message(self, client):
        """Test _request truncates long error messages."""
        from httpx import Response
        
        long_message = "A" * 300  # More than 200 chars
        mock_response = Response(400, json={"message": long_message})
        
        with patch.object(client._auth, 'get_auth_headers', new_callable=AsyncMock) as mock_auth:
            mock_auth.return_value = {"Authorization": "Bearer test_token"}
            
            with patch.object(client._rate_limiter, 'check_rate_limit', new_callable=AsyncMock) as mock_rate:
                mock_rate.return_value = (True, None)
                
                mock_http_client = AsyncMock()
                mock_http_client.request = AsyncMock(return_value=mock_response)
                
                with patch.object(client, '_get_http_client', new_callable=AsyncMock) as mock_get_client:
                    mock_get_client.return_value = mock_http_client
                    
                    result = await client._request("GET", "/deals", user_id="test-user")
        
        assert result["success"] is False
        # Message should be truncated to 200 chars + "..."
        assert len(result["error"]) <= 203
        assert result["error"].endswith("...")
    
    @pytest.mark.asyncio
    async def test_request_http_error_non_json_response(self, client):
        """Test _request handles non-JSON error responses."""
        from httpx import Response, Request
        
        # Create a request for the response
        request = Request("GET", "https://app.qontak.com/api/v3.1/deals")
        mock_response = Response(500, text="Internal Server Error", request=request)
        
        with patch.object(client._auth, 'get_auth_headers', new_callable=AsyncMock) as mock_auth:
            mock_auth.return_value = {"Authorization": "Bearer test_token"}
            
            with patch.object(client._rate_limiter, 'check_rate_limit', new_callable=AsyncMock) as mock_rate:
                mock_rate.return_value = (True, None)
                
                mock_http_client = AsyncMock()
                mock_http_client.request = AsyncMock(return_value=mock_response)
                
                with patch.object(client, '_get_http_client', new_callable=AsyncMock) as mock_get_client:
                    mock_get_client.return_value = mock_http_client
                    
                    result = await client._request("GET", "/deals", user_id="test-user")
        
        assert result["success"] is False
        assert result["status_code"] == 500
        assert result["error"] == "Request failed"
    
    @pytest.mark.asyncio
    async def test_request_success_non_json_response(self, client):
        """Test _request handles successful non-JSON responses."""
        from httpx import Response, Request
        
        # Create a request for the response
        request = Request("GET", "https://app.qontak.com/api/v3.1/export")
        mock_response = Response(200, text="CSV data here", request=request)
        
        with patch.object(client._auth, 'get_auth_headers', new_callable=AsyncMock) as mock_auth:
            mock_auth.return_value = {"Authorization": "Bearer test_token"}
            
            with patch.object(client._rate_limiter, 'check_rate_limit', new_callable=AsyncMock) as mock_rate:
                mock_rate.return_value = (True, None)
                
                mock_http_client = AsyncMock()
                mock_http_client.request = AsyncMock(return_value=mock_response)
                
                with patch.object(client, '_get_http_client', new_callable=AsyncMock) as mock_get_client:
                    mock_get_client.return_value = mock_http_client
                    
                    result = await client._request("GET", "/export", user_id="test-user")
        
        assert result["success"] is True
        assert result["data"] == {"raw": "CSV data here"}
    
    @pytest.mark.asyncio
    async def test_request_general_exception(self, client):
        """Test _request handles unexpected exceptions safely."""
        with patch.object(client._rate_limiter, 'check_rate_limit', new_callable=AsyncMock) as mock_rate:
            mock_rate.return_value = (True, None)
            
            with patch.object(client._auth, 'get_auth_headers', new_callable=AsyncMock) as mock_auth:
                mock_auth.side_effect = RuntimeError("Unexpected error")
                
                result = await client._request("GET", "/deals", user_id="test-user")
        
        assert result["success"] is False
        # Should not expose internal error details
        assert "An internal error occurred" in result["error"]
    
    @pytest.mark.asyncio
    async def test_request_with_json_body(self, client):
        """Test _request with JSON body (POST/PUT)."""
        from httpx import Response
        
        mock_response = Response(201, json={"data": {"id": 123}})
        
        with patch.object(client._auth, 'get_auth_headers', new_callable=AsyncMock) as mock_auth:
            mock_auth.return_value = {"Authorization": "Bearer test_token"}
            
            with patch.object(client._rate_limiter, 'check_rate_limit', new_callable=AsyncMock) as mock_rate:
                mock_rate.return_value = (True, None)
                
                mock_http_client = AsyncMock()
                mock_http_client.request = AsyncMock(return_value=mock_response)
                
                with patch.object(client, '_get_http_client', new_callable=AsyncMock) as mock_get_client:
                    mock_get_client.return_value = mock_http_client
                    
                    result = await client._request(
                        "POST", "/deals",
                        user_id="test-user",
                        json={"name": "Test Deal", "value": 1000}
                    )
        
        assert result["success"] is True
        assert result["data"] == {"data": {"id": 123}}
        # Verify request method was called with correct parameters
        mock_http_client.request.assert_called_once()
        call_kwargs = mock_http_client.request.call_args[1]
        assert call_kwargs["method"] == "POST"
        assert call_kwargs["json"] == {"name": "Test Deal", "value": 1000}
    
    @pytest.mark.asyncio
    async def test_request_with_params(self, client):
        """Test _request with query parameters."""
        from httpx import Response
        
        mock_response = Response(200, json={"data": []})
        
        with patch.object(client._auth, 'get_auth_headers', new_callable=AsyncMock) as mock_auth:
            mock_auth.return_value = {"Authorization": "Bearer test_token"}
            
            with patch.object(client._rate_limiter, 'check_rate_limit', new_callable=AsyncMock) as mock_rate:
                mock_rate.return_value = (True, None)
                
                mock_http_client = AsyncMock()
                mock_http_client.request = AsyncMock(return_value=mock_response)
                
                with patch.object(client, '_get_http_client', new_callable=AsyncMock) as mock_get_client:
                    mock_get_client.return_value = mock_http_client
                    
                    result = await client._request(
                        "GET", "/deals",
                        user_id="test-user",
                        params={"page": 1, "per_page": 25}
                    )
        
        assert result["success"] is True
        # Verify params were passed
        call_kwargs = mock_http_client.request.call_args[1]
        assert call_kwargs["params"] == {"page": 1, "per_page": 25}
    
    @pytest.mark.asyncio
    async def test_request_value_error_handling(self, client):
        """Test _request handles ValueError as validation error."""
        with patch.object(client._rate_limiter, 'check_rate_limit', new_callable=AsyncMock) as mock_rate:
            mock_rate.return_value = (True, None)
            
            with patch.object(client._auth, 'get_auth_headers', new_callable=AsyncMock) as mock_auth:
                mock_auth.side_effect = ValueError("Invalid parameter format")
                
                result = await client._request("GET", "/deals", user_id="test-user")
        
        assert result["success"] is False
        assert result["error_code"] == "validation"
        assert "Invalid request parameters" in result["error"]


class TestHttpClientManagement:
    """Test HTTP client lifecycle management."""
    
    @pytest.mark.asyncio
    async def test_get_http_client_creates_new(self, client):
        """Test _get_http_client creates client when none exists."""
        assert client._http_client is None
        
        http_client = await client._get_http_client()
        
        assert http_client is not None
        assert isinstance(http_client, httpx.AsyncClient)
        assert client._http_client is http_client
        
        await client.close()
    
    @pytest.mark.asyncio
    async def test_get_http_client_reuses_existing(self, client):
        """Test _get_http_client reuses existing client."""
        http_client1 = await client._get_http_client()
        http_client2 = await client._get_http_client()
        
        assert http_client1 is http_client2
        
        await client.close()
    
    @pytest.mark.asyncio
    async def test_get_http_client_recreates_after_close(self, client):
        """Test _get_http_client recreates client after it's closed."""
        http_client1 = await client._get_http_client()
        await http_client1.aclose()  # Manually close it
        
        http_client2 = await client._get_http_client()
        
        assert http_client2 is not http_client1
        assert not http_client2.is_closed
        
        await client.close()


class TestValidationInClientMethods:
    """Test validation logic in client methods."""
    
    @pytest.mark.asyncio
    async def test_list_deals_invalid_pagination(self, client):
        """Test list_deals with invalid pagination."""
        result = await client.list_deals(page=0, per_page=10)
        assert result["success"] is False
        assert "page" in result["error"].lower() or "must be" in result["error"].lower()
    
    @pytest.mark.asyncio
    async def test_list_deals_invalid_per_page(self, client):
        """Test list_deals with per_page too large."""
        result = await client.list_deals(page=1, per_page=1000)
        assert result["success"] is False
    
    @pytest.mark.asyncio
    async def test_list_deals_invalid_stage_id(self, client):
        """Test list_deals with invalid stage_id."""
        result = await client.list_deals(page=1, per_page=10, stage_id=-1)
        assert result["success"] is False
        assert "stage_id" in result["error"]
    
    @pytest.mark.asyncio
    async def test_list_deals_invalid_pipeline_id(self, client):
        """Test list_deals with invalid pipeline_id."""
        result = await client.list_deals(page=1, per_page=10, pipeline_id=-1)
        assert result["success"] is False
        assert "pipeline_id" in result["error"]
    
    @pytest.mark.asyncio
    async def test_get_deal_invalid_id(self, client):
        """Test get_deal with invalid deal_id."""
        result = await client.get_deal(deal_id=-1)
        assert result["success"] is False
        assert "deal_id" in result["error"]
    
    @pytest.mark.asyncio
    async def test_update_deal_invalid_id(self, client):
        """Test update_deal with invalid deal_id."""
        result = await client.update_deal(deal_id=-1, deal_data={"name": "test"})
        assert result["success"] is False
        assert "deal_id" in result["error"]
    
    @pytest.mark.asyncio
    async def test_get_deal_timeline_invalid_pagination(self, client):
        """Test get_deal_timeline with invalid pagination."""
        result = await client.get_deal_timeline(deal_id=1, page=0)
        assert result["success"] is False
    
    @pytest.mark.asyncio
    async def test_get_deal_timeline_invalid_deal_id(self, client):
        """Test get_deal_timeline with invalid deal_id."""
        result = await client.get_deal_timeline(deal_id=-1)
        assert result["success"] is False
        assert "deal_id" in result["error"]
    
    @pytest.mark.asyncio
    async def test_get_deal_stage_history_invalid_deal_id(self, client):
        """Test get_deal_stage_history with invalid deal_id."""
        result = await client.get_deal_stage_history(deal_id=-1)
        assert result["success"] is False
        assert "deal_id" in result["error"]
    
    @pytest.mark.asyncio
    async def test_get_deal_stage_history_invalid_pagination(self, client):
        """Test get_deal_stage_history with invalid pagination."""
        result = await client.get_deal_stage_history(deal_id=1, page=-1)
        assert result["success"] is False
    
    @pytest.mark.asyncio
    async def test_list_tickets_invalid_pipeline_id(self, client):
        """Test list_tickets with invalid pipeline_id."""
        result = await client.list_tickets(pipeline_id=-1)
        assert result["success"] is False
        assert "pipeline_id" in result["error"]
    
    @pytest.mark.asyncio
    async def test_list_tickets_invalid_pagination(self, client):
        """Test list_tickets with invalid pagination."""
        result = await client.list_tickets(page=0)
        assert result["success"] is False
    
    @pytest.mark.asyncio
    async def test_get_ticket_invalid_id(self, client):
        """Test get_ticket with invalid ticket_id."""
        result = await client.get_ticket(ticket_id=-1)
        assert result["success"] is False
        assert "ticket_id" in result["error"]
    
    @pytest.mark.asyncio
    async def test_update_ticket_invalid_id(self, client):
        """Test update_ticket with invalid ticket_id."""
        result = await client.update_ticket(ticket_id=-1, ticket_data={"subject": "test"})
        assert result["success"] is False
        assert "ticket_id" in result["error"]
    
    @pytest.mark.asyncio
    async def test_get_ticket_pipelines_invalid_pagination(self, client):
        """Test get_ticket_pipelines with invalid pagination."""
        result = await client.get_ticket_pipelines(page=0)
        assert result["success"] is False
    
    @pytest.mark.asyncio
    async def test_list_tasks_invalid_category_id(self, client):
        """Test list_tasks with invalid category_id."""
        result = await client.list_tasks(category_id=-1)
        assert result["success"] is False
        assert "category_id" in result["error"]
    
    @pytest.mark.asyncio
    async def test_list_tasks_invalid_pagination(self, client):
        """Test list_tasks with invalid pagination."""
        result = await client.list_tasks(page=0)
        assert result["success"] is False
    
    @pytest.mark.asyncio
    async def test_get_task_invalid_id(self, client):
        """Test get_task with invalid task_id."""
        result = await client.get_task(task_id=-1)
        assert result["success"] is False
        assert "task_id" in result["error"]
    
    @pytest.mark.asyncio
    async def test_update_task_invalid_id(self, client):
        """Test update_task with invalid task_id."""
        result = await client.update_task(task_id=-1, task_data={"title": "test"})
        assert result["success"] is False
        assert "task_id" in result["error"]
    
    @pytest.mark.asyncio
    async def test_list_task_categories_invalid_pagination(self, client):
        """Test list_task_categories with invalid pagination."""
        result = await client.list_task_categories(page=0)
        assert result["success"] is False
    
    @pytest.mark.asyncio
    async def test_create_task_category_with_color(self, client):
        """Test create_task_category passes color correctly."""
        with patch.object(client, '_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = {"success": True, "data": {"id": 1}}
            
            result = await client.create_task_category(name="Test", color="#FF0000")
        
        assert result["success"] is True
        mock_request.assert_called_once()
        call_kwargs = mock_request.call_args[1]
        assert call_kwargs["json"]["color"] == "#FF0000"


# =============================================================================
# CONTACTS TESTS
# =============================================================================

class TestContactsMethods:
    """Test contact-related client methods."""
    
    @pytest.mark.asyncio
    async def test_get_contact_template(self, client):
        """Test getting contact template."""
        with patch.object(client, '_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = {"success": True, "data": {"fields": []}}
            
            result = await client.get_contact_template()
        
        assert result["success"] is True
        mock_request.assert_called_once_with("GET", "/contacts/info", user_id=None)
    
    @pytest.mark.asyncio
    async def test_list_contacts(self, client):
        """Test listing contacts."""
        with patch.object(client, '_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = {"success": True, "data": []}
            
            result = await client.list_contacts(page=2, per_page=50)
        
        assert result["success"] is True
        call_kwargs = mock_request.call_args[1]
        assert call_kwargs["params"]["page"] == 2
        assert call_kwargs["params"]["per_page"] == 50
    
    @pytest.mark.asyncio
    async def test_list_contacts_invalid_pagination(self, client):
        """Test list_contacts with invalid pagination."""
        result = await client.list_contacts(page=-1)
        assert result["success"] is False
    
    @pytest.mark.asyncio
    async def test_get_contact(self, client):
        """Test getting a contact."""
        with patch.object(client, '_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = {"success": True, "data": {"id": 123}}
            
            result = await client.get_contact(contact_id=123)
        
        assert result["success"] is True
        mock_request.assert_called_once_with("GET", "/contacts/123", user_id=None)
    
    @pytest.mark.asyncio
    async def test_get_contact_invalid_id(self, client):
        """Test get_contact with invalid ID."""
        result = await client.get_contact(contact_id=-1)
        assert result["success"] is False
        assert "contact_id" in result["error"]
    
    @pytest.mark.asyncio
    async def test_create_contact(self, client):
        """Test creating a contact."""
        with patch.object(client, '_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = {"success": True, "data": {"id": 456}}
            
            result = await client.create_contact(contact_data={"first_name": "John"})
        
        assert result["success"] is True
        call_kwargs = mock_request.call_args[1]
        assert call_kwargs["json"] == {"first_name": "John"}
    
    @pytest.mark.asyncio
    async def test_update_contact(self, client):
        """Test updating a contact."""
        with patch.object(client, '_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = {"success": True, "data": {"id": 123}}
            
            result = await client.update_contact(contact_id=123, contact_data={"last_name": "Doe"})
        
        assert result["success"] is True
        mock_request.assert_called_once()
        call_args = mock_request.call_args
        assert call_args[0] == ("PUT", "/contacts/123")
    
    @pytest.mark.asyncio
    async def test_update_contact_invalid_id(self, client):
        """Test update_contact with invalid ID."""
        result = await client.update_contact(contact_id=-1, contact_data={})
        assert result["success"] is False
    
    @pytest.mark.asyncio
    async def test_delete_contact(self, client):
        """Test deleting a contact."""
        with patch.object(client, '_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = {"success": True, "data": {}}
            
            result = await client.delete_contact(contact_id=123)
        
        assert result["success"] is True
        mock_request.assert_called_once_with("DELETE", "/contacts/123", user_id=None)
    
    @pytest.mark.asyncio
    async def test_delete_contact_invalid_id(self, client):
        """Test delete_contact with invalid ID."""
        result = await client.delete_contact(contact_id=-1)
        assert result["success"] is False
    
    @pytest.mark.asyncio
    async def test_get_contact_timeline(self, client):
        """Test getting contact timeline."""
        with patch.object(client, '_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = {"success": True, "data": []}
            
            result = await client.get_contact_timeline(contact_id=123, page=1, per_page=20)
        
        assert result["success"] is True
        call_kwargs = mock_request.call_args[1]
        assert call_kwargs["params"]["page"] == 1
        assert call_kwargs["params"]["per_page"] == 20
    
    @pytest.mark.asyncio
    async def test_get_contact_timeline_invalid_id(self, client):
        """Test get_contact_timeline with invalid ID."""
        result = await client.get_contact_timeline(contact_id=-1)
        assert result["success"] is False
    
    @pytest.mark.asyncio
    async def test_get_contact_chat_history(self, client):
        """Test getting contact chat history."""
        with patch.object(client, '_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = {"success": True, "data": []}
            
            result = await client.get_contact_chat_history(contact_id=123)
        
        assert result["success"] is True
        mock_request.assert_called_once_with("GET", "/contacts/123/chat_history", user_id=None, params={"page": 1, "per_page": 25})
    
    @pytest.mark.asyncio
    async def test_get_contact_chat_history_invalid_id(self, client):
        """Test get_contact_chat_history with invalid ID."""
        result = await client.get_contact_chat_history(contact_id=-1)
        assert result["success"] is False
    
    @pytest.mark.asyncio
    async def test_update_contact_owner(self, client):
        """Test updating contact owner."""
        with patch.object(client, '_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = {"success": True, "data": {}}
            
            result = await client.update_contact_owner(contact_id=123, creator_id=456)
        
        assert result["success"] is True
        call_kwargs = mock_request.call_args[1]
        assert call_kwargs["json"] == {"creator_id": 456}
    
    @pytest.mark.asyncio
    async def test_update_contact_owner_invalid_contact_id(self, client):
        """Test update_contact_owner with invalid contact_id."""
        result = await client.update_contact_owner(contact_id=-1, creator_id=456)
        assert result["success"] is False
    
    @pytest.mark.asyncio
    async def test_update_contact_owner_invalid_owner_id(self, client):
        """Test update_contact_owner with invalid owner_id."""
        result = await client.update_contact_owner(contact_id=123, owner_id=-1)
        assert result["success"] is False


# =============================================================================
# COMPANIES TESTS
# =============================================================================

class TestCompaniesMethods:
    """Test company-related client methods."""
    
    @pytest.mark.asyncio
    async def test_get_company_template(self, client):
        """Test getting company template."""
        with patch.object(client, '_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = {"success": True, "data": {"fields": []}}
            
            result = await client.get_company_template()
        
        assert result["success"] is True
        mock_request.assert_called_once_with("GET", "/companies/info", user_id=None)
    
    @pytest.mark.asyncio
    async def test_list_companies(self, client):
        """Test listing companies."""
        with patch.object(client, '_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = {"success": True, "data": []}
            
            result = await client.list_companies(page=1, per_page=25)
        
        assert result["success"] is True
    
    @pytest.mark.asyncio
    async def test_list_companies_invalid_pagination(self, client):
        """Test list_companies with invalid pagination."""
        result = await client.list_companies(page=0)
        assert result["success"] is False
    
    @pytest.mark.asyncio
    async def test_get_company(self, client):
        """Test getting a company."""
        with patch.object(client, '_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = {"success": True, "data": {"id": 123}}
            
            result = await client.get_company(company_id=123)
        
        assert result["success"] is True
        mock_request.assert_called_once_with("GET", "/companies/123", user_id=None)
    
    @pytest.mark.asyncio
    async def test_get_company_invalid_id(self, client):
        """Test get_company with invalid ID."""
        result = await client.get_company(company_id=-1)
        assert result["success"] is False
    
    @pytest.mark.asyncio
    async def test_create_company(self, client):
        """Test creating a company."""
        with patch.object(client, '_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = {"success": True, "data": {"id": 456}}
            
            result = await client.create_company(company_data={"name": "Acme Corp"})
        
        assert result["success"] is True
        call_kwargs = mock_request.call_args[1]
        assert call_kwargs["json"] == {"name": "Acme Corp"}
    
    @pytest.mark.asyncio
    async def test_update_company(self, client):
        """Test updating a company."""
        with patch.object(client, '_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = {"success": True, "data": {"id": 123}}
            
            result = await client.update_company(company_id=123, company_data={"name": "New Name"})
        
        assert result["success"] is True
    
    @pytest.mark.asyncio
    async def test_update_company_invalid_id(self, client):
        """Test update_company with invalid ID."""
        result = await client.update_company(company_id=-1, company_data={})
        assert result["success"] is False
    
    @pytest.mark.asyncio
    async def test_delete_company(self, client):
        """Test deleting a company."""
        with patch.object(client, '_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = {"success": True, "data": {}}
            
            result = await client.delete_company(company_id=123)
        
        assert result["success"] is True
        mock_request.assert_called_once_with("DELETE", "/companies/123", user_id=None)
    
    @pytest.mark.asyncio
    async def test_delete_company_invalid_id(self, client):
        """Test delete_company with invalid ID."""
        result = await client.delete_company(company_id=-1)
        assert result["success"] is False
    
    @pytest.mark.asyncio
    async def test_get_company_timeline(self, client):
        """Test getting company timeline."""
        with patch.object(client, '_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = {"success": True, "data": []}
            
            result = await client.get_company_timeline(company_id=123, page=1, per_page=20)
        
        assert result["success"] is True
    
    @pytest.mark.asyncio
    async def test_get_company_timeline_invalid_id(self, client):
        """Test get_company_timeline with invalid ID."""
        result = await client.get_company_timeline(company_id=-1)
        assert result["success"] is False


# =============================================================================
# NOTES TESTS
# =============================================================================

class TestNotesMethods:
    """Test notes-related client methods."""
    
    @pytest.mark.asyncio
    async def test_list_notes(self, client):
        """Test listing notes."""
        with patch.object(client, '_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = {"success": True, "data": []}
            
            result = await client.list_notes(page=1, per_page=25)
        
        assert result["success"] is True
    
    @pytest.mark.asyncio
    async def test_list_notes_with_filters(self, client):
        """Test listing notes with contact/company/deal filters."""
        with patch.object(client, '_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = {"success": True, "data": []}
            
            result = await client.list_notes(
                contact_id=123,
                company_id=456,
                deal_id=789,
                page=1,
                per_page=25
            )
        
        assert result["success"] is True
        call_kwargs = mock_request.call_args[1]
        assert call_kwargs["params"]["contact_id"] == 123
        assert call_kwargs["params"]["company_id"] == 456
        assert call_kwargs["params"]["deal_id"] == 789
    
    @pytest.mark.asyncio
    async def test_list_notes_invalid_pagination(self, client):
        """Test list_notes with invalid pagination."""
        result = await client.list_notes(page=0)
        assert result["success"] is False
    
    @pytest.mark.asyncio
    async def test_list_notes_invalid_contact_id(self, client):
        """Test list_notes with invalid contact_id."""
        result = await client.list_notes(contact_id=-1)
        assert result["success"] is False
    
    @pytest.mark.asyncio
    async def test_get_note(self, client):
        """Test getting a note."""
        with patch.object(client, '_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = {"success": True, "data": {"id": 123}}
            
            result = await client.get_note(note_id=123)
        
        assert result["success"] is True
        mock_request.assert_called_once_with("GET", "/notes/123", user_id=None)
    
    @pytest.mark.asyncio
    async def test_get_note_invalid_id(self, client):
        """Test get_note with invalid ID."""
        result = await client.get_note(note_id=-1)
        assert result["success"] is False
    
    @pytest.mark.asyncio
    async def test_create_note(self, client):
        """Test creating a note."""
        with patch.object(client, '_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = {"success": True, "data": {"id": 456}}
            
            result = await client.create_note(note_data={"title": "Note", "content": "Content"})
        
        assert result["success"] is True
        call_kwargs = mock_request.call_args[1]
        assert call_kwargs["json"]["title"] == "Note"
    
    @pytest.mark.asyncio
    async def test_update_note(self, client):
        """Test updating a note."""
        with patch.object(client, '_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = {"success": True, "data": {"id": 123}}
            
            result = await client.update_note(note_id=123, note_data={"title": "Updated"})
        
        assert result["success"] is True
    
    @pytest.mark.asyncio
    async def test_update_note_invalid_id(self, client):
        """Test update_note with invalid ID."""
        result = await client.update_note(note_id=-1, note_data={})
        assert result["success"] is False
    
    @pytest.mark.asyncio
    async def test_delete_note(self, client):
        """Test deleting a note."""
        with patch.object(client, '_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = {"success": True, "data": {}}
            
            result = await client.delete_note(note_id=123)
        
        assert result["success"] is True
        mock_request.assert_called_once_with("DELETE", "/notes/123", user_id=None)
    
    @pytest.mark.asyncio
    async def test_delete_note_invalid_id(self, client):
        """Test delete_note with invalid ID."""
        result = await client.delete_note(note_id=-1)
        assert result["success"] is False


# =============================================================================
# PRODUCTS TESTS
# =============================================================================

class TestProductsMethods:
    """Test products-related client methods."""
    
    @pytest.mark.asyncio
    async def test_list_products(self, client):
        """Test listing products."""
        with patch.object(client, '_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = {"success": True, "data": []}
            
            result = await client.list_products(page=1, per_page=25)
        
        assert result["success"] is True
    
    @pytest.mark.asyncio
    async def test_list_products_invalid_pagination(self, client):
        """Test list_products with invalid pagination."""
        result = await client.list_products(page=0)
        assert result["success"] is False
    
    @pytest.mark.asyncio
    async def test_get_product(self, client):
        """Test getting a product."""
        with patch.object(client, '_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = {"success": True, "data": {"id": 123}}
            
            result = await client.get_product(product_id=123)
        
        assert result["success"] is True
        mock_request.assert_called_once_with("GET", "/products/123", user_id=None)
    
    @pytest.mark.asyncio
    async def test_get_product_invalid_id(self, client):
        """Test get_product with invalid ID."""
        result = await client.get_product(product_id=-1)
        assert result["success"] is False
    
    @pytest.mark.asyncio
    async def test_create_product(self, client):
        """Test creating a product."""
        with patch.object(client, '_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = {"success": True, "data": {"id": 456}}
            
            result = await client.create_product(product_data={"name": "Widget", "price": 99.99})
        
        assert result["success"] is True
    
    @pytest.mark.asyncio
    async def test_update_product(self, client):
        """Test updating a product."""
        with patch.object(client, '_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = {"success": True, "data": {"id": 123}}
            
            result = await client.update_product(product_id=123, product_data={"price": 109.99})
        
        assert result["success"] is True
    
    @pytest.mark.asyncio
    async def test_update_product_invalid_id(self, client):
        """Test update_product with invalid ID."""
        result = await client.update_product(product_id=-1, product_data={})
        assert result["success"] is False
    
    @pytest.mark.asyncio
    async def test_delete_product(self, client):
        """Test deleting a product."""
        with patch.object(client, '_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = {"success": True, "data": {}}
            
            result = await client.delete_product(product_id=123)
        
        assert result["success"] is True
        mock_request.assert_called_once_with("DELETE", "/products/123", user_id=None)
    
    @pytest.mark.asyncio
    async def test_delete_product_invalid_id(self, client):
        """Test delete_product with invalid ID."""
        result = await client.delete_product(product_id=-1)
        assert result["success"] is False


# =============================================================================
# PRODUCTS ASSOCIATION TESTS
# =============================================================================

class TestProductsAssociationMethods:
    """Test products association-related client methods."""
    
    @pytest.mark.asyncio
    async def test_list_products_associations(self, client):
        """Test listing product associations."""
        with patch.object(client, '_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = {"success": True, "data": []}
            
            result = await client.list_products_associations(page=1, per_page=25)
        
        assert result["success"] is True
    
    @pytest.mark.asyncio
    async def test_list_products_associations_invalid_pagination(self, client):
        """Test list_products_associations with invalid pagination."""
        result = await client.list_products_associations(page=0)
        assert result["success"] is False
    
    @pytest.mark.asyncio
    async def test_get_products_association(self, client):
        """Test getting a product association."""
        with patch.object(client, '_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = {"success": True, "data": {"id": 123}}
            
            result = await client.get_products_association(association_id=123)
        
        assert result["success"] is True
        mock_request.assert_called_once_with("GET", "/products-association/123", user_id=None)
    
    @pytest.mark.asyncio
    async def test_get_products_association_invalid_id(self, client):
        """Test get_products_association with invalid ID."""
        result = await client.get_products_association(association_id=-1)
        assert result["success"] is False
    
    @pytest.mark.asyncio
    async def test_create_products_association(self, client):
        """Test creating a product association."""
        with patch.object(client, '_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = {"success": True, "data": {"id": 456}}
            
            result = await client.create_products_association(association_data={"product_id": 1, "deal_id": 2})
        
        assert result["success"] is True
    
    @pytest.mark.asyncio
    async def test_update_products_association(self, client):
        """Test updating a product association."""
        with patch.object(client, '_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = {"success": True, "data": {"id": 123}}
            
            result = await client.update_products_association(association_id=123, association_data={"quantity": 5})
        
        assert result["success"] is True
    
    @pytest.mark.asyncio
    async def test_update_products_association_invalid_id(self, client):
        """Test update_products_association with invalid ID."""
        result = await client.update_products_association(association_id=-1, association_data={})
        assert result["success"] is False
    
    @pytest.mark.asyncio
    async def test_delete_products_association(self, client):
        """Test deleting a product association."""
        with patch.object(client, '_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = {"success": True, "data": {}}
            
            result = await client.delete_products_association(association_id=123)
        
        assert result["success"] is True
        mock_request.assert_called_once_with("DELETE", "/products-association/123", user_id=None)
    
    @pytest.mark.asyncio
    async def test_delete_products_association_invalid_id(self, client):
        """Test delete_products_association with invalid ID."""
        result = await client.delete_products_association(association_id=-1)
        assert result["success"] is False


# =============================================================================
# ADDITIONAL DEAL METHODS TESTS
# =============================================================================

class TestAdditionalDealMethods:
    """Test additional deal methods."""
    
    @pytest.mark.asyncio
    async def test_list_pipelines(self, client):
        """Test listing pipelines."""
        with patch.object(client, '_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = {"success": True, "data": []}
            
            result = await client.list_pipelines()
        
        assert result["success"] is True
        mock_request.assert_called_once_with("GET", "/pipelines", user_id=None)
    
    @pytest.mark.asyncio
    async def test_get_pipeline(self, client):
        """Test getting a pipeline."""
        with patch.object(client, '_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = {"success": True, "data": {"id": 123}}
            
            result = await client.get_pipeline(pipeline_id=123)
        
        assert result["success"] is True
        mock_request.assert_called_once_with("GET", "/pipelines/123", user_id=None)
    
    @pytest.mark.asyncio
    async def test_get_pipeline_invalid_id(self, client):
        """Test get_pipeline with invalid ID."""
        result = await client.get_pipeline(pipeline_id=-1)
        assert result["success"] is False
    
    @pytest.mark.asyncio
    async def test_list_pipeline_stages(self, client):
        """Test listing pipeline stages."""
        with patch.object(client, '_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = {"success": True, "data": []}
            
            result = await client.list_pipeline_stages(pipeline_id=123)
        
        assert result["success"] is True
        mock_request.assert_called_once_with("GET", "/pipelines/123/stages", user_id=None, params={"page": 1, "per_page": 25})
    
    @pytest.mark.asyncio
    async def test_list_pipeline_stages_invalid_id(self, client):
        """Test list_pipeline_stages with invalid ID."""
        result = await client.list_pipeline_stages(pipeline_id=-1)
        assert result["success"] is False
    
    @pytest.mark.asyncio
    async def test_list_pipeline_stages_invalid_pagination(self, client):
        """Test list_pipeline_stages with invalid pagination."""
        result = await client.list_pipeline_stages(pipeline_id=123, page=0)
        assert result["success"] is False
    
    @pytest.mark.asyncio
    async def test_get_deal_chat_history(self, client):
        """Test getting deal chat history."""
        with patch.object(client, '_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = {"success": True, "data": []}
            
            result = await client.get_deal_chat_history(deal_id=123)
        
        assert result["success"] is True
    
    @pytest.mark.asyncio
    async def test_get_deal_chat_history_invalid_id(self, client):
        """Test get_deal_chat_history with invalid ID."""
        result = await client.get_deal_chat_history(deal_id=-1)
        assert result["success"] is False
    
    @pytest.mark.asyncio
    async def test_get_deal_real_creator(self, client):
        """Test getting deal real creator."""
        with patch.object(client, '_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = {"success": True, "data": {"user_id": 456}}
            
            result = await client.get_deal_real_creator(deal_id=123)
        
        assert result["success"] is True
    
    @pytest.mark.asyncio
    async def test_get_deal_real_creator_invalid_id(self, client):
        """Test get_deal_real_creator with invalid ID."""
        result = await client.get_deal_real_creator(deal_id=-1)
        assert result["success"] is False
    
    @pytest.mark.asyncio
    async def test_get_deal_full_field(self, client):
        """Test getting deal full field."""
        with patch.object(client, '_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = {"success": True, "data": {}}
            
            result = await client.get_deal_full_field(deal_id=123)
        
        assert result["success"] is True
    
    @pytest.mark.asyncio
    async def test_get_deal_full_field_invalid_id(self, client):
        """Test get_deal_full_field with invalid ID."""
        result = await client.get_deal_full_field(deal_id=-1)
        assert result["success"] is False
    
    @pytest.mark.asyncio
    async def test_get_deal_permissions(self, client):
        """Test getting deal permissions."""
        with patch.object(client, '_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = {"success": True, "data": {}}
            
            result = await client.get_deal_permissions(deal_id=123)
        
        assert result["success"] is True
    
    @pytest.mark.asyncio
    async def test_get_deal_permissions_invalid_id(self, client):
        """Test get_deal_permissions with invalid ID."""
        result = await client.get_deal_permissions(deal_id=-1)
        assert result["success"] is False
    
    @pytest.mark.asyncio
    async def test_update_deal_owner(self, client):
        """Test updating deal owner."""
        with patch.object(client, '_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = {"success": True, "data": {}}
            
            result = await client.update_deal_owner(deal_id=123, owner_id=456)
        
        assert result["success"] is True
    
    @pytest.mark.asyncio
    async def test_update_deal_owner_invalid_deal_id(self, client):
        """Test update_deal_owner with invalid deal_id."""
        result = await client.update_deal_owner(deal_id=-1, owner_id=456)
        assert result["success"] is False
    
    @pytest.mark.asyncio
    async def test_update_deal_owner_invalid_owner_id(self, client):
        """Test update_deal_owner with invalid owner_id."""
        result = await client.update_deal_owner(deal_id=123, owner_id=-1)
        assert result["success"] is False


# =============================================================================
# DELETE METHODS TESTS
# =============================================================================

class TestDeleteMethods:
    """Test delete methods for tasks and tickets."""
    
    @pytest.mark.asyncio
    async def test_delete_task(self, client):
        """Test deleting a task."""
        with patch.object(client, '_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = {"success": True, "data": {}}
            
            result = await client.delete_task(task_id=123)
        
        assert result["success"] is True
        mock_request.assert_called_once_with("DELETE", "/tasks/123", user_id=None)
    
    @pytest.mark.asyncio
    async def test_delete_task_invalid_id(self, client):
        """Test delete_task with invalid ID."""
        result = await client.delete_task(task_id=-1)
        assert result["success"] is False
    
    @pytest.mark.asyncio
    async def test_delete_task_category(self, client):
        """Test deleting a task category."""
        with patch.object(client, '_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = {"success": True, "data": {}}
            
            result = await client.delete_task_category(category_id=123)
        
        assert result["success"] is True
        mock_request.assert_called_once_with("DELETE", "/tasks-categories/123", user_id=None)
    
    @pytest.mark.asyncio
    async def test_delete_task_category_invalid_id(self, client):
        """Test delete_task_category with invalid ID."""
        result = await client.delete_task_category(category_id=-1)
        assert result["success"] is False
    
    @pytest.mark.asyncio
    async def test_delete_ticket(self, client):
        """Test deleting a ticket."""
        with patch.object(client, '_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = {"success": True, "data": {}}
            
            result = await client.delete_ticket(ticket_id=123)
        
        assert result["success"] is True
        mock_request.assert_called_once_with("DELETE", "/tickets/123", user_id=None)
    
    @pytest.mark.asyncio
    async def test_delete_ticket_invalid_id(self, client):
        """Test delete_ticket with invalid ID."""
        result = await client.delete_ticket(ticket_id=-1)
        assert result["success"] is False