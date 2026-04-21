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
Shared pytest configuration for all molecule scenarios.
"""

import os
import sys
import io
import pytest

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from automation_library.core import (
    get_testinfra_host, TestReport, set_current_report, get_current_report, get_test_output,
    TestLogger, is_build_stream_enabled,
)


# =============================================================================
# SHARED BUILD_STREAM JOB STATE
# =============================================================================
# Module-level dict to track build_stream job validation state.
# Set by test_build_stream_job_stage in each module, used by autouse fixture
# to skip remaining tests when job is not COMPLETED.
#
# Each test module that uses build_stream should:
# 1. Import this dict: from molecule.conftest import build_stream_job_state
# 2. Set values in test_build_stream_job_stage after validation
# 3. The autouse fixture below will handle skipping automatically
# =============================================================================
build_stream_job_state: dict = {
    "checked": False,
    "success": None,
    "job_id": None,
    "job_state": None,
    "error": None,
}


class _TeeStream:
    def __init__(self, primary, buffer):
        self._primary = primary
        self._buffer = buffer

    def write(self, s):
        self._buffer.write(s)
        return self._primary.write(s)

    def flush(self):
        try:
            self._buffer.flush()
        except Exception:
            pass
        return self._primary.flush()

    def isatty(self):
        isatty = getattr(self._primary, "isatty", None)
        return bool(isatty and isatty())

    @property
    def encoding(self):
        return getattr(self._primary, "encoding", "utf-8")


def pytest_configure(config):
    """Pytest configuration."""
    config.addinivalue_line("filterwarnings", "ignore::pytest.PytestCollectionWarning")
    # Register custom markers
    config.addinivalue_line("markers", "cleanup: marks tests as cleanup verification (deselected by default)")
    config.addinivalue_line("markers", "order(n): specify test execution order (lower numbers run first)")
    # Test suite markers
    config.addinivalue_line("markers", "sanity: marks tests as sanity tests (basic functionality)")
    config.addinivalue_line("markers", "negative: marks tests as negative tests (error handling)")
    config.addinivalue_line("markers", "regression: marks tests as regression tests (full coverage)")
    config.addinivalue_line("markers", "smoke: marks tests as smoke tests (critical path only)")


def pytest_collection_modifyitems(session, config, items):
    """
    Modify test collection to control execution order.

    Tests are ordered by:
    1. @pytest.mark.order(n) marker - lower numbers run first
    2. Test file name (alphabetical)
    3. Test function order in file

    This allows controlling test order without renaming files.
    """
    def get_order_key(item):
        # Check for @pytest.mark.order(n) marker
        order_marker = item.get_closest_marker("order")
        if order_marker and order_marker.args:
            return (0, order_marker.args[0], item.fspath.basename, item.name)
        # Default: sort by file name then function name
        return (1, 0, item.fspath.basename, item.name)

    items.sort(key=get_order_key)


def pytest_sessionstart(session):
    """Called before test collection - initialize report."""
    module_name = "unknown"
    if session.config.args:
        path = session.config.args[0]
        # Extract scenario name from path (e.g., molecule/omnia_sh_install/tests -> omnia_sh_install)
        parts = path.split("/")
        for i, part in enumerate(parts):
            if part == "molecule" and i + 1 < len(parts):
                module_name = parts[i + 1]
                break
        # Fallback to old logic
        if module_name == "unknown":
            for part in parts:
                if part and part != "tests" and part != "molecule":
                    module_name = part
                    break

    report_id = os.environ.get("OMNIA_REPORT_ID")
    report = TestReport(module_name, report_id)
    set_current_report(report)


def pytest_sessionfinish(session, exitstatus):
    """Called after all tests - save report."""
    report = get_current_report()
    if report and report.results:
        report.save()


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_call(item):
    buf = io.StringIO()
    orig_out, orig_err = sys.stdout, sys.stderr
    sys.stdout = _TeeStream(orig_out, buf)
    sys.stderr = _TeeStream(orig_err, buf)
    try:
        yield
    finally:
        sys.stdout, sys.stderr = orig_out, orig_err
        item._omnia_captured_output = buf.getvalue()


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """Hook to capture test results and output."""
    outcome = yield
    result = outcome.get_result()

    report = get_current_report()
    if not report:
        return

    if result.when not in {"call", "setup"}:
        return

    if result.when == "setup" and result.outcome != "skipped":
        return

    duration = result.duration if hasattr(result, "duration") else 0
    output = getattr(item, "_omnia_captured_output", None) or get_test_output(item.name)

    skip_reason = None
    if result.outcome == "skipped":
        longrepr = getattr(result, "longrepr", None)
        if isinstance(longrepr, tuple) and len(longrepr) >= 3:
            skip_reason = longrepr[2]
        else:
            skip_reason = str(longrepr) if longrepr else "Skipped"

    if result.outcome == "passed":
        status = "PASSED"
    elif result.outcome == "failed":
        status = "FAILED"
    else:
        status = "SKIPPED"

    error = None
    if status == "FAILED":
        error = str(result.longrepr) if result.longrepr else None

    details = output if output else None
    if status == "SKIPPED" and skip_reason:
        details = (details + "\n" if details else "") + f"SKIPPED: {skip_reason}"

    report.add_result(
        {
            "test_name": item.name,
            "status": status,
            "duration": duration,
            "details": details,
            "error": error,
        },
    )


@pytest.fixture(scope="module")
def host():
    """Testinfra host fixture - connects to OIM server."""
    import shutil
    import subprocess as _sp

    from automation_library.core import load_omnia_test_config
    config = load_omnia_test_config()
    oim_ip = config.get("oim_server_ip", "")

    # Pre-check 1: Verify OIM IP is configured
    if not oim_ip:
        pytest.fail(
            "oim_server_ip is not set in omnia_test_config.yml. "
            "Please configure the OIM server IP before running tests."
        )

    # Pre-check 2: Verify sshpass is installed (needed for password-based SSH)
    if not shutil.which("sshpass"):
        pytest.fail(
            "sshpass is not installed. It is required for SSH password authentication.\n"
            "Install it: dnf install -y sshpass (RHEL) or apt install -y sshpass (Ubuntu)"
        )

    # Pre-check 3: Verify OIM server is reachable (basic TCP check on SSH port)
    ssh_port = config.get("oim_ssh_port", 22)
    try:
        _sp.run(
            ["bash", "-c", f"echo > /dev/tcp/{oim_ip}/{ssh_port}"],
            capture_output=True, timeout=5, check=True
        )
    except (_sp.CalledProcessError, _sp.TimeoutExpired, OSError):
        pytest.fail(
            f"OIM server {oim_ip}:{ssh_port} is not reachable.\n"
            f"Check oim_server_ip and oim_ssh_port in omnia_test_config.yml"
        )

    # Pre-check 4: Verify SSH authentication works
    h = get_testinfra_host()
    try:
        result = h.run("echo ok")
        if result.rc != 0 or "ok" not in result.stdout:
            stderr = result.stderr.strip() if result.stderr else ""
            pytest.fail(
                f"SSH to OIM server {oim_ip} failed (rc={result.rc}).\n"
                f"Error: {stderr}\n"
                f"Check oim_ssh_user and oim_ssh_password in omnia_test_config.yml"
            )
    except Exception as e:
        pytest.fail(
            f"SSH connection to OIM server {oim_ip} failed: {e}\n"
            f"Check oim_server_ip, oim_ssh_user, oim_ssh_password in omnia_test_config.yml"
        )

    return h


# =============================================================================
# SHARED BUILD_STREAM AUTOUSE FIXTURE
# =============================================================================
@pytest.fixture(autouse=True)
def _require_build_stream_job(host, request):
    """
    Autouse fixture: skip any test (except test_build_stream_job_stage) when
    build_stream is enabled but the job stage check did not pass.

    This fixture is shared across all modules that use build_stream validation.
    Each module's test_build_stream_job_stage must set build_stream_job_state
    values after validation.

    Uses log.skipped() so skips appear properly in test report.
    """
    # Skip the job-stage test itself (it sets the state)
    if request.node.name == "test_build_stream_job_stage":
        yield
        return

    # Only skip if build_stream is enabled AND job check failed
    if (is_build_stream_enabled(host) and
            build_stream_job_state["checked"] and
            not build_stream_job_state["success"]):

        # Use TestLogger to properly report the skip in test output/report
        log = TestLogger(request.node.name)
        job_id = build_stream_job_state.get("job_id", "unknown")
        job_state = build_stream_job_state.get("job_state", "NOT FOUND")
        error = build_stream_job_state.get("error", "unknown error")

        # Use very short skip reason with exact state for pytest (to avoid truncation)
        # Put detailed error in log.skipped details (with proper line breaks)
        short_skip_reason = job_state
        detailed_error = f"build_stream job is {job_state} — skipping test.\nFix: {error}"
        
        log.skipped(
            f"Skipped due to build_stream job failure (job_id: {job_id})",
            detailed_error
        )
        pytest.skip(short_skip_reason)

    yield


def reset_build_stream_state():
    """Reset build_stream job state. Call at start of each test module."""
    build_stream_job_state["checked"] = False
    build_stream_job_state["success"] = None
    build_stream_job_state["job_id"] = None
    build_stream_job_state["job_state"] = None
    build_stream_job_state["error"] = None
