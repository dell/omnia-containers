"""
Build Image x86_64 - Core Functions.

This module contains all functions for running and verifying build_image_x86_64.
Test functions should call these functions - all logic resides here.

Usage:
    from automation_library.build_images.functions.build_images_func import (
        check_s3_container_running,
        check_functional_group_exists,
        check_functional_group_valid,
        check_functional_group_roles,
        check_registry_images,
        check_s3_bucket_images,
    )

Author: Dell Technologies
"""

import csv
import io
from typing import Dict, Any, List

from automation_library.build_images.vars.build_images_vars import (
    BUILD_IMAGE_VARS,
    S3_CONTAINERS,
    REGISTRY_CONTAINER,
    IMAGE_TYPES,
)
from automation_library.build_images.messages.build_images_msgs import BUILD_IMAGE_MSGS


# =============================================================================
# S3 CONTAINER VERIFICATION FUNCTIONS (for pytest/testinfra)
# =============================================================================

def check_s3_container_running(host, container_name: str) -> Dict[str, Any]:
    """
    Check if a specific S3 container is running.

    Args:
        host: testinfra host object
        container_name: name of the container to check

    Returns:
        Dict with 'success', 'status', 'details', 'error'
    """
    cmd = host.run(f"podman ps --format '{{{{.Names}}}} {{{{.Status}}}}' | grep -E '^{container_name} '")

    if cmd.rc == 0 and container_name in cmd.stdout:
        status = cmd.stdout.strip().replace(container_name, "").strip()
        return {
            "success": True,
            "status": status,
            "details": f"S3 container {container_name} is running: {status}",
            "error": None
        }

    # Check if container exists but not running
    exists_cmd = host.run(f"podman ps -a --format '{{{{.Names}}}} {{{{.Status}}}}' | grep -E '^{container_name} '")
    if exists_cmd.rc == 0:
        status = exists_cmd.stdout.strip().replace(container_name, "").strip()
        return {
            "success": False,
            "status": status,
            "details": None,
            "error": f"S3 container {container_name} exists but not running: {status}"
        }

    return {
        "success": False,
        "status": "not_found",
        "details": None,
        "error": f"S3 container {container_name} does not exist"
    }


def check_all_s3_containers(host) -> Dict[str, Any]:
    """
    Check all S3 containers are running without errors.

    Args:
        host: testinfra host object

    Returns:
        Dict with 'success', 'results', 'passed', 'failed', 'details'
    """
    results = []
    passed = 0
    failed = 0

    for container in S3_CONTAINERS:
        result = check_s3_container_running(host, container)
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
# FUNCTIONAL GROUP VERIFICATION FUNCTIONS
# =============================================================================

def check_functional_group_exists(host) -> Dict[str, Any]:
    """
    Check if functional_group.yml file exists inside omnia_core container.

    Args:
        host: testinfra host object

    Returns:
        Dict with 'success', 'path', 'details', 'error'
    """
    path = BUILD_IMAGE_VARS["functional_group_path"]
    # Check inside omnia_core container
    cmd = host.run(f"podman exec omnia_core test -f {path} && echo 'EXISTS' || echo 'NOT_FOUND'")

    if "EXISTS" in cmd.stdout:
        return {
            "success": True,
            "path": path,
            "details": f"functional_group.yml exists at {path}",
            "error": None
        }

    return {
        "success": False,
        "path": path,
        "details": None,
        "error": f"functional_group.yml not found at {path}"
    }


