# Upgrade and Rollback Issues

Issues related to Omnia upgrade and rollback operations, including lock file
conflicts, manifest tracking, and component-specific failures.

## Lock File Issues

**Upgrade fails: "A rollback is currently in progress"**

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

**Rollback fails: "An upgrade is currently in progress"**

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

**Manifest shows "partial" status after upgrade**

???+ note "Symptom"

    The upgrade completes but `upgrade_status` is `partial` instead of `completed`.

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

**Manifest shows "partial" status after rollback**

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

**Manifest file is missing or corrupted**

???+ note "Symptom"

    The playbook fails because `upgrade_manifest.yml` or
    `rollback_manifest.yml` cannot be parsed.

??? note "Cause"

    The manifest file was manually deleted, corrupted due to disk errors, or
    contains invalid YAML syntax.

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

**OIM upgrade fails**

???+ note "Symptom"

    The `oim` component fails during upgrade.

??? note "Cause"

    - `oim_metadata.yml` is missing or incorrectly configured
    - `omnia_core` container is not running or inaccessible
    - Database connectivity issues

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

**Kubernetes upgrade fails**

???+ note "Symptom"

    The `k8s` component fails during upgrade with status showing `failed` in
    the upgrade manifest.

??? note "Cause"

    - Cluster nodes are not in Ready state
    - Pending pods or stuck resources
    - Network connectivity issues between nodes
    - Storage mount failures

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

**Cloud-init timeout after reboot**

???+ note "Symptom"

    First control plane or first worker reboot fails with
    "Cloud-init did not complete within timeout" error.

??? note "Cause"

    Cloud-init execution takes longer than the configured timeout period due to
    slow network, large package downloads, or system resource constraints.

??? note "Resolution"

    1. SSH to the node and check `/var/log/cloud-init-output.log` and wait for
       the cloud-init execution to complete.
    2. Once execution is completed, rerun the upgrade playbook:

        ```bash title="Run on: omnia_core container"
        cd /omnia/upgrade
        ansible-playbook upgrade.yml
        ```

**Node unreachable during upgrade**

???+ note "Symptom"

    Upgrade fails with SSH connection errors or node unreachable messages.

??? note "Cause"

    - Node is powered off or has hardware issues
    - SSH service is not running on the node
    - Network connectivity issues between OIM and the node
    - Firewall blocking SSH connections

??? note "Resolution"

    1. Verify the node is powered on and accessible.
    2. Verify SSH service is running on the node.
    3. After restoring connectivity, rerun the upgrade playbook:

        ```bash title="Run on: omnia_core container"
        cd /omnia/upgrade
        ansible-playbook upgrade.yml
        ```

**Node drain fails due to standalone pods**

???+ note "Symptom"

    - Kubernetes upgrade fails during drain with error: `cannot delete Pods that
      declare no controller (use --force to override)`
    - Node is cordoned but drain operation fails
    - Upgrade status shows `drain_failed`

??? note "Cause"

    The node has standalone pods not managed by any controller (Deployment,
    StatefulSet, etc.). These are typically test pods created manually using
    `kubectl run` or `kubectl create -f pod.yaml`.

??? note "Resolution"

    1. Identify standalone pods on the failed node:

        ```bash title="Run on: omnia_core container"
        kubectl get pods -A --field-selector spec.nodeName=<node-ip> -o json |
          jq -r '.items[] | select(.metadata.ownerReferences == null) |
          "\(.metadata.namespace)/\(.metadata.name)"'
        ```

    2. Delete the standalone pods:

        ```bash title="Run on: omnia_core container"
        kubectl delete pod <pod-name> -n <namespace>
        ```

        !!! warning

            Standalone pods will NOT be recreated after deletion.

    3. Re-run the upgrade:

        ```bash title="Run on: omnia_core container"
        cd /omnia/upgrade
        ansible-playbook upgrade.yml
        ```

!!! tip

    Before starting any upgrade, identify and remove all standalone pods:

    ```bash title="Run on: omnia_core container"
    kubectl get pods -A -o json | jq -r '.items[] |
      select(.metadata.ownerReferences == null) |
      "\(.metadata.namespace)/\(.metadata.name)"'
    ```

    Always use Deployments, StatefulSets, or Jobs instead of creating standalone
    pods in production.

