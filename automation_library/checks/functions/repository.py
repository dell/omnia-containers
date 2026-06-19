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

"""Repository management functions for OIM prerequisite checks."""

import re
from typing import Dict

from ...core import log as _log, OMNIA_GIT_RAW_BASE_URL
from ..messages.oim_prereq_msgs import OIM_PREREQ_MSGS
from ..vars.oim_prereq_vars import OIM_PREREQ_VARS, OMNIA_TEST_CONFIG_PATH
from .system import run_command, run_shell


def check_rhel_repo() -> Dict:
    """Check if any RHEL repository is configured."""
    _log("Checking RHEL repositories...", "INFO")
    rc, stdout, _ = run_shell("dnf repolist 2>/dev/null")

    if rc == 0 and stdout:
        # Look for common RHEL repo patterns
        repos = []
        for line in stdout.split("\n"):
            line_lower = line.lower()
            if any(x in line_lower for x in ["baseos", "appstream", "rhel", "codeready", "powertools"]):
                repos.append(line.strip())

        if repos:
            return {
                "found": True,
                "repos": repos,
                "message": OIM_PREREQ_MSGS["repo_found"].format(repo=repos[0])
            }

    return {
        "found": False,
        "repos": [],
        "message": "No RHEL repository configured",
        "details": OIM_PREREQ_MSGS["repo_not_found_instruction"]
    }


def check_git() -> Dict:
    """Check if Git is installed."""
    _log("Checking Git installation...", "INFO")
    rc, stdout, _ = run_command(["git", "--version"])

    if rc == 0:
        version_match = re.search(r"(\d+\.\d+\.?\d*)", stdout)
        version = version_match.group(1) if version_match else stdout
        return {
            "installed": True,
            "version": version,
            "message": OIM_PREREQ_MSGS["git_installed"].format(version=version)
        }

    return {
        "installed": False,
        "version": None,
        "message": OIM_PREREQ_MSGS["git_not_installed"]
    }


def install_git() -> Dict:
    """Install Git from RHEL repo if available."""
    # First check if repo is available
    repo_check = check_rhel_repo()
    if not repo_check["found"]:
        return {
            "success": False,
            "message": OIM_PREREQ_MSGS["git_repo_not_found"]
        }

    # Install git
    git_package = OIM_PREREQ_VARS["git_package"]
    rc, _, stderr = run_command(["dnf", "install", "-y", git_package], timeout=120)

    if rc == 0:
        return {
            "success": True,
            "message": OIM_PREREQ_MSGS["git_install_success"]
        }

    return {
        "success": False,
        "message": "Git installation FAILED",
        "error": stderr,
        "details": OIM_PREREQ_MSGS["git_install_instruction"].format(error=stderr, config_path=OMNIA_TEST_CONFIG_PATH)
    }


def ensure_git_installed() -> Dict:
    """Check Git, install if not present."""
    git_check = check_git()

    if git_check["installed"]:
        return git_check

    # Try to install
    install_result = install_git()
    if install_result["success"]:
        # Verify installation
        return check_git()

    return {
        "installed": False,
        "version": None,
        "message": install_result.get("message", "Git installation failed"),
        "details": install_result.get("details", OIM_PREREQ_MSGS["git_install_instruction"].format(error="Unknown error", config_path=OMNIA_TEST_CONFIG_PATH))
    }


def clone_omnia_repo() -> Dict:
    """Clone Omnia artifactory repository from configured URL."""
    _log("Checking Omnia artifactory repository...", "INFO")
    repo_url = OIM_PREREQ_VARS["omnia_repo_url"]
    branch = OIM_PREREQ_VARS["artifactory_branch"]
    clone_path = OIM_PREREQ_VARS["omnia_clone_path"]

    if not repo_url:
        return {
            "passed": False,
            "message": "Omnia repository URL not configured",
            "details": OIM_PREREQ_MSGS["omnia_repo_not_configured_instruction"].format(config_path=OMNIA_TEST_CONFIG_PATH)
        }

    _log(f"Repo URL: {repo_url}", "DEBUG")
    _log(f"Branch: {branch}", "DEBUG")
    _log(f"Clone path: {clone_path}", "DEBUG")

    # Always delete existing folder and re-clone fresh
    rc, _, _ = run_shell(f"test -d {clone_path}")
    if rc == 0:
        _log(f"Removing existing directory {clone_path}...", "INFO")
        # Kill any running processes that might lock the directory
        run_shell(f"pkill -9 -f build_images 2>/dev/null; pkill -9 -f 'git clone' 2>/dev/null; sleep 1")
        # Force remove
        run_shell(f"rm -rf {clone_path} 2>/dev/null")

    # Clone fresh - create parent directory on remote server
    parent_dir = "/".join(clone_path.split("/")[:-1])
    run_shell(f"mkdir -p {parent_dir}")

    # Clone repository
    _log(f"Cloning repository to {clone_path}...", "INFO")
    rc, _, stderr = run_command(["git", "clone", "-b", branch, repo_url, clone_path], timeout=300)

    if rc != 0:
        return {
            "passed": False,
            "message": f"Failed to clone Omnia artifactory",
            "details": OIM_PREREQ_MSGS["omnia_clone_instruction"].format(
                repo_url=repo_url, clone_path=clone_path, error=stderr, config_path=OMNIA_TEST_CONFIG_PATH
            )
        }

    return {
        "passed": True,
        "message": f"Omnia artifactory cloned to {clone_path}",
        "details": f"Branch: {branch}"
    }


