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
username = config.FREEIPA_USERNAME
password = config.PASSWORD

software_config_path = "/opt/omnia/input/project_default/software_config.json"

job_name = "job_test.slurm"
script_dir = os.path.dirname(os.path.abspath(__file__))
script_path = os.path.join(script_dir, "scripts")
source = os.path.join(script_dir, script_path)
destination = '/mnt/omnia_home_share/'    

@pytest.mark.dependency(name='slurm')
def test_slurmctld_status(sync_directories, run_sshpass_command, slurm_control_node, remote_user="root", container_name="omnia_core"):
    # Step 1: Check if slurm is present in the config
    cmd = f"podman exec {container_name} cat {software_config_path}"
    result = run_sshpass_command(cmd)

    if result.returncode != 0:
        pytest.fail(f"Failed to fetch file from container: {result.stderr}")

    try:
        data = json.loads(result.stdout)
        softwares = data.get("softwares", [])
        if not any(software.get("name") == "slurm" for software in softwares):
            pytest.skip("Skipping slurm tests: 'slurm' not found in software_config.json")
        print("\n✅ slurm found in software_config.json. Proceeding with service checks.")
        sync_directories(source, destination)
    except json.JSONDecodeError:
        pytest.fail("Invalid JSON in software_config.json")
    except Exception as e:
        pytest.fail(f"Unexpected error: {e}")
        
        
    # Step 2: Check slurm_control_node group presence
    assert slurm_control_node, "❌ No nodes found in 'slurm_control_node' group in the inventory."

    # Step 3: Check slurmctld status on slurm head node
    for host in slurm_control_node:
        node_ip = host.backend.host
        print(f"\n🔍 Checking slurmctld status on slurm head node: {node_ip}")

    ssh_cmd = (
        f"sshpass -p {oim_password} ssh -o StrictHostKeyChecking=no {remote_user}@{oim_ip} "
        f"'podman exec {container_name} ssh -o StrictHostKeyChecking=no -o ConnectTimeout=5 {node_ip} "
        f"systemctl status slurmctld.service'"
    )

    result = subprocess.run(ssh_cmd, shell=True, capture_output=True, text=True)

    if result.returncode != 0:
        pytest.fail(f"❌ Failed to run slurmctld status on head node {node_ip}:\n{result.stderr.strip()}")

    if "Active: active (running)" not in result.stdout:
        pytest.fail(f"❌ slurmctld is not running on {host.backend.host}.\nStatus Output:\n{result.stdout.strip()}")

    print(f"✅ slurmctld is ACTIVE on {host.backend.host}.")
    
