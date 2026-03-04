# Copyright 2026 Dell Inc. or its subsidiaries. All Rights Reserved.
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
Discovery Module - BMC Group CSV Validation Functions.

Validates bmc_group_data.csv against PXE mapping and open_network_spec.
Ensures all PXE mapping nodes with groups/parents are present in the CSV,
and that the primary OIM BMC IP (if configured) is also included.
"""

import csv
import io
from typing import Dict, Any, List

import yaml

from automation_library.core import get_nodes_info, run_in_container
from ..vars.discovery_vars import (
    BMC_GROUP_DATA_PATH,
    OPEN_NETWORK_SPEC_PATH,
)


def _read_bmc_group_csv(host) -> Dict[str, Any]:
    """Read and parse bmc_group_data.csv from container.

    Returns:
        Dict with bmc_entries list, bmc_ips set, groups set, parents set,
        and error string.
    """
    cmd = run_in_container(host, f"test -f {BMC_GROUP_DATA_PATH}")
    if cmd.rc != 0:
        return {
            "bmc_entries": [], "bmc_ips": set(),
            "groups": set(), "parents": set(),
            "error": f"File not found: {BMC_GROUP_DATA_PATH}",
        }

    cmd = run_in_container(host, f"cat {BMC_GROUP_DATA_PATH}")
    if cmd.rc != 0:
        return {
            "bmc_entries": [], "bmc_ips": set(),
            "groups": set(), "parents": set(),
            "error": f"Failed to read: {cmd.stderr}",
        }

    try:
        reader = csv.DictReader(io.StringIO(cmd.stdout))
        rows = list(reader)
    except csv.Error as exc:
        return {
            "bmc_entries": [], "bmc_ips": set(),
            "groups": set(), "parents": set(),
            "error": f"CSV parse error: {str(exc)}",
        }

    bmc_entries = []
    bmc_ips: set = set()
    groups: set = set()
    parents: set = set()
    for row in rows:
        bmc_ip = (
            row.get("BMC_IP", row.get("bmc_ip", ""))
        ).strip()
        group = (
            row.get("GROUP_NAME", row.get("group_name", ""))
        ).strip()
        parent = (
            row.get("PARENT", row.get("parent", ""))
        ).strip()
        bmc_entries.append({
            "bmc_ip": bmc_ip, "group": group, "parent": parent,
        })
        if bmc_ip:
            bmc_ips.add(bmc_ip)
        if group:
            groups.add(group)
        if parent:
            parents.add(parent)

    return {
        "bmc_entries": bmc_entries, "bmc_ips": bmc_ips,
        "groups": groups, "parents": parents, "error": "",
    }


def _read_oim_bmc_ip(host) -> str:
    """Read primary_oim_bmc_ip from open_network_spec file.

    Returns:
        The primary OIM BMC IP string, or empty string if not found.
    """
    cmd = run_in_container(host, f"cat {OPEN_NETWORK_SPEC_PATH}")
    if cmd.rc != 0:
        return ""

    try:
        spec = yaml.safe_load(cmd.stdout)
    except yaml.YAMLError:
        return ""

    if not isinstance(spec, dict):
        return ""
    return str(spec.get("primary_oim_bmc_ip", "")).strip()


def _check_pxe_nodes_in_bmc(bmc_data, pxe_nodes):
    """Check PXE mapping nodes against bmc_group_data.csv data.

    Args:
        bmc_data: Dict from _read_bmc_group_csv with groups and parents sets.
        pxe_nodes: List of node dicts from get_nodes_info.

    Returns:
        Tuple of (missing_groups list, missing_parents list).
    """
    missing_groups: List[Dict[str, str]] = []
    missing_parents: List[Dict[str, str]] = []

    for node in pxe_nodes:
        grp = node.get("group_name", "")
        parent_svc = node.get("parent_service_tag", "")
        hostname = node.get("hostname", "")

        if grp and grp not in bmc_data["groups"]:
            missing_groups.append({
                "hostname": hostname, "group_name": grp,
            })
        if parent_svc and parent_svc not in bmc_data["parents"]:
            missing_parents.append({
                "hostname": hostname,
                "parent_service_tag": parent_svc,
            })

    return missing_groups, missing_parents


def _build_bmc_errors(bmc_entries, missing_groups, missing_parents,
                      oim_bmc_ip, oim_bmc_missing):
    """Build error strings for BMC group CSV validation."""
    errors: List[str] = []
    if not bmc_entries:
        errors.append("BMC group CSV is empty")
    if missing_groups:
        grp_list = ", ".join(
            f"{m['hostname']}({m['group_name']})"
            for m in missing_groups
        )
        errors.append(f"Groups missing in CSV: {grp_list}")
    if missing_parents:
        par_list = ", ".join(
            f"{m['hostname']}({m['parent_service_tag']})"
            for m in missing_parents
        )
        errors.append(f"Parents missing in CSV: {par_list}")
    if oim_bmc_missing:
        errors.append(
            f"OIM BMC IP {oim_bmc_ip} not found in CSV"
        )
    return "; ".join(errors)


def validate_bmc_group_csv(host) -> Dict[str, Any]:
    """Validate BMC group CSV against PXE mapping and open_network_spec.

    Reads all nodes from PXE mapping file (path from provision_config.yml).
    For each node:
      - If it has a GROUP_NAME, verifies that group exists in bmc_group_data.csv.
      - If it has a PARENT_SERVICE_TAG, verifies that service tag exists as
        PARENT in bmc_group_data.csv.
    Additionally reads primary_oim_bmc_ip from open_network_spec; if present,
    verifies that IP exists in bmc_group_data.csv.

    Returns:
        Dict with success, path, bmc_count, bmc_entries, pxe_node_count,
        missing_groups, missing_parents, oim_bmc_ip, oim_bmc_missing,
        and error.
    """
    bmc_data = _read_bmc_group_csv(host)
    if bmc_data["error"]:
        return {
            "success": False, "path": BMC_GROUP_DATA_PATH,
            "bmc_count": 0, "bmc_entries": [],
            "pxe_node_count": 0, "missing_groups": [],
            "missing_parents": [], "oim_bmc_ip": "",
            "oim_bmc_missing": False,
            "error": bmc_data["error"],
        }

    pxe_nodes = get_nodes_info(host)
    missing_groups, missing_parents = _check_pxe_nodes_in_bmc(
        bmc_data, pxe_nodes
    )

    oim_bmc_ip = _read_oim_bmc_ip(host)
    oim_bmc_missing = bool(
        oim_bmc_ip and oim_bmc_ip not in bmc_data["bmc_ips"]
    )

    error = _build_bmc_errors(
        bmc_data["bmc_entries"], missing_groups,
        missing_parents, oim_bmc_ip, oim_bmc_missing,
    )

    return {
        "success": (
            len(bmc_data["bmc_entries"]) > 0
            and not missing_groups
            and not missing_parents
            and not oim_bmc_missing
        ),
        "path": BMC_GROUP_DATA_PATH,
        "bmc_count": len(bmc_data["bmc_entries"]),
        "bmc_entries": bmc_data["bmc_entries"],
        "pxe_node_count": len(pxe_nodes),
        "missing_groups": missing_groups,
        "missing_parents": missing_parents,
        "oim_bmc_ip": oim_bmc_ip,
        "oim_bmc_missing": oim_bmc_missing,
        "error": error,
    }
