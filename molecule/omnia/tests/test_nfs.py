import subprocess
import pytest
import random
import string
import config

oim_ip = config.OIM_IP
oim_password = config.OIM_PASS
container_name = "omnia_core"

def test_nfs_service_status_on_all_nodes(all_hosts, get_unique_ips):
    """
    Check if the NFS service is running on all nodes.
    """
    all_nodes = []
    for key in all_hosts:
        all_nodes.extend(all_hosts[key])
    unique_ips = get_unique_ips(all_nodes)

    failures = []
    for ip in unique_ips:
        print(f"\n🔍 Checking NFS service on node: {ip}")
        check_cmd = (
            f"sshpass -p {oim_password} ssh -o StrictHostKeyChecking=no root@{oim_ip} "
            f"'podman exec {container_name} ssh -o StrictHostKeyChecking=no {ip} "
            f"\"systemctl is-active nfs-client.target\"'"
        )
        result = subprocess.run(check_cmd, shell=True, capture_output=True, text=True)
        output = result.stdout.strip()
        print(f"📥 Output from {ip}: {output}")
        if output != "active":
            failures.append(f"NFS service is not running on node {ip}")
        else:
            print(f"✅ NFS service is active on {ip}")

    if failures:
        pytest.fail("Some nodes failed NFS service check:\n" + "\n".join(failures))


def test_nfs_mount_on_all_nodes(all_hosts, get_unique_ips, nfs_client_params_data, run_sshpass_command):
    """
    Validate that NFS shares are mounted on all nodes as per storage_config.yml.
    """
    all_nodes = []
    for key in all_hosts:
        all_nodes.extend(all_hosts[key])
    unique_ips = get_unique_ips(all_nodes)

    nfs_params = nfs_client_params_data(run_sshpass_command)

    print("\nExtracted NFS client parameters from storage_config.yml:")
    for idx, mount in enumerate(nfs_params, 1):
        print(f"\nEntry {idx}:")
        for k, v in mount.items():
            print(f"  {k}: {v}")

    failures = []
    for ip in unique_ips:
        print(f"\nChecking NFS mounts on node: {ip}")
        for mount in nfs_params:
            client_path = mount.get("client_share_path")
            if not client_path:
                continue

            check_cmd = (
                f"sshpass -p {oim_password} ssh -o StrictHostKeyChecking=no root@{oim_ip} "
                f"'podman exec {container_name} ssh -o StrictHostKeyChecking=no {ip} "
                f"\"mount | grep {client_path}\"'"
            )
            result = subprocess.run(check_cmd, shell=True, capture_output=True, text=True)
            if result.returncode != 0 or client_path not in result.stdout:
                failures.append(f"NFS mount {client_path} not found on node {ip}")
            else:
                print(f"✓ NFS mount {client_path} is present on {ip}")

    if failures:
        pytest.fail("Some nodes failed NFS mount check:\n" + "\n".join(failures))


def test_nfs_file_visibility_across_nodes(all_hosts, get_unique_ips, nfs_client_params_data, run_sshpass_command):
    """
    Create a file in the NFS mount from the first node and verify it is visible and readable from all other nodes.
    """
    all_nodes = []
    for key in all_hosts:
        all_nodes.extend(all_hosts[key])
    unique_ips = get_unique_ips(all_nodes)

    nfs_params = nfs_client_params_data(run_sshpass_command)
    if not nfs_params:
        pytest.skip("No NFS client parameters found in config.")
    mount_path = nfs_params[0].get("client_share_path")
    if not mount_path:
        pytest.fail("client_share_path not defined in NFS config.")

    test_file = f"{mount_path}/nfs_test_file.txt"
    test_content = "This is a test file for NFS mount verification."

    writer_ip = unique_ips[0]
    write_cmd = (
        f"sshpass -p {oim_password} ssh -o StrictHostKeyChecking=no root@{oim_ip} "
        f"'podman exec {container_name} ssh -o StrictHostKeyChecking=no {writer_ip} "
        f"\"echo '{test_content}' > {test_file}\"'"
    )
    result = subprocess.run(write_cmd, shell=True, capture_output=True, text=True)
    assert result.returncode == 0, f"Failed to write test file on {writer_ip}: {result.stderr}"

    failures = []
    for ip in unique_ips:
        read_cmd = (
            f"sshpass -p {oim_password} ssh -o StrictHostKeyChecking=no root@{oim_ip} "
            f"'podman exec {container_name} ssh -o StrictHostKeyChecking=no {ip} "
            f"\"cat {test_file}\"'"
        )
        result = subprocess.run(read_cmd, shell=True, capture_output=True, text=True)
        if result.returncode != 0:
            failures.append(f"Failed to read test file on {ip}: {result.stderr}")
        elif test_content not in result.stdout.strip():
            failures.append(f"File content mismatch on {ip}")
        else:
            print(f"\n✓ File content from {ip}: {result.stdout.strip()}")

    if failures:
        pytest.fail("Some nodes failed NFS file visibility check:\n" + "\n".join(failures))
