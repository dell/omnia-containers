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

"""Local Repo - Messages and Test Variables.

This module contains all messages, status strings, error instructions,
and test variables for the local_repo automation.

Author: Dell Technologies
"""

from ..vars.local_repo_vars import OMNIA_CORE_CONTAINER, PULP_CONTAINER


# =============================================================================
# TEST VARIABLES (for molecule/pytest tests)
# =============================================================================

TEST_VARS = {
    "pulp_container": PULP_CONTAINER,
    "omnia_core_container": OMNIA_CORE_CONTAINER,
}


TEST_NAMES = {
    "pulp_container_running": "Verify pulp container is running",
    "pulp_cli_repo_list": "Verify pulp CLI works (pulp rpm repository list)",
    "pulp_api_status": "Verify Pulp API status is healthy",
    "pulp_no_failed_tasks": "Verify no failed tasks in Pulp",
    "software_download_status": "Verify software download status (software.csv)",
    "per_software_package_status": "Verify per-software package status (status.csv)",
    "pulp_repositories_synced": "Verify RPM repositories are synced",
    "pulp_distributions_published": "Verify RPM distributions are published",
    "container_repos_synced": "Verify container repositories are synced",
    "file_repos_synced": "Verify file repositories are synced",
    "pulp_content_accessible": "Verify Pulp RPM content is accessible via HTTP",
    "software_packages_in_pulp": "Verify software_config packages exist in Pulp",
}


TEST_LOG_MSGS = {
    # Container
    "container_running": "Container {container} is running",
    "container_not_running": "Container {container} is NOT running",
    # Pulp CLI
    "pulp_cli_ok": "pulp rpm repository list succeeded",
    "pulp_cli_fail": "pulp rpm repository list failed",
    # Pulp API
    "pulp_api_healthy": "Pulp API status is healthy",
    "pulp_api_unhealthy": "Pulp API status check failed",
    # Failed tasks
    "pulp_no_failed_tasks": "No failed tasks in Pulp",
    "pulp_has_failed_tasks": "Failed tasks found in Pulp",
    # Software download status
    "sw_download_ok": "All softwares downloaded successfully",
    "sw_download_failed": "Some softwares failed to download",
    # Per-software package status
    "pkg_status_ok": "All packages across all softwares succeeded",
    "pkg_status_failed": "Some packages failed",
    # RPM repos
    "pulp_repos_synced": "All RPM repositories are synced",
    "pulp_repos_not_synced": "Some RPM repositories are not synced",
    # RPM distributions
    "pulp_distributions_ok": "All RPM distributions are published",
    "pulp_distributions_missing": "Some RPM distributions are not published",
    # Container repos
    "container_repos_synced": "All container repositories are synced",
    "container_repos_not_synced": "Some container repositories are not synced",
    # File repos
    "file_repos_synced": "All file repositories are synced",
    "file_repos_not_synced": "Some file repositories are not synced",
    # Content accessible
    "pulp_content_accessible": "Pulp RPM content is accessible via HTTP",
    "pulp_content_not_accessible": "Pulp RPM content is not accessible",
    # Software packages in Pulp
    "software_packages_ok": "All software_config packages found in Pulp",
    "software_packages_missing": "Some software_config packages missing from Pulp",
    "software_config_error": "Failed to load software_config.json",
}


