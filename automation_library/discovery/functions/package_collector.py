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
Discovery Module - Package Collector.

Collects expected package lists per functional group using the same logic
as build_image_x86_64 playbook:

1. Read all functional groups from PXE mapping file (dynamic, no hardcoding)
2. For each functional group, find the matching image YAML in IMAGE_CONFIG_YAML_DIR
   (rhel-<functional_group>_<uuid>-image-build-10.0.yaml)
3. Read base image YAML (rhel-<arch>_base-10.0.yaml)
4. Combine base packages + compute packages (deduplicated) - same as build_image
5. Return per-functional-group package lists for node verification

Uses load_container_file from core (caching + YAML parsing, no raw cat ops).
Uses get_functional_groups_from_pxe_mapping from core (reads PXE CSV from container).
"""

from typing import Dict, List, Set

from automation_library.core import (
    run_in_container,
    load_container_file,
    get_functional_groups_from_pxe_mapping,
)

from ..vars import IMAGE_CONFIG_YAML_DIR


# =============================================================================
# BASE IMAGE PACKAGES
# =============================================================================

def get_base_image_packages(host, arch: str = "x86_64") -> List[str]:
    """
    Get packages from base image YAML inside omnia_core container.

    Mirrors _get_base_image_packages() from build_image_func.py exactly.
    Base image YAML: rhel-<arch>_base-10.0.yaml in IMAGE_CONFIG_YAML_DIR.
    Uses load_container_file (core utility - caching + YAML parsing, no cat).

    Args:
        host: Testinfra host object
        arch: Architecture string (x86_64 or aarch64)

    Returns:
        List of package names from base image YAML, empty list if not found
    """
    base_yaml = f"{IMAGE_CONFIG_YAML_DIR}/rhel-{arch}_base-10.0.yaml"
    config = load_container_file(host, base_yaml)
    return config.get("packages", [])


# =============================================================================
# FUNCTIONAL GROUP → IMAGE YAML MAPPING
# =============================================================================

def get_image_yaml_path_for_group(host, functional_group: str) -> str:
    """
    Find the absolute path of the image YAML for a given functional group.

    Image YAML naming pattern inside IMAGE_CONFIG_YAML_DIR:
        rhel-<functional_group>_<uuid>-image-build-10.0.yaml

    Uses bash glob + grep inside container (same approach as build_image_func.py
    _verify_single_image_packages). Returns empty string if not found.

    Args:
        host: Testinfra host object
        functional_group: e.g. slurm_control_node_x86_64

    Returns:
        Absolute path string, or empty string if no YAML found
    """
    cmd = run_in_container(
        host,
        f"bash -c 'ls -1 {IMAGE_CONFIG_YAML_DIR}/*.yaml 2>/dev/null"
        f" | grep \"{functional_group}\" | head -1'"
    )
    if cmd.rc != 0 or not cmd.stdout.strip():
        return ""
    return cmd.stdout.strip()


def get_image_packages_for_group(host, functional_group: str) -> List[str]:
    """
    Get compute packages from the image YAML of a functional group.

    Finds the image YAML via get_image_yaml_path_for_group, then reads it
    with load_container_file (no cat, caching handled by core).

    Args:
        host: Testinfra host object
        functional_group: e.g. slurm_control_node_x86_64

    Returns:
        List of package names, empty list if YAML not found
    """
    yaml_path = get_image_yaml_path_for_group(host, functional_group)
    if not yaml_path:
        return []
    config = load_container_file(host, yaml_path)
    return config.get("packages", [])


# =============================================================================
# COMBINED PACKAGE LIST (base + compute, same as build_image)
# =============================================================================

def get_packages_for_functional_group(
    host,
    functional_group: str,
    base_packages: List[str],
) -> List[str]:
    """
    Get deduplicated expected package list for a functional group.

    Combines base image packages + functional group compute packages,
    exactly as build_image_func.py does in _verify_single_image_packages():
        all_expected = list(dict.fromkeys(base_packages + compute_packages))

    Args:
        host: Testinfra host object
        functional_group: e.g. slurm_control_node_x86_64
        base_packages: Packages from base image YAML (common to all nodes)

    Returns:
        Deduplicated list of expected package names (base first, then compute)
    """
    compute_packages = get_image_packages_for_group(host, functional_group)
    return list(dict.fromkeys(base_packages + compute_packages))


# =============================================================================
# COLLECT ALL FUNCTIONAL GROUPS FROM PXE MAPPING
# =============================================================================

def get_all_functional_groups(host) -> Set[str]:
    """
    Get all unique functional groups present in the PXE mapping file.

    Uses get_functional_groups_from_pxe_mapping from core (reads the PXE
    mapping CSV from inside omnia_core container dynamically).
    No hardcoding - reflects exactly what is provisioned.

    Args:
        host: Testinfra host object

    Returns:
        Set of functional group strings (e.g. {'slurm_control_node_x86_64', ...})
    """
    return get_functional_groups_from_pxe_mapping(host)


# =============================================================================
# BUILD COMPLETE PACKAGE MAP FOR ALL FUNCTIONAL GROUPS
# =============================================================================

def build_package_map(host) -> Dict[str, List[str]]:
    """
    Build a complete package map for all functional groups in the PXE mapping.

    Steps (mirrors build_image_x86_64 playbook):
    1. Read all functional groups dynamically from PXE mapping (no hardcoding)
    2. Determine architecture from functional group names
    3. Read base image YAML packages (common to all nodes)
    4. For each functional group, find its image YAML and read packages
    5. Combine base + compute packages (deduplicated)

    Uses load_container_file (no raw cat) and get_functional_groups_from_pxe_mapping
    from core. Caching is handled by core's load_container_file.

    Args:
        host: Testinfra host object

    Returns:
        Dict mapping functional_group -> List[str] of expected package names
        Empty list for any group whose image YAML was not found.

    Example:
        {
            "slurm_control_node_x86_64": ["munge", "firewalld", "slurm-slurmctld", ...],
            "slurm_node_x86_64": ["munge", "firewalld", ...],
            "service_kube_control_plane_first_x86_64": [...],
        }
    """
    functional_groups = get_all_functional_groups(host)
    if not functional_groups:
        return {}

    # Determine arch: if any aarch64 group present, handle separately
    # For mixed environments, base image is read per arch
    x86_groups = [fg for fg in functional_groups if "aarch64" not in fg]
    aarch64_groups = [fg for fg in functional_groups if "aarch64" in fg]

    # Read base packages per arch (cached by load_container_file)
    x86_base = get_base_image_packages(host, "x86_64") if x86_groups else []
    aarch64_base = get_base_image_packages(host, "aarch64") if aarch64_groups else []

    package_map: Dict[str, List[str]] = {}

    for fg in x86_groups:
        package_map[fg] = get_packages_for_functional_group(host, fg, x86_base)

    for fg in aarch64_groups:
        package_map[fg] = get_packages_for_functional_group(host, fg, aarch64_base)

    return package_map
