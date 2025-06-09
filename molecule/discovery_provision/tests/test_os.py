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

import pytest
import subprocess
import yaml
import config

oim_ip = config.OIM_IP
oim_password = config.OIM_PASS

@pytest.fixture
def oim_connection_details():
    return {
        "ip": oim_ip,
        "password": oim_password,
        "container": "omnia_core",
        "user": "root"
    }
    
@pytest.fixture
def etc_hosts_map(oim_connection_details):
    result = run_remote_cmd(oim_connection_details, "cat /etc/hosts")
    if result.returncode != 0:
        pytest.fail(f"Failed to fetch /etc/hosts: {result.stderr.strip()}")

    ip_map = {}
    for line in result.stdout.strip().splitlines():
        if line.startswith("#") or not line.strip():
            continue
        parts = line.split()
        if len(parts) >= 2:
            ip_map[parts[0]] = parts[1]
    return ip_map

@pytest.fixture
def provisioned_domain_name(oim_connection_details):
    result = run_remote_cmd(oim_connection_details, "cat /opt/omnia/input/project_default/provision_config.yml")
    if result.returncode != 0:
        pytest.fail(f"Failed to read provision config: {result.stderr.strip()}")
    try:
        config_data = yaml.safe_load(result.stdout)
        return config_data.get("domain_name")
    except yaml.YAMLError as e:
        pytest.fail(f"YAML parsing error: {e}")

def run_remote_cmd(oim, inner_cmd):
    full_cmd = (
        f"sshpass -p {oim['password']} ssh -o StrictHostKeyChecking=no {oim['user']}@{oim['ip']} "
        f"'podman exec {oim['container']} {inner_cmd}'"
    )
    return subprocess.run(full_cmd, shell=True, capture_output=True, text=True)

def get_os_details(ip, oim):
    ssh_cmd = f"ssh -o StrictHostKeyChecking=no -o ConnectTimeout=5 {ip} cat /etc/os-release"
    result = run_remote_cmd(oim, ssh_cmd)

    if result.returncode != 0:
        pytest.fail(f"Failed to fetch OS info from {ip}: {result.stderr.strip()}")

    os_name, os_version = None, None
    for line in result.stdout.strip().splitlines():
        if line.startswith("NAME="):
            os_name = line.split("=", 1)[1].strip('"')
        elif line.startswith("VERSION_ID="):
            os_version = line.split("=", 1)[1].strip('"')

    if not os_name or not os_version:
        pytest.fail(f"Could not parse OS on {ip}. Raw:\n{result.stdout}")

    return os_name, os_version


def test_os_name_and_version(all_hosts, get_unique_ips, oim_connection_details):
    print("\n🔍 Testing OS version on nodes")

    all_nodes = []
    for group in all_hosts:
        all_nodes.extend(all_hosts[group])
    unique_ips = get_unique_ips(all_nodes)

    oim_name, oim_ver = get_os_details(oim_connection_details["ip"], oim_connection_details)
    print(f"OIM OS: {oim_name} {oim_ver}")

    mismatches = []

    for ip in unique_ips:
        name, ver = get_os_details(ip, oim_connection_details)
        print(f"{ip} - OS: {name} {ver}")
        if (name, ver) != (oim_name, oim_ver):
            mismatches.append((ip, name, ver))

    if mismatches:
        msg = "\nOS version mismatches:\n" + "\n".join(
            f"{ip} Expected: {oim_name} {oim_ver}, Got: {name} {ver}" for ip, name, ver in mismatches
        )
        pytest.fail(msg)


def test_domain_name(all_hosts, get_unique_ips, oim_connection_details, provisioned_domain_name):
    print("\nChecking domain name of compute nodes")
    print(f"Expected domain name: {provisioned_domain_name}")

    all_nodes = []
    for group in all_hosts:
        all_nodes.extend(all_hosts[group])
    unique_ips = get_unique_ips(all_nodes)

    mismatches = []

    for ip in unique_ips:
        cmd = f"ssh -o StrictHostKeyChecking=no -o ConnectTimeout=5 {ip} hostname -d"
        result = run_remote_cmd(oim_connection_details, cmd)
        domain = result.stdout.strip()

        print(f"{ip} - Domain: {domain}")
        if provisioned_domain_name != domain:
            mismatches.append((ip, domain))

    if mismatches:
        pytest.fail("\nDomain mismatches:\n" + "\n".join(f"{ip} Got: {dom}" for ip, dom in mismatches))
    else:
        print("All nodes have expected domain")


def test_hostname_matches_hosts_file(all_hosts, get_unique_ips, oim_connection_details, etc_hosts_map):
    print("\nValidating hostnames from /etc/hosts")

    all_nodes = []
    for group in all_hosts:
        all_nodes.extend(all_hosts[group])
    unique_ips = get_unique_ips(all_nodes)

    mismatches = []

    for ip in unique_ips:
        expected = etc_hosts_map.get(ip)
        if not expected:
            print(f"No hostname for {ip} in /etc/hosts")
            continue

        cmd = f"ssh -o StrictHostKeyChecking=no -o ConnectTimeout=5 {ip} hostname -s"
        result = run_remote_cmd(oim_connection_details, cmd)
        hostname = result.stdout.strip()

        print(f"{ip} - Expected: {expected}, Got: {hostname}")
        if hostname != expected:
            mismatches.append((ip, expected, hostname))

    if mismatches:
        pytest.fail("\nHostname mismatches:\n" + "\n".join(
            f"{ip} Expected: {exp}, Got: {got}" for ip, exp, got in mismatches
        ))
    else:
        print("All hostnames match")
