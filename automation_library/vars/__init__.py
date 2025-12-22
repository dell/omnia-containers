"""
Vars module - Configuration variables loaded from YAML files.

Usage:
    from automation_library.vars import OIM_PREREQ_VARS
    from automation_library.vars import OMNIA_SH_VARS
"""

from .oim_prereq_vars import OIM_PREREQ_VARS, USER_CONFIG_PATH
# Import omnia_sh vars after reorganization
try:
    from ..omnia_sh.vars.omnia_sh_vars import OMNIA_SH_VARS
except ImportError:
    # Fallback if circular import occurs
    OMNIA_SH_VARS = None

__all__ = ["OIM_PREREQ_VARS", "USER_CONFIG_PATH", "OMNIA_SH_VARS"]
