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

"""Upgrade and Rollback Messages Module."""

from .upgrade_core_msgs import (
    TEST_NAMES,
    TEST_LOG_MSGS,
    TEST_ASSERT_MSGS,
    SKIP_MSGS,
)
from .backup_verify_msgs import (
    BACKUP_TEST_NAMES,
    BACKUP_LOG_MSGS,
    BACKUP_ASSERT_MSGS,
    BACKUP_SKIP_MSGS,
)
from .prepare_upgrade_msgs import (
    PREPARE_TEST_NAMES,
    PREPARE_LOG_MSGS,
    PREPARE_ASSERT_MSGS,
    PREPARE_SKIP_MSGS,
)
from .rollback_core_msgs import (
    ROLLBACK_TEST_NAMES,
    ROLLBACK_LOG_MSGS,
    ROLLBACK_ASSERT_MSGS,
    ROLLBACK_SKIP_MSGS,
)

# K8s & Telemetry upgrade
from .k8s_telemetry_upgrade_msgs import (
    PRECHECK_TEST_NAMES,
    PRECHECK_LOG_MSGS,
    PRECHECK_ASSERT_MSGS,
    POSTCHECK_TEST_NAMES,
    POSTCHECK_LOG_MSGS,
    POSTCHECK_ASSERT_MSGS,
    SKIP_MSGS as K8S_TEL_SKIP_MSGS,
)

__all__ = [
    "TEST_NAMES",
    "TEST_LOG_MSGS",
    "TEST_ASSERT_MSGS",
    "SKIP_MSGS",
    "BACKUP_TEST_NAMES",
    "BACKUP_LOG_MSGS",
    "BACKUP_ASSERT_MSGS",
    "BACKUP_SKIP_MSGS",
    "PREPARE_TEST_NAMES",
    "PREPARE_LOG_MSGS",
    "PREPARE_ASSERT_MSGS",
    "PREPARE_SKIP_MSGS",
    "ROLLBACK_TEST_NAMES",
    "ROLLBACK_LOG_MSGS",
    "ROLLBACK_ASSERT_MSGS",
    "ROLLBACK_SKIP_MSGS",
    # K8s & Telemetry upgrade
    "PRECHECK_TEST_NAMES",
    "PRECHECK_LOG_MSGS",
    "PRECHECK_ASSERT_MSGS",
    "POSTCHECK_TEST_NAMES",
    "POSTCHECK_LOG_MSGS",
    "POSTCHECK_ASSERT_MSGS",
    "K8S_TEL_SKIP_MSGS",
]
