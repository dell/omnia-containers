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

"""Post-install verification functions for install_os automation."""

from typing import Dict, Any

from automation_library.core import run_on_oim, run_on_remote_node


def check_ssh_reachable(
    host, node_ip: str, ssh_key_path: str = "/root/.ssh/id_rsa"
) -> Dict[str, Any]:
    """Verify target node is reachable via SSH with OIM key."""
    cmd = run_on_oim(
        host,
        f"ssh -o StrictHostKeyChecking=no -o ConnectTimeout=10 "
        f"-i {ssh_key_path} root@{node_ip} 'echo CONNECTED' 2>/dev/null",
    )
    connected = cmd.rc == 0 and "CONNECTED" in cmd.stdout
    return {
        "success": connected,
        "node_ip": node_ip,
        "error": "" if connected else f"SSH not reachable at {node_ip}",
    }


def verify_os_version(
    host, node_ip: str, expected_version: str = "10"
) -> Dict[str, Any]:
    """Verify RHEL version on the installed node."""
    cmd = run_on_oim(
        host,
        f"ssh -o StrictHostKeyChecking=no -o ConnectTimeout=10 "
        f"root@{node_ip} 'cat /etc/redhat-release' 2>/dev/null",
    )
    if cmd.rc != 0:
        return {
            "success": False,
            "version": "",
            "error": f"Failed to read OS version: {cmd.stderr.strip()}",
        }
    version_str = cmd.stdout.strip()
    matches = expected_version in version_str
    return {
        "success": matches,
        "version": version_str,
        "expected": expected_version,
        "error": "" if matches else f"Expected RHEL {expected_version}, got: {version_str}",
    }


def verify_architecture(
    host, node_ip: str, expected_arch: str = "aarch64"
) -> Dict[str, Any]:
    """Verify architecture of the installed node."""
    cmd = run_on_oim(
        host,
        f"ssh -o StrictHostKeyChecking=no -o ConnectTimeout=10 "
        f"root@{node_ip} 'uname -m' 2>/dev/null",
    )
    if cmd.rc != 0:
        return {
            "success": False,
            "arch": "",
            "error": f"Failed to read architecture: {cmd.stderr.strip()}",
        }
    actual = cmd.stdout.strip()
    matches = actual == expected_arch
    return {
        "success": matches,
        "arch": actual,
        "expected": expected_arch,
        "error": "" if matches else f"Expected {expected_arch}, got: {actual}",
    }


def verify_static_ip_configured(
    host, node_ip: str, expected_ip: str
) -> Dict[str, Any]:
    """Verify static admin/PXE IP is configured on the installed node."""
    cmd = run_on_oim(
        host,
        f"ssh -o StrictHostKeyChecking=no -o ConnectTimeout=10 "
        f"root@{node_ip} \"ip -4 addr show | grep '{expected_ip}'\" 2>/dev/null",
    )
    found = cmd.rc == 0 and expected_ip in cmd.stdout
    return {
        "success": found,
        "expected_ip": expected_ip,
        "error": "" if found else f"Static IP {expected_ip} not configured on node",
    }


def verify_gui_packages_installed(host, node_ip: str) -> Dict[str, Any]:
    """Verify Server with GUI packages are installed."""
    cmd = run_on_oim(
        host,
        f"ssh -o StrictHostKeyChecking=no -o ConnectTimeout=10 "
        f"root@{node_ip} 'systemctl get-default' 2>/dev/null",
    )
    if cmd.rc != 0:
        return {
            "success": False,
            "default_target": "",
            "error": f"Failed to check default target: {cmd.stderr.strip()}",
        }
    default_target = cmd.stdout.strip()
    # Check for gnome/gdm packages as indicator of GUI install
    pkg_cmd = run_on_oim(
        host,
        f"ssh -o StrictHostKeyChecking=no -o ConnectTimeout=10 "
        f"root@{node_ip} 'rpm -q gnome-shell 2>/dev/null && echo GUI_FOUND || echo GUI_NOT_FOUND'",
    )
    gui_installed = "GUI_FOUND" in pkg_cmd.stdout
    return {
        "success": gui_installed,
        "default_target": default_target,
        "gui_installed": gui_installed,
        "error": "" if gui_installed else "Server with GUI packages not found",
    }


def verify_hostname(
    host, node_ip: str, expected_hostname: str
) -> Dict[str, Any]:
    """Verify hostname of the installed node."""
    cmd = run_on_oim(
        host,
        f"ssh -o StrictHostKeyChecking=no -o ConnectTimeout=10 "
        f"root@{node_ip} 'hostname' 2>/dev/null",
    )
    if cmd.rc != 0:
        return {
            "success": False,
            "hostname": "",
            "error": f"Failed to read hostname: {cmd.stderr.strip()}",
        }
    actual = cmd.stdout.strip()
    matches = actual == expected_hostname
    return {
        "success": matches,
        "hostname": actual,
        "expected": expected_hostname,
        "error": "" if matches else f"Expected hostname '{expected_hostname}', got: '{actual}'",
    }
