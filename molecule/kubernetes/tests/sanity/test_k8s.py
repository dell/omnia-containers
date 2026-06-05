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

"""Kubernetes cluster test cases for OMNIA.

This module contains test cases to verify the health and status of Kubernetes cluster nodes.
"""

import os
import sys

# Add the project root to the Python path
_PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "../../../.."),
)
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

import pytest
from automation_library.core import TestLogger
from automation_library.kubernetes.functions.k8s_func import get_oim_operations
from automation_library.kubernetes.vars.k8s_vars import (
    DEFAULT_STORAGE_CLASS,
    EXPECTED_CONTAINER_RUNTIME,
    SERVICE_CLUSTER_METADATA_PATH,
)

# Path to sample manifests (go up to project root, then into automation_library)
POWERSCALE_PVC_BUSYBOX_MANIFEST_PATH = os.path.abspath(os.path.join(
    os.path.dirname(__file__),
    "../../../../automation_library/kubernetes/sample_manifests/powerscale_pvc_busybox.yaml",
))

# Load PowerScale manifest YAML content
with open(POWERSCALE_PVC_BUSYBOX_MANIFEST_PATH, "r", encoding="utf-8") as f:
    POWERSCALE_PVC_BUSYBOX_MANIFEST_YAML = f.read()

# Pytest fixtures
@pytest.fixture(scope="module", name="oim_ops")
def _oim_ops_fixture():
    """Fixture to provide OIMOperations instance."""
    try:
        ops = get_oim_operations()
    except (OSError, KeyError, RuntimeError, ValueError) as e:
        pytest.skip(f"Unable to initialize OIM operations: {str(e)}")
    try:
        yield ops
    finally:
        ops.close()

# =============================================================================
# 1. BASIC INFRASTRUCTURE TESTS
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(1)
def test_all_nodes_joined_cluster(oim_ops):
    """Test that all nodes from PXE mapping have joined the Kubernetes cluster."""
    log = TestLogger("Verify all PXE-mapped nodes have joined the Kubernetes cluster")
    log.check("Comparing PXE mapping nodes against 'kubectl get nodes'")
    success, message, _ = oim_ops.verify_nodes_joined_cluster_check()
    if success:
        log.passed("All PXE-mapped nodes have joined", message)
    else:
        log.failed("Some nodes have not joined the cluster", message)
    assert success, message

@pytest.mark.sanity
@pytest.mark.order(2)
def test_all_nodes_in_ready_state(oim_ops):
    """Test that all nodes in the Kubernetes cluster are in Ready state."""
    log = TestLogger("Verify all Kubernetes nodes are in Ready state")
    log.check("Checking node Ready state with retry")
    success, message, _ = oim_ops.verify_nodes_ready_state_with_retry()
    if success:
        log.passed("All nodes are Ready", message)
    else:
        log.failed("Some nodes are not Ready", message)
    assert success, message

# =============================================================================
# 2. SERVICE HEALTH TESTS
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(3)
def test_kubelet_active_on_control_planes(oim_ops):
    """Test that kubelet service is active on all kube control plane nodes."""
    log = TestLogger("Verify kubelet is active on kube control plane nodes")
    log.check("Checking kubelet service on control plane nodes")
    success, message, details = oim_ops.verify_kubelet_active_on_control_planes()
    for d in details:
        log.check(f"  {d}")
    if success:
        log.passed(message)
    else:
        log.failed(message)
    assert success, message

@pytest.mark.sanity
@pytest.mark.order(4)
def test_kubelet_active_on_kube_nodes(oim_ops):
    """Test that kubelet service is active on all kube worker nodes."""
    log = TestLogger("Verify kubelet is active on kube worker nodes")
    log.check("Checking kubelet service on kube worker nodes")
    success, message, details = oim_ops.verify_kubelet_active_on_kube_nodes()
    for d in details:
        log.check(f"  {d}")
    if success:
        log.passed(message)
    else:
        log.failed(message)
    assert success, message

