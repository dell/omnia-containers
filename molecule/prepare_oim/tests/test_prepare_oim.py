import subprocess
import pytest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../')))
import config

def test_specific_containers_running():
    ip = config.OIM_IP
    password = config.OIM_PASS

    ssh_command = [
        "sshpass", "-p", password,
        "ssh", "-o", "StrictHostKeyChecking=no",
        f"root@{ip}",
        "podman ps --all --format '{{.Names}}: {{.Status}}'"
    ]

    try:
        # Run the SSH command to get the podman container statuses
        result = subprocess.run(ssh_command, capture_output=True, text=True, timeout=10)
        assert result.returncode == 0, f"\n❌ SSH command failed: {result.stderr}"

        # List of containers we want to check
        required_containers = ["omnia_pcs", "omnia_provision", "omnia_pulp", "omnia_kubespray"]

        # Flag to track containers that are missing or not running
        containers_not_running = []
        containers_missing = []

        # Check the status of the required containers
        for container in required_containers:
            found = False
            for line in result.stdout.splitlines():
                name, status = line.split(": ")
                if container in name:
                    found = True
                    if "Up" not in status:
                        containers_not_running.append(f"{container}: {status}")
                    break
            if not found:
                containers_missing.append(container)

        # Assert that all required containers are found and running
        assert not containers_missing, (
            f"\n❌ The following required containers are missing:\n" + "\n".join(containers_missing)
        )
        assert not containers_not_running, (
            f"\n❌ The following required containers are not running:\n" + "\n".join(containers_not_running)
        )

        print("\n✅ All required containers are present and running.")

    except Exception as e:
        pytest.fail(f"\n❌ Error accessing containers: {e}")
