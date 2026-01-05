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

"""Prepare Local Repo - Verification Functions."""

import csv
import io
import json
import re
from typing import Dict, Any, List

import yaml

from ..vars.local_repo_vars import LOCAL_REPO_VARS
from ..messages.local_repo_msgs import LOCAL_REPO_MSGS


def check_container_running(host, container_name: str) -> Dict[str, Any]:
    """Check if a container is running."""
    ps_fmt = f"podman ps --format '{{{{.Names}}}} {{{{.Status}}}}' | grep -E '^{container_name} '"
    cmd = host.run(ps_fmt)
    if cmd.rc == 0 and container_name in cmd.stdout:
        status = cmd.stdout.strip().replace(container_name, "").strip()
        msg = LOCAL_REPO_MSGS["container_running"].format(container=container_name)
        return {"success": True, "status": status, "details": msg, "error": None}

    ps_cmd = (f"podman ps -a --format '{{{{.Names}}}} {{{{.Status}}}}' "
               f"| grep -E '^{container_name} '")
    exists_cmd = host.run(ps_cmd)
    if exists_cmd.rc == 0:
        status = exists_cmd.stdout.strip().replace(container_name, "").strip()
        err_msg = LOCAL_REPO_MSGS["container_not_running"].format(container=container_name)
        return {
            "success": False, "status": status,
            "details": None, "error": f"{err_msg}: {status}"
        }

    return {
        "success": False, "status": "not_found",
        "details": None, "error": f"Container {container_name} does not exist"
    }


def run_in_omnia_core(host, cmd: str) -> Dict[str, Any]:
    """Run a command in omnia_core container using bash -lc."""
    container = LOCAL_REPO_VARS["omnia_core_container"]
    res = host.run(f"podman exec {container} bash -lc \"{cmd}\"")
    return {
        "success": res.rc == 0,
        "rc": res.rc,
        "stdout": res.stdout or "",
        "stderr": res.stderr or "",
    }


def run_in_pulp_container(host, cmd: str) -> Dict[str, Any]:
    """Run a command in pulp container using bash -c."""
    container = LOCAL_REPO_VARS["pulp_container"]
    res = host.run(f"podman exec {container} bash -c \"{cmd}\"")
    return {
        "success": res.rc == 0,
        "rc": res.rc,
        "stdout": res.stdout or "",
        "stderr": res.stderr or "",
    }


def check_pulp_cli_repository_list(host) -> Dict[str, Any]:
    """Verify pulp CLI works using pulp status command."""
    # Use pulp status to verify CLI is working
    cmd = run_in_omnia_core(host, "pulp status")
    if cmd["success"]:
        stdout = (cmd["stdout"] or "").strip()
        # Check if we got valid JSON response
        if stdout and stdout.startswith("{"):
            return {
                "success": True,
                "details": "pulp status command succeeded",
                "error": None,
            }
    return {
        "success": False,
        "details": None,
        "error": (cmd["stderr"] or cmd["stdout"] or "").strip(),
    }


def get_expected_status_csv_paths(host) -> Dict[str, Any]:
    """Build expected per-software status.csv paths inside omnia_core."""
    sw = load_software_config(host)
    if not sw.get("success"):
        return {"success": False, "paths": [], "error": sw.get("error") or ""}

    config = sw.get("config") or {}
    softwares = config.get("softwares") or []
    if not isinstance(softwares, list):
        return {"success": False, "paths": [], "error": "Invalid softwares list in software_config.json"}

    base = (LOCAL_REPO_VARS.get("status_search_roots") or ["/opt/omnia/log/local_repo"])[0]
    paths: List[Dict[str, str]] = []
    for s in softwares:
        if not isinstance(s, dict):
            continue
        name = (s.get("name") or "").strip()
        if not name:
            continue
        archs = s.get("arch") or []
        if isinstance(archs, str):
            archs = [archs]
        if not isinstance(archs, list):
            continue
        for arch in archs:
            if not isinstance(arch, str) or not arch.strip():
                continue
            status_path = f"{base}/{arch.strip()}/{name}/status.csv"
            paths.append({"arch": arch.strip(), "software": name, "path": status_path})

    if not paths:
        return {"success": False, "paths": [], "error": "No softwares/arch entries found in software_config.json"}
    return {"success": True, "paths": paths, "error": None}


def find_status_csv(host) -> Dict[str, Any]:
    """Locate a status.csv inside omnia_core.

    Backward-compatible helper retained for older callers.
    With the new layout, status files are expected at:
    /opt/omnia/log/local_repo/{arch}/{software_name}/status.csv

    Returns:
        {"success": bool, "path": str, "error": Optional[str]}
    """
    expected = get_expected_status_csv_paths(host)
    if not expected.get("success"):
        return {"success": False, "path": "", "error": expected.get("error") or ""}

    for item in expected.get("paths", []):
        p = (item.get("path") or "").strip()
        if not p:
            continue
        exists = run_in_omnia_core(host, f"test -f '{p}'")
        if exists.get("success"):
            return {"success": True, "path": p, "error": None}

    return {"success": False, "path": "", "error": LOCAL_REPO_MSGS["status_csv_missing"]}


def read_file_in_omnia_core(host, path: str) -> Dict[str, Any]:
    """Read a file in omnia_core container."""
    cmd = run_in_omnia_core(host, f"cat '{path}'")
    if cmd["success"]:
        return {"success": True, "content": cmd["stdout"] or "", "error": None}
    err = (cmd["stderr"] or cmd["stdout"] or "").strip()
    return {"success": False, "content": "", "error": err}


