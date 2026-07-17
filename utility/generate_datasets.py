#!/usr/bin/env python3
"""Generate TC dataset directories from Jinja2 templates and TC variable definitions.

Usage:
    python utility/generate_datasets.py [--clean] [--no-manifest] [tc_name ...]

Options:
    --clean         Delete TC directory before regenerating (recommended)
    --no-manifest   Skip auto-generation of dataset_manifest.yml
    tc_name         One or more TC name patterns (substring match)

Templates are stored in datasets/templates/ (from dell/omnia).
TC variable definitions are embedded in this script. Custom TCs can be added
via datasets/custom_overrides.yml (see custom_overrides.yml.example).

Outputs:
    datasets/tc*/                 Generated TC directories (17 files each)
    datasets/dataset_manifest.yml Auto-generated coverage manifest

Requirements: jinja2, pyyaml (both in standard Omnia dev environment)
"""
# pylint: disable=too-many-lines
import copy
import json
import re
import shutil
import sys
from pathlib import Path

import yaml
from jinja2 import Environment, FileSystemLoader, Undefined

# ============================================================================
# Paths
# ============================================================================
SCRIPT_DIR = Path(__file__).resolve().parent
DATASETS_DIR = SCRIPT_DIR.parent / "datasets"
TEMPLATE_DIR = DATASETS_DIR / "templates"
PROJECT_DEFAULT = DATASETS_DIR / "project_default"

# Template â†’ output filename mapping
TEMPLATE_MAP = {
    "network_spec.j2": "network_spec.yml",
    "provision_config.j2": "provision_config.yml",
    "omnia_config.j2": "omnia_config.yml",
    "telemetry_config.j2": "telemetry_config.yml",
    "telemetry_storage_config.j2": "telemetry_storage_config.yml",
    "storage_config.j2": "storage_config.yml",
    "local_repo_config.j2": "local_repo_config.yml",
    "build_stream_config.j2": "build_stream_config.yml",
    "gitlab_config.j2": "gitlab_config.yml",
    "high_availability_config.j2": "high_availability_config.yml",
    "omnia_config_credentials.yml.j2": "omnia_config_credentials.yml",
    "pxe_mapping_file.csv.j2": "pxe_mapping_file.csv",
}

# Files without templates â€” copied from project_default with TC-specific overrides
NON_TEMPLATED = [
    "software_config.json",
    "security_config.yml",
    "discovery_config.yml",
    "additional_cloud_init.yml",
    "user_registry_credential.yml",
]

# Path for optional custom TC overrides file
CUSTOM_OVERRIDES_FILE = DATASETS_DIR / "custom_overrides.yml"

# ============================================================================
# Custom Jinja2 filters (Ansible-compatible)
# ============================================================================
def _filter_bool(value):
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.lower() in ("true", "yes", "1", "on")
    return bool(value)

def _filter_ternary(value, true_val, false_val=""):
    return true_val if value else false_val

def _filter_to_json(value):
    return json.dumps(value, ensure_ascii=False)

def _filter_to_nice_yaml(value, indent=2):
    return yaml.dump(value, default_flow_style=False, indent=indent, allow_unicode=True).rstrip()

def _finalize(value):
    """Convert Python types to YAML-safe strings in template output."""
    if isinstance(value, Undefined):
        return ""
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (list, dict)):
        return json.dumps(value, ensure_ascii=False)
    if value is None:
        return ""
    return value

def create_jinja_env():
    """Create a Jinja2 Environment with Ansible-compatible filters."""
    env = Environment(
        loader=FileSystemLoader(str(TEMPLATE_DIR)),
        keep_trailing_newline=True,
        trim_blocks=True,
        lstrip_blocks=True,
        undefined=Undefined,
        finalize=_finalize,
    )
    env.filters["bool"] = _filter_bool
    env.filters["ternary"] = _filter_ternary
    env.filters["to_json"] = _filter_to_json
    env.filters["to_nice_yaml"] = _filter_to_nice_yaml
    return env

# ============================================================================
# Default template variables
# ============================================================================
SAMPLER_PLUGINS = [
    {"plugin_name": "meminfo", "config_parameters": "", "activation_parameters": "interval=30000000"},
    {"plugin_name": "procstat2", "config_parameters": "", "activation_parameters": "interval=30000000"},
    {"plugin_name": "vmstat", "config_parameters": "", "activation_parameters": "interval=30000000"},
    {"plugin_name": "loadavg", "config_parameters": "", "activation_parameters": "interval=30000000"},
    {"plugin_name": "procnetdev2", "config_parameters": "", "activation_parameters": "interval=30000000"},
]

DEFAULTS = {
    # --- Network ---
    "admin_network": {
        "oim_nic_name": "", "subnet": "", "netmask_bits": "24",
        "primary_oim_admin_ip": "", "primary_oim_bmc_ip": "",
        "router": "", "dynamic_range": "",
        "dns": [], "ntp_servers": [], "additional_subnets": [],
    },
    "ib_network": {"subnet": "", "netmask_bits": "24", "dns": []},
    "network_default_subnet": "",
    "network_default_netmask_bits": "24",

    # --- Provision ---
    "provision_pxe_mapping_file_path": "/opt/omnia/input/project_default/pxe_mapping_file.csv",
    "provision_language": "en_US.UTF-8",
    "provision_default_lease_time": "86400",
    "provision_kernel_version_override": "",

    # --- Omnia clusters ---
    "omnia_slurm_cluster": [],
    "omnia_service_k8s_cluster": [],

    # --- Telemetry sources (primary vars â€” when set, override defaults) ---
    # (leave unset to use defaults; set per-TC to override)
    "telemetry_idrac_collection_targets": ["victoria_metrics", "kafka"],
    "telemetry_kafka_topic_partitions_dict": {"idrac": 1, "ldms": 2},
    "telemetry_ldms_sampler_configurations": SAMPLER_PLUGINS,

    # --- Telemetry defaults (fallback values used by templates) ---
    "telemetry_default_idrac_support": True,
    "telemetry_default_ldms_metrics_enabled": True,
    "telemetry_default_dcgm_support": False,
    "telemetry_default_powerscale_support": True,
    "telemetry_default_powerscale_log_enabled": True,
    "telemetry_default_ufm_metrics_enabled": False,
    "telemetry_default_ufm_logs_enabled": False,
    "telemetry_default_vast_metrics_enabled": False,
    "telemetry_default_vast_logs_enabled": False,
    "telemetry_default_ome_metrics_enabled": True,
    "telemetry_default_ome_logs_enabled": True,
    "telemetry_default_vector_ldms_metrics_enabled": True,
    "telemetry_default_vector_ome_metrics_enabled": True,
    "telemetry_default_vector_ome_logs_enabled": True,
    "telemetry_default_victoria_persistence_size": "8Gi",
    "telemetry_default_victoria_retention_period": 168,
    "telemetry_default_victoria_logs_storage_size": "8Gi",
    "telemetry_default_victoria_logs_retention_period": 168,
    "telemetry_default_kafka_persistence_size": "8Gi",
    "telemetry_default_kafka_log_retention_hours": 168,
    "telemetry_default_kafka_log_retention_bytes": -1,
    "telemetry_default_kafka_log_segment_bytes": 1073741824,
    "telemetry_default_ldms_agg_port": 6001,
    "telemetry_default_ldms_store_port": 6002,
    "telemetry_default_ldms_sampler_port": 10001,
    "telemetry_default_otel_collector_storage_size": "5Gi",
    "telemetry_default_csm_observability_values_file_path": "",
    "telemetry_default_ufm_endpoint": "",
    "telemetry_default_ufm_metrics_port": 9001,
    "telemetry_default_ufm_scrape_interval": "30s",
    "telemetry_default_ufm_scrape_timeout": "15s",
    "telemetry_default_ufm_tls_mode": "self_signed",
    "telemetry_default_ufm_ca_cert_path": "",
    "telemetry_default_ufm_auth_mode": "basic",
    "telemetry_default_vast_endpoint": "",
    "telemetry_default_vast_metrics_port": 443,
    "telemetry_default_vast_metrics_path": "/api/prometheusmetrics/all",
    "telemetry_default_vast_scrape_interval": "30s",
    "telemetry_default_vast_scrape_timeout": "15s",
    "telemetry_default_vast_tls_mode": "self_signed",
    "telemetry_default_vast_ca_cert_path": "",
    "telemetry_default_vast_auth_mode": "basic",

    # --- Build stream ---
    "build_stream_default_enable": False,
    "build_stream_default_host_ip": "",
    "build_stream_default_port": 8010,
    "build_stream_default_aarch64_ip": "",

    # --- GitLab ---
    "gitlab_default_host": "",
    "gitlab_default_project_name": "omnia-catalog",
    "gitlab_default_project_visibility": "private",
    "gitlab_default_branch": "main",
    "gitlab_default_https_port": 443,
    "gitlab_default_min_storage_gb": 20,
    "gitlab_default_min_memory_gb": 4,
    "gitlab_default_min_cpu_cores": 2,
    "gitlab_default_puma_workers": 2,
    "gitlab_default_sidekiq_concurrency": 10,

    # --- Storage ---
    "slurm_nfs_client_params": None,
    "k8s_nfs_client_params": None,
    "storage_powervault_config": {},

    # --- Local repo ---
    "local_repo_user_registry": [],
    "local_repo_user_repo_url_x86_64": [],
    "local_repo_user_repo_url_aarch64": [],
    "local_repo_rhel_os_url_x86_64": [],
    "local_repo_rhel_os_url_aarch64": [],
    "local_repo_additional_repos_x86_64": [],
    "local_repo_additional_repos_aarch64": [],

    # --- High Availability ---
    "ha_service_k8s_cluster_ha": [],

    # --- Credentials ---
    "provision_password": "", "bmc_username": "", "bmc_password": "",
    "s3_access_id": "", "s3_secret_key": "", "pulp_password": "",
    "docker_username": "", "docker_password": "", "slurm_db_password": "",
    "openldap_db_username": "", "openldap_db_password": "",
    "mysqldb_user": "", "mysqldb_password": "", "mysqldb_root_password": "",
    "csi_username": "", "csi_password": "", "ldms_sampler_password": "",
    "postgres_user": "", "postgres_password": "", "gitlab_root_password": "",
    "ome_username": "", "ome_password": "",
    "ufm_username": "", "ufm_password": "",
    "vast_username": "", "vast_password": "",

    # --- PXE ---
    "pxe_mapping_rows": [],
}



