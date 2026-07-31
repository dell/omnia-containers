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
Additional Packages & Repos Testing Functions.

Functions for testing:
1. Per-functional-group package scoping (8 groups)
2. additional_repos SSL certificates
3. additional_repos sync policy (always vs partial)
4. aarch64 additional packages
"""

import json
from typing import Dict, Any, List, Optional

from automation_library.core import (
    run_on_remote_node,
    run_on_oim,
    run_in_container,
    get_input_value,
    load_container_file,
)

from ..vars import (
    NEGATIVE_TEST_CASES,
    MAX_NODES_FOR_OS_TEST,
    SOFTWARE_CONFIG_JSON_PATH,
    ADDITIONAL_PACKAGES_PATH_PATTERN,
    LOCAL_REPO_CONFIG_PATH,
    REPO_CONFIG_TO_PULP_POLICY,
)


# =============================================================================
# PREREQUISITE CHECKS
# =============================================================================

def is_additional_packages_enabled(host) -> bool:
    """
    Check if additional_packages is enabled in software_config.json.

    According to Omnia documentation, additional_packages must be:
    1. Listed in softwares array: {"name": "additional_packages", "arch": [...]}
    2. Configured in additional_packages section with functional groups

    Args:
        host: Testinfra host object

    Returns:
        True if additional_packages is enabled, False otherwise
    """
    data = load_container_file(host, SOFTWARE_CONFIG_JSON_PATH)
    if not data:
        return False

    # Check if additional_packages is in softwares list
    softwares = data.get("softwares", [])
    has_additional_packages = any(
        sw.get("name") == "additional_packages"
        for sw in softwares
        if isinstance(sw, dict)
    )

    if not has_additional_packages:
        return False

    # Check if additional_packages section exists with functional groups
    additional_packages_config = data.get("additional_packages", [])
    if not additional_packages_config:
        return False

    return True


# =============================================================================
# REPO CONFIG FROM SOFTWARE_CONFIG.JSON
# =============================================================================

def get_repo_config(host) -> Optional[str]:
    """
    Read repo_config value from software_config.json.

    Returns:
        "partial", "always", or None if not set
    """
    data = load_container_file(host, SOFTWARE_CONFIG_JSON_PATH)
    if not data:
        return None
    return data.get("repo_config") or None


def verify_pulp_repos_sync_policy(host, expected_repo_config: str) -> Dict[str, Any]:
    """
    Verify ALL Pulp remotes have the sync policy matching software_config.json repo_config.

    Args:
        host: Testinfra host
        expected_repo_config: Value from software_config.json ("always" or "partial")

    Returns:
        Dict with success, expected_policy, pulp_policy, test_results, total_tests
    """
    expected_pulp_policy = REPO_CONFIG_TO_PULP_POLICY.get(expected_repo_config)

    if not expected_pulp_policy:
        return {
            "success": False,
            "error": f"Unknown repo_config value: {expected_repo_config}",
            "test_results": [],
            "total_tests": 0,
            "expected_policy": expected_repo_config,
            "pulp_policy": None,
        }

    # Query Pulp remotes via pulp CLI inside omnia_core container
    cmd = run_in_container(host, "pulp rpm remote list --limit 500 2>/dev/null")

    if cmd.rc != 0:
        return {
            "success": False,
            "error": f"Failed to query Pulp remotes: {cmd.stderr or cmd.stdout}",
            "test_results": [],
            "total_tests": 0,
            "expected_policy": expected_pulp_policy,
            "pulp_policy": None,
        }

    try:
        remotes = json.loads(cmd.stdout) if cmd.stdout.strip() else []
    except json.JSONDecodeError:
        return {
            "success": False,
            "error": f"Invalid JSON from pulp remote list: {cmd.stdout[:200]}",
            "test_results": [],
            "total_tests": 0,
            "expected_policy": expected_pulp_policy,
            "pulp_policy": None,
        }

    test_results = []
    overall_success = True

    for remote in remotes:
        repo_name = remote.get("name", "unknown")
        actual_policy = remote.get("policy", "unknown")
        success = actual_policy == expected_pulp_policy
        test_results.append({
            "repo": repo_name,
            "success": success,
            "expected": expected_pulp_policy,
            "actual": actual_policy,
            "error": "" if success else f"Expected '{expected_pulp_policy}', got '{actual_policy}'"
        })
        if not success:
            overall_success = False

    if not test_results:
        return {
            "success": True,
            "error": "No Pulp remotes found",
            "test_results": [],
            "total_tests": 0,
            "expected_policy": expected_pulp_policy,
            "pulp_policy": None,
        }

    return {
        "success": overall_success,
        "test_results": test_results,
        "total_tests": len(test_results),
        "expected_policy": expected_pulp_policy,
        "pulp_policy": expected_pulp_policy,
    }


def verify_pulp_repos_ssl_config(host) -> Dict[str, Any]:  # pylint: disable=too-many-locals
    """
    Verify TLS/SSL configuration on ALL Pulp RPM remotes.

    For each remote:
    - HTTPS remotes should have tls_validation enabled
    - Remotes with custom SSL certs should have ca_cert/client_cert/client_key set

    Returns:
        Dict with success, test_results, total_tests, https_count, custom_ssl_count
    """
    cmd = run_in_container(host, "pulp rpm remote list --limit 500 2>/dev/null")

    if cmd.rc != 0:
        return {
            "success": False,
            "error": f"Failed to query Pulp remotes: {cmd.stderr or cmd.stdout}",
            "test_results": [],
            "total_tests": 0,
        }

    try:
        remotes = json.loads(cmd.stdout) if cmd.stdout.strip() else []
    except json.JSONDecodeError:
        return {
            "success": False,
            "error": f"Invalid JSON from pulp remote list: {cmd.stdout[:200]}",
            "test_results": [],
            "total_tests": 0,
        }

    if not remotes:
        return {
            "success": True,
            "error": "No Pulp RPM remotes found",
            "test_results": [],
            "total_tests": 0,
        }

    test_results = []
    overall_success = True
    https_count = 0
    custom_ssl_count = 0

    for remote in remotes:
        repo_name = remote.get("name", "unknown")
        url = remote.get("url", "")
        is_https = url.startswith("https://")
        ca_cert = remote.get("ca_cert")
        client_cert = remote.get("client_cert")
        client_key = remote.get("client_key")
        tls_validation = remote.get("tls_validation")

        has_custom_ssl = bool(ca_cert) or bool(client_cert)
        if is_https:
            https_count += 1
        if has_custom_ssl:
            custom_ssl_count += 1

        # For HTTPS remotes, tls_validation should be enabled
        if is_https:
            success = tls_validation is not False  # True or None is acceptable
            error = "" if success else "HTTPS remote has tls_validation disabled"
        else:
            success = True
            error = ""

        test_results.append({
            "repo": repo_name,
            "success": success,
            "url_scheme": "HTTPS" if is_https else "HTTP",
            "tls_validation": tls_validation,
            "has_ca_cert": bool(ca_cert),
            "has_client_cert": bool(client_cert),
            "has_client_key": bool(client_key),
            "error": error,
        })

        if not success:
            overall_success = False

    return {
        "success": overall_success,
        "test_results": test_results,
        "total_tests": len(test_results),
        "https_count": https_count,
        "custom_ssl_count": custom_ssl_count,
    }


# =============================================================================
# ADDITIONAL_PACKAGES.JSON LOADING
# =============================================================================

def _extract_rpm_names(package_objs: List) -> List[str]:
    """Extract only RPM package names from a list of package objects (skip container images)."""
    names = []
    for pkg in package_objs:
        if isinstance(pkg, dict):
            pkg_type = pkg.get("type", "rpm")
            if pkg_type == "image":
                continue  # Images cannot be checked via rpm -q
            pkg_name = pkg.get("package", "")
            if pkg_name:
                names.append(pkg_name)
        elif isinstance(pkg, str):
            names.append(pkg)
    return names


def get_additional_packages_by_fg(host, arch: str = "x86_64") -> Dict[str, List[str]]:
    """
    Load additional_packages.json and return packages per functional group.

    File location: {INPUT_BASE_PATH}/config/<arch>/<os>/<version>/additional_packages.json

    Structure::

        {
            "additional_packages": {"cluster": []},
            "service_kube_control_plane_first": {"cluster": ["kubectl", "helm"]},
            "service_kube_control_plane": {"cluster": ["kubectl", "helm"]},
            "service_kube_node": {"cluster": ["kubelet"]},
            "slurm_control_node": {"cluster": ["slurm-slurmctld", "munge"]},
            "slurm_node": {"cluster": ["slurm-slurmd", "munge"]},
            "login_node": {"cluster": ["vim", "tmux"]},
            "login_compiler_node": {"cluster": ["gcc", "make"]},
            "os": {"cluster": ["wget", "curl"]}
        }

    Args:
        host: Testinfra host object
        arch: Architecture (x86_64 or aarch64)

    Returns:
        Dict mapping FG name to list of package names
        Example: {"os": ["wget", "curl"], "slurm_control_node": ["slurm-slurmctld"]}
    """
    # Get cluster OS type and version
    cluster_os_type = get_input_value(
        host, "provision_config.yml", "cluster_os_type", "rhel"
    )
    cluster_os_version = get_input_value(
        host, "provision_config.yml", "cluster_os_version", "10.0"
    )

    # Build path to additional_packages.json using vars pattern
    packages_file = ADDITIONAL_PACKAGES_PATH_PATTERN.format(
        arch=arch, os=cluster_os_type, version=cluster_os_version
    )

    data = load_container_file(host, packages_file)
    if not data:
        return {}

    # Extract common packages (installed on ALL nodes)
    common_objs = data.get("additional_packages", {}).get("cluster", [])
    common_packages = set(_extract_rpm_names(common_objs))

    # Extract per-FG RPM packages (exclude common packages to avoid false negatives)
    fg_packages = {}
    for fg_name, fg_config in data.items():
        if fg_name == "additional_packages":
            continue  # Handled above

        if isinstance(fg_config, dict):
            package_objs = fg_config.get("cluster", [])
            if package_objs:
                package_names = [
                    p for p in _extract_rpm_names(package_objs)
                    if p not in common_packages
                ]
                if package_names:
                    fg_packages[fg_name] = package_names

    return fg_packages


# =============================================================================
# PACKAGE VERIFICATION ON NODES
# =============================================================================

def verify_packages_on_node(
    host,
    node_ip: str,
    expected_packages: List[str],
    should_exist: bool = True
) -> Dict[str, Any]:
    """
    Verify packages on a node (positive or negative test).

    Args:
        host: Testinfra host
        node_ip: Node admin IP
        expected_packages: List of package names
        should_exist: True = packages should be installed, False = should NOT be installed

    Returns:
        Dict with:
            success: bool
            error: str
            installed: List[str] - packages found
            missing: List[str] - packages not found
            unexpected: List[str] - packages that shouldn't be there (negative test)
            details: str
    """
    installed = []
    missing = []

    for package in expected_packages:
        cmd = run_on_remote_node(host, f"rpm -q {package}", node_ip)
        if cmd.rc == 0:
            installed.append(package)
        else:
            missing.append(package)

    if should_exist:
        # Positive test: all packages should be installed
        success = len(missing) == 0
        error = f"Missing {len(missing)} packages: {missing}" if missing else ""
    else:
        # Negative test: packages should NOT be installed
        success = len(installed) == 0
        error = (
            f"Unexpected {len(installed)} packages found: {installed}"
            if installed else ""
        )

    return {
        "success": success,
        "error": error,
        "installed": installed,
        "missing": missing,
        "unexpected": installed if not should_exist else [],
        "details": f"Installed: {len(installed)}, Missing: {len(missing)}"
    }


def verify_per_fg_packages_positive(
    host,
    nodes_by_fg: Dict[str, List[Dict[str, Any]]],
    fg_packages: Dict[str, List[str]]
) -> Dict[str, Any]:
    """
    Verify FG-specific packages are installed on correct FG nodes.

    Args:
        host: Testinfra host
        nodes_by_fg: Dict mapping FG name to list of node dicts (with admin_ip, hostname)
        fg_packages: Dict mapping FG name to list of package names

    Returns:
        Dict with success, test_results, details
    """
    test_results = []
    overall_success = True

    for fg_name, expected_packages in fg_packages.items():
        if fg_name == "os":
            continue  # Test separately

        # Get nodes for this FG
        fg_nodes = nodes_by_fg.get(fg_name, [])

        if not fg_nodes or not expected_packages:
            continue

        # Test first node in FG
        test_node = fg_nodes[0]
        result = verify_packages_on_node(
            host, test_node["admin_ip"], expected_packages, should_exist=True
        )

        test_results.append({
            "fg": fg_name,
            "node": test_node["hostname"],
            "packages": len(expected_packages),
            "success": result["success"],
            "error": result["error"],
            "installed": result["installed"],
            "missing": result["missing"]
        })

        if not result["success"]:
            overall_success = False

    return {
        "success": overall_success,
        "test_results": test_results,
        "total_tests": len(test_results)
    }


def verify_per_fg_packages_negative(
    host,
    nodes_by_fg: Dict[str, List[Dict[str, Any]]],
    fg_packages: Dict[str, List[str]]
) -> Dict[str, Any]:
    """
    Verify FG-specific packages are NOT on wrong FG nodes.

    Tests negative cases:
    - K8s packages should NOT be on Slurm nodes
    - Slurm packages should NOT be on K8s nodes
    - Compiler packages should NOT be on regular login nodes

    Args:
        host: Testinfra host
        nodes_by_fg: Dict mapping FG name to list of node dicts
        fg_packages: Dict mapping FG name to list of package names

    Returns:
        Dict with success, test_results, details
    """
    test_results = []
    overall_success = True

    for test_fg, wrong_fg in NEGATIVE_TEST_CASES:
        test_nodes = nodes_by_fg.get(test_fg, [])
        wrong_packages = fg_packages.get(wrong_fg, [])

        if not test_nodes or not wrong_packages:
            continue

        test_node = test_nodes[0]
        result = verify_packages_on_node(
            host, test_node["admin_ip"], wrong_packages, should_exist=False
        )

        test_results.append({
            "test_fg": test_fg,
            "wrong_fg": wrong_fg,
            "node": test_node["hostname"],
            "packages": len(wrong_packages),
            "success": result["success"],
            "unexpected": result["unexpected"]
        })

        if not result["success"]:
            overall_success = False

    return {
        "success": overall_success,
        "test_results": test_results,
        "total_tests": len(test_results)
    }


def verify_os_packages_on_all_nodes(
    host,
    all_nodes: List[Dict[str, Any]],
    os_packages: List[str]
) -> Dict[str, Any]:
    """
    Verify OS packages are installed on ALL nodes regardless of FG.

    Args:
        host: Testinfra host
        all_nodes: List of all node dicts
        os_packages: List of OS package names

    Returns:
        Dict with success, node_results, details
    """
    node_results = []
    overall_success = True

    # Test limited number of nodes to avoid long test times
    for node in all_nodes[:MAX_NODES_FOR_OS_TEST]:
        result = verify_packages_on_node(
            host, node["admin_ip"], os_packages, should_exist=True
        )

        node_results.append({
            "hostname": node["hostname"],
            "fg": node.get("functional_group", "unknown"),
            "success": result["success"],
            "missing": result["missing"],
            "installed": result["installed"]
        })

        if not result["success"]:
            overall_success = False

    return {
        "success": overall_success,
        "node_results": node_results,
        "total_nodes": len(node_results)
    }


# =============================================================================
# ADDITIONAL_REPOS CONFIGURATION
# =============================================================================

def get_additional_repos_config(host, arch: str = "x86_64") -> List[Dict[str, Any]]:
    """
    Load additional_repos configuration from local_repo_config.yml.

    File location: LOCAL_REPO_CONFIG_PATH inside the omnia_core container.

    Returns:
        List of repo dicts with url, name, sslcacert, sslclientcert, sslclientkey, policy, etc.
    """
    data = load_container_file(host, LOCAL_REPO_CONFIG_PATH)
    if not data:
        return []

    key = f"additional_repos_{arch}"
    return data.get(key, [])


def verify_repo_ssl_config(host, repo_name: str) -> Dict[str, Any]:
    """
    Verify SSL certificates are configured for a Pulp repository.

    Queries Pulp database to check if CA cert, client cert, and client key are configured.

    Args:
        host: Testinfra host
        repo_name: Repository name

    Returns:
        Dict with:
            success: bool
            error: str
            has_ca_cert: bool
            has_client_cert: bool
            has_client_key: bool
            details: str
    """
    # Query Pulp database for remote configuration
    check_cmd = f"""
