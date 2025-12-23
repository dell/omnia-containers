"""
Messages module - User-facing messages and constants.

Usage:
    from automation_library.messages import OIM_PREREQ_MSGS
    from automation_library.messages import OMNIA_SH_MSGS
    from automation_library.messages import DISCOVERY_MSGS
"""

from .oim_prereq_msgs import OIM_PREREQ_MSGS
from .omnia_sh_msgs import OMNIA_SH_MSGS
from .discovery_msgs import DISCOVERY_MSGS

__all__ = ["OIM_PREREQ_MSGS", "OMNIA_SH_MSGS", "DISCOVERY_MSGS"]