def check_functional_group_valid(host) -> Dict[str, Any]:
    """
    Check if functional_group.yml is valid YAML.

    Args:
        host: testinfra host object

    Returns:
        Dict with 'success', 'content', 'details', 'error'
    """
    path = BUILD_IMAGE_VARS["functional_group_path"]

    # First check if file exists
    exists_result = check_functional_group_exists(host)
    if not exists_result["success"]:
        return {
            "success": False,
            "content": None,
            "details": None,
            "error": exists_result["error"]
        }

    # Read and validate YAML inside omnia_core container
    yaml_cmd = BUILD_IMAGE_VARS["yaml_validate_cmd"].format(path=path)
    cmd = host.run(yaml_cmd)

    if cmd.rc == 0:
        return {
            "success": True,
            "content": cmd.stdout.strip(),
            "details": "functional_group.yml is valid YAML",
            "error": None
        }

    return {
        "success": False,
        "content": None,
        "details": None,
        "error": f"Invalid YAML: {cmd.stdout.strip() or cmd.stderr.strip()}"
    }


def _parse_pxe_mapping(host) -> Dict[str, Any]:
    """
    Parse pxe_mapping.csv and extract roles and groups.

    Args:
        host: testinfra host object

    Returns:
        Dict with 'success', 'roles', 'groups', 'error'
    """
    path = BUILD_IMAGE_VARS["pxe_mapping_path"]

    # Check if file exists inside omnia_core container
    cmd = host.run(f"podman exec omnia_core bash -c 'test -f {path} && cat {path}'")
    if cmd.rc != 0:
        return {
            "success": False,
            "roles": [],
            "groups": [],
            "error": f"pxe_mapping.csv not found at {path}"
        }

    roles = set()
    groups = set()

    try:
        reader = csv.DictReader(io.StringIO(cmd.stdout))
        for row in reader:
            # Extract role and group from CSV columns
            if "ROLE" in row and row["ROLE"]:
                roles.add(row["ROLE"].strip())
            if "role" in row and row["role"]:
                roles.add(row["role"].strip())
            if "GROUP" in row and row["GROUP"]:
                groups.add(row["GROUP"].strip())
            if "group" in row and row["group"]:
                groups.add(row["group"].strip())
            if "functional_group" in row and row["functional_group"]:
                groups.add(row["functional_group"].strip())
            if "FUNCTIONAL_GROUP" in row and row["FUNCTIONAL_GROUP"]:
                groups.add(row["FUNCTIONAL_GROUP"].strip())

        return {
            "success": True,
            "roles": list(roles),
            "groups": list(groups),
            "error": None
        }
    except Exception as e:
        return {
            "success": False,
            "roles": [],
            "groups": [],
            "error": f"Failed to parse pxe_mapping.csv: {str(e)}"
        }


def _parse_functional_group(host) -> Dict[str, Any]:
    """
    Parse functional_group.yml and extract roles and groups.

    Args:
        host: testinfra host object

    Returns:
        Dict with 'success', 'roles', 'groups', 'data', 'error'
    """
    path = BUILD_IMAGE_VARS["functional_group_path"]

    # Read YAML content from inside omnia_core container
    cmd = host.run(f"podman exec omnia_core cat {path}")
    if cmd.rc != 0:
        return {
            "success": False,
            "roles": [],
            "groups": [],
            "data": None,
            "error": f"Cannot read functional_group.yml: {cmd.stderr}"
        }

    # Parse YAML using Python inside omnia_core container
    parse_cmd = host.run(f"""podman exec omnia_core python3 -c "
import yaml
import json
with open('{path}') as f:
    data = yaml.safe_load(f)
print(json.dumps(data))
" 2>&1""")

    if parse_cmd.rc != 0:
        return {
            "success": False,
            "roles": [],
            "groups": [],
            "data": None,
            "error": f"Failed to parse functional_group.yml: {parse_cmd.stdout}"
        }

    try:
        import json
        data = json.loads(parse_cmd.stdout.strip())

        roles = set()
        groups = set()

        # Extract roles and groups from the YAML structure
        if isinstance(data, dict):
            for key, value in data.items():
                # Key could be a group name
                groups.add(key)
                if isinstance(value, dict):
                    if "role" in value:
                        roles.add(value["role"])
                    if "roles" in value and isinstance(value["roles"], list):
                        roles.update(value["roles"])
                    if "group" in value:
                        groups.add(value["group"])
                elif isinstance(value, list):
                    for item in value:
                        if isinstance(item, dict):
                            if "role" in item:
                                roles.add(item["role"])
                            if "group" in item:
                                groups.add(item["group"])
                        elif isinstance(item, str):
                            roles.add(item)

        return {
            "success": True,
            "roles": list(roles),
            "groups": list(groups),
            "data": data,
            "error": None
        }
    except Exception as e:
        return {
            "success": False,
            "roles": [],
            "groups": [],
            "data": None,
            "error": f"Failed to parse functional_group.yml: {str(e)}"
        }


