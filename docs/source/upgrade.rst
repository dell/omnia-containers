Upgrading Omnia
================

Omnia supports in-place upgrades from version 2.1.0.0 to 2.2.0.0. The upgrade process is a three-phase workflow: **core container upgrade**, **prepare**, and **execute**. Each component is upgraded in a defined order with lock-based safety and manifest tracking for idempotent reruns.

.. important::
    * Upgrades must be initiated from the OIM host using ``omnia.sh --upgrade`` before entering the ``omnia_core`` container.
    * The upgrade orchestrator must be invoked from the parent directory containing ``upgrade/``, ``rollback/``, and ``playbooks/`` folders.
    * Ensure a full backup of the OIM node is taken before starting the upgrade.

Supported Upgrade Paths
------------------------

+-------------------+-------------------+
| Source Version    | Target Version    |
+===================+===================+
| Omnia 2.1.0.0     | Omnia 2.2.0.0     |
+-------------------+-------------------+

.. note:: Direct upgrades across multiple major versions (e.g., 2.0 → 2.2) are not supported. Upgrade one version at a time.

Prerequisites
--------------

Before starting the upgrade, ensure the following prerequisites are met:

1. The OIM node is running and accessible.
2. The ``omnia_core`` container is running.
3. All compute nodes are in a healthy state.
4. A backup of critical data has been taken (NFS shares, credentials, configuration files).
5. No other upgrade or rollback is currently in progress.
6. ``oim_metadata.yml`` at ``/opt/omnia/.data/oim_metadata.yml`` is populated with the correct version information.
7. Target container image (``omnia_core:2.2``) is available locally on the OIM host.

Upgrade Workflow
-----------------

Phase 0: Core Container Upgrade (OIM Host)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The upgrade begins on the OIM host outside the ``omnia_core`` container:

1. Run the core container upgrade command: ::

    sudo ./omnia.sh --upgrade

2. The script performs the following:

    * Detects current version from ``oim_metadata.yml``
    * Shows available upgrade targets
    * Validates version and image availability
    * Requests user approval
    * Creates backup of configs, metadata, and input files
    * Swaps or restarts the ``omnia_core`` container to the 2.2 image
    * Creates upgrade guard lock at ``/opt/omnia/.data/upgrade_in_progress.lock``
    * Seeds new input defaults
    * Displays post-upgrade instructions

3. After the container swap completes, SSH into the new ``omnia_core`` container to proceed with input preparation and component upgrades.

Upgrade Component Order
------------------------

The upgrade orchestrator processes components in the following fixed order:

.. list-table::
    :header-rows: 1
    :widths: 10 30 60

    * - Order
      - Component Tag
      - Description
    * - 1
      - ``oim``
      - Omnia Infrastructure Manager (includes OpenCHAMI)
    * - 2
      - ``build_stream``
      - BuildStream enablement / upgrade (terminal gate)
    * - 3
      - ``local_repo``
      - Local repository staging
    * - 4
      - ``build_image``
      - Compute image rebuild
    * - 5
      - ``provision``
      - Cloud-Init and BSS configuration generation
    * - 6
      - ``k8s``
      - Kubernetes cluster upgrade
    * - 7
      - ``telemetry``
      - Telemetry component upgrade
    * - 8
      - ``slurm``
      - Slurm cluster upgrade

Tag Dependencies
-----------------

The upgrade orchestrator enforces the following tag dependencies automatically:

.. list-table::
    :header-rows: 1
    :widths: 20 30 50

    * - Component Tag
      - Depends On
      - Rationale
    * - ``build_stream``
      - ``oim``
      - Requires BuildStream container at target version
    * - ``build_image``
      - ``oim``
      - Requires BuildStream container at target version
    * - ``provision``
      - ``oim``, ``build_image``
      - Requires OpenCHAMI and built images
    * - ``k8s``
      - ``oim``
      - Requires OpenCHAMI services
    * - ``telemetry``
      - ``oim``, ``k8s``
      - Requires OpenCHAMI and Kubernetes cluster
    * - ``slurm``
      - ``oim``, ``k8s``
      - Requires OpenCHAMI and Kubernetes cluster

If a dependency is not met, the upgrade will fail with a descriptive error message.

Pre-Flight Guard Ordering
--------------------------

The upgrade orchestrator follows strict validate-before-mutate ordering (C-29 constraint):

1. **Read-only guards execute first** — All validation checks run before any state mutation
2. **Lock creation occurs only after guards pass** — Prevents orphaned lock files if guards abort
3. **Manifest initialization** — Only after all guards have passed

This ensures that an early abort never leaves the system in a locked state.

Terminal Cleanup Play
---------------------

A guaranteed terminal cleanup play (``tags: always``) runs as the last play in the upgrade playbook (C-30 constraint). This provides defense-in-depth against sub-playbook fatal errors that might skip the finalize play, ensuring the upgrade lock is always removed.

Upgrade Workflow
-----------------