podman exec pulp_api pulpcore-manager shell -c "
from pulpcore.app.models import Remote
try:
    remote = Remote.objects.get(name__contains='{repo_name}')
    print('CA_CERT:', bool(remote.ca_cert))
    print('CLIENT_CERT:', bool(remote.client_cert))
    print('CLIENT_KEY:', bool(remote.client_key))
    print('URL:', remote.url)
except Remote.DoesNotExist:
    print('NOT_FOUND')
except Exception as e:
    print('ERROR:', str(e))
"
    """

    cmd = run_on_oim(host, check_cmd)

    if "NOT_FOUND" in cmd.stdout:
        return {
            "success": False,
            "error": f"Repository {repo_name} not found in Pulp",
            "has_ca_cert": False,
            "has_client_cert": False,
            "has_client_key": False,
            "details": "Repository not configured"
        }

    if "ERROR:" in cmd.stdout:
        return {
            "success": False,
            "error": f"Error querying Pulp: {cmd.stdout}",
            "has_ca_cert": False,
            "has_client_cert": False,
            "has_client_key": False,
            "details": "Query error"
        }

    has_ca_cert = "CA_CERT: True" in cmd.stdout
    has_client_cert = "CLIENT_CERT: True" in cmd.stdout
    has_client_key = "CLIENT_KEY: True" in cmd.stdout

    return {
        "success": True,
        "error": "",
        "has_ca_cert": has_ca_cert,
        "has_client_cert": has_client_cert,
        "has_client_key": has_client_key,
        "details": (
            f"CA: {has_ca_cert}, Client Cert: {has_client_cert}, "
            f"Client Key: {has_client_key}"
        )
    }


def verify_repo_sync_policy(host, repo_name: str, expected_policy: str) -> Dict[str, Any]:
    """
    Verify repository sync policy (always vs partial).

    Args:
        host: Testinfra host
        repo_name: Repository name
        expected_policy: Expected policy ("always" or "partial")

    Returns:
        Dict with:
            success: bool
            error: str
            actual_policy: Optional[str]
            expected_policy: str
            details: str
    """
    check_cmd = f"""
