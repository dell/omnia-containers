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
Discovery Output Verification Test Cases.

Verifies discovery playbook output artifacts inside omnia_core container:
1. Nodes.yaml generated from mapping input
2. BSS boot templates created per functional group
3. Cloud-init templates created per functional group

These run as the FIRST tests (order 6-8) after SSH tests, before Slurm tests.
"""

import pytest
from automation_library.core import TestLogger
from automation_library.discovery.functions import (
    verify_nodes_yaml_generated,
    verify_bss_templates_created,
    verify_cloudinit_templates_created,
)
from automation_library.discovery.messages import (
    TEST_NAMES,
    TEST_LOG_MSGS as LOG_MSGS,
    TEST_ASSERT_MSGS as ASSERT_MSGS,
)


@pytest.mark.sanity
@pytest.mark.order(2)
def test_nodes_yaml_generated(host):
    """
    Test Case 6: Verify nodes.yaml is generated completely and accurately
    from mapping input.

    Checks:
    - nodes.yaml file exists in openchami workdir/nodes
    - File is non-empty and valid
    - Valid mapping CSV file present
    """
    log = TestLogger(TEST_NAMES["nodes_yaml_generated"])

    log.check("Checking nodes.yaml generation from PXE mapping input")

    result = verify_nodes_yaml_generated(host)

    if result["success"]:
        log.passed(
            LOG_MSGS["nodes_yaml_ok"],
            result["details"]
        )
    else:
        log.failed(
            LOG_MSGS["nodes_yaml_fail"],
            result.get("error", "")
        )
        assert False, ASSERT_MSGS["nodes_yaml_failed"].format(
            details=result.get("error", "")
        )


@pytest.mark.sanity
@pytest.mark.order(3)
def test_bss_templates_created(host):
    """
    Test Case 7: Verify BSS boot templates are created per functional group.

    Checks:
    - BSS boot directory exists inside omnia_core container
    - Templates present for each functional group in PXE mapping
    """
    log = TestLogger(TEST_NAMES["bss_templates_created"])

    log.check("Checking BSS boot templates per functional group")

    result = verify_bss_templates_created(host)

    if result["success"]:
        log.passed(
            LOG_MSGS["bss_templates_ok"].format(
                count=len(result.get("functional_groups", []))
            ),
            result["details"]
        )
    else:
        log.failed(
            LOG_MSGS["bss_templates_fail"].format(
                missing=len(result.get("missing_groups", []))
            ),
            result.get("error", result.get("details", ""))
        )
        assert False, ASSERT_MSGS["bss_templates_failed"].format(
            details=result.get("error", result.get("details", ""))
        )


@pytest.mark.sanity
@pytest.mark.order(4)
def test_cloudinit_templates_created(host):
    """
    Test Case 8: Verify cloud-init templates are created per functional group.

    Checks:
    - Cloud-init template directory exists inside omnia_core container
    - Templates present for each functional group in PXE mapping
    """
    log = TestLogger(TEST_NAMES["cloudinit_templates_created"])

    log.check("Checking cloud-init templates per functional group")

    result = verify_cloudinit_templates_created(host)

    if result["success"]:
        log.passed(
            LOG_MSGS["cloudinit_templates_ok"].format(
                count=len(result.get("functional_groups", []))
            ),
            result["details"]
        )
    else:
        log.failed(
            LOG_MSGS["cloudinit_templates_fail"].format(
                missing=len(result.get("missing_groups", []))
            ),
            result.get("error", result.get("details", ""))
        )
        assert False, ASSERT_MSGS["cloudinit_templates_failed"].format(
            details=result.get("error", result.get("details", ""))
        )
