"""
Omnia Shell Functions

Modular organization of Omnia shell deployment and management functions
organized by functionality: functions, variables, and messages.
"""

# Import specific items to avoid circular imports
# Note: Import functions first, then vars and messages to avoid circular dependency
from .functions.omnia_sh_func import (
    run_full_test,
    run_omnia_sh_install,
    run_omnia_sh_uninstall,
    verify_container_running,
    verify_ssh_connection,
    verify_directories,
    check_prerequisites,
    cleanup_omnia,
)
from .vars.omnia_sh_vars import OMNIA_SH_VARS, get_omnia_sh_path, validate_config
from .messages.omnia_sh_msgs import OMNIA_SH_MSGS, TEST_VARS, TEST_NAMES
