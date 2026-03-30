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

from ...core import run_in_container
from ...core.host import run_on_remote_node
from ..vars.shared_vars import TELEMETRY_NAMESPACE
from ..messages.kafka_msgs import KAFKA_ASSERT_MSGS
from ..vars.kafka_vars import (
    KAFKA_CMD_TEMPLATES,
    LDMS_AGGR_POD_PREFIX,
    LDMS_STORE_POD_PREFIX,
    KAFKA_BRIDGE_SERVICE,
    KAFKA_BRIDGE_PORT,
    LDMS_FUNCTIONAL_GROUPS,
    OIM_METADATA_PATH,
)
from .shared_func import (
    get_telemetry_config,
    is_ldms_enabled,
)


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
    kubectl_cmd = KAFKA_CMD_TEMPLATES["get_kafka_cluster"].format(namespace=TELEMETRY_NAMESPACE)
    cmd = run_on_remote_node(host, kubectl_cmd, admin_ip)
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
    kubectl_cmd = KAFKA_CMD_TEMPLATES["get_bridge_lb_ip"].format(
        service=KAFKA_BRIDGE_SERVICE,
        namespace=TELEMETRY_NAMESPACE
    )
    cmd = run_on_remote_node(host, kubectl_cmd, admin_ip)
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
    curl_cmd = KAFKA_CMD_TEMPLATES["rest_list_topics"].format(
        bridge_ip=bridge_ip,
        port=KAFKA_BRIDGE_PORT
    )
    cmd = run_on_remote_node(host, curl_cmd, admin_ip)
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

    # Get pods in telemetry namespace
    kubectl_cmd = KAFKA_CMD_TEMPLATES["get_pods"].format(namespace=TELEMETRY_NAMESPACE)
    cmd = run_on_remote_node(host, kubectl_cmd, admin_ip)
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

    # Get services in telemetry namespace
    kubectl_cmd = KAFKA_CMD_TEMPLATES["get_services"].format(namespace=TELEMETRY_NAMESPACE)
    cmd = run_on_remote_node(host, kubectl_cmd, admin_ip)
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
                errors.append(
                    f"Service {svc_name} port mismatch: "
                    f"expected {expected_agg_port}, actual {actual_port}"
                )
    else:
        errors.append("No LDMS aggregator service found")

    # Find nersc-ldms-store service
    store_services = [
        s for s in services
        if "ldms-store" in s.get("metadata", {}).get("name", "").lower()
    ]
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
                errors.append(
                    f"Service {svc_name} port mismatch: "
                    f"expected {expected_store_port}, actual {actual_port}"
                )
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

