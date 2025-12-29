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

"""Discovery - Configuration Variables.

Loads configuration from user_config.yml for the 5 discovery validation scenarios:
1. Openchami Container
2. Provisioning Images
3. Discovery Playbook Execution
4. Node Boot Validation
5. Package Installation

Author: Dell Technologies
"""

import csv
import os
from typing import Any, Dict, List, Tuple

import yaml


def _get_project_root() -> str:
    return os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


def _load_user_config() -> Dict[str, Any]:
    config_path = os.path.join(_get_project_root(), "user_config.yml")
    if os.path.exists(config_path):
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                return yaml.safe_load(f) or {}
        except (OSError, yaml.YAMLError):
            return {}
    return {}


_USER_CONFIG = _load_user_config()
_DISCOVERY_CFG = _USER_CONFIG.get("discovery_validation", {}) or {}


def _as_list(value: Any) -> List[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(v) for v in value]
    if isinstance(value, str):
        return [v.strip() for v in value.split(",") if v.strip()]
    return [str(value)]


def _load_pxe_mapping_file(path: str, prefer_hostname: bool = True) -> Tuple[List[str], Dict[str, List[str]]]:
    nodes: List[str] = []
    node_groups: Dict[str, List[str]] = {}
    if not path or not os.path.exists(path):
        return nodes, node_groups

    try:
        with open(path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                hostname = (row.get("HOSTNAME") or "").strip()
                admin_ip = (row.get("ADMIN_IP") or "").strip()
                group = (row.get("FUNCTIONAL_GROUP_NAME") or "").strip()
                node_id = hostname if prefer_hostname and hostname else admin_ip
                if not node_id or not group:
                    continue
                if node_id not in nodes:
                    nodes.append(node_id)
                node_groups.setdefault(group, [])
                if node_id not in node_groups[group]:
                    node_groups[group].append(node_id)
    except OSError:
        return [], {}

    return nodes, node_groups


def _default_packages_by_group(functional_groups: List[str]) -> Dict[str, List[str]]:
    defaults: Dict[str, List[str]] = {}

    for g in functional_groups:
        # Default package set is based on what is expected to be present on
        # Omnia-provisioned RHEL nodes by default.
        # Note: If you want stricter checks (e.g., Slurm/Munge), set
        # discovery_validation.packages_by_group explicitly in user_config.yml.
        defaults[g] = [
            "sssd-client",
            "sssd-common",
            "sssd-kcm",
            "sssd-krb5-common",
            "sssd-nfs-idmap",
        ]

    return defaults


_DEFAULT_OMNIA_PROJECT_DEFAULT_DIR = "/opt/omnia/input/project_default"
_DEFAULT_PXE_MAPPING_FILE = os.path.join(_DEFAULT_OMNIA_PROJECT_DEFAULT_DIR, "pxe_mapping_file.csv")

_PREFER_HOSTNAME = bool(_DISCOVERY_CFG.get("prefer_pxe_hostname", True))
_PXE_MAPPING_FILE = _DISCOVERY_CFG.get("pxe_mapping_file", "") or _DEFAULT_PXE_MAPPING_FILE

_RUN_CHECKS_IN_CONTAINER = bool(_DISCOVERY_CFG.get("run_checks_in_container", True))
_DISCOVERY_CONTAINER_NAME = _DISCOVERY_CFG.get("discovery_container_name", "")

_pxe_nodes, _pxe_node_groups = _load_pxe_mapping_file(_PXE_MAPPING_FILE, prefer_hostname=_PREFER_HOSTNAME)

_cfg_nodes = _as_list(_DISCOVERY_CFG.get("nodes", []))
_cfg_node_groups: Dict[str, Any] = _DISCOVERY_CFG.get("node_groups", {}) or {}
_cfg_packages_by_group: Dict[str, Any] = _DISCOVERY_CFG.get("packages_by_group", {}) or {}

_final_nodes = _cfg_nodes if _cfg_nodes else _pxe_nodes
_final_node_groups: Dict[str, Any] = _cfg_node_groups if _cfg_node_groups else _pxe_node_groups

_cfg_slurm_controller = (_DISCOVERY_CFG.get("slurm_controller", "") or "").strip()
_default_slurm_controller = ""
try:
    _scn = _final_node_groups.get("slurm_control_node_x86_64", []) or []
    if isinstance(_scn, list) and _scn:
        _default_slurm_controller = str(_scn[0]).strip()
except AttributeError:
    _default_slurm_controller = ""

_final_slurm_controller = _cfg_slurm_controller or _default_slurm_controller

_cfg_login_node = (_DISCOVERY_CFG.get("login_node", "") or "").strip()
_cfg_login_compiler_node = (_DISCOVERY_CFG.get("login_compiler_node", "") or "").strip()

_default_login_node = ""
_default_login_compiler_node = ""
try:
    _ln = _final_node_groups.get("login_node_x86_64", []) or []
    if isinstance(_ln, list) and _ln:
        _default_login_node = str(_ln[0]).strip()
    _lcn = _final_node_groups.get("login_compiler_node_x86_64", []) or []
    if isinstance(_lcn, list) and _lcn:
        _default_login_compiler_node = str(_lcn[0]).strip()
except AttributeError:
    _default_login_node = ""
    _default_login_compiler_node = ""

_final_login_node = _cfg_login_node or _default_login_node
_final_login_compiler_node = _cfg_login_compiler_node or _default_login_compiler_node

_final_packages_by_group: Dict[str, Any]
if _cfg_packages_by_group:
    _final_packages_by_group = _cfg_packages_by_group
else:
    _final_packages_by_group = _default_packages_by_group(list(_final_node_groups.keys()))

_cfg_node_user = _DISCOVERY_CFG.get("node_ssh_user", "root")
_cfg_node_password = _DISCOVERY_CFG.get("node_ssh_password", "")
_final_node_password = _cfg_node_password

DISCOVERY_VARS: Dict[str, Any] = {
    # General
    "omnia_shared_path": _USER_CONFIG.get("omnia_shared_path", "/opt/omnia"),
    "required_kernel_version": _USER_CONFIG.get("required_kernel_version", ""),
    "pxe_mapping_file": _PXE_MAPPING_FILE,

    # Scenario 1: Openchami Container
    "openchami_container_name": _DISCOVERY_CFG.get("openchami_container_name", "omnia_core"),

    # Execution context for node checks
    "run_checks_in_container": _RUN_CHECKS_IN_CONTAINER,
    "discovery_container_name": _DISCOVERY_CONTAINER_NAME,

    # Scenario 2: Provisioning Images (S3)
    "s3_endpoint_url": _DISCOVERY_CFG.get("s3_endpoint_url", ""),
    "s3_bucket": _DISCOVERY_CFG.get("s3_bucket", ""),
    "s3_prefix": _DISCOVERY_CFG.get("s3_prefix", ""),
    "required_provisioning_images": _as_list(_DISCOVERY_CFG.get("required_provisioning_images", [])),

    # Scenario 3: Discovery Playbook Execution
    "discovery_playbook_cmd": _DISCOVERY_CFG.get("discovery_playbook_cmd", ""),
    "discovery_success_marker": _DISCOVERY_CFG.get("discovery_success_marker", ""),

    # Scenario 4: Node Boot Validation
    "nodes": _final_nodes,
    "node_ssh_user": _cfg_node_user,
    "node_ssh_password": _final_node_password,

    # Scenario 5: Package Installation
    "node_groups": _final_node_groups,
    "packages_by_group": _final_packages_by_group,

    # Scenario 6: BMC Group CSV generation (iDRAC telemetry)
    "idrac_telemetry_support": bool(_DISCOVERY_CFG.get("idrac_telemetry_support", False)),
    "bmc_group_csv_path": _DISCOVERY_CFG.get("bmc_group_csv_path", "") or "/opt/omnia/telemetry/bmc_group_data.csv",

    # Scenario 7: Slurm Cluster validation
    "slurm_controller": _final_slurm_controller,
    "ldap_test_user": (_DISCOVERY_CFG.get("ldap_test_user", "") or "").strip(),
    "external_ldap_ip": (_DISCOVERY_CFG.get("external_ldap_ip", "") or "").strip(),
    "gpu_test_nodes": _as_list(_DISCOVERY_CFG.get("gpu_test_nodes", [])),
    "ib_test_nodes": _as_list(_DISCOVERY_CFG.get("ib_test_nodes", [])),

    # Scenario 8: Login Node validation
    "login_node": _final_login_node,
    "login_compiler_node": _final_login_compiler_node,
}

__all__ = ["DISCOVERY_VARS"]
