<!-- Copyright 2026 Dell Inc. or its subsidiaries. All Rights Reserved.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License. -->

# omnia\_test\_config.yml — Complete Parameter Reference

This is the central configuration file for the Omnia Automation Framework. Every automation script, prerequisite check, and Molecule scenario reads from this file. Edit it before running any tests.

> **Location:** `omnia_test_config.yml` (repository root)
> **Note:** This file is gitignored — each user maintains their own copy.

---

## Dataset Configuration

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `dataset` | string | `"project_default"` | Name of the dataset folder under `datasets/` to use. The folder contains all deployment input files that get synced into the `omnia_core` container at `/opt/omnia/input/project_default/`. |
| `sync_dataset_to_core` | boolean | `false` | When `true`, the `converge` step copies dataset files from `datasets/<dataset>/` into the container via rsync over SSH (port 2222). When `false`, the existing files inside the container are used as-is. |

## Execution Control

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `skip_on_failure` | boolean | `false` | When `true`, prerequisite checks continue running even if one fails. When `false`, execution stops at the first failure. |

## Target OIM Server

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `oim_server_ip` | string | `""` | IP address of the OIM server. **Leave empty for local mode** — all commands run on the local machine without SSH. Set to a remote IP for remote mode. When empty, `localhost`, or `127.0.0.1`, the framework uses `local://` connection (no SSH). |
| `oim_ssh_user` | string | `""` | SSH username for remote OIM server. Only required in remote mode. |
| `oim_ssh_password` | string | `""` | SSH password for remote OIM server. Only required in remote mode. |
| `oim_ssh_port` | integer | `22` | SSH port for remote OIM server. |

### Local Mode vs Remote Mode

- **Local mode:** `oim_server_ip` is empty, `""`, `localhost`, or `127.0.0.1`. All commands run directly on the local machine. Assumes the automation is running on the OIM server itself. No SSH credentials needed.
- **Remote mode:** `oim_server_ip` is set to a remote IP. All commands execute over SSH using the provided credentials.

> **Important:** If `oim_server_ip` is not set, every scenario (including `omnia_sh_install`) runs in local mode on the current host. For `omnia_sh_install`, this means it will install the `omnia_core` container locally.

## Hostname Configuration

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `oim_hostname` | string | `""` | FQDN to set on the OIM server (e.g., `oim.omnia.test`). Must include a domain. Used during prerequisite checks. |

## Hardware Thresholds

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `min_cores` | integer | `4` | Minimum CPU cores required on the OIM server. |
| `min_memory_gb` | integer | `8` | Minimum RAM in GB. |
| `min_disk_gb` | integer | `50` | Minimum disk space in GB. |

## OS Validation

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `required_os` | string | `"rhel"` | Expected OS name (e.g., `rhel`, `rocky`). |
| `required_os_version` | string | `"10"` | Expected OS version string. |
| `required_kernel_version` | string | `""` | Expected kernel version (e.g., `6.12.0-55.9.1.el10_0.x86_64`). Leave empty to skip kernel check. |

## Network Configuration

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `network_type` | string | `"dedicated"` | Network topology: `"dedicated"` (separate PXE and public NICs) or `"lom"` (LAN-on-Motherboard — single interface shared for PXE and iDRAC). |
| `pxe_interface` | string | `""` | PXE/provisioning network interface name (e.g., `eno33np0`). |
| `public_interface` | string | `""` | Public/internet-facing network interface name. |
| `pxe_ip` | string | `""` | IP address in CIDR notation for the PXE interface (e.g., `172.16.107.254/24`). |
| `idrac_ip` | string | `""` | iDRAC IP address. Only used when `network_type` is `"lom"`. |
| `force_configure_pxe` | boolean | `true` | When `true`, removes existing PXE IP and applies new configuration. |

## NFS Configuration

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `nfs_server_ip` | string | `""` | IP address of the external NFS server. |
| `nfs_share_path` | string | `""` | NFS export path (e.g., `/mnt/share`). |
| `nfs_min_capacity_gb` | integer | `100` | Minimum NFS share capacity in GB. |

