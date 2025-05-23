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

username = config.FREEIPA_USERNAME
password = config.PASSWORD
first_name = config.FIRST_NAME
last_name = config.LAST_NAME

job_name = "job_test.slurm"
script_dir = os.path.dirname(os.path.abspath(__file__))
script_path = os.path.join(script_dir, "scripts")
source = os.path.join(script_dir, script_path)
destination = '/mnt/omnia_home_share/'

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
        print("\n✅ FreeIPA found in software_config.json. Proceeding with service checks.")
        sync_directories(source, destination)
    except json.JSONDecodeError:
        pytest.fail("Invalid JSON in software_config.json")
    except Exception as e:
        pytest.fail(f"Unexpected error: {e}")

    # Step 2: Check auth_server group presence
    assert auth_server, "❌ No nodes found in 'auth_server' group in the inventory."

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
            pytest.fail(f"❌ Failed to run ipactl status on node {node_ip}:\n{result.stderr.strip()}")

        output = result.stdout.strip()
        if not output:
            pytest.fail(f"❌ No output from ipactl status on node {node_ip}")

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
            print(f"\n✅ Running services on {node_ip}:\n" + "\n".join(f"  ✔ {svc}" for svc in running_services))
        if failing_services:
            fail_msg = f"\n❌ Failing services on {node_ip}:\n" + "\n".join(f"  ✖ {svc}" for svc in failing_services)
            pytest.fail(fail_msg)
        else:
            print(f"\n✅ All FreeIPA services are running on {node_ip}")


def test_add_user(auth_server, remote_user="root", container_name="omnia_core"):
    """
    Add a user to FreeIPA from within the omnia_core container and verify.
    """
    assert auth_server, "❌ No nodes found in 'auth_server' group in the inventory. Aborting test."

    print("\n------------ Test: Add IPA User -------------")

    for host in auth_server:
        node_ip = host.backend.host
        print(f"\n🔍 Connecting to auth server: {node_ip}")

        # Step 1: Check if the user already exists
        check_cmd = (
            f"sshpass -p {oim_password} ssh -o StrictHostKeyChecking=no {remote_user}@{oim_ip} "
            f"'podman exec {container_name} ssh -o StrictHostKeyChecking=no -o ConnectTimeout=5 {node_ip} "
            f"\"ipa user-show {username}\"'"
        )

        result = subprocess.run(check_cmd, shell=True, capture_output=True, text=True)
        time.sleep(15)  # Short wait to avoid race conditions

        if result.returncode == 0:
            print(f"⚠️  User '{username}' already exists on {node_ip}. Skipping creation.")
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
            print(f"\n❌ Failed to add user '{username}' on {node_ip}.")
            print("Error Output:\n" + add_result.stderr.strip())
            pytest.fail(f"User creation failed on {node_ip}")
        else:
            print(f"\n✅ User '{username}' added successfully on {node_ip}.")
            print("\nUser Details:\n" + add_result.stdout.strip())
            
            
