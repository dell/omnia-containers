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
Prepare OIM - Multi-Subnet Messages.

Test names, log messages, assertion messages, and skip messages
for multi-subnet CoreDHCP verification tests.
"""

from typing import Dict


# =============================================================================
# TEST NAMES — displayed in reports and TestLogger
# =============================================================================
MS_TEST_NAMES: Dict[str, str] = {
    "activate_multi_subnet": (
        "Activate multi-subnet CoreDHCP configuration (6-step process)"
    ),
    "multi_subnet_coredhcp_config": (
        "Verify multi-subnet CoreDHCP configuration after prepare_oim"
    ),
    "multi_subnet_entries_in_coredhcp": (
        "Verify all additional_subnets entries present in coredhcp.yaml"
    ),
    "coresmd_running_image": (
        "Verify running coresmd containers use multi-subnet image"
    ),
}

# =============================================================================
# LOG MESSAGES — for TestLogger during test execution
# =============================================================================
MS_TEST_LOG_MSGS: Dict[str, str] = {
    "activation_ok": (
        "Multi-subnet CoreDHCP activation completed successfully"
    ),
    "activation_failed": (
        "Multi-subnet CoreDHCP activation failed at step {step}"
    ),
    "activation_skipped_already_active": (
        "Multi-subnet mode already active, no activation needed"
    ),
    "coredhcp_file_exists": "coredhcp.yaml exists at {path}",
    "coredhcp_file_missing": "coredhcp.yaml NOT found at {path}",
    "coredhcp_multisubnet_active": (
        "CoreDHCP is in multi-subnet mode (key=value coresmd format)"
    ),
    "coredhcp_commented_mode": (
        "CoreDHCP multi-subnet entries present but commented out "
        "(6-step manual activation or re-run prepare_oim with coresmd >= v0.6.0)"
    ),
    "coredhcp_singlesubnet_active": (
        "CoreDHCP is in single-subnet mode (positional coresmd format)"
    ),
    "coredhcp_singlesubnet_verified": (
        "No additional_subnets configured — CoreDHCP correctly uses "
        "single-subnet mode (legacy positional format)"
    ),
    "coredhcp_singlesubnet_unexpected_multi": (
        "No additional_subnets configured but CoreDHCP is in "
        "multi-subnet mode — expected single-subnet positional format"
    ),
    "coredhcp_transformed": (
        "CoreDHCP successfully transformed to multi-subnet mode"
    ),
    "coredhcp_transform_failed": (
        "CoreDHCP transformation to multi-subnet mode failed"
    ),
    "subnet_entries_ok": (
        "All {count} additional subnet entries found in coredhcp.yaml"
    ),
    "subnet_entries_commented": (
        "All {count} additional subnet entries found in coredhcp.yaml "
        "(commented out — pending activation)"
    ),
    "subnet_entries_missing": (
        "{missing}/{total} subnet entries missing from coredhcp.yaml"
    ),
    "coresmd_image_ok": (
        "All coresmd containers running expected image"
    ),
    "coresmd_image_mismatch": (
        "One or more coresmd containers running wrong image"
    ),
}

# =============================================================================
# ASSERTION MESSAGES — shown when tests fail (include HOW TO FIX)
# =============================================================================
MS_TEST_ASSERT_MSGS: Dict[str, str] = {
    "coredhcp_file_missing": (
        "CoreDHCP config file not found at {path}.\n\n"
        "HOW TO FIX:\n"
        "  1. Verify prepare_oim.yml completed successfully\n"
        "  2. Check if openchami RPM is installed: rpm -qa | grep openchami\n"
        "  3. Check directory exists: ls -la /etc/openchami/configs/\n"
        "  4. Re-run prepare_oim.yml to regenerate the config"
    ),
    "activation_failed": (
        "Multi-subnet CoreDHCP activation failed.\n"
        "Step details:\n{step_details}\n\n"
        "HOW TO FIX:\n"
        "  1. SSH to OIM server and run the 6 steps manually:\n"
        "     podman pull ghcr.io/openchami/coresmd:v0.6.3\n"
        "  2. Edit /etc/openchami/configs/coredhcp.yaml:\n"
        "     - Comment out single-subnet coresmd/bootloop lines\n"
        "     - Uncomment multi-subnet coresmd/bootloop blocks\n"
        "  3. Update image in quadlet files:\n"
        "     sed -i 's|Image=.*coresmd:.*|Image=ghcr.io/openchami/coresmd:v0.6.3|' "
        "/etc/containers/systemd/coresmd-coredhcp.container "
        "/etc/containers/systemd/coresmd-coredns.container\n"
        "  4. systemctl daemon-reload\n"
        "  5. systemctl restart openchami.target"
    ),
    "coredhcp_not_multisubnet": (
        "CoreDHCP is NOT in multi-subnet mode.\n"
        "additional_subnets are configured in network_spec.yml "
        "but coredhcp.yaml still uses single-subnet format.\n\n"
        "HOW TO FIX:\n"
        "  1. Check coresmd image version: "
        "podman inspect coresmd-coredhcp --format '{{{{.Config.Image}}}}'\n"
        "  2. coresmd v0.6.0+ is required for native multi-subnet support\n"
        "  3. If coresmd < v0.6.0, follow the manual 6-step process:\n"
        "     a. Pull new coresmd image: podman pull ghcr.io/openchami/coresmd:v0.6.3\n"
        "     b. Comment out single-subnet coresmd/bootloop lines\n"
        "     c. Uncomment multi-subnet coresmd/bootloop blocks\n"
        "     d. Update image in quadlet files\n"
        "     e. systemctl daemon-reload\n"
        "     f. systemctl restart openchami.target\n"
        "  4. Re-run prepare_oim.yml with coresmd >= v0.6.0"
    ),
    "subnet_entries_missing": (
        "Subnet entries missing from coredhcp.yaml.\n"
        "Missing subnets:\n{missing_details}\n\n"
        "HOW TO FIX:\n"
        "  1. Check network_spec.yml additional_subnets configuration\n"
        "  2. Verify coredhcp.yaml was regenerated: "
        "cat /etc/openchami/configs/coredhcp.yaml\n"
        "  3. Re-run prepare_oim.yml to regenerate config from template\n"
        "  4. Check Ansible template: "
        "coredhcp/coredhcp.yaml.j2 in deploy_containers role"
    ),
    "coresmd_image_mismatch": (
        "Running coresmd containers are not using the expected image.\n"
        "{details}\n\n"
        "HOW TO FIX:\n"
        "  1. systemctl restart openchami.target\n"
        "  2. Verify quadlet files: grep Image= "
        "/etc/containers/systemd/coresmd-*.container\n"
        "  3. systemctl daemon-reload && systemctl restart openchami.target\n"
        "  4. Verify: podman inspect coresmd-coredhcp --format "
        "'{{{{.ImageName}}}}'"
    ),
    "coredhcp_unexpected_multisubnet": (
        "CoreDHCP is in multi-subnet mode but no additional_subnets are "
        "configured in network_spec.yml.\n\n"
        "HOW TO FIX:\n"
        "  1. If multi-subnet is intended, add additional_subnets to "
        "network_spec.yml\n"
        "  2. If single-subnet is intended, re-run prepare_oim.yml to "
        "regenerate coredhcp.yaml in legacy format\n"
        "  3. Inspect config: cat /etc/openchami/configs/coredhcp.yaml"
    ),
}

# =============================================================================
# SKIP MESSAGES — for pytest.skip() calls
# =============================================================================
MS_SKIP_MSGS: Dict[str, str] = {
    "no_additional_subnets": (
        "No additional_subnets configured in network_spec.yml "
        "(single-subnet deployment)"
    ),
}
