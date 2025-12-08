# OIM Prerequisite Check Tool

Tool to validate prerequisites for OIM (Omnia Infrastructure Manager) deployment on a remote server.

> **Note:** This is the prerequisite check tool only. Full automation is under development.

## Quick Start

```bash
# 1. Clone/navigate to the project
cd /opt/omnia/balaji/omnia_automation

# 2. Install the tool
pip install -r requirements.txt

# 3. Configure your settings
vi user_config.yml

# 4. Run the prerequisite check
oim-prereq-check
```

## Installation

```bash
pip install -r requirements.txt
```

This installs all dependencies and the `oim-prereq-check` command.

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

## Usage

```bash
# Run prerequisite checks
oim-prereq-check

# Show help
oim-prereq-check --help

# Run with debug output
oim-prereq-check --debug

# Override config: stop on first failure
oim-prereq-check --stop-on-failure

# Override config: continue on failure
oim-prereq-check --continue-on-failure

# Don't save report file
oim-prereq-check --no-report
```

## Checks Performed

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

## Report

After running, a report is saved to:
```
oim_prereq_report.txt
```

## Requirements

- Python 3.9+
- `sshpass` (auto-installed if using password authentication)
- Remote server accessible via SSH

## Project Structure

```
omnia_automation/
├── user_config.yml          # ← EDIT THIS FILE
├── run_prereq_check.py      # Main runner script
├── requirements.txt         # Dependencies
├── setup.py                 # Package setup
├── README.md
└── automation_library/
    ├── vars/
    │   └── oim_prereq_vars.py
    ├── messages/
    │   └── oim_prereq_msgs.py
    └── functions/
        └── oim_prereq_func.py
```

## License

Apache License 2.0
