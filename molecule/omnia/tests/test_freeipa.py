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
import sys
import os
import pytest
import json
import time
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))
import config

oim_ip = config.OIM_IP
oim_password = config.OIM_PASS

software_config_path = "/opt/omnia/input/project_default/software_config.json"

job_name = "slurm_user.sh"

username = config.FREEIPA_USERNAME
password = config.PASSWORD
first_name = config.FIRST_NAME
last_name = config.LAST_NAME

script_dir = os.path.dirname(os.path.abspath(__file__))
script_path = os.path.join(script_dir, "../../scripts")
source = os.path.join(script_dir, script_path)
destination = '/mnt/omnia_home_share/'

@pytest.mark.dependency(name='freeipa')
@pytest.mark.qtest_id("TC-3215")
def test_FreeIPA_services(sync_directories, run_sshpass_command, auth_server, remote_user="root", container_name="omnia_core"):
    # Step 1: Check if FreeIPA is present in the config
    cmd = f"podman exec {container_name} cat {software_config_path}"
    result = run_sshpass_command(cmd)

    if result.returncode != 0:
        pytest.fail(f"Failed to fetch file from container: {result.stderr}")

    try:
        data = json.loads(result.stdout)
        softwares = data.get("softwares", [])
        if not any(software.get("name") == "freeipa" for software in softwares):
            pytest.skip("Skipping FreeIPA tests: 'freeipa' not found in software_config.json")
        print("\nFreeIPA found in software_config.json. Proceeding with service checks.")
    except json.JSONDecodeError:
        pytest.fail("Invalid JSON in software_config.json")
    except Exception as e:
        pytest.fail(f"Unexpected error: {e}")

    # Step 2: Check auth_server group presence
    assert auth_server, "No nodes found in 'auth_server' group in the inventory."

    # Step 3: Check FreeIPA services on each node
    for host in auth_server:
        node_ip = host.backend.host
        print(f"\n🔍 Checking FreeIPA services on node: {node_ip}")

        ssh_cmd = (
            f"sshpass -p {oim_password} ssh -o StrictHostKeyChecking=no {remote_user}@{oim_ip} "
            f"'podman exec {container_name} ssh -o StrictHostKeyChecking=no -o ConnectTimeout=5 {node_ip} ipactl status'"
        )

        result = subprocess.run(ssh_cmd, shell=True, capture_output=True, text=True)

        if result.returncode != 0:
            pytest.fail(f"Failed to run ipactl status on node {node_ip}:\n{result.stderr.strip()}")

        output = result.stdout.strip()
        if not output:
            pytest.fail(f"No output from ipactl status on node {node_ip}")

        print("\n--- Service Status Output ---")
        print(output)
        print("-----------------------------")

        running_services = []
        failing_services = []

        for line in output.splitlines():
            if ":" not in line:
                continue
            service, status = line.split(":", 1)
            service = service.strip()
            status = status.strip().upper()

            if status == "RUNNING":
                running_services.append(service)
            else:
                failing_services.append(f"{service}: {status}")

        if running_services:
            print(f"\nRunning services on {node_ip}:\n" + "\n".join(f"  ✔ {svc}" for svc in running_services))
        if failing_services:
            fail_msg = f"\nFailing services on {node_ip}:\n" + "\n".join(f"  ✖ {svc}" for svc in failing_services)
            pytest.fail(fail_msg)
        else:
            print(f"\nAll FreeIPA services are running on {node_ip}")

