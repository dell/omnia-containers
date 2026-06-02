Rollback Omnia
====================

Omnia provides a rollback mechanism to revert an upgrade and return the cluster to the previous version. Rollback processes components in **reverse order** compared to upgrade, with manifest tracking for idempotent reruns.

.. important::
    * Rollback must be initiated from within the ``omnia_core`` container.
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

Running the Rollback
~~~~~~~~~~~~~~~~~~~~~

1. SSH into the OIM node and enter the ``omnia_core`` container: ::

    ssh omnia_core

2. Run the rollback playbook: ::

    cd /omnia/rollback
    ansible-playbook rollback.yml

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
* **rollback_status** — Overall status: ``in-progress``, ``completed``, or ``partial``.
* **component_status** — Per-component status: ``pending``, ``in-progress``, ``completed``, ``skipped``, or ``failed``.

On rerun, already-completed components are automatically skipped.

BuildStreaM Terminal Gate (Rollback)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If BuildStreaM was enabled during the upgrade, the downstream components (``slurm``, ``k8s-telemetry``) were never upgraded by Omnia — they are managed by the GitLab CI/CD pipeline. In this scenario, these components are **automatically skipped during rollback** because there is nothing to roll back. Only ``build_stream`` and ``oim`` are actually rolled back.

Components that are skipped are recorded as ``skipped`` in the rollback manifest, which is treated as a successful terminal state when the overall rollback status is determined.

Force Rollback
~~~~~~~~~~~~~~~

To force a rollback after a successful upgrade: ::

    cd /omnia/rollback
    ansible-playbook rollback.yml -e force_rollback=true

BuildStreaM Rollback
---------------------

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

Kubernetes and Telemetry Rollback (``k8s-telemetry``)
------------------------------------------------------

Kubernetes and Telemetry are rolled back as a single combined component. The etcd snapshot restore reverts the entire K8s cluster state including telemetry pods.

Rollback stages:

1. **Preflight checks** — Validates backups exist (etcd snapshot, K8s configs, etcd members), target rollback version packages are available in Pulp, and SSH connectivity to control plane nodes.
2. **Stop the cluster** — Cordons nodes and stops kubelet in correct order.
3. **Clean up stale MetalLB IPs** — Removes stale MetalLB IP assignments on all nodes.
4. **Restore etcd snapshot** — Restores the pre-upgrade etcd snapshot on all control plane nodes.
5. **Restore K8s configs** — Restores ``/etc/kubernetes/`` configs on all control plane nodes from backup.
6. **Downgrade control plane packages** — Downgrades kubeadm, kubelet, and kubectl to the previous version and starts kubelet.
7. **Fix kube-vip split-brain** — Resolves VIP ownership after control plane restore.
8. **Downgrade worker packages** — Downgrades packages on workers and starts kubelet.
9. **Post-validation** — Validates node readiness (``kubectl get nodes``) and pod health.
10. **Restart network pods** — Clears stale BIRD/speaker processes.
11. **Restore Helm binary** — Restores the Helm binary to the rollback version.
12. **Clean up stale CSI VolumeAttachments** — Removes orphaned PowerScale/Isilon VolumeAttachments.
13. **Verify telemetry rollback** — Validates that all 2.1 telemetry pods (VictoriaMetrics, Kafka, iDRAC, LDMS, etc.) are healthy and that 2.2-only components (vector-ldms, vector-ome, victoria-logs, victoria-metrics-operator) have been removed by the etcd restore.
14. **Restore BSS boot params and cloud-init** — Restores pre-upgrade BSS/cloud-init configs from backup so nodes boot with the correct (old) images on next reboot.

.. warning::
   K8s node reboots will cause temporary cluster unavailability. Plan the rollback during a maintenance window.

Slurm Rollback
--------------

The Slurm rollback restores cloud-init and BSS configurations from the 2.1 backup and reboots all Slurm and login nodes.

.. warning::
   - All Slurm and login nodes reboot simultaneously. Ensure no critical jobs are running.
   - Omnia 2.1 NFS mount points are preserved. New VAST mounts will not be supported during upgrade. Any mounts added post upgrade are not retained after a rollback.

1. Reads ``software_config.json`` and PXE mapping file from the backup directory to identify Slurm and login nodes.
2. Restores cloud-init and BSS configurations for each Slurm functional group from backup.
3. Reboots all Slurm and login nodes simultaneously with a 600-second timeout per node.
4. Waits for SSH connectivity to restore on each node (up to 60 seconds).
5. Validates Slurm services using ``sinfo`` with retries on each node.
6. Generates a node status report with the following categories:

   * **Successful** — Reboot complete, SSH active, ``sinfo`` responding
   * **Unreachable** — Node was not reachable before reboot
   * **Reboot Failed** — Reboot command failed
   * **SSH Failure** — Node did not reconnect after reboot
   * **Sinfo Failure** — Slurm services did not respond after reboot

Post-Rollback
~~~~~~~~~~~~~~

After rollback completes:

1. The ``upgrade_manifest.yml`` is archived to ``/opt/omnia/.data/archive/`` so the next upgrade starts with a fresh manifest.

2. The rollback summary displays the final component statuses.

3. Complete the core container rollback by running on the OIM host (outside the container): ::

    sudo ./omnia.sh --rollback

   The ``omnia.sh --rollback`` command performs the following:

   * Reads ``oim_metadata.yml`` to determine the previous version and backup directory
   * Validates the target container image (``omnia_core:<previous_tag>``) is available locally
   * Validates the backup directory exists and contains required files
   * Requests user confirmation before proceeding
   * Stops the current ``omnia_core`` container and swaps it to the previous version image
   * Restores input files, configuration, and metadata from the backup directory
   * Finalizes the ``rollback_manifest.yml`` with ``rollback_status: completed``

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
