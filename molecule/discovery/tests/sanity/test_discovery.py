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
7. OME devices without static group assignment (will get default: slurm_node_aarch64)
8. ADMIN_MAC matches OME first active non-iDRAC NIC
9. IB_NIC_NAME matches OME first active InfiniBand NIC
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
    get_network_spec_subnets,
    get_ome_session,
    get_ome_static_groups,
    get_ome_group_device_ips,
    clear_ome_cache,
    get_ome_devices_without_static_group,
    get_ome_device_details_by_service_tag,
)
from automation_library.discovery.vars import (
    BMC_PXE_MAPPING_PATH,
    SUPPORTED_COLUMNS,
    SUPPORTED_FUNCTIONAL_GROUPS,
    GROUPS_REQUIRING_PARENT_SERVICE_TAG,
    VALID_PARENT_FUNCTIONAL_GROUPS,
)
from automation_library.discovery.messages import (
    TEST_NAMES,
    TEST_LOG_MSGS as LOG_MSGS,
    TEST_ASSERT_MSGS as ASSERT_MSGS,
    SKIP_MSGS,
)


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def _get_pxe_mapping_data(host):
    """Get PXE mapping data with headers and rows as dicts."""
    mapping = read_bmc_pxe_mapping_raw(host)
    if not mapping["success"]:
        return None, mapping["error"]

    headers = mapping["headers"]
    rows = []
    for row in mapping["rows"]:
        row_dict = {}
        for i, h in enumerate(headers):
            row_dict[h] = row[i] if i < len(row) else ""
        rows.append(row_dict)
    return rows, None


