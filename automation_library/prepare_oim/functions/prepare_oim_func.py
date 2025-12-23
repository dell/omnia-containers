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

"""
Prepare OIM - Core Functions.

This module contains all functions for running and verifying prepare_oim.
Test functions should call these functions - all logic resides here.

Usage:
    from automation_library.functions.prepare_oim_func import (
        check_container_running,
        check_all_containers,
        check_omnia_target,
        check_openchami_target,
        check_ochami_bss_status,
        check_ochami_smd_status,
        check_auth_container,
    )

Author: Dell Technologies
"""

from typing import Dict, Any

from ..vars.prepare_oim_vars import (
    PREPARE_OIM_VARS,
    OPENCHAMI_CONTAINERS,
    CORE_CONTAINERS,
    AUTH_CONTAINER,
    is_ldap_enabled,
)
from ..messages.prepare_oim_msgs import PREPARE_OIM_MSGS


# =============================================================================
# CONTAINER VERIFICATION FUNCTIONS (for pytest/testinfra)
# =============================================================================

def check_container_running(host, container_name: str) -> Dict[str, Any]:
    """
    Check if a specific container is running.

    Args:
        host: testinfra host object
        container_name: name of the container to check

    Returns:
        Dict with 'success', 'status', 'details', 'error'
    """
    cmd = host.run(f"podman ps --format '{{{{.Names}}}} {{{{.Status}}}}' | grep -E '^{container_name} '")

    if cmd.rc == 0 and container_name in cmd.stdout:
        status = cmd.stdout.strip().replace(container_name, "").strip()
        return {
            "success": True,
            "status": status,
            "details": f"Container {container_name} is running: {status}",
            "error": None
        }

    # Check if container exists but not running
    exists_cmd = host.run(f"podman ps -a --format '{{{{.Names}}}} {{{{.Status}}}}' | grep -E '^{container_name} '")
    if exists_cmd.rc == 0:
        status = exists_cmd.stdout.strip().replace(container_name, "").strip()
        return {
            "success": False,
            "status": status,
            "details": None,
            "error": f"Container {container_name} exists but not running: {status}"
        }

    return {
        "success": False,
        "status": "not_found",
        "details": None,
        "error": f"Container {container_name} does not exist"
    }


def check_container_healthy(host, container_name: str) -> Dict[str, Any]:
    """
    Check if a container is healthy (for containers with health checks).

    Args:
        host: testinfra host object
        container_name: name of the container to check

    Returns:
        Dict with 'success', 'status', 'details', 'error'
    """
    cmd = host.run(f"podman inspect --format '{{{{.State.Health.Status}}}}' {container_name} 2>/dev/null")

    if cmd.rc == 0:
        health_status = cmd.stdout.strip()
        if health_status == "healthy":
            return {
                "success": True,
                "status": health_status,
                "details": f"Container {container_name} is healthy",
                "error": None
            }
        if health_status == "":
            # No health check configured - just check if running
            return check_container_running(host, container_name)
        return {
            "success": False,
            "status": health_status,
            "details": None,
            "error": f"Container {container_name} health status: {health_status}"
        }

    return check_container_running(host, container_name)


def check_all_containers(host, skip_on_failure: bool = True) -> Dict[str, Any]:
    """
    Check all required containers are running.
    Continues checking all containers even if some fail.

    Args:
        host: testinfra host object
        skip_on_failure: if True, continue checking all containers even if some fail

    Returns:
        Dict with 'success', 'results', 'passed', 'failed', 'skipped', 'details'
    """
    results = []
    passed = 0
    failed = 0
    skipped = 0

    # Check core containers
    for container in CORE_CONTAINERS:
        result = check_container_running(host, container)
        results.append({
            "container": container,
            "category": "core",
            "success": result["success"],
            "status": result["status"],
            "error": result["error"]
        })
        if result["success"]:
            passed += 1
        else:
            failed += 1

    # Check OpenChami containers
    for container in OPENCHAMI_CONTAINERS:
        result = check_container_running(host, container)
        results.append({
            "container": container,
            "category": "openchami",
            "success": result["success"],
            "status": result["status"],
            "error": result["error"]
        })
        if result["success"]:
            passed += 1
        else:
            failed += 1

    # Check auth container (only if LDAP enabled)
    if is_ldap_enabled():
        result = check_container_running(host, AUTH_CONTAINER)
        results.append({
            "container": AUTH_CONTAINER,
            "category": "auth",
            "success": result["success"],
            "status": result["status"],
            "error": result["error"]
        })
        if result["success"]:
            passed += 1
        else:
            failed += 1
    else:
        results.append({
            "container": AUTH_CONTAINER,
            "category": "auth",
            "success": True,
            "status": "skipped",
            "error": None,
            "skipped": True
        })
        skipped += 1

    total = passed + failed
    return {
        "success": failed == 0,
        "results": results,
        "passed": passed,
        "failed": failed,
        "skipped": skipped,
        "total": total,
        "details": f"{passed}/{total} containers running" + (f", {skipped} skipped" if skipped > 0 else "")
    }


