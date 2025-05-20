import subprocess
import json
import sys
import pytest
import os
import re

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

        
@pytest.fixture
def get_file_from_container():    
    def _get_file_from_container(run_sshpass_command, file_path):
        # Run `podman exec` inside the container to cat the file
        cmd = f"podman exec omnia_core cat {file_path}"
        result = run_sshpass_command(cmd)
        assert result.returncode == 0, f"❌ Failed to read file from container:\n{result.stderr}"
        return result.stdout
    return _get_file_from_container


@pytest.fixture
def extract_create_table_sql():
    def _extract_create_table_sql(content, table="nodeinfo"):
        # Matches the SQL string defined as: sql = '''CREATE TABLE IF NOT EXISTS ...'''
        pattern = (
            rf"sql\s*=\s*'''CREATE TABLE IF NOT EXISTS .*?{table}\s*\((.*?)\)'''"
        )
        match = re.search(pattern, content, re.IGNORECASE | re.DOTALL)
        if not match:
            raise ValueError(f"❌ Could not find CREATE TABLE definition for '{table}'")
        return f"CREATE TABLE {match.group(0).split('CREATE TABLE', 1)[1]}"
    return _extract_create_table_sql


@pytest.fixture
def extract_columns_from_create_sql():
    def _extract_columns_from_create_sql(sql):
        inside = sql.split('(', 1)[1].rsplit(')', 1)[0]
        lines = inside.splitlines()

        columns = set()
        for line in lines:
            line = line.strip().rstrip(',')
            if not line or line.upper().startswith(("PRIMARY", "FOREIGN", "CONSTRAINT")):
                continue
            column_name = line.split()[0].strip('"')
            columns.add(column_name.lower())
        return columns
    return _extract_columns_from_create_sql
