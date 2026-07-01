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
K8s & Telemetry Upgrade Post-Check Tests.

Loads the pre-upgrade snapshot saved by the Pre_check scenario and validates
every aspect of the cluster after the upgrade:
  - K8s version progression
  - Node readiness
  - System pod health (kube-system, Calico)
  - etcd quorum
  - API server + DNS
  - LB IP preservation (MetalLB)
  - Telemetry stack health (pods, Helm releases)
  - VictoriaMetrics PVC + data preservation
  - Kafka topic preservation
  - CSI PVC preservation

Test-case mapping (from K8s-Telemetry-upgrade-test-cases-v2.xls):
  TC-01  Load snapshot              -> prerequisite
  TC-02  K8s target version         -> TC-F001
  TC-03  Node readiness             -> TC-F013
  TC-04  kube-system pods           -> TC-F013
  TC-05  etcd health                -> TC-F013
  TC-06  API server reachable       -> TC-F013 / TC-F014
  TC-07  DNS resolution             -> TC-F013
  TC-08  Calico pods                -> TC-F013
  TC-09  MetalLB LB IPs preserved   -> TC-E016
  TC-10  Telemetry pods             -> TC-F020
  TC-11  VM PVCs preserved          -> TC-TEL-F005 / TC-TEL-R002
  TC-12  VM data accessible         -> TC-TEL-F005
  TC-13  Kafka topics preserved     -> TC-TEL-F004 / TC-TEL-R003
  TC-14  CSI PVCs preserved         -> TC-F019
  TC-15  Helm releases present      -> TC-TEL-F003
  TC-16  CRI-O at target            -> TC-F006
  TC-17  Calico version upgraded    -> TC-F007
  TC-18  Network policies preserved -> TC-F007
  TC-19  MetalLB version + pools    -> TC-F008
  TC-20  Helm version               -> TC-F009
  TC-21  NFS provisioner running    -> TC-F010
  TC-22  iDRAC telemetry running    -> TC-TEL-F006
  TC-23  LDMS collecting            -> TC-TEL-F007
  TC-24  Upgrade manifest status    -> TC-F013 / TC-TEL-F015
  TC-25  CPs at target version     -> TC-F002
  TC-26  Workers at target version -> TC-F004
  TC-27  Etcd backup artifacts     -> TC-F003
  TC-28  PDBs healthy              -> TC-F005
  TC-29  CRI-O storage preserved   -> TC-F006
  TC-30  BSS boot params updated   -> TC-F011
  TC-31  Kube-VIP HA               -> TC-F014
  TC-32  Strimzi/Kafka upgraded    -> TC-TEL-F004
  TC-33  KRaft migration           -> TC-TEL-F016
  TC-34  Telemetry Phase 1 gate    -> TC-TEL-F008
  TC-35  Security permissions      -> TC-S001 / TC-S002
  TC-36  Idempotency baseline      -> TC-I001 / TC-I002 / TC-TEL-I001/I002
  TC-37  Rollback: nodes at source -> TC-R001 / TC-R006 / TC-R007
  TC-38  Rollback: etcd restored   -> TC-R002 / TC-R003
  TC-39  Rollback: Helm restored   -> TC-R012
  TC-40  Rollback: telemetry OK    -> TC-R007 / TC-TEL-R001
  TC-41  Rollback: MetalLB cleaned -> TC-R009
  TC-42  Rollback: CSI cleaned     -> TC-R010
