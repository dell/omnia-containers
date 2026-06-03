New Features
=============

The following sections describe the new features and enhancements introduced in Omnia 2.2 releases.


Vast Repo and Vast Client Installation
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Omnia now supports the installation of Vast NFS client on cluster nodes. This feature allows you to:

- Build the Vast repository from source using the provided download script
- Host the Vast RPMs on an HTTP server (such as Apache) as a user repository
- Configure the Vast repository in ``local_repo_config.yml``
- Automatically install the Vast client on cluster nodes during the provisioning process when an InfiniBand NIC is present

The Vast repository can be built and hosted following the steps documented in `Vast Repo and Vast Client Installation <OmniaInstallGuide/RHEL_new/CreateLocalRepo/vast_repo_installation.html>`_.


Minimal OS Functional Groups
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Omnia now supports Minimal OS functional groups (``os_x86_64`` and ``os_aarch64``) that provide a clean operating system baseline designed specifically for downstream platform software installation.

- Minimal OS functional groups include only essential OS packages and LDMS telemetry packages
- No schedulers, container runtimes, or orchestration software are pre-installed
- Designed to deploy platform software without conflicts from Slurm, Kubernetes, or other pre-installed components
- Maintains cluster-wide telemetry capabilities through LDMS integration
- Supports optional additional packages via ``additional_packages.json`` files in ``input/config/{arch}/rhel/10.0/``
- Administrators can include custom packages like ``podman``, diagnostic tools, or monitoring agents
- If additional packages file is absent or empty, images build successfully with standard Minimal OS package set only

For detailed information on functional groups and additional packages configuration, see :doc:`../OmniaInstallGuide/RHEL_new/composable_roles`.


NVIDIA DCGM and CUDA Toolkit Provisioning for Slurm GPU Nodes
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Omnia now delivers end-to-end automated GPU readiness for Slurm clusters. This feature covers
NVIDIA driver installation, CUDA toolkit distribution to shared cluster storage, and NVIDIA Data
Center GPU Manager (DCGM) setup — all performed during stateless node provisioning, without any
user intervention on individual nodes.

- NVIDIA driver installation on all GPU-capable Slurm compute nodes
- CUDA toolkit made available cluster-wide via a shared NFS location accessible to all nodes
  simultaneously
- DCGM installation with automatic CUDA version detection and appropriate package selection
- Configurable DCGM enablement using ``dcgm.metrics_enabled`` under ``telemetry_sources`` in ``telemetry_config.yml`` (default: ``true``)
- ``nvidia-dcgm`` service enablement and validated startup on each GPU node
- GPU enumeration and discovery validation using ``dcgmi``
- ``nvidia-peermem`` kernel module installation for GPUDirect RDMA-capable environments
- Persistent CUDA environment configuration across login shells, non-login shells, and Slurm job
  environments
- Nodes without NVIDIA GPU hardware are automatically skipped — no manual exclusion required

NVIDIA HPC SDK Provisioning for Slurm Clusters
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Omnia now supports cluster-wide deployment of the NVIDIA HPC SDK (``nvhpc``) for Slurm
compiler and compute nodes. The SDK is installed once on the compiler node via DNF,
copied to shared NFS storage, and made available to all compute nodes through a
bind mount — eliminating repeated downloads or per-node installations.

- NVIDIA HPC SDK installed on the compiler node via DNF using pre-configured NVIDIA repositories
- SDK binaries and libraries copied to shared NFS at ``/hpc_tools/nvidia_sdk/nvhpc``
- All compute nodes mount the NFS copy via a local bind mount at ``/opt/nvidia/nvhpc``
- Persistent environment configuration written to ``/etc/profile.d/nvhpc.sh`` on every node,
  covering compilers (``nvc``, ``nvc++``, ``nvfortran``), MPI binaries, manual pages, and module files
- Architecture-aware: supports both ``x86_64`` and ``aarch64`` without separate configuration
- Nodes without a completed compiler-node installation are blocked with a clear error message
  rather than silently failing
- Setup script (``/usr/local/bin/setup_nvhpc_sdk.sh``) is pre-deployed to all nodes during
  provisioning; the user invokes it post-provisioning at their discretion

For detailed setup instructions, see `NVIDIA HPC SDK Setup <../OmniaInstallGuide/RHEL_new/Provision/nvhpc_sdk.html>`_.

BuildStreaM Pipeline Architecture and API Enhancements
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Omnia BuildStreaM now supports enhanced pipeline architecture and API capabilities for improved scalability, reliability, and operational flexibility.

