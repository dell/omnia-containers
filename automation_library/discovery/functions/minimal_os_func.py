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
Minimal OS - Core Functions.

This module contains all verification functions for the Minimal OS automation tests.
Each function returns a result dict with 'success', 'details', and optional 'error' keys.
"""

import json
import yaml
import csv
from io import StringIO

from automation_library.discovery.vars.minimal_os_vars import (
    FUNCTIONAL_GROUPS,
    BASE_PACKAGES,
    LDMS_PACKAGES,
    EXCLUDED_PACKAGE_PATTERNS,
    EXCLUDED_SERVICES,
    REQUIRED_SERVICES,
    IMAGE_PATHS,
)


# =============================================================================
# NODE DISCOVERY FUNCTIONS
# =============================================================================

def get_pxe_mapping(host):
    """
    Get PXE mapping configuration from OIM.
    
    Supports both YAML and CSV formats.
    
    Returns:
        dict: PXE mapping data or None if not found
    """
    # Try YAML paths first
    yaml_paths = [
        "/opt/omnia/oim_shared/input/pxe_mapping.yaml",
        "/etc/omnia/pxe_mapping.yaml",
        "/opt/omnia/config/pxe_mapping.yaml",
    ]
    
    for path in yaml_paths:
        result = host.run(f"cat {path} 2>/dev/null")
        if result.rc == 0 and result.stdout.strip():
            try:
                return yaml.safe_load(result.stdout)
            except yaml.YAMLError:
                continue
    
    # Try CSV paths
    csv_paths = [
        "/opt/omnia/input/project_default/pxe_mapping_file.csv",
        "/opt/omnia/oim_shared/input/pxe_mapping_file.csv",
        "/etc/omnia/pxe_mapping_file.csv",
    ]
    
    for path in csv_paths:
        result = host.run(f"cat {path} 2>/dev/null")
        if result.rc == 0 and result.stdout.strip():
            try:
                # Parse CSV and convert to dict format
                pxe_dict = {}
                csv_reader = csv.DictReader(StringIO(result.stdout))
                for row in csv_reader:
                    hostname = row.get('HOSTNAME', '').strip()
                    if hostname:
                        pxe_dict[hostname] = {
                            'admin_ip': row.get('ADMIN_IP', '').strip(),
                            'hostname': hostname,
                            'functional_group': row.get('FUNCTIONAL_GROUP_NAME', '').strip(),
                            'service_tag': row.get('SERVICE_TAG', '').strip(),
                            'bmc_ip': row.get('BMC_IP', '').strip(),
                        }
                return pxe_dict if pxe_dict else None
            except Exception:
                continue
    
    return None


def get_minimal_os_nodes(host, functional_group=None):
    """
    Get nodes assigned to minimal OS functional groups.
    
    Args:
        host: Testinfra host
        functional_group: Optional specific group (os_x86_64 or os_aarch64)
    
    Returns:
        list: List of node dicts with name, admin_ip, functional_group
    """
    pxe_mapping = get_pxe_mapping(host)
    if not pxe_mapping:
        return []
    
    nodes = []
    target_groups = [functional_group] if functional_group else list(FUNCTIONAL_GROUPS.values())
    
    for node_name, node_config in pxe_mapping.items():
        if not isinstance(node_config, dict):
            continue
        
        node_group = node_config.get("functional_group", "")
        if node_group in target_groups:
            nodes.append({
                "name": node_name,
                "admin_ip": node_config.get("admin_ip", ""),
                "hostname": node_config.get("hostname", node_name),
                "functional_group": node_group,
            })
    
    return nodes


def get_test_node(host, functional_group=None):
    """
    Get first available test node with admin IP.
    
    Returns:
        dict: Node info or None if no nodes available
    """
    nodes = get_minimal_os_nodes(host, functional_group)
    for node in nodes:
        if node.get("admin_ip"):
            return node
    return None


# =============================================================================
# SCHEMA VALIDATION FUNCTIONS
# =============================================================================

def check_functional_groups(host):
    """
    TC-F01: Check if minimal OS functional groups are defined.
    
    Returns:
        dict: {success, groups_found, details, error}
    """
    result = {
        "success": False,
        "groups_found": [],
        "details": "",
        "error": None,
    }
    
    # Try omnictl first
    cmd_result = host.run("omnictl functional-group list 2>/dev/null")
    output = cmd_result.stdout if cmd_result.rc == 0 else ""
    
    # Fallback to checking config files
    if not output:
        cmd_result = host.run(
            "find /opt/omnia -name '*functional_group*' -type f 2>/dev/null | head -5"
        )
        output = cmd_result.stdout
    
    # Check for minimal OS groups
    for group_name in FUNCTIONAL_GROUPS.values():
        if group_name in output:
            result["groups_found"].append(group_name)
    
    # Also check PXE mapping for assigned groups
    pxe_mapping = get_pxe_mapping(host)
    if pxe_mapping:
        for node_config in pxe_mapping.values():
            if isinstance(node_config, dict):
                fg = node_config.get("functional_group", "")
                if fg in FUNCTIONAL_GROUPS.values() and fg not in result["groups_found"]:
                    result["groups_found"].append(fg)
    
    if result["groups_found"]:
        result["success"] = True
        result["details"] = f"Found functional groups: {', '.join(result['groups_found'])}"
    else:
        result["error"] = "No minimal OS functional groups found"
        result["details"] = "os_x86_64 and os_aarch64 not found in configuration"
    
    return result


def validate_functional_group_schema(host, group_name):
    """
    Validate a specific functional group schema.
    
    Returns:
        dict: {success, details, error}
    """
    result = {
        "success": False,
        "details": "",
        "error": None,
    }
    
    schema_paths = [
        f"/etc/omnia/functional_groups/{group_name}.yaml",
        f"/opt/omnia/config/functional_groups/{group_name}.yaml",
    ]
    
    for path in schema_paths:
        cmd_result = host.run(f"test -f {path} && cat {path}")
        if cmd_result.rc == 0:
            result["success"] = True
            result["details"] = f"Schema found at {path}"
            return result
    
    # Schema file not required if group is used in PXE mapping
    pxe_mapping = get_pxe_mapping(host)
    if pxe_mapping:
        for node_config in pxe_mapping.values():
            if isinstance(node_config, dict):
                if node_config.get("functional_group") == group_name:
                    result["success"] = True
                    result["details"] = f"{group_name} is assigned in PXE mapping"
                    return result
    
    result["error"] = f"Schema for {group_name} not found"
    return result


# =============================================================================
# ARCHITECTURE VALIDATION FUNCTIONS
# =============================================================================

def get_node_architecture(host, node_ip):
    """
    Get architecture of a remote node.
    
    Returns:
        str: Architecture (x86_64, aarch64) or None
    """
    result = host.run(
        f"ssh -o StrictHostKeyChecking=no -o ConnectTimeout=10 "
        f"root@{node_ip} 'uname -m' 2>/dev/null"
    )
    if result.rc == 0:
        return result.stdout.strip()
    return None


def validate_node_architecture(host, node_ip, expected_group):
    """
    TC-F02/F03: Validate node architecture matches functional group.
    
    Returns:
        dict: {success, actual_arch, expected_arch, details, error}
    """
    result = {
        "success": False,
        "actual_arch": None,
        "expected_arch": None,
        "details": "",
        "error": None,
    }
    
    # Determine expected architecture from group name
    if "x86_64" in expected_group:
        result["expected_arch"] = "x86_64"
    elif "aarch64" in expected_group:
        result["expected_arch"] = "aarch64"
    else:
        result["error"] = f"Unknown architecture for group {expected_group}"
        return result
    
    # Get actual architecture
    result["actual_arch"] = get_node_architecture(host, node_ip)
    
    if not result["actual_arch"]:
        result["error"] = f"Could not determine architecture for {node_ip}"
        return result
    
    # Normalize aarch64/arm64
    actual = result["actual_arch"]
    if actual in ["aarch64", "arm64"]:
        actual = "aarch64"
    
    if actual == result["expected_arch"]:
        result["success"] = True
        result["details"] = f"Architecture {actual} matches {expected_group}"
    else:
        result["error"] = f"Architecture mismatch: expected {result['expected_arch']}, got {actual}"
    
    return result


# =============================================================================
# PACKAGE VERIFICATION FUNCTIONS
# =============================================================================

def _run_on_node(host, node_ip, command):
    """Run command on remote node via SSH."""
    return host.run(
        f"ssh -o StrictHostKeyChecking=no -o ConnectTimeout=10 "
        f"root@{node_ip} '{command}' 2>/dev/null"
    )


def check_base_packages(host, node_ip):
    """
    TC-F05: Check if all base OS packages are installed.
    
    Returns:
        dict: {success, installed, missing, details, error}
    """
    result = {
        "success": False,
        "installed": [],
        "missing": [],
        "details": "",
        "error": None,
    }
    
    for package in BASE_PACKAGES:
        cmd_result = _run_on_node(host, node_ip, f"rpm -q {package}")
        if cmd_result.rc == 0:
            result["installed"].append(package)
        else:
            result["missing"].append(package)
    
    if not result["missing"]:
        result["success"] = True
        result["details"] = f"All {len(BASE_PACKAGES)} base packages present"
    else:
        result["error"] = f"Missing packages: {', '.join(result['missing'])}"
        result["details"] = f"Installed: {len(result['installed'])}/{len(BASE_PACKAGES)}"
    
    return result


def check_ldms_packages(host, node_ip):
    """
    TC-F06: Check if LDMS packages are installed.
    
    Returns:
        dict: {success, installed, missing, binary_path, details, error}
    """
    result = {
        "success": False,
        "installed": [],
        "missing": [],
        "binary_path": None,
        "details": "",
        "error": None,
    }
    
    # Check packages
    for package in LDMS_PACKAGES:
        cmd_result = _run_on_node(host, node_ip, f"rpm -q {package}")
        if cmd_result.rc == 0:
            result["installed"].append(package)
        else:
            result["missing"].append(package)
    
    # Check ldmsd binary
    cmd_result = _run_on_node(host, node_ip, "which ldmsd")
    if cmd_result.rc == 0:
        result["binary_path"] = cmd_result.stdout.strip()
    
    if not result["missing"] and result["binary_path"]:
        result["success"] = True
        result["details"] = f"LDMS packages installed, binary at {result['binary_path']}"
    else:
        errors = []
        if result["missing"]:
            errors.append(f"Missing packages: {', '.join(result['missing'])}")
        if not result["binary_path"]:
            errors.append("ldmsd binary not found")
        result["error"] = "; ".join(errors)
    
    return result


def check_excluded_packages(host, node_ip):
    """
    TC-F07: Check that excluded packages are NOT present.
    
    Returns:
        dict: {success, found_packages, found_services, details, error}
    """
    result = {
        "success": True,
        "found_packages": [],
        "found_services": [],
        "details": "",
        "error": None,
    }
    
    # Check for excluded package patterns
    for pattern, name in EXCLUDED_PACKAGE_PATTERNS.items():
        cmd_result = _run_on_node(host, node_ip, f"rpm -qa | grep -E '{pattern}'")
        if cmd_result.rc == 0 and cmd_result.stdout.strip():
            result["found_packages"].append(name)
            result["success"] = False
    
    # Check for excluded services
    for service in EXCLUDED_SERVICES:
        cmd_result = _run_on_node(host, node_ip, f"systemctl is-active {service}")
        if cmd_result.rc == 0 and "active" in cmd_result.stdout:
            result["found_services"].append(service)
            result["success"] = False
    
    if result["success"]:
        result["details"] = "No excluded packages or services found"
    else:
        errors = []
        if result["found_packages"]:
            errors.append(f"Packages: {', '.join(result['found_packages'])}")
        if result["found_services"]:
            errors.append(f"Services: {', '.join(result['found_services'])}")
        result["error"] = "; ".join(errors)
    
    return result


def check_additional_packages(host, node_ip):
    """
    TC-F09: Check if additional packages from config are installed.
    
    Dynamically validates any packages listed in additional_packages.json.
    Supports LDMS and custom RPM packages.
    
    Returns:
        dict: {success, packages, installed, missing, details, error, not_configured}
    """
    result = {
        "success": False,
        "packages": [],
        "installed": [],
        "missing": [],
        "details": "",
        "error": None,
        "not_configured": False,
    }
    
    # Try multiple paths for additional_packages.json
    config_paths = [
        "/opt/omnia/oim_shared/input/additional_packages.json",
        "/etc/omnia/additional_packages.json",
        "/opt/omnia/config/additional_packages.json",
    ]
    
    config_content = None
    for path in config_paths:
        cmd_result = host.run(f"cat {path} 2>/dev/null")
        if cmd_result.rc == 0 and cmd_result.stdout.strip():
            config_content = cmd_result.stdout
            break
    
    if not config_content:
        result["not_configured"] = True
        result["success"] = True
        result["details"] = "additional_packages.json not configured (optional feature)"
        return result
    
    try:
        packages_data = json.loads(config_content)
        
        # Support both list and dict formats
        if isinstance(packages_data, dict):
            # Extract package names from dict (e.g., {"packages": ["pkg1", "pkg2"]})
            packages = packages_data.get("packages", [])
        elif isinstance(packages_data, list):
            packages = packages_data
        else:
            result["error"] = "Invalid format in additional_packages.json"
            return result
        
        if not packages:
            result["not_configured"] = True
            result["success"] = True
            result["details"] = "No additional packages configured"
            return result
        
        result["packages"] = packages
    except json.JSONDecodeError as err:
        result["error"] = f"Invalid JSON in additional_packages.json: {err}"
        return result
    
    # Check each package dynamically using rpm -q
    for package in packages:
        package_name = package.strip()
        if not package_name:
            continue
        
        cmd_result = _run_on_node(host, node_ip, f"rpm -q {package_name}")
        if cmd_result.rc == 0 and cmd_result.stdout.strip():
            result["installed"].append(package_name)
        else:
            result["missing"].append(package_name)
    
    if not result["missing"]:
        result["success"] = True
        result["details"] = (
            f"All {len(result['installed'])} additional packages installed: "
            f"{', '.join(result['installed'])}"
        )
    else:
        result["error"] = (
            f"Missing {len(result['missing'])} packages: {', '.join(result['missing'])}"
        )
    
    return result


# =============================================================================
# SERVICE VERIFICATION FUNCTIONS
# =============================================================================

def check_required_services(host, node_ip):
    """
    TC-F14: Check if required services are running.
    
    Returns:
        dict: {success, running, not_running, details, error}
    """
    result = {
        "success": False,
        "running": [],
        "not_running": [],
        "details": "",
        "error": None,
    }
    
    for service in REQUIRED_SERVICES:
        cmd_result = _run_on_node(host, node_ip, f"systemctl is-active {service}")
        if cmd_result.rc == 0 and "active" in cmd_result.stdout:
            result["running"].append(service)
        else:
            result["not_running"].append(service)
    
    if not result["not_running"]:
        result["success"] = True
        result["details"] = f"All required services running: {', '.join(result['running'])}"
    else:
        result["error"] = f"Services not running: {', '.join(result['not_running'])}"
    
    return result


def check_excluded_services(host, node_ip):
    """
    TC-F14: Check that excluded services are NOT running.
    
    Returns:
        dict: {success, running, details, error}
    """
    result = {
        "success": True,
        "running": [],
        "details": "",
        "error": None,
    }
    
    for service in EXCLUDED_SERVICES:
        cmd_result = _run_on_node(host, node_ip, f"systemctl is-active {service}")
        if cmd_result.rc == 0 and "active" in cmd_result.stdout:
            result["running"].append(service)
            result["success"] = False
    
    if result["success"]:
        result["details"] = "No excluded services running"
    else:
        result["error"] = f"Forbidden services running: {', '.join(result['running'])}"
    
    return result


def check_ldms_service_state(host, node_ip):
    """
    TC-F17: Check that LDMS service is NOT running.
    
    Returns:
        dict: {success, service_active, service_enabled, details, error}
    """
    result = {
        "success": False,
        "service_active": False,
        "service_enabled": False,
        "details": "",
        "error": None,
    }
    
    # Check if service is active
    cmd_result = _run_on_node(host, node_ip, "systemctl is-active ldmsd")
    result["service_active"] = cmd_result.rc == 0 and "active" in cmd_result.stdout
    
    # Check if service is enabled
    cmd_result = _run_on_node(host, node_ip, "systemctl is-enabled ldmsd")
    result["service_enabled"] = cmd_result.rc == 0 and "enabled" in cmd_result.stdout
    
    # Check for running processes
    cmd_result = _run_on_node(host, node_ip, "pgrep -c ldmsd")
    has_processes = cmd_result.rc == 0 and cmd_result.stdout.strip() != "0"
    
    if not result["service_active"] and not has_processes:
        result["success"] = True
        result["details"] = "LDMS service not running (as expected at handoff)"
    else:
        result["error"] = "LDMS service is running (should not be at handoff)"
    
    return result


# =============================================================================
# FILESYSTEM VERIFICATION FUNCTIONS
# =============================================================================

def check_ram_filesystem(host, node_ip):
    """
    TC-F13: Check if root filesystem is RAM-based (tmpfs).
    
    Returns:
        dict: {success, fs_type, mount_info, details, error}
    """
    result = {
        "success": False,
        "fs_type": None,
        "mount_info": "",
        "details": "",
        "error": None,
    }
    
    # Check filesystem type
    cmd_result = _run_on_node(host, node_ip, "df -T / | tail -1")
    if cmd_result.rc == 0:
        result["mount_info"] = cmd_result.stdout.strip()
        if "tmpfs" in cmd_result.stdout:
            result["fs_type"] = "tmpfs"
            result["success"] = True
            result["details"] = "Root filesystem is RAM-based (tmpfs)"
        else:
            parts = cmd_result.stdout.split()
            result["fs_type"] = parts[1] if len(parts) > 1 else "unknown"
            result["error"] = f"Root filesystem is {result['fs_type']}, not tmpfs"
    else:
        result["error"] = "Could not determine filesystem type"
    
    return result


# =============================================================================
# NETWORK VERIFICATION FUNCTIONS
# =============================================================================

def check_network_identity(host, node_ip, expected_hostname):
    """
    TC-F12: Check network identity (hostname and IP).
    
    Returns:
        dict: {success, actual_hostname, ip_configured, details, error}
    """
    result = {
        "success": False,
        "actual_hostname": None,
        "ip_configured": False,
        "details": "",
        "error": None,
    }
    
    # Check hostname
    cmd_result = _run_on_node(host, node_ip, "hostname")
    if cmd_result.rc == 0:
        result["actual_hostname"] = cmd_result.stdout.strip()
    
    # Check IP is configured
    cmd_result = _run_on_node(host, node_ip, f"ip addr show | grep {node_ip}")
    result["ip_configured"] = cmd_result.rc == 0
    
    hostname_match = result["actual_hostname"] == expected_hostname
    
    if result["ip_configured"]:
        result["success"] = True
        if hostname_match:
            result["details"] = f"Hostname: {result['actual_hostname']}, IP: {node_ip}"
        else:
            result["details"] = (
                f"IP configured. Hostname: {result['actual_hostname']} "
                f"(expected: {expected_hostname})"
            )
    else:
        result["error"] = f"Admin IP {node_ip} not configured on node"
    
    return result


# =============================================================================
# SSH VERIFICATION FUNCTIONS
# =============================================================================

def check_ssh_access(host, node_ip):
    """
    TC-F15: Check SSH access to node.
    
    Returns:
        dict: {success, details, error}
    """
    result = {
        "success": False,
        "details": "",
        "error": None,
    }
    
    cmd_result = _run_on_node(host, node_ip, "echo ok")
    if cmd_result.rc == 0 and "ok" in cmd_result.stdout:
        result["success"] = True
        result["details"] = "SSH connection successful"
    else:
        result["error"] = f"SSH connection failed: {cmd_result.stderr}"
    
    return result


def check_ssh_key_auth(host, node_ip):
    """
    TC-F15/TC-S02: Check SSH key authentication and password auth disabled.
    
    Returns:
        dict: {success, authorized_keys_exists, password_auth_disabled, details, error}
    """
    result = {
        "success": False,
        "authorized_keys_exists": False,
        "password_auth_disabled": False,
        "details": "",
        "error": None,
    }
    
    # Check authorized_keys
    cmd_result = _run_on_node(host, node_ip, "test -f /root/.ssh/authorized_keys && echo EXISTS")
    result["authorized_keys_exists"] = "EXISTS" in cmd_result.stdout
    
    # Check password auth disabled
    cmd_result = _run_on_node(
        host, node_ip,
        "grep -E '^PasswordAuthentication' /etc/ssh/sshd_config"
    )
    if cmd_result.rc == 0:
        result["password_auth_disabled"] = "no" in cmd_result.stdout.lower()
    
    if result["authorized_keys_exists"] and result["password_auth_disabled"]:
        result["success"] = True
        result["details"] = "SSH key auth enabled, password auth disabled"
    else:
        errors = []
        if not result["authorized_keys_exists"]:
            errors.append("authorized_keys not found")
        if not result["password_auth_disabled"]:
            errors.append("password auth not disabled")
        result["error"] = "; ".join(errors)
    
    return result


# =============================================================================
# PACKAGE MANAGER FUNCTIONS
# =============================================================================

def check_package_manager(host, node_ip):
    """
    TC-F16: Check dnf package manager functionality.
    
    Returns:
        dict: {success, dnf_exists, repos_configured, details, error}
    """
    result = {
        "success": False,
        "dnf_exists": False,
        "repos_configured": False,
        "repo_list": "",
        "details": "",
        "error": None,
    }
    
    # Check dnf binary
    cmd_result = _run_on_node(host, node_ip, "which dnf")
    result["dnf_exists"] = cmd_result.rc == 0
    
    if not result["dnf_exists"]:
        result["error"] = "dnf binary not found"
        return result
    
    # Check repositories
    cmd_result = _run_on_node(host, node_ip, "dnf repolist")
    if cmd_result.rc == 0:
        result["repos_configured"] = True
        result["repo_list"] = cmd_result.stdout.strip()[:200]
    
    if result["dnf_exists"] and result["repos_configured"]:
        result["success"] = True
        result["details"] = "dnf functional with configured repositories"
    else:
        result["error"] = "dnf exists but no repositories configured"
    
    return result


# =============================================================================
# IMAGE STORAGE FUNCTIONS
# =============================================================================

def check_image_in_storage(host, arch):
    """
    TC-F08: Check if OS image exists in object storage.
    
    Args:
        arch: "x86_64" or "aarch64"
    
    Returns:
        dict: {success, image_path, details, error}
    """
    result = {
        "success": False,
        "image_path": None,
        "details": "",
        "error": None,
    }
    
    image_key = f"os_{arch}"
    image_names = IMAGE_PATHS.get(image_key, [])
    base_path = IMAGE_PATHS.get("base", "/var/lib/omnia/images")
    
    for image_name in image_names:
        full_path = f"{base_path}/{image_name}"
        cmd_result = host.run(f"test -f {full_path} && stat -c '%s' {full_path}")
        if cmd_result.rc == 0:
            size = cmd_result.stdout.strip()
            if int(size) > 0:
                result["success"] = True
                result["image_path"] = full_path
                result["details"] = f"Image found: {full_path} ({size} bytes)"
                return result
    
    result["error"] = f"No {arch} image found in object storage"
    return result


# =============================================================================
# SECURITY CHECK FUNCTIONS
# =============================================================================

def check_no_embedded_credentials(host, node_ip):
    """
    TC-S03: Check that no credentials are embedded in the image.
    
    Returns:
        dict: {success, findings, details, error}
    """
    result = {
        "success": True,
        "findings": [],
        "details": "",
        "error": None,
    }
    
    # Check for password hashes in shadow
    cmd_result = _run_on_node(
        host, node_ip,
        "awk -F: '$2 !~ /^[!*]/ && $2 != \"\" {print $1}' /etc/shadow"
    )
    if cmd_result.rc == 0 and cmd_result.stdout.strip():
        result["findings"].append(f"Password hashes found for: {cmd_result.stdout.strip()}")
        result["success"] = False
    
    # Check for private keys
    cmd_result = _run_on_node(
        host, node_ip,
        "find /etc /root -name '*.key' -o -name '*_rsa' -o -name '*_dsa' 2>/dev/null | head -5"
    )
    if cmd_result.rc == 0 and cmd_result.stdout.strip():
        result["findings"].append(f"Private keys found: {cmd_result.stdout.strip()}")
        result["success"] = False
    
    if result["success"]:
        result["details"] = "No embedded credentials found"
    else:
        result["error"] = "; ".join(result["findings"])
    
    return result


def check_network_isolation(host, node_ip):
    """
    TC-S01: Check network isolation (management network only).
    
    Returns:
        dict: {success, default_route, details, error}
    """
    result = {
        "success": False,
        "default_route": None,
        "details": "",
        "error": None,
    }
    
    # Check default route
    cmd_result = _run_on_node(host, node_ip, "ip route | grep default")
    if cmd_result.rc == 0:
        result["default_route"] = cmd_result.stdout.strip()
        result["success"] = True
        result["details"] = f"Default route: {result['default_route']}"
    else:
        result["error"] = "Could not determine default route"
    
    return result