# ============================================================================
# TC names and metadata
# ============================================================================
TC_NAMES = [
    "tc01_production_standard",
    "tc02_dell_storage",
    "tc03_minimal_hpc",
    "tc04_k8s_multisubnet",
    "tc05_full_dell_stack",
    "tc06_buildstream_x86",
]

TC_METADATA = {
    "tc01_production_standard": {
        "description": "Production Standard — Slurm+K8s, iDRAC+LDMS, OpenLDAP",
        "coverage": {
            "software_stack": "Slurm+K8s",
            "telemetry_sources": "iDRAC+LDMS",
            "storage_backend": "None",
            "s3_provider": "MinIO",
            "network_topology": "Single-subnet",
            "dns_mode": "Off",
            "architecture": "x86_64",
            "repo_strategy": "partial",
            "options": ["OpenLDAP"],
        },
        "playbook_order": [
            "omnia.sh", "prepare_oim", "local_repo",
            "build_image_x86_64", "provision", "telemetry",
        ],
    },
    "tc02_dell_storage": {
        "description": "Dell Storage + Observability — PowerScale, DNS, OME",
        "coverage": {
            "software_stack": "Slurm+K8s",
            "telemetry_sources": "iDRAC+LDMS+PowerScale",
            "storage_backend": "PowerScale-NFS",
            "s3_provider": "PowerScale-S3",
            "network_topology": "Single-subnet",
            "dns_mode": "On",
            "architecture": "x86_64",
            "repo_strategy": "always",
            "options": ["cloud-init", "OME-discovery", "CSI-PowerScale"],
        },
        "playbook_order": [
            "omnia.sh", "prepare_oim", "local_repo",
            "build_image_x86_64", "provision", "discovery", "telemetry",
        ],
    },
    "tc03_minimal_hpc": {
        "description": "Minimal HPC — Slurm-only, PowerVault, kernel override",
        "coverage": {
            "software_stack": "Slurm-only",
            "telemetry_sources": "None",
            "storage_backend": "PowerVault-iSCSI",
            "s3_provider": "MinIO",
            "network_topology": "Single-subnet",
            "dns_mode": "Off",
            "architecture": "x86_64",
            "repo_strategy": "partial",
            "options": ["kernel_override"],
        },
        "playbook_order": [
            "omnia.sh", "prepare_oim", "local_repo",
            "build_image_x86_64", "provision",
        ],
    },
    "tc04_k8s_multisubnet": {
        "description": "K8s + Multi-Subnet + RHEL Subscription",
        "coverage": {
            "software_stack": "K8s-only",
            "telemetry_sources": "iDRAC",
            "storage_backend": "None",
            "s3_provider": "MinIO",
            "network_topology": "Multi-subnet (3)",
            "dns_mode": "On",
            "architecture": "x86_64",
            "repo_strategy": "RHEL-subscription",
            "options": ["Swap"],
        },
        "playbook_order": [
            "omnia.sh", "prepare_oim", "local_repo",
            "build_image_x86_64", "provision", "telemetry",
        ],
    },
    "tc05_full_dell_stack": {
        "description": "Full Dell Stack — multi-arch, air-gapped, BuildStream",
        "coverage": {
            "software_stack": "Slurm+K8s+MinOS",
            "telemetry_sources": "iDRAC+LDMS+PowerScale+VAST+UFM",
            "storage_backend": "PowerScale+PowerVault+VAST",
            "s3_provider": "PowerScale-S3",
            "network_topology": "Multi-subnet (2)",
            "dns_mode": "On",
            "architecture": "x86_64+aarch64",
            "repo_strategy": "air-gap",
            "options": ["BuildStream", "GitLab", "CSI-PowerScale", "DCGM"],
        },
        "playbook_order": [
            "omnia.sh", "prepare_oim", "local_repo",
            "build_image_x86_64", "build_image_aarch64",
            "provision", "telemetry",
        ],
    },
    "tc06_buildstream_x86": {
        "description": "BuildStream x86_64 — Slurm+K8s, LDMS, BuildStream",
        "coverage": {
            "software_stack": "Slurm+K8s",
            "telemetry_sources": "iDRAC+LDMS",
            "storage_backend": "None",
            "s3_provider": "MinIO",
            "network_topology": "Single-subnet",
            "dns_mode": "Off",
            "architecture": "x86_64",
            "repo_strategy": "partial",
            "options": ["BuildStream", "GitLab"],
        },
        "playbook_order": [
            "omnia.sh", "prepare_oim", "local_repo",
            "build_image_x86_64", "provision", "telemetry",
        ],
    },
}


# ============================================================================
# Helper: standard K8s cluster definition
# ============================================================================
def _k8s_cluster(name, ip_range, nfs="", csi_secret="", csi_values=""):
    """Build a standard K8s cluster override dict."""
    return {
        "cluster_name": name, "deployment": True, "etcd_on_local_disk": False,
        "k8s_cni": "calico", "pod_external_ip_range": ip_range,
        "k8s_service_addresses": "10.233.0.0/18", "k8s_pod_network_cidr": "10.233.64.0/18",
        "nfs_storage_name": nfs, "k8s_crio_storage_size": "20G",
        "csi_powerscale_driver_secret_file_path": csi_secret,
        "csi_powerscale_driver_values_file_path": csi_values,
    }


# ============================================================================
# Standard PXE row builder
# ============================================================================
def _pxe(fg, grp, stag, hostname, mac_suffix,  # pylint: disable=too-many-arguments,too-many-positional-arguments
         admin_ip, bmc_ip, ib_ip="", parent=""):
    """Build a PXE mapping row dict."""
    base_mac = "AA:BB:CC"
    return {
        "FUNCTIONAL_GROUP_NAME": fg, "GROUP_NAME": grp, "SERVICE_TAG": stag,
        "PARENT_SERVICE_TAG": parent, "HOSTNAME": hostname,
        "ADMIN_MAC": f"{base_mac}:01:{mac_suffix}", "ADMIN_IP": admin_ip,
        "BMC_MAC": f"{base_mac}:02:{mac_suffix}", "BMC_IP": bmc_ip,
        "IB_NIC_NAME": "", "IB_IP": ib_ip,
    }


