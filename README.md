# Omnia Automation Framework

End-to-end automation and Molecule-based infrastructure testing for **Omnia Infrastructure Manager (OIM)** deployments -- covering container installation, OIM preparation, local repository sync, image builds, node discovery, telemetry, Kubernetes, Slurm, and cleanup.

## Overview

This framework provides:

- **Prerequisite Validation** (`oim-prereq-check`) -- Validates that the target OIM server meets hardware, OS, network, and software requirements before deployment.
- **Container Lifecycle** -- Installs/uninstalls the `omnia_core` container via `omnia.sh`, verifies SSH connectivity, systemd service registration, and NFS mounts.
- **OIM Preparation** -- Runs `prepare_oim.yml` inside the container to bring up all OpenCHAMI services (Pulp, MinIO, BSS, SMD, LDAP, etc.) and verifies their status.
- **Local Repository Management** -- Syncs RPM, container-image, and file repositories via Pulp and verifies content accessibility.
- **Image Building** -- Builds bootable OS images (initrd, rootfs, vmlinuz) for x86\_64 and aarch64, pushes to S3/registry, and verifies packages.
- **Node Discovery** -- Discovers provisioned nodes via PXE mapping, validates cloud-init, SSH, Slurm services, LDAP, and Kubernetes readiness.
- **Telemetry** -- Validates iDRAC telemetry pods, Kafka topics, LDMS metric collection, VictoriaMetrics storage, TLS, and data flow -- including node-removal verification.
- **Kubernetes Validation** -- Verifies K8s cluster health, node readiness, CRI-O runtime, HA virtual IPs, and storage classes.
- **OIM Cleanup** -- Tears down all OIM infrastructure (services, containers, volumes, credentials, firewall rules, packages) and verifies removal.
- **Reporting** -- Generates JSON and interactive HTML test reports organized by server, with playbook logs and per-test output.

## Architecture

```
                          user_config.yml
                                |
                                v
                    +-------------------------+
                    |     setup_env.sh        |  Creates .venv, installs deps,
                    |                         |  registers oim-prereq-check
                    +-------------------------+
                          |             |
              +-----------+             +-----------+
              v                                     v
  +---------------------+              +------------------------+
  | oim-prereq-check    |              |   run_molecule.sh      |
  | (CLI entry point)   |              |   (test runner)        |
  +---------------------+              +------------------------+
              |                                     |
              v                                     v
  +---------------------+              +------------------------+
  | automation_library/  |              |   molecule/            |
  |   checks/           |              |     <scenario>/        |
  |     hardware.py     |              |       molecule.yml     |
  |     network.py      |              |       create.yml       |
  |     system.py       |              |       converge.yml     |
  |     validation.py   |              |       tests/           |
  |     repository.py   |              +------------------------+
  |     services.py     |                          |
  +---------------------+                          v
                                        +------------------------+
                                        | automation_library/    |
                                        |   core/                |
                                        |   prepare_oim/         |
                                        |   telemetry/           |
                                        |   discovery/           |
                                        |   omnia_sh/            |
                                        |   local_repo/          |
                                        |   build_image/         |
                                        |   kubernetes/          |
                                        |   oim_cleanup/         |
                                        +------------------------+
```

### How It Works

1. **`user_config.yml`** provides OIM server IP, SSH credentials, hardware thresholds, network settings, and feature flags.
2. **`setup_env.sh`** creates a Python virtual environment, installs all dependencies (Ansible, Molecule, pytest-testinfra, paramiko, etc.), and registers the `oim-prereq-check` CLI command.
3. **`setup.py`** packages the `automation_library` as `omnia-automation` (v0.1.0) with the console entry point `oim-prereq-check=run_prereq_check:main`.
4. **Molecule scenarios** (executed via `run_molecule.sh`) follow a `create -> converge -> verify` lifecycle:
   - **create.yml** -- Sets up dynamic Ansible inventory from `user_config.yml` and waits for SSH.
   - **converge.yml** -- Syncs `project_default/` configs to the `omnia_core` container, then executes the target Ansible playbook via `podman exec`.
   - **verify** -- Runs pytest-testinfra tests that use `automation_library` functions to validate the deployment.
