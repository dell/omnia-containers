"""
Vars module - Configuration variables loaded from YAML files.

Usage:
    from automation_library.vars import OIM_PREREQ_VARS
    from automation_library.vars import OMNIA_SH_VARS
    from automation_library.vars import DISCOVERY_VARS
"""

from .oim_prereq_vars import OIM_PREREQ_VARS, USER_CONFIG_PATH
from .omnia_sh_vars import OMNIA_SH_VARS
from .discovery_vars import DISCOVERY_VARS

__all__ = ["OIM_PREREQ_VARS", "USER_CONFIG_PATH", "OMNIA_SH_VARS", "DISCOVERY_VARS"]
