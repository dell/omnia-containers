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
Additional Cloud-Init Module - Variable Exports.

Re-exports variables from sub-files for external use.
"""

from .common_vars import (
    ADDITIONAL_CLOUD_INIT_CONFIG_PATH,
    ADDITIONAL_CLOUD_INIT_RETRY_COUNT,
    ADDITIONAL_CLOUD_INIT_RETRY_INTERVAL,
    PROHIBITED_CLOUD_INIT_KEYS,
    ALLOWED_CLOUD_INIT_KEYS,
    SMD_GROUP_PREFIX,
    COMMON_SMD_GROUP_NAME,
    BSS_CLOUD_INIT_TIMEOUT,
    BSS_CLOUD_INIT_RETRY_COUNT,
    CLOUD_INIT_TEMPLATE_NAME,
    MERGE_HOW_STRATEGY,
    DEFAULT_FILE_PERMISSIONS,
    COMMON_LOG_LOCATIONS,
    CLOUD_INIT_STATUS_CMD,
    CLOUD_INIT_STATUS_SUCCESS,
)