def parse_status_csv(content: str) -> Dict[str, Any]:
    """Parse status.csv content and detect any failures + per-package CSV references."""
    if not (content or "").strip():
        return {
            "success": False, "rows": [], "failures": [], "followups": [],
            "error": LOCAL_REPO_MSGS["status_csv_empty"]
        }

    reader = csv.DictReader(io.StringIO(content))
    rows = list(reader)
    if not rows:
        return {
            "success": False, "rows": [], "failures": [], "followups": [],
            "error": LOCAL_REPO_MSGS["status_csv_no_rows"]
        }

    failures = []
    followups = []
    for row in rows:
        row_text = " ".join([str(v) for v in row.values() if v is not None])
        if "fail" in row_text.lower():
            failures.append(row)
            for v in row.values():
                if isinstance(v, str) and v.strip().endswith(".csv"):
                    followups.append(v.strip())

    return {
        "success": len(failures) == 0,
        "rows": rows,
        "failures": failures,
        "followups": followups,
        "error": None if len(failures) == 0 else LOCAL_REPO_MSGS["status_csv_has_failures"],
    }


def check_status_csv_all_packages_downloaded(host) -> Dict[str, Any]:
    """Validate per-software status.csv files indicate no failures."""
    expected = get_expected_status_csv_paths(host)
    if not expected.get("success"):
        return {"success": False, "status_path": "", "details": None, "error": expected.get("error") or ""}

    missing = []
    failed = []
    checked = 0
    total_rows = 0

    for item in expected.get("paths", []):
        status_path = item.get("path") or ""
        software = item.get("software") or ""
        arch = item.get("arch") or ""
        if not status_path:
            continue

        status_file = read_file_in_omnia_core(host, status_path)
        if not status_file["success"]:
            missing.append({"path": status_path, "arch": arch, "software": software})
            continue

        parsed = parse_status_csv(status_file["content"])
        checked += 1
        total_rows += len(parsed.get("rows") or [])
        if not parsed.get("success"):
            failed.append({
                "path": status_path,
                "arch": arch,
                "software": software,
                "failures": len(parsed.get("failures") or []),
            })

    if missing and checked == 0:
        return {"success": False, "status_path": "", "details": None, "error": "status.csv not found"}

    if not missing and not failed:
        return {
            "success": True,
            "status_path": "",
            "details": f"Files: {checked}, Rows: {total_rows}",
            "error": None,
        }

    details_lines = []
    if missing:
        details_lines.append(f"Missing status.csv files: {len(missing)}")
        for m in missing[:20]:
            details_lines.append(f"- {m['arch']}/{m['software']}: {m['path']}")
    if failed:
        details_lines.append(f"status.csv files with failures: {len(failed)}")
        for f in failed[:20]:
            details_lines.append(f"- {f['arch']}/{f['software']}: {f['path']} (failures: {f['failures']})")

    return {
        "success": False,
        "status_path": "",
        "details": "\n".join(details_lines).strip(),
        "error": LOCAL_REPO_MSGS["status_csv_has_failures"],
    }


# =============================================================================
# SOFTWARE CONFIG PARSING AND PACKAGE VERIFICATION
# =============================================================================

def load_software_config(host) -> Dict[str, Any]:
    """Load software_config.json from omnia_core container."""
    oim_input_dir = LOCAL_REPO_VARS.get("oim_input_dir", "/opt/omnia/input/project_default")
    config_path = f"{oim_input_dir}/software_config.json"

    result = read_file_in_omnia_core(host, config_path)
    if not result["success"]:
        return {
            "success": False, "config": {},
            "error": f"Failed to read {config_path}: {result['error']}"
        }

    try:
        config = json.loads(result["content"])
        return {"success": True, "config": config, "error": None}
    except json.JSONDecodeError as e:
        return {"success": False, "config": {}, "error": f"Invalid JSON in {config_path}: {str(e)}"}


def build_config_path(os_type: str, os_version: str, arch: str, software_name: str) -> str:
    """Build path to config JSON file."""
    oim_input_dir = LOCAL_REPO_VARS.get("oim_input_dir", "/opt/omnia/input/project_default")
    return f"{oim_input_dir}/config/{arch}/{os_type}/{os_version}/{software_name}.json"


def load_package_config(host, os_type: str, os_version: str,
                        arch: str, software_name: str) -> Dict[str, Any]:
    """Load a specific package config JSON from omnia_core container."""
    config_path = build_config_path(os_type, os_version, arch, software_name)

    result = read_file_in_omnia_core(host, config_path)
    if not result["success"]:
        return {
            "success": False, "config": {}, "path": config_path,
            "error": f"Failed to read {config_path}"
        }

    try:
        config = json.loads(result["content"])
        return {"success": True, "config": config, "path": config_path, "error": None}
    except json.JSONDecodeError as e:
        return {
            "success": False, "config": {}, "path": config_path,
            "error": f"Invalid JSON: {str(e)}"
        }


def extract_packages_from_config(config: Dict[str, Any]) -> List[Dict[str, str]]:
    """Extract package list from a config JSON."""
    packages = []

    for key, value in config.items():
        if isinstance(value, dict):
            # Check for "cluster" key which contains package list
            cluster_pkgs = value.get("cluster", [])
            if isinstance(cluster_pkgs, list):
                for pkg in cluster_pkgs:
                    if isinstance(pkg, dict) and "package" in pkg:
                        packages.append({
                            "package": pkg.get("package", ""),
                            "type": pkg.get("type", "rpm"),
                            "repo_name": pkg.get("repo_name", ""),
                            "component": key,
                        })

    return packages


