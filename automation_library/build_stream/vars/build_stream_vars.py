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
Build Stream Variables - Constants for build_stream automation (v2.1).

All runtime values (port, host_ip, credentials) are read dynamically from
config files via core module functions -- nothing is hardcoded here.

For module-specific messages, see:
- build_stream_msgs.py - Test names, log messages, assert messages
"""

from typing import List

from automation_library.core.vars.build_stream_vars import (
    STAGE_BUILD_IMAGE_X86_64,
    STAGE_BUILD_IMAGE_AARCH64,
    STAGE_CREATE_LOCAL_REPO,
    STAGE_VALIDATE_IMAGE,
    STAGE_PARSE_CATALOG,
    STAGE_GENERATE_INPUT,
)

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
# PIPELINE STAGES (from GitLab CI/CD -- BuildStream 2.1)
#
# v2.1 has a SINGLE pipeline (triggered by catalog_rhel.json commit):
#   CI/CD stages:
#     initialization, parse-catalog, generate-input-files,
#     configure-local-repository, build-images, deploy-and-validate, summary
#
#   DB stage names (from StageType enum):
#     parse-catalog, generate-input-files, create-local-repository,
#     build-image-x86_64, build-image-aarch64, validate-image-on-test
#
# The "deploy-and-validate" CI/CD stage runs the validate-image-on-test
# job which deploys and validates the built images on test nodes.
#
# NOTE: v2.2 splits this into separate build + deploy pipelines.
# =============================================================================

BUILD_PIPELINE_CORE_STAGES: List[str] = [
    STAGE_PARSE_CATALOG,
    STAGE_GENERATE_INPUT,
    STAGE_CREATE_LOCAL_REPO,
]

BUILD_IMAGE_STAGE_PREFIX: str = "build-image-"

BUILD_PIPELINE_STAGES: List[str] = [
    STAGE_PARSE_CATALOG,
    STAGE_GENERATE_INPUT,
    STAGE_CREATE_LOCAL_REPO,
    STAGE_BUILD_IMAGE_X86_64,
    STAGE_BUILD_IMAGE_AARCH64,
    STAGE_VALIDATE_IMAGE,
]

# =============================================================================
# DATABASE CONFIGURATION (BuildStream 2.1 -- no image_groups/images tables)
# =============================================================================

EXPECTED_TABLES: List[str] = [
    "alembic_version",
    "artifact_metadata",
    "audit_events",
    "idempotency_keys",
    "job_stages",
    "jobs",
]

# =============================================================================
# REGISTRY AND S3 CONFIGURATION
# =============================================================================

REGISTRY_PORT: int = 5000
REGISTRY_CATALOG_PATH: str = "/v2/_catalog"
REGISTRY_IMAGE_PREFIX: str = "rhel-"

S3_BOOT_IMAGES_BUCKET: str = "s3://boot-images/"
S3_EFI_IMAGES_PREFIX: str = "s3://boot-images/efi-images/"
BOOT_IMAGE_ARTIFACTS_PER_ROLE: int = 3  # initramfs, vmlinuz, boot image

# =============================================================================
# JOB STATES (from build_stream_db.jobs)
# =============================================================================

JOB_STATE_CREATED: str = "CREATED"
JOB_STATE_IN_PROGRESS: str = "IN_PROGRESS"
JOB_STATE_COMPLETED: str = "COMPLETED"
JOB_STATE_FAILED: str = "FAILED"

# =============================================================================
# STAGE STATES (from build_stream_db.job_stages)
# =============================================================================

STAGE_STATE_PENDING: str = "PENDING"
STAGE_STATE_IN_PROGRESS: str = "IN_PROGRESS"
STAGE_STATE_COMPLETED: str = "COMPLETED"
STAGE_STATE_FAILED: str = "FAILED"

# =============================================================================
# POLLING CONFIGURATION
# =============================================================================

STAGE_POLL_INTERVAL: int = 30  # seconds between stage status checks
STAGE_POLL_TIMEOUT: int = 10800  # 3 hours max wait per stage
PIPELINE_POLL_INTERVAL: int = 5  # seconds between pipeline status checks
PIPELINE_POLL_TIMEOUT: int = 180  # 3 minutes to detect pipeline start
JOB_WAIT_TIMEOUT: int = 120  # seconds to wait for new job in database

# =============================================================================
# GITLAB API CONFIGURATION
# =============================================================================

GITLAB_API_VERSION: str = "v4"
GITLAB_ROOT_TOKEN_FILE: str = "/root/.gitlab_root_token"
CATALOG_FILE_PATH: str = "catalog_rhel.json"
CATALOG_DEFAULT_FILENAME: str = "catalog_rhel_x86_64_with_slurm_only.json"
OMNIA_CATALOG_PATH: str = "/omnia/examples/catalog"

# =============================================================================
# GITLAB CI/CD VARIABLE KEYS
# =============================================================================

BSM_CLIENT_ID_KEY: str = "BSM_CLIENT_ID"
BSM_CLIENT_SECRET_KEY: str = "BSM_CLIENT_SECRET"