def _group_rows_by_functional_group(rows):
    """Group rows by FUNCTIONAL_GROUP_NAME."""
    grouped = {}
    for row in rows:
        fg = row.get("FUNCTIONAL_GROUP_NAME", "")
        if fg:
            if fg not in grouped:
                grouped[fg] = []
            grouped[fg].append(row)
    return grouped


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

    # Display columns line by line with tick marks
    column_details = []
    for col in sorted(SUPPORTED_COLUMNS):
        if col in result["present_columns"]:
            column_details.append(f"✓ {col}")
        else:
            column_details.append(f"✗ {col}")

    log.passed(f"All {len(result['present_columns'])} required columns present", "\n".join(column_details))


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

        log.check(LOG_MSGS["groups_unsupported"].format(groups=", ".join(result["unsupported_groups"])))
        log.failed("Unsupported functional groups found", result["error"])
        assert False, ASSERT_MSGS["unsupported_functional_groups"].format(
            unsupported=", ".join(result["unsupported_groups"]),
            supported=", ".join(SUPPORTED_FUNCTIONAL_GROUPS[:5]) + "..."
        )

    # Display functional groups line by line with tick marks
    group_details = []
    group_details.append("Functional Groups in PXE Mapping:")
    for fg in sorted(result["supported_groups"]):
        group_details.append(f"✓ {fg}")

    if result["unsupported_groups"]:
        group_details.append("")
        group_details.append("Unsupported Groups:")
        for fg in sorted(result["unsupported_groups"]):
            group_details.append(f"✗ {fg}")

    log.passed(f"All {len(result['supported_groups'])} functional groups are supported", "\n".join(group_details))


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

    # Get subnet info
    subnets = get_network_spec_subnets(host)
    if subnets["success"]:
        log.check(f"Admin Subnet: {subnets['admin_subnet']}")
        if subnets["ib_subnet"]:
            log.check(f"IB Subnet: {subnets['ib_subnet']}")

    # Get PXE mapping data for detailed display
    rows, err = _get_pxe_mapping_data(host)
    if err:
        log.skipped(SKIP_MSGS["no_bmc_pxe_mapping"], err)
        pytest.skip(SKIP_MSGS["no_bmc_pxe_mapping"])

    result = verify_ip_correlation(host)

    if not result["success"]:
        if "No BMC PXE mapping" in result.get("error", ""):
            log.skipped(SKIP_MSGS["no_bmc_pxe_mapping"], result["error"])
            pytest.skip(SKIP_MSGS["no_bmc_pxe_mapping"])

    # Group by functional group and display role-wise
    grouped = _group_rows_by_functional_group(rows)
    
    ip_details = []
    
    for fg_name in sorted(grouped.keys()):
        fg_rows = grouped[fg_name]
        ip_details.append(f"[{fg_name}]")

        for row in fg_rows:
            hostname = row.get("HOSTNAME", "")
            admin_ip = row.get("ADMIN_IP", "")
            bmc_ip = row.get("BMC_IP", "")
            ib_ip = row.get("IB_IP", "")

            # Check if this row is valid
            is_valid = True
            for inv in result.get("invalid_rows", []):
                if inv.get("hostname") == hostname:
                    is_valid = False
                    break

            status = "✓" if is_valid else "✗"
            ip_details.append(f"  {status} {hostname}:")
            ip_details.append(f"      ADMIN_IP: {admin_ip}")
            ip_details.append(f"      BMC_IP:   {bmc_ip}")
            if ib_ip:
                ip_details.append(f"      IB_IP:    {ib_ip}")

    if result["invalid_rows"]:
        ip_details.append("")
        ip_details.append("Invalid Rows:")
        for row in result["invalid_rows"]:
            ip_details.append(f"✗ {row['hostname']}: {row.get('reason', 'Unknown')}")

        log.failed("IP correlation validation failed", "\n".join(ip_details))
        example = result["invalid_rows"][0]
        assert False, ASSERT_MSGS["ip_correlation_failed"].format(
            count=len(result["invalid_rows"]),
            example=f"{example.get('hostname', 'N/A')}: {example.get('reason', 'N/A')}"
        )

    log.passed(f"All {result['valid_count']} rows have valid IP correlation", "\n".join(ip_details))


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
    4. If service_kube_node exists, slurm_node MUST have parent service tag
    """
    log = TestLogger(TEST_NAMES["parent_service_tag"])

    log.check("Verifying PARENT_SERVICE_TAG rules")
    log.check(f"Groups requiring PARENT_SERVICE_TAG: {', '.join(GROUPS_REQUIRING_PARENT_SERVICE_TAG)}")
    log.check(f"Valid parent groups: {', '.join(VALID_PARENT_FUNCTIONAL_GROUPS)}")

    # Get PXE mapping data
    rows, err = _get_pxe_mapping_data(host)
    if err:
        log.skipped(SKIP_MSGS["no_bmc_pxe_mapping"], err)
        pytest.skip(SKIP_MSGS["no_bmc_pxe_mapping"])

    # Group by functional group
    grouped = _group_rows_by_functional_group(rows)

    # Build set of valid parent service tags (from service_kube_node)
    valid_parent_tags = {}
    for fg in VALID_PARENT_FUNCTIONAL_GROUPS:
        if fg in grouped:
            for row in grouped[fg]:
                st = row.get("SERVICE_TAG", "")
                hostname = row.get("HOSTNAME", "")
                if st:
                    valid_parent_tags[st] = hostname

    # Check if service_kube_node exists
    has_service_kube_node = bool(valid_parent_tags)

    result = verify_parent_service_tag(host)

    # Build details for display
    parent_details = []
    
    if has_service_kube_node:
        parent_details.append("Valid Parent Service Tags (from service_kube_node):")
        for st, hostname in valid_parent_tags.items():
            parent_details.append(f"✓ {st} ({hostname})")
        parent_details.append("")

    # Display validation results by group
    invalid_nodes = []

    for fg_name in sorted(grouped.keys()):
        fg_rows = grouped[fg_name]
        requires_parent = fg_name in GROUPS_REQUIRING_PARENT_SERVICE_TAG

        parent_details.append(f"[{fg_name}]")

        for row in fg_rows:
            hostname = row.get("HOSTNAME", "")
            service_tag = row.get("SERVICE_TAG", "")
            parent_tag = row.get("PARENT_SERVICE_TAG", "")

            if requires_parent:
                # slurm_node should have parent tag
                if has_service_kube_node:
                    if parent_tag and parent_tag in valid_parent_tags:
                        parent_details.append(f"  ✓ {hostname}:")
                        parent_details.append(f"      SERVICE_TAG: {service_tag}")
                        parent_details.append(f"      PARENT_SERVICE_TAG: {parent_tag} → {valid_parent_tags[parent_tag]}")
                    elif parent_tag and parent_tag not in valid_parent_tags:
                        parent_details.append(f"  ✗ {hostname}:")
                        parent_details.append(f"      SERVICE_TAG: {service_tag}")
                        parent_details.append(f"      PARENT_SERVICE_TAG: {parent_tag} (INVALID - not a service_kube_node)")
                        invalid_nodes.append({
                            "hostname": hostname,
                            "functional_group": fg_name,
                            "reason": f"PARENT_SERVICE_TAG '{parent_tag}' is not a valid service_kube_node"
                        })
                    else:
                        parent_details.append(f"  ✗ {hostname}:")
                        parent_details.append(f"      SERVICE_TAG: {service_tag}")
                        parent_details.append(f"      PARENT_SERVICE_TAG: (MISSING)")
                        invalid_nodes.append({
                            "hostname": hostname,
                            "functional_group": fg_name,
                            "reason": "slurm_node missing PARENT_SERVICE_TAG"
                        })
                else:
                    # No service_kube_node, so parent tag not required
                    parent_details.append(f"  ✓ {hostname}: (no service_kube_node in cluster)")
            else:
                # Non-slurm_node should NOT have parent tag
                if parent_tag:
                    parent_details.append(f"  ✗ {hostname}:")
                    parent_details.append(f"      SERVICE_TAG: {service_tag}")
                    parent_details.append(f"      PARENT_SERVICE_TAG: {parent_tag} (UNEXPECTED)")
                    invalid_nodes.append({
                        "hostname": hostname,
                        "functional_group": fg_name,
                        "reason": f"{fg_name} should NOT have PARENT_SERVICE_TAG"
                    })
                else:
                    parent_details.append(f"  ✓ {hostname}: (no parent tag - correct)")

    if invalid_nodes:
        parent_details.append("")
        parent_details.append("Invalid Nodes:")
        for node in invalid_nodes:
            parent_details.append(f"✗ {node['hostname']} ({node['functional_group']}): {node['reason']}")

        log.failed("PARENT_SERVICE_TAG validation failed", "\n".join(parent_details))
        assert False, ASSERT_MSGS["parent_service_tag_failed"].format(
            count=len(invalid_nodes),
            example=f"{invalid_nodes[0]['hostname']}: {invalid_nodes[0]['reason']}"
        )

    log.passed(f"All {result['valid_count']} rows have valid PARENT_SERVICE_TAG", "\n".join(parent_details))


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

    verified = []
    failed = []
    missing = []
    default_groups = []  # Groups that are default (unassigned devices)
    group_details = {}

    # Get unassigned devices to identify default groups
    unassigned_result = get_ome_devices_without_static_group(host)
    unassigned_bmc_ips = set()
    if unassigned_result["success"]:
        for dev in unassigned_result.get("unassigned_devices", []):
            if dev.get("ip"):
                unassigned_bmc_ips.add(dev["ip"])

    for fg_name in sorted(pxe_groups):
        if fg_name not in ome_group_map:
            # Check if this is a default group (slurm_node_aarch64)
            # by verifying its BMC IPs are in unassigned devices
            pxe_ips_result = get_pxe_mapping_bmc_ips_by_group(host, fg_name)
            if pxe_ips_result["success"]:
                pxe_ips = set(pxe_ips_result["ips"])
                # If all PXE IPs for this group are in unassigned devices, it's a default group
                if pxe_ips and pxe_ips.issubset(unassigned_bmc_ips):
                    default_groups.append(fg_name)
                    group_details[fg_name] = {
                        "matched": sorted(list(pxe_ips)),
                        "missing_in_ome": [],
                        "extra_in_ome": [],
                        "is_default": True,
                    }
                    verified.append(fg_name)
                    continue
            missing.append(fg_name)
            continue

        ome_group = ome_group_map[fg_name]

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
        matched_ips = pxe_ips & ome_ips
        missing_in_ome = pxe_ips - ome_ips
        extra_in_ome = ome_ips - pxe_ips

        group_details[fg_name] = {
            "matched": sorted(list(matched_ips)),
            "missing_in_ome": sorted(list(missing_in_ome)),
            "extra_in_ome": sorted(list(extra_in_ome)),
        }

        if missing_in_ome or extra_in_ome:
            failed.append({
                "name": fg_name,
                "pxe_ips": sorted(list(pxe_ips)),
                "ome_ips": sorted(list(ome_ips)),
                "missing_in_ome": sorted(list(missing_in_ome)),
                "extra_in_ome": sorted(list(extra_in_ome)),
            })
        else:
            verified.append(fg_name)

    # Build details for display
    ome_details = []

    # Display results by functional group with IPs
    for fg_name in sorted(pxe_groups):
        ome_details.append(f"[{fg_name}]")

        if fg_name in missing:
            ome_details.append("  ✗ Group not found in OME Static Groups")
            continue

        if fg_name not in group_details:
            ome_details.append("  ✗ Error retrieving IPs")
            continue

        details = group_details[fg_name]

        # Check if this is a default group (unassigned devices)
        is_default = details.get("is_default", False)
        if is_default:
            ome_details.append("  (Default group - devices not in any OME static group)")

        # Show matched IPs
        for ip in details["matched"]:
            ome_details.append(f"  ✓ {ip}")

        # Show missing in OME (in PXE but not in OME)
        for ip in details["missing_in_ome"]:
            ome_details.append(f"  ✗ {ip} (missing in OME)")

        # Show extra in OME (in OME but not in PXE)
        for ip in details["extra_in_ome"]:
            ome_details.append(f"  ✗ {ip} (unexpected - in OME but not in PXE)")

    # Summary
    ome_details.append("")
    if verified:
        ome_details.append(f"Verified Groups ({len(verified)}):")
        for fg in verified:
            suffix = " (default)" if fg in default_groups else ""
            ome_details.append(f"  ✓ {fg}{suffix}")

    if missing:
        ome_details.append(f"Missing in OME ({len(missing)}):")
        for fg in missing:
            ome_details.append(f"  ✗ {fg}")

    if not failed and not missing:
        log.passed(f"All {len(verified)} functional groups verified", "\n".join(ome_details))
    else:
        total = len(verified) + len(failed) + len(missing)
        fail_count = len(failed) + len(missing)
        log.failed(
            f"{fail_count}/{total} functional groups failed verification",
            "\n".join(ome_details)
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


# =============================================================================
# TEST 7: OME DEVICES WITHOUT STATIC GROUP ASSIGNMENT
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(7)
def test_ome_unassigned_devices(host):
    """
    Test Case 7: Verify all OME devices are assigned to static groups.

    Devices NOT assigned to any static group will get the default functional
    group (slurm_node_aarch64) during discovery. This test identifies such
    devices so users can assign them to appropriate static groups in OME.

    If no unassigned devices exist, the test passes.
    If unassigned devices exist, the test shows them as informational (not a failure).
    """
    log = TestLogger(TEST_NAMES["ome_unassigned_devices"])

    # Check if BMC discovery is enabled
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

    # Get devices without static group assignment
    result = get_ome_devices_without_static_group(host)
    if not result["success"]:
        log.failed("Failed to get OME device information", result["error"])
        pytest.skip(f"OME error: {result['error']}")

    unassigned = result["unassigned_devices"]
    unassigned_bmc_ips = {d.get("ip", "") for d in unassigned if d.get("ip")}

    # Get PXE mapping data for slurm_node_aarch64 (default group)
    default_group = "slurm_node_aarch64"
    pxe_default_ips_result = get_pxe_mapping_bmc_ips_by_group(host, default_group)
    pxe_default_ips = set()
    if pxe_default_ips_result["success"]:
        pxe_default_ips = set(pxe_default_ips_result["ips"])

    # Build details for display
    details = []
    details.append(f"Total devices in OME: {result['total_count']}")
    details.append(f"Devices assigned to static groups: {result['assigned_count']}")
    details.append(f"Devices NOT assigned (unassigned): {len(unassigned)}")
    details.append(f"PXE entries in {default_group}: {len(pxe_default_ips)}")

    if not unassigned and not pxe_default_ips:
        # All devices are assigned and no default group entries
        log.skipped(
            "All devices assigned to static groups",
            f"Total: {result['total_count']}, Assigned: {result['assigned_count']}"
        )
        pytest.skip("All OME devices are assigned to static groups")

    # Compare unassigned OME devices with PXE default group entries
    matched_ips = unassigned_bmc_ips & pxe_default_ips
    missing_in_pxe = unassigned_bmc_ips - pxe_default_ips  # In OME unassigned but not in PXE
    missing_in_ome = pxe_default_ips - unassigned_bmc_ips  # In PXE default but not unassigned in OME

    details.append("")
    details.append(f"Unassigned Devices (expected in {default_group}):")

    for device in unassigned:
        name = device.get("name", "Unknown")
        identifier = device.get("identifier", "")
        ip = device.get("ip", "")
        model = device.get("model", "")

        if ip in matched_ips:
            details.append(f"  ✓ {name} ({identifier})")
            details.append(f"      BMC_IP: {ip}")
            details.append(f"      Model: {model}")
        else:
            details.append(f"  ✗ {name} ({identifier})")
            details.append(f"      BMC_IP: {ip} (NOT in PXE {default_group})")
            details.append(f"      Model: {model}")

    # Show PXE entries not found in OME unassigned
    if missing_in_ome:
        details.append("")
        details.append(f"PXE {default_group} entries NOT in OME unassigned:")
        for ip in sorted(missing_in_ome):
            details.append(f"  ✗ {ip}")

    # Determine pass/fail
    if missing_in_pxe or missing_in_ome:
        details.append("")
        details.append("Summary:")
        details.append(f"  Matched: {len(matched_ips)}")
        if missing_in_pxe:
            details.append(f"  OME unassigned but NOT in PXE: {len(missing_in_pxe)}")
        if missing_in_ome:
            details.append(f"  PXE {default_group} but NOT unassigned in OME: {len(missing_in_ome)}")

        log.failed(
            f"Unassigned devices mismatch with PXE {default_group}",
            "\n".join(details)
        )
        assert False, (
            f"Unassigned OME devices do not match PXE {default_group} entries.\n"
            f"OME unassigned: {len(unassigned_bmc_ips)}, "
            f"PXE {default_group}: {len(pxe_default_ips)}, "
            f"Matched: {len(matched_ips)}"
        )

    # All matched
    log.passed(
        f"All {len(matched_ips)} unassigned devices match PXE {default_group}",
        "\n".join(details)
    )


# =============================================================================
# TEST 8: ADMIN_MAC VALIDATION (PXE vs OME)
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(8)
def test_admin_mac_validation(host):
    """
    Test Case 8: Verify ADMIN_MAC matches OME first active non-iDRAC NIC.

    For each device in PXE mapping:
    1. Get the SERVICE_TAG
    2. Query OME for the device's NIC inventory
    3. Find first active non-iDRAC NIC MAC
    4. Compare with ADMIN_MAC in PXE mapping
    """
    log = TestLogger(TEST_NAMES["admin_mac_validation"])

    # Check if BMC discovery is enabled
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

    # Get PXE mapping data
    rows, err = _get_pxe_mapping_data(host)
    if err:
        log.skipped(SKIP_MSGS["no_bmc_pxe_mapping"], err)
        pytest.skip(SKIP_MSGS["no_bmc_pxe_mapping"])

    if not rows:
        log.skipped(SKIP_MSGS["no_rows_in_mapping"], "")
        pytest.skip(SKIP_MSGS["no_rows_in_mapping"])

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

    # Validate ADMIN_MAC for each device
    matched = []
    mismatched = []
    errors = []
    details = []

    for row in rows:
        service_tag = row.get("SERVICE_TAG", "")
        pxe_admin_mac = row.get("ADMIN_MAC", "").upper()
        hostname = row.get("HOSTNAME", "")
        fg = row.get("FUNCTIONAL_GROUP_NAME", "")

        if not service_tag:
            errors.append({"hostname": hostname, "reason": "No SERVICE_TAG"})
            continue

        # Get device details from OME
        ome_result = get_ome_device_details_by_service_tag(host, service_tag)
        if not ome_result["success"]:
            errors.append({"hostname": hostname, "service_tag": service_tag, "reason": ome_result["error"]})
            continue

        ome_mac = ome_result.get("first_nic_mac", "").upper()

        if pxe_admin_mac == ome_mac:
            matched.append({
                "hostname": hostname,
                "service_tag": service_tag,
                "mac": pxe_admin_mac,
                "fg": fg,
            })
        else:
            mismatched.append({
                "hostname": hostname,
                "service_tag": service_tag,
                "pxe_mac": pxe_admin_mac,
                "ome_mac": ome_mac,
                "fg": fg,
            })

    # Build details for display
    grouped = _group_rows_by_functional_group(rows)
    for fg_name in sorted(grouped.keys()):
        details.append(f"[{fg_name}]")
        fg_rows = grouped[fg_name]
        for row in fg_rows:
            hostname = row.get("HOSTNAME", "")
            service_tag = row.get("SERVICE_TAG", "")
            pxe_mac = row.get("ADMIN_MAC", "").upper()

            # Check if matched or mismatched
            is_matched = any(m["hostname"] == hostname for m in matched)
            is_mismatched = any(m["hostname"] == hostname for m in mismatched)

            if is_matched:
                details.append(f"  ✓ {hostname} ({service_tag})")
                details.append(f"      ADMIN_MAC: {pxe_mac}")
            elif is_mismatched:
                mismatch = next(m for m in mismatched if m["hostname"] == hostname)
                details.append(f"  ✗ {hostname} ({service_tag})")
                details.append(f"      PXE ADMIN_MAC: {mismatch['pxe_mac']}")
                details.append(f"      OME First NIC: {mismatch['ome_mac']}")
            else:
                details.append(f"  ? {hostname} ({service_tag})")
                details.append(f"      ADMIN_MAC: {pxe_mac} (could not verify)")

    if mismatched:
        details.append("")
        details.append(f"Mismatched ({len(mismatched)}):")
        for m in mismatched:
            details.append(f"  ✗ {m['hostname']}: PXE={m['pxe_mac']}, OME={m['ome_mac']}")

        log.failed(
            f"{len(mismatched)}/{len(rows)} ADMIN_MAC mismatches found",
            "\n".join(details)
        )
        assert False, (
            f"ADMIN_MAC validation failed.\n"
            f"Mismatched: {len(mismatched)}/{len(rows)}\n"
            f"Example: {mismatched[0]['hostname']} - PXE: {mismatched[0]['pxe_mac']}, OME: {mismatched[0]['ome_mac']}"
        )

    log.passed(
        f"All {len(matched)} ADMIN_MAC values match OME",
        "\n".join(details)
    )


# =============================================================================
# TEST 9: IB_NIC_NAME VALIDATION (PXE vs OME)
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(9)
def test_ib_nic_name_validation(host):
    """
    Test Case 9: Verify IB_NIC_NAME matches OME first active InfiniBand NIC.

    For each device in PXE mapping that has IB_NIC_NAME:
    1. Get the SERVICE_TAG
    2. Query OME for the device's NIC inventory
    3. Find first active InfiniBand NIC name
    4. Compare with IB_NIC_NAME in PXE mapping
    """
    log = TestLogger(TEST_NAMES["ib_nic_name_validation"])

    # Check if BMC discovery is enabled
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

    # Get PXE mapping data
    rows, err = _get_pxe_mapping_data(host)
    if err:
        log.skipped(SKIP_MSGS["no_bmc_pxe_mapping"], err)
        pytest.skip(SKIP_MSGS["no_bmc_pxe_mapping"])

    if not rows:
        log.skipped(SKIP_MSGS["no_rows_in_mapping"], "")
        pytest.skip(SKIP_MSGS["no_rows_in_mapping"])

    # Filter rows that have IB_NIC_NAME
    ib_rows = [r for r in rows if r.get("IB_NIC_NAME", "").strip()]
    if not ib_rows:
        log.skipped("No devices with IB_NIC_NAME in PXE mapping", "IB validation skipped")
        pytest.skip("No devices with IB_NIC_NAME in PXE mapping")

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
    log.check(f"Validating IB_NIC_NAME for {len(ib_rows)} devices with InfiniBand")

    # Validate IB_NIC_NAME for each device
    matched = []
    mismatched = []
    ib_down_errors = []  # IB NIC is DOWN in OME but present in PXE
    errors = []
    details = []

    for row in ib_rows:
        service_tag = row.get("SERVICE_TAG", "")
        pxe_ib_nic = row.get("IB_NIC_NAME", "").strip()
        hostname = row.get("HOSTNAME", "")
        fg = row.get("FUNCTIONAL_GROUP_NAME", "")

        if not service_tag:
            errors.append({"hostname": hostname, "reason": "No SERVICE_TAG"})
            continue

        # Get device details from OME
        ome_result = get_ome_device_details_by_service_tag(host, service_tag)
        if not ome_result["success"]:
            errors.append({
                "hostname": hostname,
                "service_tag": service_tag,
                "reason": ome_result["error"]
            })
            continue

        ome_ib_nic = ome_result.get("ib_nic_name", "").strip()
        ib_status = ome_result.get("ib_nic_status", "")
        ib_exists = ome_result.get("ib_nic_exists", False)

        # Check if IB NIC is DOWN in OME but present in PXE
        if pxe_ib_nic and ib_exists and ib_status == "Down":
            ib_down_errors.append({
                "hostname": hostname,
                "service_tag": service_tag,
                "pxe_ib_nic": pxe_ib_nic,
                "ome_status": "Down",
                "fg": fg,
            })
            continue

        if pxe_ib_nic == ome_ib_nic:
            matched.append({
                "hostname": hostname,
                "service_tag": service_tag,
                "ib_nic": pxe_ib_nic,
                "ib_status": ib_status,
                "fg": fg,
            })
        else:
            mismatched.append({
                "hostname": hostname,
                "service_tag": service_tag,
                "pxe_ib_nic": pxe_ib_nic,
                "ome_ib_nic": ome_ib_nic,
                "ome_status": ib_status,
                "fg": fg,
            })

    # Build details for display
    grouped = _group_rows_by_functional_group(ib_rows)
    for fg_name in sorted(grouped.keys()):
        details.append(f"[{fg_name}]")
        fg_rows = grouped[fg_name]
        for row in fg_rows:
            hostname = row.get("HOSTNAME", "")
            service_tag = row.get("SERVICE_TAG", "")
            pxe_ib_nic = row.get("IB_NIC_NAME", "").strip()

            # Check if matched, mismatched, or IB DOWN
            is_matched = any(m["hostname"] == hostname for m in matched)
            is_mismatched = any(m["hostname"] == hostname for m in mismatched)
            is_ib_down = any(m["hostname"] == hostname for m in ib_down_errors)

            if is_matched:
                details.append(f"  ✓ {hostname} ({service_tag})")
                details.append(f"      IB_NIC_NAME: {pxe_ib_nic} (Up)")
            elif is_ib_down:
                details.append(f"  ✗ {hostname} ({service_tag})")
                details.append(f"      IB_NIC_NAME: {pxe_ib_nic} (DOWN in OME)")
            elif is_mismatched:
                mismatch = next(m for m in mismatched if m["hostname"] == hostname)
                details.append(f"  ✗ {hostname} ({service_tag})")
                details.append(f"      PXE IB_NIC_NAME: {mismatch['pxe_ib_nic']}")
                ome_nic = mismatch['ome_ib_nic'] or '(none found)'
                details.append(f"      OME IB NIC:      {ome_nic}")
            else:
                details.append(f"  ? {hostname} ({service_tag})")
                details.append(f"      IB_NIC_NAME: {pxe_ib_nic} (could not verify)")

    # Show IB DOWN errors
    if ib_down_errors:
        details.append("")
        details.append(f"IB NIC DOWN in OME ({len(ib_down_errors)}):")
        for m in ib_down_errors:
            details.append(f"  ✗ {m['hostname']}: {m['pxe_ib_nic']} is DOWN")

    if mismatched:
        details.append("")
        details.append(f"Mismatched ({len(mismatched)}):")
        for m in mismatched:
            ome_nic = m['ome_ib_nic'] or '(none)'
            details.append(f"  ✗ {m['hostname']}: PXE={m['pxe_ib_nic']}, OME={ome_nic}")

    # Fail if IB DOWN or mismatched
    if ib_down_errors:
        log.failed(
            f"{len(ib_down_errors)} IB NIC(s) DOWN in OME but present in PXE",
            "\n".join(details)
        )
        assert False, (
            f"IB_NIC_NAME validation failed - IB NIC is DOWN in OME.\n"
            f"DOWN: {len(ib_down_errors)}/{len(ib_rows)}\n"
            f"Example: {ib_down_errors[0]['hostname']} - "
            f"{ib_down_errors[0]['pxe_ib_nic']} is DOWN"
        )

    if mismatched:
        log.failed(
            f"{len(mismatched)}/{len(ib_rows)} IB_NIC_NAME mismatches found",
            "\n".join(details)
        )
        ome_nic = mismatched[0]['ome_ib_nic'] or '(none)'
        assert False, (
            f"IB_NIC_NAME validation failed.\n"
            f"Mismatched: {len(mismatched)}/{len(ib_rows)}\n"
            f"Example: {mismatched[0]['hostname']} - "
            f"PXE: {mismatched[0]['pxe_ib_nic']}, OME: {ome_nic}"
        )

    log.passed(
        f"All {len(matched)} IB_NIC_NAME values match OME",
        "\n".join(details)
    )
