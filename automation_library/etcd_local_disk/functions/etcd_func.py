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
etcd local disk operations for OMNIA test automation.

This module provides functions to verify etcd local disk setup
on Kubernetes control plane nodes.
"""

import csv
import io
import shlex
import subprocess
import time
import yaml

from paramiko import AutoAddPolicy, SSHClient
from paramiko.ssh_exception import (
    AuthenticationException,
    BadHostKeyException,
    NoValidConnectionsError,
    SSHException,
)
from automation_library.core import (
    is_local_execution,
    load_omnia_test_config,
    load_omnia_test_credentials,
)
from automation_library.etcd_local_disk.messages.etcd_msgs import (
    BOSS_CARD_CHECK_FAILED,
    BOSS_CARD_CHECK_PASSED,
    BOSS_CARD_DETECTED,
    BOSS_CARD_NOT_DETECTED,
    DISK_TYPE_CHECK_FAILED,
    DISK_TYPE_CHECK_PASSED,
    DISK_TYPE_DETECTED,
    DISK_TYPE_NOT_DETECTED,
    ETCD_CONFIG_CHECK_FAILED,
    ETCD_CONFIG_CHECK_PASSED,
    ETCD_LOCAL_DISK_DISABLED,
    ETCD_NOT_USING_LOCAL_DISK,
    ETCD_USING_LOCAL_DISK,
    FALLBACK_CHECK_FAILED,
    FALLBACK_CHECK_PASSED,
    FALLBACK_DISK_DETECTED,
    FALLBACK_DISK_NOT_DETECTED,
    FILESYSTEM_CHECK_FAILED,
    FILESYSTEM_CHECK_PASSED,
    FILESYSTEM_INVALID,
    FILESYSTEM_NOT_FOUND,
    FILESYSTEM_VALID,
    FIRST_BOOT_CHECK_FAILED,
    FIRST_BOOT_CHECK_PASSED,
    FIRST_BOOT_LOG_FAILED,
    FIRST_BOOT_LOG_MISSING,
    FIRST_BOOT_LOG_SUCCESS,
    FIRST_BOOT_SCRIPT_EXISTS,
    FIRST_BOOT_SCRIPT_MISSING,
    FSTAB_CHECK_FAILED,
    FSTAB_CHECK_PASSED,
    FSTAB_ENTRY_EXISTS,
    FSTAB_ENTRY_MISSING,
    FSTAB_UPDATE_LOG_FAILED,
    FSTAB_UPDATE_LOG_MISSING,
    FSTAB_UPDATE_LOG_SUCCESS,
    FSTAB_UPDATE_SCRIPT_EXISTS,
    FSTAB_UPDATE_SCRIPT_MISSING,
    MOUNT_ACTIVE,
    MOUNT_NOT_ACTIVE,
    NO_CONTROL_PLANE_NODES,
    PARTITION_CHECK_FAILED,
    PARTITION_CHECK_PASSED,
    PARTITION_EXISTS,
    PARTITION_IS_ROOT,
    PARTITION_NOT_FOUND,
    SUBSEQUENT_BOOT_CHECK_FAILED,
    SUBSEQUENT_BOOT_CHECK_PASSED,
    CLOUD_INIT_FAILED,
    CLOUD_INIT_PASSED,
    FSTAB_UPDATE_LOG_TIMESTAMP_STALE,
    FSTAB_UPDATE_LOG_TIMESTAMP_VALID,
    NODE_ONLINE_FAILED,
    NODE_ONLINE_PASSED,
    REBOOT_NODE_INITIATED,
    REBOOT_NODE_NOT_FOUND,
    REBOOT_NO_REMAINING_NODES,
    SUBSEQUENT_BOOT_POST_REBOOT_FAILED,
    SUBSEQUENT_BOOT_POST_REBOOT_PASSED,
)
from automation_library.etcd_local_disk.vars.etcd_vars import (
    BOSS_LSPCI_CMD,
    BOSS_MODEL_KEYWORDS,
    CONTROL_PLANE_GROUP,
    ETCD_DIR_PERMISSIONS,
    ETCD_DISK_SETUP_LOG,
    ETCD_DISK_SETUP_SCRIPT,
    ETCD_FSTAB_UPDATE_LOG,
    ETCD_FSTAB_UPDATE_SCRIPT,
    ETCD_GROUP,
    ETCD_MOUNT_PATH,
    ETCD_ON_LOCAL_DISK_KEY,
    ETCD_USER,
    NFS_MOUNT_TYPE,
    OMNIA_CONFIG_FILE,
    SUPPORTED_FILESYSTEMS,
)

# Constants
OMNIA_CORE_CONTAINER_NAME = "omnia_core"
PXE_MAPPING_FILE_PATH = "/opt/omnia/input/project_default/pxe_mapping_file.csv"
OMNIA_CONFIG_PATH = "/opt/omnia/input/project_default/omnia_config.yml"

# Reboot timeouts
REBOOT_WAIT_ONLINE_TIMEOUT = 300  # seconds to wait for node to come back
REBOOT_WAIT_ONLINE_POLL = 10      # poll interval in seconds
CLOUD_INIT_TIMEOUT = 600          # seconds to wait for cloud-init
CLOUD_INIT_POLL = 15              # poll interval in seconds


class EtcdLocalDiskOperations:
    """Collection of etcd local disk validation helpers used by OMNIA automation."""

    def __init__(self, config_path=None):
        """Initialize with user configuration.

        Args:
            config_path (str, optional): Path to the user config file.
                Defaults to standard config path. This parameter is kept
                for compatibility but is not used as config is loaded
                from standard locations.
        """
        self.config = self._load_config()
        self.ssh_client = None
        self._omnia_core_container_id = None
        self._local_mode = is_local_execution()

    def _load_config(self):
        """Load configuration from user config file and credentials file."""
        # Load main config (non-sensitive settings)
        config = load_omnia_test_config()
        # Load credentials (sensitive settings with vault decryption)
        credentials = load_omnia_test_credentials()
        # Merge credentials into config
        config.update(credentials)
        return config

    def connect_ssh(self):
        """Establish SSH connection to OIM server.

        In local mode (running on the OIM itself), this is a no-op.
        """
        if self._local_mode:
            return None

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
        except (
            AuthenticationException, BadHostKeyException,
            NoValidConnectionsError, SSHException, OSError,
        ) as e:
            try:
                if self.ssh_client is not None:
                    self.ssh_client.close()
            finally:
                self.ssh_client = None
            raise RuntimeError(
                f"Failed to establish SSH connection: {str(e)}"
            ) from e

    def close(self):
        """Close SSH connection."""
        if self.ssh_client:
            self.ssh_client.close()
            self.ssh_client = None

    def _get_omnia_core_container_id(self):
        """Get the omnia_core container ID."""
        if self._omnia_core_container_id:
            return self._omnia_core_container_id
        cmd = (
            f"podman ps --filter 'name={OMNIA_CORE_CONTAINER_NAME}'"
            " --format '{{.ID}}'"
        )
        
        if self._local_mode:
            # Run command locally
            result = subprocess.run(
                cmd, shell=True, capture_output=True, text=True, check=True
            )
            container_id = result.stdout.strip()
        else:
            # Run command via SSH
            self.connect_ssh()
            _stdin, stdout, stderr = self.ssh_client.exec_command(cmd)
            stdout.channel.recv_exit_status()
            container_id = stdout.read().decode('utf-8').strip()
        
        if not container_id:
            raise RuntimeError(
                f"Container '{OMNIA_CORE_CONTAINER_NAME}' not found"
            )
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

        if self._local_mode:
            # Run command locally
            result = subprocess.run(
                wrapped, shell=True, capture_output=True, text=True
            )
            exit_code = result.returncode
            out = result.stdout.strip()
            err = result.stderr.strip()
        else:
            # Run command via SSH
            if not self.ssh_client:
                self.connect_ssh()

            _stdin, stdout, stderr = self.ssh_client.exec_command(wrapped)
            exit_code = stdout.channel.recv_exit_status()
            out = stdout.read().decode('utf-8').strip()
            err = stderr.read().decode('utf-8').strip()

        if check and exit_code != 0:
            raise RuntimeError(
                f"Command failed with exit code {exit_code}: {err}"
            )

        return exit_code, out, err

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
            "ssh -o BatchMode=yes -o StrictHostKeyChecking=no"
            " -o UserKnownHostsFile=/dev/null"
            f" -o ConnectTimeout={connect_timeout} -p {ssh_port}"
            f" {ssh_user}@{host} {shlex.quote(remote_cmd)}"
        )
        return self._run_in_omnia_core(ssh_cmd, check=False)

    # =========================================================================
    # PXE MAPPING HELPERS
    # =========================================================================

    def read_pxe_mapping_file(self):
        """Read pxe_mapping_file from omnia_core container."""
        container_id = self._get_omnia_core_container_id()
        read_cmd = f"podman exec {container_id} cat {PXE_MAPPING_FILE_PATH}"
        
        if self._local_mode:
            # Run command locally
            result = subprocess.run(
                read_cmd, shell=True, capture_output=True, text=True, check=True
            )
            out = result.stdout.strip()
        else:
            # Run command via SSH
            self.connect_ssh()
            _stdin, stdout, stderr = self.ssh_client.exec_command(read_cmd)
            exit_code = stdout.channel.recv_exit_status()
            out = stdout.read().decode('utf-8').strip()
            err = stderr.read().decode('utf-8').strip()
            if exit_code != 0:
                raise RuntimeError(f"Error reading pxe_mapping_file: {err}")
        
        return out

    def get_control_plane_nodes(self):
        """Get all control plane nodes from PXE mapping.

        Returns:
            list: List of dicts with 'hostname' and 'admin_ip'.
        """
        pxe_mapping = self.read_pxe_mapping_file()
        reader = csv.DictReader(io.StringIO(pxe_mapping))
        nodes = []
        for row in reader:
            fg = (row.get("FUNCTIONAL_GROUP_NAME") or "").strip()
            if fg == CONTROL_PLANE_GROUP:
                hostname = (row.get("HOSTNAME") or "").strip()
                admin_ip = (row.get("ADMIN_IP") or "").strip()
                if hostname or admin_ip:
                    nodes.append({
                        "hostname": hostname,
                        "admin_ip": admin_ip,
                    })
        return nodes

    def get_control_plane_admin_ips(self):
        """Get admin IPs of all control plane nodes."""
        nodes = self.get_control_plane_nodes()
        return [
            n["admin_ip"] for n in nodes
            if (n.get("admin_ip") or "").strip()
        ]

    def _get_node_target(self, node):
        """Get the SSH target for a node (hostname or admin_ip)."""
        return (
            node.get("hostname") or node.get("admin_ip") or ""
        ).strip()

    # =========================================================================
    # OMNIA CONFIG HELPERS
    # =========================================================================

    def is_etcd_on_local_disk_enabled(self):
        """Check if etcd_on_local_disk is enabled in omnia_config.yml.

        Returns:
            tuple: (bool, str) - (True if enabled, status message)
        """
        rc, out, err = self._run_in_omnia_core(
            f"cat {OMNIA_CONFIG_PATH}", check=False,
        )
        if rc != 0:
            return False, f"Failed to read {OMNIA_CONFIG_PATH}: {err}"

        try:
            omnia_config = yaml.safe_load(out)
        except yaml.YAMLError as e:
            return False, f"Failed to parse {OMNIA_CONFIG_PATH}: {e}"

        clusters = omnia_config.get("service_k8s_cluster", [])
        if not clusters:
            return False, "No service_k8s_cluster found in omnia_config.yml"

        enabled = clusters[0].get(ETCD_ON_LOCAL_DISK_KEY, False)
        if isinstance(enabled, str):
            enabled = enabled.lower() in ("true", "yes", "1")

        return enabled, (
            f"{ETCD_ON_LOCAL_DISK_KEY}={enabled} in omnia_config.yml"
        )

    # =========================================================================
    # TC-F01: BOSS CARD DETECTION
    # =========================================================================

    def verify_boss_card_detection(self):
        """Verify Dell BOSS card detection via PCI scan on control plane nodes.

        Returns:
            tuple: (success, message, details)
        """
        nodes = self.get_control_plane_nodes()
        if not nodes:
            return False, NO_CONTROL_PLANE_NODES, None

        details_lines = []
        all_detected = True

        for node in nodes:
            target = self._get_node_target(node)
            if not target:
                continue

            rc, out, err = self._ssh_from_omnia_core(target, BOSS_LSPCI_CMD)
            boss_found = False
            if rc == 0 and out.strip():
                for keyword in BOSS_MODEL_KEYWORDS:
                    if keyword.lower() in out.lower():
                        boss_found = True
                        break

            if boss_found:
                msg = BOSS_CARD_DETECTED.format(
                    node=target, details=out.strip().split('\n')[0],
                )
                details_lines.append(f"  [PASS] {msg}")
            else:
                msg = BOSS_CARD_NOT_DETECTED.format(node=target)
                details_lines.append(f"  [INFO] {msg}")
                all_detected = False

        details = "\n".join(details_lines)

        if all_detected:
            return True, BOSS_CARD_CHECK_PASSED, details

        return (
            False,
            BOSS_CARD_CHECK_FAILED.format(
                message="BOSS card not detected on one or more nodes",
            ),
            details,
        )

    # =========================================================================
    # TC-F03: DISK PARTITIONING FOR ETCD
    # =========================================================================

    def verify_disk_partitioning(self):
        """Verify GPT partition exists for etcd data, excluding root disk.

        Returns:
            tuple: (success, message, details)
        """
        nodes = self.get_control_plane_nodes()
        if not nodes:
            return False, NO_CONTROL_PLANE_NODES, None

        details_lines = []
        all_valid = True

        for node in nodes:
            target = self._get_node_target(node)
            if not target:
                continue

            # Get root disk
            rc, root_disk, _ = self._ssh_from_omnia_core(
                target,
                "lsblk -no PKNAME $(findmnt -no SOURCE /) 2>/dev/null | head -1",
            )
            root_disk = (root_disk or "").strip()

            # Get the disk backing /var/lib/etcd
            rc, mount_src, _ = self._ssh_from_omnia_core(
                target,
                f"findmnt -no SOURCE {ETCD_MOUNT_PATH} 2>/dev/null",
            )
            mount_src = (mount_src or "").strip()

            if not mount_src:
                msg = PARTITION_NOT_FOUND.format(node=target)
                details_lines.append(f"  [FAIL] {msg}")
                all_valid = False
                continue

            # Verify it is not the root disk
            rc, part_parent, _ = self._ssh_from_omnia_core(
                target,
                f"lsblk -no PKNAME {mount_src} 2>/dev/null | head -1",
            )
            part_parent = (part_parent or "").strip()

            if part_parent and root_disk and part_parent == root_disk:
                msg = PARTITION_IS_ROOT.format(node=target)
                details_lines.append(f"  [FAIL] {msg}")
                all_valid = False
                continue

            # Verify GPT partition table
            parent_disk = f"/dev/{part_parent}" if part_parent else mount_src
            rc, pttype, _ = self._ssh_from_omnia_core(
                target,
                f"blkid -o value -s PTTYPE {parent_disk} 2>/dev/null",
            )
            pttype = (pttype or "").strip().lower()

            if pttype == "gpt":
                msg = PARTITION_EXISTS.format(
                    node=target, partition=mount_src,
                )
                details_lines.append(f"  [PASS] {msg}")
            else:
                msg = PARTITION_NOT_FOUND.format(node=target)
                details_lines.append(
                    f"  [FAIL] {msg} (partition table: {pttype or 'unknown'})"
                )
                all_valid = False

        details = "\n".join(details_lines)

        if all_valid:
            return True, PARTITION_CHECK_PASSED, details

        return (
            False,
            PARTITION_CHECK_FAILED.format(
                message="Partition verification failed on one or more nodes",
            ),
            details,
        )

    # =========================================================================
    # TC-F04: FILESYSTEM CREATION
    # =========================================================================

    def verify_filesystem_creation(self):
        """Verify ext4/xfs filesystem on etcd partition.

        Returns:
            tuple: (success, message, details)
        """
        nodes = self.get_control_plane_nodes()
        if not nodes:
            return False, NO_CONTROL_PLANE_NODES, None

        details_lines = []
        all_valid = True

        for node in nodes:
            target = self._get_node_target(node)
            if not target:
                continue

            rc, mount_src, _ = self._ssh_from_omnia_core(
                target,
                f"findmnt -no SOURCE {ETCD_MOUNT_PATH} 2>/dev/null",
            )
            mount_src = (mount_src or "").strip()

            if not mount_src:
                msg = FILESYSTEM_NOT_FOUND.format(node=target)
                details_lines.append(f"  [FAIL] {msg}")
                all_valid = False
                continue

            rc, fstype, _ = self._ssh_from_omnia_core(
                target,
                f"blkid -o value -s TYPE {mount_src} 2>/dev/null",
            )
            fstype = (fstype or "").strip().lower()

            if fstype in SUPPORTED_FILESYSTEMS:
                msg = FILESYSTEM_VALID.format(
                    node=target, fstype=fstype, partition=mount_src,
                )
                details_lines.append(f"  [PASS] {msg}")
            else:
                msg = FILESYSTEM_INVALID.format(
                    node=target, fstype=fstype or "none",
                )
                details_lines.append(f"  [FAIL] {msg}")
                all_valid = False

        details = "\n".join(details_lines)

        if all_valid:
            return True, FILESYSTEM_CHECK_PASSED, details

        return (
            False,
            FILESYSTEM_CHECK_FAILED.format(
                message="Filesystem verification failed on one or more nodes",
            ),
            details,
        )

    # =========================================================================
    # TC-F05: FSTAB UPDATE AND MOUNT
    # =========================================================================

    def verify_fstab_and_mount(self, target_node=None):
        """Verify UUID-based fstab entry and active mount for /var/lib/etcd.

        Args:
            target_node (str, optional): Hostname or IP of a specific node to
                verify. When provided, only that node is checked instead of all
                control plane nodes.

        Returns:
            tuple: (success, message, details)
        """
        if target_node:
            nodes = [{"hostname": target_node, "admin_ip": target_node}]
        else:
            nodes = self.get_control_plane_nodes()
        if not nodes:
            return False, NO_CONTROL_PLANE_NODES, None

        details_lines = []
        all_valid = True

        for node in nodes:
            target = self._get_node_target(node)
            if not target:
                continue

            # Check fstab for UUID-based entry
            rc, fstab_out, _ = self._ssh_from_omnia_core(
                target,
                f"grep '{ETCD_MOUNT_PATH}' /etc/fstab 2>/dev/null",
            )
            fstab_out = (fstab_out or "").strip()

            has_uuid_entry = False
            if fstab_out:
                for line in fstab_out.splitlines():
                    if "UUID=" in line and ETCD_MOUNT_PATH in line:
                        has_uuid_entry = True
                        break

            if has_uuid_entry:
                msg = FSTAB_ENTRY_EXISTS.format(
                    mount=ETCD_MOUNT_PATH, node=target,
                )
                details_lines.append(f"  [PASS] {msg}")
            else:
                msg = FSTAB_ENTRY_MISSING.format(
                    mount=ETCD_MOUNT_PATH, node=target,
                )
                details_lines.append(f"  [FAIL] {msg}")
                all_valid = False

            # Check mount is active
            rc, _, _ = self._ssh_from_omnia_core(
                target,
                f"mountpoint -q {ETCD_MOUNT_PATH}",
            )
            if rc == 0:
                msg = MOUNT_ACTIVE.format(
                    mount=ETCD_MOUNT_PATH, node=target,
                )
                details_lines.append(f"  [PASS] {msg}")
            else:
                msg = MOUNT_NOT_ACTIVE.format(
                    mount=ETCD_MOUNT_PATH, node=target,
                )
                details_lines.append(f"  [FAIL] {msg}")
                all_valid = False

        details = "\n".join(details_lines)

        if all_valid:
            return True, FSTAB_CHECK_PASSED, details

        return (
            False,
            FSTAB_CHECK_FAILED.format(
                message="fstab/mount verification failed on one or more nodes",
            ),
            details,
        )

    # =========================================================================
    # TC-F06: ETCD CONFIGURATION TO LOCAL DISK
    # =========================================================================

    def verify_etcd_using_local_disk(self, target_node=None):
        """Verify etcd is using local disk at /var/lib/etcd (not NFS).

        Args:
            target_node (str, optional): Hostname or IP of a specific node to
                verify. When provided, only that node is checked instead of all
                control plane nodes.

        Returns:
            tuple: (success, message, details)
        """
        if target_node:
            nodes = [{"hostname": target_node, "admin_ip": target_node}]
        else:
            nodes = self.get_control_plane_nodes()
        if not nodes:
            return False, NO_CONTROL_PLANE_NODES, None

        details_lines = []
        all_valid = True

        for node in nodes:
            target = self._get_node_target(node)
            if not target:
                continue

            # Check mount type for /var/lib/etcd
            rc, fstype, _ = self._ssh_from_omnia_core(
                target,
                f"findmnt -no FSTYPE {ETCD_MOUNT_PATH} 2>/dev/null",
            )
            fstype = (fstype or "").strip().lower()

            if fstype and fstype != NFS_MOUNT_TYPE:
                msg = ETCD_USING_LOCAL_DISK.format(
                    mount=ETCD_MOUNT_PATH, node=target,
                )
                details_lines.append(f"  [PASS] {msg}")
            else:
                reason = f"mount type is '{fstype}'" if fstype else "not mounted"
                msg = ETCD_NOT_USING_LOCAL_DISK.format(
                    node=target, details=reason,
                )
                details_lines.append(f"  [FAIL] {msg}")
                all_valid = False

            # Verify etcd user/permissions
            rc, owner, _ = self._ssh_from_omnia_core(
                target,
                f"stat -c '%U:%G' {ETCD_MOUNT_PATH} 2>/dev/null",
            )
            owner = (owner or "").strip()

            rc, perms, _ = self._ssh_from_omnia_core(
                target,
                f"stat -c '%a' {ETCD_MOUNT_PATH} 2>/dev/null",
            )
            perms = (perms or "").strip()

            expected_owner = f"{ETCD_USER}:{ETCD_GROUP}"
            if owner == expected_owner and perms == ETCD_DIR_PERMISSIONS:
                details_lines.append(
                    f"  [PASS] Permissions correct on {target}:"
                    f" {owner} {perms}"
                )
            else:
                details_lines.append(
                    f"  [FAIL] Permissions incorrect on {target}:"
                    f" owner={owner} (expected {expected_owner}),"
                    f" perms={perms} (expected {ETCD_DIR_PERMISSIONS})"
                )
                all_valid = False

        details = "\n".join(details_lines)

        if all_valid:
            return True, ETCD_CONFIG_CHECK_PASSED, details

        return (
            False,
            ETCD_CONFIG_CHECK_FAILED.format(
                message="etcd local disk config check failed on one or more nodes",
            ),
            details,
        )

    # =========================================================================
    # TC-F07: FALLBACK DISK DETECTION
    # =========================================================================

    def verify_fallback_disk_detection(self):
        """Verify fallback to available disk when BOSS card not detected.

        Returns:
            tuple: (success, message, details)
        """
        nodes = self.get_control_plane_nodes()
        if not nodes:
            return False, NO_CONTROL_PLANE_NODES, None

        details_lines = []
        all_valid = True

        for node in nodes:
            target = self._get_node_target(node)
            if not target:
                continue

            # Check if BOSS card is present
            rc, out, _ = self._ssh_from_omnia_core(target, BOSS_LSPCI_CMD)
            boss_found = False
            if rc == 0 and out.strip():
                for keyword in BOSS_MODEL_KEYWORDS:
                    if keyword.lower() in out.lower():
                        boss_found = True
                        break

            if boss_found:
                details_lines.append(
                    f"  [INFO] BOSS card detected on {target}"
                    " - fallback not needed"
                )
                continue

            # BOSS not detected, verify fallback disk is in use
            rc, mount_src, _ = self._ssh_from_omnia_core(
                target,
                f"findmnt -no SOURCE {ETCD_MOUNT_PATH} 2>/dev/null",
            )
            mount_src = (mount_src or "").strip()

            if mount_src:
                # Verify it's not the root disk
                rc, root_disk, _ = self._ssh_from_omnia_core(
                    target,
                    "lsblk -no PKNAME $(findmnt -no SOURCE /)"
                    " 2>/dev/null | head -1",
                )
                root_disk = (root_disk or "").strip()

                rc, part_parent, _ = self._ssh_from_omnia_core(
                    target,
                    f"lsblk -no PKNAME {mount_src}"
                    " 2>/dev/null | head -1",
                )
                part_parent = (part_parent or "").strip()

                if part_parent and root_disk and part_parent == root_disk:
                    msg = PARTITION_IS_ROOT.format(node=target)
                    details_lines.append(f"  [FAIL] {msg}")
                    all_valid = False
                else:
                    msg = FALLBACK_DISK_DETECTED.format(
                        node=target, disk=mount_src,
                    )
                    details_lines.append(f"  [PASS] {msg}")
            else:
                msg = FALLBACK_DISK_NOT_DETECTED.format(node=target)
                details_lines.append(f"  [FAIL] {msg}")
                all_valid = False

        details = "\n".join(details_lines)

        if all_valid:
            return (
                True,
                FALLBACK_CHECK_PASSED.format(node="all control plane nodes"),
                details,
            )

        return (
            False,
            FALLBACK_CHECK_FAILED.format(
                message="Fallback disk check failed on one or more nodes",
            ),
            details,
        )

    # =========================================================================
    # TC-F08: FIRST BOOT DISK SETUP
    # =========================================================================

    def verify_first_boot_setup(self):
        """Verify etcd-disk-setup.sh execution on first boot.

        Returns:
            tuple: (success, message, details)
        """
        nodes = self.get_control_plane_nodes()
        if not nodes:
            return False, NO_CONTROL_PLANE_NODES, None

        details_lines = []
        all_valid = True

        for node in nodes:
            target = self._get_node_target(node)
            if not target:
                continue

            # Check script exists
            rc, _, _ = self._ssh_from_omnia_core(
                target, f"[ -f {ETCD_DISK_SETUP_SCRIPT} ]",
            )
            if rc == 0:
                msg = FIRST_BOOT_SCRIPT_EXISTS.format(node=target)
                details_lines.append(f"  [PASS] {msg}")
            else:
                msg = FIRST_BOOT_SCRIPT_MISSING.format(node=target)
                details_lines.append(f"  [FAIL] {msg}")
                all_valid = False

            # Check log exists and has success marker
            rc, _, _ = self._ssh_from_omnia_core(
                target, f"[ -f {ETCD_DISK_SETUP_LOG} ]",
            )
            if rc == 0:
                # First boot log exists - check for DONE marker
                rc, log_tail, _ = self._ssh_from_omnia_core(
                    target, f"tail -5 {ETCD_DISK_SETUP_LOG} 2>/dev/null",
                )
                log_tail = (log_tail or "").strip()

                if "DONE" in log_tail:
                    msg = FIRST_BOOT_LOG_SUCCESS.format(node=target)
                    details_lines.append(f"  [PASS] {msg}")
                else:
                    msg = FIRST_BOOT_LOG_FAILED.format(node=target)
                    details_lines.append(f"  [FAIL] {msg}")
                    all_valid = False
                continue

            # First boot log missing - check if subsequent boot log exists
            # (node was rebooted, cloud-init cleaned up first boot log)
            rc, _, _ = self._ssh_from_omnia_core(
                target, f"[ -f {ETCD_FSTAB_UPDATE_LOG} ]",
            )
            if rc == 0:
                rc, log_tail, _ = self._ssh_from_omnia_core(
                    target,
                    f"tail -5 {ETCD_FSTAB_UPDATE_LOG} 2>/dev/null",
                )
                log_tail = (log_tail or "").strip()

                if "DONE" in log_tail:
                    details_lines.append(
                        f"  [PASS] etcd-disk-setup.log not found on"
                        f" {target} (node was rebooted),"
                        f" but etcd-fstab-update.sh completed"
                        f" successfully — disk setup preserved"
                    )
                else:
                    details_lines.append(
                        f"  [FAIL] etcd-disk-setup.log not found on"
                        f" {target} and etcd-fstab-update.sh did not"
                        f" complete successfully"
                    )
                    all_valid = False
            else:
                msg = FIRST_BOOT_LOG_MISSING.format(node=target)
                details_lines.append(f"  [FAIL] {msg}")
                all_valid = False

        details = "\n".join(details_lines)

        if all_valid:
            return True, FIRST_BOOT_CHECK_PASSED, details

        return (
            False,
            FIRST_BOOT_CHECK_FAILED.format(
                message="First boot setup check failed on one or more nodes",
            ),
            details,
        )

    # =========================================================================
    # TC-F09: SUBSEQUENT BOOT FSTAB UPDATE
    # =========================================================================

    def verify_subsequent_boot_fstab_update(self):
        """Verify etcd-fstab-update.sh execution on subsequent boots.

        Returns:
            tuple: (success, message, details)
        """
        nodes = self.get_control_plane_nodes()
        if not nodes:
            return False, NO_CONTROL_PLANE_NODES, None

        details_lines = []
        all_valid = True

        for node in nodes:
            target = self._get_node_target(node)
            if not target:
                continue

            # Check script exists
            rc, _, _ = self._ssh_from_omnia_core(
                target, f"[ -f {ETCD_FSTAB_UPDATE_SCRIPT} ]",
            )
            if rc == 0:
                msg = FSTAB_UPDATE_SCRIPT_EXISTS.format(node=target)
                details_lines.append(f"  [PASS] {msg}")
            else:
                msg = FSTAB_UPDATE_SCRIPT_MISSING.format(node=target)
                details_lines.append(f"  [FAIL] {msg}")
                all_valid = False

            # Check log exists and has success marker
            rc, _, _ = self._ssh_from_omnia_core(
                target, f"[ -f {ETCD_FSTAB_UPDATE_LOG} ]",
            )
            if rc != 0:
                msg = FSTAB_UPDATE_LOG_MISSING.format(node=target)
                details_lines.append(f"  [FAIL] {msg}")
                all_valid = False
                continue

            rc, log_tail, _ = self._ssh_from_omnia_core(
                target, f"tail -5 {ETCD_FSTAB_UPDATE_LOG} 2>/dev/null",
            )
            log_tail = (log_tail or "").strip()

            if "DONE" in log_tail:
                msg = FSTAB_UPDATE_LOG_SUCCESS.format(node=target)
                details_lines.append(f"  [PASS] {msg}")
            else:
                msg = FSTAB_UPDATE_LOG_FAILED.format(node=target)
                details_lines.append(f"  [FAIL] {msg}")
                all_valid = False

        details = "\n".join(details_lines)

        if all_valid:
            return True, SUBSEQUENT_BOOT_CHECK_PASSED, details

        return (
            False,
            SUBSEQUENT_BOOT_CHECK_FAILED.format(
                message="Subsequent boot check failed on one or more nodes",
            ),
            details,
        )

    # =========================================================================
    # TC-F10, TC-F11, TC-F12: DISK TYPE SUPPORT (SSD, HDD, NVMe)
    # =========================================================================

    def verify_disk_type_support(self, expected_disk_type):
        """Verify etcd local disk deployment using a specific disk type.

        Args:
            expected_disk_type (str): One of 'ssd', 'hdd', 'nvme'.

        Returns:
            tuple: (success, message, details)
        """
        nodes = self.get_control_plane_nodes()
        if not nodes:
            return False, NO_CONTROL_PLANE_NODES, None

        details_lines = []
        found_on_any = False

        for node in nodes:
            target = self._get_node_target(node)
            if not target:
                continue

            # Get the source device for /var/lib/etcd
            rc, mount_src, _ = self._ssh_from_omnia_core(
                target,
                f"findmnt -no SOURCE {ETCD_MOUNT_PATH} 2>/dev/null",
            )
            mount_src = (mount_src or "").strip()

            if not mount_src:
                details_lines.append(
                    f"  [SKIP] {ETCD_MOUNT_PATH} not mounted on {target}"
                )
                continue

            # Get parent disk name
            rc, parent_disk, _ = self._ssh_from_omnia_core(
                target,
                f"lsblk -no PKNAME {mount_src} 2>/dev/null | head -1",
            )
            parent_disk = (parent_disk or "").strip()
            if not parent_disk:
                parent_disk = mount_src.replace("/dev/", "").rstrip("0123456789").rstrip("p")

            # Detect disk type
            detected_type = self._detect_disk_type(target, parent_disk)

            if detected_type == expected_disk_type:
                msg = DISK_TYPE_DETECTED.format(
                    disk_type=expected_disk_type.upper(),
                    node=target,
                    disk=f"/dev/{parent_disk}",
                )
                details_lines.append(f"  [PASS] {msg}")
                found_on_any = True
            else:
                msg = DISK_TYPE_NOT_DETECTED.format(
                    disk_type=expected_disk_type.upper(),
                    node=target,
                )
                details_lines.append(
                    f"  [INFO] {msg} (detected: {detected_type or 'unknown'})"
                )

        details = "\n".join(details_lines)

        if found_on_any:
            return (
                True,
                DISK_TYPE_CHECK_PASSED.format(
                    disk_type=expected_disk_type.upper(),
                    node="control plane nodes",
                ),
                details,
            )

        return (
            False,
            DISK_TYPE_CHECK_FAILED.format(
                disk_type=expected_disk_type.upper(),
                message=f"No {expected_disk_type.upper()} disk found for etcd"
                " on any control plane node",
            ),
            details,
        )

    # =========================================================================
    # POST-REBOOT: REBOOT CONTROL PLANE NODE
    # =========================================================================

    def reboot_control_plane_node(self):
        """Reboot one control plane node for post-reboot etcd validation.

        Selects the first control plane node, reboots it, and returns
        information needed for subsequent post-reboot validation tests.

        Returns:
            dict: Keys: success, message, rebooted_node, rebooted_ip,
                  rebooted_hostname, remaining_nodes, reboot_time
        """
        nodes = self.get_control_plane_nodes()
        if not nodes:
            return {"success": False, "message": REBOOT_NODE_NOT_FOUND}

        if len(nodes) < 2:
            return {"success": False, "message": REBOOT_NO_REMAINING_NODES}

        reboot_node = nodes[0]
        remaining_nodes = nodes[1:]
        reboot_ip = (reboot_node.get("admin_ip") or "").strip()
        reboot_hostname = (
            reboot_node.get("hostname") or reboot_ip
        ).strip()

        if not reboot_ip:
            return {"success": False, "message": REBOOT_NODE_NOT_FOUND}

        # Record reboot time (from the node itself for accuracy)
        rc, node_time, _ = self._ssh_from_omnia_core(
            reboot_ip, "date '+%Y-%m-%d %H:%M:%S'",
        )
        reboot_time = (node_time or "").strip()

        # Trigger async reboot
        reboot_cmd = "nohup sh -c 'sleep 2; reboot' >/dev/null 2>&1 &"
        self._ssh_from_omnia_core(reboot_ip, reboot_cmd)

        return {
            "success": True,
            "message": REBOOT_NODE_INITIATED.format(
                node=reboot_hostname, ip=reboot_ip,
            ),
            "rebooted_node": reboot_node,
            "rebooted_ip": reboot_ip,
            "rebooted_hostname": reboot_hostname,
            "remaining_nodes": remaining_nodes,
            "reboot_time": reboot_time,
        }

    def wait_for_node_online(self, node_ip, hostname,
                             timeout=None, poll=None):
        """Poll SSH until the node comes back online after reboot.

        Args:
            node_ip (str): IP address of the node.
            hostname (str): Hostname of the node.
            timeout (int, optional): Timeout in seconds.
            poll (int, optional): Poll interval in seconds.

        Returns:
            dict: Keys: success, elapsed, message
        """
        timeout = REBOOT_WAIT_ONLINE_TIMEOUT if timeout is None else int(timeout)
        poll = REBOOT_WAIT_ONLINE_POLL if poll is None else int(poll)

        start = time.time()
        while time.time() - start < timeout:
            time.sleep(poll)
            rc, out, _ = self._ssh_from_omnia_core(node_ip, "echo online")
            if rc == 0 and "online" in out:
                elapsed = int(time.time() - start)
                return {
                    "success": True,
                    "elapsed": elapsed,
                    "message": NODE_ONLINE_PASSED.format(
                        node=hostname, ip=node_ip, elapsed=elapsed,
                    ),
                }

        elapsed = int(time.time() - start)
        return {
            "success": False,
            "elapsed": elapsed,
            "message": NODE_ONLINE_FAILED.format(
                node=hostname, ip=node_ip, timeout=timeout,
            ),
        }

    def wait_for_cloud_init(self, node_ip, hostname,
                            timeout=None, poll=None):
        """Wait for cloud-init to complete on a node after reboot.

        Args:
            node_ip (str): IP address of the node.
            hostname (str): Hostname of the node.
            timeout (int, optional): Timeout in seconds.
            poll (int, optional): Poll interval in seconds.

        Returns:
            dict: Keys: success, message, log_tail
        """
        timeout = CLOUD_INIT_TIMEOUT if timeout is None else int(timeout)
        poll = CLOUD_INIT_POLL if poll is None else int(poll)

        start = time.time()
        while time.time() - start < timeout:
            time.sleep(poll)
            rc, out, _ = self._ssh_from_omnia_core(
                node_ip,
                "grep 'Cloud-Init finished successfully after the reboot' "
                "/var/log/cloud-init-output.log 2>/dev/null",
            )
            if rc == 0 and "Cloud-Init finished successfully" in out:
                return {
                    "success": True,
                    "message": CLOUD_INIT_PASSED.format(node=hostname),
                    "log_tail": "",
                }

        # Timeout - get last lines of cloud-init log for debugging
        _, log_tail, _ = self._ssh_from_omnia_core(
            node_ip,
            "tail -20 /var/log/cloud-init-output.log 2>/dev/null",
        )
        return {
            "success": False,
            "message": CLOUD_INIT_FAILED.format(
                node=hostname, timeout=timeout,
            ),
            "log_tail": (log_tail or "").strip(),
        }

    # =========================================================================
    # POST-REBOOT: TC-F09 WITH TIMESTAMP VALIDATION
    # =========================================================================

    def verify_subsequent_boot_fstab_update_post_reboot(
        self, reboot_time, target_node=None,
    ):
        """Verify etcd-fstab-update.sh ran AFTER the reboot by checking log timestamps.

        Args:
            reboot_time (str): Timestamp of the reboot (YYYY-MM-DD HH:MM:SS).
            target_node (str, optional): Hostname or IP of a specific node to
                verify. When provided, only that node is checked instead of all
                control plane nodes.

        Returns:
            tuple: (success, message, details)
        """
        if target_node:
            nodes = [{"hostname": target_node, "admin_ip": target_node}]
        else:
            nodes = self.get_control_plane_nodes()
        if not nodes:
            return False, NO_CONTROL_PLANE_NODES, None

        details_lines = []
        all_valid = True

        for node in nodes:
            target = self._get_node_target(node)
            if not target:
                continue

            # Check script exists
            rc, _, _ = self._ssh_from_omnia_core(
                target, f"[ -f {ETCD_FSTAB_UPDATE_SCRIPT} ]",
            )
            if rc == 0:
                msg = FSTAB_UPDATE_SCRIPT_EXISTS.format(node=target)
                details_lines.append(f"  [PASS] {msg}")
            else:
                msg = FSTAB_UPDATE_SCRIPT_MISSING.format(node=target)
                details_lines.append(f"  [FAIL] {msg}")
                all_valid = False
                continue

            # Check log exists
            rc, _, _ = self._ssh_from_omnia_core(
                target, f"[ -f {ETCD_FSTAB_UPDATE_LOG} ]",
            )
            if rc != 0:
                msg = FSTAB_UPDATE_LOG_MISSING.format(node=target)
                details_lines.append(f"  [FAIL] {msg}")
                all_valid = False
                continue

            # Check log has DONE marker
            rc, log_tail, _ = self._ssh_from_omnia_core(
                target, f"tail -5 {ETCD_FSTAB_UPDATE_LOG} 2>/dev/null",
            )
            log_tail = (log_tail or "").strip()

            if "DONE" not in log_tail:
                msg = FSTAB_UPDATE_LOG_FAILED.format(node=target)
                details_lines.append(f"  [FAIL] {msg}")
                all_valid = False
                continue

            # Check log modification time is after reboot
            rc, log_mtime, _ = self._ssh_from_omnia_core(
                target,
                f"stat -c '%Y' {ETCD_FSTAB_UPDATE_LOG} 2>/dev/null",
            )
            rc2, reboot_epoch, _ = self._ssh_from_omnia_core(
                target,
                f"date -d '{reboot_time}' '+%s' 2>/dev/null",
            )
            log_mtime = (log_mtime or "").strip()
            reboot_epoch = (reboot_epoch or "").strip()

            if log_mtime and reboot_epoch:
                try:
                    if int(log_mtime) >= int(reboot_epoch):
                        # Get human-readable log time for message
                        _, log_time_str, _ = self._ssh_from_omnia_core(
                            target,
                            f"date -d @{log_mtime} '+%Y-%m-%d %H:%M:%S'"
                            " 2>/dev/null",
                        )
                        log_time_str = (log_time_str or "").strip()
                        msg = FSTAB_UPDATE_LOG_TIMESTAMP_VALID.format(
                            node=target,
                            log_time=log_time_str,
                            reboot_time=reboot_time,
                        )
                        details_lines.append(f"  [PASS] {msg}")
                    else:
                        _, log_time_str, _ = self._ssh_from_omnia_core(
                            target,
                            f"date -d @{log_mtime} '+%Y-%m-%d %H:%M:%S'"
                            " 2>/dev/null",
                        )
                        log_time_str = (log_time_str or "").strip()
                        msg = FSTAB_UPDATE_LOG_TIMESTAMP_STALE.format(
                            node=target,
                            log_time=log_time_str,
                            reboot_time=reboot_time,
                        )
                        details_lines.append(f"  [FAIL] {msg}")
                        all_valid = False
                except ValueError:
                    details_lines.append(
                        f"  [FAIL] Could not compare timestamps on {target}"
                    )
                    all_valid = False
            else:
                details_lines.append(
                    f"  [FAIL] Could not get timestamps on {target}"
                )
                all_valid = False

        details = "\n".join(details_lines)

        if all_valid:
            return True, SUBSEQUENT_BOOT_POST_REBOOT_PASSED, details

        return (
            False,
            SUBSEQUENT_BOOT_POST_REBOOT_FAILED.format(
                message="Timestamp verification failed on one or more nodes",
            ),
            details,
        )

    def _detect_disk_type(self, target, disk_name):
        """Detect the type of a disk (ssd, hdd, nvme).

        Args:
            target (str): SSH target for the node.
            disk_name (str): Disk name (e.g., 'sda', 'nvme0n1').

        Returns:
            str: 'nvme', 'ssd', 'hdd', or 'unknown'.
        """
        if disk_name.startswith("nvme"):
            return "nvme"

        rc, rotational, _ = self._ssh_from_omnia_core(
            target,
            f"cat /sys/block/{disk_name}/queue/rotational 2>/dev/null",
        )
        rotational = (rotational or "").strip()

        if rotational == "0":
            return "ssd"
        elif rotational == "1":
            return "hdd"

        return "unknown"


def get_etcd_operations(config_path=None):
    """Get an instance of EtcdLocalDiskOperations.

    Args:
        config_path (str, optional): Path to the user config file.

    Returns:
        EtcdLocalDiskOperations: An instance of EtcdLocalDiskOperations.
    """
    return EtcdLocalDiskOperations(config_path=config_path)
