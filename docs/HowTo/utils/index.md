# Utilities

The utils domain (collection: `omnia.utils`) provides helper utilities for OS installation, Slurm configuration backup, and aarch64 node preparation.

## Overview

The utils domain handles auxiliary tasks that support the main deployment workflow. It provides utilities for unattended OS installation, Slurm configuration backup, and aarch64 node preparation. These are optional helper utilities that can be used independently or as part of the cluster deployment process.

## System Context

```
  orchestrator_state.yml                      iso_config.yml
  +---------------------+     +---------------------+
  |    Orchestrator     |---->|                     |
  |  (upstream)           |     |      Utils           |---->  ISO files
  +---------------------+     |                     |     & backups
                              |  (iso creation,      |
                              |   log collection,    |
                              |   slurm utilities)   |
                              +---------------------+
```

## Domain Workflow

The utils domain supports the following execution tags:

| Tag | Description | Prerequisites |
|-----|-------------|---------------|
| `validate` | Validate utility configuration | No |
| `prepare` | Prepare utility environment | No |
| `execute` | Execute utility task | No |
| `cleanup` | Remove utility artifacts | No |

## Execution Flow

The utils domain provides independent utility playbooks that can be run on-demand:

```
1. Initialize domain environment
2. Validate configuration files
3. Execute specific utility task:
   - ISO creation and delivery
   - Log collection from cluster nodes
   - Slurm configuration backup/rollback
   - ARM64/aarch64 node preparation
```

## Key Inputs

| Input | Location | Purpose |
|-------|----------|---------|
| `iso_config.yml` | `/opt/omnia/utils/input/<project>/iso_config.yml` | ISO creation and delivery settings |
| `telemetry_config.yml` | `/opt/omnia/utils/input/<project>/telemetry_config.yml` | Telemetry source configuration |
| `arm_config.yml` | `/opt/omnia/utils/input/<project>/arm_config.yml` | ARM-specific settings (optional) |
| `bmc_inventory.csv` | `/opt/omnia/utils/input/<project>/bmc_inventory.csv` | BMC inventory for iDRAC operations |

**Input Sources:**
- **Administrator** - Provides utility configuration files
- **Domain initialization** - Stages input files from samples directory

## Key Outputs

| Output | Location | Purpose |
|--------|----------|---------|
| ISO files | `/opt/omnia/utils/output/<project>/` | Custom OS installation ISOs |
| Log archives | `/opt/omnia/utils/output/<project>/` | Collected logs from cluster nodes |
| Slurm config backups | `/opt/omnia/utils/output/<project>/` | Slurm configuration backup files |

## Output Contract

This contract is consumed by:
- **Administrators** - For manual cluster operations and troubleshooting
- **Cluster workflows** - For ongoing operations

## Utils Components

| Category | Component | Description |
|----------|-----------|-------------|
| **OS Installation** | ISO Creation | Create custom OS installation ISOs |
| | ISO Delivery | Deliver ISOs via iDRAC virtual media |
| | Unattended Install | Perform bare-metal OS installation |
| **Configuration** | Slurm Backup | Backup Slurm configuration files |
| | Slurm Rollback | Rollback Slurm configuration |
| | Slurm Cleanup | Clean up Slurm configuration |
| **ARM Support** | ARM Preparation | Prepare aarch64 nodes for deployment |
| | ARM Validation | Validate ARM configuration |
| **Log Collection** | Log Collector | Collect logs from cluster nodes |

## Related Guides

### OS Installation
- [Install OS Unattended](install_os_unattended.md) -- Perform bare-metal OS installation
- [Prepare aarch64 Node](prepare_aarch64_node.md) -- Prepare ARM64/aarch64 nodes

### Configuration Utilities
- [Backup Slurm Config](backup_slurm_config.md) -- Backup Slurm configuration

### Additional
- [Domain Contract](../../Reference/domain_contracts/utils_contract.md) -- Utils domain contract




