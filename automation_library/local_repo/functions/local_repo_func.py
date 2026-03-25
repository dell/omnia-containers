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

"""Local Repo - Verification Functions.

Provides functions for verifying local_repo health:
- Container status (pulp, omnia_core)
- Pulp CLI, API, and service health
- Software download status (software.csv, per-software status.csv)
- RPM / container / file repository sync and distribution
- Pulp content accessibility via HTTP
- Package-level verification against software_config.json
"""

import csv
import io
import json
import re
from typing import Any, Dict, List

from ...core.host import run_in_container, check_container_running as _core_check_container
from ...core.load_inputs import load_input_file, load_container_file
from ...core.vars import INPUT_BASE_PATH, SOFTWARE_CONFIG_FILE
from ..vars.local_repo_vars import (
    ARCH_LIST,
    CURL_CONNECT_TIMEOUT,
    LOG_BASE_PATH,
    PULP_CONTENT_PATH_PREFIX,
    PULP_CONTENT_PORT,
    PULP_CONTENT_SCHEME,
    SOFTWARE_CSV_FILENAME,
    STATUS_CSV_FILENAME,
)


# =============================================================================
# HELPERS
# =============================================================================

def run_in_omnia_core(host, cmd: str) -> Dict[str, Any]:
    """Run a command in omnia_core container via ``run_in_container``."""
    res = run_in_container(host, cmd)
    return {
        "success": res.rc == 0,
        "rc": res.rc,
        "stdout": res.stdout or "",
        "stderr": res.stderr or "",
    }


def read_file_in_omnia_core(host, path: str) -> Dict[str, Any]:
    """Read a file inside the omnia_core container."""
    cmd = run_in_omnia_core(host, f"cat '{path}'")
    if cmd["success"]:
        return {"success": True, "content": cmd["stdout"] or "", "error": None}
    err = (cmd["stderr"] or cmd["stdout"] or "").strip()
    return {"success": False, "content": "", "error": err}


def _strip_version_suffix(package_name: str) -> str:
    """Strip trailing version suffix from a package name.

    Examples:
        kubeadm-1.34.1  -> kubeadm
        cri-o-1.34.1    -> cri-o
        python3.12      -> python3.12  (no dash-version, unchanged)
        vim             -> vim         (no change)
    """
    stripped = re.sub(r'-\d[\d.]*$', '', package_name)
    return stripped if stripped else package_name


def _parse_json_output(cmd_result: Dict[str, Any]) -> Dict[str, Any]:
    """Parse JSON from a command result's stdout."""
    if not cmd_result["success"]:
        return {
            "success": False, "data": None,
            "error": (cmd_result.get("stderr") or cmd_result.get("stdout") or "").strip(),
        }
    stdout = (cmd_result.get("stdout") or "").strip()
    if not stdout:
        return {"success": True, "data": None, "error": None}
    try:
        return {"success": True, "data": json.loads(stdout), "error": None}
    except json.JSONDecodeError as exc:
        return {"success": False, "data": None, "error": f"Invalid JSON: {exc}"}


# =============================================================================
# 1. CONTAINER CHECK
# =============================================================================

def check_container_running(host, container_name: str) -> Dict[str, Any]:
    """Check if a container is running. Delegates to core."""
    return _core_check_container(host, container_name)


# =============================================================================
# 2. PULP CLI CHECK
# =============================================================================

def check_pulp_cli_repository_list(host) -> Dict[str, Any]:
    """Verify the pulp CLI works by running ``pulp rpm repository list``.

    Parses the JSON output and returns a clean summary with repo names
    instead of dumping the raw JSON.
    """
    cmd = run_in_omnia_core(host, "pulp rpm repository list 2>/dev/null")
    parsed = _parse_json_output(cmd)

    if not parsed["success"]:
        return {
            "success": False, "details": None,
            "error": f"pulp CLI failed: {parsed.get('error', '')}",
        }

    repos = parsed["data"]
    if repos is None:
        repos = []

    repo_names = [r.get("name", "unknown") for r in repos]
    details = f"Pulp CLI is working — {len(repos)} RPM repositories found\n"
    if repo_names:
        details += "\n".join([f"  - {name}" for name in sorted(repo_names)])

    return {
        "success": True,
        "repo_count": len(repos),
        "repo_names": repo_names,
        "details": details,
        "error": None,
    }


