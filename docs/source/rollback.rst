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
      - ``telemetry``
      - Rollback Telemetry components
    * - 3
      - ``k8s``
      - Rollback Kubernetes cluster
    * - 4
      - ``build_stream``
      - Rollback BuildStream upgrade / enablement
    * - 5
      - ``oim``
      - Rollback OIM (includes OpenCHAMI) — rolled back last

.. note::
    There is no separate ``local_repo``, ``build_image``, or ``provision`` rollback step. The packages and images produced during upgrade do not require active reversion, and the Cloud-Init and BSS boot configuration is restored to the previous version **within** the Slurm and Kubernetes rollbacks for the affected nodes.

Rollback Workflow
------------------

Running the Rollback
~~~~~~~~~~~~~~~~~~~~~

1. SSH into the OIM node and enter the ``omnia_core`` container: ::

    ssh omnia_core

2. Run the rollback playbook: ::

    cd /omnia/rollback
    ansible-playbook rollback.yml

Pre-flight Guards
~~~~~~~~~~~~~~~~~~

The rollback orchestrator performs the following read-only checks before any state mutation:

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

BuildStream Terminal Gate (Rollback)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If BuildStream was enabled during the upgrade, the downstream components (``slurm``, ``telemetry``, ``k8s``) were never upgraded by Omnia — they are managed by the GitLab CI/CD pipeline. In this scenario, these components are **automatically skipped during rollback** because there is nothing to roll back. Only ``build_stream`` and ``oim`` are actually rolled back.

Components that are skipped are recorded as ``skipped`` in the rollback manifest, which is treated as a successful terminal state when the overall rollback status is determined.

Force Rollback
~~~~~~~~~~~~~~~

To force a rollback after a successful upgrade: ::

    cd /omnia/rollback
    ansible-playbook rollback.yml -e force_rollback=true

Slurm Rollback
--------------

The Slurm rollback restores BSS and cloud-init configurations from the 2.1.0 backup and reboots all Slurm and login nodes to apply them.

Pre-Rollback Warnings
~~~~~~~~~~~~~~~~~~~~~

Before the Slurm rollback begins, the playbook displays the following warnings:

1. **NODE REBOOT** — All Slurm/login nodes will reboot.

2. **NFS MOUNTS** — Omnia 2.1 mount points are preserved. Do not modify during rollback.

3. **ROLLBACK SCOPE** — New NFS mounts (e.g., VAST) added during upgrade will NOT be retained on rollback.

Slurm Rollback Workflow
~~~~~~~~~~~~~~~~~~~~~~~~

**Phase 1: Cloud-Init and BSS Restoration**

* Reads ``software_config.json`` from the backup directory to verify Slurm was configured in 2.1
* Reads ``provision_config.yml`` and PXE mapping file from the backup directory to identify Slurm and login nodes
* Restores cloud-init and BSS configurations for each functional group from the backed-up OpenCHAMI workdir
* Applies the ``update_cloud_init_bss`` utility role to push restored configurations

**Phase 2: Simultaneous Node Reboot**

All Slurm and login nodes reboot simultaneously to minimize cluster downtime. The rollback orchestrator:

* Initiates reboot commands in parallel across all nodes
* Monitors reboot progress with a 600-second timeout per node
* Waits for SSH connectivity to restore on all nodes (up to 60 seconds per node)
* Validates Slurm services are responding after reboot

For each Slurm/login node, the rollback performs the following checks in sequence:

1. **SSH Connectivity Check** — Verifies each node is reachable before proceeding

2. **Reboot** — Initiates node reboot with a 600-second timeout

3. **Wait for SSH** — Waits up to 60 seconds for SSH to become available

4. **Slurm Service Validation** — Runs ``sinfo`` with 5 retries (15-second delay) to confirm Slurm services are responding

.. warning::
   Simultaneous reboot of all Slurm nodes will cause temporary cluster unavailability. Plan the rollback during a maintenance window when no critical jobs are running.

**Phase 3: Node Status Reporting**

After all nodes complete rebooting, the playbook generates a comprehensive status report:

* **Successful Nodes** — Nodes that completed reboot, SSH is active, and ``sinfo`` is responding
* **Unreachable Nodes** — Nodes that failed SSH connectivity checks before reboot
* **Reboot Failed Nodes** — Nodes where the reboot command failed
* **SSH Failures** — Nodes that did not reconnect after reboot
* **Sinfo Failures** — Nodes where Slurm services did not respond

Post-Rollback
~~~~~~~~~~~~~~

After rollback completes:

1. The ``upgrade_manifest.yml`` is archived to ``/opt/omnia/.data/archive/`` so the next upgrade starts with a fresh manifest.

2. The rollback summary displays the final component statuses.

3. Complete the core container rollback by running on the OIM host: ::

    sudo ./omnia.sh --rollback

The ``omnia.sh --rollback`` command performs the following:

* Validates root privileges
* Reads ``oim_metadata.yml`` to get ``upgrade_backup_dir`` and ``omnia_previous_version``
* Aborts if ``omnia_version`` equals ``omnia_previous_version`` (already rolled back)
* Derives rollback target from ``omnia_previous_version``
* Validates target image (``omnia_core:<old_tag>``) exists locally
* Validates backup directory exists and contains required files
* Validates backup metadata version matches expected
* Requests user confirmation
* Same-tag rollback → restart only
* Different-tag rollback:
    * Stops current container (30s graceful)
    * Updates quadlet ``Image=`` to old tag
    * Runs ``systemctl daemon-reload``
    * Starts old container
    * Waits for healthy (60s)
* Validates backup directory structure
* Restores files from backup
* Restores ``omnia_version`` in ``oim_metadata.yml`` from backup
* Finalizes ``rollback_manifest.yml`` (``rollback_status: completed``)
* Verifies restored version matches expected
* Logs rollback completion

.. note::
    ``omnia.sh --rollback`` does not touch ``upgrade_manifest.yml`` — archival is handled by ``rollback.yml`` finalize to prevent duplicate archival operations.

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
