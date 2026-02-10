# Copyright 2025 Dell Inc. or its subsidiaries. All Rights Reserved.
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
Testinfra tests for build_image_x86_64 verification.

Validations:
- S3 containers are running
- functional_group.yml exists and is valid YAML
- functional_group.yml contains roles from pxe_mapping.csv
- Registry container is running
- Base and compute images are in registry
- S3 bucket is accessible
- Images are pushed to S3 bucket
- All functional group images are in S3
"""

from automation_library.core import TestLogger
from automation_library.build_images.messages.build_images_msgs import (
    TEST_NAMES,
    TEST_LOG_MSGS as LOG_MSGS,
    TEST_ASSERT_MSGS as ASSERT_MSGS,
    TEST_VARS,
)
from automation_library.build_images.functions.build_images_func import (
    check_s3_container_running,
    check_all_s3_containers,
    check_functional_group_exists,
    check_functional_group_valid,
    check_functional_group_roles,
    check_functional_group_groups,
    check_registry_container,
    check_regctl_available,
    check_base_image_in_registry,
    check_compute_image_in_registry,
    check_s3_bucket_accessible,
    check_s3_bucket_images,
    check_all_functional_group_images_in_s3,
)


def test_s3_containers_running(host):
    """Verify all S3 containers are running."""
    log = TestLogger(TEST_NAMES["s3_containers_healthy"])
    log.check("Checking S3 containers status")

    result = check_all_s3_containers(host)
    if result["success"]:
        log.passed(LOG_MSGS["s3_containers_healthy"], result["details"])
    else:
        failed_containers = [r["container"] for r in result["results"] if not r["success"]]
        log.failed(LOG_MSGS["s3_containers_failed"].format(count=len(failed_containers)), 
                   ", ".join(failed_containers))

    assert result["success"], ASSERT_MSGS["s3_container_not_running"].format(
        container=", ".join([r["container"] for r in result["results"] if not r["success"]]),
        status=result.get("details", "unknown"),
    )


def test_functional_group_exists(host):
    """Verify functional_group.yml exists."""
    path = TEST_VARS["functional_group_path"]
    log = TestLogger(TEST_NAMES["functional_group_exists"])
    log.check(f"Checking file: {path}")

    result = check_functional_group_exists(host)
    if result["success"]:
        log.passed(LOG_MSGS["functional_group_exists"].format(path=path), "")
    else:
        log.failed(LOG_MSGS["functional_group_not_exists"].format(path=path), result.get("error"))

    assert result["success"], ASSERT_MSGS["functional_group_not_exists"].format(path=path)


def test_functional_group_valid(host):
    """Verify functional_group.yml is valid YAML."""
    path = TEST_VARS["functional_group_path"]
    log = TestLogger(TEST_NAMES["functional_group_valid"])
    log.check("Validating YAML syntax")

    result = check_functional_group_valid(host)
    if result["success"]:
        log.passed(LOG_MSGS["functional_group_valid"], "")
    else:
        log.failed(LOG_MSGS["functional_group_invalid"].format(error=result.get("error")), "")

    assert result["success"], ASSERT_MSGS["functional_group_invalid"].format(
        path=path,
        error=result.get("error", "unknown"),
    )


def test_functional_group_roles(host):
    """Verify functional_group.yml contains roles from pxe_mapping.csv."""
    log = TestLogger(TEST_NAMES["functional_group_roles"])
    log.check("Checking roles match pxe_mapping.csv")

    result = check_functional_group_roles(host)
    if result["success"]:
        log.passed(LOG_MSGS["functional_group_roles_ok"], result.get("details", ""))
    else:
        missing = ", ".join(result.get("missing", []))
        log.failed(LOG_MSGS["functional_group_roles_missing"].format(missing=missing), "")

    assert result["success"], ASSERT_MSGS["functional_group_roles_missing"].format(
        missing=", ".join(result.get("missing", [])),
    )


def test_functional_group_groups(host):
    """Verify functional_group.yml contains groups from pxe_mapping.csv."""
    log = TestLogger(TEST_NAMES["functional_group_groups"])
    log.check("Checking groups match pxe_mapping.csv")

    result = check_functional_group_groups(host)
    if result["success"]:
        log.passed(LOG_MSGS["functional_group_groups_ok"], result.get("details", ""))
    else:
        missing = ", ".join(result.get("missing", []))
        log.failed(LOG_MSGS["functional_group_groups_missing"].format(missing=missing), "")

    assert result["success"], ASSERT_MSGS["functional_group_roles_missing"].format(
        missing=", ".join(result.get("missing", [])),
    )


def test_registry_container_running(host):
    """Verify registry container is running."""
    log = TestLogger(TEST_NAMES["registry_container_running"])
    log.check("Checking registry container status")

    result = check_registry_container(host)
    if result["success"]:
        log.passed(LOG_MSGS["registry_running"], result.get("status", ""))
    else:
        log.failed(LOG_MSGS["registry_not_running"], result.get("error"))

    assert result["success"], ASSERT_MSGS["registry_not_running"].format(
        status=result.get("status", "unknown"),
    )


def test_regctl_available(host):
    """Verify regctl command is available."""
    log = TestLogger(TEST_NAMES["regctl_available"])
    log.check("Checking regctl command")

    result = check_regctl_available(host)
    if result["success"]:
        log.passed(LOG_MSGS["regctl_available"], result.get("version", ""))
    else:
        log.failed(LOG_MSGS["regctl_not_available"], result.get("error"))

    assert result["success"], "regctl command not found. Run prepare_oim playbook to set up the environment."


def test_base_image_in_registry(host):
    """Verify base images are in registry."""
    log = TestLogger(TEST_NAMES["base_image_in_registry"])
    log.check("Checking base images in registry")

    result = check_base_image_in_registry(host)
    if result["success"]:
        log.passed(LOG_MSGS["base_image_found"].format(image=", ".join(result.get("images", []))), "")
    else:
        log.failed(LOG_MSGS["base_image_not_found"].format(image="base"), result.get("error"))

    assert result["success"], ASSERT_MSGS["image_not_in_registry"].format(
        image="base",
        image_type="base",
    )


def test_compute_image_in_registry(host):
    """Verify compute images are in registry."""
    log = TestLogger(TEST_NAMES["compute_image_in_registry"])
    log.check("Checking compute images in registry")

    result = check_compute_image_in_registry(host)
    if result["success"]:
        log.passed(LOG_MSGS["compute_image_found"].format(image=", ".join(result.get("images", []))), "")
    else:
        log.failed(LOG_MSGS["compute_image_not_found"].format(image="compute"), result.get("error"))

    assert result["success"], ASSERT_MSGS["image_not_in_registry"].format(
        image="compute",
        image_type="compute",
    )


def test_s3_bucket_accessible(host):
    """Verify S3 bucket is accessible."""
    bucket = TEST_VARS["s3_bucket"]
    log = TestLogger(TEST_NAMES["s3_bucket_accessible"])
    log.check(f"Checking S3 bucket: {bucket}")

    result = check_s3_bucket_accessible(host)
    if result["success"]:
        log.passed(LOG_MSGS["s3_bucket_accessible"].format(bucket=bucket), "")
    else:
        log.failed(LOG_MSGS["s3_bucket_not_accessible"].format(bucket=bucket), result.get("error"))

    assert result["success"], ASSERT_MSGS["s3_bucket_not_accessible"].format(
        bucket=bucket,
        error=result.get("error", "unknown"),
    )


def test_images_in_s3_bucket(host):
    """Verify images are pushed to S3 bucket."""
    bucket = TEST_VARS["s3_bucket"]
    log = TestLogger(TEST_NAMES["images_in_s3"])
    log.check(f"Checking images in S3 bucket: {bucket}")

    result = check_s3_bucket_images(host)
    if result["success"]:
        log.passed(LOG_MSGS["images_in_s3"], result.get("details", ""))
    else:
        log.failed(LOG_MSGS["images_not_in_s3"], result.get("error"))

    assert result["success"], ASSERT_MSGS["images_not_in_s3"].format(
        bucket=bucket,
        group="all",
        missing="images",
    )


def test_all_functional_group_images_in_s3(host):
    """Verify all 3 images for each functional group are in S3."""
    log = TestLogger(TEST_NAMES["functional_group_images_in_s3"].format(group="all"))
    log.check("Checking all functional group images in S3")

    result = check_all_functional_group_images_in_s3(host)
    if result["success"]:
        log.passed(LOG_MSGS["functional_group_images_ok"].format(group="all"), result.get("details", ""))
    else:
        # Find which groups are missing images
        failed_groups = []
        for r in result.get("results", []):
            if not r.get("success"):
                failed_groups.append(f"{r.get('group')}: missing {', '.join(r.get('missing', []))}")
        log.failed(LOG_MSGS["functional_group_images_missing"].format(
            group="multiple",
            missing="; ".join(failed_groups)
        ), "")

    assert result["success"], ASSERT_MSGS["images_not_in_s3"].format(
        bucket=TEST_VARS["s3_bucket"],
        group="multiple functional groups",
        missing=result.get("error", "unknown"),
    )
