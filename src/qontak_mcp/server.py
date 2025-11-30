"""
Qontak CRM MCP Server - Main entry point.

Security features:
- Lazy client initialization (no temp client at import time)
- Rate limiting for API protection
- Structured security logging
- Input validation via Pydantic models
"""

import asyncio
from contextlib import asynccontextmanager
from typing import AsyncIterator, Callable

from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

from .client import QontakClient
from .logging import get_logger, configure_logger, SecurityEventType
from .rate_limit import get_rate_limiter, RateLimitConfig


# Version for logging
__version__ = "0.1.0"

# Global client instance (initialized in lifespan, not at import)
_client: QontakClient | None = None


def get_client() -> QontakClient:
    """
    Get the global client instance.
    
    This is the safe way to access the client - it will raise
    a clear error if the server hasn't been properly initialized.
    
    Returns:
        The initialized QontakClient
        
    Raises:
        RuntimeError: If called before server startup
    """
    if _client is None:
        raise RuntimeError(
            "Client not initialized. "
            "The MCP server must be started before making API calls."
        )
    return _client


@asynccontextmanager
async def lifespan(mcp: FastMCP) -> AsyncIterator[None]:
    """
    Lifespan context manager for the MCP server.
    
    Handles:
    - Environment variable loading
    - Logger configuration
    - Token store initialization (with Redis caching if configured)
    - Client initialization
    - Graceful shutdown
    """
    global _client
    
    # Load environment variables from .env file
    load_dotenv()
    
    # Configure logging
    logger = get_logger()
    logger.system_startup(__version__)
    
    # Initialize rate limiter with config from environment
    # (uses defaults if not configured)
    get_rate_limiter()
    
    # Initialize token store and seed with refresh token if using Redis
    from .auth import QontakAuth
    from .stores import get_token_store
    import os
    
    token_store = get_token_store()
    store_type = os.getenv("TOKEN_STORE", "env").lower()
    
    # If using Redis, prioritize cached tokens over environment variables
    if store_type == "redis":
        from .stores.base import TokenData
        
        # First, check if Redis already has tokens cached
        existing_token = token_store.get(user_id=None)
        
        if existing_token is not None:
            # Redis has cached tokens - use them
            logger._log(
                20,  # INFO level
                SecurityEventType.SYSTEM_STARTUP,
                f"Using cached tokens from Redis (refresh_token: ...{existing_token.refresh_token[-8:] if existing_token.refresh_token else 'None'})",
            )
        else:
            # No cached tokens - seed from environment variable
            refresh_token = os.getenv("QONTAK_REFRESH_TOKEN")
            
            if refresh_token:
                initial_token_data = TokenData(
                    refresh_token=refresh_token,
                    access_token=None,  # Will be fetched on first use
                    expires_at=None  # Will be set after first refresh
                )
                token_store.save(initial_token_data, user_id=None)
                logger._log(
                    20,  # INFO level
                    SecurityEventType.SYSTEM_STARTUP,
                    f"Initialized Redis token store with refresh token from environment",
                )
            else:
                logger._log(
                    30,  # WARNING level
                    SecurityEventType.SYSTEM_STARTUP,
                    f"No tokens in Redis and QONTAK_REFRESH_TOKEN not set - authentication will fail",
                )
    
    # Initialize client with configured token store
    auth = QontakAuth(store=token_store)
    _client = QontakClient(auth=auth)
    logger._log(
        20,  # INFO level
        SecurityEventType.SYSTEM_STARTUP,
        f"Qontak client initialized with {store_type} token store",
    )
    
    try:
        yield
    finally:
        # Cleanup
        logger.system_shutdown()
        if _client:
            await _client.close()
            _client = None


# Create the MCP server
mcp = FastMCP(
    name="Qontak CRM",
    instructions="MCP Server for managing Deals, Tickets, and Tasks in Qontak CRM",
    lifespan=lifespan,
)


# =============================================================================
# Lazy Tool Registration
# =============================================================================
# Instead of creating a temp client at import time, we use a factory pattern
# that defers client access until the tool is actually called.

def _create_lazy_tool_registrar():
    """
    Create tool registration functions that use lazy client access.
    
    This avoids creating a QontakClient at import time, which was a
    security issue (the temp client could be used before proper init).
    """
    from .tools.deals import register_deal_tools_lazy
    from .tools.tickets import register_ticket_tools_lazy
    from .tools.tasks import register_task_tools_lazy
    from .tools.contacts import register_contact_tools_lazy
    from .tools.companies import register_company_tools_lazy
    from .tools.notes import register_note_tools_lazy
    from .tools.products import register_product_tools_lazy
    from .tools.products_association import register_products_association_tools_lazy
    
    # Register tools with the get_client function
    # Tools will call get_client() when invoked, not at registration
    register_deal_tools_lazy(mcp, get_client)
    register_ticket_tools_lazy(mcp, get_client)
    register_task_tools_lazy(mcp, get_client)
    register_contact_tools_lazy(mcp, get_client)
    register_company_tools_lazy(mcp, get_client)
    register_note_tools_lazy(mcp, get_client)
    register_product_tools_lazy(mcp, get_client)
    register_products_association_tools_lazy(mcp, get_client)


# We need to handle the case where the lazy registration functions
# don't exist yet (backward compatibility). Try lazy first, fall back to old style.
try:
    _create_lazy_tool_registrar()
except ImportError:
    # Fall back to old registration style (but still defer client creation)
    # This maintains backward compatibility while we migrate
    from .tools import (
        register_deal_tools, register_ticket_tools, register_task_tools,
        register_contact_tools, register_company_tools, register_note_tools,
        register_product_tools, register_products_association_tools
    )
    
    # Create a proxy that defers to the real client
    class _LazyClientProxy:
        """Proxy that defers all calls to the real client."""
        
        def __getattr__(self, name):
            return getattr(get_client(), name)
    
    _lazy_proxy = _LazyClientProxy()
    register_deal_tools(mcp, _lazy_proxy)  # type: ignore
    register_ticket_tools(mcp, _lazy_proxy)  # type: ignore
    register_task_tools(mcp, _lazy_proxy)  # type: ignore
    register_contact_tools(mcp, _lazy_proxy)  # type: ignore
    register_company_tools(mcp, _lazy_proxy)  # type: ignore
    register_note_tools(mcp, _lazy_proxy)  # type: ignore
    register_product_tools(mcp, _lazy_proxy)  # type: ignore
    register_products_association_tools(mcp, _lazy_proxy)  # type: ignore


# Expose the ASGI app for SSE/HTTP
# This allows running with: uvicorn src.qontak_mcp.server:app
app = mcp.sse_app


def main() -> None:
    """Main entry point for the MCP server."""
    # Load environment variables
    load_dotenv()
    
    # Run the server
    mcp.run()


if __name__ == "__main__":
    main()