@pytest.mark.sanity
@pytest.mark.order(5)
def test_crio_active_on_control_planes(oim_ops):
    """Test that crio/cri-o service is active on all kube control plane nodes."""
    log = TestLogger("Verify CRI-O is active on kube control plane nodes")
    log.check("Checking CRI-O service on control plane nodes")
    success, message, details = oim_ops.verify_crio_active_on_control_planes()
    for d in details:
        log.check(f"  {d}")
    if success:
        log.passed(message)
    else:
        log.failed(message)
    assert success, message

@pytest.mark.sanity
@pytest.mark.order(6)
def test_crio_active_on_kube_nodes(oim_ops):
    """Test that crio/cri-o service is active on all kube worker nodes."""
    log = TestLogger("Verify CRI-O is active on kube worker nodes")
    log.check("Checking CRI-O service on kube worker nodes")
    success, message, details = oim_ops.verify_crio_active_on_kube_nodes()
    for d in details:
        log.check(f"  {d}")
    if success:
        log.passed(message)
    else:
        log.failed(message)
    assert success, message

@pytest.mark.sanity
@pytest.mark.order(7)
def test_chronyd_active_on_control_planes(oim_ops):
    """Test that chronyd service is active on all kube control plane nodes."""
    log = TestLogger("Verify chronyd is active on kube control plane nodes")
    log.check("Checking chronyd service on control plane nodes")
    success, message, details = oim_ops.verify_chronyd_active_on_control_planes()
    for d in details:
        log.check(f"  {d}")
    if success:
        log.passed(message)
    else:
        log.failed(message)
    assert success, message

# =============================================================================
# 3. NODE READY STATE TESTS (PER NODE TYPE)
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(8)
def test_control_plane_nodes_ready(oim_ops):
    """Test that all kube control plane nodes are in READY state."""
    log = TestLogger("Verify all kube control plane nodes are in Ready state")
    log.check("Checking control plane node Ready state")
    success, message, details = oim_ops.verify_control_plane_nodes_ready()
    for d in details:
        log.check(f"  {d}")
    if success:
        log.passed(message)
    else:
        log.failed(message)
    assert success, message

@pytest.mark.sanity
@pytest.mark.order(9)
def test_kube_nodes_ready(oim_ops):
    """Test that all kube worker nodes are in READY state."""
    log = TestLogger("Verify all kube worker nodes are in Ready state")
    log.check("Checking kube worker node Ready state")
    success, message, details = oim_ops.verify_kube_nodes_ready()
    for d in details:
        log.check(f"  {d}")
    if success:
        log.passed(message)
    else:
        log.failed(message)
    assert success, message

# =============================================================================
# 4. VERSION VALIDATION TESTS
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(10)
def test_kubectl_version(oim_ops):
    """Test that kubectl client version matches the expected version on control plane nodes."""
    log = TestLogger("Verify kubectl version on control plane nodes")
    expected_version = oim_ops.get_service_k8s_version_from_software_config()
    log.check(f"Validating kubectl client version matches service_k8s={expected_version}")
    success, message, results = oim_ops.verify_kubectl_version_on_control_planes_check(
        expected_version,
    )
    details_lines = []
    for node_name, is_correct, actual_version, error in (results or []):
        if error:
            if "No route to host" in error or "Connection refused" in error or "Connection timed out" in error:
                details_lines.append(f"{node_name}: SKIPPED (unreachable)")
            else:
                details_lines.append(f"{node_name}: error - {error}")
        elif is_correct:
            details_lines.append(f"{node_name}: expected={expected_version}, got={actual_version}")
        else:
            details_lines.append(f"{node_name}: expected={expected_version}, got={actual_version}")
    details = "\n".join(details_lines) if details_lines else None
    if success:
        log.passed("kubectl version matches expected", details)
    else:
        log.failed("kubectl version mismatch detected", details)
    assert success, message

@pytest.mark.sanity
@pytest.mark.order(11)
def test_kubeadm_version_matches_crio(oim_ops):
    """Test that kubeadm is installed with the same version as crio on control plane nodes."""
    log = TestLogger("Verify kubeadm version matches crio version")
    log.check("Comparing kubeadm and crio versions on control plane nodes")
    success, message, details = oim_ops.verify_kubeadm_version_matches_crio()
    for d in details:
        log.check(f"  {d}")
    if success:
        log.passed(message)
    else:
        log.failed(message)
    assert success, message