def check_openchami_containers(host) -> Dict[str, Any]:
    """
    Check all OpenChami containers are running.

    Args:
        host: testinfra host object

    Returns:
        Dict with 'success', 'results', 'passed', 'failed', 'details'
    """
    results = []
    passed = 0
    failed = 0

    for container in OPENCHAMI_CONTAINERS:
        result = check_container_running(host, container)
        results.append({
            "container": container,
            "success": result["success"],
            "status": result["status"],
            "error": result["error"]
        })
        if result["success"]:
            passed += 1
        else:
            failed += 1

    total = len(OPENCHAMI_CONTAINERS)
    return {
        "success": failed == 0,
        "results": results,
        "passed": passed,
        "failed": failed,
        "total": total,
        "details": f"{passed}/{total} OpenChami containers running"
    }


def check_core_containers(host) -> Dict[str, Any]:
    """
    Check all core infrastructure containers are running.

    Args:
        host: testinfra host object

    Returns:
        Dict with 'success', 'results', 'passed', 'failed', 'details'
    """
    results = []
    passed = 0
    failed = 0

    for container in CORE_CONTAINERS:
        result = check_container_running(host, container)
        results.append({
            "container": container,
            "success": result["success"],
            "status": result["status"],
            "error": result["error"]
        })
        if result["success"]:
            passed += 1
        else:
            failed += 1

    total = len(CORE_CONTAINERS)
    return {
        "success": failed == 0,
        "results": results,
        "passed": passed,
        "failed": failed,
        "total": total,
        "details": f"{passed}/{total} core containers running"
    }


def check_auth_container(host) -> Dict[str, Any]:
    """
    Check auth container status.
    Returns skipped if LDAP is not enabled in software_config.json.

    Args:
        host: testinfra host object

    Returns:
        Dict with 'success', 'status', 'skipped', 'details', 'error'
    """
    if not is_ldap_enabled():
        return {
            "success": True,
            "status": "skipped",
            "skipped": True,
            "details": "Auth container check skipped (LDAP not in software_config.json)",
            "error": None
        }

    result = check_container_running(host, AUTH_CONTAINER)
    return {
        "success": result["success"],
        "status": result["status"],
        "skipped": False,
        "details": result["details"],
        "error": result["error"]
    }


# =============================================================================
# SERVICE VERIFICATION FUNCTIONS
# =============================================================================

def check_omnia_target(host) -> Dict[str, Any]:
    """
    Check if omnia.target is active.

    Args:
        host: testinfra host object

    Returns:
        Dict with 'success', 'status', 'details', 'error'
    """
    target = PREPARE_OIM_VARS["omnia_target"]
    status_cmd = host.run(f"systemctl is-active {target}")
    status = status_cmd.stdout.strip()

    if status == "active":
        info = host.run(f"systemctl status {target} --no-pager -l 2>/dev/null | head -5").stdout.strip()
        return {
            "success": True,
            "status": status,
            "details": info,
            "error": None
        }

    return {
        "success": False,
        "status": status,
        "details": None,
        "error": f"{target} is {status}"
    }


def check_openchami_target(host) -> Dict[str, Any]:
    """
    Check if openchami.target is active.

    Args:
        host: testinfra host object

    Returns:
        Dict with 'success', 'status', 'details', 'error'
    """
    target = PREPARE_OIM_VARS["openchami_target"]
    status_cmd = host.run(f"systemctl is-active {target}")
    status = status_cmd.stdout.strip()

    if status == "active":
        info = host.run(f"systemctl status {target} --no-pager -l 2>/dev/null | head -5").stdout.strip()
        return {
            "success": True,
            "status": status,
            "details": info,
            "error": None
        }

    return {
        "success": False,
        "status": status,
        "details": None,
        "error": f"{target} is {status}"
    }


def check_service_dependencies(host, target: str = None) -> Dict[str, Any]:
    """
    Check all dependencies of a systemd target.

    Args:
        host: testinfra host object
        target: target name (default: openchami.target)

    Returns:
        Dict with 'success', 'dependencies', 'failed', 'details'
    """
    target = target or PREPARE_OIM_VARS["openchami_target"]
    cmd = host.run(f"systemctl list-dependencies {target} --plain 2>/dev/null")

    if cmd.rc != 0:
        return {
            "success": False,
            "dependencies": [],
            "failed": [],
            "details": None,
            "error": f"Failed to list dependencies for {target}"
        }

    dependencies = [line.strip() for line in cmd.stdout.strip().split('\n') if line.strip()]
    failed = []

    for dep in dependencies:
        if dep and not dep.startswith("●"):
            status_cmd = host.run(f"systemctl is-active {dep} 2>/dev/null")
            if status_cmd.stdout.strip() != "active":
                failed.append({"service": dep, "status": status_cmd.stdout.strip()})

    return {
        "success": len(failed) == 0,
        "dependencies": dependencies,
        "failed": failed,
        "details": f"{len(dependencies) - len(failed)}/{len(dependencies)} dependencies active",
        "error": f"{len(failed)} dependencies not active" if failed else None
    }


