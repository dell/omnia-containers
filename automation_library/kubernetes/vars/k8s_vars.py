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

"""
Kubernetes variables for OMNIA test automation.

This module contains constants and variables used for Kubernetes testing.
"""

# Default SSH settings for Kubernetes nodes
NODE_SSH_USER = "root"
NODE_SSH_PORT = 22
NODE_SSH_TIMEOUT = 10

# Kubernetes service names
KUBELET_SERVICE = "kubelet"
CRIO_SERVICE = "crio"
CRI_O_SERVICE = "cri-o"
CHRONYD_SERVICE = "chronyd"

# Kubernetes node types
CONTROL_PLANE_GROUP = "service_kube_control_plane_x86_64"
WORKER_NODE_GROUP = "service_kube_node_x86_64"

# HA configuration
HA_CONFIG_FILE = "/opt/omnia/input/project_default/high_availability_config.yml"

# Container runtime configuration
EXPECTED_CONTAINER_RUNTIME = "cri-o"
SERVICE_CLUSTER_METADATA_PATH = "/opt/omnia/.data/service_cluster_metadata.yml"
DEFAULT_STORAGE_CLASS = "ps01"
READY_STATE_MAX_RETRIES = 6
READY_STATE_RETRY_DELAY_SECONDS = 10

# Reboot scenario timeouts
K8S_REBOOT_WAIT_ONLINE_TIMEOUT = 900     # seconds to wait for node SSH after reboot
K8S_REBOOT_WAIT_ONLINE_POLL = 15         # poll interval while waiting for SSH
K8S_CLOUD_INIT_TIMEOUT = 2400            # seconds to wait for cloud-init completion
K8S_CLOUD_INIT_POLL = 15                 # poll interval while waiting for cloud-init
K8S_NODE_READY_TIMEOUT = 600             # seconds to wait for kubectl Ready state
K8S_NODE_READY_POLL = 15                 # poll interval while waiting for Ready
K8S_VIP_FAILOVER_TIMEOUT = 120           # seconds to wait for VIP to move
K8S_VIP_FAILOVER_POLL = 10              # poll interval while waiting for VIP failover

# =============================================================================
# Input File Paths (inside omnia_core container)
# =============================================================================
PXE_MAPPING_FILE_PATH = "/opt/omnia/input/project_default/pxe_mapping_file.csv"
TELEMETRY_CONFIG_PATH = "/opt/omnia/input/project_default/telemetry_config.yml"

# =============================================================================
# NFS Provisioner Constants
# =============================================================================
NFS_DEFAULT_STORAGE_CLASS = "nfs-client"
NFS_PROVISIONER_POD_PREFIX = "nfs-client-nfs-subdir-external-provisioner"
NFS_PROVISIONER_APP_LABEL = "nfs-subdir-external-provisioner"
NFS_SERVER_ENV_VAR = "NFS_SERVER"
NFS_PATH_ENV_VAR = "NFS_PATH"
NFS_MANUAL_PROVISIONER = "kubernetes.io/no-provisioner"
SC_BINDING_MODE_IMMEDIATE = "Immediate"
NFS_MOUNT_TMP_PREFIX = "/tmp/nfs-verify-"
NFS_MOUNT_OPTIONS = "ro,soft,timeo=30"

# =============================================================================
# StorageClass Annotation Keys
# =============================================================================
SC_DEFAULT_ANNOTATION = "storageclass.kubernetes.io/is-default-class"
SC_DEFAULT_ANNOTATION_BETA = "storageclass.beta.kubernetes.io/is-default-class"

# =============================================================================
# Telemetry PVC Constants
# =============================================================================
TELEMETRY_NAMESPACE = "telemetry"
TELEMETRY_KAFKA_PVC_PATTERN = "kafka"
TELEMETRY_VMSTORAGE_PVC_PATTERN = "vmstorage"
TELEMETRY_VLSTORAGE_PVC_PATTERN = "vlstorage"
TELEMETRY_KAFKA_CFG_SECTION = "kafka_configurations"
TELEMETRY_VICTORIA_CFG_SECTION = "victoria_configurations"
TELEMETRY_PERSISTENCE_SIZE_KEY = "persistence_size"

# =============================================================================
# etcd Constants
# =============================================================================
ETCD_NAMESPACE = "kube-system"
ETCD_PORT = 2379
ETCD_PKI_CACERT = "/etc/kubernetes/pki/etcd/ca.crt"
ETCD_PKI_CERT = "/etc/kubernetes/pki/etcd/server.crt"
ETCD_PKI_KEY = "/etc/kubernetes/pki/etcd/server.key"
ETCD_RAFT_DELTA_MAX = 10

# =============================================================================
# kubectl / Command Templates
# =============================================================================
K8S_CMD_TEMPLATES = {
    "get_pv_json": "kubectl get pv -o json",
    "get_pvc_ns_json": "kubectl get pvc -n {namespace} -o json",
    "get_sc_all_json": "kubectl get sc -o json",
    "get_sc_name_json": "kubectl get storageclass {name} -o json",
    "get_pods_all_json": "kubectl get pods --all-namespaces -o json",
    "get_pods_label_all_json": "kubectl get pods --all-namespaces -l {label} -o json",
    "get_nodes_no_headers": "kubectl get nodes --no-headers",
    "get_component_status": "kubectl get componentstatus --no-headers",
    "find_etcd_pods": "kubectl get pods -n {namespace} -o name | grep '^pod/etcd-'",
    "kubectl_exec_sh_lc": "kubectl exec -n {namespace} {pod} -- sh -lc {cmd}",
    "kubectl_exec_sh_c": "kubectl exec -n {namespace} {pod} -- sh -c {cmd}",
    "etcdctl_health": (
        "ETCDCTL_API=3 etcdctl "
        "--endpoints={endpoints} "
        "--cacert={cacert} --cert={cert} --key={key} "
        "endpoint health"
    ),
    "etcdctl_member_list": (
        "ETCDCTL_API=3 etcdctl "
        "--endpoints={endpoints} "
        "--cacert={cacert} --cert={cert} --key={key} "
        "member list -w table"
    ),
    "etcdctl_endpoint_status": (
        "ETCDCTL_API=3 etcdctl "
        "--endpoints={endpoints} "
        "--cacert={cacert} --cert={cert} --key={key} "
        "endpoint status -w json"
    ),
}

NFS_CMD_TEMPLATES = {
    "get_provisioner_pods": "kubectl get pods --all-namespaces -l app={app_label} -o json",
    "mount_nfs": (
        "mkdir -p {mount_point} && "
        "mount -t nfs -o {options} {server}:{path} {mount_point}"
    ),
    "check_dir_exists": "test -d {path} && echo EXISTS || echo MISSING",
    "stat_dir": "stat -c '%a %U %G' {path}",
    "umount_cleanup": (
        "umount {mount_point} 2>/dev/null || umount -f {mount_point} 2>/dev/null; "
        "rmdir {mount_point} 2>/dev/null"
    ),
}