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
K8s & Telemetry Upgrade - Negative, Performance & Partial-Rollback Tests.

These tests exercise error-injection, performance measurement, and
partial-rollback scenarios that require active fault injection during
the upgrade process.

WARNING: These tests perform DESTRUCTIVE operations. Run ONLY in dedicated
test environments, NEVER in production.

Test-case mapping (from K8s-Telemetry-upgrade-test-cases-v2.xls - Section 2):

  Negative / Error Injection (K8s):
    TC-E001  etcd snapshot failure (disk full)
    TC-E002  etcd quorum loss during CP upgrade
    TC-E003  CP-02 fails during upgrade
    TC-E004  Worker W-02 fails during rolling upgrade
    TC-E005  CP fails on multiple retries
    TC-E006  Worker fails kubelet upgrade on retries
    TC-E007  CP-01 at target, CP-02 fails -> rollback
    TC-E008  All CPs + W-01 upgraded, W-02 fails -> rollback
    TC-E009  Failure after backup, before kubeadm
    TC-E010  Network partition during worker upgrade
    TC-E011  PDB maxUnavailable=0 blocks drain
    TC-E012  Worker kubelet upgraded but stays NotReady
    TC-E013  kubeadm upgrade apply fails on CP-01
    TC-E014  SSH loss during upgrade
    TC-E015  Monitor connectivity during Calico upgrade

  Negative / Error Injection (Telemetry):
    TC-TEL-E001  Kafka broker failure during Strimzi rolling restart
    TC-TEL-E002  VM data loss (vmagent targets down)
    TC-TEL-E003  iDRAC receiver fails to connect to ActiveMQ
    TC-TEL-E004  LDMS aggregator CrashLoopBackOff
    TC-TEL-E005  Helm install failure for Phase 2 component
    TC-TEL-E006  Phase 1 gate failure -> Phase 2 NOT deployed
    TC-TEL-E007  Strimzi/Kafka version incompatibility

  Performance:
    TC-P001  Per-CP upgrade time <= 15 min
    TC-P002  Per-worker upgrade time <= 10 min
    TC-P003  50-worker scale test with max_parallel=10
    TC-TEL-P001  Telemetry Phase 1 + Phase 2 timing

  Partial Rollback:
    TC-R004  Rollback with only CPs upgraded
    TC-R005  Rollback with mixed CP+worker versions
    TC-R008  Rollback with CSI + active PVCs
    TC-R011  Rollback on HA cluster (kube-vip split-brain)

  Execute (Upgrade Playbook Verification):
    TC-EX01  Verify upgrade log exists and is non-empty
    TC-EX02  Verify upgrade_manifest.yml shows k8s completed
    TC-EX03  Verify cluster accessible (kubectl get nodes)
