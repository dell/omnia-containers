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

"""Core variables for automation library."""

# Omnia configuration paths
PROVISION_CONFIG_PATH = "/opt/omnia/input/project_default/provision_config.yml"
SERVICE_CLUSTER_METADATA_PATH = "/opt/omnia/.data/service_cluster_metadata.yml"

# Kubernetes functional groups (from PXE mapping file)
K8S_CONTROL_PLANE_FUNCTIONAL_GROUP = "service_kube_control_plane_x86_64"
K8S_WORKER_NODE_FUNCTIONAL_GROUP = "service_kube_node_x86_64"
