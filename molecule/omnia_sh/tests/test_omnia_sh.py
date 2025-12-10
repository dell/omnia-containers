"""
Molecule Testinfra/Pytest Tests for omnia.sh

This test file verifies that omnia.sh successfully installed and configured
the omnia_core container on the REMOTE OIM server.

All tests run on the remote OIM server specified in user_config.yml.

Usage:
    molecule verify -s omnia_sh
    pytest molecule/omnia_sh/tests/test_omnia_sh.py -v

Author: Dell Technologies
"""

import os
import sys
import pytest
import yaml

# Add project root to path for imports
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, PROJECT_ROOT)


def load_omnia_sh_config():
    """Load omnia_sh_config.yml to get test parameters."""
    config_path = os.path.join(PROJECT_ROOT, "omnia_sh_config.yml")
    if os.path.exists(config_path):
        with open(config_path, "r") as f:
            return yaml.safe_load(f) or {}
    return {}


# Load config once
OMNIA_SH_CONFIG = load_omnia_sh_config()

# Constants (same as omnia.sh defaults)
CONTAINER_NAME = "omnia_core"
SSH_PORT = 2222
OMNIA_SHARED_PATH = OMNIA_SH_CONFIG.get("omnia_shared_path", "/opt/omnia")


# =============================================================================
# Test: omnia.sh Script
# =============================================================================

def test_omnia_sh_exists(host):
    """Test that omnia.sh script exists on OIM server."""
    f = host.file("/opt/omnia-artifactory/omnia.sh")
    assert f.exists, "omnia.sh not found at /opt/omnia-artifactory/omnia.sh"
    assert f.is_file, "omnia.sh is not a file"


# =============================================================================
# Test: Container Status
# =============================================================================

def test_container_exists(host):
    """Test that omnia_core container exists."""
    cmd = host.run(f"podman ps -a --format '{{{{.Names}}}}' | grep -E '^{CONTAINER_NAME}$'")
    assert cmd.rc == 0, f"Container {CONTAINER_NAME} not found"


def test_container_running(host):
    """Test that omnia_core container is running."""
    cmd = host.run(f"podman ps --format '{{{{.Names}}}}' | grep -E '^{CONTAINER_NAME}$'")
    assert cmd.rc == 0, f"Container {CONTAINER_NAME} is not running"


def test_container_state(host):
    """Test container state is 'running'."""
    cmd = host.run(f"podman ps --format '{{{{.Names}}}} {{{{.State}}}}' | grep -E '^{CONTAINER_NAME} '")
    assert cmd.rc == 0, f"Container {CONTAINER_NAME} not found"
    assert "running" in cmd.stdout.lower(), f"Container state: {cmd.stdout}"


def test_container_image(host):
    """Test that container uses omnia_core image."""
    cmd = host.run(f"podman inspect {CONTAINER_NAME} --format '{{{{.ImageName}}}}'")
    assert cmd.rc == 0, "Failed to inspect container"
    assert "omnia_core" in cmd.stdout, f"Unexpected image: {cmd.stdout}"


# =============================================================================
# Test: SSH Connectivity
# =============================================================================

def test_ssh_port_listening(host):
    """Test that SSH port 2222 is listening."""
    socket = host.socket(f"tcp://0.0.0.0:{SSH_PORT}")
    assert socket.is_listening, f"SSH port {SSH_PORT} not listening"


def test_ssh_connection_to_container(host):
    """Test SSH connection to omnia_core container from OIM server."""
    cmd = host.run(f"ssh -o StrictHostKeyChecking=no -o ConnectTimeout=10 {CONTAINER_NAME} 'echo SSH_OK'")
    assert cmd.rc == 0, f"SSH connection failed: {cmd.stderr}"
    assert "SSH_OK" in cmd.stdout, f"SSH test failed: {cmd.stdout}"


# =============================================================================
# Test: Directory Structure
# =============================================================================

def test_omnia_directory_exists(host):
    """Test that main omnia directory exists."""
    dir_path = f"{OMNIA_SHARED_PATH}/omnia"
    assert host.file(dir_path).is_directory, f"Directory not found: {dir_path}"


def test_ssh_config_directory_exists(host):
    """Test that SSH config directory exists."""
    dir_path = f"{OMNIA_SHARED_PATH}/omnia/ssh_config/.ssh"
    assert host.file(dir_path).is_directory, f"Directory not found: {dir_path}"


def test_log_directory_exists(host):
    """Test that log directory exists."""
    dir_path = f"{OMNIA_SHARED_PATH}/omnia/log/core/container"
    assert host.file(dir_path).is_directory, f"Directory not found: {dir_path}"


def test_input_directory_exists(host):
    """Test that input directory exists."""
    dir_path = f"{OMNIA_SHARED_PATH}/omnia/input"
    assert host.file(dir_path).is_directory, f"Directory not found: {dir_path}"


def test_data_directory_exists(host):
    """Test that .data directory exists."""
    dir_path = f"{OMNIA_SHARED_PATH}/omnia/.data"
    assert host.file(dir_path).is_directory, f"Directory not found: {dir_path}"


def test_metadata_file_exists(host):
    """Test that oim_metadata.yml file exists."""
    file_path = f"{OMNIA_SHARED_PATH}/omnia/.data/oim_metadata.yml"
    assert host.file(file_path).is_file, f"Metadata file not found: {file_path}"


# =============================================================================
# Test: Systemd Service
# =============================================================================

def test_systemd_service_active(host):
    """Test that omnia_core systemd service is active."""
    cmd = host.run(f"systemctl is-active {CONTAINER_NAME}.service")
    assert cmd.stdout.strip() == "active", f"Service not active: {cmd.stdout}"


# =============================================================================
# Test: Additional Verifications
# =============================================================================

def test_omnia_sh_executable(host):
    """Test that omnia.sh is executable."""
    f = host.file("/opt/omnia-artifactory/omnia.sh")
    assert f.mode & 0o111, "omnia.sh is not executable"


def test_ssh_keys_exist(host):
    """Test that SSH keys were generated."""
    ssh_dir = f"{OMNIA_SHARED_PATH}/omnia/ssh_config/.ssh"
    assert host.file(f"{ssh_dir}/id_rsa").exists, "SSH private key not found"
    assert host.file(f"{ssh_dir}/id_rsa.pub").exists, "SSH public key not found"
