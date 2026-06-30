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
Build Image - Core Functions.

This module contains all functions for running prechecks and validations
for build_image automation.

Functions:
- Precheck: S3 containers running
- Validation: functional_groups_config.yml content
- Validation: S3 bucket images pushed

Usage:
    from automation_library.build_image.functions.build_image_func import (
        check_s3_containers,
        check_functional_group_file_exists,
        check_functional_group_content,
        check_s3_bucket_images,
    )

"""

from typing import Dict, Any, Optional

import yaml as pyyaml

from automation_library.core import (
    run_in_container,
    check_container_running as _core_check_container,
    get_functional_groups_from_pxe_mapping,
    get_group_names_from_pxe_mapping,
    get_nodes_info,
)

from ..vars.build_image_vars import (
    BUILD_IMAGE_VARS,
    S3_CONTAINERS,
    get_pxe_mapping_filename,
)
from ..messages.build_image_msgs import BUILD_IMAGE_MSGS, TEST_LOG_MSGS
from .build_stream_job_func import (
    is_build_stream_enabled,
    get_last_build_image_job_id,
)
from automation_library.build_stream.functions.db_func import (
    get_image_groups_for_job,
)


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def _filter_functional_groups_by_arch(functional_groups: list, arch: str) -> list:
    """
    Filter functional groups by architecture.

    Args:
        functional_groups: list of all functional groups from pxe_mapping
        arch: Architecture to filter by (x86_64 or aarch64)

    Returns:
        List of functional groups matching the specified architecture
    """
    if not functional_groups or not arch:
        return list(functional_groups) if functional_groups else []

    return [fg for fg in functional_groups if arch in fg]


def _get_adjusted_functional_groups(host, functional_groups: list) -> list:
    """
    Adjust functional groups list based on control plane node count.

    Logic (x86_64 only - k8s cluster not supported on aarch64):
    - Single control plane node: only service_kube_control_plane_first_x86_64 exists
    - Multiple control plane nodes: both first and non-first exist

    Args:
        host: testinfra host object
        functional_groups: list of functional groups from pxe_mapping

    Returns:
        Adjusted list of functional groups to verify
    """
    if not functional_groups:
        return functional_groups

    # K8s cluster only supported on x86_64, skip adjustment for aarch64
    control_plane_fg = "service_kube_control_plane_x86_64"
    control_plane_first_fg = "service_kube_control_plane_first_x86_64"

    # If no x86_64 control plane in functional groups, return as-is
    if control_plane_fg not in functional_groups:
        return functional_groups

    # Count control plane nodes using core module's get_nodes_info
    nodes = get_nodes_info(host, search_by="functional_group", search_value=control_plane_fg)
    control_plane_count = len(nodes)

    # Adjust groups based on control plane count
    adjusted_groups = list(functional_groups)
    if control_plane_count == 1:
        # Single control plane: replace service_kube_control_plane with _first version
        adjusted_groups.remove(control_plane_fg)
        adjusted_groups.append(control_plane_first_fg)
    elif control_plane_count > 1:
        # Multiple control planes: need both first and non-first
        if control_plane_first_fg not in adjusted_groups:
            adjusted_groups.append(control_plane_first_fg)

    return adjusted_groups


# =============================================================================
# CONTAINER VERIFICATION FUNCTIONS (PRECHECK)
# =============================================================================

def check_container_running(host, container_name: str) -> Dict[str, Any]:
    """Check if a specific container is running. Delegates to core."""
    return _core_check_container(host, container_name)


def check_s3_containers(host) -> Dict[str, Any]:
    """
    Check all S3 containers are running (PRECHECK).

    Args:
        host: testinfra host object

    Returns:
        Dict with 'success', 'results', 'passed', 'failed', 'details'
    """
    results = []
    passed = 0
    failed = 0

    for container in S3_CONTAINERS:
        result = check_container_running(host, container)
        results.append({
            "container": container,
            "success": result["success"],
            "status": result["status"],
            "error": result["error"]
        })
        if result["success"]:
            passed += 1
        else:
            failed += 1

    total = len(S3_CONTAINERS)
    return {
        "success": failed == 0,
        "results": results,
        "passed": passed,
        "failed": failed,
        "total": total,
        "details": f"{passed}/{total} S3 containers running"
    }


# =============================================================================
# FUNCTIONAL GROUP VALIDATION FUNCTIONS
# =============================================================================

def check_functional_group_file_exists(host) -> Dict[str, Any]:
    """
    Check if functional_groups_config.yml file exists inside omnia_core container.

    Args:
        host: testinfra host object

    Returns:
        Dict with 'success', 'status', 'details', 'error'
    """
    file_path = BUILD_IMAGE_VARS["functional_group_file_path"]
    cmd = run_in_container(
        host, f"test -f {file_path} && echo 'EXISTS' || echo 'NOT_FOUND'"
    )

    if cmd.rc == 0 and "EXISTS" in cmd.stdout:
        return {
            "success": True,
            "status": "exists",
            "details": f"functional_groups_config.yml found at {file_path}",
            "error": None
        }

    return {
        "success": False,
        "status": "not_found",
        "details": None,
        "error": (
            f"functional_groups_config.yml not found at {file_path} inside omnia_core container"
        )
    }


def check_functional_group_content(host, arch: str = None) -> Dict[str, Any]:
    """
    Validate functional_groups_config.yml contains all roles and groups from pxe_mapping.

    Args:
        host: testinfra host object
        arch: Architecture to filter by (x86_64 or aarch64). If None, checks all.

    Returns:
        Dict with 'success', 'status', 'details', 'error', 'missing_groups', 'found_groups'
    """
    file_path = BUILD_IMAGE_VARS["functional_group_file_path"]

    # Get expected functional groups from pxe_mapping file inside container
    raw_functional_groups = get_functional_groups_from_pxe_mapping(host)
    # Filter by architecture if specified
    if arch:
        raw_functional_groups = _filter_functional_groups_by_arch(raw_functional_groups, arch)
    expected_functional_groups = _get_adjusted_functional_groups(host, raw_functional_groups)
    expected_group_names = get_group_names_from_pxe_mapping(host)

    if not expected_functional_groups:
        return {
            "success": False,
            "status": "no_expected_groups",
            "details": None,
            "error": f"No functional groups found in {get_pxe_mapping_filename()}",
            "missing_groups": [],
            "found_groups": []
        }

    # Read functional_groups_config.yml content from container
    cmd = run_in_container(host, f"cat {file_path}")

    if cmd.rc != 0:
        return {
            "success": False,
            "status": "read_failed",
            "details": None,
            "error": f"Failed to read {file_path}: {cmd.stderr}",
            "missing_groups": list(expected_functional_groups),
            "found_groups": []
        }

    content = cmd.stdout

    # Check for each functional group in the file content
    missing_functional_groups = []
    found_functional_groups = []

    for fg in expected_functional_groups:
        if fg in content:
            found_functional_groups.append(fg)
        else:
            missing_functional_groups.append(fg)

    # Check for each group name in the file content
    missing_group_names = []
    found_group_names = []

    for grp in expected_group_names:
        if grp in content:
            found_group_names.append(grp)
        else:
            missing_group_names.append(grp)

    all_found = len(missing_functional_groups) == 0 and len(missing_group_names) == 0

    if all_found:
        return {
            "success": True,
            "status": "valid",
            "details": (
                f"functional_groups_config.yml contains all {len(expected_functional_groups)} "
                f"functional groups and {len(expected_group_names)} group names"
            ),
            "error": None,
            "missing_functional_groups": [],
            "found_functional_groups": found_functional_groups,
            "missing_group_names": [],
            "found_group_names": found_group_names
        }

    error_parts = []
    if missing_functional_groups:
        error_parts.append(f"Missing functional groups: {', '.join(missing_functional_groups)}")
    if missing_group_names:
        error_parts.append(f"Missing group names: {', '.join(missing_group_names)}")

    return {
        "success": False,
        "status": "incomplete",
        "details": (
            f"Found {len(found_functional_groups)}/{len(expected_functional_groups)} "
            f"functional groups, {len(found_group_names)}/{len(expected_group_names)} group names"
        ),
        "error": "; ".join(error_parts),
        "missing_functional_groups": missing_functional_groups,
        "found_functional_groups": found_functional_groups,
        "missing_group_names": missing_group_names,
        "found_group_names": found_group_names
    }


# =============================================================================
# REGCTL REGISTRY VALIDATION FUNCTIONS
# =============================================================================

def check_regctl_registry_images(host, arch: str = "x86_64") -> Dict[str, Any]:
    """
    Validate that base and compute images are available in the regctl registry.
    Uses: regctl repo ls <hostname>:5000

    Expected images:
    - rhel-<arch>_base (always required)
    - rhel-<functional_group> for each group from pxe_mapping

    Args:
        host: testinfra host object
        arch: Architecture string (x86_64 or aarch64)

    Returns:
        Dict with 'success', 'status', 'details', 'error', 'found_images', 'missing_images'
    """
    # Get hostname dynamically
    hostname_cmd = host.run("hostname")
    if hostname_cmd.rc != 0:
        return {
            "success": False,
            "status": "hostname_failed",
            "details": None,
            "error": f"Failed to get hostname: {hostname_cmd.stderr}",
            "found_images": [],
            "missing_images": []
        }

    hostname = hostname_cmd.stdout.strip()
    registry_url = f"{hostname}:5000"

    # Get functional groups from pxe_mapping file inside container, filtered by arch
    raw_functional_groups = get_functional_groups_from_pxe_mapping(host)
    filtered_groups = _filter_functional_groups_by_arch(raw_functional_groups, arch)
    functional_groups = _get_adjusted_functional_groups(host, filtered_groups)

    # Build expected images list (without hostname prefix for display)
    expected_images = [f"rhel-{arch}_base"]  # Base image always required
    for fg in functional_groups:
        expected_images.append(f"rhel-{fg}")

    # Run regctl repo ls command
    regctl_cmd = host.run(f"regctl repo ls {registry_url} 2>/dev/null")

    if regctl_cmd.rc != 0:
        return {
            "success": False,
            "status": "regctl_failed",
            "details": None,
            "error": (
                f"Failed to list registry images: {regctl_cmd.stderr or 'regctl command failed'}"
            ),
            "found_images": [],
            "missing_images": expected_images,
            "registry_url": registry_url
        }

    registry_content = regctl_cmd.stdout

    # Check for each expected image
    found_images = []
    missing_images = []

    for img in expected_images:
        if img in registry_content:
            found_images.append(img)
        else:
            missing_images.append(img)

    if not missing_images:
        return {
            "success": True,
            "status": "all_found",
            "details": f"All {len(found_images)} images found in registry {registry_url}",
            "error": None,
            "found_images": found_images,
            "missing_images": [],
            "registry_url": registry_url
        }

    return {
        "success": False,
        "status": "missing_images",
        "details": f"Found {len(found_images)}/{len(expected_images)} images in registry",
        "error": f"Missing images: {', '.join(missing_images)}",
        "found_images": found_images,
        "missing_images": missing_images,
        "registry_url": registry_url
    }


# =============================================================================
# S3 BUCKET VALIDATION FUNCTIONS
# =============================================================================

def _format_size(size_bytes: int) -> str:
    """Format bytes to human-readable size."""
    if size_bytes >= 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024 * 1024):.1f} GB"
    if size_bytes >= 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.1f} MB"
    if size_bytes >= 1024:
        return f"{size_bytes / 1024:.1f} KB"
    return f"{size_bytes} B"


def _parse_human_size(size_str: str) -> int:
    """Parse human-readable size (e.g., 72M, 1326M, 15K, 1.3G) to bytes."""
    size_str = size_str.strip().upper()
    multipliers = {'K': 1024, 'M': 1024 * 1024, 'G': 1024 * 1024 * 1024, 'T': 1024 ** 4}
    if size_str[-1] in multipliers:
        return int(float(size_str[:-1]) * multipliers[size_str[-1]])
    return int(size_str)


def _parse_s3_listing(s3_output: str) -> Dict[str, Any]:
    """
    Parse `s3cmd ls -Hr` output into a dict keyed by full S3 path.

    Format per line: "DATE TIME  SIZE  s3://bucket/path"
    Returns: {"s3://...": {"size": int, "filename": str}}
    """
    s3_files = {}
    for line in s3_output.strip().split("\n"):
        if not line.strip():
            continue
        parts = line.split()
        if len(parts) >= 4:
            try:
                size = _parse_human_size(parts[2])
                path = parts[3]
                filename = path.split("/")[-1]
                s3_files[path] = {"size": size, "filename": filename}
            except (ValueError, IndexError):
                pass
    return s3_files


def _match_s3_images_for_group(
    fg: str,
    image_types: list,
    s3_files: Dict[str, Any],
    job_id: Optional[str] = None,
    image_group_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Find all required image types for one functional group in the S3 listing.

    When build_stream is enabled the S3 directory name embeds both the job
    UUID and the image_group_id from the postgres ``image_groups`` table::

        s3://boot-images/<fg>/rhel-<fg>_..._<job_id>-<image_group_id>/<files>

    We build a precise segment ``<job_id>-<image_group_id>`` to match.
    If we only have the job_id (no image_group_id), we fall back to
    matching the job_id alone.

    When build_stream is disabled any path containing ``<fg>`` and the
    image type keyword is accepted.

    Returns a group-level result dict.
    """
    group_result = {
        "functional_group": fg,
        "found_images": [],
        "missing_images": [],
        "image_details": [],
        "success": True,
        "job_id": job_id,
    }

    # Build the S3 path segment to match when build_stream is enabled.
    # Prefer the precise <job_id>-<image_group_id> from the database;
    # fall back to just <job_id> if image_group_id is unavailable.
    if job_id and image_group_id:
        s3_match_segment = f"{job_id}-{image_group_id}"
    elif job_id:
        s3_match_segment = job_id
    else:
        s3_match_segment = None

    for img_type in image_types:
        found = False
        for path, info in s3_files.items():
            # Must contain the functional group name
            if fg not in path:
                continue
            # Must contain the image type keyword
            if img_type not in path:
                continue
            # When build_stream enabled, path must contain the DB-derived segment
            if s3_match_segment and s3_match_segment not in path:
                continue
            found = True
            group_result["found_images"].append(img_type)

            # Extract meaningful directory name (rhel-<fg>_<UUID>-image-build) from full path
            # From: s3://boot-images/efi-images/slurm_control_node_x86_64/rhel-slurm_control_node_x86_64_c01cdd28-3c60-4124-bcf0-b53a0ef93c8b-image-build/file
            # To: rhel-slurm_control_node_x86_64_c01cdd28-3c60-4124-bcf0-b53a0ef93c8b-image-build
            path_parts = path.split('/')
            display_path = next((part for part in path_parts if part.startswith('rhel-') and '-image-build' in part), info["filename"])

            group_result["image_details"].append({
                "type": img_type,
                "filename": info["filename"],
                "full_path": path,
                "display_path": display_path,
                "size": info["size"],
                "size_human": _format_size(info["size"]),
            })
            break

        if not found:
            group_result["missing_images"].append(img_type)
            group_result["success"] = False

    return group_result


