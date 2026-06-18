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
Upgrade Module

This module provides functions for verifying the Omnia upgrade workflow
(e.g., upgrading from 2.1.0.0 to 2.2.0.0).

Test Categories:
- Pre-upgrade: Verify current omnia_core container version
- Build: Clone new artifactory and build core image
- Upgrade: Run omnia.sh --upgrade and verify completion
- Post-upgrade: Verify backup, new container version, old container removed
"""

from .functions import (
    get_current_omnia_version,
    verify_pre_upgrade_state,
    clone_upgrade_artifactory,
    build_upgrade_core_image,
    run_omnia_upgrade,
    verify_backup_folder,
    verify_post_upgrade_version,
    verify_no_old_container,
)
from .vars import (
    UPGRADE_VARS,
)
from .messages import (
    TEST_NAMES,
    TEST_LOG_MSGS,
    TEST_ASSERT_MSGS,
    SKIP_MSGS,
)