5. **`automation_library/core/`** provides shared infrastructure: testinfra host connections (`host.py`), config file loading with caching (`load_inputs.py`), PXE mapping CSV parsing, container command execution, credential handling via ansible-vault (`secrets.py`), and HTML/JSON report generation (`report.py`).
6. Each domain module (e.g., `telemetry/`, `discovery/`) follows a consistent `functions/` + `messages/` + `vars/` structure.

## Quick Start

```bash
# 1. Clone the repository
git clone https://github.com/dell/omnia-artifactory.git
cd omnia-artifactory

# 2. Setup virtual environment
./setup_env.sh
source .venv/bin/activate

# 3. Configure your settings
vi user_config.yml          # OIM server IP, SSH creds, thresholds
vi project_default/*.yml    # Omnia config files (network, storage, telemetry, etc.)

# 4. Run prerequisite checks
oim-prereq-check

# 5. Run molecule tests
./run_molecule.sh all test          # All scenarios end-to-end
./run_molecule.sh telemetry verify  # Single scenario, verify only
```

## Installation

```bash
# Option 1: Using setup script (recommended)
./setup_env.sh            # Creates .venv, installs deps, registers CLI
source .venv/bin/activate

# Option 2: Manual installation
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt   # Installs ansible-core, molecule, pytest-testinfra, etc.
```

### Dependencies (requirements.txt)

| Package              | Version   | Purpose                          |
|----------------------|-----------|----------------------------------|
| ansible-core         | 2.20.1    | Ansible automation engine        |
| molecule             | 25.12.0   | Infrastructure test framework    |
| molecule-plugins     | 25.8.12   | Molecule driver plugins          |
| paramiko             | 4.0.0     | SSH protocol library             |
| pexpect              | 4.9.0     | Interactive process control      |
| pytest               | 9.0.2     | Test framework                   |
| pytest-testinfra     | 10.2.2    | Infrastructure testing via SSH   |
| PyYAML               | 6.0.1     | YAML parsing                     |

### System Requirements

- Python 3.9+ (3.12+ recommended)
- `sshpass` (auto-installed by `setup_env.sh`)
- SSH access to the target OIM server
- Podman on the OIM server (for container management)

## Configuration

### user\_config.yml (Required)

Central configuration for all automation tasks. Edit this file before running anything:

```yaml
# ── Target OIM Server (REQUIRED) ───────────────────────────
oim_server_ip: "192.168.1.100"
oim_ssh_user: "root"
oim_ssh_password: "your_password"
oim_ssh_port: 22

# ── Hostname ────────────────────────────────────────────────
oim_hostname: "oim.example.com"        # FQDN for OIM server

# ── Hardware Thresholds ─────────────────────────────────────
min_cores: 4
min_memory_gb: 8
min_disk_gb: 50

# ── OS Validation ───────────────────────────────────────────
required_os: "rhel"
required_os_version: "10"
required_kernel_version: "6.12.0-55.9.1.el10_0.x86_64"

# ── Network ─────────────────────────────────────────────────
network_type: "dedicated"               # "dedicated" or "lom"
pxe_interface: "eno1"
public_interface: "eno2"
pxe_ip: "172.16.107.254/24"
force_configure_pxe: false

# ── NFS ─────────────────────────────────────────────────────
nfs_server_ip: "192.168.1.200"
nfs_share_path: "/mnt/share"
nfs_min_capacity_gb: 100

# ── Podman ──────────────────────────────────────────────────
podman_min_version: "5.0.0"

# ── Container Image Build (optional) ───────────────────────
reconfigure_images: false
omnia_repo_url: "https://github.com/dell/omnia-artifactory.git"
artifactory_branch: "omnia-container"
omnia_clone_path: "/opt/omnia-artifactory"
omnia_branch: "pub/k8s_telemetry"

# ── omnia.sh Installation ──────────────────────────────────
share_option: "NFS"                     # "NFS" or "Local"
nfs_type: "external"                    # "external" or "internal"
omnia_shared_path: "/opt/omnia"
omnia_core_password: "password"

# ── LDAP (optional) ────────────────────────────────────────
ldap_credentials:
  - username: "testuser1"
    password: "testpass"
```

### project\_default/ Directory

