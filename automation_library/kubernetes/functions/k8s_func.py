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
from paramiko.ssh_exception import (
    AuthenticationException,
    BadHostKeyException,
    NoValidConnectionsError,
    SSHException,
)
from automation_library.checks.vars.oim_prereq_vars import (
    OMNIA_TEST_CONFIG_PATH as DEFAULT_USER_CONFIG_PATH,
)
from automation_library.core import (
    get_testinfra_host,
    run_in_container,
    run_on_remote_node,
    get_nodes_info,
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
    REBOOT_VIP_NODE_INITIATED,
    REBOOT_VIP_NODE_NOT_FOUND,
    REBOOT_VIP_NO_REMAINING,
    K8S_NODE_ONLINE_PASSED,
    K8S_NODE_ONLINE_FAILED,
    K8S_CLOUD_INIT_PASSED,
    K8S_CLOUD_INIT_FAILED,
    K8S_NODE_READY_PASSED,
    K8S_NODE_READY_FAILED,
    K8S_VIP_FAILOVER_PASSED,
    K8S_VIP_FAILOVER_FAILED,
    K8S_VIP_FAILOVER_MULTI,
    ERR_NO_CONTROL_PLANE_HOST,
    ERR_NO_NODES_IN_PXE,
    ERR_NO_CP_IN_PXE,
    ERR_NO_CP_ADMIN_IPS,
    ERR_CP_MISSING_HOST,
    ERR_CP_MISSING_ADMIN_IP,
    ERR_NO_VALID_CP_IPS,
    NFS_SC_NOT_FOUND,
    NFS_SC_PARSE_ERROR,
    NFS_SC_NO_DYNAMIC_PROVISIONER,
    NFS_SC_UNEXPECTED_BINDING_MODE,
    NFS_SC_NO_SERVER,
    NFS_SC_NO_PATH,
    NFS_SC_VALIDATION_FAILED,
    NFS_SC_DYNAMIC,
    NFS_SC_ERROR,
    TELEMETRY_PVC_READ_CONFIG_ERROR,
    TELEMETRY_PVC_PARSE_CONFIG_ERROR,
    TELEMETRY_PVC_GET_ERROR,
    TELEMETRY_PVC_PARSE_ERROR,
    TELEMETRY_PVC_NONE_FOUND,
    TELEMETRY_PVC_PHASE_MISMATCH,
    TELEMETRY_PVC_SC_MISMATCH,
    TELEMETRY_PVC_NO_VOLUME,
    TELEMETRY_PVC_KAFKA_SIZE_MISMATCH,
    TELEMETRY_PVC_VICTORIA_SIZE_MISMATCH,
    TELEMETRY_PVC_CHECK_FAILED,
    TELEMETRY_PVC_CHECK_PASSED,
    TELEMETRY_PVC_ERROR,
    NFS_DIR_GET_PV_ERROR,
    NFS_DIR_PARSE_PV_ERROR,
    NFS_DIR_NO_PVS,
    NFS_DIR_MOUNT_ERROR,
    NFS_DIR_NOT_FOUND,
    NFS_DIR_NOT_FOUND_REASON,
    NFS_DIR_CHECK_FAILED,
    NFS_DIR_CHECK_PASSED,
    NFS_DIR_ERROR,
    SC_GET_ERROR,
    SC_NONE_FOUND,
    SC_NOT_FOUND,
    SC_NOT_DEFAULT,
    SC_IS_DEFAULT,
    SC_PARSE_ERROR,
    SC_VERIFY_ERROR,
    ETCD_PODS_FIND_FAILED,
    ETCD_PODS_NONE_FOUND,
    ETCD_HEALTH_ALL_PASSED,
    ETCD_HEALTH_PARTIAL,
    ETCD_HEALTH_NO_OUTPUT,
    ETCD_MEMBER_COUNT_MISMATCH,
    ETCD_MEMBER_LIST_PASSED,
    ETCD_MEMBER_LIST_FAILED,
    ETCD_LEADER_FAILED_RUN,
    ETCD_LEADER_PARSE_FAILED,
)
from automation_library.kubernetes.vars.k8s_vars import (
    CRI_O_SERVICE,
    CRIO_SERVICE,
    CHRONYD_SERVICE,
    CONTROL_PLANE_GROUP,
    HA_CONFIG_FILE,
    KUBELET_SERVICE,
    READY_STATE_MAX_RETRIES,
    READY_STATE_RETRY_DELAY_SECONDS,
    WORKER_NODE_GROUP,
    K8S_REBOOT_WAIT_ONLINE_TIMEOUT,
    K8S_REBOOT_WAIT_ONLINE_POLL,
    K8S_CLOUD_INIT_TIMEOUT,
    K8S_CLOUD_INIT_POLL,
    K8S_NODE_READY_TIMEOUT,
    K8S_NODE_READY_POLL,
    K8S_VIP_FAILOVER_TIMEOUT,
    K8S_VIP_FAILOVER_POLL,
    PXE_MAPPING_FILE_PATH,
    TELEMETRY_CONFIG_PATH,
    NFS_DEFAULT_STORAGE_CLASS,
    NFS_PROVISIONER_POD_PREFIX,
    NFS_PROVISIONER_APP_LABEL,
    NFS_SERVER_ENV_VAR,
    NFS_PATH_ENV_VAR,
    NFS_MANUAL_PROVISIONER,
    SC_BINDING_MODE_IMMEDIATE,
    NFS_MOUNT_TMP_PREFIX,
    NFS_MOUNT_OPTIONS,
    SC_DEFAULT_ANNOTATION,
    SC_DEFAULT_ANNOTATION_BETA,
    TELEMETRY_NAMESPACE,
    TELEMETRY_KAFKA_PVC_PATTERN,
    TELEMETRY_VMSTORAGE_PVC_PATTERN,
    TELEMETRY_VLSTORAGE_PVC_PATTERN,
    TELEMETRY_KAFKA_CFG_SECTION,
    TELEMETRY_VICTORIA_CFG_SECTION,
    TELEMETRY_PERSISTENCE_SIZE_KEY,
    ETCD_NAMESPACE,
    ETCD_PORT,
    ETCD_PKI_CACERT,
    ETCD_PKI_CERT,
    ETCD_PKI_KEY,
    ETCD_RAFT_DELTA_MAX,
    K8S_CMD_TEMPLATES,
    NFS_CMD_TEMPLATES,
)