def build_container_images() -> Dict:
    """Build core container image using build_images.sh script."""
    _log("Building core container image...", "INFO")

    omnia_branch = OIM_PREREQ_VARS.get("omnia_branch", "")
    core_tag = OIM_PREREQ_VARS.get("core_tag", "")
    clone_path = OIM_PREREQ_VARS["omnia_clone_path"]

    if not omnia_branch:
        return {
            "passed": False,
            "message": "omnia_branch not configured",
            "details": OIM_PREREQ_MSGS["omnia_branch_not_configured"].format(config_path=OMNIA_TEST_CONFIG_PATH)
        }

    # Check if clone path exists
    rc, _, _ = run_shell(f"test -d {clone_path}")
    if rc != 0:
        return {
            "passed": False,
            "message": "Omnia artifactory not cloned",
            "details": OIM_PREREQ_MSGS["clone_path_not_found"].format(clone_path=clone_path, config_path=OMNIA_TEST_CONFIG_PATH)
        }

    # Check if build_images.sh exists
    build_script = f"{clone_path}/build_images.sh"
    rc, _, _ = run_shell(f"test -f {build_script}")
    if rc != 0:
        return {
            "passed": False,
            "message": "build_images.sh not found",
            "details": OIM_PREREQ_MSGS["build_script_not_found"].format(script_path=build_script)
        }

    # Make script executable
    run_command(["chmod", "+x", build_script])

    # Build core container image
    # Usage: ./build_images.sh core core_tag=1.1 omnia_branch=pub/q1_dev
    build_args = "core"
    if core_tag:
        build_args += f" core_tag={core_tag}"
    build_args += f" omnia_branch={omnia_branch}"

    _log(f"Running: ./build_images.sh {build_args}", "INFO")
    rc, _, stderr = run_shell(f"cd {clone_path} && ./build_images.sh {build_args}", timeout=1800)

    if rc == 0:
        return {
            "passed": True,
            "message": "Core container image built successfully",
            "details": f"Omnia Branch: {omnia_branch}\nCore Tag: {core_tag or 'default'}"
        }

    return {
        "passed": False,
        "message": "Failed to build core container image",
        "details": OIM_PREREQ_MSGS["container_build_instruction"].format(
            core_tag=core_tag or "default", omnia_branch=omnia_branch, exit_code=rc
        )
    }


def download_omnia_sh() -> Dict:
    """Download omnia.sh from configured branch/tag."""
    _log("Downloading omnia.sh...", "INFO")

    omnia_branch = OIM_PREREQ_VARS.get("omnia_branch", "")
    clone_path = OIM_PREREQ_VARS["omnia_clone_path"]

    if not omnia_branch:
        return {
            "passed": False,
            "message": "omnia_branch not configured",
            "details": OIM_PREREQ_MSGS["omnia_sh_branch_not_configured"].format(config_path=OMNIA_TEST_CONFIG_PATH)
        }

    # Create directory if it doesn't exist
    rc, _, stderr = run_shell(f"mkdir -p {clone_path}")
    if rc != 0:
        return {
            "passed": False,
            "message": OIM_PREREQ_MSGS["omnia_sh_dir_create_fail"].format(clone_path=clone_path),
            "details": f"Error: {stderr}"
        }

    # Try to download from branch first, then tag
    branch_url = f"{OMNIA_GIT_RAW_BASE_URL}/{omnia_branch}/omnia.sh"
    tag_url = f"{OMNIA_GIT_RAW_BASE_URL}/refs/tags/{omnia_branch}/omnia.sh"

    # Try branch URL
    rc, _, _ = run_command(["curl", "-f", "-o", f"{clone_path}/omnia.sh", branch_url], timeout=60)
    if rc == 0:
        _log(f"omnia.sh downloaded from branch: {omnia_branch}", "OK")
        return {
            "passed": True,
            "message": OIM_PREREQ_MSGS["omnia_sh_download_success"].format(ref_type="branch", omnia_branch=omnia_branch),
            "details": f"URL: {branch_url}\nLocation: {clone_path}/omnia.sh"
        }

    # Try tag URL
    rc, _, _ = run_command(["curl", "-f", "-o", f"{clone_path}/omnia.sh", tag_url], timeout=60)
    if rc == 0:
        _log(f"omnia.sh downloaded from tag: {omnia_branch}", "OK")
        return {
            "passed": True,
            "message": OIM_PREREQ_MSGS["omnia_sh_download_success"].format(ref_type="tag", omnia_branch=omnia_branch),
            "details": f"URL: {tag_url}\nLocation: {clone_path}/omnia.sh"
        }

    # Both URLs failed
    return {
        "passed": False,
        "message": OIM_PREREQ_MSGS["omnia_sh_download_fail"],
        "details": OIM_PREREQ_MSGS["omnia_sh_download_instruction"].format(
            omnia_branch=omnia_branch, branch_url=branch_url, tag_url=tag_url
        )
    }