Omnia deployment configuration files synced into the `omnia_core` container:

| File                           | Purpose                                                          |
|--------------------------------|------------------------------------------------------------------|
| `network_spec.yml`             | Admin network (PXE NIC, DHCP range, DNS, NTP), InfiniBand        |
| `provision_config.yml`         | PXE mapping file path, DHCP lease time, OS language              |
| `omnia_config.yml`             | Slurm and Kubernetes cluster definitions, CNI, pod networks      |
| `telemetry_config.yml`         | iDRAC telemetry, VictoriaMetrics, Kafka, LDMS sampler plugins    |
| `storage_config.yml`           | NFS and PowerVault persistent storage backends                   |
| `local_repo_config.yml`        | Pulp repository URLs (RPM, container, file) per architecture     |
| `security_config.yml`          | LDAP connection type (TLS/SSL)                                   |
| `high_availability_config.yml` | K8s HA virtual IP configuration                                  |
| `build_stream_config.yml`      | BuildStream CI/CD pipeline settings                              |
| `user_registry_credential.yml` | Container registry authentication credentials                    |

## Prerequisite Check

Validates the OIM server before deployment:

```bash
oim-prereq-check                    # Run all checks
oim-prereq-check --debug            # With debug output
oim-prereq-check --stop-on-failure  # Stop on first failure
oim-prereq-check --no-report        # Skip report generation
```

### Checks Performed

| # | Check                | Description                                                |
|---|----------------------|------------------------------------------------------------|
| 1 | IPMI Tool            | Verify/install ipmitool                                    |
| 2 | Hardware Inventory   | Validate CPU cores, memory, disk, DIMMs, storage           |
| 3 | OS Validation        | Validate OS name, version, and kernel                      |
| 4 | Network Interfaces   | Validate PXE and Public interfaces exist and are UP        |
| 5 | PXE NIC Config       | Configure PXE interface IP address                         |
| 6 | NFS Server           | Ping NFS server and verify share capacity                  |
| 7 | Internet Access      | Test internet connectivity via public interface            |
| 8 | Podman               | Validate Podman installation and version                   |
| 9 | RHEL Repository      | Check RHEL repository availability                         |
| 10 | Git                 | Verify/install git (if `reconfigure_images=true`)          |
| 11 | Omnia Artifactory   | Clone repository and download `omnia.sh` (if reconfigure)  |
| 12 | Container Images    | Build container images (if `reconfigure_images=true`)      |

The check runs either locally or remotely over SSH depending on whether `oim_server_ip` is the local machine. Results are printed with colored output and optionally saved as an HTML report.

## Molecule Testing

### Scenarios

Tests are organized into ordered scenarios that cover the full OIM lifecycle:

| # | Scenario                | Tests | What It Does                                                            |
|---|-------------------------|-------|-------------------------------------------------------------------------|
| 1 | `omnia_sh_install`      | 6     | Install `omnia_core` container via `omnia.sh`, verify container/service/SSH |
| 2 | `prepare_oim`           | 9     | Run `prepare_oim.yml`, verify services, containers, OpenCHAMI, Pulp, LDAP, BSS/SMD |
| 3 | `local_repo`            | 11    | Run `local_repo.yml`, verify Pulp API, repository sync, content accessibility |
| 4 | `build_image_x86_64`    | 4     | Build x86\_64 images, verify functional groups, registry, S3, packages  |
| 5 | `build_image_aarch64`   | 4     | Build aarch64 images (same checks as x86\_64)                          |
| 6 | `discovery`             | 18    | Run `discovery.yml`, verify cloud-init, SSH, Slurm, LDAP, K8s nodes    |
| 7 | `telemetry`             | 24    | Run `telemetry.yml`, verify iDRAC pods, Kafka, LDMS, VictoriaMetrics, node deletion |
| 8 | `kubernetes`            | 11+   | Verify K8s cluster health, nodes, CRI-O, HA, storage (verify-only)     |
| 9 | `oim_cleanup`           | 9     | Run `oim_cleanup.yml`, verify all resources removed                     |
| 10 | `omnia_sh_uninstall`   | 4     | Uninstall `omnia_core`, verify container/service/mount removed          |

### Running Tests

