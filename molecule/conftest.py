import subprocess
import json
import sys
import pytest
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))
import config

oim_ip = config.OIM_IP
password = config.OIM_PASS
software_config_path = "/opt/omnia/input/project_default/software_config.json"

@pytest.fixture
def run_sshpass_command():
    def _run(cmd):
        ssh_command = [
            "sshpass", "-p", password,
            "ssh", "-o", "StrictHostKeyChecking=no",
            f"root@{oim_ip}", cmd
        ]
        return subprocess.run(ssh_command, capture_output=True, text=True)
    return _run

@pytest.fixture
def get_required_containers(run_sshpass_command):
    """
    Determines which containers are required based on presence of 'k8s' in software_config.json.
    """
    cmd = f"podman exec omnia_core cat {software_config_path}"
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

        
@pytest.fixture        
def get_required_pcs_resources(run_sshpass_command):
    """
    Determines which containers are required based on presence of 'k8s' in software_config.json.
    """
    cmd = f"podman exec omnia_core cat {software_config_path}"
    
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
      
