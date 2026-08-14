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

"""Install OS functions module."""

from .iso_generation_func import (
    check_source_iso_exists,
    verify_source_iso_checksum,
    check_output_iso_exists,
    verify_output_iso_checksum,
    check_kickstart_in_iso,
    verify_grub_config_in_iso,
    check_tooling_available,
    check_manifest_exists,
)

from .idrac_func import (
    check_idrac_reachable,
    check_idrac_lc_status,
    check_os_deployment_job_status,
    check_virtual_media_status,
    check_boot_override_status,
    check_power_state,
    verify_nfs_share_accessible,
)

from .kickstart_func import (
    verify_kickstart_rootpw,
    verify_kickstart_sshkey,
    verify_kickstart_static_ip,
    verify_kickstart_base_environment,
    scan_user_kickstart,
)

from .post_install_func import (
    check_ssh_reachable,
    verify_os_version,
    verify_architecture,
    verify_static_ip_configured,
    verify_gui_packages_installed,
    verify_hostname,
)

from .playbook_func import (
    load_iso_config_from_container,
    run_install_os_playbook,
)

__all__ = [
    # ISO generation
    "check_source_iso_exists",
    "verify_source_iso_checksum",
    "check_output_iso_exists",
    "verify_output_iso_checksum",
    "check_kickstart_in_iso",
    "verify_grub_config_in_iso",
    "check_tooling_available",
    "check_manifest_exists",
    # iDRAC
    "check_idrac_reachable",
    "check_idrac_lc_status",
    "check_os_deployment_job_status",
    "check_virtual_media_status",
    "check_boot_override_status",
    "check_power_state",
    "verify_nfs_share_accessible",
    # Kickstart
    "verify_kickstart_rootpw",
    "verify_kickstart_sshkey",
    "verify_kickstart_static_ip",
    "verify_kickstart_base_environment",
    "scan_user_kickstart",
    # Post-install
    "check_ssh_reachable",
    "verify_os_version",
    "verify_architecture",
    "verify_static_ip_configured",
    "verify_gui_packages_installed",
    "verify_hostname",
    # Playbook helpers
    "load_iso_config_from_container",
    "run_install_os_playbook",
]
