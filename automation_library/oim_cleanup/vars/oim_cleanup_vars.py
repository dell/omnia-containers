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
OIM Cleanup - Configuration Variables.

All paths, container names, services, ports, and directories that the
oim_cleanup.yml playbook removes. Values sourced from the playbook's
role vars files inside omnia_core container.

Paths use core module constants (INPUT_BASE_PATH, SERVICE_CLUSTER_METADATA_PATH).
"""

from automation_library.core.vars import INPUT_BASE_PATH, SERVICE_CLUSTER_METADATA_PATH

# =============================================================================
# OIM Cleanup Variables
# =============================================================================
OIM_CLEANUP_VARS = {
    # =========================================================================
    # Services to verify removed (stopped/disabled)
    # =========================================================================
    "services": [
        "omnia.target",
        "openchami.target",
        "pulp.service",
        "chronyd.service",
    ],

    "openchami_services": [
        "openchami-cert-internal-network.service",
        "openchami-cert-trust.service",
        "openchami-external-network.service",
        "openchami-internal-network.service",
        "openchami-jwt-internal-network.service",
        "bss-init.service",
        "smd-init.service",
        "step-ca-db-volume.service",
        "step-ca-home-volume.service",
        "postgres-data-volume.service",
        "hydra-gen-jwks.service",
        "hydra-migrate.service",
        "haproxy-certs-volume.service",
    ],

    # =========================================================================
    # Containers to verify removed
    # =========================================================================
    "containers": [
        "pulp",
        "minio-server",
        "registry",
        "step-ca",
        "postgres",
        "hydra",
        "hydra-gen-jwks",
        "hydra-migrate",
        "opaal-idp",
        "smd",
        "smd-init",
        "bss",
        "bss-init",
        "opaal",
        "cloud-init-server",
        "haproxy",
        "coresmd",
        "acme-deploy",
        "acme-register",
        "omnia_auth",
    ],

    # =========================================================================
    # Container systemd files to verify removed
    # =========================================================================
    "container_files": [
        # Core containers
        "/etc/containers/systemd/pulp.container",
        "/etc/containers/systemd/registry.container",
        "/etc/containers/systemd/minio.container",
        # OpenCHAMI containers
        "/etc/containers/systemd/step-ca.container",
        "/etc/containers/systemd/postgres.container",
        "/etc/containers/systemd/hydra.container",
        "/etc/containers/systemd/hydra-gen-jwks.container",
        "/etc/containers/systemd/hydra-migrate.container",
        "/etc/containers/systemd/opaal-idp.container",
        "/etc/containers/systemd/smd.container",
        "/etc/containers/systemd/smd-init.container",
        "/etc/containers/systemd/bss.container",
        "/etc/containers/systemd/bss-init.container",
        "/etc/containers/systemd/opaal.container",
        "/etc/containers/systemd/cloud-init-server.container",
        "/etc/containers/systemd/haproxy.container",
        "/etc/containers/systemd/coresmd.container",
        "/etc/containers/systemd/acme-deploy.container",
        "/etc/containers/systemd/acme-register.container",
    ],
    "auth_container_file_pattern": "/etc/containers/systemd/omnia_auth*",

    # =========================================================================
    # Quadlet volume files to verify removed
    # =========================================================================
    "quadlet_volume_files": [
        "/etc/containers/systemd/acme-certs.volume",
        "/etc/containers/systemd/haproxy-certs.volume",
        "/etc/containers/systemd/postgres-data.volume",
        "/etc/containers/systemd/step-ca-db.volume",
        "/etc/containers/systemd/step-ca-home.volume",
        "/etc/containers/systemd/step-root-ca.volume",
    ],

    # =========================================================================
    # Quadlet network files to verify removed
    # =========================================================================
    "quadlet_network_files": [
        "/etc/containers/systemd/openchami-cert-internal.network",
        "/etc/containers/systemd/openchami-external.network",
        "/etc/containers/systemd/openchami-internal.network",
        "/etc/containers/systemd/openchami-jwt-internal.network",
    ],

    # =========================================================================
    # omnia.target files to verify removed
    # =========================================================================
    "omnia_target_files": [
        "/etc/systemd/system/omnia.target",
        "/etc/systemd/system/default.target.wants/omnia.target",
        "/etc/systemd/system/multi-user.target.wants/omnia.target",
    ],

    # =========================================================================
    # OpenCHAMI volumes to verify removed
    # =========================================================================
    "openchami_volumes": [
        "haproxy-certs",
        "acme-certs",
        "postgres-data",
        "step-ca-db",
        "step-root-ca",
        "step-ca-home",
    ],

    # =========================================================================
    # OpenCHAMI secrets to verify removed
    # =========================================================================
    "openchami_secrets": [
        "hydra_postgres_password",
        "hydra_dsn",
        "hydra_system_secret",
        "smd_postgres_password",
        "postgres_password",
        "postgres_multiple_databases",
        "bss_postgres_password",
    ],

    # =========================================================================
    # Credential files to verify removed (inside container)
    # =========================================================================
    "credential_files": [
        f"{INPUT_BASE_PATH}/omnia_config_credentials.yml",
        f"{INPUT_BASE_PATH}/.omnia_config_credentials_key",
    ],
    "metadata_files": [
        SERVICE_CLUSTER_METADATA_PATH,
        "/opt/omnia/.data/functional_groups_config.yml",
    ],

    # =========================================================================
    # Firewall ports to verify removed
    # =========================================================================
    "tcp_ports": [
        "9000", "9001", "5000", "5432",
        "27778", "27779", "8081", "8443",
    ],
    "udp_ports": [
        "69", "67", "68",
    ],

    # =========================================================================
    # Directories to verify removed
    # Relative paths are relative to omnia NFS share base (omnia_shared_path)
    # Absolute paths are checked as-is on the OIM host
    # =========================================================================
    "cleanup_dirs_relative": [
        "pulp/pulp_ha/cli.toml",
        "log/pulp",
        "pulp/settings",
        "pulp/nginx",
        "pulp/pulp_crt_track.txt",
        "offline_repo",
        "log/local_repo",
        "k8s_dynamic_json",
        "rhel_repo_certs",
        "telemetry",
        ".secrets",
        "log/telemetry",
        "k8s_pvc_data",
        "service_cluster",
        "openchami",
        "log/openchami",
        "auth",
    ],
    "cleanup_dirs_absolute": [
        "/etc/openchami",
        "/etc/ochami",
    ],
    "cleanup_credential_key": f"{INPUT_BASE_PATH}/.local_repo_credentials_key",

    # =========================================================================
    # regctl files to verify removed
    # =========================================================================
    "regctl_files": [
        "/usr/local/bin/regctl",
    ],

    # =========================================================================
    # Packages to verify removed
    # =========================================================================
    "packages": [
        "ochami",
        "openchami",
        "s3cmd",
    ],

    # =========================================================================
    # chrony config
    # =========================================================================
    "chrony_conf_path": "/etc/chrony.conf",
}
