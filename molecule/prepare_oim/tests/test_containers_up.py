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

def run_sshpass_command(cmd):
    """
    SSH into the remote host and execute 'podman exec' to get the software_config.json file.
    """
    remote_cmd = cmd
    
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
    cmd = f"podman exec {CONTAINER_NAME} cat {software_config_path}"
    
    result = run_sshpass_command(cmd)

    if result.returncode != 0:
        pytest.fail(f"Failed to fetch file from container: {result.stderr}")

    try:
        data = json.loads(result.stdout)
        softwares = data.get("softwares", [])
        if any(software.get("name") == "k8s" for software in softwares):
            print("\nk8s found.\n")
            return ["omnia_pcs", "omnia_provision", "omnia_pulp", "omnia_kubespray"]
        else:
            print(f"k8s not found. Skipping omnia_kubespray container.")
            return ["omnia_pcs", "omnia_provision", "omnia_pulp"]
    except json.JSONDecodeError:
        pytest.fail("Invalid JSON in software_config.json")
    except Exception as e:
        pytest.fail(f"Unexpected error: {e}")

def get_required_pcs_resources():
    """
    Determines which containers are required based on presence of 'k8s' in software_config.json.
    """
    cmd = f"podman exec {CONTAINER_NAME} cat {software_config_path}"
    
    result = run_sshpass_command(cmd)

    if result.returncode != 0:
        pytest.fail(f"Failed to fetch file from container: {result.stderr}")

    try:
        data = json.loads(result.stdout)
        softwares = data.get("softwares", [])
        if any(software.get("name") == "k8s" for software in softwares):
            print("\nk8s found.\n")
            return ["omnia_core", "omnia_pulp", "omnia_provision", "omnia_kubespray"]
        else:
            print(f"k8s not found. Skipping omnia_kubespray container.")
            return ["omnia_core", "omnia_provision", "omnia_pulp"]
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

    
def test_pcs_resources_running():
    # List of expected resource names and their group
    expected_resources = get_required_pcs_resources()
    
    cmd = f"podman exec -it omnia_pcs pcs resource"
    
    result = run_sshpass_command(cmd)
    
    assert result.returncode == 0, f"SSH command failed: {result.stderr}"

    pcs_output = result.stdout

    # Verify each resource is listed and in 'Started' state
    missing = []
    not_started = []
    
    print(pcs_output)
    for res in expected_resources:
        lines = [line.strip() for line in pcs_output.splitlines() if res in line]
        if not lines:
            missing.append(res)
            continue
        if not any("Started" in line for line in lines):
            not_started.append(res)

    assert not missing, f"Missing resources in PCS status: {missing}"
    assert not not_started, f"Resources not started: {not_started}"

    print("\n✅ All PCS resources are present and started.")


def test_pulp_status():
    
    cmd = f"podman exec -it omnia_core pulp status"
    
    result = run_sshpass_command(cmd)
    assert result.returncode == 0, f"\npulp status is disabled.\nError:\n{result.stderr}"
    print("\npulp status is active")
    