# =============================================================================
# 3. PULP API STATUS
# =============================================================================

def check_pulp_api_status(host) -> Dict[str, Any]:
    """
    Verify Pulp API status is healthy.

    Checks: database connection, online workers, content apps,
    content_settings (origin URL), and storage info.
    """
    cmd = run_in_omnia_core(host, "pulp status 2>/dev/null")
    parsed = _parse_json_output(cmd)
    if not parsed["success"] or parsed["data"] is None:
        return {
            "success": False, "details": "",
            "error": parsed.get("error") or "Empty response from pulp status",
        }

    status = parsed["data"]
    db_connected = status.get("database_connection", {}).get("connected", False)
    worker_count = len(status.get("online_workers", []))
    content_app_count = len(status.get("online_content_apps", []))

    content_settings = status.get("content_settings", {})
    content_origin = content_settings.get("content_origin", "unknown")

    storage = status.get("storage", {})
    storage_total_gb = round(storage.get("total", 0) / (1024 ** 3), 1)
    storage_free_gb = round(storage.get("free", 0) / (1024 ** 3), 1)

    details = (
        f"Database: {'connected' if db_connected else 'DISCONNECTED'}\n"
        f"Online workers: {worker_count}\n"
        f"Content apps: {content_app_count}\n"
        f"Content origin: {content_origin}\n"
        f"Storage: {storage_free_gb} GB free / {storage_total_gb} GB total"
    )

    success = db_connected and worker_count > 0
    return {
        "success": success,
        "database_connected": db_connected,
        "online_workers": worker_count,
        "content_apps": content_app_count,
        "content_origin": content_origin,
        "details": details,
        "error": None if success else "Pulp services not fully healthy",
    }


# =============================================================================
# 4. SOFTWARE DOWNLOAD STATUS (software.csv)
# =============================================================================

def _find_software_csv_paths(host) -> Dict[str, str]:
    """
    Find all software.csv files under LOG_BASE_PATH.

    Path structure: /opt/omnia/log/local_repo/<os_type>/<os_version>/<arch>/software.csv

    Returns dict mapping arch -> full path to software.csv
    """
    arch_paths = {}

    # Find all software.csv files recursively
    find_cmd = run_in_omnia_core(
        host,
        f"find {LOG_BASE_PATH} -name '{SOFTWARE_CSV_FILENAME}' -type f 2>/dev/null"
    )

    if not find_cmd["success"] or not find_cmd["stdout"].strip():
        return arch_paths

    for path in find_cmd["stdout"].strip().splitlines():
        path = path.strip()
        if not path:
            continue
        # Extract arch from path (e.g., .../x86_64/software.csv)
        for arch in ARCH_LIST:
            if f"/{arch}/" in path:
                arch_paths[arch] = path
                break

    return arch_paths


