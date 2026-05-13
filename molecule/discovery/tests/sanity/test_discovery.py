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
Discovery Verification Test Cases.

Test cases for verifying discovery playbook output:
1. BMC PXE mapping file created with timestamp
2. PXE mapping file has all required columns
3. All functional groups are Omnia-supported
4. ADMIN_IP and IB_IP correlation with BMC_IP based on network_spec.yml
5. PARENT_SERVICE_TAG rules for slurm_node groups
6. OME static groups match PXE mapping functional groups
"""

import pytest
from automation_library.core import TestLogger, load_input_file
from automation_library.core.vars import DISCOVERY_CONFIG_FILE
from automation_library.discovery.functions import (
    get_latest_bmc_pxe_mapping_file,
    read_bmc_pxe_mapping_raw,
    verify_pxe_mapping_columns,
    verify_functional_groups_supported,
    verify_ip_correlation,
    verify_parent_service_tag,
    get_pxe_mapping_bmc_ips_by_group,
    get_ome_session,
    get_ome_static_groups,
    get_ome_group_device_ips,
    clear_ome_cache,
)
from automation_library.discovery.vars import (
    BMC_PXE_MAPPING_PATH,
    SUPPORTED_COLUMNS,
    SUPPORTED_FUNCTIONAL_GROUPS,
)
from automation_library.discovery.messages import (
    TEST_NAMES,
    TEST_LOG_MSGS as LOG_MSGS,
    TEST_ASSERT_MSGS as ASSERT_MSGS,
    SKIP_MSGS,
)


# =============================================================================
# TEST 1: BMC PXE MAPPING FILE CREATED WITH TIMESTAMP
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(1)
def test_bmc_pxe_mapping_created(host):
    """
    Test Case 1: Verify BMC PXE mapping file created with timestamp.

    Discovery playbook creates bmc_pxe_mapping_file_<timestamp>.csv
    """
    log = TestLogger(TEST_NAMES["bmc_pxe_mapping_created"])

    log.check("Checking for BMC PXE mapping file with timestamp")

    result = get_latest_bmc_pxe_mapping_file(host)

    if not result["success"]:
        log.failed(LOG_MSGS["bmc_pxe_mapping_not_found"], result["error"])
        assert False, ASSERT_MSGS["bmc_pxe_mapping_not_created"].format(
            path=BMC_PXE_MAPPING_PATH
        )

    log.check(LOG_MSGS["bmc_pxe_mapping_found"].format(
        filename=result["filename"],
        timestamp=result["timestamp"]
    ))

    mapping = read_bmc_pxe_mapping_raw(host, result["filepath"])
    if mapping["success"]:
        log.check(LOG_MSGS["bmc_pxe_mapping_rows"].format(count=len(mapping["rows"])))

    log.passed(
        f"BMC PXE mapping file found: {result['filename']}",
        f"Timestamp: {result['timestamp']}"
    )


# =============================================================================
# TEST 2: PXE MAPPING FILE HAS REQUIRED COLUMNS
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(2)
def test_pxe_mapping_columns(host):
    """
    Test Case 2: Verify PXE mapping file has all required columns.
    """
    log = TestLogger(TEST_NAMES["pxe_mapping_columns"])

    log.check(f"Verifying {len(SUPPORTED_COLUMNS)} required columns")

    result = verify_pxe_mapping_columns(host)

    if not result["success"]:
        if "No BMC PXE mapping" in result.get("error", ""):
            log.skipped(SKIP_MSGS["no_bmc_pxe_mapping"], result["error"])
            pytest.skip(SKIP_MSGS["no_bmc_pxe_mapping"])

        log.check(LOG_MSGS["columns_missing"].format(columns=", ".join(result["missing_columns"])))
        log.failed("Missing required columns", result["error"])
        assert False, ASSERT_MSGS["columns_missing"].format(
            missing=", ".join(result["missing_columns"]),
            present=", ".join(result["present_columns"])
        )

    log.check(LOG_MSGS["columns_valid"].format(count=len(result["present_columns"])))
    log.passed(result["details"], f"Columns: {', '.join(result['present_columns'][:5])}...")


# =============================================================================
# TEST 3: ALL FUNCTIONAL GROUPS ARE OMNIA-SUPPORTED
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(3)
def test_functional_groups_supported(host):
    """
    Test Case 3: Verify all functional groups in PXE mapping are Omnia-supported.
    """
    log = TestLogger(TEST_NAMES["functional_groups_supported"])

    log.check(f"Verifying functional groups against {len(SUPPORTED_FUNCTIONAL_GROUPS)} supported groups")

    result = verify_functional_groups_supported(host)

    if not result["success"]:
        if "No BMC PXE mapping" in result.get("error", ""):
            log.skipped(SKIP_MSGS["no_bmc_pxe_mapping"], result["error"])
            pytest.skip(SKIP_MSGS["no_bmc_pxe_mapping"])

        log.check(LOG_MSGS["groups_found"].format(groups=", ".join(result["supported_groups"])))
        log.check(LOG_MSGS["groups_unsupported"].format(groups=", ".join(result["unsupported_groups"])))
        log.failed("Unsupported functional groups found", result["error"])
        assert False, ASSERT_MSGS["unsupported_functional_groups"].format(
            unsupported=", ".join(result["unsupported_groups"]),
            supported=", ".join(SUPPORTED_FUNCTIONAL_GROUPS[:5]) + "..."
        )

    log.check(LOG_MSGS["groups_found"].format(groups=", ".join(result["supported_groups"])))
    log.passed(result["details"], f"Groups: {', '.join(result['supported_groups'])}")


# =============================================================================
# TEST 4: IP CORRELATION (ADMIN_IP/IB_IP <-> BMC_IP)
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(4)
def test_ip_correlation(host):
    """
    Test Case 4: Verify IP correlation based on network_spec.yml.

    IP correlation logic:
    - ADMIN_IP = admin_subnet[0:2] + bmc_ip[2:4]
    - IB_IP = ib_subnet[0:2] + bmc_ip[2:4]
    """
    log = TestLogger(TEST_NAMES["ip_correlation"])

    log.check("Verifying IP correlation based on network_spec.yml subnets")

    result = verify_ip_correlation(host)

    if not result["success"]:
        if "No BMC PXE mapping" in result.get("error", ""):
            log.skipped(SKIP_MSGS["no_bmc_pxe_mapping"], result["error"])
            pytest.skip(SKIP_MSGS["no_bmc_pxe_mapping"])

        log.check(LOG_MSGS["ip_correlation_invalid"].format(count=len(result["invalid_rows"])))

        for row in result["invalid_rows"][:3]:
            log.check(f"  - {row['hostname']}: {row.get('reason', 'Unknown')}")

        log.failed("IP correlation validation failed", result["error"])

        example = result["invalid_rows"][0] if result["invalid_rows"] else {}
        assert False, ASSERT_MSGS["ip_correlation_failed"].format(
            count=len(result["invalid_rows"]),
            example=f"{example.get('hostname', 'N/A')}: {example.get('reason', 'N/A')}"
        )

    log.check(LOG_MSGS["ip_correlation_valid"].format(count=result["valid_count"]))
    log.passed(result["details"], f"Validated {result['valid_count']} rows")


# =============================================================================
# TEST 5: PARENT_SERVICE_TAG RULES
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(5)
def test_parent_service_tag(host):
    """
    Test Case 5: Verify PARENT_SERVICE_TAG rules.

    Rules:
    1. Only slurm_node groups should have PARENT_SERVICE_TAG populated
    2. PARENT_SERVICE_TAG should reference a service_kube_node's SERVICE_TAG
    3. Other functional groups should have empty PARENT_SERVICE_TAG
    """
    log = TestLogger(TEST_NAMES["parent_service_tag"])

    log.check("Verifying PARENT_SERVICE_TAG rules")

    result = verify_parent_service_tag(host)

    if not result["success"]:
        if "No BMC PXE mapping" in result.get("error", ""):
            log.skipped(SKIP_MSGS["no_bmc_pxe_mapping"], result["error"])
            pytest.skip(SKIP_MSGS["no_bmc_pxe_mapping"])

        log.check(LOG_MSGS["parent_tag_invalid"].format(count=len(result["invalid_rows"])))

        for row in result["invalid_rows"][:3]:
            log.check(f"  - {row['hostname']} ({row['functional_group']}): {row['reason']}")

        log.failed("PARENT_SERVICE_TAG validation failed", result["error"])

        example = result["invalid_rows"][0] if result["invalid_rows"] else {}
        assert False, ASSERT_MSGS["parent_service_tag_failed"].format(
            count=len(result["invalid_rows"]),
            example=f"{example.get('hostname', 'N/A')}: {example.get('reason', 'N/A')}"
        )

    log.check(LOG_MSGS["parent_tag_valid"].format(count=result["valid_count"]))
    log.passed(result["details"], f"Validated {result['valid_count']} rows")


# =============================================================================
# TEST 6: OME STATIC GROUPS MATCH PXE MAPPING
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(6)
def test_ome_static_groups_match(host):
    """
    Test Case 6: Verify OME static groups match PXE mapping.

    For each functional group in PXE mapping:
    1. Find corresponding static group in OME (under Custom Groups > Static Groups)
    2. Get device BMC IPs from OME group
    3. Compare with BMC IPs from PXE mapping
    """
    log = TestLogger(TEST_NAMES["ome_functional_groups"])

    # Check if BMC discovery is enabled using load_input_file
    config = load_input_file(host, DISCOVERY_CONFIG_FILE)
    if not config:
        log.skipped("Discovery config not found", "")
        pytest.skip("Discovery config not found")

    if not config.get("enable_bmc_discovery", False):
        log.skipped(SKIP_MSGS["bmc_discovery_disabled"], "OME verification skipped")
        pytest.skip(SKIP_MSGS["bmc_discovery_disabled"])

    ome_ip = config.get("ome_ip", "")
    if not ome_ip:
        log.skipped("OME IP not configured", "")
        pytest.skip("OME IP not configured")

    # Clear cache for fresh session
    clear_ome_cache()

    log.check(LOG_MSGS["ome_connecting"].format(ip=ome_ip))

    # Get OME session
    session = get_ome_session(host)
    if not session["success"]:
        log.failed(LOG_MSGS["ome_connection_failed"].format(error=session["error"]), session["error"])
        assert False, ASSERT_MSGS["ome_connection_failed"].format(
            ip=ome_ip,
            error=session["error"]
        )

    log.check(LOG_MSGS["ome_connected"])

    # Get OME static groups (under Custom Groups > Static Groups)
    ome_groups = get_ome_static_groups(host)
    if not ome_groups["success"]:
        log.failed("Failed to get OME static groups", ome_groups["error"])
        pytest.skip(f"OME groups error: {ome_groups['error']}")

    log.check(LOG_MSGS["ome_groups_found"].format(count=len(ome_groups["groups"])))
    ome_group_map = {g["name"]: g for g in ome_groups["groups"]}

    # Get functional groups from PXE mapping
    fg_result = verify_functional_groups_supported(host)
    if not fg_result["success"] and not fg_result["supported_groups"]:
        log.skipped("No functional groups in PXE mapping", "")
        pytest.skip("No functional groups in PXE mapping")

    pxe_groups = fg_result["supported_groups"]
    log.check(f"PXE mapping functional groups: {', '.join(pxe_groups)}")

    verified = []
    failed = []
    missing = []

    for fg_name in pxe_groups:
        if fg_name not in ome_group_map:
            missing.append(fg_name)
            log.check(LOG_MSGS["ome_group_not_found"].format(name=fg_name))
            continue

        ome_group = ome_group_map[fg_name]
        log.check(LOG_MSGS["ome_group_checking"].format(name=fg_name))

        # Get BMC IPs from PXE mapping
        pxe_ips_result = get_pxe_mapping_bmc_ips_by_group(host, fg_name)
        if not pxe_ips_result["success"]:
            failed.append({"name": fg_name, "error": pxe_ips_result["error"]})
            continue

        pxe_ips = set(pxe_ips_result["ips"])

        # Get BMC IPs from OME group
        ome_ips_result = get_ome_group_device_ips(host, ome_group["id"])
        if not ome_ips_result["success"]:
            failed.append({"name": fg_name, "error": ome_ips_result["error"]})
            continue

        ome_ips = set(ome_ips_result["ips"])

        # Compare
        missing_in_ome = pxe_ips - ome_ips
        extra_in_ome = ome_ips - pxe_ips

        if missing_in_ome or extra_in_ome:
            failed.append({
                "name": fg_name,
                "pxe_ips": sorted(list(pxe_ips)),
                "ome_ips": sorted(list(ome_ips)),
                "missing_in_ome": sorted(list(missing_in_ome)),
                "extra_in_ome": sorted(list(extra_in_ome)),
            })
            log.check(LOG_MSGS["ome_group_mismatch"].format(
                name=fg_name,
                pxe_count=len(pxe_ips),
                ome_count=len(ome_ips)
            ))
        else:
            verified.append(fg_name)
            log.check(LOG_MSGS["ome_group_match"].format(
                name=fg_name,
                matched=len(pxe_ips),
                total=len(pxe_ips)
            ))

    # Report results
    if verified:
        log.check(f"✓ Verified groups: {', '.join(verified)}")

    if missing:
        log.check(f"✗ Missing in OME: {', '.join(missing)}")

    if failed:
        for fg in failed:
            if "missing_in_ome" in fg:
                log.check(f"✗ {fg['name']}: {len(fg.get('missing_in_ome', []))} IPs missing in OME")

    if not failed and not missing:
        log.passed(
            LOG_MSGS["all_groups_verified"].format(count=len(verified)),
            f"Groups: {', '.join(verified)}"
        )
    else:
        total = len(verified) + len(failed) + len(missing)
        fail_count = len(failed) + len(missing)
        log.failed(
            LOG_MSGS["groups_verification_failed"].format(failed=fail_count, total=total),
            f"Failed: {fail_count}, Verified: {len(verified)}"
        )

        if missing:
            available = list(ome_group_map.keys())
            assert False, ASSERT_MSGS["ome_group_not_found"].format(
                name=missing[0],
                available=", ".join(available[:10])
            )

        if failed:
            fg = failed[0]
            assert False, ASSERT_MSGS["ome_group_ip_mismatch"].format(
                name=fg["name"],
                pxe_ips=", ".join(fg.get("pxe_ips", [])[:5]),
                ome_ips=", ".join(fg.get("ome_ips", [])[:5]),
                missing=", ".join(fg.get("missing_in_ome", [])[:5]),
                extra=", ".join(fg.get("extra_in_ome", [])[:5])
            )