# ============================================================================
# TC-specific variable overrides (only values that differ from DEFAULTS)
# ============================================================================
TC_OVERRIDES = {

# ------------------------------------------------------------------
# TC-01: Production Standard
# ------------------------------------------------------------------
"tc01_production_standard": {
    "admin_network": {
        "oim_nic_name": "eno1", "subnet": "10.10.0.0", "netmask_bits": "24",
        "primary_oim_admin_ip": "10.10.0.1", "primary_oim_bmc_ip": "",
        "router": "10.10.0.1", "dynamic_range": "10.10.0.100-10.10.0.200",
        "dns": [], "ntp_servers": [{"address": "10.10.0.1", "type": "server"}],
        "additional_subnets": [],
    },
    "ib_network": {"subnet": "192.168.0.0", "netmask_bits": "24", "dns": []},
    "omnia_slurm_cluster": [{"cluster_name": "hpc_cluster", "nfs_storage_name": "", "vast_storage_name": ""}],
    "omnia_service_k8s_cluster": [_k8s_cluster("service-cluster", "10.10.0.170-10.10.0.200")],
    "local_repo_user_repo_url_x86_64": [
        {"url": "https://slurm-repo.example.com/rhel10/x86_64/", "gpgkey": "", "sslcacert": "", "sslclientkey": "", "sslclientcert": "", "name": "slurm_custom"},
    ],
    "pxe_mapping_rows": [
        _pxe("service_kube_control_plane_first_x86_64", "mgmt", "SVC001", "k8s-cp01", "01:01", "10.10.0.11", "10.10.0.211"),
        _pxe("service_kube_control_plane_x86_64", "mgmt", "SVC002", "k8s-cp02", "01:02", "10.10.0.12", "10.10.0.212"),
        _pxe("service_kube_node_x86_64", "mgmt", "SVC003", "k8s-wrk01", "01:03", "10.10.0.13", "10.10.0.213"),
        _pxe("slurm_control_node_x86_64", "grp1", "SVC004", "slurm-ctrl01", "01:04", "10.10.0.14", "10.10.0.214"),
        _pxe("slurm_node_x86_64", "grp1", "SVC005", "slurm-n01", "01:05", "10.10.0.15", "10.10.0.215", "192.168.0.15"),
        _pxe("slurm_node_x86_64", "grp1", "SVC006", "slurm-n02", "01:06", "10.10.0.16", "10.10.0.216", "192.168.0.16"),
        _pxe("slurm_node_x86_64", "grp1", "SVC007", "slurm-n03", "01:07", "10.10.0.17", "10.10.0.217", "192.168.0.17"),
        _pxe("slurm_node_x86_64", "grp1", "SVC008", "slurm-n04", "01:08", "10.10.0.18", "10.10.0.218", "192.168.0.18"),
        _pxe("login_node_x86_64", "grp1", "SVC009", "login01", "01:09", "10.10.0.19", "10.10.0.219"),
        _pxe("login_compiler_node_x86_64", "grp1", "SVC010", "login-comp01", "01:0A", "10.10.0.20", "10.10.0.220"),
    ],
},

# ------------------------------------------------------------------
# TC-02: Dell Storage + Observability
# ------------------------------------------------------------------
"tc02_dell_storage": {
    "admin_network": {
        "oim_nic_name": "eno1", "subnet": "10.20.0.0", "netmask_bits": "24",
        "primary_oim_admin_ip": "10.20.0.1", "primary_oim_bmc_ip": "10.20.0.251",
        "router": "10.20.0.1", "dynamic_range": "10.20.0.100-10.20.0.200",
        "dns": ["10.20.0.1"], "ntp_servers": [{"address": "ntp.corp.example.com", "type": "pool"}],
        "additional_subnets": [],
    },
    "ib_network": {"subnet": "192.168.1.0", "netmask_bits": "24", "dns": []},
    "omnia_slurm_cluster": [{"cluster_name": "hpc_cluster", "nfs_storage_name": "powerscale_home", "vast_storage_name": ""}],
    "omnia_service_k8s_cluster": [_k8s_cluster("service-cluster", "10.20.0.170-10.20.0.200", csi_values="/opt/omnia/input/csi_powerscale_values.yaml")],
    "pxe_mapping_rows": [
        {"FUNCTIONAL_GROUP_NAME": "service_kube_control_plane_first_x86_64", "GROUP_NAME": "mgmt", "SERVICE_TAG": "SVC101", "PARENT_SERVICE_TAG": "", "HOSTNAME": "k8s-cp01", "ADMIN_MAC": "BB:CC:DD:01:01:01", "ADMIN_IP": "10.20.0.11", "BMC_MAC": "BB:CC:DD:02:01:01", "BMC_IP": "10.20.0.211", "IB_NIC_NAME": "", "IB_IP": ""},
        {"FUNCTIONAL_GROUP_NAME": "service_kube_control_plane_x86_64", "GROUP_NAME": "mgmt", "SERVICE_TAG": "SVC102", "PARENT_SERVICE_TAG": "", "HOSTNAME": "k8s-cp02", "ADMIN_MAC": "BB:CC:DD:01:01:02", "ADMIN_IP": "10.20.0.12", "BMC_MAC": "BB:CC:DD:02:01:02", "BMC_IP": "10.20.0.212", "IB_NIC_NAME": "", "IB_IP": ""},
        {"FUNCTIONAL_GROUP_NAME": "service_kube_node_x86_64", "GROUP_NAME": "mgmt", "SERVICE_TAG": "SVC103", "PARENT_SERVICE_TAG": "", "HOSTNAME": "k8s-wrk01", "ADMIN_MAC": "BB:CC:DD:01:01:03", "ADMIN_IP": "10.20.0.13", "BMC_MAC": "BB:CC:DD:02:01:03", "BMC_IP": "10.20.0.213", "IB_NIC_NAME": "", "IB_IP": ""},
        {"FUNCTIONAL_GROUP_NAME": "slurm_control_node_x86_64", "GROUP_NAME": "grp1", "SERVICE_TAG": "SVC104", "PARENT_SERVICE_TAG": "", "HOSTNAME": "slurm-ctrl01", "ADMIN_MAC": "BB:CC:DD:01:01:04", "ADMIN_IP": "10.20.0.14", "BMC_MAC": "BB:CC:DD:02:01:04", "BMC_IP": "10.20.0.214", "IB_NIC_NAME": "", "IB_IP": ""},
        {"FUNCTIONAL_GROUP_NAME": "slurm_node_x86_64", "GROUP_NAME": "grp1", "SERVICE_TAG": "SVC105", "PARENT_SERVICE_TAG": "", "HOSTNAME": "slurm-n01", "ADMIN_MAC": "BB:CC:DD:01:01:05", "ADMIN_IP": "10.20.0.15", "BMC_MAC": "BB:CC:DD:02:01:05", "BMC_IP": "10.20.0.215", "IB_NIC_NAME": "", "IB_IP": "192.168.1.15"},
        {"FUNCTIONAL_GROUP_NAME": "slurm_node_x86_64", "GROUP_NAME": "grp1", "SERVICE_TAG": "SVC106", "PARENT_SERVICE_TAG": "", "HOSTNAME": "slurm-n02", "ADMIN_MAC": "BB:CC:DD:01:01:06", "ADMIN_IP": "10.20.0.16", "BMC_MAC": "BB:CC:DD:02:01:06", "BMC_IP": "10.20.0.216", "IB_NIC_NAME": "", "IB_IP": "192.168.1.16"},
        {"FUNCTIONAL_GROUP_NAME": "login_node_x86_64", "GROUP_NAME": "grp1", "SERVICE_TAG": "SVC107", "PARENT_SERVICE_TAG": "", "HOSTNAME": "login01", "ADMIN_MAC": "BB:CC:DD:01:01:07", "ADMIN_IP": "10.20.0.17", "BMC_MAC": "BB:CC:DD:02:01:07", "BMC_IP": "10.20.0.217", "IB_NIC_NAME": "", "IB_IP": ""},
    ],
},

# ------------------------------------------------------------------
# TC-03: Minimal HPC + PowerVault
# ------------------------------------------------------------------
"tc03_minimal_hpc": {
    "admin_network": {
        "oim_nic_name": "eno1", "subnet": "10.30.0.0", "netmask_bits": "24",
        "primary_oim_admin_ip": "10.30.0.1", "primary_oim_bmc_ip": "",
        "router": "10.30.0.1", "dynamic_range": "10.30.0.100-10.30.0.200",
        "dns": [], "ntp_servers": [], "additional_subnets": [],
    },
    "ib_network": {"subnet": "192.168.2.0", "netmask_bits": "24", "dns": []},
    "provision_kernel_version_override": "6.12.0-211.7.3.el10_2.x86_64",
    "omnia_slurm_cluster": [{"cluster_name": "dev_cluster", "nfs_storage_name": "", "vast_storage_name": ""}],
    # No K8s cluster
    "telemetry_idrac_telemetry_support": False,
    "telemetry_ldms_metrics_enabled": False,
    "telemetry_dcgm_support": False,
    "telemetry_powerscale_metrics_enabled": False,
    "telemetry_powerscale_logs_enabled": False,
    "telemetry_ome_metrics_enabled": False,
    "telemetry_ome_logs_enabled": False,
    "telemetry_vector_ldms_metrics_enabled": False,
    "telemetry_vector_ome_metrics_enabled": False,
    "telemetry_vector_ome_logs_enabled": False,
    "storage_powervault_config": {
        "ip": ["10.30.0.50"], "port": 3260,
        "iscsi_initiator": "iqn.2025-01.com.dell:omnia-tc03",
        "volume_id": "00c0ff4343f1f1f1001c8c4e6901000000",
    },
    "pxe_mapping_rows": [
        {"FUNCTIONAL_GROUP_NAME": "slurm_control_node_x86_64", "GROUP_NAME": "grp1", "SERVICE_TAG": "SVC201", "PARENT_SERVICE_TAG": "", "HOSTNAME": "slurm-ctrl01", "ADMIN_MAC": "CC:DD:EE:01:01:01", "ADMIN_IP": "10.30.0.11", "BMC_MAC": "CC:DD:EE:02:01:01", "BMC_IP": "10.30.0.211", "IB_NIC_NAME": "", "IB_IP": ""},
        {"FUNCTIONAL_GROUP_NAME": "slurm_node_x86_64", "GROUP_NAME": "grp1", "SERVICE_TAG": "SVC202", "PARENT_SERVICE_TAG": "", "HOSTNAME": "slurm-n01", "ADMIN_MAC": "CC:DD:EE:01:01:02", "ADMIN_IP": "10.30.0.12", "BMC_MAC": "CC:DD:EE:02:01:02", "BMC_IP": "10.30.0.212", "IB_NIC_NAME": "", "IB_IP": "192.168.2.12"},
        {"FUNCTIONAL_GROUP_NAME": "slurm_node_x86_64", "GROUP_NAME": "grp1", "SERVICE_TAG": "SVC203", "PARENT_SERVICE_TAG": "", "HOSTNAME": "slurm-n02", "ADMIN_MAC": "CC:DD:EE:01:01:03", "ADMIN_IP": "10.30.0.13", "BMC_MAC": "CC:DD:EE:02:01:03", "BMC_IP": "10.30.0.213", "IB_NIC_NAME": "", "IB_IP": "192.168.2.13"},
        {"FUNCTIONAL_GROUP_NAME": "login_node_x86_64", "GROUP_NAME": "grp1", "SERVICE_TAG": "SVC204", "PARENT_SERVICE_TAG": "", "HOSTNAME": "login01", "ADMIN_MAC": "CC:DD:EE:01:01:04", "ADMIN_IP": "10.30.0.14", "BMC_MAC": "CC:DD:EE:02:01:04", "BMC_IP": "10.30.0.214", "IB_NIC_NAME": "", "IB_IP": ""},
    ],
},

# ------------------------------------------------------------------
# TC-04: K8s + Multi-Subnet + RHEL Subscription
# ------------------------------------------------------------------
"tc04_k8s_multisubnet": {
    "admin_network": {
        "oim_nic_name": "eno1", "subnet": "10.40.0.0", "netmask_bits": "24",
        "primary_oim_admin_ip": "10.40.0.1", "primary_oim_bmc_ip": "",
        "router": "10.40.0.1", "dynamic_range": "10.40.0.100-10.40.0.200",
        "dns": ["10.40.0.1"],
        "ntp_servers": [{"address": "10.40.0.1", "type": "server"}],
        "additional_subnets": [
            {"subnet": "10.40.1.0", "netmask_bits": "24", "router": "10.40.1.1", "dynamic_range": "10.40.1.100-10.40.1.200"},
            {"subnet": "10.40.2.0", "netmask_bits": "24", "router": "10.40.2.1", "dynamic_range": "10.40.2.100-10.40.2.200"},
        ],
    },
    "ib_network": {"subnet": "192.168.3.0", "netmask_bits": "24", "dns": []},
    # No Slurm cluster
    "omnia_service_k8s_cluster": [_k8s_cluster("infra-cluster", "10.40.0.170-10.40.0.200")],
    "telemetry_ldms_metrics_enabled": False,
    "telemetry_dcgm_support": False,
    "telemetry_powerscale_metrics_enabled": False,
    "telemetry_powerscale_logs_enabled": False,
    "telemetry_ome_metrics_enabled": False,
    "telemetry_ome_logs_enabled": False,
    "telemetry_vector_ldms_metrics_enabled": False,
    "telemetry_vector_ome_metrics_enabled": False,
    "telemetry_vector_ome_logs_enabled": False,
    "pxe_mapping_rows": [
        {"FUNCTIONAL_GROUP_NAME": "service_kube_control_plane_first_x86_64", "GROUP_NAME": "mgmt", "SERVICE_TAG": "SVC301", "PARENT_SERVICE_TAG": "", "HOSTNAME": "k8s-cp01", "ADMIN_MAC": "DD:EE:FF:01:01:01", "ADMIN_IP": "10.40.0.11", "BMC_MAC": "DD:EE:FF:02:01:01", "BMC_IP": "10.40.0.211", "IB_NIC_NAME": "", "IB_IP": ""},
        {"FUNCTIONAL_GROUP_NAME": "service_kube_control_plane_x86_64", "GROUP_NAME": "mgmt", "SERVICE_TAG": "SVC302", "PARENT_SERVICE_TAG": "", "HOSTNAME": "k8s-cp02", "ADMIN_MAC": "DD:EE:FF:01:01:02", "ADMIN_IP": "10.40.1.11", "BMC_MAC": "DD:EE:FF:02:01:02", "BMC_IP": "10.40.1.211", "IB_NIC_NAME": "", "IB_IP": ""},
        {"FUNCTIONAL_GROUP_NAME": "service_kube_node_x86_64", "GROUP_NAME": "mgmt", "SERVICE_TAG": "SVC303", "PARENT_SERVICE_TAG": "", "HOSTNAME": "k8s-wrk01", "ADMIN_MAC": "DD:EE:FF:01:01:03", "ADMIN_IP": "10.40.1.12", "BMC_MAC": "DD:EE:FF:02:01:03", "BMC_IP": "10.40.1.212", "IB_NIC_NAME": "", "IB_IP": ""},
        {"FUNCTIONAL_GROUP_NAME": "service_kube_node_x86_64", "GROUP_NAME": "mgmt", "SERVICE_TAG": "SVC304", "PARENT_SERVICE_TAG": "", "HOSTNAME": "k8s-wrk02", "ADMIN_MAC": "DD:EE:FF:01:01:04", "ADMIN_IP": "10.40.2.11", "BMC_MAC": "DD:EE:FF:02:01:04", "BMC_IP": "10.40.2.211", "IB_NIC_NAME": "", "IB_IP": ""},
    ],
},

# ------------------------------------------------------------------
# TC-05: Full Dell Stack (Multi-Arch, Air-Gapped, BuildStream)
# ------------------------------------------------------------------
"tc05_full_dell_stack": {
    "admin_network": {
        "oim_nic_name": "eno1", "subnet": "10.50.0.0", "netmask_bits": "24",
        "primary_oim_admin_ip": "10.50.0.1", "primary_oim_bmc_ip": "10.50.0.251",
        "router": "10.50.0.1", "dynamic_range": "10.50.0.100-10.50.0.200",
        "dns": ["10.50.0.1"],
        "ntp_servers": [{"address": "10.50.0.1", "type": "server"}],
        "additional_subnets": [
            {"subnet": "10.50.1.0", "netmask_bits": "24", "router": "10.50.1.1", "dynamic_range": "10.50.1.100-10.50.1.200"},
        ],
    },
    "ib_network": {"subnet": "192.168.4.0", "netmask_bits": "24", "dns": []},
    "omnia_slurm_cluster": [{"cluster_name": "hpc_production", "nfs_storage_name": "powerscale_home", "vast_storage_name": "vast_scratch"}],
    "omnia_service_k8s_cluster": [_k8s_cluster("service-cluster", "10.50.0.170-10.50.0.200", csi_values="/opt/omnia/input/csi_powerscale_values.yaml")],
    # All telemetry enabled including DCGM + VAST
    "telemetry_dcgm_support": True,
    "telemetry_ufm_metrics_enabled": True,
    "telemetry_ufm_logs_enabled": True,
    "telemetry_vast_metrics_enabled": True,
    "telemetry_vast_logs_enabled": True,
    "telemetry_victoria_persistence_size": "16Gi",
    "telemetry_victoria_retention_period": 336,
    "telemetry_victoria_logs_storage_size": "16Gi",
    "telemetry_victoria_logs_retention_period": 336,
    "telemetry_kafka_persistence_size": "16Gi",
    "telemetry_kafka_log_retention_hours": 336,
    "telemetry_kafka_topic_partitions_dict": {"idrac": 2, "ldms": 4},
    "telemetry_otel_collector_storage_size": "10Gi",
    "telemetry_ufm_endpoint": "10.50.0.240",
    "telemetry_vast_endpoint": "10.50.0.230",
    "build_stream_enable": True,
    "build_stream_host_ip": "10.50.0.1",
    "build_stream_aarch64_ip": "10.50.0.2",
    "gitlab_host": "10.50.0.1",
    "storage_powervault_config": {
        "ip": ["10.50.0.50", "10.50.0.51"], "port": 3260,
        "iscsi_initiator": "iqn.2025-01.com.dell:omnia-tc05",
        "volume_id": "00c0ff5555aabbcc001c8c4e6901000000",
    },
    "local_repo_user_registry": [{"host": "10.50.0.1:5000", "cert_path": "", "key_path": ""}],
    "local_repo_user_repo_url_x86_64": [
        {"url": "http://10.50.0.1:8080/repos/slurm_custom/x86_64/", "gpgkey": "", "sslcacert": "", "sslclientkey": "", "sslclientcert": "", "name": "slurm_custom"},
    ],
    "local_repo_user_repo_url_aarch64": [
        {"url": "http://10.50.0.1:8080/repos/slurm_custom/aarch64/", "gpgkey": "", "sslcacert": "", "sslclientkey": "", "sslclientcert": "", "name": "slurm_custom"},
    ],
    "local_repo_rhel_os_url_x86_64": [
        {"url": "http://10.50.0.1:8080/repos/rhel10/codeready-builder/x86_64/", "gpgkey": "", "sslcacert": "", "sslclientkey": "", "sslclientcert": "", "name": "codeready-builder"},
        {"url": "http://10.50.0.1:8080/repos/rhel10/baseos/x86_64/", "gpgkey": "", "sslcacert": "", "sslclientkey": "", "sslclientcert": "", "name": "baseos"},
        {"url": "http://10.50.0.1:8080/repos/rhel10/appstream/x86_64/", "gpgkey": "", "sslcacert": "", "sslclientkey": "", "sslclientcert": "", "name": "appstream"},
    ],
    "local_repo_rhel_os_url_aarch64": [
        {"url": "http://10.50.0.1:8080/repos/rhel10/codeready-builder/aarch64/", "gpgkey": "", "sslcacert": "", "sslclientkey": "", "sslclientcert": "", "name": "codeready-builder"},
        {"url": "http://10.50.0.1:8080/repos/rhel10/baseos/aarch64/", "gpgkey": "", "sslcacert": "", "sslclientkey": "", "sslclientcert": "", "name": "baseos"},
        {"url": "http://10.50.0.1:8080/repos/rhel10/appstream/aarch64/", "gpgkey": "", "sslcacert": "", "sslclientkey": "", "sslclientcert": "", "name": "appstream"},
    ],
    "pxe_mapping_rows": [
        {"FUNCTIONAL_GROUP_NAME": "service_kube_control_plane_first_x86_64", "GROUP_NAME": "mgmt", "SERVICE_TAG": "SVC401", "PARENT_SERVICE_TAG": "", "HOSTNAME": "k8s-cp01", "ADMIN_MAC": "EE:FF:00:01:01:01", "ADMIN_IP": "10.50.0.11", "BMC_MAC": "EE:FF:00:02:01:01", "BMC_IP": "10.50.0.211", "IB_NIC_NAME": "", "IB_IP": ""},
        {"FUNCTIONAL_GROUP_NAME": "service_kube_control_plane_x86_64", "GROUP_NAME": "mgmt", "SERVICE_TAG": "SVC402", "PARENT_SERVICE_TAG": "", "HOSTNAME": "k8s-cp02", "ADMIN_MAC": "EE:FF:00:01:01:02", "ADMIN_IP": "10.50.0.12", "BMC_MAC": "EE:FF:00:02:01:02", "BMC_IP": "10.50.0.212", "IB_NIC_NAME": "", "IB_IP": ""},
        {"FUNCTIONAL_GROUP_NAME": "service_kube_node_x86_64", "GROUP_NAME": "mgmt", "SERVICE_TAG": "SVC403", "PARENT_SERVICE_TAG": "", "HOSTNAME": "k8s-wrk01", "ADMIN_MAC": "EE:FF:00:01:01:03", "ADMIN_IP": "10.50.0.13", "BMC_MAC": "EE:FF:00:02:01:03", "BMC_IP": "10.50.0.213", "IB_NIC_NAME": "", "IB_IP": ""},
        {"FUNCTIONAL_GROUP_NAME": "slurm_control_node_x86_64", "GROUP_NAME": "grp1", "SERVICE_TAG": "SVC404", "PARENT_SERVICE_TAG": "", "HOSTNAME": "slurm-ctrl01", "ADMIN_MAC": "EE:FF:00:01:01:04", "ADMIN_IP": "10.50.0.14", "BMC_MAC": "EE:FF:00:02:01:04", "BMC_IP": "10.50.0.214", "IB_NIC_NAME": "", "IB_IP": ""},
        {"FUNCTIONAL_GROUP_NAME": "slurm_node_x86_64", "GROUP_NAME": "grp1", "SERVICE_TAG": "SVC405", "PARENT_SERVICE_TAG": "", "HOSTNAME": "slurm-x86-01", "ADMIN_MAC": "EE:FF:00:01:01:05", "ADMIN_IP": "10.50.0.15", "BMC_MAC": "EE:FF:00:02:01:05", "BMC_IP": "10.50.0.215", "IB_NIC_NAME": "ib0", "IB_IP": "192.168.4.15"},
        {"FUNCTIONAL_GROUP_NAME": "slurm_node_x86_64", "GROUP_NAME": "grp1", "SERVICE_TAG": "SVC406", "PARENT_SERVICE_TAG": "", "HOSTNAME": "slurm-x86-02", "ADMIN_MAC": "EE:FF:00:01:01:06", "ADMIN_IP": "10.50.0.16", "BMC_MAC": "EE:FF:00:02:01:06", "BMC_IP": "10.50.0.216", "IB_NIC_NAME": "ib0", "IB_IP": "192.168.4.16"},
        {"FUNCTIONAL_GROUP_NAME": "slurm_node_aarch64", "GROUP_NAME": "grp1", "SERVICE_TAG": "SVC407", "PARENT_SERVICE_TAG": "", "HOSTNAME": "slurm-arm-01", "ADMIN_MAC": "EE:FF:00:01:01:07", "ADMIN_IP": "10.50.1.11", "BMC_MAC": "EE:FF:00:02:01:07", "BMC_IP": "10.50.1.211", "IB_NIC_NAME": "", "IB_IP": ""},
        {"FUNCTIONAL_GROUP_NAME": "slurm_node_aarch64", "GROUP_NAME": "grp1", "SERVICE_TAG": "SVC408", "PARENT_SERVICE_TAG": "", "HOSTNAME": "slurm-arm-02", "ADMIN_MAC": "EE:FF:00:01:01:08", "ADMIN_IP": "10.50.1.12", "BMC_MAC": "EE:FF:00:02:01:08", "BMC_IP": "10.50.1.212", "IB_NIC_NAME": "", "IB_IP": ""},
        {"FUNCTIONAL_GROUP_NAME": "login_node_x86_64", "GROUP_NAME": "grp1", "SERVICE_TAG": "SVC409", "PARENT_SERVICE_TAG": "", "HOSTNAME": "login-x86-01", "ADMIN_MAC": "EE:FF:00:01:01:09", "ADMIN_IP": "10.50.0.17", "BMC_MAC": "EE:FF:00:02:01:09", "BMC_IP": "10.50.0.217", "IB_NIC_NAME": "", "IB_IP": ""},
        {"FUNCTIONAL_GROUP_NAME": "login_node_aarch64", "GROUP_NAME": "grp1", "SERVICE_TAG": "SVC410", "PARENT_SERVICE_TAG": "", "HOSTNAME": "login-arm-01", "ADMIN_MAC": "EE:FF:00:01:01:0A", "ADMIN_IP": "10.50.1.13", "BMC_MAC": "EE:FF:00:02:01:0A", "BMC_IP": "10.50.1.213", "IB_NIC_NAME": "", "IB_IP": ""},
        {"FUNCTIONAL_GROUP_NAME": "login_compiler_node_x86_64", "GROUP_NAME": "grp1", "SERVICE_TAG": "SVC411", "PARENT_SERVICE_TAG": "", "HOSTNAME": "login-comp-x86", "ADMIN_MAC": "EE:FF:00:01:01:0B", "ADMIN_IP": "10.50.0.18", "BMC_MAC": "EE:FF:00:02:01:0B", "BMC_IP": "10.50.0.218", "IB_NIC_NAME": "", "IB_IP": ""},
        {"FUNCTIONAL_GROUP_NAME": "login_compiler_node_aarch64", "GROUP_NAME": "grp1", "SERVICE_TAG": "SVC412", "PARENT_SERVICE_TAG": "", "HOSTNAME": "login-comp-arm", "ADMIN_MAC": "EE:FF:00:01:01:0C", "ADMIN_IP": "10.50.1.14", "BMC_MAC": "EE:FF:00:02:01:0C", "BMC_IP": "10.50.1.214", "IB_NIC_NAME": "", "IB_IP": ""},
        {"FUNCTIONAL_GROUP_NAME": "os_x86_64", "GROUP_NAME": "bare", "SERVICE_TAG": "SVC413", "PARENT_SERVICE_TAG": "", "HOSTNAME": "bare-x86-01", "ADMIN_MAC": "EE:FF:00:01:01:0D", "ADMIN_IP": "10.50.0.19", "BMC_MAC": "EE:FF:00:02:01:0D", "BMC_IP": "10.50.0.219", "IB_NIC_NAME": "", "IB_IP": ""},
        {"FUNCTIONAL_GROUP_NAME": "os_aarch64", "GROUP_NAME": "bare", "SERVICE_TAG": "SVC414", "PARENT_SERVICE_TAG": "", "HOSTNAME": "bare-arm-01", "ADMIN_MAC": "EE:FF:00:01:01:0E", "ADMIN_IP": "10.50.1.15", "BMC_MAC": "EE:FF:00:02:01:0E", "BMC_IP": "10.50.1.215", "IB_NIC_NAME": "", "IB_IP": ""},
    ],
},

# ------------------------------------------------------------------
# TC-06: BuildStream x86_64
# ------------------------------------------------------------------
"tc06_buildstream_x86": {
    "admin_network": {
        "oim_nic_name": "eno1", "subnet": "10.60.0.0", "netmask_bits": "24",
        "primary_oim_admin_ip": "10.60.0.1", "primary_oim_bmc_ip": "10.60.0.251",
        "router": "10.60.0.1", "dynamic_range": "10.60.0.100-10.60.0.200",
        "dns": ["10.60.0.1"], "ntp_servers": [{"address": "10.60.0.1", "type": "server"}],
        "additional_subnets": [],
    },
    "ib_network": {"subnet": "192.168.5.0", "netmask_bits": "24", "dns": []},
    "omnia_slurm_cluster": [{"cluster_name": "bs_hpc_cluster", "nfs_storage_name": "", "vast_storage_name": ""}],
    "omnia_service_k8s_cluster": [_k8s_cluster("bs-service-cluster", "10.60.0.170-10.60.0.200")],
    "telemetry_dcgm_support": False,
    "telemetry_powerscale_metrics_enabled": False,
    "telemetry_powerscale_logs_enabled": False,
    "telemetry_ome_metrics_enabled": False,
    "telemetry_ome_logs_enabled": False,
    "telemetry_vector_ome_metrics_enabled": False,
    "telemetry_vector_ome_logs_enabled": False,
    "telemetry_idrac_collection_targets": ["victoria_metrics"],
    "build_stream_enable": True,
    "build_stream_host_ip": "10.60.0.1",
    "gitlab_host": "10.60.0.1",
    "pxe_mapping_rows": [
        {"FUNCTIONAL_GROUP_NAME": "service_kube_control_plane_first_x86_64", "GROUP_NAME": "mgmt", "SERVICE_TAG": "SVC601", "PARENT_SERVICE_TAG": "", "HOSTNAME": "k8s-cp01", "ADMIN_MAC": "FF:00:00:01:01:01", "ADMIN_IP": "10.60.0.11", "BMC_MAC": "FF:00:00:02:01:01", "BMC_IP": "10.60.0.211", "IB_NIC_NAME": "", "IB_IP": ""},
        {"FUNCTIONAL_GROUP_NAME": "service_kube_control_plane_x86_64", "GROUP_NAME": "mgmt", "SERVICE_TAG": "SVC602", "PARENT_SERVICE_TAG": "", "HOSTNAME": "k8s-cp02", "ADMIN_MAC": "FF:00:00:01:01:02", "ADMIN_IP": "10.60.0.12", "BMC_MAC": "FF:00:00:02:01:02", "BMC_IP": "10.60.0.212", "IB_NIC_NAME": "", "IB_IP": ""},
        {"FUNCTIONAL_GROUP_NAME": "service_kube_node_x86_64", "GROUP_NAME": "mgmt", "SERVICE_TAG": "SVC603", "PARENT_SERVICE_TAG": "", "HOSTNAME": "k8s-wrk01", "ADMIN_MAC": "FF:00:00:01:01:03", "ADMIN_IP": "10.60.0.13", "BMC_MAC": "FF:00:00:02:01:03", "BMC_IP": "10.60.0.213", "IB_NIC_NAME": "", "IB_IP": ""},
        {"FUNCTIONAL_GROUP_NAME": "slurm_control_node_x86_64", "GROUP_NAME": "grp1", "SERVICE_TAG": "SVC604", "PARENT_SERVICE_TAG": "", "HOSTNAME": "slurm-ctrl01", "ADMIN_MAC": "FF:00:00:01:01:04", "ADMIN_IP": "10.60.0.14", "BMC_MAC": "FF:00:00:02:01:04", "BMC_IP": "10.60.0.214", "IB_NIC_NAME": "", "IB_IP": ""},
        {"FUNCTIONAL_GROUP_NAME": "slurm_node_x86_64", "GROUP_NAME": "grp1", "SERVICE_TAG": "SVC605", "PARENT_SERVICE_TAG": "", "HOSTNAME": "slurm-01", "ADMIN_MAC": "FF:00:00:01:01:05", "ADMIN_IP": "10.60.0.15", "BMC_MAC": "FF:00:00:02:01:05", "BMC_IP": "10.60.0.215", "IB_NIC_NAME": "", "IB_IP": ""},
        {"FUNCTIONAL_GROUP_NAME": "slurm_node_x86_64", "GROUP_NAME": "grp1", "SERVICE_TAG": "SVC606", "PARENT_SERVICE_TAG": "", "HOSTNAME": "slurm-02", "ADMIN_MAC": "FF:00:00:01:01:06", "ADMIN_IP": "10.60.0.16", "BMC_MAC": "FF:00:00:02:01:06", "BMC_IP": "10.60.0.216", "IB_NIC_NAME": "", "IB_IP": ""},
        {"FUNCTIONAL_GROUP_NAME": "login_node_x86_64", "GROUP_NAME": "grp1", "SERVICE_TAG": "SVC607", "PARENT_SERVICE_TAG": "", "HOSTNAME": "login-01", "ADMIN_MAC": "FF:00:00:01:01:07", "ADMIN_IP": "10.60.0.17", "BMC_MAC": "FF:00:00:02:01:07", "BMC_IP": "10.60.0.217", "IB_NIC_NAME": "", "IB_IP": ""},
        {"FUNCTIONAL_GROUP_NAME": "login_compiler_node_x86_64", "GROUP_NAME": "grp1", "SERVICE_TAG": "SVC608", "PARENT_SERVICE_TAG": "", "HOSTNAME": "login-comp-01", "ADMIN_MAC": "FF:00:00:01:01:08", "ADMIN_IP": "10.60.0.18", "BMC_MAC": "FF:00:00:02:01:08", "BMC_IP": "10.60.0.218", "IB_NIC_NAME": "", "IB_IP": ""},
    ],
},
}  # end TC_OVERRIDES


