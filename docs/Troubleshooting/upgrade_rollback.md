# Upgrade and Rollback Issues

Issues related to Omnia upgrade and rollback operations, including lock file
conflicts, manifest tracking, and component-specific failures.

## Lock File Issues

### Upgrade Fails: Rollback Lock Exists

???+ note "Symptom"

    The upgrade playbook aborts with the message:
    *A rollback is currently in progress. Cannot start an upgrade.*

??? note "Cause"

    The file `/opt/omnia/.data/rollback_in_progress.lock` exists, indicating a
    rollback is either running or was previously interrupted without cleanup.

??? note "Resolution"

    1. Check if a rollback process is actually running:

        ```bash title="Run on: OIM host"
        ps aux | grep rollback
        ```

    2. If no rollback process is active, the lock is stale. Remove it manually:

        ```bash title="Run on: OIM host"
        rm /opt/omnia/.data/rollback_in_progress.lock
        ```

    3. Rerun the upgrade playbook.

### Rollback Fails: Upgrade Lock Exists

???+ note "Symptom"

    The rollback playbook aborts with the message:
    *An upgrade is currently in progress. Cannot start a rollback.*

??? note "Cause"

    The file `/opt/omnia/.data/upgrade_in_progress.lock` exists.

??? note "Resolution"

    1. Check if an upgrade process is actually running:

        ```bash title="Run on: OIM host"
        ps aux | grep upgrade
        ```

    2. If no upgrade process is active, remove the stale lock:

        ```bash title="Run on: OIM host"
        rm /opt/omnia/.data/upgrade_in_progress.lock
        ```

    3. Rerun the rollback playbook.

## Manifest Issues

### Manifest Shows Partial Status After Upgrade

???+ note "Symptom"

    The upgrade completes but `upgrade_status` is `partial` instead of
    `completed`.

??? note "Cause"

    One or more components did not reach `completed` or `skipped` status.

??? note "Resolution"

    1. Check which components are not completed:

        ```bash title="Run on: omnia_core container"
        cat /opt/omnia/.data/upgrade_manifest.yml
        ```

    2. Review the component status to identify the failed component.
    3. After fixing the issue, rerun the full upgrade. Already-completed
       components are skipped automatically:

        ```bash title="Run on: omnia_core container"
        cd /omnia/upgrade
        ansible-playbook upgrade.yml
        ```

### Manifest Shows Partial Status After Rollback

???+ note "Symptom"

    The rollback completes but `rollback_status` is `partial` instead of
    `completed`.

??? note "Cause"

    One or more components did not reach `completed` or `skipped` status.

??? note "Resolution"

    1. Check which components are not completed:

        ```bash title="Run on: omnia_core container"
        cat /opt/omnia/.data/rollback_manifest.yml
        ```

    2. Review the component status to identify the failed component.
    3. After fixing the issue, rerun the full rollback. Already-completed
       components are skipped automatically:

        ```bash title="Run on: omnia_core container"
        cd /omnia/rollback
        ansible-playbook rollback.yml
        ```

### Manifest File Is Missing or Corrupted

???+ note "Symptom"

    The playbook fails because `upgrade_manifest.yml` or
    `rollback_manifest.yml` cannot be parsed.

??? note "Resolution"

    1. Check the manifest file for syntax errors:

        ```bash title="Run on: omnia_core container"
        cat /opt/omnia/.data/upgrade_manifest.yml
        ```

    2. If corrupted, remove the manifest to start fresh:

        ```bash title="Run on: omnia_core container"
        rm /opt/omnia/.data/upgrade_manifest.yml
        ```

    3. Rerun the playbook. A new manifest will be initialized from
       `oim_metadata.yml`.

    !!! caution

        Removing the manifest means all component statuses are reset to
        `pending`. Previously completed components will be re-executed.

## Component-Specific Issues

### OIM Upgrade Fails

???+ note "Symptom"

    The `oim` component fails during upgrade.

??? note "Resolution"

    1. Check the playbook output for the specific error.
    2. Verify `oim_metadata.yml` is populated correctly:

        ```bash title="Run on: omnia_core container"
        cat /opt/omnia/.data/oim_metadata.yml
        ```

    3. Ensure the `omnia_core` container is running and accessible:

        ```bash title="Run on: OIM host"
        podman ps | grep omnia_core
        ```

    4. After fixing the issue, rerun:

        ```bash title="Run on: omnia_core container"
        cd /omnia/upgrade
        ansible-playbook upgrade.yml
        ```

### Kubernetes Upgrade Fails

???+ note "Symptom"

    The `k8s` component fails during upgrade with status showing `failed` in
    the upgrade manifest.

