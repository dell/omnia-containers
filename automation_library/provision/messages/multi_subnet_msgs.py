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
Provision - Multi-Subnet Messages.

Test names, log messages, assertion messages, and skip messages
for multi-subnet cross-subnet SSH verification tests.
"""

from typing import Dict


# =============================================================================
# TEST NAMES — displayed in reports and TestLogger
# =============================================================================
MS_TEST_NAMES: Dict[str, str] = {
    "cross_subnet_ssh": (
        "Verify SSH reachability across additional subnets"
    ),
}

# =============================================================================
# LOG MESSAGES — for TestLogger during test execution
# =============================================================================
MS_TEST_LOG_MSGS: Dict[str, str] = {
    "cross_subnet_ssh_ok": (
        "SSH reachable across all {count} additional subnet(s)"
    ),
    "cross_subnet_ssh_failed": (
        "SSH failed for one or more additional subnets"
    ),
}

# =============================================================================
# ASSERTION MESSAGES — shown when tests fail (include HOW TO FIX)
# =============================================================================
MS_TEST_ASSERT_MSGS: Dict[str, str] = {
    "cross_subnet_ssh_failed": (
        "SSH failed to one or more additional subnets.\n"
        "{details}\n\n"
        "HOW TO FIX:\n"
        "  1. Verify network routing between OIM and additional subnets\n"
        "  2. Check DHCP relay (giaddr) configuration on switches\n"
        "  3. Ensure nodes booted and received IP via CoreDHCP\n"
        "  4. Test manually: ssh root@<node_ip> from omnia_core container"
    ),
}

# =============================================================================
# SKIP MESSAGES — for pytest.skip() calls
# =============================================================================
MS_SKIP_MSGS: Dict[str, str] = {
    "no_additional_subnets": (
        "No additional_subnets configured in network_spec.yml "
        "(single-subnet deployment)"
    ),
}
