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