```bash
# List available scenarios
./run_molecule.sh list

# Run all scenarios sequentially (full lifecycle)
./run_molecule.sh all test

# Run a specific scenario
./run_molecule.sh <scenario> test       # Full lifecycle (create + converge + verify)
./run_molecule.sh <scenario> converge   # Run playbook only
./run_molecule.sh <scenario> verify     # Run tests only (skip playbook)
./run_molecule.sh <scenario> create     # Setup inventory only
```

When running `all`, a shared `OMNIA_REPORT_ID` UUID links all scenario results into a single report run.

### Test Execution Flow

Each scenario follows the Molecule lifecycle:

```
create.yml                    converge.yml                       verify (pytest)
───────────                   ────────────                       ──────────────
1. Load user_config.yml       1. Setup inventory                 1. conftest.py:
2. Add OIM to inventory       2. Check omnia_core running           - SSH pre-checks
3. Wait for SSH               3. Sync project_default/              - Create host fixture
                              4. Run ansible playbook               - Init TestReport
                                 via podman exec               2. test_*.py:
                              5. Report success/failure            - Use automation_library
                                                                     functions
                                                                  - Assert results
                                                               3. Save report
```

### Test Reports

After running tests, reports are generated in `reports/`:
- `test_report.json` -- Machine-readable JSON organized by server IP
- `test_report.html` -- Interactive HTML report with dark theme, collapsible sections, and playbook logs

Report structure:
```
servers -> <server_ip> -> runs[] -> modules[] -> results[]
```

Each result includes: test name, status (PASSED/FAILED/SKIPPED), duration, details, and error message.

## Project Structure

