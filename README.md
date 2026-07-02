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
- [Execution](#execution)
- [Scenarios](#scenarios)
- [Project Structure](#project-structure)
- [Detailed References](#detailed-references)
- [License](#license)

---

## Overview

This framework automates testing of Omnia Infrastructure Manager (OIM) deployments. It provides:

- **Prerequisite validation** of the OIM server (hardware, OS, network, NFS, Podman)
- **Molecule-based test scenarios** that execute Ansible playbooks inside the `omnia_core` container and verify results with pytest-testinfra
- **Interactive HTML and JSON reports** for every test run

### How It Works

1. **`omnia_test_config.yml`** drives all automation — it defines the OIM server connection, hardware thresholds, deployment options, and dataset selection.
2. **`omnia_test_credentials.yml`** stores sensitive credentials (passwords) separately — automatically encrypted with Ansible Vault on first run.
3. **`setup_env.sh`** creates a Python virtual environment, installs dependencies, and registers the `oim-prereq-check` CLI and `run_molecule` shell function.
4. **Molecule scenarios** follow a `create → converge → verify` lifecycle:
   - **create.yml** — Builds dynamic Ansible inventory from `omnia_test_config.yml` and verifies SSH connectivity.
   - **converge.yml** — Optionally syncs dataset files into the `omnia_core` container at `/opt/omnia/input/project_default/`, then executes the target playbook via `podman exec`.
   - **verify** — Runs pytest-testinfra tests that use `automation_library` functions to validate deployment state.
5. **`automation_library/core/`** provides shared utilities for host connections, config loading, container command execution, PXE mapping parsing, credential decryption, and report generation.

### Local Mode vs Remote Mode

| Mode | When | How |
|------|------|-----|
| **Local mode** | `oim_server_ip` is empty, `""`, `localhost`, or `127.0.0.1` | All commands run directly on the local machine — no SSH required. Assumes the automation is running on the OIM server itself. |
| **Remote mode** | `oim_server_ip` is set to a remote IP address | All commands are executed over SSH using the provided `oim_ssh_user` and `oim_ssh_password`. |

> **Important:** If `oim_server_ip` is not set, every scenario (including `omnia_sh_install`) runs in local mode on the current host.

---

## Quick Start

```bash
# 1. Clone the repository with release-specific branch
git clone -b automation-<release> https://github.com/dell/omnia-artifactory.git
cd omnia-artifactory

# 2. Run the environment setup script
./setup_env.sh

# 3. Activate the virtual environment
source .venv/bin/activate

# 4. Configure your OIM server
vi omnia_test_config.yml

# 5. Configure credentials (passwords)
vi omnia_test_credentials.yml

# 7. (Optional) Fill dataset files — required only for converge/test runs
vi datasets/project_default/network_spec.yml
vi datasets/project_default/software_config.json
vi datasets/project_default/telemetry_config.yml

# 8. Run prerequisite checks
oim-prereq-check

# 9. Run molecule tests
run_molecule telemetry verify --suite sanity   # Single scenario
run_molecule all test                          # Full lifecycle
run_molecule --config                          # Batch from config file
```

> **Note:** For `verify`-only runs (validating an already-deployed environment), filling the dataset files is not required. Datasets are only synced during `converge` and `test` commands when `sync_dataset_to_core: true` is set.

---

## Configuration

### omnia\_test\_config.yml

This is the central configuration file for non-sensitive settings. Every automation script reads from it. Edit this file before running any tests.

> **Full parameter reference:** [docs/input_reference.md](docs/input_reference.md)

Key parameters:

| Parameter | Description |
|-----------|-------------|
| `oim_server_ip` | OIM server IP. Leave empty for local mode. |
| `oim_ssh_user` | SSH username for remote mode. |
| `dataset` | Dataset folder name under `datasets/` (default: `project_default`). |
| `sync_dataset_to_core` | When `true`, syncs dataset files into the container during converge. |
| `share_option` | Storage backend for omnia.sh: `NFS` or `Local`. |

### omnia\_test\_credentials.yml

This file stores all sensitive credentials (passwords). It is **automatically encrypted** with Ansible Vault on first Molecule run.

| Parameter | Description |
|-----------|-------------|
| `oim_ssh_password` | SSH password for remote OIM server (remote mode only). |
| `omnia_core_password` | Root password for `omnia_core` container SSH (port 2222). |
| `ldap_credentials` | LDAP user credentials for cluster login tests (format: `user:pass` or `user1:pass1,user2:pass2`). |
| `external_ldap_bind_username` | External LDAP bind username for slapd.conf configuration. |
| `external_ldap_bind_password` | External LDAP bind password for slapd.conf configuration. |

> **Security:** The credentials file is automatically encrypted using Ansible Vault. The vault key is stored in `.omnia_test_credentials.key` (gitignored). On each Molecule run, the file is decrypted, used, and re-encrypted.

### Datasets

The `datasets/project_default/` folder contains Omnia deployment input files that mirror `/opt/omnia/input/project_default/` inside the `omnia_core` container.

> **Full dataset reference:** [docs/dataset_reference.md](docs/dataset_reference.md)

Key files:

| File | Purpose |
|------|---------|
| `software_config.json` | Central control — defines OS type, version, and software stack to deploy |
| `network_spec.yml` | Admin network, InfiniBand network, DHCP, DNS, NTP |
| `telemetry_config.yml` | Telemetry sources — iDRAC, LDMS, DCGM, PowerScale |
| `omnia_config.yml` | Slurm and Kubernetes cluster definitions |
| `pxe_mapping_file.csv` | Node-to-network mapping for PXE provisioning |
| `additional_cloud_init.yml` | Custom cloud-init for stateless node provisioning |

---

## Execution

### Installation

```bash
./setup_env.sh                # Creates .venv, installs deps, registers CLI
source .venv/bin/activate     # Activates the virtual environment
```

| Flag | Description |
|------|-------------|
| `--force` | Remove existing `.venv` and recreate from scratch |
| `--debug` | Verbose output — show every package installed |

### Prerequisite Checks

Validates the OIM server before deployment. See [docs/prereq_check_reference.md](docs/prereq_check_reference.md) for details.

```bash
oim-prereq-check                       # Run all checks
oim-prereq-check --debug               # Verbose output
oim-prereq-check --stop-on-failure     # Stop on first failure
oim-prereq-check --continue-on-failure # Continue even if a check fails
oim-prereq-check --no-report           # Skip HTML report generation
```

### Running Molecule Tests

Two execution methods:

**Method A: Config-driven (batch execution)**

```bash
vi test_run_config.yml        # Enable scenarios, set command & suite
run_molecule --config          # Validate config and run all enabled scenarios
```

`test_run_config.yml` is validated before execution. Invalid scenario names, commands, run values, or suites will be rejected with a clear error message listing the supported values.

**Method B: Command-line (single scenario)**

```bash
run_molecule <scenario> test                  # Full lifecycle
run_molecule <scenario> verify                # Tests only
run_molecule <scenario> converge              # Playbook only
run_molecule <scenario> verify --suite sanity # Specific test suite
run_molecule <scenario> verify --marker smoke # Specific marker
run_molecule all test                         # All scenarios
run_molecule all verify --flow build_stream   # Build stream flow
run_molecule list                             # List available scenarios
```

Invalid scenarios, commands, or suites are validated and rejected with supported values listed.

### Suite and Marker Filtering

| Option | Mechanism | Example |
|--------|-----------|---------|
| `--suite` | Folder-based — runs tests from `tests/<suite>/` | `--suite sanity` → `tests/sanity/*.py` |
| `--marker` | Decorator-based — runs `@pytest.mark.<marker>` tests | `--marker smoke` → all `@pytest.mark.smoke` |

### Test Reports

Reports are generated in `reports/` after execution:

| Format | File | Description |
|--------|------|-------------|
| HTML | `test_report.html` | Interactive dark-themed report with collapsible sections |
| JSON | `test_report.json` | Machine-readable format for CI/CD integration |

---

## Scenarios

| # | Scenario | Omnia Playbook | Description |
|---|----------|---------------|-------------|
| 1 | `omnia_sh_install` | `omnia.sh --install` | Installs the `omnia_core` container |
| 2 | `prepare_oim` | `prepare_oim/prepare_oim.yml` | Prepares OIM — OpenCHAMI, firewall, NTP, NFS |
| 3 | `gitlab_install` | `gitlab/gitlab.yml` | Deploys GitLab for BuildStream CI/CD |
| 4 | `local_repo` | `local_repo/local_repo.yml` | Syncs packages to Pulp repository |
| 5 | `build_image_x86_64` | `build_image_x86_64/build_image_x86_64.yml` | Builds x86_64 OS images |
| 6 | `build_image_aarch64` | `build_image_aarch64/build_image_aarch64.yml` | Builds aarch64 OS images |
| 7 | `discovery` | `discovery/discovery.yml` | Discovers cluster nodes via BMC/OME |
| 8 | `provision` | `provision/provision.yml` | Provisions nodes with OS and software |
| 9 | `telemetry` | `telemetry/telemetry.yml` | Deploys telemetry stack |
| 10 | `apptainer` | — (verify only) | Verifies Apptainer runtime on Slurm nodes |
| 11 | `kubernetes` | — (verify only) | Verifies Kubernetes cluster health |
| 12 | `slurm` | — (verify only) | Verifies Slurm workload manager |
| 13 | `dcgm` | — (verify only) | Verifies NVIDIA DCGM GPU monitoring |
| 14 | `hpc_benchmarks` | — (verify only) | Verifies HPC benchmark results |
| 15 | `vast_storage` | — (verify only) | Verifies VAST storage mounts |
| 16 | `build_stream` | — (verify only) | Verifies BuildStream CI/CD pipeline |
| 17 | `one_shot_log_extraction` | — (converge + verify) | Extracts combined logs from cluster nodes |
| 18 | `upgrade_omnia_sh` | `omnia.sh --upgrade` | Upgrades the `omnia_core` container to newer version |
| 19 | `rollback_omnia_sh` | `omnia.sh --rollback` | Rolls back the `omnia_core` container to previous version |
| 20 | `gitlab_cleanup` | `gitlab/cleanup_gitlab.yml` | Removes GitLab deployment |
| 21 | `oim_cleanup` | `utils/oim_cleanup.yml` | Cleans up OIM environment |
| 22 | `omnia_sh_uninstall` | `omnia.sh --uninstall` | Uninstalls the `omnia_core` container |

---

## Project Structure

```
omnia-artifactory/
├── omnia_test_config.yml              # Central config — OIM server, settings, dataset
├── omnia_test_credentials.yml         # Sensitive credentials (auto-encrypted with Vault)
├── .omnia_test_credentials.key        # Vault encryption key (gitignored)
├── test_run_config.yml                # Batch scenario runner config
├── requirements.txt                   # Python dependencies
├── setup.py                           # Package setup (omnia-automation)
├── setup_env.sh                       # Environment setup script
├── run_molecule.sh                    # Molecule test runner (with validation)
├── run_prereq_check.py                # Prerequisite check entry point
├── pytest.ini                         # Pytest configuration and custom markers
│
├── datasets/                          # Deployment input datasets
│   └── project_default/               # Default dataset
│       ├── software_config.json
│       ├── network_spec.yml
│       ├── additional_cloud_init.yml
│       ├── ...                        # See docs/dataset_reference.md
│       └── config/                    # Per-architecture package lists
│
├── automation_library/                # Python automation library
│   ├── core/                          # Shared infrastructure
│   ├── checks/                        # Prerequisite checks
│   └── <module>/                      # Per-scenario modules
│
├── molecule/                          # Molecule test scenarios
│   ├── conftest.py                    # Global pytest fixtures
│   ├── shared/tasks/                  # Shared Ansible tasks
│   └── <scenario>/                    # Per-scenario directories
│
├── docs/                              # Detailed reference documentation
│   ├── input_reference.md             # omnia_test_config.yml parameter reference
│   ├── dataset_reference.md           # Dataset files reference
│   └── prereq_check_reference.md      # Prerequisite checks reference
│
└── reports/                           # Generated test reports (gitignored)
```

---

## Detailed References

| Document | Description |
|----------|-------------|
| [docs/input_reference.md](docs/input_reference.md) | Complete `omnia_test_config.yml` parameter reference with types, defaults, and usage |
| [docs/dataset_reference.md](docs/dataset_reference.md) | All dataset files, which Omnia playbooks consume them, and how input files flow into the container |
| [docs/prereq_check_reference.md](docs/prereq_check_reference.md) | Detailed prerequisite check descriptions and `oim-prereq-check` usage |

---

## License

Copyright 2026 Dell Inc. or its subsidiaries. All Rights Reserved.

Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at

http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.