Phase 1: Prepare Upgrade
~~~~~~~~~~~~~~~~~~~~~~~~~~

The ``prepare_upgrade.yml`` playbook transforms input files from the source version format to the target version format, restores credentials from backup, and presents a summary for user review.

1. SSH into the OIM node and enter the ``omnia_core`` container: ::

    ssh omnia_core

2. Run the prepare upgrade playbook: ::

    cd /omnia
    ansible-playbook upgrade/prepare_upgrade.yml

3. Review the output summary. The playbook identifies:

    * **Automatically migrated files** — copied as-is (e.g., ``provision_config.yml``, ``omnia_config.yml``).
    * **Files requiring review** — new parameters added in the target version (e.g., ``network_spec.yml``, ``telemetry_config.yml``).

4. Update any new or changed parameters in ``/opt/omnia/input/project_default/`` as needed.

Phase 2: Execute Upgrade
~~~~~~~~~~~~~~~~~~~~~~~~~~

Run the full upgrade: ::

    ansible-playbook upgrade/upgrade.yml

Lock Management
~~~~~~~~~~~~~~~~

The upgrade orchestrator uses lock files to prevent concurrent operations:

* ``/opt/omnia/.data/upgrade_in_progress.lock`` — Created at the start of the upgrade. Removed only on successful completion.
* ``/opt/omnia/.data/rollback_in_progress.lock`` — If this lock exists, the upgrade aborts with an error. A rollback must complete (or the lock must be manually removed) before an upgrade can proceed.

.. note::
    The ``omnia.sh --upgrade`` wrapper may pre-create the upgrade lock. The playbook detects this and proceeds normally without failing.

Manifest Tracking
~~~~~~~~~~~~~~~~~~

The upgrade state is tracked in ``/opt/omnia/.data/upgrade_manifest.yml``. This manifest records:

* **upgrade_id** — Unique identifier for this upgrade run.
* **source_version** — The version being upgraded from (derived from ``oim_metadata.yml``).
* **target_version** — The version being upgraded to.
* **upgrade_status** — Overall status: ``in-progress``, ``completed``, or ``partial``.
* **component_status** — Per-component status: ``pending``, ``in-progress``, ``completed``, ``skipped``, or ``failed``.

On rerun, already-completed components are automatically skipped. This ensures idempotent execution — you can safely rerun the upgrade after fixing a failed component.

BuildStream Terminal Gate
~~~~~~~~~~~~~~~~~~~~~~~~~~

When ``enable_build_stream=true`` in ``build_stream_config.yml``, the BuildStream terminal gate activates. The upgrade playbook determines the BuildStream path based on the state in 2.1:

**PATH A: BuildStream was ENABLED in 2.1 (upgrade path)**

* Upgrade BuildStream container image (quadlet update)
* PostgreSQL data migration (pg_dump → restore to new schema)
* Update GitLab configuration (URLs, runner tokens, registry)
* Validate BuildStream container + GitLab healthy

**PATH B: BuildStream was DISABLED in 2.1, ENABLED in 2.2 (fresh install)**

* NFS share cleanup: remove stale K8s and Slurm NFS share data
* Fresh install: PostgreSQL container (new instance)
* Fresh install: BuildStream container
* Fresh install: GitLab container + runner registration
* Validate all three containers healthy

.. note::
    NFS share cleanup is **not automatic** — the playbook displays guidance and prompts the operator to confirm manual cleanup before proceeding. The playbook verifies that NFS share directories are empty or absent after operator confirmation.

After the ``build_stream`` component completes, the following downstream components are automatically **skipped**:

* ``local_repo``
* ``build_image``
* ``provision``
* ``k8s``
* ``telemetry``
* ``slurm``

These components are managed by the GitLab CI/CD pipeline instead. The user must trigger the GitLab pipeline manually after upgrade completes. The GitLab pipeline always performs a fresh install — no incremental/delta builds are supported.

.. note::
    When ``enable_build_stream=false``, the ``build_stream`` component is marked ``skipped`` in the manifest instead of being left as ``pending``.

Force Rerun
~~~~~~~~~~~~~

After a successful upgrade, rerunning the upgrade playbook is blocked by default. To force a new upgrade cycle: ::

    ansible-playbook upgrade/upgrade.yml -e force_upgrade=true

Post-Upgrade Verification
---------------------------

After the upgrade completes, verify the following:

1. Check the upgrade summary displayed at the end of the playbook run.
2. Verify the upgrade manifest: ::

    cat /opt/omnia/.data/upgrade_manifest.yml

3. Confirm all component statuses show ``completed`` or ``skipped``.
4. Validate cluster health:

    * Kubernetes cluster: ``kubectl get nodes``
    * Slurm cluster: ``sinfo``
    * Telemetry: Verify metrics are being collected

5. If BuildStream is enabled, trigger the GitLab pipeline for downstream components.

For troubleshooting upgrade issues, see `Upgrade and Rollback Troubleshooting <troubleshootingguide.html>`_.