def check_s3_bucket_images(host, arch: str = None) -> Dict[str, Any]:
    """
    Validate that images are pushed to the S3 bucket.

    Handles two naming schemes automatically:

    **build_stream ENABLED** (enable_build_stream: true):
      The build_image playbook embeds the postgres job UUID in every image
      directory name::

          s3://boot-images/<fg>/rhel-<fg>_<UUID>-image-build/<files>

      This function queries the omnia_postgres ``job_stages`` table to get
      the UUID of the last COMPLETED ``build-image-<arch>`` stage, then
      verifies that the S3 paths contain that exact UUID.  If no COMPLETED
      job exists the check fails with a clear error.

    **build_stream DISABLED** (enable_build_stream: false):
      Images are stored without a UUID sub-directory::

          s3://boot-images/<fg>/<files>

      A simple substring match on ``<fg>`` and image type is used.

    Args:
        host: testinfra host object
        arch: Architecture to filter by (``x86_64`` or ``aarch64``).
              If None, checks all groups from pxe_mapping.

    Returns:
        Dict with ``success``, ``status``, ``details``, ``error``, ``results``,
        ``job_id`` (UUID when build_stream enabled, else None).
    """
    s3_cmd = BUILD_IMAGE_VARS["s3_list_images_cmd"]
    image_types = BUILD_IMAGE_VARS["image_types"]

    raw_functional_groups = get_functional_groups_from_pxe_mapping(host)
    if arch:
        raw_functional_groups = _filter_functional_groups_by_arch(raw_functional_groups, arch)
    functional_groups = _get_adjusted_functional_groups(host, raw_functional_groups)

    if not functional_groups:
        return {
            "success": True,
            "status": "skipped",
            "skipped": True,
            "details": (
                f"No {arch or 'any'} functional groups found in "
                f"{get_pxe_mapping_filename()} — skipping S3 check"
            ),
            "error": None,
            "results": [],
            "job_id": None,
            "s3_output": "",
        }

    # -----------------------------------------------------------------------
    # Determine whether build_stream is enabled and get the job UUID
    # -----------------------------------------------------------------------
    build_stream_on = is_build_stream_enabled(host)
    job_id: Optional[str] = None

    if build_stream_on:
        job_result = get_last_build_image_job_id(host, arch=arch or "x86_64")
        if not job_result["success"] or not job_result["job_id"]:
            return {
                "success": False,
                "status": "no_completed_job",
                "skipped": False,
                "details": None,
                "error": (
                    job_result["error"]
                    or f"No COMPLETED build-image-{arch or 'x86_64'} job found "
                       "in build_stream_db.job_stages"
                ),
                "results": [],
                "job_id": None,
                "s3_output": "",
            }
        job_id = job_result["job_id"]

    # -----------------------------------------------------------------------
    # Query DB for image_group_id (S3 path = <job_id>-<image_group_id>)
    # -----------------------------------------------------------------------
    image_group_id: Optional[str] = None
    if job_id:
        ig_result = get_image_groups_for_job(host, job_id)
        if ig_result["success"] and ig_result["image_groups"]:
            image_group_id = ig_result["image_groups"][0].get("id", "")

    # -----------------------------------------------------------------------
    # Fetch full S3 listing once
    # -----------------------------------------------------------------------
    s3_list_cmd = host.run(f"{s3_cmd} 2>/dev/null")
    s3_output = s3_list_cmd.stdout if s3_list_cmd.rc == 0 else ""
    s3_files = _parse_s3_listing(s3_output)

    # -----------------------------------------------------------------------
    # Match images per functional group
    # -----------------------------------------------------------------------
    results = []
    all_passed = True

    for fg in functional_groups:
        group_result = _match_s3_images_for_group(
            fg, image_types, s3_files, job_id, image_group_id
        )
        results.append(group_result)
        if not group_result["success"]:
            all_passed = False

    total_groups = len(functional_groups)
    passed_groups = sum(1 for r in results if r["success"])

    mode = f"UUID={job_id}" if job_id else "no-UUID (build_stream disabled)"

    if all_passed:
        return {
            "success": True,
            "status": "all_found",
            "skipped": False,
            "details": (
                f"All 3 images found for all {total_groups} functional groups "
                f"({mode})"
            ),
            "error": None,
            "results": results,
            "job_id": job_id,
            "s3_output": s3_output,
        }

    failed_groups = [r for r in results if not r["success"]]
    error_details = [
        f"{r['functional_group']}: missing {', '.join(r['missing_images'])}"
        for r in failed_groups
    ]

    return {
        "success": False,
        "status": "missing_images",
        "skipped": False,
        "details": (
            f"{passed_groups}/{total_groups} functional groups have all images "
            f"({mode})"
        ),
        "error": "; ".join(error_details),
        "results": results,
        "job_id": job_id,
        "s3_output": s3_output,
    }