def check_software_download_status(host) -> Dict[str, Any]:
    """
    Parse ``software.csv`` from each architecture under LOG_BASE_PATH.

    Path structure: /opt/omnia/log/local_repo/<os_type>/<os_version>/<arch>/software.csv

    For each architecture:
    - x86_64: Show all software with pass/fail status
    - aarch64: If no software.csv found, show "skipped - no software found"

    Returns success/failure counts and lists of failed softwares.
    """
    arch_csv_paths = _find_software_csv_paths(host)

    arch_results = {}  # arch -> {entries: [], failures: [], skipped: bool}

    for arch in ARCH_LIST:
        if arch not in arch_csv_paths:
            arch_results[arch] = {
                "entries": [],
                "failures": [],
                "skipped": True,
                "reason": f"No software.csv found for {arch}",
            }
            continue

        csv_path = arch_csv_paths[arch]
        result = read_file_in_omnia_core(host, csv_path)

        if not result["success"]:
            arch_results[arch] = {
                "entries": [],
                "failures": [],
                "skipped": True,
                "reason": f"Could not read {csv_path}: {result.get('error', '')}",
            }
            continue

        content = result["content"].strip()
        if not content:
            arch_results[arch] = {
                "entries": [],
                "failures": [],
                "skipped": True,
                "reason": f"software.csv is empty for {arch}",
            }
            continue

        entries = []
        failures = []
        reader = csv.DictReader(io.StringIO(content))
        for row in reader:
            name = row.get("name", "unknown")
            status_val = (row.get("status") or "").strip().lower()
            entry = {"name": name, "status": status_val, "arch": arch}
            entries.append(entry)
            if status_val != "success":
                failures.append(entry)

        arch_results[arch] = {
            "entries": entries,
            "failures": failures,
            "skipped": False,
            "reason": None,
        }

    # Build output details per architecture
    details = ""
    all_failures = []
    total_entries = 0
    has_any_data = False

    for arch in ARCH_LIST:
        ar = arch_results[arch]

        if ar["skipped"]:
            details += f"\n{arch}:\n"
            details += f"  ⊘ SKIPPED - {ar['reason']}\n"
            continue

        has_any_data = True
        entries = ar["entries"]
        failures = ar["failures"]
        total_entries += len(entries)
        all_failures.extend(failures)

        passed = [e for e in entries if e not in failures]

        details += f"\n{arch}: {len(passed)}/{len(entries)} passed\n"

        for entry in sorted(passed, key=lambda x: x["name"]):
            details += f"  ✓ {entry['name']}: PASS\n"

        for entry in sorted(failures, key=lambda x: x["name"]):
            details += f"  ✘ {entry['name']}: FAIL ({entry['status']})\n"

    if not has_any_data:
        return {
            "success": False,
            "total": 0,
            "failed": 0,
            "failures": [],
            "details": f"No software.csv found for any architecture under {LOG_BASE_PATH}/",
            "error": f"software.csv not found under {LOG_BASE_PATH}/<os>/<version>/<arch>/",
        }

    failed_count = len(all_failures)

    return {
        "success": failed_count == 0,
        "total": total_entries,
        "failed": failed_count,
        "failures": all_failures,
        "details": details.strip(),
        "error": None if failed_count == 0 else f"{failed_count} software(s) failed",
    }


# =============================================================================
# 5. PER-SOFTWARE PACKAGE STATUS (status.csv per software)
# =============================================================================

def _find_status_csv_files(host) -> List[Dict[str, str]]:
    """
    Find all status.csv files under LOG_BASE_PATH.

    Path structure: /opt/omnia/log/local_repo/<os>/<version>/<arch>/<software>/status.csv

    Returns list of dicts with arch, software, path
    """
    results = []

    # Find all status.csv files recursively
    find_cmd = run_in_omnia_core(
        host,
        f"find {LOG_BASE_PATH} -name '{STATUS_CSV_FILENAME}' -type f 2>/dev/null"
    )

    if not find_cmd["success"] or not find_cmd["stdout"].strip():
        return results

    for path in find_cmd["stdout"].strip().splitlines():
        path = path.strip()
        if not path:
            continue

        # Extract arch and software from path
        # e.g., /opt/omnia/log/local_repo/rhel/10.0/x86_64/openldap/status.csv
        for arch in ARCH_LIST:
            if f"/{arch}/" in path:
                # Get software name (directory containing status.csv)
                parts = path.split(f"/{arch}/")
                if len(parts) > 1:
                    sw_part = parts[1].replace(f"/{STATUS_CSV_FILENAME}", "")
                    sw_name = sw_part.split("/")[0] if "/" in sw_part else sw_part
                    results.append({
                        "arch": arch,
                        "software": sw_name,
                        "path": path,
                    })
                break

    return results


