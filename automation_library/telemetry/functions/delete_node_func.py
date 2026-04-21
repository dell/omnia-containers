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
Telemetry Automation - Delete Node Verification Functions.

This module provides functions for verifying that deleted nodes
(removed from PXE mapping file) no longer have data in:
- Kafka (LDMS topic and iDRAC topic)
- MySQL (iDRAC telemetry pods)
- VictoriaMetrics (iDRAC metrics)

Uses a local backup of the PXE mapping file (.backup/.pxe_mapping.csv)
to detect which nodes were removed between test runs.
"""

import json
import os
import time
import urllib.parse
from typing import Dict, Any, List, Set

import pytest

from ...core import PROVISION_CONFIG_FILE, get_input_value
from ...core.host import run_in_container, run_on_remote_node
from ..messages.delete_node_msgs import DELETE_NODE_LOG_MSGS
from ..vars.shared_vars import TELEMETRY_NAMESPACE
from ..vars.kafka_vars import (
    KAFKA_BRIDGE_PORT,
    LDMS_FUNCTIONAL_GROUPS,
)
from ..vars.victoria_vars import (
    DEPLOYMENT_MODE_SINGLE,
    VICTORIA_SINGLE_NODE,
    VICTORIA_CLUSTER,
    VICTORIA_TLS_SECRET,
    VICTORIA_API_ENDPOINTS,
    VICTORIA_CMD_TEMPLATES,
)
from ..vars.idrac_telemetry_vars import (
    IDRAC_TELEMETRY_POD_PREFIX,
    MYSQL_DATABASE,
    MYSQL_SERVICES_TABLE,
    CMD_TEMPLATES,
)

# =============================================================================
# MODULE-LEVEL CACHING (same pattern as _admin_ip_cache in shared_func.py)
# =============================================================================

_deleted_nodes_cache: Dict[str, Any] = {}


def clear_deleted_nodes_cache():
    """Clear the deleted nodes cache. Useful for testing or re-evaluation."""
    _deleted_nodes_cache.clear()


def get_deleted_nodes_cached(host) -> Dict[str, Any]:
    """
    Get deleted nodes info with module-level caching.

    Computes the result once per process and caches it so multiple
    test functions can call this without redundant container reads.

    Args:
        host: Testinfra host object

    Returns:
        Dict with has_backup, files_identical, deleted_entries, etc.
    """
    if "result" in _deleted_nodes_cache:
        return _deleted_nodes_cache["result"]

    result = get_deleted_nodes(host)
    _deleted_nodes_cache["result"] = result
    return result


def update_pxe_backup(host):
    """
    Update the PXE mapping backup with the current content.

    Call this after all delete-node tests have completed so the
    backup reflects the current state for the next test run.

    Args:
        host: Testinfra host object
    """
    info = get_deleted_nodes_cached(host)
    current_content = info.get("current_content", "")
    if current_content:
        save_pxe_backup(current_content)


# =============================================================================
# PXE MAPPING BACKUP MANAGEMENT
# =============================================================================

def _get_backup_dir() -> str:
    """Get the .backup/ directory path in the project root."""
    from automation_library.core import get_project_root
    return os.path.join(get_project_root(), ".backup")


def _get_backup_path() -> str:
    """Get the path to the PXE mapping backup file."""
    return os.path.join(_get_backup_dir(), ".pxe_mapping.csv")


def read_pxe_from_container(host) -> str:
    """
    Read the raw PXE mapping CSV content from the omnia_core container.

    Uses get_input_value() from core to resolve the PXE mapping file path
    from provision_config.yml, then reads the file content.

    Args:
        host: Testinfra host object

    Returns:
        Raw CSV content string, or empty string if read fails
    """
    pxe_path = get_input_value(host, PROVISION_CONFIG_FILE, "pxe_mapping_file_path")
    if not pxe_path:
        return ""

    result = run_in_container(host, f"cat {pxe_path}")
    if result.rc != 0:
        return ""

    return result.stdout.strip()


def read_pxe_backup() -> str:
    """
    Read the PXE mapping backup file from .backup/.pxe_mapping.csv.

    Returns:
        Raw CSV content string, or empty string if backup doesn't exist
    """
    backup_path = _get_backup_path()
    if not os.path.exists(backup_path):
        return ""

    with open(backup_path, "r", encoding="utf-8") as f:
        return f.read().strip()


def save_pxe_backup(content: str):
    """
    Save PXE mapping content to .backup/.pxe_mapping.csv.

    Creates the .backup/ directory if it doesn't exist.

    Args:
        content: Raw CSV content to save
    """
    backup_dir = _get_backup_dir()
    os.makedirs(backup_dir, exist_ok=True)

    backup_path = _get_backup_path()
    with open(backup_path, "w", encoding="utf-8") as f:
        f.write(content)


def parse_pxe_csv(content: str) -> List[Dict[str, str]]:
    """
    Parse raw PXE mapping CSV content into a list of node dicts.

    Uses the same column mapping as core/host.py _read_pxe_mapping().

    Args:
        content: Raw CSV content

    Returns:
        List of dicts with keys: functional_group, group_name, service_tag,
        parent_service_tag, hostname, admin_mac, admin_ip, bmc_mac, bmc_ip
    """
    column_map = {
        "FUNCTIONAL_GROUP_NAME": "functional_group",
        "GROUP_NAME": "group_name",
        "SERVICE_TAG": "service_tag",
        "PARENT_SERVICE_TAG": "parent_service_tag",
        "HOSTNAME": "hostname",
        "ADMIN_MAC": "admin_mac",
        "ADMIN_IP": "admin_ip",
        "BMC_MAC": "bmc_mac",
        "BMC_IP": "bmc_ip",
    }

    lines = content.strip().split('\n')
    if not lines:
        return []

    # Parse header
    header = [col.strip().upper() for col in lines[0].split(',')]
    column_indices = {}
    for i, col_name in enumerate(header):
        if col_name in column_map:
            column_indices[column_map[col_name]] = i

    # Parse data rows
    nodes = []
    for line in lines[1:]:
        if not line.strip():
            continue
        parts = line.split(',')
        node = {}
        for field_name, idx in column_indices.items():
            node[field_name] = parts[idx].strip() if len(parts) > idx else ""
        nodes.append(node)

    return nodes


def get_deleted_nodes(host) -> Dict[str, Any]:
    """
    Compare current PXE mapping with backup to find deleted nodes.

    Args:
        host: Testinfra host object

    Returns:
        Dict with:
            has_backup: True if backup file exists
            files_identical: True if current == backup (no changes)
            deleted_entries: List of node dicts removed from PXE mapping
            current_content: Raw current PXE mapping CSV
            current_nodes: Parsed current nodes
            backup_nodes: Parsed backup nodes
    """
    current_content = read_pxe_from_container(host)
    if not current_content:
        return {
            "has_backup": False,
            "files_identical": True,
            "deleted_entries": [],
            "current_content": "",
            "current_nodes": [],
            "backup_nodes": [],
            "error": "Failed to read current PXE mapping from container",
        }

    backup_content = read_pxe_backup()

    if not backup_content:
        # No backup exists - create baseline
        save_pxe_backup(current_content)
        return {
            "has_backup": False,
            "files_identical": True,
            "deleted_entries": [],
            "current_content": current_content,
            "current_nodes": parse_pxe_csv(current_content),
            "backup_nodes": [],
        }

    # Normalize and compare
    current_normalized = current_content.strip()
    backup_normalized = backup_content.strip()

    if current_normalized == backup_normalized:
        return {
            "has_backup": True,
            "files_identical": True,
            "deleted_entries": [],
            "current_content": current_content,
            "current_nodes": parse_pxe_csv(current_content),
            "backup_nodes": parse_pxe_csv(backup_content),
        }

    # Files differ - find deleted entries
    current_nodes = parse_pxe_csv(current_content)
    backup_nodes = parse_pxe_csv(backup_content)

    # Build a set of unique keys from current nodes (service_tag is unique)
    current_tags = {n.get("service_tag", "") for n in current_nodes if n.get("service_tag")}

    # Find entries in backup that are NOT in current
    deleted_entries = [
        n for n in backup_nodes
        if n.get("service_tag") and n["service_tag"] not in current_tags
    ]

    return {
        "has_backup": True,
        "files_identical": False,
        "deleted_entries": deleted_entries,
        "current_content": current_content,
        "current_nodes": current_nodes,
        "backup_nodes": backup_nodes,
    }


def get_deleted_ldms_hostnames(deleted_entries: List[Dict[str, str]]) -> List[str]:
    """
    Extract hostnames of deleted LDMS nodes from deleted PXE entries.

    Filters for LDMS functional groups only.

    Args:
        deleted_entries: List of deleted node dicts from get_deleted_nodes()

    Returns:
        List of deleted LDMS hostnames
    """
    hostnames = []
    for entry in deleted_entries:
        func_group = entry.get("functional_group", "")
        hostname = entry.get("hostname", "")
        if hostname and func_group in LDMS_FUNCTIONAL_GROUPS:
            hostnames.append(hostname)
    return hostnames


def get_deleted_service_tags(deleted_entries: List[Dict[str, str]]) -> List[str]:
    """
    Extract service tags from deleted PXE entries.

    Args:
        deleted_entries: List of deleted node dicts from get_deleted_nodes()

    Returns:
        List of deleted service tags
    """
    return [
        entry["service_tag"] for entry in deleted_entries
        if entry.get("service_tag")
    ]


def get_deleted_bmc_ips(deleted_entries: List[Dict[str, str]]) -> List[str]:
    """
    Extract BMC IPs from deleted PXE entries.

    Args:
        deleted_entries: List of deleted node dicts from get_deleted_nodes()

    Returns:
        List of deleted BMC IPs
    """
    return [
        entry["bmc_ip"] for entry in deleted_entries
        if entry.get("bmc_ip")
    ]


def skip_if_no_deleted_nodes(deleted_nodes_info, log):
    """
    Skip test if no nodes were deleted from PXE mapping.

    Checks for backup existence and file changes, skipping with
    appropriate log messages if no deleted nodes are detected.

    Args:
        deleted_nodes_info: Result dict from get_deleted_nodes()
        log: TestLogger instance
    """
    if not deleted_nodes_info.get("has_backup"):
        msg = DELETE_NODE_LOG_MSGS["backup_not_found"]
        log.skipped(msg, DELETE_NODE_LOG_MSGS["backup_created"])
        pytest.skip(msg)

    if deleted_nodes_info.get("files_identical"):
        msg = DELETE_NODE_LOG_MSGS["files_identical"]
        log.skipped(msg, DELETE_NODE_LOG_MSGS["no_deleted_nodes"])
        pytest.skip(msg)


# =============================================================================
# LDMS DELETE NODE VERIFICATION (KAFKA)
# =============================================================================

def verify_ldms_deleted_node_in_kafka(
    host,
    admin_ip: str,
    deleted_hostnames: List[str],
    timeout_seconds: int = 30
) -> Dict[str, Any]:
    """
    Verify that deleted LDMS node hostnames do NOT appear in the latest
    Kafka ldms topic data.

    Args:
        host: Testinfra host object
        admin_ip: Admin IP of K8s node
        deleted_hostnames: List of hostnames that should NOT have data
        timeout_seconds: Timeout for consuming records

    Returns:
        Dict with success, deleted_in_latest, deleted_not_in_latest
    """
    from .kafka_func import get_kafka_bridge_ip, get_domain_name

    bridge_ip = get_kafka_bridge_ip(host, admin_ip)
    if not bridge_ip:
        return {"success": False, "error": "Kafka bridge IP not found"}

    domain_name = get_domain_name(host)

    consumer_group = f"ldms-del-{int(time.time()) % 10000}"
    consumer_name = "ldms-del-consumer"

    latest_hostnames: Set[str] = set()
    latest_records: Dict[str, dict] = {}

    try:
        # Create consumer with 'latest' offset
        create_cmd = (
            f'curl -s -X POST http://{bridge_ip}:{KAFKA_BRIDGE_PORT}'
            f'/consumers/{consumer_group} '
            f'-H "content-type: application/vnd.kafka.v2+json" '
            f'-d \'{{"name": "{consumer_name}", "format": "json", '
            f'"auto.offset.reset": "latest", "enable.auto.commit": true}}\''
        )
        cmd = run_on_remote_node(host, create_cmd, admin_ip)
        if "error_code" in cmd.stdout:
            return {
                "success": False,
                "error": f"Failed to create Kafka consumer: {cmd.stdout}",
            }

        # Subscribe to ldms topic
        subscribe_cmd = (
            f'curl -s -X POST http://{bridge_ip}:{KAFKA_BRIDGE_PORT}'
            f'/consumers/{consumer_group}'
            f'/instances/{consumer_name}/subscription '
            f'-H "content-type: application/vnd.kafka.v2+json" '
            f'-d \'{{"topics": ["ldms"]}}\''
        )
        run_on_remote_node(host, subscribe_cmd, admin_ip)

        # Consume records
        consume_cmd = (
            f'curl -s -X GET http://{bridge_ip}:{KAFKA_BRIDGE_PORT}'
            f'/consumers/{consumer_group}'
            f'/instances/{consumer_name}/records '
            f'-H "accept: application/vnd.kafka.json.v2+json"'
        )

        start_time = time.time()
        while time.time() - start_time < timeout_seconds:
            cmd = run_on_remote_node(host, consume_cmd, admin_ip)

            if cmd.stdout.strip() and cmd.stdout.strip().startswith("["):
                try:
                    records = json.loads(cmd.stdout)
                    for record in records:
                        value = record.get("value", {})
                        instance = value.get("instance", "")
                        if instance and "/" in instance:
                            host_part = instance.split("/")[0]
                            if "." in host_part:
                                hostname = host_part.split(".")[0]
                                latest_hostnames.add(hostname)
                                if hostname not in latest_records:
                                    latest_records[hostname] = record
                except json.JSONDecodeError:
                    pass

            time.sleep(2)

    finally:
        # Cleanup consumer
        delete_cmd = (
            f'curl -s -X DELETE http://{bridge_ip}:{KAFKA_BRIDGE_PORT}'
            f'/consumers/{consumer_group}'
            f'/instances/{consumer_name}'
        )
        run_on_remote_node(host, delete_cmd, admin_ip)

    # Check which deleted hostnames still appear in latest data
    deleted_set = set(deleted_hostnames)
    deleted_in_latest = list(deleted_set & latest_hostnames)
    deleted_not_in_latest = list(deleted_set - latest_hostnames)

    # Build per-hostname results
    hostname_results = []
    for hostname in deleted_hostnames:
        found = hostname in latest_hostnames
        record = latest_records.get(hostname, {})
        hostname_results.append({
            "hostname": hostname,
            "found_in_latest": found,
            "record": record,
        })

    return {
        "success": len(deleted_in_latest) == 0,
        "bridge_ip": bridge_ip,
        "domain_name": domain_name,
        "deleted_hostnames": deleted_hostnames,
        "deleted_in_latest": deleted_in_latest,
        "deleted_not_in_latest": deleted_not_in_latest,
        "hostname_results": hostname_results,
        "error": (
            f"Deleted LDMS hostnames still in latest Kafka: {deleted_in_latest}"
            if deleted_in_latest else ""
        ),
    }


# =============================================================================
# iDRAC DELETE NODE VERIFICATION (KAFKA)
# =============================================================================

def verify_idrac_deleted_node_in_kafka(
    host,
    admin_ip: str,
    deleted_service_tags: List[str],
    timeout_seconds: int = 30
) -> Dict[str, Any]:
    """
    Verify that deleted iDRAC service tags do NOT appear in the latest
    Kafka idrac topic data.

    Args:
        host: Testinfra host object
        admin_ip: Admin IP of K8s node
        deleted_service_tags: List of service tags that should NOT have data
        timeout_seconds: Timeout for consuming records

    Returns:
        Dict with success, deleted_in_latest, deleted_not_in_latest
    """
    from .kafka_func import get_kafka_bridge_ip

    bridge_ip = get_kafka_bridge_ip(host, admin_ip)
    if not bridge_ip:
        return {"success": False, "error": "Kafka bridge IP not found"}

    consumer_group = f"idrac-del-{int(time.time()) % 10000}"
    consumer_name = "idrac-del-consumer"

    latest_service_tags: Set[str] = set()
    latest_records: Dict[str, dict] = {}

    try:
        # Create consumer with 'latest' offset
        create_cmd = (
            f'curl -s -X POST http://{bridge_ip}:{KAFKA_BRIDGE_PORT}'
            f'/consumers/{consumer_group} '
            f'-H "content-type: application/vnd.kafka.v2+json" '
            f'-d \'{{"name": "{consumer_name}", "format": "json", '
            f'"auto.offset.reset": "latest", "enable.auto.commit": true}}\''
        )
        cmd = run_on_remote_node(host, create_cmd, admin_ip)
        if "error_code" in cmd.stdout:
            return {
                "success": False,
                "error": f"Failed to create Kafka consumer: {cmd.stdout}",
            }

        # Subscribe to idrac topic
        subscribe_cmd = (
            f'curl -s -X POST http://{bridge_ip}:{KAFKA_BRIDGE_PORT}'
            f'/consumers/{consumer_group}'
            f'/instances/{consumer_name}/subscription '
            f'-H "content-type: application/vnd.kafka.v2+json" '
            f'-d \'{{"topics": ["idrac"]}}\''
        )
        run_on_remote_node(host, subscribe_cmd, admin_ip)

        # Consume records
        consume_cmd = (
            f'curl -s -X GET http://{bridge_ip}:{KAFKA_BRIDGE_PORT}'
            f'/consumers/{consumer_group}'
            f'/instances/{consumer_name}/records '
            f'-H "accept: application/vnd.kafka.json.v2+json"'
        )

        start_time = time.time()
        while time.time() - start_time < timeout_seconds:
            cmd = run_on_remote_node(host, consume_cmd, admin_ip)

            if cmd.stdout.strip() and cmd.stdout.strip().startswith("["):
                try:
                    records = json.loads(cmd.stdout)
                    for record in records:
                        value = record.get("value", {})
                        if isinstance(value, list):
                            for item in value:
                                if isinstance(item, dict):
                                    service_tag = item.get("host", "")
                                    if service_tag:
                                        latest_service_tags.add(service_tag)
                                        if service_tag not in latest_records:
                                            latest_records[service_tag] = record
                except json.JSONDecodeError:
                    pass

            time.sleep(2)

    finally:
        # Cleanup consumer
        delete_cmd = (
            f'curl -s -X DELETE http://{bridge_ip}:{KAFKA_BRIDGE_PORT}'
            f'/consumers/{consumer_group}'
            f'/instances/{consumer_name}'
        )
        run_on_remote_node(host, delete_cmd, admin_ip)

    # Check which deleted service tags still appear in latest data
    deleted_set = set(deleted_service_tags)
    deleted_in_latest = list(deleted_set & latest_service_tags)
    deleted_not_in_latest = list(deleted_set - latest_service_tags)

    # Build per-tag results
    tag_results = []
    for tag in deleted_service_tags:
        found = tag in latest_service_tags
        record = latest_records.get(tag, {})
        tag_results.append({
            "service_tag": tag,
            "found_in_latest": found,
            "record": record,
        })

    return {
        "success": len(deleted_in_latest) == 0,
        "bridge_ip": bridge_ip,
        "deleted_service_tags": deleted_service_tags,
        "deleted_in_latest": deleted_in_latest,
        "deleted_not_in_latest": deleted_not_in_latest,
        "tag_results": tag_results,
        "error": (
            f"Deleted iDRAC service tags still in latest Kafka: {deleted_in_latest}"
            if deleted_in_latest else ""
        ),
    }


# =============================================================================
# iDRAC DELETE NODE VERIFICATION (MYSQL)
# =============================================================================

def verify_idrac_deleted_node_in_mysql(
    host,
    admin_ip: str,
    deleted_bmc_ips: List[str],
) -> Dict[str, Any]:
    """
    Verify that deleted node BMC IPs do NOT appear in MySQL services table
    across all idrac-telemetry pods.

    Args:
        host: Testinfra host object
        admin_ip: Admin IP of K8s node
        deleted_bmc_ips: List of BMC IPs that should NOT be in MySQL

    Returns:
        Dict with success, found_in_mysql, not_found_in_mysql, pod_results
    """
    from .idrac_telemetry_func import get_mysql_credentials

    # Get MySQL credentials
    creds = get_mysql_credentials(host)
    if creds.get("error"):
        return {
            "success": False,
            "error": f"Failed to get MySQL credentials: {creds['error']}",
        }

    mysql_user = creds["mysqldb_user"]
    mysql_password = creds["mysqldb_password"]

    # Get list of idrac-telemetry pods
    cmd = run_on_remote_node(
        host,
        f"kubectl get pods -n {TELEMETRY_NAMESPACE} -o name | "
        f"grep {IDRAC_TELEMETRY_POD_PREFIX}",
        admin_ip
    )
    if cmd.rc != 0:
        return {
            "success": False,
            "error": "Failed to get idrac-telemetry pods",
        }

    pods = [p.replace("pod/", "").strip() for p in cmd.stdout.strip().split('\n') if p.strip()]

    # Check each pod's MySQL for deleted BMC IPs
    found_in_mysql = set()
    pod_results = []

    for pod_name in pods:
        mysql_cmd = CMD_TEMPLATES["mysql_select_ips"].format(
            namespace=TELEMETRY_NAMESPACE,
            pod_name=pod_name,
            mysql_user=mysql_user,
            mysql_password=mysql_password,
            database=MYSQL_DATABASE,
            table=MYSQL_SERVICES_TABLE,
        )
        cmd = run_on_remote_node(host, mysql_cmd, admin_ip)

        actual_ips = []
        if cmd.rc == 0:
            for line in cmd.stdout.strip().split('\n'):
                ip = line.strip()
                if ip and not ip.startswith('mysql:'):
                    actual_ips.append(ip)

        # Check if any deleted BMC IPs are in this pod
        pod_found = [ip for ip in deleted_bmc_ips if ip in actual_ips]
        pod_not_found = [ip for ip in deleted_bmc_ips if ip not in actual_ips]
        found_in_mysql.update(pod_found)

        pod_results.append({
            "pod_name": pod_name,
            "found_deleted_ips": pod_found,
            "not_found_deleted_ips": pod_not_found,
        })

    found_in_mysql = list(found_in_mysql)
    not_found_in_mysql = [ip for ip in deleted_bmc_ips if ip not in found_in_mysql]

    return {
        "success": len(found_in_mysql) == 0,
        "deleted_bmc_ips": deleted_bmc_ips,
        "found_in_mysql": found_in_mysql,
        "not_found_in_mysql": not_found_in_mysql,
        "pod_results": pod_results,
        "error": (
            f"Deleted BMC IPs still in MySQL: {found_in_mysql}"
            if found_in_mysql else ""
        ),
    }


# =============================================================================
# iDRAC DELETE NODE VERIFICATION (VICTORIAMETRICS)
# =============================================================================

def verify_idrac_deleted_node_in_victoria(
    host,
    admin_ip: str,
    deleted_service_tags: List[str],
    timeout_seconds: int = 30
) -> Dict[str, Any]:
    """
    Verify that deleted iDRAC service tags do NOT have recent metrics
    in VictoriaMetrics.

    Args:
        host: Testinfra host object
        admin_ip: Admin IP of K8s node
        deleted_service_tags: List of service tags that should NOT have data
        timeout_seconds: Timeout for API queries

    Returns:
        Dict with success, found_in_victoria, not_found_in_victoria, tag_results
    """
    from .victoria_func import get_deployment_mode

    deployment_mode = get_deployment_mode(host)

    # Get service info based on deployment mode
    if deployment_mode == DEPLOYMENT_MODE_SINGLE:
        service_name = VICTORIA_SINGLE_NODE["service_name"]
        port = VICTORIA_SINGLE_NODE["port"]
        query_endpoint = VICTORIA_API_ENDPOINTS["single_query"]
    else:
        service_name = VICTORIA_CLUSTER["vmselect"]["service_name"]
        port = VICTORIA_CLUSTER["vmselect"]["port"]
        query_endpoint = VICTORIA_API_ENDPOINTS["cluster_query"]

    # Get external IP
    kubectl_cmd = VICTORIA_CMD_TEMPLATES["get_service_external_ip"].format(
        service_name=service_name,
        namespace=TELEMETRY_NAMESPACE
    )
    cmd = run_on_remote_node(host, kubectl_cmd, admin_ip)
    external_ip = cmd.stdout.strip() if cmd.rc == 0 else ""

    if not external_ip or external_ip == "null":
        return {
            "success": False,
            "error": f"Service '{service_name}' has no external IP",
        }

    # Query for each deleted service tag
    found_in_victoria = []
    not_found_in_victoria = []
    tag_results = []

    for service_tag in deleted_service_tags:
        query = urllib.parse.quote(
            f'{{__name__=~"PowerEdge_.*",ServiceTag="{service_tag}"}}'
        )

        service_dns = f"{service_name}.{TELEMETRY_NAMESPACE}"
        curl_cmd = (
            f"kubectl get secret {VICTORIA_TLS_SECRET} -n {TELEMETRY_NAMESPACE} "
            f"-o jsonpath='{{.data.ca\\.crt}}' | base64 -d > /tmp/ca.crt && "
            f"curl -s --max-time {timeout_seconds} --cacert /tmp/ca.crt "
            f"--resolve {service_dns}:{port}:{external_ip} "
            f"'https://{service_dns}:{port}{query_endpoint}?query={query}'; echo"
        )
        cmd = run_on_remote_node(host, curl_cmd, admin_ip)

        try:
            response = json.loads(cmd.stdout) if cmd.rc == 0 else {}
            result_data = response.get("data", {}).get("result", [])
        except json.JSONDecodeError:
            result_data = []

        has_data = len(result_data) > 0

        tag_results.append({
            "service_tag": service_tag,
            "found_in_victoria": has_data,
            "metric_count": len(result_data),
        })

        if has_data:
            found_in_victoria.append(service_tag)
        else:
            not_found_in_victoria.append(service_tag)

    return {
        "success": len(found_in_victoria) == 0,
        "deployment_mode": deployment_mode,
        "external_ip": external_ip,
        "deleted_service_tags": deleted_service_tags,
        "found_in_victoria": found_in_victoria,
        "not_found_in_victoria": not_found_in_victoria,
        "tag_results": tag_results,
        "error": (
            f"Deleted service tags still in VictoriaMetrics: {found_in_victoria}"
            if found_in_victoria else ""
        ),
    }
