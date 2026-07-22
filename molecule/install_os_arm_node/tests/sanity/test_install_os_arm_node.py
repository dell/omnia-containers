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
Sanity tests for install_os_arm_node playbook.

These tests validate the complete AArch64 unattended OS installation workflow:
- Pre-flight checks (ISO source, tooling, iDRAC reachability)
- ISO generation (repacked ISO with Kickstart and GRUB2)
- Kickstart content validation
- Post-install node state (SSH, OS version, architecture, GUI packages)
"""

import pytest

from automation_library.core import TestLogger
from automation_library.install_os.functions import (
    check_source_iso_exists,
    check_tooling_available,
    check_output_iso_exists,
    check_kickstart_in_iso,
    verify_grub_config_in_iso,
    check_manifest_exists,
    check_idrac_reachable,
    check_idrac_lc_status,
    check_os_deployment_job_status,
    verify_nfs_share_accessible,
    verify_kickstart_rootpw,
    verify_kickstart_sshkey,
    verify_kickstart_static_ip,
    verify_kickstart_base_environment,
    check_ssh_reachable,
    verify_os_version,
    verify_architecture,
    verify_static_ip_configured,
    verify_gui_packages_installed,
    verify_hostname,
)
from automation_library.install_os.messages import (
    TEST_NAMES,
    TEST_LOG_MSGS,
    TEST_ASSERT_MSGS,
)
from automation_library.install_os.vars import INSTALL_OS_VARS


# =============================================================================
# Pre-flight Check Tests
# =============================================================================

class TestPreflightChecks:
    """Pre-flight validation tests for install_os_arm_node."""

    @pytest.mark.sanity
    @pytest.mark.order(1)
    def test_source_iso_exists(self, host):
        """TC-20: Verify source ISO exists at configured path."""
        log = TestLogger(TEST_NAMES["source_iso_exists"])

        log.check("Checking source ISO exists")
        result = check_source_iso_exists(host)

        if result["success"]:
            log.passed(TEST_LOG_MSGS["source_iso_found"].format(path=result["path"]))
        else:
            log.failed(TEST_LOG_MSGS["source_iso_not_found"].format(path=result["path"]))

        assert result["success"], TEST_ASSERT_MSGS["source_iso_not_found"].format(
            path=result["path"]
        )

    @pytest.mark.sanity
    @pytest.mark.order(2)
    def test_tooling_available(self, host):
        """TC-21: Verify required ISO tooling is installed."""
        log = TestLogger(TEST_NAMES["tooling_available"])

        log.check("Checking required ISO tools")
        result = check_tooling_available(host)

        tools_str = ", ".join(result.get("checked", []))
        if result["success"]:
            log.passed(TEST_LOG_MSGS["tools_available"].format(tools=tools_str))
        else:
            missing_str = ", ".join(result.get("missing", []))
            log.failed(TEST_LOG_MSGS["tools_missing"].format(missing=missing_str))

        assert result["success"], TEST_ASSERT_MSGS["tools_missing"].format(
            missing=", ".join(result.get("missing", []))
        )


# =============================================================================
# ISO Generation Tests
# =============================================================================

class TestISOGeneration:
    """ISO generation validation tests."""

    @pytest.mark.sanity
    @pytest.mark.order(10)
    def test_output_iso_exists(self, host):
        """TC-01: Verify repacked ISO was created."""
        log = TestLogger(TEST_NAMES["output_iso_exists"])

        log.check("Checking repacked ISO exists")
        result = check_output_iso_exists(host)

        if result["success"]:
            log.passed(
                TEST_LOG_MSGS["output_iso_found"].format(path=result["iso_path"])
            )
        else:
            log.failed(
                TEST_LOG_MSGS["output_iso_not_found"].format(
                    path=INSTALL_OS_VARS["default_iso_target_directory"]
                )
            )

        assert result["success"], TEST_ASSERT_MSGS["output_iso_not_found"].format(
            path=INSTALL_OS_VARS["default_iso_target_directory"]
        )

    @pytest.mark.sanity
    @pytest.mark.order(11)
    def test_kickstart_in_iso(self, host):
        """TC-01: Verify kickstart.ks is embedded in repacked ISO."""
        log = TestLogger(TEST_NAMES["kickstart_in_iso"])

        iso_result = check_output_iso_exists(host)
        if not iso_result["success"]:
            log.skipped("Repacked ISO not found, skipping")
            pytest.skip("Repacked ISO not found")

        log.check("Checking kickstart.ks in ISO")
        result = check_kickstart_in_iso(host, iso_result["iso_path"])

        if result["success"]:
            log.passed(TEST_LOG_MSGS["kickstart_found"])
        else:
            log.failed(TEST_LOG_MSGS["kickstart_not_found"])

        assert result["success"], TEST_ASSERT_MSGS["kickstart_not_in_iso"]

    @pytest.mark.sanity
    @pytest.mark.order(12)
    def test_grub_config_in_iso(self, host):
        """TC-01: Verify GRUB2 config references kickstart.ks."""
        log = TestLogger(TEST_NAMES["grub_config_in_iso"])

        iso_result = check_output_iso_exists(host)
        if not iso_result["success"]:
            log.skipped("Repacked ISO not found, skipping")
            pytest.skip("Repacked ISO not found")

        log.check("Checking GRUB2 config in ISO")
        result = verify_grub_config_in_iso(host, iso_result["iso_path"])

        if result["success"]:
            log.passed(TEST_LOG_MSGS["grub_config_ok"])
        else:
            log.failed(TEST_LOG_MSGS["grub_config_missing"])

        assert result["success"], TEST_ASSERT_MSGS["grub_config_missing"]

    @pytest.mark.sanity
    @pytest.mark.order(13)
    def test_manifest_exists(self, host):
        """Verify install manifest was generated."""
        log = TestLogger(TEST_NAMES["manifest_exists"])

        log.check("Checking install manifest")
        result = check_manifest_exists(host)

        if result["success"]:
            log.passed(TEST_LOG_MSGS["manifest_found"].format(path=result["path"]))
        else:
            log.failed(TEST_LOG_MSGS["manifest_not_found"].format(path=result["path"]))

        assert result["success"], f"Manifest not found at {result['path']}"


# =============================================================================
# iDRAC Validation Tests
# =============================================================================

class TestIDRACValidation:
    """iDRAC connectivity and status validation tests."""

    @pytest.mark.sanity
    @pytest.mark.order(20)
    def test_idrac_reachable(self, host):
        """TC-22: Verify iDRAC BMC is reachable via Redfish API."""
        log = TestLogger(TEST_NAMES["idrac_reachable"])

        # Skip if no BMC IP configured in test config
        bmc_ip = INSTALL_OS_VARS.get("test_bmc_ip", "")
        if not bmc_ip:
            log.skipped("No test BMC IP configured", "Set test_bmc_ip in vars")
            pytest.skip("No test BMC IP configured")

        log.check(f"Checking iDRAC at {bmc_ip}")
        result = check_idrac_reachable(host, bmc_ip)

        if result["success"]:
            log.passed(
                TEST_LOG_MSGS["idrac_reachable"].format(
                    bmc_ip=bmc_ip, status_code=result["status_code"]
                )
            )
        else:
            log.failed(
                TEST_LOG_MSGS["idrac_not_reachable"].format(
                    bmc_ip=bmc_ip, status_code=result["status_code"]
                )
            )

        assert result["success"], TEST_ASSERT_MSGS["idrac_not_reachable"].format(
            bmc_ip=bmc_ip, status_code=result["status_code"]
        )

    @pytest.mark.sanity
    @pytest.mark.order(21)
    def test_nfs_share_accessible(self, host):
        """Verify NFS share is accessible from OIM."""
        log = TestLogger(TEST_NAMES["nfs_share_accessible"])

        nfs_share = INSTALL_OS_VARS.get("test_nfs_share", "")
        if not nfs_share:
            log.skipped("No test NFS share configured", "Set test_nfs_share in vars")
            pytest.skip("No test NFS share configured")

        log.check(f"Checking NFS share: {nfs_share}")
        result = verify_nfs_share_accessible(host, nfs_share)

        if result["success"]:
            log.passed(
                TEST_LOG_MSGS["nfs_share_reachable"].format(
                    nfs_server=result.get("nfs_server", ""),
                    nfs_path=result.get("nfs_path", "")
                )
            )
        else:
            log.failed(
                TEST_LOG_MSGS["nfs_share_not_reachable"].format(
                    error=result.get("error", "Unknown error")
                )
            )

        assert result["success"], TEST_ASSERT_MSGS["nfs_share_not_accessible"].format(
            error=result.get("error", "Unknown error")
        )

    @pytest.mark.sanity
    @pytest.mark.order(22)
    def test_os_deployment_job_status(self, host):
        """Verify iDRAC OS deployment job status."""
        log = TestLogger(TEST_NAMES["os_deployment_job"])

        bmc_ip = INSTALL_OS_VARS.get("test_bmc_ip", "")
        if not bmc_ip:
            log.skipped("No test BMC IP configured", "Set test_bmc_ip in vars")
            pytest.skip("No test BMC IP configured")

        log.check(f"Checking OS deployment job at {bmc_ip}")
        result = check_os_deployment_job_status(host, bmc_ip)

        if result["success"] and result.get("job_status") not in ["not_found", "unknown"]:
            log.passed(
                TEST_LOG_MSGS["os_deployment_job_found"].format(
                    job_name=result.get("job_name", ""),
                    job_status=result.get("job_status", "")
                )
            )
        else:
            log.failed(TEST_LOG_MSGS["os_deployment_job_not_found"])

        assert result["success"], TEST_ASSERT_MSGS["os_deployment_job_not_found"]


# =============================================================================
# Post-Install Validation Tests
# =============================================================================

class TestPostInstallValidation:
    """Post-install node state validation tests."""

    @pytest.mark.sanity
    @pytest.mark.order(30)
    def test_ssh_reachable(self, host):
        """TC-04: Verify installed node is reachable via SSH with OIM key."""
        log = TestLogger(TEST_NAMES["ssh_reachable"])

        node_ip = INSTALL_OS_VARS.get("test_node_ip", "")
        if not node_ip:
            log.skipped("No test node IP configured", "Set test_node_ip in vars")
            pytest.skip("No test node IP configured")

        log.check(f"Checking SSH to {node_ip}")
        result = check_ssh_reachable(host, node_ip)

        if result["success"]:
            log.passed(TEST_LOG_MSGS["ssh_connected"].format(node_ip=node_ip))
        else:
            log.failed(TEST_LOG_MSGS["ssh_failed"].format(node_ip=node_ip))

        assert result["success"], TEST_ASSERT_MSGS["ssh_not_reachable"].format(
            node_ip=node_ip
        )

    @pytest.mark.sanity
    @pytest.mark.order(31)
    def test_os_version(self, host):
        """TC-05: Verify installed OS version matches expected RHEL version."""
        log = TestLogger(TEST_NAMES["os_version"])

        node_ip = INSTALL_OS_VARS.get("test_node_ip", "")
        if not node_ip:
            log.skipped("No test node IP configured")
            pytest.skip("No test node IP configured")

        expected = INSTALL_OS_VARS["expected_os_version"]
        log.check(f"Checking OS version on {node_ip}")
        result = verify_os_version(host, node_ip, expected)

        if result["success"]:
            log.passed(
                TEST_LOG_MSGS["os_version_match"].format(version=result["version"])
            )
        else:
            log.failed(
                TEST_LOG_MSGS["os_version_mismatch"].format(
                    expected=expected, actual=result.get("version", "unknown")
                )
            )

        assert result["success"], TEST_ASSERT_MSGS["os_version_mismatch"].format(
            expected=expected, actual=result.get("version", "unknown")
        )

    @pytest.mark.sanity
    @pytest.mark.order(32)
    def test_architecture(self, host):
        """TC-05: Verify installed node architecture is aarch64."""
        log = TestLogger(TEST_NAMES["architecture"])

        node_ip = INSTALL_OS_VARS.get("test_node_ip", "")
        if not node_ip:
            log.skipped("No test node IP configured")
            pytest.skip("No test node IP configured")

        expected = INSTALL_OS_VARS["expected_arch"]
        log.check(f"Checking architecture on {node_ip}")
        result = verify_architecture(host, node_ip, expected)

        if result["success"]:
            log.passed(TEST_LOG_MSGS["arch_match"].format(arch=result["arch"]))
        else:
            log.failed(
                TEST_LOG_MSGS["arch_mismatch"].format(
                    expected=expected, actual=result.get("arch", "unknown")
                )
            )

        assert result["success"], TEST_ASSERT_MSGS["arch_mismatch"].format(
            expected=expected, actual=result.get("arch", "unknown")
        )

    @pytest.mark.sanity
    @pytest.mark.order(33)
    def test_gui_packages_installed(self, host):
        """TC-03: Verify Server with GUI packages are installed."""
        log = TestLogger(TEST_NAMES["gui_packages"])

        node_ip = INSTALL_OS_VARS.get("test_node_ip", "")
        if not node_ip:
            log.skipped("No test node IP configured")
            pytest.skip("No test node IP configured")

        log.check(f"Checking GUI packages on {node_ip}")
        result = verify_gui_packages_installed(host, node_ip)

        details = f"Default target: {result.get('default_target', 'unknown')}"
        if result["success"]:
            log.passed(
                TEST_LOG_MSGS["gui_installed"].format(
                    target=result.get("default_target", "unknown")
                ),
                details,
            )
        else:
            log.failed(TEST_LOG_MSGS["gui_not_installed"], details)

        assert result["success"], TEST_ASSERT_MSGS["gui_not_installed"]