```
omnia-artifactory/
├── user_config.yml                  # User configuration (OIM server, thresholds)
├── requirements.txt                 # Python dependencies
├── setup.py                         # Package setup (omnia-automation v0.1.0)
├── setup_env.sh                     # Environment setup script
├── run_molecule.sh                  # Molecule test runner
├── run_prereq_check.py              # Prerequisite check entry point
│
├── project_default/                 # Omnia deployment configs (synced to container)
│   ├── network_spec.yml             #   Admin/IB network, DHCP, DNS, NTP
│   ├── provision_config.yml         #   PXE mapping, DHCP lease
│   ├── omnia_config.yml             #   Slurm + K8s cluster definitions
│   ├── telemetry_config.yml         #   iDRAC, VictoriaMetrics, Kafka, LDMS
│   ├── storage_config.yml           #   NFS and PowerVault storage
│   ├── local_repo_config.yml        #   Pulp repository URLs per architecture
│   ├── security_config.yml          #   LDAP TLS/SSL
│   ├── high_availability_config.yml #   K8s HA virtual IPs
│   ├── build_stream_config.yml      #   BuildStream CI/CD
│   └── user_registry_credential.yml #   Registry credentials
│
├── automation_library/              # Python automation library
│   ├── core/                        # Shared infrastructure
│   │   ├── formatting.py            #   Colors, Symbols, TestLogger, log()
│   │   ├── host.py                  #   Testinfra connections, PXE mapping parser
│   │   ├── load_inputs.py           #   Config file loader with caching
│   │   ├── report.py                #   JSON + HTML report generator
│   │   ├── secrets.py               #   Ansible-vault credential handling
│   │   └── vars.py                  #   Path constants, file names, functional groups
│   │
│   ├── checks/                      # Prerequisite validation
│   │   ├── functions/
│   │   │   ├── main.py              #   Orchestration + PrereqReport
│   │   │   ├── hardware.py          #   IPMI, CPU, memory, disk checks
│   │   │   ├── network.py           #   Interface validation, PXE config, connectivity
│   │   │   ├── system.py            #   Command execution (local/remote SSH)
│   │   │   ├── validation.py        #   OS and Podman validation
│   │   │   ├── repository.py        #   RHEL repo, git, artifactory clone
│   │   │   └── services.py          #   NFS reachability
│   │   ├── messages/
│   │   │   └── oim_prereq_msgs.py   #   User-facing messages
│   │   └── vars/
│   │       └── oim_prereq_vars.py   #   Config loaded from user_config.yml
│   │
│   ├── omnia_sh/                    # omnia.sh install/uninstall
│   │   ├── functions/omnia_sh_func.py
│   │   ├── messages/omnia_sh_msgs.py
│   │   └── vars/omnia_sh_vars.py
│   │
│   ├── prepare_oim/                 # OIM preparation verification
│   │   ├── functions/prepare_oim_func.py  # Service, container, BSS/SMD, Pulp, LDAP checks
│   │   ├── messages/prepare_oim_msgs.py
│   │   └── vars/prepare_oim_vars.py       # Container lists, service lists, auth settings
│   │
│   ├── local_repo/                  # Pulp repository verification
│   │   ├── functions/local_repo_func.py
│   │   ├── messages/local_repo_msgs.py
│   │   └── vars/local_repo_vars.py
│   │
│   ├── build_image/                 # OS image build verification
│   │   ├── functions/build_image_func.py
│   │   ├── messages/build_image_msgs.py
│   │   └── vars/build_image_vars.py
│   │
│   ├── discovery/                   # Node discovery verification
│   │   ├── functions/
│   │   │   ├── common_func.py       #   SSH, cloud-init, node retrieval
│   │   │   ├── slurm_func.py        #   Slurm services, sinfo, OpenMPI, UCX, LDMS
│   │   │   └── ldap_func.py         #   LDAP slapd.conf, user login verification
│   │   ├── messages/discovery_msgs.py
│   │   └── vars/
│   │       ├── common_vars.py
│   │       ├── slurm_vars.py
│   │       └── ldap_vars.py
│   │
│   ├── telemetry/                   # Telemetry verification
│   │   ├── functions/
│   │   │   ├── shared_func.py       #   Config reading, enable checks, caching
│   │   │   ├── idrac_telemetry_func.py  # Pod count, MySQL data, receiver metrics
│   │   │   ├── kafka_func.py        #   Kafka topics, config, LDMS pods, data flow
│   │   │   ├── victoria_func.py     #   VictoriaMetrics pods, TLS, persistence, data
│   │   │   └── delete_node_func.py  #   Node removal detection, data cleanup verification
│   │   ├── messages/
│   │   │   ├── shared_msgs.py
│   │   │   ├── idrac_telemetry_msgs.py
│   │   │   ├── kafka_msgs.py
│   │   │   ├── victoria_msgs.py
│   │   │   └── delete_node_msgs.py
│   │   └── vars/
│   │       ├── shared_vars.py
│   │       ├── idrac_telemetry_vars.py
│   │       ├── kafka_vars.py
│   │       └── victoria_vars.py
│   │
│   ├── kubernetes/                  # K8s cluster verification
│   │   ├── functions/k8s_func.py    #   OIMOperations class
│   │   ├── messages/k8s_msgs.py
│   │   └── vars/k8s_vars.py
│   │
│   └── oim_cleanup/                 # OIM cleanup verification
│       ├── functions/oim_cleanup_func.py
│       ├── messages/oim_cleanup_msgs.py
│       └── vars/oim_cleanup_vars.py
│
├── molecule/                        # Molecule test scenarios
│   ├── conftest.py                  # Global pytest config (SSH fixture, report hooks)
│   ├── shared/tasks/
│   │   ├── setup_inventory.yml      #   Dynamic inventory from user_config.yml
│   │   └── sync_project_default.yml #   Rsync configs + vault-encrypt credentials
│   │
│   ├── omnia_sh_install/            # Scenario: Install omnia_core
│   │   ├── molecule.yml
│   │   ├── create.yml
│   │   ├── prepare.yml              #   Pre-install validation (Podman, hostname, image)
│   │   ├── converge.yml             #   Run omnia.sh --install
│   │   └── tests/test_omnia_sh.py
│   │
│   ├── prepare_oim/                 # Scenario: OIM preparation
│   │   ├── molecule.yml
│   │   ├── create.yml
│   │   ├── converge.yml             #   Run prepare_oim.yml
│   │   └── tests/test_prepare_oim.py
│   │
│   ├── local_repo/                  # Scenario: Pulp repo sync
│   │   ├── molecule.yml
│   │   ├── create.yml
│   │   ├── converge.yml             #   Run local_repo.yml (with Pulp health checks)
│   │   └── tests/test_local_repo.py
│   │
│   ├── build_image_x86_64/          # Scenario: x86_64 image build
│   │   ├── molecule.yml
│   │   ├── create.yml
│   │   ├── converge.yml             #   Run build_image_x86_64.yml
│   │   └── tests/test_build_image_x86_64.py
│   │
│   ├── build_image_aarch64/         # Scenario: aarch64 image build
│   │   ├── molecule.yml
│   │   ├── create.yml
│   │   ├── converge.yml             #   Run build_image_aarch64.yml
│   │   └── tests/test_build_image_aarch64.py
│   │
│   ├── discovery/                   # Scenario: Node discovery
│   │   ├── molecule.yml
│   │   ├── create.yml
│   │   ├── converge.yml             #   Run discovery.yml
│   │   └── tests/
│   │       ├── test_cloudinit.py    #   Cloud-init completion
│   │       ├── test_ssh.py          #   SSH from OIM/container to nodes
│   │       ├── test_slurm.py        #   Slurm services, sinfo, SSH, LDAP, LDMS
│   │       └── test_k8s_telemetry.py  # K8s nodes + telemetry pods
│   │
│   ├── telemetry/                   # Scenario: Telemetry
│   │   ├── molecule.yml
│   │   ├── create.yml
│   │   ├── converge.yml             #   Run telemetry.yml (with 4 prerequisite checks)
│   │   ├── tasks/                   #   Prerequisite checks:
│   │   │   ├── check_container_and_telemetry_support.yml
│   │   │   ├── check_service_cluster.yml
│   │   │   ├── check_pxe_and_pod_count.yml
│   │   │   └── check_bmc_group_data.yml
│   │   ├── vars/vars.yml
│   │   └── tests/
│   │       ├── test_idrac_telemetry.py   # Pod count, pod status, MySQL, receiver
│   │       ├── test_kafka_telemetry.py   # LDMS pods, Kafka topics/config, data flow
│   │       ├── test_victoria_telemetry.py  # Pods, persistence, TLS, services, data
│   │       └── test_delete_node.py       # Node removal verification (MySQL, Kafka, VM)
│   │
│   ├── kubernetes/                  # Scenario: K8s validation (verify-only)
│   │   ├── molecule.yml
│   │   └── tests/test_k8s.py
│   │
│   ├── oim_cleanup/                 # Scenario: OIM cleanup
│   │   ├── molecule.yml
│   │   ├── converge.yml             #   Run oim_cleanup.yml
│   │   └── tests/test_oim_cleanup.py
│   │
│   └── omnia_sh_uninstall/          # Scenario: Uninstall omnia_core
│       ├── molecule.yml
│       ├── converge.yml             #   Run omnia.sh --uninstall
│       └── tests/test_uninstall.py
│
├── .config/
│   ├── ansible-lint.yml             # Ansible linting rules
│   └── requirements.yml             # Ansible collection dependencies
│
└── reports/                         # Generated test reports (gitignored)
    ├── test_report.json
    └── test_report.html
```