@pytest.mark.dependency(depends=["freeipa"])
def test_add_user(auth_server, remote_user="root", container_name="omnia_core"):
    """
    Add a user to FreeIPA from within the omnia_core container and verify.
    """
    assert auth_server, "No nodes found in 'auth_server' group in the inventory. Aborting test."

    print("\n------------ Test: Add IPA User -------------")

    for host in auth_server:
        node_ip = host.backend.host
        print(f"\nConnecting to auth server: {node_ip}")

        # Step 1: Check if the user already exists
        check_cmd = (
            f"sshpass -p {oim_password} ssh -o StrictHostKeyChecking=no {remote_user}@{oim_ip} "
            f"'podman exec {container_name} ssh -o StrictHostKeyChecking=no -o ConnectTimeout=5 {node_ip} "
            f"\"ipa user-show {username}\"'"
        )

        result = subprocess.run(check_cmd, shell=True, capture_output=True, text=True)
        time.sleep(15)  # Short wait to avoid race conditions

        if result.returncode == 0:
            print(f"User '{username}' already exists on {node_ip}. Skipping creation.")
            print("\nUser Details:\n" + result.stdout.strip())
            continue

        # Step 2: Add user
        print(f"➕ Adding user '{username}' on {node_ip}...")

        add_cmd = (
            f"sshpass -p {oim_password} ssh -o StrictHostKeyChecking=no {remote_user}@{oim_ip} "
            f"'podman exec {container_name} ssh -o StrictHostKeyChecking=no -o ConnectTimeout=5 {node_ip} "
            f"\"echo '{password}' | ipa user-add {username} "
            f"--first={first_name} --last={last_name} --password "
            f"--setattr krbPasswordExpiration='20351231235959Z'\"'"
        )

        add_result = subprocess.run(add_cmd, shell=True, capture_output=True, text=True)

        if add_result.returncode != 0 or "User login" not in add_result.stdout:
            print(f"\nFailed to add user '{username}' on {node_ip}.")
            print("Error Output:\n" + add_result.stderr.strip())
            pytest.fail(f"User creation failed on {node_ip}")
        else:
            print(f"\nUser '{username}' added successfully on {node_ip}.")
            print("\nUser Details:\n" + add_result.stdout.strip())
     
@pytest.mark.dependency(depends=["freeipa"])
def test_login_from_node(all_hosts, get_unique_ips, auth_server, remote_user="root", container_name="omnia_core"):
    """
    Test IPA user login to each node. When Slurm is configured, login should only work from auth_server nodes.
    """

    all_nodes = []
    for key in all_hosts:
        all_nodes.extend(all_hosts[key])
    unique_ips = get_unique_ips(all_nodes)
    
    print("\nInstalling sshpass in the auth_server node for validation purpose.")
    auth_server_ips = [host.backend.host for host in auth_server]
    
    for ip in auth_server_ips:
        # Install sshpass (if needed)
        install_cmd = (
            f"sshpass -p {oim_password} ssh -o StrictHostKeyChecking=no {remote_user}@{oim_ip} "
            f"'podman exec {container_name} ssh -o StrictHostKeyChecking=no {ip} "
            f"\"sudo yum install -y sshpass\"'"
        )
        subprocess.run(install_cmd, shell=True)

    # Step 0: Check if Slurm is enabled
    software_config_cmd = (
        f"sshpass -p {oim_password} ssh -o StrictHostKeyChecking=no {remote_user}@{oim_ip} "
        f"'podman exec {container_name} cat {software_config_path}'"
    )

    result = subprocess.run(software_config_cmd, shell=True, capture_output=True, text=True)
    if result.returncode != 0:
        pytest.fail(f"Failed to read software_config.json: {result.stderr.strip()}")

    try:
        config_data = json.loads(result.stdout)
        slurm_enabled = any(sw.get("name") == "slurm" for sw in config_data.get("softwares", []))
        print(f"\nSlurm enabled: {slurm_enabled}")
    except json.JSONDecodeError:
        pytest.fail("Invalid JSON in software_config.json")

    for ip in unique_ips:
        print(f"\nTesting login on node: {ip}")

        # Test login
        ssh_test_cmd = (
            f"sshpass -p {oim_password} ssh -o StrictHostKeyChecking=no {remote_user}@{oim_ip} "
            f"'podman exec {container_name} ssh -o StrictHostKeyChecking=no {ip} "
            f"\"sshpass -p {password} ssh -o StrictHostKeyChecking=no {username}@{ip} whoami\"'"
        )
        result = subprocess.run(ssh_test_cmd, shell=True, capture_output=True, text=True)
        login_success = username in result.stdout.strip()

        if slurm_enabled:
            if ip in auth_server_ips:
                assert login_success, f"Expected login to succeed on {ip}, but it failed."
                print(f"Login succeeded on {ip}")
            else:
                assert not login_success, f"Login should not succeed on non-auth node {ip}"
                print(f"Login blocked on compute node {ip}")
        else:
            assert login_success, f"Login failed on {ip} with Slurm disabled."
            print(f"Login succeeded on {ip}")


