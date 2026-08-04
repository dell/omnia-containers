
# Glossary

This glossary defines key terms used throughout the Omnia documentation. Terms
are listed alphabetically. Where applicable, entries link to the documentation
page that provides a full explanation.

**Apptainer**
:   Formerly known as Singularity. A container runtime designed for HPC environments that allows users to run containers without root privileges. Supported on Slurm compute nodes in Omnia 2.1+.

**BMC**
:   Baseboard Management Controller. A dedicated microcontroller embedded in server motherboards that provides out-of-band management capabilities (power control, hardware monitoring, remote console) independent of the host operating system. On Dell PowerEdge servers, the BMC is implemented as **iDRAC**.

**BSS**
:   Boot Script Service. A component of **OpenCHAMI** that dynamically generates per-node boot scripts based on the node's hardware profile and assigned role. BSS provides boot configuration during network provisioning.

**BuildStreaM**
:   Omnia's GitLab CI-based automation pipeline for catalog-driven deployment. Administrators define a deployment catalog (YAML manifest), and BuildStreaM generates a CI/CD pipeline that executes the required Ansible playbooks in order. See [Components](components.md).

**Calico**
:   A CNI (Container Network Interface) plugin for Kubernetes that provides pod-to-pod networking and network policy enforcement. Omnia deploys Calico as the default CNI in the Kubernetes cluster.

**cloud-init**
:   A cloud instance initialization system that configures systems during first boot. Omnia uses cloud-init to automate node configuration and customization during the provisioning process.

**Composable Roles**
:   Omnia's system for assigning server functions via a declarative mapping file. A single server can hold multiple roles (e.g., Slurm control node + login node), decoupling physical hardware from logical cluster functions.

**Containerd**
:   An industry-standard container runtime with an emphasis on simplicity, robustness, and portability. Omnia uses Containerd as the container runtime for Kubernetes workloads.

**CoreDHCP**
:   A DHCP server implementation that provides network boot and configuration services. Omnia uses CoreDHCP for PXE boot provisioning and multi-subnet DHCP configuration for rack-based deployments.

**CoreDNS**
:   A DNS server that is flexible and extensible, serving as the foundation for service discovery in Kubernetes. Omnia uses CoreDNS for dynamic DNS resolution and hostname management via coresmd.

**CSI drivers**
:   Container Storage Interface drivers that enable Kubernetes to orchestrate storage from arbitrary storage systems. Omnia deploys CSI drivers for PowerScale and other storage backends.

**CUDA**
:   NVIDIA's parallel computing platform and programming model. Omnia automates CUDA toolkit installation for GPU-enabled nodes to support HPC and AI workloads.

**DCGM**
:   Data Center GPU Manager. NVIDIA's suite of tools for monitoring and managing GPU data center environments. Omnia deploys DCGM for GPU telemetry collection and monitoring.

**DOCA-OFED**
:   NVIDIA's data center acceleration on Arm and NVIDIA OpenFabrics Enterprise Distribution. Omnia automatically installs DOCA-OFED drivers for NVIDIA InfiniBand adapters to enable high-performance networking.

**ETCD**
:   A distributed, reliable key-value store for the most critical data of a distributed system. Omnia uses ETCD as the Kubernetes cluster state store, with support for local disk deployment for high availability.

**Functional Groups**
:   Named role definitions in Omnia's **Composable Roles** system. Each functional group (e.g., `slurm_node`, `service_kube_control_plane`) determines which software and configuration is applied to a server.

**iDRAC**
:   Integrated Dell Remote Access Controller. Dell's implementation of the **BMC**, providing Redfish API access, remote console, virtual media, firmware management, and hardware telemetry for Dell PowerEdge servers. See [Telemetry Architecture](telemetry_architecture.md).

**InfiniBand**
:   A high-performance, low-latency networking technology designed for HPC clusters. Omnia supports InfiniBand networking with automatic DOCA-OFED driver installation for NVIDIA adapters.

**iSCSI**
:   Internet Small Computer System Interface. A storage networking protocol for linking data storage facilities. Omnia uses iSCSI for PowerVault storage integration to provide persistent storage for critical cluster components.

**Kafka**
:   Apache Kafka. A distributed event-streaming platform used as the central message broker in Omnia's telemetry pipeline. All metrics from **iDRAC** and **LDMS** flow through Kafka before reaching **VictoriaMetrics**. See [Telemetry Architecture](telemetry_architecture.md).

**LDAP**
:   Lightweight Directory Access Protocol. A protocol for accessing and maintaining distributed directory information services. Omnia integrates LDAP for centralized authentication and user management.

**LDMS**
:   Lightweight Distributed Metric Service. A high-performance, low-overhead metric collection framework developed by Sandia National Laboratories for HPC environments. Omnia deploys LDMS agents on compute nodes to collect in-band OS and application metrics. See [Telemetry Architecture](telemetry_architecture.md).

