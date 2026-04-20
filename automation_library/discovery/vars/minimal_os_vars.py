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
Minimal OS - Variables and Constants.

This module contains all constants, paths, and configuration values
for the Minimal OS automation tests.
"""

# Functional group names
FUNCTIONAL_GROUPS = {
    "os_x86_64": "os_x86_64",
    "os_aarch64": "os_aarch64",
}

# Base OS packages that must be present (AC-2.1, FS-IC-01, FS-CR-03)
BASE_PACKAGES = [
    "kernel",
    "systemd",
    "NetworkManager",
    "openssh-server",
    "chrony",
    "dnf",
]

# LDMS packages that must be present (AC-2.2, AC-5.1, FS-IC-02)
LDMS_PACKAGES = [
    "ovis-ldms",
]

# Package patterns that must NOT be present (AC-2.3-2.5, AC-4.3-4.6, FS-EX-01-03)
EXCLUDED_PACKAGE_PATTERNS = {
    "slurm": "Slurm",
    "kube|k8s|kubernetes": "Kubernetes",
    "docker|podman|containerd": "Container runtime",
    "mlnx|ofed|doca": "DOCA-OFED",
    "cuda|nvidia-driver": "CUDA",
    "openmpi|mpich": "MPI",
}

# Services that must NOT be running at handoff (AC-4.3-4.6, FS-EX-04-05)
EXCLUDED_SERVICES = [
    "slurmd",
    "slurmctld",
    "kubelet",
    "docker",
    "podman",
    "containerd",
]

# Services that MUST be running at handoff (AC-4.2, FS-HS-02)
REQUIRED_SERVICES = [
    "sshd",
    "chronyd",
    "NetworkManager",
]

# Image storage paths
IMAGE_PATHS = {
    "base": "/var/lib/omnia/images",
    "os_x86_64": [
        "os_x86_64.img",
        "minimal-os-x86_64.img",
        "omnia-minimal-x86_64.img",
    ],
    "os_aarch64": [
        "os_aarch64.img",
        "minimal-os-aarch64.img",
        "omnia-minimal-aarch64.img",
    ],
}

# PXE mapping paths
PXE_MAPPING_PATHS = [
    "/etc/omnia/pxe_mapping.yaml",
    "/opt/omnia/config/pxe_mapping.yaml",
    "/opt/omnia/oim_shared/input/pxe_mapping.yaml",
]

# Additional packages config path
ADDITIONAL_PACKAGES_PATH = "/etc/omnia/additional_packages.json"

# Functional group schema paths
FUNCTIONAL_GROUP_SCHEMA_PATHS = [
    "/etc/omnia/functional_groups",
    "/opt/omnia/config/functional_groups",
]

# All variables in a single dict for easy import
MINIMAL_OS_VARS = {
    "functional_groups": FUNCTIONAL_GROUPS,
    "base_packages": BASE_PACKAGES,
    "ldms_packages": LDMS_PACKAGES,
    "excluded_package_patterns": EXCLUDED_PACKAGE_PATTERNS,
    "excluded_services": EXCLUDED_SERVICES,
    "required_services": REQUIRED_SERVICES,
    "image_paths": IMAGE_PATHS,
    "pxe_mapping_paths": PXE_MAPPING_PATHS,
    "additional_packages_path": ADDITIONAL_PACKAGES_PATH,
    "functional_group_schema_paths": FUNCTIONAL_GROUP_SCHEMA_PATHS,
}