@pytest.mark.dependency(depends=["slurm"])
def test_slurmd_status(slurm_node, remote_user="root", container_name="omnia_core"):       
        
    # Step 2: Check slurm_node group presence
    assert slurm_node, "❌ No nodes found in 'slurm_node' group in the inventory."

    # Step 3: Check slurmd status on slurm head node
    for host in slurm_node:
        node_ip = host.backend.host
        print(f"\n🔍 Checking slurmd status on slurm head node: {node_ip}")

    ssh_cmd = (
        f"sshpass -p {oim_password} ssh -o StrictHostKeyChecking=no {remote_user}@{oim_ip} "
        f"'podman exec {container_name} ssh -o StrictHostKeyChecking=no -o ConnectTimeout=5 {node_ip} "
        f"systemctl status slurmd.service'"
    )

    result = subprocess.run(ssh_cmd, shell=True, capture_output=True, text=True)

    if result.returncode != 0:
        pytest.fail(f"❌ Failed to run slurmd status on head node {node_ip}:\n{result.stderr.strip()}")

    if "Active: active (running)" not in result.stdout:
        pytest.fail(f"❌ slurmd is not running on {host.backend.host}.\nStatus Output:\n{result.stdout.strip()}")

    print(f"✅ slurmd is ACTIVE on {host.backend.host}.")

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
def test_job_submission(run_sshpass_command, slurm_control_node, remote_user="root", container_name="omnia_core"):
    """
    Submit a Slurm job via a nested SSH from the OIM host to omnia_core container to auth server.
    If FreeIPA is configured, run as FreeIPA user; otherwise, run as root.
    """
    cmd = f"podman exec {container_name} cat {software_config_path}"
    result = run_sshpass_command(cmd)

    if result.returncode != 0:
        pytest.fail(f"Failed to fetch file from container: {result.stderr}")

    try:
        data = json.loads(result.stdout)
        softwares = data.get("softwares", [])
        use_freeipa = any(software.get("name") == "freeipa" for software in softwares)
    except json.JSONDecodeError as e:
        pytest.fail(f"Failed to parse JSON: {str(e)}")

    if use_freeipa:
        target_user = username  # FreeIPA user
        print("\n✅ FreeIPA found. Executing job as FreeIPA user.")
    else:
        target_user = "root"
        print("\n⚠️ FreeIPA not found. Executing job as root user.")

    for host in slurm_control_node:
        try:
            node_ip = host.backend.host

            submit_job_cmd = (
                f"sshpass -p {oim_password} ssh -o StrictHostKeyChecking=no {remote_user}@{oim_ip} "
                f"\"podman exec {container_name} bash -c '"
                f"ssh -o StrictHostKeyChecking=no -o ConnectTimeout=5 {node_ip} "
                f"\\\"sshpass -p {password} ssh -o StrictHostKeyChecking=no {target_user}@{node_ip} "
                f"\\\\\\\"whoami && sbatch /home/scripts/{job_name}\\\\\\\"\\\"'\""
            )

            result = subprocess.run(submit_job_cmd, shell=True, capture_output=True, text=True)

            if result.returncode != 0:
                pytest.fail(f"\n❌ SSH or job submission failed:\n{result.stderr.strip()}")

            output_lines = result.stdout.strip().splitlines()

            if not output_lines:
                pytest.fail(f"\n❌ No output received. Possible SSH or command error.")

            logged_in_user = output_lines[0].strip()
            print("\nlogged_in_user: ", logged_in_user)
            if logged_in_user != target_user:
                pytest.fail(f"\n❌ Logged in user mismatch: expected '{target_user}', got '{logged_in_user}'")
            else:
                print(f"\n✅ Logged in successfully as user: {target_user}")

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
                f"\\\"sshpass -p {password} ssh -o StrictHostKeyChecking=no {target_user}@{node_ip} "
                f"\\\\\\\"squeue -j {job_id}\\\\\\\"\\\"'\""
            )

            result = subprocess.run(check_job_cmd, shell=True, capture_output=True, text=True)
            if result.returncode != 0:
                pytest.fail(f"Failed to check job status: {result.stderr}")

            if job_id not in result.stdout:
                print(f"\n✅ Job {job_id} completed.")
                break

            print(f"⏳ Waiting for job {job_id}... still running.")
            time.sleep(5)

        # Validate job output
        job_output_cmd = (
            f"sshpass -p {oim_password} ssh -o StrictHostKeyChecking=no {remote_user}@{oim_ip} "
            f"\"podman exec {container_name} bash -c '"
            f"ssh -o StrictHostKeyChecking=no -o ConnectTimeout=5 {node_ip} "
            f"\\\"sshpass -p {password} ssh -o StrictHostKeyChecking=no {target_user}@{node_ip} "
            f"\\\\\\\"cat output_{job_id}.log\\\\\\\"\\\"'\""
        )

        result = subprocess.run(job_output_cmd, shell=True, capture_output=True, text=True)
        output = result.stdout.strip()

        if f"Running as user: {target_user}" in output:
            print(f"\n✅ Job successfully executed as user: {target_user}" + f"\nOutput:\n{output}")
        else:
            pytest.fail(f"\n❌ Job did not run as expected user '{target_user}'. Output:\n{output}")
            

        if "Hello world" in output:
            print("\n✅ MPI job executed successfully")
        else:
            pytest.fail("\n❌ MPI job failed.")
