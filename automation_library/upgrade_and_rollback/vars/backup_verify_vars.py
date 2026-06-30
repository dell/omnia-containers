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
Upgrade Module - Backup Verification Variables.

Paths and configuration for verifying openchami backup contents after
an upgrade — quadlets, boot, cloud-init, nodes, and images.
"""

from typing import Dict, Any

from .upgrade_core_vars import UPGRADE_VARS

# =============================================================================
# BACKUP PATHS  (relative to backup_path)
# =============================================================================

_backup_path: str = UPGRADE_VARS["backup_path"]

# Quadlet files: backed up from OIM /etc/containers/systemd/
QUADLETS_BACKUP_DIR: str = f"{_backup_path}/openchami/quadlets"
QUADLETS_CURRENT_DIR: str = "/etc/containers/systemd"

# Workdir sub-directories: backed up from /opt/omnia/openchami/workdir/
_workdir_backup: str = f"{_backup_path}/openchami/openchami_data/workdir"
_workdir_current: str = "/opt/omnia/openchami/workdir"

BOOT_BACKUP_DIR: str = f"{_workdir_backup}/boot"
BOOT_CURRENT_DIR: str = f"{_workdir_current}/boot"

CLOUDINIT_BACKUP_DIR: str = f"{_workdir_backup}/cloud-init"
CLOUDINIT_CURRENT_DIR: str = f"{_workdir_current}/cloud-init"

NODES_BACKUP_DIR: str = f"{_workdir_backup}/nodes"
NODES_CURRENT_DIR: str = f"{_workdir_current}/nodes"

IMAGES_BACKUP_DIR: str = f"{_workdir_backup}/images"
IMAGES_CURRENT_DIR: str = f"{_workdir_current}/images"

# =============================================================================
# CONSOLIDATED DICT
# =============================================================================

BACKUP_VERIFY_VARS: Dict[str, Any] = {
    "container_name": UPGRADE_VARS["container_name"],
    "backup_path": _backup_path,
    "quadlets": {
        "backup_dir": QUADLETS_BACKUP_DIR,
        "current_dir": QUADLETS_CURRENT_DIR,
        "on_oim": True,
        "exclude": ["omnia_core.container"],  # Updated during upgrade with new image
    },
    "boot": {
        "backup_dir": BOOT_BACKUP_DIR,
        "current_dir": BOOT_CURRENT_DIR,
        "on_oim": False,
    },
    "cloudinit": {
        "backup_dir": CLOUDINIT_BACKUP_DIR,
        "current_dir": CLOUDINIT_CURRENT_DIR,
        "on_oim": False,
    },
    "nodes": {
        "backup_dir": NODES_BACKUP_DIR,
        "current_dir": NODES_CURRENT_DIR,
        "on_oim": False,
    },
    "images": {
        "backup_dir": IMAGES_BACKUP_DIR,
        "current_dir": IMAGES_CURRENT_DIR,
        "on_oim": False,
    },
}
