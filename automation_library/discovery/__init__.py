"""Discovery module.

Exposes discovery validation subpackages:
- discovery.functions
- discovery.messages
- discovery.vars
"""

from .messages.discovery_msgs import DISCOVERY_MSGS
from .vars.discovery_vars import DISCOVERY_VARS

__all__ = [
    "DISCOVERY_MSGS",
    "DISCOVERY_VARS",
]
