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
Provision K8s Verification Test Cases.

Test cases for verifying K8s cluster matches PXE mapping:
1. Verify K8s nodes from PXE mapping are Ready
2. Verify default storage class (ps01 if CSI PowerScale, nfs-client otherwise)
3. Verify CSI PowerScale (isilon) pods running (if csi_driver_powerscale enabled)
4. Verify NFS provisioner pod running
5. Verify telemetry pods running (expected + unexpected detection)
"""

import pytest
from automation_library.core import TestLogger, is_software_enabled
from automation_library.provision.functions import (
    get_k8s_nodes,
    verify_k8s_nodes_ready,
    verify_k8s_telemetry_pods,
    verify_k8s_default_storage_class,
    verify_k8s_isilon_pods,
    verify_k8s_nfs_provisioner_pods,
)


@pytest.mark.sanity
@pytest.mark.build_stream
@pytest.mark.order(30)
def test_k8s_nodes_ready(host):
    """
    Test Case 20: Verify K8s nodes from PXE mapping are Ready.

    Checks:
    - All K8s nodes from PXE mapping exist in cluster
    - All nodes are in Ready state
    - No extra nodes exist in cluster (not in PXE mapping)
    """
    log = TestLogger("Verify K8s nodes match PXE mapping and are Ready")

    k8s_nodes = get_k8s_nodes(host)
    if not k8s_nodes:
        log.skipped("No K8s nodes in PXE mapping", "Check PXE mapping file")
        pytest.skip("No K8s nodes in PXE mapping")

    log.check(f"Checking {len(k8s_nodes)} K8s nodes from PXE mapping")

    result = verify_k8s_nodes_ready(host, k8s_nodes)

    if result.get("error"):
        log.failed("K8s node check failed", result["error"])
        assert False, result["error"]

    # Build detailed output
    details_lines = [
        f"Expected nodes: {len(result['expected'])}",
        f"Cluster nodes: {len(result['actual'])}",
    ]

    # Show expected nodes status
    details_lines.append("Expected nodes:")
    for node in result.get("node_results", []):
        status_icon = "✓" if node["ready"] else "✗"
        status_text = "Ready" if node["ready"] else node.get("status", "NotReady")
        if node["found"]:
            details_lines.append(f"  {status_icon} {node['hostname']} - {status_text}")
        else:
            details_lines.append(f"  ✗ {node['hostname']} - NOT FOUND in cluster")

    # Show extra nodes if any
    if result.get("extra"):
        details_lines.append("Extra nodes (not in PXE mapping):")
        for extra in result["extra"]:
            details_lines.append(f"  ✗ {extra}")

    details = "\n".join(details_lines)

    if result["success"]:
        log.passed(f"All {len(result['expected'])} K8s nodes Ready", details)
    else:
        error_parts = []
        if result.get("missing"):
            error_parts.append(f"missing: {', '.join(result['missing'])}")
        if result.get("not_ready"):
            error_parts.append(f"not ready: {', '.join(result['not_ready'])}")
        if result.get("extra"):
            error_parts.append(f"extra: {', '.join(result['extra'])}")
        log.failed(f"K8s node mismatch - {'; '.join(error_parts)}", details)

    assert result["success"], f"K8s node check failed: {'; '.join(error_parts)}"


@pytest.mark.sanity
@pytest.mark.build_stream
@pytest.mark.order(31)
def test_k8s_default_storage_class(host):
    """
    Test Case 21: Verify default K8s storage class.

    Rules:
    - If csi_driver_powerscale in software_config.json → default SC = ps01
    - Otherwise → default SC = nfs-client
    """
    log = TestLogger("Verify K8s default storage class")

    k8s_nodes = get_k8s_nodes(host)
    if not k8s_nodes:
        log.skipped("No K8s nodes in PXE mapping", "Check PXE mapping file")
        pytest.skip("No K8s nodes in PXE mapping")

    result = verify_k8s_default_storage_class(host, k8s_nodes)

    if result.get("error"):
        log.failed("Storage class check failed", result["error"])
        assert False, result["error"]

    # Build detailed output
    details_lines = [
        f"CSI PowerScale enabled: {'yes' if result['csi_powerscale_enabled'] else 'no'}",
        f"Expected default SC: {result['expected_default_sc']}",
        f"Actual default SC: {result['actual_default_sc'] or 'NONE'}",
        "Storage classes:",
    ]
    for sc in result.get("all_storage_classes", []):
        default_tag = " (default)" if sc["is_default"] else ""
        details_lines.append(f"  - {sc['name']}{default_tag} [{sc['provisioner']}]")

    details = "\n".join(details_lines)

    if result["success"]:
        log.passed(f"Default storage class is '{result['actual_default_sc']}'", details)
    else:
        log.failed(
            f"Expected default SC '{result['expected_default_sc']}' "
            f"but got '{result['actual_default_sc'] or 'NONE'}'",
            details,
        )

    assert result["success"], (
        f"Default storage class mismatch: expected '{result['expected_default_sc']}', "
        f"got '{result['actual_default_sc'] or 'NONE'}'"
    )


@pytest.mark.sanity
@pytest.mark.build_stream
@pytest.mark.order(32)
def test_k8s_isilon_pods(host):
    """
    Test Case 22: Verify CSI PowerScale (isilon) pods running.

    Checks isilon-controller and isilon-node pods in isilon namespace.
    Skipped if csi_driver_powerscale not in software_config.json.
    """
    log = TestLogger("Verify CSI PowerScale (isilon) pods running")

    k8s_nodes = get_k8s_nodes(host)
    if not k8s_nodes:
        log.skipped("No K8s nodes in PXE mapping", "Check PXE mapping file")
        pytest.skip("No K8s nodes in PXE mapping")

    if not is_software_enabled(host, "csi_driver_powerscale"):
        log.skipped(
            "csi_driver_powerscale not in software_config.json",
            "Test skipped - CSI PowerScale not enabled",
        )
        pytest.skip("csi_driver_powerscale not enabled in software_config.json")

    result = verify_k8s_isilon_pods(host, k8s_nodes)

    if result.get("error"):
        log.failed("Isilon pod check failed", result["error"])
        assert False, result["error"]

    details_lines = []
    for pod in result.get("pods", []):
        icon = "✓" if pod["running"] else "✗"
        details_lines.append(f"  {icon} {pod['pod_name']} ({pod['status']})")
    for m in result.get("missing", []):
        details_lines.append(f"  ✗ {m}: NOT FOUND")

    details = "\n".join(details_lines)

    if result["success"]:
        log.passed(f"All isilon pods running ({len(result['pods'])} pods)", details)
    else:
        log.failed("Isilon pods missing or not running", details)

    assert result["success"], f"Isilon pods issue: missing={result.get('missing', [])}"


@pytest.mark.sanity
@pytest.mark.build_stream
@pytest.mark.order(33)
def test_k8s_nfs_provisioner_pods(host):
    """
    Test Case 23: Verify NFS provisioner pod running.

    Checks nfs-client-nfs-subdir-external-provisioner pod in default namespace.
    """
    log = TestLogger("Verify NFS provisioner pod running")

    k8s_nodes = get_k8s_nodes(host)
    if not k8s_nodes:
        log.skipped("No K8s nodes in PXE mapping", "Check PXE mapping file")
        pytest.skip("No K8s nodes in PXE mapping")

    result = verify_k8s_nfs_provisioner_pods(host, k8s_nodes)

    if result.get("error"):
        log.failed("NFS provisioner pod check failed", result["error"])
        assert False, result["error"]

    details_lines = []
    for pod in result.get("pods", []):
        icon = "✓" if pod["running"] else "✗"
        details_lines.append(f"  {icon} {pod['pod_name']} ({pod['status']})")

    details = "\n".join(details_lines)

    if result["success"]:
        log.passed("NFS provisioner pod running", details)
    else:
        log.failed("NFS provisioner pod not running", details)

    assert result["success"], "NFS provisioner pod not running"


@pytest.mark.sanity
@pytest.mark.build_stream
@pytest.mark.order(34)
def test_k8s_telemetry_pods(host):
    """
    Test Case 24: Verify telemetry pods are running in K8s cluster.

    Checks pods based on telemetry_config.yml and software_config.json:
    - LDMS pods (nersc-ldms-aggr, nersc-ldms-store) if ldms enabled
    - iDRAC telemetry pods if telemetry_sources.idrac.metrics_enabled
    - VictoriaMetrics cluster pods if any source targets victoria_metrics
    - VictoriaLogs cluster pods if any source targets victoria_logs
    - Kafka + Strimzi pods if any source/bridge targets kafka
    - Vector bridge pods (vector-ldms, vector-ome) if bridges enabled
    - vmagent-vector / vlagent-vector write buffers for Vector bridges
    - PowerScale pods (karavi-metrics, otel-collector) if powerscale enabled
    - Detects unexpected pods not matching expected configuration
    """
    log = TestLogger("Verify K8s telemetry pods running")

    k8s_nodes = get_k8s_nodes(host)
    if not k8s_nodes:
        log.skipped("No K8s nodes in PXE mapping", "Check PXE mapping file")
        pytest.skip("No K8s nodes in PXE mapping")

    result = verify_k8s_telemetry_pods(host, k8s_nodes)

    if result.get("error"):
        log.failed("Telemetry pod check failed", result["error"])
        assert False, result["error"]

    log.check(f"Checking telemetry pods: {', '.join(result['expected_pods'])}")

    # Build detailed output with configuration info
    details_lines = [
        f"VictoriaMetrics mode: {result.get('deployment_mode', 'cluster')}",
        f"LDMS enabled: {'yes' if result.get('ldms_enabled') else 'no'}",
        f"iDRAC telemetry enabled: {'yes' if result.get('idrac_enabled') else 'no'}",
        f"Expected pod types: {len(result['expected_pods'])}",
    ]

    for pod_detail in result.get("pod_details", []):
        status_icon = "✓" if pod_detail["running"] else "✗"
        prefix = pod_detail['prefix']
        pod_name = pod_detail['pod_name']
        status = pod_detail['status']
        details_lines.append(f"  {status_icon} {prefix}: {pod_name} ({status})")

    if result.get("missing_pods"):
        details_lines.append("Missing pods:")
        for missing in result["missing_pods"]:
            details_lines.append(f"  ✗ {missing}")

    if result.get("unexpected_pods"):
        details_lines.append("Unexpected pods (not in expected config):")
        for upod in result["unexpected_pods"]:
            details_lines.append(f"  ? {upod['pod_name']} ({upod['status']})")

    details = "\n".join(details_lines)

    if result["success"]:
        if result.get("unexpected_pods"):
            log.passed(
                f"All {len(result['expected_pods'])} expected pods running "
                f"({len(result['unexpected_pods'])} unexpected pods found)",
                details,
            )
        else:
            log.passed(f"All {len(result['expected_pods'])} telemetry pod types running", details)
    else:
        log.failed("Telemetry pods missing or not running", details)

    assert result["success"], f"Missing pods: {', '.join(result['missing_pods'])}"
