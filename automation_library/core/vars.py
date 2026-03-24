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

# =============================================================================
# INPUT BASE PATH (inside omnia_core container)
# =============================================================================

INPUT_BASE_PATH = "/opt/omnia/input/project_default"

# =============================================================================
# INPUT FILE NAMES (inside omnia_core container at INPUT_BASE_PATH)
# Used by core/load_inputs.py get_input_value(host, filename, key)
# =============================================================================

SOFTWARE_CONFIG_FILE = "software_config.json"
BUILD_STREAM_CONFIG_FILE = "build_stream_config.yml"
NETWORK_SPEC_FILE = "network_spec.yml"
PROVISION_CONFIG_FILE = "provision_config.yml"
TELEMETRY_CONFIG_FILE = "telemetry_config.yml"

# =============================================================================
# OTHER PATHS (outside INPUT_BASE_PATH)
# =============================================================================

SERVICE_CLUSTER_METADATA_PATH = "/opt/omnia/.data/service_cluster_metadata.yml"

# =============================================================================
# KUBERNETES FUNCTIONAL GROUPS (from PXE mapping file)
# =============================================================================

K8S_CONTROL_PLANE_FUNCTIONAL_GROUP = "service_kube_control_plane_x86_64"
K8S_WORKER_NODE_FUNCTIONAL_GROUP = "service_kube_node_x86_64"
