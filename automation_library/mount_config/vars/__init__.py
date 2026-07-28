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
Mount configuration variables module.
"""

from .mount_config_vars import (
    DEFAULT_FS_TYPE,
    DEFAULT_MOUNT_OPTS,
    DEFAULT_DUMP_FREQ,
    DEFAULT_FSCK_PASS,
    DEFAULT_NODE_KEY,
    NODE_KEY_COMMANDS,
    FSTAB_BIND_FS_TYPE,
    FSTAB_BIND_OPTIONS,
    IO_TEST_FILE,
    IO_TEST_CONTENT,
    IO_TEST_CHECKSUM_FILE,
)

__all__ = [
    "DEFAULT_FS_TYPE",
    "DEFAULT_MOUNT_OPTS",
    "DEFAULT_DUMP_FREQ",
    "DEFAULT_FSCK_PASS",
    "DEFAULT_NODE_KEY",
    "NODE_KEY_COMMANDS",
    "FSTAB_BIND_FS_TYPE",
    "FSTAB_BIND_OPTIONS",
    "IO_TEST_FILE",
    "IO_TEST_CONTENT",
    "IO_TEST_CHECKSUM_FILE",
]
