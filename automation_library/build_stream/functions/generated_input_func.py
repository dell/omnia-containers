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
Build Stream - Generated Input Verification Functions.

Compares generated input config files (inside omnia_core container at
/opt/omnia/input/project_default/config/) against source files from
the cloned Omnia repository to verify that generate_input produced
correct output.
"""

import json
import re
from typing import Dict, Any, List

from automation_library.core import (
    run_on_oim,
    run_in_container,
    INPUT_BASE_PATH,
    SOFTWARE_CONFIG_PATH,
)

# =============================================================================
# CONSTANTS
# =============================================================================

OMNIA_REPO_URL: str = "https://github.com/dell/omnia.git"
DEFAULT_CLONE_PATH: str = "/tmp/omnia_input_verify"
GENERATED_CONFIG_BASE: str = f"{INPUT_BASE_PATH}/config"
SOURCE_CONFIG_BASE: str = "input/config"

# Jinja2 template pattern
_JINJA2_PATTERN = re.compile(r"\{\{.*?\}\}")


# =============================================================================
# BRANCH DETECTION
# =============================================================================

def get_omnia_branch(host=None) -> str:
    """
    Get the Omnia branch to clone for comparison.

    Reads omnia_branch from omnia_test_config.yml.
    If omnia_branch is not set, returns empty string (caller must fail).

    Args:
        host: Testinfra host object (unused, kept for API consistency).

    Returns:
        Branch name string, or empty string if not configured.
    """
    import yaml
    import os

    config_path = os.path.join(
        os.path.dirname(
            os.path.dirname(
                os.path.dirname(os.path.dirname(__file__))
            )
        ),
        "omnia_test_config.yml",
    )

    try:
        with open(config_path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f) or {}
        return config.get("omnia_branch", "") or ""
    except (OSError, yaml.YAMLError):
        return ""


# =============================================================================
# REPO CLONE / CLEANUP
# =============================================================================

def clone_omnia_repo(
    host, clone_path: str = DEFAULT_CLONE_PATH
) -> Dict[str, Any]:
    """
    Clone the Omnia repository to the specified path.

    Uses --depth 1 for speed. Removes any existing clone first.
    Fails if omnia_branch is not configured in omnia_test_config.yml.

    Args:
        host: Testinfra host object.
        clone_path: Path to clone into.

    Returns:
        Dict with 'success', 'branch', 'clone_path', 'error'.
    """
    result = {
        "success": False,
        "branch": "",
        "clone_path": clone_path,
        "error": "",
    }

    branch = get_omnia_branch(host)
    if not branch:
        result["error"] = (
            "omnia_branch is not set in omnia_test_config.yml. "
            "Cannot clone Omnia repository for comparison."
        )
        return result

    result["branch"] = branch

    run_on_oim(host, f"rm -rf {clone_path}")

    clone_cmd = run_on_oim(
        host,
        f"git clone --depth 1 -b {branch} "
        f"{OMNIA_REPO_URL} {clone_path} 2>&1"
    )
    if clone_cmd.rc != 0:
        out = clone_cmd.stdout.strip()[:300] if clone_cmd.stdout else ""
        result["error"] = (
            f"Failed to clone branch '{branch}': {out}"
        )
        return result

    result["success"] = True
    return result


def cleanup_omnia_clone(
    host, clone_path: str = DEFAULT_CLONE_PATH
) -> None:
    """Remove the cloned Omnia repository."""
    run_on_oim(host, f"rm -rf {clone_path}")


# =============================================================================
# SOFTWARE CONFIG READING
# =============================================================================

def get_software_config(host) -> Dict[str, Any]:
    """
    Read software_config.json from the omnia_core container.

    Returns:
        Dict with 'success', 'os_type', 'os_version', 'softwares', 'error'.
    """
    result = {
        "success": False,
        "os_type": "",
        "os_version": "",
        "softwares": [],
        "error": "",
    }

    cmd = run_in_container(
        host, f"cat {SOFTWARE_CONFIG_PATH} 2>/dev/null"
    )
    if cmd.rc != 0 or not cmd.stdout.strip():
        result["error"] = (
            f"Failed to read {SOFTWARE_CONFIG_PATH} from omnia_core"
        )
        return result

    try:
        config = json.loads(cmd.stdout)
    except json.JSONDecodeError as exc:
        result["error"] = f"Invalid JSON in software_config.json: {exc}"
        return result

    result["os_type"] = config.get("cluster_os_type", "")
    result["os_version"] = config.get("cluster_os_version", "")
    result["softwares"] = config.get("softwares", [])
    result["success"] = True
    return result


# =============================================================================
# FILE DISCOVERY
# =============================================================================

def _find_config_file(
    host, base_path: str, arch: str, os_type: str,
    os_version: str, software_name: str, is_container: bool = False,
) -> str:
    """
    Find the config JSON file for a software in the config directory.

    Tries exact match first, then prefix match for versioned files
    (e.g., service_k8s_v1.35.1.json for software name 'service_k8s').

    Returns:
        Full path to the JSON file, or empty string if not found.
    """
    config_dir = f"{base_path}/{arch}/{os_type}/{os_version}"

    if is_container:
        ls_cmd = run_in_container(
            host, f"ls {config_dir}/ 2>/dev/null"
        )
    else:
        ls_cmd = run_on_oim(
            host, f"ls {config_dir}/ 2>/dev/null"
        )

    if ls_cmd.rc != 0 or not ls_cmd.stdout.strip():
        return ""

    files = [
        f.strip() for f in ls_cmd.stdout.strip().split("\n")
        if f.strip().endswith(".json")
    ]

    exact = f"{software_name}.json"
    if exact in files:
        return f"{config_dir}/{exact}"

    for fname in files:
        if fname.startswith(f"{software_name}_"):
            return f"{config_dir}/{fname}"

    return ""


# =============================================================================
# PACKAGE KEY GENERATION
# =============================================================================

def _pkg_key(pkg: dict) -> str:
    """
    Generate a unique key for a package entry.

    Uses package name + tag (if present) to handle duplicate package
    names with different tags (e.g., two docker.io/victoriametrics/operator
    entries with different tags).
    """
    name = pkg.get("package", "")
    tag = pkg.get("tag", "")
    if tag:
        return f"{name}:{tag}"
    return name


def _build_pkg_map(pkg_list: List[Dict]) -> Dict[str, Dict]:
    """
    Build a map of packages keyed by _pkg_key.

    Returns:
        Dict mapping pkg_key -> package dict.
    """
    result = {}
    for pkg in pkg_list:
        key = _pkg_key(pkg)
        if key:
            result[key] = pkg
    return result


# =============================================================================
# JSON COMPARISON
# =============================================================================

def _has_jinja2(value: str) -> bool:
    """Check if a string contains Jinja2 template expressions."""
    if not isinstance(value, str):
        return False
    return bool(_JINJA2_PATTERN.search(value))


def _extract_packages(data: dict) -> Dict[str, Dict[str, List[Dict]]]:
    """
    Extract packages from a software config JSON grouped by role.

    Returns:
        Dict: {role_name: {group_name: [package_dicts]}}
    """
    result = {}
    for key, value in data.items():
        if isinstance(value, dict):
            result[key] = {}
            for group_name, pkg_list in value.items():
                if isinstance(pkg_list, list):
                    result[key][group_name] = pkg_list
    return result


def compare_software_json(
    source_data: dict, generated_data: dict,
    software_name: str = "",  # pylint: disable=unused-argument
) -> Dict[str, Any]:
    """
    Compare source and generated JSON for a software package.

    Checks:
      1. Every role in source exists in generated
      2. Every package in source exists in generated (by name+tag)
      3. Package attributes (type, repo_name, url, version) match
      4. Extra packages in generated not in source are reported

    Jinja2 template values in the source are skipped for exact comparison.
    Packages are matched by name+tag to handle duplicate package names.

    Args:
        source_data: Parsed JSON from cloned repo.
        generated_data: Parsed JSON from generated input.
        software_name: Name of the software being compared.

    Returns:
        Dict with 'success', 'issues', 'details'.
    """
    result = {
        "success": True,
        "issues": [],
        "details": "",
    }

    source_roles = _extract_packages(source_data)
    generated_roles = _extract_packages(generated_data)
    lines = []

    for role_name, source_groups in source_roles.items():
        if role_name not in generated_roles:
            result["success"] = False
            lines.append(
                f"    MISSING ROLE: '{role_name}'"
            )
            lines.append(
                f"      expected: role '{role_name}' with packages"
            )
            lines.append(
                "      got: none"
            )
            result["issues"].append(
                f"role '{role_name}' missing in generated"
            )
            continue

        gen_groups = generated_roles[role_name]

        for group_name, source_pkgs in source_groups.items():
            if group_name not in gen_groups:
                result["success"] = False
                lines.append(
                    f"    MISSING GROUP: '{role_name}/{group_name}'"
                )
                lines.append(
                    f"      expected: group '{group_name}' with "
                    f"{len(source_pkgs)} packages"
                )
                lines.append(
                    "      got: none"
                )
                result["issues"].append(
                    f"group '{role_name}/{group_name}' missing"
                )
                continue

            gen_pkgs = gen_groups[group_name]
            src_map = _build_pkg_map(source_pkgs)
            gen_map = _build_pkg_map(gen_pkgs)

            for src_key, src_pkg in src_map.items():
                pkg_name = src_pkg.get("package", "")
                if not pkg_name:
                    continue

                if src_key not in gen_map:
                    result["success"] = False
                    tag = src_pkg.get("tag", "")
                    display = (
                        f"{pkg_name} (tag: {tag})"
                        if tag else pkg_name
                    )
                    lines.append(
                        f"    MISSING PACKAGE: "
                        f"'{role_name}/{group_name}'"
                    )
                    lines.append(
                        f"      expected: {display}"
                    )
                    lines.append(
                        "      got: none"
                    )
                    result["issues"].append(
                        f"missing '{display}' in "
                        f"'{role_name}/{group_name}'"
                    )
                    continue

                gen_pkg = gen_map[src_key]
                _compare_pkg_attrs(
                    src_pkg, gen_pkg, pkg_name,
                    f"{role_name}/{group_name}",
                    result, lines,
                )

            for gen_key, gen_pkg in gen_map.items():
                if gen_key not in src_map:
                    pkg_name = gen_pkg.get("package", "")
                    tag = gen_pkg.get("tag", "")
                    display = (
                        f"{pkg_name} (tag: {tag})"
                        if tag else pkg_name
                    )
                    result["success"] = False
                    lines.append(
                        f"    EXTRA PACKAGE: "
                        f"'{role_name}/{group_name}'"
                    )
                    lines.append(
                        "      expected: none"
                    )
                    lines.append(
                        f"      got: {display}"
                    )
                    result["issues"].append(
                        f"extra '{display}' in "
                        f"'{role_name}/{group_name}'"
                    )

    for role_name in generated_roles:
        if role_name not in source_roles:
            result["success"] = False
            lines.append(
                f"    EXTRA ROLE: '{role_name}'"
            )
            lines.append(
                "      expected: none"
            )
            lines.append(
                f"      got: role '{role_name}' with packages"
            )
            result["issues"].append(
                f"extra role '{role_name}' in generated"
            )

    result["details"] = "\n".join(lines) if lines else ""
    return result


def _compare_pkg_attrs(
    src_pkg: dict, gen_pkg: dict, pkg_name: str,
    context: str, result: dict, lines: list,
) -> None:
    """Compare individual package attributes between source and generated."""
    compare_keys = ["type", "repo_name", "url", "version"]

    for key in compare_keys:
        src_val = src_pkg.get(key)
        gen_val = gen_pkg.get(key)

        if src_val is None:
            continue

        if _has_jinja2(str(src_val)):
            continue

        if gen_val is None:
            result["success"] = False
            lines.append(
                f"    VERSION MISMATCH: '{context}' / {pkg_name}"
            )
            lines.append(
                f"      expected {key}: {src_val}"
            )
            lines.append(
                f"      got {key}: none"
            )
            result["issues"].append(
                f"'{context}': {pkg_name} '{key}' "
                f"expected='{src_val}' got=none"
            )
        elif str(src_val) != str(gen_val):
            result["success"] = False
            lines.append(
                f"    VERSION MISMATCH: '{context}' / {pkg_name}"
            )
            lines.append(
                f"      expected {key}: {src_val}"
            )
            lines.append(
                f"      got {key}: {gen_val}"
            )
            result["issues"].append(
                f"'{context}': {pkg_name} '{key}' "
                f"expected='{src_val}' got='{gen_val}'"
            )


# =============================================================================
# MAIN VERIFICATION
# =============================================================================

def verify_generated_inputs(
    host, clone_path: str = DEFAULT_CLONE_PATH,
) -> Dict[str, Any]:
    """
    Verify all generated input config files match the Omnia source.

    For each software in software_config.json, for each architecture,
    reads the generated JSON from omnia_core container and compares it
    with the source JSON from the cloned Omnia repository.

    Output is organized: cluster-level packages first, then role-level.
    Each mismatch shows expected vs got on separate lines.

    Args:
        host: Testinfra host object.
        clone_path: Path where Omnia repo is cloned.

    Returns:
        Dict with 'success', 'results' (per-software), 'summary', 'error'.
    """
    result = {
        "success": True,
        "results": [],
        "summary": "",
        "error": "",
    }

    sw_config = get_software_config(host)
    if not sw_config["success"]:
        result["success"] = False
        result["error"] = sw_config["error"]
        return result

    os_type = sw_config["os_type"]
    os_version = sw_config["os_version"]
    softwares = sw_config["softwares"]

    if not os_type or not os_version:
        result["success"] = False
        result["error"] = (
            "cluster_os_type or cluster_os_version not set in "
            "software_config.json"
        )
        return result

    source_base = f"{clone_path}/{SOURCE_CONFIG_BASE}"
    total = 0
    passed = 0
    failed = 0
    skipped = 0
    all_lines = []

    for software in softwares:
        sw_name = software.get("name", "")
        archs = software.get("arch", [])
        if not sw_name or not archs:
            continue

        for arch in archs:
            total += 1
            entry = _verify_single_software(
                host, sw_name, arch, os_type, os_version,
                source_base,
            )
            result["results"].append(entry)

            if entry.get("skipped"):
                skipped += 1
                all_lines.append(
                    f"  [SKIP] {sw_name} ({arch}): "
                    f"{entry['details']}"
                )
            elif entry["success"]:
                passed += 1
                all_lines.append(f"  [OK] {sw_name} ({arch})")
            else:
                failed += 1
                result["success"] = False
                all_lines.append(f"  [FAIL] {sw_name} ({arch}):")
                if entry["details"]:
                    all_lines.append(entry["details"])

    result["summary"] = (
        f"Generated input verification: "
        f"{passed} passed, {failed} failed, {skipped} skipped "
        f"(total: {total})\n"
        + "\n".join(all_lines)
    )
    return result


def _verify_single_software(
    host, sw_name: str, arch: str, os_type: str,
    os_version: str, source_base: str,
) -> Dict[str, Any]:
    """
    Verify a single software's generated config against source.

    Returns:
        Dict with 'software', 'arch', 'success', 'skipped', 'details'.
    """
    entry = {
        "software": sw_name,
        "arch": arch,
        "success": False,
        "skipped": False,
        "details": "",
    }

    gen_file = _find_config_file(
        host, GENERATED_CONFIG_BASE, arch, os_type,
        os_version, sw_name, is_container=True,
    )
    if not gen_file:
        entry["skipped"] = True
        entry["details"] = "no generated config file"
        return entry

    src_file = _find_config_file(
        host, source_base, arch, os_type,
        os_version, sw_name, is_container=False,
    )
    if not src_file:
        entry["skipped"] = True
        entry["details"] = "no source file in cloned repo"
        return entry

    gen_cmd = run_in_container(
        host, f"cat {gen_file} 2>/dev/null"
    )
    src_cmd = run_on_oim(
        host, f"cat {src_file} 2>/dev/null"
    )

    if gen_cmd.rc != 0 or not gen_cmd.stdout.strip():
        entry["details"] = f"cannot read generated file {gen_file}"
        return entry

    if src_cmd.rc != 0 or not src_cmd.stdout.strip():
        entry["details"] = f"cannot read source file {src_file}"
        return entry

    try:
        gen_data = json.loads(gen_cmd.stdout)
        src_data = json.loads(src_cmd.stdout)
    except json.JSONDecodeError as exc:
        entry["details"] = f"JSON parse error: {exc}"
        return entry

    cmp = compare_software_json(src_data, gen_data, sw_name)
    entry["success"] = cmp["success"]
    entry["details"] = cmp["details"]
    return entry
