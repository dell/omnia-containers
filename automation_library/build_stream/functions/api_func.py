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
Build Stream API Functions (v2.1).

Verification functions for build_stream API health check, catalog roles,
registry images, and S3 boot images.
"""

import json
from typing import Dict, Any, List

from automation_library.core import run_on_oim

from .shared_func import (
    get_build_stream_host_ip,
    get_build_stream_port,
    get_gitlab_host,
    get_gitlab_https_port,
    get_gitlab_project_name,
)
from .gitlab_func import get_gitlab_root_token
from ..vars.build_stream_vars import (
    GITLAB_API_VERSION,
    BUILD_STREAM_HEALTH_PATH,
    REGISTRY_PORT,
    REGISTRY_IMAGE_PREFIX,
    S3_BOOT_IMAGES_BUCKET,
    S3_EFI_IMAGES_PREFIX,
    BOOT_IMAGE_ARTIFACTS_PER_ROLE,
)

# Module-level token cache
_bsm_token_cache: Dict[str, str] = {}


def _get_bsm_access_token(host) -> str:
    """
    Obtain a Build Stream API access token using OAuth2 client credentials.

    Reads BSM_CLIENT_ID and BSM_CLIENT_SECRET from GitLab CI/CD project
    variables, then calls POST /api/v1/auth/token.

    Returns:
        Access token string, or empty string on failure.
    """
    if "access_token" in _bsm_token_cache:
        return _bsm_token_cache["access_token"]

    host_ip = get_build_stream_host_ip(host)
    port = get_build_stream_port(host)
    if not host_ip or not port:
        return ""

    token_result = get_gitlab_root_token(host)
    if not token_result.get("success"):
        return ""
    gitlab_token = token_result["token"]

    gitlab_host = get_gitlab_host(host)
    gitlab_port = get_gitlab_https_port(host)
    project_name = get_gitlab_project_name(host)
    gitlab_api_url = (
        f"https://{gitlab_host}:{gitlab_port}/api/{GITLAB_API_VERSION}"
    )
    vars_cmd = run_on_oim(
        host,
        f"curl -sk --header 'PRIVATE-TOKEN: {gitlab_token}' "
        f"'{gitlab_api_url}/projects/root%2F{project_name}/variables' 2>/dev/null"
    )
    if vars_cmd.rc != 0 or not vars_cmd.stdout.strip():
        return ""

    try:
        variables = json.loads(vars_cmd.stdout.strip())
        creds = {v["key"]: v["value"] for v in variables}
    except (json.JSONDecodeError, KeyError):
        return ""

    client_id = creds.get("BSM_CLIENT_ID", "")
    client_secret = creds.get("BSM_CLIENT_SECRET", "")
    if not client_id or not client_secret:
        return ""

    token_url = f"https://{host_ip}:{port}/api/v1/auth/token"
    token_cmd = run_on_oim(
        host,
        f"curl -sk -X POST '{token_url}' "
        f"-H 'Content-Type: application/x-www-form-urlencoded' "
        f"-d 'grant_type=client_credentials"
        f"&client_id={client_id}&client_secret={client_secret}' 2>/dev/null"
    )
    if token_cmd.rc != 0 or not token_cmd.stdout.strip():
        return ""

    try:
        token_data = json.loads(token_cmd.stdout.strip())
        access_token = token_data.get("access_token", "")
        if access_token:
            _bsm_token_cache["access_token"] = access_token
        return access_token
    except json.JSONDecodeError:
        return ""


def clear_bsm_token_cache():
    """Clear the BSM token cache to force re-authentication."""
    _bsm_token_cache.clear()


def check_build_stream_health(host) -> Dict[str, Any]:
    """
    Verify the build_stream API /health endpoint returns {"status": "healthy"}.

    Reads host_ip and port from build_stream_config.yml.

    Args:
        host: Testinfra host object connected to OIM server.

    Returns:
        Dict with 'success', 'status', 'url', 'details', 'error'.
    """
    result = {
        "success": False,
        "status": "",
        "url": "",
        "details": "",
        "error": "",
    }

    host_ip = get_build_stream_host_ip(host)
    port = get_build_stream_port(host)

    if not host_ip:
        result["status"] = "config_error"
        result["error"] = "build_stream_host_ip not configured in build_stream_config.yml"
        return result

    if not port:
        result["status"] = "config_error"
        result["error"] = "build_stream_port not configured in build_stream_config.yml"
        return result

    url = f"https://{host_ip}:{port}{BUILD_STREAM_HEALTH_PATH}"
    result["url"] = url

    http_code_cmd = run_on_oim(
        host,
        f"curl -sk -o /dev/null -w '%{{http_code}}' {url} 2>/dev/null"
    )
    http_code = http_code_cmd.stdout.strip()

    if http_code_cmd.rc == 0 and http_code == "200":
        body_cmd = run_on_oim(host, f"curl -sk {url} 2>/dev/null")
        body = body_cmd.stdout.strip()

        if '"healthy"' in body.replace(" ", ""):
            result["success"] = True
            result["status"] = "healthy"
            result["details"] = f"GET {url} -> {body}"
            return result

        result["status"] = "unhealthy"
        result["details"] = body
        result["error"] = f"GET {url} returned unexpected body: {body}"
        return result

    result["status"] = "unreachable"
    result["error"] = (
        f"GET {url} unreachable. "
        f"HTTP status: {http_code or 'N/A'} (curl rc={http_code_cmd.rc})"
    )
    return result


def get_catalog_roles(host, job_id: str) -> Dict[str, Any]:
    """
    Get catalog roles and architectures from the Build Stream API.

    Calls GET /api/v1/jobs/{job_id}/catalog/roles.

    Args:
        host: Testinfra host object connected to OIM server.
        job_id: UUID of the job.

    Returns:
        Dict with 'success', 'roles', 'architectures', 'image_key', 'error'.
    """
    result = {
        "success": False,
        "roles": [],
        "architectures": [],
        "image_key": "",
        "error": "",
    }

    host_ip = get_build_stream_host_ip(host)
    port = get_build_stream_port(host)

    if not host_ip or not port:
        result["error"] = "build_stream host_ip or port not configured"
        return result

    access_token = _get_bsm_access_token(host)
    if not access_token:
        result["error"] = "Failed to obtain BSM API access token"
        return result

    url = f"https://{host_ip}:{port}/api/v1/jobs/{job_id}/catalog/roles"

    cmd = run_on_oim(
        host,
        f"curl -sk -H 'Authorization: Bearer {access_token}' '{url}' 2>/dev/null"
    )
    if cmd.rc != 0 or not cmd.stdout.strip():
        result["error"] = f"API call failed: rc={cmd.rc}"
        return result

    try:
        data = json.loads(cmd.stdout.strip())
    except json.JSONDecodeError:
        result["error"] = f"Invalid JSON response: {cmd.stdout[:200]}"
        return result

    if "detail" in data:
        result["error"] = f"API error: {data['detail']}"
        return result

    result["success"] = True
    result["roles"] = data.get("roles", [])
    result["architectures"] = data.get("architectures", [])
    result["image_key"] = data.get("image_key", "")
    return result


def get_stage_log_path(host, job_id: str, stage_name: str) -> str:
    """
    Get the log file path for a failed stage from the Build Stream API.

    Args:
        host: Testinfra host object connected to OIM server.
        job_id: UUID of the job.
        stage_name: Name of the stage.

    Returns:
        Log file path string, or empty string if not available.
    """
    host_ip = get_build_stream_host_ip(host)
    port = get_build_stream_port(host)
    if not host_ip or not port:
        return ""

    access_token = _get_bsm_access_token(host)
    if not access_token:
        return ""

    url = f"https://{host_ip}:{port}/api/v1/jobs/{job_id}"
    cmd = run_on_oim(
        host,
        f"curl -sk -H 'Authorization: Bearer {access_token}' '{url}' 2>/dev/null"
    )
    if cmd.rc != 0 or not cmd.stdout.strip():
        return ""

    try:
        data = json.loads(cmd.stdout.strip())
    except json.JSONDecodeError:
        return ""

    for stage in data.get("stages", []):
        if stage.get("stage_name") == stage_name:
            return stage.get("log_file_path", "")
    return ""


def verify_registry_images(
    host, job_id: str, roles: List[str], image_key: str
) -> Dict[str, Any]:
    """
    Verify that container images exist in the local registry for each role.

    Args:
        host: Testinfra host object connected to OIM server.
        job_id: UUID of the job.
        roles: List of role names from catalog.
        image_key: Image key identifier.

    Returns:
        Dict with 'success', 'found', 'missing', 'all_repos', 'registry_url',
        'details', 'error'.
    """
    result = {
        "success": False,
        "found": [],
        "missing": [],
        "all_repos": [],
        "registry_url": "",
        "details": "",
        "error": "",
    }

    hostname_cmd = run_on_oim(host, "hostname")
    if hostname_cmd.rc != 0 or not hostname_cmd.stdout.strip():
        result["error"] = f"Failed to get OIM hostname: {hostname_cmd.stderr}"
        return result

    hostname = hostname_cmd.stdout.strip()
    registry_url = f"{hostname}:{REGISTRY_PORT}"
    result["registry_url"] = registry_url

    regctl_cmd = run_on_oim(
        host, f"regctl repo ls {registry_url} 2>/dev/null"
    )

    if regctl_cmd.rc != 0:
        result["error"] = (
            f"regctl repo ls {registry_url} failed: "
            f"{regctl_cmd.stderr or 'regctl command failed'}"
        )
        return result

    repos = [
        line.strip()
        for line in regctl_cmd.stdout.strip().split("\n")
        if line.strip()
    ]
    result["all_repos"] = repos

    for role in roles:
        role_pattern = f"{REGISTRY_IMAGE_PREFIX}{role}"
        matched = [
            r for r in repos
            if role_pattern in r and job_id in r
        ]
        if matched:
            result["found"].append({
                "role": role,
                "repo": f"{registry_url}/{matched[0]}",
            })
        else:
            result["missing"].append(role)

    result["success"] = len(result["missing"]) == 0
    result["details"] = (
        f"Registry ({registry_url}): {len(result['found'])}/{len(roles)} "
        f"roles found, {len(repos)} total repos"
    )
    return result


def verify_s3_boot_images(
    host, job_id: str, roles: List[str], image_key: str
) -> Dict[str, Any]:
    """
    Verify that S3 boot images exist for each role.

    Expected per role (3 files total):
      - 1 rootfs in s3://boot-images/{role}/
      - 2 EFI files (initramfs + vmlinuz) in s3://boot-images/efi-images/{role}/

    Args:
        host: Testinfra host object connected to OIM server.
        job_id: UUID of the job.
        roles: List of role names from catalog.
        image_key: Image key identifier.

    Returns:
        Dict with 'success', 'found_roles', 'missing_roles', 'total_files',
        'details', 'error'.
    """
    result = {
        "success": False,
        "found_roles": [],
        "missing_roles": [],
        "total_files": 0,
        "details": "",
        "error": "",
    }

    cmd = run_on_oim(
        host,
        f"s3cmd ls -r {S3_BOOT_IMAGES_BUCKET} 2>/dev/null"
    )

    if cmd.rc != 0:
        result["error"] = f"s3cmd failed: rc={cmd.rc}, stderr={cmd.stderr[:200]}"
        return result

    s3_output = cmd.stdout.strip()
    s3_lines = [line.strip() for line in s3_output.split("\n") if line.strip()]
    result["total_files"] = len(s3_lines)

    s3_paths = []
    for line in s3_lines:
        parts = line.split()
        if parts:
            s3_path = parts[-1]
            if s3_path.startswith("s3://"):
                s3_paths.append(s3_path)

    for role in roles:
        rootfs_files = [
            p for p in s3_paths
            if p.startswith(f"{S3_BOOT_IMAGES_BUCKET}{role}/")
            and job_id in p
        ]
        efi_files = [
            p for p in s3_paths
            if p.startswith(f"{S3_EFI_IMAGES_PREFIX}{role}/")
            and job_id in p
        ]

        total_for_role = len(rootfs_files) + len(efi_files)
        role_info = {
            "role": role,
            "rootfs": len(rootfs_files),
            "rootfs_files": rootfs_files[:3],
            "efi_files": len(efi_files),
            "efi_file_paths": efi_files[:3],
            "total": total_for_role,
        }

        if (len(rootfs_files) >= 1
                and len(efi_files) >= 2
                and total_for_role >= BOOT_IMAGE_ARTIFACTS_PER_ROLE):
            result["found_roles"].append(role_info)
        else:
            result["missing_roles"].append(role_info)

    found_total = sum(r["total"] for r in result["found_roles"])
    result["success"] = len(result["missing_roles"]) == 0
    result["details"] = (
        f"S3: {len(result['found_roles'])}/{len(roles)} roles complete, "
        f"{found_total} matching files"
    )
    return result
