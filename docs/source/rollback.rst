Rolling Back Omnia
====================

Omnia provides a rollback mechanism to revert an upgrade and return the cluster to the previous version. Rollback processes components in **reverse order** compared to upgrade and supports tag-based selective rollback with manifest tracking for idempotent reruns.

.. important::
    * Rollback must be initiated from within the ``omnia_core`` container.
    * Rollback is intended for recovering from a **failed or partial upgrade**. Rolling back a fully completed upgrade is blocked by default and not recommended.
    * The rollback orchestrator must be invoked from the parent directory containing ``upgrade/``, ``rollback/``, and ``playbooks/`` folders.

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
      - Component Tag
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
      - ``provision``
      - Rollback Cloud-Init and BSS configuration
    * - 5
      - ``build_stream``
      - Rollback BuildStream upgrade / enablement
    * - 6
      - ``oim``
      - Rollback OIM (includes OpenCHAMI) — rolled back last

Rollback Workflow
------------------

Running the Rollback
~~~~~~~~~~~~~~~~~~~~~

1. SSH into the OIM node and enter the ``omnia_core`` container: ::

    ssh omnia_core

2. Run the rollback playbook: ::

    cd /omnia
    ansible-playbook rollback/rollback.yml

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

If BuildStream was enabled during the upgrade and the upgrade manifest shows that downstream components (``slurm``, ``telemetry``, ``k8s``, ``provision``) were ``skipped`` during upgrade (due to the terminal gate), the same components are **automatically skipped during rollback** — they were never upgraded, so there is nothing to roll back.

Each rollback sub-flow immediately writes ``component_status: skipped`` to ``rollback_manifest.yml`` before invoking ``end_play``. Only ``build_stream`` and ``oim`` are actually rolled back in this scenario.

The finalization play treats ``skipped`` as a valid terminal state alongside ``completed`` when determining ``rollback_status``.

Force Rollback
~~~~~~~~~~~~~~~

To force a rollback after a successful upgrade or a previously completed rollback: ::

    ansible-playbook rollback/rollback.yml -e force_rollback=true

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
