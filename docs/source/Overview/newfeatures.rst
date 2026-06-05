New Features
=============

The following sections describe the new features and enhancements introduced in Omnia 2.2 releases.


BuildStreaM Pipeline Architecture and API Enhancements
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Omnia BuildStreaM now supports enhanced pipeline architecture and API capabilities for improved scalability, reliability, and operational flexibility.

The key enhancements include:

- **Resume & Retry Capability:** Retry failed stages with smart resume (artifact reuse), re-run deploy stages after success, per-attempt log segregation, and integration with GitLab native retry mechanisms
- **Pipeline Decomposition:** Split monolithic pipeline into Build and Deploy pipelines with parent-child architecture enabling independent execution and better scalability
- **Dynamic Child Pipeline Generation:** Automatic generation of child pipelines with actual image_group names for image selection workflow
- **Image Group Lifecycle Tracking:** Automated tracking through BUILT → DEPLOYING → DEPLOYED → VALIDATING → PASSED/FAILED → CLEANED states
- **Cleanup Capability:** Manual cleanup operations via GitLab pipeline for removing old images when the build image count exceeds the configured limit
- **PowerScale Support:** Dell PowerScale as optional S3 backend alongside MinIO/NFS

For detailed information, see `BuildStreaM Documentation <../Buildstream/index.html>`_.

Vector Telemetry Pipeline for Data Routing
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Omnia now supports Vector as a high-performance data pipeline tool for collecting, transforming, and routing telemetry data from LDMS and OpenManage Enterprise (OME) sources to VictoriaMetrics and VictoriaLogs. This deployment provides enhanced telemetry data flow management with dedicated write-buffer components.

For detailed configuration instructions, see `Vector Telemetry Pipeline Configuration <../OmniaInstallGuide/RHEL_new/Telemetry/vector_telemetry.html>`_.

PowerScale Telemetry for Storage Monitoring
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Omnia now supports PowerScale Telemetry for collecting storage performance metrics and logs from Dell PowerScale storage nodes. This deployment provides comprehensive storage observability with CSM Metrics for PowerScale, OpenTelemetry Collector, and integration with CSI Driver for Dell PowerScale.

For detailed configuration instructions, see `PowerScale Telemetry Configuration <../OmniaInstallGuide/RHEL_new/Telemetry/power_scale_telemetry.html>`_.

UFM Telemetry to VictoriaMetrics
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Omnia now supports UFM (Unified Fabric Manager) telemetry collection for InfiniBand fabric monitoring. This feature enables vmagent to scrape UFM Prometheus metrics endpoints and forward them to VictoriaMetrics with dual-destination support for local and remote clusters.

**Key Features:**

- Secure HTTPS scraping from UFM Prometheus endpoint with TLS certificate validation
- Basic Auth or Bearer token authentication support
- Metric label enrichment with subsystem, domain, and cluster labels
- Dual remote-write architecture: local VictoriaDB vminsert and remote vmagent forwarding
- Write-ahead log (WAL) buffering for durability during write failures
- Scrape failure resilience with automatic retry and backoff
- Configurable scrape interval with minimum 30-second floor

For detailed configuration instructions, see `UFM Telemetry Configuration <../OmniaInstallGuide/RHEL_new/Telemetry/ufm_telemetry.html>`_.

VAST Storage Telemetry Integration
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Omnia now supports VAST storage telemetry integration for comprehensive storage observability. This feature enables metrics scraping from VAST Prometheus endpoints and syslog log collection via VLAgent.

**Key Features:**

- VMagent scraping of 4 VAST Prometheus endpoints (all, views, devices, alarms)
- Secure HTTPS connection with TLS certificate validation and Basic Auth/Bearer token authentication
- Metric label enrichment with subsystem, vast_domain, and source_subsystem labels
- Dual-destination forwarding to internal VictoriaMetrics and external Omni (if enabled)
- VLAgent syslog ingestion supporting RFC 3164/5424 formats over UDP/TLS
- Log label enrichment with vast_cluster and event_type labels
- Buffer management for metrics and logs when destinations are unavailable
- Scrape health monitoring via VMagent self-metrics

For detailed configuration instructions, see `VAST Telemetry Configuration <../OmniaInstallGuide/RHEL_new/Telemetry/vast_telemetry.html>`_.

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

This generates a timestamped PXE mapping file: ``bmc_pxe_mapping_file_<timestamp>.csv`` and a BMC Discovery Report: ``bmc_discovery_report_<timestamp>.csv`` that provides NIC link status information for all discovered servers.

**Post-Discovery Workflow**

1. Review the generated timestamped CSV file
2. Review the BMC Discovery Report for NIC link statuses (BMC, Ethernet, InfiniBand)
3. Adjust functional groups, group names, and hostnames as needed
4. Copy or rename the desired timestamped file to ``pxe_mapping_file.csv``
5. Proceed with provisioning

For more details, see `BMC Discovery Configuration <OmniaInstallGuide/Maintenance/upgrade.html#bmc-discovery-configuration>`_, `BMC Discovery Rollback Considerations <OmniaInstallGuide/Maintenance/rollback.html#bmc-discovery-rollback-considerations>`_, and `BMC Discovery Report Documentation <../OmniaInstallGuide/RHEL_new/Provision/ome_discovery.html>`_.

.. note::
    Magellan-based discovery is planned for a future release. Currently, only OME-based discovery is supported.

Multi-Subnet DHCP for Rack-Based Provisioning
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Omnia now supports multi-subnet DHCP configuration for rack-based network provisioning in large-scale HPC and AI/ML clusters. This feature enables per-rack /24 subnet assignment with clear rack identification and failure isolation.

**Key Features:**

- Rack-based Admin (PXE) network configuration with per-rack /24 subnets
- CoreDHCP multi-subnet configuration generation with subnet pools and gateway configurations
- CoreDNS forward and reverse zone generation for each rack's Admin subnet
- DHCP pool management per rack with configurable lease times for discovery and provisioning phases
- Integration with BMC discovery for IP assignment while keeping OOB/BMC network preconfigured externally
- Validation of subnet overlap and VLAN conflicts
- Support for up to 100 racks with 254 nodes per rack (25,400 total nodes)
- DHCP response time ≤ 100 ms (p50) and ≤ 300 ms (p99) during normal operation

For detailed configuration instructions, see `Multi-Subnet DHCP Configuration <../OmniaInstallGuide/RHEL_new/Network/multi_subnet_dhcp.html>`_.

CoreDNS-Based Hostname Resolution for Slurm and MPI
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Omnia now supports dynamic DNS resolution powered by coresmd, replacing static `/etc/hosts` file management. This feature provides automatic hostname resolution for Slurm and MPI workloads with real-time inventory updates.

**Key Features:**

- coresmd queries OpenCHAMI SMD inventory every 30 seconds and auto-generates forward A records for all inventoried nodes
- Cloud-init based `/etc/resolv.conf` configuration on compute nodes with cluster domain search
- K8s CoreDNS ConfigMap patching to forward cluster domain queries to OIM coresmd
- Automatic skipping of `/etc/hosts` management on OIM and Slurm nodes when DNS is enabled
- Multi-subnet CoreDHCP support for multi-rack PXE deployments
- New nodes added to SMD become resolvable within 30 seconds without playbook re-run
- Toggle via `dns_enabled` parameter in `input/provision_config.yml` (default: `false` for backward compatibility)

For detailed configuration instructions, see `CoreDNS Hostname Resolution Configuration <../OmniaInstallGuide/RHEL_new/Network/coredns_hostname_resolution.html>`_.