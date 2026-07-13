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
Provision Module - Kernel Version Override Verification Functions.

Functions for verifying kernel_version_override behavior:
- Reading kernel_version_override from provision_config.yml
- Verifying provisioned nodes run the overridden kernel version
- Verifying S3 boot images match the override
- Verifying BSS templates reference the correct kernel
"""

import re
from typing import Dict, Any

import yaml

from automation_library.core import (
    run_in_container,
    run_on_remote_node,
    get_functional_groups_from_pxe_mapping,
    get_nodes_info,
)
from automation_library.core.vars import (
    PROVISION_CONFIG_PATH,
)

# Regex for valid kernel version format: <major>.<minor>.<patch>-<release>
KERNEL_VERSION_PATTERN = re.compile(r"^[0-9]+\.[0-9]+\.[0-9]+-.+$")


# =============================================================================
# READ KERNEL VERSION OVERRIDE FROM PROVISION CONFIG
# =============================================================================

def get_kernel_version_override(host) -> Dict[str, Any]:
    """
    Read kernel_version_override from provision_config.yml.

    Returns:
        Dict with:
        - success: bool
        - kernel_version_override: str (empty if not set or auto-select)
        - is_configured: bool (True if non-empty override is set)
        - provision_config: dict (full parsed config)
        - error: str
    """
    result = run_in_container(host, f"cat {PROVISION_CONFIG_PATH}")
    if result.rc != 0:
        return {
            "success": False,
            "kernel_version_override": "",
            "is_configured": False,
            "provision_config": {},
            "error": f"Failed to read provision_config.yml: {result.stderr}",
        }

    try:
        config = yaml.safe_load(result.stdout) or {}
    except yaml.YAMLError as exc:
        return {
            "success": False,
            "kernel_version_override": "",
            "is_configured": False,
            "provision_config": {},
            "error": f"Failed to parse provision_config.yml: {exc}",
        }

    kvo = config.get("kernel_version_override", "") or ""
    kvo = kvo.strip()

    return {
        "success": True,
        "kernel_version_override": kvo,
        "is_configured": len(kvo) > 0,
        "provision_config": config,
        "error": "",
    }


# =============================================================================
# VALIDATE KERNEL VERSION OVERRIDE FORMAT
# =============================================================================

def validate_kernel_version_override_format(host) -> Dict[str, Any]:
    """
    Validate that kernel_version_override has a valid format.

    Valid formats:
    - Empty string (auto-select latest)
    - Version like "6.12.0-55.76.1.el10_0"

    Returns:
        Dict with success, kernel_version_override, is_valid_format,
        is_empty, error, details
    """
    kvo_result = get_kernel_version_override(host)
    if not kvo_result["success"]:
        return {
            "success": False,
            "kernel_version_override": "",
            "is_valid_format": False,
            "is_empty": True,
            "error": kvo_result["error"],
            "details": "",
        }

    kvo = kvo_result["kernel_version_override"]

    if not kvo:
        return {
            "success": True,
            "kernel_version_override": "",
            "is_valid_format": True,
            "is_empty": True,
            "error": "",
            "details": "kernel_version_override is empty — auto-select mode",
        }

    is_valid = bool(KERNEL_VERSION_PATTERN.match(kvo))

    return {
        "success": True,
        "kernel_version_override": kvo,
        "is_valid_format": is_valid,
        "is_empty": False,
        "error": "" if is_valid else (
            f"Invalid kernel_version_override format: '{kvo}'. "
            f"Expected: <major>.<minor>.<patch>-<release> "
            f"(e.g. '6.12.0-55.76.1.el10_0')"
        ),
        "details": f"kernel_version_override='{kvo}' format_valid={is_valid}",
    }


# =============================================================================
# VALIDATE ARBITRARY KERNEL VERSION STRING FORMAT (NEGATIVE TEST HELPER)
# =============================================================================

def validate_kernel_version_string_format(kvo: str) -> Dict[str, Any]:
    """
    Validate an arbitrary kernel version string against the expected format.

    Unlike validate_kernel_version_override_format(), this does not read from
    provision_config.yml — it validates any string directly. Used by negative
    tests to confirm malformed values are correctly rejected.

    Args:
        kvo: Kernel version string to validate (e.g. "6.12.0-55.76.1.el10_0")

    Returns:
        Dict with kernel_version_override, is_valid_format, is_empty, details
    """
    kvo = (kvo or "").strip()

    if not kvo:
        return {
            "kernel_version_override": "",
            "is_valid_format": True,
            "is_empty": True,
            "details": "Empty string — auto-select mode (valid)",
        }

    is_valid = bool(KERNEL_VERSION_PATTERN.match(kvo))
    return {
        "kernel_version_override": kvo,
        "is_valid_format": is_valid,
        "is_empty": False,
        "details": f"kernel_version_override='{kvo}' format_valid={is_valid}",
    }


# =============================================================================
# VERIFY S3 BOOT IMAGES MATCH KERNEL OVERRIDE
# =============================================================================

def verify_kernel_override_in_s3(host) -> Dict[str, Any]:
    """
    Verify that S3 boot-images contain vmlinuz and initramfs matching
    the kernel_version_override.

    Returns:
        Dict with success, kernel_version_override, matching_images,
        functional_groups_checked, error, details
    """
    kvo_result = get_kernel_version_override(host)
    if not kvo_result["success"]:
        return {
            "success": False,
            "kernel_version_override": "",
            "matching_images": [],
            "functional_groups_checked": [],
            "error": kvo_result["error"],
            "details": "",
            "not_configured": True,
        }

    kvo = kvo_result["kernel_version_override"]
    if not kvo:
        return {
            "success": True,
            "kernel_version_override": "",
            "matching_images": [],
            "functional_groups_checked": [],
            "error": "",
            "details": "kernel_version_override not set — auto-select mode",
            "not_configured": True,
        }

    # List all S3 boot images
    s3_result = run_in_container(
        host,
        "s3cmd ls -Hr s3://boot-images 2>/dev/null | awk '{print $4}'"
    )
    if s3_result.rc != 0:
        return {
            "success": False,
            "kernel_version_override": kvo,
            "matching_images": [],
            "functional_groups_checked": [],
            "error": f"Failed to list S3 boot-images: {s3_result.stderr}",
            "details": "",
            "not_configured": False,
        }

    s3_lines = [
        line.strip() for line in s3_result.stdout.strip().split("\n")
        if line.strip()
    ]

    # Find vmlinuz and initramfs matching the kernel override
    matching_vmlinuz = [
        line for line in s3_lines
        if "vmlinuz" in line and kvo in line
    ]
    matching_initramfs = [
        line for line in s3_lines
        if "initramfs" in line and kvo in line
    ]

    has_vmlinuz = len(matching_vmlinuz) > 0
    has_initramfs = len(matching_initramfs) > 0

    details_lines = [
        f"kernel_version_override: {kvo}",
        f"Total S3 entries: {len(s3_lines)}",
        f"Matching vmlinuz: {len(matching_vmlinuz)}",
        f"Matching initramfs: {len(matching_initramfs)}",
    ]
    if matching_vmlinuz:
        for entry in matching_vmlinuz[:5]:
            details_lines.append(f"  vmlinuz: {entry}")
    if matching_initramfs:
        for entry in matching_initramfs[:5]:
            details_lines.append(f"  initramfs: {entry}")

    if has_vmlinuz and has_initramfs:
        return {
            "success": True,
            "kernel_version_override": kvo,
            "matching_images": matching_vmlinuz + matching_initramfs,
            "functional_groups_checked": [],
            "error": "",
            "details": "\n".join(details_lines),
            "not_configured": False,
        }

    errors = []
    if not has_vmlinuz:
        errors.append(f"No vmlinuz matching '{kvo}' found in S3")
    if not has_initramfs:
        errors.append(f"No initramfs matching '{kvo}' found in S3")

    return {
        "success": False,
        "kernel_version_override": kvo,
        "matching_images": matching_vmlinuz + matching_initramfs,
        "functional_groups_checked": [],
        "error": "; ".join(errors),
        "details": "\n".join(details_lines),
        "not_configured": False,
    }


# =============================================================================
# VERIFY PROVISIONED NODE KERNEL MATCHES OVERRIDE
# =============================================================================

def verify_node_kernel_version(
    host,
    node_ip: str,
) -> Dict[str, Any]:
    """
    Verify that a provisioned node's running kernel matches the override.

    Args:
        host: Testinfra host (OIM)
        node_ip: Admin IP of the node to check

    Returns:
        Dict with success, node_ip, running_kernel, expected_kernel,
        matches, error
    """
    kvo_result = get_kernel_version_override(host)
    if not kvo_result["success"]:
        return {
            "success": False,
            "node_ip": node_ip,
            "running_kernel": "",
            "expected_kernel": "",
            "matches": False,
            "error": kvo_result["error"],
            "not_configured": True,
        }

    kvo = kvo_result["kernel_version_override"]
    if not kvo:
        return {
            "success": True,
            "node_ip": node_ip,
            "running_kernel": "",
            "expected_kernel": "",
            "matches": True,
            "error": "",
            "not_configured": True,
        }

    # Get running kernel from node
    uname_result = run_on_remote_node(host, node_ip, "uname -r")
    if uname_result.rc != 0:
        return {
            "success": False,
            "node_ip": node_ip,
            "running_kernel": "",
            "expected_kernel": kvo,
            "matches": False,
            "error": f"Failed to get kernel version from {node_ip}: {uname_result.stderr}",
            "not_configured": False,
        }

    running_kernel = uname_result.stdout.strip()
    matches = kvo in running_kernel

    return {
        "success": True,
        "node_ip": node_ip,
        "running_kernel": running_kernel,
        "expected_kernel": kvo,
        "matches": matches,
        "error": "" if matches else (
            f"Kernel mismatch on {node_ip}: "
            f"running={running_kernel}, expected contains '{kvo}'"
        ),
        "not_configured": False,
    }


def verify_all_nodes_kernel_version(host) -> Dict[str, Any]:
    """
    Verify kernel version on all provisioned nodes matches the override.

    Returns:
        Dict with success, kernel_version_override, nodes_checked,
        nodes_matched, nodes_mismatched, error, details
    """
    kvo_result = get_kernel_version_override(host)
    if not kvo_result["success"]:
        return {
            "success": False,
            "kernel_version_override": "",
            "nodes_checked": 0,
            "nodes_matched": [],
            "nodes_mismatched": [],
            "error": kvo_result["error"],
            "details": "",
            "not_configured": True,
        }

    kvo = kvo_result["kernel_version_override"]
    if not kvo:
        return {
            "success": True,
            "kernel_version_override": "",
            "nodes_checked": 0,
            "nodes_matched": [],
            "nodes_mismatched": [],
            "error": "",
            "details": "kernel_version_override not set — skipping node checks",
            "not_configured": True,
        }

    # Get all functional groups, then retrieve nodes for each group
    functional_groups = get_functional_groups_from_pxe_mapping(host)
    if not functional_groups:
        return {
            "success": False,
            "kernel_version_override": kvo,
            "nodes_checked": 0,
            "nodes_matched": [],
            "nodes_mismatched": [],
            "error": "No functional groups found in PXE mapping",
            "details": "",
            "not_configured": False,
        }

    # Collect all nodes across all functional groups
    all_nodes = []
    seen_ips = set()
    for fg_name in functional_groups:
        nodes = get_nodes_info(
            host, search_by="functional_group", search_value=fg_name
        )
        for node in nodes:
            ip = node.get("admin_ip", "")
            if ip and ip not in seen_ips:
                seen_ips.add(ip)
                all_nodes.append(node)

    if not all_nodes:
        return {
            "success": False,
            "kernel_version_override": kvo,
            "nodes_checked": 0,
            "nodes_matched": [],
            "nodes_mismatched": [],
            "error": "No nodes with admin IPs found in PXE mapping",
            "details": "",
            "not_configured": False,
        }

    matched = []
    mismatched = []
    errors = []

    for node in all_nodes:
        node_ip = node.get("admin_ip", "")
        if not node_ip:
            continue

        result = verify_node_kernel_version(host, node_ip)
        if result.get("not_configured"):
            continue

        if not result["success"]:
            errors.append(result["error"])
            mismatched.append({
                "node_ip": node_ip,
                "hostname": node.get("hostname", ""),
                "running_kernel": result.get("running_kernel", ""),
                "error": result["error"],
            })
            continue

        if result["matches"]:
            matched.append({
                "node_ip": node_ip,
                "hostname": node.get("hostname", ""),
                "running_kernel": result["running_kernel"],
            })
        else:
            mismatched.append({
                "node_ip": node_ip,
                "hostname": node.get("hostname", ""),
                "running_kernel": result["running_kernel"],
                "error": result["error"],
            })

    total_checked = len(matched) + len(mismatched)
    details_lines = [
        f"kernel_version_override: {kvo}",
        f"Nodes checked: {total_checked}",
        f"Nodes matched: {len(matched)}",
        f"Nodes mismatched: {len(mismatched)}",
    ]
    for m in mismatched:
        details_lines.append(
            f"  MISMATCH: {m['hostname']} ({m['node_ip']}) "
            f"running={m['running_kernel']}"
        )

    return {
        "success": len(mismatched) == 0 and total_checked > 0,
        "kernel_version_override": kvo,
        "nodes_checked": total_checked,
        "nodes_matched": matched,
        "nodes_mismatched": mismatched,
        "error": "; ".join(errors) if errors else "",
        "details": "\n".join(details_lines),
        "not_configured": False,
    }


# =============================================================================
# VERIFY BSS TEMPLATES REFERENCE KERNEL OVERRIDE
# =============================================================================

def verify_bss_kernel_override(host) -> Dict[str, Any]:
    """
    Verify BSS boot templates reference the overridden kernel version.

    Checks that the BSS boot params (kernel/initrd paths) contain the
    kernel_version_override string.

    Returns:
        Dict with success, kernel_version_override, groups_checked,
        groups_matched, groups_mismatched, error, details
    """
    kvo_result = get_kernel_version_override(host)
    if not kvo_result["success"]:
        return {
            "success": False,
            "kernel_version_override": "",
            "groups_checked": 0,
            "groups_matched": [],
            "groups_mismatched": [],
            "error": kvo_result["error"],
            "details": "",
            "not_configured": True,
        }

    kvo = kvo_result["kernel_version_override"]
    if not kvo:
        return {
            "success": True,
            "kernel_version_override": "",
            "groups_checked": 0,
            "groups_matched": [],
            "groups_mismatched": [],
            "error": "",
            "details": "kernel_version_override not set — skipping BSS check",
            "not_configured": True,
        }

    # Read BSS boot templates
    bss_result = run_in_container(
        host,
        "find /opt/omnia/.data/bss/ -name '*.json' -type f 2>/dev/null"
    )
    if bss_result.rc != 0 or not bss_result.stdout.strip():
        return {
            "success": False,
            "kernel_version_override": kvo,
            "groups_checked": 0,
            "groups_matched": [],
            "groups_mismatched": [],
            "error": "No BSS boot templates found",
            "details": "",
            "not_configured": False,
        }

    template_files = [
        f.strip() for f in bss_result.stdout.strip().split("\n") if f.strip()
    ]

    matched = []
    mismatched = []

    for tpl_path in template_files:
        cat_result = run_in_container(host, f"cat '{tpl_path}'")
        if cat_result.rc != 0:
            continue

        content = cat_result.stdout
        tpl_name = tpl_path.split("/")[-1]

        if kvo in content:
            matched.append(tpl_name)
        else:
            mismatched.append(tpl_name)

    total = len(matched) + len(mismatched)

    details_lines = [
        f"kernel_version_override: {kvo}",
        f"BSS templates checked: {total}",
        f"Templates with override: {len(matched)}",
        f"Templates without override: {len(mismatched)}",
    ]
    for m in mismatched:
        details_lines.append(f"  MISSING override: {m}")

    return {
        "success": len(mismatched) == 0 and total > 0,
        "kernel_version_override": kvo,
        "groups_checked": total,
        "groups_matched": matched,
        "groups_mismatched": mismatched,
        "error": (
            f"{len(mismatched)} BSS templates do not reference "
            f"kernel override '{kvo}'"
        ) if mismatched else "",
        "details": "\n".join(details_lines),
        "not_configured": False,
    }