## Core Library (`automation_library/core/`)

The core module provides shared infrastructure used by all domain modules:

### host.py -- Host Connections & PXE Mapping

- `get_testinfra_host()` -- Returns a testinfra host connected to the OIM server via SSH (auto-detects local vs remote).
- `run_on_oim(host, cmd)` -- Executes a command on the OIM server.
- `run_in_container(host, cmd, container)` -- Executes a command inside a Podman container (default: `omnia_core`).
- `run_on_remote_node(host, cmd, admin_ip)` -- Executes a command on a remote node via SSH from the OIM server.
- `get_node_info(host, search_by, value)` / `get_nodes_info(...)` -- Parses the PXE mapping CSV to look up nodes by functional group, hostname, service tag, admin IP, or BMC IP.
- `check_container_running(host, name)` -- Checks if a Podman container is running.

### load\_inputs.py -- Config File Loader

- `load_input_file(host, filename)` -- Loads a YAML/JSON file from `/opt/omnia/input/project_default` inside the container, with automatic caching.
- `get_input_value(host, filename, key)` -- Gets a single value using dot-notation keys (e.g., `"Networks[0].admin_network.oim_nic_name"`).
- `is_software_enabled(host, name)` -- Checks if a software component is enabled in `software_config.json`.

### formatting.py -- Terminal Output

