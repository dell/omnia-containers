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

script_dir = os.path.dirname(os.path.abspath(__file__))
script_path = os.path.join(script_dir, "../../scripts")
source = os.path.join(script_dir, script_path)
destination = '/mnt/omnia_home_share/'    

def run_slurm_job(slurm_control_node, target_user, node_ip, container_name, oim_ip, oim_password, password):
    print(f"\n🚀 Submitting Slurm job on {node_ip} as '{target_user}'")

    if target_user  == "testuser":
        job_name = "slurm_user.sh"
    elif target_user  == "root":
        job_name = "slurm_root.sh"
    else:
        pytest.fail(print("\nInvalid username"))
    
    for host in slurm_control_node:
        try:
            node_ip = host.backend.host

            # Build the command to fetch node count using sinfo
            node_count_cmd = (
                f"sshpass -p {oim_password} ssh -o StrictHostKeyChecking=no root@{oim_ip} "
                f"\"podman exec omnia_core ssh -o StrictHostKeyChecking=no -o ConnectTimeout=5 {node_ip} "
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
                f"sshpass -p {oim_password} ssh -o StrictHostKeyChecking=no root@{oim_ip} "
                f"'podman exec omnia_core ssh -o StrictHostKeyChecking=no -o ConnectTimeout=5 {node_ip} "
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
            
    
    if target_user != "root":
        submit_job_cmd = (
            f"sshpass -p {oim_password} ssh -o StrictHostKeyChecking=no root@{oim_ip} "
            f"\"podman exec {container_name} bash -c '"
            f"ssh -o StrictHostKeyChecking=no -o ConnectTimeout=5 {node_ip} "
            f"\\\"sshpass -p {password} ssh -o StrictHostKeyChecking=no {target_user}@{node_ip} "
            f"\\\\\\\"whoami && sbatch /home/scripts/{job_name}\\\\\\\"\\\"'\""
        )
    else:
        submit_job_cmd = (
            f"sshpass -p {oim_password} ssh -o StrictHostKeyChecking=no root@{oim_ip} "
            f"\"podman exec {container_name} bash -c '"
            f"ssh -o StrictHostKeyChecking=no -o ConnectTimeout=5 {node_ip} "
            f"\\\"whoami && sbatch /home/scripts/{job_name} \\\"'\""
        )
        

    result = subprocess.run(submit_job_cmd, shell=True, capture_output=True, text=True)
    if result.returncode != 0:
        pytest.fail(f"\n❌ Job submission failed:\n{result.stderr.strip()}")

    output_lines = result.stdout.strip().splitlines()
    if not output_lines:
        pytest.fail("\n❌ No output received after job submission.")

    logged_in_user = output_lines[0].strip()
    if logged_in_user != target_user:
        pytest.fail(f"\n❌ Logged in user mismatch: expected '{target_user}', got '{logged_in_user}'")
    print(f"✅ Logged in as {logged_in_user}")

    if "Submitted batch job" not in output_lines[-1]:
        pytest.fail(f"\n❌ Job not submitted:\n{result.stdout.strip()}")

    job_id = output_lines[-1].split()[-1]
    print(f"✅ Job submitted. Job ID: {job_id}")

    # Wait for job to complete
    while True:
        check_job_cmd = (
            f"sshpass -p {oim_password} ssh -o StrictHostKeyChecking=no root@{oim_ip} "
            f"\"podman exec {container_name} bash -c '"
            f"ssh -o StrictHostKeyChecking=no -o ConnectTimeout=5 {node_ip} "
            f"sshpass -p {password} ssh -o StrictHostKeyChecking=no {target_user}@{node_ip} "
            f"\\\"squeue -j {job_id}\\\"'\""
        )

        result = subprocess.run(check_job_cmd, shell=True, capture_output=True, text=True)
        if result.returncode != 0:
            pytest.fail(f"❌ Failed to check job status: {result.stderr}")

        if job_id not in result.stdout:
            print(f"✅ Job {job_id} completed.")
            break

        print(f"⏳ Waiting for job {job_id}...")
        time.sleep(5)

    # Check output
    if target_user != "root":
        output_cmd = (
            f"sshpass -p {oim_password} ssh -o StrictHostKeyChecking=no root@{oim_ip} "
            f"\"podman exec {container_name} bash -c '"
            f"ssh -o StrictHostKeyChecking=no -o ConnectTimeout=5 {node_ip} "
            f"\\\"cat /home/testuser/output_{job_id}.log \\\"'\""
        )
    else:
        output_cmd = (
            f"sshpass -p {oim_password} ssh -o StrictHostKeyChecking=no root@{oim_ip} "
            f"\"podman exec {container_name} bash -c '"
            f"ssh -o StrictHostKeyChecking=no -o ConnectTimeout=5 {node_ip} "
            f"\\\"cat /home/output_{job_id}.log \\\"'\""
        )

    result = subprocess.run(output_cmd, shell=True, capture_output=True, text=True)
    output = result.stdout.strip()

    if f"Running as user: {target_user}" not in output:
        pytest.fail(f"❌ Job did not run as expected user: {target_user}\nOutput:\n{output}")

    if "Hello world" in output:
        print(f"✅ Job executed successfully as '{target_user}'\n📄 Output:\n{output}")
    else:
        pytest.fail(f"❌ MPI job failed for user: {target_user}\nOutput:\n{output}")

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
        
    # Step 1: Check slurm_node group presence
    assert slurm_node, "❌ No nodes found in 'slurm_node' group in the inventory."

    # Step 2: Check slurmd status on slurm head node
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
def test_slurm_node_state(slurm_control_node, remote_user="root", container_name="omnia_core"):
    # Step 1: Check slurm_node group presence
    assert slurm_control_node, "❌ No nodes found in 'slurm_node' group in the inventory."

    for host in slurm_control_node:
        node_ip = host.backend.host
        print(f"\n🔍 Checking slurm node states from control node: {node_ip}")

        try:
            # Step 2: Run sinfo command inside the container via SSH
            ssh_cmd = (
                f"sshpass -p {oim_password} ssh -o StrictHostKeyChecking=no {remote_user}@{oim_ip} "
                f"\"podman exec {container_name} ssh -o StrictHostKeyChecking=no -o ConnectTimeout=5 {node_ip} "
                f"sinfo -N -h\""
            )

            result = subprocess.run(ssh_cmd, shell=True, capture_output=True, text=True)

            if result.returncode != 0:
                pytest.fail(f"❌ Failed to run sinfo on head node {node_ip}:\n{result.stderr.strip()}")

            output = result.stdout

            non_idle_nodes = []
            idle_nodes = []
            
            for line in output.splitlines():
                parts = line.split()
                node_name = parts[0]
                state = parts[-1]  # STATE is usually last column
                if state.lower() == 'idle':
                    idle_nodes.append((node_name, state))
                else:
                    non_idle_nodes.append((node_name, state))
            
            if not idle_nodes:
                pytest.fail(print("\n No nodes are in idle state."))    
                        
            if idle_nodes:
                print("\n Nodes in Idle state: ")
                for node, state in idle_nodes:
                    print(f"   - {node}: {state}")

            if non_idle_nodes:
                print(f"\n❌ Nodes not in idle state:")
                for node, state in non_idle_nodes:
                    print(f"   - {node}: {state}")
                pytest.fail("Some SLURM nodes are not in 'idle' state.")

        except Exception as e:
            pytest.fail(f"❌ Exception occurred while checking SLURM nodes on {node_ip}: {e}")


@pytest.mark.dependency(depends=["slurm"])            
def test_slurm_job_as_root(slurm_control_node):
    print("\n🧪 Running Slurm job as ROOT user\n")
    for host in slurm_control_node:
        node_ip = host.backend.host
        run_slurm_job(
            slurm_control_node,
            target_user="root",
            node_ip=node_ip,
            container_name="omnia_core",
            oim_ip=oim_ip,
            oim_password=oim_password,
            password=password  # root password if needed
        )


@pytest.mark.dependency(depends=["slurm"])
def test_slurm_job_as_freeipa_user(run_sshpass_command, slurm_control_node):
    print("\n🧪 Checking FreeIPA presence...\n")

    cmd = f"podman exec omnia_core cat {software_config_path}"
    result = run_sshpass_command(cmd)
    if result.returncode != 0:
        pytest.fail(f"❌ Failed to read software_config.json: {result.stderr}")

    try:
        data = json.loads(result.stdout)
        softwares = data.get("softwares", [])
        if not any(s.get("name") == "freeipa" for s in softwares):
            pytest.skip("⚠️ FreeIPA not found. Skipping FreeIPA user job test.")
    except Exception as e:
        pytest.fail(f"❌ Error parsing software_config.json: {str(e)}")

    print("\n✅ FreeIPA found. Running job as FreeIPA user.\n")
    for host in slurm_control_node:
        node_ip = host.backend.host
        run_slurm_job(
            slurm_control_node,
            target_user=username,
            node_ip=node_ip,
            container_name="omnia_core",
            oim_ip=oim_ip,
            oim_password=oim_password,
            password=password
        )
