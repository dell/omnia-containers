# Omnia Automation Framework - Implementation Guide

This document provides a comprehensive understanding of the Omnia Automation Framework architecture, code structure, and how all components work together.

---

## Table of Contents

1. [Overview](#1-overview)
2. [Repository Structure](#2-repository-structure)
3. [Core Module (`automation_library/core/`)](#3-core-module)
4. [Test Modules](#4-test-modules)
5. [Molecule Test Framework](#5-molecule-test-framework)
6. [Test Execution Flow](#6-test-execution-flow)
7. [Configuration Files](#7-configuration-files)
8. [Test Suites and Markers](#8-test-suites-and-markers)
9. [Adding New Tests](#9-adding-new-tests)
10. [Troubleshooting](#10-troubleshooting)

---

## 1. Overview

The Omnia Automation Framework is a Python-based testing framework built on top of:

- **Molecule** - Test orchestration for Ansible
- **Pytest** - Python testing framework
- **Testinfra** - Infrastructure testing with Python

### Purpose

The framework automates verification of Omnia Infrastructure Manager (OIM) deployments by:

1. Connecting to the OIM server via SSH
2. Running verification tests against services, containers, and configurations
3. Generating detailed HTML/JSON reports

### Key Concepts

| Concept | Description |
|---------|-------------|
| **OIM Server** | The target server where Omnia is deployed |
| **omnia_core container** | Main container on OIM that runs Omnia services |
| **Molecule Scenario** | A test module (e.g., `prepare_oim`, `telemetry`) |
| **Test Suite** | Category of tests (sanity, negative, regression, smoke) |

---

## 2. Repository Structure

```
omnia-artifactory/
├── omnia_test_config.yml          # Main configuration (OIM server IP, credentials)
├── run_molecule.sh                # Test runner script
├── setup_env.sh                   # Environment setup script
├── requirements.txt               # Python dependencies
├── pytest.ini                     # Pytest configuration
│
├── automation_library/            # Python test library
│   ├── core/                      # Shared utilities (MOST IMPORTANT)
│   ├── prepare_oim/               # prepare_oim module functions
│   ├── telemetry/                 # telemetry module functions
│   ├── discovery/                 # discovery module functions
│   ├── build_image/               # build_image module functions
│   ├── local_repo/                # local_repo module functions
│   ├── oim_cleanup/               # oim_cleanup module functions
│   ├── omnia_sh/                  # omnia.sh install/uninstall functions
│   ├── kubernetes/                # kubernetes module functions
│   └── checks/                    # Prerequisite check functions
│
├── molecule/                      # Molecule test scenarios
│   ├── conftest.py                # Shared pytest fixtures
│   ├── shared/                    # Shared Ansible tasks
│   ├── prepare_oim/               # prepare_oim scenario
│   ├── telemetry/                 # telemetry scenario
│   ├── discovery/                 # discovery scenario
│   ├── build_image_x86_64/        # build_image x86_64 scenario
│   ├── build_image_aarch64/       # build_image aarch64 scenario
│   ├── local_repo/                # local_repo scenario
│   ├── oim_cleanup/               # oim_cleanup scenario
│   ├── omnia_sh_install/          # omnia.sh install scenario
│   ├── omnia_sh_uninstall/        # omnia.sh uninstall scenario
│   └── kubernetes/                # kubernetes scenario
│
├── datasets/                      # Input configuration datasets
│   └── project_default/           # Default dataset
│       ├── software_config.json
│       ├── telemetry_config.yml
│       ├── provision_config.yml
│       ├── pxe_mapping_file.csv
│       └── ...
│
├── docs/                          # Documentation
│   ├── IMPLEMENTATION.md          # This file
│   └── BUILD_STREAM_WORKFLOW.md   # Build stream documentation
│
└── reports/                       # Generated test reports (gitignored)
    ├── test_report.html
    └── test_report.json
```

---

## 3. Core Module (`automation_library/core/`)

The `core` module is the foundation of the framework. **All other modules should import utilities from core.**

### 3.1 Module Structure

```
automation_library/core/
├── __init__.py          # Exports all public functions
├── host.py              # SSH connection and command execution
├── formatting.py        # Colors, symbols, TestLogger
├── load_inputs.py       # Load config files from container
├── secrets.py           # Credential management
├── report.py            # Test report generation
├── build_stream.py      # Build stream utilities
├── db_exec.py           # Database query execution
└── vars.py              # Shared constants and paths
```

### 3.2 Key Functions

#### Connection Functions (`host.py`)

```python
from automation_library.core import (
    get_testinfra_host,      # Get testinfra host connected to OIM
    load_user_config,        # Load omnia_test_config.yml
    run_on_oim,              # Run command on OIM server
    run_in_container,        # Run command inside omnia_core container
    run_on_remote_node,      # Run command on remote K8s node via SSH
    get_node_info,           # Get single node info from PXE mapping
    get_nodes_info,          # Get multiple nodes info from PXE mapping
    check_container_running, # Check if a container is running
    get_project_root,        # Get project root directory path
    make_verification_result,# Create standardized result dictionary
)
```

#### Input Loading Functions (`load_inputs.py`)

```python
from automation_library.core import (
    load_input_file,         # Load YAML/JSON from container
    load_container_file,     # Load raw file content from container
    get_input_value,         # Get specific value from config
    get_input_bool,          # Get boolean value from config
    is_software_enabled,     # Check if software component is enabled
)
```

#### Formatting Functions (`formatting.py`)

```python
from automation_library.core import (
    Colors,                  # ANSI color codes
    Symbols,                 # Unicode symbols (✓, ✗, →)
    TestLogger,              # Structured test logging
    log,                     # Simple logging function
)
```

#### Shared Variables (`vars.py`)

```python
from automation_library.core import (
    # Container paths
    INPUT_BASE_PATH,         # /opt/omnia/input/project_default
    OIM_SHARED_PATH,         # /opt/omnia
    OMNIA_CORE_CONTAINER,    # "omnia_core"
    
    # Config file paths (inside container)
    SOFTWARE_CONFIG_PATH,
    TELEMETRY_CONFIG_PATH,
    PROVISION_CONFIG_PATH,
    PXE_MAPPING_FILE_PATH,
    
    # Functional group names
    K8S_CONTROL_PLANE_FUNCTIONAL_GROUP,
    K8S_WORKER_NODE_FUNCTIONAL_GROUP,
)
```

### 3.3 How Commands Are Executed

```
┌─────────────────┐     SSH      ┌─────────────────┐
│  Test Machine   │ ──────────▶  │   OIM Server    │
│  (run_molecule) │              │                 │
└─────────────────┘              └────────┬────────┘
                                          │
                                   podman exec
                                          │
                                          ▼
                                 ┌─────────────────┐
                                 │  omnia_core     │
                                 │  container      │
                                 └────────┬────────┘
                                          │
                                    SSH to K8s
                                          │
                                          ▼
                                 ┌─────────────────┐
                                 │  K8s Nodes      │
                                 │  (admin_ip)     │
                                 └─────────────────┘
```

**Command execution chain:**

1. `run_on_oim(host, cmd)` - Runs command directly on OIM server
2. `run_in_container(host, cmd)` - Runs command inside omnia_core container
3. `run_on_remote_node(host, cmd, admin_ip)` - Runs command on K8s node via SSH through container

---

## 4. Test Modules

Each test module follows a consistent structure:

```
automation_library/<module_name>/
├── __init__.py              # Module exports
├── functions/
│   ├── __init__.py          # Function exports
│   └── <module>_func.py     # Core verification functions
├── vars/
│   ├── __init__.py          # Variable exports
│   └── <module>_vars.py     # Constants and configuration
└── messages/
    ├── __init__.py          # Message exports
    └── <module>_msgs.py     # Test names, log messages, assert messages
```

### 4.1 Module Pattern

Every verification function returns a standardized dictionary:

```python
def verify_something(host, admin_ip: str) -> Dict[str, Any]:
    """Verify something important."""
    # ... verification logic ...
    
    return {
        "success": True/False,
        "details": "Human-readable details",
        "error": "" or "Error message",
        # Additional keys as needed
    }
```

### 4.2 Available Modules

| Module | Purpose |
|--------|---------|
| `prepare_oim` | Verify OIM services, containers, certificates |
| `telemetry` | Verify telemetry stack (Kafka, Victoria, iDRAC) |
| `discovery` | Verify node discovery (SSH, packages, cloud-init) |
| `build_image` | Verify image builds for x86_64 and aarch64 |
| `local_repo` | Verify local repository setup |
| `oim_cleanup` | Verify OIM cleanup operations |
| `omnia_sh` | Verify omnia.sh install/uninstall |
| `kubernetes` | Verify Kubernetes cluster health |

---

## 5. Molecule Test Framework

### 5.1 Scenario Structure

Each molecule scenario has:

```
molecule/<scenario>/
├── molecule.yml             # Scenario configuration
├── create.yml               # Inventory creation playbook
├── converge.yml             # Main playbook (optional)
├── prepare.yml              # Pre-test setup (optional)
└── tests/
    └── sanity/              # Test suite folder
        ├── __init__.py
        └── test_<module>.py # Pytest test file
```

### 5.2 molecule.yml Configuration

```yaml
dependency:
  name: galaxy
driver:
  name: default
platforms:
  - name: localhost
provisioner:
  name: ansible
verifier:
  name: testinfra
  directory: tests
  options:
    v: true
```

### 5.3 Shared Fixtures (`molecule/conftest.py`)

The `conftest.py` provides shared pytest fixtures:

```python
@pytest.fixture(scope="module")
def host():
    """Testinfra host fixture - connects to OIM server."""
    # Validates configuration
    # Checks SSH connectivity
    # Returns testinfra host object
    return get_testinfra_host()
```

**Registered Markers:**

- `@pytest.mark.sanity` - Basic functionality tests
- `@pytest.mark.negative` - Error handling tests
- `@pytest.mark.regression` - Full coverage tests
- `@pytest.mark.smoke` - Critical path tests
- `@pytest.mark.cleanup` - Cleanup verification tests

---

## 6. Test Execution Flow

### 6.1 Complete Flow

```
1. User runs: run_molecule prepare_oim verify --suite sanity

2. run_molecule.sh:
   ├── Activates .venv
   ├── Sets PYTEST_ADDOPTS="-m sanity"
   └── Calls: molecule verify -s prepare_oim

3. Molecule:
   ├── Reads molecule/prepare_oim/molecule.yml
   ├── Runs verifier (testinfra)
   └── Executes pytest on tests/sanity/

4. Pytest:
   ├── Loads conftest.py fixtures
   ├── Creates testinfra host connection
   └── Runs test functions

5. Test Functions:
   ├── Import from automation_library
   ├── Call verification functions
   ├── Use TestLogger for output
   └── Assert results

6. Report Generation:
   ├── TestReport collects results
   └── Saves to reports/test_report.html
```

### 6.2 Test Function Pattern

```python
@pytest.mark.sanity
@pytest.mark.order(1)
def test_service_status(host):
    """Verify all service/target status."""
    log = TestLogger("Verify all service/target status")
    log.check("Checking all systemd services and targets")
    
    result = verify_all_services(host)
    
    if result["success"]:
        log.passed("All services in expected state", result["details"])
    else:
        log.failed("Some services not in expected state", result["error"])
    
    assert result["success"], result["error"]
```

---

## 7. Configuration Files

### 7.1 omnia_test_config.yml (Main Config)

```yaml
# OIM Server Connection
oim_server_ip: "192.168.1.100"
oim_ssh_user: "root"
oim_ssh_password: "your_password"
oim_ssh_port: 22

# Execution Control
skip_on_failure: false

# Dataset Selection
dataset: "project_default"
```

### 7.2 Dataset Files (datasets/project_default/)

| File | Purpose |
|------|---------|
| `software_config.json` | Software component enablement |
| `telemetry_config.yml` | Telemetry configuration |
| `provision_config.yml` | Provisioning settings, PXE mapping path |
| `pxe_mapping_file.csv` | Node inventory (IP, hostname, functional group) |
| `omnia_config.yml` | Omnia configuration |
| `ha_config.yml` | High availability settings |

---

## 8. Test Suites and Markers

### 8.1 Test Organization

Tests are organized in suite folders:

```
molecule/<scenario>/tests/
├── sanity/                  # Basic functionality tests
│   ├── __init__.py
│   └── test_<module>.py
├── negative/                # Error handling tests (future)
│   └── ...
└── regression/              # Full coverage tests (future)
    └── ...
```

### 8.2 Running Specific Suites

```bash
# Run sanity tests only
run_molecule prepare_oim verify --suite sanity

# Run negative tests only
run_molecule telemetry verify --suite negative

# Run multiple suites
run_molecule discovery verify --suite sanity,negative

# Run with custom marker
run_molecule telemetry verify --marker smoke
```

### 8.3 Marker Decorators

```python
@pytest.mark.sanity      # Basic functionality
@pytest.mark.negative    # Error handling
@pytest.mark.regression  # Full coverage
@pytest.mark.smoke       # Critical path only
@pytest.mark.cleanup     # Cleanup verification
@pytest.mark.order(n)    # Execution order
```

---

## 9. Adding New Tests

### 9.1 Add a New Test Function

1. Open `molecule/<scenario>/tests/sanity/test_<module>.py`
2. Add test function with markers:

```python
@pytest.mark.sanity
@pytest.mark.order(10)
def test_new_feature(host):
    """Verify new feature works correctly."""
    from automation_library.core import TestLogger
    from automation_library.<module>.functions import verify_new_feature
    
    log = TestLogger("Verify new feature")
    log.check("Checking new feature")
    
    result = verify_new_feature(host)
    
    if result["success"]:
        log.passed("New feature verified", result["details"])
    else:
        log.failed("New feature failed", result["error"])
    
    assert result["success"], result["error"]
```

### 9.2 Add a New Verification Function

1. Open `automation_library/<module>/functions/<module>_func.py`
2. Add function following the pattern:

```python
def verify_new_feature(host) -> Dict[str, Any]:
    """
    Verify new feature.
    
    Args:
        host: Testinfra host object
        
    Returns:
        Dict with success, details, error keys
    """
    from automation_library.core import run_in_container
    
    cmd = run_in_container(host, "check_something")
    
    if cmd.rc == 0:
        return {
            "success": True,
            "details": cmd.stdout.strip(),
            "error": "",
        }
    
    return {
        "success": False,
        "details": None,
        "error": cmd.stderr.strip(),
    }
```

### 9.3 Add a New Module

1. Create directory structure:
```bash
mkdir -p automation_library/new_module/{functions,vars,messages}
touch automation_library/new_module/{__init__.py,functions/__init__.py,vars/__init__.py,messages/__init__.py}
```

2. Create molecule scenario:
```bash
mkdir -p molecule/new_module/tests/sanity
touch molecule/new_module/{molecule.yml,create.yml}
touch molecule/new_module/tests/sanity/{__init__.py,test_new_module.py}
```

3. Add to `run_molecule.sh` ORDERED_SCENARIOS

---

## 10. Troubleshooting

### 10.1 Common Issues

| Issue | Solution |
|-------|----------|
| SSH connection failed | Check `oim_server_ip` and `oim_ssh_password` in `omnia_test_config.yml` |
| Module not found | Run `source .venv/bin/activate` first |
| Container not running | Verify OIM deployment with `podman ps` on OIM server |
| Tests skipped | Check if feature is enabled in config files |

### 10.2 Debug Mode

```bash
# Run with verbose output
run_molecule prepare_oim verify --suite sanity 2>&1 | tee debug.log

# Check specific test
pytest molecule/prepare_oim/tests/sanity/test_prepare_oim.py::test_service_status -v
```

### 10.3 Report Location

After test execution, reports are saved to:
- **HTML**: `reports/test_report.html`
- **JSON**: `reports/test_report.json`

---

## Quick Reference

### Commands

```bash
# Setup environment
./setup_env.sh

# Activate virtual environment
source .venv/bin/activate

# List available scenarios
run_molecule list

# Run tests
run_molecule <scenario> verify --suite sanity

# Run all scenarios
run_molecule all verify
```

### Key Imports

```python
# Core utilities
from automation_library.core import (
    get_testinfra_host,
    run_in_container,
    run_on_remote_node,
    TestLogger,
    load_input_file,
    get_node_info,
)

# Module-specific
from automation_library.<module>.functions import <function>
from automation_library.<module>.vars import <VARIABLE>
from automation_library.<module>.messages import TEST_NAMES, TEST_LOG_MSGS
```

---

*Last Updated: April 2026*
