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
Discovery Module - Discovery Output Verification Functions.

Functions for verifying discovery playbook output artifacts:
- nodes.yaml generation
- BSS boot templates per functional group
- Cloud-init templates per functional group
"""

from typing import Dict, Any, List

from automation_library.core import (
    run_in_container,
    get_functional_groups_from_pxe_mapping,
)
from ..vars import (
    BSS_BOOT_DIR,
    CLOUDINIT_TEMPLATE_DIR,
)

# Architecture suffixes used in functional group names
_ARCH_SUFFIXES = ("_x86_64", "_aarch64")


def _fg_match_names(fg: str) -> List[str]:
    """
    Return the functional group name AND its '_first' variant.

    Omnia renames the first kube_control_plane node by inserting '_first'
    before the arch suffix.  For example:
      service_kube_control_plane_x86_64 → service_kube_control_plane_first_x86_64

    Returns a list of names to try when matching against template file names.
    """
    variants = [fg]
    for suffix in _ARCH_SUFFIXES:
        if fg.endswith(suffix):
            base = fg[: -len(suffix)]
            variants.append(f"{base}_first{suffix}")
            break
    return variants


# =============================================================================
# BSS TEMPLATE CREATION VERIFICATION
# =============================================================================

def verify_bss_templates_created(host) -> Dict[str, Any]:
    """
    Verify BSS boot templates are created per functional group.

    Checks:
    - BSS_BOOT_DIR exists and contains files
    - Templates exist for functional groups in PXE mapping

    Returns:
        Dict with success, details, error, templates, functional_groups
    """
    results = {
        "success": False,
        "details": "",
        "error": "",
        "templates": [],
        "functional_groups": [],
        "missing_groups": [],
    }

    # Check if BSS boot directory exists
    cmd = run_in_container(
        host,
        f"test -d {BSS_BOOT_DIR} && echo EXISTS || echo NOT_FOUND"
    )
    if cmd.rc != 0 or "NOT_FOUND" in (cmd.stdout or ""):
        results["error"] = f"BSS boot directory not found at {BSS_BOOT_DIR}"
        return results

    # List files in BSS boot directory
    cmd = run_in_container(host, f"ls -1 {BSS_BOOT_DIR}/ 2>/dev/null")
    if cmd.rc != 0 or not cmd.stdout.strip():
        results["error"] = f"No BSS templates found in {BSS_BOOT_DIR}"
        return results

    templates = [f.strip() for f in cmd.stdout.strip().split('\n') if f.strip()]
    results["templates"] = templates

    # Get functional groups from PXE mapping
    functional_groups = get_functional_groups_from_pxe_mapping(host)
    results["functional_groups"] = sorted(functional_groups)

    # Check which functional groups have matching templates
    details_lines = [
        f"BSS boot directory: {BSS_BOOT_DIR}",
        f"Templates found: {len(templates)}",
    ]

    for template in templates:
        details_lines.append(f"  ✓ {template}")

    if functional_groups:
        details_lines.append(f"Functional groups in PXE mapping: {len(functional_groups)}")
        for fg in sorted(functional_groups):
            # Check original name and _first variant (kube_control_plane)
            names_to_try = _fg_match_names(fg)
            matched = any(name in t for t in templates for name in names_to_try)
            matched_name = None
            if matched:
                for name in names_to_try:
                    if any(name in t for t in templates):
                        matched_name = name
                        break
            status = "✓" if matched else "✗"
            if matched_name and matched_name != fg:
                label = f"{fg} (matched as {matched_name})"
            else:
                label = fg
            details_lines.append(f"  {status} {label}")
            if not matched:
                results["missing_groups"].append(fg)

    results["success"] = len(templates) > 0 and len(results["missing_groups"]) == 0
    results["details"] = "\n".join(details_lines)
    return results


# =============================================================================
# CLOUD-INIT TEMPLATE CREATION VERIFICATION
# =============================================================================

def verify_cloudinit_templates_created(host) -> Dict[str, Any]:
    """
    Verify cloud-init templates are created per functional group.

    Checks:
    - CLOUDINIT_TEMPLATE_DIR exists and contains files/directories
    - Templates exist for functional groups in PXE mapping

    Returns:
        Dict with success, details, error, templates, functional_groups
    """
    results = {
        "success": False,
        "details": "",
        "error": "",
        "templates": [],
        "functional_groups": [],
        "missing_groups": [],
    }

    # Check if cloud-init template directory exists
    cmd = run_in_container(
        host,
        f"test -d {CLOUDINIT_TEMPLATE_DIR} && echo EXISTS || echo NOT_FOUND"
    )
    if cmd.rc != 0 or "NOT_FOUND" in (cmd.stdout or ""):
        results["error"] = f"Cloud-init template directory not found at {CLOUDINIT_TEMPLATE_DIR}"
        return results

    # List files/dirs in cloud-init template directory (recursive)
    cmd = run_in_container(
        host,
        f"find {CLOUDINIT_TEMPLATE_DIR} -type f -o -type d 2>/dev/null | sort"
    )
    if cmd.rc != 0 or not cmd.stdout.strip():
        results["error"] = f"No cloud-init templates found in {CLOUDINIT_TEMPLATE_DIR}"
        return results

    all_entries = [f.strip() for f in cmd.stdout.strip().split('\n') if f.strip()]
    # Filter out the root directory itself
    templates = [
        e.replace(f"{CLOUDINIT_TEMPLATE_DIR}/", "")
        for e in all_entries
        if e != CLOUDINIT_TEMPLATE_DIR
    ]
    results["templates"] = templates

    # Get functional groups from PXE mapping
    functional_groups = get_functional_groups_from_pxe_mapping(host)
    results["functional_groups"] = sorted(functional_groups)

    # Check which functional groups have matching templates
    details_lines = [
        f"Cloud-init template directory: {CLOUDINIT_TEMPLATE_DIR}",
        f"Entries found: {len(templates)}",
    ]

    for template in templates:
        details_lines.append(f"  ✓ {template}")

    if functional_groups:
        details_lines.append(f"Functional groups in PXE mapping: {len(functional_groups)}")
        for fg in sorted(functional_groups):
            # Check original name and _first variant (kube_control_plane)
            names_to_try = _fg_match_names(fg)
            matched = any(name in t for t in templates for name in names_to_try)
            matched_name = None
            if matched:
                for name in names_to_try:
                    if any(name in t for t in templates):
                        matched_name = name
                        break
            status = "✓" if matched else "✗"
            if matched_name and matched_name != fg:
                label = f"{fg} (matched as {matched_name})"
            else:
                label = fg
            details_lines.append(f"  {status} {label}")
            if not matched:
                results["missing_groups"].append(fg)

    results["success"] = len(templates) > 0 and len(results["missing_groups"]) == 0
    results["details"] = "\n".join(details_lines)
    return results
