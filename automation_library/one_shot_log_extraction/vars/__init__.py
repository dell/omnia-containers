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

"""One-shot log extraction vars package."""

from .one_shot_log_extraction_vars import (
    LOG_COLLECTION_COMMAND,
    LOG_COLLECTION_CURATED_MODE,
    COLLECT_PLAYBOOK_PATH,
    BUNDLE_NAME_PATTERN,
    BUNDLE_NAME_FORMAT,
    OUTPUT_PATHS,
    METADATA_REQUIRED_FIELDS,
    WARNING_ENTRY_FIELDS,
    LOG_SOURCES,
    COLLECTION_MODES,
    TEST_FILES,
    SHA256_CONFIG,
    TIMEOUTS,
    EXIT_CODES,
    WARNING_PATTERNS,
    UNREACHABLE_NODE_MSG_FORMAT,
    CMD_TEMPLATES,
    TEST_CONFIG,
)

__all__ = [
    "LOG_COLLECTION_COMMAND",
    "LOG_COLLECTION_CURATED_MODE",
    "COLLECT_PLAYBOOK_PATH",
    "BUNDLE_NAME_PATTERN",
    "BUNDLE_NAME_FORMAT",
    "OUTPUT_PATHS",
    "METADATA_REQUIRED_FIELDS",
    "WARNING_ENTRY_FIELDS",
    "LOG_SOURCES",
    "COLLECTION_MODES",
    "TEST_FILES",
    "SHA256_CONFIG",
    "TIMEOUTS",
    "EXIT_CODES",
    "WARNING_PATTERNS",
    "UNREACHABLE_NODE_MSG_FORMAT",
    "CMD_TEMPLATES",
    "TEST_CONFIG",
]
