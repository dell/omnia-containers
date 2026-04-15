# Omnia Automation Framework - Development Rules

## Overview

This document defines comprehensive development rules for the Omnia Automation Framework. These rules ensure consistency, modularity, reusability, and maintainability across all modules. **All developers must follow these rules strictly.**

---

## 1. Repository Structure

```
omnia-artifactory/
├── automation_config.yml          # Main configuration (OIM server IP, credentials)
├── run_molecule.sh                # Test runner script
├── setup_env.sh                   # Environment setup script
├── requirements.txt               # Python dependencies
├── pytest.ini                     # Pytest configuration
│
├── automation_library/            # Python test library
│   ├── core/                      # Shared utilities (MOST IMPORTANT)
│   ├── prepare_oim/               # prepare_oim module
│   ├── telemetry/                 # telemetry module
│   ├── discovery/                 # discovery module
│   ├── build_image/               # build_image module
│   ├── local_repo/                # local_repo module
│   ├── oim_cleanup/               # oim_cleanup module
│   ├── omnia_sh/                  # omnia.sh module
│   ├── kubernetes/                # kubernetes module
│   └── checks/                    # Prerequisite checks
│
├── molecule/                      # Molecule test scenarios
│   ├── conftest.py                # Shared pytest fixtures
│   ├── shared/                    # Shared Ansible tasks
│   └── <scenario>/                # Individual scenarios
│       ├── molecule.yml
│       ├── create.yml
│       ├── converge.yml
│       └── tests/
│           └── sanity/            # Test suite folder
│               ├── __init__.py
│               └── test_*.py
│
├── datasets/                      # Input configuration datasets
│   └── project_default/           # Default dataset
│
├── docs/                          # Documentation
│   ├── IMPLEMENTATION.md          # Implementation guide
│   └── BUILD_STREAM_WORKFLOW.md   # Build stream docs
│
└── reports/                       # Generated test reports (gitignored)
```

---

## 2. Module Architecture Rules

### 2.1 Module Structure (MANDATORY)

Every new module MUST follow this exact directory structure:

```
automation_library/<module_name>/
├── __init__.py           # Module exports and documentation
├── functions/
│   ├── __init__.py       # Function exports
│   └── <module>_func.py  # Core functions
├── vars/
│   ├── __init__.py       # Variable exports
│   └── <module>_vars.py  # Constants and configuration
└── messages/
    ├── __init__.py       # Message exports
    └── <module>_msgs.py  # User-facing messages
```

### 2.2 Test Structure (MANDATORY)

Tests are organized in suite folders:

```
molecule/<scenario>/tests/
├── sanity/                  # Basic functionality tests
│   ├── __init__.py
│   └── test_<module>.py
├── negative/                # Error handling tests (future)
└── regression/              # Full coverage tests (future)
```

---

## 3. Core Module Usage

### 3.1 Always Import from Core

```python
from automation_library.core import (
    get_testinfra_host,
    run_in_container,
    run_on_remote_node,
    get_node_info,
    get_nodes_info,
    check_container_running,
    make_verification_result,
    get_project_root,
    load_input_file,
    get_input_value,
    is_build_stream_enabled,
    TestLogger,
)
```

### 3.2 Never Duplicate Core Functions

- Do NOT create local `_get_project_root()` functions
- Do NOT create local `check_container_running()` functions
- Do NOT read config files from local filesystem - use `load_input_file()` to read from container

---

## 4. Function Design Patterns

### 4.1 Return Dictionary Pattern (MANDATORY)

All verification functions MUST return a dictionary with consistent structure:

```python
def verify_something(host, admin_ip: str) -> Dict[str, Any]:
    """Verify something important."""
    # ... implementation
    
    return {
        "success": True/False,
        "details": "...",           # Optional: human-readable details
        "error": "" or "error msg", # Empty string if success
    }
```

### 4.2 Use make_verification_result Helper

```python
from automation_library.core import make_verification_result

return make_verification_result(
    results=results,
    passed=passed,
    failed=failed,
    total=total,
    details=details
)
```

---

## 5. Test Markers (MANDATORY)

All tests MUST have appropriate markers:

```python
@pytest.mark.sanity      # Basic functionality tests
@pytest.mark.negative    # Error handling tests
@pytest.mark.regression  # Full coverage tests
@pytest.mark.smoke       # Critical path tests
@pytest.mark.cleanup     # Cleanup verification tests
@pytest.mark.order(n)    # Execution order
```

---

## 6. Configuration Files

### 6.1 Main Configuration

- File: `automation_config.yml` (NOT `user_config.yml`)
- Contains: OIM server IP, SSH credentials, execution settings
- **NEVER commit this file** (it's in .gitignore)

### 6.2 Dataset Configuration

- Location: `datasets/project_default/`
- Contains: software_config.json, telemetry_config.yml, provision_config.yml, etc.
- Read using: `load_input_file(host, filename)` from core

---

## 7. Command Execution

### 7.1 Running Tests

```bash
# After setup
source .venv/bin/activate

# Run tests (no ./ needed after activation)
run_molecule list
run_molecule <scenario> verify --suite sanity
run_molecule <scenario> verify --suite negative
run_molecule all test
```

### 7.2 Test Suites

- `--suite sanity` - Basic functionality tests
- `--suite negative` - Error handling tests
- `--suite regression` - Full coverage tests
- `--marker smoke` - Critical path tests

---

## 8. Code Quality

### 8.1 Linting

- Run `pylint automation_library/` before committing
- Run `ansible-lint molecule/` for Ansible files
- Fix all unused imports
- Target score: 9.0+/10

### 8.2 Copyright

All files must have copyright header:
```python
# Copyright 2026 Dell Inc. or its subsidiaries. All Rights Reserved.
```

---

## 9. Documentation

### 9.1 Required Docs

- `docs/IMPLEMENTATION.md` - Full implementation guide
- `docs/BUILD_STREAM_WORKFLOW.md` - Build stream documentation
- `README.md` - User-facing documentation

### 9.2 No Unnecessary Docs

- Do NOT create CODE_ANALYSIS.md or similar analysis files
- Do NOT create multiple implementation plan files
- Keep docs/ folder clean with only essential documentation

---

## 10. Git Rules

### 10.1 Files to Never Commit

- `automation_config.yml` (contains credentials)
- `reports/` folder
- `.venv/` folder
- `__pycache__/` folders

### 10.2 Commit Messages

Use clear, descriptive commit messages:
- `feat: Add sanity test suite structure`
- `fix: Remove unused imports`
- `docs: Update README with run_molecule usage`

---

*Last Updated: April 2026*
