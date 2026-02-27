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
Discovery Module - Messages and Test Variables.

This module contains all test names, log messages, and assertion messages
for the discovery automation module.
"""

from typing import Dict

# =============================================================================
# TEST NAMES (displayed in reports)
# =============================================================================
TEST_NAMES: Dict[str, str] = {
    "nodes_ssh_reachable": "Verify all PXE mapping nodes are reachable via SSH",
    "ochami_nodes_discovered": "Verify nodes are discovered in OpenCHAMI SMD",
    "nodes_yaml_exists": "Verify nodes.yaml file exists and is valid",
    "passwordless_ssh": "Verify passwordless SSH is configured to all nodes",
    "functional_groups": "Verify functional groups are correctly assigned",
    "bmc_group_data": "Verify BMC group data file is created",
    "node_hostnames": "Verify node hostnames match PXE mapping",
}

# =============================================================================
# LOG MESSAGES (for TestLogger during test execution)
# =============================================================================
TEST_LOG_MSGS: Dict[str, str] = {
    # SSH Reachability
    "nodes_ssh_success": "All {count} nodes are reachable via SSH",
    "nodes_ssh_failed": "{failed_count}/{total_count} nodes are not reachable via SSH",

    # OpenCHAMI Discovery
    "ochami_success": "All {count} nodes discovered in OpenCHAMI SMD",
    "ochami_failed": "{missing_count}/{total_count} nodes missing from OpenCHAMI SMD",

    # nodes.yaml File
    "nodes_yaml_exists": "nodes.yaml file exists and is valid",
    "nodes_yaml_missing": "nodes.yaml file not found at {path}",
    "nodes_yaml_invalid": "nodes.yaml file is invalid: {error}",

    # Passwordless SSH
    "passwordless_ssh_success": "Passwordless SSH configured for all {count} nodes",
    "passwordless_ssh_fail": "Passwordless SSH FAILED for {hostname} ({admin_ip})",

    # Node Hostnames
    "node_hostnames_success": "All {count} node hostnames match PXE mapping",
    "node_hostnames_failed": "{mismatch_count}/{total_count} nodes have hostname mismatches",
    "node_hostnames_mismatch": (
        "Hostname mismatch for {hostname}: expected={expected}, actual={actual}"
    ),
}

# =============================================================================
# ASSERTION MESSAGES (shown when tests fail)
# =============================================================================
TEST_ASSERT_MSGS: Dict[str, str] = {
    "nodes_ssh_failed": """
╔══════════════════════════════════════════════════════════════════════════════╗
║ SSH CONNECTIVITY CHECK FAILED
╠══════════════════════════════════════════════════════════════════════════════╣
║ Failed nodes: {failed_nodes}
║ Total nodes: {total_count}
║ Reachable: {success_count}
║ Unreachable: {failed_count}
║
║ HOW TO FIX:
║   1. Verify nodes are powered on and network is configured
║   2. Check admin network connectivity from OIM:
║      podman exec omnia_core ping {first_failed_ip}
║   3. Verify PXE mapping file has correct IPs:
║      podman exec omnia_core cat /opt/omnia/input/project_default/pxe_mapping_file.csv
║   4. Check SSH service on failed nodes (if accessible via console)
║   5. Verify firewall rules allow SSH from OIM to nodes
║   6. Check if nodes have completed provisioning
╚══════════════════════════════════════════════════════════════════════════════╝
""",

    "ochami_nodes_missing": """