@pytest.mark.sanity
@pytest.mark.order(12)
def test_all_nodes_using_crio(oim_ops):
    """Test that all nodes are using CRI-O with the expected version as the container runtime."""
    log = TestLogger("Verify all nodes are using CRI-O runtime")
    expected_version = oim_ops.get_service_k8s_version_from_software_config()
    log.check(
        f"Validating container runtime is {EXPECTED_CONTAINER_RUNTIME}://{expected_version}",
    )
    all_passed, results = oim_ops.verify_all_nodes_container_runtime(
        expected_runtime=EXPECTED_CONTAINER_RUNTIME,
        expected_version=expected_version,
    )
    details = oim_ops.format_container_runtime_details(results)
    if all_passed:
        log.passed("All nodes are using expected container runtime", details)
    else:
        log.failed("One or more nodes are not using expected container runtime", details)
    assert all_passed, "Container runtime check failed. See above for details."

# =============================================================================
# 5. CLUSTER HEALTH & ETCD TESTS
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(13)
def test_k8s_component_status(oim_ops):
    """Verify k8s cluster health using kubectl get componentstatus.

    Expects controller-manager, scheduler, and etcd-0 to be Healthy.
    """
    log = TestLogger("Verify k8s cluster component status")
    log.check("Running kubectl get componentstatus")
    success, message, output = oim_ops.verify_k8s_component_status()
    if success:
        log.passed(message, output)
    else:
        log.failed(message, output)
    assert success, message

@pytest.mark.sanity
@pytest.mark.order(14)
def test_etcd_cluster_health(oim_ops):
    """Verify etcd cluster endpoint health from within an etcd pod."""
    log = TestLogger("Verify etcd cluster endpoint health")
    log.check("Running etcdctl endpoint health from within etcd pod")
    success, message, output = oim_ops.verify_etcd_cluster_health()
    if success:
        log.passed(message, output)
    else:
        log.failed(message, output)
    assert success, message

@pytest.mark.sanity
@pytest.mark.order(15)
def test_etcd_member_list(oim_ops):
    """Verify etcd member list from within an etcd pod."""
    log = TestLogger("Verify etcd member list")
    log.check("Running etcdctl member list from within etcd pod")
    success, message, output = oim_ops.verify_etcd_member_list()
    if success:
        log.passed(message, output)
    else:
        log.failed(message, output)
    assert success, message

@pytest.mark.sanity
@pytest.mark.order(16)
def test_etcd_leader_and_consistency(oim_ops):
    """Verify etcd leader identification and consistency across all control plane nodes."""
    log = TestLogger("Verify etcd leader and consistency")
    log.check("Collecting control plane admin IPs from PXE mapping file")
    log.check("Running etcdctl endpoint status across all control plane nodes")
    result = oim_ops.verify_etcd_leader_and_consistency()
    if not result["success"]:
        log.failed(result["message"])
        assert False, result["message"]
    log.check(f"etcd leader identified: {result['leader_ip']}")
    log.check(f"RAFT term: {result.get('raft_term', 'N/A')}")
    log.check(f"RAFT index: {result.get('raft_index', 'N/A')}")
    log.check("Member status:")
    for member in result.get("members", []):
        leader_status = "LEADER" if member["is_leader"] else "FOLLOWER"
        log.check(
            f"  {member['ip']} - {leader_status} "
            f"(term: {member['raft_term']}, index: {member['raft_index']})"
        )
    log.passed(result["message"])
    assert result["success"], result["message"]

# =============================================================================
# 6. NETWORK & HIGH AVAILABILITY TESTS
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(17)
def test_virtual_ip_configured_to_single_control_plane(oim_ops):
    """Test that virtual_ip_address is configured on exactly one control plane node."""
    log = TestLogger("Verify virtual IP is configured on exactly one control plane")
    log.check("Checking VIP ownership across control-plane nodes")
    success, message = oim_ops.verify_virtual_ip_configuration()
    if success:
        log.passed("VIP configuration validated", message)
    else:
        log.failed("VIP configuration validation failed", message)
    assert success, message

