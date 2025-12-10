"""
Variables for prepare_oim validation.

This file loads user configuration and provides defaults for:
- SSH connection to OIM server
- omnia_core container settings
- prepare_oim playbook configuration
- OpenCHAMI container definitions
- Auth service settings
- omnia.target dependencies
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
# PREPARE OIM VARIABLES
# =============================================================================

PREPARE_OIM_VARS = {
    # -------------------------------------------------------------------------
    # Container Settings
    # -------------------------------------------------------------------------
    "omnia_core_container": _user_config.get("omnia_core_container", "omnia_core"),
    "omnia_auth_container": _user_config.get("omnia_auth_container", "omnia_auth"),
    "container_runtime": _user_config.get("container_runtime", "podman"),

    # -------------------------------------------------------------------------
    # prepare_oim Playbook Configuration
    # -------------------------------------------------------------------------
    "prepare_oim_playbook": _user_config.get("prepare_oim_playbook", "prepare_oim/prepare_oim.yml"),
    "prepare_oim_timeout": _user_config.get("prepare_oim_timeout", 1800),

    # -------------------------------------------------------------------------
    # Input Files Path (in automation repo)
    # -------------------------------------------------------------------------
    "local_input_path": _user_config.get("local_input_path", os.path.join(_PROJECT_ROOT, "project_default")),
    "container_input_path": _user_config.get("container_input_path", "/opt/omnia/input/project_default"),

    # -------------------------------------------------------------------------
    # Core Service Name
    # -------------------------------------------------------------------------
    "omnia_core_service": _user_config.get("omnia_core_service", "omnia_core.service"),

    # -------------------------------------------------------------------------
    # software_config.json Path (inside omnia_core container)
    # -------------------------------------------------------------------------
    "software_config_path": _user_config.get(
        "software_config_path",
        "/opt/omnia/input/project_default/software_config.json"
    ),

    # -------------------------------------------------------------------------
    # OpenCHAMI Container Definitions
    # -------------------------------------------------------------------------
    # Expected containers after prepare_oim execution
    "openchami_containers": _user_config.get("openchami_containers", [
        "omnia_core",
        "pulp",
        "minio-server",
        "step-ca",
        "postgres",
        "hydra",
        "opaal-idp",
        "smd",
        "opaal",
        "bss",
        "cloud-init-server",
        "haproxy",
        "coresmd",
        "registry",
    ]),

    # -------------------------------------------------------------------------
    # Auth Container Definitions (LDAP/OpenLDAP dependent)
    # -------------------------------------------------------------------------
    "auth_containers": _user_config.get("auth_containers", [
        "omnia_auth",
    ]),

    # Auth service names to check
    "auth_service_names": _user_config.get("auth_service_names", [
        "omnia_auth.service",
    ]),

    # -------------------------------------------------------------------------
    # omnia.target Dependencies
    # -------------------------------------------------------------------------
    "omnia_target_name": "omnia.target",
    "omnia_critical_dependencies": _user_config.get("omnia_critical_dependencies", [
        "omnia_core.service",
        "omnia_auth.service",
        "pulp.service",
        "registry.service",
        "minio.service",
        "openchami.target",
    ]),

    # -------------------------------------------------------------------------
    # OpenCHAMI Services (under openchami.target)
    # -------------------------------------------------------------------------
    "openchami_services": _user_config.get("openchami_services", [
        "bss.service",
        "cloud-init-server.service",
        "coresmd.service",
        "haproxy.service",
        "hydra.service",
        "opaal-idp.service",
        "opaal.service",
        "smd.service",
        "step-ca.service",
        "postgres.service",
    ]),

    # -------------------------------------------------------------------------
    # LDAP Configuration
    # -------------------------------------------------------------------------
    "ldap_software_name": "openldap",  # Name in software_config.json softwares list
    "ldap_base_dn": _user_config.get("ldap_base_dn", "dc=omnia,dc=test"),
    "ldap_admin_dn": _user_config.get("ldap_admin_dn", "cn=admin,dc=omnia,dc=test"),
    "slapd_conf_path": "/etc/openldap/slapd.conf",

    # -------------------------------------------------------------------------
    # Validation Settings
    # -------------------------------------------------------------------------
    "container_health_check_timeout": _user_config.get("container_health_check_timeout", 30),
    "service_check_timeout": _user_config.get("service_check_timeout", 10),
    "command_timeout": _user_config.get("command_timeout", 30),

    # -------------------------------------------------------------------------
    # Credentials for prepare_oim playbook (to avoid interactive prompts)
    # -------------------------------------------------------------------------
    "minio_s3_password": _user_config.get("minio_s3_password", ""),
    "pulp_password": _user_config.get("pulp_password", ""),
    "docker_username": _user_config.get("docker_username", ""),
    "docker_password": _user_config.get("docker_password", ""),
    "openldap_db_username": _user_config.get("openldap_db_username", "admin"),
    "openldap_db_password": _user_config.get("openldap_db_password", ""),
    "provision_password": _user_config.get("provision_password", ""),
    "bmc_username": _user_config.get("bmc_username", ""),
    "bmc_password": _user_config.get("bmc_password", ""),
    "slurm_db_password": _user_config.get("slurm_db_password", ""),
}