# ============================================================================
# Non-templated file definitions per TC
# ============================================================================
def _sw(repo_config, softwares, slurm_custom=None, service_k8s=None, additional_packages=None):
    """Build a software_config.json dict."""
    d = {"cluster_os_type": "rhel", "cluster_os_version": "10.0", "repo_config": repo_config, "softwares": softwares}
    if slurm_custom:
        d["slurm_custom"] = slurm_custom
    if service_k8s:
        d["service_k8s"] = service_k8s
    if additional_packages:
        d["additional_packages"] = additional_packages
    return d


_SLURM_ROLES = [{"name": "slurm_control_node"}, {"name": "slurm_node"}, {"name": "login_node"}, {"name": "login_compiler_node"}]
_K8S_ROLES = [{"name": "service_kube_control_plane_first"}, {"name": "service_kube_control_plane"}, {"name": "service_kube_node"}]
_ALL_ROLES = _K8S_ROLES + _SLURM_ROLES
_ALL_ROLES_OS = _ALL_ROLES + [{"name": "os"}]


def _x(names):
    """Build x86_64-only package entries."""
    return [{"name": n, "arch": ["x86_64"]} for n in names]


def _xa(names):
    """Build x86_64+aarch64 package entries."""
    return [{"name": n, "arch": ["x86_64", "aarch64"]} for n in names]


