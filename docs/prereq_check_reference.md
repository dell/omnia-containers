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

# Prerequisite Check Reference

The `oim-prereq-check` command validates that the OIM server meets all hardware, OS, network, and software requirements before deploying Omnia.

---

## Usage

```bash
oim-prereq-check                       # Run all checks
oim-prereq-check --debug               # Verbose output
oim-prereq-check --stop-on-failure     # Stop on first failure
oim-prereq-check --continue-on-failure # Continue even if a check fails
oim-prereq-check --no-report           # Skip HTML report generation
```

The command reads all configuration from `omnia_test_config.yml`. See [input_reference.md](input_reference.md) for parameter details.

---

## Execution Mode

The prerequisite checks run either **locally** or **remotely** depending on `oim_server_ip`:

- **Local mode** (`oim_server_ip` is empty/localhost): Checks run directly on the local machine.
- **Remote mode** (`oim_server_ip` is set): Checks connect via SSH using `oim_ssh_user` and `oim_ssh_password`.

---

## Checks Performed

### 1. IPMI Tool

Verifies that `ipmitool` is installed on the OIM server. If missing, attempts to install it automatically via the system package manager.

**Config used:** None (always runs)

### 2. Hardware Inventory

Validates hardware resources against configured thresholds:

| Check | Config Parameter | Description |
|-------|-----------------|-------------|
| CPU cores | `min_cores` | Minimum physical CPU cores |
| Memory | `min_memory_gb` | Minimum RAM in GB |
| Disk space | `min_disk_gb` | Minimum available disk in GB |
| DIMM inventory | — | Logs DIMM count and sizes |
| Storage controllers | — | Logs storage controller info |

### 3. OS Validation

Validates the operating system against expected values:

| Check | Config Parameter | Description |
|-------|-----------------|-------------|
| OS name | `required_os` | e.g., `rhel`, `rocky` |
| OS version | `required_os_version` | e.g., `10` |
| Kernel version | `required_kernel_version` | Optional — skip if empty |

### 4. Network Interfaces

Validates that the configured network interfaces exist and are UP:

| Check | Config Parameter | Description |
|-------|-----------------|-------------|
| PXE interface | `pxe_interface` | Must exist and be UP |
| Public interface | `public_interface` | Must exist and be UP |
| iDRAC interface | `idrac_ip` | Only when `network_type` is `lom` |

### 5. PXE NIC Configuration

Configures the PXE network interface with the specified IP address:

| Config Parameter | Description |
|-----------------|-------------|
| `pxe_ip` | IP in CIDR notation (e.g., `172.16.107.254/24`) |
| `pxe_interface` | Target NIC |
| `force_configure_pxe` | When `true`, removes existing IP and reapplies |

### 6. NFS Server

Validates NFS server connectivity and capacity:

| Check | Config Parameter | Description |
|-------|-----------------|-------------|
| Ping | `nfs_server_ip` | Must be reachable |
| Mount test | `nfs_share_path` | Must be mountable |
| Capacity | `nfs_min_capacity_gb` | Minimum free space in GB |

### 7. Internet Access

Tests internet connectivity through the public interface by attempting to reach external URLs.

**Config used:** `public_interface`

### 8. Podman

Validates Podman installation and version:

| Check | Config Parameter | Description |
|-------|-----------------|-------------|
| Installed | — | `podman` command must exist |
| Version | `podman_min_version` | Minimum version (e.g., `5.0.0`) |

### 9. RHEL Repository

Checks that RHEL package repositories are configured and accessible on the OIM server.

### 10. Git (Conditional)

Verifies git is installed. Only runs when `reconfigure_images: true`.

### 11. Omnia Artifactory Clone (Conditional)

Clones the Omnia Artifactory repository to the OIM server. Only runs when `reconfigure_images: true`.

| Config Parameter | Description |
|-----------------|-------------|
| `omnia_repo_url` | Repository URL |
| `artifactory_branch` | Branch to clone |
| `omnia_clone_path` | Destination path |

### 12. Container Image Build (Conditional)

Builds Omnia container images on the OIM server. Only runs when `reconfigure_images: true`.

| Config Parameter | Description |
|-----------------|-------------|
| `omnia_branch` | Omnia branch/tag |
| `core_tag` | Container image tag |

---

## Reports

After completion, an HTML report is generated in `reports/` (unless `--no-report` is specified). The report includes:

- Server information (hostname, IP, OS)
- Pass/fail status for each check
- Detailed output and error messages
- Color-coded results (green = passed, red = failed, yellow = warning)

---

## Implementation

The prerequisite checks are implemented in `automation_library/checks/`:

| File | Description |
|------|-------------|
| `hardware.py` | CPU, memory, disk, DIMM, storage controller checks |
| `system.py` | OS name, version, kernel validation |
| `network.py` | Interface existence, state, PXE configuration |
| `validation.py` | NFS, internet, Podman checks |
| `repository.py` | RHEL repo, git, artifactory clone |
| `services.py` | Container image build |

The entry point is `run_prereq_check.py`, which is registered as `oim-prereq-check` via `setup.py`.
