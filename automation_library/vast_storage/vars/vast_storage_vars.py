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
VAST Storage automation constants, paths, and configuration.

Spec: TSPEC-STOR-2026-001 v1.0.0
"""

# =============================================================================
# NODE FUNCTIONAL GROUPS
# =============================================================================
COMPUTE_NODE_FUNCTIONAL_GROUP = "slurm_node_x86_64"
CONTROLLER_NODE_FUNCTIONAL_GROUP = "service_kube_control"
LOGIN_NODE_FUNCTIONAL_GROUP = "login_node"
LOGIN_COMPILER_NODE_FUNCTIONAL_GROUP = "login_compiler_node"

# =============================================================================
# CONFIGURATION PATHS
# =============================================================================
STORAGE_CONFIG_PATH = "/omnia/input/storage_config.yaml"
PXE_MAPPING_PATH = "/omnia/input/pxe_mapping.csv"
ANSIBLE_INVENTORY_PATH = "/omnia/inventory/ansible_inventory.yml"
FSTAB_PATH = "/etc/fstab"
CLOUD_INIT_LOG_PATH = "/var/log/cloud-init.log"

# =============================================================================
# VAST SPECIFIC PATHS AND COMMANDS
# =============================================================================
VAST_CLIENT_RPM_PATH = "/opt/omnia/omnia/offline_repo/cluster/x86_64/rhel/10.0/tarball/vastnfs*.rpm"
VAST_KERNEL_MODULE = "vastnfs"
VAST_CTL_COMMAND = "vastnfs-ctl"
VAST_MOUNT_UNIT_PREFIX = "vast-"

# =============================================================================
# STORAGE BACKEND PATHS
# =============================================================================
POWERSCALE_NFS_EXPORT = "powerscale.corp.com:/ifs/omnia"
POWERVAULT_ISCSI_TARGET = "iqn.2003-01.com.dell:powervault"

# =============================================================================
# MOUNT POINTS
# =============================================================================
VAST_MOUNT_POINTS = [
    "/home",
    "/apps",
    "/hpc_tools",
    "/scratch",
    "/projects",
]

POWERSCALE_MOUNT_POINTS = [
    "/cert",
    "/etc/slurm/epilog.d",
    "/etc/munge",
    "/var/log/slurm",
    "/var/log/track",
    "/var/lib/packages",
    "/slurm/ssh",
    "/ldapcerts",
    "/ldms",
]

POWERVAULT_MOUNT_POINTS = [
    "/var/lib/mysql",
    "/var/lib/slurm",
]

SHARED_NAMESPACE_DIRS = ["home", "apps", "slurm", "scratch"]
NODE_SPECIFIC_SCRATCH_PATH = "/scratch/$HOSTNAME"
TMP_BIND_MOUNT_PATH = "/scratch/$HOSTNAME/tmp"

# =============================================================================
# NETWORK CONFIGURATION
# =============================================================================
IB_INTERFACE = "ib0"
IB_MTU = 2408  # RHEL10 compatible
IB_SUBNET = "192.168.0.0/16"
VAST_RDMA_PORT = 20049
NFS_TCP_PORT = 2049
ISCSI_PORT = 3260

# =============================================================================
# DNS CONFIGURATION
# =============================================================================
VAST_FQDN = "hpcpool.vast.corp.com"
IB_DNS_SERVER = "192.168.10.10"

# =============================================================================
# MOUNT OPTIONS
# =============================================================================
VAST_MOUNT_OPTIONS = {
    "proto": "rdma",
    "port": str(VAST_RDMA_PORT),
    "nconnect": "8",
    "rsize": "1048576",
    "wsize": "1048576",
    "hard": None,
    "timeo": "600",
    "retrans": "2",
    "_netdev": None,
}

POWERSCALE_MOUNT_OPTIONS = {
    "nfsvers": "3",
    "proto": "tcp",
    "nconnect": "4",
    "rsize": "262144",
    "wsize": "262144",
    "hard": None,
    "timeo": "600",
    "retrans": "2",
    "_netdev": None,
}

POWERVAULT_MOUNT_OPTIONS = {
    "_netdev": None,
    "auto": None,
}

# =============================================================================
# PERFORMANCE TARGETS (from BSpec 6.1.5/6.1.6)
# =============================================================================
RDMA_LATENCY_TARGET_US = 200  # Average latency in microseconds
RDMA_LATENCY_P99_US = 500  # 99th percentile latency
THROUGHPUT_TARGET_GB = 20  # Aggregate throughput in GB/s
IOPS_TARGET = 1000000  # 1M IOPS for 4KB random read
BOOT_TIME_TOLERANCE_PERCENT = 5  # Boot time should not increase by more than 5%

# =============================================================================
# RETRY CONFIGURATION
# =============================================================================
MOUNT_RETRY_COUNT = 3
MOUNT_RETRY_DELAYS = [1, 2, 4]  # Exponential backoff in seconds

# =============================================================================
# TEST DATA CONFIGURATION
# =============================================================================
TEST_DATASET_PATH = "/tmp/vast_test_data"
CHECKPOINT_DATA_SIZE_GB = 10
RANDOM_IO_SIZE_GB = 1
SEQUENTIAL_STREAM_SIZE_GB = 100
METADATA_OPS_FILE_COUNT = 100000

# =============================================================================
# VALIDATION COMMANDS
# =============================================================================
VALIDATION_COMMANDS = {
    "check_ib_link": "ibstat {interface} | grep 'State:.*Active'",
    "check_rdma_module": "lsmod | grep -E '(mlx5_ib|ib_core|rdma_cm)'",
    "check_vast_module": f"lsmod | grep {VAST_KERNEL_MODULE}",
    "check_vast_rpm": "rpm -qa | grep vastnfs",
    "check_mount_rdma": "nfsstat -m | grep -E 'proto=rdma.*port={port}'",
    "check_mount_tcp": "nfsstat -m | grep -E 'proto=tcp.*port=2049'",
    "check_ib_ip": "ip addr show {interface} | grep 'inet '",
    "check_ib_mtu": "ip link show {interface} | grep 'mtu {mtu}'",
    "check_dns_resolution": f"nslookup {VAST_FQDN} {IB_DNS_SERVER}",
    "check_port_connectivity": "nc -zv {host} {port}",
    "check_systemd_mount": "systemctl status {unit}.mount",
    "check_fstab_entry": f"grep '{{mount_point}}' {FSTAB_PATH}",
    "check_mount_point": "mountpoint -q {mount_point}",
    "check_vast_status": f"{VAST_CTL_COMMAND} status",
}

# =============================================================================
# ERROR PATTERNS
# =============================================================================
ERROR_PATTERNS = {
    "stale_handle": r"Stale (NFS )?file handle|ESTALE",
    "mount_timeout": r"mount\.nfs: .*timed out",
    "rdma_failure": r"RDMA.*failed|rdma_resolve_addr",
    "ib_link_down": r"Port State:.*Down|IB link.*down",
    "dns_failure": r"can't find.*NXDOMAIN|Name or service not known",
    "permission_denied": r"Permission denied|Access denied",
    "transport_endpoint": r"Transport endpoint is not connected",
    "yaml_syntax": r"yaml\.scanner\.ScannerError|YAML.*error",
    "duplicate_mount": r"Duplicate mount.*detected",
    "missing_config": r"storage_config\.yaml.*not found|missing.*section",
}
