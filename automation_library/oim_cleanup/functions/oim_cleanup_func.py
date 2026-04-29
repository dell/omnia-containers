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
OIM Cleanup - Verification Functions.

Functions to verify that oim_cleanup.yml playbook executed successfully.
Each function returns a dict with success, details (multi-line string for
│ pipe display), and error keys — matching the standard used by
local_repo and telemetry modules.
"""

from typing import Dict, Any

from automation_library.core import (
    run_on_oim, run_in_container, load_container_file,
)
from automation_library.core import OIM_METADATA_PATH, OIM_SHARED_PATH

from ..vars.oim_cleanup_vars import OIM_CLEANUP_VARS

# Runtime cache for oim_shared_path
_oim_shared_path_cache: Dict[str, str] = {}


def _get_nfs_base(host) -> str:
    """
    Get NFS base path by reading oim_shared_path from oim_metadata.yml
    inside the omnia_core container, then appending /omnia.

    Returns:
        e.g. '/mmm/omnia' if oim_shared_path is '/mmm'
    """
    cache_key = "nfs_base"
    if cache_key in _oim_shared_path_cache:
        return _oim_shared_path_cache[cache_key]

    metadata = load_container_file(host, OIM_METADATA_PATH)
    oim_shared_path = metadata.get("oim_shared_path", OIM_SHARED_PATH)

    nfs_base = f"{oim_shared_path}/omnia"
    _oim_shared_path_cache[cache_key] = nfs_base
    return nfs_base


def _build_details(lines):
    """Build multi-line details string from list of status lines."""
    return "\n".join(lines)


# =============================================================================
# 1. SERVICES REMOVED
# =============================================================================

def check_services_removed(host) -> Dict[str, Any]:
    """
    Verify all OIM services are stopped and disabled.

    Returns:
        Dict with success, details, error keys
    """
    all_services = (
        OIM_CLEANUP_VARS["services"] + OIM_CLEANUP_VARS["openchami_services"]
    )

    lines = []
    failed_items = []

    for svc in all_services:
        cmd = run_on_oim(host, f"systemctl is-active {svc} 2>/dev/null")
        state = cmd.stdout.strip()
        if state in ("inactive", "unknown", "") or cmd.rc != 0:
            lines.append(f"✓ {svc}: removed")
        else:
            lines.append(f"✗ {svc}: STILL ACTIVE ({state})")
            failed_items.append(svc)

    passed = len(all_services) - len(failed_items)
    lines.append(f"Result: {passed}/{len(all_services)} services removed")

    return {
        "success": len(failed_items) == 0,
        "details": _build_details(lines),
        "error": f"Services still active: {', '.join(failed_items)}" if failed_items else "",
    }


# =============================================================================
# 2. CONTAINERS REMOVED
# =============================================================================

def check_containers_removed(host) -> Dict[str, Any]:
    """
    Verify all OIM containers are removed.

    Returns:
        Dict with success, details, error keys
    """
    containers = OIM_CLEANUP_VARS["containers"]

    lines = []
    failed_items = []

    for ctr in containers:
        cmd = run_on_oim(host, f"podman container exists {ctr} 2>/dev/null")
        if cmd.rc != 0:
            lines.append(f"✓ {ctr}: removed")
        else:
            lines.append(f"✗ {ctr}: STILL PRESENT")
            failed_items.append(ctr)

    passed = len(containers) - len(failed_items)
    lines.append(f"Result: {passed}/{len(containers)} containers removed")

    return {
        "success": len(failed_items) == 0,
        "details": _build_details(lines),
        "error": f"Containers still present: {', '.join(failed_items)}" if failed_items else "",
    }


# =============================================================================
# 3. CONTAINER FILES AND OMNIA TARGET REMOVED
# =============================================================================

def check_container_files_removed(host) -> Dict[str, Any]:
    """
    Verify all quadlet files (.container, .volume, .network) and
    omnia.target files are removed from /etc/containers/systemd/.

    Returns:
        Dict with success, details, error keys
    """
    files = (
        list(OIM_CLEANUP_VARS["container_files"])
        + list(OIM_CLEANUP_VARS["quadlet_volume_files"])
        + list(OIM_CLEANUP_VARS["quadlet_network_files"])
        + list(OIM_CLEANUP_VARS["omnia_target_files"])
    )

    lines = []
    failed_items = []
    total = 0

    for fpath in files:
        total += 1
        cmd = run_on_oim(host, f"test -e {fpath}")
        if cmd.rc != 0:
            lines.append(f"✓ {fpath}: removed")
        else:
            lines.append(f"✗ {fpath}: STILL PRESENT")
            failed_items.append(fpath)

    # Check auth container files (glob pattern)
    auth_pattern = OIM_CLEANUP_VARS["auth_container_file_pattern"]
    auth_cmd = run_on_oim(host, f"ls {auth_pattern} 2>/dev/null")
    total += 1
    if auth_cmd.rc != 0 or not auth_cmd.stdout.strip():
        lines.append("✓ omnia_auth*.container: removed")
    else:
        for line in auth_cmd.stdout.strip().split("\n"):
            if line.strip():
                lines.append(f"✗ {line.strip()}: STILL PRESENT")
                failed_items.append(line.strip())

    passed = total - len(failed_items)
    lines.append(f"Result: {passed}/{total} files removed")

    return {
        "success": len(failed_items) == 0,
        "details": _build_details(lines),
        "error": f"Files still present: {', '.join(failed_items)}" if failed_items else "",
    }


# =============================================================================
# 4. VOLUMES AND SECRETS REMOVED
# =============================================================================

def check_volumes_secrets_removed(host) -> Dict[str, Any]:
    """
    Verify OpenCHAMI podman volumes and secrets are removed.

    Returns:
        Dict with success, details, error keys
    """
    volumes = OIM_CLEANUP_VARS["openchami_volumes"]
    secrets = OIM_CLEANUP_VARS["openchami_secrets"]

    lines = []
    failed_items = []

    # Check volumes
    for vol in volumes:
        cmd = run_on_oim(host, f"podman volume exists {vol} 2>/dev/null")
        if cmd.rc != 0:
            lines.append(f"✓ volume {vol}: removed")
        else:
            lines.append(f"✗ volume {vol}: STILL PRESENT")
            failed_items.append(f"volume:{vol}")

    # Check secrets
    secret_cmd = run_on_oim(host, "podman secret ls --format '{{.Name}}' 2>/dev/null")
    existing_secrets = set()
    if secret_cmd.rc == 0 and secret_cmd.stdout.strip():
        existing_secrets = {s.strip() for s in secret_cmd.stdout.strip().split("\n")}

    for sec in secrets:
        if sec in existing_secrets:
            lines.append(f"✗ secret {sec}: STILL PRESENT")
            failed_items.append(f"secret:{sec}")
        else:
            lines.append(f"✓ secret {sec}: removed")

    total = len(volumes) + len(secrets)
    passed = total - len(failed_items)
    lines.append(f"Result: {passed}/{total} volumes/secrets removed")

    return {
        "success": len(failed_items) == 0,
        "details": _build_details(lines),
        "error": f"Still present: {', '.join(failed_items)}" if failed_items else "",
    }


# =============================================================================
# 5. CREDENTIAL FILES REMOVED
# =============================================================================

def check_credential_files_removed(host) -> Dict[str, Any]:
    """
    Verify credential files and vault key are removed (inside container).

    Returns:
        Dict with success, details, error keys
    """
    all_files = (
        list(OIM_CLEANUP_VARS["credential_files"])
        + list(OIM_CLEANUP_VARS["metadata_files"])
    )

    lines = []
    failed_items = []

    for fpath in all_files:
        cmd = run_in_container(host, f"test -f {fpath}")
        if cmd.rc != 0:
            lines.append(f"✓ {fpath}: removed")
        else:
            lines.append(f"✗ {fpath}: STILL PRESENT")
            failed_items.append(fpath)

    passed = len(all_files) - len(failed_items)
    lines.append(f"Result: {passed}/{len(all_files)} credential files removed")

    return {
        "success": len(failed_items) == 0,
        "details": _build_details(lines),
        "error": f"Files still present: {', '.join(failed_items)}" if failed_items else "",
    }


# =============================================================================
# 6. FIREWALL PORTS REMOVED
# =============================================================================

def check_firewall_ports_removed(host) -> Dict[str, Any]:
    """
    Verify firewall TCP and UDP ports are removed.

    Returns:
        Dict with success, details, error keys
    """
    tcp_ports = OIM_CLEANUP_VARS["tcp_ports"]
    udp_ports = OIM_CLEANUP_VARS["udp_ports"]

    lines = []
    failed_items = []

    fw_cmd = run_on_oim(host, "firewall-cmd --list-ports 2>/dev/null")
    open_ports = fw_cmd.stdout.strip() if fw_cmd.rc == 0 else ""

    for port in tcp_ports:
        port_str = f"{port}/tcp"
        if port_str in open_ports:
            lines.append(f"✗ {port_str}: STILL OPEN")
            failed_items.append(port_str)
        else:
            lines.append(f"✓ {port_str}: removed")

    for port in udp_ports:
        port_str = f"{port}/udp"
        if port_str in open_ports:
            lines.append(f"✗ {port_str}: STILL OPEN")
            failed_items.append(port_str)
        else:
            lines.append(f"✓ {port_str}: removed")

    total = len(tcp_ports) + len(udp_ports)
    passed = total - len(failed_items)
    lines.append(f"Result: {passed}/{total} ports removed")

    return {
        "success": len(failed_items) == 0,
        "details": _build_details(lines),
        "error": f"Ports still open: {', '.join(failed_items)}" if failed_items else "",
    }


# =============================================================================
# 7. DIRECTORIES REMOVED
# =============================================================================

def check_directories_removed(host) -> Dict[str, Any]:
    """
    Verify all cleanup directories are removed.

    Returns:
        Dict with success, details, error keys
    """
    nfs_base = _get_nfs_base(host)
    all_dirs = []
    for d in OIM_CLEANUP_VARS["cleanup_dirs_relative"]:
        all_dirs.append(f"{nfs_base}/{d}")
    for d in OIM_CLEANUP_VARS["cleanup_dirs_absolute"]:
        all_dirs.append(d)
    all_dirs.append(OIM_CLEANUP_VARS["cleanup_credential_key"])

    lines = []
    failed_items = []

    for dpath in all_dirs:
        cmd = run_on_oim(host, f"test -e {dpath}")
        if cmd.rc != 0:
            lines.append(f"✓ {dpath}: removed")
        else:
            lines.append(f"✗ {dpath}: STILL PRESENT")
            failed_items.append(dpath)

    passed = len(all_dirs) - len(failed_items)
    lines.append(f"Result: {passed}/{len(all_dirs)} directories removed")

    return {
        "success": len(failed_items) == 0,
        "details": _build_details(lines),
        "error": f"Dirs still present: {', '.join(failed_items)}" if failed_items else "",
    }


# =============================================================================
# 8. REGCTL, S3CMD, PACKAGES REMOVED
# =============================================================================

def check_packages_removed(host) -> Dict[str, Any]:
    """
    Verify regctl binary and openchami packages (ochami, openchami, s3cmd) are removed.

    Returns:
        Dict with success, details, error keys
    """
    lines = []
    failed_items = []
    total = 0

    # Check regctl files
    for fpath in OIM_CLEANUP_VARS["regctl_files"]:
        total += 1
        cmd = run_on_oim(host, f"test -e {fpath}")
        if cmd.rc != 0:
            lines.append(f"✓ {fpath}: removed")
        else:
            lines.append(f"✗ {fpath}: STILL PRESENT")
            failed_items.append(fpath)

    # Check packages
    for pkg in OIM_CLEANUP_VARS["packages"]:
        total += 1
        cmd = run_on_oim(host, f"rpm -q {pkg} 2>/dev/null")
        if cmd.rc != 0:
            lines.append(f"✓ {pkg}: removed")
        else:
            lines.append(f"✗ {pkg}: STILL INSTALLED ({cmd.stdout.strip()})")
            failed_items.append(pkg)

    passed = total - len(failed_items)
    lines.append(f"Result: {passed}/{total} packages removed")

    return {
        "success": len(failed_items) == 0,
        "details": _build_details(lines),
        "error": f"Still installed: {', '.join(failed_items)}" if failed_items else "",
    }


# =============================================================================
# 9. CHRONYD REMOVED
# =============================================================================

def check_chronyd_removed(host) -> Dict[str, Any]:
    """
    Verify chronyd is stopped, disabled, and allow list removed from chrony.conf.

    Returns:
        Dict with success, details, error keys
    """
    lines = []
    failed_items = []

    # Check chronyd service stopped
    cmd = run_on_oim(host, "systemctl is-active chronyd 2>/dev/null")
    state = cmd.stdout.strip()
    if state in ("inactive", "unknown", "") or cmd.rc != 0:
        lines.append("✓ chronyd.service: removed")
    else:
        lines.append(f"✗ chronyd.service: STILL ACTIVE ({state})")
        failed_items.append("chronyd still active")

    # Check chronyd disabled
    cmd = run_on_oim(host, "systemctl is-enabled chronyd 2>/dev/null")
    if cmd.stdout.strip() == "disabled" or cmd.rc != 0:
        lines.append("✓ chronyd: disabled")
    else:
        lines.append(f"✗ chronyd: STILL ENABLED ({cmd.stdout.strip()})")
        failed_items.append("chronyd still enabled")

    # Check allow list removed
    chrony_path = OIM_CLEANUP_VARS["chrony_conf_path"]
    cmd = run_on_oim(host, f"grep -c '^allow' {chrony_path} 2>/dev/null")
    allow_count = int(cmd.stdout.strip()) if cmd.rc == 0 else 0
    if allow_count == 0:
        lines.append(f"✓ {chrony_path}: allow list removed")
    else:
        lines.append(f"✗ {chrony_path}: {allow_count} allow directive(s) STILL PRESENT")
        failed_items.append(f"{allow_count} allow directives in chrony.conf")

    return {
        "success": len(failed_items) == 0,
        "details": _build_details(lines),
        "error": "; ".join(failed_items) if failed_items else "",
    }


# =============================================================================
# 10. AUTH REMOVED
# =============================================================================

def check_auth_removed(host) -> Dict[str, Any]:
    """
    Verify omnia_auth container and files are removed.

    Returns:
        Dict with success, details, error keys
    """
    lines = []
    failed_items = []

    # Check auth container
    cmd = run_on_oim(host, "podman container exists omnia_auth 2>/dev/null")
    if cmd.rc != 0:
        lines.append("✓ omnia_auth container: removed")
    else:
        lines.append("✗ omnia_auth container: STILL PRESENT")
        failed_items.append("omnia_auth container")

    # Check auth container files
    auth_pattern = OIM_CLEANUP_VARS["auth_container_file_pattern"]
    cmd = run_on_oim(host, f"ls {auth_pattern} 2>/dev/null")
    if cmd.rc != 0 or not cmd.stdout.strip():
        lines.append("✓ omnia_auth*.container files: removed")
    else:
        for line in cmd.stdout.strip().split("\n"):
            if line.strip():
                lines.append(f"✗ {line.strip()}: STILL PRESENT")
                failed_items.append(line.strip())

    # Check auth directories
    auth_dir = f"{_get_nfs_base(host)}/auth"
    cmd = run_on_oim(host, f"test -e {auth_dir}")
    if cmd.rc != 0:
        lines.append(f"✓ {auth_dir}: removed")
    else:
        lines.append(f"✗ {auth_dir}: STILL PRESENT")
        failed_items.append(auth_dir)

    return {
        "success": len(failed_items) == 0,
        "details": _build_details(lines),
        "error": f"Still present: {', '.join(failed_items)}" if failed_items else "",
    }


# =============================================================================
# 11. BUILD STREAM REMOVED
# =============================================================================

def check_build_stream_removed(host) -> Dict[str, Any]:
    """
    Verify build_stream containers, service, and quadlet files are removed.

    Returns:
        Dict with success, details, error keys
    """
    lines = []
    failed_items = []

    # Check build_stream containers removed
    for ctr in OIM_CLEANUP_VARS["build_stream_containers"]:
        cmd = run_on_oim(host, f"podman container exists {ctr} 2>/dev/null")
        if cmd.rc != 0:
            lines.append(f"✓ {ctr} container: removed")
        else:
            lines.append(f"✗ {ctr} container: STILL PRESENT")
            failed_items.append(f"{ctr} container")

    # Check build_stream service stopped
    svc = OIM_CLEANUP_VARS["build_stream_service"]
    cmd = run_on_oim(host, f"systemctl is-active {svc} 2>/dev/null")
    state = cmd.stdout.strip()
    if state in ("inactive", "unknown", "") or cmd.rc != 0:
        lines.append(f"✓ {svc}: removed")
    else:
        lines.append(f"✗ {svc}: STILL ACTIVE ({state})")
        failed_items.append(svc)

    # Check quadlet files removed
    for quadlet in [
        OIM_CLEANUP_VARS["build_stream_quadlet_file"],
        OIM_CLEANUP_VARS["build_stream_postgres_quadlet_file"],
    ]:
        cmd = run_on_oim(host, f"test -f {quadlet}")
        if cmd.rc != 0:
            lines.append(f"✓ {quadlet}: removed")
        else:
            lines.append(f"✗ {quadlet}: STILL PRESENT")
            failed_items.append(quadlet)

    return {
        "success": len(failed_items) == 0,
        "details": _build_details(lines),
        "error": f"Still present: {', '.join(failed_items)}" if failed_items else "",
    }