??? note "Resolution"

    1. Check the upgrade status file to identify what failed:

        ```bash title="Run on: omnia_core container"
        cat <mount_point>/upgrade/upgrade_status.yml
        ```

        The mount point is defined in your `storage_config.yml` file. Look for
        the NFS mount entry where `name: "nfs_k8s"` and the `mount_point`
        field shows the path.

    2. Verify cluster health:
        - Ensure all nodes are reachable and in a `Ready` state.
        - Check for pending pods or stuck resources.
    3. Fix the underlying issue based on the error.
    4. After resolving, rerun:

        ```bash title="Run on: omnia_core container"
        cd /omnia/upgrade
        ansible-playbook upgrade.yml
        ```

        - Completed steps will be skipped automatically.
        - Only failed steps will be retried.

    5. If the issue persists after multiple retries, rollback:

        ```bash title="Run on: omnia_core container"
        cd /omnia/rollback
        ansible-playbook rollback.yml
        ```

### Cloud-Init Timeout After Reboot

???+ note "Symptom"

    First control plane or first worker reboot fails with
    "Cloud-init did not complete within timeout" error.

??? note "Resolution"

    1. SSH to the node and check `/var/log/cloud-init-output.log` and wait for
       the cloud-init execution to complete.
    2. Once execution is completed, rerun the upgrade playbook:

        ```bash title="Run on: omnia_core container"
        cd /omnia/upgrade
        ansible-playbook upgrade.yml
        ```

### Node Unreachable During Upgrade

???+ note "Symptom"

    Upgrade fails with SSH connection errors or node unreachable messages.

??? note "Resolution"

    1. Verify the node is powered on and accessible.
    2. Verify SSH service is running on the node.
    3. After restoring connectivity, rerun the upgrade playbook:

        ```bash title="Run on: omnia_core container"
        cd /omnia/upgrade
        ansible-playbook upgrade.yml
        ```

### Build Image Fails for aarch64

???+ note "Symptom"

    The `build_image` component fails with:
    *"aarch64 functional groups detected in pxe_mapping_file but no hosts
    found in 'admin_aarch64' inventory group"* or
    *"The inventory group 'admin_aarch64' does not exist or has no hosts."*

??? note "Cause"

    The PXE mapping file contains aarch64 functional groups, but the upgrade
    was run without an inventory file containing the `[admin_aarch64]` group.

??? note "Resolution"

    1. Create an inventory file with the `[admin_aarch64]` group containing
       exactly one ARM admin node:

        ```ini title="Example: aarch64 inventory file"
        [admin_aarch64]
        <arm_admin_node_ip>
        ```

    2. Re-run the upgrade with the inventory file:

        ```bash title="Run on: omnia_core container"
        cd /omnia/upgrade
        ansible-playbook upgrade.yml -i <inventory_file>
        ```

    !!! note

        The `[admin_aarch64]` group must have exactly one host. NFS must be
        configured on the OIM for aarch64 image building.

### Target Core Container Image Is Missing

???+ note "Symptom"

    `omnia.sh --upgrade` or `omnia.sh --rollback` aborts reporting that the
    required `omnia_core` image is not available locally.

??? note "Cause"

    The container image for the target version has not been built on the OIM
    host.