# =============================================================================
# 7. CORE KUBERNETES SYSTEM PODS
# =============================================================================

def _check_pods_with_prefix(oim_ops, prefix, component_name):
    """Helper to check pods with a given prefix."""
    log = TestLogger(f"Verify {component_name} pods are running")
    log.check(f"Checking pods with prefix '{prefix}'")
    success, message = oim_ops.verify_pods_with_prefix(prefix, component_name)
    if success:
        log.passed(message)
    else:
        log.failed(message)
    assert success, message

@pytest.mark.sanity
@pytest.mark.order(18)
def test_etcd_pods_running(oim_ops):
    """Test that all etcd pods are running."""
    _check_pods_with_prefix(oim_ops, "etcd", "etcd")

@pytest.mark.sanity
@pytest.mark.order(19)
def test_kube_apiserver_pods_running(oim_ops):
    """Test that all kube-apiserver pods are running."""
    _check_pods_with_prefix(oim_ops, "kube-apiserver", "kube-apiserver")

@pytest.mark.sanity
@pytest.mark.order(20)
def test_kube_controller_manager_pods_running(oim_ops):
    """Test that all kube-controller-manager pods are running."""
    _check_pods_with_prefix(oim_ops, "kube-controller-manager", "kube-controller-manager")

@pytest.mark.sanity
@pytest.mark.order(21)
def test_kube_scheduler_pods_running(oim_ops):
    """Test that all kube-scheduler pods are running."""
    _check_pods_with_prefix(oim_ops, "kube-scheduler", "kube-scheduler")

@pytest.mark.sanity
@pytest.mark.order(22)
def test_kube_proxy_pods_running(oim_ops):
    """Test that all kube-proxy pods are running."""
    _check_pods_with_prefix(oim_ops, "kube-proxy", "kube-proxy")

@pytest.mark.sanity
@pytest.mark.order(23)
def test_kube_vip_pods_running(oim_ops):
    """Test that all kube-vip pods are running."""
    _check_pods_with_prefix(oim_ops, "kube-vip", "kube-vip")

# =============================================================================
# 8. NETWORK PODS
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(24)
def test_calico_pods_running(oim_ops):
    """Test that all Calico pods are in 'Running' state."""
    _check_pods_with_prefix(oim_ops, "calico", "Calico")

@pytest.mark.sanity
@pytest.mark.order(25)
def test_coredns_pods_running(oim_ops):
    """Test that all CoreDNS pods are running."""
    _check_pods_with_prefix(oim_ops, "coredns", "CoreDNS")

@pytest.mark.sanity
@pytest.mark.order(26)
def test_metallb_system_pods_running(oim_ops):
    """Test that all pods in the metallb-system namespace are running."""
    log = TestLogger("Verify MetalLB pods are running")
    log.check("Checking metallb-system pods")
    success, message, pod_statuses = oim_ops.verify_metallb_pods()
    details = oim_ops.format_pod_details(pod_statuses, default_namespace="metallb-system")
    if success:
        log.passed(message, details)
    else:
        log.failed(message, details)
    assert success, f"MetalLB pods check failed: {message}"

# =============================================================================
# 9. STORAGE & CSI PODS
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(27)
def test_nfs_client_provisioner_pod_running(oim_ops):
    """Test that the nfs-client-nfs-subdir-external-provisioner pod is running."""
    log = TestLogger("Verify NFS client provisioner pod is running")
    log.check("Checking nfs-client-nfs-subdir-external-provisioner pod")
    success, message, pod_info = oim_ops.verify_nfs_provisioner_pod()
    details = None
    if pod_info:
        details = (
            f"{pod_info.get('namespace')}/{pod_info.get('name')} "
            f"(Node: {pod_info.get('node', 'Unknown')}): {pod_info.get('status')}"
        )
    if success:
        log.passed(message, details)
    else:
        log.failed(message, details)
    assert success, f"NFS provisioner pod check failed: {message}"