@pytest.mark.dependency(depends=["freeipa"], name='slurm')
def test_slurm_in_software_config(sync_directories, run_sshpass_command, auth_server, remote_user="root", container_name="omnia_core"):
    # Step 1: Check if FreeIPA is present in the config
    cmd = f"podman exec {container_name} cat {software_config_path}"
    result = run_sshpass_command(cmd)

    if result.returncode != 0:
        pytest.fail(f"Failed to fetch file from container: {result.stderr}")

    try:
        data = json.loads(result.stdout)
        softwares = data.get("softwares", [])
        if not any(software.get("name") == "slurm" for software in softwares):
            pytest.skip(print("\nSlurm not found in software_config.json file, skipping slurm jobs."))
        print("\nslurm found in software_config.json. Verifying slurm job using freeipa user")
        sync_directories(source, destination)
        
    except json.JSONDecodeError:
        pytest.fail("Invalid JSON in software_config.json")
    except Exception as e:
        pytest.fail(f"Unexpected error: {e}")

@pytest.mark.dependency(depends=["slurm"])
def test_replace_node_value(slurm_control_node, remote_user="root", container_name="omnia_core"):
    """
    Replaces node and task values in a Slurm job script based on available resources.
    """
    for host in slurm_control_node:
        try:
            node_ip = host.backend.host

            # Build the command to fetch node count using sinfo
            node_count_cmd = (
                f"sshpass -p {oim_password} ssh -o StrictHostKeyChecking=no {remote_user}@{oim_ip} "
                f"\"podman exec {container_name} ssh -o StrictHostKeyChecking=no -o ConnectTimeout=5 {node_ip} "
                f"sinfo --noheader -o '%D'\""
            )

            # Run the command
            result = subprocess.run(node_count_cmd, shell=True, capture_output=True, text=True)
            if result.returncode != 0:
                pytest.fail(f"Failed to fetch node count: {result.stderr}")

            node_count = result.stdout.strip()
            if not node_count.isdigit():
                pytest.fail("Node count is invalid or empty.")
            print(f"Node count from {node_ip}: {node_count}")

            # Build the script update command
            update_script_cmd = (
                f"sshpass -p {oim_password} ssh -o StrictHostKeyChecking=no {remote_user}@{oim_ip} "
                f"'podman exec {container_name} ssh -o StrictHostKeyChecking=no -o ConnectTimeout=5 {node_ip} "
                f"\"sed -i \\\"s/^#SBATCH --ntasks=n/#SBATCH --ntasks={node_count}/\\\" /home/scripts/{job_name} && "
                f"sed -i \\\"s/^#SBATCH --nodes=n/#SBATCH --nodes={node_count}/\\\" /home/scripts/{job_name}\"'"
            )


            # Run the update command
            update_result = subprocess.run(update_script_cmd, shell=True, capture_output=True, text=True)
            if update_result.returncode != 0:
                pytest.fail(f"Failed to update job script: {update_result.stderr}")

            print(f"Updated job script on {node_ip} successfully.")

        except Exception as e:
            pytest.fail(f"Error on node {host.backend.host}: {e}")

