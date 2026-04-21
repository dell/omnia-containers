# Omnia Automation Framework

End-to-end automation and Molecule-based infrastructure testing for **Omnia Infrastructure Manager (OIM)** deployments -- covering container installation, OIM preparation, local repository sync, image builds, node discovery, telemetry, Kubernetes, Slurm, and cleanup.

## Overview

This framework automates end-to-end testing of Omnia Infrastructure Manager (OIM) deployments:

1. **Configure** - Edit `omnia_test_config.yml` with OIM server details
2. **Validate** - Run prerequisite checks on the target server
3. **Test** - Execute Molecule scenarios to run playbooks and verify results
4. **Report** - View interactive HTML reports in your browser

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

| # | Scenario                | Description                                                             |
|---|-------------------------|-------------------------------------------------------------------------|
| 1 | `omnia_sh_install`      | Install `omnia_core` container via `omnia.sh` |
| 2 | `prepare_oim`           | Run `prepare_oim.yml`, verify OpenCHAMI services |
| 3 | `local_repo`            | Run `local_repo.yml`, verify Pulp repository sync |
| 4 | `build_image_x86_64`    | Build x86\_64 images, verify registry and S3 |
| 5 | `build_image_aarch64`   | Build aarch64 images |
| 6 | `discovery`             | Run `discovery.yml`, verify node provisioning |
| 7 | `telemetry`             | Run `telemetry.yml`, verify telemetry stack |
| 8 | `kubernetes`            | Verify K8s cluster health (verify-only) |
| 9 | `oim_cleanup`           | Run `oim_cleanup.yml`, verify cleanup |
| 10 | `omnia_sh_uninstall`   | Uninstall `omnia_core` container |

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

# Run specific test suites or markers
run_molecule <scenario> verify --suite sanity
run_molecule <scenario> verify --marker smoke
```

### Suite vs Marker: What's the Difference?

| Option | Purpose | Example |
|--------|---------|----------|
| `--suite` | **Folder-based filtering** - Runs tests from a specific folder under `tests/` (e.g., `sanity/`, `negative/`, `regression/`) | `--suite sanity` runs `tests/sanity/*.py` |
| `--marker` | **Decorator-based filtering** - Runs tests with a specific `@pytest.mark.<marker>` decorator regardless of folder | `--marker smoke` runs all tests with `@pytest.mark.smoke` |

**When to use which:**
- Use `--suite sanity` for standard test runs (most common)
- Use `--marker smoke` for quick critical-path validation
- Use `--marker cleanup` for cleanup-specific tests

### Test Execution Flow

```
create.yml              converge.yml                    verify (pytest)
──────────              ────────────                    ───────────────
1. Load config          1. Check omnia_core running     1. SSH to OIM server
2. Build inventory      2. Sync dataset folder          2. Run test functions
3. Wait for SSH         3. Execute ansible playbook     3. Collect results
                        4. Report playbook status       4. Generate reports
```

### Test Reports

After running tests, two report types are generated in `reports/`:

| Report | File | Description |
|--------|------|-------------|
| **HTML** | `test_report.html` | Interactive dark-themed report with collapsible sections, playbook logs, and per-test details |
| **JSON** | `test_report.json` | Machine-readable format organized by server IP for CI/CD integration |

**How to view reports:**

```bash
# Open HTML report in browser (Linux)
xdg-open reports/test_report.html

# Open HTML report in browser (macOS)
open reports/test_report.html

# Download report from remote server
scp user@automation-server:/path/to/reports/test_report.html .

# Parse JSON report
jq '.servers' reports/test_report.json
```

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

The core module provides shared infrastructure used by all test modules. Import functions from here instead of reimplementing.

### Key Functions

```python
from automation_library.core import (
    # Connection & Command Execution
    get_testinfra_host,       # Get SSH connection to OIM server
    run_on_oim,               # Run command on OIM server
    run_in_container,         # Run command inside omnia_core container
    run_on_remote_node,       # Run command on K8s/Slurm node via SSH
    
    # PXE Mapping & Node Lookup
    get_node_info,            # Get single node by hostname, IP, or service tag
    get_nodes_info,           # Get multiple nodes by functional group
    
    # Config File Loading
    load_input_file,          # Load YAML/JSON from container
    get_input_value,          # Get specific config value with dot-notation
    is_software_enabled,      # Check if software is enabled in software_config.json
    
    # Test Output
    TestLogger,               # Structured logging with check/passed/failed/skipped
    Colors, Symbols,          # Terminal colors and Unicode symbols
    
    # Credentials
    view_credentials_file,    # Decrypt ansible-vault files
    get_credential_value,     # Get specific credential value
)
```

### Module Files

| File | Purpose |
|------|---------|
| `host.py` | SSH connections, command execution, PXE mapping parsing |
| `load_inputs.py` | Load YAML/JSON config files from container |
| `formatting.py` | Colors, symbols, TestLogger for structured output |
| `report.py` | Test report generation (HTML/JSON) |
| `secrets.py` | Ansible vault decryption, credential handling |
| `build_stream.py` | BuildStream pipeline utilities |
| `db_exec.py` | Database query execution (MySQL) |
| `vars.py` | Path constants, container names, functional groups |

## License

Apache License 2.0