@pytest.mark.sanity
@pytest.mark.order(28)
def test_snapshot_controller_pods_running(oim_ops):
    """Test that all snapshot-controller pods are running only when PowerScale CSI is configured."""
    log = TestLogger("Verify snapshot-controller pods are running")
    log.check("Checking if PowerScale CSI is configured")
    configured, config_message = oim_ops.is_powerscale_csi_configured_in_software_config()
    if configured is None:
        log.passed("snapshot-controller check skipped", config_message)
        pytest.skip(config_message)
    if not configured:
        log.passed("snapshot-controller check skipped", config_message)
        pytest.skip(config_message)
    log.check("Checking pods with prefix 'snapshot-controller'")
    success, message = oim_ops.verify_pods_with_prefix("snapshot-controller", "snapshot-controller")
    if success:
        log.passed(message)
    else:
        log.failed(message)
    assert success, message

@pytest.mark.sanity
@pytest.mark.order(29)
def test_isilon_csi_driver_pods(oim_ops):
    """Test that Isilon CSI Driver pods are running only when configured in software_config.json."""
    log = TestLogger("Verify Isilon CSI Driver pods")
    log.check("Checking if PowerScale CSI is configured and verifying Isilon pods")
    status, message = oim_ops.verify_isilon_csi_driver_pods_from_software_config()
    if status is None:
        log.passed("CSI driver check skipped", message)
        pytest.skip(message)
    if status:
        log.passed(message)
    else:
        log.failed(message)
    assert status, message

# =============================================================================
# 10. STORAGE CLASS & PERSISTENT VOLUME TESTS
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(30)
def test_default_storage_class_csi(oim_ops):
    """Test that the default storage class exists and is set as default."""
    log = TestLogger("Verify default storage class for CSI")
    log.check("Checking if PowerScale CSI is configured")
    configured, config_message = oim_ops.is_powerscale_csi_configured_in_software_config()
    if configured is None:
        log.passed("StorageClass check skipped", config_message)
        pytest.skip(config_message)
    if not configured:
        log.passed("StorageClass check skipped", config_message)
        pytest.skip(config_message)
    log.check(f"Validating default StorageClass exists: {DEFAULT_STORAGE_CLASS}")
    success, message = oim_ops.verify_default_storage_class(DEFAULT_STORAGE_CLASS)
    if success:
        log.passed(message)
    else:
        log.failed(message)
    assert success, f"Storage class verification failed: {message}"

@pytest.mark.sanity
@pytest.mark.order(31)
def test_persistent_volumes_with_nfs(oim_ops):
    """Test that all Persistent Volumes are in the expected state when NFS is configured."""
    log = TestLogger("Verify Persistent Volumes with NFS")
    log.check("Checking if PowerScale CSI is configured")
    configured, config_message = oim_ops.is_powerscale_csi_configured_in_software_config()
    if configured is None:
        log.passed("PV check skipped", config_message)
        pytest.skip(config_message)
    if configured:
        log.passed("PV check skipped", config_message)
        pytest.skip(config_message)
    log.check("Validating PVs use storageClass=nfs-client")
    success, message = oim_ops.verify_persistent_volumes(expected_storage_class="nfs-client")
    if success:
        log.passed(message)
    else:
        log.failed(message)
    assert success, message

@pytest.mark.sanity
@pytest.mark.order(32)
def test_persistent_volumes_with_csi(oim_ops):
    """Test that all Persistent Volumes are in the expected state when CSI is configured."""
    log = TestLogger("Verify Persistent Volumes with CSI")
    log.check("Checking if PowerScale CSI is configured")
    configured, config_message = oim_ops.is_powerscale_csi_configured_in_software_config()
    if configured is None:
        log.passed("PV check skipped", config_message)
        pytest.skip(config_message)
    if not configured:
        log.passed("PV check skipped", config_message)
        pytest.skip(config_message)
    log.check(f"Validating PVs use storageClass={DEFAULT_STORAGE_CLASS}")
    success, message = oim_ops.verify_persistent_volumes(
        expected_storage_class=DEFAULT_STORAGE_CLASS,
    )
    if success:
        log.passed(message)
    else:
        log.failed(message)
    assert success, message

