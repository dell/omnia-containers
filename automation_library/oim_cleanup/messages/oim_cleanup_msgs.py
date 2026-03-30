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
OIM Cleanup - Test Messages.

All user-facing messages for OIM cleanup verification tests.
"""

# =============================================================================
# Test Names (displayed as test headers)
# =============================================================================
TEST_NAMES = {
    "services_removed": "Verify all OIM services removed",
    "containers_removed": "Verify all OIM containers removed",
    "container_files_removed": "Verify .container files and omnia.target removed",
    "volumes_secrets_removed": "Verify OpenCHAMI volumes and secrets removed",
    "credential_files_removed": "Verify credential files and vault key removed",
    "firewall_ports_removed": "Verify firewall ports removed",
    "directories_removed": "Verify cleanup directories removed",
    "packages_removed": "Verify regctl, s3cmd, openchami packages removed",
    "chronyd_removed": "Verify chronyd removed",
    "auth_removed": "Verify omnia_auth removed",
}

# =============================================================================
# Test Log Messages (displayed as test details)
# =============================================================================
TEST_LOG_MSGS = {
    # Services
    "services_all_removed": "All OIM services removed",
    "services_still_active": "Some OIM services still active",

    # Containers
    "containers_all_removed": "All OIM containers removed",
    "containers_still_present": "Some OIM containers still present",

    # Container files
    "container_files_all_removed": "All .container and omnia.target files removed",
    "container_files_still_present": "Some .container/omnia.target files still present",

    # Volumes/Secrets
    "volumes_secrets_all_removed": "All OpenCHAMI volumes and secrets removed",
    "volumes_secrets_still_present": "Some volumes/secrets still present",

    # Credential files
    "credentials_all_removed": "All credential/metadata files removed",
    "credentials_still_present": "Some credential/metadata files still present",

    # Firewall
    "firewall_all_removed": "All firewall ports removed",
    "firewall_still_open": "Some firewall ports still open",

    # Directories
    "directories_all_removed": "All cleanup directories removed",
    "directories_still_present": "Some cleanup directories still present",

    # Packages
    "packages_all_removed": "regctl binary and openchami packages removed",
    "packages_still_present": "Some packages still installed",

    # chronyd
    "chronyd_removed": "chronyd stopped, disabled, and allow list removed",
    "chronyd_still_active": "chronyd cleanup incomplete",

    # Auth
    "auth_all_removed": "omnia_auth container and files removed",
    "auth_still_present": "omnia_auth cleanup incomplete",
}

# =============================================================================
# Test Assert Messages (displayed on failure)
# =============================================================================
TEST_ASSERT_MSGS = {
    "services_still_active": "Services still active after cleanup: {details}",
    "containers_still_present": "Containers still present after cleanup: {details}",
    "container_files_still_present": ".container files still present: {details}",
    "volumes_secrets_still_present": "Volumes/secrets still present: {details}",
    "credentials_still_present": "Credential files still present: {details}",
    "firewall_still_open": "Firewall ports still open: {details}",
    "directories_still_present": "Directories still present: {details}",
    "packages_still_present": "Packages still installed: {details}",
    "chronyd_still_active": "chronyd cleanup incomplete: {details}",
    "auth_still_present": "omnia_auth cleanup incomplete: {details}",
}