podman exec pulp_api pulpcore-manager shell -c "
from pulpcore.app.models import Remote
try:
    remote = Remote.objects.get(name__contains='{repo_name}')
    print('POLICY:', remote.policy)
except Remote.DoesNotExist:
    print('NOT_FOUND')
except Exception as e:
    print('ERROR:', str(e))
"
    """

    cmd = run_on_oim(host, check_cmd)

    if "NOT_FOUND" in cmd.stdout:
        return {
            "success": False,
            "error": f"Repository {repo_name} not found",
            "actual_policy": None,
            "expected_policy": expected_policy,
            "details": "Repository not configured"
        }

    if "ERROR:" in cmd.stdout:
        return {
            "success": False,
            "error": f"Error querying Pulp: {cmd.stdout}",
            "actual_policy": None,
            "expected_policy": expected_policy,
            "details": "Query error"
        }

    actual_policy = None
    for line in cmd.stdout.split('\n'):
        if line.startswith("POLICY:"):
            actual_policy = line.split(":", 1)[1].strip()

    success = actual_policy == expected_policy
    error = (
        f"Expected policy '{expected_policy}', got '{actual_policy}'"
        if not success else ""
    )

    return {
        "success": success,
        "error": error,
        "actual_policy": actual_policy,
        "expected_policy": expected_policy,
        "details": f"Policy: {actual_policy}"
    }


def verify_additional_repos_ssl(
    host,
    repos: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Verify SSL configuration for all additional_repos with SSL.

    Args:
        host: Testinfra host
        repos: List of repo configs from local_repo_config.yml

    Returns:
        Dict with success, test_results, details
    """
    # Filter repos with SSL
    ssl_repos = [r for r in repos if r.get("sslcacert") or r.get("sslclientcert")]

    if not ssl_repos:
        return {
            "success": True,
            "error": "No SSL-enabled repos configured",
            "test_results": [],
            "total_tests": 0
        }

    test_results = []
    overall_success = True

    for repo in ssl_repos:
        repo_name = repo["name"]
        result = verify_repo_ssl_config(host, repo_name)

        expected_ca = bool(repo.get("sslcacert"))
        expected_client = bool(repo.get("sslclientcert"))

        ssl_correct = (
            (not expected_ca or result["has_ca_cert"])
            and (not expected_client or (result["has_client_cert"] and result["has_client_key"]))
        )

        test_results.append({
            "repo": repo_name,
            "success": ssl_correct,
            "has_ca": result["has_ca_cert"],
            "has_client": result["has_client_cert"],
            "expected_ca": expected_ca,
            "expected_client": expected_client,
            "error": result.get("error", "")
        })

        if not ssl_correct:
            overall_success = False

    return {
        "success": overall_success,
        "test_results": test_results,
        "total_tests": len(test_results)
    }


def verify_additional_repos_sync_policy(
    host,
    repos: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Verify sync policy for all additional_repos with explicit policy.

    Args:
        host: Testinfra host
        repos: List of repo configs from local_repo_config.yml

    Returns:
        Dict with success, test_results, details
    """
    # Filter repos with explicit policy
    policy_repos = [r for r in repos if r.get("policy")]

    if not policy_repos:
        return {
            "success": True,
            "error": "No repos with explicit policy configured",
            "test_results": [],
            "total_tests": 0
        }

    test_results = []
    overall_success = True

    for repo in policy_repos:
        repo_name = repo["name"]
        expected_policy = repo["policy"]

        result = verify_repo_sync_policy(host, repo_name, expected_policy)

        test_results.append({
            "repo": repo_name,
            "success": result["success"],
            "expected": expected_policy,
            "actual": result["actual_policy"],
            "error": result.get("error", "")
        })

        if not result["success"]:
            overall_success = False

    return {
        "success": overall_success,
        "test_results": test_results,
        "total_tests": len(test_results)
    }
