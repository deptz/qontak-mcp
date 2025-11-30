"""
MCP Tools for Qontak CRM Notes.
"""

import json
from typing import Optional, Any, Callable
from mcp.server.fastmcp import FastMCP
from pydantic import ValidationError as PydanticValidationError
from ..client import QontakClient
from ..models import NoteListParams, NoteGetParams, NoteCreateParams, NoteUpdateParams
from ..errors import safe_error_response


def register_note_tools(mcp: FastMCP, client: QontakClient) -> None:
    """Register all note-related MCP tools."""
    register_note_tools_lazy(mcp, lambda: client)


def register_note_tools_lazy(mcp: FastMCP, get_client: Callable[[], QontakClient]) -> None:
    """Register all note-related MCP tools with lazy client access."""
    
    @mcp.tool()
    async def list_notes(
        page: int = 1,
        per_page: int = 25,
        crm_lead_id: Optional[int] = None,
        crm_company_id: Optional[int] = None,
        crm_deal_id: Optional[int] = None,
        user_id: Optional[str] = None,
    ) -> str:
        """List notes with optional filtering by contact, company, or deal."""
        try:
            params = NoteListParams(page=page, per_page=per_page, crm_lead_id=crm_lead_id,
                                   crm_company_id=crm_company_id, crm_deal_id=crm_deal_id, user_id=user_id)
            client = get_client()
            result = await client.list_notes(page=params.page, per_page=params.per_page,
                                            crm_lead_id=params.crm_lead_id, crm_company_id=params.crm_company_id,
                                            crm_deal_id=params.crm_deal_id, user_id=params.user_id)
            return json.dumps(result, indent=2)
        except Exception as e:
            return json.dumps(safe_error_response(e, "list_notes"), indent=2)
    
    @mcp.tool()
    async def get_note(note_id: int, user_id: Optional[str] = None) -> str:
        """Get a single note by ID."""
        try:
            params = NoteGetParams(note_id=note_id, user_id=user_id)
            client = get_client()
            result = await client.get_note(note_id=params.note_id, user_id=params.user_id)
            return json.dumps(result, indent=2)
        except Exception as e:
            return json.dumps(safe_error_response(e, "get_note"), indent=2)
    
    @mcp.tool()
    async def create_note(
        title: str,
        content: str,
        crm_lead_id: Optional[int] = None,
        crm_company_id: Optional[int] = None,
        crm_deal_id: Optional[int] = None,
        user_id: Optional[str] = None,
    ) -> str:
        """Create a new note associated with a contact, company, or deal."""
        try:
            params = NoteCreateParams(title=title, content=content, crm_lead_id=crm_lead_id,
                                     crm_company_id=crm_company_id, crm_deal_id=crm_deal_id, user_id=user_id)
            note_data: dict[str, Any] = {"title": params.title, "content": params.content}
            if params.crm_lead_id: note_data["crm_lead_id"] = params.crm_lead_id
            if params.crm_company_id: note_data["crm_company_id"] = params.crm_company_id
            if params.crm_deal_id: note_data["crm_deal_id"] = params.crm_deal_id
            
            client = get_client()
            result = await client.create_note(note_data=note_data, user_id=params.user_id)
            return json.dumps(result, indent=2)
        except Exception as e:
            return json.dumps(safe_error_response(e, "create_note"), indent=2)
    
    @mcp.tool()
    async def update_note(
        note_id: int,
        title: Optional[str] = None,
        content: Optional[str] = None,
        user_id: Optional[str] = None,
    ) -> str:
        """Update an existing note."""
        try:
            params = NoteUpdateParams(note_id=note_id, title=title, content=content, user_id=user_id)
            note_data: dict[str, Any] = {}
            if params.title: note_data["title"] = params.title
            if params.content: note_data["content"] = params.content
            
            client = get_client()
            result = await client.update_note(note_id=params.note_id, note_data=note_data, user_id=params.user_id)
            return json.dumps(result, indent=2)
        except Exception as e:
            return json.dumps(safe_error_response(e, "update_note"), indent=2)
    
    @mcp.tool()
    async def delete_note(note_id: int, user_id: Optional[str] = None) -> str:
        """Delete a note."""
        try:
            params = NoteGetParams(note_id=note_id, user_id=user_id)
            client = get_client()
            result = await client.delete_note(note_id=params.note_id, user_id=params.user_id)
            return json.dumps(result, indent=2)
        except Exception as e:
            return json.dumps(safe_error_response(e, "delete_note"), indent=2)