TEST_ASSERT_MSGS = {
    "container_not_running": """
╔══════════════════════════════════════════════════════════════════════════════╗
║ CONTAINER CHECK FAILED: {container}
╠══════════════════════════════════════════════════════════════════════════════╣
║ Status: {status}
║
║ HOW TO FIX:
║   1. Check container: podman ps -a | grep {container}
║   2. Check logs: podman logs {container}
║   3. Restart: podman restart {container}
╚══════════════════════════════════════════════════════════════════════════════╝
""",
    "pulp_cli_failed": """
╔══════════════════════════════════════════════════════════════════════════════╗
║ PULP CLI CHECK FAILED
╠══════════════════════════════════════════════════════════════════════════════╣
║ Command: pulp rpm repository list
║
║ HOW TO FIX:
║   1. Ensure omnia_core and pulp are running: podman ps
║   2. Try running inside omnia_core: podman exec -it omnia_core bash
║   3. Check pulp logs: podman logs pulp
╚══════════════════════════════════════════════════════════════════════════════╝
""",
    "pulp_api_unhealthy": """
╔══════════════════════════════════════════════════════════════════════════════╗
║ PULP API STATUS CHECK FAILED
╠══════════════════════════════════════════════════════════════════════════════╣
║ {details}
║
║ HOW TO FIX:
║   1. Check pulp container is running: podman ps | grep pulp
║   2. Check pulp status: podman exec omnia_core pulp status
║   3. Check pulp logs: podman logs pulp
╚══════════════════════════════════════════════════════════════════════════════╝
""",
    "pulp_failed_tasks": """
╔══════════════════════════════════════════════════════════════════════════════╗
║ PULP HAS FAILED TASKS
╠══════════════════════════════════════════════════════════════════════════════╣
║ {details}
║
║ HOW TO FIX:
║   1. List failed tasks: pulp task list --state=failed
║   2. Check task details for specific errors
║   3. Re-run failed sync/publish operations
║   4. Check pulp logs: podman logs pulp
╚══════════════════════════════════════════════════════════════════════════════╝
""",
    "sw_download_failed": """
╔══════════════════════════════════════════════════════════════════════════════╗
║ SOFTWARE DOWNLOAD FAILURES DETECTED
╠══════════════════════════════════════════════════════════════════════════════╣
║ {details}
║
║ HOW TO FIX:
║   1. Check /opt/omnia/log/local_repo/<arch>/software.csv for failed entries
║   2. Check /opt/omnia/log/local_repo/standard.log for errors
║   3. Verify internet connectivity and repo URL availability
║   4. Re-run local_repo.yml inside omnia_core
╚══════════════════════════════════════════════════════════════════════════════╝
""",
    "pkg_status_failed": """
╔══════════════════════════════════════════════════════════════════════════════╗
║ PACKAGE DOWNLOAD/SYNC FAILURES DETECTED
╠══════════════════════════════════════════════════════════════════════════════╣
║ {details}
║
║ HOW TO FIX:
║   1. Check per-software status.csv files under /opt/omnia/log/local_repo/
║   2. Look for 'Failed' entries and check corresponding repos
║   3. Verify repo URLs in local_repo_config.yml are accessible
║   4. Re-run local_repo.yml inside omnia_core
╚══════════════════════════════════════════════════════════════════════════════╝
""",
    "pulp_repos_not_synced": """
╔══════════════════════════════════════════════════════════════════════════════╗
║ RPM REPOSITORIES NOT SYNCED
╠══════════════════════════════════════════════════════════════════════════════╣
║ {details}
║
║ HOW TO FIX:
║   1. Check repository sync status: pulp rpm repository list
║   2. Re-run sync: pulp rpm repository sync --name <repo_name> --remote <name>
║   3. Check pulp logs for sync errors: podman logs pulp
╚══════════════════════════════════════════════════════════════════════════════╝
""",
    "pulp_distributions_missing": """
╔══════════════════════════════════════════════════════════════════════════════╗
║ RPM DISTRIBUTIONS NOT PUBLISHED
╠══════════════════════════════════════════════════════════════════════════════╣
║ {details}
║
║ HOW TO FIX:
║   1. List distributions: pulp rpm distribution list
║   2. Create missing distribution: pulp rpm distribution create
║   3. Check publication status: pulp rpm publication list
╚══════════════════════════════════════════════════════════════════════════════╝
""",
    "container_repos_not_synced": """
╔══════════════════════════════════════════════════════════════════════════════╗
║ CONTAINER REPOSITORIES NOT SYNCED
╠══════════════════════════════════════════════════════════════════════════════╣
║ {details}
║
║ HOW TO FIX:
║   1. Check container repos: pulp container repository list
║   2. Verify image references in software config JSONs
║   3. Check registry accessibility and credentials
║   4. Re-run local_repo.yml inside omnia_core
╚══════════════════════════════════════════════════════════════════════════════╝
""",
    "file_repos_not_synced": """
╔══════════════════════════════════════════════════════════════════════════════╗
║ FILE REPOSITORIES NOT SYNCED
╠══════════════════════════════════════════════════════════════════════════════╣
║ {details}
║
║ HOW TO FIX:
║   1. Check file repos: pulp file repository list
║   2. Verify tarball/ISO/manifest URLs in software config JSONs
║   3. Re-run local_repo.yml inside omnia_core
╚══════════════════════════════════════════════════════════════════════════════╝
""",
    "pulp_content_not_accessible": """
╔══════════════════════════════════════════════════════════════════════════════╗
║ PULP RPM CONTENT NOT ACCESSIBLE
╠══════════════════════════════════════════════════════════════════════════════╣
║ {details}
║
║ HOW TO FIX:
║   1. Check distribution exists: pulp rpm distribution list
║   2. Verify content URL: curl -sk https://localhost:2225/pulp/content/<base_path>/repodata/repomd.xml
║   3. Check nginx/pulp content app: podman logs pulp
╚══════════════════════════════════════════════════════════════════════════════╝
""",
    "software_packages_missing": """
╔══════════════════════════════════════════════════════════════════════════════╗
║ SOFTWARE PACKAGES MISSING FROM PULP
╠══════════════════════════════════════════════════════════════════════════════╣
║ {details}
║
║ HOW TO FIX:
║   1. Check software_config.json and config/*.json files
║   2. Verify local_repo.yml ran successfully
║   3. Check pulp sync status: pulp rpm repository list
║   4. Re-run local_repo.yml inside omnia_core
╚══════════════════════════════════════════════════════════════════════════════╝
""",
    "software_config_error": """
╔══════════════════════════════════════════════════════════════════════════════╗
║ SOFTWARE CONFIG ERROR
╠══════════════════════════════════════════════════════════════════════════════╣
║ {error}
║
║ HOW TO FIX:
║   1. Verify software_config.json exists in /opt/omnia/input/project_default/
║   2. Check JSON syntax is valid
║   3. Ensure config/<arch>/<os>/<version>/*.json files exist
╚══════════════════════════════════════════════════════════════════════════════╝
""",
}