"""

import pytest

from automation_library.core import TestLogger
from automation_library.telemetry.functions.shared_func import get_admin_ip
from automation_library.upgrade_and_rollback.functions.snapshot_func import (
    load_precheck_snapshot,
)
from automation_library.upgrade_and_rollback.functions.postcheck_func import (
    verify_k8s_target_version,
    verify_all_nodes_ready,
    verify_kube_system_healthy,
    verify_etcd_healthy,
    verify_api_server_reachable,
    verify_dns_resolution,
    verify_calico_healthy,
    verify_metallb_ips_preserved,
    verify_telemetry_pods_running,
    verify_vm_pvcs_preserved,
    verify_vm_data_accessible,
    verify_kafka_topics_preserved,
    verify_csi_pvcs_preserved,
    verify_helm_releases_present,
    verify_crio_at_target,
    verify_calico_version_upgraded,
    verify_network_policies_preserved,
    verify_metallb_version_upgraded,
    verify_helm_at_target,
    verify_nfs_provisioner_running,
    verify_idrac_telemetry_running,
    verify_ldms_collecting,
    verify_new_telemetry_components,
    verify_upgrade_manifest,
    verify_cps_at_target,
    verify_workers_at_target,
    verify_etcd_backup_exists,
    verify_pdbs_healthy,
    verify_crio_storage_preserved,
    verify_bss_params_updated,
    verify_kube_vip_ha,
    verify_strimzi_upgraded,
    verify_kraft_migration,
    verify_telemetry_phase1_gate,
    verify_security_permissions,
    verify_cluster_unchanged,
    verify_rollback_to_source,
    verify_rollback_etcd_restored,
    verify_rollback_helm_restored,
    verify_rollback_telemetry_healthy,
    verify_rollback_metallb_cleaned,
    verify_rollback_csi_cleaned,
)
from automation_library.upgrade_and_rollback.vars import (
    K8S_UPGRADE_VARS,
    SNAPSHOT_PATH,
)
from automation_library.upgrade_and_rollback.messages import (
    POSTCHECK_TEST_NAMES,
    POSTCHECK_LOG_MSGS,
    POSTCHECK_ASSERT_MSGS,
    SKIP_MSGS,
)


# =============================================================================
# MODULE-LEVEL STATE
# =============================================================================

_admin_ip: str = ""
_snapshot_loaded: bool = False
_pre_snapshot: dict = {}


def _require_snapshot():
    """Skip test if pre-upgrade snapshot was not loaded."""
    if not _snapshot_loaded:
        pytest.skip("Pre-upgrade snapshot not loaded — TC-01 did not pass")


# =============================================================================
# TC-01: Load Pre-Upgrade Snapshot
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(1)
def test_load_snapshot(host):
    """
    TC-01: Load the pre-upgrade snapshot and resolve admin IP.
    All subsequent tests depend on this.
    """
    global _admin_ip, _snapshot_loaded, _pre_snapshot

    log = TestLogger(POSTCHECK_TEST_NAMES["load_snapshot"])

    log.check(
        POSTCHECK_LOG_MSGS["loading_snapshot"].format(path=SNAPSHOT_PATH)
    )
    result = load_precheck_snapshot(host)

    if not result["success"]:
        log.failed("Snapshot load failed", result["error"])
        pytest.fail(
            POSTCHECK_ASSERT_MSGS["snapshot_not_found"].format(
                path=SNAPSHOT_PATH
            )
        )

    _pre_snapshot = result["data"]
    _snapshot_loaded = True

    # Get admin IP (from snapshot metadata or PXE mapping)
    meta = _pre_snapshot.get("_meta", {})
    _admin_ip = meta.get("admin_ip", "")
    if not _admin_ip:
        try:
            _admin_ip = get_admin_ip(host, log)
        except (AssertionError, Exception) as exc:
            log.failed("Admin IP lookup failed", str(exc))
            pytest.fail(
                POSTCHECK_ASSERT_MSGS["snapshot_load_failed"].format(
                    error=str(exc), path=SNAPSHOT_PATH,
                )
            )

    ts = meta.get("timestamp", "unknown")
    log.passed(
        POSTCHECK_LOG_MSGS["snapshot_loaded"].format(
            count=len(_pre_snapshot), ts=ts,
        ),
        f"Admin IP: {_admin_ip}\n"
        f"Pre-upgrade version: {meta.get('current_version', 'N/A')}\n"
        f"Target version: {meta.get('target_version', 'N/A')}",
    )


# =============================================================================
# TC-02: K8s Target Version  (TC-F001)
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(2)
def test_k8s_target_version(host):
    """TC-02: Verify all nodes are at the target K8s version."""
    _require_snapshot()
    target = K8S_UPGRADE_VARS.get("new_version", "")
    if not target:
        target = _pre_snapshot.get("_meta", {}).get("target_version", "")
    if not target:
        pytest.skip(SKIP_MSGS["upgrade_not_configured"])

    log = TestLogger(
        POSTCHECK_TEST_NAMES["k8s_target_version"].format(version=target)
    )

    log.check(
        POSTCHECK_LOG_MSGS["checking_version"].format(version=target)
    )
    result = verify_k8s_target_version(host, _admin_ip, target)

    for node in result.get("nodes_ok", []):
        print(
            f"    {POSTCHECK_LOG_MSGS['version_ok'].format(**node)}",
            flush=True,
        )
    for node in result.get("nodes_fail", []):
        print(
            f"    {POSTCHECK_LOG_MSGS['version_fail'].format(name=node['name'], actual=node['version'], expected=target)}",
            flush=True,
        )

    if not result["success"]:
        log.failed("Version mismatch", result["error"])
        pytest.fail(
            POSTCHECK_ASSERT_MSGS["version_mismatch"].format(
                expected=target,
                nodes=[n["name"] for n in result["nodes_fail"]],
            )
        )

    log.passed(f"All {len(result['nodes_ok'])} nodes at {target}")


# =============================================================================
# TC-03: Node Readiness  (TC-F013)
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(3)
def test_node_readiness(host):
    """TC-03: Verify all nodes are in Ready state after upgrade."""
    _require_snapshot()
    log = TestLogger(POSTCHECK_TEST_NAMES["node_readiness"])

    log.check(POSTCHECK_LOG_MSGS["checking_readiness"])
    result = verify_all_nodes_ready(host, _admin_ip)

    if not result["success"]:
        log.failed("Nodes not ready", result["error"])
        pytest.fail(
            POSTCHECK_ASSERT_MSGS["nodes_not_ready"].format(
                nodes=result["not_ready"]
            )
        )

    log.passed(f"All {result['total']} nodes Ready")


# =============================================================================
# TC-04: kube-system Pods  (TC-F013)
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(4)
def test_kube_system_pods(host):
    """TC-04: Verify all kube-system pods are Running after upgrade."""
    _require_snapshot()
    log = TestLogger(POSTCHECK_TEST_NAMES["kube_system_pods"])

    log.check(POSTCHECK_LOG_MSGS["checking_pods"].format(ns="kube-system"))
    result = verify_kube_system_healthy(host, _admin_ip)

    if not result["success"]:
        log.failed("Unhealthy kube-system pods", result["error"])
        pytest.fail(
            POSTCHECK_ASSERT_MSGS["pods_not_running"].format(
                ns="kube-system", pods=result["unhealthy"]
            )
        )

    log.passed(f"{len(result['pods'])} kube-system pods healthy")


# =============================================================================
# TC-05: etcd Health  (TC-F013)
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(5)
def test_etcd_health(host):
    """TC-05: Verify etcd cluster is healthy after upgrade."""
    _require_snapshot()
    log = TestLogger(POSTCHECK_TEST_NAMES["etcd_health"])

    log.check(POSTCHECK_LOG_MSGS["checking_etcd"])
    result = verify_etcd_healthy(host, _admin_ip)

    if not result["success"]:
        log.failed("etcd unhealthy", result["error"])
        pytest.fail(
            POSTCHECK_ASSERT_MSGS["etcd_unhealthy"].format(
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
# TC-06: API Server Reachable  (TC-F013 / TC-F014)
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(6)
def test_api_server(host):
    """TC-06: Verify API server is reachable via kubectl cluster-info."""
    _require_snapshot()
    log = TestLogger(POSTCHECK_TEST_NAMES["api_server"])

    log.check(POSTCHECK_LOG_MSGS["checking_api"])
    result = verify_api_server_reachable(host, _admin_ip)

    if not result["success"]:
        log.failed("API server unreachable", result["error"])
        pytest.fail(POSTCHECK_ASSERT_MSGS["api_unreachable"])

    log.passed("API server reachable", result["output"][:200])


# =============================================================================
# TC-07: DNS Resolution  (TC-F013)
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(7)
def test_dns_resolution(host):
    """TC-07: Verify DNS resolution works inside the cluster."""
    _require_snapshot()
    log = TestLogger(POSTCHECK_TEST_NAMES["dns_resolution"])

    log.check(POSTCHECK_LOG_MSGS["checking_dns"])
    result = verify_dns_resolution(host, _admin_ip)

    if not result["success"]:
        log.failed("DNS resolution failed", result["error"])
        pytest.fail(POSTCHECK_ASSERT_MSGS["dns_failed"])

    log.passed("DNS resolution working")


# =============================================================================
# TC-08: Calico Pods  (TC-F013)
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(8)
def test_calico_healthy(host):
    """TC-08: Verify Calico pods are Running after upgrade."""
    _require_snapshot()
    log = TestLogger(POSTCHECK_TEST_NAMES["calico_healthy"])

    log.check(POSTCHECK_LOG_MSGS["checking_calico"])
    result = verify_calico_healthy(host, _admin_ip)

    if not result["success"]:
        log.failed("Unhealthy Calico pods", result["error"])
        pytest.fail(
            POSTCHECK_ASSERT_MSGS["pods_not_running"].format(
                ns="calico-system", pods=result["unhealthy"]
            )
        )

    log.passed(f"{len(result['pods'])} Calico pods healthy")


# =============================================================================
# TC-09: MetalLB LB IPs Preserved  (TC-E016)
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(9)
def test_metallb_ips(host):
    """TC-09: Verify LoadBalancer service IPs are preserved after upgrade."""
    _require_snapshot()
    pre_services = _pre_snapshot.get("lb_service_ips", {}).get("services", [])
    if not pre_services:
        pytest.skip(SKIP_MSGS["no_lb_services"])

    log = TestLogger(POSTCHECK_TEST_NAMES["metallb_ips"])

    log.check(POSTCHECK_LOG_MSGS["comparing_lb_ips"])
    result = verify_metallb_ips_preserved(host, _admin_ip, _pre_snapshot)

    for svc in result.get("preserved", []):
        print(
            f"    {POSTCHECK_LOG_MSGS['ip_preserved'].format(namespace=svc['namespace'], name=svc['name'], ip=svc['external_ip'])}",
            flush=True,
        )
    for svc in result.get("changed", []):
        print(
            f"    {POSTCHECK_LOG_MSGS['ip_changed'].format(namespace=svc['namespace'], name=svc['name'], old=svc['external_ip'], new=svc['current_ip'])}",
            flush=True,
        )
    for svc in result.get("missing", []):
        print(
            f"    {POSTCHECK_LOG_MSGS['ip_missing'].format(namespace=svc['namespace'], name=svc['name'], old=svc['external_ip'])}",
            flush=True,
        )

    if not result["success"]:
        log.failed("LB IPs changed", result["error"])
        pytest.fail(
            POSTCHECK_ASSERT_MSGS["lb_ips_changed"].format(
                details=result["error"]
            )
        )

    log.passed(f"{len(result['preserved'])} LB IPs preserved")


# =============================================================================
# TC-10: Telemetry Pods  (TC-F020)
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(10)
def test_telemetry_pods(host):
    """TC-10: Verify all telemetry pods are Running after upgrade."""
    _require_snapshot()
    log = TestLogger(POSTCHECK_TEST_NAMES["telemetry_pods"])

    log.check(POSTCHECK_LOG_MSGS["checking_telemetry"])
    result = verify_telemetry_pods_running(host, _admin_ip)

    if not result["success"]:
        log.failed("Unhealthy telemetry pods", result["error"])
        pytest.fail(
            POSTCHECK_ASSERT_MSGS["pods_not_running"].format(
                ns="telemetry", pods=result["unhealthy"]
            )
        )

    log.passed(f"{len(result['pods'])} telemetry pods healthy")


# =============================================================================
# TC-11: VictoriaMetrics PVCs Preserved  (TC-TEL-F005 / TC-TEL-R002)
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(11)
def test_vm_pvcs(host):
    """TC-11: Verify VictoriaMetrics PVCs remain Bound after upgrade."""
    _require_snapshot()
    pre_pvcs = _pre_snapshot.get("vm_pvcs", {}).get("pvcs", [])
    if not pre_pvcs:
        pytest.skip(SKIP_MSGS["no_vm_pvcs"])

    log = TestLogger(POSTCHECK_TEST_NAMES["vm_pvcs"])

    log.check(POSTCHECK_LOG_MSGS["checking_vm_pvcs"])
    result = verify_vm_pvcs_preserved(host, _admin_ip, _pre_snapshot)

    if not result["success"]:
        log.failed("VM PVCs not preserved", result["error"])
        pytest.fail(
            POSTCHECK_ASSERT_MSGS["vm_pvcs_lost"].format(
                details=result["error"]
            )
        )

    log.passed(f"{len(result['preserved'])} VM PVCs preserved")


# =============================================================================
# TC-12: VictoriaMetrics Data Accessible  (TC-TEL-F005)
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(12)
def test_vm_data(host):
    """TC-12: Verify VictoriaMetrics historical TSDB data is accessible."""
    _require_snapshot()
    pre_pvcs = _pre_snapshot.get("vm_pvcs", {}).get("pvcs", [])
    if not pre_pvcs:
        pytest.skip(SKIP_MSGS["vm_not_deployed"])

    log = TestLogger(POSTCHECK_TEST_NAMES["vm_data"])

    log.check(POSTCHECK_LOG_MSGS["checking_vm_data"])
    result = verify_vm_data_accessible(host, _admin_ip)

    if not result["success"]:
        log.failed("VM data not accessible", result["error"])
        pytest.fail(
            POSTCHECK_ASSERT_MSGS["vm_data_lost"].format(
                error=result["error"]
            )
        )

    log.passed(
        f"VM data accessible ({result['sample_count']} series returned)"
    )


# =============================================================================
# TC-13: Kafka Topics Preserved  (TC-TEL-F004 / TC-TEL-R003)
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(13)
def test_kafka_topics(host):
    """TC-13: Verify Kafka topics from pre-upgrade are preserved."""
    _require_snapshot()
    pre_topics = _pre_snapshot.get("kafka_state", {}).get("topics", [])
    if not pre_topics:
        pytest.skip(SKIP_MSGS["no_kafka_topics"])

    log = TestLogger(POSTCHECK_TEST_NAMES["kafka_topics"])

    log.check(POSTCHECK_LOG_MSGS["checking_kafka"])
    result = verify_kafka_topics_preserved(host, _admin_ip, _pre_snapshot)

    for topic in result.get("preserved", []):
        print(
            f"    {POSTCHECK_LOG_MSGS['topic_ok'].format(topic=topic)}",
            flush=True,
        )
    for topic in result.get("missing", []):
        print(
            f"    {POSTCHECK_LOG_MSGS['topic_missing'].format(topic=topic)}",
            flush=True,
        )

    if not result["success"]:
        log.failed("Kafka topics missing", result["error"])
        pytest.fail(
            POSTCHECK_ASSERT_MSGS["kafka_topics_missing"].format(
                topics=result["missing"]
            )
        )

    log.passed(f"{len(result['preserved'])} Kafka topics preserved")


# =============================================================================
# TC-14: CSI PVCs Preserved  (TC-F019)
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(14)
def test_csi_pvcs(host):
    """TC-14: Verify CSI-backed PVCs remain Bound after upgrade."""
    _require_snapshot()
    pre_pvcs = _pre_snapshot.get("csi_status", {}).get("csi_pvcs", [])
    if not pre_pvcs:
        pytest.skip(SKIP_MSGS["no_csi_pvcs"])

    log = TestLogger(POSTCHECK_TEST_NAMES["csi_pvcs"])

    log.check(POSTCHECK_LOG_MSGS["checking_csi"])
    result = verify_csi_pvcs_preserved(host, _admin_ip, _pre_snapshot)

    if not result["success"]:
        log.failed("CSI PVCs lost", result["error"])
        pytest.fail(
            POSTCHECK_ASSERT_MSGS["csi_pvcs_lost"].format(
                details=result["error"]
            )
        )

    log.passed(f"{len(result['preserved'])} CSI PVCs preserved")


# =============================================================================
# TC-15: Helm Releases Present  (TC-TEL-F003)
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(15)
def test_helm_releases(host):
    """TC-15: Verify Helm releases from pre-upgrade are still present."""
    _require_snapshot()
    pre_releases = _pre_snapshot.get("helm_releases", {}).get("releases", [])
    if not pre_releases:
        pytest.skip("No Helm releases in pre-upgrade snapshot")

    log = TestLogger(POSTCHECK_TEST_NAMES["helm_releases"])

    log.check(POSTCHECK_LOG_MSGS["checking_helm"])
    result = verify_helm_releases_present(host, _admin_ip, _pre_snapshot)

    if not result["success"]:
        log.failed("Helm releases missing", result["error"])
        pytest.fail(
            POSTCHECK_ASSERT_MSGS["helm_releases_missing"].format(
                releases=[r["name"] for r in result["missing"]]
            )
        )

    log.passed(f"{len(result['present'])} Helm releases present")


# =============================================================================
# TC-16: CRI-O at Target  (TC-F006)
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(16)
def test_crio_at_target(host):
    """TC-16: Verify CRI-O version matches target K8s minor version."""
    _require_snapshot()
    target = K8S_UPGRADE_VARS.get("new_version", "")
    if not target:
        pytest.skip("new_version not configured")

    log = TestLogger(
        POSTCHECK_TEST_NAMES.get("crio_version", f"Post-check: CRI-O at target {target}")
    )

    log.check(f"Verifying CRI-O at target {target}")
    result = verify_crio_at_target(host, _admin_ip, target)

    if not result["success"]:
        log.failed("CRI-O version mismatch", result["error"])
        pytest.fail(result["error"])

    log.passed(f"CRI-O at target on {len(result['nodes_ok'])} nodes")


# =============================================================================
# TC-17: Calico Version Upgraded  (TC-F007)
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(17)
def test_calico_version_upgraded(host):
    """TC-17: Verify Calico pods healthy and version upgraded."""
    _require_snapshot()
    log = TestLogger(
        POSTCHECK_TEST_NAMES.get("calico_version", "Post-check: Calico version upgraded")
    )

    log.check("Verifying Calico version and pod health")
    result = verify_calico_version_upgraded(host, _admin_ip, _pre_snapshot)

    if not result["success"]:
        log.failed("Calico pods unhealthy after upgrade", result["error"])
        pytest.fail(result["error"])

    log.passed(
        f"Calico healthy: {result['pre_version']} -> {result['post_version']}"
    )


# =============================================================================
# TC-18: Network Policies Preserved  (TC-F007)
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(18)
def test_network_policies_preserved(host):
    """TC-18: Verify all pre-upgrade NetworkPolicies still exist."""
    _require_snapshot()
    pre_policies = _pre_snapshot.get("network_policies", {}).get("policies", [])
    if not pre_policies:
        pytest.skip("No network policies in pre-upgrade snapshot")

    log = TestLogger(
        POSTCHECK_TEST_NAMES.get("network_policies", "Post-check: Network policies preserved")
    )

    log.check("Verifying network policies preserved")
    result = verify_network_policies_preserved(host, _admin_ip, _pre_snapshot)

    if not result["success"]:
        log.failed("Network policies missing", result["error"])
        pytest.fail(result["error"])

    log.passed(f"{len(result['preserved'])} network policies preserved")


# =============================================================================
# TC-19: MetalLB Version + IP Pools  (TC-F008)
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(19)
def test_metallb_version_upgraded(host):
    """TC-19: Verify MetalLB pods healthy and IPAddressPool CRDs preserved."""
    _require_snapshot()
    log = TestLogger(
        POSTCHECK_TEST_NAMES.get("metallb_version", "Post-check: MetalLB version + IP pools")
    )

    log.check("Verifying MetalLB version and IP pools")
    result = verify_metallb_version_upgraded(host, _admin_ip, _pre_snapshot)

    if not result["success"]:
        log.failed("MetalLB verification failed", result["error"])
        pytest.fail(result["error"])

    log.passed(
        f"MetalLB: {result['pre_version']} -> {result['post_version']}, "
        f"pools preserved: {result['pools_preserved']}"
    )


# =============================================================================
# TC-20: Helm Version  (TC-F009)
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(20)
def test_helm_at_target(host):
    """TC-20: Verify Helm binary version after upgrade."""
    _require_snapshot()
    log = TestLogger(
        POSTCHECK_TEST_NAMES.get("helm_version", "Post-check: Helm version")
    )

    log.check("Verifying Helm version")
    result = verify_helm_at_target(host, _admin_ip)

    if not result["success"]:
        log.failed("Helm version check failed", result["error"])
        pytest.fail(result["error"])

    log.passed(f"Helm version: {result['version']}")


# =============================================================================
# TC-21: NFS Provisioner Running  (TC-F010)
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(21)
def test_nfs_provisioner_running(host):
    """TC-21: Verify NFS provisioner running if it was deployed pre-upgrade."""
    _require_snapshot()
    pre_deployed = _pre_snapshot.get("nfs_provisioner", {}).get("deployed", False)
    if not pre_deployed:
        pytest.skip("NFS provisioner was not deployed pre-upgrade")

    log = TestLogger(
        POSTCHECK_TEST_NAMES.get("nfs_provisioner", "Post-check: NFS provisioner")
    )

    log.check("Verifying NFS provisioner")
    result = verify_nfs_provisioner_running(host, _admin_ip, _pre_snapshot)

    if not result["success"]:
        log.failed("NFS provisioner not running", result["error"])
        pytest.fail(result["error"])

    log.passed("NFS provisioner running")


# =============================================================================
# TC-22: iDRAC Telemetry Running  (TC-TEL-F006)
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(22)
def test_idrac_telemetry(host):
    """TC-22: Verify iDRAC telemetry pods are Running after upgrade."""
    _require_snapshot()
    pre_idrac = _pre_snapshot.get("idrac_telemetry", {}).get("pods", [])
    if not pre_idrac:
        pytest.skip("No iDRAC telemetry pods in pre-upgrade snapshot")

    log = TestLogger(
        POSTCHECK_TEST_NAMES.get("idrac_telemetry", "Post-check: iDRAC telemetry")
    )

    log.check("Verifying iDRAC telemetry pods")
    result = verify_idrac_telemetry_running(host, _admin_ip)

    if not result["success"]:
        log.failed("iDRAC telemetry unhealthy", result["error"])
        pytest.fail(result["error"])

    log.passed(f"iDRAC telemetry: {len(result.get('pods', []))} pods healthy")


# =============================================================================
# TC-23: LDMS Running  (TC-TEL-F007)
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(23)
def test_ldms_collecting(host):
    """TC-23: Verify LDMS pods are Running after upgrade."""
    _require_snapshot()
    pre_ldms = _pre_snapshot.get("ldms_status", {}).get("pods", [])
    if not pre_ldms:
        pytest.skip("No LDMS pods in pre-upgrade snapshot")

    log = TestLogger(
        POSTCHECK_TEST_NAMES.get("ldms_status", "Post-check: LDMS collecting")
    )

    log.check("Verifying LDMS pods")
    result = verify_ldms_collecting(host, _admin_ip)

    if not result["success"]:
        log.failed("LDMS pods unhealthy", result["error"])
        pytest.fail(result["error"])

    log.passed(f"LDMS: {len(result.get('pods', []))} pods healthy")


# =============================================================================
# TC-24: Upgrade Manifest Status  (TC-F013 / TC-TEL-F015)
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(24)
def test_upgrade_manifest(host):
    """TC-24: Verify upgrade_manifest.yml shows k8s completed."""
    _require_snapshot()
    log = TestLogger(
        POSTCHECK_TEST_NAMES.get("upgrade_manifest", "Post-check: upgrade_manifest.yml")
    )

    log.check("Checking upgrade_manifest.yml status")
    result = verify_upgrade_manifest(host)

    if not result["success"]:
        log.failed("Upgrade manifest incomplete", result["error"])
        pytest.fail(result["error"])

    log.passed(
        f"Manifest: k8s={result['k8s_status']}, "
        f"telemetry={result['telemetry_status']}"
    )


# =============================================================================
# TC-25: CPs at Target Version  (TC-F002)
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(25)
def test_cps_at_target(host):
    """TC-25: Verify all control-plane nodes at target version and Ready."""
    _require_snapshot()
    target = K8S_UPGRADE_VARS.get("new_version", "")
    if not target:
        pytest.skip("new_version not configured")

    log = TestLogger(
        POSTCHECK_TEST_NAMES.get("cps_at_target", "Post-check: CPs at target version")
    )
    log.check(f"Verifying CPs at v{target}")
    result = verify_cps_at_target(host, _admin_ip, target, _snapshot)

    if not result["success"]:
        log.failed("CPs not at target", result["error"])
        pytest.fail(result["error"])

    log.passed(f"{len(result['cps_ok'])} CPs at target version")


# =============================================================================
# TC-26: Workers at Target Version  (TC-F004)
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(26)
def test_workers_at_target(host):
    """TC-26: Verify all worker nodes at target version and Ready."""
    _require_snapshot()
    target = K8S_UPGRADE_VARS.get("new_version", "")
    if not target:
        pytest.skip("new_version not configured")

    log = TestLogger(
        POSTCHECK_TEST_NAMES.get("workers_at_target", "Post-check: Workers at target version")
    )
    log.check(f"Verifying workers at v{target}")
    result = verify_workers_at_target(host, _admin_ip, target, _snapshot)

    if not result["success"]:
        log.failed("Workers not at target", result["error"])
        pytest.fail(result["error"])

    log.passed(f"{len(result['workers_ok'])} workers at target version")


# =============================================================================
# TC-27: Etcd Backup Artifacts  (TC-F003)
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(27)
def test_etcd_backup_exists(host):
    """TC-27: Verify etcd snapshot and /etc/kubernetes backup created."""
    _require_snapshot()
    log = TestLogger(
        POSTCHECK_TEST_NAMES.get("etcd_backup", "Post-check: etcd backup artifacts")
    )
    log.check("Checking for etcd snapshot and kubernetes backup files")
    result = verify_etcd_backup_exists(host, _admin_ip)

    if not result["success"]:
        log.failed("Backup artifacts missing", result["error"])
        pytest.fail(result["error"])

    log.passed(
        f"snapshot={result['snapshot_exists']}, "
        f"k8s_backup={result['k8s_backup_exists']}"
    )


# =============================================================================
# TC-28: PDBs Healthy  (TC-F005)
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(28)
def test_pdbs_healthy(host):
    """TC-28: Verify PodDisruptionBudgets satisfied after upgrade."""
    _require_snapshot()
    log = TestLogger(
        POSTCHECK_TEST_NAMES.get("pdbs_healthy", "Post-check: PDBs healthy")
    )
    log.check("Checking PDB health after upgrade")
    result = verify_pdbs_healthy(host, _admin_ip)

    if not result["success"]:
        log.failed("PDBs violated", result["error"])
        pytest.fail(result["error"])

    log.passed(f"{len(result['pdbs_ok'])} PDBs satisfied")


# =============================================================================
# TC-29: CRI-O Storage Preserved  (TC-F006)
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(29)
def test_crio_storage_preserved(host):
    """TC-29: Verify CRI-O storage config preserved after upgrade."""
    _require_snapshot()
    log = TestLogger(
        POSTCHECK_TEST_NAMES.get("crio_storage", "Post-check: CRI-O storage config")
    )
    log.check("Comparing CRI-O storage config pre vs post upgrade")
    result = verify_crio_storage_preserved(host, _admin_ip, _snapshot)

    if not result["success"]:
        log.failed("CRI-O config changed", result["error"])
        pytest.fail(result["error"])

    log.passed("CRI-O storage config preserved")


# =============================================================================
# TC-30: BSS Boot Params Updated  (TC-F011)
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(30)
def test_bss_params_updated(host):
    """TC-30: Verify BSS boot params updated after upgrade."""
    _require_snapshot()
    log = TestLogger(
        POSTCHECK_TEST_NAMES.get("bss_params", "Post-check: BSS boot params")
    )
    log.check("Checking BSS boot param changes post upgrade")
    result = verify_bss_params_updated(host, _admin_ip, _snapshot)

    log.passed(
        f"Updated: {len(result['updated_nodes'])}, "
        f"Unchanged: {len(result['unchanged_nodes'])}"
    )


# =============================================================================
# TC-31: Kube-VIP HA  (TC-F014)
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(31)
def test_kube_vip_ha(host):
    """TC-31: Verify kube-vip running and VIP reachable after upgrade."""
    _require_snapshot()
    log = TestLogger(
        POSTCHECK_TEST_NAMES.get("kube_vip_ha", "Post-check: kube-vip HA")
    )
    log.check("Checking kube-vip pods and VIP after upgrade")
    result = verify_kube_vip_ha(host, _admin_ip)

    if not result["success"]:
        log.failed("kube-vip/VIP issue", result["error"])
        pytest.fail(result["error"])

    log.passed(
        f"kube-vip pods: {len(result['pods'])}, "
        f"VIP reachable: {result['vip_reachable']}"
    )


# =============================================================================
# TC-32: Strimzi Upgraded  (TC-TEL-F004)
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(32)
def test_strimzi_upgraded(host):
    """TC-32: Verify Strimzi operator upgraded, Kafka brokers running."""
    _require_snapshot()
    log = TestLogger(
        POSTCHECK_TEST_NAMES.get("strimzi_upgraded", "Post-check: Strimzi/Kafka upgraded")
    )
    log.check("Verifying Strimzi operator and Kafka brokers post upgrade")
    result = verify_strimzi_upgraded(host, _admin_ip, _snapshot)

    log.check(f"  Strimzi: {result['pre_strimzi']} -> {result['post_strimzi']}")
    log.check(f"  Kafka: {result['pre_kafka']} -> {result['post_kafka']}")

    if not result["success"]:
        log.failed("Strimzi/Kafka issue", result["error"])
        pytest.fail(result["error"])

    log.passed("Strimzi/Kafka upgraded and healthy")


# =============================================================================
# TC-33: KRaft Migration  (TC-TEL-F016)
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(33)
def test_kraft_migration(host):
    """TC-33: Verify Kafka uses KRaft (no ZooKeeper pods)."""
    _require_snapshot()
    log = TestLogger(
        POSTCHECK_TEST_NAMES.get("kraft_migration", "Post-check: KRaft migration")
    )
    log.check("Checking KRaft migration status")
    result = verify_kraft_migration(host, _admin_ip)

    log.check(f"  KRaft: {result['uses_kraft']}, ZK pods: {result['zk_pods_count']}")

    if not result["success"]:
        log.failed("KRaft migration incomplete", result["error"])
        pytest.fail(result["error"])

    log.passed("Kafka using KRaft (no ZooKeeper)")


# =============================================================================
# TC-34: Telemetry Phase 1 Gate  (TC-TEL-F008)
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(34)
def test_telemetry_phase1_gate(host):
    """TC-34: Verify Phase 1 gate: telemetry pods, Kafka, VM all healthy."""
    _require_snapshot()
    log = TestLogger(
        POSTCHECK_TEST_NAMES.get("phase1_gate", "Post-check: Telemetry Phase 1 gate")
    )
    log.check("Running Phase 1 validation gate checks")
    result = verify_telemetry_phase1_gate(host, _admin_ip)

    for check, passed in result["checks"].items():
        log.check(f"  {check}: {'PASS' if passed else 'FAIL'}")

    if not result["success"]:
        log.failed("Phase 1 gate failed", result["error"])
        pytest.fail(result["error"])

    log.passed("Phase 1 gate: all checks passed")


# =============================================================================
# TC-35: Security Permissions  (TC-S001, TC-S002)
# =============================================================================

@pytest.mark.sanity
@pytest.mark.security
@pytest.mark.order(35)
def test_security_permissions(host):
    """TC-35: Verify backup dir (0700), SSH keys (0600) after upgrade."""
    _require_snapshot()
    log = TestLogger(
        POSTCHECK_TEST_NAMES.get("security", "Post-check: Security permissions")
    )
    log.check("Checking security permissions after upgrade")
    result = verify_security_permissions(host, _admin_ip)

    for path, mode in result["permissions"].items():
        log.check(f"  {path}: {mode}")

    if not result["success"]:
        log.failed("Permission issues", result["error"])
        pytest.fail(result["error"])

    log.passed("Security permissions OK")


# =============================================================================
# TC-36: Idempotency - Cluster Unchanged  (TC-I001, TC-I002, TC-TEL-I001/I002)
# =============================================================================

@pytest.mark.sanity
@pytest.mark.idempotency
@pytest.mark.order(36)
def test_cluster_idempotency(host):
    """TC-36: Verify cluster state consistent (idempotency baseline)."""
    _require_snapshot()
    log = TestLogger(
        POSTCHECK_TEST_NAMES.get("idempotency", "Post-check: Cluster idempotency")
    )
    log.check("Comparing cluster state for idempotency verification")
    result = verify_cluster_unchanged(host, _admin_ip, _snapshot)

    log.check(f"  Versions match: {result['node_versions_match']}")
    log.check(f"  Pod count match: {result['pod_count_match']}")

    log.passed(
        f"Versions match={result['node_versions_match']}, "
        f"Pod count match={result['pod_count_match']}"
    )


# =============================================================================
# TC-37: Rollback - All Nodes at Source  (TC-R001, TC-R006, TC-R007)
# =============================================================================

@pytest.mark.sanity
@pytest.mark.rollback
@pytest.mark.order(37)
def test_rollback_to_source(host):
    """TC-37: Verify all nodes reverted to source version after rollback."""
    _require_snapshot()
    log = TestLogger(
        POSTCHECK_TEST_NAMES.get("rollback_source", "Post-rollback: Nodes at source version")
    )
    log.check("Checking if all nodes reverted to pre-upgrade version")
    result = verify_rollback_to_source(host, _admin_ip, _snapshot)

    if not result["success"]:
        log.failed("Rollback incomplete", result["error"])
        pytest.fail(result["error"])

    log.passed(f"{len(result['nodes_at_source'])} nodes at source {result.get('source_version', '')}")


# =============================================================================
# TC-38: Rollback - Etcd Restored  (TC-R002, TC-R003)
# =============================================================================

@pytest.mark.sanity
@pytest.mark.rollback
@pytest.mark.order(38)
def test_rollback_etcd_restored(host):
    """TC-38: Verify etcd healthy after rollback restore."""
    _require_snapshot()
    log = TestLogger(
        POSTCHECK_TEST_NAMES.get("rollback_etcd", "Post-rollback: etcd restored")
    )
    log.check("Checking etcd health after rollback")
    result = verify_rollback_etcd_restored(host, _admin_ip)

    if not result["success"]:
        log.failed("etcd unhealthy after rollback", result["error"])
        pytest.fail(result["error"])

    log.passed("etcd healthy after rollback")


# =============================================================================
# TC-39: Rollback - Helm Restored  (TC-R012)
# =============================================================================

@pytest.mark.sanity
@pytest.mark.rollback
@pytest.mark.order(39)
def test_rollback_helm_restored(host):
    """TC-39: Verify Helm binary restored to pre-upgrade version."""
    _require_snapshot()
    log = TestLogger(
        POSTCHECK_TEST_NAMES.get("rollback_helm", "Post-rollback: Helm restored")
    )
    log.check("Checking Helm version after rollback")
    result = verify_rollback_helm_restored(host, _admin_ip, _snapshot)

    log.check(f"  Pre: {result['pre_version']} -> Post: {result['post_version']}")

    if not result["success"]:
        log.failed("Helm not restored", result["error"])
        pytest.fail(result["error"])

    log.passed(f"Helm at {result['post_version']}")


# =============================================================================
# TC-40: Rollback - Telemetry Healthy  (TC-R007, TC-TEL-R001)
# =============================================================================

@pytest.mark.sanity
@pytest.mark.rollback
@pytest.mark.order(40)
def test_rollback_telemetry_healthy(host):
    """TC-40: Verify telemetry stack healthy after rollback."""
    _require_snapshot()
    log = TestLogger(
        POSTCHECK_TEST_NAMES.get("rollback_telemetry", "Post-rollback: Telemetry healthy")
    )
    log.check("Checking telemetry health after rollback")
    result = verify_rollback_telemetry_healthy(host, _admin_ip, _snapshot)

    if not result["success"]:
        log.failed("Telemetry unhealthy after rollback", result["error"])
        pytest.fail(result["error"])

    log.passed(
        f"Pods healthy={result['pods_healthy']}, "
        f"VM preserved={result['vm_preserved']}, "
        f"Kafka preserved={result['kafka_preserved']}"
    )


# =============================================================================
# TC-41: Rollback - MetalLB Cleaned  (TC-R009)
# =============================================================================

@pytest.mark.sanity
@pytest.mark.rollback
@pytest.mark.order(41)
def test_rollback_metallb_cleaned(host):
    """TC-41: Verify MetalLB healthy after rollback (stale IPs cleaned)."""
    _require_snapshot()
    log = TestLogger(
        POSTCHECK_TEST_NAMES.get("rollback_metallb", "Post-rollback: MetalLB cleaned")
    )
    log.check("Checking MetalLB health after rollback")
    result = verify_rollback_metallb_cleaned(host, _admin_ip)

    if not result["success"]:
        log.failed("MetalLB unhealthy", result["error"])
        pytest.fail(result["error"])

    log.passed("MetalLB healthy after rollback")


# =============================================================================
# TC-42: Rollback - CSI Cleaned  (TC-R010)
# =============================================================================

@pytest.mark.sanity
@pytest.mark.rollback
@pytest.mark.order(42)
def test_rollback_csi_cleaned(host):
    """TC-42: Verify no stale CSI VolumeAttachments after rollback."""
    _require_snapshot()
    log = TestLogger(
        POSTCHECK_TEST_NAMES.get("rollback_csi", "Post-rollback: CSI cleaned")
    )
    log.check("Checking for stale VolumeAttachments after rollback")
    result = verify_rollback_csi_cleaned(host, _admin_ip)

    if not result["success"]:
        log.failed("Stale VolumeAttachments found", result["error"])
        pytest.fail(result["error"])

    log.passed("No stale VolumeAttachments")
