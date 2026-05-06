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

"""Kubernetes message constants used by the OMNIA automation library."""

TEST_PASSED = "PASSED"
TEST_FAILED = "FAILED"
TEST_SKIPPED = "SKIPPED"

ERROR_NODES_UNREACHABLE = "All Kubernetes nodes are unreachable"
ERROR_SERVICE_INACTIVE = "Service {service} is not active on node {node}"
ERROR_PXE_MAPPING_EMPTY = "No kube control-plane / kube-node nodes found in pxe_mapping_file"
ERROR_NO_NODES_FOUND = "No nodes found in PXE mapping file"
ERROR_NO_CONTROL_PLANE_NODES = "No control plane nodes found in the cluster"
ERROR_KUBECTL_VERSION_MISMATCH = (
    "kubectl version mismatch. Expected: {expected}, Actual: {actual} "
    "on node: {node}"
)

STATUS_CHECKING_NODE = "Checking node: {node} (target: {target})"
STATUS_SERVICE_ACTIVE = "{service} is active on {node}"
STATUS_SERVICE_INACTIVE = "{service} is not active on {node}"
STATUS_NODE_UNREACHABLE = "Node {node} is unreachable via {target}"
STATUS_TEST_PASSED = "All reachable nodes passed {service} check"
STATUS_TEST_FAILED = "One or more reachable nodes failed {service} check"

HA_VIRTUAL_IP_NOT_FOUND = "virtual_ip_address not found in high_availability_config.yml"
HA_INVALID_YAML = "Invalid YAML in {file_path}"
HA_NO_CONTROL_PLANE_NODES = "No control plane nodes found in PXE mapping"
HA_VIP_MULTIPLE_NODES = "Virtual IP {vip} is configured on multiple control plane nodes: {nodes}"
HA_VIP_NOT_CONFIGURED = "Virtual IP {vip} is not configured on any control plane node"
HA_VIP_CONFIGURED = "Virtual IP {vip} is configured on exactly one control plane node: {node}"
HA_VIP_CHECK_PASSED = "Virtual IP check passed: {message}"
HA_VIP_CHECK_FAILED = "Virtual IP check failed: {message}"

RUNTIME_CHECK_PASSED = "All nodes are using the expected container runtime: {runtime}"
RUNTIME_CHECK_FAILED = "One or more nodes are not using the expected container runtime: {runtime}"
RUNTIME_MISMATCH = (
    "Container runtime mismatch. Expected '{expected}', got '{actual}' on node: {node}"
)
RUNTIME_CHECK_ERROR = "Error checking container runtime on node {node}: {error}"

POD_CHECK_PREFIX = "Checking pods with prefix: {prefix}"
POD_CHECK_PASSED = "All {component} pods are running"
POD_CHECK_FAILED = "One or more {component} pods are not running"
POD_NOT_FOUND = "No pods found with prefix '{prefix}'"
POD_STATUS = "{status} {namespace}/{name} (Node: {node}): {phase}"

METALLB_NAMESPACE_NOT_FOUND = "metallb-system namespace not found. Is MetalLB installed?"
METALLB_PODS_RUNNING = "All MetalLB pods are running"
METALLB_PODS_FAILED = "Some MetalLB pods are not running: {failed_pods}"
METALLB_NO_PODS_FOUND = "No pods found in the metallb-system namespace. Is MetalLB installed?"
METALLB_CHECK_ERROR = "Error verifying MetalLB pods: {error}"

NFS_PROVISIONER_NOT_FOUND = (
    "NFS client provisioner pod not found. Is the NFS subdir external provisioner installed?"
)
NFS_PROVISIONER_RUNNING = "NFS client provisioner pod is running"
NFS_PROVISIONER_NOT_RUNNING = "NFS client provisioner pod is not running. Current status: {status}"
NFS_PROVISIONER_CHECK_ERROR = "Error verifying NFS provisioner pod: {error}"