def check_s3_bucket_images_for_group(host, functional_group: str) -> Dict[str, Any]:
    """
    Validate that all 3 images for a specific functional group are in S3 bucket.
    Uses: s3cmd ls -Hr s3://boot-images | grep <image_pattern>

    Args:
        host: testinfra host object
        functional_group: name of the functional group to check

    Returns:
        Dict with 'success', 'status', 'details', 'error', 'found_images', 'missing_images'
    """
    s3_cmd = BUILD_IMAGE_VARS["s3_list_images_cmd"]
    image_types = BUILD_IMAGE_VARS["image_types"]

    found_images = []
    missing_images = []

    for img_type in image_types:
        # Use s3cmd ls | grep to check for each image
        grep_cmd = host.run(f"{s3_cmd} 2>/dev/null | grep -q '{functional_group}.*{img_type}'")

        if grep_cmd.rc == 0:
            found_images.append(img_type)
        else:
            missing_images.append(img_type)

    if not missing_images:
        return {
            "success": True,
            "status": "all_found",
            "details": f"All 3 images (initrd, rootfs, vmlinuz) found for {functional_group}",
            "error": None,
            "found_images": found_images,
            "missing_images": []
        }

    return {
        "success": False,
        "status": "missing_images",
        "details": f"Found {len(found_images)}/3 images for {functional_group}",
        "error": f"Missing: {', '.join(missing_images)}",
        "found_images": found_images,
        "missing_images": missing_images
    }