## Podman Configuration

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `podman_min_version` | string | `"5.0.0"` | Minimum required Podman version on the OIM server. |

## Container Image Build

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `reconfigure_images` | boolean | `false` | When `true`, clones the artifactory repo and builds container images. When `false`, skips the build. |
| `omnia_repo_url` | string | `"https://github.com/dell/omnia-artifactory.git"` | Git URL for the Omnia Artifactory repository. |
| `artifactory_branch` | string | `"omnia-container"` | Branch to clone. |
| `omnia_clone_path` | string | `"/opt/omnia-artifactory"` | Clone destination on the OIM server. |
| `core_tag` | string | `""` | Version tag for the core container image. |
| `omnia_branch` | string | `""` | Omnia branch or tag for the core image build (e.g., `main`, `pub/q1_dev`, `v1.6.0`). |

## omnia.sh Installation

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `share_option` | string | `"NFS"` | Storage backend: `"NFS"` (external or internal NFS server) or `"Local"` (local disk). |
| `nfs_type` | string | `"external"` | NFS type: `"external"` (pre-existing NFS server outside OIM) or `"internal"` (NFS managed by OIM itself — for flat provisioning only). |
| `omnia_shared_path` | string | `""` | Local directory for Omnia data. For external NFS, this is the mount point. For local storage, data is stored here directly. |
| `omnia_core_password` | string | `""` | Root password for the `omnia_core` container SSH access (port 2222). Required for dataset sync and container operations. |

## LDAP Configuration

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `ldap_credentials` | string | `""` | LDAP credentials for SSH login tests. Format: `"user:password"` or comma-separated `"user1:pass1,user2:pass2"`. Used by Slurm LDAP, Apptainer, and provisioning tests. |
| `external_ldap_server_ip` | string | `""` | External LDAP server IP for slapd.conf tests. |
| `external_ldap_server_port` | string | `""` | External LDAP server port. |
| `external_ldap_domain` | string | `""` | External LDAP domain (e.g., `omnia.test` → `dc=omnia,dc=test`). |
| `external_ldap_bind_username` | string | `""` | External LDAP bind username. |
| `external_ldap_bind_password` | string | `""` | External LDAP bind password. |

## Build Stream (CI/CD Pipeline)

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `build_stream_job_id` | string | `""` | Pin a specific BuildStream job UUID for verification. When empty, the automation resolves the latest `COMPLETED` job from the Postgres database. |
| `allow_pipeline_cancel` | boolean | `false` | When `true`, automation auto-cancels running/pending pipelines before triggering new ones. |
| `image_identifier` | string | `""` | Specific image group ID for deploy/cleanup pipeline tests (e.g., `image-build-20260530-061909`). When empty, auto-selects the latest `BUILT` image group. |

---

## Example Configuration

```yaml
# Target OIM Server
oim_server_ip: "<OIM_SERVER_IP>"
oim_ssh_user: "root"
oim_ssh_password: "<SSH_PASSWORD>"
oim_ssh_port: 22

# Hostname
oim_hostname: "oim.omnia.test"

# Hardware Thresholds
min_cores: 4
min_memory_gb: 8
min_disk_gb: 50

# OS Validation
required_os: "rhel"
required_os_version: "10"
required_kernel_version: ""

# Network
network_type: "dedicated"
pxe_interface: "eno33np0"
public_interface: "eno1"
pxe_ip: "172.16.107.254/24"
force_configure_pxe: true

# NFS
nfs_server_ip: "<NFS_SERVER_IP>"
nfs_share_path: "/mnt/share"
nfs_min_capacity_gb: 100

# Podman
podman_min_version: "5.0.0"

# omnia.sh Installation
share_option: "NFS"
nfs_type: "external"
omnia_shared_path: "/opt/omnia"
omnia_core_password: "<CONTAINER_PASSWORD>"

# Dataset
dataset: "project_default"
sync_dataset_to_core: false

# Execution Control
skip_on_failure: false
```