- `Colors` / `Symbols` classes -- ANSI color codes and Unicode symbols (auto-disabled when no TTY).
- `TestLogger` -- Structured logger for test output with `check()`, `passed()`, `failed()`, `skipped()` methods.
- `log(message, level)` -- Timestamped log with color.

### report.py -- Test Reports

- `TestReport(module_name, report_id)` -- Collects test results and generates JSON/HTML reports.
- Results are organized by server IP and grouped by module within each test run.
- HTML reports feature a dark theme, collapsible sections, and embedded playbook logs.

### secrets.py -- Credential Handling

- `view_credentials_file(host, path, key_path)` -- Decrypts ansible-vault files or reads plain YAML.
- `get_credential_value(host, path, key_path, key)` -- Gets a single credential value.

### vars.py -- Path Constants

Defines all container paths (`/opt/omnia/...`), config file names, container names, and functional group identifiers used throughout the library.

## Module Structure Pattern

Every domain module follows a consistent three-directory structure:

```
automation_library/<module>/
├── functions/      # Business logic (verification functions)
│   └── <module>_func.py
├── messages/       # User-facing strings (test names, log messages, assert messages)
│   └── <module>_msgs.py
└── vars/           # Configuration constants and thresholds
    └── <module>_vars.py
```

Functions return structured dicts with `success`, `details`/`results`, and `error` keys. Messages provide formatted strings with placeholders for dynamic values and remediation instructions.

## Telemetry Test Details

The telemetry scenario (24 tests) covers the full telemetry stack:

**iDRAC Telemetry** (tests 1-4):
- Pod count matches `service_kube_node` count + 1 (management pod)
- All telemetry pods in Running state (retry 3x with 60s intervals)
- MySQL contains data for activated BMC IPs
- Receiver pod collecting metrics

**Kafka** (tests 5-11):
- LDMS aggregator and store pods running
- LDMS service ports match `telemetry_config.yml`
- Expected Kafka topics exist via REST proxy
- Kafka cluster config matches declared settings
- iDRAC data flowing to `idrac` topic (verified via Redfish service tag lookup)
- LDMS data in topics (both earliest and latest, all sampler plugins)

**VictoriaMetrics** (tests 12-20):
- Deployment mode (single-node or cluster) with correct pod count
- PVC persistence size matches config
- VMagent pod running
- Services have external LoadBalancer IPs
- TLS secret present with `tls.crt`, `tls.key`, `ca.crt`
- HTTPS health endpoint responding
- iDRAC metric data queryable

**Node Deletion** (tests 21-24):
- Uses PXE mapping backup (`.backup/.pxe_mapping.csv`) to detect removed nodes
- Verifies deleted BMC IPs absent from MySQL
- Verifies deleted service tags absent from Kafka `idrac` topic
- Verifies deleted LDMS hostnames absent from Kafka `ldms` topic
- Verifies deleted service tags absent from VictoriaMetrics
- Skips gracefully on first run (no backup) or when no deletions detected

## Discovery Test Details

The discovery scenario (18 tests) validates post-provisioning state:

- **Cloud-init** -- All discovered nodes completed cloud-init without errors
- **SSH** (4 tests) -- Passwordless SSH from OIM and from `omnia_core` container to all nodes, via both admin IP and hostname
- **Slurm** (11 tests) -- Control node services (slurmctld, slurmdbd, munge, mariadb, sssd), compute/login node services (slurmd, munge, sssd), cross-node SSH, `sinfo` node list, optional OpenMPI/UCX/LDMS verification, LDAP slapd configuration and user login
- **Kubernetes** (2 tests) -- K8s nodes from PXE mapping in Ready state, telemetry pods running

## Contributing

1. Follow the existing `functions/` + `messages/` + `vars/` module pattern.
2. Use `@pytest.mark.order(n)` to control test execution order.
3. Use `automation_library.core` functions for all host operations -- never shell out directly.
4. Return structured dicts from functions (`success`, `details`, `error`).
5. Add user-facing messages with remediation instructions in `messages/`.

## License

Apache License 2.0
