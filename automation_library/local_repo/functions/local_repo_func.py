"""Prepare Local Repo - Verification Functions."""

import csv
import io
import json
from typing import Dict, Any, List

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


def check_pulp_cli_repository_list(host) -> Dict[str, Any]:
    """Verify pulp CLI works (pulp rpm repository list)."""
    cmd = run_in_omnia_core(host, "pulp rpm repository list")
    if cmd["success"]:
        return {
            "success": True,
            "details": (cmd["stdout"] or "").strip(),
            "error": None,
        }
    return {
        "success": False,
        "details": None,
        "error": (cmd["stderr"] or cmd["stdout"] or "").strip(),
    }


def find_status_csv(host) -> Dict[str, Any]:
    """Locate status.csv inside omnia_core. Returns newest match when possible."""
    roots = LOCAL_REPO_VARS.get("status_search_roots", ["/opt/omnia", "/local/omnia", "/omnia"])
    roots_str = " ".join(roots)
    # Prefer newest file across roots
    find_cmd = run_in_omnia_core(
        host,
        "find "
        + roots_str
        + " -name status.csv -printf '%T@ %p\\n' 2>/dev/null "
        + "| sort -nr | head -1 | awk '{print $2}'",
    )
    raw = (find_cmd["stdout"] or "").strip()
    path = raw
    # Be defensive: if command output still includes a leading timestamp ("<ts> <path>"),
    # strip the first field and keep the remainder.
    if " " in path:
        first, rest = path.split(" ", 1)
        try:
            float(first)
            path = rest.strip()
        except ValueError:
            pass
    if find_cmd["success"] and path:
        return {"success": True, "path": path, "error": None}

    # Fallback: any match
    fallback = run_in_omnia_core(host, f"find {roots_str} -name status.csv 2>/dev/null | head -20")
    paths = [p.strip() for p in (fallback["stdout"] or "").splitlines() if p.strip()]
    if paths:
        return {"success": True, "path": paths[0], "error": None}

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
    """Validate status.csv indicates no failures; if failures, check referenced per-package CSVs."""
    status = find_status_csv(host)
    if not status["success"]:
        return {"success": False, "status_path": "", "details": None, "error": status["error"]}

    status_path = status["path"]
    status_file = read_file_in_omnia_core(host, status_path)
    if not status_file["success"]:
        return {
            "success": False, "status_path": status_path,
            "details": None, "error": status_file["error"]
        }

    parsed = parse_status_csv(status_file["content"])
    if parsed["success"]:
        return {
            "success": True,
            "status_path": status_path,
            "details": f"Rows: {len(parsed['rows'])}",
            "error": None,
        }

    # If failures exist, check referenced per-package CSVs if present
    per_pkg_failures = []
    for fp in parsed.get("followups", []):
        fp = fp.strip()
        if not fp:
            continue
        cmd = run_in_omnia_core(host, f"test -f '{fp}' && cat '{fp}' || true")
        data = (cmd.get("stdout") or "").lower()
        if not data.strip():
            per_pkg_failures.append({"file": fp, "error": "missing or empty"})
        elif "fail" in data:
            per_pkg_failures.append({"file": fp, "error": "contains 'fail'"})

    details = (
        f"status.csv: {status_path}\n"
        f"Top-level failures: {len(parsed.get('failures', []))}\n"
        f"Per-package refs: {len(parsed.get('followups', []))}\n"
        f"Per-package failures: {len(per_pkg_failures)}"
    )

    if per_pkg_failures:
        extra = "\n".join([f"- {x['file']}: {x['error']}" for x in per_pkg_failures[:20]])
        return {
            "success": False,
            "status_path": status_path,
            "details": details + "\n" + extra,
            "error": LOCAL_REPO_MSGS["status_csv_has_failures"],
        }

    return {
        "success": False,
        "status_path": status_path,
        "details": details,
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


def check_package_in_pulp(host, package_name: str) -> Dict[str, Any]:
    """Check if a package exists in Pulp using pulp rpm content list."""
    pulp_cmd = f"pulp rpm content list --name {package_name} --limit 1 2>/dev/null"
    cmd = run_in_omnia_core(host, pulp_cmd)

    if not cmd["success"]:
        return {"success": False, "found": False, "error": cmd.get("stderr", "Command failed")}

    stdout = cmd.get("stdout", "").strip()

    # Empty list [] means not found
    if stdout == "[]" or not stdout:
        return {"success": True, "found": False, "error": None}

    # Non-empty response means package exists
    return {"success": True, "found": True, "error": None}


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

    found_count = 0
    missing_packages = []

    for name, pkg_info in unique_packages.items():
        result = check_package_in_pulp(host, name)
        if result.get("found"):
            found_count += 1
        else:
            missing_packages.append({
                "package": name,
                "repo_name": pkg_info.get("repo_name", ""),
                "software": pkg_info.get("software", ""),
                "component": pkg_info.get("component", ""),
            })

    total = len(unique_packages)
    missing_count = len(missing_packages)

    details = f"Verified: {total} unique packages\nFound: {found_count}\nMissing: {missing_count}"

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
    Verify Pulp API status is healthy using 'pulp status' command.
    Checks database connection and online workers.
    """
    cmd = run_in_omnia_core(host, "pulp status 2>/dev/null")

    if not cmd["success"]:
        return {
            "success": False,
            "details": "",
            "error": f"pulp status command failed: {cmd.get('stderr', '')}",
        }

    stdout = (cmd.get("stdout") or "").strip()
    if not stdout:
        return {
            "success": False,
            "details": "",
            "error": "Empty response from pulp status",
        }

    try:
        status = json.loads(stdout)

        # Check database connection
        db_conn = status.get("database_connection", {})
        db_connected = db_conn.get("connected", False)

        # Check online workers
        online_workers = status.get("online_workers", [])
        worker_count = len(online_workers)

        # Check content app
        online_content_apps = status.get("online_content_apps", [])
        content_app_count = len(online_content_apps)

        # Get versions
        versions = status.get("versions", [])
        version_str = ", ".join(
            [f"{v.get('component', '?')}: {v.get('version', '?')}" for v in versions[:3]])

        details = (
            f"Database: {'connected' if db_connected else 'DISCONNECTED'}\n"
            f"Online workers: {worker_count}\n"
            f"Content apps: {content_app_count}\n"
            f"Versions: {version_str}"
        )

        # Success if database connected and at least one worker online
        success = db_connected and worker_count > 0

        return {
            "success": success,
            "database_connected": db_connected,
            "online_workers": worker_count,
            "content_apps": content_app_count,
            "details": details,
            "error": None if success else "Pulp services not fully healthy",
        }
    except json.JSONDecodeError as e:
        return {
            "success": False,
            "details": stdout[:200],
            "error": f"Invalid JSON from pulp status: {str(e)}",
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
