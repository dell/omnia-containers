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
Telemetry Failover Test Variables.

Configuration for node poweroff/reboot telemetry resilience tests.
"""

# =============================================================================
# POD RESCHEDULE RETRY CONFIGURATION
# =============================================================================

# Maximum number of retries to wait for pods to reschedule
POD_RESCHEDULE_RETRY_LIMIT = 30

# Seconds to wait between retry attempts
POD_RESCHEDULE_RETRY_INTERVAL = 20

# =============================================================================
# NODE POWEROFF CONFIGURATION
# =============================================================================

# Seconds to wait after powering off node before checking pods
NODE_POWEROFF_WAIT_SECONDS = 60

# Valid pod statuses that indicate pod is running properly
POD_RUNNING_STATUSES = ["Running", "Completed"]

# Pod statuses that indicate pod is in trouble (for detection)
POD_TROUBLE_STATUSES = ["CrashLoopBackOff", "Error", "Pending", "Terminating"]

# =============================================================================
# NODE REBOOT CONFIGURATION
# =============================================================================

# Seconds to wait after reboot command before checking node status
NODE_REBOOT_WAIT_SECONDS = 30

# Maximum seconds to wait for node to come back online after reboot
NODE_ONLINE_TIMEOUT_SECONDS = 300

# Cloud-init retry configuration for reboot (10 minutes total)
CLOUDINIT_RETRY_LIMIT = 60
CLOUDINIT_RETRY_INTERVAL = 10
CLOUDINIT_PASSED_STATUSES = ["done"]
CLOUDINIT_RETRY_STATUSES = ["running", "not started"]

# =============================================================================
# KUBECTL COMMANDS (no hardcoding in functions)
# =============================================================================

# Get worker nodes (excludes control-plane)
CMD_GET_WORKER_NODES = "kubectl get nodes -o wide --no-headers | grep -v control-plane"

# Get pods on specific node (use .format(namespace=, node_name=))
CMD_GET_PODS_ON_NODE = (
    "kubectl get pods -n {namespace} -o wide --no-headers "
    "--field-selector spec.nodeName={node_name}"
)

# Get all pods in namespace (use .format(namespace=))
CMD_GET_ALL_PODS = "kubectl get pods -n {namespace} -o wide --no-headers"

# =============================================================================
# SSH/POWEROFF/REBOOT COMMANDS
# =============================================================================

# SSH poweroff command (use .format(target_ip=))
CMD_SSH_POWEROFF = (
    "ssh -o StrictHostKeyChecking=no -o ConnectTimeout=10 root@{target_ip} "
    "'nohup shutdown -h now &' 2>&1 || true"
)

# SSH reboot command (use .format(target_ip=))
CMD_SSH_REBOOT = (
    "ssh -o StrictHostKeyChecking=no -o ConnectTimeout=10 root@{target_ip} "
    "'nohup reboot &' 2>&1 || true"
)

# Ping command to check node is online (use .format(target_ip=))
CMD_PING_NODE = "ping -c 1 -W 2 {target_ip}"

# SSH check command (use .format(target_ip=))
CMD_SSH_CHECK = (
    "ssh -o StrictHostKeyChecking=no -o ConnectTimeout=5 -o BatchMode=yes "
    "root@{target_ip} 'echo ok' 2>&1"
)

# Cloud-init status command
CMD_CLOUDINIT_STATUS = "cloud-init status 2>&1"