def _xv(name, ver):
    """Build a versioned x86_64 package entry."""
    return [{"name": name, "version": ver, "arch": ["x86_64"]}]


SOFTWARE_CONFIGS = {
    "tc01_production_standard": _sw("partial",
        _x(["default_packages", "admin_debug_packages", "openldap", "slurm_custom"]) + _xv("service_k8s", "1.35.1") + _x(["ldms", "additional_packages"]),
        _SLURM_ROLES, _K8S_ROLES, _ALL_ROLES),
    "tc02_dell_storage": _sw("always",
        _x(["default_packages", "admin_debug_packages", "slurm_custom"]) + _xv("service_k8s", "1.35.1") + [{"name": "csi_driver_powerscale", "version": "v2.16.0", "arch": ["x86_64"]}] + _x(["ldms", "additional_packages"]),
        _SLURM_ROLES, _K8S_ROLES, _ALL_ROLES),
    "tc03_minimal_hpc": _sw("partial",
        _x(["default_packages", "admin_debug_packages", "slurm_custom", "additional_packages"]),
        _SLURM_ROLES, None, [{"name": "slurm_control_node"}, {"name": "slurm_node"}]),
    "tc04_k8s_multisubnet": _sw("partial",
        _x(["default_packages", "admin_debug_packages"]) + _xv("service_k8s", "1.35.1") + _x(["additional_packages"]),
        None, _K8S_ROLES, _K8S_ROLES),
    "tc05_full_dell_stack": _sw("always",
        _xa(["default_packages", "admin_debug_packages", "openldap", "slurm_custom"]) + _xv("service_k8s", "1.35.1") + [{"name": "ucx", "version": "1.19.0", "arch": ["x86_64", "aarch64"]}, {"name": "openmpi", "version": "5.0.8", "arch": ["x86_64", "aarch64"]}, {"name": "csi_driver_powerscale", "version": "v2.16.0", "arch": ["x86_64"]}] + _xa(["ldms", "additional_packages"]),
        _SLURM_ROLES, _K8S_ROLES, _ALL_ROLES_OS),
    "tc06_buildstream_x86": _sw("partial",
        _x(["default_packages", "admin_debug_packages", "slurm_custom"]) + _xv("service_k8s", "1.35.1") + _x(["ldms", "additional_packages"]),
        _SLURM_ROLES, _K8S_ROLES, _ALL_ROLES),
}

