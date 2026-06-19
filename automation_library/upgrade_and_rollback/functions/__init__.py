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

"""Upgrade and Rollback Functions Module."""

from .common_func import (
    compare_versions,
    get_oim_metadata,
    check_container_service_status,
)
from .upgrade_core_func import (
    validate_upgrade_versions,
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
    verify_post_upgrade_state,
)
from .prepare_upgrade_func import run_prepare_upgrade
from .backup_verify_func import verify_backup_md5sum
from .rollback_core_func import (
    verify_rollback_precondition,
    check_rollback_image,
    download_omnia_sh_for_rollback,
    run_omnia_rollback,
    verify_rollback_container,
    verify_rollback_backup_md5sum,
)

__all__ = [
    "compare_versions",
    "get_oim_metadata",
    "check_container_service_status",
    "validate_upgrade_versions",
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
    "verify_post_upgrade_state",
    "run_prepare_upgrade",
    "verify_backup_md5sum",
    "verify_rollback_precondition",
    "check_rollback_image",
    "download_omnia_sh_for_rollback",
    "run_omnia_rollback",
    "verify_rollback_container",
    "verify_rollback_backup_md5sum",
]
