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
"""

from typing import Dict

# =============================================================================
# Config File Paths (inside omnia_core container)
# =============================================================================
# These paths are INSIDE the omnia_core container
OPENCHAMI_NODES_PATH = "/opt/omnia/openchami/workdir/nodes/nodes.yaml"
BMC_GROUP_DATA_PATH = "/opt/omnia/telemetry/bmc_group_data.csv"
OPEN_NETWORK_SPEC_PATH = "/opt/omnia/input/project_default/open_network_spec"

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
FUNCTIONAL_GROUP_SLURM_CONTROL = "slurm_control_node"
FUNCTIONAL_GROUP_KUBE_CONTROL = "kube_control_plane"

# =============================================================================
# Command Templates
# =============================================================================
CMD_TEMPLATES: Dict[str, str] = {
    # SSH options for non-interactive connections
    "ssh_opts": (
        "-o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null "
        "-o ConnectTimeout={timeout}"
    ),

    # SSH with batch mode (no password prompt)
    "ssh_opts_batch": (
        "-o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null "
        "-o BatchMode=yes -o ConnectTimeout={timeout}"
    ),

    # OpenCHAMI commands - Run OUTSIDE container (ochami is installed on OIM)
    "ochami_smd_get_all": "ochami smd component get",

    # SSH to node from omnia_core container (SSH keys are inside container)
    "ssh_to_node": (
        "podman exec {container} ssh {ssh_opts} root@{admin_ip} '{command}'"
    ),

    # Kubernetes commands (run on kube control plane)
    "kubectl_get_nodes": "kubectl get nodes -o wide",
    "kubectl_get_nodes_all": "kubectl get nodes -A",

    # Package check
    "rpm_query": "rpm -q {package}",

    # OpenCHAMI ACME certificate renewal (run on OIM host)
    "acme_restart_register": "systemctl restart acme-register.service",
    "acme_restart_deploy": "systemctl restart acme-deploy.service",
    "haproxy_reload": "podman kill -s HUP haproxy",
}

# =============================================================================
# ACME / TLS Constants
# =============================================================================
HAPROXY_CERT_VOLUME_PATH = "/var/lib/containers/storage/volumes/haproxy-certs/_data"
ACME_CERT_RENEW_WAIT = 10
