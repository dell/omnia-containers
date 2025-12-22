"""
Prerequisite Check Functions

Modular organization of OIM prerequisite validation functions
organized by functionality: system, hardware, network, services, repository, and validation.
"""

# Import all functions to maintain compatibility
from .main import run_all_prereq_checks
from .system import configure_hostname
from .hardware import check_ipmi_tool, install_ipmi_tool, get_hardware_inventory, validate_hardware
from .network import validate_network_interfaces, configure_pxe_nic, check_internet
from .services import check_nfs_reachable
from .repository import ensure_git_installed, clone_omnia_repo, build_container_images, download_omnia_sh
from .validation import validate_os, check_podman

__all__ = [
    "run_all_prereq_checks",
    "configure_hostname", 
    "check_ipmi_tool",
    "install_ipmi_tool",
    "get_hardware_inventory",
    "validate_hardware",
    "validate_network_interfaces",
    "configure_pxe_nic", 
    "check_internet",
    "check_nfs_reachable",
    "ensure_git_installed",
    "clone_omnia_repo",
    "build_container_images",
    "download_omnia_sh",
    "validate_os",
    "check_podman"
]
