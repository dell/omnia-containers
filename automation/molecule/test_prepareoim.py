# Copyright 2025 Dell Inc. or its subsidiaries. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an "AS IS"
# BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND,
# either express or implied. See the License for the specific language
# governing permissions and limitations under the License.
"""
Pytest to validate required Omnia services (pulp, kubespray, auth, ochami)
after OIM preparation.
"""

import sys
import os
import pytest
from automation_library.prepareoim import verify_required_services  # pylint: disable=E0401

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


def test_required_services_running():
    """
    Verify pulp, kubespray, auth and ochami containers are running.
    Fail test if any service is missing.
    """
    status, running, missing = verify_required_services()

    if not status:
        pytest.fail(
            f"Some services are missing. Running: {running} | Missing: {missing}"
        )
    assert status
    print(f"All required services are running: {running}")
