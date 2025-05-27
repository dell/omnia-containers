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
first_name = config.FIRST_NAME
last_name = config.LAST_NAME

software_config_path = "/opt/omnia/input/project_default/software_config.json"
expect_k8s_version = "v1.31.4"

job_name = "test-k8s.job"
script_dir = os.path.dirname(os.path.abspath(__file__))
script_path = os.path.join(script_dir, "scripts")
source = os.path.join(script_dir, script_path)
destination = '/mnt/omnia_home_share/'

import subprocess
import pytest
import time

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

def run_k8s_job(target_user, node_ip, job_name, container_name, oim_ip, oim_password):
    print(f"\n🚀 Submitting k8s job on {node_ip} as '{target_user}'")

    # Submit job
    result = run_ssh_command(
        oim_ip, container_name, node_ip,
        f"kubectl apply -f /home/scripts/{job_name}",
        oim_password
    )
    if result.returncode != 0:
        pytest.fail(print(f"\n❌ Job submission failed:\n{result.stderr.strip()}"))
    print("\n✅ Job submitted successfully!")

    # Wait for pod to start
    time.sleep(10)

    # Get pods
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

        
@pytest.mark.dependency(name='k8s')
def test_k8s_installation(sync_directories, run_sshpass_command, kube_control_plane, remote_user="root", container_name="omnia_core"):
    # Step 1: Read the config file from the container
    cmd = f"podman exec {container_name} cat {software_config_path}"
    result = run_sshpass_command(cmd)

    if result.returncode != 0:
        pytest.fail(print(f"Failed to fetch file from container: {result.stderr}"))

    try:
        data = json.loads(result.stdout)
        softwares = data.get("softwares", [])
        
        # Find the k8s config
        k8s_config = next((s for s in softwares if s.get("name") == "k8s"), None)
        if not k8s_config:
            pytest.skip(print("Skipping k8s tests: 'k8s' not found in software_config.json"))
        print("\n✅ 'k8s' found in software_config.json.")
        sync_directories(source, destination)

        # Step 2: Check kube_control_plane group presence
        assert kube_control_plane, "❌ No nodes found in 'kube_control_plane' group in the inventory."
    
        for host in kube_control_plane:
            node_ip = host.backend.host

            print(f"\n🔍 Checking 'kubectl version'")

            ssh_cmd = (
                f"sshpass -p {oim_password} ssh -o StrictHostKeyChecking=no {remote_user}@{oim_ip} "
                f"\"podman exec {container_name} ssh -o StrictHostKeyChecking=no -o ConnectTimeout=5 {node_ip} "
                f"kubectl version --client | grep 'Client Version' | awk '{{print $3}}'\""
            )

            result = subprocess.run(ssh_cmd, shell=True, capture_output=True, text=True)

            if result.returncode != 0:
                pytest.fail(print(f"❌ Failed to run kubectl version on node {node_ip}:\n{result.stderr.strip()}"))

            k8s_version = result.stdout
            
            if expect_k8s_version == k8s_version:
                pytest.fail(print(f"Kubernetes version incorrect, expected:{expect_k8s_version}, got:{k8s_version}"))
            print(f"Kubernetes version verified: {k8s_version}")
        
    except json.JSONDecodeError:
        pytest.fail("Invalid JSON in software_config.json")
    except Exception as e:
        pytest.fail(f"Unexpected error: {e}")