# =============================================================================
# IMAGE CONTENT VERIFICATION FUNCTIONS
# =============================================================================

def _check_squashfs_tools_installed(host) -> Dict[str, Any]:
    """
    Ensure squashfs-tools is installed (required for mounting images).

    If the package is not present, this function will **automatically install
    it** using ``dnf install -y squashfs-tools``.  If the install fails
    (e.g. no repo provides it), the function returns a clear error.

    Returns dict with 'installed' boolean and 'error' message if not installed.
    """
    check_cmd = host.run("which unsquashfs 2>/dev/null || rpm -q squashfs-tools 2>/dev/null")
    if check_cmd.rc == 0:
        return {"installed": True, "error": None}

    # Not installed — attempt automatic install
    install_cmd = host.run("dnf install -y squashfs-tools 2>&1")
    if install_cmd.rc == 0:
        # Verify it's actually available now
        verify = host.run("which unsquashfs 2>/dev/null || rpm -q squashfs-tools 2>/dev/null")
        if verify.rc == 0:
            return {"installed": True, "error": None}

    # Install failed — check if any enabled repo provides it
    repo_check = host.run("dnf provides squashfs-tools --quiet 2>/dev/null | grep -q 'squashfs-tools'")
    if repo_check.rc != 0:
        return {
            "installed": False,
            "error": (
                TEST_LOG_MSGS["squashfs_repo_not_configured"] + "\n"
                "  squashfs-tools is not available in any enabled repository.\n"
                "  Auto-install attempted but failed.\n"
                "  Enable a repository that provides it "
                "(e.g., 'dnf config-manager --enable <repo>'), then re-run."
            ),
        }

    # Repo provides it but install still failed
    stderr = install_cmd.stderr.strip()[:300] if install_cmd.stderr else ""
    stdout = install_cmd.stdout.strip()[:300] if install_cmd.stdout else ""
    return {
        "installed": False,
        "error": (
            TEST_LOG_MSGS["squashfs_tools_not_installed"] + "\n"
            f"  Auto-install attempted: dnf install -y squashfs-tools\n"
            f"  Exit code: {install_cmd.rc}\n"
            f"  Output: {stdout or stderr}"
        ),
    }