**MetalLB**
:   A bare-metal load balancer for Kubernetes. MetalLB assigns external IP addresses to Kubernetes `LoadBalancer` services in environments without a cloud provider. Omnia deploys MetalLB automatically in the Kubernetes cluster.

**OIM**
:   Omnia Infrastructure Manager. The dedicated management node that runs all Omnia control-plane services, including the `omnia_core` Ansible container, OpenCHAMI, Pulp, and telemetry collectors. The OIM is the single point from which the entire cluster is provisioned and managed. See [Architecture](architecture.md).

**OpenCHAMI**
:   Composable Hierarchical Automated Management Infrastructure. The provisioning engine at the core of Omnia, providing API-driven node discovery, hardware inventory, and bare-metal lifecycle management. Includes **SMD** and **BSS** as sub-services. See [Components](components.md).

**OpenManage Enterprise (OME)**
:   Dell's infrastructure management solution that provides unified management for Dell PowerEdge servers. Omnia integrates with OME for automated BMC discovery and inventory management.

**OpenTelemetry**
:   An observability framework for cloud-native software. Omnia uses OpenTelemetry Collector for PowerScale telemetry collection and data transformation.

**Podman**
:   A daemonless, rootless container engine for running OCI containers on Linux. Omnia uses Podman on the **OIM** to run all management services (`omnia_core`, OpenCHAMI, Pulp, OpenLDAP) as isolated containers without requiring Docker. See [Architecture](architecture.md).

**PowerScale**
:   Dell's enterprise-scale network-attached storage (NAS) platform. Omnia integrates with PowerScale for storage provisioning, telemetry collection, and CSI driver support.

**PowerVault**
:   Dell's direct-attached storage (DAS) and network-attached storage (NAS) solutions. Omnia integrates with PowerVault for persistent storage using iSCSI block storage with multipath support for Slurm controller components.

**PXE**
:   Preboot Execution Environment. An industry-standard protocol that allows servers to boot an operating system image over the network rather than from local disk. Omnia uses PXE for initial node discovery and OS provisioning.

**Pulp**
:   An open-source repository management platform. Omnia deploys Pulp as a Podman container on the **OIM** to mirror RPM repositories, container images, and Python packages locally. Essential for air-gapped deployments. See [Components](components.md).

**ROCm**
:   Radeon Open Compute. AMD's open-source software platform for GPU-accelerated computing. Omnia supports ROCm installation on nodes with AMD Instinct GPUs for AI/ML and HPC workloads.

**SMD**
:   State Manager Daemon. The inventory and state-tracking service within **OpenCHAMI**. SMD maintains a real-time record of every node's hardware configuration, power state, and component hierarchy.

**SmartFabric Manager (SFM)**
:   Dell's network management solution for SONiC that streamlines network management with automation, analytics, and scalability. Omnia supports SFM telemetry collection for fabric monitoring and performance analysis.

**Slurm**
:   Simple Linux Utility for Resource Management. An open-source, highly scalable job scheduler and workload manager widely used in HPC clusters. Omnia deploys and configures Slurm for batch job scheduling on compute nodes. See [Architecture](architecture.md).

**TFTP**
:   Trivial File Transfer Protocol. A simple file transfer protocol used during PXE boot to deliver the initial bootloader binary to bare-metal nodes.

**Vector**
:   A high-performance, vendor-neutral observability data pipeline. Omnia uses Vector for collecting, transforming, and routing telemetry data from LDMS and OME sources to VictoriaMetrics and VictoriaLogs.

**VictoriaLogs**
:   A high-performance log database built for log storage and analysis. Omnia uses VictoriaLogs for centralized log collection and storage, working alongside VictoriaMetrics for complete observability.

**VictoriaMetrics**
:   A high-performance time-series database that stores all telemetry data in Omnia's monitoring pipeline. Supports PromQL and MetricsQL for querying, and achieves high compression ratios for efficient long-term metric retention. See [Telemetry Architecture](telemetry_architecture.md).

**vlagent**
:   VictoriaLogs agent that collects logs from various sources and pushes them to VictoriaLogs. Omnia deploys vlagent for log collection from cluster components.

**vminsert**
:   VictoriaMetrics component responsible for ingesting time-series data into the VictoriaMetrics database. Omnia uses vminsert as the data ingestion endpoint for metrics storage.

**vmselect**
:   VictoriaMetrics query component that executes queries against stored metrics data. Omnia uses vmselect for querying and retrieving metrics from the VictoriaMetrics database.

**vmstorage**
:   VictoriaMetrics storage backend component that persists time-series data. Omnia uses vmstorage for durable storage of metrics data in cluster mode deployments.

**vmagent**
:   VictoriaMetrics agent that collects metrics from various sources and pushes them to VictoriaMetrics. Omnia deploys vmagent for metrics collection from cluster components.
