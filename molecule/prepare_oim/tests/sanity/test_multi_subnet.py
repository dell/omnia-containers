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
Prepare OIM Multi-Subnet Test Cases.

Test cases for verifying multi-subnet (multi-RAC) CoreDHCP configuration
after prepare_oim execution.

Test cases:
 9. Activate multi-subnet CoreDHCP configuration (6-step process)
    - Pull coresmd v0.6.3 image
    - Comment out single-subnet coresmd/bootloop lines
    - Uncomment multi-subnet coresmd/bootloop blocks
    - Update coresmd image in quadlet container files
    - systemctl daemon-reload
    - systemctl restart openchami.target
10. Verify CoreDHCP configuration mode matches network_spec.yml
    - If additional_subnets configured: verify multi-subnet mode (key=value)
    - If no additional_subnets: verify single-subnet mode (positional)
11. Verify all additional_subnet entries present in coredhcp.yaml
    - Each subnet has coresmd rule=subnet:CIDR,type:Node directives
    - Each subnet has coresmd rule=subnet:CIDR,type:NodeBMC directives
    - Each subnet has bootloop subnet_pool=CIDR,start,end directives
12. Verify running coresmd containers use multi-subnet image
    - Inspects actual running container image (not just quadlet file)
    - Confirms activation restart was effective
