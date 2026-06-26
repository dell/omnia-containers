Rollback Omnia
====================

Omnia provides a rollback mechanism to revert an upgrade and return the cluster to the previous version. Rollback processes components in **reverse order** compared to upgrade, with manifest tracking for idempotent reruns.

.. important::
    * Rollback must be initiated from the OIM host using ``omnia.sh --rollback`` before entering the ``omnia_core`` container.
    * Rollback is intended for recovering from a **failed or partial upgrade**. Rolling back a fully completed upgrade is blocked by default and not recommended.
    * The rollback orchestrator must be invoked from the parent directory containing ``rollback/`` folders.

When to Use Rollback
---------------------

Use rollback in the following scenarios:

* An upgrade failed partway through and components are in an inconsistent state.
* A component upgrade completed but introduced regressions or failures.
* The upgrade was interrupted (e.g., network failure, process crash) and cannot be resumed.

.. caution::
    Rolling back after a **fully successful upgrade** is not recommended because all components were upgraded consistently. If you need to rollback despite successful completion, use ``-e force_rollback=true``.

Rollback Component Order
--------------------------

Rollback processes components in **reverse order** of the upgrade:

.. list-table::
    :header-rows: 1
    :widths: 10 30 60

    * - Order
      - Component
      - Description
    * - 1
      - ``slurm``
      - Rollback Slurm cluster (rolled back first)
    * - 2
      - ``k8s-telemetry``
      - Rollback Kubernetes cluster and verify telemetry pods (single combined component)
    * - 3
      - ``build_stream``
      - Rollback BuildStreaM upgrade / enablement
    * - 4
      - ``oim``
      - Rollback OIM (includes OpenCHAMI) — rolled back last

.. note::
    - Kubernetes and Telemetry are handled as a **single combined rollback component** (``k8s-telemetry``). The etcd snapshot restore reverts the K8s cluster to its pre-upgrade state, which also restores all telemetry pods (VictoriaMetrics, Kafka, etc.) to their 2.1 versions. Telemetry pod health verification is performed as part of the K8s rollback (Stage 8d). There is no separate telemetry rollback step.
    - There is no separate ``local_repo``, ``build_image``, or ``provision`` rollback step. The packages and images produced during upgrade do not require active reversion, and the Cloud-Init and BSS boot configuration is restored to the previous version **within** the Slurm and Kubernetes rollbacks for the affected nodes.

Rollback Workflow
------------------

Phase 0: Core Container Rollback (OIM Host)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The rollback begins on the OIM host outside the ``omnia_core`` container.

.. important::
    **Use the Omnia 2.2.0.0 omnia.sh script for rollback operations**

    The ``omnia.sh`` script from Omnia 2.1.0.0 does **not** support correct rollback operations. You must download and use the Omnia 2.2.0.0 version of ``omnia.sh`` to perform rollbacks.

    Do **not** attempt to run ``./omnia.sh --rollback`` using the 2.1.0.0 script.

Download the Omnia 2.2.0.0 omnia.sh Script
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Before starting the rollback, download the correct version of the ``omnia.sh`` script:

1. Download the Omnia 2.2.0.0 ``omnia.sh`` script from the Omnia repository: ::

     wget https://raw.githubusercontent.com/dell/omnia/refs/tags/v2.2.0.0/omnia.sh

2. Set executable permissions: ::

    chmod +x omnia.sh

3. Verify the script version (optional): ::

    ./omnia.sh --version

Running the Core Container Rollback
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

1. Run the core container rollback command: ::

    sudo ./omnia.sh --rollback

2. The script performs the following:

    * Detects current version from ``oim_metadata.yml``
    * Shows available rollback targets
    * Validates version and backup availability
    * Requests user approval
    * Stops the current ``omnia_core`` container and swaps it to the previous version image
    * Restores input files, configuration, and metadata from the backup directory
    * Creates rollback guard lock at ``/opt/omnia/.data/rollback_in_progress.lock``
    * Displays post-rollback instructions

3. After the container swap completes, SSH into the ``omnia_core`` container to proceed with component rollbacks.

Running the Component Rollback
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

1. SSH into the OIM node and enter the ``omnia_core`` container: ::

    ssh omnia_core