# =============================================================================
# PULP VERIFICATION FUNCTIONS
# =============================================================================

def check_pulp_api_status(host) -> Dict[str, Any]:
    """
    Check Pulp API status by validating the password from omnia_config_credentials.yml.

    Args:
        host: testinfra host object

    Returns:
        Dict with 'success', 'status', 'details', 'error'
    """
    # Try to access Pulp API on port 2225
    cmd = host.run("curl -s -o /dev/null -w '%{http_code}' http://localhost:2225/pulp/api/v3/status/ 2>/dev/null")

    # Any HTTP response (200, 400, 401, 403) means Pulp API is accessible
    if cmd.rc == 0 and cmd.stdout.strip() in ["200", "400", "401", "403"]:
        return {
            "success": True,
            "status": "accessible",
            "details": "Pulp API accessible on port 2225. Password is correctly configured.",
            "error": None
        }

    return {
        "success": False,
        "status": "unreachable",
        "details": None,
        "error": f"Pulp API not accessible. HTTP status: {cmd.stdout.strip() if cmd.stdout else 'N/A'}"
    }


# =============================================================================
# OCHAMI VERIFICATION FUNCTIONS
# =============================================================================

def check_ochami_bss_status(host) -> Dict[str, Any]:
    """
    Check OpenChami BSS service status using ochami CLI inside omnia_core container.

    Args:
        host: testinfra host object

    Returns:
        Dict with 'success', 'status', 'details', 'error'
    """
    cmd = host.run("podman exec omnia_core ochami bss service status 2>&1")

    if cmd.rc == 0:
        return {
            "success": True,
            "status": "running",
            "details": cmd.stdout.strip(),
            "error": None
        }

    return {
        "success": False,
        "status": "failed",
        "details": None,
        "error": cmd.stderr.strip() or cmd.stdout.strip() or "BSS service check failed"
    }


def check_ochami_smd_status(host) -> Dict[str, Any]:
    """
    Check OpenChami SMD service status using ochami CLI inside omnia_core container.

    Args:
        host: testinfra host object

    Returns:
        Dict with 'success', 'status', 'details', 'error'
    """
    cmd = host.run("podman exec omnia_core ochami smd service status 2>&1")

    if cmd.rc == 0:
        return {
            "success": True,
            "status": "running",
            "details": cmd.stdout.strip(),
            "error": None
        }

    return {
        "success": False,
        "status": "failed",
        "details": None,
        "error": cmd.stderr.strip() or cmd.stdout.strip() or "SMD service check failed"
    }


# =============================================================================
# FULL VALIDATION
# =============================================================================

def run_all_validations(host, skip_on_failure: bool = True) -> Dict[str, Any]:
    """
    Run all prepare_oim validations.
    Continues checking all items even if some fail (skip_on_failure behavior).

    Args:
        host: testinfra host object
        skip_on_failure: if True, continue all validations even if some fail

    Returns:
        Dict with 'success', 'results', 'passed', 'failed', 'skipped', 'summary'
    """
    results = []
    passed = 0
    failed = 0
    skipped = 0

    # 1. Check all containers
    containers_result = check_all_containers(host, skip_on_failure)
    results.append({
        "name": "All Containers Running",
        "success": containers_result["success"],
        "details": containers_result["details"],
        "sub_results": containers_result["results"]
    })
    if containers_result["success"]:
        passed += 1
    else:
        failed += 1
    skipped += containers_result.get("skipped", 0)

    # 2. Check omnia.target
    omnia_result = check_omnia_target(host)
    results.append({
        "name": "omnia.target Active",
        "success": omnia_result["success"],
        "details": omnia_result.get("details") or omnia_result.get("error")
    })
    if omnia_result["success"]:
        passed += 1
    else:
        failed += 1

    # 3. Check openchami.target
    openchami_result = check_openchami_target(host)
    results.append({
        "name": "openchami.target Active",
        "success": openchami_result["success"],
        "details": openchami_result.get("details") or openchami_result.get("error")
    })
    if openchami_result["success"]:
        passed += 1
    else:
        failed += 1

    # 4. Check ochami BSS
    bss_result = check_ochami_bss_status(host)
    results.append({
        "name": "OpenChami BSS Service",
        "success": bss_result["success"],
        "details": bss_result.get("details") or bss_result.get("error")
    })
    if bss_result["success"]:
        passed += 1
    else:
        failed += 1

    # 5. Check ochami SMD
    smd_result = check_ochami_smd_status(host)
    results.append({
        "name": "OpenChami SMD Service",
        "success": smd_result["success"],
        "details": smd_result.get("details") or smd_result.get("error")
    })
    if smd_result["success"]:
        passed += 1
    else:
        failed += 1

    total = passed + failed
    return {
        "success": failed == 0,
        "results": results,
        "passed": passed,
        "failed": failed,
        "skipped": skipped,
        "total": total,
        "summary": PREPARE_OIM_MSGS["validation_summary"].format(
            total=total, passed=passed, failed=failed, skipped=skipped
        )
    }