def check_functional_group_roles(host) -> Dict[str, Any]:
    """
    Check if functional_group.yml contains all roles from pxe_mapping.csv.

    Args:
        host: testinfra host object

    Returns:
        Dict with 'success', 'expected', 'found', 'missing', 'details', 'error'
    """
    # Parse pxe_mapping.csv
    pxe_result = _parse_pxe_mapping(host)
    if not pxe_result["success"]:
        return {
            "success": False,
            "expected": [],
            "found": [],
            "missing": [],
            "details": None,
            "error": pxe_result["error"]
        }

    # Parse functional_group.yml
    fg_result = _parse_functional_group(host)
    if not fg_result["success"]:
        return {
            "success": False,
            "expected": pxe_result["roles"],
            "found": [],
            "missing": pxe_result["roles"],
            "details": None,
            "error": fg_result["error"]
        }

    expected_roles = set(pxe_result["roles"])
    found_roles = set(fg_result["roles"])
    missing_roles = expected_roles - found_roles

    if not missing_roles:
        return {
            "success": True,
            "expected": list(expected_roles),
            "found": list(found_roles),
            "missing": [],
            "details": f"All {len(expected_roles)} roles from pxe_mapping.csv found in functional_group.yml",
            "error": None
        }

    return {
        "success": False,
        "expected": list(expected_roles),
        "found": list(found_roles),
        "missing": list(missing_roles),
        "details": None,
        "error": f"Missing roles: {', '.join(missing_roles)}"
    }


def check_functional_group_groups(host) -> Dict[str, Any]:
    """
    Check if functional_group.yml contains all groups from pxe_mapping.csv.

    Args:
        host: testinfra host object

    Returns:
        Dict with 'success', 'expected', 'found', 'missing', 'details', 'error'
    """
    # Parse pxe_mapping.csv
    pxe_result = _parse_pxe_mapping(host)
    if not pxe_result["success"]:
        return {
            "success": False,
            "expected": [],
            "found": [],
            "missing": [],
            "details": None,
            "error": pxe_result["error"]
        }

    # Parse functional_group.yml
    fg_result = _parse_functional_group(host)
    if not fg_result["success"]:
        return {
            "success": False,
            "expected": pxe_result["groups"],
            "found": [],
            "missing": pxe_result["groups"],
            "details": None,
            "error": fg_result["error"]
        }

    expected_groups = set(pxe_result["groups"])
    found_groups = set(fg_result["groups"])
    missing_groups = expected_groups - found_groups

    if not missing_groups:
        return {
            "success": True,
            "expected": list(expected_groups),
            "found": list(found_groups),
            "missing": [],
            "details": f"All {len(expected_groups)} groups from pxe_mapping.csv found in functional_group.yml",
            "error": None
        }

    return {
        "success": False,
        "expected": list(expected_groups),
        "found": list(found_groups),
        "missing": list(missing_groups),
        "details": None,
        "error": f"Missing groups: {', '.join(missing_groups)}"
    }


# =============================================================================
# REGISTRY VERIFICATION FUNCTIONS
# =============================================================================

