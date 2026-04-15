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
                          omnia_test_config.yml
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

1. **`omnia_test_config.yml`** provides OIM server IP, SSH credentials, hardware thresholds, network settings, and dataset selection.
2. **`setup_env.sh`** creates a Python virtual environment, installs all dependencies, and registers the `oim-prereq-check` CLI command.
3. **`setup.py`** packages the `automation_library` as `omnia-automation` with the console entry point `oim-prereq-check=run_prereq_check:main`.
4. **Molecule scenarios** (executed via `run_molecule.sh`) follow a `create -> converge -> verify` lifecycle:
   - **create.yml** -- Sets up dynamic Ansible inventory from `omnia_test_config.yml` and waits for SSH.
   - **converge.yml** -- Syncs the configured dataset folder (e.g., `datasets/project_default/`) to the `omnia_core` container, then executes the target Ansible playbook via `podman exec`.
   - **verify** -- Runs pytest-testinfra tests that use `automation_library` functions to validate the deployment.
5. **`automation_library/core/`** provides shared infrastructure for host connections, config loading, PXE mapping parsing, container commands, and report generation.

## Quick Start

```bash
# 1. Clone the repository
git clone https://github.com/dell/omnia-artifactory.git
cd omnia-artifactory

# 2. Setup virtual environment
./setup_env.sh
source .venv/bin/activate

# 3. Configure your settings
vi omnia_test_config.yml              # OIM server IP, SSH creds, dataset selection
vi datasets/project_default/*.yml     # Omnia config files (network, storage, telemetry, etc.)

# 4. Run prerequisite checks
oim-prereq-check

# 5. Run molecule tests
run_molecule all test                    # All scenarios end-to-end
run_molecule telemetry verify            # Single scenario, verify only
run_molecule prepare_oim verify --suite sanity  # Run sanity tests only
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

### omnia\_test\_config.yml (Required)

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

### datasets/project\_default/ Directory

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
run_molecule list

# Run all scenarios sequentially (full lifecycle)
run_molecule all test

# Run a specific scenario
run_molecule <scenario> test       # Full lifecycle (create + converge + verify)
run_molecule <scenario> converge   # Run playbook only
run_molecule <scenario> verify     # Run tests only (skip playbook)
run_molecule <scenario> create     # Setup inventory only

# Run specific test suites
run_molecule <scenario> verify --suite sanity     # Run sanity tests only
run_molecule <scenario> verify --suite negative   # Run negative tests only
run_molecule <scenario> verify --marker smoke     # Run smoke tests
```

When running `all`, a shared `OMNIA_REPORT_ID` UUID links all scenario results into a single report run.

### Test Execution Flow

Each scenario follows the Molecule lifecycle:

```
create.yml                    converge.yml                       verify (pytest)
───────────                   ────────────                       ──────────────
1. Load omnia_test_config.yml       1. Setup inventory                 1. conftest.py:
2. Add OIM to inventory       2. Check omnia_core running           - SSH pre-checks
3. Wait for SSH               3. Sync dataset folder              - Create host fixture
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
├── omnia_test_config.yml            # Test configuration (OIM server, credentials, dataset)
├── requirements.txt                 # Python dependencies
├── setup.py                         # Package setup (omnia-automation)
├── setup_env.sh                     # Environment setup script
├── run_molecule.sh                  # Molecule test runner
├── run_prereq_check.py              # Prerequisite check entry point
│
├── datasets/                        # Input configuration datasets
│   └── project_default/             # Default dataset (synced to container)
│       ├── network_spec.yml
│       ├── provision_config.yml
│       ├── telemetry_config.yml
│       └── ...
│
├── automation_library/              # Python automation library
│   ├── core/                        # Shared infrastructure
│   ├── checks/                      # Prerequisite validation
│   ├── omnia_sh/                    # omnia.sh install/uninstall
│   ├── prepare_oim/                 # OIM preparation verification
│   ├── local_repo/                  # Pulp repository verification
│   ├── build_image/                 # OS image build verification
│   ├── discovery/                   # Node discovery verification
│   ├── telemetry/                   # Telemetry verification
│   ├── kubernetes/                  # K8s cluster verification
│   └── oim_cleanup/                 # OIM cleanup verification
│
├── molecule/                        # Molecule test scenarios
│   ├── conftest.py                  # Global pytest config
│   ├── shared/tasks/                # Shared Ansible tasks
│   └── <scenario>/                  # Individual scenarios
│       ├── molecule.yml
│       ├── create.yml
│       ├── converge.yml
│       └── tests/sanity/            # Test suite folder
│
└── reports/                         # Generated test reports (gitignored)
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

## License

Apache License 2.0