def verify_idrac_data_in_kafka(
    host, admin_ip: str, timeout_seconds: int = 30
) -> Dict[str, Any]:
    """
    Verify iDRAC telemetry data is flowing to Kafka idrac topic.

    Gets activated IPs from MySQL, uses Redfish to get service tags,
    then consumes data from Kafka and verifies service tags are present.
    Waits up to timeout_seconds for metrics with actual values to arrive.

    Args:
        host: Testinfra host object
        admin_ip: Admin IP of K8s node
        timeout_seconds: Timeout for consuming records (default 30s)

    Returns:
        Dict with success, service_tag_results, found_tags, missing_tags
    """
    from .idrac_telemetry_func import get_activated_ips
    from .shared_func import is_kafka_enabled, get_ip_to_service_tag_mapping

    # Check if Kafka is enabled
    if not is_kafka_enabled(host):
        return {
            "success": True,
            "skipped": True,
            "reason": KAFKA_ASSERT_MSGS["idrac_kafka_not_enabled"],
        }

    # Get bridge IP
    bridge_ip = get_kafka_bridge_ip(host, admin_ip)
    if not bridge_ip:
        return {
            "success": False,
            "error": KAFKA_ASSERT_MSGS["kafka_bridge_not_found"],
        }

    # Get activated IPs from telemetry report
    activated_ips = get_activated_ips(host)
    if not activated_ips:
        return {
            "success": True,
            "skipped": True,
            "reason": KAFKA_ASSERT_MSGS["idrac_kafka_no_activated_ips"],
        }

    # Get IP to service tag mapping (uses cache)
    ip_to_service_tag = get_ip_to_service_tag_mapping(host, admin_ip, activated_ips)

    if not ip_to_service_tag:
        return {
            "success": False,
            "error": KAFKA_ASSERT_MSGS["idrac_kafka_redfish_failed"],
            "activated_ips": activated_ips,
        }

    expected_service_tags = set(ip_to_service_tag.values())

    consumer_group = f"idrac-test-{int(time.time()) % 10000}"
    consumer_name = "idrac-test-consumer"

    found_service_tags = set()
    service_tag_records = {}  # Store sample records per service tag
    service_tag_has_values = set()  # Tags that have at least 1 metric with a value

    try:
        # Step 1: Create consumer group with 'latest' offset to get live data
        create_cmd = (
            f'curl -s -X POST http://{bridge_ip}:{KAFKA_BRIDGE_PORT}/consumers/{consumer_group} '
            f'-H "content-type: application/vnd.kafka.v2+json" '
            f'-d \'{{"name": "{consumer_name}", "format": "json", '
            f'"auto.offset.reset": "latest", "enable.auto.commit": true}}\''
        )
        cmd = run_on_remote_node(host, create_cmd, admin_ip)
        if "error_code" in cmd.stdout:
            return {
                "success": False,
                "bridge_ip": bridge_ip,
                "error": KAFKA_ASSERT_MSGS["idrac_kafka_consumer_failed"].format(
                    error=cmd.stdout
                ),
            }

        # Step 2: Subscribe to idrac topic
        subscribe_cmd = (
            f'curl -s -X POST http://{bridge_ip}:{KAFKA_BRIDGE_PORT}/consumers/{consumer_group}'
            f'/instances/{consumer_name}/subscription '
            f'-H "content-type: application/vnd.kafka.v2+json" '
            f'-d \'{{"topics": ["idrac"]}}\''
        )
        run_on_remote_node(host, subscribe_cmd, admin_ip)

        # Step 3: Consume records with multiple attempts
        # Each attempt fetches a batch of records
        consume_cmd = (
            f'curl -s -X GET http://{bridge_ip}:{KAFKA_BRIDGE_PORT}/consumers/{consumer_group}'
            f'/instances/{consumer_name}/records '
            f'-H "accept: application/vnd.kafka.json.v2+json"'
        )

        max_attempts = timeout_seconds // 2  # 2 seconds per attempt
        for _ in range(max_attempts):
            cmd = run_on_remote_node(host, consume_cmd, admin_ip)

            if cmd.stdout.strip() and cmd.stdout.strip().startswith("["):
                try:
                    records = json.loads(cmd.stdout)
                    for record in records:
                        value = record.get("value", {})
                        # iDRAC Kafka data structure:
                        # value is a list of items with: host (ServiceTag), time, event, fields
                        # fields contains: metric_name, _value
                        if isinstance(value, list):
                            for item in value:
                                if isinstance(item, dict):
                                    # 'host' field contains the ServiceTag
                                    service_tag = item.get("host", "")
                                    if service_tag and service_tag in expected_service_tags:
                                        found_service_tags.add(service_tag)
                                        if service_tag not in service_tag_records:
                                            # Extract Kafka timestamp from record
                                            kafka_timestamp = item.get("time", "")
                                            service_tag_records[service_tag] = {
                                                "record": record,
                                                "sample_metrics": [],
                                                "kafka_timestamp": kafka_timestamp,
                                            }
                                        # Extract metric from fields
                                        fields = item.get("fields", {})
                                        metric_name = fields.get("metric_name", "")
                                        # _value can be 0, None, or missing - use sentinel
                                        metric_value = fields.get("_value")
                                        if metric_value is None:
                                            metric_value = fields.get("value")
                                        # Only collect metrics that have actual values
                                        has_value = metric_value is not None and str(metric_value).strip() != ""
                                        if metric_name and len(service_tag_records[service_tag]["sample_metrics"]) < 5:
                                            # Avoid duplicate metrics, prefer ones with values
                                            existing = [m["metric_name"] for m in service_tag_records[service_tag]["sample_metrics"]]
                                            if metric_name not in existing:
                                                if has_value:
                                                    service_tag_records[service_tag]["sample_metrics"].append({
                                                        "metric_name": metric_name,
                                                        "value": metric_value,
                                                    })
                                                    service_tag_has_values.add(service_tag)
                                            elif has_value:
                                                # Update existing entry if it had no value
                                                for m in service_tag_records[service_tag]["sample_metrics"]:
                                                    if m["metric_name"] == metric_name and (m["value"] is None or str(m["value"]).strip() == ""):
                                                        m["value"] = metric_value
                                                        service_tag_has_values.add(service_tag)
                                                        break
                                        # Update timestamp if we get a newer one
                                        latest_ts = item.get("time", "")
                                        if latest_ts:
                                            service_tag_records[service_tag]["kafka_timestamp"] = latest_ts
                except json.JSONDecodeError:
                    pass

            # Break only when ALL service tags have at least 1 metric with value
            if service_tag_has_values >= expected_service_tags:
                break

            time.sleep(2)

    finally:
        # Step 4: Delete consumer (cleanup)
        delete_cmd = KAFKA_CMD_TEMPLATES["rest_delete_consumer"].format(
            bridge_ip=bridge_ip,
            port=KAFKA_BRIDGE_PORT,
            consumer_group=consumer_group,
            consumer_name=consumer_name,
        )
        run_on_remote_node(host, delete_cmd, admin_ip)

    # Build results
    missing_tags = expected_service_tags - found_service_tags
    service_tag_results = []

    for ip, service_tag in ip_to_service_tag.items():
        found = service_tag in found_service_tags
        record_data = service_tag_records.get(service_tag, {})
        service_tag_results.append({
            "ip": ip,
            "service_tag": service_tag,
            "found": found,
            "has_values": service_tag in service_tag_has_values,
            "sample_metrics": record_data.get("sample_metrics", []),
            "kafka_timestamp": record_data.get("kafka_timestamp", ""),
        })

    # Determine error message
    # A service tag is only considered successful if it has actual metric values
    tags_without_values = found_service_tags - service_tag_has_values
    all_have_values = len(tags_without_values) == 0 and len(missing_tags) == 0

    if all_have_values:
        error_msg = ""
    elif len(found_service_tags) == 0:
        error_msg = KAFKA_ASSERT_MSGS["idrac_kafka_no_data"].format(
            expected=list(expected_service_tags)
        )
    elif len(tags_without_values) > 0:
        error_msg = f"Service tags found but no metric values: {list(tags_without_values)}"
    else:
        error_msg = KAFKA_ASSERT_MSGS["idrac_kafka_data_missing"].format(
            missing=list(missing_tags),
            found=list(found_service_tags)
        )

    return {
        "success": all_have_values,
        "skipped": False,
        "bridge_ip": bridge_ip,
        "activated_ips": activated_ips,
        "ip_to_service_tag": ip_to_service_tag,
        "service_tag_results": service_tag_results,
        "found_tags": list(found_service_tags),
        "missing_tags": list(missing_tags),
        "error": error_msg,
    }


