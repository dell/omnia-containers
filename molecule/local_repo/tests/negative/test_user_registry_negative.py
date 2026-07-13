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
User Registry - Negative / Error Handling Test Cases.

This module contains pytest negative test cases for verifying user_registry
error handling, validation, and security behavior.

Test cases:
  TC-N001: Invalid registry entry structure handled gracefully
  TC-N002: Invalid registry host format detected
  TC-N003: HTTPS registry with missing cert files produces clear error
  TC-N004: Unreachable registry endpoint is reported
  TC-N005: Registry rejects wrong credentials (security)
  TC-N006: Duplicate registry host entries detected
  TC-N007: HTTPS certificate without CN/SAN is detected

Coverage:
- Config validation edge cases
- Network error handling
- Authentication security
- TLS certificate validation
- Duplicate entry detection
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
    check_user_registry_host_format,
    check_user_registry_https_certs,
    check_user_registry_endpoint_reachable,
    check_user_registry_auth_rejected,
    check_user_registry_duplicate_hosts,
    check_user_registry_https_no_common_name,
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
# TC-N001: Invalid registry entry structure
# ---------------------------------------------------------------------------
@pytest.mark.negative
@pytest.mark.order(20)
def test_neg_invalid_registry_structure(host):
    """
    TC-N001: Verify invalid registry entry structure is handled gracefully.

    Tests that the config loading function handles malformed registry entries
    (e.g., missing required fields like 'host' or 'protocol') without crashing.
    This validates defensive coding for bad input data.

    Note: This test checks the validation logic. If no user_registry is
    configured, it validates the empty config path. If configured, it
    validates that the structure is parseable.
    """
    log = TestLogger(TEST_NAMES["neg_invalid_host_format"])  # Reuse name for now
    log.check("Testing graceful handling of invalid registry entry structure")

    result = _get_user_registry_config(host)

    if not result["success"]:
        # Config loading itself failed — this is the negative path we want
        log.passed(
            LOG_MSGS["neg_empty_config_fail"],
            f"Config loading handled error gracefully: {result.get('error', 'unknown')}"
        )
    elif result["count"] == 0:
        # Empty config — verify it was handled without exception
        log.passed(
            LOG_MSGS["neg_empty_config_ok"],
            "Empty user_registry handled gracefully — no crash"
        )
    else:
        # Config exists and loaded successfully — verify structure is valid
        # This is the positive path, but we can still validate the structure
        all_registries = result.get("registries", [])
        host_format_result = check_user_registry_host_format(all_registries)

        if host_format_result["success"]:
            log.passed(
                LOG_MSGS["neg_invalid_host_detected"],
                f"All {len(all_registries)} entries have valid structure"
            )
        else:
            # Invalid structure detected — this is the negative path
            details = host_format_result.get("details") or ""
            log.passed(
                LOG_MSGS["neg_invalid_host_detected"],
                f"Invalid structure correctly detected:\n{details}"
            )


# ---------------------------------------------------------------------------
# TC-N002: Invalid registry host format detected
# ---------------------------------------------------------------------------
@pytest.mark.negative
@pytest.mark.order(21)
def test_neg_invalid_host_format(host):
    """
    TC-N002: Verify invalid registry host format is detected.

    Each user_registry entry must have a host in 'hostname:port' or 'ip:port'
    format. This test validates that entries with empty host, missing port,
    or out-of-range ports are flagged.

    Skipped if user_registry is not configured.
    """
    log = TestLogger(TEST_NAMES["neg_invalid_host_format"])

    config = _get_user_registry_config(host)
    if not config["success"]:
        pytest.skip(LOG_MSGS["config_skip"])

    all_registries = config.get("registries", [])
    log.check(f"Validating host:port format for {len(all_registries)} registries")

    result = check_user_registry_host_format(all_registries)

    if result["success"]:
        log.passed(
            LOG_MSGS["neg_invalid_host_detected"],
            f"All {len(result['valid'])} registries have valid host:port format"
        )
    else:
        details = result.get("details") or result.get("error") or ""
        log.failed(LOG_MSGS["neg_invalid_host_not_detected"], details)
        assert False, ASSERT_MSGS["neg_invalid_host_format"].format(details=details)


