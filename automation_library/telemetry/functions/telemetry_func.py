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
Telemetry Automation - Common Functions.

This module provides common functions used by both Kafka and VictoriaMetrics
telemetry verification modules.
"""

import json
from typing import Dict, Any

import yaml

from ..vars.idrac_telemetry_vars import TELEMETRY_VARS
from ..messages.telemetry_msgs import SHARED_ASSERT_MSGS

# Get paths from TELEMETRY_VARS (common config) - no defaults
TELEMETRY_CONFIG_PATH = TELEMETRY_VARS["telemetry_config_path"]
SOFTWARE_CONFIG_PATH = TELEMETRY_VARS["software_config_path"]


# =============================================================================
# CONFIGURATION READING FUNCTIONS
# =============================================================================

def get_telemetry_config(host) -> Dict[str, Any]:
    """
    Read telemetry_config.yml from container.

    Args:
        host: Testinfra host object

    Returns:
        Dict with telemetry configuration
    """
    container = TELEMETRY_VARS["container_name"]
    cmd = host.run(f"podman exec {container} cat {TELEMETRY_CONFIG_PATH}")

    if cmd.rc != 0:
        return {
            "error": SHARED_ASSERT_MSGS["telemetry_config_read_failed"].format(
                error=cmd.stderr
            )
        }

    try:
        config = yaml.safe_load(cmd.stdout)
        return config if config else {}
    except yaml.YAMLError as e:
        return {
            "error": SHARED_ASSERT_MSGS["telemetry_config_parse_failed"].format(
                error=e
            )
        }


def get_software_config(host) -> Dict[str, Any]:
    """
    Read software_config.json from container.

    Args:
        host: Testinfra host object

    Returns:
        Dict with software configuration
    """
    container = TELEMETRY_VARS["container_name"]
    cmd = host.run(f"podman exec {container} cat {SOFTWARE_CONFIG_PATH}")

    if cmd.rc != 0:
        return {
            "error": SHARED_ASSERT_MSGS["software_config_read_failed"].format(
                error=cmd.stderr
            )
        }

    try:
        config = json.loads(cmd.stdout)
        return config if config else {}
    except json.JSONDecodeError as e:
        return {
            "error": SHARED_ASSERT_MSGS["software_config_parse_failed"].format(
                error=e
            )
        }


# =============================================================================
# ENABLE CHECK FUNCTIONS
# =============================================================================

def is_idrac_telemetry_enabled(host) -> bool:
    """
    Check if iDRAC telemetry is enabled in telemetry_config.yml.

    Args:
        host: Testinfra host object

    Returns:
        True if idrac_telemetry_support is true
    """
    config = get_telemetry_config(host)
    if config.get("error"):
        return False

    return config.get("idrac_telemetry_support", False)


def is_kafka_enabled(host) -> bool:
    """
    Check if Kafka is enabled in idrac_telemetry_collection_type.

    Args:
        host: Testinfra host object

    Returns:
        True if 'kafka' is in collection type
    """
    config = get_telemetry_config(host)
    if config.get("error"):
        return False

    collection_type = config.get("idrac_telemetry_collection_type", "")
    return "kafka" in collection_type.lower()


def is_victoria_enabled(host) -> bool:
    """
    Check if VictoriaMetrics is enabled in telemetry_config.yml.

    Returns True if:
    - idrac_telemetry_support is true AND
    - 'victoria' is in idrac_telemetry_collection_type
    """
    config = get_telemetry_config(host)
    if config.get("error"):
        return False

    idrac_telemetry_support = config.get("idrac_telemetry_support", False)
    if not idrac_telemetry_support:
        return False

    collection_type = config.get("idrac_telemetry_collection_type", "")
    return "victoria" in collection_type.lower()


def is_ldms_enabled(host) -> bool:
    """
    Check if LDMS is enabled in software_config.json.

    Args:
        host: Testinfra host object

    Returns:
        True if 'ldms' is in softwares list
    """
    config = get_software_config(host)
    if config.get("error"):
        return False

    softwares = config.get("softwares", [])
    for software in softwares:
        if software.get("name", "").lower() == "ldms":
            return True
    return False


# =============================================================================
# SERVICE TAG FUNCTIONS
# =============================================================================

def get_activated_service_tags(host, admin_ip: str = ""):
    """
    Get list of activated service tags from idrac_telemetry_report.yml.

    The report file contains activated IPs. We get the actual service tag
    by querying the iDRAC via Redfish (same as receiver test).

    Args:
        host: Testinfra host object
        admin_ip: Admin IP (kube_vip) for SSH access to K8s cluster

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

    # For each activated IP, get the service tag via Redfish
    activated_tags = []
    for ip in activated_ips:
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
                    activated_tags.append(service_tag)
                break

    return activated_tags
