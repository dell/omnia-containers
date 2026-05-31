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

"""Build Stream Variables Module."""

from .build_stream_vars import (
    # Build Stream API
    BUILD_STREAM_HEALTH_PATH,
    BUILD_STREAM_HOST_IP_KEY,
    BUILD_STREAM_PORT_KEY,
    BUILD_STREAM_API_VERSION,
    BUILD_STREAM_AUTH_TOKEN_PATH,
    # Pipeline stages
    BUILD_PIPELINE_CORE_STAGES,
    BUILD_IMAGE_STAGE_PREFIX,
    BUILD_PIPELINE_STAGES,
    DEPLOY_PIPELINE_STAGES,
    CLEANUP_PIPELINE_STAGES,
    # Database configuration
    EXPECTED_TABLES,
    IMAGE_GROUP_STATUS_BUILT,
    IMAGE_GROUP_STATUS_CLEANED,
    # Registry and S3
    REGISTRY_PORT,
    REGISTRY_CATALOG_PATH,
    REGISTRY_IMAGE_PREFIX,
    S3_BOOT_IMAGES_BUCKET,
    S3_EFI_IMAGES_PREFIX,
    BOOT_IMAGE_ARTIFACTS_PER_ROLE,
    # Stress test
    STRESS_BUILD_PIPELINE_COUNT,
    STRESS_STOP_ON_FIRST_FAILURE,
    # Job states
    JOB_STATE_PENDING,
    JOB_STATE_IN_PROGRESS,
    JOB_STATE_COMPLETED,
    JOB_STATE_FAILED,
    # Stage states
    STAGE_STATE_PENDING,
    STAGE_STATE_RUNNING,
    STAGE_STATE_COMPLETED,
    STAGE_STATE_FAILED,
    # Polling configuration
    STAGE_POLL_INTERVAL,
    STAGE_POLL_TIMEOUT,
    PIPELINE_POLL_INTERVAL,
    PIPELINE_POLL_TIMEOUT,
    JOB_WAIT_TIMEOUT,
    CLEANUP_WAIT_TIMEOUT,
    # GitLab API
    GITLAB_API_VERSION,
    GITLAB_ROOT_TOKEN_FILE,
    CATALOG_FILE_PATH,
    PXE_MAPPING_FILE_PATH,
    # GitLab CI/CD variable keys
    BSM_CLIENT_ID_KEY,
    BSM_CLIENT_SECRET_KEY,
    PIPELINE_TYPE_KEY,
    PIPELINE_TYPE_BUILD,
    PIPELINE_TYPE_DEPLOY,
    PIPELINE_TYPE_CLEANUP,
)
