# Omnia Automation Framework - Implementation Guide

Comprehensive technical documentation for the Omnia Automation Framework architecture, execution flow, and development patterns.

---

## Table of Contents

1. [Framework Overview](#1-framework-overview)
2. [Architecture](#2-architecture)
3. [Execution Flow](#3-execution-flow)
4. [Core Library](#4-core-library)
5. [Module Structure](#5-module-structure)
6. [Configuration Reference](#6-configuration-reference)
7. [Development Guide](#7-development-guide)
8. [Troubleshooting](#8-troubleshooting)

---

## 1. Framework Overview

### What This Framework Does

The Omnia Automation Framework automates end-to-end testing of Omnia Infrastructure Manager (OIM) deployments. It:

1. **Configures** - User edits `omnia_test_config.yml` with OIM server details and dataset selection
2. **Validates** - Runs prerequisite checks on the target OIM server
3. **Executes** - Runs Ansible playbooks inside the `omnia_core` container
4. **Verifies** - Runs pytest tests to validate deployment state
5. **Reports** - Generates interactive HTML and JSON reports for download and browser viewing

### Technology Stack

| Component | Purpose |
|-----------|----------|
| **Molecule** | Test orchestration for Ansible playbooks |
| **Pytest** | Python test framework with markers and fixtures |
| **Testinfra** | Infrastructure testing via SSH |
| **Ansible** | Playbook execution inside containers |
| **Ansible-lint** | Playbook linting and validation |

### Test Report Types

The framework generates two report formats:

| Report | Location | Description |
|--------|----------|-------------|
| **HTML Report** | `reports/test_report.html` | Interactive dark-themed report with collapsible sections, playbook logs, and per-test details. Open in browser. |
| **JSON Report** | `reports/test_report.json` | Machine-readable format organized by server IP, suitable for CI/CD integration. |

---

## 2. Architecture

### Connection Topology

```
┌─────────────────────────────────────────────────────────────────────────┐
│  AUTOMATION SERVER (where tests run)                                    │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │  run_molecule.sh                                                │    │
│  │    └── molecule verify -s <scenario>                            │    │
│  │          └── pytest (testinfra)                                 │    │
│  │                └── automation_library/core/host.py              │    │
│  └─────────────────────────────────────────────────────────────────┘    │
└────────────────────────────────┬────────────────────────────────────────┘
                                 │ SSH (oim_server_ip)
                                 ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  OIM SERVER                                                             │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │  podman exec omnia_core <command>                               │    │
│  │    └── Ansible playbooks                                        │    │
│  │    └── Pulp CLI, ochami CLI                                     │    │
│  │    └── kubectl, ssh to nodes                                    │    │
│  └─────────────────────────────────────────────────────────────────┘    │
└────────────────────────────────┬────────────────────────────────────────┘
                                 │ SSH (admin_ip from PXE mapping)
                                 ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  COMPUTE/K8S NODES                                                      │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐          │
│  │ k8s_control_plane│  │ k8s_worker_node │  │ slurm_node      │          │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘          │
└─────────────────────────────────────────────────────────────────────────┘
```

### Command Execution Layers

```python
# Layer 1: Run on OIM server directly
run_on_oim(host, "systemctl status podman")

# Layer 2: Run inside omnia_core container
run_in_container(host, "pulp rpm repository list")

# Layer 3: Run on remote node via SSH through container
run_on_remote_node(host, "kubectl get nodes", admin_ip="10.0.0.5")
```

---

## 3. Execution Flow

### High-Level Workflow

```
┌─────────────────────────────────────────────────────────────────────────┐
│  STEP 1: CONFIGURE                                                      │
│  ─────────────────                                                      │
│  Edit omnia_test_config.yml:                                            │
│    - OIM server IP and SSH credentials                                  │
│    - Dataset selection (project_default)                                │
│    - Hardware thresholds, network settings                              │
└─────────────────────────────────────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  STEP 2: PREREQUISITE CHECK (optional)                                  │
│  ─────────────────────────────────────                                  │
│  Run: oim-prereq-check                                                  │
│    - Validates hardware (CPU, memory, disk)                             │
│    - Validates OS and kernel version                                    │
│    - Validates network interfaces                                       │
│    - Validates NFS server connectivity                                  │
│    - Validates Podman installation                                      │
└─────────────────────────────────────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  STEP 3: RUN TESTS                                                      │
│  ─────────────────                                                      │
│  Run: run_molecule <scenario> verify --suite sanity                     │
│    - Molecule loads scenario configuration                              │
│    - Syncs dataset folder to container                                  │
│    - Executes Ansible playbook (converge)                               │
│    - Runs pytest verification tests                                     │
└─────────────────────────────────────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  STEP 4: VIEW REPORTS                                                   │
│  ────────────────────                                                   │
│  Open: reports/test_report.html in browser                              │
│    - Interactive HTML with dark theme                                   │
│    - Collapsible test sections                                          │
│    - Playbook logs embedded                                             │
│    - Per-test pass/fail/skip status                                     │
└─────────────────────────────────────────────────────────────────────────┘
```

### Molecule Lifecycle

Each scenario follows the Molecule lifecycle:

```
create.yml              converge.yml                    verify (pytest)
──────────              ────────────                    ───────────────
1. Load config          1. Check omnia_core running     1. SSH to OIM server
2. Build inventory      2. Sync dataset folder          2. Run test functions
3. Wait for SSH         3. Execute ansible playbook     3. Collect results
                        4. Report playbook status       4. Generate reports
```

---

## 4. Core Library

The `automation_library/core/` module provides shared infrastructure for all test modules.

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

### Key Functions

```python
from automation_library.core import (
    # Connection
    get_testinfra_host,       # Get SSH connection to OIM
    run_on_oim,               # Run command on OIM server
    run_in_container,         # Run command in omnia_core
    run_on_remote_node,       # Run command on K8s node
    
    # PXE Mapping
    get_node_info,            # Get single node by search criteria
    get_nodes_info,           # Get multiple nodes by functional group
    
    # Config Loading
    load_input_file,          # Load YAML/JSON from container
    get_input_value,          # Get specific config value
    is_software_enabled,      # Check software_config.json
    
    # Output
    TestLogger,               # Structured test logging
    Colors, Symbols,          # Terminal formatting
    
    # Credentials
    view_credentials_file,    # Decrypt ansible-vault files
    get_credential_value,     # Get specific credential
)
```

### TestLogger Usage

```python
log = TestLogger("Verify container running")
log.check("Checking omnia_core container status")

if result["success"]:
    log.passed("Container is running", result["details"])
else:
    log.failed("Container not running", result["error"])

# For skipped tests
log.skipped("Feature not enabled", "Enable in config")
pytest.skip("Feature not enabled")
```

---

## 5. Module Structure

### Directory Layout

Each test module follows this structure:

```
automation_library/<module>/
├── __init__.py              # Module exports
├── functions/
│   ├── __init__.py          # Function exports
│   └── <module>_func.py     # Verification functions
├── vars/
│   ├── __init__.py          # Variable exports
│   └── <module>_vars.py     # Constants, expected values
└── messages/
    ├── __init__.py          # Message exports
    └── <module>_msgs.py     # TEST_NAMES, LOG_MSGS, ASSERT_MSGS
```

### Molecule Scenario Layout

```
molecule/<scenario>/
├── molecule.yml             # Scenario configuration
├── create.yml               # Inventory setup playbook
├── converge.yml             # Main Ansible playbook execution
└── tests/
    └── sanity/              # Test suite folder
        ├── __init__.py
        └── test_<module>.py # Pytest test file
```

### Verification Function Pattern

All verification functions return a standardized dictionary:

```python
def verify_something(host, param: str) -> Dict[str, Any]:
    """Verify something."""
    cmd = run_in_container(host, f"check {param}")
    
    if cmd.rc == 0:
        return {
            "success": True,
            "details": cmd.stdout.strip(),
            "error": "",
        }
    
    return {
        "success": False,
        "details": "",
        "error": cmd.stderr.strip(),
    }
```

---

## 6. Configuration Reference

### omnia_test_config.yml

```yaml
# ═══════════════════════════════════════════════════════════════════════════
# OIM SERVER CONNECTION (REQUIRED)
# ═══════════════════════════════════════════════════════════════════════════
oim_server_ip: "192.168.1.100"      # Target OIM server IP address
oim_ssh_user: "root"                # SSH username
oim_ssh_password: "your_password"   # SSH password
oim_ssh_port: 22                    # SSH port
oim_hostname: "oim.example.com"     # FQDN for OIM server

# ═══════════════════════════════════════════════════════════════════════════
# DATASET SELECTION
# ═══════════════════════════════════════════════════════════════════════════
dataset: "project_default"          # Folder name under datasets/

# ═══════════════════════════════════════════════════════════════════════════
# EXECUTION CONTROL
# ═══════════════════════════════════════════════════════════════════════════
skip_on_failure: false              # Stop on first failure

# ═══════════════════════════════════════════════════════════════════════════
# PREREQUISITE CHECK SETTINGS
# ═══════════════════════════════════════════════════════════════════════════
min_cores: 4                        # Minimum CPU cores
min_memory_gb: 8                    # Minimum RAM in GB
min_disk_gb: 50                     # Minimum disk space in GB
required_os: "rhel"                 # Required OS name
required_os_version: "10"           # Required OS version
required_kernel_version: "6.12.0"   # Required kernel version

# ═══════════════════════════════════════════════════════════════════════════
# NETWORK SETTINGS
# ═══════════════════════════════════════════════════════════════════════════
network_type: "dedicated"           # "dedicated" or "lom"
pxe_interface: "eno1"               # PXE network interface
public_interface: "eno2"            # Public network interface
pxe_ip: "172.16.107.254/24"         # PXE interface IP with CIDR
force_configure_pxe: false          # Force PXE IP configuration

# ═══════════════════════════════════════════════════════════════════════════
# NFS SETTINGS
# ═══════════════════════════════════════════════════════════════════════════
nfs_server_ip: "192.168.1.200"      # NFS server IP
nfs_share_path: "/mnt/share"        # NFS share path
nfs_min_capacity_gb: 100            # Minimum NFS capacity

# ═══════════════════════════════════════════════════════════════════════════
# PODMAN SETTINGS
# ═══════════════════════════════════════════════════════════════════════════
podman_min_version: "5.0.0"         # Minimum Podman version

# ═══════════════════════════════════════════════════════════════════════════
# CONTAINER IMAGE BUILD (optional)
# ═══════════════════════════════════════════════════════════════════════════
reconfigure_images: false           # Build container images
omnia_repo_url: "https://github.com/dell/omnia-artifactory.git"
artifactory_branch: "omnia-container"
omnia_clone_path: "/opt/omnia-artifactory"
omnia_branch: "pub/k8s_telemetry"

# ═══════════════════════════════════════════════════════════════════════════
# OMNIA.SH INSTALLATION
# ═══════════════════════════════════════════════════════════════════════════
share_option: "NFS"                 # "NFS" or "Local"
nfs_type: "external"                # "external" or "internal"
omnia_shared_path: "/opt/omnia"     # Omnia shared path
omnia_core_password: "password"     # Container password

# ═══════════════════════════════════════════════════════════════════════════
# LDAP CREDENTIALS (optional)
# ═══════════════════════════════════════════════════════════════════════════
ldap_credentials:
  - username: "testuser1"
    password: "testpass"

# ═══════════════════════════════════════════════════════════════════════════
# BUILD STREAM JOB OVERRIDE (optional)
# ═══════════════════════════════════════════════════════════════════════════
build_stream_job_id: ""             # Override job ID for testing
```

---

## 7. Development Guide

### Adding a New Test Function

1. Open `molecule/<scenario>/tests/sanity/test_<module>.py`
2. Add test with proper docstring:

```python
@pytest.mark.sanity
@pytest.mark.order(10)
def test_new_feature(host):
    """
    Test Case 10: Verify new feature works.

    Checks:
    - Feature is enabled in config
    - Feature returns expected output
    """
    log = TestLogger("Verify new feature")
    log.check("Checking new feature")
    
    result = verify_new_feature(host)
    
    if result["success"]:
        log.passed("Feature verified", result["details"])
    else:
        log.failed("Feature failed", result["error"])
    
    assert result["success"], result["error"]
```

### Adding a New Module

```bash
# 1. Create module structure
mkdir -p automation_library/new_module/{functions,vars,messages}
touch automation_library/new_module/{__init__.py,functions/__init__.py}
touch automation_library/new_module/{vars/__init__.py,messages/__init__.py}

# 2. Create molecule scenario
mkdir -p molecule/new_module/tests/sanity
touch molecule/new_module/{molecule.yml,create.yml,converge.yml}
touch molecule/new_module/tests/sanity/{__init__.py,test_new_module.py}

# 3. Add to run_molecule.sh ORDERED_SCENARIOS array
```

### Running Ansible-lint

```bash
# Lint all playbooks
ansible-lint molecule/*/converge.yml

# Lint specific playbook
ansible-lint molecule/prepare_oim/converge.yml
```

---

## 8. Troubleshooting

### Common Issues

| Issue | Solution |
|-------|----------|
| SSH connection failed | Verify `oim_server_ip` and `oim_ssh_password` in config |
| Module not found | Run `source .venv/bin/activate` first |
| Container not running | Check `podman ps` on OIM server |
| Tests skipped | Verify feature is enabled in dataset config files |
| Permission denied | Ensure SSH user has root/sudo access |

### Debug Commands

```bash
# Verbose test output
run_molecule prepare_oim verify --suite sanity 2>&1 | tee debug.log

# Run single test
pytest molecule/prepare_oim/tests/sanity/test_prepare_oim.py::test_service_status -v

# Check OIM server connectivity
ssh root@<oim_server_ip> "podman ps"

# Check container logs
ssh root@<oim_server_ip> "podman logs omnia_core"
```

### Report Locations

| Report | Path | How to View |
|--------|------|-------------|
| HTML | `reports/test_report.html` | Open in browser |
| JSON | `reports/test_report.json` | Parse with jq or Python |

---

*Last Updated: April 2026*
