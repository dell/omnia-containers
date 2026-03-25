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
Discovery Module - Additional Packages & Container Images Verification Functions.

Reads additional_packages.json from omnia_core container, extracts RPM packages
and container images per functional group / role, then verifies installation
on discovered nodes via SSH.

Functions:
- get_additional_packages_json_path: Build path to additional_packages.json
- is_additional_packages_enabled: Check if feature is enabled in software_config
- get_allowed_additional_subgroups: Get allowed roles from software_config
- extract_rpm_packages_for_role: Get RPM list for a role
- extract_images_for_role: Get container image list for a role
- verify_additional_packages: Verify RPMs on nodes grouped by functional group
- verify_additional_container_images: Verify images on K8s nodes
"""

import json
from typing import Dict, Any, List, Tuple

from automation_library.core import (
    run_in_container,
    run_on_remote_node,
    get_nodes_info,
    get_functional_groups_from_pxe_mapping,
    load_input_file,
)
from automation_library.core.vars import SOFTWARE_CONFIG_FILE

from ..vars.additional_pkgs_vars import (
    ADDITIONAL_PACKAGES_JSON_TEMPLATE,
    ROLE_SPECIFIC_KEYS,
    IMAGE_ROLE_KEYS,
    CMD_TEMPLATES,
)


# =============================================================================
# CACHE
# =============================================================================

_additional_json_cache: Dict[str, Any] = {}


def clear_additional_pkgs_cache():
    """Clear all caches. Call at start of test run."""
    _additional_json_cache.clear()


# =============================================================================
# CONFIG HELPERS
# =============================================================================

def _get_software_config(host) -> Dict[str, Any]:
    """Load software_config.json from omnia_core container."""
    return load_input_file(host, SOFTWARE_CONFIG_FILE)


def get_additional_packages_json_path(host) -> str:
    """
    Build the path to additional_packages.json inside omnia_core container.

    Reads cluster_os_type and cluster_os_version from software_config.json
    to construct the dynamic path.

    Args:
        host: Testinfra host object

    Returns:
        Full path string, or empty string if software_config is unavailable.
    """
    sw_config = _get_software_config(host)
    if not sw_config:
        return ""

    os_type = sw_config.get("cluster_os_type", "")
    os_version = sw_config.get("cluster_os_version", "")
    if not os_type or not os_version:
        return ""

    # Default to x86_64; extend if aarch64 support is needed
    arch = "x86_64"
    return ADDITIONAL_PACKAGES_JSON_TEMPLATE.format(
        arch=arch, os_type=os_type, os_version=os_version
    )


def is_additional_packages_enabled(host) -> bool:
    """
    Check if additional_packages is enabled in software_config.json.

    Returns True if 'additional_packages' appears in the softwares array.
    """
    sw_config = _get_software_config(host)
    if not sw_config:
        return False
    softwares = sw_config.get("softwares", [])
    return any(sw.get("name") == "additional_packages" for sw in softwares)


def get_allowed_additional_subgroups(host) -> List[str]:
    """
    Get allowed subgroups (roles) from additional_packages array in software_config.json.

    Returns:
        List of role name strings (e.g. ["slurm_control_node", "service_kube_node"]).
    """
    sw_config = _get_software_config(host)
    if not sw_config:
        return []
    additional_packages_list = sw_config.get("additional_packages", [])
    return [item.get("name") for item in additional_packages_list if item.get("name")]


def _load_additional_json(host) -> Dict[str, Any]:
    """
    Load and cache additional_packages.json from omnia_core container.

    Returns:
        Parsed JSON dict, or empty dict on failure.
    """
    cache_key = "additional_packages_json"
    if cache_key in _additional_json_cache:
        return _additional_json_cache[cache_key]

    json_path = get_additional_packages_json_path(host)
    if not json_path:
        _additional_json_cache[cache_key] = {}
        return {}

    cmd = run_in_container(host, f"cat '{json_path}' 2>/dev/null")
    if cmd.rc != 0 or not cmd.stdout.strip():
        _additional_json_cache[cache_key] = {}
        return {}

    try:
        data = json.loads(cmd.stdout.strip())
    except json.JSONDecodeError:
        data = {}

    _additional_json_cache[cache_key] = data
    return data


# =============================================================================
# EXTRACTION HELPERS
# =============================================================================

def _strip_arch_suffix(functional_group: str) -> str:
    """Strip _x86_64 or _aarch64 suffix to get base role name."""
    return functional_group.replace("_x86_64", "").replace("_aarch64", "")


def _normalize_kube_control_plane_role(host, functional_group: str) -> str:
    """
    Normalize kube control plane role based on node count.
    
    Logic:
    - If only 1 kube control plane node exists: treat as 'service_kube_control_plane_first'
    - If multiple kube control plane nodes exist:
        - 1st node: 'service_kube_control_plane_first'
        - Other nodes: 'service_kube_control_plane'
    
    Args:
        host: Testinfra host object
        functional_group: Full functional group name (e.g., "service_kube_control_plane_x86_64")
    
    Returns:
        Normalized role name for looking up in additional_packages.json
    """
    role_name = _strip_arch_suffix(functional_group)
    
    # Only apply logic to kube control plane roles
    if role_name not in ["service_kube_control_plane", "service_kube_control_plane_first"]:
        return role_name
    
    # Get all kube control plane nodes (both first and regular)
    all_kube_cp_groups = [
        fg for fg in get_functional_groups_from_pxe_mapping(host)
        if _strip_arch_suffix(fg) in ["service_kube_control_plane", "service_kube_control_plane_first"]
    ]
    
    if not all_kube_cp_groups:
        return role_name
    
    # Get all nodes across all kube control plane groups
    all_kube_cp_nodes = []
    for fg in all_kube_cp_groups:
        nodes = get_nodes_info(host, search_by="functional_group", search_value=fg)
        all_kube_cp_nodes.extend(nodes)
    
    # Sort by hostname to ensure consistent ordering
    all_kube_cp_nodes.sort(key=lambda n: n.get("hostname", ""))
    
    total_kube_cp_nodes = len(all_kube_cp_nodes)
    
    # If only 1 node total, it should be treated as 'first'
    if total_kube_cp_nodes == 1:
        return "service_kube_control_plane_first"
    
    # If multiple nodes, determine if current functional_group contains the first node
    if total_kube_cp_nodes > 1:
        first_node_hostname = all_kube_cp_nodes[0].get("hostname", "")
        current_nodes = get_nodes_info(host, search_by="functional_group", search_value=functional_group)
        
        # Check if the first node is in the current functional group
        for node in current_nodes:
            if node.get("hostname") == first_node_hostname:
                return "service_kube_control_plane_first"
        
        # Otherwise, treat as regular control plane
        return "service_kube_control_plane"
    
    return role_name


def extract_rpm_packages_for_role(
    host, functional_group: str
) -> Tuple[List[str], List[str]]:
    """
    Extract RPM package names for a functional group from additional_packages.json.

    Returns both global packages (additional_packages.cluster[]) and
    role-specific packages (<role>.cluster[]).

    Args:
        host: Testinfra host object
        functional_group: Full functional group name (e.g. "slurm_node_x86_64")

    Returns:
        Tuple of (global_packages, role_packages) — both are lists of package name strings.
    """
    data = _load_additional_json(host)
    if not data:
        return [], []

    role_name = _strip_arch_suffix(functional_group)
    # Use normalized role for kube control plane to handle first vs regular logic
    normalized_role = _normalize_kube_control_plane_role(host, functional_group)

    # Global RPMs from additional_packages.cluster[]
    global_cluster = data.get("additional_packages", {}).get("cluster", [])
    global_rpms = [
        item["package"] for item in global_cluster
        if item.get("type") == "rpm" and item.get("package")
    ]

    # Role-specific RPMs from <normalized_role>.cluster[]
    # Use normalized role for kube control plane to handle first vs regular logic
    role_rpms = []
    if normalized_role in ROLE_SPECIFIC_KEYS and normalized_role in data:
        role_cluster = data[normalized_role].get("cluster", [])
        role_rpms = [
            item["package"] for item in role_cluster
            if item.get("type") == "rpm" and item.get("package")
        ]

    return global_rpms, role_rpms


def extract_images_for_role(
    host, functional_group: str
) -> Tuple[List[Dict[str, str]], List[Dict[str, str]]]:
    """
    Extract container image entries for a functional group from additional_packages.json.

    Only IMAGE_ROLE_KEYS (Kubernetes roles) receive container images.
    For non-K8s roles (e.g., Slurm), returns empty lists.

    Args:
        host: Testinfra host object
        functional_group: Full functional group name

    Returns:
        Tuple of (global_images, role_images).
        Each image is a dict with keys: package, tag/digest, pull_ref.
        Returns ([], []) for non-K8s roles.
    """
    data = _load_additional_json(host)
    if not data:
        return [], []

    role_name = _strip_arch_suffix(functional_group)
    normalized_role = _normalize_kube_control_plane_role(host, functional_group)

    # Only K8s roles get container images - but we still return empty lists for non-K8s
    if role_name not in IMAGE_ROLE_KEYS:
        return [], []

    def _extract_images(cluster_items):
        images = []
        if not cluster_items or not isinstance(cluster_items, list):
            return images
        for item in cluster_items:
            if item.get("type") == "image" and item.get("package"):
                entry = {"package": item["package"]}
                if item.get("digest"):
                    entry["digest"] = item["digest"]
                    entry["pull_ref"] = f"{item['package']}@{item['digest']}"
                else:
                    tag = item.get("tag", "latest")
                    entry["tag"] = tag
                    entry["pull_ref"] = f"{item['package']}:{tag}"
                images.append(entry)
        return images

    # Global images from additional_packages.cluster[]
    global_cluster = data.get("additional_packages", {}).get("cluster", [])
    global_images = _extract_images(global_cluster)

    # Role-specific images from <normalized_role>.cluster[]
    # Use normalized role for kube control plane to handle first vs regular logic
    role_images = []
    if normalized_role in ROLE_SPECIFIC_KEYS and normalized_role in data:
        role_cluster = data[normalized_role].get("cluster", [])
        role_images = _extract_images(role_cluster)

    return global_images, role_images


# =============================================================================
# NODE-LEVEL VERIFICATION HELPERS
# =============================================================================

def _check_rpm_on_node(host, admin_ip: str, package: str) -> Dict[str, Any]:
    """Check if an RPM package is installed on a remote node."""
    cmd_str = CMD_TEMPLATES["rpm_query"].format(package=package)
    cmd = run_on_remote_node(host, cmd_str, admin_ip)
    installed = cmd.rc == 0 and "not installed" not in cmd.stdout.lower()
    return {
        "package": package,
        "installed": installed,
        "output": cmd.stdout.strip(),
        "error": "" if installed else cmd.stdout.strip() or cmd.stderr.strip(),
    }


def _check_image_on_node(host, admin_ip: str, image_entry: Dict[str, str]) -> Dict[str, Any]:
    """
    Check if a container image is present on a remote K8s node.

    First tries crictl images (CRI-O runtime), falls back to podman images.
    Matches by image name (package field).
    """
    pull_ref = image_entry.get("pull_ref", "")
    package = image_entry.get("package", "")
    tag = image_entry.get("tag", "")

    # Try crictl first (K8s nodes use CRI-O)
    cmd = run_on_remote_node(host, CMD_TEMPLATES["crictl_image_check"], admin_ip)
    if cmd.rc == 0 and cmd.stdout.strip():
        try:
            crictl_data = json.loads(cmd.stdout.strip())
            crictl_images = crictl_data.get("images", [])
            for img in crictl_images:
                repo_tags = img.get("repoTags", [])
                repo_digests = img.get("repoDigests", [])
                all_refs = repo_tags + repo_digests
                for ref in all_refs:
                    if package in ref:
                        return {
                            "pull_ref": pull_ref,
                            "present": True,
                            "matched_ref": ref,
                            "error": "",
                        }
        except json.JSONDecodeError:
            pass

    # Fallback to podman
    cmd = run_on_remote_node(host, CMD_TEMPLATES["podman_image_check"], admin_ip)
    if cmd.rc == 0 and package in cmd.stdout:
        return {
            "pull_ref": pull_ref,
            "present": True,
            "matched_ref": package,
            "error": "",
        }

    return {
        "pull_ref": pull_ref,
        "present": False,
        "matched_ref": "",
        "error": f"Image {pull_ref} not found on node",
    }


# =============================================================================
# MAIN VERIFICATION FUNCTIONS
# =============================================================================

def verify_additional_packages(host) -> Dict[str, Any]:
    """
    Verify additional RPM packages are installed on all nodes.

    Reads additional_packages.json from omnia_core container, determines
    which packages should be on each functional group, then checks via
    rpm -q on each node (SSH via omnia_core).

    Results are grouped by functional group.

    Returns:
        Dict with success, skipped, details, error, results_by_group.
    """
    if not is_additional_packages_enabled(host):
        return {
            "success": True,
            "skipped": True,
            "reason": "additional_packages not enabled in software_config.json",
            "results_by_group": {},
            "error": "",
        }

    allowed_subgroups = get_allowed_additional_subgroups(host)
    if not allowed_subgroups:
        return {
            "success": True,
            "skipped": True,
            "reason": "No subgroups defined in additional_packages array of software_config.json",
            "results_by_group": {},
            "error": "",
        }

    data = _load_additional_json(host)
    if not data:
        json_path = get_additional_packages_json_path(host)
        return {
            "success": False,
            "skipped": False,
            "reason": "",
            "results_by_group": {},
            "error": f"Failed to load additional_packages.json from {json_path}",
        }

    functional_groups = get_functional_groups_from_pxe_mapping(host)
    if not functional_groups:
        return {
            "success": False,
            "skipped": False,
            "reason": "",
            "results_by_group": {},
            "error": "No functional groups found in PXE mapping",
        }

    results_by_group = {}
    all_success = True
    total_packages_checked = 0
    total_missing = 0

    for fg in sorted(functional_groups):
        role_name = _strip_arch_suffix(fg)
        if role_name not in allowed_subgroups:
            continue

        global_rpms, role_rpms = extract_rpm_packages_for_role(host, fg)
        all_rpms = list(dict.fromkeys(global_rpms + role_rpms))  # dedupe, preserve order

        if not all_rpms:
            results_by_group[fg] = {
                "packages_expected": [],
                "nodes": [],
                "skipped": True,
                "reason": f"No RPM packages defined for {role_name}",
            }
            continue

        nodes = get_nodes_info(host, search_by="functional_group", search_value=fg)
        if not nodes:
            continue

        node_results = []
        for node in nodes:
            hostname = node.get("hostname", "")
            admin_ip = node.get("admin_ip", "")

            if not admin_ip:
                node_results.append({
                    "hostname": hostname,
                    "admin_ip": "",
                    "packages": {},
                    "missing": all_rpms,
                    "error": "No admin_ip",
                })
                all_success = False
                total_missing += len(all_rpms)
                continue

            pkg_results = {}
            missing = []
            for pkg in all_rpms:
                check = _check_rpm_on_node(host, admin_ip, pkg)
                pkg_results[pkg] = check["installed"]
                total_packages_checked += 1
                if not check["installed"]:
                    missing.append(pkg)
                    total_missing += 1

            if missing:
                all_success = False

            node_results.append({
                "hostname": hostname,
                "admin_ip": admin_ip,
                "packages": pkg_results,
                "missing": missing,
                "error": "" if not missing else f"Missing: {', '.join(missing)}",
            })

        results_by_group[fg] = {
            "packages_expected": all_rpms,
            "nodes": node_results,
            "skipped": False,
            "reason": "",
        }

    return {
        "success": all_success,
        "skipped": False,
        "reason": "",
        "total_packages_checked": total_packages_checked,
        "total_missing": total_missing,
        "results_by_group": results_by_group,
        "error": "" if all_success else f"{total_missing} package(s) missing across nodes",
    }


def verify_additional_container_images(host) -> Dict[str, Any]:
    """
    Verify additional container images are present on K8s nodes.

    Reads additional_packages.json from omnia_core container, extracts
    container image entries for IMAGE_ROLE_KEYS, then checks via
    crictl/podman on each K8s node.

    Results are grouped by functional group.

    Returns:
        Dict with success, skipped, details, error, results_by_group.
    """
    if not is_additional_packages_enabled(host):
        return {
            "success": True,
            "skipped": True,
            "reason": "additional_packages not enabled in software_config.json",
            "results_by_group": {},
            "error": "",
        }

    allowed_subgroups = get_allowed_additional_subgroups(host)
    if not allowed_subgroups:
        return {
            "success": True,
            "skipped": True,
            "reason": "No subgroups defined in additional_packages array of software_config.json",
            "results_by_group": {},
            "error": "",
        }

    data = _load_additional_json(host)
    if not data:
        json_path = get_additional_packages_json_path(host)
        return {
            "success": False,
            "skipped": False,
            "reason": "",
            "results_by_group": {},
            "error": f"Failed to load additional_packages.json from {json_path}",
        }

    functional_groups = get_functional_groups_from_pxe_mapping(host)
    if not functional_groups:
        return {
            "success": False,
            "skipped": False,
            "reason": "",
            "results_by_group": {},
            "error": "No functional groups found in PXE mapping",
        }

    results_by_group = {}
    all_success = True
    total_images_checked = 0
    total_missing = 0

    for fg in sorted(functional_groups):
        role_name = _strip_arch_suffix(fg)

        # Skip if role not in allowed subgroups
        if role_name not in allowed_subgroups:
            continue

        # Check if this is a K8s role that should have images
        is_k8s_role = role_name in IMAGE_ROLE_KEYS

        global_images, role_images = extract_images_for_role(host, fg)
        # Deduplicate by pull_ref
        seen = set()
        all_images = []
        for img in global_images + role_images:
            if img["pull_ref"] not in seen:
                all_images.append(img)
                seen.add(img["pull_ref"])

        # For non-K8s roles (e.g., Slurm), show them with "no images present" message
        if not is_k8s_role:
            nodes = get_nodes_info(host, search_by="functional_group", search_value=fg)
            node_results = []
            for node in nodes:
                node_results.append({
                    "hostname": node.get("hostname", ""),
                    "admin_ip": node.get("admin_ip", ""),
                    "images": {},
                    "missing": [],
                    "error": "",
                    "note": "No container images expected for this role",
                })
            results_by_group[fg] = {
                "images_expected": [],
                "nodes": node_results,
                "skipped": False,
                "reason": f"Non-K8s role - no container images expected",
                "is_k8s_role": False,
            }
            continue

        # For K8s roles with no images defined
        if not all_images:
            results_by_group[fg] = {
                "images_expected": [],
                "nodes": [],
                "skipped": True,
                "reason": f"No container images defined for {role_name}",
                "is_k8s_role": True,
            }
            continue

        nodes = get_nodes_info(host, search_by="functional_group", search_value=fg)
        if not nodes:
            continue

        node_results = []
        for node in nodes:
            hostname = node.get("hostname", "")
            admin_ip = node.get("admin_ip", "")

            if not admin_ip:
                node_results.append({
                    "hostname": hostname,
                    "admin_ip": "",
                    "images": {},
                    "missing": [img["pull_ref"] for img in all_images],
                    "error": "No admin_ip",
                })
                all_success = False
                total_missing += len(all_images)
                continue

            img_results = {}
            missing = []
            for img in all_images:
                check = _check_image_on_node(host, admin_ip, img)
                img_results[img["pull_ref"]] = check["present"]
                total_images_checked += 1
                if not check["present"]:
                    missing.append(img["pull_ref"])
                    total_missing += 1

            if missing:
                all_success = False

            node_results.append({
                "hostname": hostname,
                "admin_ip": admin_ip,
                "images": img_results,
                "missing": missing,
                "error": "" if not missing else f"Missing: {', '.join(missing)}",
            })

        results_by_group[fg] = {
            "images_expected": [img["pull_ref"] for img in all_images],
            "nodes": node_results,
            "skipped": False,
            "reason": "",
            "is_k8s_role": True,
        }

    # If no K8s groups were processed at all, skip
    if not results_by_group:
        return {
            "success": True,
            "skipped": True,
            "reason": "No K8s functional groups found in PXE mapping for image verification",
            "results_by_group": {},
            "error": "",
        }

    return {
        "success": all_success,
        "skipped": False,
        "reason": "",
        "total_images_checked": total_images_checked,
        "total_missing": total_missing,
        "results_by_group": results_by_group,
        "error": "" if all_success else f"{total_missing} image(s) missing across nodes",
    }
