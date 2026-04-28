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
Local Repo Test Cases.

This module contains pytest test cases for verifying local_repo (Pulp) deployment.

Test cases:
1. Verify build_stream pipeline stage 'create-local-repository' COMPLETED (when enabled)
2. Verify Pulp container is running
3. Verify Pulp CLI connectivity (rpm repository list)
4. Verify Pulp API health (DB, workers, storage)
5. Verify software download results (software.csv)
6. Verify per-package download results (status.csv)
7. Verify all RPM repositories synced in Pulp
8. Verify all RPM distributions published
9. Verify all container image repositories synced
10. Verify all file repositories synced
11. Verify RPM content reachable via HTTPS (repomd.xml)
12. Verify all software_config.json RPM packages in Pulp
13. Verify RHEL10 BaseOS and AppStream repos synced in Pulp
14. Verify aarch64 ARM repos available in Pulp from x86 OIM
15. Verify EPEL repos synced for both x86_64 and aarch64
16. Verify CRB repos synced for both architectures
17. Verify Slurm repo available in Pulp
18. Verify CUDA packages available in Pulp
19. Verify OpenMPI and UCX packages available in Pulp for ARM
20. Verify OpenLDAP packages available in Pulp
21. Verify multi-arch repo segregation (x86_64 vs aarch64) in Pulp
22. Verify RHEL10 subscription-manager is registered and active
23. Verify software_config.json is valid and parseable
24. Verify repo metadata (repomd.xml) present for all distributions
"""

import pytest

from automation_library.core import (
    TestLogger,
    is_build_stream_enabled,
    get_build_stream_job_id,
    STAGE_CREATE_LOCAL_REPO,
)
from automation_library.local_repo.messages.local_repo_msgs import (
    TEST_NAMES,
    TEST_LOG_MSGS as LOG_MSGS,
    TEST_ASSERT_MSGS as ASSERT_MSGS,
    TEST_VARS,
)
from automation_library.local_repo.functions.local_repo_func import (
    check_container_running,
    check_pulp_cli_repository_list,
    check_pulp_api_status,
    check_software_download_status,
    check_per_software_package_status,
    check_pulp_repositories_synced,
    check_pulp_distributions_published,
    check_container_repos_synced,
    check_file_repos_synced,
    check_pulp_content_accessible,
    check_software_packages_in_pulp,
    check_rhel10_base_repos_in_pulp,
    check_aarch64_repos_in_pulp,
    check_epel_repos_in_pulp,
    check_crb_repos_in_pulp,
    check_slurm_repo_in_pulp,
    check_cuda_packages_in_pulp,
    check_openmpi_ucx_packages_in_pulp,
    check_openldap_packages_in_pulp,
    check_multiarch_repo_segregation,
    check_subscription_status,
    check_software_config_json_valid,
    check_pulp_repo_metadata_present,
)
from molecule.conftest import build_stream_job_state


# ---------------------------------------------------------------------------
# 1. Build stream job stage validation
# ---------------------------------------------------------------------------
@pytest.mark.sanity
@pytest.mark.order(1)
def test_build_stream_job_stage(host):
    """
    Test 1: When build_stream is enabled, verify the create-local-repository
    pipeline stage completed successfully before running any Pulp checks.

    - Reads build_stream_job_id override from omnia_test_config.yml if set.
    - Falls back to the latest job in build_stream_db otherwise.
    - Prints the exact DB stage_state if not COMPLETED.
    - Skipped when build_stream is disabled.
    """
    stage = STAGE_CREATE_LOCAL_REPO
    if not is_build_stream_enabled(host):
        pytest.skip(LOG_MSGS["build_stream_disabled_skip"])

    log = TestLogger(TEST_NAMES["build_stream_job_stage"].format(stage=stage))

    result = get_build_stream_job_id(host, stage_name=stage)
    job_id = result.get("job_id") or "unknown"
    job_state = result.get("job_state") or "NOT FOUND"
    source = result.get("source", "database")

    # Set shared state so autouse fixture in conftest.py can skip remaining tests
    build_stream_job_state["checked"] = True
    build_stream_job_state["success"] = result["success"]
    build_stream_job_state["job_id"] = job_id
    build_stream_job_state["job_state"] = job_state
    build_stream_job_state["error"] = result.get("error", "")

    log.check(LOG_MSGS["build_stream_job_checking"].format(stage=stage, source=source))

    if result["success"]:
        log.passed(
            LOG_MSGS["build_stream_job_ok"].format(
                stage=stage, job_id=job_id, source=source
            )
        )
    else:
        log.failed(
            LOG_MSGS["build_stream_job_failed"].format(
                stage=stage, state=job_state, job_id=job_id
            ),
            result.get("error", "")
        )
        # Use pytest.fail() so this test shows as FAILED (not skipped)
        # Remaining tests will be SKIPPED via autouse fixture
        pytest.fail(
            ASSERT_MSGS["build_stream_job_stage_failed"].format(
                stage=stage, job_id=job_id, state=job_state
            )
        )


# ---------------------------------------------------------------------------
# 2. Pulp container running
# ---------------------------------------------------------------------------
@pytest.mark.sanity
@pytest.mark.order(2)
def test_pulp_container_running(host):
    container = TEST_VARS["pulp_container"]
    log = TestLogger(TEST_NAMES["pulp_container_running"])
    log.check(f"Verifying '{container}' container is running via podman ps")

    result = check_container_running(host, container)
    if result["success"]:
        log.passed(LOG_MSGS["container_running"].format(container=container), result["status"])
    else:
        log.failed(LOG_MSGS["container_not_running"].format(container=container), result.get("error"))

    assert result["success"], ASSERT_MSGS["container_not_running"].format(
        container=container,
        status=result.get("status", "unknown"),
    )


# ---------------------------------------------------------------------------
# 2. Pulp CLI connectivity
# ---------------------------------------------------------------------------
@pytest.mark.sanity
@pytest.mark.order(3)
def test_pulp_cli_repository_list(host):
    log = TestLogger(TEST_NAMES["pulp_cli_repo_list"])
    log.check("Running 'pulp rpm repository list' inside omnia_core container")

    result = check_pulp_cli_repository_list(host)
    if result["success"]:
        log.passed(LOG_MSGS["pulp_cli_ok"], result.get("details") or "")
    else:
        log.failed(LOG_MSGS["pulp_cli_fail"], result.get("error") or "")

    assert result["success"], ASSERT_MSGS["pulp_cli_failed"]


# ---------------------------------------------------------------------------
# 3. Pulp API health
# ---------------------------------------------------------------------------
@pytest.mark.sanity
@pytest.mark.order(4)
def test_pulp_api_status(host):
    log = TestLogger(TEST_NAMES["pulp_api_status"])
    log.check("Querying 'pulp status' for DB connection, workers, content apps, storage")

    result = check_pulp_api_status(host)
    if result["success"]:
        log.passed(LOG_MSGS["pulp_api_healthy"], result.get("details") or "")
    else:
        details = result.get("details") or result.get("error") or ""
        log.failed(LOG_MSGS["pulp_api_unhealthy"], details)
        assert False, ASSERT_MSGS["pulp_api_unhealthy"].format(details=details)


# ---------------------------------------------------------------------------
# 4. Software download status (software.csv)
# ---------------------------------------------------------------------------
@pytest.mark.sanity
@pytest.mark.order(5)
def test_software_download_status(host):
    log = TestLogger(TEST_NAMES["software_download_status"])
    log.check("Parsing software.csv per architecture for download success/failure")

    result = check_software_download_status(host)
    if result["success"]:
        log.passed(LOG_MSGS["sw_download_ok"], result.get("details") or "")
    else:
        details = result.get("details") or result.get("error") or ""
        log.failed(LOG_MSGS["sw_download_failed"], details)
        assert False, ASSERT_MSGS["sw_download_failed"].format(details=details)


# ---------------------------------------------------------------------------
# 5. Per-software package status (status.csv per software)
# ---------------------------------------------------------------------------
@pytest.mark.sanity
@pytest.mark.order(6)
def test_per_software_package_status(host):
    log = TestLogger(TEST_NAMES["per_software_package_status"])
    log.check("Parsing per-software status.csv for individual package download results")

    result = check_per_software_package_status(host)
    if result["success"]:
        log.passed(LOG_MSGS["pkg_status_ok"], result.get("details") or "")
    else:
        details = result.get("details") or result.get("error") or ""
        log.failed(LOG_MSGS["pkg_status_failed"], details)
        assert False, ASSERT_MSGS["pkg_status_failed"].format(details=details)


# ---------------------------------------------------------------------------
# 6. RPM repositories synced
# ---------------------------------------------------------------------------
@pytest.mark.sanity
@pytest.mark.order(7)
def test_pulp_repositories_synced(host):
    log = TestLogger(TEST_NAMES["pulp_repositories_synced"])
    log.check("Querying Pulp RPM repos for latest_version_href (sync indicator)")

    result = check_pulp_repositories_synced(host)
    if result["success"]:
        log.passed(LOG_MSGS["pulp_repos_synced"], result.get("details") or "")
    else:
        details = result.get("details") or result.get("error") or ""
        log.failed(LOG_MSGS["pulp_repos_not_synced"], details)
        assert False, ASSERT_MSGS["pulp_repos_not_synced"].format(details=details)


# ---------------------------------------------------------------------------
# 7. RPM distributions published
# ---------------------------------------------------------------------------
@pytest.mark.sanity
@pytest.mark.order(8)
def test_pulp_distributions_published(host):
    log = TestLogger(TEST_NAMES["pulp_distributions_published"])
    log.check("Querying Pulp RPM distributions for publication/repository attachment")

    result = check_pulp_distributions_published(host)
    if result["success"]:
        log.passed(LOG_MSGS["pulp_distributions_ok"], result.get("details") or "")
    else:
        details = result.get("details") or result.get("error") or ""
        log.failed(LOG_MSGS["pulp_distributions_missing"], details)
        assert False, ASSERT_MSGS["pulp_distributions_missing"].format(details=details)


# ---------------------------------------------------------------------------
# 8. Container image repositories synced
# ---------------------------------------------------------------------------
@pytest.mark.sanity
@pytest.mark.order(9)
def test_container_repos_synced(host):
    log = TestLogger(TEST_NAMES["container_repos_synced"])
    log.check("Querying Pulp container repos for latest_version_href (sync indicator)")

    result = check_container_repos_synced(host)
    if result["success"]:
        log.passed(LOG_MSGS["container_repos_synced"], result.get("details") or "")
    else:
        details = result.get("details") or result.get("error") or ""
        log.failed(LOG_MSGS["container_repos_not_synced"], details)
        assert False, ASSERT_MSGS["container_repos_not_synced"].format(details=details)


# ---------------------------------------------------------------------------
# 9. File repositories synced
# ---------------------------------------------------------------------------
@pytest.mark.sanity
@pytest.mark.order(10)
def test_file_repos_synced(host):
    log = TestLogger(TEST_NAMES["file_repos_synced"])
    log.check("Querying Pulp file repos for latest_version_href (sync indicator)")

    result = check_file_repos_synced(host)
    if result["success"]:
        log.passed(LOG_MSGS["file_repos_synced"], result.get("details") or "")
    else:
        details = result.get("details") or result.get("error") or ""
        log.failed(LOG_MSGS["file_repos_not_synced"], details)
        assert False, ASSERT_MSGS["file_repos_not_synced"].format(details=details)


# ---------------------------------------------------------------------------
# 10. RPM content accessible via HTTPS (repomd.xml)
# ---------------------------------------------------------------------------
@pytest.mark.sanity
@pytest.mark.order(11)
def test_pulp_content_accessible(host):
    log = TestLogger(TEST_NAMES["pulp_content_accessible"])
    log.check("Curling repomd.xml for each RPM distribution base_path")

    result = check_pulp_content_accessible(host)
    if result["success"]:
        log.passed(LOG_MSGS["pulp_content_accessible"], result.get("details") or "")
    else:
        details = result.get("details") or result.get("error") or ""
        log.failed(LOG_MSGS["pulp_content_not_accessible"], details)
        assert False, ASSERT_MSGS["pulp_content_not_accessible"].format(details=details)


# ---------------------------------------------------------------------------
# 11. Software packages in Pulp
# ---------------------------------------------------------------------------
@pytest.mark.sanity
@pytest.mark.order(12)
def test_software_packages_in_pulp(host):
    log = TestLogger(TEST_NAMES["software_packages_in_pulp"])
    log.check("Loading software_config.json, extracting RPM packages, verifying each in Pulp")

    result = check_software_packages_in_pulp(host)

    if result["success"]:
        # Show full details with all individual package names
        details = result.get("details") or ""
        log.passed(LOG_MSGS["software_packages_ok"], details)
        return

    if "config" in (result.get("error") or "").lower():
        log.failed(LOG_MSGS["software_config_error"], result.get("error") or "")
        assert False, ASSERT_MSGS["software_config_error"].format(
            error=result.get("error") or ""
        )

    details = result.get("details") or result.get("error") or ""
    missing_count = result.get("missing_packages", 0)
    log.failed(
        LOG_MSGS["software_packages_missing"],
        f"Missing: {missing_count} packages\n{details}",
    )
    assert False, ASSERT_MSGS["software_packages_missing"].format(details=details)


# ---------------------------------------------------------------------------
# 13. RHEL10 BaseOS and AppStream repos in Pulp
# ---------------------------------------------------------------------------
@pytest.mark.sanity
@pytest.mark.order(13)
def test_rhel10_base_repos_in_pulp(host):
    """
    Test 13: Verify RHEL10 BaseOS and AppStream repos are synced in Pulp.

    Checks both x86_64 (required) and aarch64 (optional) variants.
    Maps to: pulp_rhel10_structure, validate_fallback_to_iso_mount_when.
    """
    log = TestLogger(TEST_NAMES["rhel10_base_repos"])
    log.check("Verifying RHEL10 BaseOS and AppStream repos in Pulp for both architectures")

    result = check_rhel10_base_repos_in_pulp(host)
    if result["success"]:
        log.passed(LOG_MSGS["rhel10_base_repos_ok"], result.get("details") or "")
    else:
        details = result.get("details") or result.get("error") or ""
        log.failed(LOG_MSGS["rhel10_base_repos_fail"], details)
        assert False, ASSERT_MSGS["rhel10_base_repos_fail"].format(details=details)


# ---------------------------------------------------------------------------
# 14. aarch64 ARM repos in Pulp
# ---------------------------------------------------------------------------
@pytest.mark.sanity
@pytest.mark.order(14)
def test_aarch64_repos_in_pulp(host):
    """
    Test 14: Verify aarch64 ARM repos are available and synced in Pulp from x86 OIM.

    Maps to: validate_availability_of_arm_repo_on, pulp_multiarch_repo_validation.
    """
    log = TestLogger(TEST_NAMES["aarch64_repos"])
    log.check("Checking Pulp RPM repository list for aarch64 (ARM) repos")

    result = check_aarch64_repos_in_pulp(host)
    if result["success"]:
        log.passed(LOG_MSGS["aarch64_repos_ok"], result.get("details") or "")
    else:
        details = result.get("details") or result.get("error") or ""
        log.failed(LOG_MSGS["aarch64_repos_fail"], details)
        assert False, ASSERT_MSGS["aarch64_repos_fail"].format(details=details)


# ---------------------------------------------------------------------------
# 15. EPEL repos for both architectures
# ---------------------------------------------------------------------------
@pytest.mark.sanity
@pytest.mark.order(15)
def test_epel_repos_in_pulp(host):
    """
    Test 15: Verify EPEL repos for both x86_64 and aarch64 are synced in Pulp.

    Maps to: validate_epel_repository_sync_for_both.
    """
    log = TestLogger(TEST_NAMES["epel_repos"])
    log.check("Checking Pulp for EPEL repos for x86_64 and aarch64")

    result = check_epel_repos_in_pulp(host)
    if result["success"]:
        log.passed(LOG_MSGS["epel_repos_ok"], result.get("details") or "")
    else:
        details = result.get("details") or result.get("error") or ""
        log.failed(LOG_MSGS["epel_repos_fail"], details)
        assert False, ASSERT_MSGS["epel_repos_fail"].format(details=details)


# ---------------------------------------------------------------------------
# 16. CRB repos for both architectures
# ---------------------------------------------------------------------------
@pytest.mark.sanity
@pytest.mark.order(16)
def test_crb_repos_in_pulp(host):
    """
    Test 16: Verify CRB repos for both architectures are synced in Pulp.

    Maps to: validate_crb_repo_sync_and_visibility.
    """
    log = TestLogger(TEST_NAMES["crb_repos"])
    log.check("Checking Pulp for CRB (CodeReady Builder) repos for x86_64 and aarch64")

    result = check_crb_repos_in_pulp(host)
    if result.get("skipped"):
        reason = result.get("reason", "CRB repos not configured")
        log.skipped(reason)
        pytest.skip(reason)
    elif result["success"]:
        log.passed(LOG_MSGS["crb_repos_ok"], result.get("details") or "")
    else:
        details = result.get("details") or result.get("error") or ""
        log.failed(LOG_MSGS["crb_repos_fail"], details)
        assert False, ASSERT_MSGS["crb_repos_fail"].format(details=details)


# ---------------------------------------------------------------------------
# 17. Slurm repos in Pulp
# ---------------------------------------------------------------------------
@pytest.mark.sanity
@pytest.mark.order(17)
def test_slurm_repo_in_pulp(host):
    """
    Test 17: Verify Slurm repos are present and synced in Pulp.

    Maps to: validate_custom_slurm_repo_creation_and, pulp_slurm_repo_ready,
             validate_multi_architecture_slurm_image_creation.
    """
    log = TestLogger(TEST_NAMES["slurm_repos"])
    log.check("Checking Pulp for Slurm repos")

    result = check_slurm_repo_in_pulp(host)
    if result["success"]:
        log.passed(LOG_MSGS["slurm_repos_ok"], result.get("details") or "")
    else:
        details = result.get("details") or result.get("error") or ""
        log.failed(LOG_MSGS["slurm_repos_fail"], details)
        assert False, ASSERT_MSGS["slurm_repos_fail"].format(details=details)


# ---------------------------------------------------------------------------
# 18. CUDA packages in Pulp
# ---------------------------------------------------------------------------
@pytest.mark.sanity
@pytest.mark.order(18)
def test_cuda_packages_in_pulp(host):
    """
    Test 18: Verify CUDA packages or repos are available in Pulp.

    Maps to: validate_cuda_packages_availability_from_local.
    """
    log = TestLogger(TEST_NAMES["cuda_packages"])
    log.check("Checking Pulp for CUDA repos or RPM packages")

    result = check_cuda_packages_in_pulp(host)
    if result["success"]:
        log.passed(LOG_MSGS["cuda_ok"], result.get("details") or "")
    else:
        details = result.get("details") or result.get("error") or ""
        log.failed(LOG_MSGS["cuda_fail"], details)
        assert False, ASSERT_MSGS["cuda_fail"].format(details=details)


# ---------------------------------------------------------------------------
# 19. OpenMPI and UCX packages in Pulp
# ---------------------------------------------------------------------------
@pytest.mark.sanity
@pytest.mark.order(19)
def test_openmpi_ucx_packages_in_pulp(host):
    """
    Test 19: Verify OpenMPI and UCX packages are available in Pulp for ARM workloads.

    Maps to: validate_openmpi_and_ucx_packages_served.
    """
    log = TestLogger(TEST_NAMES["openmpi_ucx_packages"])
    log.check("Checking Pulp RPM content for openmpi and ucx packages")

    result = check_openmpi_ucx_packages_in_pulp(host)
    if result["success"]:
        log.passed(LOG_MSGS["openmpi_ucx_ok"], result.get("details") or "")
    else:
        details = result.get("details") or result.get("error") or ""
        log.failed(LOG_MSGS["openmpi_ucx_fail"], details)
        assert False, ASSERT_MSGS["openmpi_ucx_fail"].format(details=details)


# ---------------------------------------------------------------------------
# 20. OpenLDAP packages in Pulp
# ---------------------------------------------------------------------------
@pytest.mark.sanity
@pytest.mark.order(20)
def test_openldap_packages_in_pulp(host):
    """
    Test 20: Verify OpenLDAP packages are available in Pulp.

    Maps to: validate_openldap_rpms_are_available_after.
    """
    log = TestLogger(TEST_NAMES["openldap_packages"])
    log.check("Checking Pulp RPM content for openldap, openldap-servers, openldap-clients")

    result = check_openldap_packages_in_pulp(host)
    if result["success"]:
        log.passed(LOG_MSGS["openldap_ok"], result.get("details") or "")
    else:
        details = result.get("details") or result.get("error") or ""
        log.failed(LOG_MSGS["openldap_fail"], details)
        assert False, ASSERT_MSGS["openldap_fail"].format(details=details)


# ---------------------------------------------------------------------------
# 21. Multi-arch repo segregation
# ---------------------------------------------------------------------------
@pytest.mark.sanity
@pytest.mark.order(21)
def test_multiarch_repo_segregation(host):
    """
    Test 21: Verify x86_64 and aarch64 repos are stored separately in Pulp.

    Maps to: pulp_multiarch_repo_validation, validate_multi_arch_repo_sync_within.
    """
    log = TestLogger(TEST_NAMES["multiarch_segregation"])
    log.check("Verifying x86_64 and aarch64 repos are segregated in Pulp")

    result = check_multiarch_repo_segregation(host)
    if result["success"]:
        log.passed(LOG_MSGS["multiarch_ok"], result.get("details") or "")
    else:
        details = result.get("details") or result.get("error") or ""
        log.failed(LOG_MSGS["multiarch_fail"], details)
        assert False, ASSERT_MSGS["multiarch_fail"].format(details=details)


# ---------------------------------------------------------------------------
# 22. RHEL10 subscription status
# ---------------------------------------------------------------------------
@pytest.mark.sanity
@pytest.mark.order(22)
def test_subscription_status(host):
    """
    Test 22: Verify RHEL subscription-manager is registered and active on the OIM node.

    Maps to: validate_subscription_enablement_for_rhel10.
    """
    log = TestLogger(TEST_NAMES["subscription_status"])
    log.check("Running 'subscription-manager status' on the OIM node")

    result = check_subscription_status(host)
    if result["success"]:
        log.passed(LOG_MSGS["subscription_ok"], result.get("details") or "")
    else:
        details = result.get("details") or result.get("error") or ""
        log.failed(LOG_MSGS["subscription_fail"], details)
        assert False, ASSERT_MSGS["subscription_fail"].format(details=details)


# ---------------------------------------------------------------------------
# 23. software_config.json validation
# ---------------------------------------------------------------------------
@pytest.mark.sanity
@pytest.mark.order(23)
def test_software_config_json_valid(host):
    """
    Test 23: Verify software_config.json is parseable and has well-formed entries.

    Maps to: custom_json_valid_inputs, custom_json_duplicate_entries.
    """
    log = TestLogger(TEST_NAMES["software_config_valid"])
    log.check("Loading and validating software_config.json structure and entries")

    result = check_software_config_json_valid(host)
    if result["success"]:
        log.passed(LOG_MSGS["software_config_ok"], result.get("details") or "")
    else:
        details = result.get("details") or result.get("error") or ""
        log.failed(LOG_MSGS["software_config_fail"], details)
        assert False, ASSERT_MSGS["software_config_fail"].format(details=details)


# ---------------------------------------------------------------------------
# 24. Pulp repo metadata (repomd.xml) present
# ---------------------------------------------------------------------------
@pytest.mark.sanity
@pytest.mark.order(24)
def test_pulp_repo_metadata_present(host):
    """
    Test 24: Verify repomd.xml metadata is accessible for all published RPM distributions.

    Maps to: pulp_metadata_verification, validate_repo_metadata_creation_and_storage.
    """
    log = TestLogger(TEST_NAMES["repo_metadata_present"])
    log.check("Curling repomd.xml for each RPM distribution to verify metadata presence")

    result = check_pulp_repo_metadata_present(host)
    if result["success"]:
        log.passed(LOG_MSGS["repo_metadata_ok"], result.get("details") or "")
    else:
        details = result.get("details") or result.get("error") or ""
        log.failed(LOG_MSGS["repo_metadata_fail"], details)
        assert False, ASSERT_MSGS["repo_metadata_fail"].format(details=details)


# =============================================================================
# PYTEST HOOKS FOR TEST SUMMARY
# =============================================================================

def pytest_terminal_summary(terminalreporter, exitstatus, _config):
    """Add custom test summary at the end of pytest output."""
    passed = len(terminalreporter.stats.get("passed", []))
    failed = len(terminalreporter.stats.get("failed", []))
    skipped = len(terminalreporter.stats.get("skipped", []))
    errors = len(terminalreporter.stats.get("error", []))
    total = passed + failed + skipped + errors
    
    terminalreporter.write_sep("=", "LOCAL_REPO TEST SUMMARY", bold=True)
    terminalreporter.write_line(f"  Total Tests   : {total}")
    terminalreporter.write_line(f"  ✓ Passed      : {passed}", green=True)
    if failed > 0:
        terminalreporter.write_line(f"  ✗ Failed      : {failed}", red=True)
    else:
        terminalreporter.write_line(f"  ✗ Failed      : {failed}")
    if skipped > 0:
        terminalreporter.write_line(f"  ⊘ Skipped     : {skipped}", yellow=True)
    else:
        terminalreporter.write_line(f"  ⊘ Skipped     : {skipped}")
    if errors > 0:
        terminalreporter.write_line(f"  ⚠ Errors      : {errors}", red=True)
    terminalreporter.write_sep("=", "")
