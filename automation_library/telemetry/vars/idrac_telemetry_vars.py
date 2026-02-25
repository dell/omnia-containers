# Copyright 2025 Dell Inc. or its subsidiaries. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Telemetry Automation - Configuration Variables.

Loads user configuration from user_config.yml for OIM server connection.
"""

import os
from typing import Dict, Any

import yaml


# =============================================================================
# Configuration File Paths
# =============================================================================

_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__)))))
_USER_CONFIG_FILE = os.path.join(_PROJECT_ROOT, "user_config.yml")


# =============================================================================
# Configuration Loader
# =============================================================================

def _load_user_config() -> Dict[str, Any]:
    """Load user configuration from YAML file."""
    if os.path.exists(_USER_CONFIG_FILE):
        try:
            with open(_USER_CONFIG_FILE, "r", encoding="utf-8") as f:
                return yaml.safe_load(f) or {}
        except (IOError, yaml.YAMLError):
            return {}
    return {}


_user_config = _load_user_config()


# =============================================================================
# TELEMETRY VARIABLES
# =============================================================================

TELEMETRY_VARS: Dict[str, Any] = {
    # OIM Server Connection (from user_config.yml)
    "oim_server_ip": _user_config.get("oim_server_ip", ""),
    "oim_ssh_user": _user_config.get("oim_ssh_user", "root"),
    "oim_ssh_password": _user_config.get("oim_ssh_password", ""),
    "oim_ssh_port": _user_config.get("oim_ssh_port", 22),
    "omnia_shared_path": _user_config.get("omnia_shared_path", "/opt/omnia"),

    # Container
    "container_name": "omnia_core",

    # Telemetry playbook path (inside container)
    "telemetry_playbook": "/omnia/telemetry/telemetry.yml",

    # Prerequisite files (inside container)
    "provision_config_path": "/opt/omnia/input/project_default/provision_config.yml",
    "bmc_group_data_path": "/opt/omnia/telemetry/bmc_group_data.csv",
    "service_cluster_metadata_path": "/opt/omnia/.data/service_cluster_metadata.yml",

    # Telemetry namespace in K8s
    "telemetry_namespace": "telemetry",

    # Telemetry config files (inside container)
    "telemetry_config_path": "/opt/omnia/input/project_default/telemetry_config.yml",
    "software_config_path": "/opt/omnia/input/project_default/software_config.json",

    # Functional group for K8s control plane (used to get admin IP for SSH)
    "k8s_control_plane_functional_group": "service_kube_control_plane_x86_64",

    # iDRAC telemetry pod prefix
    "idrac_telemetry_pod_prefix": "idrac-telemetry",

    # Stability check wait time (seconds)
    "stability_wait_time": 30,

    # iDRAC telemetry report path
    "idrac_telemetry_report_path": "/opt/omnia/telemetry/idrac_telemetry_report.yml",

    # Omnia config credentials (ansible vault)
    "omnia_config_credentials_path": (
        "/opt/omnia/input/project_default/omnia_config_credentials.yml"
    ),
    "omnia_config_credentials_key_path": (
        "/opt/omnia/input/project_default/.omnia_config_credentials_key"
    ),
}


# =============================================================================
# Convenience Constants
# =============================================================================

# Import common constants from core (single source of truth)
from ...core.vars import (
    K8S_CONTROL_PLANE_FUNCTIONAL_GROUP,
)

PROVISION_CONFIG_PATH = TELEMETRY_VARS["provision_config_path"]
BMC_GROUP_DATA_PATH = TELEMETRY_VARS["bmc_group_data_path"]
SERVICE_CLUSTER_METADATA_PATH = TELEMETRY_VARS["service_cluster_metadata_path"]
TELEMETRY_NAMESPACE = TELEMETRY_VARS["telemetry_namespace"]
IDRAC_TELEMETRY_POD_PREFIX = TELEMETRY_VARS["idrac_telemetry_pod_prefix"]
STABILITY_WAIT_TIME = TELEMETRY_VARS["stability_wait_time"]
IDRAC_TELEMETRY_REPORT_PATH = TELEMETRY_VARS["idrac_telemetry_report_path"]
OMNIA_CONFIG_CREDENTIALS_PATH = TELEMETRY_VARS["omnia_config_credentials_path"]
OMNIA_CONFIG_CREDENTIALS_KEY_PATH = TELEMETRY_VARS["omnia_config_credentials_key_path"]


# =============================================================================
# Command Templates
# =============================================================================

CMD_TEMPLATES: Dict[str, str] = {
    # SSH options for remote commands
    "ssh_opts": "-o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null",

    # Kubectl commands
    "kubectl_get_pods": "kubectl get pods -n {namespace} -o wide",
    "kubectl_get_pods_names": "kubectl get pods -n {namespace} -o name",
    "kubectl_logs": "kubectl logs -n {namespace} {pod_name} -c {container} --tail={tail_lines}",

    # MySQL commands
    # NOTE: run_on_remote_node auto-escapes double quotes for SSH.
    # Callers pass normal commands with plain double quotes.
    "mysql_select_ips": (
        'kubectl exec -n {namespace} {pod_name} -c mysqldb -- '
        'mysql -u {mysql_user} -p{mysql_password} -N -e '
        '"SELECT ip FROM {database}.{table};"'
    ),
    "mysql_select_auth": (
        'kubectl exec -n {namespace} {pod_name} -c mysqldb -- '
        'mysql -u {mysql_user} -p{mysql_password} -N -B -e '
        '"SELECT auth FROM {database}.{table} WHERE ip=\'{ip}\';"'
    ),

    # Redfish command to get service tag
    "redfish_get_service_tag": (
        "curl -sk -u {idrac_user}:{idrac_password} "
        "https://{idrac_ip}/redfish/v1/Systems/System.Embedded.1 | "
        'python3 -c \'import sys,json; print(json.load(sys.stdin).get("SKU",""))\''
    ),

    # Ansible vault commands
    "vault_view": "ansible-vault view {vault_file} --vault-password-file {key_file}",

    # Podman exec with SSH
    "podman_ssh_cmd": (
        "podman exec {container} ssh {ssh_opts} root@{admin_ip} "
        '"{remote_cmd}" 2>/dev/null'
    ),
}

# MySQL database and table names
MYSQL_DATABASE = "idrac_telemetrydb"
MYSQL_SERVICES_TABLE = "services"

# Receiver container name
IDRAC_RECEIVER_CONTAINER = "idrac-telemetry-receiver"


# =============================================================================
# Validation Functions
# =============================================================================

def validate_telemetry_config() -> Dict[str, Any]:
    """Validate telemetry configuration."""
    errors = []

    if not TELEMETRY_VARS.get("oim_server_ip"):
        errors.append("oim_server_ip is required in user_config.yml")

    if not TELEMETRY_VARS.get("oim_ssh_password"):
        errors.append("oim_ssh_password is required in user_config.yml")

    return {
        "valid": len(errors) == 0,
        "errors": errors,
    }
