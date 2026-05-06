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
Core Connectivity Messages.

User-facing messages for ping and SSH connectivity checks.
"""

# =============================================================================
# TEST NAMES
# =============================================================================

CONNECTIVITY_TEST_NAMES = {
    "node_connectivity": "Verify node connectivity (ping + SSH)",
    "ping_check": "Verify nodes are pingable",
    "ssh_check": "Verify SSH connectivity to nodes",
}

# =============================================================================
# LOG MESSAGES
# =============================================================================

CONNECTIVITY_LOG_MSGS = {
    "checking_ping": "Checking ping connectivity to {count} nodes",
    "checking_ssh": "Checking SSH connectivity to {count} nodes",
    "ping_success": "Node {hostname} is pingable",
    "ping_failed": "Node {hostname} is not pingable",
    "ssh_success": "SSH to {hostname} is working",
    "ssh_failed": "SSH to {hostname} failed",
    "all_nodes_reachable": "All {count} nodes are reachable",
    "some_nodes_unreachable": "{unreachable} of {total} nodes are unreachable",
    "waiting_ping": "Waiting for {hostname} to respond to ping ({elapsed}s/{timeout}s)",
    "waiting_ssh": "Waiting for SSH on {hostname} ({elapsed}s/{timeout}s)",
}

# =============================================================================
# ASSERT MESSAGES
# =============================================================================

CONNECTIVITY_ASSERT_MSGS = {
    "ping_failed": "Node {hostname} ({admin_ip}) is not pingable after {timeout}s",
    "ssh_failed": "SSH to {hostname} ({admin_ip}) failed after {timeout}s",
    "nodes_unreachable": "{count} nodes are unreachable: {nodes}",
}
