New Features
=============

The following sections describe the new features and enhancements introduced in Omnia 2.x releases.

Version 2.1.0.0-rc1
-------------------

PowerVault Storage Integration
------------------------------

The PowerVault integration, with a preconfigured volume, provides persistent storage for critical Slurm controller components using iSCSI block storage with multipath support. This ensures data persistence for Slurm’s StateSaveLocation and the MariaDB/MySQL database.

InfiniBand Networking Support
------------------------------

Provides comprehensive support for InfiniBand (IB) networking in HPC clusters, including automatic DOCA-OFED driver installation for Mellanox InfiniBand cards, static IP assignment for IB interfaces, and prerequisite validation for Open Subnet Manager (OpenSM) service configuration. This ensures high-performance, low-latency interconnects for parallel computing workloads.

Version 2.0.0.0
---------------

Support for Podman Containers
-----------------------------

Enables deployment of the following Omnia core services as Podman containers, ensuring secure, lightweight, and OCI-compliant environments for HPC clusters. This simplifies lifecycle management, accelerates updates, and improves isolation for critical services:

- **Omnia Core** — Orchestrates HPC cluster operations.
- **Omnia Auth** — Provides LDAP-based authentication.
- **OpenCHAMI** — Powers diskless provisioning workflows.
- **Pulp Repository Service** — Hosts local repositories for air-gapped deployments.

Repository Management
---------------------

Provides a Pulp-based local repository service deployed as a Podman container, enabling secure and efficient package distribution in air-gapped HPC environments. This reduces dependency on external networks and accelerates provisioning workflows.

Authentication Service
----------------------

Integrates an LDAP server within the Omnia Auth Podman container for centralized authentication and directory services. This enhances security and simplifies identity management across HPC clusters.

Telemetry Collection and Monitoring
-----------------------------------

Automates the configuration of Kubernetes Service Clusters to host essential monitoring components for telemetry collection and monitoring. The following telemetry capabilities are supported:

- **iDRAC Telemetry** — Collects out-of-band system metrics, including power, thermal, and hardware health data, from Dell servers. Telemetry data is streamed as time-series data to Kafka or VictoriaMetrics, depending on deployment requirements. VictoriaPump is included for storing telemetry metrics in the VictoriaMetrics database.

- **LDMS Telemetry** — Captures in-band performance metrics such as CPU, memory, network, and I/O usage from Slurm cluster nodes. Metrics are streamed as time-series data to Kafka for scalable ingestion and analysis.

- **Air-gapped telemetry support** — Supports telemetry collection in air-gapped or offline environments to meet security and compliance requirements.

Kubernetes Cluster High Availability
------------------------------------

Delivers built-in high-availability (HA) failover for Service Kubernetes Cluster control plane nodes, ensuring uninterrupted cluster management and improved resilience for HPC workloads.

Provisioning and Deployment Based on Functional Groups
------------------------------------------------------

Enables role-based provisioning for HPC clusters using mapping files. Automatically assigns functional roles (for example, Slurm Control Node and Login Node) and deploys customized operating system images tailored to workload-specific configurations.

The following functional roles are supported:

- Login Node
- Login Compiler Node
- Slurm Node
- Slurm Control Node
- Service Kubernetes Node
- Service Kubernetes Control Plane

Stateless Boot
--------------

Introduces stateless provisioning for RHEL 10 using OpenCHAMI, reducing deployment time and storage overhead for HPC clusters.

Automatic CUDA Installation for GPU Workloads
---------------------------------------------

Automatically installs CUDA during node provisioning, ensuring GPU-enabled nodes are ready for HPC workloads immediately after deployment. This reduces manual setup time and accelerates readiness for GPU-intensive applications.

Security Enhancements
---------------------

Credentials are now encrypted using industry-standard algorithms (for example, AES-256), improving compliance with security best practices and reducing the risk of data exposure.

Platform Support
----------------

Supports ``x86_64`` and ``aarch64`` architectures, enabling deployment on both traditional and ARM-based HPC nodes for improved flexibility and energy efficiency.

Input Template and Validator
----------------------------

Provides predefined configuration templates and early input validation to reduce configuration errors and accelerate HPC cluster provisioning. This improves deployment reliability and overall user experience.
