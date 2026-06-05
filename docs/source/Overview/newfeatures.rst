New Features
=============

The following sections describe the new features and enhancements introduced in Omnia 2.2 releases.


BuildStreaM Pipeline Architecture and API Enhancements
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Enhanced BuildStreaM pipeline architecture and API capabilities improve scalability, reliability, and operational flexibility with resume & retry capability, pipeline decomposition into Build and Deploy pipelines, dynamic child pipeline generation, image group lifecycle tracking, manual cleanup operations, and PowerScale support as an optional S3 backend.

For detailed information, see `BuildStreaM Documentation <../Buildstream/index.html>`_.

BMC Discovery via Dell OpenManage Enterprise
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Automated BMC (Baseboard Management Controller) discovery via Dell OpenManage Enterprise (OME) enables large-scale server discovery and automatic PXE mapping file generation with paginated API queries, automatic extraction of service tags and iDRAC details, Scalable Unit extraction from hostnames, timestamped file generation, and OME group mapping to functional groups.

Usage: ``ansible-playbook discovery/discovery.yml -e "discovery_mechanism=ome"`` generates a timestamped PXE mapping file and BMC Discovery Report with NIC link status information.

For more details, see `BMC Discovery Configuration <OmniaInstallGuide/Maintenance/upgrade.html#bmc-discovery-configuration>`_, `BMC Discovery Rollback Considerations <OmniaInstallGuide/Maintenance/rollback.html#bmc-discovery-rollback-considerations>`_, and `BMC Discovery Report Documentation <../OmniaInstallGuide/RHEL_new/Provision/ome_discovery.html>`_.

.. note::
    Magellan-based discovery is planned for a future release. Currently, only OME-based discovery is supported.

Multi-Subnet DHCP for Rack-Based Provisioning
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Multi-subnet DHCP configuration enables rack-based network provisioning for large-scale HPC and AI/ML clusters with per-rack /24 subnet assignment, CoreDHCP multi-subnet configuration generation, CoreDNS forward and reverse zone generation, and support for up to 100 racks with 254 nodes per rack.

For detailed configuration instructions, see `Multi-Subnet DHCP Configuration <../OmniaInstallGuide/RHEL_new/Network/multi_subnet_dhcp.html>`_.

CoreDNS-Based Hostname Resolution for Slurm and MPI
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Dynamic DNS resolution powered by coresmd replaces static `/etc/hosts` file management with automatic hostname resolution for Slurm and MPI workloads, real-time inventory updates from OpenCHAMI SMD, cloud-init based `/etc/resolv.conf` configuration, and K8s CoreDNS forwarding.

For detailed configuration instructions, see `CoreDNS Hostname Resolution Configuration <../OmniaInstallGuide/RHEL_new/Network/coredns_hostname_resolution.html>`_.

Vector Telemetry Pipeline for Data Routing
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Vector serves as a high-performance data pipeline tool for collecting, transforming, and routing telemetry data from LDMS and OpenManage Enterprise (OME) sources to VictoriaMetrics and VictoriaLogs with enhanced telemetry data flow management and dedicated write-buffer components.

For detailed configuration instructions, see `Vector Telemetry Pipeline Configuration <../OmniaInstallGuide/RHEL_new/Telemetry/vector_telemetry.html>`_.

PowerScale Telemetry for Storage Monitoring
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

PowerScale Telemetry enables comprehensive storage observability by collecting storage performance metrics and logs from Dell PowerScale storage nodes with CSM Metrics for PowerScale, OpenTelemetry Collector, and integration with CSI Driver for Dell PowerScale.

For detailed configuration instructions, see `PowerScale Telemetry Configuration <../OmniaInstallGuide/RHEL_new/Telemetry/power_scale_telemetry.html>`_.

UFM Telemetry to VictoriaMetrics
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

UFM (Unified Fabric Manager) telemetry collection provides InfiniBand fabric monitoring through vmagent scraping of UFM Prometheus metrics endpoints with secure HTTPS, TLS certificate validation, and dual-destination forwarding to local and remote VictoriaMetrics clusters.

For detailed configuration instructions, see `UFM Telemetry Configuration <../OmniaInstallGuide/RHEL_new/Telemetry/ufm_telemetry.html>`_.

VAST Storage Telemetry Integration
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

VAST storage telemetry integration delivers comprehensive storage observability through VMagent scraping of VAST Prometheus endpoints and VLAgent syslog log collection with secure HTTPS, TLS authentication, and dual-destination forwarding to internal and external VictoriaMetrics.

For detailed configuration instructions, see `VAST Telemetry Configuration <../OmniaInstallGuide/RHEL_new/Telemetry/vast_telemetry.html>`_.

Minimal OS Functional Groups
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Minimal OS functional groups (``os_x86_64`` and ``os_aarch64``) provide a clean operating system baseline designed specifically for downstream platform software installation.

For detailed information on functional groups and additional packages configuration, see :doc:`../OmniaInstallGuide/RHEL_new/composable_roles`.

NVIDIA DCGM and CUDA Toolkit Provisioning for Slurm GPU Nodes
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

End-to-end automated GPU readiness for Slurm clusters delivers NVIDIA driver installation, CUDA toolkit distribution to shared cluster storage, and NVIDIA Data Center GPU Manager (DCGM) setup during stateless node provisioning without user intervention on individual nodes.

This includes automatic GPU hardware detection, DCGM installation with CUDA version detection, ``nvidia-peermem`` kernel module installation for GPUDirect RDMA, persistent CUDA environment configuration, and automatic skipping of nodes without NVIDIA GPU hardware.

NVIDIA HPC SDK Provisioning for Slurm Clusters
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Cluster-wide deployment of the NVIDIA HPC SDK (``nvhpc``) for Slurm compiler and compute nodes eliminates repeated downloads or per-node installations by installing the SDK once on the compiler node via DNF, copying to shared NFS storage, and making it available to all compute nodes through a bind mount.

This includes architecture-aware support for both ``x86_64`` and ``aarch64``, persistent environment configuration, error blocking for incomplete compiler-node installations, and a pre-deployed setup script invoked post-provisioning.

For detailed setup instructions, see `NVIDIA HPC SDK Setup <../OmniaInstallGuide/RHEL_new/Provision/nvhpc_sdk.html>`_.

Vast Repo and Vast Client Installation
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Vast NFS client installation on cluster nodes is streamlined by building the Vast repository from source, hosting the RPMs on an HTTP server, configuring the repository in ``local_repo_config.yml``, and automatically installing the client during provisioning when an InfiniBand NIC is present.

The Vast repository can be built and hosted following the steps documented in `Vast Repo and Vast Client Installation <OmniaInstallGuide/RHEL_new/CreateLocalRepo/vast_repo_installation.html>`_.

One-Shot Combined Log Extraction for Debugging
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

A one-shot log collection playbook gathers cluster logs from Kubernetes and Slurm nodes for debugging and support handoff with full and curated support collection modes, log collection from all node types (Kubernetes master/worker, Slurm controller/compute, login nodes), and timestamped tar.gz bundle output with metadata and checksum.

Usage: ``cd omnia/log_collector && ansible-playbook collect.yml`` for full mode or ``ansible-playbook collect.yml --tags curated_support`` for curated support mode.