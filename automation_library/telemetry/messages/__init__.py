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

"""Telemetry messages module."""

# Kafka-specific messages
from .kafka_msgs import (
    KAFKA_TEST_NAMES,
    KAFKA_LOG_MSGS,
    KAFKA_ASSERT_MSGS,
)

# iDRAC telemetry-specific messages
from .idrac_telemetry_msgs import (
    IDRAC_TEST_NAMES,
    IDRAC_LOG_MSGS,
    IDRAC_ASSERT_MSGS,
)

# VictoriaMetrics-specific messages
from .victoria_msgs import (
    VICTORIA_TEST_NAMES,
    VICTORIA_LOG_MSGS,
    VICTORIA_ASSERT_MSGS,
)

# Delete node verification messages
from .delete_node_msgs import (
    DELETE_NODE_TEST_NAMES,
    DELETE_NODE_LOG_MSGS,
    DELETE_NODE_ASSERT_MSGS,
)

# VictoriaLogs-specific messages
from .victoria_logs_msgs import (
    VICTORIA_LOGS_TEST_NAMES,
    VICTORIA_LOGS_LOG_MSGS,
    VICTORIA_LOGS_ASSERT_MSGS,
)

# PowerScale-specific messages
from .powerscale_msgs import (
    POWERSCALE_TEST_NAMES,
    POWERSCALE_LOG_MSGS,
    POWERSCALE_ASSERT_MSGS,
)

# VAST telemetry-specific messages
from .vast_telemetry_msgs import (
    VAST_TEST_NAMES,
    VAST_LOG_MSGS,
    VAST_ASSERT_MSGS,
)

# Shared messages (used across all telemetry modules)
from .shared_msgs import (
    TELEMETRY_MSGS,
    TEST_NAMES,
    TEST_LOG_MSGS,
    TEST_ASSERT_MSGS,
    SHARED_TEST_NAMES,
    SHARED_LOG_MSGS,
    SHARED_ASSERT_MSGS,
)
