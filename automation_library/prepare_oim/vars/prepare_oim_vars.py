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
Prepare OIM - Configuration Variables.

Pure constants for prepare_oim automation.
All config reading is done via automation_library.core.load_inputs.

Usage:
    from automation_library.prepare_oim.vars.prepare_oim_vars import PULP_CERT_PATH

"""

from typing import List

from automation_library.core.vars import (
    PULP_CERT_PATH as _CORE_PULP_CERT,
    LDAP_CERT_PATH as _CORE_LDAP_CERT,
    OMNIA_CORE_CONTAINER as _CORE_CONTAINER,
)


# =============================================================================
# CONTAINER DEFINITIONS
# =============================================================================

# OpenChami containers (deployed by prepare_oim)
OPENCHAMI_CONTAINERS: List[str] = [
    "pulp",
    "minio-server",
    "registry",
    "step-ca",
    "postgres",
    "hydra",
    "smd",
    "opaal-idp",
    "bss",
    "opaal",
    "cloud-init-server",
    "haproxy",
    "coresmd",
]

# Core container (prerequisite - deployed by omnia.sh --install)
CORE_CONTAINERS: List[str] = [
    _CORE_CONTAINER,
]

# Auth container (only required when LDAP is in software_config.json)
AUTH_CONTAINER: str = "omnia_auth"

# =============================================================================
# SERVICE DEFINITIONS (from systemctl list-dependencies)
# =============================================================================

# Always-on direct dependencies of omnia.target
OMNIA_TARGET_SERVICES: List[str] = [
    "omnia_core.service",
    "pulp.service",
    "registry.service",
    "minio.service",
    "network-online.target",
]

# Services under openchami.target (always required)
OPENCHAMI_TARGET_SERVICES: List[str] = [
    "acme-deploy.service",
    "acme-register.service",
    "bss-init.service",
    "bss.service",
    "cloud-init-server.service",
    "coresmd.service",
    "haproxy.service",
    "hydra-gen-jwks.service",
    "hydra-migrate.service",
    "hydra.service",
    "opaal-idp.service",
    "opaal.service",
    "openchami-cert-trust.service",
    "postgres.service",
    "smd.service",
    "step-ca.service",
]

# =============================================================================
# BUILD STREAM DEFINITIONS (deployed only when enable_build_stream is true)
# =============================================================================

# Containers deployed by build_stream role
BUILD_STREAM_CONTAINERS: List[str] = [
    "omnia_postgres",
    "omnia_build_stream",
]

# Systemd service deployed by build_stream role
BUILD_STREAM_SERVICE: str = "playbook_watcher.service"

# Quadlet files for build_stream containers
BUILD_STREAM_QUADLET_FILES: List[str] = [
    "/etc/containers/systemd/omnia_build_stream.container",
    "/etc/containers/systemd/omnia_postgres.container",
]

# =============================================================================
# PULP API SETTINGS
# =============================================================================

# Pulp API port for status checks
PULP_API_PORT: int = 2225

# =============================================================================
# OCHAMI AUTH / CERTIFICATE RENEWAL SETTINGS
# =============================================================================

# Number of retries for gen_access_token
OCHAMI_AUTH_RETRIES: int = 3

# Delay in seconds between gen_access_token retries
OCHAMI_AUTH_DELAY: int = 5

# Seconds to wait after restarting acme-deploy before rechecking
CERT_WAIT_TIME: int = 30

# =============================================================================
# CERTIFICATE PATHS (inside omnia_core container)
# =============================================================================

PULP_CERT_PATH: str = _CORE_PULP_CERT
LDAP_CERT_PATH: str = _CORE_LDAP_CERT
