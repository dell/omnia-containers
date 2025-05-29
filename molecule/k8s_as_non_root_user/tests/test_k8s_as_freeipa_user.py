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
username = config.FREEIPA_USERNAME
password = config.PASSWORD

software_config_path = "/opt/omnia/input/project_default/software_config.json"

script_dir = os.path.dirname(os.path.abspath(__file__))
script_path = os.path.join(script_dir, "../../scripts")
source = os.path.join(script_dir, script_path)
destination = '/mnt/omnia_home_share/' 

def run_ssh_command(oim_ip, container_name, node_ip, inner_cmd, oim_password):
    """
    Runs a kubectl or shell command via nested SSH + podman exec.
    Returns: CompletedProcess object
    """
    ssh_cmd = (
        f"sshpass -p {oim_password} ssh -o StrictHostKeyChecking=no root@{oim_ip} "
        f"\"podman exec {container_name} bash -c '"
        f"ssh -o StrictHostKeyChecking=no -o ConnectTimeout=5 {node_ip} "
        f"\\\"{inner_cmd}\\\"'\""
    )
    return subprocess.run(ssh_cmd, shell=True, capture_output=True, text=True)

def run_k8s_job(kube_control_plane, target_user, node_ip, container_name, oim_ip, oim_password, password):
    print(f"\n🚀 Submitting k8s job on {node_ip} as '{target_user}'")

    job_name = "test-k8s.job"

    # Submit job
    submit_job_cmd = (
            f"sshpass -p {oim_password} ssh -o StrictHostKeyChecking=no root@{oim_ip} "
            f"\"podman exec {container_name} bash -c '"
            f"ssh -o StrictHostKeyChecking=no -o ConnectTimeout=5 {node_ip} "
            f"\\\"sshpass -p {password} ssh -o StrictHostKeyChecking=no {target_user}@{node_ip} "
            f"\\\\\\\"whoami && kubectl apply -f /home/scripts/{job_name}\\\\\\\"\\\"'\""
        )
    
    result = subprocess.run(submit_job_cmd, shell=True, capture_output=True, text=True)
    
    if result.returncode != 0:
        pytest.fail(print(f"\n❌ Job submission failed:\n{result.stderr.strip()}"))
    print("\n✅ Job submitted successfully!")        
        
    # Wait for pod to start
    time.sleep(10)

    output_lines = result.stdout.strip().splitlines()
    if not output_lines:
        pytest.fail("\n❌ No output received after job submission.")
        
    logged_in_user = output_lines[0].strip()
    if logged_in_user != target_user:
        pytest.fail(f"\n❌ Logged in user mismatch: expected '{target_user}', got '{logged_in_user}'")
    print(f"✅ Logged in as {logged_in_user}")
    
    # get pods
    result = run_ssh_command(
        oim_ip, container_name, node_ip,
        "kubectl get pods --no-headers",
        oim_password
    )
    
    if result.returncode != 0:
        pytest.fail(print(f"❌ Failed to get pods: {result.stderr.strip()}"))
        
    pod_name = None
    for line in result.stdout.strip().splitlines():
        cols = line.split()
        if cols[0].startswith("k8s-example-job"):
            pod_name = cols[0]
            pod_status = cols[2]
            if pod_status == "Completed":
                print(f"\n✅ Pod '{pod_name}' completed successfully.")
            else:
                pytest.fail(print(f"\n❌ Pod '{pod_name}' did not complete successfully. Status: {pod_status}"))
            break

    if not pod_name:
        pytest.fail(print("\n❌ 'k8s-example-job' pod not found."))

    # Get logs
    result = run_ssh_command(
        oim_ip, container_name, node_ip,
        f"kubectl logs {pod_name}",
        oim_password
    )
    if result.returncode != 0:
        pytest.fail(print(f"❌ Failed to get logs: {result.stderr.strip()}"))
    logs = result.stdout.strip()
    print(f"\n📦 Logs from pod '{pod_name}':\n{logs}")

    if "Hello from k8s" in logs:
        print("\n✅ Job log contains expected output.")
    else:
        pytest.fail(print(f"\n❌ Unexpected job output:\n{logs}"))

    # Delete job
    result = run_ssh_command(
        oim_ip, container_name, node_ip,
        f"kubectl delete -f /home/scripts/{job_name}",
        oim_password
    )
    if result.returncode != 0:
        pytest.fail(print(f"\n❌ Job deletion failed:\n{result.stderr.strip()}"))
    print("\nJob deleted successfully.")
              

def test_k8s_job_as_freeipa_user(run_sshpass_command, kube_control_plane):
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
    for host in kube_control_plane:
        node_ip = host.backend.host
        run_k8s_job(
            kube_control_plane,
            target_user=username,
            node_ip=node_ip,
            container_name="omnia_core",
            oim_ip=oim_ip,
            oim_password=oim_password,
            password=password
        )
