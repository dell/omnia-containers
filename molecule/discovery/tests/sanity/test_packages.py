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
Discovery - Node Package Verification Test Cases.

Runs AFTER cloud-init test (order=2) to verify all required packages
are installed on every provisioned node.

Package lists are derived using the SAME logic as build_image_x86_64 playbook:
  - Reads base image YAML (rhel-<arch>_base-10.0.yaml) from IMAGE_CONFIG_YAML_DIR
    inside omnia_core container via load_container_file (core utility)
  - Finds per-functional-group image YAML
    (rhel-<functional_group>_<uuid>-image-build-10.0.yaml)
  - Combines base packages + compute packages (deduplicated)
  - SSHes to each node and verifies via rpm -qa
  - Reports packages below each node name: INSTALLED (✓ pkg → version)
    and NOT INSTALLED (✗ pkg) - same format as test_build_image_x86_64.py

Test cases:
1. Verify build_stream pipeline stage 'validate-image-on-test' COMPLETED (when enabled)
2. Verify all required packages are installed on all nodes
"""

import pytest

from automation_library.core import (
    TestLogger,
    is_build_stream_enabled,
    get_build_stream_job_id,
    STAGE_VALIDATE_IMAGE,
)
from molecule.conftest import build_stream_job_state
from automation_library.discovery.functions import (
    get_all_slurm_nodes,
    get_k8s_nodes,
    verify_node_packages,
)
from automation_library.discovery.messages import (
    TEST_NAMES, TEST_LOG_MSGS as LOG_MSGS, TEST_ASSERT_MSGS as ASSERT_MSGS,
    SKIP_MSGS,
)


# =============================================================================
# 1. BUILD STREAM JOB STAGE VALIDATION (first test — gates all others)
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(1)
def test_build_stream_job_stage(host):
    """
    Test 1: When build_stream is enabled, verify the validate-image-on-test
    pipeline stage completed successfully before checking node packages.

    - Reads build_stream_job_id override from omnia_test_config.yml if set.
    - Falls back to the latest job in build_stream_db otherwise.
    - Prints the exact DB stage_state if not COMPLETED.
    - Skipped when build_stream is disabled.
    """
    stage = STAGE_VALIDATE_IMAGE
    if not is_build_stream_enabled(host):
        pytest.skip(LOG_MSGS["build_stream_disabled_skip"])

    log = TestLogger(TEST_NAMES["build_stream_job_stage"].format(stage=stage))

    result = get_build_stream_job_id(host, stage_name=stage)
    job_id = result.get("job_id") or "unknown"
    job_state = result.get("job_state") or "NOT FOUND"
    source = result.get("source", "database")

    # Set shared state so autouse fixture in conftest.py can skip remaining tests
    build_stream_job_state["checked"] = True
    build_stream_job_state["success"] = result["success"]
    build_stream_job_state["job_id"] = job_id
    build_stream_job_state["job_state"] = job_state
    build_stream_job_state["error"] = result.get("error", "")

    log.check(LOG_MSGS["build_stream_job_checking"].format(stage=stage, source=source))

    if result["success"]:
        log.passed(
            LOG_MSGS["build_stream_job_ok"].format(
                stage=stage, job_id=job_id, source=source
            )
        )
    else:
        log.failed(
            LOG_MSGS["build_stream_job_failed"].format(
                stage=stage, state=job_state, job_id=job_id
            ),
            result.get("error", "")
        )
        # Use pytest.fail() so this test shows as FAILED (not skipped)
        # Remaining tests will be SKIPPED via autouse fixture
        pytest.fail(
            ASSERT_MSGS["build_stream_job_stage_failed"].format(
                stage=stage, job_id=job_id, state=job_state
            )
        )


# =============================================================================
# 2. NODE PACKAGE VERIFICATION TEST
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(2)
def test_node_packages_installed(host):
    """
    Test Case 1: Verify all required packages are installed on all nodes.

    Runs after cloud-init (order=2) - nodes are confirmed booted before this.

    For each node in PXE mapping:
    - Reads base image YAML + per-functional-group image YAML from
      IMAGE_CONFIG_YAML_DIR inside omnia_core (same YAMLs build_image_x86_64 uses)
    - Combines base + compute packages (deduplicated)
    - SSHs to node and verifies via rpm -qa
    - Reports INSTALLED and NOT INSTALLED packages below each node name

    Skips if no nodes are found in PXE mapping.
    """
    log = TestLogger(TEST_NAMES["node_packages"])

    slurm_nodes = get_all_slurm_nodes(host)
    k8s_nodes = get_k8s_nodes(host)
    all_nodes = slurm_nodes + k8s_nodes

    if not all_nodes:
        log.skipped(
            SKIP_MSGS["no_nodes_for_packages"],
            "Test skipped - no nodes in PXE mapping"
        )
        pytest.skip(SKIP_MSGS["no_nodes_for_packages"])

    log.check(
        f"Verifying packages on {len(all_nodes)} nodes "
        f"(packages from image YAMLs in IMAGE_CONFIG_YAML_DIR - same source as build_image)"
    )

    result = verify_node_packages(host, all_nodes)

    # Build detailed per-node output - same format as test_build_image_x86_64.py
    details_lines = []
    for node_result in result.get("results", []):
        hostname = node_result["hostname"]
        expected = len(node_result.get("found_packages", [])) + len(node_result.get("missing_packages", []))
        found = len(node_result.get("found_packages", []))
        status = "\u2713" if node_result["success"] else "\u2717"

        details_lines.append(f"{status} {hostname}: {found}/{expected} packages")

        pkg_details = node_result.get("package_details", [])
        installed = [p for p in pkg_details if p["status"] == "installed"]
        not_installed = [p for p in pkg_details if p["status"] == "missing"]

        if installed:
            details_lines.append(f"    INSTALLED ({len(installed)}):")
            for pkg in installed:
                details_lines.append(f"      \u2713 {pkg['expected']} \u2192 {pkg['found']}")

        if not_installed:
            details_lines.append(f"    NOT INSTALLED ({len(not_installed)}):")
            for pkg in not_installed:
                details_lines.append(f"      \u2717 {pkg['expected']}")

        if node_result.get("error") and not node_result["success"]:
            details_lines.append(f"    Error: {node_result['error']}")

    details = "\n".join(details_lines)

    if result["success"]:
        log.passed(
            LOG_MSGS["packages_ok"].format(count=result["total"]),
            details
        )
    else:
        log.failed(
            LOG_MSGS["packages_fail"].format(
                failed=result["failed"], total=result["total"]
            ),
            details
        )
        assert False, ASSERT_MSGS["packages_failed"].format(
            failed_nodes=", ".join(result["nodes_missing_packages"]),
            details=details
        )