╔══════════════════════════════════════════════════════════════════════════════╗
║ OPENCHAMI NODE DISCOVERY FAILED
╠══════════════════════════════════════════════════════════════════════════════╣
║ Missing nodes: {missing_nodes}
║ Total expected: {total_count}
║ Discovered: {discovered_count}
║ Missing: {missing_count}
║
║ HOW TO FIX:
║   1. Check if discovery playbook ran successfully
║   2. Verify OpenCHAMI SMD status:
║      podman exec omnia_core ochami smd component get
║   3. Check nodes.yaml file was created:
║      podman exec omnia_core cat /opt/omnia/openchami/nodes.yaml
║   4. Re-run discovery manually:
║      podman exec omnia_core ochami discover static -f yaml -d @/opt/omnia/openchami/nodes.yaml --overwrite
║   5. Check OpenCHAMI logs for errors:
║      podman logs openchami-smd
╚══════════════════════════════════════════════════════════════════════════════╝
""",

    "nodes_yaml_missing": """
╔══════════════════════════════════════════════════════════════════════════════╗
║ NODES.YAML FILE NOT FOUND
╠══════════════════════════════════════════════════════════════════════════════╣
║ Expected path: {path}
║
║ HOW TO FIX:
║   1. Verify discovery playbook ran successfully
║   2. Check if file exists:
║      podman exec omnia_core ls -la /opt/omnia/openchami/
║   3. Check discovery playbook logs for errors
║   4. Re-run discovery playbook:
║      cd /path/to/omnia && ansible-playbook discovery/discovery.yml
║   5. Verify PXE mapping file is valid:
║      podman exec omnia_core cat /opt/omnia/input/project_default/pxe_mapping_file.csv
╚══════════════════════════════════════════════════════════════════════════════╝
""",

    "nodes_yaml_invalid": """
╔══════════════════════════════════════════════════════════════════════════════╗
║ NODES.YAML FILE IS INVALID
╠══════════════════════════════════════════════════════════════════════════════╣
║ Path: {path}
║ Error: {error}
║ Missing nodes: {missing_nodes}
║
║ HOW TO FIX:
║   1. Check YAML syntax:
║      podman exec omnia_core cat /opt/omnia/openchami/nodes.yaml | yq .
║   2. Verify all PXE mapping nodes are present in nodes.yaml
║   3. Re-run discovery playbook to regenerate file
║   4. Check for template errors in discovery playbook
╚══════════════════════════════════════════════════════════════════════════════╝
""",

    "passwordless_ssh_failed": """
╔══════════════════════════════════════════════════════════════════════════════╗
║ PASSWORDLESS SSH CONFIGURATION FAILED
╠══════════════════════════════════════════════════════════════════════════════╣
║ Failed nodes: {failed_nodes}
║ Total nodes: {total_count}
║ Configured: {success_count}
║ Failed: {failed_count}
║
║ HOW TO FIX:
║   1. Verify SSH keys are generated on OIM:
║      podman exec omnia_core ls -la /root/.ssh/
║   2. Check if public key is copied to nodes:
║      ssh root@{first_failed_ip} "cat /root/.ssh/authorized_keys"
║   3. Re-run discovery playbook (passwordless_ssh role)
║   4. Manually copy SSH key to failed node:
║      ssh-copy-id root@{first_failed_ip}
║   5. Verify SSH service allows key-based authentication on nodes
╚══════════════════════════════════════════════════════════════════════════════╝
""",

    "node_hostnames_mismatch": """
╔══════════════════════════════════════════════════════════════════════════════╗
║ NODE HOSTNAME MISMATCH
╠══════════════════════════════════════════════════════════════════════════════╣
║ Mismatched nodes: {mismatch_count}/{total_count}
║ Details: {mismatch_details}
║
║ HOW TO FIX:
║   1. Verify hostnames in PXE mapping are correct
║   2. Check if cloud-init configured hostnames on nodes
║   3. Manually set hostname on failed nodes:
║      ssh root@{first_failed_ip} "hostnamectl set-hostname {expected_hostname}"
║   4. Re-run discovery playbook (configure_ochami role)
║   5. Verify hostname.yaml was created:
║      podman exec omnia_core cat /opt/omnia/openchami/hostname.yaml
╚══════════════════════════════════════════════════════════════════════════════╝
""",

}
