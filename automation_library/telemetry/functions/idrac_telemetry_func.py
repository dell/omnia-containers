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
Telemetry Automation - Core Functions.

This module provides functions for verifying telemetry pods in K8s cluster.
"""

import re
import yaml
from typing import Dict, Any, List

from ..vars.idrac_telemetry_vars import (
    TELEMETRY_VARS,
    PROVISION_CONFIG_PATH,
    TELEMETRY_NAMESPACE,
    IDRAC_TELEMETRY_POD_PREFIX,
    BMC_GROUP_DATA_PATH,
    SERVICE_CLUSTER_METADATA_PATH,
    IDRAC_TELEMETRY_REPORT_PATH,
    OMNIA_CONFIG_CREDENTIALS_PATH,
    OMNIA_CONFIG_CREDENTIALS_KEY_PATH,
    CMD_TEMPLATES,
    MYSQL_DATABASE,
    MYSQL_SERVICES_TABLE,
    IDRAC_RECEIVER_CONTAINER,
)


# =============================================================================
# TELEMETRY POD VERIFICATION FUNCTIONS
# =============================================================================

def get_service_kube_node_count(host) -> int:
    """
    Get count of service_kube_node entries from PXE mapping file.

    Args:
        host: Testinfra host object

    Returns:
        Count of service_kube_node entries
    """
    container = TELEMETRY_VARS["container_name"]
    provision_config_path = PROVISION_CONFIG_PATH

    # Read provision_config.yml to get pxe_mapping_file_path
    cmd = host.run(f"podman exec {container} cat {provision_config_path}")
    if cmd.rc != 0:
        return 0

    # Extract pxe_mapping_file_path
    match = re.search(
        r'pxe_mapping_file_path:\s*["\']?([^"\'#\n]+)["\']?',
        cmd.stdout
    )
    if not match:
        return 0
    pxe_mapping_path = match.group(1).strip()

    # Read PXE mapping file and count service_kube_node entries
    cmd = host.run(f"podman exec {container} cat {pxe_mapping_path}")
    if cmd.rc != 0:
        return 0

    count = 0
    for line in cmd.stdout.strip().split('\n'):
        if 'service_kube_node' in line.lower():
            count += 1

    return count


def get_service_kube_nodes_with_children(host) -> List[str]:
    """
    Get list of service_kube_node tags that have child slurm_nodes.

    Args:
        host: Testinfra host object

    Returns:
        List of service_kube_node tags that have children
    """
    container = TELEMETRY_VARS["container_name"]
    provision_config_path = PROVISION_CONFIG_PATH

    # Read provision_config.yml to get pxe_mapping_file_path
    cmd = host.run(f"podman exec {container} cat {provision_config_path}")
    if cmd.rc != 0:
        return []

    # Extract pxe_mapping_file_path
    match = re.search(
        r'pxe_mapping_file_path:\s*["\']?([^"\'#\n]+)["\']?',
        cmd.stdout
    )
    if not match:
        return []
    pxe_mapping_path = match.group(1).strip()

    # Read PXE mapping file
    cmd = host.run(f"podman exec {container} cat {pxe_mapping_path}")
    if cmd.rc != 0:
        return []

    # Parse PXE mapping file
    lines = cmd.stdout.strip().split('\n')
    service_kube_nodes = []
    slurm_parents = set()
    
    for line in lines[1:]:  # Skip header
        if 'service_kube_node' in line.lower():
            parts = line.split(',')
            if len(parts) >= 3:
                service_kube_nodes.append(parts[2].strip())  # SERVICE_TAG column
        elif 'slurm_node' in line.lower():
            parts = line.split(',')
            if len(parts) >= 4 and parts[3].strip():  # PARENT_SERVICE_TAG column
                slurm_parents.add(parts[3].strip())
    
    # Return service_kube_nodes that have children
    return [node for node in service_kube_nodes if node in slurm_parents]


def verify_idrac_telemetry_pod_count(host, admin_ip: str) -> Dict[str, Any]:
    """
    Verify idrac-telemetry pods count matches expected count.

    SSH to remote node and check kubectl get pods for idrac-telemetry.
    Expected count = service_kube_nodes with children + 1 (for management layer pod).

    Args:
        host: Testinfra host object
        admin_ip: Admin IP of node to SSH to (from PXE mapping file)

    Returns:
        Dict with success, expected_count, actual_count, pods, error
    """
    from ...core.host import run_on_remote_node

    # Get expected count (service_kube_nodes with children + 1 for mgmt)
    service_kube_nodes_with_children = get_service_kube_nodes_with_children(host)
    service_kube_node_count = get_service_kube_node_count(host)
    expected_count = len(service_kube_nodes_with_children) + 1

    # Get idrac-telemetry pods from remote node
    namespace = TELEMETRY_NAMESPACE
    pod_prefix = IDRAC_TELEMETRY_POD_PREFIX
    cmd = run_on_remote_node(
        host,
        f"kubectl get pods -n {namespace} -o name 2>/dev/null | grep {pod_prefix}",
        admin_ip
    )

    pods = []
    if cmd.rc == 0 and cmd.stdout.strip():
        pods = [p.strip() for p in cmd.stdout.strip().split('\n') if p.strip()]

    actual_count = len(pods)
    success = actual_count == expected_count

    return {
        "success": success,
        "expected_count": expected_count,
        "actual_count": actual_count,
        "service_kube_node_count": service_kube_node_count,
        "service_kube_nodes_with_children": service_kube_nodes_with_children,
        "pods": pods,
        "error": "" if success else (
            f"Expected {expected_count} idrac-telemetry pods, found {actual_count}"
        ),
    }


def verify_all_telemetry_pods_running(host, admin_ip: str) -> Dict[str, Any]:
    """
    Verify all pods in telemetry namespace are running.

    Args:
        host: Testinfra host object
        admin_ip: Admin IP of node to SSH to (from PXE mapping file)

    Returns:
        Dict with success, total_pods, running_pods, not_running_pods, output, error
    """
    from ...core.host import run_on_remote_node

    namespace = TELEMETRY_NAMESPACE

    # Get all pods with status
    cmd = run_on_remote_node(
        host,
        f"kubectl get pods -n {namespace} --no-headers 2>/dev/null",
        admin_ip
    )

    if cmd.rc != 0:
        return {
            "success": False,
            "total_pods": 0,
            "running_pods": [],
            "not_running_pods": [],
            "output": "",
            "error": f"Failed to get pods: {cmd.stderr}",
        }

    running_pods = []
    not_running_pods = []

    # Valid statuses: Running for regular pods, Completed for job/cronjob pods
    valid_statuses = ["Running", "Completed"]

    for line in cmd.stdout.strip().split('\n'):
        if not line.strip():
            continue
        parts = line.split()
        if len(parts) >= 3:
            pod_name = parts[0]
            status = parts[2]
            if status in valid_statuses:
                running_pods.append({
                    "name": pod_name,
                    "status": status,
                    "line": line
                })
            else:
                not_running_pods.append({
                    "name": pod_name,
                    "status": status,
                    "line": line
                })

    total_pods = len(running_pods) + len(not_running_pods)
    success = len(not_running_pods) == 0 and total_pods > 0

    # Get full output with headers for display
    cmd_full = run_on_remote_node(
        host,
        f"kubectl get pods -n {namespace} -o wide 2>/dev/null",
        admin_ip
    )

    return {
        "success": success,
        "total_pods": total_pods,
        "running_pods": running_pods,
        "not_running_pods": not_running_pods,
        "running_count": len(running_pods),
        "not_running_count": len(not_running_pods),
        "output": cmd_full.stdout if cmd_full.rc == 0 else cmd.stdout,
        "error": "" if success else (
            f"{len(not_running_pods)} pods not in Running state"
        ),
    }


# =============================================================================
# MYSQL DATA VERIFICATION FUNCTIONS
# =============================================================================

def get_mysql_credentials(host) -> Dict[str, str]:
    """
    Get MySQL credentials from ansible vault file.

    Handles both encrypted and already-decrypted (plain YAML) files.

    Args:
        host: Testinfra host object

    Returns:
        Dict with mysqldb_user and mysqldb_password
    """
    container = TELEMETRY_VARS["container_name"]
    vault_file = OMNIA_CONFIG_CREDENTIALS_PATH
    key_file = OMNIA_CONFIG_CREDENTIALS_KEY_PATH

    # First, try to decrypt vault file
    cmd = host.run(
        f"podman exec {container} ansible-vault view {vault_file} "
        f"--vault-password-file {key_file} 2>/dev/null"
    )

    if cmd.rc == 0:
        # Successfully decrypted
        content = cmd.stdout
    else:
        # Vault decrypt failed - file might be plain YAML, try reading directly
        cmd = host.run(f"podman exec {container} cat {vault_file}")
        if cmd.rc != 0:
            return {"mysqldb_user": "", "mysqldb_password": "", "error": cmd.stderr}
        content = cmd.stdout

    # Parse YAML content
    try:
        creds = yaml.safe_load(content)
        return {
            "mysqldb_user": creds.get("mysqldb_user", ""),
            "mysqldb_password": creds.get("mysqldb_password", ""),
            "error": "",
        }
    except yaml.YAMLError as e:
        return {"mysqldb_user": "", "mysqldb_password": "", "error": str(e)}


def get_activated_ips(host) -> List[str]:
    """
    Get list of activated IPs from idrac_telemetry_report.yml.

    Args:
        host: Testinfra host object

    Returns:
        List of activated IP addresses
    """
    container = TELEMETRY_VARS["container_name"]
    report_path = IDRAC_TELEMETRY_REPORT_PATH

    # Read telemetry report
    cmd = host.run(f"podman exec {container} cat {report_path}")
    if cmd.rc != 0:
        return []

    # Parse activated IPs from report
    activated_ips = []
    lines = cmd.stdout.strip().split('\n')
    capture_section = False
    
    for line in lines:
        if "Telemetry activated IPs List:" in line:
            capture_section = True
            continue
        elif capture_section and line.startswith('  - '):
            ip = line.strip()[4:]  # Remove '  - ' prefix
            activated_ips.append(ip)
        elif capture_section and line.strip() and not line.startswith('  -'):
            # End of the IP list section
            break
    
    return activated_ips


def has_activated_ips(host) -> bool:
    """
    Check if there are any activated IPs in telemetry report.

    Args:
        host: Testinfra host object

    Returns:
        True if there are activated IPs, False otherwise
    """
    return len(get_activated_ips(host)) > 0


def get_bmc_group_data(host) -> List[Dict[str, str]]:
    """
    Parse bmc_group_data.csv and return list of BMC entries.

    Args:
        host: Testinfra host object

    Returns:
        List of dicts with bmc_ip, group_name, parent keys
    """
    container = TELEMETRY_VARS["container_name"]
    bmc_path = BMC_GROUP_DATA_PATH

    cmd = host.run(f"podman exec {container} cat {bmc_path}")
    if cmd.rc != 0:
        return []

    entries = []
    lines = cmd.stdout.strip().split('\n')

    # Skip header if present
    for line in lines:
        if line.startswith('BMC_IP'):
            continue
        parts = line.split(',')
        if len(parts) >= 1:
            entries.append({
                "bmc_ip": parts[0].strip() if len(parts) > 0 else "",
                "group_name": parts[1].strip() if len(parts) > 1 else "",
                "parent": parts[2].strip() if len(parts) > 2 else "",
            })

    return entries


def get_service_cluster_metadata(host) -> Dict[str, Any]:
    """
    Parse service_cluster_metadata.yml and return pod-to-parent mapping.

    Args:
        host: Testinfra host object

    Returns:
        Dict with kube_vip and service_cluster_metadata
    """
    container = TELEMETRY_VARS["container_name"]
    metadata_path = SERVICE_CLUSTER_METADATA_PATH

    cmd = host.run(f"podman exec {container} cat {metadata_path}")
    if cmd.rc != 0:
        return {}

    try:
        return yaml.safe_load(cmd.stdout) or {}
    except yaml.YAMLError:
        return {}


def get_expected_ips_for_pod(
    pod_name: str,
    bmc_data: List[Dict[str, str]],
    activated_ips: List[str],
    cluster_metadata: Dict[str, Any]
) -> List[str]:
    """
    Get expected IPs for a specific idrac-telemetry pod.

    Logic:
    - idrac-telemetry-0 (MGMT): IPs with no PARENT AND activated
    - idrac-telemetry-N: IPs with PARENT=service_tag AND activated

    Args:
        pod_name: Pod name (e.g., idrac-telemetry-0)
        bmc_data: List of BMC entries from bmc_group_data.csv
        activated_ips: List of activated IPs from report
        cluster_metadata: Service cluster metadata

    Returns:
        List of expected IPs for this pod
    """
    expected_ips = []
    metadata = cluster_metadata.get("service_cluster_metadata", {})

    # Find which service_tag this pod belongs to
    pod_service_tag = None
    for service_tag, info in metadata.items():
        if info.get("idrac_podname") == pod_name:
            pod_service_tag = service_tag
            break

    if pod_service_tag == "MGMT_node":
        # idrac-telemetry-0: IPs with no PARENT
        for entry in bmc_data:
            if not entry["parent"] and entry["bmc_ip"] in activated_ips:
                expected_ips.append(entry["bmc_ip"])
    else:
        # idrac-telemetry-N: IPs with PARENT=service_tag
        for entry in bmc_data:
            if entry["parent"] == pod_service_tag and entry["bmc_ip"] in activated_ips:
                expected_ips.append(entry["bmc_ip"])

    return expected_ips


def get_mysql_ips_from_pod(
    host,
    admin_ip: str,
    pod_name: str,
    mysql_user: str,
    mysql_password: str
) -> List[str]:
    """
    Get IPs from MySQL services table in a specific pod.

    Args:
        host: Testinfra host object
        admin_ip: Admin IP of K8s node
        pod_name: Pod name (e.g., idrac-telemetry-0)
        mysql_user: MySQL username
        mysql_password: MySQL password

    Returns:
        List of IPs from services table
    """
    container = TELEMETRY_VARS["container_name"]
    ssh_opts = CMD_TEMPLATES["ssh_opts"]

    mysql_cmd = CMD_TEMPLATES["mysql_select_ips"].format(
        namespace=TELEMETRY_NAMESPACE,
        pod_name=pod_name,
        mysql_user=mysql_user,
        mysql_password=mysql_password,
        database=MYSQL_DATABASE,
        table=MYSQL_SERVICES_TABLE
    )

    full_cmd = (
        f"podman exec {container} ssh {ssh_opts} root@{admin_ip} "
        f'"{mysql_cmd}" 2>/dev/null'
    )

    cmd = host.run(full_cmd)

    if cmd.rc != 0:
        return []

    # Parse output - each line is an IP
    ips = []
    for line in cmd.stdout.strip().split('\n'):
        ip = line.strip()
        if ip and not ip.startswith('mysql:'):
            ips.append(ip)

    return ips


def verify_mysql_data_in_pods(host, admin_ip: str) -> Dict[str, Any]:
    """
    Verify MySQL data in all idrac-telemetry pods.

    For each pod, verify that expected IPs (from bmc_group_data.csv + activated list)
    are present in the MySQL services table.

    Args:
        host: Testinfra host object
        admin_ip: Admin IP of K8s node (kube_vip)

    Returns:
        Dict with success, pod_results, error
    """
    # Get MySQL credentials
    creds = get_mysql_credentials(host)
    if creds.get("error"):
        return {
            "success": False,
            "pod_results": [],
            "error": f"Failed to get MySQL credentials: {creds['error']}",
        }

    mysql_user = creds["mysqldb_user"]
    mysql_password = creds["mysqldb_password"]

    # Get activated IPs
    activated_ips = get_activated_ips(host)
    if not activated_ips:
        return {
            "success": False,
            "pod_results": [],
            "error": "No activated IPs found in telemetry report",
        }

    # Get BMC group data
    bmc_data = get_bmc_group_data(host)
    if not bmc_data:
        return {
            "success": False,
            "pod_results": [],
            "error": "Failed to read bmc_group_data.csv",
        }

    # Get service cluster metadata
    cluster_metadata = get_service_cluster_metadata(host)
    if not cluster_metadata:
        return {
            "success": False,
            "pod_results": [],
            "error": "Failed to read service_cluster_metadata.yml",
        }

    # Get kube_vip for SSH
    kube_vip = cluster_metadata.get("kube_vip", admin_ip)

    # Get list of idrac-telemetry pods
    from ...core.host import run_on_remote_node
    namespace = TELEMETRY_NAMESPACE
    cmd = run_on_remote_node(
        host,
        f"kubectl get pods -n {namespace} -o name 2>/dev/null | "
        f"grep {IDRAC_TELEMETRY_POD_PREFIX}",
        kube_vip
    )

    if cmd.rc != 0:
        return {
            "success": False,
            "pod_results": [],
            "error": "Failed to get idrac-telemetry pods",
        }

    pods = [p.replace("pod/", "").strip() for p in cmd.stdout.strip().split('\n')]

    # Verify each pod
    pod_results = []
    all_success = True

    for pod_name in pods:
        # Get expected IPs for this pod
        expected_ips = get_expected_ips_for_pod(
            pod_name, bmc_data, activated_ips, cluster_metadata
        )

        # Get actual IPs from MySQL
        actual_ips = get_mysql_ips_from_pod(
            host, kube_vip, pod_name, mysql_user, mysql_password
        )

        # Compare
        missing_ips = [ip for ip in expected_ips if ip not in actual_ips]
        extra_ips = [ip for ip in actual_ips if ip not in expected_ips]

        pod_success = len(missing_ips) == 0

        pod_results.append({
            "pod_name": pod_name,
            "success": pod_success,
            "expected_ips": expected_ips,
            "actual_ips": actual_ips,
            "missing_ips": missing_ips,
            "extra_ips": extra_ips,
        })

        if not pod_success:
            all_success = False

    return {
        "success": all_success,
        "activated_ips": activated_ips,
        "pod_results": pod_results,
        "error": "" if all_success else "Some pods have missing IPs in MySQL",
    }


# =============================================================================
# RECEIVER LOGS VERIFICATION FUNCTIONS
# =============================================================================

def get_receiver_logs(host, admin_ip: str, pod_name: str, tail_lines: int = 500) -> str:
    """
    Get idrac-telemetry-receiver container logs from a pod.

    Args:
        host: Testinfra host object
        admin_ip: Admin IP of K8s node (kube_vip)
        pod_name: Pod name (e.g., idrac-telemetry-0)
        tail_lines: Number of log lines to retrieve

    Returns:
        Log output as string
    """
    container = TELEMETRY_VARS["container_name"]
    ssh_opts = CMD_TEMPLATES["ssh_opts"]

    kubectl_cmd = CMD_TEMPLATES["kubectl_logs"].format(
        namespace=TELEMETRY_NAMESPACE,
        pod_name=pod_name,
        container=IDRAC_RECEIVER_CONTAINER,
        tail_lines=tail_lines
    )

    full_cmd = (
        f"podman exec {container} ssh {ssh_opts} root@{admin_ip} "
        f"'{kubectl_cmd}' 2>/dev/null"
    )

    cmd = host.run(full_cmd)
    return cmd.stdout if cmd.rc == 0 else ""


def get_service_tag_via_redfish(
    host,
    admin_ip: str,
    idrac_ip: str,
    idrac_user: str,
    idrac_password: str
) -> str:
    """
    Get service tag from iDRAC via Redfish API.

    Args:
        host: Testinfra host object
        admin_ip: Admin IP of K8s node (kube_vip)
        idrac_ip: iDRAC IP address
        idrac_user: iDRAC username
        idrac_password: iDRAC password

    Returns:
        Service tag string or empty string on failure
    """
    container = TELEMETRY_VARS["container_name"]
    ssh_opts = CMD_TEMPLATES["ssh_opts"]

    redfish_cmd = CMD_TEMPLATES["redfish_get_service_tag"].format(
        idrac_user=idrac_user,
        idrac_password=idrac_password,
        idrac_ip=idrac_ip
    )

    full_cmd = (
        f"podman exec {container} ssh {ssh_opts} root@{admin_ip} "
        f'"{redfish_cmd}" 2>/dev/null'
    )

    cmd = host.run(full_cmd)
    if cmd.rc != 0:
        return ""

    return cmd.stdout.strip()


def get_idrac_credentials_from_mysql(
    host,
    admin_ip: str,
    pod_name: str,
    mysql_user: str,
    mysql_password: str,
    idrac_ip: str
) -> Dict[str, str]:
    """
    Get iDRAC credentials for a specific IP from MySQL.

    Args:
        host: Testinfra host object
        admin_ip: Admin IP of K8s node (kube_vip)
        pod_name: Name of the idrac-telemetry pod
        mysql_user: MySQL username
        mysql_password: MySQL password
        idrac_ip: iDRAC IP to get credentials for

    Returns:
        Dict with username and password
    """
    container = TELEMETRY_VARS["container_name"]
    ssh_opts = CMD_TEMPLATES["ssh_opts"]

    mysql_cmd = CMD_TEMPLATES["mysql_select_auth"].format(
        namespace=TELEMETRY_NAMESPACE,
        pod_name=pod_name,
        mysql_user=mysql_user,
        mysql_password=mysql_password,
        database=MYSQL_DATABASE,
        table=MYSQL_SERVICES_TABLE,
        ip=idrac_ip
    )

    full_cmd = (
        f"podman exec {container} ssh {ssh_opts} root@{admin_ip} "
        f'"{mysql_cmd}" 2>/dev/null'
    )

    cmd = host.run(full_cmd)
    if cmd.rc != 0 or not cmd.stdout.strip():
        return {"username": "", "password": ""}

    # Parse JSON auth column
    try:
        import json
        auth_data = json.loads(cmd.stdout.strip())
        return {
            "username": auth_data.get("username", ""),
            "password": auth_data.get("password", "")
        }
    except (json.JSONDecodeError, KeyError):
        return {"username": "", "password": ""}


def extract_ip_to_service_tag_mapping(logs: str) -> Dict[str, str]:
    """
    Extract IP to service_tag mapping from receiver logs.

    Looks for pattern:
    - "<IP>: Got System ID <SERVICE_TAG>, Hostname <HOSTNAME>"

    Args:
        logs: Raw log output

    Returns:
        Dict mapping IP to service_tag
    """
    ip_to_tag = {}

    for line in logs.split('\n'):
        # Pattern: <IP>: Got System ID <SERVICE_TAG>, Hostname <HOSTNAME>
        if ': Got System ID ' in line:
            parts = line.split(': Got System ID ')
            if len(parts) >= 2:
                # Extract IP (last word before colon)
                ip_part = parts[0].split()[-1] if parts[0].split() else ""
                # Extract service tag (before comma)
                tag_part = parts[1].split(',')[0].strip()
                if ip_part and tag_part:
                    ip_to_tag[ip_part] = tag_part

    return ip_to_tag


def extract_collecting_service_tags(logs: str) -> List[str]:
    """
    Extract unique service tags that are actively collecting metrics.

    Looks for pattern:
    - "<SERVICE_TAG>: Got new report for /redfish"

    Args:
        logs: Raw log output

    Returns:
        List of unique service tags collecting metrics
    """
    tags = set()

    for line in logs.split('\n'):
        # Pattern: 2LXT933: Got new report for /redfish/v1/TelemetryService/MetricReports/
        if ': Got new report for /redfish' in line:
            parts = line.split(': Got new report')
            if len(parts) >= 1:
                tag_part = parts[0].split()[-1] if parts[0].split() else ""
                if tag_part:
                    tags.add(tag_part)

    return list(tags)


def extract_service_tags_from_logs(logs: str) -> Dict[str, Dict[str, Any]]:
    """
    Extract service tags and their status from receiver logs.

    Looks for patterns:
    - "<SERVICE_TAG>: Got new report" = collecting metrics
    - "<SERVICE_TAG>: Got SSE error" = connection issue
    - "Got Status: 200" after service tag = successful connection

    Args:
        logs: Raw log output

    Returns:
        Dict mapping service_tag to status info
    """
    service_tags = {}

    for line in logs.split('\n'):
        # Pattern: SERVICE_TAG: Got new report
        if ': Got new report for' in line:
            parts = line.split(': Got new report')
            if len(parts) >= 1:
                # Extract service tag (last word before colon)
                tag_part = parts[0].split()[-1] if parts[0].split() else ""
                if tag_part and tag_part not in service_tags:
                    service_tags[tag_part] = {
                        "collecting_metrics": True,
                        "connection_ok": True,
                        "last_status": "collecting"
                    }
                elif tag_part:
                    service_tags[tag_part]["collecting_metrics"] = True

        # Pattern: SERVICE_TAG: Got SSE error
        elif ': Got SSE error' in line:
            parts = line.split(': Got SSE error')
            if len(parts) >= 1:
                tag_part = parts[0].split()[-1] if parts[0].split() else ""
                if tag_part and tag_part not in service_tags:
                    service_tags[tag_part] = {
                        "collecting_metrics": False,
                        "connection_ok": False,
                        "last_status": "sse_error"
                    }

        # Pattern: Got Status: 200 (successful connection)
        elif 'Got Status:  200' in line:
            # This indicates successful SSE connection
            # The service tag is usually in the line before
            pass

    return service_tags


def get_metric_reports_for_tag(logs: str, service_tag: str, count: int = 3) -> List[str]:
    """
    Get recent 'Got new report' log entries for a specific service tag.

    Args:
        logs: Raw log output
        service_tag: Service tag to filter
        count: Number of entries to return

    Returns:
        List of metric report log lines
    """
    reports = []
    for line in logs.split('\n'):
        if f'{service_tag}: Got new report for /redfish' in line:
            reports.append(line.strip())

    # Return last N entries
    return reports[-count:] if reports else []


def verify_receiver_collecting_metrics(
    host,
    admin_ip: str
) -> Dict[str, Any]:
    """
    Verify idrac-telemetry-receiver is collecting metrics for each MySQL IP.

    For each pod:
    1. Get IPs from MySQL
    2. Extract IP→service_tag mapping from logs
    3. For each IP/service_tag, verify 'Got new report' entries exist
    4. Show 2-3 sample metric report entries per IP

    Args:
        host: Testinfra host object
        admin_ip: Admin IP of K8s node (kube_vip)

    Returns:
        Dict with success, pod_results, error
    """
    # Get MySQL credentials
    creds = get_mysql_credentials(host)
    if creds.get("error"):
        return {
            "success": False,
            "pod_results": [],
            "error": f"Failed to get MySQL credentials: {creds['error']}",
        }

    mysql_user = creds["mysqldb_user"]
    mysql_password = creds["mysqldb_password"]

    # Get service cluster metadata for kube_vip
    cluster_metadata = get_service_cluster_metadata(host)
    kube_vip = cluster_metadata.get("kube_vip", admin_ip)

    # Get list of idrac-telemetry pods
    from ...core.host import run_on_remote_node
    namespace = TELEMETRY_NAMESPACE
    cmd = run_on_remote_node(
        host,
        f"kubectl get pods -n {namespace} -o name 2>/dev/null | "
        f"grep {IDRAC_TELEMETRY_POD_PREFIX}",
        kube_vip
    )

    if cmd.rc != 0:
        return {
            "success": False,
            "pod_results": [],
            "error": "Failed to get idrac-telemetry pods",
        }

    pods = [p.replace("pod/", "").strip() for p in cmd.stdout.strip().split('\n')]

    # Verify each pod
    pod_results = []
    all_success = True

    for pod_name in pods:
        # Get IPs from MySQL for this pod
        mysql_ips = get_mysql_ips_from_pod(
            host, kube_vip, pod_name, mysql_user, mysql_password
        )

        # Get receiver logs
        logs = get_receiver_logs(host, kube_vip, pod_name, tail_lines=2000)

        # Build results for each MySQL IP
        ip_results = []
        pod_has_metrics = False

        for ip in mysql_ips:
            # Get service tag via Redfish for exact mapping
            idrac_creds = get_idrac_credentials_from_mysql(
                host, kube_vip, pod_name, mysql_user, mysql_password, ip
            )

            service_tag = ""
            if idrac_creds.get("username") and idrac_creds.get("password"):
                service_tag = get_service_tag_via_redfish(
                    host, kube_vip, ip,
                    idrac_creds["username"], idrac_creds["password"]
                )

            if service_tag:
                # Get sample metric reports for this service tag
                sample_reports = get_metric_reports_for_tag(logs, service_tag, count=3)

                if sample_reports:
                    pod_has_metrics = True

                ip_results.append({
                    "ip": ip,
                    "service_tag": service_tag,
                    "collecting_metrics": len(sample_reports) > 0,
                    "sample_reports": sample_reports,
                })
            else:
                # No service_tag found for this IP
                ip_results.append({
                    "ip": ip,
                    "service_tag": "",
                    "collecting_metrics": False,
                    "sample_reports": [],
                })

        # Check for connection status (Got Status: 200)
        has_connection = 'Got Status:  200' in logs

        # Pod success ONLY if ALL IPs have "Got new report" entries
        # SSE connected without metrics is NOT enough - must have live reports
        all_ips_have_metrics = all(r["collecting_metrics"] for r in ip_results) if ip_results else False

        pod_success = all_ips_have_metrics

        pod_results.append({
            "pod_name": pod_name,
            "success": pod_success,
            "mysql_ips": mysql_ips,
            "ip_results": ip_results,
            "collecting_metrics": pod_has_metrics,
            "connection_ok": has_connection,
        })

        if not pod_success:
            all_success = False

    return {
        "success": all_success,
        "pod_results": pod_results,
        "error": "" if all_success else "Some pods not collecting metrics",
    }
