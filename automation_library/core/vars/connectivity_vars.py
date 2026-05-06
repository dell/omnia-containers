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
Core Connectivity Variables.

Configuration for ping and SSH connectivity checks with retry logic.
"""

# =============================================================================
# PING RETRY CONFIGURATION (20 minutes total)
# =============================================================================

PING_RETRY_LIMIT = 240  # 240 retries * 5s = 20 minutes
PING_RETRY_INTERVAL = 5  # 5 seconds between retries

# =============================================================================
# SSH RETRY CONFIGURATION (5 minutes total)
# =============================================================================

SSH_RETRY_LIMIT = 60  # 60 retries * 5s = 5 minutes
SSH_RETRY_INTERVAL = 5  # 5 seconds between retries

# =============================================================================
# PARALLEL CONNECTIVITY CONFIGURATION
# =============================================================================

MAX_PARALLEL_WORKERS = 6  # Maximum parallel threads for connectivity checks
CONNECTIVITY_PROGRESS_INTERVAL = 5  # Print progress every 5 seconds

# =============================================================================
# CONNECTIVITY COMMANDS
# =============================================================================

CMD_PING_NODE = "ping -c 1 -W 2 {target_ip}"

CMD_SSH_CHECK = (
    "ssh -o StrictHostKeyChecking=no -o ConnectTimeout=5 -o BatchMode=yes "
    "root@{target_ip} 'echo ok' 2>&1"
)
