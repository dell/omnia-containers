"""
Build Image x86_64 - Messages and Test Variables.

This module contains all messages, status strings, error instructions,
and test variables for the build_image_x86_64 automation.

Author: Dell Technologies
"""

from typing import Dict
from automation_library.build_images.vars.build_images_vars import (
    BUILD_IMAGE_VARS,
    S3_CONTAINERS,
    REGISTRY_CONTAINER,
    IMAGE_TYPES,
)

# =============================================================================
# TEST VARIABLES (for molecule/pytest tests)
# =============================================================================

TEST_VARS = {
    "s3_containers": S3_CONTAINERS,
    "registry_container": REGISTRY_CONTAINER,
    "image_types": IMAGE_TYPES,
    "s3_bucket": BUILD_IMAGE_VARS["s3_bucket"],
    "functional_group_path": BUILD_IMAGE_VARS["functional_group_path"],
    "pxe_mapping_path": BUILD_IMAGE_VARS["pxe_mapping_path"],
    "oim_server_ip": BUILD_IMAGE_VARS["oim_server_ip"],
}

# Test names (displayed in test output header)
TEST_NAMES = {
    # S3 Container verification
    "s3_container_running": "Verify S3 container {container} is running",
    "s3_containers_healthy": "Verify all S3 containers are healthy",
    # Functional group verification
    "functional_group_exists": "Verify functional_group.yml exists",
    "functional_group_valid": "Verify functional_group.yml is valid YAML",
    "functional_group_roles": "Verify functional_group.yml contains roles from pxe_mapping.csv",
    "functional_group_groups": "Verify functional_group.yml contains groups from pxe_mapping.csv",
    # Registry verification
    "registry_container_running": "Verify registry container is running",
    "regctl_available": "Verify regctl command is available",
    "base_image_in_registry": "Verify base image is available in registry",
    "compute_image_in_registry": "Verify compute image is available in registry",
    # S3 bucket verification
    "s3_bucket_accessible": "Verify S3 bucket is accessible",
    "images_in_s3": "Verify images are pushed to S3 bucket",
    "functional_group_images_in_s3": "Verify all 3 images for functional group {group} in S3",
}

# Test log messages
TEST_LOG_MSGS = {
    # S3 Container messages
    "s3_container_running": "S3 container {container} is running",
    "s3_container_not_running": "S3 container {container} is NOT running",
    "s3_containers_healthy": "All S3 containers are healthy",
    "s3_containers_failed": "{count} S3 container(s) not running",
    # Functional group messages
    "functional_group_exists": "functional_group.yml exists at {path}",
    "functional_group_not_exists": "functional_group.yml NOT found at {path}",
    "functional_group_valid": "functional_group.yml is valid YAML",
    "functional_group_invalid": "functional_group.yml is invalid YAML: {error}",
    "functional_group_roles_ok": "All roles from pxe_mapping.csv found in functional_group.yml",
    "functional_group_roles_missing": "Missing roles in functional_group.yml: {missing}",
    "functional_group_groups_ok": "All groups from pxe_mapping.csv found in functional_group.yml",
    "functional_group_groups_missing": "Missing groups in functional_group.yml: {missing}",
    # Registry messages
    "registry_running": "Registry container is running",
    "registry_not_running": "Registry container is NOT running",
    "regctl_available": "regctl command is available",
    "regctl_not_available": "regctl command is NOT available",
    "base_image_found": "Base image found in registry: {image}",
    "base_image_not_found": "Base image NOT found in registry: {image}",
    "compute_image_found": "Compute image found in registry: {image}",
    "compute_image_not_found": "Compute image NOT found in registry: {image}",
    # S3 bucket messages
    "s3_bucket_accessible": "S3 bucket {bucket} is accessible",
    "s3_bucket_not_accessible": "S3 bucket {bucket} is NOT accessible",
    "images_in_s3": "Images found in S3 bucket",
    "images_not_in_s3": "Images NOT found in S3 bucket",
    "functional_group_images_ok": "All 3 images for functional group {group} found in S3",
    "functional_group_images_missing": "Missing images for functional group {group}: {missing}",
}

