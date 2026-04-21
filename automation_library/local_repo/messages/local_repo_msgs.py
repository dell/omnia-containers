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
    "build_stream_job_stage": (
        "Verify build_stream pipeline stage '{stage}' completed successfully"
    ),
    "pulp_container_running": "Verify Pulp container is running",
    "pulp_cli_repo_list": "Verify Pulp CLI connectivity (rpm repository list)",
    "pulp_api_status": "Verify Pulp API health (DB, workers, storage)",
    "software_download_status": "Verify software download results (software.csv)",
    "per_software_package_status": "Verify per-package download results (status.csv)",
    "pulp_repositories_synced": "Verify all RPM repositories synced in Pulp",
    "pulp_distributions_published": "Verify all RPM distributions published",
    "container_repos_synced": "Verify all container image repositories synced",
    "file_repos_synced": "Verify all file repositories synced",
    "pulp_content_accessible": "Verify RPM content reachable via HTTPS (repomd.xml)",
    "software_packages_in_pulp": "Verify all software_config.json RPM packages in Pulp",
}


TEST_LOG_MSGS = {
    # 0. Build stream job stage
    "build_stream_disabled_skip": (
        "build_stream is DISABLED \u2014 skipping job stage validation"
    ),
    "build_stream_job_checking": (
        "Checking build_stream stage '{stage}' (source: {source})"
    ),
    "build_stream_job_ok": (
        "Stage '{stage}' COMPLETED \u2014 job UUID: {job_id} (source: {source})"
    ),
    "build_stream_job_failed": (
        "Stage '{stage}' is '{state}' \u2014 expected COMPLETED (job: {job_id})"
    ),
    # 1. Container
    "container_running": "Container {container} is running",
    "container_not_running": "Container {container} is NOT running",
    # 2. Pulp CLI
    "pulp_cli_ok": "Pulp CLI responding — repository list retrieved",
    "pulp_cli_fail": "Pulp CLI not responding — repository list failed",
    # 3. Pulp API
    "pulp_api_healthy": "Pulp API healthy — DB connected, workers online",
    "pulp_api_unhealthy": "Pulp API unhealthy — check DB/workers",
    # 4. Software download status
    "sw_download_ok": "All software downloads succeeded (software.csv)",
    "sw_download_failed": "Software download failures detected (software.csv)",
    # 5. Per-software package status
    "pkg_status_ok": "All per-package downloads succeeded (status.csv)",
    "pkg_status_failed": "Package download failures detected (status.csv)",
    # 6. RPM repos
    "pulp_repos_synced": "All RPM repositories synced with latest version",
    "pulp_repos_not_synced": "RPM repositories with missing sync detected",
    # 7. RPM distributions
    "pulp_distributions_ok": "All RPM distributions published and serving",
    "pulp_distributions_missing": "Unpublished RPM distributions detected",
    # 8. Container repos
    "container_repos_synced": "All container image repositories synced",
    "container_repos_not_synced": "Container image repositories with missing sync",
    # 9. File repos
    "file_repos_synced": "All file repositories synced",
    "file_repos_not_synced": "File repositories with missing sync detected",
    # 10. Content accessible
    "pulp_content_accessible": "All RPM distribution endpoints return HTTP 200",
    "pulp_content_not_accessible": "RPM distribution endpoints not returning HTTP 200",
    # 11. Software packages in Pulp
    "software_packages_ok": "All software_config.json RPM packages found in Pulp",
    "software_packages_missing": "RPM packages from software_config.json missing in Pulp",
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
    "build_stream_job_stage_failed": """
╔══════════════════════════════════════════════════════════════════════════════╗
║ BUILD STREAM STAGE VALIDATION FAILED
╠══════════════════════════════════════════════════════════════════════════════╣
║ Stage   : {stage}
║ Job ID  : {job_id}
║ Status  : {state}
║ Expected: COMPLETED
║
║ WHAT HAPPENED:
║   The build_stream pipeline stage did not complete successfully.
║   local_repo verification depends on the pipeline completing first.
║
║ HOW TO FIX:
║   1. Check build_stream API logs on the OIM server
║   2. Query DB: podman exec omnia_postgres psql -U omnia -d build_stream_db
║             -c "SELECT * FROM job_stages WHERE job_id = '{job_id}';"
║   3. If FAILED, re-trigger the build_stream pipeline
║   4. If still RUNNING, wait for it to complete
║   5. To override: set build_stream_job_id in omnia_test_config.yml
╚══════════════════════════════════════════════════════════════════════════════╝
""",
}
