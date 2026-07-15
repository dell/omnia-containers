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
etcd local disk variables for OMNIA test automation.

This module contains constants and variables used for etcd local disk testing.
"""

# =============================================================================
# OMNIA CONFIG
# =============================================================================

ETCD_ON_LOCAL_DISK_KEY = "etcd_on_local_disk"

# =============================================================================
# ETCD PATHS
# =============================================================================

ETCD_MOUNT_PATH = "/var/lib/etcd"
ETCD_DISK_SETUP_SCRIPT = "/usr/local/bin/etcd-disk-setup.sh"
ETCD_FSTAB_UPDATE_SCRIPT = "/usr/local/bin/etcd-fstab-update.sh"
ETCD_DISK_SETUP_LOG = "/var/log/etcd-disk-setup.log"
ETCD_FSTAB_UPDATE_LOG = "/var/log/diskless-etcd-mount.log"

# =============================================================================
# BOSS CARD DETECTION
# =============================================================================

BOSS_PCI_VENDOR_ID = "1028"
BOSS_MODEL_KEYWORDS = ["boss", "BOSS"]
BOSS_LSPCI_CMD = "lspci -nn -d 1028:"

# =============================================================================
# RAID CONFIGURATION
# =============================================================================

MEGACLI_LDINFO_CMD = "MegaCli -LDInfo -Lall -aALL"
RAID_OPTIMAL_STATE = "Optimal"
RAID_SUPPORTED_LEVELS = ["RAID-1", "RAID-10"]

# =============================================================================
# DISK AND FILESYSTEM
# =============================================================================

SUPPORTED_FILESYSTEMS = ["ext4"]
PARTITION_TABLE_TYPE = "gpt"
ETCD_DATA_LABEL = "etcd_data"

# =============================================================================
# DISK TYPES
# =============================================================================

DISK_TYPE_SSD = "ssd"
DISK_TYPE_HDD = "hdd"
DISK_TYPE_NVME = "nvme"

# =============================================================================
# ETCD USER AND PERMISSIONS
# =============================================================================

ETCD_USER = "etcd"
ETCD_GROUP = "etcd"
ETCD_DIR_PERMISSIONS = "700"

# =============================================================================
# NFS FALLBACK
# =============================================================================

NFS_MOUNT_TYPE = "nfs"

# =============================================================================
# REBOOT TIMEOUTS
# =============================================================================

REBOOT_WAIT_ONLINE_TIMEOUT = 300  # seconds to wait for node to come back
REBOOT_WAIT_ONLINE_POLL = 10      # poll interval in seconds
CLOUD_INIT_TIMEOUT = 600          # seconds to wait for cloud-init
CLOUD_INIT_POLL = 15              # poll interval in seconds
