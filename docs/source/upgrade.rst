Upgrade Omnia
================

Omnia supports in-place upgrades from version 2.1.0.0 to 2.2.0.0. The upgrade process is a three-phase workflow: **core container upgrade**, **prepare**, and **execute**. Each component is upgraded in a defined order with lock-based safety and manifest tracking for idempotent reruns.

.. important::
    * Upgrades must be initiated from the OIM host using ``omnia.sh --upgrade`` before entering the ``omnia_core`` container.
    * The upgrade orchestrator must be invoked from the parent directory containing ``upgrade/`` folders.

Supported Upgrade Paths
~~~~~~~~~~~~~~~~~~~~~~~

+-------------------+-------------------+
| Source Version    | Target Version    |
+===================+===================+
| Omnia 2.1.0.0     | Omnia 2.2.0.0     |
+-------------------+-------------------+

.. note:: Direct upgrades across multiple major versions (e.g., 2.0 → 2.2) are not supported. Upgrade one version at a time.

Prerequisites
---------------

Before starting the upgrade, ensure the following prerequisites are met:

1. The OIM node is running and accessible.
2. The ``omnia_core`` container is running and the cluster is currently on Omnia 2.1.0.0.
3. All compute nodes are in a healthy state.
4. No other upgrade or rollback is currently in progress.
5. ``oim_metadata.yml`` at ``/opt/omnia/.data/oim_metadata.yml`` contains the correct current version information.
6. The target Omnia 2.2.0.0 core container image (``omnia_core:2.2``) is available locally on the OIM host. If it is not already available, build it as described in :ref:`build-core-container`.
7. **aarch64 clusters only:** If the PXE mapping file contains aarch64 functional groups, an inventory file with an ``[admin_aarch64]`` group is required. This group must contain exactly one ARM admin node. See :ref:`aarch64-inventory` for details.

Pre-Flight Checks
^^^^^^^^^^^^^^^^

Before initiating the upgrade, perform the following pre-flight checks to ensure the system is ready for upgrade:

1. **Verify OIM node health** — Ensure the OIM node is responsive and has sufficient resources (CPU, memory, disk space) for the upgrade process
2. **Check network connectivity** — Verify all cluster nodes can reach the OIM node and each other through the admin network
3. **Validate NFS shares** — Ensure all NFS shares defined in ``storage_config.yml`` are accessible from the OIM and all cluster nodes
4. **Check disk space** — Verify sufficient disk space is available on the OIM node for backups and container images (minimum 50 GB free recommended)
5. **Verify time synchronization** — Ensure NTP is configured and time is synchronized across all cluster nodes
6. **Check running services** — Verify all critical services (OpenCHAMI, PostgreSQL, Kubernetes if applicable) are running and healthy
7. **Review logs** — Check recent logs in ``/opt/omnia/log/`` for any errors or warnings that might indicate issues
8. **Validate configuration files** — Ensure all input configuration files in ``/opt/omnia/input/project_default/`` are syntactically correct and contain valid values

.. _build-core-container:

Build the Omnia 2.2.0.0 Core Container Image
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The upgrade swaps the running ``omnia_core`` container to the 2.2.0.0 image. This image must be present on the OIM host before you run ``omnia.sh --upgrade``. To build it:

1. On the OIM host, clone the Omnia artifactory repository on the ``omnia-container-v2.2.0.0`` branch: ::

    git clone -b omnia-container-v2.2.0.0 https://github.com/dell/omnia-artifactory.git

2. Build the core container image using the build script provided in the repository: ::

    cd omnia-artifactory
    ./build_images.sh core core_tag=2.2 omnia_branch=v2.2.0.0

3. Confirm the image is available locally before proceeding: ::

    podman images | grep omnia_core

.. note::
    Ensure the OIM host has stable internet connectivity and sufficient disk space while building the container image.

Upgrade Workflow
----------------

Phase 0: Core Container Upgrade (OIM Host)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The upgrade begins on the OIM host outside the ``omnia_core`` container.

.. important::
    **Use the Omnia 2.2.0.0 omnia.sh script for upgrade operations**
    
    The ``omnia.sh`` script from Omnia 2.1.0.0 does **not** support correct upgrade or rollback operations. You must download and use the Omnia 2.2.0.0 version of ``omnia.sh`` to perform upgrades and rollbacks.
    
    Do **not** attempt to run ``./omnia.sh --upgrade`` or ``./omnia.sh --rollback`` using the 2.1.0.0 script.