def get_expected_packages_from_software_config(host) -> Dict[str, Any]:
    """
    Parse software_config.json and load all referenced config JSONs.
    Returns a consolidated list of expected packages with their repo names.
    """
    # Load software_config.json
    sw_result = load_software_config(host)
    if not sw_result["success"]:
        return {"success": False, "packages": [], "details": "", "error": sw_result["error"]}

    sw_config = sw_result["config"]
    os_type = sw_config.get("cluster_os_type", "rhel")
    os_version = sw_config.get("cluster_os_version", "10.0")
    softwares = sw_config.get("softwares", [])

    if not softwares:
        return {
            "success": False, "packages": [], "details": "",
            "error": "No softwares defined in software_config.json"
        }

    all_packages = []
    loaded_configs = []
    errors = []

    for sw in softwares:
        if not isinstance(sw, dict):
            continue

        name = sw.get("name", "")
        archs = sw.get("arch", [])

        if not name or not archs:
            continue

        for arch in archs:
            pkg_result = load_package_config(host, os_type, os_version, arch, name)
            if not pkg_result["success"]:
                errors.append(f"{name}/{arch}: {pkg_result['error']}")
                continue

            loaded_configs.append(f"{arch}/{os_type}/{os_version}/{name}.json")
            packages = extract_packages_from_config(pkg_result["config"])

            for pkg in packages:
                pkg["arch"] = arch
                pkg["software"] = name
                all_packages.append(pkg)

    # Filter to only RPM packages (skip iso, url types)
    rpm_packages = [p for p in all_packages if p.get("type", "rpm") == "rpm"]

    details = (
        f"OS: {os_type} {os_version}\n"
        f"Softwares: {len(softwares)}\n"
        f"Configs loaded: {len(loaded_configs)}\n"
        f"Total packages: {len(all_packages)}\n"
        f"RPM packages: {len(rpm_packages)}"
    )

    if errors:
        details += f"\nErrors: {len(errors)}"

    return {
        "success": True,
        "packages": rpm_packages,
        "all_packages": all_packages,
        "configs_loaded": loaded_configs,
        "errors": errors,
        "details": details,
        "error": None,
    }


def _split_name_version(package_name: str) -> Dict[str, str]:
    """Best-effort split for strings like 'kubelet-1.34.1' into name/version."""
    pkg = (package_name or "").strip()
    if not pkg or "-" not in pkg:
        return {"name": pkg, "version": ""}

    # Heuristic: treat the last '-' segment as version if it looks version-like.
    base, tail = pkg.rsplit("-", 1)
    if re.fullmatch(r"\d+(?:[._-]\d+)*", tail or ""):
        return {"name": base, "version": tail}
    return {"name": pkg, "version": ""}


def _resolve_pulp_repo_name(repo_name: str, arch: str) -> str:
    """Map config repo_name to actual Pulp repository naming."""
    r = (repo_name or "").strip()
    a = (arch or "").strip()
    if not r:
        return ""
    if not a:
        return r

    # If already prefixed with an arch, keep as-is.
    if r.startswith(f"{a}_"):
        return r

    # Common repos are created in Pulp with arch prefix.
    if r in {"baseos", "appstream", "epel", "kubernetes", "cri-o", "docker-ce", "codeready-builder"}:
        return f"{a}_{r}"

    return r


def _get_pulp_repo_versions_by_name(host) -> Dict[str, str]:
    """Return mapping: repo name -> latest_version_href."""
    cmd = run_in_omnia_core(host, "pulp rpm repository list 2>/dev/null")
    if not cmd.get("success"):
        return {}

    stdout = (cmd.get("stdout") or "").strip()
    if not stdout or stdout == "[]":
        return {}

    try:
        repos = json.loads(stdout)
    except json.JSONDecodeError:
        return {}

    versions = {}
    for r in repos:
        name = (r.get("name") or "").strip()
        href = (r.get("latest_version_href") or "").strip()
        if name and href:
            versions[name] = href
    return versions


def check_package_in_pulp(host, package_name: str, repository_version: str = "") -> Dict[str, Any]:
    """Check if a package exists in Pulp using pulp rpm content list.

    Note: Pulp stores RPM fields separately (name/version/release/arch). Some
    expected package strings in config may be formatted like 'name-version'.
    """
    pkg = (package_name or "").strip()
    if not pkg:
        return {"success": True, "found": False, "error": None}

    repo_v = (repository_version or "").strip()
    repo_arg = f" --repository-version '{repo_v}'" if repo_v else ""

    # 1) Try exact name match first.
    pulp_cmd = f"pulp rpm content list{repo_arg} --name '{pkg}' --limit 1 2>/dev/null"
    cmd = run_in_omnia_core(host, pulp_cmd)
    if cmd.get("success"):
        stdout = (cmd.get("stdout") or "").strip()
        if stdout and stdout != "[]":
            return {"success": True, "found": True, "error": None}

    # 2) If expected looks like name-version, try name-only and match version.
    nv = _split_name_version(pkg)
    name_only = (nv.get("name") or "").strip()
    ver = (nv.get("version") or "").strip()
    if name_only and ver:
        # Pull more than 1 so we can scan versions.
        cmd2 = run_in_omnia_core(host, f"pulp rpm content list{repo_arg} --name '{name_only}' --limit 200 2>/dev/null")
        if cmd2.get("success"):
            out2 = (cmd2.get("stdout") or "").strip()
            if out2 and out2 != "[]" and f'"version": "{ver}"' in out2:
                return {"success": True, "found": True, "error": None}

    # If pulp command failed, surface a useful error; otherwise it's simply not found.
    if cmd and not cmd.get("success"):
        return {"success": False, "found": False, "error": (cmd.get("stderr") or cmd.get("stdout") or "Command failed").strip()}

    return {"success": True, "found": False, "error": None}


def _get_status_csv_path_for_software(arch: str, software: str) -> str:
    base = (LOCAL_REPO_VARS.get("status_search_roots") or ["/opt/omnia/log/local_repo"])[0]
    a = (arch or "").strip()
    s = (software or "").strip()
    if not a or not s:
        return ""
    return f"{base}/{a}/{s}/status.csv"


def _is_rpm_success_in_status_csv(host, arch: str, software: str, package_name: str) -> bool:
    """Return True if per-software status.csv shows the RPM package as Success."""
    pkg = (package_name or "").strip()
    if not pkg:
        return False

    status_path = _get_status_csv_path_for_software(arch, software)
    if not status_path:
        return False

    res = read_file_in_omnia_core(host, status_path)
    if not res.get("success"):
        return False

    content = res.get("content") or ""
    if not content.strip():
        return False

    try:
        reader = csv.DictReader(io.StringIO(content))
        for row in reader:
            name = (row.get("name") or "").strip()
            typ = (row.get("type") or "").strip().lower()
            status = (row.get("status") or "").strip().lower()
            if name == pkg and typ == "rpm" and status == "success":
                return True
    except Exception:
        return False

    return False


