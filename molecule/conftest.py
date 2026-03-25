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
Shared pytest configuration for all molecule scenarios.
"""

import os
import sys
import io
import pytest

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from automation_library.core import (
    get_testinfra_host, TestReport, set_current_report, get_current_report, get_test_output
)


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

        print(f"\nSKIPPED REASON: {skip_reason}")

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

    from automation_library.core import load_user_config
    config = load_user_config()
    oim_ip = config.get("oim_server_ip", "")

    # Pre-check 1: Verify OIM IP is configured
    if not oim_ip:
        pytest.fail(
            "oim_server_ip is not set in user_config.yml. "
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
            f"Check oim_server_ip and oim_ssh_port in user_config.yml"
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
                f"Check oim_ssh_user and oim_ssh_password in user_config.yml"
            )
    except Exception as e:
        pytest.fail(
            f"SSH connection to OIM server {oim_ip} failed: {e}\n"
            f"Check oim_server_ip, oim_ssh_user, oim_ssh_password in user_config.yml"
        )

    return h