@pytest.mark.dependency(depends=["k8s"])
def test_kubelet_service(kube_node, remote_user="root", container_name="omnia_core"):
    """
    Test to verify if the kubelet service is running.
    """
    print("\n---------- Testing kubelet service on daemon nodes ----------")

    failed_nodes = []
    success_nodes = []

    count = len(kube_node)

    for host in kube_node:
        node_ip = host.backend.host

        try:
            print(f"\nConnecting to node: {node_ip}")

            ssh_cmd = (
                f"sshpass -p {oim_password} ssh -o StrictHostKeyChecking=no {remote_user}@{oim_ip} "
                f"\"podman exec {container_name} ssh -o StrictHostKeyChecking=no -o ConnectTimeout=5 {node_ip} "
                f"systemctl is-active kubelet\""
            )

            result = subprocess.run(ssh_cmd, shell=True, capture_output=True, text=True)

            if result.returncode != 0:
                print(f"Failed to check kubelet service on node {node_ip}: {result.stderr.strip()}")
                failed_nodes.append(node_ip)
                continue

            kubelet_active = result.stdout.strip()

            if kubelet_active == "active":
                success_nodes.append(node_ip)
                print(f"✅ Kubelet is active on node: {node_ip}")
            else:
                print(f"❌ Kubelet is not active on node: {node_ip} (status: {kubelet_active})")
                failed_nodes.append(node_ip)

        except Exception as e:
            print(f"\nError on the node {node_ip}: {e}")
            failed_nodes.append(node_ip)

    if len(success_nodes) == count:
        print("All the nodes have kubelet running successfully!")
    else:
        print(f"❌ Kubelet is not running on nodes: {failed_nodes}")
        pytest.fail(print(f"Kubelet service inactive on nodes: {failed_nodes}"))


@pytest.mark.dependency(depends=["k8s"])
def test_kubectl_commands(kube_control_plane, remote_user="root", container_name="omnia_core"):
    """
    Test to verify basic kubectl commands on all control plane nodes.
    """
    print("\n------ Testing basic kubectl commands on kube control plane ------\n")

    kubectl_cmds = ['kubectl get pods -A', 'kubectl get nodes', 'kubectl get svc -A']
    failed_cmds = []

    for host in kube_control_plane:
        node_ip = host.backend.host
        print(f"\n🔍 Connecting to node: {node_ip}")

        for cmd in kubectl_cmds:
            print(f"▶️ Running: {cmd}")
            ssh_cmd = (
                f"sshpass -p {oim_password} ssh -o StrictHostKeyChecking=no {remote_user}@{oim_ip} "
                f"\"podman exec {container_name} ssh -o StrictHostKeyChecking=no -o ConnectTimeout=5 {node_ip} "
                f"{cmd}\""
            )

            result = subprocess.run(ssh_cmd, shell=True, capture_output=True, text=True)

            if result.returncode != 0:
                print(f"❌ Command '{cmd}' failed on node {node_ip}: {result.stderr.strip()}")
                failed_cmds.append((node_ip, cmd))
            else:
                print(f"✅ Command succeeded on {node_ip}")

    if failed_cmds:
        error_details = "\n".join([f"Node: {node}, Command: {command}" for node, command in failed_cmds])
        pytest.fail(print(f"\nSome kubectl commands failed:\n{error_details}"))
    
    print("\nAll kubectl commands ran successfully on kube control plane")