def verify_packages_in_pulp(host, packages: List[Dict[str, str]]) -> Dict[str, Any]:
    """
    Verify that all expected packages exist in Pulp.
    Returns summary of found/missing packages.
    """
    if not packages:
        return {
            "success": True,
            "total": 0,
            "found": 0,
            "missing": 0,
            "missing_packages": [],
            "details": "No packages to verify",
            "error": None,
        }

    # Deduplicate by package name
    unique_packages = {}
    for pkg in packages:
        name = pkg.get("package", "")
        if name and name not in unique_packages:
            unique_packages[name] = pkg

    repo_versions = _get_pulp_repo_versions_by_name(host)
    found_count = 0
    status_fallback_count = 0
    missing_packages = []

    for name, pkg_info in unique_packages.items():
        arch = pkg_info.get("arch", "")
        repo_name = pkg_info.get("repo_name", "")
        pulp_repo_name = _resolve_pulp_repo_name(repo_name, arch)
        repo_version = repo_versions.get(pulp_repo_name, "")
        result = check_package_in_pulp(host, name, repository_version=repo_version)
        if result.get("found"):
            found_count += 1
            continue

        # Option B fallback: treat as found if status.csv says rpm Success.
        software = pkg_info.get("software", "")
        if _is_rpm_success_in_status_csv(host, arch, software, name):
            found_count += 1
            status_fallback_count += 1
            continue

        missing_packages.append({
            "package": name,
            "repo_name": repo_name,
            "software": software,
            "component": pkg_info.get("component", ""),
        })

    total = len(unique_packages)
    missing_count = len(missing_packages)

    details = (
        f"Verified: {total} unique packages\n"
        f"Found: {found_count}\n"
        f"Missing: {missing_count}"
    )
    if status_fallback_count:
        details += f"\nFound via status.csv fallback: {status_fallback_count}"

    if missing_packages:
        missing_list = "\n".join(
            [f"  - {p['package']} (repo: {p['repo_name']}, software: {p['software']})"
             for p in missing_packages[:20]])
        if len(missing_packages) > 20:
            missing_list += f"\n  ... and {len(missing_packages) - 20} more"
        details += f"\n\nMissing packages:\n{missing_list}"

    return {
        "success": missing_count == 0,
        "total": total,
        "found": found_count,
        "missing": missing_count,
        "missing_packages": missing_packages,
        "details": details,
        "error": None if missing_count == 0 else f"{missing_count} packages not found in Pulp",
    }


def check_software_packages_in_pulp(host) -> Dict[str, Any]:
    """
    Full verification: parse software_config.json, load configs, verify all packages in Pulp.
    This is the main entry point for the test.
    """
    # Step 1: Get expected packages from software_config.json
    pkg_result = get_expected_packages_from_software_config(host)
    if not pkg_result["success"]:
        return {
            "success": False,
            "details": "",
            "error": pkg_result["error"],
        }

    packages = pkg_result.get("packages", [])
    config_details = pkg_result.get("details", "")
    config_errors = pkg_result.get("errors", [])

    if not packages:
        return {
            "success": False,
            "details": config_details,
            "error": "No RPM packages found in software configs",
        }

    # Step 2: Verify packages in Pulp
    verify_result = verify_packages_in_pulp(host, packages)

    full_details = (
        f"=== Software Config ===\n{config_details}\n\n"
        f"=== Pulp Verification ===\n{verify_result['details']}"
    )

    if config_errors:
        full_details += "\n\n=== Config Load Errors ===\n" + "\n".join(config_errors[:10])

    return {
        "success": verify_result["success"],
        "total_packages": verify_result["total"],
        "found_packages": verify_result["found"],
        "missing_packages": verify_result["missing"],
        "missing_list": verify_result["missing_packages"],
        "details": full_details,
        "error": verify_result["error"],
    }


# =============================================================================
# PULP API AND FUNCTIONALITY VERIFICATION FUNCTIONS
# =============================================================================

