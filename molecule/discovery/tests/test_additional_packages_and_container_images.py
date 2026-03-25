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
Additional Packages and Container Images Test Cases.

This module contains pytest test cases for verifying additional RPM packages
and container images on discovered nodes.

Test cases:
1. Verify additional RPM packages are installed on all nodes
2. Verify additional container images are present on K8s nodes
"""

import pytest
from automation_library.core import TestLogger
from automation_library.discovery.functions import (
    verify_additional_packages,
    verify_additional_container_images,
    is_additional_packages_enabled,
    get_allowed_additional_subgroups,
    get_additional_packages_json_path,
)
from automation_library.discovery.functions.additional_pkgs_func import (
    _normalize_kube_control_plane_role,
    _strip_arch_suffix,
)
from automation_library.discovery.messages import (
    ADDITIONAL_PKGS_TEST_NAMES,
    ADDITIONAL_PKGS_LOG_MSGS,
    ADDITIONAL_PKGS_ASSERT_MSGS,
)


# =============================================================================
# ADDITIONAL RPM PACKAGES TEST
# =============================================================================

def test_additional_packages(host):
    """
    Test Case 1: Verify additional RPM packages are installed on nodes.

    Reads additional_packages.json from omnia_core container to determine
    expected packages per functional group. For each node, checks that
    packages are installed using rpm -q.

    Packages are split into:
    - Global packages: additional_packages.cluster[] (applied to all roles)
    - Role-specific packages: <role_name>.cluster[] (per functional group)

    Skips if additional_packages is not enabled in software_config.json.
    """
    log = TestLogger(ADDITIONAL_PKGS_TEST_NAMES["additional_packages"])

    # Check if enabled
    log.check("Checking additional_packages configuration")
    result = verify_additional_packages(host)

    # Handle skip
    if result.get("skipped"):
        reason = result.get("reason", "Not enabled")
        log.check(ADDITIONAL_PKGS_LOG_MSGS["additional_pkgs_skipped"].format(reason=reason))
        pytest.skip(reason)

    # Handle load failure
    if result.get("error") and not result.get("results_by_group"):
        log.failed("Configuration load failed", result["error"])
        json_path = get_additional_packages_json_path(host)
        assert False, ADDITIONAL_PKGS_ASSERT_MSGS["additional_json_load_failed"].format(
            json_path=json_path
        )

    # Build details output
    details_lines = []
    total_checked = result.get("total_packages_checked", 0)
    total_missing = result.get("total_missing", 0)
    
    for fg, group_data in result.get("results_by_group", {}).items():
        if group_data.get("skipped"):
            details_lines.append(f"\n{fg}: skipped - {group_data.get('reason', '')}")
            continue

        expected_pkgs = group_data.get("packages_expected", [])
        
        # Check if kube control plane is normalized
        role_name = _strip_arch_suffix(fg)
        normalized_role = _normalize_kube_control_plane_role(host, fg)
        
        # Header with normalization indicator
        if role_name in ["service_kube_control_plane", "service_kube_control_plane_first"] and normalized_role != role_name:
            details_lines.append(f"\n{fg} ({len(expected_pkgs)} packages) [treated as: {normalized_role}]")
        else:
            details_lines.append(f"\n{fg} ({len(expected_pkgs)} packages)")
        
        details_lines.append(f"  Expected: {', '.join(expected_pkgs)}")

        for node in group_data.get("nodes", []):
            hostname = node["hostname"]
            admin_ip = node.get("admin_ip", "")
            missing = node.get("missing", [])

            if not admin_ip:
                details_lines.append(f"  ✗ {hostname} (no admin_ip)")
                continue

            if not missing:
                details_lines.append(f"  ✓ {hostname} ({admin_ip})")
            else:
                details_lines.append(f"  ✗ {hostname} ({admin_ip}) - missing: {', '.join(missing)}")

    details = "\n".join(details_lines)

    # Log result
    if result["success"]:
        log.passed(
            ADDITIONAL_PKGS_LOG_MSGS["additional_pkgs_success"].format(checked=total_checked),
            details
        )
    else:
        log.failed(
            ADDITIONAL_PKGS_LOG_MSGS["additional_pkgs_failed"].format(
                missing=total_missing, checked=total_checked
            ),
            details
        )

    # Build assertion details
    failed_details = ""
    json_path = get_additional_packages_json_path(host)
    for fg, group_data in result.get("results_by_group", {}).items():
        if group_data.get("skipped"):
            continue
        for node in group_data.get("nodes", []):
            if node.get("missing"):
                failed_details += (
                    f"  {node['hostname']} ({node.get('admin_ip', '')}): "
                    f"{', '.join(node['missing'])}\n"
                )

    assert result["success"], ADDITIONAL_PKGS_ASSERT_MSGS[
        "additional_packages_failed"
    ].format(
        missing_count=total_missing,
        checked_count=total_checked,
        failed_details=failed_details,
        json_path=json_path,
    )


# =============================================================================
# ADDITIONAL CONTAINER IMAGES TEST
# =============================================================================

def test_additional_container_images(host):
    """
    Test Case 2: Verify additional container images are present on K8s nodes.

    Reads additional_packages.json from omnia_core container to determine
    expected container images per K8s functional group. For each K8s node,
    checks that images are present using crictl images or podman images.

    Only K8s roles receive container images:
    - service_kube_control_plane
    - service_kube_control_plane_first
    - service_kube_node

    Images are split into:
    - Global images: additional_packages.cluster[] (type: "image")
    - Role-specific images: <role_name>.cluster[] (type: "image")

    Skips if additional_packages is not enabled or no K8s groups in PXE mapping.
    """
    log = TestLogger(ADDITIONAL_PKGS_TEST_NAMES["additional_container_images"])

    # Check if enabled
    log.check("Checking additional container images configuration")
    result = verify_additional_container_images(host)

    # Handle skip
    if result.get("skipped"):
        reason = result.get("reason", "Not enabled")
        log.check(ADDITIONAL_PKGS_LOG_MSGS["additional_images_skipped"].format(reason=reason))
        pytest.skip(reason)

    # Handle load failure
    if result.get("error") and not result.get("results_by_group"):
        log.failed("Configuration load failed", result["error"])
        json_path = get_additional_packages_json_path(host)
        assert False, ADDITIONAL_PKGS_ASSERT_MSGS["additional_json_load_failed"].format(
            json_path=json_path
        )

    # Build details output
    details_lines = []
    total_checked = result.get("total_images_checked", 0)
    total_missing = result.get("total_missing", 0)

    for fg, group_data in result.get("results_by_group", {}).items():
        if group_data.get("skipped"):
            details_lines.append(f"\n{fg}: skipped - {group_data.get('reason', '')}")
            continue

        is_k8s_role = group_data.get("is_k8s_role", True)
        expected_images = group_data.get("images_expected", [])
        
        # Check if kube control plane is normalized
        role_name = _strip_arch_suffix(fg)
        normalized_role = _normalize_kube_control_plane_role(host, fg)
        
        # Header based on role type
        if is_k8s_role:
            if role_name in ["service_kube_control_plane", "service_kube_control_plane_first"] and normalized_role != role_name:
                details_lines.append(f"\n{fg} ({len(expected_images)} images) [treated as: {normalized_role}]")
            else:
                details_lines.append(f"\n{fg} ({len(expected_images)} images)")
            if expected_images:
                details_lines.append(f"  Expected: {', '.join(expected_images)}")
        else:
            # Non-K8s role (e.g., Slurm)
            details_lines.append(f"\n{fg} (Non-K8s role)")
            details_lines.append(f"  Note: {group_data.get('reason', 'No container images expected')}")

        for node in group_data.get("nodes", []):
            hostname = node["hostname"]
            admin_ip = node.get("admin_ip", "")
            missing = node.get("missing", [])
            note = node.get("note", "")

            if not admin_ip:
                details_lines.append(f"  ✗ {hostname} (no admin_ip)")
                continue

            # Handle non-K8s nodes
            if not is_k8s_role:
                details_lines.append(f"  ○ {hostname} ({admin_ip}) - no images expected")
                continue

            # Handle K8s nodes
            if not missing:
                details_lines.append(f"  ✓ {hostname} ({admin_ip})")
            else:
                details_lines.append(f"  ✗ {hostname} ({admin_ip}) - missing: {', '.join(missing)}")

    details = "\n".join(details_lines)

    # Log result
    if result["success"]:
        log.passed(
            ADDITIONAL_PKGS_LOG_MSGS["additional_images_success"].format(checked=total_checked),
            details
        )
    else:
        log.failed(
            ADDITIONAL_PKGS_LOG_MSGS["additional_images_failed"].format(
                missing=total_missing, checked=total_checked
            ),
            details
        )

    # Build assertion details
    failed_details = ""
    json_path = get_additional_packages_json_path(host)
    for fg, group_data in result.get("results_by_group", {}).items():
        if group_data.get("skipped") or not group_data.get("is_k8s_role", True):
            continue
        for node in group_data.get("nodes", []):
            if node.get("missing"):
                failed_details += (
                    f"  {node['hostname']} ({node.get('admin_ip', '')}): "
                    f"{', '.join(node['missing'])}\n"
                )

    assert result["success"], ADDITIONAL_PKGS_ASSERT_MSGS[
        "additional_images_failed"
    ].format(
        missing_count=total_missing,
        checked_count=total_checked,
        failed_details=failed_details,
        json_path=json_path,
    )
