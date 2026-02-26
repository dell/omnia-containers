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
Kafka Telemetry Test Cases.

This module contains pytest test cases for verifying Kafka configuration
and data flow in the telemetry namespace.

Test cases:
1. Verify LDMS pods running (if ldms enabled)
2. Verify LDMS services ports match telemetry_config.yml (if ldms enabled)
3. Verify Kafka topics via REST proxy
4. Verify Kafka configurations match telemetry_config.yml
5. Verify idrac Kafka topic ready (with service tag verification via Redfish)
6. Verify LDMS data in Kafka topic (if ldms enabled)

Note: Kafka tests skip if kafka is not in idrac_telemetry_collection_type.
      LDMS tests skip if ldms is not in software_config.json.
      Actual iDRAC data verification is done in test_victoria_idrac_data.
"""

from datetime import datetime

import pytest

from automation_library.core import TestLogger
from automation_library.telemetry.messages import (
    TEST_NAMES,
    TEST_LOG_MSGS as LOG_MSGS,
    TEST_ASSERT_MSGS as ASSERT_MSGS,
)
from automation_library.telemetry.functions.shared_func import (
    get_admin_ip,
    skip_if_kafka_not_enabled,
    skip_if_ldms_not_enabled,
)
from automation_library.telemetry.functions.kafka_func import (
    verify_ldms_pods_running,
    verify_ldms_services_ports,
    verify_kafka_topics_via_rest,
    verify_kafka_config_match,
    verify_idrac_data_in_kafka,
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

    skip_if_ldms_not_enabled(host, log)
    admin_ip = get_admin_ip(host, log)

    # Verify LDMS pods
    log.check("Verifying LDMS pods are running in telemetry namespace")
    result = verify_ldms_pods_running(host, admin_ip)

    if result.get("skipped"):
        pytest.skip(result.get("reason", "LDMS not enabled"))

    # Build details
    details_lines = []
    for pod_result in result.get("pod_results", []):
        pod = pod_result["pod"]
        phase = pod_result["phase"]
        running = pod_result["running"]
        status = "✓" if running else "✗"
        details_lines.append(f"{status} Pod '{pod}': {phase}")

    details = "\n".join(details_lines)

    if result["success"]:
        log.passed("All LDMS pods are running", details)
    else:
        errors = result.get("errors", [])
        log.failed("LDMS pods verification failed", details + "\n" + "; ".join(errors))
        assert False, f"LDMS pods not running: {'; '.join(errors)}"


def test_ldms_services_ports(host):
    """
    Test Case 2: Verify LDMS services ports match telemetry_config.yml.

    If LDMS is enabled, verifies:
    - ldms-aggr service port matches ldms_agg_port in telemetry_config.yml
    - ldms-store service port matches ldms_store_port in telemetry_config.yml
    """
    log = TestLogger(TEST_NAMES.get("ldms_services_ports", "Verify LDMS services ports"))

    skip_if_ldms_not_enabled(host, log)
    admin_ip = get_admin_ip(host, log)

    # Verify LDMS services ports
    log.check("Verifying LDMS services ports match telemetry_config.yml")
    result = verify_ldms_services_ports(host, admin_ip)

    if result.get("skipped"):
        pytest.skip(result.get("reason", "LDMS not enabled"))

    if result.get("error"):
        log.failed("Failed to get LDMS services", result["error"])
        assert False, result["error"]

    # Build details
    expected = result.get("expected_config", {})
    details_lines = [
        f"Expected ldms_agg_port: {expected.get('ldms_agg_port')}",
        f"Expected ldms_store_port: {expected.get('ldms_store_port')}",
    ]

    for svc_result in result.get("service_results", []):
        svc = svc_result["service"]
        expected_port = svc_result["expected_port"]
        actual_port = svc_result["actual_port"]
        match = svc_result["match"]
        status = "✓" if match else "✗"
        details_lines.append(f"{status} Service '{svc}': expected={expected_port}, actual={actual_port}")

    details = "\n".join(details_lines)

    if result["success"]:
        log.passed("All LDMS services ports match", details)
    else:
        errors = result.get("errors", [])
        log.failed("LDMS services port mismatch", details + "\n" + "; ".join(errors))
        assert False, f"LDMS services port mismatch: {'; '.join(errors)}"


# =============================================================================
# KAFKA TEST CASES
# =============================================================================

def test_kafka_topics(host):
    """
    Test Case 3: Verify Kafka topics via REST proxy.

    Checks:
    1. If kafka not in idrac_telemetry_collection_type -> skip test
    2. If idrac_telemetry_support=true -> idrac topic MUST exist
    3. If idrac_telemetry_support=false -> idrac topic should NOT exist
    4. If ldms in software_config.json -> ldms topic MUST exist
    5. If ldms NOT in software_config.json -> ldms topic should NOT exist

    All checks run and all errors are reported before failing.
    """
    log = TestLogger(TEST_NAMES["kafka_topics_verification"])

    admin_ip = get_admin_ip(host, log)

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

    # Build details
    bridge_ip = result.get("bridge_ip", "")
    topics = result.get("topics", [])
    idrac_telemetry_support = result.get("idrac_telemetry_support", False)
    ldms_enabled = result.get("ldms_enabled", False)

    details_lines = [
        f"Kafka bridge IP: {bridge_ip}",
        f"Topics found: {topics}",
        f"idrac_telemetry_support: {idrac_telemetry_support}",
        f"ldms_enabled: {ldms_enabled}",
        "",
        "Topic verification:",
    ]

    for topic_result in result.get("topic_results", []):
        topic = topic_result["topic"]
        exists = topic_result["exists"]
        required = topic_result["required"]
        reason = topic_result.get("reason", "")

        if required:
            if exists:
                details_lines.append(f"  ✓ '{topic}': exists ({reason})")
            else:
                details_lines.append(f"  ✗ '{topic}': MISSING ({reason})")
        else:
            if not exists:
                details_lines.append(f"  ✓ '{topic}': correctly absent ({reason})")
            else:
                details_lines.append(f"  ✗ '{topic}': EXISTS but should not ({reason})")

    details = "\n".join(details_lines)

    if result["success"]:
        log.passed("All Kafka topic checks passed", details)
    else:
        errors = result.get("errors", [])
        err_details = details + "\n\nErrors:\n" + "\n".join([f"  - {e}" for e in errors])
        log.failed("Kafka topic verification failed", err_details)
        assert False, "; ".join(errors)


def test_kafka_config_match(host):
    """
    Test Case 4: Verify Kafka configurations match telemetry_config.yml.

    Checks inside the Kafka broker pod to verify actual config matches expected.
    Verifies:
    - log_retention_hours matches
    - log_retention_bytes matches
    - log_segment_bytes matches
    """
    log = TestLogger(TEST_NAMES["kafka_config_match"])

    skip_if_kafka_not_enabled(host, log)
    admin_ip = get_admin_ip(host, log)

    # Verify config match (checks inside Kafka pod)
    log.check("Checking Kafka config inside broker pod vs telemetry_config.yml")
    result = verify_kafka_config_match(host, admin_ip)

    if result.get("error"):
        log.failed("Failed to get Kafka config", result["error"])
        assert False, result["error"]

    # Build details
    expected = result.get("expected_config", {})
    actual = result.get("actual_config", {})

    details_lines = [
        f"log_retention_hours: expected={expected.get('log_retention_hours')}, "
        f"actual={actual.get('log.retention.hours')}",
        f"log_retention_bytes: expected={expected.get('log_retention_bytes')}, "
        f"actual={actual.get('log.retention.bytes')}",
        f"log_segment_bytes: expected={expected.get('log_segment_bytes')}, "
        f"actual={actual.get('log.segment.bytes')}",
    ]

    mismatches = result.get("mismatches", [])
    details = "\n".join(details_lines)

    if result["success"]:
        log.passed(LOG_MSGS["kafka_config_match"], details)
    else:
        mismatch_str = "\n".join([
            f"  ✗ {m['config']}: expected {m['expected']}, actual {m['actual']}"
            for m in mismatches
        ])
        log.failed("Kafka configuration mismatch", details + "\n\nMismatches:\n" + mismatch_str)
        assert False, ASSERT_MSGS["kafka_config_mismatch"].format(mismatches=mismatch_str)


def test_idrac_data_in_kafka_topic(host):
    """
    Test Case 5: Verify iDRAC telemetry data in Kafka topic.

    Gets activated IPs from MySQL, uses Redfish to get service tags,
    then consumes data from Kafka and verifies service tags are present.
    Shows sample metrics for each service tag.
    """
    log = TestLogger(TEST_NAMES.get("kafka_idrac_data", "Verify iDRAC data in Kafka topic"))

    skip_if_kafka_not_enabled(host, log)
    admin_ip = get_admin_ip(host, log)

    # Verify iDRAC data in Kafka (wait up to 30s for metrics with values)
    log.check("Verifying iDRAC telemetry data in Kafka topic")
    result = verify_idrac_data_in_kafka(host, admin_ip, timeout_seconds=30)

    if result.get("skipped"):
        log.skipped(result.get("reason", ""), "Test skipped")
        pytest.skip(result.get("reason", ""))

    if result.get("error") and not result.get("service_tag_results"):
        log.failed("Failed to verify iDRAC data in Kafka", result["error"])
        assert False, result["error"]

    # Build details
    details_lines = [f"Kafka bridge IP: {result.get('bridge_ip', '')}"]

    ip_to_tag = result.get("ip_to_service_tag", {})
    details_lines.append("")
    details_lines.append("Activated IPs → Service Tags (via Redfish):")
    for ip, tag in ip_to_tag.items():
        details_lines.append(f"  {ip} → {tag}")

    details_lines.append("")
    details_lines.append("Service tag verification:")
    for tag_result in result.get("service_tag_results", []):
        ip = tag_result["ip"]
        service_tag = tag_result["service_tag"]
        found = tag_result["found"]
        sample_metrics = tag_result.get("sample_metrics", [])
        kafka_ts = tag_result.get("kafka_timestamp", "")

        if found:
            details_lines.append(f"  ✓ {service_tag}")
            details_lines.append(f"      IP          : {ip}")
            if kafka_ts:
                try:
                    human_ts = datetime.fromtimestamp(int(kafka_ts)).strftime("%Y-%m-%d %H:%M:%S")
                    details_lines.append(f"      Kafka Time  : {kafka_ts} ({human_ts})")
                except (ValueError, OSError):
                    details_lines.append(f"      Kafka Time  : {kafka_ts}")
            if sample_metrics:
                details_lines.append(f"      Metrics     :")
                for metric in sample_metrics:
                    val = metric.get('value')
                    val_str = str(val) if val is not None and str(val).strip() != "" else "(no value yet)"
                    details_lines.append(f"        - {metric['metric_name']}: {val_str}")
            else:
                details_lines.append(f"      Metrics     : (no values captured yet)")
        else:
            details_lines.append(f"  ✗ {service_tag}")
            details_lines.append(f"      IP          : {ip}")
            details_lines.append(f"      Status      : NO DATA FOUND")

    details = "\n".join(details_lines)

    if result["success"]:
        found_count = len(result.get("found_tags", []))
        msg = LOG_MSGS.get(
            "idrac_kafka_data_success",
            "iDRAC data found for all {count} service tags"
        ).format(count=found_count)
        log.passed(msg, details)
    else:
        missing = result.get("missing_tags", [])
        log.failed(
            f"iDRAC data missing for {len(missing)} service tags",
            details
        )
        assert False, result.get("error", "iDRAC data missing")


def test_ldms_data_in_kafka_topic(host):
    """
    Test Case 6: Verify LDMS data is flowing to Kafka topic.

    Verifies that data from all LDMS-enabled nodes (slurm_node, slurm_control_node,
    login_node, login_compiler_node) with all configured plugins is present in
    the ldms Kafka topic.

    Uses Kafka REST proxy to consume records and verify data presence.
    """
    log = TestLogger(TEST_NAMES.get("ldms_data_in_kafka", "Verify LDMS data in Kafka topic"))

    skip_if_ldms_not_enabled(host, log)
    admin_ip = get_admin_ip(host, log)

    # Verify LDMS data in Kafka (waits up to 30s for ALL hostname×plugin data)
    log.check(LOG_MSGS.get("ldms_data_verifying", "Verifying live LDMS data in Kafka topic"))
    result = verify_ldms_data_in_kafka(host, admin_ip, timeout_seconds=30)

    if result.get("skipped"):
        log.skipped(result.get("reason", "LDMS not enabled"), "Test skipped")
        pytest.skip(result.get("reason", "LDMS not enabled"))

    # Build details
    expected_count = result.get("expected_instance_count", 0)
    found_count = result.get("found_instance_count", 0)
    details_lines = [
        f"Kafka bridge IP: {result.get('bridge_ip', '')}",
        f"Domain: {result.get('domain_name', '')}",
        f"Expected plugins: {result.get('expected_plugins', [])}",
        f"Expected hostnames: {result.get('expected_hostnames', [])}",
        f"Expected instances (hostname×plugin): {expected_count}",
        f"Found instances: {found_count}/{expected_count}",
        "",
        "Hostname verification (by functional group):",
    ]

    results_by_group = result.get("results_by_group", {})
    for func_group, hosts in results_by_group.items():
        display_group = func_group
        details_lines.append(f"  [{display_group}]")
        for hr in hosts:
            hostname = hr.get("hostname", "")
            found = hr.get("found", False)
            all_plugins = hr.get("all_plugins_found", False)
            plugins_found = hr.get("plugins_found", [])
            plugins_missing = hr.get("plugins_missing", [])
            plugins_expected = hr.get("plugins_expected", [])

            status_icon = "✓" if all_plugins else ("⚠" if found else "✗")
            status_text = (
                f"all {len(plugins_expected)} plugins found" if all_plugins
                else f"{len(plugins_found)}/{len(plugins_expected)} plugins" if found
                else "NO DATA"
            )
            details_lines.append(f"    {status_icon} {hostname} ({status_text})")

            for plugin_data in plugins_found:
                plugin = plugin_data.get("plugin", "")
                record = plugin_data.get("record", {})
                value = record.get("value", {})
                ldms_ts = value.get("timestamp", "")
                if ldms_ts:
                    try:
                        ts_float = float(ldms_ts)
                        human_ts = datetime.fromtimestamp(ts_float).strftime("%Y-%m-%d %H:%M:%S")
                        details_lines.append(f"        ✓ {plugin}: {ldms_ts} ({human_ts})")
                    except (ValueError, OSError):
                        details_lines.append(f"        ✓ {plugin}: {ldms_ts}")
                else:
                    details_lines.append(f"        ✓ {plugin}")

                exclude = ["timestamp", "hostname", "instance",
                          "component_id", "job_id", "app_id"]
                sample_keys = [k for k in value.keys() if k not in exclude][:5]
                if sample_keys:
                    for k in sample_keys:
                        details_lines.append(f"            - {k}: {value[k]}")

            for mp in plugins_missing:
                details_lines.append(f"        ✗ {mp}: MISSING")

    details = "\n".join(details_lines)

    if result["success"]:
        host_count = len(result.get("found_hostnames", []))
        plugin_count = len(result.get("expected_plugins", []))
        log.passed(
            LOG_MSGS.get("ldms_data_success", "LDMS data verified for all {count} hostnames").format(count=host_count),
            details
        )
    else:
        missing_hosts = result.get("missing_hostnames", [])
        missing_instances = result.get("missing_instances", [])
        if missing_hosts:
            log.failed(
                f"LDMS data missing from {len(missing_hosts)} hostnames",
                details
            )
        else:
            log.failed(
                f"LDMS data missing {len(missing_instances)} plugin instances",
                details
            )
        assert False, ASSERT_MSGS.get("ldms_data_missing_hostnames", "LDMS data missing").format(
            missing=missing_hosts or missing_instances,
            found=result.get("found_hostnames", [])
        )