??? note "Resolution"

    1. Confirm which image tags are available:

        ```bash title="Run on: OIM host"
        podman images | grep omnia_core
        ```

    2. If the required image is missing, build it on the OIM host (see
       [Build the Omnia 2.2.0.0 Core Container Image](../Operations/upgrade_omnia.md#build-the-omnia-2200-core-container-image)
       in the Upgrade guide):

        ```bash title="Run on: OIM host"
        git clone -b omnia-container-v2.2.0.0 https://github.com/dell/omnia-artifactory.git
        cd omnia-artifactory
        ./build_images.sh core core_tag=2.2 omnia_branch=v2.2.0.0
        ```

    3. Re-run the `omnia.sh` command.

### Kubernetes Rollback Fails

???+ note "Symptom"

    The `k8s-telemetry` component fails during rollback.

??? note "Resolution"

    1. Check the rollback status file to identify what failed. The status file
       is located at `<mount_point>/upgrade/rollback_status.yml`. The mount
       point is defined in your `storage_config.yml` file. Look for the NFS
       mount entry where `name: "nfs_k8s"` and the `mount_point` field shows
       the path.

    2. Verify the control plane is reachable and check node status.

    3. Check for missing backup files:
        - Verify the backup directory exists on NFS at
          `<mount_point>/upgrade/backup/`.
        - Check for required backup files:
            - etcd snapshot:
              `<mount_point>/upgrade/backup/etcd-snapshot-*.db`
            - etcd members:
              `<mount_point>/upgrade/backup/etcd-members.json`
            - K8s configs:
              `<mount_point>/upgrade/backup/configs/<node>/k8s-config.tar.gz`
        - If backups are missing, rollback cannot proceed. The upgrade must
          have failed before backups were created, or backups were accidentally
          deleted.

    4. Check etcd restore issues. If rollback fails during etcd restore stage
       with "etcd snapshot restore failed" or "/var/lib/etcd/member does not
       exist":
        - SSH to the affected control plane node.
        - Check if etcd data directory is accessible at `/var/lib/etcd/`.
        - Verify `etcdutl` binary is available in backup directory at
          `<mount_point>/upgrade/backup/etcdutl`.
        - Manually verify etcd snapshot integrity using `etcdutl`.
        - If snapshot is corrupted, rollback cannot proceed.

    5. Check for nodes stuck in `NotReady` state. If nodes remain in
       `NotReady` state after rollback:
        - Check node status and identify `NotReady` nodes.
        - Check kubelet service status and logs on the affected node.
        - Verify CNI pods are running in the `calico-system` namespace.
        - Restart kubelet service on the affected node.
        - If issue persists, verify network connectivity and CNI
          configuration.

    6. After resolving the issue, rerun the full rollback.
       Already-completed stages are skipped automatically.

### Slurm Nodes Do Not Recover After Rollback

???+ note "Symptom"

    The rollback summary reports one or more Slurm/login nodes as unreachable,
    reboot-failed, or `sinfo` not responding.

??? note "Cause"

    A node did not boot back with the restored 2.1 configuration, or Slurm
    services did not start after reboot.

??? note "Resolution"

    1. Review the node status report printed at the end of the Slurm rollback.
    2. For unreachable nodes, verify power and network connectivity.
    3. For `sinfo` failures, check the Slurm service on the node and
       reconfigure:

        ```bash title="Run on: affected Slurm node"
        systemctl restart slurmd
        scontrol reconfigure
        ```

    4. Re-run the full rollback. Nodes that already rebooted successfully are
       not rebooted again:

        ```bash title="Run on: omnia_core container"
        cd /omnia/rollback
        ansible-playbook rollback.yml
        ```

    !!! note

        There is no standalone `provision` rollback. Cloud-Init and BSS boot
        configuration is restored within the Slurm and Kubernetes rollbacks. If
        a node's boot configuration appears incorrect after rollback, rerun the
        rollback for the corresponding component (`slurm` or `k8s`).

## General Troubleshooting Steps

### Check Playbook Logs

Increase Ansible verbosity for detailed output:

```bash title="Run on: omnia_core container"
cd /omnia/upgrade
ansible-playbook upgrade.yml -vvv
```

### Review State Files

All state files are stored in `/opt/omnia/.data/`:

```bash title="Run on: omnia_core container"
ls -la /opt/omnia/.data/
cat /opt/omnia/.data/upgrade_manifest.yml
cat /opt/omnia/.data/rollback_manifest.yml
cat /opt/omnia/.data/oim_metadata.yml
```

### Check Archived Manifests

Previous manifests are archived for history:

```bash title="Run on: omnia_core container"
ls /opt/omnia/.data/archive/
```

### Reset Upgrade/Rollback State

To completely reset the upgrade/rollback state and start fresh:

!!! caution

    This will discard all upgrade/rollback progress. Use only as a last resort.

```bash title="Run on: omnia_core container"
rm -f /opt/omnia/.data/upgrade_manifest.yml
rm -f /opt/omnia/.data/rollback_manifest.yml
rm -f /opt/omnia/.data/upgrade_in_progress.lock
rm -f /opt/omnia/.data/rollback_in_progress.lock
```

### Verify oim_metadata.yml

The `oim_metadata.yml` file is the source of truth for version information.
Ensure it contains the correct values:

```bash title="Run on: omnia_core container"
cat /opt/omnia/.data/oim_metadata.yml
```

Expected fields:

- `omnia_version` — Currently installed version.
- `previous_omnia_version` — Previous version.
- `upgrade_backup_dir` — Path to the backup directory.

!!! note

    `oim_metadata.yml` is read-only for upgrade and rollback flows. It is
    never modified by the playbooks. If the version information is incorrect,
    it must be fixed manually before rerunning.

!!! info "Related Documentation"

    - [Upgrade Omnia](../Operations/upgrade_omnia.md) — Upgrade procedure.
    - [Rollback Omnia](../Operations/rollback_omnia.md) — Rollback procedure.
