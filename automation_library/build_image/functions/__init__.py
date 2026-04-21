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

"""Build Image functions module."""

# Re-export from core module for backward compatibility
from automation_library.core import (
    get_functional_groups_from_pxe_mapping,
    get_group_names_from_pxe_mapping,
)

from .build_image_func import (
    check_container_running,
    check_s3_containers,
    check_functional_group_file_exists,
    check_functional_group_content,
    check_regctl_registry_images,
    check_s3_bucket_images,
    check_s3_bucket_images_for_group,
    verify_all_image_packages,
    run_all_prechecks,
    run_all_validations,
)

from .build_stream_job_func import (
    is_build_stream_enabled,
    get_last_build_image_job_id,
)

__all__ = [
    "check_container_running",
    "check_s3_containers",
    "check_functional_group_file_exists",
    "check_functional_group_content",
    "check_regctl_registry_images",
    "check_s3_bucket_images",
    "check_s3_bucket_images_for_group",
    "verify_all_image_packages",
    "run_all_prechecks",
    "run_all_validations",
    # Re-exported from core module
    "get_functional_groups_from_pxe_mapping",
    "get_group_names_from_pxe_mapping",
    # Build stream job functions
    "is_build_stream_enabled",
    "get_last_build_image_job_id",
]