def check_registry_container(host) -> Dict[str, Any]:
    """
    Check if registry container is running.

    Args:
        host: testinfra host object

    Returns:
        Dict with 'success', 'status', 'details', 'error'
    """
    container = REGISTRY_CONTAINER
    cmd = host.run(f"podman ps --format '{{{{.Names}}}} {{{{.Status}}}}' | grep -E '^{container} '")

    if cmd.rc == 0 and container in cmd.stdout:
        status = cmd.stdout.strip().replace(container, "").strip()
        return {
            "success": True,
            "status": status,
            "details": f"Registry container is running: {status}",
            "error": None
        }

    return {
        "success": False,
        "status": "not_running",
        "details": None,
        "error": "Registry container is not running"
    }


def check_regctl_available(host) -> Dict[str, Any]:
    """
    Check if regctl command is available.

    Args:
        host: testinfra host object

    Returns:
        Dict with 'success', 'version', 'details', 'error'
    """
    cmd = host.run("which regctl && regctl version 2>/dev/null || echo 'NOT_FOUND'")

    if "NOT_FOUND" not in cmd.stdout and cmd.rc == 0:
        return {
            "success": True,
            "version": cmd.stdout.strip(),
            "details": "regctl command is available",
            "error": None
        }

    return {
        "success": False,
        "version": None,
        "details": None,
        "error": "regctl command not found"
    }


def check_image_in_registry(host, image_type: str) -> Dict[str, Any]:
    """
    Check if a specific image type is available in the registry.

    Args:
        host: testinfra host object
        image_type: type of image (base, compute, initrd)

    Returns:
        Dict with 'success', 'images', 'details', 'error'
    """
    registry_url = BUILD_IMAGE_VARS["registry_url"]

    # List images in registry using regctl
    cmd = host.run(f"regctl repo ls {registry_url} 2>/dev/null | grep -i {image_type}")

    if cmd.rc == 0 and cmd.stdout.strip():
        images = [img.strip() for img in cmd.stdout.strip().split('\n') if img.strip()]
        return {
            "success": True,
            "images": images,
            "details": f"{image_type} images found in registry: {', '.join(images)}",
            "error": None
        }

    return {
        "success": False,
        "images": [],
        "details": None,
        "error": f"No {image_type} images found in registry"
    }


def check_base_image_in_registry(host) -> Dict[str, Any]:
    """
    Check if base images are available in the registry.

    Args:
        host: testinfra host object

    Returns:
        Dict with 'success', 'images', 'details', 'error'
    """
    return check_image_in_registry(host, "base")


def check_compute_image_in_registry(host) -> Dict[str, Any]:
    """
    Check if compute images are available in the registry.

    Args:
        host: testinfra host object

    Returns:
        Dict with 'success', 'images', 'details', 'error'
    """
    return check_image_in_registry(host, "compute")


# =============================================================================
# S3 BUCKET VERIFICATION FUNCTIONS
# =============================================================================

def check_s3_bucket_accessible(host) -> Dict[str, Any]:
    """
    Check if S3 bucket is accessible.

    Args:
        host: testinfra host object

    Returns:
        Dict with 'success', 'bucket', 'details', 'error'
    """
    bucket = BUILD_IMAGE_VARS["s3_bucket"]
    cmd = host.run(f"s3cmd ls s3://{bucket} 2>&1")

    if cmd.rc == 0:
        return {
            "success": True,
            "bucket": bucket,
            "details": f"S3 bucket {bucket} is accessible",
            "error": None
        }

    return {
        "success": False,
        "bucket": bucket,
        "details": None,
        "error": f"S3 bucket {bucket} not accessible: {cmd.stdout.strip() or cmd.stderr.strip()}"
    }


