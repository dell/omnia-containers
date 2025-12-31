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
Testinfra tests for telemetry verification.

This file contains test functions that verify telemetry deployment was successful.

Usage:
    ./run_molecule.sh telemetry test      # Run playbook + verify
    ./run_molecule.sh telemetry verify    # Verify only
"""

import time
import pytest
from automation_library.core import (
    TestLogger,
    get_node_admin_ip,
)
from automation_library.telemetry.vars import (
    TELEMETRY_VARS,
    K8S_CONTROL_PLANE_FUNCTIONAL_GROUP,
    STABILITY_WAIT_TIME,
)
from automation_library.telemetry.messages import (
    TEST_NAMES,
    TEST_LOG_MSGS as LOG_MSGS,
    TEST_ASSERT_MSGS as ASSERT_MSGS,
)
from automation_library.telemetry.functions import (
    verify_idrac_telemetry_pod_count,
    verify_all_telemetry_pods_running,
)


# =============================================================================
# TEST FUNCTIONS
# =============================================================================

def test_idrac_telemetry_pod_count(host):
    """
    Test Case 1: Verify idrac-telemetry pods count matches expected.

    SSH to K8s control plane via omnia_core container and verify:
    - idrac-telemetry pods count = service_kube_node count + 1 (for mgmt layer)

    Uses get_node_admin_ip() with functional_group or hostname to get admin IP.
    """
    log = TestLogger(TEST_NAMES["idrac_telemetry_pod_count"])

    # Get admin IP by functional_group_name
    log.check("Getting admin IP from PXE mapping file")
    admin_ip = get_node_admin_ip(host, functional_group=K8S_CONTROL_PLANE_FUNCTIONAL_GROUP)
    assert admin_ip, "Failed to get admin IP from PXE mapping file"

    # Verify pod count
    log.check(f"Checking idrac-telemetry pods on {admin_ip}")
    result = verify_idrac_telemetry_pod_count(host, admin_ip)

    details = (
        f"service_kube_node count: {result['service_kube_node_count']}\n"
        f"Expected pods: {result['expected_count']}\n"
        f"Actual pods: {result['actual_count']}\n"
        f"Pods: {result['pods']}"
    )

    if result["success"]:
        log.passed(
            LOG_MSGS["idrac_pod_count_match"].format(expected=result['expected_count']),
            details
        )
    else:
        log.failed(LOG_MSGS["idrac_pod_count_mismatch"], details)

    assert result["success"], ASSERT_MSGS["idrac_pod_count_mismatch"].format(
        expected=result['expected_count'],
        actual=result['actual_count'],
        svc_count=result['service_kube_node_count']
    )


def test_all_telemetry_pods_running(host):
    """
    Test Case 2: Verify all pods in telemetry namespace are running.

    Checks all pods, waits for stability, then rechecks to ensure stability.
    Shows pod output on screen.
    """
    log = TestLogger(TEST_NAMES["all_telemetry_pods_running"])

    # Get admin IP
    log.check("Getting admin IP from PXE mapping file")
    admin_ip = get_node_admin_ip(host, functional_group=K8S_CONTROL_PLANE_FUNCTIONAL_GROUP)
    assert admin_ip, "Failed to get admin IP from PXE mapping file"

    # First check
    log.check("Checking all pods in telemetry namespace")
    result1 = verify_all_telemetry_pods_running(host, admin_ip)

    # Show output
    log.check("Pod status (first check):")
    if result1["output"]:
        for line in result1["output"].strip().split('\n'):
            print(f"    {line}")

    if not result1["success"]:
        not_running_names = [p["name"] for p in result1["not_running_pods"]]
        log.failed(
            LOG_MSGS["some_pods_not_running"].format(
                not_running=result1["not_running_count"],
                total=result1["total_pods"]
            ),
            f"Not running: {not_running_names}"
        )
        assert False, ASSERT_MSGS["telemetry_pods_not_running"].format(
            total=result1["total_pods"],
            running=result1["running_count"],
            not_running=result1["not_running_count"]
        )

    # Wait for stability
    log.check(f"Waiting {STABILITY_WAIT_TIME}s for stability check...")
    time.sleep(STABILITY_WAIT_TIME)

    # Second check (stability)
    log.check("Rechecking pods after wait (stability check)")
    result2 = verify_all_telemetry_pods_running(host, admin_ip)

    # Show output
    log.check("Pod status (stability check):")
    if result2["output"]:
        for line in result2["output"].strip().split('\n'):
            print(f"    {line}")

    if result2["success"]:
        log.passed(
            LOG_MSGS["all_pods_running"].format(total=result2["total_pods"]),
            LOG_MSGS["stability_check_pass"].format(wait_time=STABILITY_WAIT_TIME)
        )
    else:
        not_running_names = [p["name"] for p in result2["not_running_pods"]]
        log.failed(
            LOG_MSGS["some_pods_not_running"].format(
                not_running=result2["not_running_count"],
                total=result2["total_pods"]
            ),
            f"Not running after {STABILITY_WAIT_TIME}s: {not_running_names}"
        )

    assert result2["success"], ASSERT_MSGS["telemetry_pods_not_running"].format(
        total=result2["total_pods"],
        running=result2["running_count"],
        not_running=result2["not_running_count"]
    )
