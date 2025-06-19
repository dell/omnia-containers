# Copyright 2025 Dell Inc. or its subsidiaries. All Rights Reserved.
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.

import subprocess
import json
import sys
import pytest
import os
import re
import testinfra
import testinfra.utils.ansible_runner
import shutil

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))
import config


script_dir = os.path.dirname(os.path.abspath(__file__))
inventory_path = os.path.join(script_dir, "/home/omnia_input/inv")
os.environ['ANSIBLE_INVENTORY'] = inventory_path

oim_ip = config.OIM_IP
oim_password = config.OIM_PASS
software_config_path = "/opt/omnia/input/project_default/software_config.json"

@pytest.fixture
def run_sshpass_command():
    def _run(cmd):
        ssh_command = [
            "sshpass", "-p", oim_password,
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
            return ["omnia_pcs", "omnia_provision", "pulp", "omnia_kubespray"]
        else:
            print(f"k8s not found. Skipping omnia_kubespray container.")
            return ["omnia_pcs", "omnia_provision", "pulp"]
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
            return ["omnia_core", "pulp", "omnia_provision", "omnia_kubespray"]
        else:
            print(f"k8s not found. Skipping omnia_kubespray container.")
            return ["omnia_core", "omnia_provision", "pulp"]
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
        assert result.returncode == 0, f"Failed to read file from container:\n{result.stderr}"
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
            raise ValueError(f"Could not find CREATE TABLE definition for '{table}'")
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


@pytest.fixture
def kube_control_plane():
    testinfra_hosts = [
        'ansible://kube_control_plane',
    ]
    return testinfra.get_hosts(testinfra_hosts)

@pytest.fixture
def kube_node():
    testinfra_hosts = [
        'ansible://kube_node',
    ]
    return testinfra.get_hosts(testinfra_hosts)

# Fixture for etcd nodes
@pytest.fixture
def etcd():
    testinfra_hosts = [
        'ansible://etcd',
    ]
    return testinfra.get_hosts(testinfra_hosts)

# Fixture for auth_server nodes
@pytest.fixture
def auth_server():
    testinfra_hosts = [
        'ansible://auth_server',
    ]
    return testinfra.get_hosts(testinfra_hosts)

# Fixture for slurm_control_node
@pytest.fixture
def slurm_control_node():
    testinfra_hosts = [
        'ansible://slurm_control_node',
    ]
    return testinfra.get_hosts(testinfra_hosts)

# Fixture for slurm_node
@pytest.fixture
def slurm_node():
    testinfra_hosts = [
        'ansible://slurm_node',
    ]
    return testinfra.get_hosts(testinfra_hosts)

# Fixture for login nodes
@pytest.fixture
def login():
    testinfra_hosts = [
        'ansible://login',
    ]
    return testinfra.get_hosts(testinfra_hosts)

@pytest.fixture
def all_hosts():
    hosts = {
        'kube_control_plane': testinfra.get_hosts(['ansible://kube_control_plane']),
        'kube_node': testinfra.get_hosts(['ansible://kube_node']),
        'etcd': testinfra.get_hosts(['ansible://etcd']),
        'auth_server': testinfra.get_hosts(['ansible://auth_server']),
        'slurm_control_node': testinfra.get_hosts(['ansible://slurm_control_node']),
        'slurm_node': testinfra.get_hosts(['ansible://slurm_node']),
        'login': testinfra.get_hosts(['ansible://login']),
    }
    return hosts

@pytest.fixture
def get_unique_ips():
    def _get_unique_ips(nodes):
        """
        This function extracts unique IPs (or hostnames) from a list of node objects.
        It eliminates any duplicates by using a set and returns a list of unique hostnames/IPs.
        This is useful when we need to ensure that a node is only checked once, even if it appears multiple times.

        Parameters:
        - nodes (list): A list of node objects.

        Returns:
        - list: A list of unique IPs (or hostnames) extracted from the nodes list.
        """
        unique_ips = set(host.backend.host for host in nodes)  # Use a set to eliminate duplicates
        return list(unique_ips)  # Return the unique IPs as a list
    return _get_unique_ips

@pytest.fixture
def sync_directories():
    def _sync_directories(source, destination):
        scp_command = [
            "sshpass", "-p", oim_password,
            "scp","-r", "-o", "StrictHostKeyChecking=no",
            source, f"root@{oim_ip}:{destination}"
        ]
        try:
            scp_result = subprocess.run(scp_command, capture_output=True, text=True)
            if scp_result.returncode != 0:
                print("Failed to copy input file to remote host:")
                print(scp_result.stderr)
            else:
                print(f"Copied file: {source} -> {destination}")
        except Exception as e:
            print(f"error: {e}")
            
    return _sync_directories


test_results = []

# Hook to capture test case results (ID, Name, Status)
@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    report = outcome.get_result()
    if report.when == "call":  # Capture results for executed tests only
        test_name = item.nodeid.split("::")[-1]  # Full test function name
        scenario_name = os.getenv("MOLECULE_SCENARIO_NAME", "default")  # Scenario Name
        qtest_marker = item.get_closest_marker("qtest_id")
        qtest_id = qtest_marker.args[0] if qtest_marker else "N/A"  # Extract qTest ID
        status = "Passed" if report.passed else "Failed" if report.failed else "Skipped"
        
        # Append results to global list
        test_results.append((scenario_name, qtest_id, test_name, status))


def pytest_sessionfinish(session, exitstatus):
    if test_results:
        scenario_name = test_results[0][0]  # Get the scenario name from the first test result
    else:
        scenario_name = "default"

    filename = f"{scenario_name}.html"

    # **Count Test Case Results**
    total_tests = len(test_results)
    passed_tests = sum(1 for _, _, _, status in test_results if status == "Passed")
    failed_tests = sum(1 for _, _, _, status in test_results if status == "Failed")
    skipped_tests = sum(1 for _, _, _, status in test_results if status == "Skipped")

    # Generate HTML content
    html_content = f"""<!DOCTYPE html>
<html>
<head>
    <title>Molecule Test Results</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
        th, td {{ border: 1px solid #ddd; padding: 10px; text-align: left; }}
        th {{ background-color: #f4f4f4; }}
        .passed {{ color: green; }}
        .failed {{ color: red; }}
        .skipped {{ color: orange; }}
        .summary {{ margin-top: 20px; font-size: 18px; }}
    </style>
</head>
<body>
    <h2>Molecule Test Results Summary</h2>

    <!-- Summary Section -->
    <div class="summary">
        <strong>Total Test Cases:</strong> {total_tests} <br>
        <strong>Passed:</strong> <span class="passed">{passed_tests}</span> <br>
        <strong>Failed:</strong> <span class="failed">{failed_tests}</span> <br>
        <strong>Skipped:</strong> <span class="skipped">{skipped_tests}</span> <br>
    </div>

    <table>
        <tr>
            <th>Scenario Name</th>
            <th>Test Case ID</th>
            <th>Test Name</th>
            <th>Test Status</th>
        </tr>"""

    # Add test results to the HTML table
    for scenario, qtest_id, test_name, status in test_results:
        status_class = "passed" if status == "Passed" else "failed" if status == "Failed" else "skipped"
        html_content += f"""
        <tr>
            <td>{scenario}</td>
            <td>{qtest_id}</td>
            <td>{test_name}</td>
            <td class="{status_class}">{status}</td>
        </tr>"""

    html_content += """
    </table>
</body>
</html>"""

    # Save to an HTML file
    with open(filename, "w") as file:
        file.write(html_content)

    print(f"\nMolecule test results saved to {filename}")
    print(f"Summary: Total={total_tests}, Passed={passed_tests}, Failed={failed_tests}, Skipped={skipped_tests}")
