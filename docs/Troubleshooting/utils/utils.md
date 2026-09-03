# Utils Issues

Helper utilities issues - Backup, install, and prepare operations

## Backup Issues

???+ note "Symptom"

    Slurm configuration backup operations fail.

??? note "Cause"

    - Insufficient permissions
    - Backup directory not accessible
    - Disk space issues

??? note "Resolution"

    1. Verify backup directory permissions
    2. Check available disk space
    3. Re-run backup operation

## Install Issues

???+ note "Symptom"

    Installation operations fail.

??? note "Cause"

    - Missing dependencies
    - Network connectivity issues
    - Permission problems

??? note "Resolution"

    1. Verify all dependencies are installed
    2. Check network connectivity
    3. Verify user permissions

## Prepare Issues

???+ note "Symptom"

    Prepare operations fail.

??? note "Cause"

    - Configuration errors
    - Missing prerequisites
    - Environment issues

??? note "Resolution"

    1. Verify configuration files
    2. Check prerequisites are met
    3. Verify environment setup

!!! info
    - [Config Backup](../HowTo/utils/backup_slurm_config.md) -- Slurm configuration backup
    - [Prepare aarch64 Node](../HowTo/utils/prepare_aarch64_node.md) -- aarch64 node preparation
    - [Log Management](../Operations/log_management.md) -- Where to find logs for deeper diagnosis