def check_pulp_api_status(host) -> Dict[str, Any]:
    """
    Verify Pulp API status is healthy by checking:
    1. PostgreSQL database connectivity inside pulp container (psql -U pulp)
    2. List databases and tables to ensure DB commands work
    3. Pulp worker list with last heartbeat verification (via omnia_core)
    """
    details_parts = []
    errors = []

    # Step 1: Check PostgreSQL connectivity inside pulp container
    # Login to postgres and list databases (user is 'pulp', not 'admin')
    db_list_cmd = run_in_pulp_container(host, "psql -U pulp -c '\\\\l' 2>/dev/null")
    db_connected = False
    if db_list_cmd["success"]:
        db_output = (db_list_cmd.get("stdout") or "").strip()
        if "pulp" in db_output.lower() or "List of databases" in db_output:
            db_connected = True
            details_parts.append("PostgreSQL: connected (psql -U pulp)")
            # Count databases
            db_lines = [l for l in db_output.split("\n") if "|" in l and "Name" not in l]
            details_parts.append(f"Databases found: {len(db_lines)}")
        else:
            errors.append("PostgreSQL: could not list databases")
    else:
        errors.append(f"PostgreSQL: connection failed - {(db_list_cmd.get('stderr') or '').strip()[:100]}")

    # Step 2: List tables in pulp database to ensure commands work
    tables_cmd = run_in_pulp_container(host, "psql -U pulp -d pulp -c '\\\\dt' 2>/dev/null")
    tables_ok = False
    if tables_cmd["success"]:
        tables_output = (tables_cmd.get("stdout") or "").strip()
        if "List of relations" in tables_output or "public |" in tables_output:
            tables_ok = True
            # Count tables
            table_lines = [l for l in tables_output.split("\n") if "public |" in l]
            details_parts.append(f"Tables in pulp DB: {len(table_lines)}")
        elif "(0 rows)" in tables_output:
            tables_ok = True
            details_parts.append("Tables in pulp DB: 0 (empty)")
    else:
        errors.append("Could not list tables in pulp database")

    # Step 3: Check pulp workers using pulp worker list (via omnia_core, not pulp container)
    # The pulp CLI is available in omnia_core, not in the pulp container
    worker_cmd = run_in_omnia_core(host, "pulp worker list 2>/dev/null")
    worker_count = 0
    workers_healthy = False
    if worker_cmd["success"]:
        worker_output = (worker_cmd.get("stdout") or "").strip()
        if worker_output and worker_output != "[]":
            try:
                workers = json.loads(worker_output)
                worker_count = len(workers)
                if worker_count > 0:
                    workers_healthy = True
                    details_parts.append(f"Online workers: {worker_count}")
                    # Show last heartbeat for each worker
                    for w in workers[:5]:
                        name = w.get("name", "unknown")
                        heartbeat = w.get("last_heartbeat", "N/A")
                        details_parts.append(f"  - {name}: last heartbeat {heartbeat}")
                else:
                    errors.append("No workers found in pulp worker list")
            except json.JSONDecodeError:
                errors.append("Invalid JSON from pulp worker list")
        else:
            errors.append("Empty response from pulp worker list")
    else:
        errors.append(f"pulp worker list failed: {(worker_cmd.get('stderr') or '').strip()[:100]}")

    # Build final details
    details = "\n".join(details_parts)
    if errors:
        details += "\n\nErrors:\n" + "\n".join([f"  - {e}" for e in errors])

    # Success if database connected and workers are healthy
    success = db_connected and workers_healthy

    return {
        "success": success,
        "database_connected": db_connected,
        "tables_accessible": tables_ok,
        "online_workers": worker_count,
        "details": details,
        "error": None if success else "; ".join(errors) if errors else "Pulp services not fully healthy",
    }


def check_pulp_repositories_synced(host) -> Dict[str, Any]:
    """
    Verify all Pulp RPM repositories have content (are synced).
    A repository is considered synced if it has a latest_version_href.
    """
    cmd = run_in_omnia_core(host, "pulp rpm repository list 2>/dev/null")

    if not cmd["success"]:
        return {
            "success": False,
            "details": "",
            "error": f"pulp rpm repository list failed: {cmd.get('stderr', '')}",
        }

    stdout = (cmd.get("stdout") or "").strip()
    if stdout == "[]" or not stdout:
        return {
            "success": True,
            "total_repos": 0,
            "synced_repos": 0,
            "details": "No repositories found (empty is valid)",
            "error": None,
        }

    try:
        repos = json.loads(stdout)
        total_repos = len(repos)
        synced_repos = []
        not_synced_repos = []

        for repo in repos:
            name = repo.get("name", "unknown")
            latest_version = repo.get("latest_version_href")

            if latest_version:
                synced_repos.append(name)
            else:
                not_synced_repos.append(name)

        synced_count = len(synced_repos)
        not_synced_count = len(not_synced_repos)

        details = (f"Total repositories: {total_repos}\n"
                   f"Synced: {synced_count}\nNot synced: {not_synced_count}")

        if not_synced_repos:
            details += "\n\nNot synced repos:\n" + "\n".join(
                [f"  - {r}" for r in not_synced_repos[:10]])
            if not_synced_count > 10:
                details += f"\n  ... and {not_synced_count - 10} more"

        return {
            "success": not_synced_count == 0,
            "total_repos": total_repos,
            "synced_repos": synced_count,
            "not_synced_repos": not_synced_count,
            "not_synced_list": not_synced_repos,
            "details": details,
            "error": (None if not_synced_count == 0
                      else f"{not_synced_count} repositories not synced"),
        }
    except json.JSONDecodeError:
        return {
            "success": False,
            "details": stdout[:200],
            "error": "Invalid JSON from repository list",
        }


def check_pulp_distributions_published(host) -> Dict[str, Any]:
    """
    Verify Pulp RPM distributions are created and have publications.
    Distributions serve content to clients.
    """
    cmd = run_in_omnia_core(host, "pulp rpm distribution list 2>/dev/null")

    if not cmd["success"]:
        return {
            "success": False,
            "details": "",
            "error": f"pulp rpm distribution list failed: {cmd.get('stderr', '')}",
        }

    stdout = (cmd.get("stdout") or "").strip()
    if stdout == "[]" or not stdout:
        return {
            "success": True,
            "total_distributions": 0,
            "details": "No distributions found (empty is valid if no repos)",
            "error": None,
        }

    try:
        distributions = json.loads(stdout)
        total_dists = len(distributions)
        published_dists = []
        unpublished_dists = []

        for dist in distributions:
            name = dist.get("name", "unknown")
            base_path = dist.get("base_path", "")
            publication = dist.get("publication")
            repository = dist.get("repository")

            # A distribution is valid if it has either a publication or repository
            if publication or repository:
                published_dists.append({"name": name, "base_path": base_path})
            else:
                unpublished_dists.append({"name": name, "base_path": base_path})

        published_count = len(published_dists)
        unpublished_count = len(unpublished_dists)

        details = (f"Total distributions: {total_dists}\n"
                   f"Published: {published_count}\nUnpublished: {unpublished_count}")

        if published_dists:
            details += "\n\nPublished distributions:\n" + "\n".join(
                [f"  - {d['name']} ({d['base_path']})" for d in published_dists[:5]])

        if unpublished_dists:
            details += "\n\nUnpublished distributions:\n" + "\n".join(
                [f"  - {d['name']}" for d in unpublished_dists[:5]])

        return {
            "success": unpublished_count == 0,
            "total_distributions": total_dists,
            "published_count": published_count,
            "unpublished_count": unpublished_count,
            "details": details,
            "error": (None if unpublished_count == 0
                      else f"{unpublished_count} distributions not published"),
        }
    except json.JSONDecodeError:
        return {
            "success": False,
            "details": stdout[:200],
            "error": "Invalid JSON from distribution list",
        }


