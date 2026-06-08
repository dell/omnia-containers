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
Build Stream - Generated Input Verification Tests.

Verifies that the generated input config files in
/opt/omnia/input/project_default/config/ match the source config files
from the Omnia repository.

For each software in software_config.json:
  - Clones the Omnia repo (branch from omnia_test_config.yml, REQUIRED)
  - Reads the generated JSON from omnia_core container
  - Reads the source JSON from the cloned Omnia repo
  - Compares packages by name+tag: missing, extra, version mismatches
  - Fails immediately if any package from the source is missing,
    any extra package is found, or any version/attribute mismatches

This test is standalone and does NOT depend on job_id or pipeline state.
It can be run individually at any time.

Test Order (after test_autotrigger_pipeline.py):
  - Order 40: Verify generated input configs
"""

import pytest

from automation_library.core import TestLogger, is_build_stream_enabled
from automation_library.build_stream import (
    clone_omnia_repo,
    cleanup_omnia_clone,
    verify_generated_inputs,
    TEST_NAMES,
    TEST_LOG_MSGS,
    TEST_ASSERT_MSGS,
    SKIP_MSGS,
)


# =============================================================================
# 40. VERIFY GENERATED INPUT CONFIGS
# =============================================================================

@pytest.mark.sanity
@pytest.mark.order(40)
def test_verify_generated_inputs(host):
    """
    Test Case 40: Verify generated input config files match Omnia source.

    Steps:
      1. Clone Omnia repo (branch from omnia_branch in omnia_test_config.yml)
      2. Read software_config.json from omnia_core container
      3. For each software and architecture, compare:
         - Missing packages (expected in source, got none in generated)
         - Extra packages (not in source, found in generated)
         - Version/attribute mismatches (expected vs got)
      4. Cleanup the cloned repo
      5. Fail if any differences are found

    omnia_branch MUST be set in omnia_test_config.yml. No fallback.
    """
    if not is_build_stream_enabled(host):
        pytest.skip(SKIP_MSGS["build_stream_disabled"])

    log = TestLogger(TEST_NAMES["verify_generated_inputs"])
    log.check("Cloning Omnia repository and verifying generated input configs")

    clone_result = clone_omnia_repo(host)

    if not clone_result["success"]:
        log.failed(
            TEST_LOG_MSGS["clone_fail"].format(
                error=clone_result["error"]
            ),
            clone_result["error"],
        )
        assert False, TEST_ASSERT_MSGS["clone_failed"].format(
            error=clone_result["error"],
        )

    log.check(
        f"Comparing generated configs with source "
        f"(branch: {clone_result['branch']})"
    )

    try:
        result = verify_generated_inputs(
            host, clone_path=clone_result["clone_path"],
        )
    finally:
        cleanup_omnia_clone(host, clone_result["clone_path"])

    if result["success"]:
        log.passed(
            TEST_LOG_MSGS["generated_inputs_ok"],
            result["summary"],
        )
    else:
        log.failed(
            TEST_LOG_MSGS["generated_inputs_fail"],
            result["summary"],
        )

    assert result["success"], TEST_ASSERT_MSGS[
        "generated_inputs_failed"
    ].format(summary=result["summary"])
