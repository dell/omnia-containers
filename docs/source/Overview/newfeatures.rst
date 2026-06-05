New Features
=============

The following sections describe the new features and enhancements introduced in Omnia 2.2 releases.

.. list-table:: New Features Summary
   :widths: 25 40 35
   :header-rows: 1

   * - Functional Area
     - Feature Description
     - Summary of Benefits
   * - BuildStreaM
     - Enhanced pipeline architecture and API capabilities with resume & retry, pipeline decomposition, dynamic child pipeline generation, image group lifecycle tracking, manual cleanup operations, and PowerScale S3 backend support
     - Improved scalability, reliability, and operational flexibility for image build and deploy workflows
   * - Provisioning
     - Automated BMC discovery via Dell OpenManage Enterprise (OME) with paginated API queries, automatic extraction of service tags and iDRAC details, Scalable Unit extraction, timestamped file generation, and OME group mapping
     - Large-scale server discovery and automatic PXE mapping file generation for deployments with thousands of nodes
   * - Networking
     - Multi-subnet DHCP configuration for rack-based network provisioning with per-rack /24 subnet assignment, CoreDHCP multi-subnet configuration generation, and CoreDNS forward and reverse zone generation
     - Scalable rack-based network provisioning supporting up to 100 racks with 254 nodes per rack
   * - Networking
     - Dynamic DNS resolution powered by coresmd replacing static `/etc/hosts` file management with automatic hostname resolution, real-time inventory updates from OpenCHAMI SMD, cloud-init based `/etc/resolv.conf` configuration, and K8s CoreDNS forwarding
     - Automatic hostname resolution for Slurm and MPI workloads with real-time inventory updates without playbook re-runs
   * - Telemetry
     - Vector high-performance data pipeline for collecting, transforming, and routing telemetry data from LDMS and OME sources to VictoriaMetrics and VictoriaLogs with dedicated write-buffer components
     - Enhanced telemetry data flow management with improved reliability and performance
   * - Telemetry
     - PowerScale Telemetry for comprehensive storage observability collecting storage performance metrics and logs from Dell PowerScale storage nodes with CSM Metrics, OpenTelemetry Collector, and CSI Driver integration
     - Comprehensive storage monitoring and observability for Dell PowerScale storage
   * - Telemetry
     - UFM (Unified Fabric Manager) telemetry collection for InfiniBand fabric monitoring through vmagent scraping with secure HTTPS, TLS certificate validation, and dual-destination forwarding to local and remote VictoriaMetrics clusters
     - InfiniBand fabric monitoring with secure data collection and multi-cluster support
   * - Telemetry
     - VAST storage telemetry integration through VMagent scraping of VAST Prometheus endpoints and VLAgent syslog log collection with secure HTTPS, TLS authentication, and dual-destination forwarding
     - Comprehensive storage observability for VAST storage with metrics and logs
   * - OS/Provisioning
     - Minimal OS functional groups (``os_x86_64`` and ``os_aarch64``) providing a clean operating system baseline designed specifically for downstream platform software installation
     - Clean OS baseline optimized for platform software installation
   * - GPU/HPC
     - End-to-end automated GPU readiness for Slurm clusters with NVIDIA driver installation, CUDA toolkit distribution to shared cluster storage, and DCGM setup during stateless node provisioning
     - Automated GPU provisioning without user intervention on individual nodes with automatic hardware detection
   * - HPC
     - Cluster-wide deployment of NVIDIA HPC SDK (``nvhpc``) for Slurm compiler and compute nodes with single installation on compiler node, NFS sharing, and bind mount distribution
     - Eliminates repeated downloads and per-node installations with architecture-aware support
   * - Storage
     - Vast NFS client installation streamlined by building Vast repository from source, hosting RPMs on HTTP server, configuring repository, and automatic installation during provisioning when InfiniBand NIC is present
     - Automated Vast client installation for InfiniBand-enabled clusters
   * - Debugging
     - One-shot log collection playbook for gathering cluster logs from Kubernetes and Slurm nodes with full and curated support collection modes, log collection from all node types, and timestamped tar.gz bundle output
     - Efficient log collection for debugging and support handoff with metadata and checksum verification