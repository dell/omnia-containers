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
Telemetry Automation - Shared Messages.

This module contains shared messages used across all telemetry modules
(iDRAC, Kafka, VictoriaMetrics).

For module-specific messages, see:
- idrac_telemetry_msgs.py - iDRAC telemetry specific
- kafka_msgs.py - Kafka and LDMS specific
- victoria_msgs.py - VictoriaMetrics specific
"""

from typing import Dict

from .kafka_msgs import KAFKA_TEST_NAMES, KAFKA_LOG_MSGS, KAFKA_ASSERT_MSGS
from .idrac_telemetry_msgs import IDRAC_TEST_NAMES, IDRAC_LOG_MSGS, IDRAC_ASSERT_MSGS


# =============================================================================
# SHARED TEST NAMES (currently empty - module-specific names in their own files)
# =============================================================================

SHARED_TEST_NAMES: Dict[str, str] = {}

# Combined TEST_NAMES for backward compatibility
TEST_NAMES: Dict[str, str] = {
    **SHARED_TEST_NAMES,
    **KAFKA_TEST_NAMES,
    **IDRAC_TEST_NAMES,
}


# =============================================================================
# SHARED LOG MESSAGES (only messages actually used)
# =============================================================================

SHARED_LOG_MSGS: Dict[str, str] = {
    # Config reading errors (used in shared_func.py)
    "telemetry_config_read_failed": "Failed to read telemetry_config.yml: {error}",
    "telemetry_config_parse_failed": "Failed to parse telemetry_config.yml: {error}",
    "software_config_read_failed": "Failed to read software_config.json: {error}",
    "software_config_parse_failed": "Failed to parse software_config.json: {error}",
}

# Combined TEST_LOG_MSGS for backward compatibility
TEST_LOG_MSGS: Dict[str, str] = {
    **SHARED_LOG_MSGS,
    **KAFKA_LOG_MSGS,
    **IDRAC_LOG_MSGS,
}


# =============================================================================
# SHARED ASSERTION MESSAGES (only messages actually used)
# =============================================================================

SHARED_ASSERT_MSGS: Dict[str, str] = {
    # Config reading errors (used in shared_func.py)
    "telemetry_config_read_failed": "Failed to read telemetry_config.yml: {error}",
    "telemetry_config_parse_failed": "Failed to parse telemetry_config.yml: {error}",
    "software_config_read_failed": "Failed to read software_config.json: {error}",
    "software_config_parse_failed": "Failed to parse software_config.json: {error}",
}

# Combined TEST_ASSERT_MSGS for backward compatibility
TEST_ASSERT_MSGS: Dict[str, str] = {
    **SHARED_ASSERT_MSGS,
    **KAFKA_ASSERT_MSGS,
    **IDRAC_ASSERT_MSGS,
}


# TELEMETRY_MSGS kept for backward compatibility (exported from telemetry/__init__.py)
TELEMETRY_MSGS: Dict[str, str] = {}