2. Run the rollback playbook: ::

    cd /omnia/rollback
    ansible-playbook rollback.yml -e force_rollback=true

Validation Checks
~~~~~~~~~~~~~~~~~~

The rollback orchestrator performs the following validation checks before making any changes:

1. **Upgrade lock check** — If ``/opt/omnia/.data/upgrade_in_progress.lock`` exists, the rollback aborts. An upgrade must complete (or the lock must be manually removed) before rollback can proceed.

2. **Completed upgrade check** — If the ``upgrade_manifest.yml`` shows ``upgrade_status: completed``, the rollback is blocked by default. Override with ``-e force_rollback=true``.

3. **Already-completed rollback check** — If a previous ``rollback_manifest.yml`` shows ``rollback_status: completed``, the rollback is blocked. Override with ``-e force_rollback=true``.

Lock Management
~~~~~~~~~~~~~~~~

* ``/opt/omnia/.data/rollback_in_progress.lock`` — Created at the start of the rollback. Removed on completion.
* ``/opt/omnia/.data/upgrade_in_progress.lock`` — If this lock exists, rollback aborts.

.. note::
    The ``omnia.sh --rollback`` wrapper may pre-create the rollback lock. The playbook detects this and proceeds normally.

Manifest Tracking
~~~~~~~~~~~~~~~~~~

Rollback state is tracked in ``/opt/omnia/.data/rollback_manifest.yml``:

* **rollback_id** — Unique identifier for this rollback run.
* **triggered_from_upgrade_id** — The upgrade ID that triggered this rollback.
* **source_version** — The currently installed version (rolling back from).
* **target_version** — The version being rolled back to.
* **rollback_status** — Overall status: ``in-progress`` or ``completed``.
* **component_status** — Per-component status: ``pending``, ``in-progress``, ``completed``, ``skipped``, or ``failed``.

On rerun, already-completed components are automatically skipped.

BuildStreaM Terminal Gate (Rollback)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If BuildStreaM was enabled during the upgrade, the downstream components (``slurm``, ``k8s-telemetry``) were never upgraded by Omnia — they are managed by the GitLab CI/CD pipeline. In this scenario, these components are **automatically skipped during rollback** because there is nothing to roll back. Only ``build_stream`` and ``oim`` are actually rolled back.

Components that are skipped are recorded as ``skipped`` in the rollback manifest, which is treated as a successful terminal state when the overall rollback status is determined.

BuildStreaM Rollback
~~~~~~~~~~~~~~~~~~~~

The BuildStreaM rollback path is automatically determined from metadata stored during the upgrade:

**Restore Path** (BuildStreaM was enabled in 2.1)

1. Validates backup files (quadlets, database dump) exist in the backup directory.
2. Runs Alembic database migration downgrade (from 2.2 schema back to 2.1 schema) while the 2.2 container is still running.
3. Stops BuildStreaM and PostgreSQL services.
4. Restores 2.1 quadlets, configuration files, and source directories from backup.
5. Restarts services in dependency order (PostgreSQL first, then BuildStreaM).
6. Reverts the GitLab upgrade commit via API and restores GitLab configuration (``gitlab.rb``, ``gitlab-secrets.json``) from backup.
7. Validates BuildStreaM API health, PostgreSQL connectivity, and GitLab readiness.

**Uninstall Path** (BuildStreaM was newly enabled during upgrade)

1. Stops and removes BuildStreaM and PostgreSQL containers and quadlets.
2. Removes all BuildStreaM NFS directories, watcher service, and automation framework.
3. Uninstalls GitLab packages and removes configuration directories from the GitLab host.
4. Sets ``enable_build_stream: false`` in ``build_stream_config.yml``.
5. Validates that containers, quadlets, and GitLab packages are fully removed.

.. note::
    If BuildStreaM was never upgraded (upgrade metadata file does not exist), the component is automatically marked as ``skipped``.

.. note::
    GitLab project rollback depends on the upgrade commit being the latest commit. If additional commits exist after the upgrade, automatic rollback will not revert GitLab content. Ensure that manual GitLab commit revert to the previous configuration files is performed.

Kubernetes and Telemetry Rollback (``k8s-telemetry``)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Kubernetes and Telemetry are rolled back as a single combined component. The etcd snapshot restore reverts the entire K8s cluster state including telemetry pods.