# Constants
USER_CONFIG_PATH = DEFAULT_USER_CONFIG_PATH
OMNIA_CORE_CONTAINER_NAME = "omnia_core"

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
        self._testinfra_host = None

    def _load_config(self):
        """Load configuration from user config file."""
        with open(self.config_path, 'r', encoding="utf-8") as file:
            return yaml.safe_load(file)

    def connect_ssh(self):
        """Establish SSH connection to OIM server."""
        if self.ssh_client is not None:
            transport = self.ssh_client.get_transport()
            if transport and transport.is_active():
                return self.ssh_client
            try:
                self.ssh_client.close()
            except (OSError, SSHException):
                pass
            self.ssh_client = None

        try:
            self.ssh_client = SSHClient()
            self.ssh_client.set_missing_host_key_policy(AutoAddPolicy())
            self.ssh_client.connect(
                self.config['oim_server_ip'],
                username=self.config['oim_ssh_user'],
                password=self.config['oim_ssh_password'],
                port=self.config.get('oim_ssh_port', 22),
                timeout=int(self.config.get('oim_ssh_timeout', 10) or 10),
            )
            return self.ssh_client
        except (AuthenticationException, BadHostKeyException, NoValidConnectionsError, SSHException, OSError) as e:
            try:
                if self.ssh_client is not None:
                    self.ssh_client.close()
            finally:
                self.ssh_client = None
            raise RuntimeError(f"Failed to establish SSH connection: {str(e)}") from e

    def _run_ssh_command(self, command):
        """Run a command on the remote server via SSH and return the output.

        Args:
            command (str): The command to run on the remote server.

        Returns:
            str: The command output.

        Raises:
            Exception: If the command fails.
        """
        self.connect_ssh()

        try:
            _stdin, stdout, stderr = self.ssh_client.exec_command(command)
        except (AttributeError, SSHException, OSError) as e:
            # Transport can become None/inactive mid-run; reconnect once and retry.
            try:
                if self.ssh_client is not None:
                    self.ssh_client.close()
            except (OSError, SSHException):
                pass
            self.ssh_client = None
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
            try:
                self.ssh_client.close()
            except (OSError, SSHException):
                pass
            finally:
                self.ssh_client = None
        self._testinfra_host = None

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

        endpoints = ",".join([f"https://{ip}:{ETCD_PORT}" for ip in admin_ips])

        # Get all etcd pods
        find_pods_inner = K8S_CMD_TEMPLATES["find_etcd_pods"].format(namespace=ETCD_NAMESPACE)
        find_pods_cmd = f"bash -lc {shlex.quote(find_pods_inner)}"
        rc, out, err = self._ssh_from_omnia_core(watcher_host, find_pods_cmd)
        if rc != 0 or not out:
            return False, ETCD_PODS_FIND_FAILED.format(error=err or out), (err or out or "")

        etcd_pods = [line.strip().replace("pod/", "") for line in (out or "").splitlines() if line.strip()]
        if not etcd_pods:
            return False, ETCD_PODS_NONE_FOUND, out

        etcdctl_cmd = K8S_CMD_TEMPLATES["etcdctl_health"].format(
            endpoints=shlex.quote(endpoints),
            cacert=ETCD_PKI_CACERT,
            cert=ETCD_PKI_CERT,
            key=ETCD_PKI_KEY,
        )

        # Try each etcd pod until one succeeds or we get valid output
        last_error = ""
        last_output = ""
        for etcd_pod in etcd_pods:
            exec_inner = K8S_CMD_TEMPLATES["kubectl_exec_sh_lc"].format(
                namespace=ETCD_NAMESPACE,
                pod=shlex.quote(etcd_pod),
                cmd=shlex.quote(etcdctl_cmd),
            )
            exec_cmd = f"bash -lc {shlex.quote(exec_inner)}"
            rc, out, err = self._ssh_from_omnia_core(watcher_host, exec_cmd)
            output = (out or "").strip() + ("\n" + (err or "").strip() if (err or "").strip() else "")

            # Check if we got valid health output (even if rc != 0)
            # etcdctl returns non-zero if any endpoint is unhealthy
            health_lines = [line for line in (out or "").splitlines() if line.strip()]
            healthy_count = sum(1 for line in health_lines if "is healthy" in line.lower())
            unhealthy_count = sum(1 for line in health_lines if "is unhealthy" in line.lower())

            if healthy_count > 0 or unhealthy_count > 0:
                expected_count = len(admin_ips)
                if healthy_count == expected_count:
                    return True, ETCD_HEALTH_ALL_PASSED.format(count=expected_count), output
                unhealthy_endpoints = [
                    line.split()[0] for line in health_lines if "is unhealthy" in line.lower()
                ]
                return False, ETCD_HEALTH_PARTIAL.format(
                    healthy=healthy_count, total=expected_count,
                    unhealthy=", ".join(unhealthy_endpoints),
                ), output
            else:
                last_error = f"Pod {etcd_pod}: no valid health output"
                last_output = output

        return False, ETCD_HEALTH_NO_OUTPUT.format(error=last_error), last_output

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
            list: List of dicts containing node information (hostname, admin_ip, role).
        """
        reader = csv.DictReader(io.StringIO(pxe_mapping))
        nodes = []
        wanted = {"service_kube_control_plane_x86_64", "service_kube_node_x86_64"}
        for row in reader:
            func_group = (row.get("FUNCTIONAL_GROUP_NAME") or "").strip()
            if func_group in wanted:
                hostname = (row.get("HOSTNAME") or "").strip()
                admin_ip = (row.get("ADMIN_IP") or "").strip()
                role = "control_plane" if func_group == "service_kube_control_plane_x86_64" else "worker"
                if hostname or admin_ip:
                    nodes.append({"hostname": hostname, "admin_ip": admin_ip, "role": role})
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
            status_display = f"{status}"
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
            if node.get("role") == "control_plane"
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
        reachable_count = 0
        
        for node_name, is_correct, actual_version, error in results:
            if error:
                # Check if it's an SSH/connectivity error (unreachable node)
                if "No route to host" in error or "Connection refused" in error or "Connection timed out" in error:
                    # Skip unreachable nodes
                    continue
                all_passed = False
                failures.append(f"{node_name}: {error}")
            elif not is_correct:
                reachable_count += 1
                all_passed = False
                failures.append(
                    f"{node_name}: expected {expected_version}, got {actual_version}"
                )
            else:
                reachable_count += 1

        if reachable_count == 0:
            return False, "All control plane nodes are unreachable", results
            
        if all_passed:
            return True, f"kubectl client version matches expected version {expected_version} on all reachable control planes", results
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
            if node.get("role") == "control_plane"
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

    def format_pod_details(self, pod_statuses, default_namespace="default"):
        """Format pod statuses into a details string for logging.

        Args:
            pod_statuses (list): List of pod status dictionaries with keys:
                - name: Pod name
                - namespace: Pod namespace
                - status: Pod status (e.g., Running, Pending)
                - node: Node name where pod is running
            default_namespace (str): Default namespace if not present in pod dict

        Returns:
            str or None: Formatted details string, or None if no pods
        """
        if not pod_statuses:
            return None
        details_lines = []
        for pod in pod_statuses:
            namespace = pod.get("namespace") or default_namespace
            line = (
                f"{namespace}/{pod.get('name')} (Node: {pod.get('node', 'Unknown')}): "
                f"{pod.get('status')}"
            )
            details_lines.append(line)
        return "\n".join(details_lines) if details_lines else None

    def format_container_runtime_details(self, results):
        """Format container runtime verification results into a details string.

        Args:
            results (list): List of tuples (node_name, is_correct, actual_runtime, error)

        Returns:
            str or None: Formatted details string, or None if no results
        """
        if not results:
            return None
        details_lines = []
        for node_name, is_correct, actual_runtime, error in results:
            if is_correct:
                details_lines.append(f"{node_name}: {actual_runtime}")
            else:
                suffix = f" ({error})" if error else ""
                details_lines.append(f"{node_name}: {actual_runtime or 'unknown'}{suffix}")
        return "\n".join(details_lines) if details_lines else None

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
            cmd = K8S_CMD_TEMPLATES["get_pods_all_json"]
            rc, out, err = self._ssh_from_omnia_core(control_plane_host, cmd)

            if rc != 0:
                return False, f"Failed to get pod information: {err}", {}

            # Process the output
            pod_info = {}
            try:
                pods_data = json.loads(out)
                for item in pods_data.get('items', []):
                    pod_name = item.get('metadata', {}).get('name', '')
                    if pod_name.startswith(NFS_PROVISIONER_POD_PREFIX):
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

    def _get_nfs_provisioner_server_path(self, control_plane_host):
        """Get NFS server and path from the nfs-subdir-external-provisioner pod env vars.

        The Helm chart for nfs-subdir-external-provisioner stores NFS_SERVER and NFS_PATH
        as container env vars in the provisioner deployment, not in the StorageClass parameters.

        Returns:
            tuple: (nfs_server, nfs_path) strings, or (None, None) if not found
        """
        cmd = NFS_CMD_TEMPLATES["get_provisioner_pods"].format(
            app_label=NFS_PROVISIONER_APP_LABEL,
        )
        rc, out, _ = self._ssh_from_omnia_core(control_plane_host, cmd)
        if rc != 0 or not out:
            return None, None
        try:
            pods = json.loads(out)
            for pod in pods.get("items", []):
                for container in pod.get("spec", {}).get("containers", []):
                    env_map = {e["name"]: e.get("value", "") for e in container.get("env", [])}
                    nfs_server = env_map.get(NFS_SERVER_ENV_VAR, "")
                    nfs_path = env_map.get(NFS_PATH_ENV_VAR, "")
                    if nfs_server and nfs_path:
                        return nfs_server, nfs_path
        except (json.JSONDecodeError, KeyError):
            pass
        return None, None

    def verify_nfs_storage_class(self, storage_class_name="nfs-client"):
        """Verify the NFS StorageClass exists, has a dynamic provisioner, and is usable.

        Checks:
          - StorageClass exists
          - Provisioner is set and not manual (kubernetes.io/no-provisioner)
          - volumeBindingMode is Immediate or unset (default Immediate)
          - NFS server and path resolved from provisioner pod env vars (NFS_SERVER, NFS_PATH)

        Returns:
            tuple: (bool, str, dict) - (success, message, sc_details)
        """
        try:
            pxe_mapping = self.read_pxe_mapping_file()
            nodes = self.get_k8s_nodes_from_pxe(pxe_mapping)
            control_plane = self._get_control_plane_node(nodes)
            control_plane_host = control_plane.get("hostname") or control_plane.get("admin_ip")
            if not control_plane_host:
                return False, "Control plane node has no hostname or IP address", {}

            rc, out, err = self._ssh_from_omnia_core(
                control_plane_host,
                K8S_CMD_TEMPLATES["get_sc_name_json"].format(name=storage_class_name),
            )
            if rc != 0:
                return False, NFS_SC_NOT_FOUND.format(name=storage_class_name, error=err or out), {}

            try:
                sc = json.loads(out)
            except json.JSONDecodeError as e:
                return False, NFS_SC_PARSE_ERROR.format(error=str(e)), {}

            provisioner = sc.get("provisioner", "")
            reclaim_policy = sc.get("reclaimPolicy", "")
            binding_mode = sc.get("volumeBindingMode", "")

            # NFS server/path are in the provisioner pod env vars, not SC parameters
            nfs_server, nfs_path = self._get_nfs_provisioner_server_path(control_plane_host)

            sc_details = {
                "name": storage_class_name,
                "provisioner": provisioner,
                "reclaimPolicy": reclaim_policy,
                "volumeBindingMode": binding_mode or SC_BINDING_MODE_IMMEDIATE,
                "nfs_server": nfs_server or "",
                "nfs_path": nfs_path or "",
            }

            errors = []
            if not provisioner or provisioner == NFS_MANUAL_PROVISIONER:
                errors.append(NFS_SC_NO_DYNAMIC_PROVISIONER.format(provisioner=provisioner))
            if binding_mode and binding_mode != SC_BINDING_MODE_IMMEDIATE:
                errors.append(NFS_SC_UNEXPECTED_BINDING_MODE.format(mode=binding_mode))
            if not nfs_server:
                errors.append(NFS_SC_NO_SERVER)
            if not nfs_path:
                errors.append(NFS_SC_NO_PATH)

            if errors:
                return False, NFS_SC_VALIDATION_FAILED.format(
                    name=storage_class_name, errors="; ".join(errors),
                ), sc_details

            return True, NFS_SC_DYNAMIC.format(
                name=storage_class_name, provisioner=provisioner,
                server=nfs_server, path=nfs_path,
            ), sc_details

        except Exception as e:
            return False, NFS_SC_ERROR.format(error=str(e)), {}

    def _read_telemetry_config(self):
        """Read and parse telemetry_config.yml from the omnia_core container.

        Returns:
            tuple: (dict or None, error_str or None)
        """
        rc, out, err = self._run_in_omnia_core(f"cat {TELEMETRY_CONFIG_PATH}", check=False)
        if rc != 0:
            return None, TELEMETRY_PVC_READ_CONFIG_ERROR.format(error=err or out)
        try:
            return yaml.safe_load(out), None
        except yaml.YAMLError as e:
            return None, TELEMETRY_PVC_PARSE_CONFIG_ERROR.format(error=str(e))

    def verify_telemetry_pvcs(self, storage_class_name="nfs-client", namespace="telemetry"):
        """Verify all telemetry PVCs are Bound with correct storage class, PV, and volume size.

        Reads telemetry_config.yml to validate expected storage sizes:
          - PVCs with 'kafka' in the name: kafka_configurations.persistence_size
          - PVCs with 'vmstorage' in the name: victoria_configurations.persistence_size
          - PVCs with 'vlstorage' in the name: victoria_configurations.persistence_size
          - Other PVCs (mysql, vlagent, etc.): verified Bound and correct SC only

        Works for both NFS (storage_class_name='nfs-client') and CSI (e.g. 'ps01') setups.

        Returns:
            tuple: (bool, str, list) - (success, message, pvc_results)
        """
        try:
            telemetry_cfg, cfg_err = self._read_telemetry_config()
            if cfg_err:
                return False, cfg_err, []

            kafka_size = (
                (telemetry_cfg.get(TELEMETRY_KAFKA_CFG_SECTION) or {})
                .get(TELEMETRY_PERSISTENCE_SIZE_KEY, "")
            )
            victoria_size = (
                (telemetry_cfg.get(TELEMETRY_VICTORIA_CFG_SECTION) or {})
                .get(TELEMETRY_PERSISTENCE_SIZE_KEY, "")
            )

            pxe_mapping = self.read_pxe_mapping_file()
            nodes = self.get_k8s_nodes_from_pxe(pxe_mapping)
            control_plane = self._get_control_plane_node(nodes)
            control_plane_host = control_plane.get("hostname") or control_plane.get("admin_ip")
            if not control_plane_host:
                return False, ERR_NO_CONTROL_PLANE_HOST, []

            rc, out, err = self._ssh_from_omnia_core(
                control_plane_host,
                K8S_CMD_TEMPLATES["get_pvc_ns_json"].format(namespace=namespace),
            )
            if rc != 0:
                return False, TELEMETRY_PVC_GET_ERROR.format(namespace=namespace, error=err or out), []

            try:
                pvcs_json = json.loads(out)
            except json.JSONDecodeError as e:
                return False, TELEMETRY_PVC_PARSE_ERROR.format(error=str(e)), []

            items = pvcs_json.get("items", [])
            if not items:
                return False, TELEMETRY_PVC_NONE_FOUND.format(namespace=namespace), []

            pvc_results = []
            errors = []

            for pvc in items:
                pvc_name = pvc.get("metadata", {}).get("name", "unknown")
                phase = pvc.get("status", {}).get("phase", "")
                sc = pvc.get("spec", {}).get("storageClassName", "")
                volume_name = pvc.get("spec", {}).get("volumeName", "")
                actual_size = (
                    pvc.get("spec", {}).get("resources", {}).get("requests", {}).get("storage", "")
                )

                result = {
                    "pvc": pvc_name,
                    "phase": phase,
                    "storageClass": sc,
                    "volumeName": volume_name,
                    "actualSize": actual_size,
                    "success": True,
                    "issues": [],
                }

                if phase != "Bound":
                    result["issues"].append(TELEMETRY_PVC_PHASE_MISMATCH.format(phase=phase))
                if sc != storage_class_name:
                    result["issues"].append(
                        TELEMETRY_PVC_SC_MISMATCH.format(sc=sc, expected=storage_class_name)
                    )
                if not volume_name:
                    result["issues"].append(TELEMETRY_PVC_NO_VOLUME)

                if TELEMETRY_KAFKA_PVC_PATTERN in pvc_name and kafka_size:
                    if actual_size != kafka_size:
                        result["issues"].append(
                            TELEMETRY_PVC_KAFKA_SIZE_MISMATCH.format(
                                actual=actual_size, expected=kafka_size,
                            )
                        )
                elif (
                    TELEMETRY_VMSTORAGE_PVC_PATTERN in pvc_name
                    or TELEMETRY_VLSTORAGE_PVC_PATTERN in pvc_name
                ) and victoria_size:
                    if actual_size != victoria_size:
                        result["issues"].append(
                            TELEMETRY_PVC_VICTORIA_SIZE_MISMATCH.format(
                                actual=actual_size, expected=victoria_size,
                            )
                        )

                if result["issues"]:
                    result["success"] = False
                    errors.append(f"PVC {pvc_name}: " + "; ".join(result["issues"]))

                pvc_results.append(result)

            if errors:
                return False, TELEMETRY_PVC_CHECK_FAILED.format(
                    failed=len(errors), total=len(items), errors="; ".join(errors),
                ), pvc_results

            return True, TELEMETRY_PVC_CHECK_PASSED.format(
                count=len(items), namespace=namespace, sc=storage_class_name,
            ), pvc_results

        except Exception as e:
            return False, TELEMETRY_PVC_ERROR.format(error=str(e)), []

    def verify_nfs_backend_directories(self, storage_class_name="nfs-client"):
        """Verify NFS backend directories exist for each PV and have correct permissions.

        For each PV using the NFS storage class:
          - Reads NFS server and full path from pv.spec.nfs
          - Groups PVs by (nfs_server, base_path) to minimise mount operations
          - Mounts the NFS export read-only on the control plane node
          - Verifies each PV subdirectory exists and reports permissions
          - Unmounts after all checks

        Note: Uses NFS mount from the control plane node rather than SSH to the NFS
        server, since the NFS server may not have SSH access configured.

        Returns:
            tuple: (bool, str, list) - (success, message, dir_results)
        """
        try:
            pxe_mapping = self.read_pxe_mapping_file()
            nodes = self.get_k8s_nodes_from_pxe(pxe_mapping)
            control_plane = self._get_control_plane_node(nodes)
            control_plane_host = control_plane.get("hostname") or control_plane.get("admin_ip")
            if not control_plane_host:
                return False, ERR_NO_CONTROL_PLANE_HOST, []

            rc, out, err = self._ssh_from_omnia_core(
                control_plane_host, K8S_CMD_TEMPLATES["get_pv_json"],
            )
            if rc != 0:
                return False, NFS_DIR_GET_PV_ERROR.format(error=err or out), []

            try:
                pvs_json = json.loads(out)
            except json.JSONDecodeError as e:
                return False, NFS_DIR_PARSE_PV_ERROR.format(error=str(e)), []

            nfs_pvs = [
                pv for pv in pvs_json.get("items", [])
                if pv.get("spec", {}).get("storageClassName", "") == storage_class_name
                and pv.get("spec", {}).get("nfs")
            ]

            if not nfs_pvs:
                return True, NFS_DIR_NO_PVS.format(sc=storage_class_name), []

            # Group PVs by (nfs_server, base_path) to share mount points
            # pv.spec.nfs.path = <base_path>/<subdir> (the provisioner creates one subdir level)
            mount_groups = {}  # (server, base_path) -> [(pv_name, subdir), ...]
            for pv in nfs_pvs:
                pv_name = pv.get("metadata", {}).get("name", "unknown")
                nfs_spec = pv.get("spec", {}).get("nfs", {})
                nfs_server = nfs_spec.get("server", "")
                full_path = nfs_spec.get("path", "").rstrip("/")
                if not nfs_server or not full_path:
                    continue
                parts = full_path.rsplit("/", 1)
                base_path = parts[0] if len(parts) == 2 else "/"
                subdir = parts[1] if len(parts) == 2 else full_path.lstrip("/")
                key = (nfs_server, base_path)
                mount_groups.setdefault(key, []).append((pv_name, subdir))

            dir_results = []
            errors = []

            for (nfs_server, base_path), pv_subdirs in mount_groups.items():
                mount_point = f"{NFS_MOUNT_TMP_PREFIX}{abs(hash((nfs_server, base_path))) % 100000}"
                mount_cmd = NFS_CMD_TEMPLATES["mount_nfs"].format(
                    mount_point=mount_point,
                    options=NFS_MOUNT_OPTIONS,
                    server=nfs_server,
                    path=base_path,
                )
                rc, out, err = self._ssh_from_omnia_core(control_plane_host, mount_cmd)
                if rc != 0:
                    msg = NFS_DIR_MOUNT_ERROR.format(
                        server=nfs_server, path=base_path, error=err or out,
                    )
                    for pv_name, _ in pv_subdirs:
                        errors.append(f"PV {pv_name}: {msg}")
                        dir_results.append({
                            "pv": pv_name, "nfs_server": nfs_server,
                            "path": base_path, "success": False, "reason": msg,
                        })
                    continue

                try:
                    for pv_name, subdir in pv_subdirs:
                        full_dir = f"{mount_point}/{subdir}"
                        check_rc, check_out, _ = self._ssh_from_omnia_core(
                            control_plane_host,
                            NFS_CMD_TEMPLATES["check_dir_exists"].format(path=full_dir),
                        )
                        exists = check_rc == 0 and "EXISTS" in check_out

                        if not exists:
                            errors.append(
                                f"PV {pv_name}: "
                                + NFS_DIR_NOT_FOUND.format(
                                    subdir=subdir, server=nfs_server, path=base_path,
                                )
                            )
                            dir_results.append({
                                "pv": pv_name, "nfs_server": nfs_server,
                                "path": f"{base_path}/{subdir}", "success": False,
                                "reason": NFS_DIR_NOT_FOUND_REASON,
                            })
                            continue

                        stat_rc, stat_out, _ = self._ssh_from_omnia_core(
                            control_plane_host,
                            NFS_CMD_TEMPLATES["stat_dir"].format(path=full_dir),
                        )
                        perms = stat_out.strip() if stat_rc == 0 else "unknown"
                        dir_results.append({
                            "pv": pv_name, "nfs_server": nfs_server,
                            "path": f"{base_path}/{subdir}", "success": True,
                            "permissions": perms,
                        })
                finally:
                    self._ssh_from_omnia_core(
                        control_plane_host,
                        NFS_CMD_TEMPLATES["umount_cleanup"].format(mount_point=mount_point),
                    )

            if errors:
                return False, NFS_DIR_CHECK_FAILED.format(
                    failed=len(errors), total=len(nfs_pvs), errors="; ".join(errors),
                ), dir_results

            return True, NFS_DIR_CHECK_PASSED.format(count=len(nfs_pvs)), dir_results

        except Exception as e:
            return False, NFS_DIR_ERROR.format(error=str(e)), []

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
                return False, ERR_NO_NODES_IN_PXE

            control_plane = self._get_control_plane_node(nodes)
            control_plane_host = control_plane.get("hostname") or control_plane.get("admin_ip")

            if not control_plane_host:
                return False, ERR_NO_CONTROL_PLANE_HOST

            # Run kubectl get sc with output in JSON format
            rc, out, err = self._ssh_from_omnia_core(
                control_plane_host, K8S_CMD_TEMPLATES["get_sc_all_json"],
            )

            if rc != 0:
                return False, SC_GET_ERROR.format(error=err)

            try:
                sc_data = json.loads(out)
                if 'items' not in sc_data:
                    return False, SC_NONE_FOUND

                # Look for the specified storage class and check if it's default
                target_sc = None
                for sc in sc_data['items']:
                    if sc['metadata']['name'] == storage_class_name:
                        target_sc = sc
                        break

                if not target_sc:
                    return False, SC_NOT_FOUND.format(name=storage_class_name)

                # Check if it's the default storage class
                annotations = target_sc['metadata'].get('annotations', {})
                is_default = (
                    annotations.get(SC_DEFAULT_ANNOTATION) == 'true'
                    or annotations.get(SC_DEFAULT_ANNOTATION_BETA) == 'true'
                )

                if is_default:
                    return True, SC_IS_DEFAULT.format(name=storage_class_name)
                return False, SC_NOT_DEFAULT.format(name=storage_class_name)

            except json.JSONDecodeError as e:
                return False, SC_PARSE_ERROR.format(error=str(e))

        except Exception as e:
            return False, SC_VERIFY_ERROR.format(error=str(e))

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
        """Verify that all Persistent Volumes in the cluster are Bound and use the expected storage class.

        Args:
            expected_storage_class (str): The expected storageClassName for all PVs.

        Returns:
            tuple: (bool, str) - (True if all PVs pass validation, status message)
        """
        try:
            pxe_mapping = self.read_pxe_mapping_file()
            nodes = self.get_k8s_nodes_from_pxe(pxe_mapping)
            if not nodes:
                return False, "No nodes found in PXE mapping"

            control_plane = self._get_control_plane_node(nodes)
            control_plane_host = control_plane.get("hostname") or control_plane.get("admin_ip")
            if not control_plane_host:
                return False, "Control plane node has no hostname or IP address"

            rc, out, err = self._ssh_from_omnia_core(control_plane_host, "kubectl get pv -o json")
            if rc != 0:
                return False, f"Failed to get PVs: {err or out}"

            try:
                pvs_json = json.loads(out)
            except json.JSONDecodeError as e:
                return False, f"Failed to parse PV output: {str(e)}"

            items = pvs_json.get("items", [])
            if not items:
                return True, f"No Persistent Volumes found in the cluster (storageClass={expected_storage_class})"

            errors = []
            checked = 0
            for pv in items:
                name = pv.get("metadata", {}).get("name", "unknown")
                status = pv.get("status", {}).get("phase", "")
                storage_class = pv.get("spec", {}).get("storageClassName", "")
                capacity = pv.get("spec", {}).get("capacity", {}).get("storage", "")
                claim_ref = pv.get("spec", {}).get("claimRef") or {}
                claim = f"{claim_ref.get('namespace','')}/{claim_ref.get('name','')}" if claim_ref else ""

                # Skip PVs with no storage class (manually provisioned)
                if not storage_class:
                    continue

                checked += 1

                if status != "Bound":
                    errors.append(
                        f"PV {name} (claim: {claim}) is not Bound (current: {status})"
                    )

                if storage_class != expected_storage_class:
                    errors.append(
                        f"PV {name} (claim: {claim}) has storageClass={storage_class} (expected: {expected_storage_class}), capacity={capacity}"
                    )

            if not checked:
                return True, f"No PVs with storageClass found to validate (storageClass={expected_storage_class})"

            if errors:
                return False, (
                    f"PV validation failed ({len(errors)} issue(s) across {checked} PVs, "
                    f"expected storageClass={expected_storage_class}):\n"
                    + "\n".join(f"  - {e}" for e in errors)
                )

            return True, (
                f"All {checked} Persistent Volume(s) are Bound with storageClass={expected_storage_class}"
            )

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


    # =========================================================================
    # Per-node-type service checks
    # =========================================================================

    def _verify_service_on_node_type(self, service_name, node_type, display_name=None):
        """Verify a service is active on nodes of a specific type.

        Args:
            service_name: systemd service name
            node_type: 'control_plane' or 'worker'
            display_name: human-readable name for logging

        Returns:
            tuple: (success, message, details_list)
        """
        display_name = display_name or service_name
        if node_type == "control_plane":
            nodes = self.get_control_plane_nodes_from_pxe_mapping()
            type_label = "kube control plane"
        else:
            nodes = self.get_worker_nodes_from_pxe_mapping()
            type_label = "kube node"

        if not nodes:
            return False, f"No {type_label} nodes found in PXE mapping", []

        failures = []
        details = []
        for node in nodes:
            hostname = node.get("hostname") or node.get("admin_ip") or "<unknown>"
            is_active, target, out, err, unreachable = self.is_service_active_on_node(
                node, service_name,
            )
            if unreachable:
                details.append(f"{hostname}: SKIPPED (unreachable)")
                continue
            if is_active:
                details.append(f"{hostname}: active")
            else:
                details.append(f"{hostname}: NOT active (out={out!r}, err={err!r})")
                failures.append(hostname)

        if failures:
            msg = f"{display_name} is NOT active on {type_label} node(s): {', '.join(failures)}"
            return False, msg, details
        return True, f"{display_name} is active on all {type_label} nodes", details

    def verify_kubelet_active_on_control_planes(self):
        """Verify kubelet is active on all kube control plane nodes."""
        return self._verify_service_on_node_type(KUBELET_SERVICE, "control_plane", "kubelet")

    def verify_kubelet_active_on_kube_nodes(self):
        """Verify kubelet is active on all kube worker nodes."""
        return self._verify_service_on_node_type(KUBELET_SERVICE, "worker", "kubelet")

    def verify_crio_active_on_control_planes(self):
        """Verify crio/cri-o is active on all kube control plane nodes."""
        nodes = self.get_control_plane_nodes_from_pxe_mapping()
        if not nodes:
            return False, "No kube control plane nodes found in PXE mapping", []

        failures = []
        details = []
        for node in nodes:
            hostname = node.get("hostname") or node.get("admin_ip") or "<unknown>"
            crio_active, _, _, _, crio_unreach = self.is_service_active_on_node(node, CRIO_SERVICE)
            crio_o_active, _, _, _, crio_o_unreach = self.is_service_active_on_node(node, CRI_O_SERVICE)
            if crio_unreach and crio_o_unreach:
                details.append(f"{hostname}: SKIPPED (unreachable)")
                continue
            if crio_active or crio_o_active:
                svc = "crio" if crio_active else "cri-o"
                details.append(f"{hostname}: {svc} active")
            else:
                details.append(f"{hostname}: crio/cri-o NOT active")
                failures.append(hostname)

        if failures:
            return False, f"crio/cri-o is NOT active on control plane node(s): {', '.join(failures)}", details
        return True, "crio/cri-o is active on all kube control plane nodes", details

    def verify_crio_active_on_kube_nodes(self):
        """Verify crio/cri-o is active on all kube worker nodes."""
        nodes = self.get_worker_nodes_from_pxe_mapping()
        if not nodes:
            return False, "No kube worker nodes found in PXE mapping", []

        failures = []
        details = []
        for node in nodes:
            hostname = node.get("hostname") or node.get("admin_ip") or "<unknown>"
            crio_active, _, _, _, crio_unreach = self.is_service_active_on_node(node, CRIO_SERVICE)
            crio_o_active, _, _, _, crio_o_unreach = self.is_service_active_on_node(node, CRI_O_SERVICE)
            if crio_unreach and crio_o_unreach:
                details.append(f"{hostname}: SKIPPED (unreachable)")
                continue
            if crio_active or crio_o_active:
                svc = "crio" if crio_active else "cri-o"
                details.append(f"{hostname}: {svc} active")
            else:
                details.append(f"{hostname}: crio/cri-o NOT active")
                failures.append(hostname)

        if failures:
            return False, f"crio/cri-o is NOT active on kube node(s): {', '.join(failures)}", details
        return True, "crio/cri-o is active on all kube worker nodes", details

    def verify_chronyd_active_on_control_planes(self):
        """Verify chronyd is active on all kube control plane nodes."""
        return self._verify_service_on_node_type(CHRONYD_SERVICE, "control_plane", "chronyd")

    # =========================================================================
    # Per-node-type READY state checks
    # =========================================================================

    def _verify_nodes_ready_by_type(self, node_type):
        """Verify nodes of a specific type are in READY state.

        Args:
            node_type: 'control_plane' or 'worker'

        Returns:
            tuple: (success, message, details_list)
        """
        if node_type == "control_plane":
            pxe_nodes = self.get_control_plane_nodes_from_pxe_mapping()
            type_label = "kube control plane"
        else:
            pxe_nodes = self.get_worker_nodes_from_pxe_mapping()
            type_label = "kube node"

        if not pxe_nodes:
            return False, f"No {type_label} nodes found in PXE mapping", []

        # Get a control plane host to run kubectl
        control_planes = self.get_control_plane_nodes_from_pxe_mapping()
        if not control_planes:
            return False, "No control plane nodes found to run kubectl", []
        cp_host = (control_planes[0].get("hostname") or control_planes[0].get("admin_ip") or "").strip()
        if not cp_host:
            return False, "Control plane node has no hostname/admin_ip", []

        rc, out, err = self._ssh_from_omnia_core(cp_host, "kubectl get nodes --no-headers")
        if rc != 0:
            return False, f"Failed to run kubectl get nodes: {err}", []

        # Build map: node_name -> status
        node_status_map = {}
        for line in (out or "").splitlines():
            parts = line.split()
            if len(parts) >= 2:
                node_status_map[parts[0]] = parts[1]

        # Check each PXE node
        failures = []
        details = []
        for node in pxe_nodes:
            hostname = (node.get("hostname") or "").strip()
            admin_ip = (node.get("admin_ip") or "").strip()
            # Try to find in kubectl output
            status = node_status_map.get(hostname) or node_status_map.get(admin_ip)
            if status is None:
                details.append(f"{hostname or admin_ip}: NOT FOUND in cluster")
                failures.append(hostname or admin_ip)
            elif status == "Ready":
                details.append(f"{hostname or admin_ip}: Ready")
            else:
                details.append(f"{hostname or admin_ip}: {status}")
                failures.append(hostname or admin_ip)

        if failures:
            return False, f"Not all {type_label} nodes are in Ready state: {', '.join(failures)}", details
        return True, f"All {type_label} nodes are in Ready state", details

    def verify_control_plane_nodes_ready(self):
        """Verify all kube control plane nodes are in READY state."""
        return self._verify_nodes_ready_by_type("control_plane")

    def verify_kube_nodes_ready(self):
        """Verify all kube worker nodes are in READY state."""
        return self._verify_nodes_ready_by_type("worker")

    # =========================================================================
    # kubeadm version matches crio version
    # =========================================================================

    def verify_kubeadm_version_matches_crio(self):
        """Verify kubeadm is installed with same version as crio on control plane nodes.

        Returns:
            tuple: (success, message, details_list)
        """
        control_planes = self.get_control_plane_nodes_from_pxe_mapping()
        if not control_planes:
            return False, "No control plane nodes found in PXE mapping", []

        failures = []
        details = []
        reachable_count = 0

        for node in control_planes:
            hostname = (node.get("hostname") or node.get("admin_ip") or "").strip()
            if not hostname:
                continue

            # Get kubeadm version
            rc_ka, ka_out, ka_err = self._ssh_from_omnia_core(hostname, "kubeadm version -o short")
            if rc_ka != 0:
                # Check if it's an SSH/connectivity error (unreachable node)
                if "No route to host" in ka_err or "Connection refused" in ka_err or "Connection timed out" in ka_err:
                    details.append(f"{hostname}: SKIPPED (unreachable)")
                    continue
                details.append(f"{hostname}: kubeadm version failed ({ka_err})")
                failures.append(hostname)
                continue
            
            reachable_count += 1
            kubeadm_ver = (ka_out or "").strip()

            # Get crio version
            rc_cr, cr_out, cr_err = self._ssh_from_omnia_core(hostname, "crio --version 2>/dev/null || cri-o --version 2>/dev/null")
            if rc_cr != 0:
                details.append(f"{hostname}: crio version failed ({cr_err})")
                failures.append(hostname)
                continue

            # Parse crio version - e.g. "crio version 1.34.1"
            crio_ver = ""
            for line in (cr_out or "").splitlines():
                ver_match = re.search(r'(\d+\.\d+\.\d+)', line)
                if ver_match:
                    crio_ver = ver_match.group(1)
                    break

            # Parse kubeadm version - e.g. "v1.34.1"
            kubeadm_parsed = ""
            ka_match = re.search(r'v?(\d+\.\d+\.\d+)', kubeadm_ver)
            if ka_match:
                kubeadm_parsed = ka_match.group(1)

            if not kubeadm_parsed or not crio_ver:
                details.append(f"{hostname}: could not parse versions (kubeadm={kubeadm_ver!r}, crio={cr_out!r})")
                failures.append(hostname)
                continue

            if kubeadm_parsed == crio_ver:
                details.append(f"{hostname}: kubeadm={kubeadm_parsed}, crio={crio_ver} (match)")
            else:
                details.append(f"{hostname}: kubeadm={kubeadm_parsed}, crio={crio_ver} (MISMATCH)")
                failures.append(hostname)

        if reachable_count == 0:
            return False, "All control plane nodes are unreachable", details

        if failures:
            return False, f"kubeadm/crio version mismatch on: {', '.join(failures)}", details
        return True, "kubeadm version matches crio version on all reachable control plane nodes", details

    # =========================================================================
    # etcd member list
    # =========================================================================

    def verify_etcd_member_list(self):
        """Verify etcd member list from within an etcd pod.

        Returns:
            tuple: (success, message, output)
        """
        if self._testinfra_host is None:
            self._testinfra_host = get_testinfra_host()

        control_planes = self.get_control_plane_nodes_from_pxe_mapping()
        if not control_planes:
            return False, ERR_NO_CP_IN_PXE, ""

        admin_ips = self.get_control_plane_admin_ips_from_pxe_mapping()
        if not admin_ips:
            return False, ERR_NO_CP_ADMIN_IPS, ""

        watcher_ip = (control_planes[0].get("admin_ip") or "").strip()
        if not watcher_ip:
            return False, ERR_CP_MISSING_ADMIN_IP, ""

        # Get all etcd pods
        find_pods_cmd = K8S_CMD_TEMPLATES["find_etcd_pods"].format(namespace=ETCD_NAMESPACE)
        result = run_on_remote_node(self._testinfra_host, find_pods_cmd, watcher_ip)
        if result.rc != 0 or not result.stdout:
            return False, ETCD_PODS_FIND_FAILED.format(
                error=result.stderr or result.stdout,
            ), (result.stderr or result.stdout or "")

        etcd_pods = [line.strip().replace("pod/", "") for line in (result.stdout or "").splitlines() if line.strip()]
        if not etcd_pods:
            return False, ETCD_PODS_NONE_FOUND, result.stdout

        endpoints = ",".join([f"https://{ip}:{ETCD_PORT}" for ip in admin_ips])

        etcdctl_cmd = K8S_CMD_TEMPLATES["etcdctl_member_list"].format(
            endpoints=endpoints,
            cacert=ETCD_PKI_CACERT,
            cert=ETCD_PKI_CERT,
            key=ETCD_PKI_KEY,
        )

        # Try each etcd pod until one succeeds
        last_error = ""
        for etcd_pod in etcd_pods:
            exec_cmd = K8S_CMD_TEMPLATES["kubectl_exec_sh_c"].format(
                namespace=ETCD_NAMESPACE,
                pod=etcd_pod,
                cmd=f"'{etcdctl_cmd}'",
            )
            result = run_on_remote_node(self._testinfra_host, exec_cmd, watcher_ip)
            output = (result.stdout or "").strip() + ("\n" + (result.stderr or "").strip() if (result.stderr or "").strip() else "")

            if result.rc == 0:
                member_lines = [
                    line for line in (result.stdout or "").splitlines()
                    if line.strip() and "|" in line and "ID" not in line.upper() and "---" not in line
                ]
                expected_count = len(admin_ips)
                if len(member_lines) < expected_count:
                    return False, ETCD_MEMBER_COUNT_MISMATCH.format(
                        found=len(member_lines), expected=expected_count,
                    ), output
                return True, ETCD_MEMBER_LIST_PASSED.format(count=len(member_lines)), output
            else:
                last_error = f"Pod {etcd_pod}: {output}"

        return False, ETCD_MEMBER_LIST_FAILED.format(error=last_error), last_error

    # =========================================================================
    # kubectl get componentstatus
    # =========================================================================

    def verify_k8s_component_status(self):
        """Verify k8s cluster health using kubectl get componentstatus.

        Expected: controller-manager, scheduler, etcd-0 all Healthy.

        Returns:
            tuple: (success, message, output)
        """
        if self._testinfra_host is None:
            self._testinfra_host = get_testinfra_host()

        control_planes = self.get_control_plane_nodes_from_pxe_mapping()
        if not control_planes:
            return False, ERR_NO_CP_IN_PXE, ""

        cp_ip = (control_planes[0].get("admin_ip") or "").strip()
        if not cp_ip:
            return False, ERR_CP_MISSING_ADMIN_IP, ""

        result = run_on_remote_node(
            self._testinfra_host, K8S_CMD_TEMPLATES["get_component_status"], cp_ip,
        )
        if result.rc != 0:
            return False, f"kubectl get componentstatus failed: {result.stderr}", (result.stdout or "")

        output = (result.stdout or "").strip()
        if not output:
            return False, "No component status output received", ""

        unhealthy = []
        details = []
        for line in output.splitlines():
            parts = line.split()
            if len(parts) < 2:
                continue
            name = parts[0]
            status = parts[1]
            details.append(f"{name}: {status}")
            if status != "Healthy":
                unhealthy.append(name)

        full_output = (result.stdout or "") + ("\n" + (result.stderr or "") if result.stderr else "")

        if unhealthy:
            return False, f"Unhealthy components: {', '.join(unhealthy)}", full_output
        return True, "All k8s components are Healthy", full_output


    # =========================================================================
    # ETCD Leader and Consistency Verification
    # =========================================================================

    def verify_etcd_leader_and_consistency(self):
        """Verify etcd leader identification and consistency across all control plane nodes.

        Returns:
            Dict with keys:
                success (bool)
                message (str)
                leader_ip (str)
                members (list): List of dicts with member details
                raft_term (int)
                raft_index (int)
        """
        import shlex
        import json

        cp_nodes = self.get_control_plane_nodes_from_pxe_mapping()
        if not cp_nodes:
            return {
                "success": False,
                "message": ERR_NO_CP_IN_PXE,
                "leader_ip": "",
                "members": [],
            }

        # Build endpoints list from control plane admin IPs
        endpoints = []
        for node in cp_nodes:
            admin_ip = (node.get("admin_ip") or "").strip()
            if admin_ip:
                endpoints.append(f"https://{admin_ip}:{ETCD_PORT}")

        if not endpoints:
            return {
                "success": False,
                "message": ERR_NO_VALID_CP_IPS,
                "leader_ip": "",
                "members": [],
            }

        endpoints_str = ",".join(endpoints)
        watcher_host = (cp_nodes[0].get("hostname") or cp_nodes[0].get("admin_ip") or "").strip()
        if not watcher_host:
            return {
                "success": False,
                "message": ERR_CP_MISSING_HOST,
                "leader_ip": "",
                "members": [],
            }

        # Get etcd pods
        find_pods_inner = K8S_CMD_TEMPLATES["find_etcd_pods"].format(namespace=ETCD_NAMESPACE)
        find_pods_cmd = f"bash -lc {shlex.quote(find_pods_inner)}"
        rc, out, err = self._ssh_from_omnia_core(watcher_host, find_pods_cmd)
        if rc != 0 or not out:
            return {
                "success": False,
                "message": ETCD_PODS_FIND_FAILED.format(error=err or out),
                "leader_ip": "",
                "members": [],
            }

        etcd_pods = [line.strip().replace("pod/", "") for line in (out or "").splitlines() if line.strip()]
        if not etcd_pods:
            return {
                "success": False,
                "message": ETCD_PODS_NONE_FOUND,
                "leader_ip": "",
                "members": [],
            }

        # Run etcdctl endpoint status to get leader and consistency info
        etcd_cmd = K8S_CMD_TEMPLATES["etcdctl_endpoint_status"].format(
            endpoints=shlex.quote(endpoints_str),
            cacert=ETCD_PKI_CACERT,
            cert=ETCD_PKI_CERT,
            key=ETCD_PKI_KEY,
        )

        # Try each etcd pod until one succeeds
        last_error = ""
        for etcd_pod in etcd_pods:
            exec_inner = K8S_CMD_TEMPLATES["kubectl_exec_sh_lc"].format(
                namespace=ETCD_NAMESPACE,
                pod=shlex.quote(etcd_pod),
                cmd=shlex.quote(etcd_cmd),
            )
            exec_cmd = f"bash -lc {shlex.quote(exec_inner)}"
            rc, stdout, stderr = self._ssh_from_omnia_core(watcher_host, exec_cmd)

            if rc == 0 and stdout:
                break
            last_error = stderr or stdout
        else:
            return {
                "success": False,
                "message": ETCD_LEADER_FAILED_RUN.format(error=last_error),
                "leader_ip": "",
                "members": [],
            }

        # Parse JSON output
        try:
            members_data = json.loads(stdout)
        except json.JSONDecodeError as e:
            return {
                "success": False,
                "message": ETCD_LEADER_PARSE_FAILED.format(error=str(e)),
                "leader_ip": "",
                "members": [],
            }

        # Extract member info
        members = []
        leader_ip = ""
        raft_terms = set()
        raft_indices = []

        for member in members_data:
            endpoint = member.get("Endpoint", "")
            is_leader = member.get("Status", {}).get("leader") == member.get("Status", {}).get("header", {}).get("member_id")
            raft_term = member.get("Status", {}).get("header", {}).get("raft_term", 0)
            raft_index = member.get("Status", {}).get("raftIndex", 0)

            # Extract IP from endpoint
            member_ip = endpoint.replace("https://", "").replace(f":{ETCD_PORT}", "")

            members.append({
                "endpoint": endpoint,
                "ip": member_ip,
                "is_leader": is_leader,
                "raft_term": raft_term,
                "raft_index": raft_index,
            })

            if is_leader:
                leader_ip = member_ip

            raft_terms.add(raft_term)
            raft_indices.append(raft_index)

        # Verify consistency
        if len(raft_terms) != 1:
            return {
                "success": False,
                "message": f"Inconsistent RAFT terms across members: {raft_terms}",
                "leader_ip": leader_ip,
                "members": members,
            }

        # RAFT indices can differ slightly due to ongoing operations
        # Check that all indices are within a reasonable delta (e.g., 10)
        if raft_indices:
            min_index = min(raft_indices)
            max_index = max(raft_indices)
            index_delta = max_index - min_index
            if index_delta > 10:
                return {
                    "success": False,
                    "message": f"RAFT indices too far apart (delta={index_delta}): {sorted(set(raft_indices))}",
                    "leader_ip": leader_ip,
                    "members": members,
                }

        if not leader_ip:
            return {
                "success": False,
                "message": "No etcd leader found",
                "leader_ip": "",
                "members": members,
            }

        return {
            "success": True,
            "message": f"etcd leader identified ({leader_ip}) and consistency validated across all members",
            "leader_ip": leader_ip,
            "members": members,
            "raft_term": list(raft_terms)[0],
            "raft_index": raft_indices[0] if raft_indices else 0,
        }

    # =========================================================================
    # VIP Control-Plane Reboot Scenario
    # =========================================================================

    def reboot_vip_control_plane(self):
        """Find which control plane holds the VIP and reboot it.

        Returns:
            Dict with keys:
                success (bool)
                message (str)
                virtual_ip (str)        - the HA virtual IP
                vip_node (dict)         - {hostname, admin_ip} of rebooted node
                remaining_nodes (list)  - other CP nodes
                watcher_host (str)      - hostname/IP of a remaining CP for kubectl
        """
        try:
            virtual_ip = self.get_virtual_ip_from_config()
        except Exception as e:
            return {"success": False, "message": str(e)}

        cp_nodes = self.get_control_plane_nodes_from_pxe_mapping()
        if not cp_nodes:
            return {"success": False, "message": HA_NO_CONTROL_PLANE_NODES}

        vip_node = None
        remaining_nodes = []
        for node in cp_nodes:
            node_ip = (node.get("admin_ip") or "").strip()
            if not node_ip:
                continue
            try:
                has_vip, _ = self.is_virtual_ip_configured(node_ip, virtual_ip)
            except Exception:
                has_vip = False
            if has_vip:
                vip_node = node
            else:
                remaining_nodes.append(node)

        if vip_node is None:
            return {
                "success": False,
                "message": REBOOT_VIP_NODE_NOT_FOUND.format(vip=virtual_ip),
            }

        if not remaining_nodes:
            return {"success": False, "message": REBOOT_VIP_NO_REMAINING}

        vip_node_ip = (vip_node.get("admin_ip") or "").strip()
        vip_node_hostname = (vip_node.get("hostname") or vip_node_ip).strip()
        watcher_host = (
            remaining_nodes[0].get("hostname") or
            remaining_nodes[0].get("admin_ip") or ""
        ).strip()

        reboot_cmd = "nohup sh -c 'sleep 2; reboot' >/dev/null 2>&1 &"
        self._ssh_from_omnia_core(vip_node_ip, reboot_cmd)

        return {
            "success": True,
            "message": REBOOT_VIP_NODE_INITIATED.format(
                node=vip_node_hostname, ip=vip_node_ip,
            ),
            "virtual_ip": virtual_ip,
            "vip_node": vip_node,
            "remaining_nodes": remaining_nodes,
            "watcher_host": watcher_host,
        }

    def wait_for_node_online_via_omnia_core(
        self, node_ip, hostname, timeout=None, poll=None,
    ):
        """Poll SSH (via omnia_core) until the node comes back online after reboot.

        Returns:
            Dict with success, elapsed, message, error.
        """
        timeout = K8S_REBOOT_WAIT_ONLINE_TIMEOUT if timeout is None else int(timeout)
        poll = K8S_REBOOT_WAIT_ONLINE_POLL if poll is None else int(poll)
        start = time.time()
        while time.time() - start < timeout:
            time.sleep(poll)
            rc, out, _ = self._ssh_from_omnia_core(node_ip, "echo online")
            if rc == 0 and "online" in out:
                elapsed = int(time.time() - start)
                return {
                    "success": True,
                    "elapsed": elapsed,
                    "message": K8S_NODE_ONLINE_PASSED.format(
                        node=hostname, ip=node_ip, elapsed=elapsed,
                    ),
                    "error": "",
                }
        elapsed = int(time.time() - start)
        return {
            "success": False,
            "elapsed": elapsed,
            "message": K8S_NODE_ONLINE_FAILED.format(
                node=hostname, ip=node_ip, timeout=timeout,
            ),
            "error": f"Node {hostname} ({node_ip}) did not respond within {timeout}s",
        }

    def verify_cloud_init_on_node(self, node_ip, hostname, timeout=None, poll=None):
        """Verify cloud-init completed successfully on a node after reboot.

        Polls /var/log/cloud-init-output.log until the success string appears
        or the timeout is reached.

        Returns:
            Dict with success, message, log_tail, error.
        """
        timeout = K8S_CLOUD_INIT_TIMEOUT if timeout is None else int(timeout)
        poll = K8S_CLOUD_INIT_POLL if poll is None else int(poll)
        start = time.time()
        while time.time() - start < timeout:
            time.sleep(poll)
            rc, out, _ = self._ssh_from_omnia_core(
                node_ip,
                "grep 'Cloud-Init finished successfully after the reboot' "
                "/var/log/cloud-init-output.log 2>/dev/null",
            )
            if rc == 0 and "Cloud-Init finished successfully after the reboot" in out:
                return {
                    "success": True,
                    "message": K8S_CLOUD_INIT_PASSED.format(node=hostname, ip=node_ip),
                    "log_tail": out.strip(),
                    "error": "",
                }
        rc, out, _ = self._ssh_from_omnia_core(
            node_ip, "tail -50 /var/log/cloud-init-output.log 2>/dev/null",
        )
        log_tail = out.strip() if rc == 0 else "log file not accessible"
        return {
            "success": False,
            "message": K8S_CLOUD_INIT_FAILED.format(
                node=hostname, ip=node_ip, timeout=timeout,
            ),
            "log_tail": log_tail,
            "error": (
                f"cloud-init did not complete within {timeout}s on {hostname}. "
                f"Last 50 lines of log:\n{log_tail}"
            ),
        }

    def wait_for_node_ready_after_reboot(self, node, watcher_host, timeout=None, poll=None):
        """Wait for a control plane node to return to Ready state in kubectl.

        Args:
            node (dict): {hostname, admin_ip} of the rebooted node
            watcher_host (str): hostname/IP of a remaining CP to run kubectl from
            timeout (int): seconds to wait
            poll (int): poll interval in seconds

        Returns:
            tuple (success: bool, message: str)
        """
        timeout = K8S_NODE_READY_TIMEOUT if timeout is None else int(timeout)
        poll = K8S_NODE_READY_POLL if poll is None else int(poll)
        node_hostname = (node.get("hostname") or "").strip()
        node_ip = (node.get("admin_ip") or "").strip()
        identity = node_hostname or node_ip

        last_status = "Unknown"
        start = time.time()
        while time.time() - start < timeout:
            time.sleep(poll)
            rc, out, _ = self._ssh_from_omnia_core(
                watcher_host, "kubectl get nodes --no-headers",
            )
            if rc != 0:
                continue
            for line in (out or "").splitlines():
                parts = line.split()
                if len(parts) < 2:
                    continue
                name, status = parts[0], parts[1]
                if identity and (name == identity or identity in name):
                    last_status = status
                    if status == "Ready":
                        return True, K8S_NODE_READY_PASSED.format(node=identity)
        return False, K8S_NODE_READY_FAILED.format(
            node=identity, timeout=timeout, status=last_status,
        )

    def verify_vip_failover_to_remaining_nodes(
        self, virtual_ip, original_node_ip, remaining_nodes, timeout=None, poll=None,
    ):
        """Verify the VIP has moved to one of the remaining control plane nodes.

        Args:
            virtual_ip (str): The HA virtual IP address to watch
            original_node_ip (str): admin_ip of the rebooted node (for display)
            remaining_nodes (list): List of {hostname, admin_ip} dicts
            timeout (int): seconds to wait
            poll (int): poll interval in seconds

        Returns:
            tuple (success: bool, message: str, new_vip_holder: dict or None)
        """
        timeout = K8S_VIP_FAILOVER_TIMEOUT if timeout is None else int(timeout)
        poll = K8S_VIP_FAILOVER_POLL if poll is None else int(poll)
        start = time.time()
        while time.time() - start < timeout:
            time.sleep(poll)
            holders = []
            for node in remaining_nodes:
                node_ip = (node.get("admin_ip") or "").strip()
                if not node_ip:
                    continue
                try:
                    has_vip, _ = self.is_virtual_ip_configured(node_ip, virtual_ip)
                    if has_vip:
                        holders.append(node)
                except Exception:
                    pass

            if len(holders) == 1:
                holder = holders[0]
                new_ip = (holder.get("admin_ip") or "").strip()
                new_name = (holder.get("hostname") or new_ip).strip()
                return True, K8S_VIP_FAILOVER_PASSED.format(
                    vip=virtual_ip,
                    old_node=original_node_ip,
                    new_node=new_name,
                    new_ip=new_ip,
                ), holder

            if len(holders) > 1:
                names = [n.get("hostname") or n.get("admin_ip") for n in holders]
                return False, K8S_VIP_FAILOVER_MULTI.format(
                    vip=virtual_ip, nodes=", ".join(names),
                ), None

        return False, K8S_VIP_FAILOVER_FAILED.format(
            vip=virtual_ip, timeout=timeout,
        ), None

    # =========================================================================
    # High-Level Reboot Scenario Wrappers (with cloud-init verification)
    # =========================================================================

    def verify_control_plane_reboot_scenario(self, max_wait_seconds: int = 600, poll_seconds: int = 10):
        """Reboot a control plane node and verify it returns to Ready with cloud-init success.

        Returns:
            tuple (success: bool, message: str) or (None, skip_reason)
        """
        control_planes = self.get_control_plane_nodes_from_pxe_mapping()
        if len(control_planes) < 2:
            return None, "Less than two control-plane nodes found in PXE mapping"

        reboot_node = control_planes[0]
        watcher_node = control_planes[1]

        reboot_host = (reboot_node.get("hostname") or reboot_node.get("admin_ip") or "").strip()
        watcher_host = (watcher_node.get("hostname") or watcher_node.get("admin_ip") or "").strip()

        if not reboot_host or not watcher_host:
            return False, "Control-plane nodes are missing hostname/admin_ip in PXE mapping"

        reboot_node_ip = (reboot_node.get("admin_ip") or "").strip()
        if not reboot_node_ip:
            return False, "Reboot target node has no admin_ip"

        # Reboot the node
        reboot_cmd = "nohup sh -c 'sleep 2; reboot' >/dev/null 2>&1 &"
        self._ssh_from_omnia_core(reboot_node_ip, reboot_cmd)

        # Wait for node to come back online
        online_result = self.wait_for_node_online_via_omnia_core(reboot_node_ip, reboot_host)
        if not online_result["success"]:
            return False, f"Node did not come back online: {online_result['message']}"

        # Verify cloud-init completed
        cloud_init_result = self.verify_cloud_init_on_node(reboot_node_ip, reboot_host)
        if not cloud_init_result["success"]:
            return False, f"Cloud-init verification failed: {cloud_init_result['message']}"

        # Wait for node to be Ready
        success, message = self.wait_for_node_ready_after_reboot(reboot_node, watcher_host, timeout=max_wait_seconds, poll=poll_seconds)

        if success:
            return True, f"Control-plane reboot scenario passed: {reboot_host} returned to Ready within {max_wait_seconds}s"
        return False, f"Control-plane reboot scenario failed: {message}"

    def verify_worker_node_reboot_scenario(self, max_wait_seconds: int = 600, poll_seconds: int = 10):
        """Reboot a worker node and verify it returns to Ready with cloud-init success.

        Returns:
            tuple (success: bool, message: str) or (None, skip_reason)
        """
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

        reboot_node_ip = (reboot_node.get("admin_ip") or "").strip()
        if not reboot_node_ip:
            return False, "Reboot target node has no admin_ip"

        # Reboot the node
        reboot_cmd = "nohup sh -c 'sleep 2; reboot' >/dev/null 2>&1 &"
        self._ssh_from_omnia_core(reboot_node_ip, reboot_cmd)

        # Wait for node to come back online
        online_result = self.wait_for_node_online_via_omnia_core(reboot_node_ip, reboot_host)
        if not online_result["success"]:
            return False, f"Node did not come back online: {online_result['message']}"

        # Verify cloud-init completed
        cloud_init_result = self.verify_cloud_init_on_node(reboot_node_ip, reboot_host)
        if not cloud_init_result["success"]:
            return False, f"Cloud-init verification failed: {cloud_init_result['message']}"

        # Wait for node to be Ready
        success, message = self.wait_for_node_ready_after_reboot(reboot_node, watcher_host, timeout=max_wait_seconds, poll=poll_seconds)

        if success:
            return True, f"Worker reboot scenario passed: {reboot_host} returned to Ready within {max_wait_seconds}s"
        return False, f"Worker reboot scenario failed: {message}"

    def verify_vip_failover_scenario(self, max_wait_seconds: int = 600, poll_seconds: int = 5):
        """Reboot the VIP-holding control plane and verify VIP fails over with cloud-init verification.

        This function:
        1. Identifies which control plane holds the VIP
        2. Reboots that node
        3. Waits for node to come back online
        4. Verifies cloud-init completes successfully
        5. Waits for node to return to Ready state
        6. Verifies VIP has failed over to another control plane

        Returns:
            tuple (success: bool, message: str) or (None, skip_reason)
        """
        try:
            virtual_ip = self.get_virtual_ip_from_config()
        except Exception as e:
            return None, str(e)

        control_plane_nodes = self.get_control_plane_nodes()
        if not control_plane_nodes:
            return None, "No control-plane nodes found"

        if len(control_plane_nodes) < 2:
            return None, "Less than two control-plane nodes found"

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
        vip_node_hostname = (vip_node.get("hostname") or vip_node_ip).strip()
        if not vip_node_ip:
            return False, "VIP holder node has no admin_ip"

        remaining_nodes = [n for n in control_plane_nodes if (n.get("admin_ip") or "").strip() and (n.get("admin_ip") or "").strip() != vip_node_ip]
        if not remaining_nodes:
            return None, "No remaining control-plane nodes found for VIP failover verification"

        # Reboot the VIP holder
        reboot_cmd = "nohup sh -c 'sleep 2; reboot' >/dev/null 2>&1 &"
        self._ssh_from_omnia_core(vip_node_ip, reboot_cmd)

        # Wait for node to come back online
        online_result = self.wait_for_node_online_via_omnia_core(vip_node_ip, vip_node_hostname)
        if not online_result["success"]:
            return False, f"Node did not come back online: {online_result['message']}"

        # Verify cloud-init completed
        cloud_init_result = self.verify_cloud_init_on_node(vip_node_ip, vip_node_hostname)
        if not cloud_init_result["success"]:
            return False, f"Cloud-init verification failed: {cloud_init_result['message']}"

        # Wait for node to be Ready
        watcher_host = (remaining_nodes[0].get("hostname") or remaining_nodes[0].get("admin_ip") or "").strip()
        ready_success, ready_message = self.wait_for_node_ready_after_reboot(vip_node, watcher_host)
        if not ready_success:
            return False, f"Node did not return to Ready: {ready_message}"

        # Verify VIP failover
        vip_success, vip_message, new_holder = self.verify_vip_failover_to_remaining_nodes(
            virtual_ip=virtual_ip,
            original_node_ip=vip_node_ip,
            remaining_nodes=remaining_nodes,
            timeout=max_wait_seconds,
            poll=poll_seconds,
        )

        if vip_success:
            return True, vip_message
        return False, vip_message


def get_oim_operations(config_path=None):
    """Get an instance of OIMOperations.
        config_path (str, optional): Path to the user config file.

    Returns:
        OIMOperations: An instance of OIMOperations.
    """
    return OIMOperations(config_path=config_path)