def check_s3_bucket_images(host) -> Dict[str, Any]:
    """
    Check if images are pushed to S3 bucket.
    Uses: s3cmd ls -Hr s3://boot-images

    Args:
        host: testinfra host object

    Returns:
        Dict with 'success', 'images', 'details', 'error'
    """
    bucket = BUILD_IMAGE_VARS["s3_bucket"]
    cmd = host.run(f"s3cmd ls -Hr s3://{bucket} 2>&1")

    if cmd.rc == 0 and cmd.stdout.strip():
        images = [line.strip() for line in cmd.stdout.strip().split('\n') if line.strip()]
        return {
            "success": True,
            "images": images,
            "count": len(images),
            "details": f"Found {len(images)} items in S3 bucket {bucket}",
            "error": None
        }

    if cmd.rc == 0:
        return {
            "success": False,
            "images": [],
            "count": 0,
            "details": None,
            "error": f"S3 bucket {bucket} is empty"
        }

    return {
        "success": False,
        "images": [],
        "count": 0,
        "details": None,
        "error": f"Failed to list S3 bucket: {cmd.stdout.strip() or cmd.stderr.strip()}"
    }


def get_functional_groups(host) -> List[str]:
    """
    Get list of functional groups from functional_group.yml.

    Args:
        host: testinfra host object

    Returns:
        List of functional group names
    """
    fg_result = _parse_functional_group(host)
    if fg_result["success"]:
        return fg_result["groups"]
    return []


def check_functional_group_images_in_s3(host, group: str) -> Dict[str, Any]:
    """
    Check if all 3 images (base, compute, initrd) for a functional group are in S3.

    Args:
        host: testinfra host object
        group: functional group name

    Returns:
        Dict with 'success', 'group', 'found', 'missing', 'details', 'error'
    """
    bucket = BUILD_IMAGE_VARS["s3_bucket"]
    image_types = IMAGE_TYPES

    # List images for this functional group
    cmd = host.run(f"s3cmd ls -Hr s3://{bucket}/{group}/ 2>&1")

    found_types = []
    missing_types = []

    if cmd.rc == 0 and cmd.stdout.strip():
        s3_content = cmd.stdout.lower()
        for img_type in image_types:
            if img_type.lower() in s3_content:
                found_types.append(img_type)
            else:
                missing_types.append(img_type)
    else:
        missing_types = image_types.copy()

    if not missing_types:
        return {
            "success": True,
            "group": group,
            "found": found_types,
            "missing": [],
            "details": f"All {len(image_types)} images for {group} found in S3",
            "error": None
        }

    return {
        "success": False,
        "group": group,
        "found": found_types,
        "missing": missing_types,
        "details": None,
        "error": f"Missing images for {group}: {', '.join(missing_types)}"
    }


def check_all_functional_group_images_in_s3(host) -> Dict[str, Any]:
    """
    Check all 3 images for each functional group are in S3.

    Args:
        host: testinfra host object

    Returns:
        Dict with 'success', 'results', 'passed', 'failed', 'details', 'error'
    """
    groups = get_functional_groups(host)

    if not groups:
        return {
            "success": False,
            "results": [],
            "passed": 0,
            "failed": 0,
            "details": None,
            "error": "No functional groups found in functional_group.yml"
        }

    results = []
    passed = 0
    failed = 0

    for group in groups:
        result = check_functional_group_images_in_s3(host, group)
        results.append(result)
        if result["success"]:
            passed += 1
        else:
            failed += 1

    total = len(groups)
    return {
        "success": failed == 0,
        "results": results,
        "passed": passed,
        "failed": failed,
        "total": total,
        "details": f"{passed}/{total} functional groups have all images in S3",
        "error": f"{failed} functional group(s) missing images" if failed > 0 else None
    }


# =============================================================================
# FULL VALIDATION
# =============================================================================