- Core API Implementation including Upload, Images, Deploy, Restart, Validate, and CleanUp with proper state machine management and precondition checks
- Pipeline Decomposition splitting monolithic pipeline into Build and Deploy pipelines with parent-child architecture enabling independent execution and better scalability
- Image Lifecycle Management with image_group_id extraction, uniqueness validation, metadata persistence, and automated creation of image_groups and images records
- Deploy Pipeline Enhancements including list_images stage, dynamic child pipeline generation, and image selection workflow for deployments
- CleanUp Pipeline with guarded execution, artifact/image deletion, and controlled state transitions
- Automated Cleanup Capability for failed job artifacts, images, and DB records with state machine validation
- Resume & Retry Capability with stage-level retry classification (Build vs Deploy), per-attempt log segregation, DB schema updates for attempt tracking, and integration with GitLab native retry mechanisms
- PowerScale Support adding Dell PowerScale as optional S3 backend alongside MinIO/NFS
- Validate API Implementation with Molecule test framework replacing stub implementation with full execution, result parsing, and outcome evaluation
- Molecule Framework Integration including invocation, test suite selection, timeout handling, and API-based validation integration

For detailed information, see `BuildStreaM Documentation <../Buildstream/index.html>`_.

One-Shot Combined Log Extraction for Debugging
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Omnia provides a one-shot log collection playbook for gathering cluster logs from Kubernetes and Slurm nodes for debugging and support handoff.

**Usage**

::

    cd omnia/log_collector
    ansible-playbook collect.yml

**Collection modes**

* **Full mode** (default): Collects all logs from target nodes

::

    ansible-playbook collect.yml

* **Curated support mode**: Excludes temporary and stale log files

::

    ansible-playbook collect.yml --tags curated_support

**What is collected**

* Kubernetes master nodes: Container logs, pod logs, CNI logs, runtime logs, system logs
* Kubernetes worker nodes: System logs, bootstrap logs
* Slurm controller nodes: Scheduler logs, service logs, database logs, system logs
* Slurm compute nodes: Job logs, system logs
* Login nodes: System logs, authentication logs
* Login compiler nodes: System logs, authentication logs

**Output artifacts**

* Workspace: ``/opt/omnia/collector_logs``
* Bundle: ``omnia_logs_<YYYYMMDD-HHMMSS>.tar.gz``
* Metadata: ``metadata.json`` (included in bundle)
* Checksum: ``.sha256`` file for integrity verification

**Prerequisites**

* PXE mapping file must exist at ``/opt/omnia/input/project_default/pxe_mapping_file.csv``
* Nodes must be reachable from OIM


BMC Discovery via Dell OpenManage Enterprise
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Omnia introduces automated BMC (Baseboard Management Controller) discovery via Dell OpenManage Enterprise (OME). This feature enables large-scale server discovery and automatic PXE mapping file generation, which is particularly useful for deployments with thousands of nodes.

**Key Features**

- Automated server inventory collection from OME REST API
- Support for paginated API queries to handle large-scale deployments (100 servers per page)
- Automatic extraction of service tags, iDRAC details, NIC MACs, and group membership
- Scalable Unit (SU) extraction from iDRAC hostnames for logical grouping
- Timestamped PXE mapping file generation for version control and audit trails
- IP address derivation from BMC IPs using configured subnets
- OME group mapping to functional groups for role-based provisioning

**Configuration Requirements**

- Dell OpenManage Enterprise (OME) appliance must be operational and have discovered target servers
- ``input/discovery_config.yml`` - OME IP configuration
- ``input/network_spec.yml`` - Network configuration for admin and InfiniBand subnets
- OME credentials stored in Ansible Vault (``omnia_config_credentials.yml``)
- Run ``prepare_oim`` to set up OME credentials

**Usage**

To perform BMC discovery using OME:

::

    ansible-playbook discovery/discovery.yml -e "discovery_mechanism=ome"

This generates a timestamped PXE mapping file: ``bmc_pxe_mapping_file_<timestamp>.csv``

**Post-Discovery Workflow**

1. Review the generated timestamped CSV file
2. Adjust functional groups, group names, and hostnames as needed
3. Copy or rename the desired timestamped file to ``pxe_mapping_file.csv``
4. Proceed with provisioning

For more details, see `BMC Discovery Configuration <OmniaInstallGuide/Maintenance/upgrade.html#bmc-discovery-configuration>`_ and `BMC Discovery Rollback Considerations <OmniaInstallGuide/Maintenance/rollback.html#bmc-discovery-rollback-considerations>`_.

.. note::
    Magellan-based discovery is planned for a future release. Currently, only OME-based discovery is supported.