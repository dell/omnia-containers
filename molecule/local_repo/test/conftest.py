"""
Pytest configuration and fixtures for local_repo tests.

Uses variables from automation_library.vars.local_repo_vars
and messages from automation_library.messages.local_repo_msgs
"""

import os
import sys
import pytest
import testinfra

# Add automation_library to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from automation_library.vars.local_repo_vars import LOCAL_REPO_VARS
from automation_library.messages.local_repo_msgs import LOCAL_REPO_MSGS


def pytest_addoption(parser):
    """Add custom command line options."""
    parser.addoption(
        "--status-file-path",
        action="store",
        default=LOCAL_REPO_VARS.get("top_level_status_file", "/opt/omnia/offline/status.csv"),
        help="Path to top-level status.csv file"
    )
    parser.addoption(
        "--package-status-dir",
        action="store",
        default=LOCAL_REPO_VARS.get("package_status_dir", "/opt/omnia/offline/packages"),
        help="Path to package status directory"
    )


@pytest.fixture(scope="session")
def host(request):
    """
    Return a testinfra host instance for the target system.
    Uses local connection when running via Molecule.
    """
    return testinfra.get_host("local://")


@pytest.fixture(scope="session")
def container_runtime(host):
    """
    Detect available container runtime (podman or docker).
    Returns 'podman', 'docker', or None.
    """
    configured_runtime = LOCAL_REPO_VARS.get("container_runtime", "podman")

    podman_check = host.run("which podman")
    if podman_check.rc == 0:
        return "podman"

    docker_check = host.run("which docker")
    if docker_check.rc == 0:
        return "docker"

    return None


@pytest.fixture(scope="session")
def pulp_container_name():
    """Get Pulp container name from LOCAL_REPO_VARS."""
    return LOCAL_REPO_VARS.get("pulp_container_name", "pulp")


@pytest.fixture(scope="session")
def omnia_core_container_name():
    """Get omnia_core container name from LOCAL_REPO_VARS."""
    return LOCAL_REPO_VARS.get("omnia_core_container", "omnia_core")


@pytest.fixture(scope="session")
def top_level_status_file(request):
    """Get top-level status file path."""
    return os.environ.get(
        "TOP_LEVEL_STATUS_FILE",
        request.config.getoption("--status-file-path")
    )


@pytest.fixture(scope="session")
def package_status_dir(request):
    """Get package status directory path."""
    return os.environ.get(
        "PACKAGE_STATUS_DIR",
        request.config.getoption("--package-status-dir")
    )


@pytest.fixture(scope="session")
def pulp_commands():
    """Get list of Pulp commands to validate."""
    return LOCAL_REPO_VARS.get("pulp_commands", [
        "pulp rpm repository list",
        "pulp rpm remote list",
        "pulp rpm publication list",
        "pulp rpm distribution list",
    ])


@pytest.fixture(scope="session")
def custom_repo_endpoints():
    """Get list of custom repo endpoints to check."""
    return LOCAL_REPO_VARS.get("custom_repo_endpoints", [
        "/pulp/api/v3/status/",
        "/pulp/api/v3/repositories/rpm/rpm/",
    ])


@pytest.fixture(scope="session")
def custom_repo_base_url():
    """Get custom repo base URL."""
    return LOCAL_REPO_VARS.get("custom_repo_base_url", "http://localhost:8080")


@pytest.fixture(scope="session")
def status_success_values():
    """Get list of status values that indicate success."""
    return LOCAL_REPO_VARS.get("status_success_values", [
        "success", "completed", "downloaded", "ok"
    ])


@pytest.fixture(scope="session")
def status_failed_values():
    """Get list of status values that indicate failure."""
    return LOCAL_REPO_VARS.get("status_failed_values", [
        "failed", "error", "failure"
    ])


@pytest.fixture(scope="session")
def local_repo_msgs():
    """Provide access to LOCAL_REPO_MSGS for assertion messages."""
    return LOCAL_REPO_MSGS


@pytest.fixture(scope="session")
def local_repo_vars():
    """Provide access to LOCAL_REPO_VARS for test configuration."""
    return LOCAL_REPO_VARS