**Build image fails for aarch64 — missing inventory**

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

**Target core container image is missing**

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
        git clone -b omnia-container-v2.2.0.0 https://github.com/dell/omnia-containers.git
        cd omnia-containers
        ./build_images.sh core core_tag=2.2 omnia_branch=v2.2.0.0
        ```

    3. Re-run the `omnia.sh` command.

**Kubernetes rollback fails**

???+ note "Symptom"

    The `k8s-telemetry` component fails during rollback.

??? note "Cause"

    - Control plane is unreachable or nodes are not in Ready state
    - Backup files are missing or corrupted on NFS
    - Storage mount failures preventing access to backup directory
    - Network connectivity issues between OIM and Kubernetes cluster

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

**Slurm nodes do not recover after rollback**

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

**BuildStreaM rollback hangs during Alembic database migration**

???+ note "Symptom"

    The BuildStreaM rollback appears to hang during the Alembic database
    migration downgrade step.

??? note "Cause"

    One or more PostgreSQL sessions are stuck `idle in transaction`, blocking
    the Alembic migration that downgrades the BuildStreaM database from the
    2.2 schema back to the 2.1 schema.

??? note "Resolution"

    1. Show all PostgreSQL sessions that are `idle in transaction`:

        ```bash title="Run on: OIM host"
        podman exec omnia_postgres psql -U <postgres_db_username> -d build_stream_db \
          -c "SELECT pid, state, now() - xact_start AS age, LEFT(query, 80) FROM pg_stat_activity WHERE state = 'idle in transaction';"
        ```

    2. Terminate the blocking session(s) by PID. Replace `<pid>` with the value
       from the `pid` column returned in the previous step:

        ```bash title="Run on: OIM host"
        podman exec omnia_postgres psql -U <postgres_db_username> -d build_stream_db \
          -c "SELECT pg_terminate_backend(<pid>);"
        ```

    3. If the Alembic downgrade still hangs, check all active database sessions
       and terminate only the PIDs associated with old migration queries:

        ```bash title="Run on: OIM host"
        podman exec omnia_postgres psql -U <postgres_db_username> -d build_stream_db \
          -c "SELECT pid, state, LEFT(query, 100) FROM pg_stat_activity WHERE state <> 'idle';"
        ```

    4. After clearing the blocking sessions, re-run the BuildStreaM/rollback
       playbook step.

## Upgrade or Rollback Fails at the Cloud-Init/BSS Verification Gate

???+ note "Symptom"

    - `upgrade/upgrade.yml` or `rollback/rollback.yml` fails during the `renew_certificates.yml` step with the error: `Certificate recovery gate FAILED. Services still unreachable after acme-deploy restart.`
    - `ochami bss service status` or `ochami cloud-init service status` returns `connection refused` or a non-zero exit code
    - Critical OpenCHAMI services (for example, `haproxy`, `coresmd`, `cloud-init-server`) are inactive or in a failed state after certificate renewal

??? note "Cause"

    - OpenCHAMI services have not fully stabilized following the certificate update and container restart
    - HAProxy is using a stale backend or DNS cache, or an outdated TLS certificate
    - The `coresmd` service (v2.1) or the `coresmd-coredhcp`/`coresmd-coredns` services (v2.2) did not restart after HAProxy

??? note "Resolution"

    Perform the following commands on the OIM node to verify and recover the services:

    1. Identify services that are not running:

        ```bash title="Run on: OIM host"
        systemctl list-dependencies openchami.target --plain | while read svc; do
          echo "$svc: $(systemctl is-active $svc)"
        done
        ```

    2. Verify BSS and cloud-init service status:

        ```bash title="Run on: OIM host"
        ochami bss service status
        ochami cloud-init service status
        ```

    3. Reset failed services and restart the OpenCHAMI target:

        ```bash title="Run on: OIM host"
        systemctl reset-failed
        systemctl restart openchami.target
        sleep 30
        ```

    4. If cloud-init or BSS remains unreachable, refresh HAProxy and the certificate:

        ```bash title="Run on: OIM host"
        systemctl restart acme-deploy.service
        sleep 10
        systemctl stop haproxy.service
        systemctl start haproxy.service
        sleep 10
        ```

    5. Verify that all OpenCHAMI services are operational:

        ```bash title="Run on: OIM host"
        systemctl list-dependencies openchami.target
        ```

    6. Re-run the upgrade or rollback playbook:

        ```bash title="Run on: OIM host"
        # For upgrade
        cd /omnia/upgrade
        ansible-playbook upgrade.yml

        # For rollback
        cd /omnia/rollback
        ansible-playbook rollback.yml
        ```

## Cloud-Init/BSS Updates Fail During Upgrade or Rollback

???+ note "Symptom"

    - The OpenCHAMI `update_cloud_init_bss` step (executed as part of `upgrade/upgrade.yml` or `rollback/rollback.yml`) fails with the error: `OpenCHAMI services are unreachable after certificate renewal and HAProxy restart.`
    - `ochami cloud-init service status` or `ochami bss service status` fails before the BSS or cloud-init updates are applied

??? note "Cause"

    - OpenCHAMI services are not yet reachable when the step begins
    - HAProxy or `cloud-init-server` has not completed startup following the certificate renewal or container restart

??? note "Resolution"

    1. Verify OpenCHAMI service health on the OIM:

        ```bash title="Run on: OIM host"
        ochami cloud-init service status
        ochami bss service status
        systemctl status haproxy.service
        podman logs cloud-init-server
        ```

    2. Recover the services using the procedure in [Upgrade or Rollback Fails at the Cloud-Init/BSS Verification Gate](#upgrade-or-rollback-fails-at-the-cloud-initbss-verification-gate).

    3. Re-run the failed playbook:

        ```bash title="Run on: OIM host"
        # For upgrade
        cd /omnia/upgrade
        ansible-playbook upgrade.yml

        # For rollback
        cd /omnia/rollback
        ansible-playbook rollback.yml
        ```

## Start OpenCHAMI Services with New Images Task Gets Stuck

???+ note "Symptom"

    The "Start OpenCHAMI services with new images" task gets stuck during the Omnia 2.1 to 2.2 upgrade.

??? note "Cause"

    The Hydra service fails during the upgrade due to an environment variable configuration issue.

??? note "Resolution"

    1. Check the OpenCHAMI services status:

        ```bash title="Run on: OIM host"
        systemctl status hydra.service
        ```

    2. If hydra.service fails with the following error:

        ```
        secrets.system: <nil>
        expected array, but got null
        ```

        The SECRETS_SYSTEM environment variable is overriding the valid secrets.system array in hydra.yml.

    3. **Workaround**: In the Hydra Quadlet file, comment out the following entry:

        ```ini title="Hydra Quadlet file"
        #Secret=hydra_system_secret,type=env,target=SECRETS_SYSTEM
        ```

        Keep the DSN secret unchanged:

        ```ini title="Hydra Quadlet file"
        Secret=hydra_dsn,type=env,target=DSN
        ```

    4. Reload systemd and restart Hydra:

        ```bash title="Run on: OIM host"
        systemctl daemon-reload
        systemctl reset-failed hydra.service
        systemctl restart hydra.service
        ```

    5. Verify that Hydra is running:

        ```bash title="Run on: OIM host"
        systemctl status hydra.service
        ```

    6. Re-run the upgrade playbook:

        ```bash title="Run on: omnia_core container"
        cd /omnia/upgrade
        ansible-playbook upgrade.yml
        ```

!!! info

    - [Kernel Version Override Issues](kernel_version_override.md) — Kernel override troubleshooting.
    - [General Troubleshooting Steps](general_troubleshooting.md) — Common troubleshooting steps.
    - [Upgrade Omnia](../Operations/upgrade_omnia.md) — Upgrade procedure.
    - [Rollback Omnia](../Operations/rollback_omnia.md) — Rollback procedure.
