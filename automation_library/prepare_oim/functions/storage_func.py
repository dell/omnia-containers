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
Prepare OIM - Storage Verification Functions.

Verification functions for S3 storage backends (MinIO and PowerScale),
s3cmd configuration, regctl registry, and S3 bucket/directory checks.
"""

from typing import Dict, Any

from automation_library.core import (
    run_on_oim,
    run_in_container,
    get_input_value,
    check_container_running as _core_check_container,
    OIM_SHARED_PATH,
    OMNIA_CORE_CONTAINER,
    STORAGE_CONFIG_FILE,
)
from ..vars.prepare_oim_vars import (
    STORAGE_BACKEND_MINIO,
    STORAGE_BACKEND_POWERSCALE,
    S3_CONFIG_KEY,
    S3_PROVIDER_KEY,
    S3_ENDPOINT_URL_KEY,
    S3_EXPECTED_BUCKETS,
    MINIO_CONTAINER,
    MINIO_DATA_DIR_SUFFIX,
    S3CMD_CONFIG_PATH,
    REGISTRY_PORT,
    REGCTL_CONFIG_PATH,
    REGCTL_BINARY_PATH,
)


# =============================================================================
# STORAGE BACKEND DETECTION (reads from storage_config.yml dynamically)
# =============================================================================

def get_storage_backend(host) -> str:
    """
    Get the configured S3 storage backend from storage_config.yml.

    Returns:
        Storage backend string ('minio' or 'powerscale'), or empty string
        if not configured.
    """
    s3_config = get_input_value(
        host, STORAGE_CONFIG_FILE, S3_CONFIG_KEY, default={}
    )
    if not s3_config or not isinstance(s3_config, dict):
        return ""
    return s3_config.get(S3_PROVIDER_KEY, "").lower()


def get_s3_endpoint_url(host) -> str:
    """
    Get the S3 endpoint URL from storage_config.yml.

    Returns:
        Endpoint URL string, or empty string if not configured.
    """
    s3_config = get_input_value(
        host, STORAGE_CONFIG_FILE, S3_CONFIG_KEY, default={}
    )
    if not s3_config or not isinstance(s3_config, dict):
        return ""
    return s3_config.get(S3_ENDPOINT_URL_KEY, "")


# =============================================================================
# STORAGE BACKEND VERIFICATION
# =============================================================================

def verify_storage_backend(host) -> Dict[str, Any]:
    """
    Verify S3 storage backend is configured and operational.

    Checks:
    - storage_config.yml has valid s3_configurations
    - If MinIO: minio-server container is running
    - If PowerScale: endpoint_url is configured and reachable

    Returns:
        Dict with 'success', 'backend', 'details', 'error'.
    """
    result = {
        "success": False,
        "backend": "",
        "details": "",
        "error": "",
    }

    backend = get_storage_backend(host)
    if not backend:
        result["error"] = (
            "S3 storage backend not configured. "
            "Check s3_configurations.provider in storage_config.yml"
        )
        return result

    if backend not in (STORAGE_BACKEND_MINIO, STORAGE_BACKEND_POWERSCALE):
        result["error"] = (
            f"Unknown storage backend '{backend}'. "
            f"Expected '{STORAGE_BACKEND_MINIO}' or "
            f"'{STORAGE_BACKEND_POWERSCALE}'"
        )
        return result

    result["backend"] = backend

    if backend == STORAGE_BACKEND_MINIO:
        container_result = _core_check_container(host, MINIO_CONTAINER)
        if container_result["success"]:
            minio_data_path = (
                f"{OIM_SHARED_PATH}/{MINIO_DATA_DIR_SUFFIX}"
            )
            dir_cmd = run_in_container(
                host,
                f"test -d {minio_data_path} && echo 'EXISTS' "
                f"|| echo 'NOT_FOUND'",
                container=OMNIA_CORE_CONTAINER,
            )
            dir_exists = (
                dir_cmd.rc == 0 and "EXISTS" in dir_cmd.stdout
            )
            result["success"] = True
            result["details"] = (
                f"Storage backend: MinIO (local)\n"
                f"  Container '{MINIO_CONTAINER}': running\n"
                f"  Data directory '{minio_data_path}': "
                f"{'exists' if dir_exists else 'not found'}"
            )
        else:
            result["error"] = (
                f"MinIO container '{MINIO_CONTAINER}' is not running. "
                f"Status: {container_result.get('status', 'unknown')}"
            )

    elif backend == STORAGE_BACKEND_POWERSCALE:
        endpoint_url = get_s3_endpoint_url(host)
        if not endpoint_url:
            result["error"] = (
                "PowerScale endpoint_url not configured in "
                "storage_config.yml s3_configurations"
            )
            return result

        cmd = run_on_oim(
            host,
            f"curl -sk -o /dev/null -w '%{{http_code}}' "
            f"'{endpoint_url}' --connect-timeout 10 2>/dev/null"
        )
        http_code = cmd.stdout.strip() if cmd.stdout else "0"
        reachable = http_code in ["200", "403", "404", "405"]

        if reachable:
            result["success"] = True
            result["details"] = (
                f"Storage backend: PowerScale (external)\n"
                f"  Endpoint: {endpoint_url}\n"
                f"  Reachable: yes (HTTP {http_code})"
            )
        else:
            result["error"] = (
                f"PowerScale endpoint unreachable at {endpoint_url}. "
                f"HTTP status: {http_code}"
            )

    return result


# =============================================================================
# S3CMD VERIFICATION
# =============================================================================

def verify_s3cmd_working(host) -> Dict[str, Any]:
    """
    Verify s3cmd is installed and can communicate with the S3 endpoint.

    Checks:
    - s3cmd binary is available
    - ~/.s3cfg config file exists
    - s3cmd ls executes successfully

    Returns:
        Dict with 'success', 'config_exists', 'buckets', 'details', 'error'.
    """
    result = {
        "success": False,
        "config_exists": False,
        "buckets": [],
        "details": "",
        "error": "",
    }

    which_cmd = run_on_oim(host, "which s3cmd 2>/dev/null")
    if which_cmd.rc != 0:
        result["error"] = "s3cmd binary not found. Is s3cmd installed?"
        return result

    cfg_cmd = run_on_oim(
        host,
        f"test -f {S3CMD_CONFIG_PATH} && echo 'EXISTS' "
        f"|| echo 'NOT_FOUND'"
    )
    result["config_exists"] = (
        cfg_cmd.rc == 0 and "EXISTS" in cfg_cmd.stdout
    )
    if not result["config_exists"]:
        result["error"] = (
            f"s3cmd config not found at {S3CMD_CONFIG_PATH}. "
            "Run prepare_oim to generate it."
        )
        return result

    ls_cmd = run_on_oim(host, "s3cmd ls 2>/dev/null")
    if ls_cmd.rc != 0:
        stderr = ""
        if ls_cmd.stderr:
            stderr = ls_cmd.stderr.strip()[:200]
        result["error"] = (
            f"s3cmd ls failed (rc={ls_cmd.rc}). "
            f"Check S3 endpoint and credentials in {S3CMD_CONFIG_PATH}. "
            f"stderr: {stderr or 'N/A'}"
        )
        return result

    buckets = []
    for line in ls_cmd.stdout.strip().split("\n"):
        line = line.strip()
        if not line:
            continue
        for part in line.split():
            if part.startswith("s3://"):
                buckets.append(part)

    result["success"] = True
    result["buckets"] = buckets
    result["details"] = (
        f"s3cmd: installed and working\n"
        f"  Config: {S3CMD_CONFIG_PATH}\n"
        f"  Buckets found: {len(buckets)}"
    )
    for bucket in buckets:
        result["details"] += f"\n    - {bucket}"

    return result


# =============================================================================
# S3 BUCKET VERIFICATION
# =============================================================================

def verify_s3_buckets(host) -> Dict[str, Any]:
    """
    Verify required S3 buckets exist (efi, boot-images).

    Uses s3cmd ls to check bucket presence.

    Returns:
        Dict with 'success', 'found', 'missing', 'details', 'error'.
    """
    result = {
        "success": False,
        "found": [],
        "missing": [],
        "details": "",
        "error": "",
    }

    ls_cmd = run_on_oim(host, "s3cmd ls 2>/dev/null")
    if ls_cmd.rc != 0:
        result["error"] = (
            f"s3cmd ls failed (rc={ls_cmd.rc}). Cannot verify buckets."
        )
        return result

    output = ls_cmd.stdout.strip()

    for bucket in S3_EXPECTED_BUCKETS:
        if bucket in output:
            result["found"].append(bucket)
        else:
            result["missing"].append(bucket)

    result["success"] = len(result["missing"]) == 0
    bucket_total = len(S3_EXPECTED_BUCKETS)
    result["details"] = (
        f"S3 buckets: {len(result['found'])}/{bucket_total} present\n"
    )
    for bucket in result["found"]:
        result["details"] += f"  [ok] {bucket}\n"
    for bucket in result["missing"]:
        result["details"] += f"  [missing] {bucket}\n"

    return result


# =============================================================================
# REGCTL VERIFICATION
# =============================================================================

def verify_regctl_working(host) -> Dict[str, Any]:
    """
    Verify regctl is installed and registry is accessible.

    Checks:
    - regctl binary exists
    - regctl config file exists
    - regctl repo ls against local registry succeeds

    Returns:
        Dict with 'success', 'registry_url', 'repos', 'details', 'error'.
    """
    result = {
        "success": False,
        "registry_url": "",
        "repos": [],
        "details": "",
        "error": "",
    }

    binary_cmd = run_on_oim(
        host,
        f"test -x {REGCTL_BINARY_PATH} && echo 'EXISTS' "
        f"|| echo 'NOT_FOUND'"
    )
    if binary_cmd.rc != 0 or "NOT_FOUND" in binary_cmd.stdout:
        result["error"] = (
            f"regctl binary not found at {REGCTL_BINARY_PATH}. "
            "Run prepare_oim to install it."
        )
        return result

    config_cmd = run_on_oim(
        host,
        f"test -f {REGCTL_CONFIG_PATH} && echo 'EXISTS' "
        f"|| echo 'NOT_FOUND'"
    )
    config_exists = (
        config_cmd.rc == 0 and "EXISTS" in config_cmd.stdout
    )
    if not config_exists:
        result["error"] = (
            f"regctl config not found at {REGCTL_CONFIG_PATH}. "
            "Run prepare_oim to configure it."
        )
        return result

    hostname_cmd = run_on_oim(host, "hostname")
    if hostname_cmd.rc != 0 or not hostname_cmd.stdout.strip():
        result["error"] = "Failed to get OIM hostname for registry URL"
        return result

    hostname = hostname_cmd.stdout.strip()
    registry_url = f"{hostname}:{REGISTRY_PORT}"
    result["registry_url"] = registry_url

    regctl_cmd = run_on_oim(
        host, f"regctl repo ls {registry_url} 2>/dev/null"
    )

    if regctl_cmd.rc != 0:
        stderr = ""
        if regctl_cmd.stderr:
            stderr = regctl_cmd.stderr.strip()[:200]
        result["error"] = (
            f"regctl repo ls {registry_url} failed "
            f"(rc={regctl_cmd.rc}). {stderr}"
        )
        return result

    repos = [
        line.strip()
        for line in regctl_cmd.stdout.strip().split("\n")
        if line.strip()
    ]
    result["success"] = True
    result["repos"] = repos
    result["details"] = (
        f"regctl: installed and working\n"
        f"  Binary: {REGCTL_BINARY_PATH}\n"
        f"  Config: {REGCTL_CONFIG_PATH}\n"
        f"  Registry: {registry_url}\n"
        f"  Repositories: {len(repos)}"
    )

    return result


# =============================================================================
# S3 ENDPOINT DIRECTORY VERIFICATION
# =============================================================================

def verify_s3_directories(host) -> Dict[str, Any]:
    """
    Verify S3 directories are created at the configured endpoint.

    For MinIO: checks local NFS data directory exists.
    For PowerScale: checks buckets are accessible via s3cmd.

    Returns:
        Dict with 'success', 'backend', 'directories', 'details', 'error'.
    """
    result = {
        "success": False,
        "backend": "",
        "directories": [],
        "details": "",
        "error": "",
    }

    backend = get_storage_backend(host)
    if not backend:
        result["error"] = "Storage backend not configured"
        return result

    result["backend"] = backend

    if backend == STORAGE_BACKEND_MINIO:
        minio_data_path = (
            f"{OIM_SHARED_PATH}/{MINIO_DATA_DIR_SUFFIX}"
        )
        dir_cmd = run_in_container(
            host,
            f"ls -d {minio_data_path}/*/ 2>/dev/null || echo 'EMPTY'",
            container=OMNIA_CORE_CONTAINER,
        )

        if dir_cmd.rc == 0 and "EMPTY" not in dir_cmd.stdout:
            dirs = [
                d.strip().rstrip("/")
                for d in dir_cmd.stdout.strip().split("\n")
                if d.strip()
            ]
            result["directories"] = dirs
            result["success"] = True
            result["details"] = (
                f"MinIO data directory: {minio_data_path}\n"
                f"  Subdirectories: {len(dirs)}"
            )
            for d in dirs:
                result["details"] += f"\n    - {d}"
        else:
            dir_exists_cmd = run_in_container(
                host,
                f"test -d {minio_data_path} && echo 'EXISTS' "
                f"|| echo 'NOT_FOUND'",
                container=OMNIA_CORE_CONTAINER,
            )
            if "EXISTS" in dir_exists_cmd.stdout:
                result["success"] = True
                result["details"] = (
                    f"MinIO data directory exists: {minio_data_path}\n"
                    f"  Subdirectories: 0 (empty - buckets created "
                    f"on first use)"
                )
            else:
                result["error"] = (
                    f"MinIO data directory not found: "
                    f"{minio_data_path}"
                )

    elif backend == STORAGE_BACKEND_POWERSCALE:
        ls_cmd = run_on_oim(host, "s3cmd ls 2>/dev/null")
        if ls_cmd.rc != 0:
            result["error"] = (
                "Cannot verify PowerScale S3 directories. "
                f"s3cmd ls failed (rc={ls_cmd.rc})"
            )
            return result

        output = ls_cmd.stdout.strip()
        dirs = []
        for line in output.split("\n"):
            for part in line.split():
                if part.startswith("s3://"):
                    dirs.append(part)

        result["directories"] = dirs
        endpoint_url = get_s3_endpoint_url(host)
        result["success"] = len(dirs) > 0
        result["details"] = (
            f"PowerScale S3 endpoint: {endpoint_url}\n"
            f"  Buckets: {len(dirs)}"
        )
        for d in dirs:
            result["details"] += f"\n    - {d}"

        if not result["success"]:
            result["error"] = (
                f"No S3 buckets found at PowerScale endpoint "
                f"{endpoint_url}. Expected at least efi and "
                f"boot-images buckets."
            )

    return result
