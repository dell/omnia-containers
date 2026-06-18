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
Upgrade Module.

Functions, variables, and messages for testing the Omnia upgrade / rollback
workflow (e.g., upgrading from 2.1.0.0 to 2.2.0.0).

Test Categories:
- Pre-upgrade: Validate operation, verify current container version
- Build: Clone repo, build core image, download omnia.sh
- Upgrade: Run omnia.sh --upgrade with automated interactive input
- Post-upgrade: Verify backup folders, new container version, container health
"""

from .functions import (
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
    verify_post_upgrade_state,
    run_prepare_upgrade,
    verify_backup_md5sum,
)
from .vars import (
    UPGRADE_VARS,
    SUPPORTED_VERSIONS,
    VALID_OPERATIONS,
    VERSION_PROPERTIES,
    get_core_tag_for_version,
    PREPARE_UPGRADE_VARS,
    BACKUP_VERIFY_VARS,
)
from .messages import (
    TEST_NAMES,
    TEST_LOG_MSGS,
    TEST_ASSERT_MSGS,
    SKIP_MSGS,
)
