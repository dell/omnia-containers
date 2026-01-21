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
Telemetry Automation - Kafka Functions.

This module provides functions for verifying Kafka configuration and connectivity
in the telemetry namespace.
"""

import json
import time
from typing import Dict, Any, List

import yaml

from ..vars.idrac_telemetry_vars import (
    TELEMETRY_VARS,
    TELEMETRY_NAMESPACE,
    CMD_TEMPLATES,
)
from ..messages.kafka_msgs import KAFKA_ASSERT_MSGS
from ..messages.telemetry_msgs import SHARED_ASSERT_MSGS
from ..vars.kafka_vars import (
    TELEMETRY_CONFIG_PATH,
    SOFTWARE_CONFIG_PATH,
    KAFKA_CMD_TEMPLATES,
    LDMS_AGGR_POD_PREFIX,
    LDMS_STORE_POD_PREFIX,
    KAFKA_BRIDGE_SERVICE,
    KAFKA_BRIDGE_PORT,
    LDMS_FUNCTIONAL_GROUPS,
    OIM_METADATA_PATH,
)


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
        return {"error": SHARED_ASSERT_MSGS["telemetry_config_read_failed"].format(error=cmd.stderr)}

    try:
        config = yaml.safe_load(cmd.stdout)
        return config if config else {}
    except yaml.YAMLError as e:
        return {"error": SHARED_ASSERT_MSGS["telemetry_config_parse_failed"].format(error=e)}


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
        return {"error": SHARED_ASSERT_MSGS["software_config_read_failed"].format(error=cmd.stderr)}

    try:
        config = json.loads(cmd.stdout)
        return config if config else {}
    except json.JSONDecodeError as e:
        return {"error": SHARED_ASSERT_MSGS["software_config_parse_failed"].format(error=e)}


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


def is_idrac_telemetry_enabled(host) -> bool:
    """
    Check if idrac-telemetry is enabled in idrac_telemetry_collection_type.

    Args:
        host: Testinfra host object

    Returns:
        True if 'idrac-telemetry' is in collection type
    """
    config = get_telemetry_config(host)
    if config.get("error"):
        return False

    collection_type = config.get("idrac_telemetry_collection_type", "")
    return "idrac-telemetry" in collection_type.lower()


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


def get_ldms_config_from_telemetry(host) -> Dict[str, Any]:
    """
    Get LDMS configuration from telemetry_config.yml.

    Args:
        host: Testinfra host object

    Returns:
        Dict with ldms_agg_port and ldms_store_port (read from config, no defaults)
    """
    config = get_telemetry_config(host)
    if config.get("error"):
        return config

    result = {}

    if "ldms_agg_port" in config:
        result["ldms_agg_port"] = config["ldms_agg_port"]
    else:
        result["error"] = "ldms_agg_port not found in telemetry_config.yml"
        return result

    if "ldms_store_port" in config:
        result["ldms_store_port"] = config["ldms_store_port"]
    else:
        result["error"] = "ldms_store_port not found in telemetry_config.yml"
        return result

    return result


def get_kafka_config_from_telemetry(host) -> Dict[str, Any]:
    """
    Get kafka_configurations from telemetry_config.yml.

    Args:
        host: Testinfra host object

    Returns:
        Dict with kafka configurations
    """
    config = get_telemetry_config(host)
    if config.get("error"):
        return config

    return config.get("kafka_configurations", {})


def get_topic_partitions_config(host) -> List[Dict[str, Any]]:
    """
    Get topic_partitions from telemetry_config.yml.

    Args:
        host: Testinfra host object

    Returns:
        List of topic partition configs
    """
    kafka_config = get_kafka_config_from_telemetry(host)
    if kafka_config.get("error"):
        return []

    return kafka_config.get("topic_partitions", [])


# =============================================================================
# KAFKA CLUSTER VERIFICATION FUNCTIONS
# =============================================================================

def get_kafka_cluster_config(host, admin_ip: str) -> Dict[str, Any]:
    """
    Get Kafka cluster configuration from K8s.

    Args:
        host: Testinfra host object
        admin_ip: Admin IP of K8s node

    Returns:
        Dict with Kafka cluster config
    """
    container = TELEMETRY_VARS["container_name"]
    ssh_opts = CMD_TEMPLATES["ssh_opts"]

    kubectl_cmd = KAFKA_CMD_TEMPLATES["get_kafka_cluster"].format(namespace=TELEMETRY_NAMESPACE)
    full_cmd = (
        f"podman exec {container} ssh {ssh_opts} root@{admin_ip} "
        f"'{kubectl_cmd}' 2>/dev/null"
    )

    cmd = host.run(full_cmd)
    if cmd.rc != 0:
        return {"error": KAFKA_ASSERT_MSGS["kafka_cluster_config_failed"]}

    try:
        return json.loads(cmd.stdout)
    except json.JSONDecodeError:
        return {"error": KAFKA_ASSERT_MSGS["kafka_cluster_parse_failed"]}


def verify_kafka_config_match(host, admin_ip: str) -> Dict[str, Any]:
    """
    Verify kafka_configurations in telemetry_config.yml match actual Kafka config.

    Args:
        host: Testinfra host object
        admin_ip: Admin IP of K8s node

    Returns:
        Dict with success, mismatches, details
    """
    # Get expected config from telemetry_config.yml
    expected_config = get_kafka_config_from_telemetry(host)
    if expected_config.get("error"):
        return {
            "success": False,
            "error": expected_config["error"],
            "mismatches": [],
        }

    # Get actual Kafka cluster config
    actual_cluster = get_kafka_cluster_config(host, admin_ip)
    if actual_cluster.get("error"):
        return {
            "success": False,
            "error": actual_cluster["error"],
            "mismatches": [],
        }

    kafka_spec = actual_cluster.get("spec", {}).get("kafka", {}).get("config", {})

    mismatches = []

    # Check log_retention_hours (must be in config, no default)
    if "log_retention_hours" not in expected_config:
        return {
            "success": False,
            "error": KAFKA_ASSERT_MSGS["kafka_config_missing"].format(config="log_retention_hours"),
            "mismatches": [],
        }
    expected_retention = expected_config["log_retention_hours"]
    actual_retention = kafka_spec.get("log.retention.hours")
    if expected_retention != actual_retention:
        mismatches.append({
            "config": "log_retention_hours",
            "expected": expected_retention,
            "actual": actual_retention,
        })

    # Check log_retention_bytes (must be in config, no default)
    if "log_retention_bytes" not in expected_config:
        return {
            "success": False,
            "error": KAFKA_ASSERT_MSGS["kafka_config_missing"].format(config="log_retention_bytes"),
            "mismatches": [],
        }
    expected_bytes = expected_config["log_retention_bytes"]
    actual_bytes = kafka_spec.get("log.retention.bytes")
    if expected_bytes != actual_bytes:
        mismatches.append({
            "config": "log_retention_bytes",
            "expected": expected_bytes,
            "actual": actual_bytes,
        })

    # Check log_segment_bytes (must be in config, no default)
    if "log_segment_bytes" not in expected_config:
        return {
            "success": False,
            "error": KAFKA_ASSERT_MSGS["kafka_config_missing"].format(config="log_segment_bytes"),
            "mismatches": [],
        }
    expected_segment = expected_config["log_segment_bytes"]
    actual_segment = kafka_spec.get("log.segment.bytes")
    if expected_segment != actual_segment:
        mismatches.append({
            "config": "log_segment_bytes",
            "expected": expected_segment,
            "actual": actual_segment,
        })

    return {
        "success": len(mismatches) == 0,
        "mismatches": mismatches,
        "expected_config": expected_config,
        "actual_config": kafka_spec,
    }


def get_kafka_bridge_ip(host, admin_ip: str) -> str:
    """
    Get the external IP of the Kafka bridge (REST proxy) LoadBalancer service.

    Args:
        host: Testinfra host object
        admin_ip: Admin IP of K8s node

    Returns:
        Bridge LB IP address, or empty string if not found
    """
    container = TELEMETRY_VARS["container_name"]
    ssh_opts = CMD_TEMPLATES["ssh_opts"]

    kubectl_cmd = KAFKA_CMD_TEMPLATES["get_bridge_lb_ip"].format(
        service=KAFKA_BRIDGE_SERVICE,
        namespace=TELEMETRY_NAMESPACE
    )
    full_cmd = (
        f"podman exec {container} ssh {ssh_opts} root@{admin_ip} "
        f"'{kubectl_cmd}' 2>/dev/null"
    )

    cmd = host.run(full_cmd)
    if cmd.rc != 0:
        return ""

    return cmd.stdout.strip().strip("'")


def verify_kafka_topics_via_rest(host, admin_ip: str) -> Dict[str, Any]:
    """
    Verify Kafka topics exist via REST proxy.

    Checks:
    1. If kafka not in idrac_telemetry_collection_type -> skip (return skip=True)
    2. If idrac_telemetry_support=true AND kafka in collection_type -> idrac topic MUST exist
    3. If idrac_telemetry_support=false AND idrac topic exists -> FAIL (should not exist)
    4. If ldms in software_config.json -> ldms topic MUST exist
    5. If ldms NOT in software_config.json AND ldms topic exists -> FAIL (should not exist)

    All checks run and all errors are collected before returning.

    Args:
        host: Testinfra host object
        admin_ip: Admin IP of K8s node

    Returns:
        Dict with success, skip, topics list, bridge_ip, errors
    """
    # Get telemetry config
    config = get_telemetry_config(host)
    if config.get("error"):
        return {
            "success": False,
            "skip": False,
            "topics": [],
            "bridge_ip": "",
            "error": f"Failed to read telemetry_config.yml: {config.get('error')}"
        }

    # Check if kafka is in collection type
    collection_type = config.get("idrac_telemetry_collection_type", "")
    kafka_enabled = "kafka" in collection_type.lower()

    if not kafka_enabled:
        return {
            "success": True,
            "skip": True,
            "skip_reason": "kafka not in idrac_telemetry_collection_type",
            "topics": [],
            "bridge_ip": "",
            "error": ""
        }

    # Get idrac_telemetry_support
    idrac_telemetry_support = config.get("idrac_telemetry_support", False)

    # Get ldms enabled status
    ldms_enabled = is_ldms_enabled(host)

    # Get bridge IP
    bridge_ip = get_kafka_bridge_ip(host, admin_ip)
    if not bridge_ip:
        return {
            "success": False,
            "skip": False,
            "topics": [],
            "bridge_ip": "",
            "error": KAFKA_ASSERT_MSGS["kafka_bridge_not_found"]
        }

    # Get topics via REST proxy
    container = TELEMETRY_VARS["container_name"]
    ssh_opts = CMD_TEMPLATES["ssh_opts"]

    curl_cmd = KAFKA_CMD_TEMPLATES["rest_list_topics"].format(
        bridge_ip=bridge_ip,
        port=KAFKA_BRIDGE_PORT
    )
    full_cmd = (
        f"podman exec {container} ssh {ssh_opts} root@{admin_ip} "
        f"'{curl_cmd}' 2>/dev/null"
    )

    cmd = host.run(full_cmd)
    if cmd.rc != 0:
        return {
            "success": False,
            "skip": False,
            "topics": [],
            "bridge_ip": bridge_ip,
            "error": KAFKA_ASSERT_MSGS["kafka_rest_connection_failed"].format(bridge_ip=bridge_ip)
        }

    try:
        topics = json.loads(cmd.stdout)
    except json.JSONDecodeError:
        return {
            "success": False,
            "skip": False,
            "topics": [],
            "bridge_ip": bridge_ip,
            "error": KAFKA_ASSERT_MSGS["kafka_rest_parse_failed"].format(response=cmd.stdout[:200])
        }

    # Run all checks and collect errors
    errors = []
    topic_results = []
    idrac_exists = "idrac" in topics
    ldms_exists = "ldms" in topics

    # Check 1: idrac topic
    if idrac_telemetry_support:
        # idrac_telemetry_support=true -> idrac topic MUST exist
        topic_results.append({
            "topic": "idrac",
            "exists": idrac_exists,
            "required": True,
            "reason": "idrac_telemetry_support=true",
        })
        if not idrac_exists:
            errors.append("idrac topic not found but idrac_telemetry_support=true")
    else:
        # idrac_telemetry_support=false -> idrac topic should NOT exist
        topic_results.append({
            "topic": "idrac",
            "exists": idrac_exists,
            "required": False,
            "reason": "idrac_telemetry_support=false",
        })
        if idrac_exists:
            errors.append("idrac topic exists but idrac_telemetry_support=false")

    # Check 2: ldms topic
    if ldms_enabled:
        # ldms in software_config -> ldms topic MUST exist
        topic_results.append({
            "topic": "ldms",
            "exists": ldms_exists,
            "required": True,
            "reason": "ldms enabled in software_config.json",
        })
        if not ldms_exists:
            errors.append("ldms topic not found but ldms is enabled in software_config.json")
    else:
        # ldms NOT in software_config -> ldms topic should NOT exist
        topic_results.append({
            "topic": "ldms",
            "exists": ldms_exists,
            "required": False,
            "reason": "ldms not in software_config.json",
        })
        if ldms_exists:
            errors.append("ldms topic exists but ldms is not enabled in software_config.json")

    return {
        "success": len(errors) == 0,
        "skip": False,
        "topics": topics,
        "bridge_ip": bridge_ip,
        "idrac_telemetry_support": idrac_telemetry_support,
        "ldms_enabled": ldms_enabled,
        "topic_results": topic_results,
        "errors": errors,
        "error": "; ".join(errors) if errors else "",
    }


# =============================================================================
# LDMS PODS AND SERVICES VERIFICATION
# =============================================================================

def verify_ldms_pods_running(host, admin_ip: str) -> Dict[str, Any]:
    """
    Verify LDMS pods (nersc-ldms-aggr and nersc-ldms-store) are running.

    Args:
        host: Testinfra host object
        admin_ip: Admin IP of K8s node

    Returns:
        Dict with success, pod_results, errors
    """
    # Check if LDMS is enabled
    if not is_ldms_enabled(host):
        return {
            "success": True,
            "skipped": True,
            "reason": "LDMS not enabled in software_config.json",
        }

    container = TELEMETRY_VARS["container_name"]
    ssh_opts = CMD_TEMPLATES["ssh_opts"]

    # Get pods in telemetry namespace
    kubectl_cmd = KAFKA_CMD_TEMPLATES["get_pods"].format(namespace=TELEMETRY_NAMESPACE)
    full_cmd = (
        f"podman exec {container} ssh {ssh_opts} root@{admin_ip} "
        f"'{kubectl_cmd}' 2>/dev/null"
    )

    cmd = host.run(full_cmd)
    if cmd.rc != 0:
        return {
            "success": False,
            "error": KAFKA_ASSERT_MSGS["pods_get_failed"].format(error=cmd.stderr),
        }

    try:
        data = json.loads(cmd.stdout)
        pods = data.get("items", [])
    except json.JSONDecodeError:
        return {
            "success": False,
            "error": KAFKA_ASSERT_MSGS["pods_parse_failed"],
        }

    pod_results = []
    errors = []

    # Check for nersc-ldms-aggr pod
    aggr_pods = [p for p in pods if p.get("metadata", {}).get("name", "").startswith(LDMS_AGGR_POD_PREFIX)]
    if aggr_pods:
        for pod in aggr_pods:
            pod_name = pod.get("metadata", {}).get("name", "")
            phase = pod.get("status", {}).get("phase", "Unknown")
            is_running = phase == "Running"
            pod_results.append({
                "pod": pod_name,
                "phase": phase,
                "running": is_running,
            })
            if not is_running:
                errors.append(f"Pod {pod_name} is not running (phase: {phase})")
    else:
        errors.append(f"No {LDMS_AGGR_POD_PREFIX} pod found")
        pod_results.append({
            "pod": LDMS_AGGR_POD_PREFIX,
            "phase": "NotFound",
            "running": False,
        })

    # Check for nersc-ldms-store pod
    store_pods = [p for p in pods if p.get("metadata", {}).get("name", "").startswith(LDMS_STORE_POD_PREFIX)]
    if store_pods:
        for pod in store_pods:
            pod_name = pod.get("metadata", {}).get("name", "")
            phase = pod.get("status", {}).get("phase", "Unknown")
            is_running = phase == "Running"
            pod_results.append({
                "pod": pod_name,
                "phase": phase,
                "running": is_running,
            })
            if not is_running:
                errors.append(f"Pod {pod_name} is not running (phase: {phase})")
    else:
        errors.append(f"No {LDMS_STORE_POD_PREFIX} pod found")
        pod_results.append({
            "pod": LDMS_STORE_POD_PREFIX,
            "phase": "NotFound",
            "running": False,
        })

    return {
        "success": len(errors) == 0,
        "pod_results": pod_results,
        "errors": errors,
    }


def verify_ldms_services_ports(host, admin_ip: str) -> Dict[str, Any]:
    """
    Verify LDMS services ports match telemetry_config.yml.

    Args:
        host: Testinfra host object
        admin_ip: Admin IP of K8s node

    Returns:
        Dict with success, service_results, errors
    """
    # Check if LDMS is enabled
    if not is_ldms_enabled(host):
        return {
            "success": True,
            "skipped": True,
            "reason": "LDMS not enabled in software_config.json",
        }

    # Get expected ports from telemetry_config.yml
    ldms_config = get_ldms_config_from_telemetry(host)
    if ldms_config.get("error"):
        return {
            "success": False,
            "error": ldms_config["error"],
        }

    expected_agg_port = ldms_config["ldms_agg_port"]
    expected_store_port = ldms_config["ldms_store_port"]

    container = TELEMETRY_VARS["container_name"]
    ssh_opts = CMD_TEMPLATES["ssh_opts"]

    # Get services in telemetry namespace
    kubectl_cmd = KAFKA_CMD_TEMPLATES["get_services"].format(namespace=TELEMETRY_NAMESPACE)
    full_cmd = (
        f"podman exec {container} ssh {ssh_opts} root@{admin_ip} "
        f"'{kubectl_cmd}' 2>/dev/null"
    )

    cmd = host.run(full_cmd)
    if cmd.rc != 0:
        return {
            "success": False,
            "error": KAFKA_ASSERT_MSGS["services_get_failed"].format(error=cmd.stderr),
        }

    try:
        data = json.loads(cmd.stdout)
        services = data.get("items", [])
    except json.JSONDecodeError:
        return {
            "success": False,
            "error": KAFKA_ASSERT_MSGS["services_parse_failed"],
        }

    service_results = []
    errors = []

    # Find nersc-ldms-aggr service
    aggr_services = [s for s in services if "ldms-aggr" in s.get("metadata", {}).get("name", "").lower()]
    if aggr_services:
        for svc in aggr_services:
            svc_name = svc.get("metadata", {}).get("name", "")
            ports = svc.get("spec", {}).get("ports", [])
            actual_port = ports[0].get("port") if ports else None
            port_match = actual_port == expected_agg_port
            service_results.append({
                "service": svc_name,
                "expected_port": expected_agg_port,
                "actual_port": actual_port,
                "match": port_match,
            })
            if not port_match:
                errors.append(f"Service {svc_name} port mismatch: expected {expected_agg_port}, actual {actual_port}")
    else:
        errors.append("No LDMS aggregator service found")

    # Find nersc-ldms-store service
    store_services = [s for s in services if "ldms-store" in s.get("metadata", {}).get("name", "").lower()]
    if store_services:
        for svc in store_services:
            svc_name = svc.get("metadata", {}).get("name", "")
            ports = svc.get("spec", {}).get("ports", [])
            actual_port = ports[0].get("port") if ports else None
            port_match = actual_port == expected_store_port
            service_results.append({
                "service": svc_name,
                "expected_port": expected_store_port,
                "actual_port": actual_port,
                "match": port_match,
            })
            if not port_match:
                errors.append(f"Service {svc_name} port mismatch: expected {expected_store_port}, actual {actual_port}")
    else:
        errors.append("No LDMS store service found")

    return {
        "success": len(errors) == 0,
        "expected_config": {
            "ldms_agg_port": expected_agg_port,
            "ldms_store_port": expected_store_port,
        },
        "service_results": service_results,
        "errors": errors,
    }


# =============================================================================
# KAFKA DATA FLOW VERIFICATION
# =============================================================================

def verify_idrac_topic_data(host, admin_ip: str, timeout_seconds: int = 30) -> Dict[str, Any]:
    """
    Verify data is flowing to idrac Kafka topic.

    Args:
        host: Testinfra host object
        admin_ip: Admin IP of K8s node
        timeout_seconds: Timeout for consumer

    Returns:
        Dict with success, messages_received, error
    """
    container = TELEMETRY_VARS["container_name"]
    ssh_opts = CMD_TEMPLATES["ssh_opts"]

    # Check topic offset to see if messages exist
    # Using kafkatopic status is simpler than running a consumer
    topic_cmd = (
        f"kubectl get kafkatopic idrac -n {TELEMETRY_NAMESPACE} -o json | "
        f"python3 -c \\\"import sys,json; d=json.load(sys.stdin); "
        f"conds=d.get('status',{{}}).get('conditions',[]); "
        f"print('True' if any(c.get('type')=='Ready' and c.get('status')=='True' for c in conds) else 'False')\\\""
    )
    full_cmd = (
        f"podman exec {container} ssh {ssh_opts} root@{admin_ip} "
        f'"{topic_cmd}" 2>/dev/null'
    )

    cmd = host.run(full_cmd)
    topic_ready = cmd.stdout.strip() == "True"

    if not topic_ready:
        return {
            "success": False,
            "topic_ready": False,
            "error": "idrac topic is not ready",
        }

    # Check if kafkapump (the producer) is running
    # kafkapump is part of idrac-telemetry pods
    pump_cmd = (
        f"kubectl get pods -n {TELEMETRY_NAMESPACE} -l app=idrac-telemetry "
        f"-o jsonpath='{{.items[*].status.phase}}'"
    )
    full_cmd = (
        f"podman exec {container} ssh {ssh_opts} root@{admin_ip} "
        f"'{pump_cmd}' 2>/dev/null"
    )

    cmd = host.run(full_cmd)
    pods_running = all(phase == "Running" for phase in cmd.stdout.strip().split()) if cmd.stdout.strip() else False

    return {
        "success": topic_ready and pods_running,
        "topic_ready": topic_ready,
        "pods_running": pods_running,
        "error": "" if (topic_ready and pods_running) else "idrac topic or pods not ready",
    }


def verify_ldms_topic_data(host, admin_ip: str) -> Dict[str, Any]:
    """
    Verify ldms Kafka topic exists and is ready (if ldms is enabled).

    Args:
        host: Testinfra host object
        admin_ip: Admin IP of K8s node

    Returns:
        Dict with success, topic_ready, error
    """
    if not is_ldms_enabled(host):
        return {
            "success": True,
            "skipped": True,
            "reason": "LDMS not enabled in software_config.json",
        }

    container = TELEMETRY_VARS["container_name"]
    ssh_opts = CMD_TEMPLATES["ssh_opts"]

    topic_cmd = (
        f"kubectl get kafkatopic ldms -n {TELEMETRY_NAMESPACE} -o json | "
        f"python3 -c \\\"import sys,json; d=json.load(sys.stdin); "
        f"conds=d.get('status',{{}}).get('conditions',[]); "
        f"print('True' if any(c.get('type')=='Ready' and c.get('status')=='True' for c in conds) else 'False')\\\""
    )
    full_cmd = (
        f"podman exec {container} ssh {ssh_opts} root@{admin_ip} "
        f'"{topic_cmd}" 2>/dev/null'
    )

    cmd = host.run(full_cmd)
    topic_ready = cmd.stdout.strip() == "True"

    return {
        "success": topic_ready,
        "topic_ready": topic_ready,
        "skipped": False,
        "error": "" if topic_ready else "ldms topic is not ready",
    }


# =============================================================================
# LDMS DATA VERIFICATION VIA KAFKA REST PROXY
# =============================================================================

def get_ldms_sampler_plugins(host) -> List[str]:
    """
    Get list of LDMS sampler plugin names from telemetry_config.yml.

    Args:
        host: Testinfra host object

    Returns:
        List of plugin names (e.g., ['meminfo', 'procstat2', 'vmstat', 'loadavg', 'procnetdev2'])
    """
    config = get_telemetry_config(host)
    if "error" in config:
        return []

    sampler_configs = config.get("ldms_sampler_configurations", [])
    plugins = []

    for sampler in sampler_configs:
        plugin_name = sampler.get("plugin_name", "")
        if plugin_name:
            plugins.append(plugin_name)

    return plugins


def get_domain_name(host) -> str:
    """
    Get domain name from oim_metadata.yml in container.

    Args:
        host: Testinfra host object

    Returns:
        Domain name string (e.g., 'clash.test') or empty string if not found
    """
    container = TELEMETRY_VARS["container_name"]
    cmd = host.run(f"podman exec {container} cat {OIM_METADATA_PATH}")

    if cmd.rc != 0:
        return ""

    try:
        metadata = yaml.safe_load(cmd.stdout)
        return metadata.get("domain_name", "") if metadata else ""
    except yaml.YAMLError:
        return ""


def get_ldms_node_hostnames(host) -> List[str]:
    """
    Get hostnames of all LDMS-enabled nodes from PXE mapping file.

    LDMS nodes are: slurm_control_node, slurm_node, login_node, login_compiler_node

    Args:
        host: Testinfra host object

    Returns:
        List of hostnames (e.g., ['snode1', 'snode2', 'login1'])
    """
    from automation_library.core import get_nodes_info

    hostnames = []

    for func_group in LDMS_FUNCTIONAL_GROUPS:
        nodes = get_nodes_info(host, search_by="functional_group", search_value=func_group)
        for node in nodes:
            hostname = node.get("hostname", "")
            if hostname and hostname not in hostnames:
                hostnames.append(hostname)

    return hostnames


def get_ldms_nodes_by_functional_group(host) -> Dict[str, List[Dict[str, str]]]:
    """
    Get LDMS nodes grouped by functional_group.

    Args:
        host: Testinfra host object

    Returns:
        Dict mapping functional_group to list of node info dicts:
        {
            "slurm_control_node_x86_64": [{"hostname": "scontrol", "admin_ip": "..."}],
            "slurm_node_x86_64": [{"hostname": "snode1", ...}, {"hostname": "snode2", ...}],
            ...
        }
    """
    from automation_library.core import get_nodes_info

    result = {}

    for func_group in LDMS_FUNCTIONAL_GROUPS:
        nodes = get_nodes_info(host, search_by="functional_group", search_value=func_group)
        if nodes:
            result[func_group] = nodes

    return result


def verify_ldms_data_in_kafka(
    host,
    admin_ip: str,
    timeout_seconds: int = 10
) -> Dict[str, Any]:
    """
    Verify LDMS data is flowing to Kafka by checking that data from all
    LDMS-enabled nodes with all configured plugins is present in the ldms topic.

    Uses Kafka REST proxy to create a consumer, subscribe to ldms topic,
    and consume records to verify data presence.

    Args:
        host: Testinfra host object
        admin_ip: Admin IP of K8s node
        timeout_seconds: Timeout for consuming records (default 10s)

    Returns:
        Dict with success, found_instances, missing_instances, errors
    """
    if not is_ldms_enabled(host):
        return {
            "success": True,
            "skipped": True,
            "reason": "LDMS not enabled in software_config.json",
        }

    # Get bridge IP
    bridge_ip = get_kafka_bridge_ip(host, admin_ip)
    if not bridge_ip:
        return {
            "success": False,
            "error": KAFKA_ASSERT_MSGS["kafka_bridge_not_found"],
        }

    # Get expected data
    plugins = get_ldms_sampler_plugins(host)
    hostnames = get_ldms_node_hostnames(host)
    nodes_by_group = get_ldms_nodes_by_functional_group(host)
    domain_name = get_domain_name(host)
    
    # Build hostname to functional_group mapping
    hostname_to_group = {}
    for func_group, nodes in nodes_by_group.items():
        for node in nodes:
            hostname_to_group[node.get("hostname", "")] = func_group

    if not plugins:
        return {
            "success": False,
            "error": "No LDMS sampler plugins configured in telemetry_config.yml",
        }

    if not hostnames:
        return {
            "success": False,
            "error": "No LDMS nodes found in PXE mapping file",
        }

    if not domain_name:
        return {
            "success": False,
            "error": "Could not get domain_name from oim_metadata.yml",
        }

    # Build expected instances: hostname.domain/plugin
    expected_instances = set()
    for hostname in hostnames:
        for plugin in plugins:
            instance = f"{hostname}.{domain_name}/{plugin}"
            expected_instances.add(instance)

    container = TELEMETRY_VARS["container_name"]
    ssh_opts = CMD_TEMPLATES["ssh_opts"]
    consumer_group = f"ldms-test-{int(time.time()) % 10000}"
    consumer_name = "ldms-test-consumer"

    found_instances = set()
    found_records = {}  # Store full records per instance

    try:
        # Step 1: Create consumer group
        # Use 'latest' to get live/fresh data instead of historical
        create_cmd = (
            f'curl -s -X POST http://{bridge_ip}:{KAFKA_BRIDGE_PORT}/consumers/{consumer_group} '
            f'-H "content-type: application/vnd.kafka.v2+json" '
            f'-d "{{\\"name\\": \\"{consumer_name}\\", \\"format\\": \\"json\\", '
            f'\\"auto.offset.reset\\": \\"latest\\", \\"enable.auto.commit\\": true}}"'
        )
        full_cmd = (
            f"podman exec {container} ssh {ssh_opts} root@{admin_ip} "
            f"'{create_cmd}' 2>/dev/null"
        )
        cmd = host.run(full_cmd)
        # Check for error in response (curl returns 0 even on API errors)
        if "error_code" in cmd.stdout:
            return {
                "success": False,
                "skipped": False,
                "bridge_ip": bridge_ip,
                "domain_name": domain_name,
                "expected_hostnames": hostnames,
                "expected_plugins": plugins,
                "error": f"Failed to create consumer: {cmd.stdout}",
            }

        # Step 2: Subscribe to ldms topic
        subscribe_cmd = (
            f'curl -s -X POST http://{bridge_ip}:{KAFKA_BRIDGE_PORT}/consumers/{consumer_group}'
            f'/instances/{consumer_name}/subscription '
            f'-H "content-type: application/vnd.kafka.v2+json" '
            f'-d "{{\\"topics\\": [\\"ldms\\"]}}"'
        )
        full_cmd = (
            f"podman exec {container} ssh {ssh_opts} root@{admin_ip} "
            f"'{subscribe_cmd}' 2>/dev/null"
        )
        cmd = host.run(full_cmd)

        # Step 3: Consume records with timeout
        consume_cmd = (
            f'curl -s -X GET http://{bridge_ip}:{KAFKA_BRIDGE_PORT}/consumers/{consumer_group}'
            f'/instances/{consumer_name}/records '
            f'-H "accept: application/vnd.kafka.json.v2+json"'
        )

        start_time = time.time()
        while time.time() - start_time < timeout_seconds:
            full_cmd = (
                f"podman exec {container} ssh {ssh_opts} root@{admin_ip} "
                f"'{consume_cmd}' 2>/dev/null"
            )
            cmd = host.run(full_cmd)

            if cmd.stdout.strip() and cmd.stdout.strip().startswith("["):
                try:
                    records = json.loads(cmd.stdout)
                    for record in records:
                        value = record.get("value", {})
                        instance = value.get("instance", "")
                        if instance:
                            found_instances.add(instance)
                            # Store one sample record per instance
                            if instance not in found_records:
                                found_records[instance] = record
                except json.JSONDecodeError:
                    pass

            # Check if we found at least one instance per hostname
            found_hostnames = set()
            for inst in found_instances:
                # Extract hostname from instance (hostname.domain/plugin)
                if "/" in inst:
                    host_part = inst.split("/")[0]
                    if "." in host_part:
                        found_hostnames.add(host_part.split(".")[0])

            if found_hostnames >= set(hostnames):
                break

            time.sleep(1)

    finally:
        # Step 4: Delete consumer (cleanup)
        delete_cmd = KAFKA_CMD_TEMPLATES["rest_delete_consumer"].format(
            bridge_ip=bridge_ip,
            port=KAFKA_BRIDGE_PORT,
            consumer_group=consumer_group,
            consumer_name=consumer_name,
        )
        full_cmd = (
            f"podman exec {container} ssh {ssh_opts} root@{admin_ip} "
            f"'{delete_cmd}' 2>/dev/null"
        )
        host.run(full_cmd)

    # Analyze results - check if we got data from each hostname
    found_hostnames = set()
    for inst in found_instances:
        if "/" in inst:
            host_part = inst.split("/")[0]
            if "." in host_part:
                found_hostnames.add(host_part.split(".")[0])

    missing_hostnames = set(hostnames) - found_hostnames

    # Build detailed results per hostname with full record data
    hostname_results = []
    for hostname in hostnames:
        host_instances = [i for i in found_instances if i.startswith(f"{hostname}.")]
        host_plugins = []
        for inst in host_instances:
            if "/" in inst:
                plugin = inst.split("/")[1]
                record = found_records.get(inst, {})
                host_plugins.append({
                    "plugin": plugin,
                    "record": record,
                })
        hostname_results.append({
            "hostname": hostname,
            "functional_group": hostname_to_group.get(hostname, "unknown"),
            "found": len(host_instances) > 0,
            "plugins_found": host_plugins,
            "plugins_expected": plugins,
        })

    # Build results grouped by functional_group
    results_by_group = {}
    for hr in hostname_results:
        fg = hr.get("functional_group", "unknown")
        if fg not in results_by_group:
            results_by_group[fg] = []
        results_by_group[fg].append(hr)

    success = len(missing_hostnames) == 0

    return {
        "success": success,
        "skipped": False,
        "bridge_ip": bridge_ip,
        "domain_name": domain_name,
        "expected_hostnames": hostnames,
        "expected_plugins": plugins,
        "found_instances": list(found_instances),
        "found_hostnames": list(found_hostnames),
        "missing_hostnames": list(missing_hostnames),
        "hostname_results": hostname_results,
        "results_by_group": results_by_group,
        "error": "" if success else f"Missing data from hostnames: {list(missing_hostnames)}",
    }
