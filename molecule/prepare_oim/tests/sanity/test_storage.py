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
Prepare OIM - Storage Verification Test Cases.

Test cases for verifying S3 storage backend configuration:
1. Verify S3 storage backend (MinIO or PowerScale) is configured
2. Verify s3cmd is installed and working
3. Verify required S3 buckets exist (efi, boot-images)
4. Verify regctl is installed and registry is accessible
5. Verify S3 endpoint directories are created properly
"""

import pytest

from automation_library.core import TestLogger
from automation_library.prepare_oim.messages import (
    TEST_NAMES,
    TEST_LOG_MSGS as LOG_MSGS,
    TEST_ASSERT_MSGS as ASSERT_MSGS,
)
from automation_library.prepare_oim.functions import (
    verify_storage_backend,
    verify_s3cmd_working,
    verify_s3_buckets,
    verify_regctl_working,
    verify_s3_directories,
)


# =============================================================================
# 10. STORAGE BACKEND VERIFICATION TEST
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(10)
def test_storage_backend(host):
    """
    Test Case 10: Verify S3 storage backend is configured and operational.

    Checks:
    - storage_config.yml has valid s3_configurations.provider
    - If MinIO: minio-server container is running and data dir exists
    - If PowerScale: endpoint_url is configured and reachable
    """
    log = TestLogger(TEST_NAMES["storage_backend"])
    log.check("Checking S3 storage backend configuration")

    result = verify_storage_backend(host)

    if result["success"]:
        log.passed(
            LOG_MSGS["storage_backend_ok"].format(
                backend=result["backend"]
            ),
            result["details"],
        )
    else:
        log.failed(LOG_MSGS["storage_backend_failed"], result["error"])

    assert result["success"], ASSERT_MSGS["storage_backend_failed"].format(
        backend=result.get("backend", "unknown"),
        error=result["error"],
    )


# =============================================================================
# 11. S3CMD VERIFICATION TEST
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(11)
def test_s3cmd_working(host):
    """
    Test Case 11: Verify s3cmd is installed and working.

    Checks:
    - s3cmd binary is available on the OIM host
    - ~/.s3cfg config file exists with correct S3 endpoint settings
    - s3cmd ls executes successfully
    """
    log = TestLogger(TEST_NAMES["s3cmd_working"])
    log.check("Checking s3cmd installation and connectivity")

    result = verify_s3cmd_working(host)

    if result["success"]:
        log.passed(LOG_MSGS["s3cmd_ok"], result["details"])
    else:
        log.failed(LOG_MSGS["s3cmd_failed"], result["error"])

    assert result["success"], ASSERT_MSGS["s3cmd_failed"].format(
        error=result["error"],
    )


# =============================================================================
# 12. S3 BUCKET VERIFICATION TEST
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(12)
def test_s3_buckets(host):
    """
    Test Case 12: Verify required S3 buckets exist.

    Checks:
    - s3://efi bucket is present
    - s3://boot-images bucket is present
    """
    log = TestLogger(TEST_NAMES["s3_buckets"])
    log.check("Checking required S3 buckets (efi, boot-images)")

    result = verify_s3_buckets(host)

    if result["success"]:
        log.passed(LOG_MSGS["s3_buckets_ok"], result["details"])
    else:
        log.failed(LOG_MSGS["s3_buckets_failed"], result["details"])

    assert result["success"], ASSERT_MSGS["s3_buckets_failed"].format(
        missing=", ".join(result.get("missing", [])),
    )


# =============================================================================
# 13. REGCTL VERIFICATION TEST
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(13)
def test_regctl_working(host):
    """
    Test Case 13: Verify regctl is installed and registry is accessible.

    Checks:
    - regctl binary exists at /usr/local/bin/regctl
    - regctl config exists at /root/.regctl/config.json
    - regctl repo ls against local registry succeeds
    """
    log = TestLogger(TEST_NAMES["regctl_working"])
    log.check("Checking regctl installation and registry connectivity")

    result = verify_regctl_working(host)

    if result["success"]:
        log.passed(LOG_MSGS["regctl_ok"], result["details"])
    else:
        log.failed(LOG_MSGS["regctl_failed"], result["error"])

    assert result["success"], ASSERT_MSGS["regctl_failed"].format(
        error=result["error"],
    )


# =============================================================================
# 14. S3 ENDPOINT DIRECTORY VERIFICATION TEST
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(14)
def test_s3_directories(host):
    """
    Test Case 14: Verify S3 endpoint directories are created properly.

    Checks:
    - For MinIO: local NFS data directory exists with bucket subdirs
    - For PowerScale: S3 buckets accessible via s3cmd at endpoint
    """
    log = TestLogger(TEST_NAMES["s3_directories"])
    log.check("Checking S3 endpoint directories")

    result = verify_s3_directories(host)

    if result["success"]:
        log.passed(LOG_MSGS["s3_dirs_ok"], result["details"])
    else:
        log.failed(LOG_MSGS["s3_dirs_failed"], result["error"])

    assert result["success"], ASSERT_MSGS["s3_dirs_failed"].format(
        backend=result.get("backend", "unknown"),
        error=result.get("error", ""),
    )