Download the Omnia 2.2.0.0 omnia.sh Script
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Before starting the upgrade, download the correct version of the ``omnia.sh`` script:

1. Download the Omnia 2.2.0.0 ``omnia.sh`` script from the Omnia repository: ::

     wget https://raw.githubusercontent.com/dell/omnia/refs/tags/v2.2.0.0/omnia.sh

2. Set executable permissions: ::

    chmod +x omnia.sh

3. Verify the script version (optional): ::

    ./omnia.sh --version

1. Run the core container upgrade command: ::

    sudo ./omnia.sh --upgrade

2. The script performs the following:

    * Detects current version from ``oim_metadata.yml``
    * Shows available upgrade targets
    * Validates version and image availability
    * Requests user approval
    * Creates backup of:
        - Input configuration files (``/opt/omnia/input/``)
        - Metadata files (``oim_metadata.yml``)
        - OpenCHAMI data (PostgreSQL database dump, container environment variables)
        - OpenCHAMI quadlet files (``/etc/containers/systemd/``)
        - OpenCHAMI configuration files (``/etc/openchami/``)
        - Cloud-init data (groups, defaults, hostname mappings)
    * Swaps or restarts the ``omnia_core`` container to the 2.2 image
    * Creates upgrade guard lock at ``/opt/omnia/.data/upgrade_in_progress.lock``
    * Seeds new input defaults
    * Displays post-upgrade instructions

3. After the container swap completes, SSH into the new ``omnia_core`` container to proceed with input preparation and component upgrades.

Upgrade Component Order
^^^^^^^^^^^^^^^^^^^^^^

The upgrade orchestrator processes components in the following fixed order:

.. list-table::
    :header-rows: 1
    :widths: 10 30 60

    * - Order
      - Component
      - Description
    * - 1
      - ``oim``
      - Omnia Infrastructure Manager (includes OpenCHAMI)
    * - 2
      - ``build_stream``
      - BuildStreaM enablement / upgrade (terminal gate)
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

Safety Mechanisms
^^^^^^^^^^^^^^^^^^

The upgrade is designed to be safe to rerun and to fail cleanly:

* **Validation before changes** — All validation checks (version, locks, existing upgrade state) run before any change is made to the cluster. If a check fails, the upgrade stops without leaving the system in a locked state.
* **Automatic lock cleanup** — If a component fails partway, the upgrade lock is still released at the end of the run so you can investigate and rerun without manually clearing locks.
* **Idempotent reruns** — Already-completed components are skipped automatically when you rerun the upgrade, so only pending or failed components are processed.

Phase 1: Prepare Upgrade
~~~~~~~~~~~~~~~~~~~~~~~~

The ``prepare_upgrade.yml`` playbook transforms input files from the source version format to the target version format, restores credentials from backup, and presents a summary for user review.

1. SSH into the OIM node and enter the ``omnia_core`` container: ::

    ssh omnia_core

2. Run the prepare upgrade playbook: ::

    cd /omnia/upgrade
    ansible-playbook prepare_upgrade.yml

3. Review the output summary. The playbook identifies:

    * **Automatically migrated files** — copied as-is (e.g., ``provision_config.yml``, ``omnia_config.yml``).
    * **Files requiring review** — new parameters added in the target version (e.g., ``network_spec.yml``, ``telemetry_config.yml``).

4. Update any new or changed parameters in ``/opt/omnia/input/project_default/`` as needed.

.. warning::
   **Do not re-run prepare_upgrade.yml after making input changes**

   Re-running ``prepare_upgrade.yml`` after you have modified input files will overwrite your changes and revert to the original 2.1 inputs. Only run ``prepare_upgrade.yml`` once at the beginning of the upgrade process. After reviewing and updating the migrated inputs, proceed directly to the execute phase.

Lock Management
^^^^^^^^^^^^^^^^

The upgrade orchestrator uses lock files to prevent concurrent operations:

* ``/opt/omnia/.data/upgrade_in_progress.lock`` — Created at the start of the upgrade. Removed only on successful completion.
* ``/opt/omnia/.data/rollback_in_progress.lock`` — If this lock exists, the upgrade aborts with an error. A rollback must complete (or the lock must be manually removed) before an upgrade can proceed.

.. note::
    The ``omnia.sh --upgrade`` wrapper may pre-create the upgrade lock. The playbook detects this and proceeds normally without failing.

Manifest Tracking
^^^^^^^^^^^^^^^^

The upgrade state is tracked in ``/opt/omnia/.data/upgrade_manifest.yml``. This manifest records:

* **upgrade_id** — Unique identifier for this upgrade run.
* **source_version** — The version being upgraded from (derived from ``oim_metadata.yml``).
* **target_version** — The version being upgraded to.
* **upgrade_status** — Overall status: ``in-progress`` or ``completed``.
* **component_status** — Per-component status: ``pending``, ``in-progress``, ``completed``, ``skipped``, or ``failed``.

On rerun, already-completed components are automatically skipped. This ensures idempotent execution — you can safely rerun the upgrade after fixing a failed component.

.. _buildstream-terminal-gate:

BuildStreaM Terminal Gate
^^^^^^^^^^^^^^^^^^^^^^^^^^

When ``enable_build_stream=true`` in ``build_stream_config.yml``, the BuildStreaM terminal gate activates. The upgrade playbook determines the BuildStreaM path based on the state in 2.1:

**PATH A: BuildStreaM was ENABLED in 2.1 (upgrade path)**

* Upgrade BuildStreaM container image (quadlet update)
* PostgreSQL data migration (pg_dump → restore to new schema)
* Update GitLab configuration (URLs, runner tokens, registry)
* Validate BuildStreaM container + GitLab healthy

**PATH B: BuildStreaM was DISABLED in 2.1, ENABLED in 2.2 (fresh install)**

* NFS share cleanup: remove stale K8s and Slurm NFS share data
* Fresh install: PostgreSQL container (new instance)
* Fresh install: BuildStreaM container
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

Kubernetes Upgrade
~~~~~~~~~~~~~~~~~~

.. note::
   The Kubernetes upgrade is automatically executed as part of :ref:`phase-2-execute-upgrade`. The upgrade orchestrator processes the ``k8s`` component in the correct order (after provision and before telemetry) and handles all validation and status tracking automatically.

Kubernetes upgrade provides a robust, resumable, and transparent upgrade process for Kubernetes clusters.

Pre-Upgrade Checklist for Kubernetes Clusters
"""""""""""""""""""""""""""""""""""""""""""

Before initiating the Kubernetes upgrade, verify the following conditions are met:

1. **All nodes Ready** — All nodes in Ready state, no NotReady
2. **All kube-system pods Running** — No CrashLoopBackOff, Pending, or Error pods
3. **etcd cluster healthy** — Cluster should report all members healthy
4. **All PVCs Bound** — No PVCs in Lost or Pending state
5. **No PVs in Failed state** — No PVs in Failed state
6. **All nodes from PXE mapping are part of the cluster** — Every node defined in ``pxe_mapping_file.csv`` under ``service_kube_control_plane_*`` and ``service_kube_node_*`` must appear in ``kubectl get nodes``
7. **NFS mount accessible** — The shared NFS storage mount must be reachable from all cluster nodes
8. **API server reachable via kube_vip** — ``kubectl cluster-info`` works through the HA virtual IP
9. **.cluster_initialized marker exists on all control planes** — ``/etc/kubernetes/.cluster_initialized`` must be present on every CP node (confirms provisioning completed)

Kubernetes Upgrade Workflow
""""""""""""""""""""""""

The K8s upgrade follows this sequence:

1. **Pre-checks** — Validates ``service_k8s`` configuration and prerequisites
2. **Version Detection** — Detects current K8s version across all nodes
3. **Hop Chain Calculation** — Determines hop chain for upgrade
4. **Backup Phase** — Backs up etcd and K8s configurations
5. **Repository Setup** — Configures package repositories on all nodes
6. **First Control Plane Upgrade** — Upgrades the first control plane node
7. **BSS/Cloud-init Update for First Control Plane** — Updates boot configuration and reboots first control plane
8. **Additional Control Planes Upgrade** — Upgrades remaining control plane nodes sequentially
9. **BSS/Cloud-init Update for Additional Control Planes** — Updates boot configuration (no reboot)
10. **Addon Upgrade** — Upgrades Calico, MetalLB, Helm, and PowerScale CSI driver (if PowerScale is configured)
11. **First Worker Upgrade** — Upgrades the first worker node
12. **BSS/Cloud-init Update for All Workers** — Updates boot configuration for all workers and reboots first worker
13. **Remaining Workers Upgrade** — Upgrades remaining worker nodes sequentially
14. **Post-Validation** — Comprehensive cluster health checks
15. **Completion** — Updates manifest and displays summary

.. important::
   * BSS (Boot Script Service) and cloud-init configurations are updated for **ALL** nodes in their respective groups (control planes and workers)
   * Only the first control plane and first worker are rebooted during the upgrade to verify the new boot configuration
   * Remaining nodes are **NOT** rebooted — they continue running with the upgraded software and can be rebooted at any time post successful upgrade
   * All worker nodes are upgraded sequentially (one at a time) to ensure cluster stability

