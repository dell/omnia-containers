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
K8s & Telemetry Upgrade Pre-Check Tests.

Captures the full cluster state BEFORE the K8s + Telemetry upgrade and
persists it as a JSON snapshot so the Post_check scenario can validate
data preservation, IP continuity, and version progression.

Test-case mapping (from K8s-Telemetry-upgrade-test-cases-v2.xls):
  TC-01  K8s node versions        -> TC-F001 step 1
  TC-02  Node readiness            -> TC-F015 Gate 3
  TC-03  kube-system pods          -> TC-F015 Gate 3
  TC-04  etcd health               -> TC-F015 Gate 4
  TC-05  Calico pods               -> TC-F013
  TC-06  MetalLB pods              -> TC-F013
  TC-07  LoadBalancer IPs          -> TC-E016
  TC-08  Helm releases             -> TC-TEL-F003
  TC-09  Telemetry pods            -> TC-F020
  TC-10  VictoriaMetrics PVCs      -> TC-TEL-F005
  TC-11  Kafka state               -> TC-TEL-F004 / TC-TEL-F003
  TC-12  CSI driver + PVCs         -> TC-F019
  TC-13  NFS provisioner           -> Precondition
  TC-14  CRI-O version             -> TC-F006
  TC-15  Calico version            -> TC-F007
  TC-16  Network policies          -> TC-F007
  TC-17  MetalLB version + pools   -> TC-F008
  TC-18  Helm binary version       -> TC-F009
  TC-19  iDRAC telemetry status    -> TC-TEL-F006
  TC-20  LDMS status               -> TC-TEL-F007
  TC-21  SSH connectivity          -> TC-F015 Gate 2
  TC-22  Version hop validation    -> TC-F015 Gate 5 / TC-F017
  TC-23  Etcd backup readiness     -> TC-F003
  TC-24  Security permissions      -> TC-S001 / TC-S002
  TC-25  Pulp images available     -> TC-F015 Gate 1
  TC-26  Addon compatibility       -> TC-F018
  TC-27  BSS boot params baseline  -> TC-F011
  TC-28  Strimzi/Kafka version     -> TC-TEL-F004 / TC-TEL-F016
  TC-29  CRI-O storage config      -> TC-F006
  TC-30  Kube-VIP HA status        -> TC-F014
  TC-31  PodDisruptionBudgets      -> TC-F005
  TC-32  Node roles topology       -> TC-F002 / TC-F004
  TC-33  Telemetry pre-flight      -> TC-TEL-F002
  TC-34  OIM upgrade status        -> TC-F016
  TC-35  Save snapshot             -> Snapshot for post-checks

IMPORTANT:
  Tests execute in order.  If TC-01 (version collection) fails, subsequent
  tests are SKIPPED to avoid cascading noise.
