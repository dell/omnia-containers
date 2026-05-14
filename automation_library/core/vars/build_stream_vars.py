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

"""Core Build Stream Variables."""

# =============================================================================
# POSTGRES CONFIGURATION
# =============================================================================

POSTGRES_CONTAINER = "omnia_postgres"
POSTGRES_DB = "build_stream_db"
POSTGRES_USER_KEY = "postgres_user"
COMPLETED_STATE = "COMPLETED"

# =============================================================================
# WELL-KNOWN STAGE NAMES
# =============================================================================

STAGE_BUILD_IMAGE_X86_64 = "build-image-x86_64"
STAGE_BUILD_IMAGE_AARCH64 = "build-image-aarch64"
STAGE_CREATE_LOCAL_REPO = "create-local-repository"
STAGE_VALIDATE_IMAGE = "validate"
STAGE_PARSE_CATALOG = "parse-catalog"
STAGE_GENERATE_INPUT = "generate-input-files"
