"""
Functions module - Core automation functions.

Usage:
    from automation_library.functions import run_all_prereq_checks
    from automation_library.functions import run_omnia_sh_install
"""

# OIM Prereq Functions
from .oim_prereq_func import run_all_prereq_checks

# Omnia.sh Functions
from .omnia_sh_func import (
    run_full_test as run_omnia_sh_test,
    run_omnia_sh_install,
    run_omnia_sh_uninstall,
    verify_container_running,
    verify_ssh_connection,
    verify_directories,
    check_prerequisites as check_omnia_sh_prerequisites,
    cleanup_omnia,
)

# Discovery Validation Functions
from .discovery_func import run_all_discovery_validations, run_discovery

__all__ = [
    # Prereq
    "run_all_prereq_checks",
    # Omnia.sh
    "run_omnia_sh_test",
    "run_omnia_sh_install",
    "run_omnia_sh_uninstall",
    "verify_container_running",
    "verify_ssh_connection",
    "verify_directories",
    "check_omnia_sh_prerequisites",
    "cleanup_omnia",
    # Discovery
    "run_discovery",
    "run_all_discovery_validations",
]