def run_all_validations(host, skip_on_failure: bool = True) -> Dict[str, Any]:
    """
    Run all build_image_x86_64 validations.
    Continues checking all items even if some fail (skip_on_failure behavior).

    Args:
        host: testinfra host object
        skip_on_failure: if True, continue all validations even if some fail

    Returns:
        Dict with 'success', 'results', 'passed', 'failed', 'skipped', 'summary'
    """
    results = []
    passed = 0
    failed = 0
    skipped = 0

    # 1. Check S3 containers
    s3_result = check_all_s3_containers(host)
    results.append({
        "name": "S3 Containers Running",
        "success": s3_result["success"],
        "details": s3_result["details"],
        "sub_results": s3_result["results"]
    })
    if s3_result["success"]:
        passed += 1
    else:
        failed += 1

    # 2. Check functional_group.yml exists
    fg_exists = check_functional_group_exists(host)
    results.append({
        "name": "functional_group.yml Exists",
        "success": fg_exists["success"],
        "details": fg_exists.get("details") or fg_exists.get("error")
    })
    if fg_exists["success"]:
        passed += 1
    else:
        failed += 1

    # 3. Check functional_group.yml is valid
    fg_valid = check_functional_group_valid(host)
    results.append({
        "name": "functional_group.yml Valid YAML",
        "success": fg_valid["success"],
        "details": fg_valid.get("details") or fg_valid.get("error")
    })
    if fg_valid["success"]:
        passed += 1
    else:
        failed += 1

    # 4. Check functional_group.yml roles
    fg_roles = check_functional_group_roles(host)
    results.append({
        "name": "functional_group.yml Roles Match pxe_mapping.csv",
        "success": fg_roles["success"],
        "details": fg_roles.get("details") or fg_roles.get("error")
    })
    if fg_roles["success"]:
        passed += 1
    else:
        failed += 1

    # 5. Check functional_group.yml groups
    fg_groups = check_functional_group_groups(host)
    results.append({
        "name": "functional_group.yml Groups Match pxe_mapping.csv",
        "success": fg_groups["success"],
        "details": fg_groups.get("details") or fg_groups.get("error")
    })
    if fg_groups["success"]:
        passed += 1
    else:
        failed += 1

    # 6. Check registry container
    registry_result = check_registry_container(host)
    results.append({
        "name": "Registry Container Running",
        "success": registry_result["success"],
        "details": registry_result.get("details") or registry_result.get("error")
    })
    if registry_result["success"]:
        passed += 1
    else:
        failed += 1

    # 7. Check base images in registry
    base_result = check_base_image_in_registry(host)
    results.append({
        "name": "Base Images in Registry",
        "success": base_result["success"],
        "details": base_result.get("details") or base_result.get("error")
    })
    if base_result["success"]:
        passed += 1
    else:
        failed += 1

    # 8. Check compute images in registry
    compute_result = check_compute_image_in_registry(host)
    results.append({
        "name": "Compute Images in Registry",
        "success": compute_result["success"],
        "details": compute_result.get("details") or compute_result.get("error")
    })
    if compute_result["success"]:
        passed += 1
    else:
        failed += 1

    # 9. Check S3 bucket accessible
    s3_bucket_result = check_s3_bucket_accessible(host)
    results.append({
        "name": "S3 Bucket Accessible",
        "success": s3_bucket_result["success"],
        "details": s3_bucket_result.get("details") or s3_bucket_result.get("error")
    })
    if s3_bucket_result["success"]:
        passed += 1
    else:
        failed += 1

    # 10. Check all images in S3 bucket
    s3_images_result = check_s3_bucket_images(host)
    results.append({
        "name": "Images in S3 Bucket",
        "success": s3_images_result["success"],
        "details": s3_images_result.get("details") or s3_images_result.get("error")
    })
    if s3_images_result["success"]:
        passed += 1
    else:
        failed += 1

    # 11. Check all functional group images in S3
    fg_s3_result = check_all_functional_group_images_in_s3(host)
    results.append({
        "name": "All Functional Group Images in S3",
        "success": fg_s3_result["success"],
        "details": fg_s3_result.get("details") or fg_s3_result.get("error"),
        "sub_results": fg_s3_result.get("results", [])
    })
    if fg_s3_result["success"]:
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
