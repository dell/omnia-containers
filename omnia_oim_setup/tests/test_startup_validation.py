import subprocess
import pytest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
import config

def test_omnia_core_container_running():
    ip = config.OIM_IP
    password = config.OIM_PASS

    # Check if the container is running and can respond to a command
    ssh_command = [
        "sshpass", "-p", password,
        "ssh", "-o", "StrictHostKeyChecking=no",
        f"root@{ip}",
        "podman exec omnia_core echo CONTAINER_ACCESS_SUCCESS"
    ]

    try:
        result = subprocess.run(ssh_command, capture_output=True, text=True)
        assert result.returncode == 0, f"❌ Failed to exec into omnia_core: {result.stderr}"
        assert "CONTAINER_ACCESS_SUCCESS" in result.stdout, "❌ Container did not return expected output."
        print("✅ Successfully accessed omnia_core container.")
    except Exception as e:
        pytest.fail(f"❌ Error accessing omnia_core container: {e}")