# =============================================================================
# 11. NFS STORAGE VERIFICATION TESTS
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(33)
def test_nfs_storage_class_dynamic(oim_ops):
    """Verify the NFS StorageClass is dynamic and properly configured."""
    log = TestLogger("Verify NFS StorageClass is dynamic")
    log.check("Checking if PowerScale CSI is configured")
    configured, config_message = oim_ops.is_powerscale_csi_configured_in_software_config()
    if configured is None:
        log.passed("NFS StorageClass check skipped", config_message)
        pytest.skip(config_message)
    if configured:
        log.passed("NFS StorageClass check skipped", config_message)
        pytest.skip(config_message)
    log.check("Verifying StorageClass 'nfs-client' exists and is dynamic")
    success, message, sc_details = oim_ops.verify_nfs_storage_class(storage_class_name="nfs-client")
    if success:
        details = (
            f"provisioner={sc_details.get('provisioner')}, "
            f"server={sc_details.get('nfs_server')}, "
            f"path={sc_details.get('nfs_path')}"
        )
        log.passed(message, details)
    else:
        log.failed(message)
    assert success, message


@pytest.mark.sanity
@pytest.mark.order(34)
def test_nfs_telemetry_pvcs_bound(oim_ops):
    """Verify all telemetry PVCs are Bound with correct storage class, PV, and volume size.

    Checks every PVC in the 'telemetry' namespace against telemetry_config.yml:
      - Kafka PVCs size == telemetry_sinks.kafka.persistence_size
      - vmstorage PVC size == telemetry_sinks.victoria_metrics.persistence_size
      - vlstorage PVC size == telemetry_sinks.victoria_logs.storage_size
      - All PVCs: phase=Bound, storageClass=nfs-client, volumeName set
    """
    log = TestLogger("Verify telemetry PVCs Bound with correct PV and size")
    log.check("Checking if PowerScale CSI is configured")
    configured, config_message = oim_ops.is_powerscale_csi_configured_in_software_config()
    if configured is None:
        log.passed("Telemetry PVC check skipped", config_message)
        pytest.skip(config_message)
    if configured:
        log.passed("Telemetry PVC check skipped", config_message)
        pytest.skip(config_message)
    log.check("Verifying all PVCs in 'telemetry' namespace: Bound, nfs-client SC, correct size from telemetry_config.yml")
    success, message, pvc_results = oim_ops.verify_telemetry_pvcs(
        storage_class_name="nfs-client", namespace="telemetry",
    )
    for r in pvc_results:
        status = "OK" if r.get("success") else "FAIL"
        issues = "; ".join(r.get("issues", [])) or "OK"
        log.check(
            f"[{status}] {r.get('pvc')}: phase={r.get('phase')}, "
            f"SC={r.get('storageClass')}, PV={r.get('volumeName') or 'NONE'}, "
            f"size={r.get('actualSize')} | {issues}"
        )
    if success:
        log.passed(message)
    else:
        log.failed(message)
    assert success, message


@pytest.mark.sanity
@pytest.mark.order(35)
def test_nfs_backend_directories(oim_ops):
    """Verify NFS backend directories exist for each PV with correct permissions."""
    log = TestLogger("Verify NFS backend directories")
    log.check("Checking if PowerScale CSI is configured")
    configured, config_message = oim_ops.is_powerscale_csi_configured_in_software_config()
    if configured is None:
        log.passed("NFS backend directory check skipped", config_message)
        pytest.skip(config_message)
    if configured:
        log.passed("NFS backend directory check skipped", config_message)
        pytest.skip(config_message)
    log.check("Checking NFS backend directories and permissions for all NFS PVs")
    success, message, dir_results = oim_ops.verify_nfs_backend_directories(storage_class_name="nfs-client")
    for r in dir_results:
        status = "OK" if r.get("success") else "FAIL"
        log.check(
            f"[{status}] PV {r.get('pv')}: {r.get('path')} on {r.get('nfs_server')} "
            f"(perms: {r.get('permissions', r.get('reason', ''))})"
        )
    if success:
        log.passed(message)
    else:
        log.failed(message)
    assert success, message


