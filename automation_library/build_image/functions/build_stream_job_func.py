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
Build Image - Build Stream Job Functions.

Thin wrappers that delegate to ``automation_library.core.build_stream``.
Kept here for backward-compatibility so existing imports from this module
continue to work.

For new code prefer importing directly from ``automation_library.core``.
"""

from typing import Dict, Any

from automation_library.core.build_stream import (
    is_build_stream_enabled,
    get_build_stream_job_id as _core_get_job_id,
    STAGE_BUILD_IMAGE_X86_64,
    STAGE_BUILD_IMAGE_AARCH64,
)


def get_last_build_image_job_id(host, arch: str = "x86_64") -> Dict[str, Any]:
    """
    Return the job_id (UUID) for the last successfully completed build-image
    job for the given architecture.

    Delegates to ``core.get_build_stream_job_id`` which:
      - Honours the ``build_stream_job_id`` override in ``omnia_test_config.yml``
      - Falls back to the latest COMPLETED entry in ``build_stream_db``
      - Returns exact DB ``job_state`` so callers can print it on failure

    Args:
        host: Testinfra host object.
        arch: ``"x86_64"`` (default) or ``"aarch64"``.
    """
    stage = STAGE_BUILD_IMAGE_AARCH64 if arch == "aarch64" else STAGE_BUILD_IMAGE_X86_64
    return _core_get_job_id(host, stage_name=stage)


__all__ = [
    "is_build_stream_enabled",
    "get_last_build_image_job_id",
]
