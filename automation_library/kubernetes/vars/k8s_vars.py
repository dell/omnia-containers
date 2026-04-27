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
Kubernetes variables for OMNIA test automation.

This module contains constants and variables used for Kubernetes testing.
"""

# Default SSH settings for Kubernetes nodes
NODE_SSH_USER = "root"
NODE_SSH_PORT = 22
NODE_SSH_TIMEOUT = 10

# Kubernetes service names
KUBELET_SERVICE = "kubelet"
CRIO_SERVICE = "crio"
CRI_O_SERVICE = "cri-o"
CHRONYD_SERVICE = "chronyd"

# Kubernetes node types
CONTROL_PLANE_GROUP = "service_kube_control_plane_x86_64"
WORKER_NODE_GROUP = "service_kube_node_x86_64"

# HA configuration
HA_CONFIG_FILE = "/opt/omnia/input/project_default/high_availability_config.yml"

# Container runtime configuration
EXPECTED_CONTAINER_RUNTIME = "cri-o"
SERVICE_CLUSTER_METADATA_PATH = "/opt/omnia/.data/service_cluster_metadata.yml"
DEFAULT_STORAGE_CLASS = "ps01"
READY_STATE_MAX_RETRIES = 6
READY_STATE_RETRY_DELAY_SECONDS = 10

# Reboot scenario timeouts
K8S_REBOOT_WAIT_ONLINE_TIMEOUT = 900     # seconds to wait for node SSH after reboot
K8S_REBOOT_WAIT_ONLINE_POLL = 15         # poll interval while waiting for SSH
K8S_CLOUD_INIT_TIMEOUT = 2400            # seconds to wait for cloud-init completion
K8S_CLOUD_INIT_POLL = 15                 # poll interval while waiting for cloud-init
K8S_NODE_READY_TIMEOUT = 600             # seconds to wait for kubectl Ready state
K8S_NODE_READY_POLL = 15                 # poll interval while waiting for Ready
K8S_VIP_FAILOVER_TIMEOUT = 120           # seconds to wait for VIP to move
K8S_VIP_FAILOVER_POLL = 10              # poll interval while waiting for VIP failover