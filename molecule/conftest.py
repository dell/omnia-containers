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
import yaml

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))
import config


script_dir = os.path.dirname(os.path.abspath(__file__))
inventory_path = os.path.join(script_dir, "/home/omnia_input/inv")
os.environ['ANSIBLE_INVENTORY'] = inventory_path

software_config_path = "/opt/omnia/input/project_default/software_config.json"

oim_ip = config.OIM_IP
oim_password = config.OIM_PASS

oim_ha_ip = config.OIM_HA_IP
oim_ha_password = config.OIM_HA_PASS

@pytest.fixture
def run_sshpass_command():
    def _run(cmd, use_ha=False):
        ip = config.OIM_HA_IP if use_ha else config.OIM_IP
        password = config.OIM_HA_PASS if use_ha else config.OIM_PASS

        ssh_command = [
            "sshpass", "-p", password,
            "ssh", "-o", "StrictHostKeyChecking=no",
            f"root@{ip}", cmd
        ]
        return subprocess.run(ssh_command, capture_output=True, text=True)
    return _run

@pytest.fixture
def get_required_containers(run_sshpass_command):
    """
    Returns a function to determine required containers based on the presence of 'k8s'
    in software_config.json. Supports both OIM and OIM_HA via `use_ha` flag.
    """
    def _get_required_containers(use_ha=False):
        cmd = f"podman exec omnia_core cat {software_config_path}"
        result = run_sshpass_command(cmd, use_ha=use_ha)

        if result.returncode != 0:
            pytest.fail(f"Failed to fetch file from container: {result.stderr}")

        try:
            data = json.loads(result.stdout)
            softwares = data.get("softwares", [])
            if any(software.get("name") == "k8s" for software in softwares):
                print(f"\nk8s found on {'OIM_HA' if use_ha else 'OIM'} node.\n")
                return ["omnia_pcs", "omnia_provision", "pulp", "omnia_kubespray"]
            else:
                print(f"\nk8s not found on {'OIM_HA' if use_ha else 'OIM'} node. Skipping omnia_kubespray.\n")
                return ["omnia_pcs", "omnia_provision", "pulp"]
        except json.JSONDecodeError:
            pytest.fail("Invalid JSON in software_config.json")
        except Exception as e:
            pytest.fail(f"Unexpected error: {e}")
    return _get_required_containers

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

@pytest.fixture(scope="session")
def get_oim_shared_path():
    def _get_oim_shared_path(run_sshpass_command):
        """Read OIM metadata file and return the shared path"""
        # Get metadata from container
        cmd = f"podman exec omnia_core cat /opt/omnia/.data/oim_metadata.yml"
        result = run_sshpass_command(cmd)
        
        if result.returncode != 0:
            pytest.fail(f"Failed to fetch OIM metadata: {result.stderr}")
                
        # Parse YAML and get shared path
        metadata = yaml.safe_load(result.stdout)
        shared_path = metadata.get('oim_shared_path')
        
        if not shared_path:
            pytest.fail("oim_shared_path not found in metadata")

        print(f"\noim_shared_path: {shared_path}")
        return shared_path
    return _get_oim_shared_path

@pytest.fixture
def check_if_oim_ha_is_enabled():
    def _check(run_sshpass_command):
        cmd = f"podman exec omnia_core cat /opt/omnia/input/project_default/high_availability_config.yml"
        result = run_sshpass_command(cmd)
        assert result.returncode == 0, f"Failed to fetch HA config: {result.stderr}"
        if "enable_oim_ha: true" not in result.stdout:
            pytest.skip("Skipping OIM HA tests: Not enabled.")
        return True
    return _check

@pytest.fixture
def get_oim_ha_nodes():
    def _get_oim_ha_nodes(run_sshpass_command, use_ha=False):
        postgres_password = os.getenv("POSTGRES_PASSWORD")
        assert postgres_password, print("Missing environment variable: POSTGRES_PASSWORD")

        query = "SELECT node FROM cluster.nodeinfo WHERE role = 'oim_ha_node';"

        cmd = (
            f"podman exec -e PGPASSWORD='{postgres_password}' omnia_provision "
            f"psql -q -U postgres -d omniadb -t -A -c \"{query}\""
        )

        result = run_sshpass_command(cmd, use_ha=use_ha)
        assert result.returncode == 0, print(f"\nFailed to query column names.\nError:\n{result.stderr}")

        oim_ha_nodes = result.stdout.strip().splitlines()

        return oim_ha_nodes
    return _get_oim_ha_nodes