# discovery_config.yml overrides (TC -> {key: value})
DISCOVERY_OVERRIDES = {
    "tc02_dell_storage": {"enable_bmc_discovery": True, "ome_ip": "10.20.0.250"},
}

# additional_cloud_init.yml overrides
CLOUD_INIT_OVERRIDES = {
    "tc02_dell_storage": {
        "common": {
            "write_files": [{"path": "/etc/motd", "content": "Welcome to TC-02 Dell Storage Cluster\n", "permissions": "0644"}],
            "runcmd": ["echo 'TC-02 custom setup complete' >> /var/log/custom_setup.log"],
        },
        "groups": {
            "slurm_node_x86_64": {"runcmd": ["echo 'Slurm compute node initialized' >> /var/log/custom.log"]},
        },
    },
}

# user_registry_credential.yml overrides
USER_REG_CRED_OVERRIDES = {
    "tc05_full_dell_stack": [{"name": "10.50.0.1:5000", "username": "", "password": ""}],
}

# storage_config post-processing: extra mounts to append
STORAGE_EXTRA_MOUNTS = {
    "tc02_dell_storage": [
        {"name": "powerscale_home", "source": "10.43.1.10:/ifs/data/hpc_home", "mount_point": "/home", "fs_type": "nfs4", "mnt_opts": "defaults,nofail,vers=4.1", "functional_group_prefix": ["slurm", "login"]},
        {"name": "powerscale_scratch", "source": "10.43.1.10:/ifs/data/hpc_scratch", "mount_point": "/scratch", "fs_type": "nfs4", "mnt_opts": "defaults,nofail,vers=4.1", "functional_group_prefix": ["slurm", "login"]},
    ],
    "tc05_full_dell_stack": [
        {"name": "powerscale_home", "source": "10.43.1.10:/ifs/data/hpc_home", "mount_point": "/home", "fs_type": "nfs4", "mnt_opts": "defaults,nofail,vers=4.1", "functional_group_prefix": ["slurm", "login"]},
        {"name": "vast_scratch", "source": "10.43.2.10:/vast/scratch", "mount_point": "/scratch", "fs_type": "nfs", "mnt_opts": "defaults,nofail,vers=3,tcp", "functional_group_prefix": ["slurm", "login"]},
        {"name": "vast_apps", "source": "10.43.2.10:/vast/apps", "mount_point": "/apps", "fs_type": "nfs", "mnt_opts": "defaults,nofail,vers=3,tcp", "functional_group_prefix": ["slurm", "login"]},
    ],
}

# S3 config overrides (default is minio with empty endpoint)
STORAGE_S3_OVERRIDES = {
    "tc02_dell_storage": {"provider": "powerscale", "endpoint_url": "https://10.43.1.11:9021"},
    "tc05_full_dell_stack": {"provider": "powerscale", "endpoint_url": "https://10.43.1.11:9021"},
}

# Swap config (TC-04 only)
STORAGE_SWAP = {
    "tc04_k8s_multisubnet": [{"name": "k8s_swap", "filename": "/swapfile", "size": "2G", "maxsize": "4G", "functional_group_prefix": ["service_kube_node"]}],
}

# DNS enabled override for provision_config (template has dns_enabled: false as default)
PROVISION_DNS_ENABLED = {"tc02_dell_storage", "tc04_k8s_multisubnet", "tc05_full_dell_stack"}

# Additional cloud-init path override
PROVISION_CLOUD_INIT = {
    "tc02_dell_storage": "/opt/omnia/input/project_default/additional_cloud_init.yml",
}