"""

import pytest

from automation_library.core import TestLogger
from automation_library.prepare_oim.functions import (
    has_additional_subnets,
    get_additional_subnets,
    check_coredhcp_file_exists,
    check_coredhcp_multisubnet_mode,
    verify_subnet_entries_in_coredhcp,
    activate_multisubnet_coredhcp,
    verify_coresmd_running_image,
)
from automation_library.prepare_oim.vars import (
    COREDHCP_CONFIG_PATH,
    CORESMD_MULTISUBNET_IMAGE,
)
from automation_library.prepare_oim.messages import (
    MS_TEST_NAMES,
    MS_TEST_LOG_MSGS as LOG_MSGS,
    MS_TEST_ASSERT_MSGS as ASSERT_MSGS,
    MS_SKIP_MSGS as SKIP_MSGS,
)


# =============================================================================
# 9. ACTIVATE MULTI-SUBNET COREDHCP CONFIGURATION
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(9)
def test_activate_multi_subnet(host):
    """
    Test Case 9: Activate multi-subnet CoreDHCP configuration (6-step process).

    Runs BEFORE the verification tests. Performs:
      1. podman pull ghcr.io/openchami/coresmd:v0.6.3
      2. Comment out single-subnet coresmd and bootloop lines
      3. Uncomment multi-subnet coresmd and bootloop blocks
      4. Update coresmd image in quadlet container files
      5. systemctl daemon-reload
      6. systemctl restart openchami.target

    Idempotent — skips if already in multi-subnet mode.
    Skips if no additional_subnets are configured.
    """
    log = TestLogger(MS_TEST_NAMES["activate_multi_subnet"])

    if not has_additional_subnets(host):
        log.skipped(SKIP_MSGS["no_additional_subnets"])
        pytest.skip(SKIP_MSGS["no_additional_subnets"])

    subnets = get_additional_subnets(host)
    log.check(
        f"Found {len(subnets)} additional subnet(s) — "
        f"running 6-step multi-subnet activation"
    )

    result = activate_multisubnet_coredhcp(host)

    # Build step-by-step details
    details_lines = []
    for step in result.get("steps", []):
        icon = "\u2713" if step.get("success", True) else "\u2717"
        details_lines.append(
            f"  {icon} Step {step['step']}: {step['name']} — {step.get('detail', '')}"
        )
    details = "\n".join(details_lines)

    if result["success"]:
        if result["steps"] and result["steps"][0].get("step") == 0:
            log.passed(LOG_MSGS["activation_skipped_already_active"], details)
        else:
            log.passed(LOG_MSGS["activation_ok"], details)
    else:
        failed_step = ""
        for step in result.get("steps", []):
            if not step.get("success", True):
                failed_step = step.get("name", "")
                break
        log.failed(
            LOG_MSGS["activation_failed"].format(step=failed_step),
            details,
        )
        assert False, ASSERT_MSGS["activation_failed"].format(
            step_details=details
        )


# =============================================================================
# 10. MULTI-SUBNET COREDHCP CONFIGURATION TEST
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(10)
def test_multi_subnet_coredhcp_config(host):
    """
    Test Case 10: Verify CoreDHCP configuration mode matches network_spec.yml.

    Steps:
    1. Check if additional_subnets is configured in network_spec.yml
    2. Verify coredhcp.yaml exists on OIM host
    3. If additional_subnets present: verify multi-subnet mode (key=value)
       If no additional_subnets: verify single-subnet mode (positional)

    This test runs in BOTH modes — it does not skip for single-subnet.
    """
    log = TestLogger(MS_TEST_NAMES["multi_subnet_coredhcp_config"])

    multi_subnet = has_additional_subnets(host)

    # Step 1: Verify coredhcp.yaml exists on OIM host
    log.check(f"Checking coredhcp.yaml at {COREDHCP_CONFIG_PATH}")
    file_result = check_coredhcp_file_exists(host)

    if not file_result["success"]:
        log.failed(
            LOG_MSGS["coredhcp_file_missing"].format(path=COREDHCP_CONFIG_PATH),
            file_result["error"],
        )
        assert False, ASSERT_MSGS["coredhcp_file_missing"].format(
            path=COREDHCP_CONFIG_PATH
        )

    log.check(LOG_MSGS["coredhcp_file_exists"].format(path=COREDHCP_CONFIG_PATH))

    # Step 2: Check configuration mode
    log.check("Checking coredhcp.yaml configuration mode")
    mode_result = check_coredhcp_multisubnet_mode(host)

    if multi_subnet:
        # ── Multi-subnet path: expect key=value format ──
        subnets = get_additional_subnets(host)
        subnet_summary = ", ".join(
            f"{s.get('subnet', '')}/{s.get('netmask_bits', '')}"
            for s in subnets
        )
        log.check(
            f"Found {len(subnets)} additional subnet(s): {subnet_summary}"
        )

        details_lines = [
            f"Configuration mode: {mode_result['mode']}",
            f"Additional subnets configured: {len(subnets)}",
        ]
        if mode_result.get("details"):
            details_lines.append(mode_result["details"])
        details = "\n".join(details_lines)

        if mode_result["success"]:
            if mode_result["mode"] == "multi-subnet":
                log.passed(LOG_MSGS["coredhcp_multisubnet_active"], details)
            else:
                log.passed(LOG_MSGS["coredhcp_commented_mode"], details)
        else:
            log.failed(
                LOG_MSGS["coredhcp_singlesubnet_active"],
                details,
            )
            assert False, ASSERT_MSGS["coredhcp_not_multisubnet"]
    else:
        # ── Single-subnet path: expect positional format ──
        log.check("No additional_subnets configured — verifying single-subnet mode")

        details_lines = [
            f"Configuration mode: {mode_result['mode']}",
            "Additional subnets configured: 0",
        ]
        if mode_result.get("details"):
            details_lines.append(mode_result["details"])
        details = "\n".join(details_lines)

        if mode_result["mode"] == "single-subnet":
            log.passed(LOG_MSGS["coredhcp_singlesubnet_verified"], details)
        else:
            log.failed(
                LOG_MSGS["coredhcp_singlesubnet_unexpected_multi"],
                details,
            )
            assert False, ASSERT_MSGS["coredhcp_unexpected_multisubnet"]


# =============================================================================
# 11. SUBNET ENTRIES VERIFICATION TEST
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(11)
def test_multi_subnet_entries_in_coredhcp(host):
    """
    Test Case 11: Verify all additional_subnet entries present in coredhcp.yaml.

    For each subnet in network_spec.yml additional_subnets:
    - coresmd rule=subnet:CIDR,type:Node,routers:ROUTER,cidr:BITS
    - coresmd rule=subnet:CIDR,type:NodeBMC,routers:ROUTER,cidr:BITS
    - bootloop subnet_pool=CIDR,start_ip,end_ip

    Skips if no additional_subnets are configured.
    """
    log = TestLogger(MS_TEST_NAMES["multi_subnet_entries_in_coredhcp"])

    if not has_additional_subnets(host):
        log.skipped(SKIP_MSGS["no_additional_subnets"])
        pytest.skip(SKIP_MSGS["no_additional_subnets"])

    subnets = get_additional_subnets(host)
    log.check(f"Verifying {len(subnets)} subnet entries in coredhcp.yaml")

    result = verify_subnet_entries_in_coredhcp(host)

    # Build detailed output
    details_lines = [
        f"Total subnets: {result['total']}, "
        f"Missing: {result['missing_count']}"
    ]

    all_commented = True
    for sr in result.get("subnets", []):
        status = "✓" if sr["success"] else "✗"
        state_label = f" [{sr.get('state', 'unknown')}]" if sr["success"] else ""
        details_lines.append(
            f"\n{status} Subnet: {sr['subnet']} "
            f"(router: {sr['router']}){state_label}"
        )

        node_icon = "✓" if sr["node_rule_found"] else "✗"
        bmc_icon = "✓" if sr["bmc_rule_found"] else "✗"
        pool_icon = "✓" if sr["pool_found"] else "✗"

        details_lines.append(f"    {node_icon} Node rule: {sr['expected_node_rule']}")
        details_lines.append(f"    {bmc_icon} BMC rule:  {sr['expected_bmc_rule']}")
        details_lines.append(f"    {pool_icon} Pool:      {sr['expected_pool']}")

        if sr.get("state") != "commented":
            all_commented = False

    details = "\n".join(details_lines)

    if result["success"]:
        if all_commented:
            log.passed(
                LOG_MSGS["subnet_entries_commented"].format(
                    count=result["total"]
                ),
                details,
            )
        else:
            log.passed(
                LOG_MSGS["subnet_entries_ok"].format(count=result["total"]),
                details,
            )
    else:
        # Build missing details for assertion message
        missing_parts = []
        for sr in result.get("subnets", []):
            if not sr["success"]:
                missing_items = []
                if not sr["node_rule_found"]:
                    missing_items.append(f"Node rule ({sr['expected_node_rule']})")
                if not sr["bmc_rule_found"]:
                    missing_items.append(f"BMC rule ({sr['expected_bmc_rule']})")
                if not sr["pool_found"]:
                    missing_items.append(f"Pool ({sr['expected_pool']})")
                missing_parts.append(
                    f"  {sr['subnet']}: {', '.join(missing_items)}"
                )

        log.failed(
            LOG_MSGS["subnet_entries_missing"].format(
                missing=result["missing_count"],
                total=result["total"],
            ),
            details,
        )
        assert False, ASSERT_MSGS["subnet_entries_missing"].format(
            missing_details="\n".join(missing_parts)
        )


# =============================================================================
# 12. CORESMD RUNNING CONTAINER IMAGE VERIFICATION
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(12)
def test_coresmd_running_image(host):
    """
    Test Case 12: Verify running coresmd containers use multi-subnet image.

    Inspects the actual running coresmd-coredhcp and coresmd-coredns
    containers to confirm they are using the expected v0.6.3 image.
    This goes beyond the quadlet file check — it confirms the restart
    was effective.

    Skips if no additional_subnets are configured.
    """
    log = TestLogger(MS_TEST_NAMES["coresmd_running_image"])

    if not has_additional_subnets(host):
        log.skipped(SKIP_MSGS["no_additional_subnets"])
        pytest.skip(SKIP_MSGS["no_additional_subnets"])

    log.check(
        f"Verifying running containers use {CORESMD_MULTISUBNET_IMAGE}"
    )

    result = verify_coresmd_running_image(host)

    details_lines = []
    for cr in result.get("container_results", []):
        icon = "✓" if cr["match"] else "✗"
        if cr["running"]:
            details_lines.append(
                f"{icon} {cr['container']}: {cr['actual_image']}"
            )
        else:
            details_lines.append(
                f"{icon} {cr['container']}: NOT RUNNING — {cr['error']}"
            )

    details_lines.append(f"\nExpected: {CORESMD_MULTISUBNET_IMAGE}")
    details = "\n".join(details_lines)

    if result["success"]:
        log.passed(LOG_MSGS["coresmd_image_ok"], details)
    else:
        log.failed(LOG_MSGS["coresmd_image_mismatch"], details)
        assert False, ASSERT_MSGS["coresmd_image_mismatch"].format(
            details=details
        )
