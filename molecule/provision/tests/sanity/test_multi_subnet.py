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
Provision Multi-Subnet Test Cases.

Post-provision verification for multi-subnet (multi-RAC) deployments.
These tests verify that nodes across additional subnets are reachable
and functional after provisioning.

Test cases:
1. Verify cross-subnet SSH reachability
   - SSHs to one representative node per additional subnet
   - Confirms multi-subnet routing/DHCP relay is working end-to-end
"""

import pytest

from automation_library.core import TestLogger
from automation_library.prepare_oim.functions.multi_subnet_func import (
    has_additional_subnets,
    get_additional_subnets,
    verify_cross_subnet_ssh,
)
from automation_library.provision.messages import (
    MS_TEST_NAMES,
    MS_TEST_LOG_MSGS as LOG_MSGS,
    MS_TEST_ASSERT_MSGS as ASSERT_MSGS,
    MS_SKIP_MSGS as SKIP_MSGS,
)


# =============================================================================
# 1. CROSS-SUBNET SSH REACHABILITY
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(20)
def test_cross_subnet_ssh(host):
    """
    Test Case 1: Verify SSH reachability across additional subnets.

    For each additional subnet, picks one representative node from the PXE
    mapping and SSHs to it from the omnia_core container. Confirms that
    multi-subnet routing/DHCP relay is working end-to-end after provision.

    Skips if no additional_subnets are configured.
    """
    log = TestLogger(MS_TEST_NAMES["cross_subnet_ssh"])

    if not has_additional_subnets(host):
        log.skipped(SKIP_MSGS["no_additional_subnets"])
        pytest.skip(SKIP_MSGS["no_additional_subnets"])

    subnets = get_additional_subnets(host)
    log.check(
        f"Testing SSH to one node per additional subnet "
        f"({len(subnets)} subnet(s))"
    )

    result = verify_cross_subnet_ssh(host)

    details_lines = []
    for sr in result.get("subnet_results", []):
        icon = "\u2713" if sr["ssh_success"] else "\u2717"
        if sr.get("test_node"):
            details_lines.append(
                f"{icon} {sr['subnet']} \u2014 "
                f"{sr['test_node']} ({sr['test_ip']}): "
                f"{sr['output']}"
            )
        else:
            details_lines.append(
                f"{icon} {sr['subnet']} \u2014 {sr['output']}"
            )

    details = "\n".join(details_lines)

    if result["success"]:
        log.passed(
            LOG_MSGS["cross_subnet_ssh_ok"].format(
                count=len(result.get("subnet_results", []))
            ),
            details,
        )
    else:
        log.failed(LOG_MSGS["cross_subnet_ssh_failed"], details)
        assert False, ASSERT_MSGS["cross_subnet_ssh_failed"].format(
            details=details
        )
