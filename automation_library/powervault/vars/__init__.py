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
PowerVault iSCSI storage automation variables module.
"""

from .powervault_vars import *

__all__ = [
    # Default config values
    "DEFAULT_ISCSI_PORT",
    "DEFAULT_FS_TYPE",
    "DEFAULT_MOUNT_OPTS",
    "DEFAULT_NODE_KEY",
    "DEFAULT_PERMISSIONS_OWNER",
    "DEFAULT_PERMISSIONS_GROUP",
    "DEFAULT_PERMISSIONS_MODE",
    # Paths
    "STORAGE_CONFIG_PATH",
    "FSTAB_PATH",
    "ISCSI_INITIATOR_PATH",
    # Services
    "ISCSID_SERVICE",
    "MULTIPATHD_SERVICE",
    # Log
    "ISCSI_SETUP_LOG_TEMPLATE",
    "ISCSI_SETUP_COMPLETE_MSG",
    # Multipath
    "MULTIPATH_VENDOR_PATTERNS",
    "LSSCSI_VENDOR_PATTERN",
    # Node key
    "NODE_KEY_COMMANDS",
    # I/O test
    "IO_TEST_FILE",
    "IO_TEST_BS",
    "IO_TEST_COUNT",
    "IO_TEST_CHECKSUM_FILE",
    "BIND_IO_TEST_FILE",
    # Retry
    "PORT_CHECK_TIMEOUT",
    # Commands
    "CMD_ISCSID_ACTIVE",
    "CMD_ISCSID_ENABLED",
    "CMD_MULTIPATHD_ACTIVE",
    "CMD_MULTIPATHD_ENABLED",
    "CMD_ISCSI_DISCOVERY",
    "CMD_ISCSI_SESSION",
    "CMD_ISCSI_NODE_SHOW",
    "CMD_MULTIPATH_LIST",
    "CMD_CHECK_MOUNTPOINT",
    "CMD_CHECK_DIR_EXISTS",
    "CMD_GET_FSTAB",
    "CMD_GET_PROC_MOUNTS",
    "CMD_BLKID_FSTYPE",
    "CMD_PARTED_PRINT",
    "CMD_LSBLK",
    "CMD_PORT_CHECK",
    "CMD_DF",
    "CMD_MOUNT_GREP",
]
