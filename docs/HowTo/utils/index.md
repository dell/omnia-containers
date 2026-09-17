# Utilities

## Overview

The Utils module provides optional utilities that run from the
Omnia Infrastructure Manager (OIM). The current Utils entry point supports
collecting Kubernetes and Slurm logs, installing RHEL on a bare-metal node
through iDRAC Virtual Media, backing up Omnia domain logs stored on the OIM,
managing the active Slurm configuration, and cleaning up artifacts from those
workflows.

The OS installation workflow supports both `x86_64` and `aarch64`. Slurm
configuration backup, cleanup, and rollback are exposed through separate,
on-demand tags in the Utils entry-point playbook.

## Prerequisites

| Requirement | Supported by the Utils source |
|---|---|
| Operating system | RHEL 10.x or a compatible Enterprise Linux 10 system |
| Python | 3.12 or later |
| Ansible | `ansible-core` 2.20 or later |
| Runtime location | Omnia Infrastructure Manager |
| Environment | `/etc/omnia/omnia.env` installed and consistent with the OIM |
| Project inputs | Initialized under `$OMNIA_DATA_PATH/utils/input/$OMNIA_PROJECT_NAME/` |

The default data path is `/opt/omnia`, and the default project name is
`project_default`. Network access, storage, credentials, and target-system
requirements depend on the selected utility.

## Workflow tags

Run Utils workflows through the OIM domain launcher:

=== "Using omnia.sh (recommended)"

    ```bash title="Run on: OIM host"
    cd <OMNIA_SOURCE_PATH>/src/main
    ./omnia.sh --run utils --tags <tag>
    ```

=== "Using ansible-playbook"

    ```bash title="Run on: OIM host"
    source /opt/omnia/activate-omnia.sh
    cd <OMNIA_SOURCE_PATH>/src/utils
    ansible-playbook playbooks/utils.yml --tags <tag>
    ```

| Tag | Behavior |
|---|---|
| No tag or `setup` | Initialize Utils facts and project paths without running a utility workflow. |
| `precheck` | Validate the installed OIM environment used by Utils. |
| `collect` | Collect and bundle Kubernetes and Slurm logs. |
| `install_os` | Build and deploy installation media through iDRAC Virtual Media. |
| `backup_oim_logs` | Archive selected Omnia domain logs to local or NFS storage. |
| `slurm_config_backup` | Back up the active Slurm controller configuration with checksummed metadata. |
| `slurm_config_cleanup` | Delete the active Slurm configuration after an optional backup and explicit confirmation. |
| `slurm_config_rollback` | Restore a selected Slurm configuration backup and reconfigure the controller. |
| `cleanup_logs` | Remove log-collection artifacts. |
| `cleanup_install_os` | Remove temporary OS-installation artifacts and optionally reset credentials. |
| `cleanup_backup_oim_logs` | Remove every OIM log-backup run directory from the resolved destination. |
| `cleanup_slurm_config_backups` | Remove every Slurm configuration backup-run directory from the resolved destination. |
| `cleanup` | Run all four cleanup playbooks, including OIM log-backup and Slurm configuration backup cleanup. |

!!! note

    Running `./omnia.sh --run utils` without a tag performs Utils setup only.
    It does not collect or back up logs, manage Slurm configuration, or install
    an operating system. The `upgrade` and `rollback` tags are placeholders in
    the current source and do not perform lifecycle operations. The supported
    Slurm restore operation is `slurm_config_rollback`.

!!! danger

    The general `cleanup` tag includes `cleanup_slurm_config_backups`, which
    removes all stored Slurm configuration backup runs from the resolved
    destination without confirmation. Use a scoped cleanup tag when other
    utility artifacts must be preserved.

## Choose a task

| Task | Use it to |
|---|---|
| [Install an OS unattended](install_os_unattended.md) | Build a Kickstart-enabled ISO, attach it through iDRAC Virtual Media, and install one `x86_64` or `aarch64` node. |
| [Collect cluster logs](../../Operations/collect_cluster_logs.md) | Collect Kubernetes and Slurm logs from configured nodes and create a support archive with metadata. |
| [Back up OIM logs](backup_oim_logs.md) | Archive logs from selected Omnia domains on the OIM to local or NFS storage. |
| [Clean up Utils](cleanup_utils.md) | Remove cluster-log, OS-installation, OIM log-backup, or Slurm configuration backup artifacts with the applicable cleanup tag. |
| [Manage Slurm configuration](backup_slurm_config.md) | Back up, delete, or restore the active Slurm configuration and remove stored backups. |

## Contract reference

See the [Utils Domain Contract](../../Reference/domain_contracts/utils_contract.md)
for the environment, input files, credentials, output paths, and generated
status structures used by the current workflows.
