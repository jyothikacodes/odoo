from enum import Enum
from typing import List, Dict, Set

class Role(str, Enum):
    ADMIN = "admin"
    INTERNAL = "internal"
    CUSTOMER = "customer"

ROLE_PERMISSIONS: Dict[str, Set[str]] = {
    Role.ADMIN: {
        "admin.staff.manage",
        "admin.settings.manage",
        "catalog.manage",
        "discounts.manage",
        "subscriptions.manage",
        "invoices.manage",
        "payments.manage",
        "payments.reverse",
        "reports.view",
        "portal.view",
    },
    Role.INTERNAL: {
        "catalog.view",
        "subscriptions.manage",
        "invoices.manage",
        "payments.manage",
        "reports.view",
    },
    Role.CUSTOMER: {
        "portal.view",
        "portal.actions",
    }
}

def has_permission(role: str, perm: str) -> bool:
    perms = ROLE_PERMISSIONS.get(role, set())
    return perm in perms
