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
Upgrade and Rollback Module - Common Functions.

Shared utility functions used by both upgrade and rollback workflows.
"""

from typing import Tuple


def compare_versions(v1: str, v2: str) -> int:
    """
    Compare two version strings (e.g., "2.1.0.0" vs "2.2.0.0").

    Args:
        v1: First version string
        v2: Second version string

    Returns:
        -1 if v1 < v2, 0 if v1 == v2, 1 if v1 > v2
    """
    def parse(v: str) -> Tuple[int, ...]:
        try:
            return tuple(int(x) for x in v.split("."))
        except (ValueError, AttributeError):
            return (0,)

    p1, p2 = parse(v1), parse(v2)
    if p1 < p2:
        return -1
    if p1 > p2:
        return 1
    return 0