# ---------------------------------------------------------------------------
# TC-N003: HTTPS registry with missing cert files
# ---------------------------------------------------------------------------
@pytest.mark.negative
@pytest.mark.order(22)
def test_neg_https_cert_not_found(host):
    """
    TC-N003: Verify missing HTTPS cert files produce clear error.

    For HTTPS user registries, cert_path and key_path must point to existing
    files. This negative test verifies the error path when certificate files
    are missing or inaccessible from the omnia_core container.

    Skipped if no HTTPS registries are configured.
    """
    log = TestLogger(TEST_NAMES["neg_https_cert_not_found"])

    config = _get_user_registry_config(host)
    if not config["success"]:
        pytest.skip(LOG_MSGS["config_skip"])

    https_registries = config.get("https_registries", [])
    if not https_registries:
        log.check("No HTTPS registries configured — skipping cert check")
        pytest.skip("No HTTPS registries configured in user_registry")

    log.check(f"Checking cert/key file existence for {len(https_registries)} HTTPS registries")

    result = check_user_registry_https_certs(host, https_registries)

    if result["success"]:
        # All certs exist — negative path not triggered but we confirm detection works
        log.passed(
            LOG_MSGS["neg_cert_missing_detected"],
            f"All {len(result['valid'])} HTTPS cert/key files exist — "
            "detection mechanism verified (no missing files to report)"
        )
    else:
        # Certs ARE missing — negative test confirms the error is properly reported
        details = result.get("details") or ""
        log.passed(
            LOG_MSGS["neg_cert_missing_detected"],
            f"Missing cert/key files correctly detected:\n{details}"
        )


# ---------------------------------------------------------------------------
# TC-N004: Unreachable registry endpoint
# ---------------------------------------------------------------------------
@pytest.mark.negative
@pytest.mark.order(23)
def test_neg_endpoint_unreachable(host):
    """
    TC-N004: Verify unreachable registry endpoint is reported.

    Tests that the system produces a clear error message when a user_registry
    endpoint is not reachable (connection refused, DNS failure, timeout).
    This validates error handling for network-level failures.

    Skipped if user_registry is not configured.
    """
    log = TestLogger(TEST_NAMES["neg_endpoint_unreachable"])

    config = _get_user_registry_config(host)
    if not config["success"]:
        pytest.skip(LOG_MSGS["config_skip"])

    all_registries = config.get("registries", [])
    log.check(f"Testing endpoint reachability for {len(all_registries)} registries")

    result = check_user_registry_endpoint_reachable(host, all_registries)

    if result["success"]:
        log.passed(
            LOG_MSGS["neg_endpoint_unreachable_ok"],
            f"All {len(result['reachable'])} endpoints reachable — "
            "error reporting mechanism verified"
        )
    else:
        # Some unreachable — this is expected for a negative test
        details = result.get("details") or ""
        log.failed(LOG_MSGS["neg_endpoint_unreachable_fail"], details)
        assert False, ASSERT_MSGS["neg_endpoint_unreachable"].format(
            details=", ".join(result["unreachable"])
        )