def check_per_software_package_status(host) -> Dict[str, Any]:
    """
    Parse each ``<software>/status.csv`` under LOG_BASE_PATH.

    Path structure: /opt/omnia/log/local_repo/<os>/<version>/<arch>/<software>/status.csv

    Shows individual package pass/fail for each architecture and software.
    """
    status_files = _find_status_csv_files(host)

    arch_results = {}  # arch -> {softwares: {sw_name: {packages: [], failures: []}}}

    for arch in ARCH_LIST:
        arch_results[arch] = {"softwares": {}, "skipped": True}

    for sf in status_files:
        arch = sf["arch"]
        sw_name = sf["software"]
        csv_path = sf["path"]

        result = read_file_in_omnia_core(host, csv_path)
        if not result["success"]:
            continue

        content = result["content"].strip()
        if not content:
            continue

        arch_results[arch]["skipped"] = False

        if sw_name not in arch_results[arch]["softwares"]:
            arch_results[arch]["softwares"][sw_name] = {"packages": [], "failures": []}

        reader = csv.DictReader(io.StringIO(content))
        for row in reader:
            pkg_name = row.get("name", "unknown")
            pkg_status = (row.get("status") or "").strip().lower()
            pkg_type = row.get("type", "")
            repo_name = row.get("repo_name", "")

            entry = {
                "name": pkg_name,
                "type": pkg_type,
                "repo_name": repo_name,
                "status": pkg_status,
                "software": sw_name,
                "arch": arch,
            }

            arch_results[arch]["softwares"][sw_name]["packages"].append(entry)
            if pkg_status not in ("success", ""):
                arch_results[arch]["softwares"][sw_name]["failures"].append(entry)

    # Build output details per architecture
    details = ""
    all_failures = []
    total_packages = 0
    has_any_data = False

    for arch in ARCH_LIST:
        ar = arch_results[arch]

        if ar["skipped"] or not ar["softwares"]:
            details += f"\n{arch}:\n"
            details += f"  ⊘ SKIPPED - No status.csv found for {arch}\n"
            continue

        has_any_data = True
        arch_total = 0
        arch_failed = 0

        for sw_name, sw_data in sorted(ar["softwares"].items()):
            packages = sw_data["packages"]
            failures = sw_data["failures"]
            arch_total += len(packages)
            arch_failed += len(failures)
            total_packages += len(packages)
            all_failures.extend(failures)

        details += f"\n{arch}: {arch_total - arch_failed}/{arch_total} packages passed\n"

        for sw_name, sw_data in sorted(ar["softwares"].items()):
            packages = sw_data["packages"]
            failures = sw_data["failures"]
            passed = [p for p in packages if p not in failures]

            details += f"  [{sw_name}] {len(passed)}/{len(packages)} passed:\n"

            for pkg in sorted(passed, key=lambda x: x["name"]):
                details += f"    ✓ {pkg['name']}: PASS\n"

            for pkg in sorted(failures, key=lambda x: x["name"]):
                details += f"    ✘ {pkg['name']}: FAIL ({pkg['status']})\n"

    if not has_any_data:
        return {
            "success": True,  # No data means nothing to fail
            "total": 0,
            "failed": 0,
            "failures": [],
            "details": f"No status.csv found for any software under {LOG_BASE_PATH}/",
            "error": None,
        }

    failed_count = len(all_failures)

    return {
        "success": failed_count == 0,
        "total": total_packages,
        "failed": failed_count,
        "failures": all_failures,
        "details": details.strip(),
        "error": None if failed_count == 0 else f"{failed_count} package(s) failed",
    }


# =============================================================================
# 6. RPM REPOSITORIES SYNCED
# =============================================================================

def check_pulp_repositories_synced(host) -> Dict[str, Any]:
    """Verify all Pulp RPM repositories have been synced (latest_version_href set)."""
    cmd = run_in_omnia_core(host, "pulp rpm repository list 2>/dev/null")
    parsed = _parse_json_output(cmd)

    if not parsed["success"]:
        return {
            "success": False, "details": "",
            "error": f"pulp rpm repository list failed: {parsed.get('error', '')}",
        }

    repos = parsed["data"]
    if not repos:
        return {
            "success": True, "total_repos": 0, "synced_repos": 0,
            "details": "No RPM repositories found", "error": None,
        }

    synced = []
    not_synced = []
    for repo in repos:
        name = repo.get("name", "unknown")
        if repo.get("latest_version_href"):
            synced.append(name)
        else:
            not_synced.append(name)

    details = (
        f"RPM repositories: {len(synced)}/{len(repos)} synced\n"
    )
    for name in sorted(synced):
        details += f"  ✓ {name}\n"
    if not_synced:
        for name in sorted(not_synced):
            details += f"  ✘ {name} (not synced)\n"

    return {
        "success": len(not_synced) == 0,
        "total_repos": len(repos),
        "synced_repos": len(synced),
        "not_synced_repos": len(not_synced),
        "not_synced_list": not_synced,
        "details": details,
        "error": None if not not_synced else f"{len(not_synced)} repos not synced",
    }


# =============================================================================
# 7. RPM DISTRIBUTIONS PUBLISHED
# =============================================================================

