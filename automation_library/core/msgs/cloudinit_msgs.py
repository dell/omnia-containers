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
Core Cloud-Init Messages.

User-facing messages for cloud-init status verification.
"""

# =============================================================================
# TEST NAMES
# =============================================================================

CLOUDINIT_TEST_NAMES = {
    "cloudinit_status": "Verify cloud-init completed on all nodes",
}

# =============================================================================
# LOG MESSAGES
# =============================================================================

CLOUDINIT_LOG_MSGS = {
    "checking_status": "Checking cloud-init status on {count} nodes",
    "status_done": "Cloud-init completed on {hostname}",
    "status_running": "Cloud-init still running on {hostname}",
    "status_error": "Cloud-init error on {hostname}",
    "all_done": "Cloud-init completed on all {count} nodes",
    "some_failed": "Cloud-init failed on {failed} of {total} nodes",
}

# =============================================================================
# ASSERT MESSAGES
# =============================================================================

CLOUDINIT_ASSERT_MSGS = {
    "status_failed": "Cloud-init failed on {hostname}: {status}",
    "nodes_failed": "Cloud-init failed on {count} nodes: {nodes}",
}
