"""
Pytest configuration and fixtures for prepare_oim tests.

Uses variables from automation_library.vars.prepare_oim_vars
and messages from automation_library.messages.prepare_oim_msgs
"""

import os
import sys
import json
import pytest
import testinfra

# Add automation_library to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from automation_library.vars.prepare_oim_vars import PREPARE_OIM_VARS
from automation_library.messages.prepare_oim_msgs import PREPARE_OIM_MSGS


def pytest_addoption(parser):
    """Add custom command line options."""
    parser.addoption(
        "--software-config-path",
        action="store",
        default=PREPARE_OIM_VARS.get("software_config_path", "/opt/omnia/software_config.json"),
        help="Path to software_config.json"
    )


@pytest.fixture(scope="session")
def host(request):
    """
    Return a testinfra host instance for the target system.
    Uses local connection when running via Molecule.
    """
    # When running via Molecule, use local connection
    # The converge playbook already runs on the target host
    return testinfra.get_host("local://")


@pytest.fixture(scope="session")
def software_config_path(request):
    """Get software_config.json path from environment or command line."""
    return os.environ.get(
        "SOFTWARE_CONFIG_PATH",
        request.config.getoption("--software-config-path")
    )


@pytest.fixture(scope="session")
def ldap_enabled(host):
    """
    Check if LDAP is enabled in software_config.json.
    Returns True if LDAP is configured, False otherwise.
    """
    # First check the molecule env vars file
    env_file = host.file("/tmp/molecule_env_vars")
    if env_file.exists:
        content = env_file.content_string
        if "LDAP_ENABLED=true" in content.lower():
            return True
        if "LDAP_ENABLED=false" in content.lower():
            return False
    
    # Fallback: check software_config.json directly
    config_path = os.environ.get(
        "SOFTWARE_CONFIG_PATH",
        PREPARE_OIM_VARS.get("software_config_path", "/opt/omnia/software_config.json")
    )
    
    config_file = host.file(config_path)
    if not config_file.exists:
        return False
    
    try:
        content = config_file.content_string
        config = json.loads(content)
        ldap_key = PREPARE_OIM_VARS.get("ldap_config_key", "ldap")
        return config.get(ldap_key, False)
    except (json.JSONDecodeError, Exception):
        return False


@pytest.fixture(scope="session")
def container_runtime(host):
    """
    Detect available container runtime (podman or docker).
    Returns 'podman', 'docker', or None.
    """
    # Check configured runtime first
    configured_runtime = PREPARE_OIM_VARS.get("container_runtime", "podman")
    
    # Check for podman first (preferred on RHEL)
    podman_check = host.run("which podman")
    if podman_check.rc == 0:
        return "podman"
    
    # Fallback to docker
    docker_check = host.run("which docker")
    if docker_check.rc == 0:
        return "docker"
    
    return None


@pytest.fixture(scope="session")
def openchami_containers():
    """
    List of expected OpenCHAMI container names from PREPARE_OIM_VARS.
    These containers should be running for a healthy OpenCHAMI deployment.
    """
    return PREPARE_OIM_VARS.get("openchami_containers", [
        "openchami-smd",
        "openchami-bss",
        "openchami-cloud-init",
        "openchami-dnsmasq",
        "openchami-postgres",
        "openchami-hydra",
        "openchami-hydra-consent",
        "openchami-jwt-security",
        "openchami-step-ca",
    ])


@pytest.fixture(scope="session")
def auth_containers():
    """
    List of expected auth container names from PREPARE_OIM_VARS (when LDAP is enabled).
    """
    return PREPARE_OIM_VARS.get("auth_containers", [
        "openchami-opaal",
        "openchami-ldap",
    ])


@pytest.fixture(scope="session")
def omnia_target_dependencies():
    """
    List of expected omnia.target dependencies from PREPARE_OIM_VARS.
    These services should be running for omnia.target to be healthy.
    """
    return PREPARE_OIM_VARS.get("omnia_critical_dependencies", [
        "openchami.service",
        "network.target",
        "multi-user.target",
    ])


@pytest.fixture(scope="session")
def prepare_oim_msgs():
    """Provide access to PREPARE_OIM_MSGS for assertion messages."""
    return PREPARE_OIM_MSGS


@pytest.fixture(scope="session")
def prepare_oim_vars():
    """Provide access to PREPARE_OIM_VARS for test configuration."""
    return PREPARE_OIM_VARS