# Test assert messages (user-friendly with instructions)
TEST_ASSERT_MSGS = {
    "s3_container_not_running": """
╔══════════════════════════════════════════════════════════════════════════════╗
║ S3 CONTAINER CHECK FAILED: {container}
╠══════════════════════════════════════════════════════════════════════════════╣
║ Status: {status}
║
║ HOW TO FIX:
║   1. SSH to OIM server and check container: podman ps -a | grep {container}
║   2. Check container logs: podman logs {container}
║   3. Try restarting: podman restart {container}
║   4. If container doesn't exist, re-run prepare_oim.yml
╚══════════════════════════════════════════════════════════════════════════════╝
""",
    "functional_group_not_exists": """
╔══════════════════════════════════════════════════════════════════════════════╗
║ FUNCTIONAL GROUP FILE NOT FOUND
╠══════════════════════════════════════════════════════════════════════════════╣
║ Expected path: {path}
║
║ HOW TO FIX:
║   1. Verify build_image_x86_64.yml playbook was executed successfully
║   2. Check if pxe_mapping.csv exists and is valid
║   3. Re-run build_image_x86_64.yml playbook
║   4. Check logs: /opt/omnia/log/
╚══════════════════════════════════════════════════════════════════════════════╝
""",
    "functional_group_invalid": """
╔══════════════════════════════════════════════════════════════════════════════╗
║ FUNCTIONAL GROUP FILE INVALID
╠══════════════════════════════════════════════════════════════════════════════╣
║ Path: {path}
║ Error: {error}
║
║ HOW TO FIX:
║   1. Check file syntax: cat {path}
║   2. Validate YAML: python -c "import yaml; yaml.safe_load(open('{path}'))"
║   3. Re-run build_image_x86_64.yml to regenerate the file
╚══════════════════════════════════════════════════════════════════════════════╝
""",
    "functional_group_roles_missing": """
╔══════════════════════════════════════════════════════════════════════════════╗
║ FUNCTIONAL GROUP ROLES MISMATCH
╠══════════════════════════════════════════════════════════════════════════════╣
║ Missing roles: {missing}
║
║ HOW TO FIX:
║   1. Check pxe_mapping.csv for expected roles
║   2. Verify build_image_x86_64.yml processed all entries
║   3. Re-run build_image_x86_64.yml playbook
╚══════════════════════════════════════════════════════════════════════════════╝
""",
    "registry_not_running": """
╔══════════════════════════════════════════════════════════════════════════════╗
║ REGISTRY CONTAINER NOT RUNNING
╠══════════════════════════════════════════════════════════════════════════════╣
║ Status: {status}
║
║ HOW TO FIX:
║   1. Check container status: podman ps -a | grep registry
║   2. Check container logs: podman logs registry
║   3. Try restarting: podman restart registry
║   4. Re-run prepare_oim.yml if registry was not deployed
╚══════════════════════════════════════════════════════════════════════════════╝
""",
    "image_not_in_registry": """
╔══════════════════════════════════════════════════════════════════════════════╗
║ IMAGE NOT FOUND IN REGISTRY
╠══════════════════════════════════════════════════════════════════════════════╣
║ Image: {image}
║ Type: {image_type}
║
║ HOW TO FIX:
║   1. Check registry catalog: regctl repo ls
║   2. Check if image was built: podman images | grep {image}
║   3. Re-run build_image_x86_64.yml to build and push images
║   4. Check build logs for errors
╚══════════════════════════════════════════════════════════════════════════════╝
""",
    "s3_bucket_not_accessible": """
╔══════════════════════════════════════════════════════════════════════════════╗
║ S3 BUCKET NOT ACCESSIBLE
╠══════════════════════════════════════════════════════════════════════════════╣
║ Bucket: {bucket}
║ Error: {error}
║
║ HOW TO FIX:
║   1. Check minio-server container: podman ps | grep minio
║   2. Check S3 configuration: s3cmd info s3://{bucket}
║   3. Verify S3 credentials are configured correctly
║   4. Check minio logs: podman logs minio-server
╚══════════════════════════════════════════════════════════════════════════════╝
""",
    "images_not_in_s3": """
╔══════════════════════════════════════════════════════════════════════════════╗
║ IMAGES NOT FOUND IN S3 BUCKET
╠══════════════════════════════════════════════════════════════════════════════╣
║ Bucket: {bucket}
║ Functional Group: {group}
║ Missing Images: {missing}
║
║ HOW TO FIX:
║   1. List S3 contents: s3cmd ls -Hr s3://boot-images
║   2. Check if images were pushed: s3cmd ls s3://boot-images/{group}/
║   3. Re-run build_image_x86_64.yml to push images
║   4. Check build logs for S3 upload errors
╚══════════════════════════════════════════════════════════════════════════════╝
""",
    "validation_failed": "Validation failed: {error}",
}

