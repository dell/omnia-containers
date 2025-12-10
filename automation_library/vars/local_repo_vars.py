"""
Variables for local_repo validation.

This file loads user configuration and provides defaults for:
- Pulp container settings
- Custom repo accessibility
- local_repo playbook configuration
- Package download validation
- Status file paths
"""

import os
import yaml

# Path to user config file (in project root)
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_USER_CONFIG_FILE = os.path.join(_PROJECT_ROOT, "user_config.yml")


def _load_user_config() -> dict:
    """Load user configuration from YAML file."""
    if os.path.exists(_USER_CONFIG_FILE):
        try:
            with open(_USER_CONFIG_FILE, "r") as f:
                return yaml.safe_load(f) or {}
        except Exception:
            return {}
    return {}


# Load user config
_user_config = _load_user_config()

# =============================================================================
# LOCAL REPO VARIABLES
# =============================================================================

LOCAL_REPO_VARS = {
    # -------------------------------------------------------------------------
    # SSH Connection to OIM Server
    # -------------------------------------------------------------------------
    "oim_server_ip": _user_config.get("oim_server_ip", ""),
    "oim_ssh_user": _user_config.get("oim_ssh_user", "root"),
    "oim_ssh_password": _user_config.get("oim_ssh_password", ""),
    "oim_ssh_port": _user_config.get("oim_ssh_port", 22),

    # -------------------------------------------------------------------------
    # Container Runtime Settings
    # -------------------------------------------------------------------------
    "container_runtime": _user_config.get("container_runtime", "podman"),
    "omnia_core_container": _user_config.get("omnia_core_container", "omnia_core"),

    # -------------------------------------------------------------------------
    # Pulp Container Settings
    # -------------------------------------------------------------------------
    "pulp_container_name": _user_config.get("pulp_container_name", "pulp"),
    "pulp_expected_status": "Up",
    "pulp_health_check_timeout": _user_config.get("pulp_health_check_timeout", 30),

    # -------------------------------------------------------------------------
    # local_repo Playbook Configuration
    # -------------------------------------------------------------------------
    "local_repo_playbook": _user_config.get(
        "local_repo_playbook",
        "/omnia/local_repo/local_repo.yml"
    ),
    "local_repo_inventory": _user_config.get(
        "local_repo_inventory",
        "/opt/omnia/inventory"
    ),
    "local_repo_timeout": _user_config.get("local_repo_timeout", 1800),

    # -------------------------------------------------------------------------
    # Custom Repo Accessibility Settings
    # -------------------------------------------------------------------------
    "custom_repo_base_url": _user_config.get(
        "custom_repo_base_url",
        "https://localhost:2225"
    ),
    "custom_repo_endpoints": _user_config.get("custom_repo_endpoints", [
        "/pulp/api/v3/status/",
    ]),

    # -------------------------------------------------------------------------
    # Pulp API Configuration for Validation
    # -------------------------------------------------------------------------
    "pulp_api_base_url": _user_config.get("pulp_api_base_url", "https://localhost:2225"),
    "pulp_api_username": _user_config.get("pulp_api_username", "admin"),
    "pulp_api_password": _user_config.get("pulp_api_password", "Dell1234"),
    "pulp_api_endpoints": _user_config.get("pulp_api_endpoints", [
        "/pulp/api/v3/repositories/rpm/rpm/",
        "/pulp/api/v3/remotes/rpm/rpm/",
        "/pulp/api/v3/publications/rpm/rpm/",
        "/pulp/api/v3/distributions/rpm/rpm/",
    ]),

    # -------------------------------------------------------------------------
    # Status File Paths for Package Download Validation
    # -------------------------------------------------------------------------
    "top_level_status_file": _user_config.get(
        "top_level_status_file",
        "/diya/omnia/log/local_repo/x86_64/software.csv"
    ),
    "package_status_dir": _user_config.get(
        "package_status_dir",
        "/diya/omnia/log/local_repo/x86_64"
    ),
    "status_file_pattern": _user_config.get(
        "status_file_pattern",
        "status.csv"
    ),

    # -------------------------------------------------------------------------
    # Status File Column Definitions
    # -------------------------------------------------------------------------
    "status_column_name": _user_config.get("status_column_name", "status"),
    "package_column_name": _user_config.get("package_column_name", "package"),
    "status_success_values": _user_config.get("status_success_values", [
        "success",
        "completed",
        "downloaded",
        "ok",
    ]),
    "status_failed_values": _user_config.get("status_failed_values", [
        "failed",
        "error",
        "failure",
    ]),

    # -------------------------------------------------------------------------
    # Validation Settings
    # -------------------------------------------------------------------------
    "command_timeout": _user_config.get("command_timeout", 60),
    "api_request_timeout": _user_config.get("api_request_timeout", 30),
    "max_failed_packages_to_show": _user_config.get("max_failed_packages_to_show", 20),

    # -------------------------------------------------------------------------
    # Air-gap Configuration for Image Registry Validation
    # -------------------------------------------------------------------------
    # Directory containing JSON config files with image references
    "json_config_dir": _user_config.get(
        "json_config_dir",
        "/diya/omnia/input/project_default/config/x86_64/rhel/10.0"
    ),
    # JSON files to check for image references
    "json_files_to_check": _user_config.get("json_files_to_check", [
        "service_k8s.json",
        "csi_driver_powerscale.json",
    ]),
    # External registries that should be replaced in air-gapped environment
    "external_registries": _user_config.get("external_registries", [
        "docker.io/",
        "registry.k8s.io/",
        "ghcr.io/",
        "quay.io/",
        "gcr.io/",
        "k8s.gcr.io/",
        "mcr.microsoft.com/",
    ]),
    # Local/user registry that images should point to in air-gapped mode
    "local_registry": _user_config.get("local_registry", "localhost:5000"),
    # Whether to enable air-gap validation (set to True for air-gapped environments)
    "airgap_enabled": _user_config.get("airgap_enabled", True),
}
