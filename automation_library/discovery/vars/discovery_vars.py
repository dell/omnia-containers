# Copyright 2026 Dell Inc. or its subsidiaries. All Rights Reserved.
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
Discovery Module - Configuration Variables.

This module defines all constants, paths, and command templates for discovery automation.
All paths are relative to the omnia_core container.

Author: Dell Technologies
"""

from typing import Dict

# =============================================================================
# Config File Paths (inside omnia_core container)
# =============================================================================
# These paths are INSIDE the omnia_core container
OPENCHAMI_NODES_PATH = "/opt/omnia/openchami/workdir/nodes/nodes.yaml"
OPENCHAMI_HOSTNAME_PATH = "/opt/omnia/openchami/workdir/nodes/hostname.yaml"
BMC_GROUP_DATA_PATH = "/opt/omnia/telemetry/bmc_group_data.csv"
OIM_METADATA_PATH = "/opt/omnia/.data/oim_metadata.yml"

# =============================================================================
# Constants
# =============================================================================
CONTAINER_NAME = "omnia_core"

# SSH connection timeout (seconds)
SSH_TIMEOUT = 10

# =============================================================================
# Service and Validation Constants
# =============================================================================
# Services to check on login/compute nodes
LOGIN_SERVICES = ["sssd", "munge", "slurmd"]

# Services to check on slurm control nodes (slurmctld instead of slurmd)
SLURM_CONTROL_SERVICES = ["sssd", "munge", "slurmctld"]

# Functional group patterns (used as 'contains' match against PXE mapping values)
# e.g., 'login_node' matches 'login_node_x86_64' but NOT 'login_compiler_node_x86_64'
FUNCTIONAL_GROUP_LOGIN = "login_node"
FUNCTIONAL_GROUP_LOGIN_COMPILER = "login_compiler"
FUNCTIONAL_GROUP_SLURM_CONTROL = "slurm_control_node"
FUNCTIONAL_GROUP_KUBE_CONTROL = "kube_control_plane"

# =============================================================================
# Command Templates
# =============================================================================
CMD_TEMPLATES: Dict[str, str] = {
    # SSH options for non-interactive connections
    "ssh_opts": "-o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o ConnectTimeout={timeout}",

    # SSH with batch mode (no password prompt)
    "ssh_opts_batch": "-o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o BatchMode=yes -o ConnectTimeout={timeout}",

    # OpenCHAMI commands - Run OUTSIDE container (ochami is installed on OIM)
    "ochami_smd_get_all": "ochami smd component get",
    "ochami_smd_get_nodes": "ochami smd component get | jq '.Components[] | select(.Type == \"Node\")'",
    "ochami_discover_static": "ochami discover static -f yaml -d @{nodes_file} --overwrite",

    # SSH to node from omnia_core container (SSH keys are inside container)
    "ssh_to_node": "podman exec {container} ssh {ssh_opts} root@{admin_ip} '{command}'",

    # Read file from omnia_core container
    "read_file_container": "podman exec {container} cat {file_path}",

    # Check file exists in omnia_core container
    "file_exists_container": "podman exec {container} test -f {file_path}",

    # Read file directly on OIM (outside container)
    "read_file_oim": "cat {file_path}",

    # Check file exists on OIM (outside container)
    "file_exists_oim": "test -f {file_path}",

    # Service status check - detailed output
    "systemctl_status": "systemctl is-active {service} && systemctl is-enabled {service}",
    "systemctl_status_detail": "systemctl status {service} --no-pager -l 2>/dev/null | head -10",

    # Slurm commands - actual output, not version
    "slurm_sinfo": "sinfo",
    "slurm_sinfo_detail": "sinfo -N -l",
    "slurm_squeue": "squeue",
    "slurm_scontrol": "scontrol show partition",

    # LDAP check - list LDAP/directory users via getent passwd
    # Avoids awk single-quote nesting issues with SSH command wrapping
    "ldap_check": "getent passwd -s sss 2>/dev/null || getent passwd -s ldap 2>/dev/null",

    # Kubernetes commands (run on kube control plane)
    "kubectl_get_nodes": "kubectl get nodes -o wide",
    "kubectl_get_nodes_all": "kubectl get nodes -A",
    "kubectl_get_nodes_json": "kubectl get nodes -o json",

    # Package check
    "rpm_query": "rpm -q {package}",
    "dpkg_query": "dpkg -l {package} 2>/dev/null | grep -q ^ii && echo installed",
}
