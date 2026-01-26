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
Telemetry Kafka Test Cases.

This module contains pytest test cases for verifying Kafka configuration
and connectivity in the telemetry namespace.

Test cases:
1. Verify LDMS pods running (if ldms enabled)
2. Verify LDMS services ports match telemetry_config.yml (if ldms enabled)
3. Verify Kafka mTLS connection
4. Verify Kafka topics configuration
5. Verify Kafka configurations match telemetry_config.yml (inside pod)
6. Verify data flowing to idrac topic
7. Verify data flowing to ldms topic (if ldms enabled)

Note: Kafka tests skip if kafka is not in idrac_telemetry_collection_type.
      LDMS tests skip if ldms is not in software_config.json.
"""

import pytest

from automation_library.core import (
    TestLogger,
    get_node_info,
)
from automation_library.telemetry.vars import (
    K8S_CONTROL_PLANE_FUNCTIONAL_GROUP,
)
from automation_library.telemetry.messages import (
    TEST_NAMES,
    TEST_LOG_MSGS as LOG_MSGS,
    TEST_ASSERT_MSGS as ASSERT_MSGS,
)
from automation_library.telemetry.functions.telemetry_func import (
    is_kafka_enabled,
    is_ldms_enabled,
)
from automation_library.telemetry.functions.kafka_func import (
    verify_ldms_pods_running,
    verify_ldms_services_ports,
    verify_kafka_topics_via_rest,
    verify_kafka_config_match,
    verify_idrac_topic_data,
    verify_ldms_topic_data,
    verify_ldms_data_in_kafka,
)


# =============================================================================
# LDMS TEST CASES (run first, before Kafka tests)
# =============================================================================

def test_ldms_pods_running(host):
    """
    Test Case 1: Verify LDMS pods are running.

    If LDMS is enabled in software_config.json, verifies:
    - nersc-ldms-aggr pod is running
    - nersc-ldms-store pod is running
    """
    log = TestLogger(TEST_NAMES.get("ldms_pods_running", "Verify LDMS pods running"))

    # Skip if LDMS not enabled
    if not is_ldms_enabled(host):
        log.skipped(
            "LDMS is not enabled in software_config.json",
            "Test skipped - LDMS not enabled"
        )
        pytest.skip("LDMS is not enabled in software_config.json")

    # Get admin IP
    log.check("Getting admin IP from PXE mapping file")
    node = get_node_info(
        host, search_by="functional_group",
        search_value=K8S_CONTROL_PLANE_FUNCTIONAL_GROUP
    )
    admin_ip = node.get("admin_ip", "")
    assert admin_ip, "Failed to get admin IP from PXE mapping file"

    # Verify LDMS pods
    log.check("Verifying LDMS pods are running in telemetry namespace")
    result = verify_ldms_pods_running(host, admin_ip)

    if result.get("skipped"):
        pytest.skip(result.get("reason", "LDMS not enabled"))

    # Show pod results
    for pod_result in result.get("pod_results", []):
        pod = pod_result["pod"]
        phase = pod_result["phase"]
        running = pod_result["running"]
        status = "✓" if running else "✗"
        log.check(f"  {status} Pod '{pod}': {phase}")

    if result["success"]:
        log.passed("All LDMS pods are running", "nersc-ldms-aggr and nersc-ldms-store")
    else:
        errors = result.get("errors", [])
        log.failed("LDMS pods verification failed", "; ".join(errors))
        assert False, f"LDMS pods not running: {'; '.join(errors)}"


def test_ldms_services_ports(host):
    """
    Test Case 2: Verify LDMS services ports match telemetry_config.yml.

    If LDMS is enabled, verifies:
    - ldms-aggr service port matches ldms_agg_port in telemetry_config.yml
    - ldms-store service port matches ldms_store_port in telemetry_config.yml
    """
    log = TestLogger(TEST_NAMES.get("ldms_services_ports", "Verify LDMS services ports"))

    # Skip if LDMS not enabled
    if not is_ldms_enabled(host):
        log.skipped(
            "LDMS is not enabled in software_config.json",
            "Test skipped - LDMS not enabled"
        )
        pytest.skip("LDMS is not enabled in software_config.json")

    # Get admin IP
    log.check("Getting admin IP from PXE mapping file")
    node = get_node_info(
        host, search_by="functional_group",
        search_value=K8S_CONTROL_PLANE_FUNCTIONAL_GROUP
    )
    admin_ip = node.get("admin_ip", "")
    assert admin_ip, "Failed to get admin IP from PXE mapping file"

    # Verify LDMS services ports
    log.check("Verifying LDMS services ports match telemetry_config.yml")
    result = verify_ldms_services_ports(host, admin_ip)

    if result.get("skipped"):
        pytest.skip(result.get("reason", "LDMS not enabled"))

    if result.get("error"):
        log.failed("Failed to get LDMS services", result["error"])
        assert False, result["error"]

    # Show expected config
    expected = result.get("expected_config", {})
    log.check(f"  Expected ldms_agg_port: {expected.get('ldms_agg_port')}")
    log.check(f"  Expected ldms_store_port: {expected.get('ldms_store_port')}")

    # Show service results
    for svc_result in result.get("service_results", []):
        svc = svc_result["service"]
        expected_port = svc_result["expected_port"]
        actual_port = svc_result["actual_port"]
        match = svc_result["match"]
        status = "✓" if match else "✗"
        log.check(f"  {status} Service '{svc}': expected={expected_port}, actual={actual_port}")

    if result["success"]:
        log.passed("All LDMS services ports match", "Ports configured correctly")
    else:
        errors = result.get("errors", [])
        log.failed("LDMS services port mismatch", "; ".join(errors))
        assert False, f"LDMS services port mismatch: {'; '.join(errors)}"


# =============================================================================
# KAFKA TEST CASES
# =============================================================================

def test_kafka_topics(host):
    """
    Test Case 2: Verify Kafka topics via REST proxy.

    Checks:
    1. If kafka not in idrac_telemetry_collection_type -> skip test
    2. If idrac_telemetry_support=true -> idrac topic MUST exist
    3. If idrac_telemetry_support=false -> idrac topic should NOT exist
    4. If ldms in software_config.json -> ldms topic MUST exist
    5. If ldms NOT in software_config.json -> ldms topic should NOT exist

    All checks run and all errors are reported before failing.
    """
    log = TestLogger(TEST_NAMES["kafka_topics_verification"])

    # Get admin IP
    log.check("Getting admin IP from PXE mapping file")
    node = get_node_info(
        host, search_by="functional_group",
        search_value=K8S_CONTROL_PLANE_FUNCTIONAL_GROUP
    )
    admin_ip = node.get("admin_ip", "")
    assert admin_ip, "Failed to get admin IP from PXE mapping file"

    # Verify topics via REST proxy
    log.check("Getting Kafka topics via REST proxy")
    result = verify_kafka_topics_via_rest(host, admin_ip)

    # Check if test should be skipped (kafka not in collection type)
    if result.get("skip"):
        skip_reason = result.get("skip_reason", "Kafka not enabled")
        log.skipped(skip_reason, "Test skipped")
        pytest.skip(skip_reason)

    # Check for errors getting topics
    if result.get("error") and not result.get("topics"):
        log.failed("Failed to get topics via REST proxy", result["error"])
        assert False, result["error"]

    # Show configuration
    bridge_ip = result.get("bridge_ip", "")
    topics = result.get("topics", [])
    idrac_telemetry_support = result.get("idrac_telemetry_support", False)
    ldms_enabled = result.get("ldms_enabled", False)

    log.check(f"  Kafka bridge IP: {bridge_ip}")
    log.check(f"  Topics found: {topics}")
    log.check(f"  idrac_telemetry_support: {idrac_telemetry_support}")
    log.check(f"  ldms_enabled: {ldms_enabled}")

    # Show all topic verification results
    log.check("Topic verification results:")
    for topic_result in result.get("topic_results", []):
        topic = topic_result["topic"]
        exists = topic_result["exists"]
        required = topic_result["required"]
        reason = topic_result.get("reason", "")

        if required:
            # Topic should exist
            if exists:
                log.check(f"  ✓ Topic '{topic}': exists (required - {reason})")
            else:
                log.check(f"  ✗ Topic '{topic}': MISSING (required - {reason})")
        else:
            # Topic should NOT exist
            if not exists:
                log.check(f"  ✓ Topic '{topic}': correctly not present ({reason})")
            else:
                log.check(f"  ✗ Topic '{topic}': EXISTS but should not ({reason})")

    # Final result - show all errors
    if result["success"]:
        log.passed("All Kafka topic checks passed", f"Topics: {topics}")
    else:
        errors = result.get("errors", [])
        log.check("Errors found:")
        for error in errors:
            log.check(f"  - {error}")
        log.failed("Kafka topic verification failed", f"{len(errors)} error(s) found")
        assert False, "; ".join(errors)


def test_kafka_config_match(host):
    """
    Test Case 3: Verify Kafka configurations match telemetry_config.yml.

    Checks inside the Kafka broker pod to verify actual config matches expected.
    Verifies:
    - log_retention_hours matches
    - log_retention_bytes matches
    - log_segment_bytes matches
    """
    log = TestLogger(TEST_NAMES["kafka_config_match"])

    # Skip if Kafka not enabled
    if not is_kafka_enabled(host):
        log.skipped(
            "Kafka is not enabled in idrac_telemetry_collection_type",
            "Test skipped - Kafka not enabled"
        )
        pytest.skip("Kafka is not enabled in idrac_telemetry_collection_type")

    # Get admin IP
    log.check("Getting admin IP from PXE mapping file")
    node = get_node_info(
        host, search_by="functional_group",
        search_value=K8S_CONTROL_PLANE_FUNCTIONAL_GROUP
    )
    admin_ip = node.get("admin_ip", "")
    assert admin_ip, "Failed to get admin IP from PXE mapping file"

    # Verify config match (checks inside Kafka pod)
    log.check("Checking Kafka config inside broker pod vs telemetry_config.yml")
    result = verify_kafka_config_match(host, admin_ip)

    if result.get("error"):
        log.failed("Failed to get Kafka config", result["error"])
        assert False, result["error"]

    # Show config comparison (values read from telemetry_config.yml and Kafka CRD)
    expected = result.get("expected_config", {})
    actual = result.get("actual_config", {})

    log.check(f"  log_retention_hours: expected={expected.get('log_retention_hours')}, "
              f"actual={actual.get('log.retention.hours')}")
    log.check(f"  log_retention_bytes: expected={expected.get('log_retention_bytes')}, "
              f"actual={actual.get('log.retention.bytes')}")
    log.check(f"  log_segment_bytes: expected={expected.get('log_segment_bytes')}, "
              f"actual={actual.get('log.segment.bytes')}")

    mismatches = result.get("mismatches", [])
    if result["success"]:
        log.passed(LOG_MSGS["kafka_config_match"], "All configurations match")
    else:
        mismatch_str = "\n".join([
            f"  - {m['config']}: expected {m['expected']}, actual {m['actual']}"
            for m in mismatches
        ])
        log.failed("Kafka configuration mismatch", mismatch_str)
        assert False, ASSERT_MSGS["kafka_config_mismatch"].format(mismatches=mismatch_str)


def test_kafka_idrac_topic_data(host):
    """
    Test Case 4: Verify data is flowing to idrac Kafka topic.

    Verifies:
    - idrac topic is ready
    - idrac-telemetry pods are running (kafkapump sends data)
    """
    log = TestLogger(TEST_NAMES["kafka_idrac_topic_data"])

    # Skip if Kafka not enabled
    if not is_kafka_enabled(host):
        log.skipped("Kafka is not enabled", "Test skipped - Kafka not enabled")
        pytest.skip("Kafka is not enabled in idrac_telemetry_collection_type")

    # Get admin IP
    log.check("Getting admin IP from PXE mapping file")
    node = get_node_info(
        host, search_by="functional_group",
        search_value=K8S_CONTROL_PLANE_FUNCTIONAL_GROUP
    )
    admin_ip = node.get("admin_ip", "")
    assert admin_ip, "Failed to get admin IP from PXE mapping file"

    # Verify idrac topic data
    log.check("Verifying data flow to idrac Kafka topic")
    result = verify_idrac_topic_data(host, admin_ip)

    log.check(f"  Topic ready: {result.get('topic_ready', False)}")
    log.check(f"  Pods running: {result.get('pods_running', False)}")

    if result["success"]:
        log.passed(LOG_MSGS["kafka_idrac_data_flowing"], "idrac topic is receiving data")
    else:
        log.failed("idrac topic data flow verification failed", result.get("error", ""))
        assert False, ASSERT_MSGS["kafka_idrac_data_not_flowing"].format(
            topic_ready=result.get("topic_ready", False),
            pods_running=result.get("pods_running", False)
        )


def test_kafka_ldms_topic_data(host):
    """
    Test Case 6: Verify data is flowing to ldms Kafka topic.

    Only runs if LDMS is enabled in software_config.json.
    """
    log = TestLogger(TEST_NAMES["kafka_ldms_topic_data"])

    # Skip if Kafka not enabled
    if not is_kafka_enabled(host):
        log.skipped("Kafka is not enabled", "Test skipped - Kafka not enabled")
        pytest.skip("Kafka is not enabled")

    # Skip if LDMS not enabled
    if not is_ldms_enabled(host):
        log.skipped(
            "LDMS is not enabled in software_config.json",
            "Test skipped - LDMS not enabled"
        )
        pytest.skip("LDMS is not enabled in software_config.json")

    # Get admin IP
    log.check("Getting admin IP from PXE mapping file")
    node = get_node_info(
        host, search_by="functional_group",
        search_value=K8S_CONTROL_PLANE_FUNCTIONAL_GROUP
    )
    admin_ip = node.get("admin_ip", "")
    assert admin_ip, "Failed to get admin IP from PXE mapping file"

    # Verify ldms topic data
    log.check("Verifying ldms Kafka topic")
    result = verify_ldms_topic_data(host, admin_ip)

    if result.get("skipped"):
        log.check(f"  Skipped: {result.get('reason', '')}")
        pytest.skip(result.get("reason", "LDMS not enabled"))

    log.check(f"  Topic ready: {result.get('topic_ready', False)}")

    if result["success"]:
        log.passed(LOG_MSGS["kafka_ldms_data_flowing"], "ldms topic is ready")
    else:
        log.failed("ldms topic verification failed", result.get("error", ""))
        assert False, ASSERT_MSGS["kafka_ldms_data_not_flowing"].format(
            topic_ready=result.get("topic_ready", False)
        )


def test_ldms_data_in_kafka_topic(host):
    """
    Test Case 8: Verify LDMS data is flowing to Kafka topic.

    Verifies that data from all LDMS-enabled nodes (slurm_node, slurm_control_node,
    login_node, login_compiler_node) with all configured plugins is present in
    the ldms Kafka topic.

    Uses Kafka REST proxy to consume records and verify data presence.
    """
    log = TestLogger(TEST_NAMES.get("ldms_data_in_kafka", "Verify LDMS data in Kafka topic"))

    # Skip if LDMS not enabled
    if not is_ldms_enabled(host):
        log.skipped(
            "LDMS is not enabled in software_config.json",
            "Test skipped - LDMS not enabled"
        )
        pytest.skip("LDMS is not enabled in software_config.json")

    # Get admin IP
    log.check("Getting admin IP from PXE mapping file")
    node = get_node_info(
        host, search_by="functional_group",
        search_value=K8S_CONTROL_PLANE_FUNCTIONAL_GROUP
    )
    admin_ip = node.get("admin_ip", "")
    assert admin_ip, "Failed to get admin IP from PXE mapping file"

    # Verify LDMS data in Kafka (live data - waits for fresh messages)
    log.check(LOG_MSGS.get("ldms_data_verifying", "Verifying live LDMS data in Kafka topic"))
    result = verify_ldms_data_in_kafka(host, admin_ip, timeout_seconds=20)

    if result.get("skipped"):
        log.skipped(result.get("reason", "LDMS not enabled"), "Test skipped")
        pytest.skip(result.get("reason", "LDMS not enabled"))

    # Log details
    log.check(f"  Kafka bridge IP: {result.get('bridge_ip', '')}")
    log.check(f"  Domain: {result.get('domain_name', '')}")
    log.check(f"  Expected plugins: {result.get('expected_plugins', [])}")
    log.check(f"  Expected hostnames: {result.get('expected_hostnames', [])}")

    # Log results grouped by functional_group
    log.check("Hostname verification results (by functional group):")
    results_by_group = result.get("results_by_group", {})
    for func_group, hosts in results_by_group.items():
        # Clean up functional group name for display (remove _x86_64 suffix)
        display_group = func_group.replace("_x86_64", "")
        log.check(f"  [{display_group}]")
        for hr in hosts:
            hostname = hr.get("hostname", "")
            found = hr.get("found", False)
            plugins_found = hr.get("plugins_found", [])
            if found:
                log.check(f"    ✓ {hostname}: found")
                for plugin_data in plugins_found:
                    plugin = plugin_data.get("plugin", "")
                    record = plugin_data.get("record", {})
                    log.check(f"        - {plugin}:")
                    log.check(f"            topic: {record.get('topic', '')}")
                    log.check(f"            partition: {record.get('partition', '')}")
                    log.check(f"            offset: {record.get('offset', '')}")
                    value = record.get("value", {})
                    log.check(f"            instance: {value.get('instance', '')}")
                    log.check(f"            timestamp: {value.get('timestamp', '')}")
                    exclude = ["timestamp", "hostname", "instance",
                              "component_id", "job_id", "app_id"]
                    sample_keys = [k for k in value.keys() if k not in exclude][:5]
                    if sample_keys:
                        data_str = ', '.join(f'{k}: {value[k]}' for k in sample_keys)
                        log.check(f"            sample_data: {{{data_str}}}")
            else:
                log.check(f"    ✗ {hostname}: MISSING")

    if result["success"]:
        found_count = len(result.get("found_hostnames", []))
        log.passed(
            LOG_MSGS.get("ldms_data_success", "LDMS data verified").format(count=found_count),
            f"Data found from all {found_count} hostnames"
        )
    else:
        missing = result.get("missing_hostnames", [])
        found = result.get("found_hostnames", [])
        log.failed(
            f"LDMS data missing from {len(missing)} hostnames",
            result.get("error", "")
        )
        assert False, ASSERT_MSGS.get("ldms_data_missing_hostnames", "LDMS data missing").format(
            missing=missing,
            found=found
        )