Primary Status File
"""""""""""""""

**Location:** ``<K8s_NFS_mount_point>/upgrade/upgrade_status.yml``

How to find your K8s NFS mount point:

The mount point is defined in your ``storage_config.yml`` file. Look for the NFS mount entry where ``name: "nfs_k8s"`` and the ``mount_point`` field shows the path.

Example from ``storage_config.yml``: ::

    mounts:
      - name: "nfs_k8s"
        source: "172.16.107.121:/mnt/share/omnia_k8s"
        mount_point: "/opt/omnia/k8s_mount"  # ← This is your K8s NFS mount point
        fs_type: "nfs"
        mnt_opts: "nosuid,rw,sync,hard,intr"
        mount_on_oim: true
        functional_group_prefix: ["service_kube"]

In this example, the upgrade status file would be located at: ::

    /opt/omnia/k8s_mount/upgrade/upgrade_status.yml

.. note::
   The mount point path may be different in your environment. Always check your ``storage_config.yml`` file (located at ``/opt/omnia/input/project_default/storage_config.yml``) to find the exact path configured for your K8s NFS storage.

Running the Kubernetes Upgrade
"""""""""""""""""""""""""

The Kubernetes upgrade is executed automatically by the upgrade orchestrator when you run the main upgrade playbook. See :ref:`phase-2-execute-upgrade` for instructions.

.. note::
   1. User should run the ``upgrade.yml`` playbook from the ``/omnia/upgrade`` directory so that logs are captured in ``/opt/omnia/log/core/playbooks/upgrade.log``
   2. If upgrade fails, check the cluster is healthy, fix issues if any and rerun the ``upgrade.yml`` playbook

Telemetry Upgrade
~~~~~~~~~~~~~~~~~

.. note::
   The telemetry upgrade is automatically executed as part of :ref:`phase-2-execute-upgrade`. The upgrade orchestrator processes the ``telemetry`` component in the correct order (after Kubernetes and before Slurm) and handles all validation and status tracking automatically.

The telemetry upgrade process upgrades telemetry components to their 2.2 versions while ensuring minimal disruption to metric collection and monitoring services.

**Upgrade Process**

The telemetry upgrade automatically performs the following operations:

1. **Component Detection** — Identifies which telemetry components are currently deployed in the cluster
2. **Upgrade Path Determination** — Determines the appropriate upgrade procedure for each detected component
3. **Component-Specific Upgrade** — Executes the upgrade procedure for each telemetry component
4. **Validation** — Verifies successful upgrade and pod readiness before proceeding

**Post-Upgrade Validation**

After the telemetry upgrade completes, the playbook performs the following validation steps:

1. Retrieves the status of all telemetry pods in the telemetry namespace
2. Waits for all pods to reach Running or Completed state (60 retries × 15 seconds per retry)
3. Displays the final pod readiness status
4. Updates the upgrade manifest with completed status

**Initiating Telemetry Upgrade**

The telemetry upgrade is executed automatically by the upgrade orchestrator when you run the main upgrade playbook. See :ref:`phase-2-execute-upgrade` for instructions.

Slurm Upgrade
~~~~~~~~~~~~~

.. note::
   The Slurm upgrade is automatically executed as part of :ref:`phase-2-execute-upgrade`. The upgrade orchestrator processes the ``slurm`` component in the correct order (after telemetry) and handles all validation and status tracking automatically.

The Slurm upgrade workflow updates the cloud-init and BSS configurations on all Slurm cluster nodes and applies the changes through a coordinated reboot of the cluster infrastructure. This process ensures that provisioning, node configuration, and runtime settings are synchronized with the target Omnia release.

.. warning::

   - All Slurm compute, control, and login nodes are rebooted simultaneously during the upgrade process. Ensure that no critical or long-running jobs are active before starting the upgrade.
   - Do not modify Slurm node definitions or host mappings in the PXE mapping file while the upgrade is in progress.
   - Existing NFS mount configurations from Omnia 2.1 are preserved during the upgrade. Do not add, remove, or modify NFS mount points until the upgrade has completed successfully.

Slurm Upgrade Workflow
"""""""""""""""""""

During the Slurm upgrade, Omnia performs the following operations:

#. Updates cloud-init configurations for all Slurm functional node groups.
#. Updates BSS configurations used for node provisioning and configuration management.
#. Applies the updated configurations to the following node categories:

   - ``slurm_control_node``
   - ``slurm_node``
   - ``login_node``
   - ``login_compiler_node``

#. Initiates a coordinated reboot of all Slurm and login nodes.
#. Waits for each node to complete the reboot cycle and restore SSH connectivity.
#. Verifies the operational status of Slurm services on each node.
#. Generates a consolidated upgrade status report for all nodes.

Node Reboot and Validation
"""""""""""""""""""""

