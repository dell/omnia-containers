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
Slurm messages module.
"""

from .slurm_msgs import (
    TEST_NAMES,
    TEST_LOG_MSGS,
    TEST_ASSERT_MSGS,
    LDAP_TEST_NAMES,
    LDAP_LOG_MSGS,
    LDAP_ASSERT_MSGS,
    QUEUEING_TEST_NAMES,
    QUEUEING_LOG_MSGS,
    PAM_TEST_NAMES,
    PAM_LOG_MSGS,
    PAM_ASSERT_MSGS,
    STABILITY_TEST_NAMES,
    STABILITY_LOG_MSGS,
    STABILITY_ASSERT_MSGS,
    DRAIN_TEST_NAMES,
    DRAIN_LOG_MSGS,
    DRAIN_ASSERT_MSGS,
    RESOURCE_LIMIT_TEST_NAMES,
    RESOURCE_LIMIT_LOG_MSGS,
    RESOURCE_LIMIT_ASSERT_MSGS,
)

__all__ = [
    "TEST_NAMES",
    "TEST_LOG_MSGS",
    "TEST_ASSERT_MSGS",
    "LDAP_TEST_NAMES",
    "LDAP_LOG_MSGS",
    "LDAP_ASSERT_MSGS",
    "QUEUEING_TEST_NAMES",
    "QUEUEING_LOG_MSGS",
    "PAM_TEST_NAMES",
    "PAM_LOG_MSGS",
    "PAM_ASSERT_MSGS",
    "STABILITY_TEST_NAMES",
    "STABILITY_LOG_MSGS",
    "STABILITY_ASSERT_MSGS",
    "DRAIN_TEST_NAMES",
    "DRAIN_LOG_MSGS",
    "DRAIN_ASSERT_MSGS",
    "RESOURCE_LIMIT_TEST_NAMES",
    "RESOURCE_LIMIT_LOG_MSGS",
    "RESOURCE_LIMIT_ASSERT_MSGS",
]