def check_pulp_distributions_published(host) -> Dict[str, Any]:
    """Verify all RPM distributions have a publication or repository attached."""
    cmd = run_in_omnia_core(host, "pulp rpm distribution list 2>/dev/null")
    parsed = _parse_json_output(cmd)

    if not parsed["success"]:
        return {
            "success": False, "details": "",
            "error": f"pulp rpm distribution list failed: {parsed.get('error', '')}",
        }

    dists = parsed["data"]
    if not dists:
        return {
            "success": True, "total_distributions": 0,
            "details": "No RPM distributions found", "error": None,
        }

    published = []
    unpublished = []
    for dist in dists:
        name = dist.get("name", "unknown")
        base_path = dist.get("base_path", "")
        if dist.get("publication") or dist.get("repository"):
            published.append({"name": name, "base_path": base_path})
        else:
            unpublished.append({"name": name, "base_path": base_path})

    details = (
        f"RPM distributions: {len(published)}/{len(dists)} published\n"
    )
    for d in sorted(published, key=lambda x: x["name"]):
        details += f"  ✓ {d['name']} → /{d['base_path']}\n"
    if unpublished:
        for d in sorted(unpublished, key=lambda x: x["name"]):
            details += f"  ✘ {d['name']} → /{d['base_path']} (unpublished)\n"

    return {
        "success": len(unpublished) == 0,
        "total_distributions": len(dists),
        "published_count": len(published),
        "unpublished_count": len(unpublished),
        "details": details,
        "error": None if not unpublished else f"{len(unpublished)} distributions not published",
    }


# =============================================================================
# 8. CONTAINER REPOS SYNCED
# =============================================================================

def check_container_repos_synced(host) -> Dict[str, Any]:
    """Verify all Pulp container repositories have been synced."""
    cmd = run_in_omnia_core(host, "pulp container repository list 2>/dev/null")
    parsed = _parse_json_output(cmd)

    if not parsed["success"]:
        return {
            "success": False, "details": "",
            "error": f"pulp container repository list failed: {parsed.get('error', '')}",
        }

    repos = parsed["data"]
    if not repos:
        return {
            "success": True, "total_repos": 0,
            "details": "No container repositories found", "error": None,
        }

    synced = []
    not_synced = []
    for repo in repos:
        name = repo.get("name", "unknown")
        if repo.get("latest_version_href"):
            synced.append(name)
        else:
            not_synced.append(name)

    details = (
        f"Container repositories: {len(synced)}/{len(repos)} synced\n"
    )
    for name in sorted(synced):
        details += f"  ✓ {name}\n"
    if not_synced:
        for name in sorted(not_synced):
            details += f"  ✘ {name} (not synced)\n"

    return {
        "success": len(not_synced) == 0,
        "total_repos": len(repos),
        "synced_repos": len(synced),
        "not_synced_repos": len(not_synced),
        "not_synced_list": not_synced,
        "details": details,
        "error": None if not not_synced else f"{len(not_synced)} container repos not synced",
    }


# =============================================================================
# 9. FILE REPOS SYNCED
# =============================================================================

def check_file_repos_synced(host) -> Dict[str, Any]:
    """Verify all Pulp file repositories have been synced."""
    cmd = run_in_omnia_core(host, "pulp file repository list 2>/dev/null")
    parsed = _parse_json_output(cmd)

    if not parsed["success"]:
        return {
            "success": False, "details": "",
            "error": f"pulp file repository list failed: {parsed.get('error', '')}",
        }

    repos = parsed["data"]
    if not repos:
        return {
            "success": True, "total_repos": 0,
            "details": "No file repositories found", "error": None,
        }

    synced = []
    not_synced = []
    for repo in repos:
        name = repo.get("name", "unknown")
        if repo.get("latest_version_href"):
            synced.append(name)
        else:
            not_synced.append(name)

    details = (
        f"File repositories: {len(synced)}/{len(repos)} synced\n"
    )
    for name in sorted(synced):
        details += f"  ✓ {name}\n"
    if not_synced:
        for name in sorted(not_synced):
            details += f"  ✘ {name} (not synced)\n"

    return {
        "success": len(not_synced) == 0,
        "total_repos": len(repos),
        "synced_repos": len(synced),
        "not_synced_repos": len(not_synced),
        "not_synced_list": not_synced,
        "details": details,
        "error": None if not not_synced else f"{len(not_synced)} file repos not synced",
    }


# =============================================================================
# 10. RPM CONTENT ACCESSIBLE (ALL distributions)
# =============================================================================

