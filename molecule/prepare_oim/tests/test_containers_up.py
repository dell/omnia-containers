import subprocess
import pytest
import sys
import os
import json

# Add project root to path to import config
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../')))
import config

# Configuration
oim_ip = config.OIM_IP
password = config.OIM_PASS
CONTAINER_NAME = "omnia_core"
software_config_path = "/opt/omnia/input/project_default/software_config.json"

def run_sshpass_command():
    """
    SSH into the remote host and execute 'podman exec' to get the software_config.json file.
    """
    remote_cmd = f"podman exec {CONTAINER_NAME} cat {software_config_path}"
    ssh_command = [
        "sshpass", "-p", password,
        "ssh", "-o", "StrictHostKeyChecking=no", "-o", "UserKnownHostsFile=/dev/null",
        f"root@{oim_ip}", remote_cmd
    ]

    result = subprocess.run(ssh_command, capture_output=True, text=True)
    return result

def get_required_containers():
    """
    Determines which containers are required based on presence of 'k8s' in software_config.json.
    """
    result = run_sshpass_command()

    if result.returncode != 0:
        pytest.fail(f"Failed to fetch file from container: {result.stderr}")

    try:
        data = json.loads(result.stdout)
        softwares = data.get("softwares", [])
        if any(software.get("name") == "k8s" for software in softwares):
            print("\nk8s found.\n")
            return ["omnia_pcs", "omnia_provision", "omnia_pulp", "omnia_kubespray"]
        else:
            print(f"k8s not found. Skipping omnia_kubespray.")
            return ["omnia_pcs", "omnia_provision", "omnia_pulp"]
    except json.JSONDecodeError:
        pytest.fail("Invalid JSON in software_config.json")
    except Exception as e:
        pytest.fail(f"Unexpected error: {e}")

def test_required_containers_running():
    """
    Checks that all required containers are present and running in podman.
    """
    required_containers = get_required_containers()

    ssh_command = [
        "sshpass", "-p", password,
        "ssh", "-o", "StrictHostKeyChecking=no",
        f"root@{oim_ip}",
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
        
        # Flag to track containers that are running
        containers_running = []

        # Check the status of the required containers
        for container in required_containers:
            found = False
            for line in result.stdout.splitlines():
                name, status = line.split(": ")
                if container in name:
                    found = True
                    if "Up" not in status:
                        containers_not_running.append(f"{container}: {status}")
                    else:
                        containers_running.append(f"{container}: {status}")
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
        print(f"\nThe following required containers are running:\n" + "\n".join(containers_running))
        
        if not containers_not_running:
            print("\n✅ All required containers are present and running.")

    except Exception as e:
        pytest.fail(f"\n❌ Error accessing containers: {e}")
