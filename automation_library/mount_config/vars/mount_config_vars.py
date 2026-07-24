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
Variables for mount_config test automation.
"""

# Default mount values (same priority as mount_config role)
DEFAULT_FS_TYPE = "auto"
DEFAULT_MOUNT_OPTS = "defaults"
DEFAULT_DUMP_FREQ = "0"
DEFAULT_FSCK_PASS = "0"
DEFAULT_NODE_KEY = "local_hostname"
DEFAULT_MOUNT_DIR_PERM = "0755"

# Supported node_key values
NODE_KEY_COMMANDS = {
    "local_hostname": "hostname -s",
    "local_ipv4": "hostname -I | awk '{print $1}'",
    "instance_id": "cloud-init query v1.instance_id",
}

# Node-specific bind mount fstab field separator
FSTAB_BIND_FS_TYPE = "none"
FSTAB_BIND_OPTIONS = "bind,_netdev"

# Test file used for bind isolation / I/O tests
IO_TEST_FILE = "omnia_mount_test"
IO_TEST_CONTENT = "omnia_mount_config_test"
IO_TEST_CHECKSUM_FILE = "omnia_mount_test.sha256"