def verify_ldms_topic_ready(host, admin_ip: str) -> Dict[str, Any]:
    """
    Verify ldms Kafka topic exists and is ready (if ldms is enabled).

    Note: This is a quick check. For actual data verification,
    use verify_ldms_data_in_kafka() instead.

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

    topic_cmd = (
        f"kubectl get kafkatopic ldms -n {TELEMETRY_NAMESPACE} -o json | "
        f'python3 -c \'import sys,json; d=json.load(sys.stdin); '
        f'conds=d.get("status",{{}}).get("conditions",[]);'
        f' print("True" if any(c.get("type")=="Ready" and c.get("status")=="True" for c in conds) else "False")\''
    )
    cmd = run_on_remote_node(host, topic_cmd, admin_ip)
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
    cmd = run_in_container(host, f"cat {OIM_METADATA_PATH}")

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
    timeout_seconds: int = 30
) -> Dict[str, Any]:
    """
    Verify LDMS data is flowing to Kafka by checking that data from all
    LDMS-enabled nodes with ALL configured plugins is present in the ldms topic.

    Reads ldms_sampler_configurations from telemetry_config.yml to know which
    plugin metrics (e.g., meminfo, procstat2, vmstat) should be collected.
    Waits up to timeout_seconds for all hostname×plugin combinations to arrive.

    Uses Kafka REST proxy to create a consumer, subscribe to ldms topic,
    and consume records to verify data presence.

    Args:
        host: Testinfra host object
        admin_ip: Admin IP of K8s node
        timeout_seconds: Timeout for consuming records (default 30s)

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

    # Build expected instances: hostname.domain/plugin (ALL combinations)
    expected_instances = set()
    for hostname in hostnames:
        for plugin in plugins:
            instance = f"{hostname}.{domain_name}/{plugin}"
            expected_instances.add(instance)

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
            f'-d \'{{"name": "{consumer_name}", "format": "json", '
            f'"auto.offset.reset": "latest", "enable.auto.commit": true}}\''
        )
        cmd = run_on_remote_node(host, create_cmd, admin_ip)
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
            f'-d \'{{"topics": ["ldms"]}}\''
        )
        run_on_remote_node(host, subscribe_cmd, admin_ip)

        # Step 3: Consume records with timeout
        # Wait until ALL expected instances (hostname×plugin) are found
        consume_cmd = (
            f'curl -s -X GET http://{bridge_ip}:{KAFKA_BRIDGE_PORT}/consumers/{consumer_group}'
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
                        if instance:
                            found_instances.add(instance)
                            # Store one sample record per instance
                            if instance not in found_records:
                                found_records[instance] = record
                except json.JSONDecodeError:
                    pass

            # Break only when ALL expected instances are found
            if found_instances >= expected_instances:
                break

            time.sleep(2)

    finally:
        # Step 4: Delete consumer (cleanup)
        delete_cmd = KAFKA_CMD_TEMPLATES["rest_delete_consumer"].format(
            bridge_ip=bridge_ip,
            port=KAFKA_BRIDGE_PORT,
            consumer_group=consumer_group,
            consumer_name=consumer_name,
        )
        run_on_remote_node(host, delete_cmd, admin_ip)

    # Analyze results - check ALL instances (hostname×plugin)
    missing_instances = expected_instances - found_instances

    # Also compute per-hostname summary
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
        host_plugins_found = []
        host_plugins_missing = []
        for plugin in plugins:
            expected_inst = f"{hostname}.{domain_name}/{plugin}"
            record = found_records.get(expected_inst, {})
            if expected_inst in found_instances:
                host_plugins_found.append({
                    "plugin": plugin,
                    "record": record,
                })
            else:
                host_plugins_missing.append(plugin)

        hostname_results.append({
            "hostname": hostname,
            "functional_group": hostname_to_group.get(hostname, "unknown"),
            "found": len(host_plugins_found) > 0,
            "all_plugins_found": len(host_plugins_missing) == 0,
            "plugins_found": host_plugins_found,
            "plugins_missing": host_plugins_missing,
            "plugins_expected": plugins,
        })

    # Build results grouped by functional_group
    results_by_group = {}
    for hr in hostname_results:
        fg = hr.get("functional_group", "unknown")
        if fg not in results_by_group:
            results_by_group[fg] = []
        results_by_group[fg].append(hr)

    # Success = ALL expected instances found (every hostname × every plugin)
    success = len(missing_instances) == 0

    # Build error message
    if success:
        error_msg = ""
    elif missing_hostnames:
        error_msg = f"Missing data from hostnames: {list(missing_hostnames)}"
    else:
        # All hostnames have some data but missing some plugins
        missing_details = []
        for hr in hostname_results:
            if hr.get("plugins_missing"):
                missing_details.append(
                    f"{hr['hostname']}: missing plugins {hr['plugins_missing']}"
                )
        error_msg = f"Missing plugins: {'; '.join(missing_details)}"

    return {
        "success": success,
        "skipped": False,
        "bridge_ip": bridge_ip,
        "domain_name": domain_name,
        "expected_hostnames": hostnames,
        "expected_plugins": plugins,
        "expected_instance_count": len(expected_instances),
        "found_instances": list(found_instances),
        "found_instance_count": len(found_instances),
        "missing_instances": list(missing_instances),
        "found_hostnames": list(found_hostnames),
        "missing_hostnames": list(missing_hostnames),
        "hostname_results": hostname_results,
        "results_by_group": results_by_group,
        "error": error_msg,
    }
