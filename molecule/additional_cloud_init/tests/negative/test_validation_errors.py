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
Additional Cloud-Init Validation Error Test Cases (Integration).

Each test writes an invalid additional_cloud_init.yml into the omnia_core
container, runs the actual Omnia ``validate_input`` role (L1+L2 validation),
and verifies the playbook fails at the validation task with the expected
error message.  The original config file is always restored afterwards.

Negative test cases:
1.  TC-E01: Missing config file
2.  TC-E02: Invalid YAML syntax
3.  TC-E03: Invalid top-level key
4.  TC-E04: Prohibited key - common section
5.  TC-E05: Prohibited key - groups section
6.  TC-E06: Prohibited key - packages
7.  TC-E07: Unknown allowed key
8.  TC-E08: write_files missing path
9.  TC-E09: runcmd non-string entry
10. TC-E10: Invalid FG name
11. TC-E11: write_files not a list
12. TC-E12: runcmd not a list
13. TC-E13: Empty file (null YAML) - should PASS
14. TC-E14: Multi-error reporting
15. TC-E15: Non-dict root
"""

import pytest
from automation_library.core import TestLogger
from automation_library.additional_cloud_init.functions import (
    run_omnia_validation_playbook,
)
from automation_library.additional_cloud_init.messages import (
    TEST_NAMES,
    TEST_LOG_MSGS,
    TEST_ASSERT_MSGS,
)


@pytest.mark.negative
@pytest.mark.order(101)
def test_missing_config_file(host):
    """
    TC-E01: Verify provision validation fails when config file is missing.

    Temporarily removes additional_cloud_init.yml so the Omnia validation
    encounters a non-existent file path.
    """
    log = TestLogger(TEST_NAMES["missing_config_file"])

    log.check("Removing config file and running Omnia validation")

    try:
        result = run_omnia_validation_playbook(host, remove_config=True)

        if result["validation_passed"]:
            log.failed(
                "Validation should have failed for missing config file",
                f"Playbook exited cleanly (rc={result['rc']})"
            )
            assert False, "Validation should fail when config file is missing"

        has_expected_error = any("File not found" in e or "not found" in e.lower() for e in result["errors"])
        if not has_expected_error:
            has_expected_error = "not found" in result["output"].lower()

        details = (
            f"Playbook rc: {result['rc']}\n"
            f"Errors: {result['errors']}\n"
            f"Contains file-not-found error: {has_expected_error}"
        )

        if not has_expected_error:
            log.failed("Validation failed but without expected file-not-found error", details)
            assert False, f"Expected file-not-found error, got: {result['error_summary']}"

        log.passed("Omnia validation correctly fails for missing config file", details)

    except AssertionError:
        raise
    except Exception as e:
        log.failed(f"Exception: {str(e)}", str(e))
        assert False, f"Exception: {str(e)}"


@pytest.mark.negative
@pytest.mark.order(102)
def test_invalid_yaml_syntax(host):
    """
    TC-E02: Verify provision validation fails for malformed YAML.

    Writes syntactically invalid YAML to the config file and confirms
    the Omnia validation reports a YAML syntax error.
    """
    log = TestLogger(TEST_NAMES["invalid_yaml_syntax"])

    invalid_yaml = "{{invalid_yaml_content}}"
    log.check(f"Writing invalid YAML and running Omnia validation")

    try:
        result = run_omnia_validation_playbook(host, config_content=invalid_yaml)

        if result["validation_passed"]:
            log.failed(
                "Validation should have failed for invalid YAML",
                f"Playbook exited cleanly (rc={result['rc']})"
            )
            assert False, "Validation should fail for invalid YAML syntax"

        has_expected = any("YAML syntax error" in e or "syntax" in e.lower() for e in result["errors"])
        if not has_expected:
            has_expected = "syntax" in result["output"].lower() or "yaml" in result["output"].lower()

        details = (
            f"Invalid YAML content: {invalid_yaml!r}\n"
            f"Playbook rc: {result['rc']}\n"
            f"Errors: {result['errors']}\n"
            f"Contains syntax error: {has_expected}"
        )

        if not has_expected:
            log.failed("Validation failed but without expected YAML syntax error", details)
            assert False, f"Expected YAML syntax error, got: {result['error_summary']}"

        log.passed("Omnia validation correctly fails for invalid YAML", details)

    except AssertionError:
        raise
    except Exception as e:
        log.failed(f"Exception: {str(e)}", str(e))
        assert False, f"Exception: {str(e)}"


@pytest.mark.negative
@pytest.mark.order(103)
def test_invalid_top_level_key(host):
    """
    TC-E03: Verify provision validation fails for unknown top-level keys.

    Only 'common' and 'groups' are allowed at the top level.
    """
    log = TestLogger(TEST_NAMES["invalid_top_level_key"])

    config_yaml = (
        "invalid_key:\n"
        "  runcmd:\n"
        "    - echo test\n"
    )
    log.check("Writing config with invalid top-level key")

    try:
        result = run_omnia_validation_playbook(host, config_content=config_yaml)

        if result["validation_passed"]:
            log.failed(
                "Validation should have failed for invalid top-level key",
                f"Playbook exited cleanly (rc={result['rc']})"
            )
            assert False, "Validation should fail for unknown top-level key 'invalid_key'"

        has_expected = any("Unknown top-level key" in e or "top-level" in e.lower() for e in result["errors"])
        if not has_expected:
            has_expected = "top-level" in result["output"].lower() or "invalid_key" in result["output"]

        details = (
            f"Playbook rc: {result['rc']}\n"
            f"Errors: {result['errors']}\n"
            f"Contains top-level key error: {has_expected}"
        )

        if not has_expected:
            log.failed("Validation failed but without expected top-level key error", details)
            assert False, f"Expected top-level key error, got: {result['error_summary']}"

        log.passed("Omnia validation correctly rejects unknown top-level key", details)

    except AssertionError:
        raise
    except Exception as e:
        log.failed(f"Exception: {str(e)}", str(e))
        assert False, f"Exception: {str(e)}"


@pytest.mark.negative
@pytest.mark.order(104)
def test_prohibited_key_common(host):
    """
    TC-E04: Verify provision validation fails for prohibited keys in common.

    bootcmd, network, network-config, and packages are platform-managed
    and must not appear in the common section.
    """
    log = TestLogger(TEST_NAMES["prohibited_key_common"])

    prohibited_keys = ["bootcmd", "network", "network-config", "packages"]
    results = []

    for key in prohibited_keys:
        config_yaml = f"common:\n  {key}:\n    - echo test\n"
        log.check(f"Testing prohibited key: {key}")

        result = run_omnia_validation_playbook(host, config_content=config_yaml)
        passed = result["validation_passed"]
        has_error = any("Prohibited key" in e or "prohibited" in e.lower() for e in result["errors"])

        results.append({"key": key, "passed": passed, "has_error": has_error, "errors": result["errors"]})

        if passed:
            log.check(f"  ✗ {key}: Validation should have failed")
        elif has_error:
            log.check(f"  ✓ {key}: Correctly rejected as prohibited")
        else:
            log.check(f"  ? {key}: Failed but without prohibited-key error")

    incorrect = [r for r in results if r["passed"]]
    details_lines = [f"Prohibited keys in common: {len(prohibited_keys)} tested", ""]
    for r in results:
        status = "✗ PASSED (SHOULD FAIL)" if r["passed"] else "✓ FAILED (CORRECT)"
        details_lines.append(f"  {r['key']}: {status}")
    details = "\n".join(details_lines)

    if incorrect:
        log.failed(f"{len(incorrect)} prohibited key(s) incorrectly passed", details)
        assert False, f"These prohibited keys should have been rejected: {[r['key'] for r in incorrect]}"

    log.passed(f"All {len(prohibited_keys)} prohibited keys correctly rejected in common section", details)


@pytest.mark.negative
@pytest.mark.order(105)
def test_prohibited_key_groups(host):
    """
    TC-E05: Verify provision validation fails for prohibited keys in groups.

    Same prohibition rules apply to per-functional-group sections.
    """
    log = TestLogger(TEST_NAMES["prohibited_key_groups"])

    prohibited_keys = ["bootcmd", "network", "network-config", "packages"]
    results = []

    for key in prohibited_keys:
        config_yaml = (
            "groups:\n"
            "  test_fg:\n"
            f"    {key}:\n"
            "      - echo test\n"
        )
        log.check(f"Testing prohibited key in groups: {key}")

        result = run_omnia_validation_playbook(host, config_content=config_yaml)
        passed = result["validation_passed"]
        has_error = any("Prohibited key" in e or "prohibited" in e.lower() for e in result["errors"])

        results.append({"key": key, "passed": passed, "has_error": has_error})

        if passed:
            log.check(f"  ✗ {key}: Validation should have failed")
        elif has_error:
            log.check(f"  ✓ {key}: Correctly rejected as prohibited in groups")
        else:
            log.check(f"  ? {key}: Failed but without prohibited-key error")

    incorrect = [r for r in results if r["passed"]]
    details_lines = [f"Prohibited keys in groups: {len(prohibited_keys)} tested", ""]
    for r in results:
        status = "✗ PASSED (SHOULD FAIL)" if r["passed"] else "✓ FAILED (CORRECT)"
        details_lines.append(f"  groups.test_fg.{r['key']}: {status}")
    details = "\n".join(details_lines)

    if incorrect:
        log.failed(f"{len(incorrect)} prohibited key(s) incorrectly passed in groups", details)
        assert False, f"Prohibited keys in groups should have been rejected: {[r['key'] for r in incorrect]}"

    log.passed(f"All {len(prohibited_keys)} prohibited keys correctly rejected in groups section", details)


@pytest.mark.negative
@pytest.mark.order(106)
def test_prohibited_key_packages(host):
    """
    TC-E06: Verify provision validation fails for packages key specifically.

    packages is platform-managed; test in both common and groups sections.
    """
    log = TestLogger(TEST_NAMES["prohibited_key_packages"])

    configs = [
        ("common packages", "common:\n  packages:\n    - vim\n    - git\n"),
        ("groups packages", "groups:\n  test_fg:\n    packages:\n      - python3\n"),
        ("mixed with valid", "common:\n  packages:\n    - curl\n  write_files:\n    - path: /tmp/test\n      content: hello\n"),
    ]
    results = []

    for label, config_yaml in configs:
        log.check(f"Testing: {label}")
        result = run_omnia_validation_playbook(host, config_content=config_yaml)
        passed = result["validation_passed"]
        has_packages_error = any("packages" in e.lower() and "rohibited" in e for e in result["errors"])

        results.append({"label": label, "passed": passed, "has_packages_error": has_packages_error})

        if passed:
            log.check(f"  ✗ {label}: Validation should have failed")
        else:
            log.check(f"  ✓ {label}: Correctly rejected")

    incorrect = [r for r in results if r["passed"]]
    details_lines = [f"Packages key prohibition: {len(configs)} configs tested", ""]
    for r in results:
        status = "✗ PASSED (SHOULD FAIL)" if r["passed"] else "✓ FAILED (CORRECT)"
        details_lines.append(f"  {r['label']}: {status}")
    details = "\n".join(details_lines)

    if incorrect:
        log.failed(f"{len(incorrect)} packages config(s) incorrectly passed", details)
        assert False, f"Configs with packages key should be rejected: {[r['label'] for r in incorrect]}"

    log.passed(f"All {len(configs)} packages key configs correctly rejected", details)


@pytest.mark.negative
@pytest.mark.order(107)
def test_unknown_allowed_key(host):
    """
    TC-E07: Verify provision validation fails for unknown section keys.

    Only 'write_files' and 'runcmd' are allowed inside common/groups sections.
    """
    log = TestLogger(TEST_NAMES["unknown_allowed_key"])

    configs = [
        ("common unknown_key", "common:\n  unknown_key: value\n"),
        ("common custom_script", "common:\n  custom_script:\n    - echo test\n"),
        ("groups mystery_config", "groups:\n  test_fg:\n    mystery_config:\n      key: val\n"),
    ]
    results = []

    for label, config_yaml in configs:
        log.check(f"Testing: {label}")
        result = run_omnia_validation_playbook(host, config_content=config_yaml)
        passed = result["validation_passed"]
        has_error = any("Unknown key" in e or "nknown" in e for e in result["errors"])

        results.append({"label": label, "passed": passed, "has_error": has_error})

        if passed:
            log.check(f"  ✗ {label}: Validation should have failed")
        else:
            log.check(f"  ✓ {label}: Correctly rejected")

    incorrect = [r for r in results if r["passed"]]
    details_lines = [f"Unknown key validation: {len(configs)} tested", "Allowed keys: write_files, runcmd", ""]
    for r in results:
        status = "✗ PASSED (SHOULD FAIL)" if r["passed"] else "✓ FAILED (CORRECT)"
        details_lines.append(f"  {r['label']}: {status}")
    details = "\n".join(details_lines)

    if incorrect:
        log.failed(f"{len(incorrect)} unknown key config(s) incorrectly passed", details)
        assert False, f"Unknown keys should be rejected: {[r['label'] for r in incorrect]}"

    log.passed(f"All {len(configs)} unknown key configs correctly rejected", details)


@pytest.mark.negative
@pytest.mark.order(108)
def test_write_files_missing_path(host):
    """
    TC-E08: Verify provision validation fails when write_files entry has no path.

    Every write_files entry must contain the 'path' field.
    """
    log = TestLogger(TEST_NAMES["write_files_missing_path"])

    config_yaml = (
        "common:\n"
        "  write_files:\n"
        "    - content: this entry has no path\n"
        "      permissions: '0644'\n"
    )
    log.check("Writing config with write_files missing path field")

    try:
        result = run_omnia_validation_playbook(host, config_content=config_yaml)

        if result["validation_passed"]:
            log.failed(
                "Validation should have failed for write_files missing path",
                f"Playbook exited cleanly (rc={result['rc']})"
            )
            assert False, "write_files entry without path should be rejected"

        has_expected = any("path" in e.lower() for e in result["errors"])
        if not has_expected:
            has_expected = "path" in result["output"].lower()

        details = (
            f"Playbook rc: {result['rc']}\n"
            f"Errors: {result['errors']}\n"
            f"Contains missing-path error: {has_expected}"
        )

        if not has_expected:
            log.failed("Validation failed but without expected missing-path error", details)
            assert False, f"Expected missing-path error, got: {result['error_summary']}"

        log.passed("Omnia validation correctly rejects write_files without path", details)

    except AssertionError:
        raise
    except Exception as e:
        log.failed(f"Exception: {str(e)}", str(e))
        assert False, f"Exception: {str(e)}"


@pytest.mark.negative
@pytest.mark.order(109)
def test_runcmd_non_string(host):
    """
    TC-E09: Verify provision validation fails for non-string runcmd entries.

    Every runcmd entry must be a string.  YAML-native integers or dicts
    must be rejected.
    """
    log = TestLogger(TEST_NAMES["runcmd_non_string"])

    config_yaml = (
        "common:\n"
        "  runcmd:\n"
        "    - echo valid_command\n"
        "    - 12345\n"
    )
    log.check("Writing config with non-string runcmd entry (integer)")

    try:
        result = run_omnia_validation_playbook(host, config_content=config_yaml)

        if result["validation_passed"]:
            log.failed(
                "Validation should have failed for non-string runcmd entry",
                f"Playbook exited cleanly (rc={result['rc']})"
            )
            assert False, "runcmd entries must be strings"

        has_expected = any("not a string" in e.lower() or "string" in e.lower() for e in result["errors"])
        if not has_expected:
            has_expected = "string" in result["output"].lower()

        details = (
            f"Playbook rc: {result['rc']}\n"
            f"Errors: {result['errors']}\n"
            f"Contains non-string error: {has_expected}"
        )

        if not has_expected:
            log.failed("Validation failed but without expected non-string error", details)
            assert False, f"Expected non-string runcmd error, got: {result['error_summary']}"

        log.passed("Omnia validation correctly rejects non-string runcmd entry", details)

    except AssertionError:
        raise
    except Exception as e:
        log.failed(f"Exception: {str(e)}", str(e))
        assert False, f"Exception: {str(e)}"


@pytest.mark.negative
@pytest.mark.order(110)
def test_invalid_fg_name(host):
    """
    TC-E10: Verify provision validation fails for invalid FG names.

    Functional group names in the 'groups' section must match entries
    in the PXE mapping file.
    """
    log = TestLogger(TEST_NAMES["invalid_fg_name"])

    config_yaml = (
        "groups:\n"
        "  nonexistent_fg_name:\n"
        "    runcmd:\n"
        "      - echo test\n"
    )
    log.check("Writing config with invalid functional group name")

    try:
        result = run_omnia_validation_playbook(host, config_content=config_yaml)

        if result["validation_passed"]:
            log.failed(
                "Validation should have failed for invalid FG name",
                f"Playbook exited cleanly (rc={result['rc']})"
            )
            assert False, "Invalid functional group name should be rejected"

        has_expected = any(
            "functional group" in e.lower() or "nonexistent_fg_name" in e
            for e in result["errors"]
        )
        if not has_expected:
            has_expected = "nonexistent_fg_name" in result["output"]

        details = (
            f"Playbook rc: {result['rc']}\n"
            f"Errors: {result['errors']}\n"
            f"Contains invalid FG error: {has_expected}"
        )

        if not has_expected:
            log.failed("Validation failed but without expected FG-name error", details)
            assert False, f"Expected invalid FG name error, got: {result['error_summary']}"

        log.passed("Omnia validation correctly rejects invalid functional group name", details)

    except AssertionError:
        raise
    except Exception as e:
        log.failed(f"Exception: {str(e)}", str(e))
        assert False, f"Exception: {str(e)}"


@pytest.mark.negative
@pytest.mark.order(111)
def test_write_files_not_list(host):
    """
    TC-E11: Verify provision validation fails when write_files is not a list.

    write_files must be a YAML list/sequence, not a scalar or mapping.
    """
    log = TestLogger(TEST_NAMES["write_files_not_list"])

    config_yaml = (
        "common:\n"
        "  write_files: not_a_list\n"
    )
    log.check("Writing config with write_files as string instead of list")

    try:
        result = run_omnia_validation_playbook(host, config_content=config_yaml)

        if result["validation_passed"]:
            log.failed(
                "Validation should have failed for write_files not a list",
                f"Playbook exited cleanly (rc={result['rc']})"
            )
            assert False, "write_files must be a list"

        has_expected = any("must be a list" in e.lower() or "list" in e.lower() for e in result["errors"])
        if not has_expected:
            has_expected = "list" in result["output"].lower()

        details = (
            f"Playbook rc: {result['rc']}\n"
            f"Errors: {result['errors']}\n"
            f"Contains must-be-list error: {has_expected}"
        )

        if not has_expected:
            log.failed("Validation failed but without expected type error", details)
            assert False, f"Expected must-be-list error, got: {result['error_summary']}"

        log.passed("Omnia validation correctly rejects write_files that is not a list", details)

    except AssertionError:
        raise
    except Exception as e:
        log.failed(f"Exception: {str(e)}", str(e))
        assert False, f"Exception: {str(e)}"


@pytest.mark.negative
@pytest.mark.order(112)
def test_runcmd_not_list(host):
    """
    TC-E12: Verify provision validation fails when runcmd is not a list.

    runcmd must be a YAML list/sequence, not a scalar or mapping.
    """
    log = TestLogger(TEST_NAMES["runcmd_not_list"])

    config_yaml = (
        "common:\n"
        "  runcmd: echo single_command\n"
    )
    log.check("Writing config with runcmd as string instead of list")

    try:
        result = run_omnia_validation_playbook(host, config_content=config_yaml)

        if result["validation_passed"]:
            log.failed(
                "Validation should have failed for runcmd not a list",
                f"Playbook exited cleanly (rc={result['rc']})"
            )
            assert False, "runcmd must be a list"

        has_expected = any("must be a list" in e.lower() or "list" in e.lower() for e in result["errors"])
        if not has_expected:
            has_expected = "list" in result["output"].lower()

        details = (
            f"Playbook rc: {result['rc']}\n"
            f"Errors: {result['errors']}\n"
            f"Contains must-be-list error: {has_expected}"
        )

        if not has_expected:
            log.failed("Validation failed but without expected type error", details)
            assert False, f"Expected must-be-list error, got: {result['error_summary']}"

        log.passed("Omnia validation correctly rejects runcmd that is not a list", details)

    except AssertionError:
        raise
    except Exception as e:
        log.failed(f"Exception: {str(e)}", str(e))
        assert False, f"Exception: {str(e)}"


@pytest.mark.negative
@pytest.mark.order(113)
def test_empty_file_null_yaml(host):
    """
    TC-E13: Verify empty/null config file passes validation (feature disabled).

    An empty YAML file (parsed as ``None``) should NOT cause a validation
    failure - Omnia treats it as "feature disabled".
    """
    log = TestLogger(TEST_NAMES["empty_file_null_yaml"])

    configs = [
        ("empty file", ""),
        ("YAML null", "---\n"),
        ("empty common", "common: {}\n"),
        ("empty groups", "groups: {}\n"),
        ("both empty", "common: {}\ngroups: {}\n"),
    ]
    results = []

    for label, config_yaml in configs:
        log.check(f"Testing: {label}")
        result = run_omnia_validation_playbook(host, config_content=config_yaml)
        results.append({"label": label, "passed": result["validation_passed"]})

        if result["validation_passed"]:
            log.check(f"  ✓ {label}: Validation passed (correct)")
        else:
            log.check(f"  ✗ {label}: Validation failed (should have passed)")

    failed = [r for r in results if not r["passed"]]
    details_lines = [f"Empty/null config validation: {len(configs)} tested", ""]
    for r in results:
        status = "✓ PASSED (CORRECT)" if r["passed"] else "✗ FAILED (SHOULD PASS)"
        details_lines.append(f"  {r['label']}: {status}")
    details = "\n".join(details_lines)

    if failed:
        log.failed(f"{len(failed)} empty config(s) incorrectly failed validation", details)
        assert False, f"Empty configs should pass: {[r['label'] for r in failed]}"

    log.passed(f"All {len(configs)} empty/null configs correctly treated as valid (disabled)", details)


@pytest.mark.negative
@pytest.mark.order(114)
def test_multi_error_reporting(host):
    """
    TC-E14: Verify Omnia reports multiple errors in a single validation pass.

    A config with several different error types should produce multiple
    validation errors without early termination.
    """
    log = TestLogger(TEST_NAMES["multi_error_reporting"])

    config_yaml = (
        "invalid_top_level_key: {}\n"
        "common:\n"
        "  bootcmd:\n"
        "    - prohibited_cmd\n"
        "  unknown_key: not_allowed\n"
        "  write_files:\n"
        "    - content: missing path field\n"
        "  runcmd:\n"
        "    - valid string\n"
        "    - 12345\n"
        "groups:\n"
        "  nonexistent_fg:\n"
        "    packages:\n"
        "      - prohibited_pkg\n"
    )
    log.check("Writing config with multiple intentional errors")

    try:
        result = run_omnia_validation_playbook(host, config_content=config_yaml)

        if result["validation_passed"]:
            log.failed(
                "Multi-error config incorrectly passed validation",
                f"Playbook exited cleanly (rc={result['rc']})"
            )
            assert False, "Configuration with multiple errors should fail validation"

        errors = result["errors"]
        error_text = result["error_summary"].lower()

        expected_patterns = {
            "top-level key": "top-level" in error_text or any("top-level" in e.lower() for e in errors),
            "prohibited key": "prohibited" in error_text or any("rohibited" in e for e in errors),
            "unknown key": "unknown" in error_text or any("nknown" in e for e in errors),
            "missing path": "path" in error_text or any("path" in e.lower() for e in errors),
            "non-string runcmd": "string" in error_text or any("string" in e.lower() for e in errors),
            "invalid FG": "nonexistent_fg" in error_text or any("nonexistent_fg" in e for e in errors),
        }

        found_count = sum(1 for v in expected_patterns.values() if v)
        min_required = 3

        details_lines = [
            f"Multi-error reporting:",
            f"  Total errors parsed: {len(errors)}",
            f"  Error categories found: {found_count}/{len(expected_patterns)}",
            ""
        ]
        for pattern, found in expected_patterns.items():
            status = "✓" if found else "?"
            details_lines.append(f"  {status} {pattern}")
        details_lines.append("")
        details_lines.append("Individual errors:")
        for i, err in enumerate(errors):
            details_lines.append(f"  {i+1}. {err[:120]}")
        details = "\n".join(details_lines)

        if found_count < min_required:
            log.failed(
                f"Insufficient error categories: {found_count}, need >= {min_required}",
                details
            )
            assert False, f"Multi-error reporting found {found_count} categories, expected >= {min_required}"

        log.passed(f"Multi-error reporting correct: {found_count} error categories detected", details)

    except AssertionError:
        raise
    except Exception as e:
        log.failed(f"Exception: {str(e)}", str(e))
        assert False, f"Exception: {str(e)}"


@pytest.mark.negative
@pytest.mark.order(115)
def test_non_dict_root(host):
    """
    TC-E15: Verify provision validation fails when config root is not a dict.

    A YAML file that parses to a list or scalar must be rejected.
    """
    log = TestLogger(TEST_NAMES["non_dict_root"])

    config_yaml = (
        "- this\n"
        "- is\n"
        "- a\n"
        "- list\n"
    )
    log.check("Writing config with list root instead of dict")

    try:
        result = run_omnia_validation_playbook(host, config_content=config_yaml)

        if result["validation_passed"]:
            log.failed(
                "Validation should have failed for non-dict root",
                f"Playbook exited cleanly (rc={result['rc']})"
            )
            assert False, "Non-dict root config should be rejected"

        has_expected = any("mapping" in e.lower() or "dict" in e.lower() for e in result["errors"])
        if not has_expected:
            has_expected = "mapping" in result["output"].lower() or "dict" in result["output"].lower()

        details = (
            f"Playbook rc: {result['rc']}\n"
            f"Errors: {result['errors']}\n"
            f"Contains non-dict error: {has_expected}"
        )

        if not has_expected:
            log.failed("Validation failed but without expected non-dict error", details)
            assert False, f"Expected non-dict root error, got: {result['error_summary']}"

        log.passed("Omnia validation correctly rejects non-dict root config", details)

    except AssertionError:
        raise
    except Exception as e:
        log.failed(f"Exception: {str(e)}", str(e))
        assert False, f"Exception: {str(e)}"