def check_pulp_content_accessible(host) -> Dict[str, Any]:
    """
    Verify Pulp RPM content is accessible for ALL distributions.

    Iterates over every RPM distribution and checks that
    ``repomd.xml`` is reachable via HTTPS.
    """
    cmd = run_in_omnia_core(host, "pulp rpm distribution list 2>/dev/null")
    parsed = _parse_json_output(cmd)

    if not parsed["success"]:
        return {
            "success": False, "details": "",
            "error": f"Failed to list distributions: {parsed.get('error', '')}",
        }

    dists = parsed["data"]
    if not dists:
        return {
            "success": True,
            "details": "No RPM distributions to check",
            "error": None,
        }

    accessible = []
    not_accessible = []

    for dist in dists:
        name = dist.get("name", "unknown")
        base_path = dist.get("base_path", "")
        if not base_path:
            not_accessible.append({"name": name, "http_code": "no_base_path"})
            continue

        curl_cmd = (
            f"curl -sk {PULP_CONTENT_SCHEME}://localhost:{PULP_CONTENT_PORT}"
            f"{PULP_CONTENT_PATH_PREFIX}{base_path}/repodata/repomd.xml "
            f"-o /dev/null -w '%{{http_code}}' "
            f"--connect-timeout {CURL_CONNECT_TIMEOUT} 2>/dev/null"
        )
        curl_result = run_in_omnia_core(host, curl_cmd)
        http_code = (curl_result.get("stdout") or "").strip()

        if http_code == "200":
            accessible.append({"name": name, "http_code": http_code})
        else:
            not_accessible.append({"name": name, "http_code": http_code})

    details = (
        f"Content accessibility: {len(accessible)}/{len(dists)} reachable\n"
    )
    for d in sorted(accessible, key=lambda x: x["name"]):
        details += f"  ✓ {d['name']} → HTTP {d['http_code']}\n"
    if not_accessible:
        for d in sorted(not_accessible, key=lambda x: x["name"]):
            details += f"  ✘ {d['name']} → HTTP {d['http_code']}\n"

    return {
        "success": len(not_accessible) == 0,
        "total_checked": len(dists),
        "accessible": len(accessible),
        "not_accessible_count": len(not_accessible),
        "not_accessible_list": not_accessible,
        "details": details,
        "error": (
            None if not not_accessible
            else f"{len(not_accessible)} distribution(s) not accessible"
        ),
    }


# =============================================================================
# 11. SOFTWARE PACKAGES IN PULP
# =============================================================================

def load_software_config(host) -> Dict[str, Any]:
    """Load software_config.json from the omnia_core container."""
    config = load_input_file(host, SOFTWARE_CONFIG_FILE)
    if not config:
        return {
            "success": False, "config": {},
            "error": f"Failed to read {SOFTWARE_CONFIG_FILE} from container",
        }
    return {"success": True, "config": config, "error": None}


def _build_config_path(os_type: str, os_version: str, arch: str, sw_name: str) -> str:
    """Build path to a software's package config JSON inside the container."""
    return f"{INPUT_BASE_PATH}/config/{arch}/{os_type}/{os_version}/{sw_name}.json"


def _load_package_config(host, os_type: str, os_version: str,
                         arch: str, sw_name: str) -> Dict[str, Any]:
    """Load a specific package config JSON from the container."""
    path = _build_config_path(os_type, os_version, arch, sw_name)
    config = load_container_file(host, path)
    if not config:
        return {"success": False, "config": {}, "path": path, "error": f"Failed to read {path}"}
    return {"success": True, "config": config, "path": path, "error": None}


def _extract_packages(config: Dict[str, Any]) -> List[Dict[str, str]]:
    """Extract package entries from a config JSON's ``cluster`` lists."""
    packages = []
    for key, value in config.items():
        if not isinstance(value, dict):
            continue
        for pkg in value.get("cluster", []):
            if isinstance(pkg, dict) and "package" in pkg:
                packages.append({
                    "package": pkg.get("package", ""),
                    "type": pkg.get("type", "rpm"),
                    "repo_name": pkg.get("repo_name", ""),
                    "component": key,
                })
    return packages


