"""Local Repo - Messages and Test Variables.

This module contains all messages, status strings, error instructions,
and test variables for the local_repo automation.

Author: Dell Technologies
"""

from typing import Dict

from ..vars.local_repo_vars import LOCAL_REPO_VARS


# =============================================================================
# TEST VARIABLES (for molecule/pytest tests)
# =============================================================================

TEST_VARS = {
    "pulp_container": LOCAL_REPO_VARS["pulp_container"],
    "omnia_core_container": LOCAL_REPO_VARS["omnia_core_container"],
    "status_search_roots": LOCAL_REPO_VARS["status_search_roots"],
}


TEST_NAMES = {
    "pulp_container_running": "Verify pulp container is running",
    "pulp_cli_repo_list": "Verify pulp CLI works (pulp rpm repository list)",
    "status_csv": "Verify packages downloaded successfully (status.csv)",
    "software_packages_in_pulp": "Verify software_config packages exist in Pulp",
    "pulp_api_status": "Verify Pulp API status is healthy",
    "pulp_repositories_synced": "Verify Pulp repositories are synced",
    "pulp_distributions_published": "Verify Pulp distributions are published",
    "pulp_no_failed_tasks": "Verify no failed tasks in Pulp",
    "pulp_content_accessible": "Verify Pulp content is accessible via HTTP",
}


TEST_LOG_MSGS = {
    "container_running": "Container {container} is running",
    "container_not_running": "Container {container} is NOT running",
    "pulp_cli_ok": "pulp rpm repository list succeeded",
    "pulp_cli_fail": "pulp rpm repository list failed",
    "status_csv_found": "Found status.csv",
    "status_csv_missing": "status.csv not found",
    "status_csv_empty": "status.csv is empty",
    "status_csv_no_rows": "status.csv has no rows",
    "status_csv_no_failures": "All packages show success in top-level status.csv",
    "status_csv_has_failures": "Top-level status.csv contains failures",
    "per_pkg_some_failed": "Some packages failed download/validation",
    "software_packages_ok": "All software_config packages found in Pulp",
    "software_packages_missing": "Some software_config packages missing from Pulp",
    "software_config_error": "Failed to load software_config.json",
    # Pulp API and functionality messages
    "pulp_api_healthy": "Pulp API status is healthy",
    "pulp_api_unhealthy": "Pulp API status check failed",
    "pulp_repos_synced": "All Pulp repositories are synced",
    "pulp_repos_not_synced": "Some Pulp repositories are not synced",
    "pulp_distributions_ok": "All Pulp distributions are published",
    "pulp_distributions_missing": "Some Pulp distributions are missing",
    "pulp_no_failed_tasks": "No failed tasks in Pulp",
    "pulp_has_failed_tasks": "Failed tasks found in Pulp",
    "pulp_content_accessible": "Pulp content is accessible via HTTP",
    "pulp_content_not_accessible": "Pulp content is not accessible",
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
    "status_csv_missing": """
╔══════════════════════════════════════════════════════════════════════════════╗
║ STATUS.CSV NOT FOUND
╠══════════════════════════════════════════════════════════════════════════════╣
║ Searched: {roots}
║
║ HOW TO FIX:
║   1. Confirm local_repo playbook ran successfully
║   2. Check logs under /opt/omnia/log and /local/omnia/log
║   3. Search manually: find {roots} -name status.csv
╚══════════════════════════════════════════════════════════════════════════════╝
""",
    "status_csv_failed": """
╔══════════════════════════════════════════════════════════════════════════════╗
║ STATUS.CSV INDICATES FAILURES
╠══════════════════════════════════════════════════════════════════════════════╣
║ Details:
║ {details}
║
║ HOW TO FIX:
║   1. Inspect status.csv and referenced per-package CSVs
║   2. Check pulp logs: podman logs pulp
║   3. Re-run local_repo.yml inside omnia_core
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
║   4. Restart pulp: systemctl restart pulp
╚══════════════════════════════════════════════════════════════════════════════╝
""",
    "pulp_repos_not_synced": """
╔══════════════════════════════════════════════════════════════════════════════╗
║ PULP REPOSITORIES NOT SYNCED
╠══════════════════════════════════════════════════════════════════════════════╣
║ {details}
║
║ HOW TO FIX:
║   1. Check repository sync status: pulp rpm repository list
║   2. Re-run sync: pulp rpm repository sync --name <repo_name>
║   3. Check pulp logs for sync errors: podman logs pulp
╚══════════════════════════════════════════════════════════════════════════════╝
""",
    "pulp_distributions_missing": """
╔══════════════════════════════════════════════════════════════════════════════╗
║ PULP DISTRIBUTIONS NOT PUBLISHED
╠══════════════════════════════════════════════════════════════════════════════╣
║ {details}
║
║ HOW TO FIX:
║   1. List distributions: pulp rpm distribution list
║   2. Create missing distribution: pulp rpm distribution create
║   3. Check publication status: pulp rpm publication list
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
    "pulp_content_not_accessible": """
╔══════════════════════════════════════════════════════════════════════════════╗
║ PULP CONTENT NOT ACCESSIBLE
╠══════════════════════════════════════════════════════════════════════════════╣
║ {details}
║
║ HOW TO FIX:
║   1. Check distribution exists: pulp rpm distribution list
║   2. Verify content URL: curl -s <pulp_url>/pulp/content/<repo>/repodata/repomd.xml
║   3. Check nginx/pulp content app: podman logs pulp
╚══════════════════════════════════════════════════════════════════════════════╝
""",
}


# =============================================================================
# FUNCTION MESSAGES (for local_repo_func.py)
# =============================================================================

LOCAL_REPO_MSGS: Dict[str, str] = {
    "container_running": "Container {container} is running",
    "container_not_running": "Container {container} is NOT running",
    "status_csv_missing": "status.csv not found",
    "status_csv_empty": "status.csv is empty",
    "status_csv_no_rows": "status.csv has no rows",
    "status_csv_has_failures": "status.csv indicates failures",
}
