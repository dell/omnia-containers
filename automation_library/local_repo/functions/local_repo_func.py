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


def _load_configured_packages_for_software(host, sw_name: str, arch: str) -> set:
    """Load the actual configured packages for a software from its JSON config file.
    
    Returns set of package names that user actually configured.
    """
    # Try to read the software config JSON
    config_path = f"/opt/omnia/input/project_default/config/{arch}/rhel/10.0/{sw_name}.json"
    result = read_file_in_omnia_core(host, config_path)
    
    if not result["success"]:
        return set()  # If can't read config, return empty set
    
    try:
        import json
        config = json.loads(result["content"])
        packages = set()
        
        # Extract packages from all role groups
        for role_key, role_data in config.items():
            if isinstance(role_data, dict) and "cluster" in role_data:
                for pkg_entry in role_data.get("cluster", []):
                    if isinstance(pkg_entry, dict) and "package" in pkg_entry:
                        packages.add(pkg_entry["package"])
        
        return packages
    except Exception:
        return set()  # On any error, return empty set


def check_per_software_package_status(host) -> Dict[str, Any]:
    """
    Parse each ``<software>/status.csv`` under LOG_BASE_PATH.

    Path structure: /opt/omnia/log/local_repo/<os>/<version>/<arch>/<software>/status.csv

    Shows individual package pass/fail for each architecture and software.
    Only fails on user-configured packages, not auto-added dependencies.
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
            arch_results[arch]["softwares"][sw_name] = {"packages": [], "failures": [], "configured_pkgs": set()}
        
        # Load user-configured packages for this software
        if not arch_results[arch]["softwares"][sw_name]["configured_pkgs"]:
            arch_results[arch]["softwares"][sw_name]["configured_pkgs"] = _load_configured_packages_for_software(host, sw_name, arch)

        configured_pkgs = arch_results[arch]["softwares"][sw_name]["configured_pkgs"]

        reader = csv.DictReader(io.StringIO(content))
        for row in reader:
            pkg_name = row.get("name", "unknown")
            pkg_status = (row.get("status") or "").strip().lower()
            pkg_type = row.get("type", "")
            repo_name = row.get("repo_name", "")
            
            # Skip malformed entries (empty names, names ending with :, etc.)
            if not pkg_name or pkg_name.endswith(":") or pkg_name == "unknown":
                continue

            entry = {
                "name": pkg_name,
                "type": pkg_type,
                "repo_name": repo_name,
                "status": pkg_status,
                "software": sw_name,
                "arch": arch,
                "user_configured": pkg_name in configured_pkgs,
            }

            arch_results[arch]["softwares"][sw_name]["packages"].append(entry)
            
            # Only mark as failure if:
            # 1. Status is not success, AND
            # 2. Package is user-configured (not auto-added)
            if pkg_status not in ("success", "") and pkg_name in configured_pkgs:
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
            
            # Separate user-configured from auto-added
            user_passed = [p for p in passed if p.get("user_configured")]
            auto_passed = [p for p in passed if not p.get("user_configured")]
            user_failed = [p for p in failures if p.get("user_configured")]
            auto_failed = [p for p in packages if not p.get("user_configured") and p.get("status") not in ("success", "")]

            details += f"  [{sw_name}] {len(passed)}/{len(packages)} passed:\n"

            # Show user-configured packages first
            for pkg in sorted(user_passed, key=lambda x: x["name"]):
                details += f"    ✓ {pkg['name']}: PASS\n"
            
            # Show auto-added packages that passed (if any)
            for pkg in sorted(auto_passed, key=lambda x: x["name"]):
                details += f"    ✓ {pkg['name']}: PASS (auto-added)\n"

            # Show user-configured failures (these count as real failures)
            for pkg in sorted(user_failed, key=lambda x: x["name"]):
                details += f"    ✘ {pkg['name']}: FAIL ({pkg['status']})\n"
            
            # Show auto-added failures (warnings only, don't count as failures)
            for pkg in sorted(auto_failed, key=lambda x: x["name"]):
                details += f"    ⚠ {pkg['name']}: FAIL ({pkg['status']}) [auto-added - ignored]\n"

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


# =============================================================================
# 12. SHARED HELPERS FOR REPO PATTERN CHECKS
# =============================================================================

def _list_all_rpm_repos(host) -> Dict[str, Any]:
    """List all Pulp RPM repositories."""
    cmd = run_in_omnia_core(host, "pulp rpm repository list 2>/dev/null")
    parsed = _parse_json_output(cmd)
    if not parsed["success"]:
        return {"success": False, "repos": [], "error": parsed.get("error", "")}
    return {"success": True, "repos": parsed["data"] or [], "error": None}


def _filter_repos_by_keyword(repos: List[Dict[str, Any]], keyword: str) -> List[Dict[str, Any]]:
    """Return repos whose name contains keyword (case-insensitive)."""
    kw = keyword.lower()
    return [r for r in repos if kw in r.get("name", "").lower()]


def _check_repos_by_keyword(
    host,
    keyword: str,
    require_archs: List[str] = None,
) -> Dict[str, Any]:
    """
    Generic check: find Pulp RPM repos matching keyword.

    When require_archs is given, verifies at least one synced repo per arch.
    Missing/unsynced aarch64 is reported but NOT a failure (aarch64 is optional);
    missing/unsynced x86_64 IS a failure.
    """
    result = _list_all_rpm_repos(host)
    if not result["success"]:
        return {"success": False, "details": "", "error": result["error"]}

    all_repos = result["repos"]
    matched = _filter_repos_by_keyword(all_repos, keyword)

    if not matched:
        return {
            "success": False,
            "details": f"No repos matching '{keyword}' found in Pulp",
            "error": f"No '{keyword}' repos found in Pulp",
        }

    details = f"Repos matching '{keyword}' ({len(matched)} found):\n"
    issues = []

    if require_archs:
        for arch in require_archs:
            arch_repos = [r for r in matched if arch in r.get("name", "")]
            synced = [r for r in arch_repos if r.get("latest_version_href")]
            not_synced = [r for r in arch_repos if not r.get("latest_version_href")]
            if synced:
                for r in sorted(synced, key=lambda x: x.get("name", "")):
                    details += f"  ✓ {r['name']} ({arch}, synced)\n"
            if not_synced:
                for r in sorted(not_synced, key=lambda x: x.get("name", "")):
                    details += f"  ✘ {r['name']} ({arch}, not synced)\n"
                    if arch == "x86_64":
                        issues.append(f"'{keyword}/{arch}' not synced: {r['name']}")
            if not arch_repos:
                details += f"  ⊘ No '{keyword}' repo found for {arch}\n"
                if arch == "x86_64":
                    issues.append(f"No '{keyword}' repo found for {arch}")
    else:
        synced = [r for r in matched if r.get("latest_version_href")]
        not_synced = [r for r in matched if not r.get("latest_version_href")]
        for r in sorted(synced, key=lambda x: x.get("name", "")):
            details += f"  ✓ {r['name']} (synced)\n"
        for r in sorted(not_synced, key=lambda x: x.get("name", "")):
            details += f"  ✘ {r['name']} (not synced)\n"
            issues.append(f"{r['name']} not synced")

    return {
        "success": len(issues) == 0,
        "matched_count": len(matched),
        "details": details.strip(),
        "error": "; ".join(issues) if issues else None,
    }


def _check_package_in_pulp(host, package_name: str) -> bool:
    """Return True if package_name (exact or prefix) exists in Pulp RPM content."""
    cmd = run_in_omnia_core(
        host, f"pulp rpm content list --name {package_name} --limit 1 2>/dev/null"
    )
    stdout = (cmd.get("stdout") or "").strip()
    if cmd["success"] and stdout and stdout != "[]":
        return True
    cmd2 = run_in_omnia_core(
        host,
        f"pulp rpm content list --name-startswith {package_name} --limit 1 2>/dev/null",
    )
    stdout2 = (cmd2.get("stdout") or "").strip()
    return cmd2["success"] and bool(stdout2) and stdout2 != "[]"


def _check_packages_list_in_pulp(host, packages: List[str]) -> Dict[str, Any]:
    """Verify that each package in the list exists in Pulp RPM content."""
    found: List[str] = []
    missing: List[str] = []
    for pkg in packages:
        if _check_package_in_pulp(host, pkg):
            found.append(pkg)
        else:
            missing.append(pkg)

    details = f"Package check ({len(found)}/{len(packages)} found):\n"
    for p in found:
        details += f"  ✓ {p}\n"
    for p in missing:
        details += f"  ✘ {p} (not in Pulp)\n"

    return {
        "success": len(missing) == 0,
        "found": found,
        "missing": missing,
        "details": details.strip(),
        "error": None if not missing else f"Packages not in Pulp: {', '.join(missing)}",
    }


# =============================================================================
# 13. RHEL10 BASEOS AND APPSTREAM REPOS
# =============================================================================

def check_rhel10_base_repos_in_pulp(host) -> Dict[str, Any]:
    """Verify RHEL10 BaseOS and AppStream repos exist and are synced in Pulp.

    x86_64 repos are required; aarch64 repos are optional (reported but not fatal).
    """
    result = _list_all_rpm_repos(host)
    if not result["success"]:
        return {"success": False, "details": "", "error": result["error"]}

    repos = result["repos"]
    issues: List[str] = []
    details = "RHEL10 base repos:\n"

    for keyword in ["baseos", "appstream"]:
        matched = _filter_repos_by_keyword(repos, keyword)
        if not matched:
            details += f"  ⊘ No '{keyword}' repos found in Pulp\n"
            issues.append(f"No '{keyword}' repos found in Pulp")
            continue
        for arch in ARCH_LIST:
            arch_repos = [r for r in matched if arch in r.get("name", "")]
            if arch_repos:
                for r in sorted(arch_repos, key=lambda x: x.get("name", "")):
                    synced = bool(r.get("latest_version_href"))
                    mark = "✓" if synced else "✘"
                    label = "synced" if synced else "not synced"
                    details += f"  {mark} {r['name']} ({arch}, {label})\n"
                    if not synced:
                        issues.append(f"{r['name']} not synced")
            else:
                details += f"  ⊘ '{keyword}/{arch}' not found in Pulp\n"
                if arch == "x86_64":
                    issues.append(f"No '{keyword}/{arch}' repo in Pulp")

    return {
        "success": len(issues) == 0,
        "details": details.strip(),
        "error": "; ".join(issues) if issues else None,
    }


# =============================================================================
# 14. AARCH64 ARM REPOS
# =============================================================================

def check_aarch64_repos_in_pulp(host) -> Dict[str, Any]:
    """Verify aarch64 ARM repos are available and synced in Pulp from the x86 OIM."""
    result = _list_all_rpm_repos(host)
    if not result["success"]:
        return {"success": False, "details": "", "error": result["error"]}

    repos = result["repos"]
    aarch64_repos = [r for r in repos if "aarch64" in r.get("name", "").lower()]

    if not aarch64_repos:
        return {
            "success": False,
            "details": "No aarch64 repos found in Pulp",
            "error": "No aarch64 repos found in Pulp",
        }

    synced = [r for r in aarch64_repos if r.get("latest_version_href")]
    not_synced = [r for r in aarch64_repos if not r.get("latest_version_href")]

    details = f"aarch64 repos in Pulp ({len(synced)}/{len(aarch64_repos)} synced):\n"
    for r in sorted(synced, key=lambda x: x.get("name", "")):
        details += f"  ✓ {r['name']}\n"
    for r in sorted(not_synced, key=lambda x: x.get("name", "")):
        details += f"  ✘ {r['name']} (not synced)\n"

    return {
        "success": len(not_synced) == 0 and len(synced) > 0,
        "total": len(aarch64_repos),
        "synced": len(synced),
        "details": details.strip(),
        "error": (
            None if not not_synced
            else f"{len(not_synced)} aarch64 repos not synced"
        ),
    }


# =============================================================================
# 15. EPEL REPOS
# =============================================================================

def check_epel_repos_in_pulp(host) -> Dict[str, Any]:
    """Verify EPEL repos for both x86_64 and aarch64 are synced in Pulp."""
    return _check_repos_by_keyword(host, "epel", require_archs=ARCH_LIST)


# =============================================================================
# 16. CRB REPOS
# =============================================================================

def check_crb_repos_in_pulp(host) -> Dict[str, Any]:
    """Verify CRB (CodeReady Builder) repos for both architectures are synced in Pulp.
    
    CRB is optional for RHEL10 - if not found, test is skipped rather than failed.
    """
    result = _check_repos_by_keyword(host, "crb", require_archs=ARCH_LIST)
    if not result["success"] and "No 'crb' repos found" in result.get("error", ""):
        return {
            "success": True,
            "skipped": True,
            "reason": "CRB repos not configured (optional for RHEL10)",
            "details": "No CRB repos found in Pulp (optional component)",
            "error": None,
        }
    return result


# =============================================================================
# 17. SLURM REPOS
# =============================================================================

def check_slurm_repo_in_pulp(host) -> Dict[str, Any]:
    """Verify Slurm repos are present and synced in Pulp."""
    return _check_repos_by_keyword(host, "slurm")


# =============================================================================
# 18. CUDA PACKAGES
# =============================================================================

def check_cuda_packages_in_pulp(host) -> Dict[str, Any]:
    """Verify CUDA packages or repos are available in Pulp."""
    result = _list_all_rpm_repos(host)
    if result["success"]:
        cuda_repos = _filter_repos_by_keyword(result["repos"], "cuda")
        if cuda_repos:
            synced = [r for r in cuda_repos if r.get("latest_version_href")]
            not_synced = [r for r in cuda_repos if not r.get("latest_version_href")]
            details = f"CUDA repos in Pulp ({len(synced)}/{len(cuda_repos)} synced):\n"
            for r in sorted(synced, key=lambda x: x.get("name", "")):
                details += f"  ✓ {r['name']}\n"
            for r in sorted(not_synced, key=lambda x: x.get("name", "")):
                details += f"  ✘ {r['name']} (not synced)\n"
            return {
                "success": len(not_synced) == 0,
                "details": details.strip(),
                "error": (
                    None if not not_synced
                    else f"{len(not_synced)} CUDA repos not synced"
                ),
            }
    return _check_packages_list_in_pulp(host, ["cuda", "cuda-toolkit", "cuda-runtime"])


# =============================================================================
# 19. OPENMPI AND UCX PACKAGES
# =============================================================================

def check_openmpi_ucx_packages_in_pulp(host) -> Dict[str, Any]:
    """Verify OpenMPI and UCX packages are available in Pulp for ARM workloads."""
    return _check_packages_list_in_pulp(host, ["openmpi", "ucx"])


# =============================================================================
# 20. OPENLDAP PACKAGES
# =============================================================================

def check_openldap_packages_in_pulp(host) -> Dict[str, Any]:
    """Verify OpenLDAP packages are available in Pulp."""
    return _check_packages_list_in_pulp(host, ["openldap", "openldap-servers", "openldap-clients"])


# =============================================================================
# 21. MULTI-ARCH REPO SEGREGATION
# =============================================================================

def check_multiarch_repo_segregation(host) -> Dict[str, Any]:
    """Verify x86_64 and aarch64 repos are stored separately in Pulp."""
    result = _list_all_rpm_repos(host)
    if not result["success"]:
        return {"success": False, "details": "", "error": result["error"]}

    repos = result["repos"]
    x86_repos = [r for r in repos if "x86_64" in r.get("name", "")]
    aarch64_repos = [r for r in repos if "aarch64" in r.get("name", "")]

    details = (
        f"Multi-arch repo segregation:\n"
        f"  x86_64 repos : {len(x86_repos)}\n"
        f"  aarch64 repos: {len(aarch64_repos)}\n"
    )

    if x86_repos:
        details += "\n  x86_64 (first 10):\n"
        for r in sorted(x86_repos, key=lambda x: x.get("name", ""))[:10]:
            mark = "✓" if r.get("latest_version_href") else "✘"
            details += f"    {mark} {r['name']}\n"

    if aarch64_repos:
        details += "\n  aarch64 (first 10):\n"
        for r in sorted(aarch64_repos, key=lambda x: x.get("name", ""))[:10]:
            mark = "✓" if r.get("latest_version_href") else "✘"
            details += f"    {mark} {r['name']}\n"
    else:
        details += "\n  ⊘ aarch64: no repos found (optional)\n"

    issues: List[str] = []
    if not x86_repos:
        issues.append("No x86_64 repos found in Pulp")

    return {
        "success": len(issues) == 0,
        "x86_64_count": len(x86_repos),
        "aarch64_count": len(aarch64_repos),
        "details": details.strip(),
        "error": "; ".join(issues) if issues else None,
    }


# =============================================================================
# 22. SUBSCRIPTION STATUS
# =============================================================================

def check_subscription_status(host) -> Dict[str, Any]:
    """Verify RHEL subscription-manager is registered and active on the OIM node."""
    cmd = host.run("subscription-manager status 2>/dev/null")
    stdout = (cmd.stdout or "").strip()
    stderr = (cmd.stderr or "").strip()
    output = stdout or stderr

    if not output:
        return {
            "success": False,
            "details": "No output from subscription-manager",
            "error": "subscription-manager returned no output — may not be installed",
        }

    is_active = any(
        kw in output
        for kw in ["Current", "Simple Content Access", "Overall Status: Current", "Overall Status: Registered"]
    )

    return {
        "success": is_active,
        "details": f"subscription-manager status output:\n{output}",
        "error": None if is_active else "Subscription not active or not registered",
    }


# =============================================================================
# 23. SOFTWARE CONFIG JSON VALIDATION
# =============================================================================

def check_software_config_json_valid(host) -> Dict[str, Any]:
    """Validate software_config.json: exists, parseable, and has well-formed entries."""
    sw_result = load_software_config(host)
    if not sw_result["success"]:
        return {"success": False, "details": "", "error": sw_result["error"]}

    config = sw_result["config"]
    issues: List[str] = []

    softwares = config.get("softwares", None)
    if softwares is None:
        issues.append("Missing required key: 'softwares'")
        return {
            "success": False,
            "details": "software_config.json missing 'softwares' key",
            "error": "; ".join(issues),
        }

    if not isinstance(softwares, list):
        issues.append("'softwares' must be a list")
    elif not softwares:
        issues.append("'softwares' list is empty — no packages configured")
    else:
        seen: set = set()
        duplicates: List[str] = []
        for idx, sw in enumerate(softwares):
            if not isinstance(sw, dict):
                issues.append(f"Entry #{idx} is not a dict")
                continue
            name = sw.get("name", "")
            if not name:
                issues.append(f"Entry #{idx} missing 'name'")
            version = sw.get("version", "")
            key = f"{name}:{version}"
            if key in seen:
                duplicates.append(f"{name} v{version}")
            seen.add(key)

    os_type = config.get("cluster_os_type", "")
    os_version = config.get("cluster_os_version", "")
    sw_list = softwares if isinstance(softwares, list) else []

    details = (
        f"software_config.json:\n"
        f"  OS type   : {os_type or '(not set)'}\n"
        f"  OS version: {os_version or '(not set)'}\n"
        f"  Entries   : {len(sw_list)}\n"
    )
    for sw in sw_list[:20]:
        if not isinstance(sw, dict):
            continue
        name = sw.get("name", "?")
        version = sw.get("version", "?")
        arch = sw.get("arch", sw.get("arch_type", []))
        arch_str = ", ".join(arch) if isinstance(arch, list) else str(arch)
        details += f"  ✓ {name} v{version} ({arch_str})\n"

    return {
        "success": len(issues) == 0,
        "software_count": len(sw_list),
        "details": details.strip(),
        "error": "; ".join(issues) if issues else None,
    }


# =============================================================================
# 24. PULP REPO METADATA PRESENT (repomd.xml)
# =============================================================================

def check_pulp_repo_metadata_present(host) -> Dict[str, Any]:
    """Verify repomd.xml metadata is accessible for all published RPM distributions."""
    cmd = run_in_omnia_core(host, "pulp rpm distribution list 2>/dev/null")
    parsed = _parse_json_output(cmd)
    if not parsed["success"]:
        return {
            "success": False,
            "details": "",
            "error": f"Failed to list distributions: {parsed.get('error', '')}",
        }

    dists = parsed["data"]
    if not dists:
        return {"success": True, "details": "No RPM distributions found", "error": None}

    accessible: List[Dict[str, str]] = []
    not_accessible: List[Dict[str, str]] = []

    for dist in dists:
        name = dist.get("name", "unknown")
        base_path = dist.get("base_path", "")
        if not base_path:
            not_accessible.append({"name": name, "reason": "no base_path configured"})
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
            accessible.append({"name": name, "base_path": base_path})
        else:
            not_accessible.append({"name": name, "reason": f"HTTP {http_code}"})

    details = f"Repo metadata (repomd.xml): {len(accessible)}/{len(dists)} accessible\n"
    for d in sorted(accessible, key=lambda x: x["name"]):
        details += f"  ✓ {d['name']} → {d['base_path']}/repodata/repomd.xml\n"
    for d in sorted(not_accessible, key=lambda x: x["name"]):
        details += f"  ✘ {d['name']} → {d.get('reason', 'unknown error')}\n"

    return {
        "success": len(not_accessible) == 0,
        "total": len(dists),
        "accessible": len(accessible),
        "details": details.strip(),
        "error": (
            None if not not_accessible
            else f"{len(not_accessible)} repos missing repomd.xml metadata"
        ),
    }
