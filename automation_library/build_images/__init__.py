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
Build Images Functions

Modular organization of Build Image x86_64 deployment and management functions
organized by functionality: functions, variables, and messages.
"""

# Import specific items to avoid circular imports
# Note: Import functions first, then vars and messages to avoid circular dependency
from .functions.build_images_func import (
    check_s3_container_running,
    check_all_s3_containers,
    check_functional_group_exists,
    check_functional_group_valid,
    check_functional_group_roles,
    check_functional_group_groups,
    check_registry_container,
    check_regctl_available,
    check_image_in_registry,
    check_base_image_in_registry,
    check_compute_image_in_registry,
    check_s3_bucket_accessible,
    check_s3_bucket_images,
    get_functional_groups,
    check_functional_group_images_in_s3,
    check_all_functional_group_images_in_s3,
    run_all_validations,
)
from .vars.build_images_vars import (
    BUILD_IMAGE_VARS,
    S3_CONTAINERS,
    REGISTRY_CONTAINER,
    IMAGE_TYPES,
    get_s3_containers,
    get_image_types,
    get_functional_group_path,
    get_pxe_mapping_path,
)
from .messages.build_images_msgs import (
    BUILD_IMAGE_MSGS,
    TEST_VARS,
    TEST_NAMES,
    TEST_LOG_MSGS,
    TEST_ASSERT_MSGS,
)
