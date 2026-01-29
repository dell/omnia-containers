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

"""
Local Repo - Configuration Variables.

This module loads all configuration for local_repo automation.
Reads from user_config.yml (via OIM_PREREQ_VARS) and input/local_repo_config.yml.

Usage:
    from automation_library.local_repo.vars.local_repo_vars import LOCAL_REPO_VARS

Author: Dell Technologies
"""

import os
from typing import Dict, Any, List

import yaml

from ...checks.vars.oim_prereq_vars import OIM_PREREQ_VARS


def _get_project_root() -> str:
    """Get the project root directory."""
    return os.path.dirname(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    )


def _load_local_repo_config() -> Dict[str, Any]:
    """Load local_repo_config.yml from input directory."""
    config_path = os.path.join(_get_project_root(), "input", "local_repo_config.yml")
    if os.path.exists(config_path):
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                return yaml.safe_load(f) or {}
        except (IOError, yaml.YAMLError):
            return {}
    return {}


def _extract_repo_urls(cfg: Dict[str, Any]) -> List[str]:
    """Extract repo URLs from local_repo_config.yml structure."""
    keys = [
        "user_repo_url_x86_64",
        "user_repo_url_aarch64",
        "rhel_os_url_x86_64",
        "rhel_os_url_aarch64",
        "omnia_repo_url_rhel_x86_64",
        "omnia_repo_url_rhel_aarch64",
    ]

    urls: List[str] = []
    for k in keys:
        items = cfg.get(k, []) or []
        if not isinstance(items, list):
            continue
        for item in items:
            if isinstance(item, dict):
                u = item.get("url")
                if isinstance(u, str) and u.strip():
                    urls.append(u.strip())
            elif isinstance(item, str) and item.strip():
                urls.append(item.strip())
    return urls


# =============================================================================
# LOCAL_REPO VARIABLES
# =============================================================================

_LOCAL_REPO_CONFIG = _load_local_repo_config()

LOCAL_REPO_VARS: Dict[str, Any] = {
    # Connection (from user_config.yml)
    "oim_server_ip": OIM_PREREQ_VARS.get("oim_server_ip", ""),
    "oim_ssh_user": OIM_PREREQ_VARS.get("oim_ssh_user", "root"),
    "oim_ssh_password": OIM_PREREQ_VARS.get("oim_ssh_password", ""),
    "oim_ssh_port": OIM_PREREQ_VARS.get("oim_ssh_port", 22),

    # Containers
    "omnia_core_container": "omnia_core",
    "pulp_container": "pulp",

    # Paths
    "input_dir": os.path.join(_get_project_root(), "input"),
    "oim_input_dir": "/opt/omnia/input/project_default",
    "local_repo_playbook": "/omnia/local_repo/local_repo.yml",

    # Repo URLs (from input/local_repo_config.yml)
    "repo_urls": _extract_repo_urls(_LOCAL_REPO_CONFIG),

    # Status file search root (single path)
    "status_log_path": "/opt/omnia/log/local_repo",

    # Pulp content server
    "pulp_https_port": 2225,
    "pulp_http_port": 80,
    "pulp_content_base_url": "/pulp/content",

    # NFS mount paths inside Pulp container
    "nfs_mounts": [
        {"path": "/var/lib/pulp", "description": "Pulp storage"},
        {"path": "/var/lib/pgsql", "description": "PostgreSQL data"},
        {"path": "/var/log/pulp", "description": "Pulp logs"},
    ],

    # Pulp storage path for permission checks
    "pulp_storage_path": "/var/lib/pulp",

    # Common repo names that get arch prefix in Pulp
    "arch_prefixed_repos": {
        "baseos", "appstream", "epel", "kubernetes",
        "cri-o", "docker-ce", "codeready-builder",
    },

    # Timeouts
    "pulp_api_timeout_seconds": 300,
    "repo_url_timeout_seconds": 10,
    "curl_connect_timeout": 10,

    # Execution control
    "skip_on_failure": OIM_PREREQ_VARS.get("skip_on_failure", False),
}


def get_local_repo_config_path() -> str:
    """Get the path to local_repo_config.yml."""
    return os.path.join(_get_project_root(), "input", "local_repo_config.yml")


def get_repo_urls() -> List[str]:
    """Get repository URLs from local_repo_config.yml."""
    return LOCAL_REPO_VARS.get("repo_urls", []) or []
