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
Rollback Module.

Functions, variables, and messages for testing the Omnia rollback workflow.
Rollback restores the omnia_core container from the upgraded version back
to the original version (e.g., 2.2.0.0 → 2.1.0.0).

Test Categories:
- Pre-rollback: Verify rollback image is available
- Rollback: Download omnia.sh, run --rollback
- Post-rollback: Verify container version, verify restored files
"""

from .functions import (
    verify_rollback_precondition,
    check_rollback_image,
    download_omnia_sh_for_rollback,
    run_omnia_rollback,
    verify_rollback_container,
    verify_rollback_backup_md5sum,
)
from .vars import (
    ROLLBACK_VARS,
)
from .messages import (
    ROLLBACK_TEST_NAMES,
    ROLLBACK_LOG_MSGS,
    ROLLBACK_ASSERT_MSGS,
    ROLLBACK_SKIP_MSGS,
)
