import pytest
import subprocess
import yaml
import config

oim_ip = config.OIM_IP
oim_password = config.OIM_PASS

container_name = "omnia_provision"
remote_user = "root"

@pytest.fixture
def oim_connection_details():
    return {
        "ip": oim_ip,
        "password": oim_password,
        "container": "omnia_core",
        "user": "root"
    }

@pytest.fixture
def compute_nodes(run_sshpass_command):
    file_path = "/opt/omnia/omnia_inventory/compute_hostname_ip"
    cmd = f"podman exec {container_name} cat {file_path}"
    result = run_sshpass_command(cmd)

    assert result.returncode == 0, f"Failed to read compute_hostname_ip file: {result.stderr}"

    compute_nodes = []
    collect = False
    for line in result.stdout.splitlines():
        line = line.strip()
        if line.startswith("[") and line.endswith("]"):
            collect = (line == "[compute_hostname_ip]")
            continue
        if collect and line and not line.startswith("#"):
            # extract hostname before first space
            hostname = line.split()[0]
            compute_nodes.append(hostname)

    if not compute_nodes:
        pytest.fail(print("No nodes found."))
    
    print("\nCompute nodes: ", compute_nodes)
    return compute_nodes

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

def run_remote_cmd(oim, inner_cmd):
    full_cmd = (
        f"sshpass -p {oim['password']} ssh -o StrictHostKeyChecking=no {oim['user']}@{oim['ip']} "
        f"'podman exec {oim['container']} {inner_cmd}'"
    )
    return subprocess.run(full_cmd, shell=True, capture_output=True, text=True)

def test_os_name_and_version(compute_nodes, oim_connection_details):
    print("\nTesting OS version on nodes")

    oim_name, oim_ver = get_os_details(oim_connection_details["ip"], oim_connection_details)
    print(f"OIM OS: {oim_name} {oim_ver}")

    mismatches = []

    for node in compute_nodes:
        node = node.split('.')[0]
        name, ver = get_os_details(node, oim_connection_details)
        print(f"{node} - OS: {name} {ver}")
        if (name, ver) != (oim_name, oim_ver):
            mismatches.append((node, name, ver))

    if mismatches:
        msg = "\nOS version mismatches:\n" + "\n".join(
            f"{node} Expected: {oim_name} {oim_ver}, Got: {name} {ver}" for node, name, ver in mismatches
        )
        pytest.fail(msg)


def test_domain_name(compute_nodes, oim_connection_details, provisioned_domain_name):
    print("\nChecking domain name of compute nodes")
    print(f"\nExpected domain name: {provisioned_domain_name}")
    mismatches = []

    for node in compute_nodes:
        node = node.split('.')[0]
        cmd = f"ssh -o StrictHostKeyChecking=no -o ConnectTimeout=5 {node} hostname -d"
        result = run_remote_cmd(oim_connection_details, cmd)
        domain = result.stdout.strip()

        print(f"{node} - Domain: {domain}")
        if provisioned_domain_name != domain:
            mismatches.append((node, domain))

    if mismatches:
        pytest.fail("\nDomain mismatches:\n" + "\n".join(f"{node} Got: {dom}" for node, dom in mismatches))
    else:
        print("\nAll nodes have expected domain")


def test_hostname(compute_nodes, oim_connection_details):
    print("\nValidating hostnames from /etc/hosts")

    mismatches = []

    for node in compute_nodes:
        node = node.split('.')[0]
        expected = node
        if not expected:
            print(f"No hostname for {node} in /etc/hosts")
            continue

        cmd = f"ssh -o StrictHostKeyChecking=no -o ConnectTimeout=5 {node} hostname -s"
        result = run_remote_cmd(oim_connection_details, cmd)
        hostname = result.stdout.strip()

        print(f"{node} - Expected: {expected}, Got: {hostname}")
        if hostname != expected:
            mismatches.append((node, expected, hostname))

    if mismatches:
        pytest.fail("\nHostname mismatches:\n" + "\n".join(
            f"{node} Expected: {exp}, Got: {got}" for node, exp, got in mismatches
        ))
    else:
        print("All hostnames match")

