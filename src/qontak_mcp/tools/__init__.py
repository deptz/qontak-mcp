"""
Qontak CRM MCP Tools

Provides both standard and lazy registration functions for MCP tools.
Lazy registration is preferred for security (avoids client creation at import time).
"""

from .deals import register_deal_tools, register_deal_tools_lazy
from .tickets import register_ticket_tools, register_ticket_tools_lazy
from .tasks import register_task_tools, register_task_tools_lazy
from .contacts import register_contact_tools, register_contact_tools_lazy
from .companies import register_company_tools, register_company_tools_lazy
from .notes import register_note_tools, register_note_tools_lazy
from .products import register_product_tools, register_product_tools_lazy
from .products_association import register_products_association_tools, register_products_association_tools_lazy

__all__ = [
    # Standard registration (backwards compatibility)
    "register_deal_tools",
    "register_ticket_tools",
    "register_task_tools",
    "register_contact_tools",
    "register_company_tools",
    "register_note_tools",
    "register_product_tools",
    "register_products_association_tools",
    # Lazy registration (security-preferred)
    "register_deal_tools_lazy",
    "register_ticket_tools_lazy",
    "register_task_tools_lazy",
    "register_contact_tools_lazy",
    "register_company_tools_lazy",
    "register_note_tools_lazy",
    "register_product_tools_lazy",
    "register_products_association_tools_lazy",
]