def check_pulp_no_failed_tasks(host) -> Dict[str, Any]:
    """
    Check for failed tasks in Pulp task queue.
    Failed tasks indicate sync/publish problems.
    """
    cmd = run_in_omnia_core(host, "pulp task list --state=failed --limit=20 2>/dev/null")

    if not cmd["success"]:
        return {
            "success": False,
            "failed_count": -1,
            "details": "",
            "error": f"pulp task list failed: {cmd.get('stderr', '')}",
        }

    stdout = (cmd.get("stdout") or "").strip()

    if stdout == "[]" or not stdout:
        return {
            "success": True,
            "failed_count": 0,
            "details": "No failed tasks",
            "error": None,
        }

    try:
        tasks = json.loads(stdout)
        failed_count = len(tasks)

        if failed_count == 0:
            return {
                "success": True,
                "failed_count": 0,
                "details": "No failed tasks",
                "error": None,
            }

        # Extract task summaries
        task_summaries = []
        for task in tasks[:5]:
            task_name = task.get("name", "unknown")
            task_error = task.get("error", {})
            if isinstance(task_error, dict):
                error_desc = task_error.get("description", "")[:80]
            else:
                error_desc = str(task_error)[:80]
            task_summaries.append(f"- {task_name}: {error_desc}")

        details = f"Failed tasks: {failed_count}\n" + "\n".join(task_summaries)
        if failed_count > 5:
            details += f"\n... and {failed_count - 5} more"

        return {
            "success": False,
            "failed_count": failed_count,
            "tasks": tasks[:10],
            "details": details,
            "error": f"{failed_count} failed tasks found",
        }
    except json.JSONDecodeError:
        return {
            "success": False,
            "failed_count": -1,
            "details": stdout[:200],
            "error": "Invalid task list response",
        }


def check_pulp_content_accessible(host) -> Dict[str, Any]:
    """
    Verify Pulp content is accessible via HTTP by checking repomd.xml of a distribution.
    This confirms the content serving pipeline is working.
    """
    # First get a distribution to test
    dist_cmd = run_in_omnia_core(host, "pulp rpm distribution list --limit 1 2>/dev/null")

    if not dist_cmd["success"]:
        return {
            "success": False,
            "details": "",
            "error": f"Failed to list distributions: {dist_cmd.get('stderr', '')}",
        }

    stdout = (dist_cmd.get("stdout") or "").strip()
    if stdout == "[]" or not stdout:
        return {
            "success": True,
            "details": "No distributions to check (empty repo is valid)",
            "error": None,
        }

    try:
        dists = json.loads(stdout)
        if not dists:
            return {
                "success": True,
                "details": "No distributions to check",
                "error": None,
            }

        base_path = dists[0].get("base_path", "")
        dist_name = dists[0].get("name", "unknown")

        if not base_path:
            return {
                "success": False,
                "details": f"Distribution '{dist_name}' has no base_path",
                "error": "Distribution has no base_path",
            }

        # Try to access repodata via localhost (inside omnia_core which can reach pulp)
        # Use pulp's content URL - typically https://localhost:port/pulp/content/<base_path>/
        curl_https = (f"curl -sk https://localhost:2225/pulp/content/{base_path}"
                      "/repodata/repomd.xml -o /dev/null -w '%{http_code}' "
                      "--connect-timeout 10 2>/dev/null")
        curl_http = (f"curl -s http://localhost:80/pulp/content/{base_path}"
                     "/repodata/repomd.xml -o /dev/null -w '%{http_code}' "
                     "--connect-timeout 10 2>/dev/null")
        content_cmd = run_in_omnia_core(host, f"{curl_https} || {curl_http}")

        http_code = (content_cmd.get("stdout") or "").strip()

        # Accept 200 (success) or 404 (repo exists but no packages yet)
        success = http_code in ["200", "404"]

        details = f"Distribution: {dist_name}\nBase path: {base_path}\nHTTP status: {http_code}"

        return {
            "success": success,
            "distribution": dist_name,
            "base_path": base_path,
            "http_code": http_code,
            "details": details,
            "error": None if success else f"Content not accessible: HTTP {http_code}",
        }
    except json.JSONDecodeError:
        return {
            "success": False,
            "details": "",
            "error": "Invalid distribution list response",
        }


def load_local_repo_config_from_container(host) -> Dict[str, Any]:
    """Load local_repo_config.yml from omnia_core container."""
    oim_input_dir = LOCAL_REPO_VARS.get("oim_input_dir", "/opt/omnia/input/project_default")
    config_path = f"{oim_input_dir}/local_repo_config.yml"

    result = read_file_in_omnia_core(host, config_path)
    if not result["success"]:
        return {
            "success": False,
            "config": {},
            "error": f"Failed to read {config_path}: {result.get('error', '')}",
        }

    content = result.get("content", "")
    if not content.strip():
        return {
            "success": False,
            "config": {},
            "error": f"{config_path} is empty",
        }

    try:
        config = yaml.safe_load(content) or {}
        return {"success": True, "config": config, "error": None}
    except yaml.YAMLError as e:
        return {
            "success": False,
            "config": {},
            "error": f"Invalid YAML in {config_path}: {str(e)}",
        }


