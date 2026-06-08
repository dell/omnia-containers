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
Provision Module - Slurm Variables.

Services and paths for Slurm cluster verification.
Based on cloud-init templates in:
/omnia/provision/roles/configure_ochami/templates/cloud_init/
"""

# =============================================================================
# SLURM SERVICES TO CHECK BY NODE TYPE (from cloud-init templates)
# =============================================================================

# slurm_control_node: slurmctld, slurmdbd, munge, mariadb, sshd
# sssd only if openldap enabled
SLURM_CONTROL_SERVICES = ["slurmctld", "slurmdbd", "munge", "mariadb"]

# slurm_node: slurmd, munge, sshd
# sssd only if openldap enabled
SLURM_NODE_SERVICES = ["slurmd", "munge"]

# login_node and login_compiler_node: slurmd, munge, sshd
# sssd only if openldap enabled
LOGIN_NODE_SERVICES = ["slurmd", "munge"]

# =============================================================================
# LDMS PATHS AND SERVICE
# =============================================================================

LDMS_SAMPLER_SERVICE = "ldmsd.sampler.service"
LDMS_SAMPLER_CONF_PATH = "/opt/ovis-ldms/etc/ldms/sampler.conf"
LDMS_SAMPLER_ENV_PATH = "/opt/ovis-ldms/etc/ldms/ldmsd.sampler.env"