Rollback stages:

1. **Preflight checks** — Validates backups exist (etcd snapshot, K8s configs, etcd members), target rollback version packages are available in Pulp, and SSH connectivity to control plane nodes.
2. **Stop the cluster** — Cordons nodes and stops kubelet in correct order.
3. **Clean up stale MetalLB IPs** — Removes stale MetalLB IP assignments on all nodes.
4. **Restore etcd snapshot** — Restores the pre-upgrade etcd snapshot on all control plane nodes.
5. **Restore K8s configs** — Restores ``/etc/kubernetes/`` configs on all control plane nodes from backup.
6. **Remove kubelet feature gates** — Removes kubelet feature gates for compatibility with older versions.
7. **Update kubelet config parameters** — Updates kubelet config.yaml parameters to match cloud-init settings.
8. **Downgrade control plane packages** — Downgrades kubeadm, kubelet, and kubectl to the previous version and starts kubelet.
9. **Fix kube-vip split-brain** — Resolves VIP ownership after control plane restore.
10. **Downgrade worker packages** — Downgrades packages on workers and starts kubelet.
11. **Post-validation** — Validates node readiness (``kubectl get nodes``) and pod health.
12. **Restart network pods** — Clears stale BIRD/speaker processes.
13. **Restore Helm binary** — Restores the Helm binary to the rollback version.
14. **Clean up stale CSI VolumeAttachments** — Removes orphaned PowerScale/Isilon VolumeAttachments.
15. **Verify telemetry rollback** — Validates that all 2.1 telemetry pods (VictoriaMetrics, Kafka, iDRAC, LDMS, etc.) are healthy and that 2.2-only components (vector-ldms, vector-ome, victoria-logs, victoria-metrics-operator) have been removed by the etcd restore.
16. **Restore BSS boot params and cloud-init** — Restores pre-upgrade BSS/cloud-init configs from backup so nodes boot with the correct (old) images on next reboot.

.. warning::
   K8s node reboots will cause temporary cluster unavailability. Plan the rollback during a maintenance window.

Slurm Rollback
---------------

The Slurm rollback workflow restores the Slurm cluster configuration to the previously backed-up Omnia 2.1 state. During rollback, Omnia restores the cloud-init and Bare System Setup (BSS) configurations from the upgrade backup and applies the restored configuration by rebooting all Slurm and login nodes.

Rollback is intended primarily for recovery from a failed or partially completed upgrade. It restores the node provisioning and configuration state captured before the upgrade and validates the operational health of the Slurm cluster after recovery.

.. warning::

   - All Slurm control, compute, and login nodes are rebooted simultaneously during rollback. Ensure that no critical workloads or user sessions are active before starting the rollback process.
   - Existing Omnia 2.1 NFS mount configurations are preserved during rollback.
   - VAST mounts added after the upgrade are not restored during rollback. Any new mounts configured after the upgrade must be recreated manually after rollback, if required.
   - Rollback restores the configuration state captured during the backup process. Configuration changes made after the upgrade may be lost.

Rollback Workflow
~~~~~~~~~~~~~~~~

During rollback, Omnia performs the following operations:

#. Reads the backed-up ``software_config.json`` file to identify the Slurm deployment configuration that existed before the upgrade.
#. Reads the backed-up PXE mapping file to determine the Slurm and login nodes that must participate in the rollback process.
#. Restores cloud-init configurations from the Omnia 2.1 backup.
#. Restores BSS configurations from the Omnia 2.1 backup.
#. Applies the restored configuration to the following functional groups:

   - ``slurm_control_node``
   - ``slurm_node``
   - ``login_node``
   - ``login_compiler_node``

#. Initiates a coordinated reboot of all affected nodes.
#. Waits for nodes to return online after reboot.
#. Validates the operational status of Slurm services.
#. Generates a rollback status report summarizing the outcome for each node.

Configuration Restoration
~~~~~~~~~~~~~~~~~~~~~~~~~

The rollback process restores the pre-upgrade configuration captured during the upgrade backup phase.

The following configuration components are restored:

- Cloud-init configuration files.
- BSS configuration files.
- Slurm node role assignments.
- Node provisioning configuration.
- PXE-based node mapping information used by Omnia.

