# Omnia Automation Framework

Automation library for OIM (Omnia Infrastructure Manager) deployment, testing, and management.

## Overview

This framework provides:
- **Prerequisite Validation** - Validates OIM server meets all requirements
- **Container Image Build** - Clones repository and builds Omnia container images
- **Automated Testing** - Molecule-based infrastructure testing with detailed reports

## Quick Start

```bash
# 1. Clone the repository
git clone https://github.com/dell/omnia-artifactory.git
cd omnia-artifactory

# 2. Setup virtual environment
./setup_env.sh
source .venv/bin/activate

# 3. Configure your settings
vi user_config.yml

# 4. Run prerequisite checks
oim-prereq-check

# 5. Run molecule tests (optional)
./run_molecule.sh all test
```

## Workflow

```
┌─────────────────────────────────────────────────────────────┐
│  1. CONFIGURE                                               │
│     Edit user_config.yml with target server details         │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│  2. PREREQUISITE CHECK (oim-prereq-check)                   │
│     • Validates hardware, OS, network                       │
│     • Configures PXE interface                              │
│     • Verifies NFS connectivity                             │
│     • Clones omnia-artifactory repository                   │
│     • Builds container images                               │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│  ✓ OIM SERVER READY FOR DEPLOYMENT                          │
│     All prerequisites passed. Server is ready for omnia.sh  │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│  3. MOLECULE TESTS (optional)                               │
│     • Runs omnia.sh installation                            │
│     • Validates deployment                                  │
│     • Generates HTML/JSON reports                           │
└─────────────────────────────────────────────────────────────┘
```

## Installation

```bash
# Option 1: Using setup script (recommended)
./setup_env.sh
source .venv/bin/activate

# Option 2: Manual installation
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Molecule Testing

Run automated infrastructure tests:

```bash
# List available scenarios
./run_molecule.sh list

# Run all scenarios
./run_molecule.sh all test

# Run specific scenario
./run_molecule.sh <scenario> test

# Other commands
./run_molecule.sh <scenario> converge   # Run playbooks only
./run_molecule.sh <scenario> verify     # Run tests only
./run_molecule.sh <scenario> destroy    # Cleanup
```

### Test Reports

After running tests, reports are generated in `reports/`:
- `test_report.json` - JSON format
- `test_report.html` - Interactive HTML report

## Configuration

Edit `user_config.yml` in the project root:

```yaml
# Target OIM Server (REQUIRED)
oim_server_ip: "192.168.1.100"      # Remote server IP
oim_ssh_user: "root"                 # SSH username
oim_ssh_password: "your_password"    # SSH password

# OS Validation
required_os: "rhel"
required_os_version: "10"
required_kernel_version: "6.12.0-55.9.1.el10_0.x86_64"

# Hardware Requirements
min_cores: 4
min_memory_gb: 8
min_disk_gb: 50

# Network Interfaces
pxe_interface: "eno1"
public_interface: "eno2"
pxe_ip: "172.16.107.254/24"

# NFS Configuration
nfs_server_ip: "192.168.1.200"
nfs_share_path: "/mnt/share"
nfs_min_capacity_gb: 100

# Podman
podman_min_version: "4.0.0"

# Container Image Build (optional)
reconfigure_images: false            # Set true to clone repo & build images
artifactory_repo_url: "https://github.com/dell/omnia-artifactory.git"
artifactory_branch: "omnia-container"
omnia_clone_path: "/opt/omnia-artifactory"
container_images: "core"
omnia_branch: "pub/k8s_telemetry"    # Required if reconfigure_images is true

# Behavior
skip_on_failure: true                # true=continue all checks, false=stop on first failure
```

## Prerequisite Check

Validate OIM server prerequisites before deployment:

```bash
oim-prereq-check              # Run all checks
oim-prereq-check --debug      # With debug output
oim-prereq-check --help       # Show help
```

### Checks Performed

| # | Check | Description |
|---|-------|-------------|
| 1 | IPMI Tool | Verify/install ipmitool |
| 2 | Hardware Inventory | Validate CPU cores, memory, disk space |
| 3 | OS Validation | Validate OS, version, and kernel |
| 4 | Network Interfaces | Validate PXE and Public interfaces exist and are UP |
| 5 | PXE NIC Configuration | Configure PXE interface IP address |
| 6 | NFS Server | Ping NFS server and verify share capacity |
| 7 | Internet Connectivity | Test internet access via public interface |
| 8 | Podman | Validate Podman version |
| 9 | RHEL Repository | Check RHEL repository availability |
| 10 | Git | Verify/install git (if reconfigure_images=true) |
| 11 | Omnia Artifactory | Clone repository & download omnia.sh (if reconfigure_images=true) |
| 12 | Container Images | Build container images (if reconfigure_images=true) |

## Project Structure

```
omnia-artifactory/
├── user_config.yml           # ← EDIT THIS FILE
├── requirements.txt          # Dependencies
├── setup.py                  # Package setup
├── setup_env.sh              # Virtual environment setup
├── run_molecule.sh           # Molecule test runner
├── run_prereq_check.py       # Prerequisite check runner
├── README.md
├── automation_library/
│   ├── core/                 # Core utilities
│   │   ├── formatting.py     # Logging and colors
│   │   ├── host.py           # Testinfra host utilities
│   │   └── report.py         # Test report generator
│   ├── vars/                 # Configuration variables
│   ├── messages/             # User-facing messages
│   └── functions/            # Business logic
├── molecule/
│   ├── conftest.py           # Pytest configuration
│   ├── shared/               # Shared tasks
│   └── <scenario>/           # Test scenarios
│       ├── molecule.yml
│       ├── converge.yml
│       └── tests/
└── reports/                  # Generated test reports
```

## Requirements

- Python 3.12+
- SSH access to target OIM server
- `sshpass` (auto-installed if needed)

## License

Apache License 2.0
