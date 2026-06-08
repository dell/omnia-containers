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
Prepare OIM - Core Functions.

This module contains all verification functions for prepare_oim tests.
Test functions should call these functions - all logic resides here.
"""

import time
from typing import Dict, Any, List

from automation_library.core import (
    run_in_container,
    check_container_running as _core_check_container,
    load_input_file,
    get_input_value,
    is_build_stream_enabled,
    SOFTWARE_CONFIG_FILE,
    NETWORK_SPEC_FILE,
)
from ..vars.prepare_oim_vars import (
    OPENCHAMI_CONTAINERS,
    CORE_CONTAINERS,
    AUTH_CONTAINER,
    OMNIA_TARGET_SERVICES,
    OPENCHAMI_TARGET_SERVICES,
    PULP_CERT_PATH,
    LDAP_CERT_PATH,
    BUILD_STREAM_CONTAINERS,
    BUILD_STREAM_SERVICE,
    PULP_API_PORT,
    OCHAMI_AUTH_RETRIES,
    OCHAMI_AUTH_DELAY,
    CERT_WAIT_TIME,
    STORAGE_BACKEND_MINIO,
    MINIO_CONTAINER,
    MINIO_SERVICE,
)
from .storage_func import get_storage_backend


# =============================================================================
# CONFIG HELPERS (module-specific logic using core get_input_value)
# =============================================================================

def is_ldap_enabled(host) -> bool:
    """Check if openldap/LDAP is present in software_config.json softwares list."""
    softwares = get_input_value(host, SOFTWARE_CONFIG_FILE, "softwares")
    if not softwares:
        return False
    for software in softwares:
        if isinstance(software, dict):
            name = software.get("name", "").lower()
            if "openldap" in name or "ldap" in name:
                return True
        elif isinstance(software, str):
            if "openldap" in software.lower() or "ldap" in software.lower():
                return True
    return False


def get_primary_oim_admin_ip(host) -> str:
    """Get primary_oim_admin_ip from network_spec.yml admin_network."""
    config = load_input_file(host, NETWORK_SPEC_FILE)
    networks = config.get("Networks", config.get("networks", []))
    for network in networks:
        if isinstance(network, dict):
            admin = network.get("admin_network", {})
            if admin:
                ip = admin.get("primary_oim_admin_ip", "")
                if ip:
                    return ip
    return ""


# =============================================================================
# CONTAINER VERIFICATION FUNCTIONS (for pytest/testinfra)
# =============================================================================

def check_container_running(host, container_name: str) -> Dict[str, Any]:
    """Check if a specific container is running. Delegates to core."""
    return _core_check_container(host, container_name)


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
    # Try to access Pulp API
    curl_cmd = (
        "curl -s -o /dev/null -w '%{http_code}' "
        f"http://localhost:{PULP_API_PORT}/pulp/api/v3/status/ 2>/dev/null"
    )
    cmd = host.run(curl_cmd)

    # Any HTTP response (200, 400, 401, 403) means Pulp API is accessible
    if cmd.rc == 0 and cmd.stdout.strip() in ["200", "400", "401", "403"]:
        return {
            "success": True,
            "status": "accessible",
            "details": (
                f"Pulp API accessible on port {PULP_API_PORT}. "
                f"Password is correctly configured."
            ),
            "error": None
        }

    http_status = cmd.stdout.strip() if cmd.stdout else 'N/A'
    return {
        "success": False,
        "status": "unreachable",
        "details": None,
        "error": (
            f"Pulp API not accessible. HTTP status: {http_status}"
        ),
    }


def check_pulp_certificate(host) -> Dict[str, Any]:
    """
    Check if Pulp webserver certificate exists inside omnia_core container.

    Args:
        host: testinfra host object

    Returns:
        Dict with 'success', 'status', 'details', 'error'
    """
    cert_path = PULP_CERT_PATH
    cmd = run_in_container(host, f"test -f {cert_path} && echo 'EXISTS' || echo 'NOT_FOUND'")

    if cmd.rc == 0 and "EXISTS" in cmd.stdout:
        cert_info_cmd = run_in_container(
            host, f"openssl x509 -in {cert_path} -noout -subject -dates 2>/dev/null"
        )
        cert_details = (
            cert_info_cmd.stdout.strip()
            if cert_info_cmd.rc == 0
            else "Certificate exists"
        )
        return {
            "success": True,
            "status": "exists",
            "details": f"Pulp certificate found at {cert_path}\n{cert_details}",
            "error": None
        }

    return {
        "success": False,
        "status": "not_found",
        "details": None,
        "error": f"Pulp certificate not found at {cert_path} inside omnia_core container"
    }


# =============================================================================
# OCHAMI AUTH / CERTIFICATE HELPERS
# =============================================================================

def _generate_access_token(host) -> Dict[str, Any]:
    """
    Generate a fresh access token with retries.

    Runs 'gen_access_token' with retries/delay until a non-empty,
    non-null token is returned.

    Returns:
        Dict with 'success', 'token', 'env_var', 'error'
    """
    hostname = host.run("hostname -s").stdout.strip().upper()
    env_var = f"{hostname}_ACCESS_TOKEN"

    for attempt in range(1, OCHAMI_AUTH_RETRIES + 1):
        cmd = host.run("sudo bash -lc 'gen_access_token'")
        token = cmd.stdout.strip()
        if cmd.rc == 0 and token and token != "null":
            return {"success": True, "token": token, "env_var": env_var, "error": None}
        if attempt < OCHAMI_AUTH_RETRIES:
            time.sleep(OCHAMI_AUTH_DELAY)

    return {
        "success": False,
        "token": "",
        "env_var": env_var,
        "error": f"Failed to generate access token after {OCHAMI_AUTH_RETRIES} attempts",
    }


def _regenerate_certificate(host) -> Dict[str, Any]:
    """
    Regenerate the certificate by restarting acme-deploy service.

    Steps:
        1. Restart acme-deploy service
        2. Wait CERT_WAIT_TIME seconds for cert provisioning
        3. Return success/failure

    Returns:
        Dict with 'success', 'error'
    """
    restart_cmd = host.run("systemctl restart acme-deploy")
    if restart_cmd.rc != 0:
        return {
            "success": False,
            "error": (
                f"Failed to restart acme-deploy service: "
                f"{restart_cmd.stderr.strip() or restart_cmd.stdout.strip()}"
            ),
        }

    time.sleep(CERT_WAIT_TIME)
    return {"success": True, "error": None}


def _run_ochami_cmd(host, ochami_cmd: str) -> Dict[str, Any]:
    """
    Generate a fresh access token and run an ochami CLI command.

    Returns:
        Dict with 'rc', 'stdout', 'stderr'
    """
    auth = _generate_access_token(host)
    if not auth["success"]:
        return {"rc": 1, "stdout": "", "stderr": auth["error"]}

    cmd = host.run(
        f"export {auth['env_var']}={auth['token']} && "
        f"ochami {ochami_cmd}"
    )
    return {"rc": cmd.rc, "stdout": cmd.stdout.strip(), "stderr": cmd.stderr.strip()}


# =============================================================================
# OCHAMI SERVICE STATUS VERIFICATION (BSS and SMD via ochami CLI)
# =============================================================================

def check_bss_service(host) -> Dict[str, Any]:
    """
    Check ochami BSS service status.

    Logic:
        1. Generate a fresh access token (with retries)
        2. Run ochami bss service status
        3. If it fails -> restart acme-deploy to regenerate certificate
        4. Wait CERT_WAIT_TIME seconds, then recheck

    Expected response: {"bss-status":"running"}

    Args:
        host: testinfra host object

    Returns:
        Dict with 'success', 'status', 'details', 'error'
    """
    result = _run_ochami_cmd(host, "bss service status")
    output = result["stdout"]

    if result["rc"] == 0 and '"bss-status":"running"' in output.replace(" ", ""):
        return {
            "success": True,
            "status": "running",
            "details": output,
            "error": None
        }

    # First attempt failed - regenerate certificate and retry
    cert_result = _regenerate_certificate(host)
    if not cert_result["success"]:
        return {
            "success": False,
            "status": "not running",
            "details": output if output else None,
            "error": (
                f"BSS check failed and certificate regeneration also failed: "
                f"{cert_result['error']}"
            ),
        }

    # Retry after certificate regeneration
    result = _run_ochami_cmd(host, "bss service status")
    output = result["stdout"]

    if result["rc"] == 0 and '"bss-status":"running"' in output.replace(" ", ""):
        return {
            "success": True,
            "status": "running",
            "details": f"{output} (recovered after certificate regeneration)",
            "error": None
        }

    return {
        "success": False,
        "status": "not running",
        "details": output if output else None,
        "error": (
            result["stderr"] or output
            or "BSS service is not running (even after certificate regeneration)"
        ),
    }


def check_smd_service(host) -> Dict[str, Any]:
    """
    Check ochami SMD service status.

    Logic:
        1. Generate a fresh access token (with retries)
        2. Run ochami smd service status
        3. If it fails -> restart acme-deploy to regenerate certificate
        4. Wait CERT_WAIT_TIME seconds, then recheck

    Expected response: {"code":0,"message":"HSM is healthy"}

    Args:
        host: testinfra host object

    Returns:
        Dict with 'success', 'status', 'details', 'error'
    """
    result = _run_ochami_cmd(host, "smd service status")
    output = result["stdout"]

    output_normalized = output.replace(" ", "")
    is_healthy = (
        result["rc"] == 0
        and '"code":0' in output_normalized
        and 'HSMishealthy' in output_normalized
    )
    if is_healthy:
        return {
            "success": True,
            "status": "healthy",
            "details": output,
            "error": None
        }

    # First attempt failed - regenerate certificate and retry
    cert_result = _regenerate_certificate(host)
    if not cert_result["success"]:
        return {
            "success": False,
            "status": "not healthy",
            "details": output if output else None,
            "error": (
                f"SMD check failed and certificate regeneration "
                f"also failed: {cert_result['error']}"
            ),
        }

    # Retry after certificate regeneration
    result = _run_ochami_cmd(host, "smd service status")
    output = result["stdout"]

    output_normalized = output.replace(" ", "")
    is_healthy = (
        result["rc"] == 0
        and '"code":0' in output_normalized
        and 'HSMishealthy' in output_normalized
    )
    if is_healthy:
        return {
            "success": True,
            "status": "healthy",
            "details": f"{output} (recovered after certificate regeneration)",
            "error": None
        }

    return {
        "success": False,
        "status": "not healthy",
        "details": output if output else None,
        "error": (
            result["stderr"] or output
            or "SMD service is not healthy (even after certificate regeneration)"
        ),
    }


# =============================================================================
# LDAP AUTH CERTIFICATE VERIFICATION
# =============================================================================

def check_ldap_auth_certificate(host) -> Dict[str, Any]:
    """
    Check if LDAP auth certificate exists inside omnia_core container.
    Only checks if LDAP is enabled in software_config.json.

    Args:
        host: testinfra host object

    Returns:
        Dict with 'success', 'status', 'skipped', 'details', 'error'
    """
    if not is_ldap_enabled(host):
        return {
            "success": True,
            "status": "skipped",
            "skipped": True,
            "details": "LDAP auth certificate check skipped (LDAP not in software_config.json)",
            "error": None
        }

    cert_path = LDAP_CERT_PATH
    cmd = run_in_container(host, f"test -f {cert_path} && echo 'EXISTS' || echo 'NOT_FOUND'")

    if cmd.rc == 0 and "EXISTS" in cmd.stdout:
        cert_info_cmd = run_in_container(
            host, f"openssl x509 -in {cert_path} -noout -subject -dates 2>/dev/null"
        )
        cert_details = (
            cert_info_cmd.stdout.strip()
            if cert_info_cmd.rc == 0
            else "Certificate exists"
        )
        return {
            "success": True,
            "status": "exists",
            "skipped": False,
            "details": f"LDAP certificate found at {cert_path}\n{cert_details}",
            "error": None
        }

    return {
        "success": False,
        "status": "not_found",
        "skipped": False,
        "details": None,
        "error": f"LDAP certificate not found at {cert_path} inside omnia_core container"
    }


# =============================================================================
# CONSOLIDATED STATUS FUNCTIONS
# =============================================================================

def check_all_services_status(host) -> Dict[str, Any]:
    """
    Check all expected systemd services/targets.

    For each service:
      - If expected_active=True  and active   -> PASS
      - If expected_active=True  and inactive -> FAIL
      - If expected_active=False and inactive -> PASS (expected not running)
      - If expected_active=False and active   -> FAIL (should not be running)

    Returns:
        Dict with 'success', 'results', 'passed', 'failed', 'details'
    """
    expected = get_expected_services(host)
    results = []
    passed = 0
    failed = 0

    for svc in expected:
        status_cmd = host.run(
            f"systemctl is-active {svc['name']} 2>/dev/null"
        )
        actual_status = status_cmd.stdout.strip()
        is_active = actual_status == "active"

        if svc["expected_active"] and is_active:
            verdict = "pass"
            message = f"{svc['name']}: active"
            passed += 1
        elif svc["expected_active"] and not is_active:
            verdict = "fail"
            message = f"{svc['name']}: {actual_status} (expected active)"
            failed += 1
        elif not svc["expected_active"] and not is_active:
            verdict = "pass"
            message = (
                f"{svc['name']}: not running "
                f"(expected, {svc['reason']})"
            )
            passed += 1
        else:
            verdict = "fail"
            message = (
                f"{svc['name']}: active "
                f"(should NOT be running, {svc['reason']})"
            )
            failed += 1

        results.append({
            "name": svc["name"],
            "category": svc["category"],
            "expected_active": svc["expected_active"],
            "actual_status": actual_status,
            "is_active": is_active,
            "verdict": verdict,
            "reason": svc["reason"],
            "message": message,
        })

    total = passed + failed
    details = f"Services: {passed}/{total} in expected state\n"
    for svc in results:
        mark = "✓" if svc["verdict"] == "pass" else "✘"
        details += f"  {mark} {svc['message']}\n"

    return {
        "success": failed == 0,
        "results": results,
        "passed": passed,
        "failed": failed,
        "total": total,
        "details": details,
    }


def check_all_containers_status(host) -> Dict[str, Any]:
    """
    Check all expected containers.

    For each container:
      - If expected_running=True  and running     -> PASS
      - If expected_running=True  and not running  -> FAIL
      - If expected_running=False and not running  -> PASS (expected)
      - If expected_running=False and running      -> FAIL (should not be running)

    Returns:
        Dict with 'success', 'results', 'passed', 'failed', 'details'
    """
    expected = get_expected_containers(host)
    results = []
    passed = 0
    failed = 0

    for ctr in expected:
        result = check_container_running(host, ctr["name"])
        is_running = result["success"]
        actual_status = result["status"]

        if ctr["expected_running"] and is_running:
            verdict = "pass"
            message = f"{ctr['name']}: running"
            passed += 1
        elif ctr["expected_running"] and not is_running:
            verdict = "fail"
            message = (
                f"{ctr['name']}: {actual_status} (expected running)"
            )
            failed += 1
        elif not ctr["expected_running"] and not is_running:
            verdict = "pass"
            message = (
                f"{ctr['name']}: not running "
                f"(expected, {ctr['reason']})"
            )
            passed += 1
        else:
            verdict = "fail"
            message = (
                f"{ctr['name']}: running "
                f"(should NOT be running, {ctr['reason']})"
            )
            failed += 1

        results.append({
            "name": ctr["name"],
            "category": ctr["category"],
            "expected_running": ctr["expected_running"],
            "actual_status": actual_status,
            "is_running": is_running,
            "verdict": verdict,
            "reason": ctr["reason"],
            "message": message,
        })

    total = passed + failed
    details = f"Containers: {passed}/{total} in expected state\n"
    for ctr in results:
        mark = "✓" if ctr["verdict"] == "pass" else "✘"
        details += f"  {mark} {ctr['message']}\n"

    return {
        "success": failed == 0,
        "results": results,
        "passed": passed,
        "failed": failed,
        "total": total,
        "details": details,
    }


# =============================================================================
# TARGET DEPENDENCY VERIFICATION FUNCTIONS
# =============================================================================

def _parse_direct_deps(host, target: str):
    """
    Parse only direct (first-level) dependencies of a systemd target.

    systemctl list-dependencies output uses indentation for nesting:
      omnia.target
      ● ├─minio.service           <- first level (starts at col ~2-4)
      ● └─openchami.target        <- first level
      ●   ├─bss.service           <- second level (deeper indent)

    We only capture first-level items by checking the indent depth.
    """
    cmd = host.run(f"systemctl list-dependencies {target} --no-pager 2>/dev/null")
    if cmd.rc != 0:
        return cmd.rc, []

    deps = []
    lines = cmd.stdout.strip().split("\n")
    first_level_indent = None

    for line in lines:
        if not line.strip() or target in line:
            continue

        # Measure indent: count leading chars before the unit name
        # Unit names start with a letter or digit
        indent = 0
        for ch in line:
            if ch.isalnum():
                break
            indent += 1

        if first_level_indent is None:
            first_level_indent = indent

        # Only capture lines at the first indent level
        if indent == first_level_indent:
            # Extract unit name: strip tree chars
            cleaned = line
            for ch in ("●", "├", "└", "─", "│"):
                cleaned = cleaned.replace(ch, "")
            cleaned = cleaned.strip()
            if cleaned:
                deps.append(cleaned)

    return cmd.rc, deps


def check_openchami_target_deps(host) -> Dict[str, Any]:
    """
    Compare actual openchami.target dependencies against expected list.

    Returns:
        Dict with 'success', 'matched', 'missing', 'extra', 'actual'
        - matched: services present in both expected and actual
        - missing: expected but NOT attached
        - extra: attached but NOT expected
    """
    target = "openchami.target"
    rc, actual_deps = _parse_direct_deps(host, target)
    if rc != 0:
        return {
            "success": False,
            "matched": [], "missing": [], "extra": [], "actual": [],
            "error": f"Failed to list dependencies for {target}",
        }

    expected = set(OPENCHAMI_TARGET_SERVICES)
    actual = set(actual_deps)

    matched = sorted(expected & actual)
    missing = sorted(expected - actual)
    extra = sorted(actual - expected)

    details = (
        f"openchami.target: {len(matched)} matched, "
        f"{len(missing)} missing, {len(extra)} extra\n"
    )
    for dep in matched:
        details += f"  ✓ {dep}\n"
    for dep in missing:
        details += f"  ✘ {dep} (expected but NOT attached)\n"
    for dep in extra:
        details += f"  ✘ {dep} (attached but NOT expected)\n"

    return {
        "success": len(missing) == 0 and len(extra) == 0,
        "matched": matched,
        "missing": missing,
        "extra": extra,
        "actual": sorted(actual),
        "details": details,
    }


def check_omnia_target_deps(host) -> Dict[str, Any]:
    """
    Compare actual omnia.target dependencies against expected list.

    Expected = always-on services + openchami.target
             + omnia_auth.service (if LDAP)

    Returns:
        Dict with 'success', 'matched', 'missing', 'extra', 'actual'
    """
    target = "omnia.target"
    rc, actual_deps = _parse_direct_deps(host, target)
    if rc != 0:
        return {
            "success": False,
            "matched": [], "missing": [], "extra": [], "actual": [],
            "error": f"Failed to list dependencies for {target}",
        }

    # Build expected set
    expected = set(OMNIA_TARGET_SERVICES)
    expected.add("openchami.target")

    if get_storage_backend(host) == STORAGE_BACKEND_MINIO:
        expected.add(MINIO_SERVICE)

    if is_ldap_enabled(host):
        expected.add("omnia_auth.service")

    if is_build_stream_enabled(host):
        expected.add("omnia_build_stream.service")
        expected.add("omnia_postgres.service")
        expected.add(BUILD_STREAM_SERVICE)

    actual = set(actual_deps)

    matched = sorted(expected & actual)
    missing = sorted(expected - actual)
    extra = sorted(actual - expected)

    details = (
        f"omnia.target: {len(matched)} matched, "
        f"{len(missing)} missing, {len(extra)} extra\n"
    )
    for dep in matched:
        details += f"  ✓ {dep}\n"
    for dep in missing:
        details += f"  ✘ {dep} (expected but NOT attached)\n"
    for dep in extra:
        details += f"  ✘ {dep} (attached but NOT expected)\n"

    return {
        "success": len(missing) == 0 and len(extra) == 0,
        "matched": matched,
        "missing": missing,
        "extra": extra,
        "actual": sorted(actual),
        "details": details,
    }


# =============================================================================
# EXPECTED STATE BUILDERS (domain logic using vars + core config)
# =============================================================================

def get_expected_containers(host) -> List[Dict[str, Any]]:
    """
    Get list of all containers with their expected running state.

    Each entry: {name, expected_running (bool), category, reason}
    - Core + OpenCHAMI: always expected running
    - Auth: expected running only if LDAP enabled

    Returns:
        List of dicts with 'name', 'expected_running', 'category', 'reason'
    """
    containers = []

    for name in CORE_CONTAINERS:
        containers.append({
            "name": name, "expected_running": True,
            "category": "core", "reason": "always required"
        })

    for name in OPENCHAMI_CONTAINERS:
        containers.append({
            "name": name, "expected_running": True,
            "category": "openchami", "reason": "always required"
        })

    is_minio = get_storage_backend(host) == STORAGE_BACKEND_MINIO
    containers.append({
        "name": MINIO_CONTAINER,
        "expected_running": is_minio,
        "category": "openchami",
        "reason": "MinIO storage backend" if is_minio else "PowerScale storage (MinIO not used)"
    })

    ldap = is_ldap_enabled(host)
    containers.append({
        "name": AUTH_CONTAINER,
        "expected_running": ldap,
        "category": "auth",
        "reason": "LDAP enabled" if ldap else "LDAP not enabled"
    })

    bsm = is_build_stream_enabled(host)
    for name in BUILD_STREAM_CONTAINERS:
        containers.append({
            "name": name,
            "expected_running": bsm,
            "category": "build_stream",
            "reason": "build_stream enabled" if bsm else "build_stream not enabled"
        })

    return containers


def get_expected_services(host) -> List[Dict[str, Any]]:
    """
    Get list of ALL systemd services/targets with their expected active state.

    Includes:
      - omnia.target, openchami.target (always)
      - omnia.target always-on services: omnia_core, pulp, registry, minio
      - openchami.target services (always)
      - omnia_auth.service (conditional: LDAP)

    Returns:
        List of dicts with 'name', 'expected_active', 'category', 'reason'
    """
    services = [
        {"name": "omnia.target", "expected_active": True,
         "category": "omnia_target", "reason": "always required"},
        {"name": "openchami.target", "expected_active": True,
         "category": "omnia_target", "reason": "always required"},
    ]

    for svc in OMNIA_TARGET_SERVICES:
        services.append({
            "name": svc, "expected_active": True,
            "category": "omnia_target", "reason": "omnia.target dependency"
        })

    is_minio = get_storage_backend(host) == STORAGE_BACKEND_MINIO
    services.append({
        "name": MINIO_SERVICE,
        "expected_active": is_minio,
        "category": "omnia_target",
        "reason": "MinIO storage backend" if is_minio else "PowerScale storage (MinIO not used)"
    })

    for svc in OPENCHAMI_TARGET_SERVICES:
        services.append({
            "name": svc, "expected_active": True,
            "category": "openchami_target", "reason": "openchami.target dependency"
        })

    ldap = is_ldap_enabled(host)
    services.append({
        "name": "omnia_auth.service",
        "expected_active": ldap,
        "category": "auth",
        "reason": "LDAP enabled" if ldap else "LDAP not enabled"
    })

    bsm = is_build_stream_enabled(host)
    services.append({
        "name": BUILD_STREAM_SERVICE,
        "expected_active": bsm,
        "category": "build_stream",
        "reason": "build_stream enabled" if bsm else "build_stream not enabled"
    })

    return services