def check_software_packages_in_pulp(host) -> Dict[str, Any]:
    """
    Full verification: parse software_config.json, load per-software config
    JSONs, and verify all RPM packages exist in Pulp.
    """
    sw_result = load_software_config(host)
    if not sw_result["success"]:
        return {"success": False, "details": "", "error": sw_result["error"]}

    sw_config = sw_result["config"]
    os_type = sw_config.get("cluster_os_type", "rhel")
    os_version = sw_config.get("cluster_os_version", "10.0")
    softwares = sw_config.get("softwares", [])

    if not softwares:
        return {"success": False, "details": "", "error": "No softwares in software_config.json"}

    all_packages: List[Dict[str, str]] = []
    loaded_configs: List[str] = []
    errors: List[str] = []

    for sw in softwares:
        if not isinstance(sw, dict):
            continue
        name = sw.get("name", "")
        archs = sw.get("arch", [])
        if not name or not archs:
            continue

        for arch in archs:
            pkg_result = _load_package_config(host, os_type, os_version, arch, name)
            if not pkg_result["success"]:
                errors.append(f"{name}/{arch}: {pkg_result['error']}")
                continue

            loaded_configs.append(f"{arch}/{os_type}/{os_version}/{name}.json")
            for pkg in _extract_packages(pkg_result["config"]):
                pkg["arch"] = arch
                pkg["software"] = name
                all_packages.append(pkg)

    rpm_packages = [p for p in all_packages if p.get("type") == "rpm"]

    # Deduplicate
    unique: Dict[str, Dict[str, str]] = {}
    for pkg in rpm_packages:
        pname = pkg.get("package", "")
        if pname and pname not in unique:
            unique[pname] = pkg

    # Verify each unique RPM in Pulp
    # Some config entries embed version in the name (e.g. kubeadm-1.34.1).
    # Pulp stores the RPM name without version (e.g. kubeadm).
    # Search order: exact → stripped base name → prefix match.
    found_packages: List[Dict[str, str]] = []
    missing_packages: List[Dict[str, str]] = []
    for pname, pkg_info in unique.items():
        pkg_entry = {
            "package": pname,
            "repo_name": pkg_info.get("repo_name", ""),
            "software": pkg_info.get("software", ""),
        }

        # 1) Exact name search
        pulp_cmd = f"pulp rpm content list --name {pname} --limit 1 2>/dev/null"
        res = run_in_omnia_core(host, pulp_cmd)
        stdout = (res.get("stdout") or "").strip()
        if res["success"] and stdout and stdout != "[]":
            found_packages.append(pkg_entry)
            continue

        # 2) Fallback: strip version suffix and try base name
        base_name = _strip_version_suffix(pname)
        if base_name != pname:
            pulp_cmd2 = (
                f"pulp rpm content list --name {base_name} --limit 1 2>/dev/null"
            )
            res2 = run_in_omnia_core(host, pulp_cmd2)
            stdout2 = (res2.get("stdout") or "").strip()
            if res2["success"] and stdout2 and stdout2 != "[]":
                found_packages.append(pkg_entry)
                continue

        # 3) Fallback: prefix match (e.g. vim → vim-enhanced)
        prefix_cmd = (
            f"pulp rpm content list --name-startswith {pname} --limit 1 2>/dev/null"
        )
        res3 = run_in_omnia_core(host, prefix_cmd)
        stdout3 = (res3.get("stdout") or "").strip()
        if res3["success"] and stdout3 and stdout3 != "[]":
            found_packages.append(pkg_entry)
            continue

        missing_packages.append(pkg_entry)

    total = len(unique)
    found_count = len(found_packages)
    missing_count = len(missing_packages)
    full_details = (
        f"RPM packages in Pulp: {found_count}/{total} found "
        f"({os_type} {os_version}, {len(loaded_configs)} configs)\n"
    )
    for p in sorted(found_packages, key=lambda x: x["package"]):
        full_details += f"  ✓ {p['package']} (sw: {p['software']})\n"
    if missing_packages:
        for p in sorted(missing_packages, key=lambda x: x["package"]):
            full_details += (
                f"  ✘ {p['package']} (repo: {p['repo_name']}, "
                f"sw: {p['software']})\n"
            )
    if errors:
        full_details += "\nConfig load errors:\n"
        for e in errors[:10]:
            full_details += f"  ⚠ {e}\n"

    return {
        "success": missing_count == 0,
        "total_packages": total,
        "found_packages": found_count,
        "missing_packages": missing_count,
        "missing_list": missing_packages,
        "details": full_details,
        "error": None if missing_count == 0 else f"{missing_count} packages not found in Pulp",
    }