# TC-05 telemetry_storage_config.yml resource overrides (text replacements on static template)
TC05_TELEM_STORAGE_REPLACEMENTS = [
    # vmstorage: double resources
    ('        memory: "1Gi"\n        cpu: "250m"\n      limits:\n        memory: "2Gi"\n        cpu: "1000m"',
     '        memory: "2Gi"\n        cpu: "500m"\n      limits:\n        memory: "4Gi"\n        cpu: "2000m"'),
    # vminsert: double
    ('  vminsert:\n    replicas: 2\n    resources:\n      requests:\n        memory: "256Mi"\n        cpu: "100m"\n      limits:\n        memory: "512Mi"\n        cpu: "500m"',
     '  vminsert:\n    replicas: 2\n    resources:\n      requests:\n        memory: "512Mi"\n        cpu: "200m"\n      limits:\n        memory: "1Gi"\n        cpu: "1000m"'),
    # vmselect: double
    ('  vmselect:\n    replicas: 2\n    resources:\n      requests:\n        memory: "256Mi"\n        cpu: "100m"\n      limits:\n        memory: "512Mi"\n        cpu: "500m"',
     '  vmselect:\n    replicas: 2\n    resources:\n      requests:\n        memory: "512Mi"\n        cpu: "200m"\n      limits:\n        memory: "1Gi"\n        cpu: "1000m"'),
    # vmagent: double
    ('  vmagent:\n    replicas: 2\n    resources:\n      requests:\n        memory: "128Mi"\n        cpu: "50m"\n      limits:\n        memory: "512Mi"\n        cpu: "250m"',
     '  vmagent:\n    replicas: 2\n    resources:\n      requests:\n        memory: "256Mi"\n        cpu: "100m"\n      limits:\n        memory: "1Gi"\n        cpu: "500m"'),
    # kafka: double
    ('  kafka:\n    resources:\n      requests:\n        memory: "512Mi"\n        cpu: "200m"\n      limits:\n        memory: "1Gi"\n        cpu: "1000m"',
     '  kafka:\n    resources:\n      requests:\n        memory: "1Gi"\n        cpu: "500m"\n      limits:\n        memory: "2Gi"\n        cpu: "2000m"'),
    # entity_operator limits memory
    ('        limits:\n          memory: "512Mi"\n          cpu: "1000m"',
     '        limits:\n          memory: "1Gi"\n          cpu: "1000m"'),
]


# ============================================================================
# Utility functions
# ============================================================================
def deep_merge(base, override):
    """Deep merge override into base, returning a new dict."""
    result = copy.deepcopy(base)
    for k, v in override.items():
        if isinstance(v, dict) and isinstance(result.get(k), dict):
            result[k] = deep_merge(result[k], v)
        else:
            result[k] = copy.deepcopy(v)
    return result


def render_mounts_yaml(mounts):
    """Render a list of mount dicts as YAML block text."""
    if not mounts:
        return ""
    lines = ["mounts:"]
    for m in mounts:
        lines.append(f'  - name: "{m["name"]}"')
        lines.append(f'    source: "{m["source"]}"')
        lines.append(f'    mount_point: "{m["mount_point"]}"')
        if "mount_params" in m:
            lines.append(f'    mount_params: "{m["mount_params"]}"')
        if "fs_type" in m:
            lines.append(f'    fs_type: "{m["fs_type"]}"')
        if "mnt_opts" in m:
            lines.append(f'    mnt_opts: "{m["mnt_opts"]}"')
        if m.get("mount_on_oim"):
            lines.append('    mount_on_oim: true')
        lines.append(f'    functional_group_prefix: {json.dumps(m["functional_group_prefix"])}')
        lines.append("")
    return "\n".join(lines)


def render_swap_yaml(swap_list):
    """Render swap configuration as YAML."""
    if not swap_list:
        return ""
    lines = ["swap:"]
    for s in swap_list:
        lines.append(f'  - name: "{s["name"]}"')
        lines.append(f'    filename: "{s["filename"]}"')
        lines.append(f'    size: "{s["size"]}"')
        if "maxsize" in s:
            lines.append(f'    maxsize: "{s["maxsize"]}"')
        lines.append(f'    functional_group_prefix: {json.dumps(s["functional_group_prefix"])}')
        lines.append("")
    return "\n".join(lines)


# ============================================================================
# Post-processing helpers
# ============================================================================
def _postprocess_provision(rendered, tc):
    """Apply provision_config.yml post-processing overrides."""
    if tc in PROVISION_DNS_ENABLED:
        rendered = re.sub(
            r'^(dns_enabled:)\s*.*$', r'\1 true',
            rendered, count=1, flags=re.MULTILINE,
        )
    if tc in PROVISION_CLOUD_INIT:
        rendered = re.sub(
            r'^(additional_cloud_init_config_file:)\s*.*$',
            rf'\1 "{PROVISION_CLOUD_INIT[tc]}"',
            rendered, count=1, flags=re.MULTILINE,
        )
    return rendered


def _postprocess_omnia_config(rendered, overrides):
    """Uncomment and set vast_storage_name for TCs that need it."""
    for sc in overrides.get("omnia_slurm_cluster", []):
        vsn = sc.get("vast_storage_name", "")
        if vsn:
            rendered = rendered.replace(
                '# vast_storage_name: "vast_storage"',
                f'vast_storage_name: "{vsn}"', 1,
            )
    return rendered


def _postprocess_storage(rendered, tc):
    """Apply storage_config.yml mount, S3, and swap overrides."""
    extra_mounts = STORAGE_EXTRA_MOUNTS.get(tc, [])
    if extra_mounts:
        mounts_yaml = render_mounts_yaml(extra_mounts)
        has_mounts = bool(re.search(r'^\s*mounts:', rendered, re.MULTILINE))
        if has_mounts:
            rendered = re.sub(
                r'^\s*mounts:.*?(?=\n\n)', mounts_yaml.rstrip(),
                rendered, count=1, flags=re.DOTALL | re.MULTILINE,
            )
        else:
            rendered = rendered.replace(
                "  # VAST Storage", mounts_yaml + "\n\n  # VAST Storage",
            )
    s3_override = STORAGE_S3_OVERRIDES.get(tc)
    if s3_override:
        rendered = re.sub(
            r'provider: "minio"', f'provider: "{s3_override["provider"]}"', rendered,
        )
        rendered = re.sub(
            r'endpoint_url: ""', f'endpoint_url: "{s3_override["endpoint_url"]}"', rendered,
        )
    swap = STORAGE_SWAP.get(tc, [])
    if swap:
        swap_yaml = render_swap_yaml(swap)
        rendered = re.sub(
            r'^(s3_configurations:)', swap_yaml + r'\n\1',
            rendered, count=1, flags=re.MULTILINE,
        )
    return rendered


def _postprocess_local_repo(rendered, tc):
    """Apply local_repo_config.yml TC-specific repo overrides."""
    if tc == "tc03_minimal_hpc":
        new_block = (
            'omnia_repo_url_rhel_x86_64:\n'
            '  - { url: "https://download.docker.com/linux/centos/10/x86_64/stable/",'
            ' gpgkey: "https://download.docker.com/linux/centos/gpg", name: "docker-ce"}\n'
            '  - { url: "https://dl.fedoraproject.org/pub/epel/10/Everything/x86_64/",'
            ' gpgkey: "https://dl.fedoraproject.org/pub/epel/RPM-GPG-KEY-EPEL-10", name: "epel"}'
        )
        rendered = re.sub(
            r'omnia_repo_url_rhel_x86_64:.*?(?=\nomnia_repo_url_rhel_aarch64:)',
            new_block + "\n", rendered, count=1, flags=re.DOTALL,
        )
    if tc == "tc04_k8s_multisubnet":
        sub_repos = (
            'rhel_subscription_repo_config_x86_64:\n'
            '  - { url: "https://cdn.redhat.com/content/dist/rhel10/10.0/x86_64/baseos/os/",'
            ' name: "baseos" }\n'
            '  - { url: "https://cdn.redhat.com/content/dist/rhel10/10.0/x86_64/appstream/os/",'
            ' name: "appstream" }\n'
            '  - { url: "https://cdn.redhat.com/content/dist/rhel10/10.0/x86_64/codeready-builder/os/",'
            ' name: "codeready-builder" }'
        )
        rendered = re.sub(
            r'^rhel_subscription_repo_config_x86_64:\s*$', sub_repos,
            rendered, count=1, flags=re.MULTILINE,
        )
    if tc == "tc05_full_dell_stack":
        rendered = _apply_airgap_repos(rendered)
    return rendered


def _apply_airgap_repos(rendered):
    """Replace standard omnia repos with air-gap mirrors for TC-05."""
    airgap_x86 = (
        'omnia_repo_url_rhel_x86_64:\n'
        '  - { url: "http://10.50.0.1:8080/repos/docker-ce/x86_64/", gpgkey: "", name: "docker-ce" }\n'
        '  - { url: "http://10.50.0.1:8080/repos/epel/x86_64/", gpgkey: "", name: "epel" }\n'
        '  - { url: "http://10.50.0.1:8080/repos/kubernetes/x86_64/", gpgkey: "", name: "kubernetes-v1-35" }\n'
        '  - { url: "http://10.50.0.1:8080/repos/cri-o/x86_64/", gpgkey: "", name: "cri-o-v1-35" }\n'
        '  - { url: "http://10.50.0.1:8080/repos/doca/x86_64/", gpgkey: "", name: "doca" }\n'
        '  - { url: "http://10.50.0.1:8080/repos/cuda/x86_64/", gpgkey: "", name: "cuda" }\n'
        '  - { url: "http://10.50.0.1:8080/repos/nvidia-hpc-sdk/x86_64/", gpgkey: "", name: "nvidia-hpc-sdk" }'
    )
    rendered = re.sub(
        r'omnia_repo_url_rhel_x86_64:.*?(?=\nomnia_repo_url_rhel_aarch64:)',
        airgap_x86 + "\n", rendered, count=1, flags=re.DOTALL,
    )
    airgap_aarch64 = (
        'omnia_repo_url_rhel_aarch64:\n'
        '  - { url: "http://10.50.0.1:8080/repos/docker-ce/aarch64/", gpgkey: "", name: "docker-ce" }\n'
        '  - { url: "http://10.50.0.1:8080/repos/epel/aarch64/", gpgkey: "", name: "epel" }\n'
        '  - { url: "http://10.50.0.1:8080/repos/doca/aarch64/", gpgkey: "", name: "doca" }\n'
        '  - { url: "http://10.50.0.1:8080/repos/cuda/aarch64/", gpgkey: "", name: "cuda" }\n'
        '  - { url: "http://10.50.0.1:8080/repos/nvidia-hpc-sdk/aarch64/", gpgkey: "", name: "nvidia-hpc-sdk" }'
    )
    rendered = re.sub(
        r'omnia_repo_url_rhel_aarch64:.*?(?=\n#)',
        airgap_aarch64 + "\n", rendered, count=1, flags=re.DOTALL,
    )
    return rendered


