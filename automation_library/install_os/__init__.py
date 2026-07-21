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
Install OS module - Functions, messages, and variables for install_os automation.

This module automates the install_os_arm_node playbook execution and validates:
- ISO source exists and checksum matches (precheck)
- Required ISO tooling is available (xorrisofs, isomd5sum)
- Kickstart rendering/injection is correct
- iDRAC virtual media mount and boot operations
- Post-install node state (SSH reachable, correct OS/arch, GUI packages)

Usage:
    from automation_library.install_os.functions import (
        check_source_iso_exists,
        verify_source_iso_checksum,
        check_output_iso_exists,
        check_kickstart_in_iso,
        check_tooling_available,
        check_idrac_reachable,
        check_ssh_reachable,
        verify_os_version,
        verify_architecture,
    )
    from automation_library.install_os.messages import TEST_NAMES
    from automation_library.install_os.vars import INSTALL_OS_VARS
"""
