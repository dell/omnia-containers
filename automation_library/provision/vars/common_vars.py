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
Provision Module - Common Variables.

SSH options and common constants used across provision tests.
"""

from automation_library.core import (
    OMNIA_CORE_CONTAINER as _CORE_CONTAINER,
    OIM_SHARED_PATH as _OIM_SHARED_PATH,
)

# =============================================================================
# SSH OPTIONS (for handling changed host keys)
# =============================================================================

SSH_OPTS = (
    "-o StrictHostKeyChecking=no "
    "-o UserKnownHostsFile=/dev/null "
    "-o BatchMode=yes "
    "-o ConnectTimeout=10"
)

# =============================================================================
# CONTAINER NAME - from core vars
# =============================================================================

CONTAINER_NAME = _CORE_CONTAINER

# =============================================================================
# REACHABILITY CHECK CONFIGURATION (for subsequent tests)
# =============================================================================

# Number of retries for unreachable nodes in subsequent tests
PROVISION_REACHABILITY_RETRY = 2

# Seconds between reachability retry attempts
PROVISION_REACHABILITY_INTERVAL = 5

# =============================================================================
# CLOUD-INIT RETRY CONFIGURATION
# =============================================================================

# Maximum number of retries per node when cloud-init is still running
CLOUDINIT_RETRY_LIMIT = 50

# Seconds to wait between retry attempts
CLOUDINIT_RETRY_INTERVAL = 10

# Statuses that indicate cloud-init completed successfully (no retry needed)
CLOUDINIT_PASSED_STATUSES = ["done"]

# Statuses that indicate cloud-init is still in progress (should retry)
CLOUDINIT_RETRY_STATUSES = ["running", "not started"]

# =============================================================================
# IMAGE CONFIG YAML DIRECTORY
# Same path used by build_image_x86_64 playbook (build_image_vars.py).
# Contains per-functional-group YAML files with 'packages' list.
# e.g. rhel-slurm_control_node_x86_64_<uuid>-image-build-10.0.yaml
# =============================================================================

IMAGE_CONFIG_YAML_DIR = f"{_OIM_SHARED_PATH}/openchami/workdir/images"

# =============================================================================
# OPENCHAMI WORKDIR PATHS (provision output artifacts inside omnia_core)
# =============================================================================

OPENCHAMI_WORKDIR = f"{_OIM_SHARED_PATH}/openchami/workdir"
BSS_BOOT_DIR = f"{OPENCHAMI_WORKDIR}/boot"
CLOUDINIT_TEMPLATE_DIR = f"{OPENCHAMI_WORKDIR}/cloud-init"

# =============================================================================
# BUILD STREAM VALIDATION FORCE FLAG
# =============================================================================
# Force provision tests to run even when build_stream validate stage
# failed or is still pending.
#
# Default: False (recommended - ensures pipeline validation before tests)
#
# HOW TO ENABLE:
#   1. Open this file:
#      automation_library/provision/vars/common_vars.py
#   2. Change the value below from False to True
#   3. Re-run: bash run_molecule.sh provision verify
#
# WARNING: When True, tests run against images that have NOT been
#          validated by the build_stream pipeline!
FORCE_PROVISION_VALIDATE_FAILED = False

# =============================================================================
# K8S STORAGE CLASS CONSTANTS
# =============================================================================

# PowerScale CSI storage class name (deployed by k8s_config role)
POWERSCALE_STORAGE_CLASS = "ps01"

# NFS storage class name (deployed by k8s_config role)
NFS_STORAGE_CLASS = "nfs-client"

# PowerScale CSI driver name
POWERSCALE_CSI_DRIVER = "csi-isilon.dellemc.com"

# Isilon namespace where CSI pods run
ISILON_NAMESPACE = "isilon"

# Isilon pod prefixes
ISILON_POD_PREFIXES = ["isilon-controller", "isilon-node"]

# NFS provisioner pod prefix
NFS_PROVISIONER_PREFIX = "nfs-client-nfs-subdir-external-provisioner"