def _postprocess_rendered(out_name, rendered, tc, overrides):
    """Dispatch post-processing for a rendered template file."""
    if out_name == "provision_config.yml":
        rendered = _postprocess_provision(rendered, tc)
    elif out_name == "omnia_config.yml":
        rendered = _postprocess_omnia_config(rendered, overrides)
    elif out_name == "storage_config.yml":
        rendered = _postprocess_storage(rendered, tc)
    elif out_name == "telemetry_storage_config.yml" and tc == "tc05_full_dell_stack":
        for old, new in TC05_TELEM_STORAGE_REPLACEMENTS:
            rendered = rendered.replace(old, new, 1)
    elif out_name == "local_repo_config.yml":
        rendered = _postprocess_local_repo(rendered, tc)
    return rendered


def _write_non_templated(tc, tc_dir):
    """Write non-templated files (software_config, discovery, cloud-init, etc.)."""
    # software_config.json
    sw_data = SOFTWARE_CONFIGS[tc]
    (tc_dir / "software_config.json").write_text(
        json.dumps(sw_data, indent=4, ensure_ascii=False) + "\n",
        encoding="utf-8", newline="\n",
    )

    # security_config.yml â€” same for all TCs, copy from project_default
    shutil.copy2(PROJECT_DEFAULT / "security_config.yml", tc_dir / "security_config.yml")

    # discovery_config.yml
    disc_text = (PROJECT_DEFAULT / "discovery_config.yml").read_text(encoding="utf-8")
    for key, val in DISCOVERY_OVERRIDES.get(tc, {}).items():
        if isinstance(val, bool):
            val = "true" if val else "false"
        elif isinstance(val, str):
            val = f'"{val}"'
        disc_text = re.sub(
            rf'^({re.escape(key)}:)\s*.*$', rf'\1 {val}',
            disc_text, count=1, flags=re.MULTILINE,
        )
    (tc_dir / "discovery_config.yml").write_text(disc_text, encoding="utf-8", newline="\n")

    # additional_cloud_init.yml
    ci_text = (PROJECT_DEFAULT / "additional_cloud_init.yml").read_text(encoding="utf-8")
    ci_overrides = CLOUD_INIT_OVERRIDES.get(tc, {})
    if ci_overrides:
        for section in ("common", "groups"):
            if section in ci_overrides:
                section_yaml = yaml.dump(
                    ci_overrides[section], default_flow_style=False,
                    indent=2, allow_unicode=True,
                ).rstrip()
                indented = "\n".join("  " + ln for ln in section_yaml.split("\n"))
                ci_text = ci_text.replace(f"{section}: {{}}", f"{section}:\n{indented}")
    (tc_dir / "additional_cloud_init.yml").write_text(ci_text, encoding="utf-8", newline="\n")

    # user_registry_credential.yml
    urc_text = (PROJECT_DEFAULT / "user_registry_credential.yml").read_text(encoding="utf-8")
    urc_override = USER_REG_CRED_OVERRIDES.get(tc)
    if urc_override:
        old_line = '  - {name: "", username: "", password: ""}'
        new_lines = "\n".join(
            f'  - {{name: "{e["name"]}", username: "{e["username"]}", password: "{e["password"]}"}}'
            for e in urc_override
        )
        urc_text = urc_text.replace(old_line, new_lines)
    (tc_dir / "user_registry_credential.yml").write_text(urc_text, encoding="utf-8", newline="\n")


# ============================================================================
# Main generation
# ============================================================================
def generate(targets=None, clean=False):
    """Generate TC dataset directories from templates and TC variable overrides."""
    env = create_jinja_env()
    targets = targets if targets else TC_NAMES

    for tc in targets:
        tc_dir = DATASETS_DIR / tc
        if clean and tc_dir.exists():
            shutil.rmtree(tc_dir)
        tc_dir.mkdir(exist_ok=True)

        overrides = TC_OVERRIDES.get(tc, {})
        ctx = deep_merge(DEFAULTS, overrides)

        # Render templated files
        for tmpl_name, out_name in TEMPLATE_MAP.items():
            tmpl = env.get_template(tmpl_name)
            rendered = tmpl.render(**ctx)
            rendered = _postprocess_rendered(out_name, rendered, tc, overrides)
            (tc_dir / out_name).write_text(rendered, encoding="utf-8", newline="\n")

        # Write non-templated files
        _write_non_templated(tc, tc_dir)

        file_count = len(list(tc_dir.iterdir()))
        print(f"  [OK] {tc}: {file_count} files")

    print(f"\nDone â€” {len(targets)} TC directories generated from templates.")


# ============================================================================
# Custom TC override loading
# ============================================================================
def load_custom_overrides():
    """Load custom TC definitions from custom_overrides.yml if present.

    Returns a dict of {tc_name: {metadata: {...}, overrides: {...}, software_config: {...}}}
    """
    if not CUSTOM_OVERRIDES_FILE.exists():
        return {}

    print(f"  Loading custom overrides from {CUSTOM_OVERRIDES_FILE.name}")
    with open(CUSTOM_OVERRIDES_FILE, encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}

    custom_tcs = {}
    for tc_name, tc_def in data.get("custom_test_cases", {}).items():
        custom_tcs[tc_name] = {
            "metadata": tc_def.get("metadata", {}),
            "overrides": tc_def.get("overrides", {}),
            "software_config": tc_def.get("software_config", {}),
        }
    return custom_tcs


def apply_custom_tcs(custom_tcs):
    """Merge custom TC definitions into the global TC registries."""
    for tc_name, tc_def in custom_tcs.items():
        if tc_name not in TC_NAMES:
            TC_NAMES.append(tc_name)
        if tc_def.get("metadata"):
            TC_METADATA[tc_name] = tc_def["metadata"]
        if tc_def.get("overrides"):
            TC_OVERRIDES[tc_name] = tc_def["overrides"]
        if tc_def.get("software_config"):
            SOFTWARE_CONFIGS[tc_name] = tc_def["software_config"]
        elif tc_name not in SOFTWARE_CONFIGS:
            # Default to project_default software_config
            SOFTWARE_CONFIGS[tc_name] = json.loads(
                (PROJECT_DEFAULT / "software_config.json").read_text(encoding="utf-8")
            )


# ============================================================================
# Manifest generation
# ============================================================================
def generate_manifest(targets):
    """Auto-generate dataset_manifest.yml with TC metadata and coverage matrix."""
    manifest = {
        "version": "3.5",
        "description": "Auto-generated dataset manifest. DO NOT EDIT â€” regenerate with: python utility/generate_datasets.py",
        "test_cases": {},
    }

    all_tc_names = targets if targets else TC_NAMES

    for tc in all_tc_names:
        meta = TC_METADATA.get(tc, {})
        tc_dir = DATASETS_DIR / tc
        files = sorted(f.name for f in tc_dir.iterdir()) if tc_dir.exists() else []

        manifest["test_cases"][tc] = {
            "description": meta.get("description", tc),
            "coverage": meta.get("coverage", {}),
            "playbook_order": meta.get("playbook_order", []),
            "files": files,
            "file_count": len(files),
        }

    # Build coverage matrix summary
    axes = [
        "software_stack", "telemetry_sources", "storage_backend",
        "s3_provider", "network_topology", "dns_mode",
        "architecture", "repo_strategy", "options",
    ]
    coverage_matrix = {}
    for axis in axes:
        coverage_matrix[axis] = {}
        for tc in all_tc_names:
            meta = TC_METADATA.get(tc, {})
            val = meta.get("coverage", {}).get(axis, "N/A")
            if isinstance(val, list):
                val = ", ".join(val) if val else "None"
            coverage_matrix[axis][tc] = val

    manifest["coverage_matrix"] = coverage_matrix

    manifest_path = DATASETS_DIR / "dataset_manifest.yml"
    with open(manifest_path, "w", encoding="utf-8", newline="\n") as f:
        f.write("# Auto-generated by generate_datasets.py â€” DO NOT EDIT manually\n")
        f.write("# Regenerate: python utility/generate_datasets.py --clean\n\n")
        yaml.dump(manifest, f, default_flow_style=False, indent=2, allow_unicode=True,
                  sort_keys=False, width=120)

    print(f"  Manifest written: {manifest_path.name}")


# ============================================================================
# CLI
# ============================================================================
if __name__ == "__main__":
    _clean = "--clean" in sys.argv
    _no_manifest = "--no-manifest" in sys.argv
    _tc_filter = [a for a in sys.argv[1:] if not a.startswith("--")]

    # Load custom overrides if present
    _custom_tcs = load_custom_overrides()
    if _custom_tcs:
        apply_custom_tcs(_custom_tcs)

    # Support partial name matching
    if _tc_filter:
        _matched = []
        for _pattern in _tc_filter:
            _matched.extend(tc for tc in TC_NAMES if _pattern in tc)
        _tc_filter = _matched or None
    else:
        _tc_filter = None

    print(f"Generating datasets from templates ({TEMPLATE_DIR})")
    if _tc_filter:
        print(f"  TCs: {', '.join(_tc_filter)}")
    generate(targets=_tc_filter, clean=_clean)

    # Generate manifest unless suppressed
    if not _no_manifest:
        generate_manifest(_tc_filter)
