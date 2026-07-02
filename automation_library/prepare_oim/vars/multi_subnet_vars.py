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
Prepare OIM - Multi-Subnet Configuration Variables.

Constants for multi-subnet (multi-RAC) CoreDHCP verification.
"""

# =============================================================================
# CoreDHCP Configuration
# =============================================================================

# Path to coredhcp.yaml on the OIM host (outside container)
COREDHCP_CONFIG_PATH = "/etc/openchami/configs/coredhcp.yaml"

# =============================================================================
# coresmd Container Image
# =============================================================================

# Container quadlet files that reference coresmd image
CORESMD_COREDHCP_CONTAINER_FILE = "/etc/containers/systemd/coresmd-coredhcp.container"
CORESMD_COREDNS_CONTAINER_FILE = "/etc/containers/systemd/coresmd-coredns.container"

# Minimum coresmd version required for native multi-subnet support
CORESMD_MIN_MULTISUBNET_VERSION = "0.6.0"

# coresmd image to pull for multi-subnet support
CORESMD_MULTISUBNET_IMAGE = "ghcr.io/openchami/coresmd:v0.6.3"

# =============================================================================
# CoreDHCP Multi-Subnet Markers (used to detect config mode)
# =============================================================================

# Markers present in multi-subnet (key=value) mode
MULTISUBNET_CORESMD_MARKER = "svc_base_uri="
MULTISUBNET_BOOTLOOP_MARKER = "subnet_pool="

# Markers present in single-subnet (positional) mode
SINGLE_SUBNET_CORESMD_COMMENT = "# Single-subnet mode"

# =============================================================================
# Systemd Targets
# =============================================================================

OPENCHAMI_TARGET = "openchami.target"