@pytest.mark.dependency(depends=["k8s"])
def test_all_pods_running(kube_control_plane, remote_user="root", container_name="omnia_core"):
    """
    Test to verify that all pods across control plane nodes are in 'Running' or 'Completed' state.
    """
    print("\n------ Verifying that all pods are in 'Running' or 'Completed' state ------")

    all_pod_statuses = []
    failed_nodes = []

    for host in kube_control_plane:
        node_ip = host.backend.host
        print(f"\n🔍 Connecting to node: {node_ip}")

        try:
            ssh_cmd = (
                f"sshpass -p {oim_password} ssh -o StrictHostKeyChecking=no {remote_user}@{oim_ip} "
                f"\"podman exec {container_name} ssh -o StrictHostKeyChecking=no -o ConnectTimeout=5 {node_ip} "
                f"kubectl get pods -A\""
            )

            result = subprocess.run(ssh_cmd, shell=True, capture_output=True, text=True)

            if result.returncode != 0:
                print(f"❌ Failed to retrieve pods on node {node_ip}: {result.stderr.strip()}")
                failed_nodes.append(node_ip)
                continue

            output = result.stdout.strip()
            print(f"📄 Output from node {node_ip}:\n{output}")

            lines = output.splitlines()

            for line in lines[1:]:  # Skip the header
                columns = line.split()
                if len(columns) >= 4:
                    namespace = columns[0]
                    pod_name = columns[1]
                    ready = columns[2]
                    status = columns[3]
                    all_pod_statuses.append((node_ip, namespace, pod_name, ready, status))

        except Exception as e:
            pytest.fail(print(f"\n❌ Error while connecting to node {node_ip}: {e}"))

    not_running_pods = [
        (node, namespace, pod, ready, status)
        for node, namespace, pod, ready, status in all_pod_statuses
        if status not in ["Running", "Completed"]
    ]

    if failed_nodes:
        pytest.fail(print(f"\n❌ Failed to retrieve pod information from nodes: {failed_nodes}"))

    if not_running_pods:
        error_summary = "\n".join([
            f"Node: {node} | Namespace: {namespace} | Pod: {pod} | Status: {status}"
            for node, namespace, pod, ready, status in not_running_pods
        ])
        pytest.fail(print(f"\n❌ Some pods are not in a healthy state:\n{error_summary}"))

    print("\n✅ All pods are in 'Running' or 'Completed' state across all control plane nodes.")

def test_list_of_kube_nodes(kube_node, kube_control_plane, remote_user="root", container_name="omnia_core"):
    kube_nodes_inv = []
    mismatched_nodes = []

    # Step 1: Collect inventory IPs
    for host in kube_node:
        node_ip = host.backend.host
        kube_nodes_inv.append(node_ip)

    print(f"📦 Inventory node IPs: {kube_nodes_inv}")

    # Step 2: Query kubectl on control plane node(s)
    for host in kube_control_plane:
        node_ip = host.backend.host
        print(f"\nConnecting to control plane node: {node_ip}")

        try:
            ssh_cmd = (
                f"sshpass -p {oim_password} ssh -o StrictHostKeyChecking=no {remote_user}@{oim_ip} "
                f"\"podman exec {container_name} ssh -o StrictHostKeyChecking=no -o ConnectTimeout=5 {node_ip} "
                f"kubectl get nodes --no-headers -o custom-columns=NAME:.metadata.name\""
            )

            result = subprocess.run(ssh_cmd, shell=True, capture_output=True, text=True)

            if result.returncode != 0:
                print(f"❌ Failed to retrieve node list on {node_ip}: {result.stderr.strip()}")
                failed_nodes.append(node_ip)
                continue

            output = result.stdout.strip()
            kube_nodes = output.splitlines()
            print(f"\nOutput from control plane {node_ip}:\n{kube_nodes}")

            # Step 3: Validate strict match
            missing_nodes = [ip for ip in kube_nodes_inv if ip not in kube_nodes]   #ip in inv but not in o/p
            extra_nodes = [name for name in kube_nodes if name not in kube_nodes_inv] #ip in o/p but not in inv

            if missing_nodes:
                print(f"\nMissing nodes in the output fron kube nodes: {missing_nodes}")
                mismatched_nodes.extend(missing_nodes)

            if extra_nodes:
                print(f"\nExtra/unexpected nodes in output fron kube nodes: {extra_nodes}")
                mismatched_nodes.extend(extra_nodes)

        except Exception as e:
            print(f"\n❌ Error on the node {node_ip}: {e}")

    # Step 4: Final result
    if mismatched_nodes:
        pytest.fail(print(f"\nMismatched nodes: {mismatched_nodes}"))


@pytest.mark.dependency(depends=["k8s"])
def test_k8s_job_as_root_user(kube_control_plane):
    print("\n🧪 Running k8s job as ROOT user\n")
    for host in kube_control_plane:
        node_ip = host.backend.host
        run_k8s_job(
            target_user="root",
            node_ip=node_ip,
            job_name=job_name,
            container_name="omnia_core",
            oim_ip=oim_ip,
            oim_password=oim_password
        )