def test_login_from_node(kube_node, auth_server, remote_user="root", container_name="omnia_core"):
    """
    Test IPA user login to each kube node from within the omnia_core container.
    If Slurm is configured, the user should only be able to login from auth server node.
    """
    assert kube_node, "❌ No nodes found in 'kube_node' group. Aborting test."
    assert auth_server, "❌ No nodes found in 'auth_server' group. Aborting test."

    print("\n------------ Test: Login IPA User from Node -------------")

    # Step 0: Check if Slurm is present in software_config.json
    slurm_enabled = False
    software_config_cmd = (
        f"sshpass -p {oim_password} ssh -o StrictHostKeyChecking=no {remote_user}@{oim_ip} "
        f"'podman exec {container_name} cat {software_config_path}'"
    )

    config_result = subprocess.run(software_config_cmd, shell=True, capture_output=True, text=True)
    if config_result.returncode != 0:
        pytest.fail(f"❌ Failed to fetch software_config.json from container. Error:\n{config_result.stderr.strip()}")

    try:
        config_data = json.loads(config_result.stdout)
        slurm_enabled = any(
            software.get("name") == "slurm" for software in config_data.get("softwares", [])
        )
        print(f"🔍 Slurm enabled: {slurm_enabled}")
    except json.JSONDecodeError as e:
        pytest.fail(f"❌ Failed to parse software_config.json: {e}")

    auth_server_ips = [host.backend.host for host in auth_server]

    for host in kube_node:
        node_ip = getattr(host.backend, "host", None)
        if not node_ip or not isinstance(node_ip, str) or not node_ip.strip():
            pytest.fail(f"❌ Invalid or missing node IP for host: {host}")

        print(f"\n🔍 Testing login to node: {node_ip}")

        # Step 1: Install sshpass on the node via container
        install_cmd = (
            f"sshpass -p {oim_password} ssh -o StrictHostKeyChecking=no {remote_user}@{oim_ip} "
            f"'podman exec {container_name} ssh -o StrictHostKeyChecking=no -o ConnectTimeout=5 {node_ip} "
            f"\"sudo yum install -y sshpass\"'"
        )

        install_result = subprocess.run(install_cmd, shell=True, capture_output=True, text=True)
        if install_result.returncode != 0:
            print(f"❌ Failed to install sshpass on {node_ip}.\nError:\n{install_result.stderr.strip()}")
            pytest.fail(f"sshpass installation failed on {node_ip}")

        # Step 2: Test login
        ssh_test_cmd = (
            f"sshpass -p {oim_password} ssh -o StrictHostKeyChecking=no {remote_user}@{oim_ip} "
            f"'podman exec {container_name} ssh -o StrictHostKeyChecking=no -o ConnectTimeout=5 {node_ip} "
            f"\"sshpass -p {password} ssh -o StrictHostKeyChecking=no {username}@{node_ip} whoami\"'"
        )

        login_result = subprocess.run(ssh_test_cmd, shell=True, capture_output=True, text=True)
        login_success = username in login_result.stdout.strip()

        if slurm_enabled:
            if node_ip in auth_server_ips:
                if not login_success:
                    print(f"\n❌ Login failed from auth server node {node_ip} when it should succeed.\nError:\n{login_result.stderr.strip()}")
                    pytest.fail(f"Login failed from auth server node: {node_ip}")
                else:
                    print(f"\n✅ Login successful for user '{username}' from auth server node {node_ip}.")
            else:
                if login_success:
                    print(f"\n❌ Login succeeded from non-auth node {node_ip} with Slurm enabled, which is not allowed.")
                    pytest.fail(f"Login should not succeed from compute node {node_ip} when Slurm is enabled.")
                else:
                    print(f"\n✅ Login correctly failed from compute node {node_ip} with Slurm enabled.")
        else:
            if not login_success:
                print(f"\n❌ Login failed for user '{username}' on {node_ip}.\nError:\n{login_result.stderr.strip()}")
                pytest.fail(f"Login failed on node {node_ip} when it should succeed.")
            else:
                print(f"\n✅ Login successful for user '{username}' on {node_ip}.")
                
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

def test_slurm_job_submission(slurm_control_node, remote_user="root", container_name="omnia_core"):
    """
    Submit a Slurm job from the IPA user via a nested SSH from the OIM host to omnia_core container to auth server.
    """        
    
    print("n---------Testing Slurm job submission using freeipa user----------\n")
     
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
                pytest.fail(f"\n❌ SSH or job submission failed:\n{result.stderr.strip()}")

            output_lines = result.stdout.strip().splitlines()

            if not output_lines:
                pytest.fail(f"\n❌ No output received. Possible SSH or command error.")

            logged_in_user = output_lines[0].strip()
            print("\nlogged_in_user: ",logged_in_user)
            if logged_in_user != username:
                pytest.fail(f"\n❌ Logged in user mismatch: expected '{username}', got '{logged_in_user}'")
            else:
                print(f"\nLogged in successfully to the freeipa user: {username}")

            if "Submitted batch job" not in output_lines[-1]:
                pytest.fail(f"\n❌ Job submission failed:\n{result.stdout.strip()}")

            job_id = output_lines[-1].split()[-1]
            print(f"\n✅ Job submitted with user '{logged_in_user}' on {node_ip}. Job ID: {job_id}")

        except Exception as e:
            pytest.fail(f"❌ Exception on node {node_ip}: {str(e)}")



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
                print(f"\n✅ Job {job_id} completed.")
                break

            print(f"⏳ Waiting for job {job_id}... still running.")
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
        
        if "Running as user: testuser" in result.stdout:
            print("\n✅Job successfully executed as Freeipa user")
        elif "Running as user: root":
            pytest.fail(print(f"\nJob executed as root user"))
            
        if "Hello world" in result.stdout:
            print("\n✅mpi job executed successfully")
        else:
            pytest.fail(print("\nmpi job failed."))
