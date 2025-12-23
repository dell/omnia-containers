"""
Shared pytest configuration for all molecule scenarios.
"""

import os
import sys
import pytest

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from automation_library.core import (
    get_testinfra_host, TestReport, set_current_report, get_current_report, get_test_output
)


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
def pytest_runtest_makereport(item, call):
    """Hook to capture test results and output."""
    outcome = yield
    result = outcome.get_result()

    if result.when == "call":
        report = get_current_report()
        if report:
            passed = result.outcome == "passed"
            duration = result.duration if hasattr(result, "duration") else 0
            error = str(result.longrepr) if result.longrepr else None

            # Get captured test output from logger
            output = get_test_output(item.name)

            report.add_result(
                test_name=item.name,
                passed=passed,
                duration=duration,
                details=output if output else None,
                error=error if not passed else None
            )


@pytest.fixture(scope="module")
def host():
    """Testinfra host fixture - connects to OIM server."""
    return get_testinfra_host()
