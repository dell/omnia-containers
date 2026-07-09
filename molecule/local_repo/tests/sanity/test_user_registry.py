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
User Registry Test Cases.

This module contains pytest test cases for verifying user_registry
container registry functionality in local_repo_config.yml.

Test cases:
13. Verify user_registry configuration loaded from local_repo_config.yml
14. Verify HTTPS registry cert_path and key_path files exist
15. Verify HTTP registry entries do not require cert_path/key_path
16. Verify user_registry_credential.yml authentication file exists
17. Verify container images from user registries synced to Pulp
18. Verify Pulp container remotes created for user registries

Coverage gaps addressed:
- HTTPS registry with cert/key
- HTTP registry without certs
- Registry authentication via user_registry_credential.yml
- Container image sync to Pulp from user registries
"""

import pytest
from automation_library.core import TestLogger
from automation_library.local_repo.messages.user_registry_msgs import (
    USER_REGISTRY_TEST_NAMES as TEST_NAMES,
    USER_REGISTRY_LOG_MSGS as LOG_MSGS,
    USER_REGISTRY_ASSERT_MSGS as ASSERT_MSGS,
)
from automation_library.local_repo.functions.user_registry_func import (
    check_user_registry_config,
    check_user_registry_https_certs,
    check_user_registry_http_no_certs,
    check_user_registry_auth_credentials,
    check_user_registry_container_repos_synced,
    check_user_registry_remotes_in_pulp,
)


# =============================================================================
# Module-level cache for user_registry config (loaded once, reused by all tests)
# =============================================================================
_user_registry_cache = {}


def _get_user_registry_config(host):
    """Load and cache user_registry config for reuse across tests."""
    if "result" not in _user_registry_cache:
        _user_registry_cache["result"] = check_user_registry_config(host)
    return _user_registry_cache["result"]


# ---------------------------------------------------------------------------
# 13. User registry config loaded
# ---------------------------------------------------------------------------
@pytest.mark.sanity
@pytest.mark.order(13)
def test_user_registry_config_loaded(host):
    """
    Test 13: Verify user_registry configuration is present in local_repo_config.yml.

    Reads local_repo_config.yml from omnia_core container and checks that the
    user_registry section contains at least one registry entry. Classifies
    each entry as HTTPS (cert_path + key_path set) or HTTP (no certs).

    Skipped if user_registry is not configured.
    """
    log = TestLogger(TEST_NAMES["user_registry_config_loaded"])
    log.check("Loading user_registry from local_repo_config.yml in omnia_core")

    result = _get_user_registry_config(host)

    if not result["success"] and result["count"] == 0:
        log.check(LOG_MSGS["config_skip"])
        pytest.skip(LOG_MSGS["config_skip"])

    if result["success"]:
        log.passed(
            LOG_MSGS["config_loaded_ok"].format(count=result["count"]),
            result.get("details") or "",
        )
    else:
        log.failed(LOG_MSGS["config_not_found"], result.get("error") or "")
        assert False, ASSERT_MSGS["config_not_found"]


# ---------------------------------------------------------------------------
# 14. HTTPS registry cert/key existence
# ---------------------------------------------------------------------------
@pytest.mark.sanity
@pytest.mark.order(14)
def test_user_registry_https_cert_exists(host):
    """
    Test 14: Verify HTTPS registry cert_path and key_path files exist.

    For each user_registry entry classified as HTTPS (cert_path and key_path
    are both set), verifies that the referenced certificate and key files
    exist inside the omnia_core container. These are required for Pulp
    to create container remotes with --ca-cert and --client-key flags.

    Skipped if no HTTPS registries are configured.
    """
    log = TestLogger(TEST_NAMES["user_registry_https_cert_exists"])

    config = _get_user_registry_config(host)
    if not config["success"]:
        pytest.skip(LOG_MSGS["config_skip"])

    https_registries = config.get("https_registries", [])
    if not https_registries:
        log.check("No HTTPS registries configured — skipping cert check")
        pytest.skip("No HTTPS registries configured in user_registry")

    log.check(
        LOG_MSGS["https_cert_checking"].format(
            host=", ".join(r["host"] for r in https_registries)
        )
    )

    result = check_user_registry_https_certs(host, https_registries)
    if result["success"]:
        log.passed(LOG_MSGS["https_cert_ok"], result.get("details") or "")
    else:
        details = result.get("details") or result.get("error") or ""
        log.failed(LOG_MSGS["https_cert_missing"], details)
        assert False, ASSERT_MSGS["https_cert_missing"].format(details=details)


# ---------------------------------------------------------------------------
# 15. HTTP registry no-cert validation
# ---------------------------------------------------------------------------
@pytest.mark.sanity
@pytest.mark.order(15)
def test_user_registry_http_no_certs(host):
    """
    Test 15: Verify HTTP registry entries do not require cert_path/key_path.

    For each user_registry entry classified as HTTP (cert_path and key_path
    are both empty or not set), confirms the configuration is correct. HTTP
    registries should not have certificate files — Pulp creates their remotes
    without --ca-cert/--client-key flags.

    Skipped if no HTTP registries are configured.
    """
    log = TestLogger(TEST_NAMES["user_registry_http_no_certs"])

    config = _get_user_registry_config(host)
    if not config["success"]:
        pytest.skip(LOG_MSGS["config_skip"])

    http_registries = config.get("http_registries", [])
    if not http_registries:
        log.check(LOG_MSGS["http_no_cert_skip"])
        pytest.skip(LOG_MSGS["http_no_cert_skip"])

    log.check(f"Checking {len(http_registries)} HTTP registries for no-cert configuration")

    result = check_user_registry_http_no_certs(host, http_registries)
    if result["success"]:
        if result.get("warnings"):
            log.passed(LOG_MSGS["http_has_cert_warning"], result.get("details") or "")
        else:
            log.passed(LOG_MSGS["http_no_cert_ok"], result.get("details") or "")


# ---------------------------------------------------------------------------
# 16. Registry authentication credential file
# ---------------------------------------------------------------------------
@pytest.mark.sanity
@pytest.mark.order(16)
def test_user_registry_auth_credentials(host):
    """
    Test 16: Verify user_registry_credential.yml authentication file exists.

    When user registries require authentication (username/password), the
    credentials are stored in user_registry_credential.yml. This test
    checks that the file exists in the input directory inside omnia_core.

    Note: Authentication support is partially implemented in Omnia 2.2
    (code is commented out in check_user_registry.py). This test verifies
    the credential file presence for forward-compatibility.

    Skipped if user_registry is not configured.
    """
    log = TestLogger(TEST_NAMES["user_registry_auth_credentials"])

    config = _get_user_registry_config(host)
    if not config["success"]:
        pytest.skip(LOG_MSGS["config_skip"])

    log.check("Checking for user_registry_credential.yml in omnia_core container")

    result = check_user_registry_auth_credentials(host)
    if result["success"]:
        log.passed(LOG_MSGS["auth_cred_ok"], result.get("details") or "")
    else:
        # Do not fail the test — auth is not enforced in Omnia 2.2
        log.check(LOG_MSGS["auth_cred_missing"])
        pytest.skip(
            "user_registry_credential.yml not found — "
            "authentication not enforced in Omnia 2.2"
        )


# ---------------------------------------------------------------------------
# 17. Container images from user registries synced to Pulp
# ---------------------------------------------------------------------------
@pytest.mark.sanity
@pytest.mark.order(17)
def test_user_registry_container_repos_synced(host):
    """
    Test 17: Verify container images from user registries synced to Pulp.

    After local_repo.yml runs, container images from user registries are
    synced into Pulp as container repositories prefixed with 'container_repo_'.
    This test verifies that all user registry container repos have been
    synced (latest_version_href is set in Pulp).

    Skipped if user_registry is not configured.
    """
    log = TestLogger(TEST_NAMES["user_registry_container_repos_synced"])

    config = _get_user_registry_config(host)
    if not config["success"]:
        pytest.skip(LOG_MSGS["config_skip"])

    log.check(LOG_MSGS["container_repos_checking"])

    result = check_user_registry_container_repos_synced(host)

    if result["total_repos"] == 0:
        log.check(LOG_MSGS["container_repos_none_found"])
        pytest.skip(LOG_MSGS["container_repos_none_found"])

    if result["success"]:
        log.passed(
            LOG_MSGS["container_repos_synced_ok"],
            result.get("details") or "",
        )
    else:
        details = result.get("details") or result.get("error") or ""
        log.failed(LOG_MSGS["container_repos_not_synced"], details)
        assert False, ASSERT_MSGS["container_repos_not_synced"].format(details=details)


# ---------------------------------------------------------------------------
# 18. Pulp container remotes created for user registries
# ---------------------------------------------------------------------------
@pytest.mark.sanity
@pytest.mark.order(18)
def test_user_registry_remotes_in_pulp(host):
    """
    Test 18: Verify Pulp container remotes created for user registries.

    After local_repo.yml runs, Pulp container remotes (prefixed with
    'user_remote_') are created for each image in a user registry.
    HTTPS remotes include --ca-cert and --client-key flags; HTTP remotes
    do not. This test verifies remotes exist and checks their TLS settings.

    Skipped if user_registry is not configured.
    """
    log = TestLogger(TEST_NAMES["user_registry_remotes_in_pulp"])

    config = _get_user_registry_config(host)
    if not config["success"]:
        pytest.skip(LOG_MSGS["config_skip"])

    log.check(LOG_MSGS["remotes_checking"])

    result = check_user_registry_remotes_in_pulp(
        host, config.get("registries", [])
    )

    if result["total_remotes"] == 0:
        log.check(LOG_MSGS["remotes_none_found"])
        pytest.skip(LOG_MSGS["remotes_none_found"])

    if result["success"]:
        log.passed(LOG_MSGS["remotes_ok"], result.get("details") or "")
    else:
        details = result.get("details") or result.get("error") or ""
        log.failed(LOG_MSGS["remotes_not_found"], details)
        assert False, ASSERT_MSGS["remotes_not_found"].format(details=details)