@pytest.mark.dependency(depends=["slurm"])
def test_slurm_job_submission(slurm_control_node, remote_user="root", container_name="omnia_core"):
    """
    Submit a Slurm job from the IPA user via a nested SSH from the OIM host to omnia_core container to auth server.
    """        
    
    print("\n---------Testing Slurm job submission using freeipa user----------\n")
     
    for host in slurm_control_node:
        try:
            node_ip = host.backend.host

            submit_job_cmd = (
                f"sshpass -p {oim_password} ssh -o StrictHostKeyChecking=no {remote_user}@{oim_ip} "
                f"\"podman exec {container_name} bash -c '"
                f"ssh -o StrictHostKeyChecking=no -o ConnectTimeout=5 {node_ip} "
                f"\\\"sshpass -p {password} ssh -o StrictHostKeyChecking=no {username}@{node_ip} "
                f"\\\\\\\"whoami && sbatch /home/scripts/{job_name}\\\\\\\"\\\"'\""
            )

            result = subprocess.run(submit_job_cmd, shell=True, capture_output=True, text=True)

            if result.returncode != 0:
                pytest.fail(f"\nSSH or job submission failed:\n{result.stderr.strip()}")

            output_lines = result.stdout.strip().splitlines()

            if not output_lines:
                pytest.fail(f"\nNo output received. Possible SSH or command error.")

            logged_in_user = output_lines[0].strip()
            print("\nlogged_in_user: ",logged_in_user)

            if logged_in_user != username:
                pytest.fail(f"\nLogged in user mismatch: expected '{username}', got '{logged_in_user}'")
            else:
                print(f"\nLogged in successfully to the freeipa user: {username}")

            if "Submitted batch job" not in output_lines[-1]:
                pytest.fail(f"\nJob submission failed:\n{result.stdout.strip()}")

            job_id = output_lines[-1].split()[-1]
            print(f"\nJob submitted with user '{logged_in_user}' on {node_ip}. Job ID: {job_id}")

        except Exception as e:
            pytest.fail(f"Exception on node {node_ip}: {str(e)}")



        # Wait for the job to complete (no timeout)
        while True:
            check_job_cmd = (
                f"sshpass -p {oim_password} ssh -o StrictHostKeyChecking=no {remote_user}@{oim_ip} "
                f"\"podman exec {container_name} bash -c '"
                f"ssh -o StrictHostKeyChecking=no -o ConnectTimeout=5 {node_ip} "
                f"\\\"sshpass -p {password} ssh -o StrictHostKeyChecking=no {username}@{node_ip} "
                f"\\\\\\\"squeue -j {job_id}\\\\\\\"\\\"'\""
            )

            result = subprocess.run(check_job_cmd, shell=True, capture_output=True, text=True)
            if result.returncode != 0:
                pytest.fail(f"Failed to check job status: {result.stderr}")

            if job_id not in result.stdout:
                print(f"\nJob {job_id} completed.")
                break

            print(f"Waiting for job {job_id}... still running.")
            time.sleep(5)  # Poll every 5 seconds



        # Validate job output
        job_output_path = (
                f"sshpass -p {oim_password} ssh -o StrictHostKeyChecking=no {remote_user}@{oim_ip} "
                f"\"podman exec {container_name} bash -c '"
                f"ssh -o StrictHostKeyChecking=no -o ConnectTimeout=5 {node_ip} "
                f"\\\"sshpass -p {password} ssh -o StrictHostKeyChecking=no {username}@{node_ip} "
                f"\\\\\\\"cat output_{job_id}.log\\\\\\\"\\\"'\""
            )
        
        result = subprocess.run(job_output_path, shell=True, capture_output=True, text=True)
        output = result.stdout.strip()
        
        if "Running as user: testuser" in result.stdout:
            print(f"\nJob successfully executed as Freeipa user" + f"\nOutput:\n{output}")
        elif "Running as user: root":
            pytest.fail(print(f"\nJob executed as root user" + f"\nOutput:\n{output}"))
            
        if "Hello world" in result.stdout:
            print("\nmpi job executed successfully")
        else:
            pytest.fail(print("\nmpi job failed."))


