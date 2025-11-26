"""
Qontak CRM MCP Tools

Provides both standard and lazy registration functions for MCP tools.
Lazy registration is preferred for security (avoids client creation at import time).
"""

from .deals import register_deal_tools, register_deal_tools_lazy
from .tickets import register_ticket_tools, register_ticket_tools_lazy
from .tasks import register_task_tools, register_task_tools_lazy

__all__ = [
    # Standard registration (backwards compatibility)
    "register_deal_tools",
    "register_ticket_tools",
    "register_task_tools",
    # Lazy registration (security-preferred)
    "register_deal_tools_lazy",
    "register_ticket_tools_lazy",
    "register_task_tools_lazy",
]
