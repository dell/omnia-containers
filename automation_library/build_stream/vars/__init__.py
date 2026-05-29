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
    # Pipeline stages
    BUILD_PIPELINE_CORE_STAGES,
    BUILD_IMAGE_STAGE_PREFIX,
    BUILD_PIPELINE_STAGES,
    DEPLOY_PIPELINE_STAGES,
    CLEANUP_PIPELINE_STAGES,
    # Registry and S3
    REGISTRY_PORT,
    REGISTRY_CATALOG_PATH,
    REGISTRY_IMAGE_PREFIX,
    S3_BOOT_IMAGES_BUCKET,
    S3_EFI_IMAGES_PREFIX,
    BOOT_IMAGE_ARTIFACTS_PER_ROLE,
    # Stress test
    STRESS_BUILD_PIPELINE_COUNT,
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
    # GitLab API
    GITLAB_API_VERSION,
    GITLAB_ROOT_TOKEN_FILE,
    CATALOG_FILE_PATH,
)
