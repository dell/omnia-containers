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

"""Upgrade Functions Module."""

from .upgrade_core_func import (
    validate_operation,
    validate_versions,
    validate_config,
    check_backup_exists,
    check_pre_upgrade_container,
    clone_upgrade_repo,
    build_core_image,
    verify_podman_image,
    download_omnia_sh,
    run_omnia_upgrade,
    verify_backup_directory,
    verify_input_files_backup,
    verify_metadata_backup,
    verify_quadlet_backup,
    verify_post_upgrade_state,
)
from .prepare_upgrade_func import (
    run_prepare_upgrade,
)

__all__ = [
    "validate_operation",
    "validate_versions",
    "validate_config",
    "check_backup_exists",
    "check_pre_upgrade_container",
    "clone_upgrade_repo",
    "build_core_image",
    "verify_podman_image",
    "download_omnia_sh",
    "run_omnia_upgrade",
    "verify_backup_directory",
    "verify_input_files_backup",
    "verify_metadata_backup",
    "verify_quadlet_backup",
    "verify_post_upgrade_state",
    "run_prepare_upgrade",
]