def _get_base_image_packages(host, images_dir: str, arch: str = "x86_64") -> list:
    """
    Get packages from base image YAML.
    Base image packages should be present in all compute images.
    """
    version = BUILD_IMAGE_VARS["base_image_version"]
    base_yaml = f"{images_dir}/rhel-{arch}_base-{version}.yaml"
    cat_cmd = run_in_container(host, f"cat {base_yaml} 2>/dev/null")
    if cat_cmd.rc != 0:
        return []
    try:
        config = pyyaml.safe_load(cat_cmd.stdout)
        return config.get("packages", [])
    except Exception:
        return []


def _verify_single_image_packages(
    host, functional_group: str, images_dir: str,
    temp_image: str, temp_mount: str,
    base_packages: list = None,
    job_id: Optional[str] = None,
    image_group_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Helper function to verify packages in a single image.
    Downloads, mounts, checks RPM database, and cleans up.
    Includes base image packages in verification.
    """
    # Get expected packages from image config YAML (use bash -c for glob expansion)
    yaml_cmd = run_in_container(host, f"bash -c 'ls -1 {images_dir}/*.yaml 2>/dev/null | grep {functional_group}'")
    if yaml_cmd.rc != 0 or not yaml_cmd.stdout.strip():
        return {
            "functional_group": functional_group,
            "success": False,
            "error": "No image config YAML found",
            "expected_count": 0,
            "found_count": 0,
            "missing_count": 0,
            "package_details": []
        }

    yaml_file = yaml_cmd.stdout.strip().split('\n')[0]
    cat_cmd = run_in_container(host, f"cat {yaml_file}")
    if cat_cmd.rc != 0:
        return {
            "functional_group": functional_group,
            "success": False,
            "error": "Failed to read YAML config",
            "expected_count": 0,
            "found_count": 0,
            "missing_count": 0,
            "package_details": []
        }

    try:
        config = pyyaml.safe_load(cat_cmd.stdout)
        compute_packages = config.get("packages", [])
    except Exception as e:
        return {
            "functional_group": functional_group,
            "success": False,
            "error": f"Failed to parse YAML: {e}",
            "expected_count": 0,
            "found_count": 0,
            "missing_count": 0,
            "package_details": []
        }

    # Combine base image packages + compute image packages (deduplicated)
    if base_packages:
        all_expected = list(dict.fromkeys(base_packages + compute_packages))
    else:
        all_expected = compute_packages

    if not all_expected:
        return {
            "functional_group": functional_group,
            "success": True,
            "error": None,
            "expected_count": 0,
            "found_count": 0,
            "missing_count": 0,
            "package_details": [],
            "base_package_count": len(base_packages) if base_packages else 0,
            "compute_package_count": len(compute_packages),
            "note": "No packages defined in config"
        }

    expected_packages = all_expected

    # Find the S3 image path
    # When build_stream is enabled, use <job_id>-<image_group_id> from DB.
    # When build_stream is disabled, match by functional group name only.
    s3_cmd = BUILD_IMAGE_VARS["s3_list_images_cmd"]
    if job_id and image_group_id:
        s3_match = f"{job_id}-{image_group_id}"
    elif job_id:
        s3_match = job_id
    else:
        s3_match = None

    if s3_match:
        s3_list = host.run(
            f"{s3_cmd} 2>/dev/null | grep '{functional_group}' | "
            f"grep '{s3_match}' | "
            "grep -v efi-images | grep -v initramfs | grep -v vmlinuz"
        )
    else:
        s3_list = host.run(
            f"{s3_cmd} 2>/dev/null | grep '{functional_group}' | "
            "grep -v efi-images | grep -v initramfs | grep -v vmlinuz"
        )
    if s3_list.rc != 0 or not s3_list.stdout.strip():
        return {
            "functional_group": functional_group,
            "success": False,
            "error": "No rootfs image found in S3",
            "expected_count": len(expected_packages),
            "found_count": 0,
            "missing_count": len(expected_packages),
            "package_details": []
        }

    # Parse S3 path
    s3_line = s3_list.stdout.strip().split('\n')[0]
    s3_path = s3_line.split()[-1] if s3_line else None
    if not s3_path:
        return {
            "functional_group": functional_group,
            "success": False,
            "error": "Failed to parse S3 image path",
            "expected_count": len(expected_packages),
            "found_count": 0,
            "missing_count": len(expected_packages),
            "package_details": []
        }

    # Download image
    download_cmd = host.run(f"s3cmd get {s3_path} {temp_image} --force 2>/dev/null")
    if download_cmd.rc != 0:
        return {
            "functional_group": functional_group,
            "success": False,
            "error": "Failed to download image",
            "expected_count": len(expected_packages),
            "found_count": 0,
            "missing_count": len(expected_packages),
            "package_details": []
        }

    # Mount the squashfs image
    host.run(f"mkdir -p {temp_mount}")
    mount_cmd = host.run(f"mount -t squashfs -o ro {temp_image} {temp_mount} 2>/dev/null")
    if mount_cmd.rc != 0:
        host.run(f"rm -f {temp_image}")
        return {
            "functional_group": functional_group,
            "success": False,
            "error": "Failed to mount image",
            "expected_count": len(expected_packages),
            "found_count": 0,
            "missing_count": len(expected_packages),
            "package_details": []
        }

    # Query RPM database inside the image
    rpm_cmd = host.run(f"rpm --root={temp_mount} -qa 2>/dev/null")
    installed_packages = rpm_cmd.stdout.strip().split('\n') if rpm_cmd.rc == 0 else []

    # Verify each expected package
    found_packages = []
    missing_packages = []
    package_details = []

    for pkg in expected_packages:
        # Strip version suffix for matching (e.g., kubeadm-1.34.1 -> kubeadm)
        base_pkg = pkg.split('-')[0] if '-' in pkg and pkg.split('-')[-1][0].isdigit() else pkg

        # Search for package in installed list using multiple strategies:
        # 1. Exact prefix match (e.g., firewalld -> firewalld-2.3.0)
        # 2. Package name contains base_pkg (e.g., python3.12 -> python3.12-libs)
        # 3. Special case: python3.12 -> python3-3.12.x (RHEL naming convention)
        found = False
        found_version = None
        for installed in installed_packages:
            inst_lower = installed.lower()
            base_lower = base_pkg.lower()
            # Strategy 1: Starts with base package name
            if inst_lower.startswith(base_lower):
                found = True
                found_version = installed
                break
            # Strategy 2: Contains base package (for cases like python3.12)
            if base_lower in inst_lower and inst_lower.split('-')[0] == base_lower:
                found = True
                found_version = installed
                break
            # Strategy 3: python3.12 -> python3-3.12 (RHEL naming)
            if base_lower.startswith('python') and '.' in base_lower:
                # python3.12 -> look for python3-3.12
                py_version = base_lower.replace('python', '')
                if inst_lower.startswith(f'python3-{py_version}'):
                    found = True
                    found_version = installed
                    break

        if found:
            found_packages.append(pkg)
            package_details.append({
                "expected": pkg,
                "found": found_version,
                "status": "installed"
            })
        else:
            missing_packages.append(pkg)
            package_details.append({
                "expected": pkg,
                "found": None,
                "status": "missing"
            })

    # Cleanup - ensure proper unmount and remove temp files
    host.run(f"umount -l {temp_mount} 2>/dev/null")  # lazy unmount to handle busy mounts
    host.run(f"rm -rf {temp_mount} 2>/dev/null")     # remove mount point directory
    host.run(f"rm -f {temp_image} 2>/dev/null")      # remove downloaded image

    # Determine base vs compute package counts
    base_pkg_count = len(base_packages) if base_packages else 0

    return {
        "functional_group": functional_group,
        "success": len(missing_packages) == 0,
        "image_path": s3_path,
        "expected_count": len(expected_packages),
        "found_count": len(found_packages),
        "missing_count": len(missing_packages),
        "base_package_count": base_pkg_count,
        "compute_package_count": len(compute_packages),
        "found_packages": found_packages,
        "missing_packages": missing_packages,
        "package_details": package_details,
        "error": f"Missing: {', '.join(missing_packages)}" if missing_packages else None
    }


def verify_all_image_packages(host, arch: str = None) -> Dict[str, Any]:
    """
    Download ALL S3 images, mount each, and verify all expected packages are installed.
    Uses RPM database inside each squashfs image for accurate verification.

    Args:
        host: testinfra host object
        arch: Architecture to filter by (x86_64 or aarch64). If None, checks all.

    Returns:
        Dict with 'success', 'results' containing package verification for each functional group
    """
    # Check if squashfs-tools is installed (required for mounting images)
    squashfs_check = _check_squashfs_tools_installed(host)
    if not squashfs_check["installed"]:
        return {
            "success": False,
            "error": squashfs_check["error"],
            "results": [],
            "total_groups": 0,
            "passed_groups": 0,
            "failed_groups": 0,
            "prerequisite_failed": True
        }

    functional_groups = get_functional_groups_from_pxe_mapping(host)
    # Filter by architecture if specified
    if arch:
        functional_groups = _filter_functional_groups_by_arch(functional_groups, arch)
    if not functional_groups:
        return {
            "success": False,
            "error": f"No functional groups found in pxe_mapping for arch={arch}",
            "results": [],
            "total_groups": 0,
            "passed_groups": 0,
            "failed_groups": 0
        }

    # Adjust functional groups based on control plane count
    groups_to_verify = _get_adjusted_functional_groups(host, functional_groups)
    # Determine arch from groups if not specified
    if not arch:
        arch = "x86_64" if any("x86_64" in fg for fg in functional_groups) else "aarch64"

    images_dir = BUILD_IMAGE_VARS["image_config_yaml_dir"]
    temp_image = BUILD_IMAGE_VARS["temp_image_path"]
    temp_mount = BUILD_IMAGE_VARS["temp_mount_path"]

    # Get base image packages (these should be in all compute images)
    base_packages = _get_base_image_packages(host, images_dir, arch)

    # Ensure mount point exists and is clean
    host.run(f"umount {temp_mount} 2>/dev/null")
    host.run(f"rm -f {temp_image}")
    host.run(f"mkdir -p {temp_mount}")

    results = []
    all_passed = True

    # Resolve job_id and image_group_id for S3 path filtering
    job_id: Optional[str] = None
    image_group_id: Optional[str] = None
    if is_build_stream_enabled(host):
        job_result = get_last_build_image_job_id(host, arch=arch or "x86_64")
        if job_result["success"]:
            job_id = job_result["job_id"]
    if job_id:
        ig_result = get_image_groups_for_job(host, job_id)
        if ig_result["success"] and ig_result["image_groups"]:
            image_group_id = ig_result["image_groups"][0].get("id", "")

    for fg in groups_to_verify:
        result = _verify_single_image_packages(
            host, fg, images_dir, temp_image, temp_mount,
            base_packages, job_id, image_group_id,
        )
        results.append(result)
        if not result["success"]:
            all_passed = False

    # Final cleanup - ensure everything is cleaned up
    host.run(f"umount -l {temp_mount} 2>/dev/null")
    host.run(f"rm -rf {temp_mount} 2>/dev/null")
    host.run(f"rm -f {temp_image} 2>/dev/null")

    passed_count = sum(1 for r in results if r["success"])
    failed_count = len(results) - passed_count

    return {
        "success": all_passed,
        "results": results,
        "total_groups": len(groups_to_verify),
        "passed_groups": passed_count,
        "failed_groups": failed_count,
        "details": f"Verified packages in {passed_count}/{len(groups_to_verify)} images",
        "error": None if all_passed else f"{failed_count} image(s) have missing packages"
    }


# =============================================================================
# COMBINED VALIDATION FUNCTIONS
# =============================================================================

def run_all_prechecks(host) -> Dict[str, Any]:
    """
    Run all prechecks before build_image playbook execution.
    Currently checks: S3 containers running.

    Args:
        host: testinfra host object

    Returns:
        Dict with 'success', 'results', 'passed', 'failed'
    """
    results = []
    passed = 0
    failed = 0

    # Check S3 containers
    s3_result = check_s3_containers(host)
    results.append({
        "name": "S3 Containers Running",
        "success": s3_result["success"],
        "details": s3_result["details"],
        "error": s3_result.get("error")
    })
    if s3_result["success"]:
        passed += 1
    else:
        failed += 1

    return {
        "success": failed == 0,
        "results": results,
        "passed": passed,
        "failed": failed,
        "total": passed + failed
    }


def run_all_validations(host) -> Dict[str, Any]:
    """
    Run all post-playbook validations for build_image.

    Args:
        host: testinfra host object

    Returns:
        Dict with 'success', 'results', 'passed', 'failed', 'skipped', 'summary'
    """
    results = []
    passed = 0
    failed = 0
    skipped = 0

    # 1. Check functional_group.yml exists
    fg_exists_result = check_functional_group_file_exists(host)
    results.append({
        "name": "functional_group.yml Exists",
        "success": fg_exists_result["success"],
        "details": fg_exists_result.get("details") or fg_exists_result.get("error")
    })
    if fg_exists_result["success"]:
        passed += 1
    else:
        failed += 1

    # 2. Check functional_group.yml content (only if file exists)
    if fg_exists_result["success"]:
        fg_content_result = check_functional_group_content(host)
        results.append({
            "name": "functional_group.yml Content Valid",
            "success": fg_content_result["success"],
            "details": fg_content_result.get("details") or fg_content_result.get("error")
        })
        if fg_content_result["success"]:
            passed += 1
        else:
            failed += 1
    else:
        results.append({
            "name": "functional_group.yml Content Valid",
            "success": False,
            "details": "Skipped - file does not exist",
            "skipped": True
        })
        skipped += 1

    # 3. Check S3 bucket images
    s3_result = check_s3_bucket_images(host)
    results.append({
        "name": "S3 Bucket Images Pushed",
        "success": s3_result["success"],
        "details": s3_result.get("details") or s3_result.get("error")
    })
    if s3_result["success"]:
        passed += 1
    else:
        failed += 1

    total = passed + failed
    return {
        "success": failed == 0,
        "results": results,
        "passed": passed,
        "failed": failed,
        "skipped": skipped,
        "total": total,
        "summary": BUILD_IMAGE_MSGS["validation_summary"].format(
            total=total, passed=passed, failed=failed, skipped=skipped
        )
    }