# =============================================================================
# 12. CSI STORAGE VERIFICATION TESTS
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(36)
def test_csi_telemetry_pvcs_bound(oim_ops):
    """Verify all telemetry PVCs are Bound with the CSI storage class, correct PV, and volume size.

    Checks every PVC in the 'telemetry' namespace against telemetry_config.yml:
      - Kafka PVCs size == telemetry_sinks.kafka.persistence_size
      - vmstorage PVC size == telemetry_sinks.victoria_metrics.persistence_size
      - vlstorage PVC size == telemetry_sinks.victoria_logs.storage_size
      - All PVCs: phase=Bound, storageClass=DEFAULT_STORAGE_CLASS, volumeName set
    """
    log = TestLogger("Verify CSI telemetry PVCs Bound with correct PV and size")
    log.check("Checking if PowerScale CSI is configured")
    configured, config_message = oim_ops.is_powerscale_csi_configured_in_software_config()
    if configured is None:
        log.passed("CSI telemetry PVC check skipped", config_message)
        pytest.skip(config_message)
    if not configured:
        log.passed("CSI telemetry PVC check skipped", config_message)
        pytest.skip(config_message)
    log.check(
        f"Verifying all PVCs in 'telemetry' namespace: Bound, {DEFAULT_STORAGE_CLASS} SC, "
        "correct size from telemetry_config.yml"
    )
    success, message, pvc_results = oim_ops.verify_telemetry_pvcs(
        storage_class_name=DEFAULT_STORAGE_CLASS, namespace="telemetry",
    )
    for r in pvc_results:
        status = "OK" if r.get("success") else "FAIL"
        issues = "; ".join(r.get("issues", [])) or "OK"
        log.check(
            f"[{status}] {r.get('pvc')}: phase={r.get('phase')}, "
            f"SC={r.get('storageClass')}, PV={r.get('volumeName') or 'NONE'}, "
            f"size={r.get('actualSize')} | {issues}"
        )
    if success:
        log.passed(message)
    else:
        log.failed(message)
    assert success, message


# =============================================================================
# 13. APPLICATION DEPLOYMENT TESTS
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(37)
def test_deploy_basic_busybox_pod(oim_ops):
    """Deploy a basic BusyBox pod and verify it reaches Running/Ready state."""
    log = TestLogger("Deploy and verify BusyBox pod")
    log.check("Deploying a basic BusyBox pod and waiting for Ready")
    success, message, pod_info = oim_ops.verify_basic_nginx_pod_running()
    details = None
    if pod_info:
        details = (
            f"{pod_info.get('namespace')}/{pod_info.get('name')} "
            f"(Node: {pod_info.get('node', 'Unknown')}): "
            f"{pod_info.get('status')}, Ready={pod_info.get('ready')}"
        )
    if success:
        log.passed(message, details)
    else:
        log.failed(message, details)
    assert success, message

@pytest.mark.sanity
@pytest.mark.order(38)
def test_pvc_pv_bound_and_pod_running_powerscale(oim_ops):
    """Verify PowerScale PVC/PV binding and a test pod reaching Running/Ready."""
    log = TestLogger("Verify PowerScale PVC/PV bind and pod running")
    log.check("Checking if PowerScale CSI is configured")
    configured, config_message = oim_ops.is_powerscale_csi_configured_in_software_config()
    if configured is None:
        log.passed("PVC/PV check skipped", config_message)
        pytest.skip(config_message)
    if not configured:
        log.passed("PVC/PV check skipped", config_message)
        pytest.skip(config_message)

    success, message = oim_ops.verify_pvc_pv_bound_and_pod_running(
        manifest_yaml=POWERSCALE_PVC_BUSYBOX_MANIFEST_YAML,
        pvc_name="pvc-powerscale",
        deployment_name="deploy-busybox-01",
        pod_selector="app=deploy-busybox-01",
        namespace="default",
        timeout_seconds=300,
        cleanup=True,
    )
    if success:
        log.passed(message)
    else:
        log.failed(message)
    assert success, message