def check_pulp_distributions_match_config(host) -> Dict[str, Any]:
    """
    Verify Pulp distributions match expected repos from local_repo_config.yml.

    Steps:
    1. Load local_repo_config.yml from omnia_core container
    2. Extract expected repo names per arch from omnia_repo_url_rhel_{arch}
    3. Get actual Pulp distributions via `pulp rpm distribution list`
    4. For each expected repo, check if {arch}_{name} exists in Pulp
    5. Report matched/missing distributions
    """
    # Step 1: Load local_repo_config.yml
    config_result = load_local_repo_config_from_container(host)
    if not config_result["success"]:
        return {
            "success": False,
            "total_expected": 0,
            "matched": 0,
            "missing": 0,
            "missing_distributions": [],
            "details": "",
            "error": config_result.get("error", "Failed to load config"),
        }

    config = config_result.get("config", {})

    # Step 2: Build expected distributions per arch
    expected = []
    for arch in ["x86_64", "aarch64"]:
        key = f"omnia_repo_url_rhel_{arch}"
        repos = config.get(key, []) or []
        if not isinstance(repos, list):
            continue
        for repo in repos:
            if not isinstance(repo, dict):
                continue
            name = (repo.get("name") or "").strip()
            if name:
                expected.append({
                    "arch": arch,
                    "repo_name": name,
                    "expected_dist": f"{arch}_{name}",
                })

    if not expected:
        return {
            "success": True,
            "total_expected": 0,
            "matched": 0,
            "missing": 0,
            "missing_distributions": [],
            "details": "No repos defined in omnia_repo_url_rhel_* keys",
            "error": None,
        }

    # Step 3: Get actual Pulp distributions
    cmd = run_in_omnia_core(host, "pulp rpm distribution list --field name 2>/dev/null")
    if not cmd["success"]:
        return {
            "success": False,
            "total_expected": len(expected),
            "matched": 0,
            "missing": len(expected),
            "missing_distributions": expected,
            "details": "",
            "error": f"pulp rpm distribution list failed: {cmd.get('stderr', '')}",
        }

    stdout = (cmd.get("stdout") or "").strip()
    actual_dists = set()
    if stdout and stdout != "[]":
        try:
            dists = json.loads(stdout)
            for dist in dists:
                name = (dist.get("name") or "").strip()
                if name:
                    actual_dists.add(name)
        except json.JSONDecodeError:
            return {
                "success": False,
                "total_expected": len(expected),
                "matched": 0,
                "missing": len(expected),
                "missing_distributions": expected,
                "details": stdout[:200],
                "error": "Invalid JSON from distribution list",
            }

    # Step 4: Match expected vs actual
    matched = []
    missing = []
    for exp in expected:
        dist_name = exp["expected_dist"]
        if dist_name in actual_dists:
            matched.append(exp)
        else:
            missing.append(exp)

    # Step 5: Build results
    total_expected = len(expected)
    matched_count = len(matched)
    missing_count = len(missing)

    details = (
        f"Expected: {total_expected}\n"
        f"Found: {matched_count}\n"
        f"Missing: {missing_count}"
    )

    if matched:
        details += "\n\nMatched distributions:\n" + "\n".join(
            [f"  - {m['expected_dist']} ({m['arch']}/{m['repo_name']})" for m in matched[:10]]
        )
        if len(matched) > 10:
            details += f"\n  ... and {len(matched) - 10} more"

    if missing:
        details += "\n\nMissing distributions:\n" + "\n".join(
            [f"  - {m['expected_dist']} ({m['arch']}/{m['repo_name']})" for m in missing[:10]]
        )
        if len(missing) > 10:
            details += f"\n  ... and {len(missing) - 10} more"

    return {
        "success": missing_count == 0,
        "total_expected": total_expected,
        "matched": matched_count,
        "missing": missing_count,
        "matched_distributions": matched,
        "missing_distributions": missing,
        "details": details,
        "error": None if missing_count == 0 else f"{missing_count} expected distributions not found in Pulp",
    }


def run_in_pulp_container(host, cmd: str) -> Dict[str, Any]:
    """Run a command in pulp container using bash -c."""
    container = LOCAL_REPO_VARS["pulp_container"]
    res = host.run(f"podman exec {container} bash -c \"{cmd}\"")
    return {
        "success": res.rc == 0,
        "rc": res.rc,
        "stdout": res.stdout or "",
        "stderr": res.stderr or "",
    }


def check_nfs_mounts_in_pulp(host) -> Dict[str, Any]:
    """
    Verify NFS mounts are present inside the Pulp container.
    
    Checks for critical NFS mount points:
    - /var/lib/pulp (Pulp storage)
    - /var/lib/pgsql (PostgreSQL data)
    - /var/log/pulp (Pulp logs)
    """
    required_mounts = [
        {"path": "/var/lib/pulp", "description": "Pulp storage"},
        {"path": "/var/lib/pgsql", "description": "PostgreSQL data"},
        {"path": "/var/log/pulp", "description": "Pulp logs"},
    ]
    
    # Get all NFS mounts inside pulp container
    cmd = run_in_pulp_container(host, "mount | grep 'type nfs'")
    if not cmd["success"] and cmd["rc"] != 1:  # rc=1 means no matches (grep)
        return {
            "success": False,
            "total_mounts": 0,
            "verified_mounts": [],
            "missing_mounts": [m["path"] for m in required_mounts],
            "details": "",
            "error": f"Failed to check mounts: {cmd.get('stderr', '')}",
        }
    
    mount_output = cmd.get("stdout", "")
    
    verified = []
    missing = []
    
    for mount in required_mounts:
        path = mount["path"]
        desc = mount["description"]
        # Check if mount path appears in mount output
        if f" on {path} type nfs" in mount_output or f" {path} " in mount_output:
            # Extract NFS server info
            for line in mount_output.split("\n"):
                if f" on {path} " in line or f" {path} " in line:
                    # Parse NFS source (e.g., 100.98.69.235:/mnt/...)
                    parts = line.split(" on ")
                    nfs_source = parts[0] if parts else "unknown"
                    verified.append({
                        "path": path,
                        "description": desc,
                        "nfs_source": nfs_source.strip(),
                        "status": "mounted",
                    })
                    break
        else:
            missing.append({
                "path": path,
                "description": desc,
                "status": "not_mounted",
            })
    
    total = len(required_mounts)
    verified_count = len(verified)
    missing_count = len(missing)
    
    details = (
        f"Total required: {total}\n"
        f"Verified: {verified_count}\n"
        f"Missing: {missing_count}"
    )
    
    if verified:
        details += "\n\nVerified NFS mounts:\n" + "\n".join(
            [f"  - {v['path']} ({v['description']})\n    Source: {v['nfs_source']}" for v in verified]
        )
    
    if missing:
        details += "\n\nMissing NFS mounts:\n" + "\n".join(
            [f"  - {m['path']} ({m['description']})" for m in missing]
        )
    
    return {
        "success": missing_count == 0,
        "total_mounts": total,
        "verified_count": verified_count,
        "missing_count": missing_count,
        "verified_mounts": verified,
        "missing_mounts": missing,
        "details": details,
        "error": None if missing_count == 0 else f"{missing_count} required NFS mounts not found",
    }


