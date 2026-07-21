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

"""Kickstart verification functions for install_os automation."""

from typing import Dict, Any

from automation_library.core import run_on_oim


def verify_kickstart_rootpw(host, kickstart_path: str) -> Dict[str, Any]:
    """Verify rootpw directive is present in the Kickstart file."""
    cmd = run_on_oim(host, f"grep -c '^rootpw' {kickstart_path} 2>/dev/null")
    count = int(cmd.stdout.strip()) if cmd.rc == 0 else 0
    return {
        "success": count > 0,
        "count": count,
        "error": "" if count > 0 else "rootpw directive not found in Kickstart",
    }


def verify_kickstart_sshkey(host, kickstart_path: str) -> Dict[str, Any]:
    """Verify sshkey directive is present in the Kickstart file."""
    cmd = run_on_oim(host, f"grep -c '^sshkey' {kickstart_path} 2>/dev/null")
    count = int(cmd.stdout.strip()) if cmd.rc == 0 else 0
    return {
        "success": count > 0,
        "count": count,
        "error": "" if count > 0 else "sshkey directive not found in Kickstart",
    }


def verify_kickstart_static_ip(
    host, kickstart_path: str, expected_ip: str
) -> Dict[str, Any]:
    """Verify static IP address is configured in the Kickstart file."""
    cmd = run_on_oim(
        host, f"grep 'network.*--ip={expected_ip}' {kickstart_path} 2>/dev/null"
    )
    found = cmd.rc == 0 and expected_ip in cmd.stdout
    return {
        "success": found,
        "expected_ip": expected_ip,
        "error": "" if found else f"Static IP {expected_ip} not found in Kickstart",
    }


def verify_kickstart_base_environment(
    host, kickstart_path: str
) -> Dict[str, Any]:
    """Verify Server with GUI base environment is configured."""
    cmd = run_on_oim(
        host, f"grep -E '@\\^graphical-server-environment' {kickstart_path} 2>/dev/null"
    )
    found = cmd.rc == 0
    return {
        "success": found,
        "error": "" if found else "graphical-server-environment not found in Kickstart",
    }


def scan_user_kickstart(host, kickstart_path: str) -> Dict[str, Any]:
    """Scan user-provided Kickstart for required directives."""
    has_rootpw = verify_kickstart_rootpw(host, kickstart_path)["success"]
    has_sshkey = verify_kickstart_sshkey(host, kickstart_path)["success"]
    return {
        "success": True,
        "has_rootpw": has_rootpw,
        "has_sshkey": has_sshkey,
        "warnings": [
            w for w in [
                "rootpw directive missing" if not has_rootpw else None,
                "sshkey directive missing" if not has_sshkey else None,
            ] if w
        ],
        "error": "",
    }