@pytest.fixture
def get_compute_nodes():
    def _get_compute_nodes(run_sshpass_command, use_ha=False):    
        postgres_password = os.getenv("POSTGRES_PASSWORD")
        assert postgres_password, print("Missing environment variable: POSTGRES_PASSWORD")

        query = "SELECT node FROM cluster.nodeinfo WHERE role = 'default';"

        cmd = (
            f"podman exec -e PGPASSWORD='{postgres_password}' omnia_provision "
            f"psql -q -U postgres -d omniadb -t -A -c \"{query}\""
        )

        result = run_sshpass_command(cmd, use_ha=use_ha)
        assert result.returncode == 0, print(f"\nFailed to query column names.\nError:\n{result.stderr}")

        compute_nodes = result.stdout.strip().splitlines()
    
        print("\nCompute nodes: ", compute_nodes)
        
        return compute_nodes
    return _get_compute_nodes
    
@pytest.fixture
def get_required_pcs_resources():
    """
    Returns a function that fetches required PCS resources based on presence of 'k8s' in config.
    Supports both OIM and OIM_HA via the `use_ha` flag and includes VIPs.
    """
    def _get(run_sshpass_command, use_ha=False, include_vips=False):
        cmd = "podman exec omnia_core cat /opt/omnia/input/project_default/software_config.json"
        result = run_sshpass_command(cmd, use_ha=use_ha)
        
        assert result.returncode == 0, f"Failed to fetch software config: {result.stderr}"

        try:
            data = json.loads(result.stdout)
            softwares = data.get("softwares", [])
            has_k8s = any(s.get("name") == "k8s" for s in softwares)

            base_resources = ["omnia_core", "omnia_provision", "pulp"]
            if has_k8s:
                base_resources.append("omnia_kubespray")

            if include_vips:
                base_resources = ["admin_VIP", "bmc_VIP"] + base_resources

            print(f"\nk8s {'found' if has_k8s else 'not found'} on {'OIM_HA' if use_ha else 'OIM'} node.")
            return base_resources

        except json.JSONDecodeError:
            pytest.fail("Invalid JSON in software_config.json")
        except Exception as e:
            pytest.fail(f"Unexpected error: {e}")
    
    return _get


@pytest.fixture
def check_pcs_resource_status():
    def _check(output, resources, expected_node):
        missing, not_started = [], []
        for res in resources:
            lines = [line.strip() for line in output.splitlines() if res in line]
            if not lines:
                missing.append(res)
            elif not any(f"Started {expected_node}" in line for line in lines):
                not_started.append(res)
        return missing, not_started
    return _check

@pytest.fixture
def get_hostname():
    def _get(run_sshpass_command, use_ha=False):
        result = run_sshpass_command("hostname -s", use_ha=use_ha)
        assert result.returncode == 0, f"Failed to get hostname: {result.stderr}"
        return result.stdout.strip()
    return _get

@pytest.fixture
def check_pcs_daemon_status():
    def _check(run_sshpass_command, node):
        cmd = (
            f"podman exec omnia_core ssh -o StrictHostKeyChecking=no -o ConnectTimeout=5 "
            f"{node} podman exec omnia_pcs pcs status"
        )
        result = run_sshpass_command(cmd)
        if result.returncode != 0:
            return False, "PCS status fetch failed"
        out = result.stdout.lower()
        if "corosync: active/enabled" not in out:
            return False, "corosync not active"
        if "pacemaker: active/enabled" not in out:
            return False, "pacemaker not active"
        return True, ""
    return _check

@pytest.fixture
def parse_online_nodes():
    def _parse(output):
        for line in output.splitlines():
            line = line.strip()
            if line.startswith("* Online:") and '[' in line:
                return [n.strip() for n in line.split('[', 1)[1].split(']')[0].split()]
            elif line.startswith("Online:"):
                return [n.strip() for n in line.split(':', 1)[1].split()]
        return []
    return _parse

@pytest.fixture
def get_system_ips():
    def _get_system_ips(result):
        """Get all IP addresses from a remote system"""
        try:
            if result.returncode == 0:
                return [ip.strip() for ip in result.stdout.split()]
            return []
        except Exception as e:
            pytest.fail(f"Error getting system IPs: {e}")
    return _get_system_ips

@pytest.fixture
def get_virtual_ips():
    def _get_virtual_ips(result):
        """Read virtual IPs from configuration file"""
        try:
            if result.returncode != 0:
                pytest.fail(f"Failed to fetch project default configuration: {result.stderr}")
            config = yaml.safe_load(result.stdout)
            return (
                config['oim_ha']['admin_virtual_ip_address'],
                config['oim_ha']['bmc_virtual_ip_address']
            )
        except Exception as e:
            pytest.fail(f"Error reading configuration: {e}")
    return _get_virtual_ips

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