RUNTIME_CHECK_HEADER = "\n=== Container Runtime Check ==="
EXPECTED_RUNTIME_MSG = "Expected runtime: {runtime} {version}"
RUNTIME_CHECK_NODE_PASS = "[PASS] {node}: Using {runtime}"
RUNTIME_CHECK_NODE_FAIL = "[FAIL] {node}: Expected {expected}, got {actual}"
RUNTIME_CHECK_NODE_ERROR = "[ERROR] {node}: {error}"
RUNTIME_CHECK_NO_NODES = "[ERROR] No nodes found to check container runtime"
RUNTIME_CHECK_ALL_PASSED = "\nAll nodes are using the expected container runtime"
RUNTIME_CHECK_SOME_FAILED = "\nSome nodes are not using the expected container runtime"
RUNTIME_CHECK_FAILED_MSG = "Not all nodes are using the expected container runtime"

FILE_EXISTS = "File {path} exists in omnia_core container"
FILE_NOT_FOUND = "File {path} not found in omnia_core container"
DIRECTORY_EXISTS = "Directory {path} exists"
DIRECTORY_NOT_FOUND = "Directory {path} does not exist"
FILE_CHECK_ERROR = "Error checking file: {error}"

REBOOT_VIP_NODE_INITIATED = "Reboot initiated on VIP-holder control plane {node} ({ip})"
REBOOT_VIP_NODE_NOT_FOUND = "VIP {vip} is not configured on any control plane node"
REBOOT_VIP_NO_REMAINING = "No remaining control plane nodes found after VIP holder identified"

K8S_NODE_ONLINE_PASSED = "Node {node} ({ip}) is back online after reboot (elapsed: {elapsed}s)"
K8S_NODE_ONLINE_FAILED = "Node {node} ({ip}) did not come back online within {timeout}s"

K8S_CLOUD_INIT_PASSED = "cloud-init completed successfully on {node} ({ip})"
K8S_CLOUD_INIT_FAILED = "cloud-init did NOT complete on {node} ({ip}) within {timeout}s"

K8S_NODE_READY_PASSED = "Node {node} returned to Ready state after reboot"
K8S_NODE_READY_FAILED = "Node {node} did not return to Ready state within {timeout}s (last status: {status})"

K8S_VIP_FAILOVER_PASSED = "VIP {vip} successfully failed over from {old_node} to {new_node} ({new_ip})"
K8S_VIP_FAILOVER_FAILED = "VIP {vip} did not fail over to any remaining control plane within {timeout}s"
K8S_VIP_FAILOVER_MULTI = "VIP {vip} found on multiple nodes after failover: {nodes}"

# =============================================================================
# Generic / shared kubectl errors
# =============================================================================
ERR_NO_CONTROL_PLANE_HOST = "Control plane node has no hostname or IP address"
ERR_NO_NODES_IN_PXE = "No nodes found in PXE mapping"
ERR_NO_CP_IN_PXE = "No control-plane nodes found in PXE mapping"
ERR_NO_CP_ADMIN_IPS = "No control-plane admin IPs found in PXE mapping"
ERR_CP_MISSING_HOST = "Control-plane node missing hostname/admin_ip in PXE mapping"
ERR_CP_MISSING_ADMIN_IP = "Control-plane node missing admin_ip"
ERR_NO_VALID_CP_IPS = "No valid admin IPs found for control plane nodes"

# =============================================================================
# NFS StorageClass messages
# =============================================================================
NFS_SC_NOT_FOUND = "StorageClass '{name}' not found: {error}"
NFS_SC_PARSE_ERROR = "Failed to parse StorageClass output: {error}"
NFS_SC_NO_DYNAMIC_PROVISIONER = "StorageClass has no dynamic provisioner (provisioner={provisioner})"
NFS_SC_UNEXPECTED_BINDING_MODE = "Unexpected volumeBindingMode: {mode} (expected 'Immediate')"
NFS_SC_NO_SERVER = "Could not resolve NFS server from provisioner pod env vars (NFS_SERVER)"
NFS_SC_NO_PATH = "Could not resolve NFS path from provisioner pod env vars (NFS_PATH)"
NFS_SC_VALIDATION_FAILED = "NFS StorageClass '{name}' validation failed: {errors}"
NFS_SC_DYNAMIC = "NFS StorageClass '{name}' is dynamic: provisioner={provisioner}, server={server}, path={path}"
NFS_SC_ERROR = "Error verifying NFS StorageClass: {error}"