# =============================================================================
# FUNCTION MESSAGES (for build_images_func.py)
# =============================================================================

BUILD_IMAGE_MSGS: Dict[str, str] = {

    # =========================================================================
    # PLAYBOOK EXECUTION
    # =========================================================================
    "playbook_start": "Starting build_image_x86_64.yml playbook execution...",
    "playbook_success": "build_image_x86_64.yml completed successfully",
    "playbook_fail": "build_image_x86_64.yml failed",
    "playbook_timeout": "build_image_x86_64.yml timed out after {timeout} seconds",

    # =========================================================================
    # S3 CONTAINER VERIFICATION
    # =========================================================================
    "s3_check_start": "Checking S3 container status...",
    "s3_container_running": "S3 container {container} is running",
    "s3_container_not_running": "S3 container {container} is NOT running",
    "s3_containers_ok": "All S3 containers are running",
    "s3_containers_failed": "{failed} of {total} S3 containers not running",

    # =========================================================================
    # FUNCTIONAL GROUP VERIFICATION
    # =========================================================================
    "functional_group_check_start": "Checking functional_group.yml...",
    "functional_group_exists": "functional_group.yml exists",
    "functional_group_not_exists": "functional_group.yml does NOT exist",
    "functional_group_valid": "functional_group.yml is valid YAML",
    "functional_group_invalid": "functional_group.yml is invalid: {error}",
    "functional_group_roles_ok": "All roles from pxe_mapping.csv found",
    "functional_group_roles_missing": "Missing roles: {missing}",
    "functional_group_groups_ok": "All groups from pxe_mapping.csv found",
    "functional_group_groups_missing": "Missing groups: {missing}",

    # =========================================================================
    # REGISTRY VERIFICATION
    # =========================================================================
    "registry_check_start": "Checking registry and images...",
    "registry_running": "Registry container is running",
    "registry_not_running": "Registry container is NOT running",
    "regctl_available": "regctl command is available",
    "regctl_not_available": "regctl command is NOT available",
    "base_image_found": "Base image available in registry",
    "base_image_not_found": "Base image NOT found in registry",
    "compute_image_found": "Compute image available in registry",
    "compute_image_not_found": "Compute image NOT found in registry",

    # =========================================================================
    # S3 BUCKET VERIFICATION
    # =========================================================================
    "s3_bucket_check_start": "Checking S3 bucket for images...",
    "s3_bucket_accessible": "S3 bucket {bucket} is accessible",
    "s3_bucket_not_accessible": "S3 bucket {bucket} is NOT accessible",
    "s3_images_found": "Images found in S3 bucket for {group}",
    "s3_images_missing": "Images missing in S3 bucket for {group}",
    "s3_all_images_ok": "All images for all functional groups found in S3",
    "s3_images_failed": "Some images missing in S3 bucket",

    # =========================================================================
    # VALIDATION SUMMARY
    # =========================================================================
    "validation_start": "Starting build_image_x86_64 validation...",
    "validation_pass": "All build_image_x86_64 validations PASSED",
    "validation_fail": "build_image_x86_64 validation FAILED: {failed_count} check(s) failed",
    "validation_summary": """
Validation Summary:
- Total: {total}
- Passed: {passed}
- Failed: {failed}
- Skipped: {skipped}
""",

    # =========================================================================
    # INSTRUCTIONS
    # =========================================================================
    "s3_container_instruction": """
ACTION REQUIRED: S3 container is not running.
- Check container logs: podman logs {container}
- Check if container exists: podman ps -a | grep {container}
- Try restarting: podman restart {container}
""",

    "functional_group_instruction": """
ACTION REQUIRED: functional_group.yml validation failed.
- Check if file exists: ls -la {path}
- Validate YAML syntax: python -c "import yaml; yaml.safe_load(open('{path}'))"
- Re-run build_image_x86_64.yml playbook
""",

    "registry_instruction": """
ACTION REQUIRED: Registry or image check failed.
- Check registry container: podman ps | grep registry
- List registry images: regctl repo ls
- Re-run build_image_x86_64.yml to build and push images
""",

    "s3_bucket_instruction": """
ACTION REQUIRED: S3 bucket check failed.
- Check minio container: podman ps | grep minio
- List S3 bucket: s3cmd ls -Hr s3://boot-images
- Check S3 credentials and configuration
""",
}