def check_pulp_remotes_exist(host) -> Dict[str, Any]:
    """
    Verify Pulp remotes are configured for repositories.
    
    Remotes define the upstream repository URLs. Without them, sync won't work.
    This test:
    1. Lists all RPM remotes via `pulp rpm remote list`
    2. Verifies remotes exist and have URLs configured
    3. Optionally matches against expected repos from local_repo_config.yml
    """
    cmd = run_in_omnia_core(host, "pulp rpm remote list 2>/dev/null")
    
    if not cmd["success"]:
        return {
            "success": False,
            "total_remotes": 0,
            "remotes": [],
            "details": "",
            "error": f"pulp rpm remote list failed: {cmd.get('stderr', '')}",
        }
    
    stdout = (cmd.get("stdout") or "").strip()
    if stdout == "[]" or not stdout:
        return {
            "success": False,
            "total_remotes": 0,
            "remotes": [],
            "details": "No remotes found",
            "error": "No Pulp remotes configured. Remotes are required for syncing upstream repos.",
        }
    
    try:
        remotes = json.loads(stdout)
        total_remotes = len(remotes)
        
        valid_remotes = []
        invalid_remotes = []
        
        for remote in remotes:
            name = remote.get("name", "unknown")
            url = remote.get("url", "")
            
            if url:
                valid_remotes.append({"name": name, "url": url})
            else:
                invalid_remotes.append({"name": name, "url": url})
        
        valid_count = len(valid_remotes)
        invalid_count = len(invalid_remotes)
        
        details = (
            f"Total remotes: {total_remotes}\n"
            f"Valid (with URL): {valid_count}\n"
            f"Invalid (no URL): {invalid_count}"
        )
        
        if valid_remotes:
            details += "\n\nConfigured remotes:\n" + "\n".join(
                [f"  - {r['name']}: {r['url'][:60]}..." if len(r['url']) > 60 else f"  - {r['name']}: {r['url']}" 
                 for r in valid_remotes[:10]]
            )
            if len(valid_remotes) > 10:
                details += f"\n  ... and {len(valid_remotes) - 10} more"
        
        if invalid_remotes:
            details += "\n\nRemotes without URL:\n" + "\n".join(
                [f"  - {r['name']}" for r in invalid_remotes]
            )
        
        # Success if we have at least one valid remote
        success = valid_count > 0
        
        return {
            "success": success,
            "total_remotes": total_remotes,
            "valid_count": valid_count,
            "invalid_count": invalid_count,
            "remotes": valid_remotes,
            "invalid_remotes": invalid_remotes,
            "details": details,
            "error": None if success else "No valid remotes with URLs found",
        }
    except json.JSONDecodeError:
        return {
            "success": False,
            "total_remotes": 0,
            "remotes": [],
            "details": stdout[:200],
            "error": "Invalid JSON from remote list",
        }


def check_nfs_storage_permissions(host) -> Dict[str, Any]:
    """
    Verify NFS storage permissions and read/write access in Pulp container.
    
    Checks:
    - /var/lib/pulp ownership and permissions
    - Read/write access test
    """
    storage_path = "/var/lib/pulp"
    
    # Check if path exists
    exists_cmd = run_in_pulp_container(host, f"test -d {storage_path} && echo 'exists'")
    if "exists" not in exists_cmd.get("stdout", ""):
        return {
            "success": False,
            "path": storage_path,
            "exists": False,
            "readable": False,
            "writable": False,
            "details": f"Storage path {storage_path} does not exist",
            "error": f"Storage path {storage_path} not found",
        }
    
    # Get ownership and permissions
    stat_cmd = run_in_pulp_container(host, f"stat -c '%U:%G %a' {storage_path}")
    ownership = stat_cmd.get("stdout", "").strip() if stat_cmd["success"] else "unknown"
    
    # Test read access
    read_cmd = run_in_pulp_container(host, f"ls {storage_path} >/dev/null 2>&1 && echo 'readable'")
    readable = "readable" in read_cmd.get("stdout", "")
    
    # Test write access (create and remove temp file)
    test_file = f"{storage_path}/.nfs_write_test_{host.backend.get_hostname()}"
    write_cmd = run_in_pulp_container(
        host, 
        f"touch {test_file} 2>/dev/null && rm -f {test_file} && echo 'writable'"
    )
    writable = "writable" in write_cmd.get("stdout", "")
    
    # Get disk usage
    df_cmd = run_in_pulp_container(host, f"df -h {storage_path} | tail -1")
    disk_info = df_cmd.get("stdout", "").strip() if df_cmd["success"] else "unknown"
    
    success = readable and writable
    
    details = (
        f"Path: {storage_path}\n"
        f"Ownership: {ownership}\n"
        f"Readable: {'Yes' if readable else 'No'}\n"
        f"Writable: {'Yes' if writable else 'No'}\n"
        f"Disk: {disk_info}"
    )
    
    error = None
    if not readable:
        error = f"Storage path {storage_path} is not readable"
    elif not writable:
        error = f"Storage path {storage_path} is not writable"
    
    return {
        "success": success,
        "path": storage_path,
        "exists": True,
        "ownership": ownership,
        "readable": readable,
        "writable": writable,
        "disk_info": disk_info,
        "details": details,
        "error": error,
    }
