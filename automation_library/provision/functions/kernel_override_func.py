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

# Regex for valid kernel version format: <major>.<minor>.<patch>-<release>.<dist_tag>
# Example: 6.12.0-55.76.1.el10_0
KERNEL_VERSION_PATTERN = re.compile(r"^[0-9]+\.[0-9]+\.[0-9]+-[0-9]+\.[0-9]+\.[0-9]+\.[a-z]+[0-9_]+$")

# Architecture suffixes stripped from uname -r for comparison
_ARCH_SUFFIXES = (".x86_64", ".aarch64", ".ppc64le", ".s390x")

# Detects dist tags like "el100" (3+ unbroken digits after ".el") which
# almost certainly should be "el10_0" — RHEL uses el<major>_<minor>.
_SUSPICIOUS_DIST_TAG_RE = re.compile(r'\.el(\d{3,})$')


def _strip_arch_suffix(kernel_version: str) -> str:
    """Strip architecture suffix (e.g. .x86_64) from a kernel version string."""
    for suffix in _ARCH_SUFFIXES:
        if kernel_version.endswith(suffix):
            return kernel_version[:-len(suffix)]
    return kernel_version


def _check_suspicious_dist_tag(kvo: str) -> tuple:
    """
    Check if the dist tag looks like a typo (e.g., el100 instead of el10_0).

    RHEL dist tags use ``el<major>_<minor>`` (e.g., ``el10_0``, ``el9_3``).
    If the string ends with ``el`` followed by 3+ digits and no underscore,
    it is almost certainly a typo with a missing underscore separator.

    Returns:
        (is_suspicious: bool, suggested_fix: str)
    """
    m = _SUSPICIOUS_DIST_TAG_RE.search(kvo)
    if m:
        digits = m.group(1)
        major = digits[:2]
        minor = digits[2:]
        suggested = kvo[:m.start()] + f".el{major}_{minor}"
        return True, suggested
    return False, ""


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

    # Secondary check: suspicious dist tag (e.g., el100 instead of el10_0)
    dist_suspicious, dist_suggestion = _check_suspicious_dist_tag(kvo)
    if is_valid and dist_suspicious:
        is_valid = False

    error = ""
    if not is_valid:
        error = (
            f"Invalid kernel_version_override format: '{kvo}'. "
            f"Expected: <major>.<minor>.<patch>-<release> "
            f"(e.g. '6.12.0-55.76.1.el10_0')"
        )
        if dist_suspicious:
            error += f" Possible dist tag typo \u2014 did you mean '{dist_suggestion}'?"

    details = f"kernel_version_override='{kvo}' format_valid={is_valid}"
    if dist_suspicious:
        details += f" (possible dist tag typo \u2014 did you mean '{dist_suggestion}'?)"

    return {
        "success": True,
        "kernel_version_override": kvo,
        "is_valid_format": is_valid,
        "is_empty": False,
        "error": error,
        "details": details,
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

    # Secondary check: suspicious dist tag (e.g., el100 instead of el10_0)
    dist_suspicious, dist_suggestion = _check_suspicious_dist_tag(kvo)
    if is_valid and dist_suspicious:
        is_valid = False

    details = f"kernel_version_override='{kvo}' format_valid={is_valid}"
    if dist_suspicious:
        details += f" (possible dist tag typo \u2014 did you mean '{dist_suggestion}'?)"

    return {
        "kernel_version_override": kvo,
        "is_valid_format": is_valid,
        "is_empty": False,
        "details": details,
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

    # List all S3 boot images - s3cmd runs on OIM host (ochami server)
    s3_result = host.run("s3cmd ls -Hr s3://boot-images 2>&1")
    if s3_result.rc != 0:
        return {
            "success": False,
            "kernel_version_override": kvo,
            "matching_images": [],
            "functional_groups_checked": [],
            "error": f"Failed to list S3 boot-images: {s3_result.stderr}",
            "details": f"s3cmd stderr: {s3_result.stderr}\ns3cmd stdout: {s3_result.stdout}",
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

    # Extract available kernel versions from S3 for troubleshooting
    available_versions = set()
    for line in s3_lines:
        if "vmlinuz-" in line:
            for segment in line.split("/"):
                if segment.startswith("vmlinuz-"):
                    version = _strip_arch_suffix(
                        segment[len("vmlinuz-"):].strip()
                    )
                    if version:
                        available_versions.add(version)

    if available_versions:
        details_lines.append("Available kernel versions in S3:")
        for v in sorted(available_versions):
            details_lines.append(f"  - {v}")

    # Check for dist tag typo hint
    dist_suspicious, dist_suggestion = _check_suspicious_dist_tag(kvo)
    if dist_suspicious:
        details_lines.append(
            f"Hint: Possible dist tag typo \u2014 did you mean '{dist_suggestion}'?"
        )

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
    uname_result = run_on_remote_node(host, "uname -r", node_ip)
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
    
    # If kernel is empty, it might be a SSH or command issue
    if not running_kernel:
        return {
            "success": False,
            "node_ip": node_ip,
            "running_kernel": "",
            "expected_kernel": kvo,
            "matches": False,
            "error": f"Empty kernel version returned from {node_ip} - SSH may have failed",
            "not_configured": False,
        }
    
    # Normalize: strip architecture suffix for comparison
    normalized_running = _strip_arch_suffix(running_kernel)
    normalized_kvo = _strip_arch_suffix(kvo)
    matches = normalized_kvo == normalized_running

    error = ""
    if not matches:
        error = (
            f"Kernel mismatch on {node_ip}: "
            f"running={running_kernel}, expected='{kvo}'"
        )
        # Check for dist tag typo hint
        dist_suspicious, dist_suggestion = _check_suspicious_dist_tag(kvo)
        if dist_suspicious:
            error += f" (possible dist tag typo \u2014 did you mean '{dist_suggestion}'?)"

    return {
        "success": True,
        "node_ip": node_ip,
        "running_kernel": running_kernel,
        "expected_kernel": kvo,
        "matches": matches,
        "error": error,
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

    # Read BSS boot templates - inside omnia_core container
    # BSS templates are YAML files in /opt/omnia/openchami/workdir/boot/
    bss_result = run_in_container(
        host,
        "find /opt/omnia/openchami/workdir/boot/ -name 'bss-*.yaml' -type f"
    )
    if bss_result.rc != 0 or not bss_result.stdout.strip():
        return {
            "success": True,
            "kernel_version_override": kvo,
            "groups_checked": 0,
            "groups_matched": [],
            "groups_mismatched": [],
            "error": "",
            "details": "BSS templates not found in /opt/omnia/openchami/workdir/boot/ - provision may not have been run",
            "not_configured": True,
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

    # Check for dist tag typo hint
    if mismatched:
        dist_suspicious, dist_suggestion = _check_suspicious_dist_tag(kvo)
        if dist_suspicious:
            details_lines.append(
                f"Hint: Possible dist tag typo \u2014 did you mean '{dist_suggestion}'?"
            )

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


# =============================================================================
# VERIFY KERNEL CONSISTENCY ACROSS ALL NODES
# =============================================================================

def verify_kernel_consistency(host) -> Dict[str, Any]:
    """
    Verify all provisioned nodes run the same kernel version.

    If kernel_version_override is set in provision_config.yml, this verifies
    all nodes run the overridden kernel. If not set, it verifies all nodes run
    the same kernel version (auto-select mode).

    Identified from /root/omnia analysis — provision/roles/
    provision_validations/tasks/validate_image.yml selects a single
    kernel per functional group; all nodes in the cluster should
    therefore converge on the same kernel version.

    Returns:
        Dict with success, nodes, unique_versions, error, details
    """
    # Get kernel_version_override from config
    kvo_result = get_kernel_version_override(host)
    kvo = kvo_result.get("kernel_version_override", "")
    is_configured = kvo_result.get("is_configured", False)

    functional_groups = get_functional_groups_from_pxe_mapping(host)
    if not functional_groups:
        return {
            "success": False,
            "nodes": [],
            "unique_versions": [],
            "error": "No functional groups found in PXE mapping",
            "details": "",
            "kernel_version_override": kvo,
            "is_configured": is_configured,
        }

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
            "nodes": [],
            "unique_versions": [],
            "error": "No nodes with admin IPs found in PXE mapping",
            "details": "",
            "kernel_version_override": kvo,
            "is_configured": is_configured,
        }

    node_results = []
    for node in all_nodes:
        node_ip = node.get("admin_ip", "")
        hostname = node.get("hostname", "")
        if not node_ip:
            continue

        uname_result = run_on_remote_node(host, "uname -r", node_ip)
        running_kernel = ""
        if uname_result.rc == 0:
            running_kernel = uname_result.stdout.strip()

        node_results.append({
            "hostname": hostname,
            "admin_ip": node_ip,
            "running_kernel": running_kernel,
        })

    versions = set(
        n["running_kernel"] for n in node_results if n["running_kernel"]
    )

    details_lines = []
    for n in node_results:
        details_lines.append(
            f"  {n['hostname']} : {n['running_kernel'] or 'UNREACHABLE'}"
        )
    details_lines.append(f"Unique kernel versions: {len(versions)}")
    for v in sorted(versions):
        details_lines.append(f"  - {v}")

    # If kernel_version_override is configured, check against it
    if is_configured:
        normalized_kvo = _strip_arch_suffix(kvo)
        matched = []
        mismatched = []
        for n in node_results:
            normalized_running = _strip_arch_suffix(n["running_kernel"])
            if normalized_kvo == normalized_running:
                matched.append(n["hostname"])
            else:
                mismatched.append({
                    "hostname": n["hostname"],
                    "expected": kvo,
                    "actual": n["running_kernel"],
                })

        if mismatched:
            details_lines.append(f"Expected kernel: {kvo}")
            for m in mismatched:
                details_lines.append(
                    f"  {m['hostname']} : {m['actual']} — MISMATCH"
                )

        return {
            "success": len(mismatched) == 0 and len(node_results) > 0,
            "nodes": node_results,
            "unique_versions": sorted(versions),
            "kernel_version_override": kvo,
            "is_configured": is_configured,
            "matched": matched,
            "mismatched": mismatched,
            "error": (
                f"{len(mismatched)}/{len(node_results)} nodes do not match kernel override '{kvo}'"
            ) if mismatched else "",
            "details": "\n".join(details_lines),
        }
    else:
        # Auto-select mode: just check all nodes run the same kernel
        return {
            "success": len(versions) == 1 and len(node_results) > 0,
            "nodes": node_results,
            "unique_versions": sorted(versions),
            "kernel_version_override": kvo,
            "is_configured": is_configured,
            "error": (
                f"Found {len(versions)} different kernel versions "
            f"across {len(node_results)} nodes"
        ) if len(versions) != 1 else "",
        "details": "\n".join(details_lines),
    }


# =============================================================================
# VERIFY PER-FUNCTIONAL-GROUP S3 IMAGES MATCH KERNEL OVERRIDE
# =============================================================================

def verify_per_fg_s3_images(host) -> Dict[str, Any]:
    """
    Verify S3 boot images exist per functional group matching the kernel
    override.

    Mirrors omnia's provision/roles/provision_validations/tasks/
    validate_image.yml which validates images per functional group.
    For each functional group in the PXE mapping, checks that S3
    contains both vmlinuz and initramfs files matching the
    kernel_version_override.

    Returns:
        Dict with success, kernel_version_override, groups,
        missing_groups, error, details, not_configured
    """
    kvo_result = get_kernel_version_override(host)
    if not kvo_result["success"]:
        return {
            "success": False,
            "kernel_version_override": "",
            "groups": {},
            "missing_groups": [],
            "error": kvo_result["error"],
            "details": "",
            "not_configured": True,
        }

    kvo = kvo_result["kernel_version_override"]
    if not kvo:
        return {
            "success": True,
            "kernel_version_override": "",
            "groups": {},
            "missing_groups": [],
            "error": "",
            "details": "kernel_version_override not set — auto-select mode",
            "not_configured": True,
        }

    functional_groups = get_functional_groups_from_pxe_mapping(host)
    if not functional_groups:
        return {
            "success": False,
            "kernel_version_override": kvo,
            "groups": {},
            "missing_groups": [],
            "error": "No functional groups found in PXE mapping",
            "details": "",
            "not_configured": False,
        }

    # List all S3 boot images - s3cmd runs on OIM host (ochami server)
    s3_result = host.run("s3cmd ls -Hr s3://boot-images 2>&1")
    if s3_result.rc != 0:
        return {
            "success": False,
            "kernel_version_override": kvo,
            "groups": {},
            "missing_groups": [],
            "error": f"Failed to list S3 boot-images: {s3_result.stderr}",
            "details": "",
            "not_configured": False,
        }

    s3_lines = [
        line.strip() for line in s3_result.stdout.strip().split("\n")
        if line.strip()
    ]

    groups = {}
    missing_groups = []

    for fg in sorted(functional_groups):
        fg_lines = [l for l in s3_lines if fg in l]
        fg_vmlinuz = [l for l in fg_lines if "vmlinuz" in l and kvo in l]
        fg_initramfs = [l for l in fg_lines if "initramfs" in l and kvo in l]

        has_both = len(fg_vmlinuz) > 0 and len(fg_initramfs) > 0
        groups[fg] = {
            "has_vmlinuz": len(fg_vmlinuz) > 0,
            "has_initramfs": len(fg_initramfs) > 0,
            "has_both": has_both,
        }
        if not has_both:
            missing_groups.append(fg)

    details_lines = [f"kernel_version_override: {kvo}"]
    for fg in sorted(groups):
        status = "MATCH" if groups[fg]["has_both"] else "MISSING"
        details_lines.append(f"  {fg} : {status}")

    return {
        "success": len(missing_groups) == 0 and len(groups) > 0,
        "kernel_version_override": kvo,
        "groups": groups,
        "missing_groups": missing_groups,
        "error": (
            f"S3 images missing for {len(missing_groups)} functional groups: "
            + ", ".join(missing_groups)
        ) if missing_groups else "",
        "details": "\n".join(details_lines),
        "not_configured": False,
    }