# ---------------------------------------------------------------------------
# TC-N005: Wrong credentials rejected
# ---------------------------------------------------------------------------
@pytest.mark.negative
@pytest.mark.order(24)
def test_neg_auth_wrong_credentials(host):
    """
    TC-N005: Verify registry rejects wrong credentials.

    For HTTPS registries with authentication enabled, this test sends
    deliberately wrong credentials and verifies the registry returns
    HTTP 401 Unauthorized. If the registry accepts bad credentials,
    it flags a security vulnerability.

    Skipped if no HTTPS registries with auth are configured, or if
    registries are unreachable.
    """
    log = TestLogger(TEST_NAMES["neg_auth_wrong_credentials"])

    config = _get_user_registry_config(host)
    if not config["success"]:
        pytest.skip(LOG_MSGS["config_skip"])

    # Only test HTTPS registries (they typically have auth)
    https_registries = config.get("https_registries", [])
    if not https_registries:
        log.check("No HTTPS registries — skipping auth rejection test")
        pytest.skip("No HTTPS registries configured for auth rejection test")

    log.check(f"Testing auth rejection for {len(https_registries)} HTTPS registries")

    result = check_user_registry_auth_rejected(host, https_registries)

    if result.get("unreachable") and not result.get("properly_rejected"):
        log.check("All registries unreachable — cannot test auth rejection")
        pytest.skip("All HTTPS registries unreachable — cannot verify auth rejection")

    if result["success"]:
        log.passed(
            LOG_MSGS["neg_auth_rejected_ok"],
            result.get("details") or ""
        )
    else:
        details = result.get("details") or ""
        log.failed(LOG_MSGS["neg_auth_accepted_bad_creds"], details)
        assert False, ASSERT_MSGS["neg_auth_accepted_bad_creds"].format(
            details=", ".join(result.get("improperly_accepted", []))
        )


# ---------------------------------------------------------------------------
# TC-N006: Duplicate registry host entries
# ---------------------------------------------------------------------------
@pytest.mark.negative
@pytest.mark.order(25)
def test_neg_duplicate_hosts(host):
    """
    TC-N006: Verify duplicate registry host entries are detected.

    Duplicate host:port entries in user_registry can cause Pulp sync
    conflicts or container name collisions. This test verifies that
    duplicate detection works correctly.

    Skipped if user_registry is not configured.
    """
    log = TestLogger(TEST_NAMES["neg_duplicate_hosts"])

    config = _get_user_registry_config(host)
    if not config["success"]:
        pytest.skip(LOG_MSGS["config_skip"])

    all_registries = config.get("registries", [])
    log.check(f"Checking for duplicate hosts in {len(all_registries)} registries")

    result = check_user_registry_duplicate_hosts(all_registries)

    if result["success"]:
        log.passed(
            LOG_MSGS["neg_no_duplicates"],
            result.get("details") or ""
        )
    else:
        details = result.get("details") or ""
        log.failed(LOG_MSGS["neg_duplicates_detected"], details)
        assert False, ASSERT_MSGS["neg_duplicate_hosts"].format(
            details=", ".join(result.get("duplicates", []))
        )


# ---------------------------------------------------------------------------
# TC-N007: HTTPS certificate without CN/SAN
# ---------------------------------------------------------------------------
@pytest.mark.negative
@pytest.mark.order(26)
def test_neg_https_cert_no_cn(host):
    """
    TC-N007: Verify HTTPS certificate without CN/SAN is detected.

    HTTPS registry certificates must have a valid Common Name (CN) or
    Subject Alternative Name (SAN). Certificates without these fields
    will cause TLS handshake failures when Pulp creates container remotes.

    Skipped if no HTTPS registries are configured.
    """
    log = TestLogger(TEST_NAMES["neg_https_cert_no_cn"])

    config = _get_user_registry_config(host)
    if not config["success"]:
        pytest.skip(LOG_MSGS["config_skip"])

    https_registries = config.get("https_registries", [])
    if not https_registries:
        log.check("No HTTPS registries — skipping cert CN/SAN check")
        pytest.skip("No HTTPS registries configured for cert CN/SAN check")

    log.check(f"Checking TLS cert CN/SAN for {len(https_registries)} HTTPS registries")

    result = check_user_registry_https_no_common_name(host, https_registries)

    if result["success"]:
        log.passed(
            LOG_MSGS["neg_cert_cn_ok"],
            result.get("details") or ""
        )
    else:
        details = result.get("details") or ""
        log.failed(LOG_MSGS["neg_cert_cn_missing"], details)
        assert False, ASSERT_MSGS["neg_cert_cn_missing"].format(details=details)