After configuration updates are applied, Omnia initiates a cluster-wide reboot to activate the new settings.

The reboot workflow includes the following validations:

- A reboot command is issued to all Slurm and login nodes.
- Each node is allowed up to **1200 seconds** to complete the reboot process.
- Omnia continuously checks for SSH availability after the reboot.
- Nodes are given up to **60 seconds** to re-establish SSH connectivity once booting is complete.
- After SSH connectivity is restored, Omnia validates Slurm functionality using the ``sinfo`` command.
- The validation operation is retried automatically to accommodate service startup delays.

Health Checks Performed
""""""""""""""""""

The following checks are performed for every upgraded node:

**Pre-Reboot Validation**

- Verify that the node is reachable before initiating the reboot.
- Confirm that the node is accessible through SSH.

**Post-Reboot Validation**

- Verify successful completion of the reboot operation.
- Confirm restoration of SSH connectivity.
- Validate that Slurm services are running correctly.
- Verify that ``sinfo`` returns a valid response from the node.

Upgrade Status Report
""""""""""""""""

At the end of the upgrade process, Omnia generates a node-level status report summarizing the outcome for every node in the cluster.
The report categorizes nodes into the following groups:

* **Successful** -The node completed all upgrade stages successfully.
* **Unreachable** - The node was not reachable before the reboot phase.
* **Reboot Failed** - The reboot command could not be executed successfully.
* **SSH Failure** - The node rebooted but did not restore SSH connectivity within the allowed timeout period.
* **sinfo Failure** - Slurm services failed to start correctly or did not respond to ``sinfo`` validation checks.

Post-Upgrade Recommendations
""""""""""""""""""""""""

After a successful upgrade:

- Verify overall cluster health using ``sinfo`` and ``scontrol show nodes``.
- Confirm that all expected compute nodes have returned to the ``IDLE`` or intended operational state.
- Validate NFS accessibility from login and compute nodes.
- Submit a small test job to confirm scheduler functionality.
- Review the generated status report and investigate any nodes reported under the *Unreachable*, *Reboot Failed*, *SSH Failure*, or *Sinfo Failure* categories before returning the cluster to production use.

.. _phase-2-execute-upgrade:

Phase 2: Execute Upgrade
~~~~~~~~~~~~~~~~~~~~~~~~

After reviewing the component-specific upgrade details above, run the full upgrade: ::

    cd /omnia/upgrade
    ansible-playbook upgrade.yml

.. _aarch64-inventory:

**aarch64 clusters:** If your PXE mapping file contains aarch64 functional groups (e.g., ``slurm_node_aarch64``), you must pass an inventory file with the ``[admin_aarch64]`` group: ::

    cd /omnia/upgrade
    ansible-playbook upgrade.yml -i <inventory_file>

The inventory file must define exactly one ARM admin node under the ``[admin_aarch64]`` group. Example inventory: ::

    [admin_aarch64]
    <arm_admin_node_ip_or_hostname>

.. note::
    - The ``[admin_aarch64]`` group must contain exactly one host. Multiple hosts or an empty group will cause the upgrade to fail.
    - The ARM admin node must be accessible via SSH from the OIM host.
    - NFS must be configured on the OIM for aarch64 image building to work.
    - If your cluster has only x86_64 nodes (no aarch64 entries in the PXE mapping file), the ``-i`` option is not required.

Post-Upgrade Verification
~~~~~~~~~~~~~~~~~~~~~~~~

After the upgrade completes, verify the following:

1. Check the upgrade summary displayed at the end of the playbook run.
2. Verify the upgrade manifest: ::

    cat /opt/omnia/.data/upgrade_manifest.yml

3. Confirm all component statuses show ``completed`` or ``skipped``.
4. Validate cluster health:

    * Kubernetes cluster: ``kubectl get nodes``
    * Slurm cluster: ``sinfo``
    * Telemetry: Verify metrics are being collected

5. If BuildStreaM is enabled, trigger the GitLab pipeline for downstream components.

For troubleshooting upgrade issues, see `Upgrade and Rollback Troubleshooting <troubleshootingguide.html>`_.