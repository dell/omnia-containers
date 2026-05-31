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
Build Stream Variables - Constants for build_stream automation.

All runtime values (port, host_ip, credentials) are read dynamically from
config files via core module functions — nothing is hardcoded here.

For module-specific messages, see:
- build_stream_msgs.py - Test names, log messages, assert messages
"""

from typing import List

# =============================================================================
# BUILD STREAM API (omnia_build_stream container)
# Keys used to read runtime values from build_stream_config.yml
# =============================================================================

BUILD_STREAM_HOST_IP_KEY: str = "build_stream_host_ip"
BUILD_STREAM_PORT_KEY: str = "build_stream_port"
BUILD_STREAM_HEALTH_PATH: str = "/health"
BUILD_STREAM_API_VERSION: str = "v1"
BUILD_STREAM_AUTH_TOKEN_PATH: str = "/api/v1/auth/token"

# =============================================================================
# PIPELINE STAGES (from GitLab CI/CD)
# =============================================================================

BUILD_PIPELINE_CORE_STAGES: List[str] = [
    "upload",
    "parse-catalog",
    "generate-input-files",
    "create-local-repository",
]

BUILD_IMAGE_STAGE_PREFIX: str = "build-image-"

BUILD_PIPELINE_STAGES: List[str] = [
    "upload",
    "parse-catalog",
    "generate-input-files",
    "create-local-repository",
    "build-image-x86_64",
    "build-image-aarch64",
]

DEPLOY_PIPELINE_STAGES: List[str] = [
    "deploy",
    "restart",
    "validate",
]

CLEANUP_PIPELINE_STAGES: List[str] = [
    "cleanup",
]

# =============================================================================
# DATABASE CONFIGURATION
# =============================================================================

EXPECTED_TABLES: List[str] = [
    "alembic_version",
    "artifact_metadata",
    "audit_events",
    "idempotency_keys",
    "image_groups",
    "images",
    "job_stages",
    "jobs",
]

IMAGE_GROUP_STATUS_BUILT: str = "BUILT"
IMAGE_GROUP_STATUS_CLEANED: str = "CLEANED"

# =============================================================================
# REGISTRY AND S3 CONFIGURATION
# =============================================================================

REGISTRY_PORT: int = 5000
REGISTRY_CATALOG_PATH: str = "/v2/_catalog"
REGISTRY_IMAGE_PREFIX: str = "rhel-"  # Role prefix in registry (hostname added dynamically)

S3_BOOT_IMAGES_BUCKET: str = "s3://boot-images/"
S3_EFI_IMAGES_PREFIX: str = "s3://boot-images/efi-images/"
BOOT_IMAGE_ARTIFACTS_PER_ROLE: int = 3  # initramfs, vmlinuz, boot image

# =============================================================================
# STRESS TEST CONFIGURATION
# =============================================================================

STRESS_BUILD_PIPELINE_COUNT: int = 50  # Number of build pipeline runs for stress test
STRESS_STOP_ON_FIRST_FAILURE: bool = True  # Stop stress test on first failure

# =============================================================================
# JOB STATES (from build_stream_db.jobs)
# =============================================================================

JOB_STATE_PENDING: str = "PENDING"
JOB_STATE_IN_PROGRESS: str = "IN_PROGRESS"
JOB_STATE_COMPLETED: str = "COMPLETED"
JOB_STATE_FAILED: str = "FAILED"

# =============================================================================
# STAGE STATES (from build_stream_db.job_stages)
# =============================================================================

STAGE_STATE_PENDING: str = "PENDING"
STAGE_STATE_RUNNING: str = "RUNNING"
STAGE_STATE_COMPLETED: str = "COMPLETED"
STAGE_STATE_FAILED: str = "FAILED"

# =============================================================================
# POLLING CONFIGURATION
# =============================================================================

STAGE_POLL_INTERVAL: int = 30  # seconds between stage status checks
STAGE_POLL_TIMEOUT: int = 10800  # 3 hours max wait per stage (build stages can take 2+ hours)
PIPELINE_POLL_INTERVAL: int = 5  # seconds between pipeline status checks
PIPELINE_POLL_TIMEOUT: int = 180  # 3 minutes to detect pipeline start
JOB_WAIT_TIMEOUT: int = 120  # seconds to wait for new job in database
CLEANUP_WAIT_TIMEOUT: int = 300  # seconds to wait for cleanup completion

# =============================================================================
# GITLAB API CONFIGURATION
# =============================================================================

GITLAB_API_VERSION: str = "v4"
GITLAB_ROOT_TOKEN_FILE: str = "/root/.gitlab_root_token"
CATALOG_FILE_PATH: str = "catalog_rhel.json"
PXE_MAPPING_FILE_PATH: str = "input/pxe_mapping_file.csv"

# =============================================================================
# GITLAB CI/CD VARIABLE KEYS
# =============================================================================

BSM_CLIENT_ID_KEY: str = "BSM_CLIENT_ID"
BSM_CLIENT_SECRET_KEY: str = "BSM_CLIENT_SECRET"
PIPELINE_TYPE_KEY: str = "PIPELINE_TYPE"
PIPELINE_TYPE_BUILD: str = "build"
PIPELINE_TYPE_DEPLOY: str = "deploy"
PIPELINE_TYPE_CLEANUP: str = "cleanup"
