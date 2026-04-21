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
    POWERSCALE_PVC_BUSYBOX_MANIFEST_YAML,
    SERVICE_CLUSTER_METADATA_PATH,
)

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

def test_kubelet_active_on_k8s_nodes(oim_ops):
    """Test that kubelet is active on all reachable Kubernetes nodes."""
    log = TestLogger("Verify kubelet is active on all reachable Kubernetes nodes")
    log.check("Checking kubelet service on Kubernetes nodes")
    success, message, _ = oim_ops.verify_kubelet_active_on_nodes()
    if success:
        log.passed(message)
    else:
        log.failed(message)
    assert success, message

def test_crio_active_on_k8s_nodes(oim_ops):
    """Test that crio (or cri-o) is active on all reachable Kubernetes nodes."""
    log = TestLogger("Verify CRI-O is active on all reachable Kubernetes nodes")
    log.check("Checking CRI-O service on Kubernetes nodes")
    success, message, _ = oim_ops.verify_crio_or_cri_o_active_on_nodes()
    if success:
        log.passed(message)
    else:
        log.failed(message)
    assert success, message

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

def test_kubectl_version(oim_ops):
    """Test that kubectl client version matches the expected version on control plane nodes."""
    log = TestLogger("Verify kubectl version on control plane nodes")
    expected_version = oim_ops.get_service_k8s_version_from_software_config()
    log.check(f"Validating kubectl client version matches service_k8s={expected_version}")
    success, message, _ = oim_ops.verify_kubectl_version_on_control_planes_check(
        expected_version,
    )
    if success:
        log.passed("kubectl version matches expected", message)
    else:
        log.failed("kubectl version mismatch detected", message)
    assert success, message

def test_all_nodes_using_crio(oim_ops):
    """Test that all nodes are using CRI-O with the expected version as the container runtime."""
    log = TestLogger("Verify all nodes are using CRI-O runtime")
    expected_version = oim_ops.get_service_k8s_version_from_software_config()
    log.check(
        f"Validating container runtime is {EXPECTED_CONTAINER_RUNTIME}://{expected_version}",
    )

    # Verify container runtime on all nodes using the new method
    all_passed, results = oim_ops.verify_all_nodes_container_runtime(
        expected_runtime=EXPECTED_CONTAINER_RUNTIME,
        expected_version=expected_version,
    )

    details_lines = []
    for node_name, is_correct, actual_runtime, error in (results or []):
        if is_correct:
            details_lines.append(f"✔ {node_name}: {actual_runtime}")
        else:
            suffix = f" ({error})" if error else ""
            details_lines.append(
                f"✘ {node_name}: {actual_runtime or 'unknown'}{suffix}",
            )
    details = "\n".join(details_lines) if details_lines else None

    if all_passed:
        log.passed("All nodes are using expected container runtime", details)
    else:
        log.failed("One or more nodes are not using expected container runtime", details)

    assert all_passed, "Container runtime check failed. See above for details."

def test_virtual_ip_configured_to_single_control_plane(oim_ops):
    """
    Test that virtual_ip_address is configured on exactly one control plane node.

    This test verifies that the virtual IP defined in the high availability config
    is configured on exactly one of the control plane nodes in the Kubernetes cluster.
    """
    log = TestLogger("Verify virtual IP is configured on exactly one control plane")
    log.check("Checking VIP ownership across control-plane nodes")
    success, message = oim_ops.verify_virtual_ip_configuration()
    if success:
        log.passed("VIP configuration validated", message)
    else:
        log.failed("VIP configuration validation failed", message)
    assert success, message

def test_clico_pods_running(oim_ops):
    """Test that all Calico pods are in 'Running' state."""
    _check_pods_with_prefix(oim_ops, "calico", "Calico")

def _check_pods_with_prefix(oim_ops, prefix, component_name):
    """
    Helper function to check pods with a given prefix.

    This is a wrapper around the OIMOperations.verify_pods_with_prefix method
    to maintain backward compatibility with existing test code.
    """
    log = TestLogger(f"Verify {component_name} pods are running")
    log.check(f"Checking pods with prefix '{prefix}'")
    success, message = oim_ops.verify_pods_with_prefix(prefix, component_name)
    if success:
        log.passed(message)
    else:
        log.failed(message)
    assert success, message

def test_coredns_pods_running(oim_ops):
    """Test that all CoreDNS pods are running."""
    _check_pods_with_prefix(oim_ops, "coredns", "CoreDNS")

def test_etcd_pods_running(oim_ops):
    """Test that all etcd pods are running."""
    _check_pods_with_prefix(oim_ops, "etcd", "etcd")

def test_kube_apiserver_pods_running(oim_ops):
    """Test that all kube-apiserver pods are running."""
    _check_pods_with_prefix(oim_ops, "kube-apiserver", "kube-apiserver")

def test_kube_controller_manager_pods_running(oim_ops):
    """Test that all kube-controller-manager pods are running."""
    _check_pods_with_prefix(oim_ops, "kube-controller-manager", "kube-controller-manager")

def test_kube_proxy_pods_running(oim_ops):
    """Test that all kube-proxy pods are running."""
    _check_pods_with_prefix(oim_ops, "kube-proxy", "kube-proxy")

def test_kube_scheduler_pods_running(oim_ops):
    """Test that all kube-scheduler pods are running."""
    _check_pods_with_prefix(oim_ops, "kube-scheduler", "kube-scheduler")

def test_kube_vip_pods_running(oim_ops):
    """Test that all kube-vip pods are running."""
    _check_pods_with_prefix(oim_ops, "kube-vip", "kube-vip")

def test_snapshot_controller_pods_running(oim_ops):
    """Test that all snapshot-controller pods are running."""
    _check_pods_with_prefix(oim_ops, "snapshot-controller", "snapshot-controller")

def test_metallb_system_pods_running(oim_ops):
    """Test that all pods in the metallb-system namespace are running."""
    log = TestLogger("Verify MetalLB pods are running")
    log.check("Checking metallb-system pods")
    success, message, pod_statuses = oim_ops.verify_metallb_pods()
    details_lines = []
    for pod in pod_statuses or []:
        ok = pod.get("status") == "Running"
        namespace = pod.get("namespace") or "metallb-system"
        line = (
            f"{namespace}/{pod.get('name')} (Node: {pod.get('node', 'Unknown')}): "
            f"{pod.get('status')}"
        )
        details_lines.append(("✔ " if ok else "✘ ") + line)
    details = "\n".join(details_lines) if details_lines else None
    if success:
        log.passed(message, details)
    else:
        log.failed(message, details)
    assert success, f"MetalLB pods check failed: {message}"

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

def test_service_cluster_metadata_exists(oim_ops):
    """Test that service_cluster_metadata.yml exists in the omnia_core container."""
    log = TestLogger("Verify service_cluster_metadata.yml exists")
    log.check(f"Checking file exists: {SERVICE_CLUSTER_METADATA_PATH}")
    exists, message, _ = oim_ops.verify_file_exists(SERVICE_CLUSTER_METADATA_PATH)
    if exists:
        log.passed(message)
    else:
        log.failed(message)
    assert exists, f"Required file not found: {SERVICE_CLUSTER_METADATA_PATH}"

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
