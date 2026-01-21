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

Author: Dell Technologies
"""

from typing import Dict, Any

from ..vars.build_image_vars import (
    BUILD_IMAGE_VARS,
    S3_CONTAINERS,
    get_pxe_mapping_filename,
)
from ..messages.build_image_msgs import BUILD_IMAGE_MSGS


# Import pxe_mapping functions from core module for reuse
from automation_library.core import (
    get_functional_groups_from_pxe_mapping,
    get_group_names_from_pxe_mapping,
)


# =============================================================================
# CONTAINER VERIFICATION FUNCTIONS (PRECHECK)
# =============================================================================

def check_container_running(host, container_name: str) -> Dict[str, Any]:
    """
    Check if a specific container is running.

    Args:
        host: testinfra host object
        container_name: name of the container to check

    Returns:
        Dict with 'success', 'status', 'details', 'error'
    """
    cmd = host.run(
        f"podman ps --format '{{{{.Names}}}} {{{{.Status}}}}' | grep -E '^{container_name} '"
    )

    if cmd.rc == 0 and container_name in cmd.stdout:
        status = cmd.stdout.strip().replace(container_name, "").strip()
        return {
            "success": True,
            "status": status,
            "details": f"Container {container_name} is running: {status}",
            "error": None
        }

    # Check if container exists but not running
    exists_cmd = host.run(
        f"podman ps -a --format '{{{{.Names}}}} {{{{.Status}}}}' | grep -E '^{container_name} '"
    )
    if exists_cmd.rc == 0:
        status = exists_cmd.stdout.strip().replace(container_name, "").strip()
        return {
            "success": False,
            "status": status,
            "details": None,
            "error": f"Container {container_name} exists but not running: {status}"
        }

    return {
        "success": False,
        "status": "not_found",
        "details": None,
        "error": f"Container {container_name} does not exist"
    }


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
    cmd = host.run(
        f"podman exec omnia_core test -f {file_path} && echo 'EXISTS' || echo 'NOT_FOUND'"
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


def check_functional_group_content(host) -> Dict[str, Any]:
    """
    Validate functional_groups_config.yml contains all roles and groups from pxe_mapping.

    Args:
        host: testinfra host object

    Returns:
        Dict with 'success', 'status', 'details', 'error', 'missing_groups', 'found_groups'
    """
    file_path = BUILD_IMAGE_VARS["functional_group_file_path"]

    # Get expected functional groups from pxe_mapping file inside container
    expected_functional_groups = get_functional_groups_from_pxe_mapping(host)
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
    cmd = host.run(f"podman exec omnia_core cat {file_path}")

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

def check_regctl_registry_images(host) -> Dict[str, Any]:
    """
    Validate that base and compute images are available in the regctl registry.
    Uses: regctl repo ls <hostname>.omnia.test:5000
    
    Expected images:
    - rhel-x86_64_base (always required)
    - rhel-<functional_group> for each group from pxe_mapping
    
    Args:
        host: testinfra host object
    
    Returns:
        Dict with 'success', 'status', 'details', 'error', 'found_images', 'missing_images'
    """
    # Get hostname dynamically
    hostname_cmd = host.run("hostname -s")
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
    registry_url = f"{hostname}.omnia.test:5000"

    # Get functional groups from pxe_mapping file inside container
    functional_groups = get_functional_groups_from_pxe_mapping(host)

    # Build expected images list (without hostname prefix for display)
    expected_images = ["rhel-x86_64_base"]  # Base image always required
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

def check_s3_bucket_images(host) -> Dict[str, Any]:
    """
    Validate that images are pushed to the S3 bucket.
    Checks for all 3 images (initrd, rootfs, vmlinuz) for each functional group.
    Uses: s3cmd ls -Hr s3://boot-images | grep <image_pattern>

    Args:
        host: testinfra host object

    Returns:
        Dict with 'success', 'status', 'details', 'error', 'results'
    """
    s3_cmd = BUILD_IMAGE_VARS["s3_list_images_cmd"]
    image_types = BUILD_IMAGE_VARS["image_types"]
    functional_groups = get_functional_groups_from_pxe_mapping(host)

    if not functional_groups:
        return {
            "success": False,
            "status": "no_groups",
            "details": None,
            "error": f"No functional groups found in {get_pxe_mapping_filename()}",
            "results": [],
            "s3_output": ""
        }

    # Get complete S3 bucket listing (removing s3://boot-images/ and efi-images/ prefix)
    s3_list_cmd = host.run(f"{s3_cmd} 2>/dev/null | sed 's|s3://boot-images/||g' | sed 's|efi-images/||g'")
    s3_output = s3_list_cmd.stdout if s3_list_cmd.rc == 0 else ""

    # Check for each functional group's images using grep
    results = []
    all_passed = True

    for fg in functional_groups:
        group_result = {
            "functional_group": fg,
            "found_images": [],
            "missing_images": [],
            "success": True
        }

        for img_type in image_types:
            # Use s3cmd ls | grep to check for each image
            grep_cmd = host.run(f"{s3_cmd} 2>/dev/null | grep -q '{fg}.*{img_type}'")

            if grep_cmd.rc == 0:
                group_result["found_images"].append(img_type)
            else:
                group_result["missing_images"].append(img_type)
                group_result["success"] = False
                all_passed = False

        results.append(group_result)

    total_groups = len(functional_groups)
    passed_groups = sum(1 for r in results if r["success"])

    if all_passed:
        return {
            "success": True,
            "status": "all_found",
            "details": f"All 3 images found for all {total_groups} functional groups in S3 bucket",
            "error": None,
            "results": results,
            "s3_output": s3_output
        }

    failed_groups = [r for r in results if not r["success"]]
    error_details = []
    for fg_result in failed_groups:
        error_details.append(
            f"{fg_result['functional_group']}: missing {', '.join(fg_result['missing_images'])}"
        )

    return {
        "success": False,
        "status": "missing_images",
        "details": f"{passed_groups}/{total_groups} functional groups have all images",
        "error": "; ".join(error_details),
        "results": results,
        "s3_output": s3_output
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