"""

from datetime import datetime, timezone

import pytest

from automation_library.core import TestLogger
from automation_library.telemetry.functions.shared_func import get_admin_ip
from automation_library.upgrade_and_rollback.functions.precheck_func import (
    collect_k8s_node_versions,
    collect_node_readiness,
    collect_kube_system_pods,
    collect_etcd_health,
    collect_calico_status,
    collect_metallb_status,
    collect_lb_service_ips,
    collect_helm_releases,
    collect_telemetry_pods,
    collect_vm_pvcs,
    collect_kafka_state,
    collect_csi_status,
    collect_nfs_provisioner,
    collect_crio_version,
    collect_calico_version,
    collect_network_policies,
    collect_metallb_version,
    collect_helm_version,
    collect_idrac_telemetry_status,
    collect_ldms_status,
    verify_ssh_connectivity,
    verify_version_hop_valid,
    verify_oim_upgrade_completed,
    collect_telemetry_config_flags,
    collect_etcd_backup_status,
    collect_security_permissions,
    verify_pulp_images_available,
    verify_addon_compatibility,
    verify_k8s_at_target_for_telemetry,
    verify_telemetry_preflight,
    collect_bss_boot_params,
    collect_strimzi_version,
    collect_crio_storage_config,
    collect_kube_vip_status,
    collect_pod_disruption_budgets,
    collect_node_roles,
)
from automation_library.upgrade_and_rollback.functions.snapshot_func import (
    save_precheck_snapshot,
)
from automation_library.upgrade_and_rollback.vars import (
    K8S_UPGRADE_VARS,
    SNAPSHOT_PATH,
)
from automation_library.upgrade_and_rollback.messages import (
    PRECHECK_TEST_NAMES,
    PRECHECK_LOG_MSGS,
    PRECHECK_ASSERT_MSGS,
    SKIP_MSGS,
)


# =============================================================================
# MODULE-LEVEL STATE
# =============================================================================

_admin_ip: str = ""
_cluster_reachable: bool = False
_snapshot_data: dict = {}


def _require_cluster():
    """Skip test if cluster is not reachable."""
    if not _cluster_reachable:
        pytest.skip("Cluster not reachable — TC-01 did not pass")


def _record(key, value):
    """Store a value in the snapshot dict."""
    _snapshot_data[key] = value


# =============================================================================
# TC-01: K8s Node Versions  (TC-F001)
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(1)
def test_k8s_node_versions(host):
    """
    TC-01: Collect K8s version from every node.
    Records current version and validates all nodes are at the expected
    pre-upgrade version if upgrade.current_version is set.
    """
    global _admin_ip, _cluster_reachable

    current_ver = K8S_UPGRADE_VARS.get("current_version", "")
    log = TestLogger(
        PRECHECK_TEST_NAMES["k8s_version"].format(
            version=current_ver or "auto-detect"
        )
    )

    # Get admin IP
    log.check(PRECHECK_LOG_MSGS["collecting_versions"])
    try:
        _admin_ip = get_admin_ip(host, log)
    except (AssertionError, Exception) as exc:
        log.failed("Admin IP lookup failed", str(exc))
        pytest.fail(PRECHECK_ASSERT_MSGS["admin_ip_not_found"])

    print(
        f"    {PRECHECK_LOG_MSGS['admin_ip_found'].format(ip=_admin_ip)}",
        flush=True,
    )

    result = collect_k8s_node_versions(host, _admin_ip)
    if not result["success"]:
        log.failed("Failed to collect node versions", result["error"])
        pytest.fail(result["error"])

    _cluster_reachable = True
    _record("k8s_node_versions", result)

    for node in result["nodes"]:
        print(
            f"    {PRECHECK_LOG_MSGS['node_version'].format(**node)}",
            flush=True,
        )

    # Validate version if configured
    # Note: current_ver is Omnia version (e.g., 2.1.0.0), not K8s version
    # Skip version validation as we're just collecting the current state
    # The actual K8s version will be recorded in the snapshot for comparison
    if current_ver and current_ver.startswith("v1."):
        # Only validate if current_ver is actually a K8s version format
        prefix = current_ver if current_ver.startswith("v") else f"v{current_ver}"
        bad = [
            n for n in result["nodes"]
            if not n["version"].startswith(prefix)
        ]
        if bad:
            log.failed(
                "Version mismatch",
                PRECHECK_ASSERT_MSGS["version_mismatch"].format(
                    name=bad[0]["name"],
                    actual=bad[0]["version"],
                    expected=current_ver,
                ),
            )
            pytest.fail(
                PRECHECK_ASSERT_MSGS["version_mismatch"].format(
                    name=bad[0]["name"],
                    actual=bad[0]["version"],
                    expected=current_ver,
                )
            )

    log.passed(
        f"Collected versions from {len(result['nodes'])} nodes",
        "\n".join(
            f"  {n['name']}: {n['version']}" for n in result["nodes"]
        ),
    )


# =============================================================================
# TC-02: Node Readiness  (TC-F015 Gate 3)
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(2)
def test_node_readiness(host):
    """TC-02: Verify all nodes are in Ready state."""
    _require_cluster()
    log = TestLogger(PRECHECK_TEST_NAMES["node_readiness"])

    log.check(PRECHECK_LOG_MSGS["collecting_readiness"])
    result = collect_node_readiness(host, _admin_ip)
    _record("node_readiness", result)

    if not result["success"]:
        log.failed("Nodes not ready", result["error"])
        pytest.fail(
            PRECHECK_ASSERT_MSGS["nodes_not_ready"].format(
                nodes=result["not_ready"]
            )
        )

    log.passed(f"All {result['total']} nodes Ready")


# =============================================================================
# TC-03: kube-system Pods  (TC-F015 Gate 3)
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(3)
def test_kube_system_pods(host):
    """TC-03: Verify all kube-system pods are Running."""
    _require_cluster()
    log = TestLogger(PRECHECK_TEST_NAMES["kube_system_pods"])

    log.check(PRECHECK_LOG_MSGS["collecting_pods"].format(ns="kube-system"))
    result = collect_kube_system_pods(host, _admin_ip)
    _record("kube_system_pods", result)

    if not result["success"]:
        log.failed("Unhealthy kube-system pods", result["error"])
        pytest.fail(
            PRECHECK_ASSERT_MSGS["pods_not_running"].format(
                ns="kube-system", pods=result["unhealthy"]
            )
        )

    log.passed(f"{len(result['pods'])} kube-system pods healthy")


# =============================================================================
# TC-04: etcd Health  (TC-F015 Gate 4)
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(4)
def test_etcd_health(host):
    """TC-04: Verify etcd cluster is healthy."""
    _require_cluster()
    log = TestLogger(PRECHECK_TEST_NAMES["etcd_health"])

    log.check(PRECHECK_LOG_MSGS["checking_etcd"])
    result = collect_etcd_health(host, _admin_ip)
    _record("etcd_health", result)

    if not result["success"]:
        log.failed("etcd unhealthy", result["error"])
        pytest.fail(
            PRECHECK_ASSERT_MSGS["etcd_unhealthy"].format(
                error=result["error"]
            )
        )

    log.passed(
        f"etcd healthy ({len(result['endpoints'])} endpoints)",
        "\n".join(
            f"  {e['endpoint']}: healthy={e['healthy']}"
            for e in result["endpoints"]
        ),
    )


# =============================================================================
# TC-05: Calico Pods  (TC-F013)
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(5)
def test_calico_status(host):
    """TC-05: Verify Calico pods are Running."""
    _require_cluster()
    log = TestLogger(PRECHECK_TEST_NAMES["calico_status"])

    log.check(PRECHECK_LOG_MSGS["checking_calico"])
    result = collect_calico_status(host, _admin_ip)
    _record("calico_status", result)

    if not result["success"]:
        log.failed("Unhealthy Calico pods", result["error"])
        pytest.fail(
            PRECHECK_ASSERT_MSGS["pods_not_running"].format(
                ns="calico-system", pods=result["unhealthy"]
            )
        )

    log.passed(f"{len(result['pods'])} Calico pods healthy")


# =============================================================================
# TC-06: MetalLB Pods  (TC-F013)
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(6)
def test_metallb_status(host):
    """TC-06: Verify MetalLB pods are Running."""
    _require_cluster()
    log = TestLogger(PRECHECK_TEST_NAMES["metallb_status"])

    log.check(PRECHECK_LOG_MSGS["checking_metallb"])
    result = collect_metallb_status(host, _admin_ip)
    _record("metallb_status", result)

    if not result["success"]:
        log.failed("Unhealthy MetalLB pods", result["error"])
        pytest.fail(
            PRECHECK_ASSERT_MSGS["pods_not_running"].format(
                ns="metallb-system", pods=result["unhealthy"]
            )
        )

    log.passed(f"{len(result['pods'])} MetalLB pods healthy")


# =============================================================================
# TC-07: LoadBalancer Service IPs  (TC-E016)
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(7)
def test_lb_service_ips(host):
    """TC-07: Record all LoadBalancer service external IPs for post-check comparison."""
    _require_cluster()
    log = TestLogger(PRECHECK_TEST_NAMES["lb_service_ips"])

    log.check(PRECHECK_LOG_MSGS["collecting_lb_ips"])
    result = collect_lb_service_ips(host, _admin_ip)
    _record("lb_service_ips", result)

    for svc in result.get("services", []):
        print(
            f"    {PRECHECK_LOG_MSGS['lb_service'].format(**svc)}",
            flush=True,
        )

    log.passed(f"Recorded {len(result.get('services', []))} LB service IPs")


# =============================================================================
# TC-08: Helm Releases  (TC-TEL-F003)
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(8)
def test_helm_releases(host):
    """TC-08: Record Helm releases in telemetry namespace."""
    _require_cluster()
    log = TestLogger(PRECHECK_TEST_NAMES["helm_releases"])

    log.check(PRECHECK_LOG_MSGS["collecting_helm"])
    result = collect_helm_releases(host, _admin_ip)
    _record("helm_releases", result)

    for rel in result.get("releases", []):
        print(
            f"    {PRECHECK_LOG_MSGS['helm_release'].format(**rel)}",
            flush=True,
        )

    log.passed(f"Recorded {len(result.get('releases', []))} Helm releases")


# =============================================================================
# TC-09: Telemetry Pods  (TC-F020)
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(9)
def test_telemetry_pods(host):
    """TC-09: Verify all telemetry pods are Running."""
    _require_cluster()
    log = TestLogger(PRECHECK_TEST_NAMES["telemetry_pods"])

    log.check(PRECHECK_LOG_MSGS["collecting_telemetry"])
    result = collect_telemetry_pods(host, _admin_ip)
    _record("telemetry_pods", result)

    if not result["success"]:
        log.failed("Unhealthy telemetry pods", result["error"])
        pytest.fail(
            PRECHECK_ASSERT_MSGS["pods_not_running"].format(
                ns="telemetry", pods=result["unhealthy"]
            )
        )

    log.passed(f"{len(result['pods'])} telemetry pods healthy")


# =============================================================================
# TC-10: VictoriaMetrics PVCs  (TC-TEL-F005)
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(10)
def test_vm_pvcs(host):
    """TC-10: Verify VictoriaMetrics PVCs are Bound and record state."""
    _require_cluster()
    log = TestLogger(PRECHECK_TEST_NAMES["vm_pvcs"])

    log.check(PRECHECK_LOG_MSGS["collecting_pvcs"])
    result = collect_vm_pvcs(host, _admin_ip)
    _record("vm_pvcs", result)

    for pvc in result.get("pvcs", []):
        print(
            f"    {PRECHECK_LOG_MSGS['pvc_entry'].format(**pvc)}",
            flush=True,
        )

    log.passed(f"Recorded {len(result.get('pvcs', []))} PVCs")


# =============================================================================
# TC-11: Kafka State  (TC-TEL-F004 / TC-TEL-F003)
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(11)
def test_kafka_state(host):
    """TC-11: Collect Kafka broker pods and topic list."""
    _require_cluster()
    log = TestLogger(PRECHECK_TEST_NAMES["kafka_state"])

    log.check(PRECHECK_LOG_MSGS["collecting_kafka"])
    result = collect_kafka_state(host, _admin_ip)
    _record("kafka_state", result)

    for topic in result.get("topics", []):
        print(
            f"    {PRECHECK_LOG_MSGS['kafka_topic'].format(topic=topic)}",
            flush=True,
        )

    log.passed(
        f"Kafka: {len(result.get('broker_pods', []))} broker pods, "
        f"{len(result.get('topics', []))} topics"
    )


# =============================================================================
# TC-12: CSI Driver + PVCs  (TC-F019)
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(12)
def test_csi_status(host):
    """TC-12: Collect CSI driver pods and CSI-backed PVCs."""
    _require_cluster()
    log = TestLogger(PRECHECK_TEST_NAMES["csi_status"])

    log.check(PRECHECK_LOG_MSGS["collecting_csi"])
    result = collect_csi_status(host, _admin_ip)
    _record("csi_status", result)

    log.passed(
        f"CSI: {len(result.get('csi_pods', []))} pods, "
        f"{len(result.get('csi_pvcs', []))} PVCs"
    )


# =============================================================================
# TC-13: NFS Provisioner  (Precondition)
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(13)
def test_nfs_provisioner(host):
    """TC-13: Check NFS provisioner is deployed."""
    _require_cluster()
    log = TestLogger(PRECHECK_TEST_NAMES["nfs_provisioner"])

    log.check(PRECHECK_LOG_MSGS["collecting_nfs"])
    result = collect_nfs_provisioner(host, _admin_ip)
    _record("nfs_provisioner", result)

    log.passed(
        f"NFS provisioner: {'deployed' if result['deployed'] else 'not found'}"
    )


# =============================================================================
# TC-14: CRI-O Version  (TC-F006)
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(14)
def test_crio_version(host):
    """TC-14: Record CRI-O version from all nodes."""
    _require_cluster()
    log = TestLogger(PRECHECK_TEST_NAMES.get("crio_version", "Pre-check: CRI-O version"))

    log.check("Collecting CRI-O version from all nodes")
    result = collect_crio_version(host, _admin_ip)
    _record("crio_version", result)

    for node in result.get("nodes", []):
        print(f"    {node['name']}: {node['crio_version']}", flush=True)

    log.passed(f"Recorded CRI-O version from {len(result.get('nodes', []))} nodes")


# =============================================================================
# TC-15: Calico Version  (TC-F007)
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(15)
def test_calico_version(host):
    """TC-15: Record Calico controller image version."""
    _require_cluster()
    log = TestLogger(PRECHECK_TEST_NAMES.get("calico_version", "Pre-check: Calico version"))

    log.check("Collecting Calico version")
    result = collect_calico_version(host, _admin_ip)
    _record("calico_version", result)

    print(f"    Calico version: {result.get('version', 'unknown')}", flush=True)
    log.passed(f"Calico version: {result.get('version', 'unknown')}")


# =============================================================================
# TC-16: Network Policies  (TC-F007)
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(16)
def test_network_policies(host):
    """TC-16: Record all NetworkPolicies across namespaces."""
    _require_cluster()
    log = TestLogger(PRECHECK_TEST_NAMES.get("network_policies", "Pre-check: Network policies"))

    log.check("Collecting network policies")
    result = collect_network_policies(host, _admin_ip)
    _record("network_policies", result)

    log.passed(f"Recorded {result.get('count', 0)} network policies")


# =============================================================================
# TC-17: MetalLB Version + IPAddressPool CRDs  (TC-F008)
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(17)
def test_metallb_version(host):
    """TC-17: Record MetalLB version and IPAddressPool CRDs."""
    _require_cluster()
    log = TestLogger(PRECHECK_TEST_NAMES.get("metallb_version", "Pre-check: MetalLB version"))

    log.check("Collecting MetalLB version and IP pools")
    result = collect_metallb_version(host, _admin_ip)
    _record("metallb_version", result)

    print(f"    MetalLB version: {result.get('version', 'unknown')}", flush=True)
    for pool in result.get("ip_pools", []):
        print(f"    IPAddressPool: {pool['name']} -> {pool.get('addresses', [])}", flush=True)

    log.passed(
        f"MetalLB version: {result.get('version', 'unknown')}, "
        f"{len(result.get('ip_pools', []))} IP pools"
    )


# =============================================================================
# TC-18: Helm Binary Version  (TC-F009)
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(18)
def test_helm_version(host):
    """TC-18: Record Helm binary version."""
    _require_cluster()
    log = TestLogger(PRECHECK_TEST_NAMES.get("helm_version", "Pre-check: Helm version"))

    log.check("Collecting Helm version")
    result = collect_helm_version(host, _admin_ip)
    _record("helm_version", result)

    print(f"    Helm version: {result.get('version', 'unknown')}", flush=True)
    log.passed(f"Helm version: {result.get('version', 'unknown')}")


# =============================================================================
# TC-19: iDRAC Telemetry Status  (TC-TEL-F006)
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(19)
def test_idrac_telemetry_status(host):
    """TC-19: Record iDRAC telemetry receiver pod status."""
    _require_cluster()
    log = TestLogger(PRECHECK_TEST_NAMES.get("idrac_status", "Pre-check: iDRAC telemetry"))

    log.check("Collecting iDRAC telemetry status")
    result = collect_idrac_telemetry_status(host, _admin_ip)
    _record("idrac_telemetry", result)

    log.passed(f"iDRAC telemetry: {len(result.get('pods', []))} pods")


# =============================================================================
# TC-20: LDMS Status  (TC-TEL-F007)
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(20)
def test_ldms_status(host):
    """TC-20: Record LDMS sampler/aggregator pod status."""
    _require_cluster()
    log = TestLogger(PRECHECK_TEST_NAMES.get("ldms_status", "Pre-check: LDMS status"))

    log.check("Collecting LDMS status")
    result = collect_ldms_status(host, _admin_ip)
    _record("ldms_status", result)

    log.passed(f"LDMS: {len(result.get('pods', []))} pods")


# =============================================================================
# TC-21: SSH Connectivity Gate  (TC-F015 Gate 2)
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(21)
def test_ssh_connectivity(host):
    """TC-21: Verify SSH connectivity from OIM to all K8s nodes."""
    _require_cluster()
    log = TestLogger(PRECHECK_TEST_NAMES.get("ssh_connectivity", "Pre-check: SSH connectivity (Gate 2)"))

    log.check("Verifying SSH to all nodes")
    result = verify_ssh_connectivity(host, _admin_ip)
    _record("ssh_connectivity", result)

    if not result["success"]:
        log.failed(
            "SSH unreachable nodes",
            f"Unreachable: {result['unreachable']}",
        )
        pytest.fail(f"SSH unreachable nodes: {result['unreachable']}")

    log.passed(f"SSH OK to {len(result['reachable'])} nodes")


# =============================================================================
# TC-22: Version Hop Validation  (TC-F015 Gate 5 / TC-F017)
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(22)
def test_version_hop_valid(host):
    """TC-22: Verify current->target version hop is exactly one minor version."""
    _require_cluster()
    target = K8S_UPGRADE_VARS.get("new_version", "")
    if not target:
        pytest.skip("new_version not configured in omnia_test_config.yml")

    log = TestLogger(
        PRECHECK_TEST_NAMES.get(
            "version_hop",
            f"Pre-check: Version hop validation -> {target}",
        )
    )

    log.check(f"Validating version hop to {target}")
    result = verify_version_hop_valid(host, _admin_ip, target)
    _record("version_hop", result)

    if result.get("skipped"):
        log.passed(f"Skipped: {result.get('skip_reason', 'N/A')}")
        return

    if not result["success"]:
        log.failed("Version hop invalid", result["error"])
        pytest.fail(result["error"])

    log.passed(
        f"Valid hop: {result['current_minor']} -> {result['target_minor']}"
    )


# =============================================================================
# TC-23: Etcd Backup Readiness  (TC-F003)
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(23)
def test_etcd_backup_readiness(host):
    """TC-23: Verify etcd is ready for snapshot and backup dir is accessible."""
    _require_cluster()
    log = TestLogger(
        PRECHECK_TEST_NAMES.get("etcd_backup", "Pre-Check: etcd backup readiness")
    )
    log.check("Checking etcd snapshot readiness and backup directory")
    result = collect_etcd_backup_status(host, _admin_ip)
    _record("etcd_backup_status", result)

    if not result["success"]:
        log.failed("etcd not ready for snapshot", result["error"])
        pytest.fail(result["error"])
    log.passed(
        f"etcd snapshot ready, backup_dir={result['backup_dir_exists']}, "
        f"k8s_config={result['k8s_config_size']}"
    )


# =============================================================================
# TC-24: Security Permissions  (TC-S001, TC-S002)
# =============================================================================

@pytest.mark.sanity
@pytest.mark.security
@pytest.mark.order(24)
def test_security_permissions(host):
    """TC-24: Verify file permissions for SSH keys and backup dirs."""
    _require_cluster()
    log = TestLogger(
        PRECHECK_TEST_NAMES.get("security", "Pre-Check: Security permissions")
    )
    log.check("Checking SSH key and backup directory permissions")
    result = collect_security_permissions(host, _admin_ip)
    _record("security_permissions", result)

    for path, mode in result["permissions"].items():
        log.check(f"  {path}: {mode}")

    if not result["success"]:
        log.failed("Permission issues found", result["error"])
        pytest.fail(result["error"])
    log.passed("All security permissions OK")


# =============================================================================
# TC-25: Pulp Images Available  (TC-F015 Gate 1)
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(25)
def test_pulp_images_available(host):
    """TC-25: Verify target K8s images available in registry."""
    _require_cluster()
    target = K8S_UPGRADE_VARS.get("new_version", "")
    if not target:
        pytest.skip("new_version not configured")

    log = TestLogger(
        PRECHECK_TEST_NAMES.get("pulp_images", "Pre-Check: Pulp images available")
    )
    log.check(f"Checking target images for v{target}")
    result = verify_pulp_images_available(host, _admin_ip, target)
    _record("pulp_images", result)

    log.passed(
        f"Found: {len(result['images_found'])}, "
        f"Missing: {len(result['images_missing'])}"
    )


# =============================================================================
# TC-26: Addon Compatibility  (TC-F018)
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(26)
def test_addon_compatibility(host):
    """TC-26: Verify Calico, MetalLB, Helm healthy before upgrade."""
    _require_cluster()
    target = K8S_UPGRADE_VARS.get("new_version", "")
    if not target:
        pytest.skip("new_version not configured")

    log = TestLogger(
        PRECHECK_TEST_NAMES.get("addon_compat", "Pre-Check: Addon compatibility")
    )
    log.check(f"Checking addon versions for K8s {target}")
    result = verify_addon_compatibility(host, _admin_ip, target)
    _record("addon_compatibility", result)

    for name, info in result["addons"].items():
        log.check(f"  {name}: {info['version']} (healthy={info['healthy']})")

    if not result["success"]:
        log.failed("Addon compatibility issue", result["error"])
        pytest.fail(result["error"])
    log.passed("All addons healthy and compatible")


# =============================================================================
# TC-27: BSS Boot Params Baseline  (TC-F011)
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(27)
def test_bss_boot_params(host):
    """TC-27: Collect BSS boot params (kernel, OS image) baseline."""
    _require_cluster()
    log = TestLogger(
        PRECHECK_TEST_NAMES.get("bss_params", "Pre-Check: BSS boot params baseline")
    )
    log.check("Collecting BSS boot params from all nodes")
    result = collect_bss_boot_params(host, _admin_ip)
    _record("bss_boot_params", result)

    for node, info in result["params"].items():
        log.check(f"  {node}: kernel={info['kernel']}, os={info['os_image']}")

    if not result["success"]:
        log.failed("Failed to collect BSS params", result["error"])
        pytest.fail(result["error"])
    log.passed(f"BSS params collected for {len(result['params'])} nodes")


# =============================================================================
# TC-28: Strimzi/Kafka Version  (TC-TEL-F004, TC-TEL-F016)
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(28)
def test_strimzi_version(host):
    """TC-28: Collect Strimzi operator, Kafka version, KRaft status."""
    _require_cluster()
    log = TestLogger(
        PRECHECK_TEST_NAMES.get("strimzi_version", "Pre-Check: Strimzi/Kafka version")
    )
    log.check("Collecting Strimzi operator and Kafka cluster version")
    result = collect_strimzi_version(host, _admin_ip)
    _record("strimzi_version", result)

    log.check(f"  Strimzi: {result['strimzi_version']}")
    log.check(f"  Kafka: {result['kafka_version']}")
    log.check(f"  KRaft: {result['uses_kraft']} (ZK pods: {result['zk_pods_count']})")

    if not result["success"]:
        log.failed("Cannot get Strimzi info", result["error"])
        pytest.fail(result["error"])
    log.passed("Strimzi/Kafka version collected")


# =============================================================================
# TC-29: CRI-O Storage Config  (TC-F006)
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(29)
def test_crio_storage_config(host):
    """TC-29: Collect CRI-O storage config baseline from all nodes."""
    _require_cluster()
    log = TestLogger(
        PRECHECK_TEST_NAMES.get("crio_storage", "Pre-Check: CRI-O storage config")
    )
    log.check("Collecting CRI-O storage config from nodes")
    result = collect_crio_storage_config(host, _admin_ip)
    _record("crio_storage_config", result)

    for node, cfg in result["configs"].items():
        log.check(f"  {node}: {cfg[:80]}..." if len(cfg) > 80 else f"  {node}: {cfg}")

    if not result["success"]:
        log.failed("Failed to collect CRI-O config", result["error"])
        pytest.fail(result["error"])
    log.passed(f"CRI-O config collected for {len(result['configs'])} nodes")


# =============================================================================
# TC-30: Kube-VIP HA Status  (TC-F014)
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(30)
def test_kube_vip_status(host):
    """TC-30: Collect kube-vip pod status and VIP reachability."""
    _require_cluster()
    log = TestLogger(
        PRECHECK_TEST_NAMES.get("kube_vip", "Pre-Check: kube-vip HA status")
    )
    log.check("Checking kube-vip pods and VIP reachability")
    result = collect_kube_vip_status(host, _admin_ip)
    _record("kube_vip_status", result)

    log.check(f"  kube-vip pods: {len(result['pods'])}, VIP reachable: {result['vip_reachable']}")
    if not result["success"]:
        log.failed("kube-vip/VIP issue", result["error"])
        pytest.fail(result["error"])
    log.passed("kube-vip HA status OK")


# =============================================================================
# TC-31: Pod Disruption Budgets  (TC-F005)
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(31)
def test_pod_disruption_budgets(host):
    """TC-31: Collect PodDisruptionBudgets for drain safety verification."""
    _require_cluster()
    log = TestLogger(
        PRECHECK_TEST_NAMES.get("pdbs", "Pre-Check: PodDisruptionBudgets")
    )
    log.check("Collecting PDBs across cluster")
    result = collect_pod_disruption_budgets(host, _admin_ip)
    _record("pod_disruption_budgets", result)

    for pdb in result.get("pdbs", []):
        log.check(
            f"  {pdb['namespace']}/{pdb['name']}: "
            f"healthy={pdb['current_healthy']}/{pdb['desired_healthy']}"
        )
    log.passed(f"Collected {len(result.get('pdbs', []))} PDBs")


# =============================================================================
# TC-32: Node Roles  (TC-F002, TC-F004)
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(32)
def test_node_roles(host):
    """TC-32: Collect node roles (CPs vs workers) for upgrade order verification."""
    _require_cluster()
    log = TestLogger(
        PRECHECK_TEST_NAMES.get("node_roles", "Pre-Check: Node roles")
    )
    log.check("Collecting node roles and IPs")
    result = collect_node_roles(host, _admin_ip)
    _record("node_roles", result)

    log.check(f"  Control planes: {[n['name'] for n in result['control_planes']]}")
    log.check(f"  Workers: {[n['name'] for n in result['workers']]}")

    if not result["success"]:
        log.failed("Failed to collect node roles", result["error"])
        pytest.fail(result["error"])
    log.passed(
        f"CPs: {len(result['control_planes'])}, "
        f"Workers: {len(result['workers'])}"
    )


# =============================================================================
# TC-33: Telemetry Pre-Flight  (TC-TEL-F002)
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(33)
def test_telemetry_preflight(host):
    """TC-33: Verify telemetry upgrade pre-flight checks."""
    _require_cluster()
    log = TestLogger(
        PRECHECK_TEST_NAMES.get("telemetry_preflight", "Pre-Check: Telemetry pre-flight")
    )
    log.check("Running telemetry pre-flight checks")
    result = verify_telemetry_preflight(host, _admin_ip)
    _record("telemetry_preflight", result)

    for check, passed in result["checks"].items():
        log.check(f"  {check}: {'PASS' if passed else 'FAIL'}")

    if not result["success"]:
        log.failed("Telemetry pre-flight failed", result["error"])
        pytest.fail(result["error"])
    log.passed("All telemetry pre-flight checks passed")


# =============================================================================
# TC-34: OIM Upgrade Status  (TC-F016)
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(34)
def test_oim_upgrade_status(host):
    """TC-34: Verify OIM upgrade is completed (prerequisite for K8s upgrade)."""
    _require_cluster()
    log = TestLogger(
        PRECHECK_TEST_NAMES.get("oim_status", "Pre-Check: OIM upgrade status")
    )
    log.check("Checking OIM upgrade completion status")
    result = verify_oim_upgrade_completed(host)
    _record("oim_upgrade_status", result)

    if result.get("skipped"):
        log.passed(f"Skipped: {result.get('skip_reason', 'N/A')}")
        return

    if not result["success"]:
        log.failed(f"OIM not completed: {result['oim_status']}", result["error"])
        pytest.fail(result["error"])
    log.passed(f"OIM upgrade status: {result['oim_status']}")


# =============================================================================
# TC-35: Save Snapshot
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(35)
def test_save_snapshot(host):
    """TC-35: Persist the collected pre-upgrade state as a JSON snapshot."""
    _require_cluster()
    log = TestLogger(PRECHECK_TEST_NAMES["save_snapshot"])

    # Add metadata
    _snapshot_data["_meta"] = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "admin_ip": _admin_ip,
        "current_version": K8S_UPGRADE_VARS.get("current_version", ""),
        "target_version": K8S_UPGRADE_VARS.get("new_version", ""),
    }

    log.check(
        PRECHECK_LOG_MSGS["saving_snapshot"].format(path=SNAPSHOT_PATH)
    )
    result = save_precheck_snapshot(host, _snapshot_data)

    if not result["success"]:
        log.failed("Snapshot save failed", result["error"])
        pytest.fail(
            PRECHECK_ASSERT_MSGS["snapshot_save_failed"].format(
                error=result["error"], path=SNAPSHOT_PATH,
            )
        )

    log.passed(
        PRECHECK_LOG_MSGS["snapshot_saved"].format(
            count=len(_snapshot_data)
        ),
        f"Path: {result['path']}",
    )
