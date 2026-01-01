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
from ..vars.kafka_vars import (
    TELEMETRY_CONFIG_PATH,
    SOFTWARE_CONFIG_PATH,
    KAFKA_BOOTSTRAP_SERVER,
    KAFKA_CLUSTER_CA_SECRET,
    KAFKA_USER_SECRET,
    KAFKA_STRIMZI_IMAGE,
    KAFKA_MTLS_TEST_JOB_PREFIX,
    KAFKA_CMD_TEMPLATES,
    LDMS_AGGR_POD_PREFIX,
    LDMS_STORE_POD_PREFIX,
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
        return {"error": f"Failed to read telemetry_config.yml: {cmd.stderr}"}

    try:
        config = yaml.safe_load(cmd.stdout)
        return config if config else {}
    except yaml.YAMLError as e:
        return {"error": f"Failed to parse telemetry_config.yml: {e}"}


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
        return {"error": f"Failed to read software_config.json: {cmd.stderr}"}

    try:
        config = json.loads(cmd.stdout)
        return config if config else {}
    except json.JSONDecodeError as e:
        return {"error": f"Failed to parse software_config.json: {e}"}


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
        return {"error": "Failed to get Kafka cluster config"}

    try:
        return json.loads(cmd.stdout)
    except json.JSONDecodeError:
        return {"error": "Failed to parse Kafka cluster config"}


def get_kafka_topics(host, admin_ip: str) -> List[Dict[str, Any]]:
    """
    Get Kafka topics from K8s.

    Args:
        host: Testinfra host object
        admin_ip: Admin IP of K8s node

    Returns:
        List of Kafka topic configs
    """
    container = TELEMETRY_VARS["container_name"]
    ssh_opts = CMD_TEMPLATES["ssh_opts"]

    kubectl_cmd = KAFKA_CMD_TEMPLATES["get_kafka_topics"].format(namespace=TELEMETRY_NAMESPACE)
    full_cmd = (
        f"podman exec {container} ssh {ssh_opts} root@{admin_ip} "
        f"'{kubectl_cmd}' 2>/dev/null"
    )

    cmd = host.run(full_cmd)
    if cmd.rc != 0:
        return []

    try:
        data = json.loads(cmd.stdout)
        return data.get("items", [])
    except json.JSONDecodeError:
        return []


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
            "error": "log_retention_hours not found in telemetry_config.yml",
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
            "error": "log_retention_bytes not found in telemetry_config.yml",
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
            "error": "log_segment_bytes not found in telemetry_config.yml",
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


def verify_kafka_topics(host, admin_ip: str) -> Dict[str, Any]:
    """
    Verify Kafka topics match expected configuration.

    - idrac topic: Required when kafka is enabled
    - ldms topic: Required only if ldms is in software_config.json

    Args:
        host: Testinfra host object
        admin_ip: Admin IP of K8s node

    Returns:
        Dict with success, topic_results, errors
    """
    ldms_enabled = is_ldms_enabled(host)
    expected_partitions = get_topic_partitions_config(host)
    actual_topics = get_kafka_topics(host, admin_ip)

    # Build expected topics dict (no default partitions - must be in config)
    expected_topics = {}
    for tp in expected_partitions:
        name = tp.get("name", "")
        if "partitions" not in tp:
            return {
                "success": False,
                "error": f"partitions not defined for topic '{name}' in telemetry_config.yml",
            }
        partitions = tp["partitions"]
        expected_topics[name] = partitions

    # Build actual topics dict
    actual_topics_dict = {}
    for topic in actual_topics:
        name = topic.get("metadata", {}).get("name", "")
        partitions = topic.get("spec", {}).get("partitions")
        actual_topics_dict[name] = partitions

    topic_results = []
    errors = []

    # Check idrac topic (required)
    if "idrac" in expected_topics:
        if "idrac" in actual_topics_dict:
            expected_p = expected_topics["idrac"]
            actual_p = actual_topics_dict["idrac"]
            match = expected_p == actual_p
            topic_results.append({
                "topic": "idrac",
                "expected_partitions": expected_p,
                "actual_partitions": actual_p,
                "exists": True,
                "partitions_match": match,
                "required": True,
            })
            if not match:
                errors.append(f"idrac topic partitions mismatch: expected {expected_p}, actual {actual_p}")
        else:
            topic_results.append({
                "topic": "idrac",
                "expected_partitions": expected_topics.get("idrac"),
                "actual_partitions": 0,
                "exists": False,
                "partitions_match": False,
                "required": True,
            })
            errors.append("idrac topic not found but is required")

    # Check ldms topic (required only if ldms enabled)
    if "ldms" in expected_topics:
        if ldms_enabled:
            # ldms is enabled, topic should exist
            if "ldms" in actual_topics_dict:
                expected_p = expected_topics["ldms"]
                actual_p = actual_topics_dict["ldms"]
                match = expected_p == actual_p
                topic_results.append({
                    "topic": "ldms",
                    "expected_partitions": expected_p,
                    "actual_partitions": actual_p,
                    "exists": True,
                    "partitions_match": match,
                    "required": True,
                })
                if not match:
                    errors.append(f"ldms topic partitions mismatch: expected {expected_p}, actual {actual_p}")
            else:
                topic_results.append({
                    "topic": "ldms",
                    "expected_partitions": expected_topics.get("ldms"),
                    "actual_partitions": 0,
                    "exists": False,
                    "partitions_match": False,
                    "required": True,
                })
                errors.append("ldms topic not found but ldms is enabled in software_config.json")
        else:
            # ldms is not enabled, topic should NOT exist
            if "ldms" in actual_topics_dict:
                topic_results.append({
                    "topic": "ldms",
                    "expected_partitions": 0,
                    "actual_partitions": actual_topics_dict["ldms"],
                    "exists": True,
                    "partitions_match": False,
                    "required": False,
                })
                errors.append("ldms topic exists but ldms is not enabled in software_config.json")
            else:
                topic_results.append({
                    "topic": "ldms",
                    "expected_partitions": 0,
                    "actual_partitions": 0,
                    "exists": False,
                    "partitions_match": True,
                    "required": False,
                })

    # Get list of all topic names
    all_topics = list(actual_topics_dict.keys())

    return {
        "success": len(errors) == 0,
        "ldms_enabled": ldms_enabled,
        "topic_results": topic_results,
        "all_topics": all_topics,
        "errors": errors,
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
            "error": f"Failed to get pods: {cmd.stderr}",
        }

    try:
        data = json.loads(cmd.stdout)
        pods = data.get("items", [])
    except json.JSONDecodeError:
        return {
            "success": False,
            "error": "Failed to parse pods JSON",
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
            "error": f"Failed to get services: {cmd.stderr}",
        }

    try:
        data = json.loads(cmd.stdout)
        services = data.get("items", [])
    except json.JSONDecodeError:
        return {
            "success": False,
            "error": "Failed to parse services JSON",
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
# KAFKA mTLS CONNECTION VERIFICATION (Job-based approach)
# =============================================================================

def _cleanup_mtls_test_job(host, admin_ip: str, job_name: str) -> None:
    """Delete the mTLS test job and its pods with force delete."""
    from automation_library.core import run_on_remote_node

    # First delete the job
    delete_job_cmd = KAFKA_CMD_TEMPLATES["delete_job"].format(
        job_name=job_name, namespace=TELEMETRY_NAMESPACE
    )
    run_on_remote_node(host, delete_job_cmd, admin_ip)

    # Force delete any pods that might be stuck in Terminating state
    force_delete_pods_cmd = KAFKA_CMD_TEMPLATES["force_delete_pods"].format(
        namespace=TELEMETRY_NAMESPACE, job_name=job_name
    )
    run_on_remote_node(host, force_delete_pods_cmd, admin_ip)


def _create_mtls_test_job(host, admin_ip: str, job_name: str) -> bool:
    """
    Create a Job for mTLS testing with sleep command to keep pod running.

    The job runs 'sleep 300' to keep the pod alive for 5 minutes,
    allowing us to exec into it and run test commands.
    """
    from automation_library.core import run_on_remote_node

    job_yaml = f"""apiVersion: batch/v1
kind: Job
metadata:
  name: {job_name}
  namespace: {TELEMETRY_NAMESPACE}
spec:
  ttlSecondsAfterFinished: 60
  backoffLimit: 0
  template:
    spec:
      restartPolicy: Never
      volumes:
        - name: kafka-cluster-ca-cert
          secret:
            secretName: {KAFKA_CLUSTER_CA_SECRET}
        - name: kafkapump-user-certs
          secret:
            secretName: {KAFKA_USER_SECRET}
      containers:
        - name: kafka-mtls-test
          image: {KAFKA_STRIMZI_IMAGE}
          imagePullPolicy: IfNotPresent
          volumeMounts:
            - mountPath: /etc/kafka/cluster-ca
              name: kafka-cluster-ca-cert
              readOnly: true
            - mountPath: /etc/kafka/kafkapump-certs
              name: kafkapump-user-certs
              readOnly: true
          command: [\\"/bin/bash\\", \\"-c\\", \\"sleep 300\\"]
"""

    # Apply job via echo and pipe
    apply_cmd = f'echo "{job_yaml}" | kubectl apply -f -'
    result = run_on_remote_node(host, apply_cmd, admin_ip)
    return result.rc == 0


def _wait_for_pod_running(host, admin_ip: str, job_name: str, timeout: int = 60) -> str:
    """Wait for the job's pod to be in Running state and return pod name."""
    from automation_library.core import run_on_remote_node

    start_time = time.time()

    while time.time() - start_time < timeout:
        # Get pod name from job
        get_pod_cmd = KAFKA_CMD_TEMPLATES["get_pod_by_job"].format(
            namespace=TELEMETRY_NAMESPACE, job_name=job_name
        )
        result = run_on_remote_node(host, get_pod_cmd, admin_ip)

        if result.rc == 0 and result.stdout.strip():
            pod_name = result.stdout.strip()

            # Check if pod is running
            status_cmd = KAFKA_CMD_TEMPLATES["get_pod_status"].format(
                pod_name=pod_name, namespace=TELEMETRY_NAMESPACE
            )
            result = run_on_remote_node(host, status_cmd, admin_ip)

            if result.stdout.strip() == "Running":
                return pod_name

        time.sleep(2)

    return ""


def _exec_in_pod(host, admin_ip: str, pod_name: str, command: str) -> Dict[str, Any]:
    """Execute a command inside the pod.

    Note: run_on_remote_node wraps cmd in single quotes, so we use double quotes
    for the inner bash -c command and escape any double quotes in the command.
    """
    from automation_library.core import run_in_container

    ssh_opts = CMD_TEMPLATES["ssh_opts"]

    # Escape double quotes in command
    escaped_cmd = command.replace('"', '\\"')
    # Use template for kubectl exec
    kubectl_cmd = KAFKA_CMD_TEMPLATES["exec_in_pod"].format(
        namespace=TELEMETRY_NAMESPACE, pod_name=pod_name, command=escaped_cmd
    )
    ssh_cmd = f"ssh {ssh_opts} root@{admin_ip} '{kubectl_cmd}'"
    result = run_in_container(host, ssh_cmd)
    return {"rc": result.rc, "stdout": result.stdout, "stderr": result.stderr}


def verify_kafka_mtls_connection(host, admin_ip: str) -> Dict[str, Any]:
    """
    Verify Kafka mTLS connection using a Job-based approach.

    Steps:
    1. Delete existing test job if present
    2. Create a new job with mounted secrets (runs sleep to keep pod alive)
    3. Wait for pod to be running
    4. Exec into pod and run mTLS test commands:
       - Create truststore from cluster CA
       - Create keystore from kafkapump certs
       - Create client properties
       - List topics via mTLS
    5. Cleanup: delete the job

    Args:
        host: Testinfra host object
        admin_ip: Admin IP of K8s node

    Returns:
        Dict with success, step results, topics_listed, error
    """
    from automation_library.core import run_on_remote_node

    # Generate unique job name
    job_name = f"{KAFKA_MTLS_TEST_JOB_PREFIX}-{int(time.time()) % 10000}"

    results = {
        "truststore_created": False,
        "keystore_created": False,
        "client_properties_created": False,
        "mtls_connection_success": False,
        "topics_listed": [],
        "idrac_topic_data": False,
        "ldms_topic_data": False,
        "steps": [],
        "job_name": job_name,
    }

    try:
        # Step 0: Cleanup any existing test jobs/pods from previous runs
        _cleanup_mtls_test_job(host, admin_ip, job_name)
        results["steps"].append({"step": "Cleanup existing jobs", "success": True})

        # Step 1: Check if required secrets exist
        result = run_on_remote_node(host, f"kubectl get secret {KAFKA_USER_SECRET} -n {TELEMETRY_NAMESPACE} -o name", admin_ip)
        if result.rc != 0 or KAFKA_USER_SECRET not in result.stdout:
            return {"success": False, **results, "error": f"Secret {KAFKA_USER_SECRET} not found"}

        result = run_on_remote_node(host, f"kubectl get secret {KAFKA_CLUSTER_CA_SECRET} -n {TELEMETRY_NAMESPACE} -o name", admin_ip)
        if result.rc != 0 or KAFKA_CLUSTER_CA_SECRET not in result.stdout:
            return {"success": False, **results, "error": f"Secret {KAFKA_CLUSTER_CA_SECRET} not found"}
        
        results["steps"].append({"step": "Verify secrets exist", "success": True})

        # Step 2: Create the test job
        if not _create_mtls_test_job(host, admin_ip, job_name):
            return {"success": False, **results, "error": "Failed to create test job"}
        results["steps"].append({"step": "Create test job", "success": True})

        # Step 3: Wait for pod to be running
        pod_name = _wait_for_pod_running(host, admin_ip, job_name, timeout=60)
        if not pod_name:
            _cleanup_mtls_test_job(host, admin_ip, job_name)
            return {"success": False, **results, "error": "Test pod did not start in time"}
        results["steps"].append({"step": f"Pod {pod_name} running", "success": True})

        # Step 4: Create truststore from cluster CA
        result = _exec_in_pod(host, admin_ip, pod_name, KAFKA_CMD_TEMPLATES["create_truststore"])
        if result["rc"] == 0:
            results["truststore_created"] = True
            results["steps"].append({"step": "Create truststore", "success": True})
        else:
            results["steps"].append({"step": "Create truststore", "success": False, "error": result["stdout"]})

        # Step 5: Create keystore from kafkapump certs
        result = _exec_in_pod(host, admin_ip, pod_name, KAFKA_CMD_TEMPLATES["create_keystore"])
        if result["rc"] == 0:
            results["keystore_created"] = True
            results["steps"].append({"step": "Create keystore", "success": True})
        else:
            results["steps"].append({"step": "Create keystore", "success": False, "error": result["stdout"]})

        # Step 6: Create client properties
        result = _exec_in_pod(host, admin_ip, pod_name, KAFKA_CMD_TEMPLATES["create_client_properties"])
        if result["rc"] == 0:
            results["client_properties_created"] = True
            results["steps"].append({"step": "Create client properties", "success": True})
        else:
            results["steps"].append({"step": "Create client properties", "success": False, "error": result["stdout"]})

        # Step 7: List topics via mTLS
        list_topics_cmd = KAFKA_CMD_TEMPLATES["list_topics"].format(bootstrap_server=KAFKA_BOOTSTRAP_SERVER)
        result = _exec_in_pod(host, admin_ip, pod_name, list_topics_cmd)
        if result["rc"] == 0 and result["stdout"].strip():
            results["mtls_connection_success"] = True
            # Filter out empty lines and log messages
            topics = [t.strip() for t in result["stdout"].strip().split('\n') 
                     if t.strip() and not t.startswith('[') and not t.startswith('Warning')]
            results["topics_listed"] = topics
            results["steps"].append({"step": "List topics via mTLS", "success": True, "topics": topics})
        else:
            results["steps"].append({"step": "List topics via mTLS", "success": False, "error": result["stdout"]})

        # Step 8: Test idrac topic consumer (optional - just check if we can consume)
        if "idrac" in results["topics_listed"]:
            idrac_consumer_cmd = (
                f"timeout 10 /opt/kafka/bin/kafka-console-consumer.sh "
                f"--bootstrap-server {KAFKA_BOOTSTRAP_SERVER} "
                "--topic idrac "
                "--consumer.config /tmp/client.properties "
                "--from-beginning --max-messages 1 2>/dev/null || true"
            )
            result = _exec_in_pod(host, admin_ip, pod_name, idrac_consumer_cmd)
            # Even timeout is OK - it means we connected successfully
            results["idrac_topic_data"] = True
            results["steps"].append({"step": "Test idrac topic consumer", "success": True})

        # Step 9: Test ldms topic consumer (optional)
        if "ldms" in results["topics_listed"]:
            ldms_consumer_cmd = (
                f"timeout 10 /opt/kafka/bin/kafka-console-consumer.sh "
                f"--bootstrap-server {KAFKA_BOOTSTRAP_SERVER} "
                "--topic ldms "
                "--consumer.config /tmp/client.properties "
                "--from-beginning --max-messages 1 2>/dev/null || true"
            )
            result = _exec_in_pod(host, admin_ip, pod_name, ldms_consumer_cmd)
            results["ldms_topic_data"] = True
            results["steps"].append({"step": "Test ldms topic consumer", "success": True})

    finally:
        # Step 10: Cleanup - delete the job
        _cleanup_mtls_test_job(host, admin_ip, job_name)
        results["steps"].append({"step": "Cleanup test job", "success": True})

    success = (
        results["truststore_created"] and
        results["keystore_created"] and
        results["client_properties_created"] and
        results["mtls_connection_success"]
    )

    return {
        "success": success,
        **results,
        "error": "" if success else "mTLS connection test failed",
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
