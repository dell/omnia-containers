# Copyright 2025 Dell Inc. or its subsidiaries. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Kubernetes operations for OMNIA test automation.

This module provides functions to interact with Kubernetes clusters
from within the OMNIA test environment.
"""

import csv
import io
import json
import os
import re
import shlex
import time
import yaml

from paramiko import AutoAddPolicy, SSHClient
from automation_library.checks.vars.oim_prereq_vars import (
    USER_CONFIG_PATH as DEFAULT_USER_CONFIG_PATH,
)
from automation_library.kubernetes.messages.k8s_msgs import (
    ERROR_NO_CONTROL_PLANE_NODES,
    ERROR_NO_NODES_FOUND,
    HA_INVALID_YAML,
    HA_NO_CONTROL_PLANE_NODES,
    HA_VIP_CHECK_FAILED,
    HA_VIP_CHECK_PASSED,
    HA_VIP_CONFIGURED,
    HA_VIP_MULTIPLE_NODES,
    HA_VIP_NOT_CONFIGURED,
    HA_VIRTUAL_IP_NOT_FOUND,
    POD_CHECK_FAILED,
    POD_CHECK_PASSED,
    POD_CHECK_PREFIX,
    POD_NOT_FOUND,
    POD_STATUS,
    RUNTIME_CHECK_ALL_PASSED,
    RUNTIME_CHECK_ERROR,
    RUNTIME_CHECK_FAILED,
    RUNTIME_CHECK_HEADER,
    RUNTIME_CHECK_NODE_ERROR,
    RUNTIME_CHECK_NODE_FAIL,
    RUNTIME_CHECK_NODE_PASS,
    RUNTIME_CHECK_NO_NODES,
    RUNTIME_CHECK_PASSED,
    RUNTIME_CHECK_SOME_FAILED,
    RUNTIME_MISMATCH,
    EXPECTED_RUNTIME_MSG,
)
from automation_library.kubernetes.vars.k8s_vars import (
    CRI_O_SERVICE,
    CRIO_SERVICE,
    CONTROL_PLANE_GROUP,
    HA_CONFIG_FILE,
    KUBELET_SERVICE,
    READY_STATE_MAX_RETRIES,
    READY_STATE_RETRY_DELAY_SECONDS,
    WORKER_NODE_GROUP,
)

# Constants
USER_CONFIG_PATH = DEFAULT_USER_CONFIG_PATH
OMNIA_CORE_CONTAINER_NAME = "omnia_core"
PXE_MAPPING_FILE_PATH = "/opt/omnia/input/project_default/pxe_mapping_file.csv"

class OIMOperations:
    """Collection of Kubernetes validation helpers used by OMNIA automation."""
    def __init__(self, config_path=None):
        """Initialize OIM operations with configuration.

        Args:
            config_path (str, optional): Path to the user config file.
                Defaults to USER_CONFIG_PATH.
        """
        self.config_path = config_path or USER_CONFIG_PATH
        self.config = self._load_config()
        self.ssh_client = None
        self._omnia_core_container_id = None

    def _load_config(self):
        """Load configuration from user config file."""
        with open(self.config_path, 'r', encoding="utf-8") as file:
            return yaml.safe_load(file)

    def connect_ssh(self):
        """Establish SSH connection to OIM server."""
        if self.ssh_client is None:
            self.ssh_client = SSHClient()
            self.ssh_client.set_missing_host_key_policy(AutoAddPolicy())
            self.ssh_client.connect(
                self.config['oim_server_ip'],
                username=self.config['oim_ssh_user'],
                password=self.config['oim_ssh_password'],
                port=self.config.get('oim_ssh_port', 22)
            )
        return self.ssh_client

    def _run_ssh_command(self, command):
        """Run a command on the remote server via SSH and return the output.

        Args:
            command (str): The command to run on the remote server.

        Returns:
            str: The command output.

        Raises:
            Exception: If the command fails.
        """
        if not self.ssh_client:
            self.connect_ssh()

        _stdin, stdout, stderr = self.ssh_client.exec_command(command)
        exit_code = stdout.channel.recv_exit_status()
        output = stdout.read().decode('utf-8').strip()
        error = stderr.read().decode('utf-8').strip()

        if exit_code != 0:
            raise RuntimeError(f"Command failed with exit code {exit_code}: {error}")

        return output

    def read_pxe_mapping_file(self):
        """Read pxe_mapping_file from omnia_core container using Podman.

        Returns:
            str: The content of the pxe_mapping_file.

        Raises:
            Exception: If the file cannot be read or the container is not found.
        """
        hostname = "<unknown>"
        try:
            # Get the container ID if only name is provided
            get_container_cmd = (
                f"podman ps --filter 'name={OMNIA_CORE_CONTAINER_NAME}' --format '{{{{.ID}}}}'"
            )
            container_id = self._run_ssh_command(get_container_cmd)

            if not container_id:
                raise RuntimeError(f"Container '{OMNIA_CORE_CONTAINER_NAME}' not found")

            self._omnia_core_container_id = container_id

            # Read the file from the container
            read_cmd = f"podman exec {container_id} cat {PXE_MAPPING_FILE_PATH}"
            return self._run_ssh_command(read_cmd)

        except Exception as e:
            raise RuntimeError(f"Error reading pxe_mapping_file: {str(e)}") from e

    def close(self):
        """Close SSH connection."""
        if self.ssh_client:
            self.ssh_client.close()
            self.ssh_client = None

    def get_virtual_ip_from_config(self):
        """
        Get the virtual IP address from the high availability config file.

        Returns:
            str: The virtual IP address

        Raises:
            Exception: If there's an error reading or parsing the config file
        """
        # Read the high availability config file
        rc, ha_config_content, err = self._run_in_omnia_core(f"cat {HA_CONFIG_FILE}")

        if rc != 0:
            raise RuntimeError(f"Failed to read {HA_CONFIG_FILE}: {err}")

        # Parse the YAML content
        try:
            ha_config = yaml.safe_load(ha_config_content)
            virtual_ip = ha_config.get('service_k8s_cluster_ha', [{}])[0].get('virtual_ip_address')

            if not virtual_ip:
                raise ValueError(HA_VIRTUAL_IP_NOT_FOUND)

            return virtual_ip

        except yaml.YAMLError as e:
            raise RuntimeError(HA_INVALID_YAML.format(file_path=HA_CONFIG_FILE)) from e

    def get_control_plane_nodes(self):
        """
        Get all control plane nodes from PXE mapping.

        Returns:
            list: List of dictionaries containing node information

        Raises:
            Exception: If no control plane nodes are found
        """
        pxe_mapping = self.read_pxe_mapping_file()
        nodes = []

        # Parse PXE mapping file
        for line in pxe_mapping.strip().split('\n')[1:]:  # Skip header
            if not line.strip():
                continue

            parts = [p.strip() for p in line.split(',')]
            if len(parts) >= 6:  # Ensure we have enough parts
                node = {
                    'functional_group_name': parts[0],
                    'hostname': parts[4],
                    'admin_ip': parts[6] if len(parts) > 6 else None
                }
                nodes.append(node)

        # Filter control plane nodes
        control_plane_nodes = [
            node for node in nodes
            if 'service_kube_control_plane' in node.get('functional_group_name', '').lower()
        ]

        if not control_plane_nodes:
            raise ValueError(HA_NO_CONTROL_PLANE_NODES)

        return control_plane_nodes

    def is_virtual_ip_configured(self, node_ip, virtual_ip):
        """
        Check if the virtual IP is configured on a node.

        Args:
            node_ip (str): IP address of the node to check
            virtual_ip (str): Virtual IP to look for

        Returns:
            tuple: (bool, str) - (True if VIP is configured, output from ip command)
        """
        # Run a parse-friendly ip command on the node
        cmd = f"ssh -o StrictHostKeyChecking=no root@{node_ip} 'ip -4 -o addr show'"
        rc, ip_output, err = self._run_in_omnia_core(cmd)

        if rc != 0:
            raise RuntimeError(f"Failed to check IP on {node_ip}: {err}")

        vip = (virtual_ip or "").strip()
        has_vip = False
        for line in (ip_output or "").splitlines():
            parts = line.split()
            if "inet" not in parts:
                continue
            try:
                inet_idx = parts.index("inet")
            except ValueError:
                continue
            if inet_idx + 1 >= len(parts):
                continue
            addr_cidr = parts[inet_idx + 1]
            addr = addr_cidr.split("/", 1)[0]
            if addr == vip:
                has_vip = True
                break

        return has_vip, ip_output

    def verify_virtual_ip_configuration(self):
        """
        Verify that the virtual IP is configured on exactly one control plane node.

        Returns:
            tuple: (bool, str) - (True if test passed, status message)
        """
        try:
            # Get virtual IP from config
            virtual_ip = self.get_virtual_ip_from_config()

            # Get control plane nodes
            control_plane_nodes = self.get_control_plane_nodes()
            nodes_with_vip = []

            # Check each control plane node for the virtual IP
            for node in control_plane_nodes:
                node_ip = node.get('admin_ip')
                if not node_ip:
                    continue

                try:
                    has_vip, _ = self.is_virtual_ip_configured(node_ip, virtual_ip)
                    if has_vip:
                        nodes_with_vip.append(node)
                except Exception as e:
                    print(f"[WARNING] {str(e)}")

            # Verify exactly one control plane node has the virtual IP
            if len(nodes_with_vip) == 1:
                message = HA_VIP_CONFIGURED.format(
                    vip=virtual_ip,
                    node=nodes_with_vip[0].get('hostname')
                )
                return True, HA_VIP_CHECK_PASSED.format(message=message)

            if len(nodes_with_vip) > 1:
                node_names = [n.get('hostname', 'unknown') for n in nodes_with_vip]
                message = HA_VIP_MULTIPLE_NODES.format(
                    vip=virtual_ip,
                    nodes=", ".join(node_names)
                )
                return False, HA_VIP_CHECK_FAILED.format(message=message)

            message = HA_VIP_NOT_CONFIGURED.format(vip=virtual_ip)
            return False, HA_VIP_CHECK_FAILED.format(message=message)

        except Exception as e:
            return False, HA_VIP_CHECK_FAILED.format(message=str(e))

    def verify_vip_failover_scenario(self, max_wait_seconds: int = 60, poll_seconds: int = 5):
        try:
            virtual_ip = self.get_virtual_ip_from_config()
        except Exception as e:
            return None, str(e)

        try:
            control_plane_nodes = self.get_control_plane_nodes()
        except Exception as e:
            return None, str(e)

        if len(control_plane_nodes) < 2:
            return None, "Less than two control-plane nodes found in PXE mapping"

        nodes_with_vip = []
        for node in control_plane_nodes:
            node_ip = (node.get("admin_ip") or "").strip()
            if not node_ip:
                continue
            try:
                has_vip, _ = self.is_virtual_ip_configured(node_ip, virtual_ip)
            except Exception:
                has_vip = False
            if has_vip:
                nodes_with_vip.append(node)

        if len(nodes_with_vip) != 1:
            if len(nodes_with_vip) == 0:
                return False, HA_VIP_NOT_CONFIGURED.format(vip=virtual_ip)
            node_names = [n.get("hostname", "unknown") for n in nodes_with_vip]
            return False, HA_VIP_MULTIPLE_NODES.format(vip=virtual_ip, nodes=", ".join(node_names))

        vip_node = nodes_with_vip[0]
        vip_node_ip = (vip_node.get("admin_ip") or "").strip()
        if not vip_node_ip:
            return False, "VIP holder node has no admin_ip"

        remaining_nodes = [n for n in control_plane_nodes if (n.get("admin_ip") or "").strip() and (n.get("admin_ip") or "").strip() != vip_node_ip]
        if not remaining_nodes:
            return None, "No remaining control-plane nodes found for VIP failover verification"

        reboot_cmd = "nohup sh -c 'sleep 2; reboot' >/dev/null 2>&1 &"
        self._ssh_from_omnia_core(vip_node_ip, reboot_cmd)

        start = time.time()
        last_state = ""

        while time.time() - start < float(max_wait_seconds):
            new_vip_holders = []
            unreachable = []

            for node in remaining_nodes:
                node_ip = (node.get("admin_ip") or "").strip()
                try:
                    has_vip, _ = self.is_virtual_ip_configured(node_ip, virtual_ip)
                    if has_vip:
                        new_vip_holders.append(node)
                except Exception:
                    unreachable.append(node_ip)

            if len(new_vip_holders) == 1:
                new_holder = new_vip_holders[0]
                new_holder_ip = (new_holder.get("admin_ip") or "").strip()
                return True, (
                    f"VIP failover passed: VIP {virtual_ip} moved from {vip_node.get('hostname') or vip_node_ip} "
                    f"to {new_holder.get('hostname') or new_holder_ip} within {max_wait_seconds}s"
                )

            if len(new_vip_holders) > 1:
                holder_names = [h.get("hostname") or (h.get("admin_ip") or "unknown") for h in new_vip_holders]
                return False, f"VIP failover failed: VIP {virtual_ip} found on multiple nodes after reboot: {', '.join(holder_names)}"

            last_state = f"vip_holders=0 unreachable={','.join(unreachable) if unreachable else 'none'}"
            time.sleep(int(poll_seconds))

        return False, (
            f"VIP failover failed: VIP {virtual_ip} did not appear on any remaining control-plane node within {max_wait_seconds}s "
            f"(last_state={last_state})"
        )

    def get_control_plane_nodes_from_pxe_mapping(self):
        pxe_mapping = self.read_pxe_mapping_file()
        reader = csv.DictReader(io.StringIO(pxe_mapping))
        nodes = []
        for row in reader:
            if (row.get("FUNCTIONAL_GROUP_NAME") or "").strip() in [CONTROL_PLANE_GROUP, "service_kube_control_plane_x86_64"]:
                hostname = (row.get("HOSTNAME") or "").strip()
                admin_ip = (row.get("ADMIN_IP") or "").strip()
                if hostname or admin_ip:
                    nodes.append({"hostname": hostname, "admin_ip": admin_ip})
        return nodes

    def get_control_plane_admin_ips_from_pxe_mapping(self):
        control_planes = self.get_control_plane_nodes_from_pxe_mapping()
        admin_ips = []
        for node in control_planes:
            ip = (node.get("admin_ip") or "").strip()
            if ip:
                admin_ips.append(ip)
        return admin_ips

    def get_worker_nodes_from_pxe_mapping(self):
        pxe_mapping = self.read_pxe_mapping_file()
        reader = csv.DictReader(io.StringIO(pxe_mapping))
        nodes = []
        for row in reader:
            if (row.get("FUNCTIONAL_GROUP_NAME") or "").strip() in [WORKER_NODE_GROUP, "service_kube_node_x86_64"]:
                hostname = (row.get("HOSTNAME") or "").strip()
                admin_ip = (row.get("ADMIN_IP") or "").strip()
                if hostname or admin_ip:
                    nodes.append({"hostname": hostname, "admin_ip": admin_ip})
        return nodes

    def verify_control_plane_reboot_scenario(self, max_wait_seconds: int = 600, poll_seconds: int = 10):
        control_planes = self.get_control_plane_nodes_from_pxe_mapping()
        if len(control_planes) < 2:
            return None, "Less than two control-plane nodes found in PXE mapping"

        reboot_node = control_planes[0]
        watcher_node = control_planes[1]

        reboot_host = (reboot_node.get("hostname") or reboot_node.get("admin_ip") or "").strip()
        watcher_host = (watcher_node.get("hostname") or watcher_node.get("admin_ip") or "").strip()

        if not reboot_host or not watcher_host:
            return False, "Control-plane nodes are missing hostname/admin_ip in PXE mapping"

        reboot_identity_candidates = []
        if reboot_node.get("hostname"):
            reboot_identity_candidates.append(reboot_node.get("hostname"))
        if reboot_node.get("admin_ip"):
            reboot_identity_candidates.append(reboot_node.get("admin_ip"))

        def _kubectl_get_nodes():
            rc, out, err = self._ssh_from_omnia_core(watcher_host, "kubectl get nodes --no-headers")
            if rc != 0:
                return None, err or out
            return out, ""

        def _find_node_status(nodes_output: str):
            if not nodes_output:
                return None
            for line in nodes_output.splitlines():
                parts = line.split()
                if len(parts) < 2:
                    continue
                name = parts[0]
                status = parts[1]
                if any(c and (name == c) for c in reboot_identity_candidates):
                    return status
            for line in nodes_output.splitlines():
                for c in reboot_identity_candidates:
                    if c and c in line:
                        parts = line.split()
                        if len(parts) >= 2:
                            return parts[1]
            return None

        nodes_out, nodes_err = _kubectl_get_nodes()
        if nodes_out is None:
            return False, f"Failed to run kubectl from watcher control-plane {watcher_host}: {nodes_err}"

        initial_status = _find_node_status(nodes_out)
        if initial_status is None:
            return False, f"Reboot target node not found in 'kubectl get nodes' output (target={reboot_host})"

        if not initial_status.startswith("Ready"):
            return False, f"Reboot target node is not Ready before reboot (node={reboot_host}, status={initial_status})"

        reboot_cmd = "nohup sh -c 'sleep 2; reboot' >/dev/null 2>&1 &"
        self._ssh_from_omnia_core(reboot_host, reboot_cmd)

        start = time.time()
        observed_not_ready = False
        last_status = initial_status

        while time.time() - start < float(max_wait_seconds):
            nodes_out, nodes_err = _kubectl_get_nodes()
            if nodes_out is None:
                last_status = f"kubectl_error: {nodes_err}"
                time.sleep(int(poll_seconds))
                continue

            status = _find_node_status(nodes_out)
            if status is None:
                last_status = "NotFound"
                observed_not_ready = True
            else:
                last_status = status
                if not status.startswith("Ready"):
                    observed_not_ready = True
                if observed_not_ready and status.startswith("Ready"):
                    return True, f"Control-plane reboot scenario passed: {reboot_host} transitioned to NotReady/NotFound and returned to Ready within {max_wait_seconds}s"

            time.sleep(int(poll_seconds))

        if not observed_not_ready:
            return False, f"Control-plane reboot scenario failed: node {reboot_host} never became NotReady within {max_wait_seconds}s (last_status={last_status})"
        return False, f"Control-plane reboot scenario failed: node {reboot_host} did not return to Ready within {max_wait_seconds}s (last_status={last_status})"

    def verify_worker_node_reboot_scenario(self, max_wait_seconds: int = 600, poll_seconds: int = 10):
        control_planes = self.get_control_plane_nodes_from_pxe_mapping()
        workers = self.get_worker_nodes_from_pxe_mapping()
        if not control_planes:
            return None, "No control-plane nodes found in PXE mapping"
        if not workers:
            return None, "No worker nodes found in PXE mapping"

        reboot_node = workers[0]
        watcher_node = control_planes[0]

        reboot_host = (reboot_node.get("hostname") or reboot_node.get("admin_ip") or "").strip()
        watcher_host = (watcher_node.get("hostname") or watcher_node.get("admin_ip") or "").strip()

        if not reboot_host or not watcher_host:
            return False, "Worker/control-plane nodes are missing hostname/admin_ip in PXE mapping"

        reboot_identity_candidates = []
        if reboot_node.get("hostname"):
            reboot_identity_candidates.append(reboot_node.get("hostname"))
        if reboot_node.get("admin_ip"):
            reboot_identity_candidates.append(reboot_node.get("admin_ip"))

        def _kubectl_get_nodes():
            rc, out, err = self._ssh_from_omnia_core(watcher_host, "kubectl get nodes --no-headers")
            if rc != 0:
                return None, err or out
            return out, ""

        def _find_node_status(nodes_output: str):
            if not nodes_output:
                return None
            for line in nodes_output.splitlines():
                parts = line.split()
                if len(parts) < 2:
                    continue
                name = parts[0]
                status = parts[1]
                if any(c and (name == c) for c in reboot_identity_candidates):
                    return status
            for line in nodes_output.splitlines():
                for c in reboot_identity_candidates:
                    if c and c in line:
                        parts = line.split()
                        if len(parts) >= 2:
                            return parts[1]
            return None

        nodes_out, nodes_err = _kubectl_get_nodes()
        if nodes_out is None:
            return False, f"Failed to run kubectl from watcher control-plane {watcher_host}: {nodes_err}"

        initial_status = _find_node_status(nodes_out)
        if initial_status is None:
            return False, f"Worker reboot target not found in 'kubectl get nodes' output (target={reboot_host})"

        if not initial_status.startswith("Ready"):
            return False, f"Worker reboot target node is not Ready before reboot (node={reboot_host}, status={initial_status})"

        reboot_cmd = "nohup sh -c 'sleep 2; reboot' >/dev/null 2>&1 &"
        self._ssh_from_omnia_core(reboot_host, reboot_cmd)

        start = time.time()
        observed_not_ready = False
        last_status = initial_status

        while time.time() - start < float(max_wait_seconds):
            nodes_out, nodes_err = _kubectl_get_nodes()
            if nodes_out is None:
                last_status = f"kubectl_error: {nodes_err}"
                time.sleep(int(poll_seconds))
                continue

            status = _find_node_status(nodes_out)
            if status is None:
                last_status = "NotFound"
                observed_not_ready = True
            else:
                last_status = status
                if not status.startswith("Ready"):
                    observed_not_ready = True
                if observed_not_ready and status.startswith("Ready"):
                    return True, f"Worker reboot scenario passed: {reboot_host} transitioned to NotReady/NotFound and returned to Ready within {max_wait_seconds}s"

            time.sleep(int(poll_seconds))

        if not observed_not_ready:
            return False, f"Worker reboot scenario failed: node {reboot_host} never became NotReady within {max_wait_seconds}s (last_status={last_status})"
        return False, f"Worker reboot scenario failed: node {reboot_host} did not return to Ready within {max_wait_seconds}s (last_status={last_status})"

    def verify_etcd_cluster_health(self):
        control_planes = self.get_control_plane_nodes_from_pxe_mapping()
        if not control_planes:
            return False, "No control-plane nodes found in PXE mapping", ""

        admin_ips = self.get_control_plane_admin_ips_from_pxe_mapping()
        if not admin_ips:
            return False, "No control-plane admin IPs found in PXE mapping", ""

        watcher_host = (control_planes[0].get("hostname") or control_planes[0].get("admin_ip") or "").strip()
        if not watcher_host:
            return False, "Control-plane node missing hostname/admin_ip in PXE mapping", ""

        endpoints = ",".join([f"https://{ip}:2379" for ip in admin_ips])

        find_pod_inner = "kubectl get pods -n kube-system -o name | grep '^pod/etcd-' | head -n 1"
        find_pod_cmd = f"bash -lc {shlex.quote(find_pod_inner)}"
        rc, out, err = self._ssh_from_omnia_core(watcher_host, find_pod_cmd)
        etcd_pod = ((out or "").strip() or "").replace("pod/", "")
        if rc != 0 or not etcd_pod:
            return False, f"Failed to find etcd pod: {err or out}", (err or out or "")

        etcdctl_cmd = (
            "ETCDCTL_API=3 etcdctl "
            f"--endpoints={shlex.quote(endpoints)} "
            "--cacert=/etc/kubernetes/pki/etcd/ca.crt "
            "--cert=/etc/kubernetes/pki/etcd/server.crt "
            "--key=/etc/kubernetes/pki/etcd/server.key "
            "endpoint health"
        )
        exec_inner = (
            f"kubectl exec -n kube-system {shlex.quote(etcd_pod)} -- sh -lc {shlex.quote(etcdctl_cmd)}"
        )
        exec_cmd = f"bash -lc {shlex.quote(exec_inner)}"
        rc, out, err = self._ssh_from_omnia_core(watcher_host, exec_cmd)
        output = (out or "").strip() + ("\n" + (err or "").strip() if (err or "").strip() else "")

        if rc != 0:
            return False, f"etcdctl endpoint health command failed (rc={rc})", output

        health_lines = [line for line in (out or "").splitlines() if line.strip()]
        healthy_count = sum(1 for line in health_lines if "is healthy" in line.lower())
        expected_count = len(admin_ips)
        if healthy_count < expected_count:
            return False, f"Not all etcd endpoints are healthy (healthy={healthy_count}, expected={expected_count})", output

        return True, "All etcd endpoints are healthy", output

    def verify_container_runtime_via_crictl(self, expected_runtime, expected_version):
        """
        Verify that all nodes are using the expected container runtime and version.

        Args:
            expected_runtime (str): Expected container runtime (e.g., 'cri-o')
            expected_version (str): Expected container runtime version

        Returns:
            tuple: (bool, str) - (True if all nodes match, status message)
        """
        expected_runtime_str = f"{expected_runtime}://{expected_version}"
        all_passed = True
        results = []

        # Get all nodes from PXE mapping
        pxe_mapping = self.read_pxe_mapping_file()
        nodes = self.get_k8s_nodes_from_pxe(pxe_mapping)

        if not nodes:
            return False, "No nodes found in PXE mapping"

        # Check each node
        for node in nodes:
            node_name = node.get('hostname')
            node_ip = node.get('admin_ip')

            if not node_ip:
                continue

            try:
                # Get container runtime info from node
                cmd = f"ssh -o StrictHostKeyChecking=no root@{node_ip} 'crictl info | jq -r .config.containerd.runtime'"
                rc, runtime_info, err = self._run_in_omnia_core(cmd)

                if rc != 0:
                    error_msg = RUNTIME_CHECK_ERROR.format(node=node_name, error=err)
                    results.append((node_name, False, None, error_msg))
                    all_passed = False
                    continue

                runtime_info = runtime_info.strip()
                is_correct = (runtime_info == expected_runtime_str)

                if not is_correct:
                    error_msg = RUNTIME_MISMATCH.format(
                        expected=expected_runtime_str,
                        actual=runtime_info,
                        node=node_name
                    )
                    all_passed = False
                else:
                    error_msg = None

                results.append((node_name, is_correct, runtime_info, error_msg))

            except Exception as e:
                error_msg = RUNTIME_CHECK_ERROR.format(node=node_name, error=str(e))
                results.append((node_name, False, None, error_msg))
                all_passed = False

        # Generate summary message
        if all_passed:
            message = RUNTIME_CHECK_PASSED.format(runtime=expected_runtime_str)
        else:
            message = RUNTIME_CHECK_FAILED.format(runtime=expected_runtime_str)

        return all_passed, message, results

    def verify_pods_with_prefix(self, prefix, component_name):
        """
        Verify that all pods with the given prefix are in 'Running' state.

        Args:
            prefix (str): Pod name prefix to check
            component_name (str): Human-readable name of the component

        Returns:
            tuple: (bool, str) - (True if all pods are running, status message)
        """
        print(POD_CHECK_PREFIX.format(prefix=prefix))

        try:
            # Get control plane node
            pxe_mapping = self.read_pxe_mapping_file()
            nodes = self.get_k8s_nodes_from_pxe(pxe_mapping)
            control_plane = self._get_control_plane_node(nodes)
            control_plane_host = control_plane.get("hostname") or control_plane.get("admin_ip")

            if not control_plane_host:
                raise ValueError("No control plane node found")

            # Get all pods in JSON format
            cmd = "kubectl get pods --all-namespaces -o json"
            rc, out, err = self._ssh_from_omnia_core(control_plane_host, cmd)

            if rc != 0:
                raise RuntimeError(f"Failed to get pod information: {err}")

            # Process the output
            pod_statuses = []
            pods_data = json.loads(out)

            for item in pods_data.get('items', []):
                pod_name = item.get('metadata', {}).get('name', '')
                if pod_name.startswith(prefix):
                    deletion_timestamp = item.get('metadata', {}).get('deletionTimestamp')
                    phase = item.get('status', {}).get('phase', 'Unknown')
                    effective_status = 'Terminating' if deletion_timestamp else phase
                    pod_statuses.append({
                        'namespace': item.get('metadata', {}).get('namespace', ''),
                        'name': pod_name,
                        'node': item.get('spec', {}).get('nodeName', 'Unknown'),
                        'status': effective_status
                    })

            if not pod_statuses:
                message = POD_NOT_FOUND.format(prefix=prefix)
                return False, message

            # Check status of each pod
            failed_pods = []
            for pod in pod_statuses:
                status = "[PASS]" if pod['status'] == 'Running' else "[FAIL]"
                print(POD_STATUS.format(
                    status=status,
                    namespace=pod['namespace'],
                    name=pod['name'],
                    phase=pod['status'],
                    node=pod.get('node', 'Unknown')
                ))

                if pod['status'] != 'Running':
                    failed_pods.append(f"{pod['namespace']}/{pod['name']} (Status: {pod['status']})")

            # Generate result
            if not failed_pods:
                message = POD_CHECK_PASSED.format(component=component_name)
                print(message)
                return True, message

            message = POD_CHECK_FAILED.format(component=component_name)
            message += "\n" + "\n".join(failed_pods)
            print(message)
            return False, message

        except Exception as e:
            return False, f"Error checking pods: {str(e)}"

    def _get_omnia_core_container_id(self):
        """Get the container ID of the omnia_core container."""
        if self._omnia_core_container_id:
            return self._omnia_core_container_id

        get_container_cmd = f"podman ps --filter 'name={OMNIA_CORE_CONTAINER_NAME}' --format '{{{{.ID}}}}'"
        container_id = self._run_ssh_command(get_container_cmd)
        if not container_id:
            raise Exception(f"Container '{OMNIA_CORE_CONTAINER_NAME}' not found")
        self._omnia_core_container_id = container_id
        return container_id

    def _run_in_omnia_core(self, command, check=True):
        """Run a command inside the omnia_core container.

        Args:
            command (str): The command to run.
            check (bool): Whether to raise an exception if the command fails.

        Returns:
            tuple: (exit_code, stdout, stderr)
        """
        container_id = self._get_omnia_core_container_id()
        wrapped = f"podman exec {container_id} bash -lc {shlex.quote(command)}"

        if not self.ssh_client:
            self.connect_ssh()

        _stdin, stdout, stderr = self.ssh_client.exec_command(wrapped)
        exit_code = stdout.channel.recv_exit_status()
        out = stdout.read().decode('utf-8').strip()
        err = stderr.read().decode('utf-8').strip()

        if check and exit_code != 0:
            raise RuntimeError(f"Command failed with exit code {exit_code}: {err}")

        return exit_code, out, err

    def get_k8s_nodes_from_pxe(self, pxe_mapping):
        """Extract Kubernetes node information from PXE mapping.

        Args:
            pxe_mapping (str): The content of the pxe_mapping_file.

        Returns:
            list: List of dicts containing node information (hostname, admin_ip).
        """
        reader = csv.DictReader(io.StringIO(pxe_mapping))
        nodes = []
        wanted = {"service_kube_control_plane_x86_64", "service_kube_node_x86_64"}
        for row in reader:
            if (row.get("FUNCTIONAL_GROUP_NAME") or "").strip() in wanted:
                hostname = (row.get("HOSTNAME") or "").strip()
                admin_ip = (row.get("ADMIN_IP") or "").strip()
                if hostname or admin_ip:
                    nodes.append({"hostname": hostname, "admin_ip": admin_ip})
        return nodes

    def _ssh_from_omnia_core(self, host, remote_cmd):
        """Run a command on a remote host via SSH from the omnia_core container.

        Args:
            host (str): The target host to connect to.
            remote_cmd (str): The command to run on the remote host.

        Returns:
            tuple: (exit_code, stdout, stderr)
        """
        ssh_user = (self.config.get("node_ssh_user") or "root").strip()
        ssh_port = int(self.config.get("node_ssh_port") or 22)
        connect_timeout = int(self.config.get("node_ssh_timeout") or 10)
        ssh_cmd = (
            "ssh -o BatchMode=yes -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null "
            f"-o ConnectTimeout={connect_timeout} -p {ssh_port} "
            f"{ssh_user}@{host} {shlex.quote(remote_cmd)}"
        )
        return self._run_in_omnia_core(ssh_cmd, check=False)

    def check_k8s_nodes_ready(self, control_plane_node):
        """Check if all Kubernetes nodes are in Ready state.

        Args:
            control_plane_node (dict): Control plane node information with 'hostname' and 'admin_ip'.

        Returns:
            tuple: (all_ready, output, error, unreachable)
                - all_ready (bool): True if all nodes are Ready, False otherwise
                - output (str): Command output
                - error (str): Error message if any
                - unreachable (bool): True if the control plane node is unreachable
        """
        hostname = (control_plane_node.get("hostname") or "").strip()
        admin_ip = (control_plane_node.get("admin_ip") or "").strip()

        if not (hostname or admin_ip):
            return False, "", "No hostname or admin_ip provided for control plane node", True

        target = hostname or admin_ip

        try:
            # Run 'kubectl get nodes' on the control plane node
            cmd = "kubectl get nodes --no-headers"
            rc, out, err = self._ssh_from_omnia_core(target, cmd)

            if rc != 0:
                return False, out, err, False

            # Parse the output to check node status
            lines = [line.strip() for line in out.split('\n') if line.strip()]
            if not lines:
                return False, out, "No nodes found in the cluster", False

            all_ready = True
            for line in lines:
                parts = line.split()
                if len(parts) < 2:
                    continue
                status = parts[1]
                if status != "Ready":
                    all_ready = False
                    break

            return all_ready, out, "", False

        except Exception as e:
            return False, "", str(e), True

    def is_service_active_on_node(self, node, service_name):
        """Check if a service is active on a node.

        Args:
            node (dict): Node information with 'hostname' and 'admin_ip'.
            service_name (str): Name of the service to check.

        Returns:
            tuple: (is_active, target_used, stdout, stderr, is_unreachable)
        """
        hostname = (node.get("hostname") or "").strip()
        admin_ip = (node.get("admin_ip") or "").strip()

        def _is_unreachable_error(error):
            e = (error or "").lower()
            patterns = [
                "no route to host",
                "network is unreachable",
                "connection timed out",
                "could not resolve",
                "name or service not known",
                "temporary failure in name resolution",
                "connection refused",
            ]
            return any(p in e for p in patterns)

        candidates = []
        if hostname:
            candidates.append(hostname)
        if admin_ip and admin_ip != hostname:
            candidates.append(admin_ip)

        if not candidates:
            return False, "", "", "no hostname or admin_ip provided", True

        last_host = candidates[-1]
        last_out = ""
        last_err = ""
        for host in candidates:
            rc, out, err = self._ssh_from_omnia_core(host, f"systemctl is-active {service_name}")
            last_host, last_out, last_err = host, out, err

            if rc == 0:
                return out.strip() == "active", host, out, err, False

            if _is_unreachable_error(err):
                continue

            return False, host, out, err, False

        return False, last_host, last_out, last_err, True

    def verify_service_on_nodes(self, service_name, service_display_name=None):
        """Verify a service is active on all reachable Kubernetes nodes.

        Args:
            service_name: Name of the service to check
            service_display_name: Display name for the service in output messages

        Returns:
            list: List of error messages for nodes where the service is not active
        """
        service_display_name = service_display_name or service_name
        pxe_mapping = self.read_pxe_mapping_file()
        nodes = self.get_k8s_nodes_from_pxe(pxe_mapping)

        if not nodes:
            raise ValueError("No nodes found in PXE mapping file")

        failures = []
        reachable = 0

        print(f"\n{service_display_name.upper()} STATUS:")

        for node in nodes:
            hostname = node.get("hostname") or node.get("admin_ip") or "<unknown>"

            # Check the service on the node
            is_active, target, out, err, unreachable = self.is_service_active_on_node(node, service_name)

            if unreachable:
                print(f"{hostname}: SKIPPED (unreachable via {target})")
                continue

            reachable += 1

            if is_active:
                print(f"{hostname}: PASSED (target={target})")
            else:
                print(f"{hostname}: FAILED (target={target}, service not active)")
                failures.append(f"{hostname}: {service_display_name} is not active (target={target}, out={out!r}, err={err!r})")

        if reachable == 0:
            raise Exception("All nodes are unreachable")

        return failures

    def verify_kubelet_active_on_nodes(self):
        failures = self.verify_service_on_nodes(KUBELET_SERVICE, "kubelet")
        if failures:
            return False, "\n".join(failures), failures
        return True, "kubelet is active on all reachable Kubernetes nodes", []

    def verify_crio_or_cri_o_active_on_nodes(self):
        pxe_mapping = self.read_pxe_mapping_file()
        nodes = self.get_k8s_nodes_from_pxe(pxe_mapping)

        if not nodes:
            raise ValueError("No nodes found in PXE mapping file")

        failures = []
        reachable = 0

        print("\nCONTAINER RUNTIME SERVICE STATUS:")

        for node in nodes:
            hostname = node.get("hostname") or node.get("admin_ip") or "<unknown>"

            crio_active, crio_target, crio_out, crio_err, crio_unreachable = self.is_service_active_on_node(node, CRIO_SERVICE)
            crio_o_active, crio_o_target, crio_o_out, crio_o_err, crio_o_unreachable = self.is_service_active_on_node(node, CRI_O_SERVICE)

            if crio_unreachable and crio_o_unreachable:
                target = crio_target or crio_o_target
                print(f"{hostname}: SKIPPED (unreachable via {target})")
                continue

            reachable += 1

            if crio_active or crio_o_active:
                active_service = "crio" if crio_active else "cri-o"
                target = crio_target if crio_active else crio_o_target
                print(f"{hostname}: PASSED (target={target}, service={active_service})")
                continue

            target = crio_target or crio_o_target
            print(f"{hostname}: FAILED (target={target}, service not active)")
            failures.append(
                f"{hostname}: crio/cri-o is not active (target={target}, crio_out={crio_out!r}, crio_err={crio_err!r}, cri_o_out={crio_o_out!r}, cri_o_err={crio_o_err!r})"
            )

        if reachable == 0:
            raise Exception("All nodes are unreachable")

        if failures:
            return False, "\n".join(failures), failures

        return True, "crio/cri-o is active on all reachable Kubernetes nodes", []

    def verify_nodes_joined_cluster(self):
        """Verify all expected nodes have joined the cluster.

        Returns:
            list: List of error messages for missing nodes
        """
        pxe_mapping = self.read_pxe_mapping_file()
        expected_nodes = self.get_k8s_nodes_from_pxe(pxe_mapping)

        if not expected_nodes:
            raise ValueError("No nodes found in PXE mapping file")

        control_plane_node = self._get_control_plane_node(expected_nodes)
        node_name = control_plane_node.get("hostname") or control_plane_node.get("admin_ip") or "unknown"

        print(f"\nVerifying nodes have joined the cluster from control plane: {node_name}")

        # Get actual cluster nodes
        _all_ready, output, error, unreachable = self.check_k8s_nodes_ready(control_plane_node)

        if unreachable:
            raise Exception(f"Control plane node {node_name} is unreachable: {error}")
        if error:
            raise Exception(f"Error checking node status: {error}")

        # Parse the kubectl output to get actual nodes
        actual_nodes = set()
        for line in output.strip().split('\n'):
            parts = line.split()
            if parts:  # Skip empty lines
                actual_nodes.add(parts[0])  # Node IP is the first column

        # Verify all expected nodes are in the cluster
        missing_nodes = []
        for expected in expected_nodes:
            node_ip = expected.get("admin_ip")
            node_name = expected.get("hostname", "unknown")

            found = any(
                (node_ip and node_ip in actual) or
                (node_name and node_name in actual)
                for actual in actual_nodes
            )

            if not found:
                missing_nodes.append(f"- {node_name} ({node_ip or 'no IP'})")

        # Print status for debugging
        print("\n" + "="*50)
        print("Cluster Node Membership:")
        print("="*50)
        print("\nExpected nodes from PXE mapping:")
        for node in expected_nodes:
            print(f"- {node.get('hostname', 'N/A')} ({node.get('admin_ip', 'no IP')})")

        print("\nActual nodes in cluster:")
        for node in actual_nodes:
            print(f"- {node}")

        print("\n" + "="*50)

        return missing_nodes

    def verify_nodes_joined_cluster_check(self):
        missing_nodes = self.verify_nodes_joined_cluster()
        if missing_nodes:
            return False, "Some nodes from PXE mapping are not in the cluster:\n" + "\n".join(missing_nodes), missing_nodes
        return True, "All nodes from PXE mapping have joined the Kubernetes cluster", []

    def verify_nodes_ready_state(self):
        """Verify all nodes in the cluster are in Ready state.

        Returns:
            list: List of error messages for nodes not in Ready state
        """
        pxe_mapping = self.read_pxe_mapping_file()
        expected_nodes = self.get_k8s_nodes_from_pxe(pxe_mapping)

        if not expected_nodes:
            raise ValueError("No nodes found in PXE mapping file")

        control_plane_node = self._get_control_plane_node(expected_nodes)
        node_name = control_plane_node.get("hostname") or control_plane_node.get("admin_ip") or "unknown"

        print(f"\nVerifying node status from control plane: {node_name}")

        # Get actual cluster nodes and their statuses
        _all_ready, output, error, unreachable = self.check_k8s_nodes_ready(control_plane_node)

        if unreachable:
            raise Exception(f"Control plane node {node_name} is unreachable: {error}")
        if error:
            raise Exception(f"Error checking node status: {error}")

        # Parse the kubectl output to get node statuses
        node_statuses = []
        for line in output.strip().split('\n'):
            parts = line.split()
            if parts:  # Skip empty lines
                node_ip = parts[0]
                status = parts[1] if len(parts) > 1 else "Unknown"
                node_statuses.append((node_ip, status))

        # Print status for debugging
        print("\n" + "="*50)
        print("Node Status Summary:")
        print("="*50)
        print("\nNodes in cluster and their status:")
        for ip, status in node_statuses:
            status_display = f"{status} {'✅' if status == 'Ready' else '❌'}"
            print(f"- {ip}: {status_display}")

        print("\n" + "="*50)

        # Return nodes that are not in Ready state
        return [f"- {ip}: {status}" for ip, status in node_statuses if status != "Ready"]

    def verify_nodes_ready_state_wait(self, timeout_seconds):
        pxe_mapping = self.read_pxe_mapping_file()
        expected_nodes = self.get_k8s_nodes_from_pxe(pxe_mapping)

        if not expected_nodes:
            raise ValueError("No nodes found in PXE mapping file")

        control_plane_node = self._get_control_plane_node(expected_nodes)
        node_name = control_plane_node.get("hostname") or control_plane_node.get("admin_ip") or "unknown"

        print(f"\nVerifying node status from control plane: {node_name}")

        inner = (
            f"kubectl wait --for=condition=Ready nodes --all --timeout={int(timeout_seconds)}s "
            f">/dev/null 2>&1; kubectl get nodes --no-headers"
        )
        remote_cmd = f"bash -lc {shlex.quote(inner)}"
        rc, out, err = self._ssh_from_omnia_core(node_name, remote_cmd)

        if rc != 0 and not out:
            raise Exception(f"Error checking node status: {err}")

        node_statuses = []
        for line in (out or "").strip().split('\n'):
            parts = line.split()
            if parts:
                node_ip = parts[0]
                status = parts[1] if len(parts) > 1 else "Unknown"
                node_statuses.append((node_ip, status))

        print("\n" + "="*50)
        print("Node Status Summary:")
        print("="*50)
        print("\nNodes in cluster and their status:")
        for ip, status in node_statuses:
            status_display = f"{status} {'✅' if status == 'Ready' else '❌'}"
            print(f"- {ip}: {status_display}")
        print("\n" + "="*50)

        not_ready = [f"- {ip}: {status}" for ip, status in node_statuses if status != "Ready"]
        if not_ready:
            return False, "Not all Kubernetes nodes are in Ready state:\n" + "\n".join(not_ready), not_ready
        return True, "All Kubernetes nodes are in Ready state", []

    def verify_nodes_ready_state_with_retry(self, max_retries=None, delay_seconds=None):
        max_retries = READY_STATE_MAX_RETRIES if max_retries is None else int(max_retries)
        delay_seconds = READY_STATE_RETRY_DELAY_SECONDS if delay_seconds is None else int(delay_seconds)

        timeout_seconds = max_retries * delay_seconds
        return self.verify_nodes_ready_state_wait(timeout_seconds)

    def _get_control_plane_node(self, nodes):
        """Get a control plane node from the list of nodes.

        Args:
            nodes: List of node dictionaries

        Returns:
            dict: The first control plane node found, or the first node if none found
        """
        control_plane_nodes = [
            node for node in nodes
            if any(k in (node.get("hostname") or "").lower()
                   for k in ["master", "control", "kcp"])
        ]
        return control_plane_nodes[0] if control_plane_nodes else nodes[0]

    def verify_kubectl_version(self, expected_version, node=None):
        """Verify kubectl client version matches the expected version.

        Args:
            expected_version (str): Expected kubectl version (e.g., "1.34.1")
            node (dict, optional): Node to check. If None, will use the first control plane node.

        Returns:
            tuple: (bool, str) - (True if version matches, version string)

        Raises:
            Exception: If kubectl command fails
        """
        hostname = "<unknown>"
        try:
            # If no node is provided, get the first control plane node
            if node is None:
                pxe_mapping = self.read_pxe_mapping_file()
                nodes = self.get_k8s_nodes_from_pxe(pxe_mapping)
                if not nodes:
                    raise RuntimeError("No nodes found in PXE mapping")
                node = self._get_control_plane_node(nodes)

            # Get node hostname or IP
            hostname = node.get("hostname") or node.get("admin_ip")
            if not hostname:
                raise RuntimeError("Node has no hostname or IP address")

            # Command to get kubectl version in plain text
            cmd = "kubectl version --client"

            # Run the command on the node via SSH from omnia_core
            rc, out, err = self._ssh_from_omnia_core(hostname, cmd)

            if rc != 0:
                raise RuntimeError(f"Failed to get kubectl version on {hostname}: {err}")

            # Extract version from the output
            # Expected format: "Client Version: v1.34.1"
            version_line = next((line for line in out.split('\n') if line.startswith('Client Version:')), None)
            if not version_line:
                raise RuntimeError(f"Could not find version in kubectl output: {out}")

            # Extract version number (e.g., "1.34.1" from "Client Version: v1.34.1")
            version_match = re.search(r'v?(\d+\.\d+\.\d+)', version_line)
            if not version_match:
                raise RuntimeError(f"Could not parse version from: {version_line}")

            version_str = version_match.group(1)

            # Check if the version matches the expected version
            return version_str == expected_version, version_str

        except Exception as e:
            raise RuntimeError(f"Error verifying kubectl version on {hostname}: {str(e)}") from e

    def verify_container_runtime(self, expected_runtime="cri-o", expected_version=None):
        """Verify that all nodes are using the expected container runtime and version.

        Args:
            expected_runtime (str): Expected container runtime (default: "cri-o")
            expected_version (str, optional): Expected container runtime version (e.g., "1.34.1")

        Yields:
            tuple: (node_name, is_correct, actual_runtime, error) for each node
                  where is_correct is True only if both runtime and version match
        """
        try:
            # Get the control plane node to run kubectl commands
            pxe_mapping = self.read_pxe_mapping_file()
            nodes = self.get_k8s_nodes_from_pxe(pxe_mapping)
            if not nodes:
                raise ValueError("No nodes found in PXE mapping")

            control_plane = self._get_control_plane_node(nodes)
            control_plane_host = control_plane.get("hostname") or control_plane.get("admin_ip")

            if not control_plane_host:
                raise ValueError("Control plane node has no hostname or IP address")

            # Run kubectl get nodes -o wide on the control plane
            cmd = "kubectl get nodes -o wide"
            rc, out, err = self._ssh_from_omnia_core(control_plane_host, cmd)

            if rc != 0:
                raise Exception(f"Failed to get node information: {err}")

            # Split the output into lines
            lines = [line for line in out.strip().split('\n') if line.strip()]
            if len(lines) < 2:  # Header + at least one node
                raise Exception("No nodes found in cluster")

            # Process each node line
            for line in lines[1:]:  # Skip header line
                if not line.strip():
                    continue

                # Split the line into parts, handling the fact that some columns might contain spaces
                # We'll split on whitespace but need to handle the ROLES column which might contain spaces
                parts = line.split()

                # The NAME is the first column, and CONTAINER-RUNTIME is the last
                node_name = parts[0]  # First column is always the node name
                runtime = parts[-1]   # Last column is always the container runtime

                # The expected runtime string is in the format "cri-o://1.34.1"
                expected_runtime_str = (
                    f"{expected_runtime}://{expected_version}"
                    if expected_version
                    else f"{expected_runtime}://"
                )

                # Check if the actual runtime matches exactly
                if expected_version:
                    is_correct = runtime == expected_runtime_str
                else:
                    is_correct = runtime.startswith(expected_runtime_str)

                yield node_name, is_correct, runtime, None

        except Exception as e:
            # If we can't get the full list, yield an error for each node we know about
            for node in nodes:
                node_name = node.get("hostname") or node.get("admin_ip") or "unknown"
                yield node_name, False, None, str(e)

    def verify_kubectl_version_on_control_planes_check(self, expected_version):
        results = list(self.verify_kubectl_version_on_control_planes(expected_version))
        all_passed = True
        failures = []
        for node_name, is_correct, actual_version, error in results:
            if error:
                all_passed = False
                failures.append(f"{node_name}: {error}")
            elif not is_correct:
                all_passed = False
                failures.append(
                    f"{node_name}: expected {expected_version}, got {actual_version}"
                )

        if all_passed:
            return True, f"kubectl client version matches expected version {expected_version} on all control planes", results
        return False, "\n".join(failures) if failures else "kubectl version check failed", results

    def verify_all_nodes_container_runtime(self, expected_runtime="cri-o", expected_version=None):
        """Verify that all nodes are using the expected container runtime and version.

        Args:
            expected_runtime (str): Expected container runtime (default: "cri-o")
            expected_version (str, optional): Expected container runtime version (e.g., "1.34.1")

        Returns:
            tuple: (all_passed, results)
                - all_passed (bool): True if all nodes passed the check
                - results (list): List of tuples with (node_name, is_correct, actual_runtime, error)
        """
        results_gen = self.verify_container_runtime(
            expected_runtime=expected_runtime,
            expected_version=expected_version
        )

        all_passed = True
        results = []

        print(RUNTIME_CHECK_HEADER)
        print(EXPECTED_RUNTIME_MSG.format(runtime=expected_runtime, version=expected_version or 'any'))

        for node_name, is_correct, actual_runtime, error in results_gen:
            results.append((node_name, is_correct, actual_runtime, error))

            if error:
                print(RUNTIME_CHECK_NODE_ERROR.format(node=node_name, error=error))
            elif is_correct:
                print(RUNTIME_CHECK_NODE_PASS.format(node=node_name, runtime=actual_runtime))
            else:
                expected = f"{expected_runtime}://{expected_version}" if expected_version else expected_runtime
                print(RUNTIME_CHECK_NODE_FAIL.format(
                    node=node_name,
                    expected=expected,
                    actual=actual_runtime
                ))

            if not is_correct:
                all_passed = False

        if not results:
            print(RUNTIME_CHECK_NO_NODES)
            return False, []

        # Print summary
        if all_passed:
            print(RUNTIME_CHECK_ALL_PASSED)
        else:
            print(RUNTIME_CHECK_SOME_FAILED)

        return all_passed, results

    def verify_kubectl_version_on_control_planes(self, expected_version):
        """Verify kubectl version on all control plane nodes.

        Args:
            expected_version (str): Expected kubectl version (e.g., "1.34.1")

        Yields:
            tuple: (node_name, is_correct, actual_version, error) for each control plane node
        """
        # Get all nodes
        pxe_mapping = self.read_pxe_mapping_file()
        nodes = self.get_k8s_nodes_from_pxe(pxe_mapping)

        if not nodes:
            raise ValueError(ERROR_NO_NODES_FOUND)

        # Get control plane nodes
        control_plane_nodes = [
            node for node in nodes
            if any(k in (node.get("hostname") or "").lower()
                for k in ["master", "control", "kcp"])
        ]

        if not control_plane_nodes:
            raise ValueError(ERROR_NO_CONTROL_PLANE_NODES)

        # Test on each control plane node
        for node in control_plane_nodes:
            node_name = node.get("hostname") or node.get("admin_ip") or "unknown"

            try:
                is_correct, actual_version = self.verify_kubectl_version(
                    expected_version,
                    node=node
                )
                yield node_name, is_correct, actual_version, None
            except Exception as e:
                yield node_name, False, None, str(e)

    def verify_metallb_pods(self):
        """Verify that all pods in the metallb-system namespace are running.

        Returns:
            tuple: (success, message, results)
                - success (bool): True if all pods are running, False otherwise
                - message (str): Status message
                - results (list): List of pod status dictionaries
        """
        try:
            # Get control plane node
            pxe_mapping = self.read_pxe_mapping_file()
            nodes = self.get_k8s_nodes_from_pxe(pxe_mapping)
            control_plane = self._get_control_plane_node(nodes)
            control_plane_host = control_plane.get("hostname") or control_plane.get("admin_ip")

            # Get all pods in metallb-system namespace
            cmd = "kubectl get pods -n metallb-system -o json"
            rc, out, err = self._ssh_from_omnia_core(control_plane_host, cmd)

            if rc != 0:
                if "namespaces \"metallb-system\" not found" in err:
                    return False, "metallb-system namespace not found. Is MetalLB installed?", []
                return False, f"Failed to get pod information: {err}", []

            # Process the output
            pod_statuses = []
            try:
                pods_data = json.loads(out)
                for item in pods_data.get('items', []):
                    deletion_timestamp = item.get('metadata', {}).get('deletionTimestamp')
                    phase = item.get('status', {}).get('phase', 'Unknown')
                    effective_status = 'Terminating' if deletion_timestamp else phase
                    pod_statuses.append({
                        'name': item.get('metadata', {}).get('name', ''),
                        'namespace': item.get('metadata', {}).get('namespace', ''),
                        'status': effective_status,
                        'node': item.get('spec', {}).get('nodeName', 'Unknown')
                    })
            except json.JSONDecodeError as e:
                return False, f"Failed to parse pod information: {e}", []

            # Check if any pods were found
            if not pod_statuses:
                return False, "No pods found in the metallb-system namespace. Is MetalLB installed?", []

            # Check status of each pod
            failed_pods = [
                f"{pod['name']} (Status: {pod['status']})"
                for pod in pod_statuses
                if pod['status'] != 'Running'
            ]

            success = not bool(failed_pods)
            message = (
                "All MetalLB pods are running" if success
                else f"Some MetalLB pods are not running: {', '.join(failed_pods)}"
            )

            return success, message, pod_statuses

        except Exception as e:
            return False, f"Error verifying MetalLB pods: {str(e)}", []

    def verify_nfs_provisioner_pod(self):
        """Verify that the nfs-client-nfs-subdir-external-provisioner pod is running.

        Returns:
            tuple: (success, message, pod_info)
                - success (bool): True if pod is found and running, False otherwise
                - message (str): Status message
                - pod_info (dict): Pod information if found, empty dict otherwise
        """
        try:
            # Get control plane node
            pxe_mapping = self.read_pxe_mapping_file()
            nodes = self.get_k8s_nodes_from_pxe(pxe_mapping)
            control_plane = self._get_control_plane_node(nodes)
            control_plane_host = control_plane.get("hostname") or control_plane.get("admin_ip")

            # Get all pods in all namespaces to find the NFS provisioner pod
            cmd = "kubectl get pods --all-namespaces -o json"
            rc, out, err = self._ssh_from_omnia_core(control_plane_host, cmd)

            if rc != 0:
                return False, f"Failed to get pod information: {err}", {}

            # Process the output
            pod_info = {}
            try:
                pods_data = json.loads(out)
                for item in pods_data.get('items', []):
                    pod_name = item.get('metadata', {}).get('name', '')
                    if pod_name.startswith('nfs-client-nfs-subdir-external-provisioner'):
                        deletion_timestamp = item.get('metadata', {}).get('deletionTimestamp')
                        phase = item.get('status', {}).get('phase', 'Unknown')
                        effective_status = 'Terminating' if deletion_timestamp else phase
                        pod_info = {
                            'name': pod_name,
                            'namespace': item.get('metadata', {}).get('namespace', 'default'),
                            'status': effective_status,
                            'node': item.get('spec', {}).get('nodeName', 'Unknown'),
                            'creation_timestamp': item.get('metadata', {}).get('creationTimestamp')
                        }
                        break
            except json.JSONDecodeError as e:
                return False, f"Failed to parse pod information: {e}", {}

            if not pod_info:
                return False, "NFS client provisioner pod not found. Is the NFS subdir external provisioner installed?", {}

            success = pod_info.get('status') == 'Running'
            message = (
                "NFS client provisioner pod is running" if success
                else f"NFS client provisioner pod is not running. Current status: {pod_info.get('status')}"
            )

            return success, message, pod_info

        except Exception as e:
            return False, f"Error verifying NFS provisioner pod: {str(e)}", {}

    def verify_file_exists(self, file_path):
        """Check if a file exists in the omnia_core container.

        Args:
            file_path (str): Path to the file to check

        Returns:
            tuple: (bool, str, dict) - (True if file exists, status message, file info)
        """
        try:
            # Check if file exists using _run_in_omnia_core
            cmd = f"[ -f {file_path} ] && echo 'File exists' || echo 'File not found'"
            rc, out, err = self._run_in_omnia_core(cmd)

            if "File exists" in out:
                # Get file details
                cmd = f"ls -la {file_path} && echo '---CONTENTS---' && cat {file_path}"
                rc, out, err = self._run_in_omnia_core(cmd)

                # Parse the output
                if rc == 0 and '---CONTENTS---' in out:
                    ls_output, _, contents = out.partition('---CONTENTS---')
                    ls_parts = ls_output.strip().split()

                    if len(ls_parts) >= 8:
                        file_info = {
                            'path': file_path,
                            'exists': True,
                            'mode': ls_parts[0],
                            'owner': ls_parts[2],
                            'group': ls_parts[3],
                            'size': int(ls_parts[4]),
                            'mtime': ' '.join(ls_parts[5:8]),
                            'contents': contents.strip()
                        }
                        return True, f"File {file_path} exists in omnia_core container", file_info

                # If we couldn't parse all details, return basic info
                file_info = {
                    'path': file_path,
                    'exists': True,
                    'contents': out
                }
                return True, f"File {file_path} exists in omnia_core container", file_info

            # File doesn't exist, check if directory exists
            dir_path = os.path.dirname(file_path)
            rc, out, err = self._run_in_omnia_core(
                f"[ -d {dir_path} ] && echo 'Directory exists' || echo 'Directory not found'"
            )

            dir_info = {
                'path': dir_path,
                'exists': "Directory exists" in out
            }

            if dir_info['exists']:
                # Get directory listing
                rc, ls_out, err = self._run_in_omnia_core(f"ls -la {dir_path}")
                dir_info['contents'] = ls_out if rc == 0 else f"Error getting directory contents: {err}"

            return False, f"File {file_path} not found in omnia_core container", {'directory_info': dir_info}

        except Exception as e:
            return False, f"Error checking file: {str(e)}", {}

    def verify_default_storage_class(self, storage_class_name="ps01"):
        """Verify that the specified storage class exists and is set as default.

        Args:
            storage_class_name (str): Name of the storage class to check

        Returns:
            tuple: (bool, str) - (True if storage class exists and is default, status message)
        """
        try:
            # Get the control plane node to run kubectl commands
            pxe_mapping = self.read_pxe_mapping_file()
            nodes = self.get_k8s_nodes_from_pxe(pxe_mapping)
            if not nodes:
                return False, "No nodes found in PXE mapping"

            control_plane = self._get_control_plane_node(nodes)
            control_plane_host = control_plane.get("hostname") or control_plane.get("admin_ip")

            if not control_plane_host:
                return False, "Control plane node has no hostname or IP address"

            # Run kubectl get sc with output in JSON format
            cmd = "kubectl get sc -o json"
            rc, out, err = self._ssh_from_omnia_core(control_plane_host, cmd)

            if rc != 0:
                return False, f"Failed to get storage classes: {err}"

            try:
                sc_data = json.loads(out)
                if 'items' not in sc_data:
                    return False, "No storage classes found"

                # Look for the specified storage class and check if it's default
                target_sc = None
                for sc in sc_data['items']:
                    if sc['metadata']['name'] == storage_class_name:
                        target_sc = sc
                        break

                if not target_sc:
                    return False, f"Storage class '{storage_class_name}' not found"

                # Check if it's the default storage class
                is_default = False
                annotations = target_sc['metadata'].get('annotations', {})
                if annotations.get('storageclass.kubernetes.io/is-default-class') == 'true' or \
                   annotations.get('storageclass.beta.kubernetes.io/is-default-class') == 'true':
                    is_default = True

                if is_default:
                    return True, f"Storage class '{storage_class_name}' exists and is set as default"
                return False, f"Storage class '{storage_class_name}' exists but is not set as default"

            except json.JSONDecodeError as e:
                return False, f"Failed to parse storage class information: {str(e)}"

        except Exception as e:
            return False, f"Error verifying storage class: {str(e)}"

    def verify_pvc_pv_bound_and_pod_running(
        self,
        manifest_yaml: str,
        pvc_name: str,
        deployment_name: str,
        pod_selector: str,
        namespace: str = "default",
        timeout_seconds: int = 300,
        cleanup: bool = True,
    ):
        pxe_mapping = self.read_pxe_mapping_file()
        nodes = self.get_k8s_nodes_from_pxe(pxe_mapping)
        if not nodes:
            return False, "No nodes found in PXE mapping"

        control_plane = self._get_control_plane_node(nodes)
        control_plane_host = control_plane.get("hostname") or control_plane.get("admin_ip")
        if not control_plane_host:
            return False, "Control plane node has no hostname or IP address"

        pv_name = ""
        outputs = []

        def _run(remote_cmd: str):
            rc, out, err = self._ssh_from_omnia_core(control_plane_host, remote_cmd)
            return rc, (out or "").strip(), (err or "").strip()

        def _apply_or_delete(action: str):
            if action not in {"apply", "delete"}:
                raise ValueError("Invalid action")

            extra = ""
            if action == "delete":
                extra = " --ignore-not-found=true"

            inner = (
                f"kubectl {action} -n {shlex.quote(namespace)} -f -{extra} <<'EOF'\n"
                f"{manifest_yaml.rstrip()}\n"
                "EOF\n"
            )
            remote_cmd = f"bash -lc {shlex.quote(inner)}"
            return _run(remote_cmd)

        try:
            rc, out, err = _apply_or_delete("apply")
            outputs.append(("apply", rc, out, err))
            if rc != 0:
                return False, f"Failed to apply manifest: {err or out}"

            wait_pvc_inner = (
                f"kubectl wait -n {shlex.quote(namespace)} --for=jsonpath='{{.status.phase}}'=Bound "
                f"pvc/{shlex.quote(pvc_name)} --timeout={int(timeout_seconds)}s"
            )
            rc, out, err = _run(wait_pvc_inner)
            outputs.append(("wait_pvc", rc, out, err))
            if rc != 0:
                describe_cmd = f"kubectl describe -n {shlex.quote(namespace)} pvc/{shlex.quote(pvc_name)}"
                _, d_out, d_err = _run(describe_cmd)
                return False, f"PVC did not reach Bound state. {err or out}\n{d_out or d_err}"

            get_pv_cmd = (
                f"kubectl get -n {shlex.quote(namespace)} pvc/{shlex.quote(pvc_name)} "
                "-o jsonpath='{.spec.volumeName}'"
            )
            rc, out, err = _run(get_pv_cmd)
            outputs.append(("get_pv", rc, out, err))
            if rc != 0:
                return False, f"Failed to get PV name from PVC: {err or out}"

            pv_name = out.strip().strip("'")
            if not pv_name:
                return False, "PVC does not have a bound PV name (.spec.volumeName is empty)"

            wait_pv_cmd = (
                f"kubectl wait --for=jsonpath='{{.status.phase}}'=Bound pv/{shlex.quote(pv_name)} "
                f"--timeout={int(timeout_seconds)}s"
            )
            rc, out, err = _run(wait_pv_cmd)
            outputs.append(("wait_pv", rc, out, err))
            if rc != 0:
                describe_cmd = f"kubectl describe pv/{shlex.quote(pv_name)}"
                _, d_out, d_err = _run(describe_cmd)
                return False, f"PV did not reach Bound state. {err or out}\n{d_out or d_err}"

            rollout_cmd = (
                f"kubectl rollout status -n {shlex.quote(namespace)} deployment/{shlex.quote(deployment_name)} "
                f"--timeout={int(timeout_seconds)}s"
            )
            rc, out, err = _run(rollout_cmd)
            outputs.append(("rollout", rc, out, err))
            if rc != 0:
                describe_cmd = f"kubectl describe -n {shlex.quote(namespace)} deployment/{shlex.quote(deployment_name)}"
                _, d_out, d_err = _run(describe_cmd)
                return False, f"Deployment did not roll out successfully. {err or out}\n{d_out or d_err}"

            wait_pod_cmd = (
                f"kubectl wait -n {shlex.quote(namespace)} --for=condition=Ready pod "
                f"-l {shlex.quote(pod_selector)} --timeout={int(timeout_seconds)}s"
            )
            rc, out, err = _run(wait_pod_cmd)
            outputs.append(("wait_pod", rc, out, err))
            if rc != 0:
                get_pods_cmd = (
                    f"kubectl get pods -n {shlex.quote(namespace)} -l {shlex.quote(pod_selector)} "
                    "-o wide"
                )
                _, p_out, p_err = _run(get_pods_cmd)
                return False, f"Pod did not reach Ready state. {err or out}\n{p_out or p_err}"

            pvc_status_cmd = f"kubectl get -n {shlex.quote(namespace)} pvc/{shlex.quote(pvc_name)} -o wide"
            pv_status_cmd = f"kubectl get pv/{shlex.quote(pv_name)} -o wide"
            pods_status_cmd = (
                f"kubectl get pods -n {shlex.quote(namespace)} -l {shlex.quote(pod_selector)} -o wide"
            )
            _, pvc_out, _ = _run(pvc_status_cmd)
            _, pv_out, _ = _run(pv_status_cmd)
            _, pods_out, _ = _run(pods_status_cmd)

            message = (
                "PVC/PV and pod verification passed\n"
                f"{pvc_out}\n{pv_out}\n{pods_out}"
            )
            return True, message

        finally:
            if cleanup:
                delete_deploy_cmd = (
                    f"kubectl delete -n {shlex.quote(namespace)} deployment/{shlex.quote(deployment_name)} "
                    f"--ignore-not-found=true --wait=true --timeout={int(timeout_seconds)}s"
                )
                _run(delete_deploy_cmd)

                delete_pvc_cmd = (
                    f"kubectl delete -n {shlex.quote(namespace)} pvc/{shlex.quote(pvc_name)} "
                    f"--ignore-not-found=true --wait=true --timeout={int(timeout_seconds)}s"
                )
                _run(delete_pvc_cmd)

    def get_storage_class_details(self, storage_class_name):
        """Get detailed information about a storage class.

        Args:
            storage_class_name (str): Name of the storage class to get details for

        Returns:
            tuple: (bool, dict) - (True if successful, dictionary with storage class details or error message)
        """
        try:
            pxe_mapping = self.read_pxe_mapping_file()
            nodes = self.get_k8s_nodes_from_pxe(pxe_mapping)
            if not nodes:
                return False, {"error": "No nodes found in PXE mapping"}

            control_plane = self._get_control_plane_node(nodes)
            control_plane_host = control_plane.get("hostname") or control_plane.get("admin_ip")
            if not control_plane_host:
                return False, {"error": "Control plane node has no hostname or IP address"}

            # Get detailed storage class information
            cmd = f"kubectl get sc {storage_class_name} -o json"
            rc, out, err = self._ssh_from_omnia_core(control_plane_host, cmd)

            if rc != 0:
                return False, {"error": f"Failed to get storage class details: {err}"}

            try:
                sc_info = json.loads(out)
                return True, {
                    "name": sc_info.get("metadata", {}).get("name"),
                    "provisioner": sc_info.get("provisioner"),
                    "reclaim_policy": sc_info.get("reclaimPolicy"),
                    "volume_binding_mode": sc_info.get("volumeBindingMode"),
                    "parameters": sc_info.get("parameters", {}),
                    "annotations": sc_info.get("metadata", {}).get("annotations", {})
                }
            except json.JSONDecodeError as e:
                return False, {"error": f"Failed to parse storage class information: {str(e)}"}

        except Exception as e:
            return False, {"error": f"Error getting storage class details: {str(e)}"}

    def verify_persistent_volumes(self, expected_storage_class: str = "ps01"):
        """Verify that all Persistent Volumes are in the expected state.

        Returns:
            tuple: (bool, str) - (True if all PVs are valid, status message)
        """
        try:
            telemetry_config_path = "/opt/omnia/input/project_default/telemetry_config.yml"
            exists, _, file_info = self.verify_file_exists(telemetry_config_path)
            if not exists:
                return False, f"Telemetry config file not found: {telemetry_config_path}"

            telemetry_config_raw = (file_info or {}).get("contents") or ""
            try:
                telemetry_config = yaml.safe_load(telemetry_config_raw) or {}
            except Exception as e:
                return False, f"Failed to parse telemetry config file: {str(e)}"

            victoria_cfg = telemetry_config.get("victoria_configurations") or {}
            deployment_mode = str(victoria_cfg.get("deployment_mode") or "cluster").strip().strip('"').strip("'")
            if deployment_mode not in {"cluster", "single-node"}:
                deployment_mode = "cluster"

            expected_claim_to_capacity = {
                "telemetry/mysqldb-pvc-idrac-telemetry-0": "1Gi",
                "telemetry/data-0-kafka-broker-0": "8Gi",
                "telemetry/data-0-kafka-broker-1": "8Gi",
                "telemetry/data-0-kafka-broker-2": "8Gi",
                "telemetry/data-0-kafka-controller-3": "8Gi",
                "telemetry/data-0-kafka-controller-4": "8Gi",
                "telemetry/data-0-kafka-controller-5": "8Gi",
                "telemetry/vmstorage-data-vmstorage-0": "8Gi",
                "telemetry/vmstorage-data-vmstorage-1": "8Gi",
                "telemetry/vmstorage-data-vmstorage-2": "8Gi",
            }

            if deployment_mode == "single-node":
                expected_claim_to_capacity = {
                    k: v
                    for k, v in expected_claim_to_capacity.items()
                    if k
                    not in {
                        "telemetry/vmstorage-data-vmstorage-1",
                        "telemetry/vmstorage-data-vmstorage-2",
                    }
                }

                if expected_storage_class != "ps01":
                    expected_claim_to_capacity.pop("default/pvc-powerscale", None)

            pxe_mapping = self.read_pxe_mapping_file()
            nodes = self.get_k8s_nodes_from_pxe(pxe_mapping)
            if not nodes:
                return False, "No nodes found in PXE mapping"

            control_plane = self._get_control_plane_node(nodes)
            control_plane_host = control_plane.get("hostname") or control_plane.get("admin_ip")
            if not control_plane_host:
                return False, "Control plane node has no hostname or IP address"

            # Get PVs in JSON format
            cmd = "kubectl get pv -o json"
            rc, out, err = self._ssh_from_omnia_core(control_plane_host, cmd)

            if rc != 0:
                return False, f"Failed to get PVs: {err}"

            try:
                pvs = json.loads(out)
                if 'items' not in pvs:
                    return False, "No PVs found in the cluster"

                errors = []
                pv_by_claim = {}
                for pv in pvs['items']:
                    claim = pv.get('spec', {}).get('claimRef', {}).get('name', '')
                    namespace = pv.get('spec', {}).get('claimRef', {}).get('namespace', '')
                    if claim and namespace:
                        pv_by_claim[f"{namespace}/{claim}"] = pv

                for claim_key, expected_capacity in expected_claim_to_capacity.items():
                    pv = pv_by_claim.get(claim_key)
                    if not pv:
                        errors.append(f"Expected PV for claim {claim_key} was not found")
                        continue

                    name = pv.get('metadata', {}).get('name', 'unknown')
                    status = pv.get('status', {}).get('phase', '')
                    storage_class = pv.get('spec', {}).get('storageClassName', '')
                    capacity = pv.get('spec', {}).get('capacity', {}).get('storage', '')

                    if status != 'Bound':
                        errors.append(
                            f"PV {name} for claim {claim_key} is not in Bound state (current: {status})"
                        )

                    if storage_class != expected_storage_class:
                        errors.append(
                            f"PV {name} for claim {claim_key} has unexpected storage class: {storage_class} (expected: {expected_storage_class})"
                        )

                    if expected_capacity and capacity != expected_capacity:
                        errors.append(
                            f"PV {name} for claim {claim_key} has unexpected capacity: {capacity} (expected: {expected_capacity})"
                        )

                if errors:
                    return False, "PV validation failed:\n" + "\n".join(f"  - {e}" for e in errors)

                return True, (
                    f"Validated {len(expected_claim_to_capacity)} PV claims in deployment_mode={deployment_mode} "
                    f"with storageClass={expected_storage_class}"
                )

            except json.JSONDecodeError as e:
                return False, f"Failed to parse PV information: {str(e)}"

        except Exception as e:
            return False, f"Error verifying PVs: {str(e)}"

    def verify_basic_nginx_pod_running(self, namespace: str = "default", pod_name: str = "busybox-pod", image: str = "busybox:1.36"):
        try:
            pxe_mapping = self.read_pxe_mapping_file()
            nodes = self.get_k8s_nodes_from_pxe(pxe_mapping)
            if not nodes:
                return False, "No nodes found in PXE mapping", None

            control_plane = self._get_control_plane_node(nodes)
            control_plane_host = control_plane.get("hostname") or control_plane.get("admin_ip")
            if not control_plane_host:
                return False, "Control plane node has no hostname or IP address", None

            print(f"Deploying basic pod: {namespace}/{pod_name}")

            cleanup_cmd = f"kubectl delete pod {pod_name} -n {namespace} --ignore-not-found --wait=true --timeout=60s"
            self._ssh_from_omnia_core(control_plane_host, cleanup_cmd)

            apply_cmd = (
                f"cat <<'EOF' | kubectl apply -n {namespace} -f -\n"
                "apiVersion: v1\n"
                "kind: Pod\n"
                "metadata:\n"
                f"  name: {pod_name}\n"
                "spec:\n"
                "  containers:\n"
                "    - name: busybox\n"
                f"      image: {image}\n"
                "      command: [\"sh\", \"-c\"]\n"
                "      args:\n"
                "        - while true; do echo 'BusyBox pod running'; sleep 5; done\n"
                "EOF"
            )
            rc, out, err = self._ssh_from_omnia_core(control_plane_host, apply_cmd)
            if rc != 0:
                return False, f"Failed to apply pod manifest: {err}", None

            wait_cmd = f"kubectl wait --for=condition=Ready pod/{pod_name} -n {namespace} --timeout=30s"
            rc, out, err = self._ssh_from_omnia_core(control_plane_host, wait_cmd)
            if rc != 0:
                describe_cmd = f"kubectl get pod {pod_name} -n {namespace} -o json"
                _, pod_json, _ = self._ssh_from_omnia_core(control_plane_host, describe_cmd)
                return False, f"Pod did not become Ready: {err}\n{pod_json}", None

            get_cmd = f"kubectl get pod {pod_name} -n {namespace} -o json"
            rc, out, err = self._ssh_from_omnia_core(control_plane_host, get_cmd)
            if rc != 0:
                return False, f"Failed to get pod status: {err}", None

            pod = json.loads(out)
            deletion_timestamp = pod.get("metadata", {}).get("deletionTimestamp")
            phase = pod.get("status", {}).get("phase", "Unknown")
            status = "Terminating" if deletion_timestamp else phase
            node = pod.get("spec", {}).get("nodeName", "Unknown")

            ready = False
            for condition in pod.get("status", {}).get("conditions", []) or []:
                if condition.get("type") == "Ready":
                    ready = condition.get("status") == "True"
                    break

            pod_info = {
                "name": pod_name,
                "namespace": namespace,
                "status": status,
                "node": node,
                "ready": ready,
            }

            if status == "Running" and ready:
                message = f"Pod is Running and Ready: {namespace}/{pod_name} (Node: {node})"
                print(message)
                return True, message, pod_info

            container_reason = ""
            statuses = pod.get("status", {}).get("containerStatuses") or []
            if statuses:
                state = statuses[0].get("state") or {}
                waiting = state.get("waiting") or {}
                terminated = state.get("terminated") or {}
                if waiting.get("reason"):
                    container_reason = f" (Reason: {waiting.get('reason')})"
                elif terminated.get("reason"):
                    container_reason = f" (Reason: {terminated.get('reason')})"

            message = f"Pod is not Running/Ready: {namespace}/{pod_name} (Node: {node}): {status}, Ready={ready}{container_reason}"
            print(message)
            return False, message, pod_info

        except Exception as e:
            return False, f"Error deploying/verifying pod: {str(e)}", None
        finally:
            try:
                pxe_mapping = self.read_pxe_mapping_file()
                nodes = self.get_k8s_nodes_from_pxe(pxe_mapping)
                control_plane = self._get_control_plane_node(nodes)
                control_plane_host = control_plane.get("hostname") or control_plane.get("admin_ip")
                if control_plane_host:
                    delete_cmd = f"kubectl delete pod {pod_name} -n {namespace} --ignore-not-found --wait=false"
                    self._ssh_from_omnia_core(control_plane_host, delete_cmd)
            except Exception:
                pass



    def verify_pods_in_namespace(self, namespace, component_name, expect_none=False):
        """
        Verify that pods exist in the specified namespace.

        Args:
            namespace (str): The namespace to check for pods
            component_name (str): Human-readable name of the component
            expect_none (bool): If True, expect no pods to exist in the namespace

        Returns:
            tuple: (bool, str) - (True if condition is met, status message)
        """
        print(f"Checking pods in namespace: {namespace}")

        try:
            # Get control plane node
            pxe_mapping = self.read_pxe_mapping_file()
            nodes = self.get_k8s_nodes_from_pxe(pxe_mapping)
            control_plane = self._get_control_plane_node(nodes)
            control_plane_host = control_plane.get("hostname") or control_plane.get("admin_ip")

            if not control_plane_host:
                raise ValueError("No control plane node found")

            # Get all pods in the specified namespace
            cmd = f"kubectl get pods -n {namespace} -o json"
            rc, out, err = self._ssh_from_omnia_core(control_plane_host, cmd)

            if "namespaces" in err and "not found" in err:
                if expect_none:
                    return True, f"Namespace '{namespace}' not found (as expected)"
                return False, f"Namespace '{namespace}' not found"

            if rc != 0:
                raise RuntimeError(f"Failed to get pod information: {err}")

            # Process the pods
            pods_data = json.loads(out)
            pods = pods_data.get('items', [])

            if expect_none:
                if not pods:
                    return True, f"No pods found in namespace '{namespace}' (as expected)"
                pod_list = [p['metadata']['name'] for p in pods]
                return False, (
                    f"Found pods in namespace '{namespace}' when none were expected: {', '.join(pod_list)}"
                )

            if not pods:
                return False, f"No pods found in namespace '{namespace}'"

            # Check each pod
            failed_pods = []
            for pod in pods:
                pod_name = pod['metadata']['name']
                deletion_timestamp = pod.get('metadata', {}).get('deletionTimestamp')
                phase = pod.get('status', {}).get('phase', 'Unknown')
                status = 'Terminating' if deletion_timestamp else phase
                node = pod.get('spec', {}).get('nodeName', 'Unknown')

                status_display = "[PASS]" if status == "Running" else "[FAIL]"
                print(f"{status_display} {namespace}/{pod_name} (Node: {node}): {status}")

                if status != "Running":
                    failed_pods.append(f"{namespace}/{pod_name} (Status: {status})")

            if failed_pods:
                message = f"Some {component_name} pods are not in Running state:\n"
                message += "\n".join(failed_pods)
                print(message)
                return False, message

            message = POD_CHECK_PASSED.format(component=component_name)
            print(message)
            return True, message

        except Exception as e:
            return False, f"Error checking {component_name} pods: {str(e)}"

    def verify_isilon_csi_driver_pods_from_software_config(self):
        configured, config_message = self.is_powerscale_csi_configured_in_software_config()
        if configured is None:
            return None, config_message
        if not configured:
            return None, config_message

        success, pods_message = self.verify_pods_in_namespace(
            namespace="isilon",
            component_name="Isilon CSI Driver",
        )
        return success, pods_message

    def get_service_k8s_version_from_software_config(self):
        software_config_path = "/opt/omnia/input/project_default/software_config.json"

        exists, message, file_info = self.verify_file_exists(software_config_path)
        if not exists:
            raise RuntimeError(message)

        config_content = file_info.get("contents") or ""
        if "---CONTENTS---" in config_content:
            _, _, config_content = config_content.partition("---CONTENTS---")
            config_content = config_content.strip()
        if not config_content:
            raise RuntimeError("Failed to read software config file")

        try:
            software_config = json.loads(config_content)
        except Exception as e:
            raise RuntimeError(f"Failed to parse software config file: {str(e)}") from e

        for sw in software_config.get("softwares", []):
            if isinstance(sw, dict) and sw.get("name") == "service_k8s":
                version = (sw.get("version") or "").strip()
                if version.startswith("v"):
                    version = version[1:]
                if version:
                    return version
                break

        raise RuntimeError("service_k8s version not found in software_config.json")

    def is_powerscale_csi_configured_in_software_config(self):
        software_config_path = "/opt/omnia/input/project_default/software_config.json"

        exists, message, file_info = self.verify_file_exists(software_config_path)
        if not exists:
            return None, message

        config_content = file_info.get("contents") or ""
        if not config_content:
            return False, "Failed to read software config file"

        try:
            software_config = json.loads(config_content)
        except Exception as e:
            return False, f"Failed to parse software config file: {str(e)}"

        is_configured = any(
            isinstance(sw, dict)
            and sw.get("name") == "csi_driver_powerscale"
            and sw.get("version") == "v2.15.0"
            and "x86_64" in sw.get("arch", [])
            for sw in software_config.get("softwares", [])
        )

        if is_configured:
            return True, "csi_driver_powerscale is present in software_config.json"

        return False, "csi_driver_powerscale is not present in software_config.json"


def get_oim_operations(config_path=None):
    """Get an instance of OIMOperations.
        config_path (str, optional): Path to the user config file.

    Returns:
        OIMOperations: An instance of OIMOperations.
    """
    return OIMOperations(config_path=config_path)
