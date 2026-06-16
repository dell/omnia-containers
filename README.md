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

# Omnia Automation Framework

End-to-end automation and testing for **Omnia Infrastructure Manager (OIM)** deployments using Molecule and pytest-testinfra.

## Table of Contents

- [Overview](#overview)
- [Quick Start](#quick-start)
- [Configuration](#configuration)
  - [omnia\_test\_config.yml](#omnia_test_configyml)
  - [Datasets](#datasets)
- [Execution](#execution)
  - [Prerequisite Checks](#prerequisite-checks)
  - [Running Molecule Tests](#running-molecule-tests)
  - [Config-Driven Batch Execution](#config-driven-batch-execution)
  - [Suite and Marker Filtering](#suite-and-marker-filtering)
  - [Test Reports](#test-reports)
- [Scenarios](#scenarios)
- [Project Structure](#project-structure)
- [Core Library Reference](#core-library-reference)
- [License](#license)

---

## Overview

This framework automates testing of Omnia Infrastructure Manager (OIM) deployments. It provides:

- **Prerequisite validation** of the OIM server (hardware, OS, network, NFS, Podman)
- **Molecule-based test scenarios** that execute Ansible playbooks inside the `omnia_core` container and verify results with pytest-testinfra
- **Interactive HTML and JSON reports** for every test run

### How It Works

1. **`omnia_test_config.yml`** drives all automation — it defines the OIM server connection, hardware thresholds, deployment options, and dataset selection.
2. **`setup_env.sh`** creates a Python virtual environment, installs dependencies, and registers the `oim-prereq-check` CLI and `run_molecule` shell function.
3. **Molecule scenarios** follow a `create → converge → verify` lifecycle:
   - **create.yml** — Builds dynamic Ansible inventory from `omnia_test_config.yml` and verifies SSH connectivity to the OIM server.
   - **converge.yml** — Optionally syncs dataset files into the `omnia_core` container at `/opt/omnia/input/project_default/`, then executes the target playbook via `podman exec` inside the container.
   - **verify** — Runs pytest-testinfra tests that use `automation_library` functions to SSH into the OIM, execute commands inside the container, and validate deployment state.
4. **`automation_library/core/`** provides shared utilities for host connections, config loading, container command execution, PXE mapping parsing, credential decryption, and report generation.

### Local Mode vs Remote Mode

| Mode | When | How |
|------|------|-----|
| **Local mode** | `oim_server_ip` is empty, `""`, `localhost`, or `127.0.0.1` | All commands run directly on the local machine via `local://` — no SSH required. Assumes the automation is running on the OIM server itself. |
| **Remote mode** | `oim_server_ip` is set to a remote IP address | All commands are executed over SSH using the provided `oim_ssh_user` and `oim_ssh_password`. |

> **Important:** If `oim_server_ip` is not set, every scenario (including `omnia_sh_install`) runs in local mode. For `omnia_sh_install`, passwordless SSH is required to the OIM server — if no IP is provided, it will validate against localhost.

---

## Quick Start

```bash
# 1. Clone the repository
git clone https://github.com/dell/omnia-artifactory.git
cd omnia-artifactory

# 2. Run the environment setup script
./setup_env.sh

# 3. Activate the virtual environment
source .venv/bin/activate

# 4. Configure your OIM server
vi omnia_test_config.yml

# 5. (Optional) Fill dataset files — required only for converge/test runs
vi datasets/project_default/network_spec.yml
vi datasets/project_default/software_config.json
# ... edit other dataset files as needed

# 6. Run prerequisite checks
oim-prereq-check

# 7. Run molecule tests
run_molecule telemetry verify --suite sanity   # Single scenario
run_molecule all test                          # Full lifecycle
run_molecule --config                          # Batch from config file
```

> **Note:** For `verify`-only runs (validating an already-deployed environment), filling the dataset files is not required. Datasets are only synced during `converge` and `test` commands when `sync_dataset_to_core: true` is set.

---

## Configuration

### omnia\_test\_config.yml

This is the central configuration file. Every automation script reads from it. Edit this file before running any tests.

#### Dataset Configuration

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `dataset` | string | `"project_default"` | Name of the dataset folder under `datasets/` to use. The folder contains all deployment input files that get synced into the `omnia_core` container at `/opt/omnia/input/project_default/`. |
| `sync_dataset_to_core` | boolean | `false` | When `true`, the `converge` step copies dataset files from `datasets/<dataset>/` into the container via rsync. When `false`, the existing files inside the container are used as-is. |

#### Execution Control

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `skip_on_failure` | boolean | `false` | When `true`, prerequisite checks continue running even if one fails. When `false`, execution stops at the first failure. |

#### Target OIM Server

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `oim_server_ip` | string | `""` | IP address of the OIM server. **Leave empty for local mode** — all commands run on the local machine without SSH. Set to a remote IP for remote mode. |
| `oim_ssh_user` | string | `""` | SSH username for remote OIM server. Only required in remote mode. |
| `oim_ssh_password` | string | `""` | SSH password for remote OIM server. Only required in remote mode. |
| `oim_ssh_port` | integer | `22` | SSH port for remote OIM server. |

#### Hostname Configuration

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `oim_hostname` | string | `""` | FQDN to set on the OIM server (e.g., `oim.omnia.test`). Must include a domain. Used during prerequisite checks. |

#### Hardware Thresholds

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `min_cores` | integer | `4` | Minimum CPU cores required on the OIM server. |
| `min_memory_gb` | integer | `8` | Minimum RAM in GB. |
| `min_disk_gb` | integer | `50` | Minimum disk space in GB. |

#### OS Validation

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `required_os` | string | `"rhel"` | Expected OS name (e.g., `rhel`, `rocky`). |
| `required_os_version` | string | `"10"` | Expected OS version string. |
| `required_kernel_version` | string | `""` | Expected kernel version (e.g., `6.12.0-55.9.1.el10_0.x86_64`). Leave empty to skip kernel check. |

#### Network Configuration

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `network_type` | string | `"dedicated"` | Network topology: `"dedicated"` (separate PXE and public NICs) or `"lom"` (LAN-on-Motherboard — single interface shared for PXE and iDRAC). |
| `pxe_interface` | string | `""` | PXE/provisioning network interface name (e.g., `eno33np0`). |
| `public_interface` | string | `""` | Public/internet-facing network interface name. |
| `pxe_ip` | string | `""` | IP address in CIDR notation for the PXE interface (e.g., `172.16.107.254/24`). If empty, defaults to `172.16.107.254/24`. |
| `idrac_ip` | string | `""` | iDRAC IP address. Only used when `network_type` is `"lom"`. |
| `force_configure_pxe` | boolean | `true` | When `true`, removes existing PXE IP and applies new configuration. |

#### NFS Configuration

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `nfs_server_ip` | string | `""` | IP address of the external NFS server. |
| `nfs_share_path` | string | `""` | NFS export path (e.g., `/mnt/share`). |
| `nfs_min_capacity_gb` | integer | `100` | Minimum NFS share capacity in GB. |

#### Podman Configuration

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `podman_min_version` | string | `"5.0.0"` | Minimum required Podman version on the OIM server. |

#### Container Image Build

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `reconfigure_images` | boolean | `false` | When `true`, clones the artifactory repo and builds container images. When `false`, skips the build. |
| `omnia_repo_url` | string | `"https://github.com/dell/omnia-artifactory.git"` | Git URL for the Omnia Artifactory repository. |
| `artifactory_branch` | string | `"omnia-container"` | Branch to clone. |
| `omnia_clone_path` | string | `"/opt/omnia-artifactory"` | Clone destination on the OIM server. |
| `core_tag` | string | `""` | Version tag for the core container image. |
| `omnia_branch` | string | `""` | Omnia branch or tag for the core image build (e.g., `main`, `pub/q1_dev`, `v1.6.0`). |

#### omnia.sh Installation

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `share_option` | string | `"NFS"` | Storage backend: `"NFS"` (external or internal NFS server) or `"Local"` (local disk). |
| `nfs_type` | string | `"external"` | NFS type: `"external"` (pre-existing NFS server outside OIM) or `"internal"` (NFS managed by OIM itself — for flat provisioning only). |
| `omnia_shared_path` | string | `""` | Local directory for Omnia data. For external NFS, this is the mount point. For local storage, data is stored here directly. |
| `omnia_core_password` | string | `""` | Root password for the `omnia_core` container SSH access (port 2222). Required for dataset sync and container operations. |

#### LDAP Configuration

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `ldap_credentials` | string | `""` | LDAP credentials for SSH login tests. Format: `"user:password"` or comma-separated `"user1:pass1,user2:pass2"`. Used by Slurm LDAP, Apptainer, and provisioning tests. |
| `external_ldap_server_ip` | string | `""` | External LDAP server IP for slapd.conf tests. |
| `external_ldap_server_port` | string | `""` | External LDAP server port. |
| `external_ldap_domain` | string | `""` | External LDAP domain (e.g., `omnia.test` → `dc=omnia,dc=test`). |
| `external_ldap_bind_username` | string | `""` | External LDAP bind username. |
| `external_ldap_bind_password` | string | `""` | External LDAP bind password. |

#### Build Stream (CI/CD Pipeline)

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `build_stream_job_id` | string | `""` | Pin a specific BuildStream job UUID for verification. When empty, the automation resolves the latest `COMPLETED` job from the Postgres database. |
| `allow_pipeline_cancel` | boolean | `false` | When `true`, automation auto-cancels running/pending pipelines before triggering new ones. When `false`, waits for completion or prompts user. |
| `image_identifier` | string | `""` | Specific image group ID for deploy/cleanup pipeline tests (e.g., `image-build-20260530-061909`). When empty, auto-selects the latest `BUILT` image group. |

#### Example Configuration

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

---

### Datasets

The `datasets/project_default/` folder contains Omnia deployment input files. These files mirror what the Omnia playbooks expect at `/opt/omnia/input/project_default/` inside the `omnia_core` container.

When `sync_dataset_to_core: true` is set and a `converge` or `test` command runs, the automation:
1. Uses `rsync` over SSH (port 2222) to copy `datasets/<dataset>/` into the container at `/opt/omnia/input/project_default/`
2. Creates a vault key and encrypts `omnia_config_credentials.yml` using `ansible-vault` (same mechanism as Omnia playbooks)

#### How Omnia Uses These Files

Inside the `omnia_core` container, every playbook starts by importing `utils/include_input_dir.yml`, which:
1. Reads `/opt/omnia/input/default.yml` to get the `project_name` (default: `project_default`)
2. Sets `input_project_dir` to `/opt/omnia/input/project_default/`
3. All subsequent playbook roles load their config files from `input_project_dir`

For example:
- `prepare_oim.yml` reads `software_config.json` to determine which services to deploy (Slurm, K8s, OpenLDAP, etc.)
- `discovery.yml` reads `discovery_config.yml` for BMC discovery and OME integration settings
- `local_repo.yml` reads `local_repo_config.yml` and `software_config.json` for package and repository URLs
- `provision.yml` reads `provision_config.yml`, `build_stream_config.yml`, and `network_spec.yml` for node provisioning
- `telemetry.yml` reads `telemetry_config.yml` for iDRAC, LDMS, DCGM, and PowerScale telemetry settings
- `gitlab.yml` reads `gitlab_config.yml` for GitLab server and pipeline configuration
- `oim_cleanup.yml` reads `omnia_config.yml` and `storage_config.yml` for cleanup paths

#### Dataset Files

| File | Consumed By | Description |
|------|-------------|-------------|
| `software_config.json` | `prepare_oim.yml`, `local_repo.yml`, `build_image_*.yml`, `input_validation/` | **Central control file.** Defines `cluster_os_type`, `cluster_os_version`, `repo_config`, and the list of softwares to deploy (e.g., `slurm_custom`, `service_k8s`, `openldap`, `ldms`, `ucx`, `openmpi`, `csi_driver_powerscale`). Each software entry specifies `name`, optional `version`, and `arch` (`x86_64`/`aarch64`). |
| `network_spec.yml` | `prepare_oim.yml`, `discovery.yml`, `provision.yml`, `local_repo.yml` | Defines the `admin_network` (OIM NIC name, subnet, DHCP dynamic range, DNS, NTP servers) and `ib_network` (InfiniBand subnet). Also supports `additional_subnets` for multi-RAC PXE deployments. |
| `provision_config.yml` | `provision.yml` | PXE mapping file path, DHCP lease time, OS language, kernel version override, and optional additional cloud-init config file path. |
| `discovery_config.yml` | `discovery.yml` | BMC discovery toggle (`enable_bmc_discovery`) and OME IP address. |
| `omnia_config.yml` | `provision.yml`, `oim_cleanup.yml` | Slurm cluster definition (cluster name, NFS storage name) and service K8s cluster definition (deployment toggle, CNI, pod IP ranges, NFS storage name, CRI-O storage size, CSI PowerScale paths). |
| `omnia_config_credentials.yml` | `prepare_oim.yml`, `provision.yml`, `gitlab.yml` (via `credential_utility/`) | Ansible-vault encrypted credentials for cluster node access, container registry, and service accounts. Auto-encrypted during dataset sync. |
| `telemetry_config.yml` | `telemetry.yml` | Telemetry source configuration: iDRAC metrics (collection targets: `victoria_metrics`, `kafka`), LDMS metrics, DCGM GPU metrics, and PowerScale storage metrics. Each source has `metrics_enabled` and `collection_targets`. |
| `telemetry_storage_config.yml` | `telemetry.yml` | VictoriaMetrics cluster sizing (vmstorage, vminsert, vmselect replicas and resource limits), vmagent, and Kafka resource allocations. |
| `storage_config.yml` | `provision.yml`, `oim_cleanup.yml` | NFS mount definitions (source, mount point, options, functional group prefix), mount parameter presets (`nfs_default`, `vast_rdma`, `vast_tcp`), and S3 configuration (provider, endpoint URL). |
| `local_repo_config.yml` | `local_repo.yml` | RPM repository URLs per architecture — `user_repo_url_x86_64`, `user_repo_url_aarch64`, `rhel_os_url_*`, `omnia_repo_url_rhel_*`, and `additional_repos_*`. Each entry has `url`, `gpgkey`, and `name`. |
| `security_config.yml` | `prepare_oim.yml` | LDAP connection type (`TLS` or `SSL`). |
| `high_availability_config.yml` | `provision.yml` | Kubernetes HA configuration — `enable_k8s_ha`, `virtual_ip_address` per cluster. |
| `gitlab_config.yml` | `gitlab.yml` | GitLab server settings — host IP, project name, visibility, HTTPS port, resource minimums, Puma workers, Sidekiq concurrency. |
| `build_stream_config.yml` | `provision.yml`, `build_stream/` | BuildStream toggle (`enable_build_stream`), host IP, port, and aarch64 inventory host IP. |
| `user_registry_credential.yml` | `local_repo.yml` | Container registry authentication credentials for pulling images during local repo sync. |
| `pxe_mapping_file.csv` | `discovery.yml`, `provision.yml` | Node-to-network mapping — hostname, admin IP, BMC IP, MAC address, functional groups. Used by OpenCHAMI for PXE boot and node assignment. |
| `config/<arch>/<os>/<version>/*.json` | `local_repo.yml`, `build_image_*.yml` | Per-architecture, per-OS package lists. Each JSON file corresponds to a software name from `software_config.json` and defines the RPM packages, container images, and files to sync for that component. |

---

## Execution

### Installation

```bash
./setup_env.sh                # Creates .venv, installs deps, registers CLI
source .venv/bin/activate     # Activates the virtual environment
```

The setup script:
- Validates system prerequisites (Python 3.9+, venv module, sshpass)
- Creates a Python virtual environment at `.venv/`
- Installs all Python dependencies from `requirements.txt`
- Makes `run_molecule.sh` executable
- Registers the `run_molecule` shell function with tab-completion

| Flag | Description |
|------|-------------|
| `--force` | Remove existing `.venv` and recreate from scratch |
| `--debug` | Verbose output — show every package installed |

### Prerequisite Checks

Validates the OIM server meets all requirements before deployment:

```bash
oim-prereq-check                       # Run all checks
oim-prereq-check --debug               # Verbose output
oim-prereq-check --stop-on-failure     # Stop on first failure
oim-prereq-check --continue-on-failure # Continue even if a check fails
oim-prereq-check --no-report           # Skip HTML report generation
```

Checks performed:

| # | Check | Description |
|---|-------|-------------|
| 1 | IPMI Tool | Verify/install ipmitool |
| 2 | Hardware Inventory | Validate CPU cores, memory, disk against `min_cores`, `min_memory_gb`, `min_disk_gb` |
| 3 | OS Validation | Validate OS name, version, and kernel against `required_os`, `required_os_version`, `required_kernel_version` |
| 4 | Network Interfaces | Validate PXE and public interfaces exist and are UP |
| 5 | PXE NIC Config | Configure PXE interface IP address based on `pxe_ip` and `force_configure_pxe` |
| 6 | NFS Server | Ping NFS server and verify share capacity against `nfs_min_capacity_gb` |
| 7 | Internet Access | Test internet connectivity via public interface |
| 8 | Podman | Validate Podman installation and version against `podman_min_version` |
| 9 | RHEL Repository | Check RHEL repository availability |
| 10 | Git | Verify/install git (only when `reconfigure_images: true`) |
| 11 | Omnia Artifactory | Clone repository (only when `reconfigure_images: true`) |
| 12 | Container Images | Build container images (only when `reconfigure_images: true`) |

### Running Molecule Tests

```bash
# List available scenarios
run_molecule list

# Full lifecycle (create + converge + verify)
run_molecule <scenario> test

# Run playbook only (no tests)
run_molecule <scenario> converge

# Run tests only (skip playbook — for already-deployed environments)
run_molecule <scenario> verify

# Setup inventory only
run_molecule <scenario> create

# Run specific test suites
run_molecule <scenario> verify --suite sanity

# Run specific markers
run_molecule <scenario> verify --marker smoke

# Run all scenarios sequentially
run_molecule all test

# Run build_stream flow
run_molecule all verify --flow build_stream
```

### Config-Driven Batch Execution

Enable/disable scenarios in `test_run_config.yml` and run them all at once:

```bash
vi test_run_config.yml        # Enable desired scenarios
run_molecule --config          # Execute all enabled scenarios
```

Each scenario entry in `test_run_config.yml`:

```yaml
telemetry:
  run: true              # true/false — whether to execute
  command: "verify"      # test/verify/converge
  suite: "sanity"        # sanity/negative/regression/smoke/"" (empty = all)
```

### Suite and Marker Filtering

| Option | Mechanism | Example |
|--------|-----------|---------|
| `--suite` | Folder-based — runs tests from `tests/<suite>/` directory | `--suite sanity` → runs `tests/sanity/*.py` |
| `--marker` | Decorator-based — runs tests with `@pytest.mark.<marker>` | `--marker smoke` → runs all `@pytest.mark.smoke` tests |

Registered markers (defined in `pytest.ini`): `sanity`, `negative`, `regression`, `smoke`, `build_auto`, `deploy_auto`, `cleanup_manual`, `ldap`, `sanityib`, `vast_telemetry`

### Test Reports

After test execution, reports are generated in `reports/`:

| Format | File | Description |
|--------|------|-------------|
| HTML | `test_report.html` | Interactive dark-themed report with collapsible sections and per-test details |
| JSON | `test_report.json` | Machine-readable format for CI/CD integration |

```bash
xdg-open reports/test_report.html        # Open in browser
jq '.servers' reports/test_report.json    # Parse JSON
```

---

## Scenarios

| # | Scenario | Omnia Playbook | Description |
|---|----------|---------------|-------------|
| 1 | `omnia_sh_install` | `omnia.sh --install` | Installs the `omnia_core` container on the OIM server |
| 2 | `prepare_oim` | `prepare_oim/prepare_oim.yml` | Prepares OIM — deploys OpenCHAMI services, configures firewall, NTP, NFS |
| 3 | `gitlab_install` | `gitlab/gitlab.yml` | Deploys GitLab server for BuildStream CI/CD pipeline |
| 4 | `local_repo` | `local_repo/local_repo.yml` | Syncs RPM packages, container images, and files to Pulp repository |
| 5 | `build_image_x86_64` | `build_image_x86_64/build_image_x86_64.yml` | Builds x86_64 OS images, pushes to registry and S3 |
| 6 | `build_image_aarch64` | `build_image_aarch64/build_image_aarch64.yml` | Builds aarch64 OS images |
| 7 | `discovery` | `discovery/discovery.yml` | Discovers cluster nodes via BMC/OME, generates PXE mapping |
| 8 | `provision` | `provision/provision.yml` | Provisions discovered nodes with OS and software stack |
| 9 | `telemetry` | `telemetry/telemetry.yml` | Deploys telemetry stack — iDRAC, LDMS, DCGM, PowerScale, VictoriaMetrics, Kafka |
| 10 | `apptainer` | — (verify only) | Verifies Apptainer container runtime on Slurm nodes |
| 11 | `build_stream` | — (verify only) | Verifies BuildStream CI/CD pipeline job stages in Postgres |
| 12 | `gitlab_cleanup` | `gitlab/cleanup_gitlab.yml` | Removes GitLab deployment |
| 13 | `oim_cleanup` | `utils/oim_cleanup.yml` | Cleans up OIM — removes containers, credentials, NFS mounts |
| 14 | `omnia_sh_uninstall` | `omnia.sh --uninstall` | Uninstalls the `omnia_core` container |

> Scenarios not listed above (e.g., `kubernetes`, `slurm`, `dcgm`, `hpc_benchmarks`, `vast_storage`, `one_shot_log_extraction`) are verify-only scenarios that validate already-deployed components without running a converge playbook.

---

## Project Structure

```
omnia-artifactory/
├── omnia_test_config.yml              # Central config — OIM server, credentials, dataset
├── test_run_config.yml                # Batch scenario runner — enable/disable scenarios
├── requirements.txt                   # Python dependencies
├── setup.py                           # Package setup (omnia-automation)
├── setup_env.sh                       # Environment setup script
├── run_molecule.sh                    # Molecule test runner
├── run_prereq_check.py                # Prerequisite check entry point
├── pytest.ini                         # Pytest configuration and custom markers
│
├── datasets/                          # Deployment input datasets
│   └── project_default/               # Default dataset (synced to omnia_core container)
│       ├── software_config.json       # Software enablement (Slurm, K8s, LDMS, etc.)
│       ├── network_spec.yml           # Admin network, IB network, NTP, DNS
│       ├── provision_config.yml       # PXE mapping path, DHCP, language
│       ├── discovery_config.yml       # BMC discovery, OME IP
│       ├── omnia_config.yml           # Slurm and K8s cluster definitions
│       ├── omnia_config_credentials.yml # Cluster credentials (ansible-vault encrypted)
│       ├── telemetry_config.yml       # Telemetry sources (iDRAC, LDMS, DCGM, PowerScale)
│       ├── telemetry_storage_config.yml # VictoriaMetrics cluster sizing
│       ├── storage_config.yml         # NFS mounts, VAST storage, S3 config
│       ├── local_repo_config.yml      # RPM repository URLs per architecture
│       ├── security_config.yml        # LDAP connection type
│       ├── high_availability_config.yml # K8s HA virtual IP
│       ├── gitlab_config.yml          # GitLab server settings
│       ├── build_stream_config.yml    # BuildStream pipeline settings
│       ├── user_registry_credential.yml # Container registry credentials
│       ├── pxe_mapping_file.csv       # Node-to-network mapping
│       └── config/                    # Per-architecture package lists
│           ├── x86_64/rhel/10.0/      # x86_64 RHEL 10 package definitions
│           └── aarch64/rhel/10.0/     # aarch64 RHEL 10 package definitions
│
├── automation_library/                # Python automation library
│   ├── core/                          # Shared infrastructure
│   │   ├── functions/                 # Host connections, config loading, reporting
│   │   ├── vars/                      # Path constants, container names
│   │   └── msgs/                      # Message templates
│   ├── checks/                        # Prerequisite validation checks
│   ├── apptainer/                     # Apptainer verification
│   ├── build_image/                   # OS image build verification
│   ├── build_stream/                  # BuildStream pipeline verification
│   ├── discovery/                     # Node discovery verification
│   ├── gitlab/                        # GitLab deployment verification
│   ├── kubernetes/                    # Kubernetes cluster verification
│   ├── local_repo/                    # Pulp repository verification
│   ├── oim_cleanup/                   # OIM cleanup verification
│   ├── omnia_sh/                      # omnia.sh install/uninstall verification
│   ├── prepare_oim/                   # OIM preparation verification
│   ├── provision/                     # Provisioned node verification
│   ├── slurm/                         # Slurm verification
│   ├── telemetry/                     # Telemetry stack verification
│   └── ...                            # Additional modules
│
├── molecule/                          # Molecule test scenarios
│   ├── conftest.py                    # Global pytest fixtures and report hooks
│   ├── shared/tasks/                  # Shared Ansible tasks
│   │   ├── setup_inventory.yml        # Dynamic inventory from omnia_test_config.yml
│   │   └── sync_project_default.yml   # Dataset sync and credential encryption
│   ├── omnia_sh_install/
│   ├── prepare_oim/
│   ├── telemetry/
│   ├── ...                            # One directory per scenario
│   └── oim_cleanup/
│
└── reports/                           # Generated test reports (gitignored)
    ├── test_report.html
    └── test_report.json
```

---

## Core Library Reference

The `automation_library/core/` module provides shared utilities used by all test modules.

### Key Functions

```python
from automation_library.core import (
    # Connection and Command Execution
    get_testinfra_host,       # Get SSH or local connection to OIM server
    run_on_oim,               # Run command on OIM host
    run_in_container,         # Run command inside omnia_core container
    run_on_remote_node,       # Run command on cluster node via SSH

    # PXE Mapping and Node Lookup
    get_node_info,            # Get single node by hostname, IP, or service tag
    get_nodes_info,           # Get multiple nodes by functional group

    # Config File Loading (reads from inside the container)
    load_input_file,          # Load YAML/JSON from /opt/omnia/input/project_default/
    get_input_value,          # Get specific value with dot-notation key
    is_software_enabled,      # Check if software is in software_config.json

    # Test Output
    TestLogger,               # Structured logging with check/passed/failed/skipped
    Colors, Symbols,          # Terminal colors and Unicode symbols

    # Credentials
    view_credentials_file,    # Decrypt ansible-vault files
    get_credential_value,     # Get specific credential value

    # Build Stream
    is_build_stream_enabled,  # Check if BuildStream CI/CD is active
    check_build_stream_stage, # Validate a specific pipeline stage

    # Node Connectivity
    verify_nodes_connectivity,# Verify ping + SSH to a list of nodes
    get_reachable_nodes,      # Get nodes that passed connectivity checks
    get_unreachable_nodes,    # Get nodes that failed connectivity checks
)
```

### Module Structure

Each automation module follows a consistent pattern:

```
automation_library/<module>/
├── __init__.py            # Public API exports
├── functions/             # Business logic and verification functions
├── messages/              # Test assertion and log message templates
└── vars/                  # Module-specific constants
```

---

## License

Copyright 2026 Dell Inc. or its subsidiaries. All Rights Reserved.

Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at

http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.
