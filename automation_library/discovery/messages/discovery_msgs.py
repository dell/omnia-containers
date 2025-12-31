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

"""Discovery - Messages.

Messages for the 5 discovery validation scenarios:
1. Openchami Container
2. Provisioning Images
3. Discovery Playbook Execution
4. Node Boot Validation
5. Package Installation

Author: Dell Technologies
"""

from typing import Dict


DISCOVERY_MSGS: Dict[str, str] = {
    "validation_start": "Starting discovery workflow validation...",
    "validation_pass": "All discovery workflow validations PASSED",
    "validation_fail": "Discovery workflow validation FAILED: {failed_count} check(s) failed",

    "missing_config": "Missing required configuration: {item}",

    # Scenario 1: Openchami Container
    "openchami_running": "OpenCHAMI container {container} is running",
    "openchami_not_running": "OpenCHAMI container {container} is not running",

    # Scenario 2: Provisioning Images
    "s3_images_ok": "All required provisioning images are present in S3",
    "s3_images_missing": "Missing provisioning images in S3: {missing}",
    "s3_images_unexpected": "Unexpected provisioning image groups found in S3 (not present in PXE mapping): {groups}",

    # Scenario 3: Discovery Playbook Execution
    "discovery_ok": "discovery workflow indicates success",
    "discovery_fail": "discovery workflow did not indicate success",

    # Scenario 4: Node Boot Validation
    "nodes_boot_ok": "Nodes reachable via ping and SSH",
    "nodes_boot_fail": "Some nodes are not reachable",

    # Scenario 5: Package Installation
    "packages_ok": "Required packages are installed for all functional groups",
    "packages_missing": "Missing packages detected",

    # Scenario 6: BMC Group CSV validation
    "bmc_group_ok": "BMC Group File is generated correctly",
    "bmc_group_missing": "BMC Group File is missing or invalid",

    # Scenario 7: Slurm Cluster validation
    "slurm_ok": "Slurm Cluster: Services are running; sinfo and srun commands succeed; LDAP authentication works; GPU and IB communication validated.",
    "slurm_fail": "Slurm Cluster validation failed",

    # Scenario 8: Login Node validation
    "login_node_ok": "Login Node: Services (slurmd, sssd, munge) are active; srun works; LDAP authentication succeeds.",
    "login_node_fail": "Login Node validation failed",

    # Scenario 9: Login Compiler Node validation
    "login_compiler_ok": "Login Compiler Node: Same services active; srun works; LDAP authentication succeeds; OpenMPI and UCX installed correctly.",
    "login_compiler_fail": "Login Compiler Node validation failed",

    # Scenario 10: External LDAP Proxy validation
    "external_ldap_ok": "External LDAP Proxy Validation: ldapsearch succeeded and expected user is visible.",
    "external_ldap_fail": "External LDAP Proxy Validation failed",
}

__all__ = ["DISCOVERY_MSGS"]