# =============================================================================
# Telemetry PVC messages
# =============================================================================
TELEMETRY_PVC_READ_CONFIG_ERROR = "Failed to read telemetry_config.yml: {error}"
TELEMETRY_PVC_PARSE_CONFIG_ERROR = "Failed to parse telemetry_config.yml: {error}"
TELEMETRY_PVC_GET_ERROR = "Failed to get PVCs in namespace '{namespace}': {error}"
TELEMETRY_PVC_PARSE_ERROR = "Failed to parse PVC output: {error}"
TELEMETRY_PVC_NONE_FOUND = "No PVCs found in namespace '{namespace}'"
TELEMETRY_PVC_PHASE_MISMATCH = "phase={phase} (expected 'Bound')"
TELEMETRY_PVC_SC_MISMATCH = "storageClass={sc} (expected {expected})"
TELEMETRY_PVC_NO_VOLUME = "volumeName not set (no PV provisioned)"
TELEMETRY_PVC_KAFKA_SIZE_MISMATCH = (
    "size={actual} (expected {expected} from kafka_configurations.persistence_size)"
)
TELEMETRY_PVC_VICTORIA_SIZE_MISMATCH = (
    "size={actual} (expected {expected} from victoria_configurations.persistence_size)"
)
TELEMETRY_PVC_CHECK_FAILED = (
    "Telemetry PVC check failed ({failed}/{total} PVCs): {errors}"
)
TELEMETRY_PVC_CHECK_PASSED = (
    "All {count} telemetry PVC(s) in namespace '{namespace}' are Bound "
    "with StorageClass={sc} and correct PV/size assigned"
)
TELEMETRY_PVC_ERROR = "Error verifying telemetry PVCs: {error}"

# =============================================================================
# NFS backend directory messages
# =============================================================================
NFS_DIR_GET_PV_ERROR = "Failed to get PVs: {error}"
NFS_DIR_PARSE_PV_ERROR = "Failed to parse PV output: {error}"
NFS_DIR_NO_PVS = "No PVs found with StorageClass={sc} to check directories for"
NFS_DIR_MOUNT_ERROR = "Could not mount NFS export {server}:{path}: {error}"
NFS_DIR_NOT_FOUND = "directory '{subdir}' not found under {server}:{path}"
NFS_DIR_NOT_FOUND_REASON = "Directory not found"
NFS_DIR_CHECK_FAILED = "NFS backend directory check failed ({failed}/{total} PVs): {errors}"
NFS_DIR_CHECK_PASSED = "All {count} NFS backend directories verified via NFS mount"
NFS_DIR_ERROR = "Error verifying NFS backend directories: {error}"

# =============================================================================
# StorageClass (default SC) messages
# =============================================================================
SC_GET_ERROR = "Failed to get storage classes: {error}"
SC_NONE_FOUND = "No storage classes found"
SC_NOT_FOUND = "Storage class '{name}' not found"
SC_NOT_DEFAULT = "Storage class '{name}' exists but is not set as default"
SC_IS_DEFAULT = "Storage class '{name}' exists and is set as default"
SC_PARSE_ERROR = "Failed to parse storage class information: {error}"
SC_VERIFY_ERROR = "Error verifying storage class: {error}"

# =============================================================================
# etcd messages
# =============================================================================
ETCD_PODS_FIND_FAILED = "Failed to find etcd pods: {error}"
ETCD_PODS_NONE_FOUND = "No etcd pods found in kube-system namespace"
ETCD_HEALTH_ALL_PASSED = "All {count} etcd endpoints are healthy"
ETCD_HEALTH_PARTIAL = (
    "Not all etcd endpoints are healthy: {healthy}/{total} healthy. "
    "Unhealthy endpoints: {unhealthy}"
)
ETCD_HEALTH_NO_OUTPUT = "etcdctl endpoint health failed on all etcd pods. Last error: {error}"
ETCD_MEMBER_COUNT_MISMATCH = "etcd member count mismatch (found={found}, expected={expected})"
ETCD_MEMBER_LIST_PASSED = "etcd member list verified ({count} members)"
ETCD_MEMBER_LIST_FAILED = "etcdctl member list failed on all etcd pods. Last error: {error}"
ETCD_LEADER_FAILED_RUN = "Failed to run etcdctl from etcd pods: {error}"
ETCD_LEADER_PARSE_FAILED = "Failed to parse etcdctl output: {error}"
