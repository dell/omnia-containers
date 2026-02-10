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

POWERSCALE_PVC_BUSYBOX_MANIFEST_YAML = """apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: pvc-powerscale
spec:
  accessModes:
    - ReadWriteMany
  resources:
    requests:
      storage: 1Gi
  storageClassName: ps01
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: deploy-busybox-01
spec:
  strategy:
    type: Recreate
  replicas: 1
  selector:
    matchLabels:
      app: deploy-busybox-01
  template:
    metadata:
      labels:
        app: deploy-busybox-01
    spec:
      containers:
        - name: busybox
          image: docker.io/library/busybox:1.36
          command: [\"sh\", \"-c\"]
          args: [\"while true; do touch /data/datafile; rm -f /data/datafile; done\"]
          volumeMounts:
            - name: data
              mountPath: /data
      volumes:
        - name: data
          persistentVolumeClaim:
            claimName: pvc-powerscale
"""
