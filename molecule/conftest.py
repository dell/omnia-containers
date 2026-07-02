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

Test Markers:
- sanity: Basic functionality tests (default test suite)
- negative: Error handling tests
- regression: Full coverage tests
- smoke: Critical path only tests
- build_stream: Build stream pipeline validation tests
- cleanup: Cleanup verification tests (deselected by default)

Usage Examples:
  pytest -m sanity                    # Run all sanity tests (includes build_stream)
  pytest -m build_stream              # Run only build_stream tests
  pytest -m "sanity and build_stream" # Run tests with both markers
  pytest -m "sanity and not build_stream" # Run sanity tests excluding build_stream
"""

import os
import sys
import io
import pytest

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from automation_library.core import (
    get_testinfra_host, is_local_execution, TestReport, set_current_report, get_current_report, get_test_output,
    TestLogger, is_build_stream_enabled, encrypt_omnia_test_credentials,
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


# =============================================================================
# DCGM GPU NODE PARAMETRIZATION STATE
# =============================================================================
# Module-level state for DCGM GPU node discovery and parametrization.
# Used by dcgm scenario to parametrize tests across all GPU nodes.
#
# Only active when running dcgm scenario tests.
# =============================================================================
_gpu_node_ips: list = []
_gpu_collection_error: str = None
_login_compiler_ips: list = []
_login_compiler_collection_error: str = None


# =============================================================================
# HPC BENCHMARKS NODE PARAMETRIZATION STATE
# =============================================================================
# Module-level state for HPC benchmark node discovery and parametrization.
# Used by hpc_benchmarks scenario to parametrize tests across cluster nodes.
#
# Only active when running hpc_benchmarks scenario tests.
# =============================================================================
_x86_64_node_ips: list = []
_x86_64_node_collection_error: str = None
_aarch64_node_ips: list = []
_aarch64_node_collection_error: str = None
_x86_64_login_compiler_ips: list = []
_x86_64_login_compiler_collection_error: str = None
_aarch64_login_compiler_ips: list = []
_aarch64_login_compiler_collection_error: str = None
_all_cluster_node_ips: list = []
_all_cluster_node_collection_error: str = None
_all_login_compiler_ips: list = []
_all_login_compiler_collection_error: str = None


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
    config.addinivalue_line("markers", "build_stream: marks tests as build stream related tests (pipeline validation)")
    config.addinivalue_line("markers", "deploy: marks tests as deploy pipeline tests")
    config.addinivalue_line("markers", "stress: marks tests as stress/load tests (e.g., repeated pipeline runs)")
    config.addinivalue_line("markers", "build: marks tests as build pipeline tests")

    # DCGM GPU node collection - only for dcgm scenario
    _collect_dcgm_gpu_nodes(config)

    # HPC benchmarks node collection - only for hpc_benchmarks scenario
    _collect_hpc_benchmark_nodes(config)


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


def _collect_dcgm_gpu_nodes(config):
    """Collect GPU node IPs and login_compiler IPs for DCGM scenario parametrization."""
    global _gpu_node_ips, _gpu_collection_error, _login_compiler_ips, _login_compiler_collection_error

    # Only run for dcgm scenario
    if config.args:
        path = config.args[0] if config.args else ""
        if "dcgm" not in path:
            return

    try:
        from automation_library.dcgm.functions import get_gpu_nodes, get_login_compiler_nodes
        from automation_library.dcgm.messages import TEST_ASSERT_MSGS as ASSERT

        host = get_testinfra_host()
        
        # Collect GPU nodes
        nodes = get_gpu_nodes(host)
        _gpu_node_ips = [node["admin_ip"] for node in nodes] if nodes else []
        
        # Collect login_compiler nodes
        lc_nodes = get_login_compiler_nodes(host)
        _login_compiler_ips = [node["admin_ip"] for node in lc_nodes] if lc_nodes else []
    except Exception as e:
        _gpu_collection_error = f"GPU node collection failed: {e}"
        _login_compiler_collection_error = f"Login compiler node collection failed: {e}"
        _gpu_node_ips = []
        _login_compiler_ips = []


def _collect_hpc_benchmark_nodes(config):
    """Collect x86_64 and aarch64 node IPs for HPC benchmarks scenario parametrization."""
    global _x86_64_node_ips, _x86_64_node_collection_error
    global _aarch64_node_ips, _aarch64_node_collection_error
    global _x86_64_login_compiler_ips, _x86_64_login_compiler_collection_error
    global _aarch64_login_compiler_ips, _aarch64_login_compiler_collection_error
    global _all_cluster_node_ips, _all_cluster_node_collection_error
    global _all_login_compiler_ips, _all_login_compiler_collection_error

    # Only run for hpc_benchmarks scenario
    if config.args:
        path = config.args[0] if config.args else ""
        if "hpc_benchmarks" not in path:
            return

    try:
        from automation_library.hpc_benchmarks.functions import (
            get_x86_64_cluster_nodes,
            get_aarch64_cluster_nodes,
            get_login_compiler_nodes_x86_64,
            get_login_compiler_nodes_aarch64,
        )

        host = get_testinfra_host()

        # Collect x86_64 cluster nodes
        x86_nodes = get_x86_64_cluster_nodes(host)
        _x86_64_node_ips = [n["admin_ip"] for n in x86_nodes] if x86_nodes else []

        # Collect aarch64 cluster nodes
        aa64_nodes = get_aarch64_cluster_nodes(host)
        _aarch64_node_ips = [n["admin_ip"] for n in aa64_nodes] if aa64_nodes else []

        # Collect x86_64 login/compiler nodes
        lc_nodes = get_login_compiler_nodes_x86_64(host)
        _x86_64_login_compiler_ips = [n["admin_ip"] for n in lc_nodes] if lc_nodes else []

        # Collect aarch64 login/compiler nodes
        lc_aa64_nodes = get_login_compiler_nodes_aarch64(host)
        _aarch64_login_compiler_ips = [n["admin_ip"] for n in lc_aa64_nodes] if lc_aa64_nodes else []

        # Build generic lists (any arch)
        _all_cluster_node_ips = _x86_64_node_ips + _aarch64_node_ips
        _all_login_compiler_ips = _x86_64_login_compiler_ips + _aarch64_login_compiler_ips
    except Exception as e:
        _x86_64_node_collection_error = f"x86_64 node collection failed: {e}"
        _aarch64_node_collection_error = f"aarch64 node collection failed: {e}"
        _x86_64_login_compiler_collection_error = f"x86_64 login/compiler node collection failed: {e}"
        _aarch64_login_compiler_collection_error = f"aarch64 login/compiler node collection failed: {e}"
        _all_cluster_node_collection_error = f"Cluster node collection failed: {e}"
        _all_login_compiler_collection_error = f"Login/compiler node collection failed: {e}"
        _x86_64_node_ips = []
        _aarch64_node_ips = []
        _x86_64_login_compiler_ips = []
        _aarch64_login_compiler_ips = []
        _all_cluster_node_ips = []
        _all_login_compiler_ips = []


def pytest_generate_tests(metafunc):
    """Parametrize tests with node IP fixtures for DCGM and HPC benchmarks scenarios."""
    # Parametrize gpu_node_ip
    if "gpu_node_ip" in metafunc.fixturenames:
        if not _gpu_node_ips:
            from automation_library.dcgm.messages import TEST_ASSERT_MSGS as ASSERT
            reason = _gpu_collection_error if _gpu_collection_error else ASSERT["no_gpu_nodes"]
            metafunc.parametrize(
                "gpu_node_ip",
                [pytest.param(None, marks=pytest.mark.skip(reason=reason))],
            )
        else:
            metafunc.parametrize(
                "gpu_node_ip",
                _gpu_node_ips,
                ids=_gpu_node_ips,
            )
    
    # Parametrize login_compiler_ip
    if "login_compiler_ip" in metafunc.fixturenames:
        if not _login_compiler_ips:
            reason = _login_compiler_collection_error if _login_compiler_collection_error else "No login_compiler nodes found"
            metafunc.parametrize(
                "login_compiler_ip",
                [pytest.param(None, marks=pytest.mark.skip(reason=reason))],
            )
        else:
            metafunc.parametrize(
                "login_compiler_ip",
                _login_compiler_ips,
                ids=_login_compiler_ips,
            )

    # Parametrize x86_64_node_ip (HPC benchmarks)
    if "x86_64_node_ip" in metafunc.fixturenames:
        if not _x86_64_node_ips:
            reason = (
                _x86_64_node_collection_error
                if _x86_64_node_collection_error
                else "No x86_64 cluster nodes found (functional group: slurm_node_x86_64)"
            )
            metafunc.parametrize(
                "x86_64_node_ip",
                [pytest.param(None, marks=pytest.mark.skip(reason=reason))],
            )
        else:
            metafunc.parametrize(
                "x86_64_node_ip",
                _x86_64_node_ips,
                ids=_x86_64_node_ips,
            )

    # Parametrize aarch64_node_ip (HPC benchmarks)
    if "aarch64_node_ip" in metafunc.fixturenames:
        if not _aarch64_node_ips:
            reason = (
                _aarch64_node_collection_error
                if _aarch64_node_collection_error
                else "No aarch64 cluster nodes found (functional group: slurm_node_aarch64)"
            )
            metafunc.parametrize(
                "aarch64_node_ip",
                [pytest.param(None, marks=pytest.mark.skip(reason=reason))],
            )
        else:
            metafunc.parametrize(
                "aarch64_node_ip",
                _aarch64_node_ips,
                ids=_aarch64_node_ips,
            )

    # Parametrize x86_64_login_compiler_ip (HPC benchmarks)
    if "x86_64_login_compiler_ip" in metafunc.fixturenames:
        if not _x86_64_login_compiler_ips:
            reason = (
                _x86_64_login_compiler_collection_error
                if _x86_64_login_compiler_collection_error
                else "No x86_64 login/compiler nodes found (functional group: login_compiler_x86_64)"
            )
            metafunc.parametrize(
                "x86_64_login_compiler_ip",
                [pytest.param(None, marks=pytest.mark.skip(reason=reason))],
            )
        else:
            metafunc.parametrize(
                "x86_64_login_compiler_ip",
                _x86_64_login_compiler_ips,
                ids=_x86_64_login_compiler_ips,
            )

    # Parametrize cluster_node_ip (any arch — HPC benchmarks)
    if "cluster_node_ip" in metafunc.fixturenames:
        if not _all_cluster_node_ips:
            reason = (
                _all_cluster_node_collection_error
                if _all_cluster_node_collection_error
                else "No cluster nodes found (x86_64 or aarch64)"
            )
            metafunc.parametrize(
                "cluster_node_ip",
                [pytest.param(None, marks=pytest.mark.skip(reason=reason))],
            )
        else:
            metafunc.parametrize(
                "cluster_node_ip",
                [_all_cluster_node_ips[0]],
                ids=[_all_cluster_node_ips[0]],
            )

    # Parametrize hpc_login_compiler_ip (any arch — HPC benchmarks)
    if "hpc_login_compiler_ip" in metafunc.fixturenames:
        if not _all_login_compiler_ips:
            reason = (
                _all_login_compiler_collection_error
                if _all_login_compiler_collection_error
                else "No login/compiler nodes found (x86_64 or aarch64)"
            )
            metafunc.parametrize(
                "hpc_login_compiler_ip",
                [pytest.param(None, marks=pytest.mark.skip(reason=reason))],
            )
        else:
            metafunc.parametrize(
                "hpc_login_compiler_ip",
                [_all_login_compiler_ips[0]],
                ids=[_all_login_compiler_ips[0]],
            )


def pytest_sessionstart(session):
    """Called before test collection - initialize report and ensure credentials encrypted."""
    # Ensure omnia_test_credentials.yml is encrypted before running tests
    # This handles the case where user runs 'verify' without 'test' (converge)
    try:
        encrypt_omnia_test_credentials()
    except Exception:
        pass  # File may not exist or already encrypted - that's OK

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
    """Testinfra host fixture - connects to OIM server.

    When running on the OIM itself (oim_server_ip is empty or matches a local IP),
    returns a local testinfra host — no SSH credentials required.
    When running remotely, validates SSH connectivity before returning the host.
    """
    import shutil
    import subprocess as _sp

    from automation_library.core import load_omnia_test_config
    config = load_omnia_test_config()
    oim_ip = config.get("oim_server_ip", "")

    # Local execution mode: running on the OIM itself — skip all SSH checks
    if is_local_execution():
        h = get_testinfra_host()
        # Quick sanity check that local execution works
        try:
            result = h.run("echo ok")
            if result.rc != 0 or "ok" not in result.stdout:
                pytest.fail(
                    "Local command execution failed. "
                    "Verify that the test user has proper permissions."
                )
        except Exception as e:
            pytest.fail(f"Local command execution failed: {e}")
        return h

    # --- Remote execution mode: oim_server_ip is set to a remote IP ---

    # Pre-check 1: Verify sshpass is installed (needed for password-based SSH)
    if not shutil.which("sshpass"):
        pytest.fail(
            "sshpass is not installed. It is required for SSH password authentication.\n"
            "Install it: dnf install -y sshpass (RHEL) or apt install -y sshpass (Ubuntu)"
        )

    # Pre-check 2: Verify OIM server is reachable (basic TCP check on SSH port)
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

    # Pre-check 3: Verify SSH authentication works
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

    # Only skip if build_stream is enabled AND job check failed AND not forced
    if (is_build_stream_enabled(host) and
            build_stream_job_state["checked"] and
            not build_stream_job_state["success"] and
            not build_stream_job_state.get("forced", False)):

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
