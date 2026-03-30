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
Telemetry Automation - Shared Functions.

This module provides shared functions used across all telemetry modules
(iDRAC, Kafka, VictoriaMetrics).

For module-specific functions, see:
- idrac_telemetry_func.py - iDRAC telemetry specific
- kafka_func.py - Kafka and LDMS specific
- victoria_func.py - VictoriaMetrics specific
"""

from typing import Dict, Any

import pytest

from ...core import (
    get_node_info,
    load_input_file,
    get_input_value,
    get_input_bool,
    clear_input_cache,
    K8S_CONTROL_PLANE_FUNCTIONAL_GROUP,
    TELEMETRY_CONFIG_FILE,
    SOFTWARE_CONFIG_FILE,
)

# =============================================================================
# CACHING - Uses core/load_inputs.py cache
# =============================================================================

_admin_ip_cache: Dict[int, str] = {}
_service_tag_cache: Dict[str, str] = {}  # IP -> ServiceTag mapping


def clear_cache():
    """Clear all caches. Useful for testing or when config changes."""
    clear_input_cache()  # Clear core config cache
    _admin_ip_cache.clear()
    _service_tag_cache.clear()


# =============================================================================
# CONFIGURATION READING FUNCTIONS (using core/load_inputs.py)
# =============================================================================

def get_telemetry_config(host) -> Dict[str, Any]:
    """
    Read telemetry_config.yml from container (cached by core).

    Args:
        host: Testinfra host object

    Returns:
        Dict with telemetry configuration
    """
    return load_input_file(host, TELEMETRY_CONFIG_FILE)


def get_software_config(host) -> Dict[str, Any]:
    """
    Read software_config.json from container (cached by core).

    Args:
        host: Testinfra host object

    Returns:
        Dict with software configuration
    """
    return load_input_file(host, SOFTWARE_CONFIG_FILE)


# =============================================================================
# ENABLE CHECK FUNCTIONS (using core get_input_value/get_input_bool)
# =============================================================================

def is_idrac_telemetry_enabled(host) -> bool:
    """Check if iDRAC telemetry is enabled in telemetry_config.yml."""
    return get_input_bool(host, TELEMETRY_CONFIG_FILE, "idrac_telemetry_support")


def is_kafka_enabled(host) -> bool:
    """Check if Kafka is enabled in idrac_telemetry_collection_type."""
    collection_type = get_input_value(host, TELEMETRY_CONFIG_FILE, "idrac_telemetry_collection_type")
    if not collection_type:
        return False
    return "kafka" in collection_type.lower()


def is_victoria_enabled(host) -> bool:
    """
    Check if VictoriaMetrics is enabled in telemetry_config.yml.

    Returns True if:
    - idrac_telemetry_support is true AND
    - 'victoria' is in idrac_telemetry_collection_type
    """
    if not get_input_bool(host, TELEMETRY_CONFIG_FILE, "idrac_telemetry_support"):
        return False
    collection_type = get_input_value(host, TELEMETRY_CONFIG_FILE, "idrac_telemetry_collection_type")
    if not collection_type:
        return False
    return "victoria" in collection_type.lower()


def is_ldms_enabled(host) -> bool:
    """Check if LDMS is enabled in software_config.json."""
    softwares = get_input_value(host, SOFTWARE_CONFIG_FILE, "softwares")
    if not softwares:
        return False
    for software in softwares:
        if isinstance(software, dict) and software.get("name", "").lower() == "ldms":
            return True
    return False


# =============================================================================
# SERVICE TAG FUNCTIONS
# =============================================================================

def get_activated_service_tags(host, admin_ip: str = "", use_cache: bool = True):
    """
    Get list of activated service tags from idrac_telemetry_report.yml.

    The report file contains activated IPs. We get the actual service tag
    by querying the iDRAC via Redfish (same as receiver test).

    Uses caching to avoid repeated Redfish calls when running multiple tests.

    Args:
        host: Testinfra host object
        admin_ip: Admin IP (kube_vip) for SSH access to K8s cluster
        use_cache: If True, use cached service tags if available (default: True)

    Returns:
        List of service tags that have been activated
    """
    from .idrac_telemetry_func import (
        get_activated_ips,
        get_service_cluster_metadata,
        get_mysql_credentials,
        get_idrac_credentials_from_mysql,
        get_service_tag_via_redfish,
    )

    # Get activated IPs from telemetry report
    activated_ips = get_activated_ips(host)
    if not activated_ips:
        return []

    # Get kube_vip if admin_ip not provided
    if not admin_ip:
        cluster_metadata = get_service_cluster_metadata(host)
        admin_ip = cluster_metadata.get("kube_vip", "")
        if not admin_ip:
            return []

    # Get MySQL credentials for querying iDRAC credentials
    creds = get_mysql_credentials(host)
    if creds.get("error"):
        return []

    mysql_user = creds["mysqldb_user"]
    mysql_password = creds["mysqldb_password"]

    # For each activated IP, get the service tag via Redfish (with caching)
    activated_tags = []
    for ip in activated_ips:
        # Check cache first
        if use_cache and ip in _service_tag_cache:
            activated_tags.append(_service_tag_cache[ip])
            continue

        # Find which pod has this IP in MySQL
        # Try each pod until we find the credentials
        for pod_num in range(3):  # idrac-telemetry-0, 1, 2
            pod_name = f"idrac-telemetry-{pod_num}"
            idrac_creds = get_idrac_credentials_from_mysql(
                host, admin_ip, pod_name, mysql_user, mysql_password, ip
            )
            if idrac_creds.get("username") and idrac_creds.get("password"):
                service_tag = get_service_tag_via_redfish(
                    host, admin_ip, ip,
                    idrac_creds["username"], idrac_creds["password"]
                )
                if service_tag:
                    # Cache the result
                    if use_cache:
                        _service_tag_cache[ip] = service_tag
                    activated_tags.append(service_tag)
                break

    return activated_tags


def get_ip_to_service_tag_mapping(
    host, admin_ip: str, activated_ips: list, use_cache: bool = True
) -> Dict[str, str]:
    """
    Get IP to service tag mapping for activated IPs via Redfish.

    Uses caching to avoid repeated Redfish calls when running multiple tests.

    Args:
        host: Testinfra host object
        admin_ip: Admin IP (kube_vip) for SSH access to K8s cluster
        activated_ips: List of activated iDRAC IPs
        use_cache: If True, use cached service tags if available (default: True)

    Returns:
        Dict mapping IP -> ServiceTag
    """
    from .idrac_telemetry_func import (
        get_mysql_credentials,
        get_idrac_credentials_from_mysql,
        get_service_tag_via_redfish,
    )

    if not activated_ips:
        return {}

    # Get MySQL credentials for querying iDRAC credentials
    creds = get_mysql_credentials(host)
    if creds.get("error"):
        return {}

    mysql_user = creds["mysqldb_user"]
    mysql_password = creds["mysqldb_password"]

    # For each activated IP, get the service tag via Redfish (with caching)
    ip_to_service_tag = {}
    for ip in activated_ips:
        # Check cache first
        if use_cache and ip in _service_tag_cache:
            ip_to_service_tag[ip] = _service_tag_cache[ip]
            continue

        # Find which pod has this IP in MySQL
        # Try each pod until we find the credentials
        for pod_num in range(3):  # idrac-telemetry-0, 1, 2
            pod_name = f"idrac-telemetry-{pod_num}"
            idrac_creds = get_idrac_credentials_from_mysql(
                host, admin_ip, pod_name, mysql_user, mysql_password, ip
            )
            if idrac_creds.get("username") and idrac_creds.get("password"):
                service_tag = get_service_tag_via_redfish(
                    host, admin_ip, ip,
                    idrac_creds["username"], idrac_creds["password"]
                )
                if service_tag:
                    # Cache the result
                    if use_cache:
                        _service_tag_cache[ip] = service_tag
                    ip_to_service_tag[ip] = service_tag
                break

    return ip_to_service_tag


# =============================================================================
# TEST HELPER FUNCTIONS
# =============================================================================

def get_admin_ip(host, log=None, use_cache: bool = True) -> str:
    """
    Get admin IP from PXE mapping file with caching.

    Common helper function used by all telemetry test files.
    Caches the result to avoid repeated PXE file reads during test runs.

    Args:
        host: Testinfra host object
        log: TestLogger instance (optional - for backward compatibility)
        use_cache: If True, return cached IP if available (default: True)

    Returns:
        Admin IP string

    Raises:
        AssertionError if admin IP not found
    """
    # Check cache first
    cache_key = id(host)
    if use_cache and cache_key in _admin_ip_cache:
        if log:
            log.check("Getting admin IP from PXE mapping file (cached)")
        return _admin_ip_cache[cache_key]

    if log:
        log.check("Getting admin IP from PXE mapping file")

    node = get_node_info(
        host,
        search_by="functional_group",
        search_value=K8S_CONTROL_PLANE_FUNCTIONAL_GROUP
    )
    admin_ip = node.get("admin_ip", "")
    assert admin_ip, "Failed to get admin IP from PXE mapping file"

    # Cache the result
    if use_cache:
        _admin_ip_cache[cache_key] = admin_ip

    return admin_ip


def skip_if_kafka_not_enabled(host, log):
    """
    Skip test if Kafka is not enabled.

    Checks if 'kafka' is in idrac_telemetry_collection_type.

    Args:
        host: Testinfra host object
        log: TestLogger instance
    """
    if not is_kafka_enabled(host):
        log.skipped(
            "Kafka is not enabled in idrac_telemetry_collection_type",
            "Test skipped - Kafka not enabled"
        )
        pytest.skip("Kafka is not enabled in idrac_telemetry_collection_type")


def skip_if_victoria_not_enabled(host, log):
    """
    Skip test if VictoriaMetrics is not enabled.

    Checks:
    - idrac_telemetry_support must be true
    - 'victoria' must be in idrac_telemetry_collection_type

    Args:
        host: Testinfra host object
        log: TestLogger instance
    """
    if not is_idrac_telemetry_enabled(host):
        log.skipped(
            "iDRAC telemetry is not enabled (idrac_telemetry_support=false)",
            "Test skipped - iDRAC telemetry not enabled"
        )
        pytest.skip("iDRAC telemetry is not enabled")

    if not is_victoria_enabled(host):
        log.skipped(
            "VictoriaMetrics is not enabled in idrac_telemetry_collection_type",
            "Test skipped - VictoriaMetrics not enabled"
        )
        pytest.skip("VictoriaMetrics is not enabled")


def skip_if_ldms_not_enabled(host, log):
    """
    Skip test if LDMS is not enabled.

    Checks if 'ldms' is in software_config.json softwares list.

    Args:
        host: Testinfra host object
        log: TestLogger instance
    """
    if not is_ldms_enabled(host):
        log.skipped(
            "LDMS is not enabled in software_config.json",
            "Test skipped - LDMS not enabled"
        )
        pytest.skip("LDMS is not enabled in software_config.json")
