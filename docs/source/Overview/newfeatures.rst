New Features
=============

The following sections describe the new features and enhancements introduced in Omnia 2.2 releases.

.. list-table:: New Features Summary
   :widths: 25 30 45
   :header-rows: 1

   * - Functional area
     - Feature name
     - Feature description
   * - BuildStreaM
     - BuildStreaM Pipeline Architecture and API Enhancements
     - Enhanced pipeline architecture and API capabilities with resume & retry, pipeline decomposition, dynamic child pipeline generation, image group lifecycle tracking, manual cleanup operations, and PowerScale S3 backend support
   * - Provisioning
     - BMC Discovery via Dell OpenManage Enterprise
     - Automated BMC discovery via Dell OpenManage Enterprise (OME) with paginated API queries, automatic extraction of service tags and iDRAC details, Scalable Unit extraction, timestamped file generation, and OME group mapping
   * - Networking
     - Multi-Subnet DHCP for Rack-Based Provisioning
     - Multi-subnet DHCP configuration for rack-based network provisioning with per-rack /24 subnet assignment, CoreDHCP multi-subnet configuration generation, and CoreDNS forward and reverse zone generation
   * - Networking
     - CoreDNS-Based Hostname Resolution for Slurm and MPI
     - Dynamic DNS resolution powered by coresmd replacing static `/etc/hosts` file management with automatic hostname resolution, real-time inventory updates from OpenCHAMI SMD, cloud-init based `/etc/resolv.conf` configuration, and K8s CoreDNS forwarding
   * - Telemetry
     - Vector Telemetry Pipeline for Data Routing
     - Vector high-performance data pipeline for collecting, transforming, and routing telemetry data from LDMS and OME sources to VictoriaMetrics and VictoriaLogs with dedicated write-buffer components
   * - Telemetry
     - PowerScale Telemetry for Storage Monitoring
     - PowerScale Telemetry for comprehensive storage observability collecting storage performance metrics and logs from Dell PowerScale storage nodes with CSM Metrics, OpenTelemetry Collector, and CSI Driver integration
   * - Telemetry
     - UFM Telemetry to VictoriaMetrics
     - UFM (Unified Fabric Manager) telemetry collection for InfiniBand fabric monitoring through vmagent scraping with secure HTTPS, TLS certificate validation, and dual-destination forwarding to local and remote VictoriaMetrics clusters
   * - Telemetry
     - VAST Storage Telemetry Integration
     - VAST storage telemetry integration through VMagent scraping of VAST Prometheus endpoints and VLAgent syslog log collection with secure HTTPS, TLS authentication, and dual-destination forwarding
   * - OS/Provisioning
     - Minimal OS Functional Groups
     - Minimal OS functional groups (``os_x86_64`` and ``os_aarch64``) providing a clean operating system baseline designed specifically for downstream platform software installation
   * - GPU/HPC
     - NVIDIA DCGM and CUDA Toolkit Provisioning for Slurm GPU Nodes
     - End-to-end automated GPU readiness for Slurm clusters with NVIDIA driver installation, CUDA toolkit distribution to shared cluster storage, and DCGM setup during stateless node provisioning
   * - HPC
     - NVIDIA HPC SDK Provisioning for Slurm Clusters
     - Cluster-wide deployment of NVIDIA HPC SDK (``nvhpc``) for Slurm compiler and compute nodes with single installation on compiler node, NFS sharing, and bind mount distribution
   * - Storage
     - Vast Repo and Vast Client Installation
     - Vast NFS client installation streamlined by building Vast repository from source, hosting RPMs on HTTP server, configuring repository, and automatic installation during provisioning when InfiniBand NIC is present
   * - Debugging
     - One-Shot Combined Log Extraction for Debugging
     - One-shot log collection playbook for gathering cluster logs from Kubernetes and Slurm nodes with full and curated support collection modes, log collection from all node types, and timestamped tar.gz bundle output