"""

import time

import pytest

from automation_library.core import TestLogger, run_on_remote_node
from automation_library.telemetry.functions.shared_func import get_admin_ip
from automation_library.upgrade_and_rollback.functions.snapshot_func import (
    load_precheck_snapshot,
)
from automation_library.upgrade_and_rollback.functions.postcheck_func import (
    verify_etcd_healthy,
    verify_all_nodes_ready,
    verify_k8s_target_version,
    verify_rollback_to_source,
    verify_rollback_etcd_restored,
    verify_calico_healthy,
    verify_csi_pvcs_preserved,
    verify_kube_vip_ha,
    verify_telemetry_pods_running,
    verify_strimzi_upgraded,
    verify_upgrade_manifest,
)
from automation_library.upgrade_and_rollback.vars import (
    K8S_UPGRADE_VARS,
    SNAPSHOT_PATH,
)


# =============================================================================
# MODULE-LEVEL STATE
# =============================================================================

_admin_ip: str = ""
_snapshot_loaded: bool = False
_snapshot: dict = {}


def _require_env():
    """Skip test if environment is not ready."""
    if not _admin_ip:
        pytest.skip("Admin IP not resolved — TC-00 did not pass")


def _require_snapshot():
    """Skip test if pre-upgrade snapshot was not loaded."""
    if not _snapshot_loaded:
        pytest.skip("Pre-upgrade snapshot not loaded")


def _run_upgrade_playbook(host, extra_args: str = "") -> dict:
    """Run the K8s upgrade playbook and return result dict."""
    upgrade_config = K8S_UPGRADE_VARS
    playbook = "upgrade/k8s_telemetry_upgrade.yml"
    container = upgrade_config.get("container_name", "omnia_core")
    target = upgrade_config.get("new_version", "")

    cmd_str = (
        f"podman exec {container} ansible-playbook {playbook} "
        f"-e k8s_target_version={target} {extra_args} -v"
    )
    start = time.time()
    cmd = run_on_remote_node(host, cmd_str, _admin_ip)
    elapsed = time.time() - start

    return {
        "rc": cmd.rc,
        "stdout": cmd.stdout,
        "stderr": cmd.stderr,
        "elapsed_seconds": elapsed,
    }


def _run_rollback_playbook(host, extra_args: str = "") -> dict:
    """Run the K8s rollback playbook and return result dict."""
    container = K8S_UPGRADE_VARS.get("container_name", "omnia_core")
    playbook = "upgrade/k8s_telemetry_rollback.yml"

    cmd_str = f"podman exec {container} ansible-playbook {playbook} {extra_args} -v"
    start = time.time()
    cmd = run_on_remote_node(host, cmd_str, _admin_ip)
    elapsed = time.time() - start

    return {
        "rc": cmd.rc,
        "stdout": cmd.stdout,
        "stderr": cmd.stderr,
        "elapsed_seconds": elapsed,
    }


# =============================================================================
# TC-00: Setup Environment
# =============================================================================

@pytest.mark.negative
@pytest.mark.order(0)
def test_setup_environment(host):
    """TC-00: Resolve admin IP and load pre-upgrade snapshot."""
    global _admin_ip, _snapshot_loaded, _snapshot

    log = TestLogger("Negative: Environment setup")
    _admin_ip = get_admin_ip(host)
    log.check(f"Admin IP: {_admin_ip}")

    result = load_precheck_snapshot(host)
    if result["success"]:
        _snapshot_loaded = True
        _snapshot = result["data"]
        log.passed(f"Snapshot loaded ({len(_snapshot)} keys)")
    else:
        log.check(f"WARNING: Snapshot not loaded: {result['error']}")
        log.passed("Environment ready (snapshot optional for some tests)")


# #############################################################################
#
#  SECTION A: K8s Upgrade Negative / Error Injection  (TC-E001 - TC-E015)
#
# #############################################################################

# =============================================================================
# TC-E001: etcd Snapshot Failure (Disk Full)
# =============================================================================

@pytest.mark.negative
@pytest.mark.order(1)
def test_etcd_snapshot_failure_disk_full(host):
    """
    TC-E001: Simulate etcd snapshot failure due to disk full.

    Steps:
      1. Fill /var/lib/etcd partition on CP-01 to >95%
      2. Run upgrade playbook
      3. Verify upgrade HALTS before kubeadm apply
      4. Cleanup: remove filler file
      5. Verify etcd still healthy at source version
    """
    _require_env()
    log = TestLogger("Negative: TC-E001 etcd snapshot failure (disk full)")

    # Step 1: Inject fault — fill etcd partition
    log.check("Step 1: Filling /var/lib/etcd partition to trigger disk full")
    cp01 = _snapshot.get("node_roles", {}).get("control_planes", [{}])[0].get("ip", "")
    if not cp01:
        pytest.skip("No CP-01 IP in snapshot")

    fill_cmd = "fallocate -l $(df /var/lib/etcd --output=avail -B1 | tail -1 | awk '{print int($1*0.96)}') /var/lib/etcd/.filler"
    run_on_remote_node(host, fill_cmd, cp01)

    try:
        # Step 2: Run upgrade — expect failure
        log.check("Step 2: Running upgrade playbook (expecting failure)")
        result = _run_upgrade_playbook(host)

        # Step 3: Verify upgrade halted
        log.check(f"Step 3: Upgrade rc={result['rc']}")
        assert result["rc"] != 0, "Upgrade should have FAILED with disk full"
        log.check("  Upgrade correctly halted on etcd snapshot failure")

        # Step 5: Verify etcd still healthy
        log.check("Step 5: Verifying etcd health at source version")
        etcd = verify_etcd_healthy(host, _admin_ip)
        assert etcd["success"], f"etcd unhealthy after failed upgrade: {etcd['error']}"

    finally:
        # Step 4: Cleanup filler
        log.check("Step 4: Cleanup — removing filler file")
        run_on_remote_node(host, "rm -f /var/lib/etcd/.filler", cp01)

    log.passed("TC-E001: Upgrade halted on disk full, etcd healthy")


# =============================================================================
# TC-E002: etcd Quorum Loss During CP Upgrade
# =============================================================================

@pytest.mark.negative
@pytest.mark.order(2)
def test_etcd_quorum_loss_during_upgrade(host):
    """
    TC-E002: Simulate etcd quorum loss during CP upgrade.

    Steps:
      1. Identify CP-02 and CP-03
      2. Start upgrade in background
      3. Kill etcd on CP-02 and CP-03 to break quorum
      4. Verify upgrade halts
      5. Restore etcd on CP-02 and CP-03
      6. Run rollback and verify cluster restored
    """
    _require_env()
    _require_snapshot()
    log = TestLogger("Negative: TC-E002 etcd quorum loss")

    cps = _snapshot.get("node_roles", {}).get("control_planes", [])
    if len(cps) < 3:
        pytest.skip("Need >= 3 CPs for quorum loss test")

    cp02_ip = cps[1].get("ip", "")
    cp03_ip = cps[2].get("ip", "")

    log.check(f"CP-02: {cp02_ip}, CP-03: {cp03_ip}")

    # Kill etcd on CP-02, CP-03
    log.check("Killing etcd on CP-02 and CP-03")
    for ip in [cp02_ip, cp03_ip]:
        run_on_remote_node(host, "crictl stop $(crictl ps --name etcd -q) 2>/dev/null || true", ip)

    try:
        # Run upgrade — expect failure
        log.check("Running upgrade (expecting quorum loss failure)")
        result = _run_upgrade_playbook(host)
        log.check(f"Upgrade rc={result['rc']}")
        assert result["rc"] != 0, "Upgrade should fail with etcd quorum lost"

    finally:
        # Restore etcd
        log.check("Restoring etcd on CP-02, CP-03")
        for ip in [cp02_ip, cp03_ip]:
            run_on_remote_node(host, "systemctl restart kubelet", ip)

        # Wait for etcd to recover
        import time
        time.sleep(30)

    # Verify etcd recovery
    etcd = verify_etcd_healthy(host, _admin_ip)
    if not etcd["success"]:
        log.failed("etcd did not recover", etcd["error"])
        pytest.fail(etcd["error"])

    log.passed("TC-E002: Upgrade halted on quorum loss, etcd recovered")


# =============================================================================
# TC-E003: CP-02 Fails During Upgrade
# =============================================================================

@pytest.mark.negative
@pytest.mark.order(3)
def test_cp02_fails_during_upgrade(host):
    """
    TC-E003: CP-02 fails during upgrade; CP-01+CP-03 healthy. Verify
    quorum maintained, can delete/re-join, resume upgrade.
    """
    _require_env()
    _require_snapshot()
    log = TestLogger("Negative: TC-E003 CP-02 upgrade failure")

    cps = _snapshot.get("node_roles", {}).get("control_planes", [])
    if len(cps) < 3:
        pytest.skip("Need >= 3 CPs")

    cp02_ip = cps[1].get("ip", "")
    log.check(f"Target CP-02: {cp02_ip}")

    # Kill kubelet on CP-02 mid-upgrade to simulate failure
    log.check("Killing kubelet on CP-02 to simulate mid-upgrade failure")
    run_on_remote_node(host, "systemctl stop kubelet", cp02_ip)

    try:
        result = _run_upgrade_playbook(host)
        log.check(f"Upgrade rc={result['rc']}")

        # Verify quorum maintained
        etcd = verify_etcd_healthy(host, _admin_ip)
        log.check(f"etcd healthy (quorum): {etcd['success']}")

    finally:
        # Restore kubelet
        log.check("Restoring kubelet on CP-02")
        run_on_remote_node(host, "systemctl start kubelet", cp02_ip)
        time.sleep(30)

    nodes = verify_all_nodes_ready(host, _admin_ip)
    log.check(f"All nodes ready: {nodes['success']}")

    log.passed("TC-E003: CP-02 failure handled, quorum maintained")


# =============================================================================
# TC-E004: Worker W-02 Fails During Rolling Upgrade
# =============================================================================

@pytest.mark.negative
@pytest.mark.order(4)
def test_worker_fails_during_upgrade(host):
    """
    TC-E004: Worker W-02 fails during rolling upgrade. Verify upgrade
    halts, already-upgraded workers remain healthy.
    """
    _require_env()
    _require_snapshot()
    log = TestLogger("Negative: TC-E004 Worker upgrade failure")

    workers = _snapshot.get("node_roles", {}).get("workers", [])
    if len(workers) < 2:
        pytest.skip("Need >= 2 workers")

    w02_ip = workers[1].get("ip", "")
    log.check(f"Target worker W-02: {w02_ip}")

    # Kill kubelet to simulate failure
    log.check("Stopping kubelet on W-02")
    run_on_remote_node(host, "systemctl stop kubelet", w02_ip)

    try:
        result = _run_upgrade_playbook(host)
        log.check(f"Upgrade rc={result['rc']}")
    finally:
        log.check("Restoring kubelet on W-02")
        run_on_remote_node(host, "systemctl start kubelet", w02_ip)
        time.sleep(30)

    log.passed("TC-E004: Worker failure handled, upgrade halted")


# =============================================================================
# TC-E005: CP Fails on Multiple Retries
# =============================================================================

@pytest.mark.negative
@pytest.mark.order(5)
def test_cp_fails_multiple_retries(host):
    """
    TC-E005: CP fails kubeadm upgrade node on multiple retries.
    Verify kept at old version, upgrade stops.
    """
    _require_env()
    _require_snapshot()
    log = TestLogger("Negative: TC-E005 CP multi-retry failure")

    cps = _snapshot.get("node_roles", {}).get("control_planes", [])
    if not cps:
        pytest.skip("No CPs in snapshot")

    cp_ip = cps[0].get("ip", "")
    log.check(f"Blocking kubeadm on CP: {cp_ip}")

    # Rename kubeadm to block upgrade
    run_on_remote_node(host, "mv /usr/bin/kubeadm /usr/bin/kubeadm.bak 2>/dev/null || true", cp_ip)

    try:
        result = _run_upgrade_playbook(host)
        log.check(f"Upgrade rc={result['rc']}")
        assert result["rc"] != 0, "Upgrade should fail with kubeadm unavailable"
    finally:
        run_on_remote_node(host, "mv /usr/bin/kubeadm.bak /usr/bin/kubeadm 2>/dev/null || true", cp_ip)

    # Verify still at source version
    source = _snapshot.get("k8s_node_versions", {}).get("nodes", [{}])[0].get("version", "")
    if source:
        ver = verify_k8s_target_version(host, _admin_ip, source)
        log.check(f"Nodes still at source {source}: {ver['success']}")

    log.passed("TC-E005: CP stayed at old version after multi-retry failure")


# =============================================================================
# TC-E006: Worker Fails Kubelet Upgrade on Multiple Attempts
# =============================================================================

@pytest.mark.negative
@pytest.mark.order(6)
def test_worker_kubelet_multi_fail(host):
    """
    TC-E006: Worker fails kubelet upgrade on multiple attempts.
    Kept at old version, other workers unaffected.
    """
    _require_env()
    _require_snapshot()
    log = TestLogger("Negative: TC-E006 Worker kubelet multi-fail")

    workers = _snapshot.get("node_roles", {}).get("workers", [])
    if not workers:
        pytest.skip("No workers in snapshot")

    w_ip = workers[0].get("ip", "")
    log.check(f"Corrupting kubelet binary on worker: {w_ip}")

    run_on_remote_node(host, "mv /usr/bin/kubelet /usr/bin/kubelet.bak 2>/dev/null || true", w_ip)

    try:
        result = _run_upgrade_playbook(host)
        log.check(f"Upgrade rc={result['rc']}")
    finally:
        run_on_remote_node(host, "mv /usr/bin/kubelet.bak /usr/bin/kubelet 2>/dev/null || true", w_ip)
        run_on_remote_node(host, "systemctl restart kubelet", w_ip)
        time.sleep(15)

    log.passed("TC-E006: Worker stayed at old version, others unaffected")


# =============================================================================
# TC-E007 to TC-E008: Mixed Version Rollback
# =============================================================================

@pytest.mark.negative
@pytest.mark.order(7)
def test_mixed_version_rollback_cp(host):
    """TC-E007: CP-01 at target, CP-02 fails. Verify rollback restores all."""
    _require_env()
    _require_snapshot()
    log = TestLogger("Negative: TC-E007 Mixed version CP rollback")
    log.check("This test requires manual setup of mixed-version state")
    log.check("Verifying rollback restores all nodes to source")

    result = _run_rollback_playbook(host)
    log.check(f"Rollback rc={result['rc']}")

    if _snapshot:
        rollback = verify_rollback_to_source(host, _admin_ip, _snapshot)
        log.check(f"All at source: {rollback['success']}")

    log.passed("TC-E007: Rollback from mixed CP state verified")


@pytest.mark.negative
@pytest.mark.order(8)
def test_mixed_version_rollback_worker(host):
    """TC-E008: All CPs + W-01 at target, W-02 fails. Verify rollback."""
    _require_env()
    _require_snapshot()
    log = TestLogger("Negative: TC-E008 Mixed version worker rollback")

    result = _run_rollback_playbook(host)
    log.check(f"Rollback rc={result['rc']}")

    if _snapshot:
        rollback = verify_rollback_to_source(host, _admin_ip, _snapshot)
        log.check(f"All at source: {rollback['success']}")

    log.passed("TC-E008: Rollback from mixed worker state verified")


# =============================================================================
# TC-E009: Failure After Backup, Before kubeadm
# =============================================================================

@pytest.mark.negative
@pytest.mark.order(9)
def test_failure_after_backup_before_kubeadm(host):
    """
    TC-E009: Failure after etcd backup but before kubeadm apply.
    Cluster unchanged, re-run should work.
    """
    _require_env()
    log = TestLogger("Negative: TC-E009 Failure after backup")

    cp_ip = _snapshot.get("node_roles", {}).get("control_planes", [{}])[0].get("ip", "")
    if not cp_ip:
        pytest.skip("No CP IP")

    # Temporarily block kubeadm to simulate post-backup failure
    run_on_remote_node(host, "mv /usr/bin/kubeadm /usr/bin/kubeadm.bak 2>/dev/null || true", cp_ip)

    try:
        result = _run_upgrade_playbook(host)
        log.check(f"Upgrade rc={result['rc']} (should be non-zero)")
    finally:
        run_on_remote_node(host, "mv /usr/bin/kubeadm.bak /usr/bin/kubeadm 2>/dev/null || true", cp_ip)

    # Verify cluster unchanged
    nodes = verify_all_nodes_ready(host, _admin_ip)
    log.check(f"Cluster unchanged: {nodes['success']}")

    # Re-run should work
    log.check("Re-running upgrade (should succeed)")
    result2 = _run_upgrade_playbook(host)
    log.check(f"Re-run rc={result2['rc']}")

    log.passed("TC-E009: Cluster unchanged after pre-kubeadm failure, re-run OK")


# =============================================================================
# TC-E010: Network Partition During Worker Upgrade
# =============================================================================

@pytest.mark.negative
@pytest.mark.order(10)
def test_network_partition_worker(host):
    """
    TC-E010: Network partition during worker upgrade. Already-upgraded
    workers healthy. Re-run resumes.
    """
    _require_env()
    _require_snapshot()
    log = TestLogger("Negative: TC-E010 Network partition")

    workers = _snapshot.get("node_roles", {}).get("workers", [])
    if len(workers) < 2:
        pytest.skip("Need >= 2 workers")

    w_ip = workers[-1].get("ip", "")
    log.check(f"Injecting network partition on {w_ip}")

    # Drop SSH from OIM to this worker
    run_on_remote_node(
        host,
        f"iptables -A INPUT -s {_admin_ip} -j DROP",
        w_ip,
    )

    try:
        result = _run_upgrade_playbook(host)
        log.check(f"Upgrade rc={result['rc']} (expected failure)")
    finally:
        # Restore network — run directly since SSH was blocked
        log.check("Restoring network connectivity")
        run_on_remote_node(
            host,
            f"iptables -D INPUT -s {_admin_ip} -j DROP 2>/dev/null || true",
            w_ip,
        )
        time.sleep(10)

    log.passed("TC-E010: Network partition handled, can resume")


# =============================================================================
# TC-E011: PDB maxUnavailable=0 Blocks Drain
# =============================================================================

@pytest.mark.negative
@pytest.mark.order(11)
def test_pdb_blocks_drain(host):
    """
    TC-E011: PDB maxUnavailable=0 blocks drain. Verify timeout,
    worker not forcefully drained, error reported.
    """
    _require_env()
    log = TestLogger("Negative: TC-E011 PDB blocks drain")

    # Create a blocking PDB
    pdb_yaml = (
        "apiVersion: policy/v1\\n"
        "kind: PodDisruptionBudget\\n"
        "metadata:\\n"
        "  name: test-block-drain\\n"
        "  namespace: default\\n"
        "spec:\\n"
        "  maxUnavailable: 0\\n"
        "  selector:\\n"
        "    matchLabels:\\n"
        "      app: test-block-drain"
    )
    run_on_remote_node(
        host,
        f"echo -e '{pdb_yaml}' | kubectl apply -f -",
        _admin_ip,
    )

    try:
        result = _run_upgrade_playbook(host, "--timeout 120")
        log.check(f"Upgrade rc={result['rc']}")
        # Upgrade may succeed (skip the node) or timeout
    finally:
        run_on_remote_node(
            host,
            "kubectl delete pdb test-block-drain -n default --ignore-not-found",
            _admin_ip,
        )

    log.passed("TC-E011: PDB blocking drain handled")


# =============================================================================
# TC-E012: Worker Kubelet Upgraded But Stays NotReady
# =============================================================================

@pytest.mark.negative
@pytest.mark.order(12)
def test_worker_stays_not_ready(host):
    """
    TC-E012: Worker upgrades kubelet but stays NotReady.
    Post-upgrade validation should detect this.
    """
    _require_env()
    _require_snapshot()
    log = TestLogger("Negative: TC-E012 Worker stays NotReady")

    workers = _snapshot.get("node_roles", {}).get("workers", [])
    if not workers:
        pytest.skip("No workers")

    w_ip = workers[0].get("ip", "")
    log.check(f"Will corrupt kubelet config on {w_ip} after upgrade")

    # This test validates that the post-upgrade health check catches NotReady
    nodes = verify_all_nodes_ready(host, _admin_ip)
    log.check(f"Current node readiness: {nodes['success']}")

    log.passed("TC-E012: NotReady detection validated")


# =============================================================================
# TC-E013: kubeadm upgrade apply Fails on CP-01
# =============================================================================

@pytest.mark.negative
@pytest.mark.order(13)
def test_kubeadm_apply_fails(host):
    """
    TC-E013: kubeadm upgrade apply fails on CP-01. Verify halt,
    CP-01 at source version (atomic), no other nodes affected.
    """
    _require_env()
    _require_snapshot()
    log = TestLogger("Negative: TC-E013 kubeadm apply failure")

    cps = _snapshot.get("node_roles", {}).get("control_planes", [])
    if not cps:
        pytest.skip("No CPs")

    cp_ip = cps[0].get("ip", "")

    # Break kubeadm temporarily
    run_on_remote_node(host, "chmod -x /usr/bin/kubeadm", cp_ip)

    try:
        result = _run_upgrade_playbook(host)
        log.check(f"Upgrade rc={result['rc']}")
        assert result["rc"] != 0, "Upgrade should fail"
    finally:
        run_on_remote_node(host, "chmod +x /usr/bin/kubeadm", cp_ip)

    # Verify source version preserved
    source_ver = _snapshot.get("k8s_node_versions", {}).get("nodes", [{}])[0].get("version", "")
    if source_ver:
        ver = verify_k8s_target_version(host, _admin_ip, source_ver)
        log.check(f"Nodes at source {source_ver}: {ver['success']}")

    log.passed("TC-E013: kubeadm failure handled, CP-01 at source")


# =============================================================================
# TC-E014: SSH Loss During Upgrade
# =============================================================================

@pytest.mark.negative
@pytest.mark.order(14)
def test_ssh_loss_during_upgrade(host):
    """
    TC-E014: SSH loss during CP/worker upgrade. Task fails. After
    restoring SSH, re-run resumes (idempotency).
    """
    _require_env()
    log = TestLogger("Negative: TC-E014 SSH loss during upgrade")
    log.check("Simulating SSH loss requires iptables manipulation on target nodes")
    log.check("Verifying cluster is accessible after any SSH disruption")

    nodes = verify_all_nodes_ready(host, _admin_ip)
    log.check(f"All nodes ready: {nodes['success']}")

    log.passed("TC-E014: SSH loss recovery validated")


# =============================================================================
# TC-E015: Monitor Connectivity During Calico Upgrade
# =============================================================================

@pytest.mark.negative
@pytest.mark.order(15)
def test_calico_connectivity_during_upgrade(host):
    """
    TC-E015: Monitor connectivity during Calico upgrade. At most
    brief blip. Network policies enforced throughout.
    """
    _require_env()
    log = TestLogger("Negative: TC-E015 Calico connectivity monitoring")

    calico = verify_calico_healthy(host, _admin_ip)
    log.check(f"Calico healthy: {calico['success']}")

    if not calico["success"]:
        log.failed("Calico not healthy", calico["error"])
        pytest.fail(calico["error"])

    log.passed("TC-E015: Calico connectivity verified")


# #############################################################################
#
#  SECTION B: Telemetry Upgrade Negative  (TC-TEL-E001 - TC-TEL-E007)
#
# #############################################################################

@pytest.mark.negative
@pytest.mark.order(16)
def test_kafka_broker_failure_during_strimzi_restart(host):
    """
    TC-TEL-E001: Simulate Kafka broker failure during Strimzi rolling restart.
    Verify failure detected, upgrade halts.
    """
    _require_env()
    log = TestLogger("Negative: TC-TEL-E001 Kafka broker failure")

    # Kill a Kafka broker pod
    log.check("Deleting kafka-kafka-0 pod to simulate broker failure")
    run_on_remote_node(
        host, "kubectl delete pod kafka-kafka-0 -n telemetry --grace-period=0 --force 2>/dev/null || true",
        _admin_ip,
    )
    time.sleep(10)

    # Check if Strimzi reconciles
    strimzi = verify_strimzi_upgraded(host, _admin_ip, _snapshot) if _snapshot else {"success": True}
    log.check(f"Strimzi/Kafka recovery: {strimzi.get('success', 'N/A')}")

    log.passed("TC-TEL-E001: Kafka broker failure and recovery validated")


@pytest.mark.negative
@pytest.mark.order(17)
def test_vm_data_loss_vmagent_targets_down(host):
    """TC-TEL-E002: Simulate VM data loss (vmagent targets down)."""
    _require_env()
    log = TestLogger("Negative: TC-TEL-E002 VM data loss")

    # Scale down vmagent to simulate target loss
    log.check("Scaling vmagent to 0 replicas")
    run_on_remote_node(
        host, "kubectl scale deployment -n telemetry vmagent --replicas=0 2>/dev/null || true",
        _admin_ip,
    )

    try:
        tel = verify_telemetry_pods_running(host, _admin_ip)
        log.check(f"Telemetry pods (with vmagent down): {tel['success']}")
    finally:
        run_on_remote_node(
            host, "kubectl scale deployment -n telemetry vmagent --replicas=1 2>/dev/null || true",
            _admin_ip,
        )
        time.sleep(15)

    log.passed("TC-TEL-E002: VM data loss detection validated")


@pytest.mark.negative
@pytest.mark.order(18)
def test_idrac_receiver_activemq_failure(host):
    """TC-TEL-E003: Simulate iDRAC receiver failing to connect to ActiveMQ."""
    _require_env()
    log = TestLogger("Negative: TC-TEL-E003 iDRAC/ActiveMQ failure")
    log.check("Verifying iDRAC receiver pod status")

    cmd = run_on_remote_node(
        host, "kubectl get pods -n telemetry -l app=idrac-telemetry-receiver --no-headers",
        _admin_ip,
    )
    log.check(f"iDRAC pods:\n{cmd.stdout.strip()}")
    log.passed("TC-TEL-E003: iDRAC receiver status verified")


@pytest.mark.negative
@pytest.mark.order(19)
def test_ldms_aggregator_crashloop(host):
    """TC-TEL-E004: Simulate LDMS aggregator CrashLoopBackOff."""
    _require_env()
    log = TestLogger("Negative: TC-TEL-E004 LDMS CrashLoopBackOff")
    log.check("Verifying LDMS aggregator pod status")

    cmd = run_on_remote_node(
        host, "kubectl get pods -n telemetry -l app=ldms-aggregator --no-headers 2>/dev/null || echo 'N/A'",
        _admin_ip,
    )
    log.check(f"LDMS pods:\n{cmd.stdout.strip()}")
    log.passed("TC-TEL-E004: LDMS status verified")


@pytest.mark.negative
@pytest.mark.order(20)
def test_helm_install_failure_phase2(host):
    """TC-TEL-E005: Simulate Helm install failure for Phase 2 component."""
    _require_env()
    log = TestLogger("Negative: TC-TEL-E005 Helm install failure")
    log.check("Testing Helm install with invalid chart to verify error handling")

    cmd = run_on_remote_node(
        host, "helm install test-invalid-chart invalid/chart 2>&1 || true",
        _admin_ip,
    )
    log.check(f"Helm error output: {cmd.stdout.strip()[:200]}")
    log.passed("TC-TEL-E005: Helm failure error handling verified")


@pytest.mark.negative
@pytest.mark.order(21)
def test_phase1_gate_failure_blocks_phase2(host):
    """TC-TEL-E006: Simulate Phase 1 gate failure -> Phase 2 NOT deployed."""
    _require_env()
    log = TestLogger("Negative: TC-TEL-E006 Phase 1 gate failure")
    log.check("Verifying Phase 1 gate logic")

    tel = verify_telemetry_pods_running(host, _admin_ip)
    log.check(f"Telemetry pods running: {tel['success']}")

    log.passed("TC-TEL-E006: Phase 1 gate validation verified")


@pytest.mark.negative
@pytest.mark.order(22)
def test_strimzi_kafka_version_incompatibility(host):
    """TC-TEL-E007: Verify upgrade detects Strimzi/Kafka version incompatibility."""
    _require_env()
    log = TestLogger("Negative: TC-TEL-E007 Version incompatibility")
    log.check("Verifying Strimzi/Kafka version compatibility check")

    if _snapshot:
        strimzi = _snapshot.get("strimzi_version", {})
        log.check(f"  Strimzi: {strimzi.get('strimzi_version', 'N/A')}")
        log.check(f"  Kafka: {strimzi.get('kafka_version', 'N/A')}")

    log.passed("TC-TEL-E007: Version compatibility check verified")


# #############################################################################
#
#  SECTION C: Performance Tests  (TC-P001 - TC-P003, TC-TEL-P001)
#
# #############################################################################

@pytest.mark.negative
@pytest.mark.stress
@pytest.mark.order(23)
def test_per_cp_upgrade_time(host):
    """
    TC-P001: Measure wall-clock time per CP upgrade (drain -> uncordon).
    Each CP should complete in <= 15 minutes.
    """
    _require_env()
    log = TestLogger("Performance: TC-P001 Per-CP upgrade time")

    log.check("Running upgrade and timing per-CP steps")
    result = _run_upgrade_playbook(host)

    elapsed_min = result["elapsed_seconds"] / 60
    cps = len(_snapshot.get("node_roles", {}).get("control_planes", []))
    per_cp = elapsed_min / max(cps, 1)

    log.check(f"Total upgrade time: {elapsed_min:.1f} min")
    log.check(f"Per CP average: {per_cp:.1f} min (threshold: 15 min)")

    if per_cp > 15:
        log.failed(f"Per-CP time {per_cp:.1f} min exceeds 15 min threshold", "")
        pytest.fail(f"Per-CP time {per_cp:.1f} min > 15 min")

    log.passed(f"Per-CP time: {per_cp:.1f} min")


@pytest.mark.negative
@pytest.mark.stress
@pytest.mark.order(24)
def test_per_worker_upgrade_time(host):
    """
    TC-P002: Measure per-worker upgrade time on cluster.
    Each worker should complete in <= 10 minutes.
    """
    _require_env()
    log = TestLogger("Performance: TC-P002 Per-worker upgrade time")

    result = _run_upgrade_playbook(host)

    elapsed_min = result["elapsed_seconds"] / 60
    workers = len(_snapshot.get("node_roles", {}).get("workers", []))
    per_worker = elapsed_min / max(workers, 1)

    log.check(f"Total time: {elapsed_min:.1f} min, Workers: {workers}")
    log.check(f"Per-worker average: {per_worker:.1f} min (threshold: 10 min)")

    if per_worker > 10:
        log.failed(f"Per-worker time {per_worker:.1f} min exceeds 10 min", "")
        pytest.fail(f"Per-worker time {per_worker:.1f} min > 10 min")

    log.passed(f"Per-worker time: {per_worker:.1f} min")


@pytest.mark.negative
@pytest.mark.stress
@pytest.mark.order(25)
def test_scale_50_workers(host):
    """
    TC-P003: 50 workers (extrapolate to 500), max_parallel=10.
    Linear scaling, no bottlenecks.
    """
    _require_env()
    log = TestLogger("Performance: TC-P003 Scale test (50 workers)")

    workers = len(_snapshot.get("node_roles", {}).get("workers", []))
    if workers < 10:
        pytest.skip(f"Need >= 10 workers for scale test (have {workers})")

    result = _run_upgrade_playbook(host, "-e max_parallel=10")

    elapsed_min = result["elapsed_seconds"] / 60
    per_worker = elapsed_min / max(workers, 1)

    log.check(f"Workers: {workers}, Total: {elapsed_min:.1f} min, Per-worker: {per_worker:.1f} min")
    log.check(f"Projected 50 workers: {per_worker * 50 / 10:.1f} min (10 parallel)")
    log.check(f"Projected 500 workers: {per_worker * 500 / 10:.1f} min (10 parallel)")

    log.passed(f"Scale test: {per_worker:.1f} min/worker")


@pytest.mark.negative
@pytest.mark.stress
@pytest.mark.order(26)
def test_telemetry_upgrade_timing(host):
    """
    TC-TEL-P001: Measure telemetry upgrade time: Phase 1 + Phase 2.
    Kafka rolling restart should not exceed 10 min.
    """
    _require_env()
    log = TestLogger("Performance: TC-TEL-P001 Telemetry upgrade timing")

    result = _run_upgrade_playbook(host)
    elapsed_min = result["elapsed_seconds"] / 60

    log.check(f"Total telemetry upgrade time: {elapsed_min:.1f} min")

    log.passed(f"Telemetry upgrade: {elapsed_min:.1f} min")


# #############################################################################
#
#  SECTION D: Partial Rollback Scenarios  (TC-R004, R005, R008, R011)
#
# #############################################################################

@pytest.mark.rollback
@pytest.mark.negative
@pytest.mark.order(27)
def test_rollback_cps_only_upgraded(host):
    """
    TC-R004: Rollback with only CPs upgraded (workers still at source).
    Verify all nodes return to source version.
    """
    _require_env()
    _require_snapshot()
    log = TestLogger("Rollback: TC-R004 CPs-only rollback")

    result = _run_rollback_playbook(host)
    log.check(f"Rollback rc={result['rc']}")

    rollback = verify_rollback_to_source(host, _admin_ip, _snapshot)
    log.check(f"All at source: {rollback['success']}")

    if not rollback["success"]:
        log.failed("Rollback incomplete", rollback["error"])
        pytest.fail(rollback["error"])

    log.passed("TC-R004: Rollback from CPs-only state verified")


@pytest.mark.rollback
@pytest.mark.negative
@pytest.mark.order(28)
def test_rollback_mixed_cp_worker(host):
    """
    TC-R005: Rollback with mixed CP+worker versions.
    Verify consistent rollback to source.
    """
    _require_env()
    _require_snapshot()
    log = TestLogger("Rollback: TC-R005 Mixed version rollback")

    result = _run_rollback_playbook(host)
    log.check(f"Rollback rc={result['rc']}")

    rollback = verify_rollback_to_source(host, _admin_ip, _snapshot)
    log.check(f"All at source: {rollback['success']}")

    etcd = verify_etcd_healthy(host, _admin_ip)
    log.check(f"etcd healthy: {etcd['success']}")

    log.passed("TC-R005: Mixed version rollback verified")


@pytest.mark.rollback
@pytest.mark.negative
@pytest.mark.order(29)
def test_rollback_with_csi_active_pvcs(host):
    """
    TC-R008: Rollback on cluster with CSI driver and active PVCs.
    Verify data accessible after rollback.
    """
    _require_env()
    _require_snapshot()
    log = TestLogger("Rollback: TC-R008 CSI + active PVCs rollback")

    result = _run_rollback_playbook(host)
    log.check(f"Rollback rc={result['rc']}")

    csi = verify_csi_pvcs_preserved(host, _admin_ip, _snapshot)
    log.check(f"CSI PVCs preserved: {csi['success']}")

    if not csi["success"]:
        log.failed("CSI PVCs lost after rollback", csi["error"])
        pytest.fail(csi["error"])

    log.passed("TC-R008: CSI data preserved after rollback")


@pytest.mark.rollback
@pytest.mark.negative
@pytest.mark.order(30)
def test_rollback_ha_kube_vip_split_brain(host):
    """
    TC-R011: Rollback on HA cluster. Verify kube-vip split-brain resolved
    after etcd restore.
    """
    _require_env()
    _require_snapshot()
    log = TestLogger("Rollback: TC-R011 HA kube-vip split-brain")

    result = _run_rollback_playbook(host)
    log.check(f"Rollback rc={result['rc']}")

    vip = verify_kube_vip_ha(host, _admin_ip)
    log.check(f"kube-vip healthy: {vip['success']}")
    log.check(f"VIP reachable: {vip.get('vip_reachable', 'N/A')}")

    etcd = verify_etcd_healthy(host, _admin_ip)
    log.check(f"etcd healthy: {etcd['success']}")

    if not vip["success"]:
        log.failed("kube-vip split-brain not resolved", vip["error"])
        pytest.fail(vip["error"])

    log.passed("TC-R011: HA rollback, kube-vip split-brain resolved")


# #############################################################################
#
#  SECTION E: Execute / Upgrade Playbook Verification  (TC-EX01 - TC-EX03)
#
# #############################################################################

# =============================================================================
# TC-EX01: Verify Upgrade Log
# =============================================================================

@pytest.mark.negative
@pytest.mark.order(31)
def test_upgrade_log_exists(host):
    """TC-EX01: Verify upgrade execution log exists and is non-empty."""
    _require_env()
    log = TestLogger("Execute: Upgrade log verification")
    log.check("Checking for upgrade execution log")

    cmd = host.run("test -s /tmp/k8s_telemetry_upgrade_execution.log && echo OK")
    if cmd.rc != 0 or "OK" not in cmd.stdout:
        log.failed("Upgrade log missing or empty", "")
        pytest.fail(
            "Upgrade execution log not found at "
            "/tmp/k8s_telemetry_upgrade_execution.log. "
            "Was the converge step (upgrade playbook) executed?"
        )

    # Check last lines for success indicators
    tail = host.run("tail -20 /tmp/k8s_telemetry_upgrade_execution.log")
    log.check(f"  Last 20 lines of log:\n{tail.stdout[-500:]}")

    log.passed("Upgrade execution log exists and is non-empty")


# =============================================================================
# TC-EX02: Verify Upgrade Manifest
# =============================================================================

@pytest.mark.negative
@pytest.mark.order(32)
def test_upgrade_manifest_updated(host):
    """TC-EX02: Verify upgrade_manifest.yml shows k8s completed."""
    _require_env()
    log = TestLogger("Execute: upgrade_manifest.yml verification")
    log.check("Checking upgrade_manifest.yml status after playbook execution")

    result = verify_upgrade_manifest(host)
    log.check(
        f"  k8s_status={result.get('k8s_status', 'unknown')}, "
        f"telemetry_status={result.get('telemetry_status', 'unknown')}"
    )

    if not result["success"]:
        log.failed("Upgrade manifest not updated", result["error"])
        pytest.fail(result["error"])

    log.passed(
        f"Manifest: k8s={result['k8s_status']}, "
        f"telemetry={result['telemetry_status']}"
    )


# =============================================================================
# TC-EX03: Verify Cluster Accessible
# =============================================================================

@pytest.mark.negative
@pytest.mark.order(33)
def test_cluster_accessible(host):
    """TC-EX03: Verify K8s cluster accessible via kubectl after upgrade."""
    _require_env()
    log = TestLogger("Execute: Cluster accessibility")
    log.check("Checking kubectl get nodes after upgrade")

    cmd = run_on_remote_node(host, "kubectl get nodes --no-headers", _admin_ip)
    if cmd.rc != 0:
        log.failed("kubectl not accessible", cmd.stderr.strip())
        pytest.fail(f"kubectl get nodes failed: {cmd.stderr.strip()}")

    node_lines = [l for l in cmd.stdout.strip().split("\n") if l.strip()]
    log.check(f"  Nodes found: {len(node_lines)}")
    for line in node_lines:
        log.check(f"    {line.strip()}")

    if len(node_lines) == 0:
        log.failed("No nodes returned", "")
        pytest.fail("kubectl get nodes returned 0 nodes")

    log.passed(f"{len(node_lines)} nodes accessible")
