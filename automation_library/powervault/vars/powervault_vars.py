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
PowerVault iSCSI storage automation constants, paths, and configuration.
"""

# =============================================================================
# DEFAULT CONFIGURATION VALUES
# =============================================================================
DEFAULT_ISCSI_PORT = 3260
DEFAULT_FS_TYPE = "xfs"
DEFAULT_MOUNT_OPTS = "defaults,_netdev"
DEFAULT_NODE_KEY = "local_hostname"
DEFAULT_PERMISSIONS_OWNER = "root"
DEFAULT_PERMISSIONS_GROUP = "root"
DEFAULT_PERMISSIONS_MODE = "0755"

# =============================================================================
# CONFIGURATION PATHS (inside omnia_core container)
# =============================================================================
STORAGE_CONFIG_PATH = "/opt/omnia/input/project_default/storage_config.yml"
FSTAB_PATH = "/etc/fstab"
ISCSI_INITIATOR_PATH = "/etc/iscsi/initiatorname.iscsi"

# =============================================================================
# ISCSI SERVICE NAMES
# =============================================================================
ISCSID_SERVICE = "iscsid"
MULTIPATHD_SERVICE = "multipathd"

# =============================================================================
# LOG PATH TEMPLATE
# =============================================================================
ISCSI_SETUP_LOG_TEMPLATE = "/var/log/omnia_iscsi_setup_{name}.log"
ISCSI_SETUP_COMPLETE_MSG = "iSCSI/multipath setup complete"

# =============================================================================
# MULTIPATH VENDOR PATTERNS
# =============================================================================
MULTIPATH_VENDOR_PATTERNS = ["DellEMC,ME5", "DellEMC,ME4", "DELL", "ME"]
LSSCSI_VENDOR_PATTERN = "ME|DELL"

# =============================================================================
# NODE KEY RESOLUTION COMMANDS
# =============================================================================
NODE_KEY_COMMANDS = {
    "local_hostname": "hostname -s",
    "local_ipv4": "hostname -I | awk '{print $1}'",
    "instance_id": "cloud-init query instance_id 2>/dev/null || cat /var/lib/cloud/data/instance-id 2>/dev/null || hostname",
}

# =============================================================================
# I/O TEST CONFIGURATION
# =============================================================================
IO_TEST_FILE = "test_io_pv"
IO_TEST_BS = "1M"
IO_TEST_COUNT = 100
IO_TEST_CHECKSUM_FILE = "/tmp/pv_checksum"
BIND_IO_TEST_FILE = "test_bind_io"

# =============================================================================
# RETRY CONFIGURATION
# =============================================================================
PORT_CHECK_TIMEOUT = 5

# =============================================================================
# VALIDATION COMMANDS
# =============================================================================
CMD_ISCSID_ACTIVE = "systemctl is-active iscsid"
CMD_ISCSID_ENABLED = "systemctl is-enabled iscsid"
CMD_MULTIPATHD_ACTIVE = "systemctl is-active multipathd"
CMD_MULTIPATHD_ENABLED = "systemctl is-enabled multipathd"
CMD_ISCSI_DISCOVERY = "iscsiadm -m discovery -t sendtargets -p {ip}:{port}"
CMD_ISCSI_SESSION = "iscsiadm -m session"
CMD_ISCSI_NODE_SHOW = "iscsiadm -m node -o show"
CMD_MULTIPATH_LIST = "multipath -ll"
CMD_CHECK_MOUNTPOINT = "mountpoint -q {path} && echo mounted || echo not_mounted"
CMD_CHECK_DIR_EXISTS = "test -d {path} && echo exists || echo not_exists"
CMD_GET_FSTAB = "cat /etc/fstab"
CMD_GET_PROC_MOUNTS = "cat /proc/mounts"
CMD_BLKID_FSTYPE = "blkid -s TYPE -o value {device}"
CMD_PARTED_PRINT = "parted -s {device} print 2>/dev/null"
CMD_LSBLK = "lsblk -o NAME,TYPE,FSTYPE {device} 2>/dev/null"
CMD_PORT_CHECK = "timeout {timeout} bash -c 'echo > /dev/tcp/{ip}/{port}' 2>/dev/null && echo reachable || echo unreachable"
CMD_DF = "df -h {path}"
CMD_MOUNT_GREP = "mount | grep '{pattern}'"