This restoration ensures that the Slurm infrastructure returns to the same configuration state that existed before the upgrade was initiated.

Node Restart and Recovery Validation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

After the backup configuration has been restored, Omnia performs a cluster-wide reboot to activate the recovered settings.

The reboot and validation workflow includes the following steps:

- A reboot command is issued to all Slurm and login nodes.
- Each node is allowed up to **1200 seconds** to complete the reboot process.
- Omnia continuously monitors node availability after the reboot.
- SSH connectivity is verified for every node.
- Each node is allowed up to **60 seconds** to restore SSH connectivity after boot completion.
- Once SSH connectivity is confirmed, Omnia validates Slurm functionality using the ``sinfo`` command.
- Validation checks are retried automatically to account for service startup delays.

Health Checks Performed
~~~~~~~~~~~~~~~~~~~~~~~

The following checks are executed during rollback validation:

**Pre-Reboot Checks**

- Verify that the node is reachable.
- Confirm SSH accessibility before initiating the reboot.

**Post-Reboot Checks**

- Verify successful reboot completion.
- Confirm restoration of SSH connectivity.
- Validate Slurm daemon availability.
- Verify successful execution of ``sinfo``.
- Confirm that the node can participate in normal cluster operations.

Rollback Status Report
~~~~~~~~~~~~~~~~~~~~~

At the end of the rollback process, Omnia generates a node-level status report showing the outcome for every Slurm and login node.

Nodes are grouped into the following categories:

* **Successful** - The node successfully completed all rollback operations.
* **Unreachable** - The node was not reachable before the reboot phase.
* **Reboot Failed** - The reboot command failed.
* **SSH Failure** - The node rebooted but did not restore SSH connectivity within the allowed timeout period.
* **Sinfo Failure** - SSH connectivity was restored successfully.

Post-Rollback Recommendations
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

After rollback completes successfully:

- Verify cluster health using ``sinfo`` and ``scontrol show nodes``.
- Confirm that all expected compute nodes are visible and in the appropriate state.
- Validate connectivity and accessibility of all required NFS mounts.
- Review any custom storage mounts that were added after the upgrade and recreate them if necessary.
- Run a small test workload to verify scheduler functionality.
- Review the rollback status report and investigate any nodes reported under the *Unreachable*, *Reboot Failed*, *SSH Failure*, or *Sinfo Failure* categories before returning the cluster to production use.

Post-Rollback
~~~~~~~~~~~~~~

After rollback completes:

1. The ``upgrade_manifest.yml`` is archived to ``/opt/omnia/.data/archive/`` so the next upgrade starts with a fresh manifest.

2. **Kubernetes artifacts archival** — If the k8s-telemetry rollback completed successfully, all upgrade and rollback artifacts are automatically archived to a timestamped directory on the NFS share (``<nfs_mount>/upgrade/archive/<rollback_id>_<timestamp>/``). This includes:

   * ``upgrade_status.yml`` — Per-node upgrade step tracking
   * ``rollback_status.yml`` — Per-node rollback step tracking
   * ``backup/`` — etcd snapshot, K8s configs, and addon backups
   * ``telemetry/`` — Telemetry backups
   * ``logs/`` — Upgrade and rollback execution logs from the OIM container

   The archival process also cleans up:

   * Lock files on NFS (``upgrade.lock``, ``rollback.lock``)
   * ``omnia-upgrade.repo`` from all K8s nodes

   This ensures a clean slate for the next upgrade run while preserving all evidence for root cause analysis.

3. The rollback summary displays the final component statuses.

Post-Rollback Verification
----------------------------

After the rollback completes, verify the following:

1. Check the rollback summary displayed at the end of the playbook run.
2. Verify the rollback manifest: ::

    cat /opt/omnia/.data/rollback_manifest.yml

3. Confirm all component statuses show ``completed`` or ``skipped``.
4. Validate cluster health:

    * Kubernetes cluster: ``kubectl get nodes``
    * Slurm cluster: ``sinfo``
    * Telemetry: Verify metrics are flowing

5. Confirm the ``upgrade_manifest.yml`` has been archived: ::

    ls /opt/omnia/.data/archive/

For troubleshooting rollback issues, see `Upgrade and Rollback Troubleshooting <troubleshootingguide.html>`_.
