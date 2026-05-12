New Features
=============

The following sections describe the new features and enhancements introduced in Omnia 2.1 releases.


Minimal OS Functional Groups
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Introduces new Minimal OS functional groups (``os_x86_64`` and ``os_aarch64``) that provide a clean operating system baseline designed specifically for downstream platform software installation.Use Minimal OS functional groups when you need to deploy platform software without conflicts from Slurm, Kubernetes, or other pre-installed components, while maintaining cluster-wide telemetry capabilities.


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

* Workspace: ``/opt/omnia/logs/``
* Bundle: ``omnia-logs-<identifier>-<YYYYMMDD-HHMMSS-IST>.tar.gz``
* Metadata: ``metadata.json`` (included in bundle)
* Checksum: ``.sha256`` file for integrity verification

**Prerequisites**

* PXE mapping file must exist at ``/opt/omnia/input/project_default/pxe_mapping_file.csv``
* Nodes must be reachable from OIM
* Write permissions on ``/opt/omnia/logs``