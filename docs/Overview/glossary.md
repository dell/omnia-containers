
# Glossary


This glossary defines key terms used throughout the Omnia documentation. Terms
are listed alphabetically. Where applicable, entries link to the documentation
page that provides a full explanation.

**OIM**
:   Omnia Infrastructure Manager. The dedicated management node that runs all Omnia control-plane services, including the `omnia_core` Ansible container, OpenCHAMI, Pulp, and telemetry collectors. The OIM is the single point from which the entire cluster is provisioned and managed. See [Architecture](architecture.md).

**BMC**
:   Baseboard Management Controller. A dedicated microcontroller embedded in server motherboards that provides out-of-band management capabilities (power control, hardware monitoring, remote console) independent of the host operating system. On Dell PowerEdge servers, the BMC is implemented as **iDRAC**.

**iDRAC**
:   Integrated Dell Remote Access Controller. Dell's implementation of the **BMC**, providing Redfish API access, remote console, virtual media, firmware management, and hardware telemetry for Dell PowerEdge servers. See [Telemetry Architecture](telemetry_architecture.md).

**PXE**
:   Preboot Execution Environment. An industry-standard protocol that allows servers to boot an operating system image over the network rather than from local disk. Omnia uses PXE for initial node discovery and OS provisioning.

**TFTP**
:   Trivial File Transfer Protocol. A simple file transfer protocol used during PXE boot to deliver the initial bootloader binary (typically **iPXE**) to bare-metal nodes.

**iPXE**
:   An open-source network bootloader that extends **PXE** with HTTP, iSCSI, and scripting capabilities. Omnia uses iPXE to chain to the **BSS** endpoint, which returns a customized boot script for each node.

**OpenCHAMI**
:   Composable Hierarchical Automated Management Infrastructure. The provisioning engine at the core of Omnia, providing API-driven node discovery, hardware inventory, and bare-metal lifecycle management. Includes **SMD** and **BSS** as sub-services. See [Components](components.md).

**SMD**
:   State Manager Daemon. The inventory and state-tracking service within **OpenCHAMI**. SMD maintains a real-time record of every node's hardware configuration, power state, and component hierarchy.

**BSS**
:   Boot Script Service. A component of **OpenCHAMI** that dynamically generates per-node boot scripts based on the node's hardware profile and assigned role. BSS is queried by **iPXE** during network boot.

**LDMS**
:   Lightweight Distributed Metric Service. A high-performance, low-overhead metric collection framework developed by Sandia National Laboratories for HPC environments. Omnia deploys LDMS agents on compute nodes to collect in-band OS and application metrics. See [Telemetry Architecture](telemetry_architecture.md).

**Slurm**
:   Simple Linux Utility for Resource Management. An open-source, highly scalable job scheduler and workload manager widely used in HPC clusters. Omnia deploys and configures Slurm for batch job scheduling on compute nodes. See [Architecture](architecture.md).

**AWX**
:   The open-source upstream project for Red Hat Ansible Automation Platform (formerly Ansible Tower). Provides a web-based UI and REST API for managing Ansible playbooks, inventories, and job scheduling. AWX is an optional component in Omnia.

**Podman**
:   A daemonless, rootless container engine for running OCI containers on Linux. Omnia uses Podman on the **OIM** to run all management services (`omnia_core`, OpenCHAMI, Pulp, OpenLDAP) as isolated containers without requiring Docker. See [Architecture](architecture.md).

**MetalLB**
:   A bare-metal load balancer for Kubernetes. MetalLB assigns external IP addresses to Kubernetes `LoadBalancer` services in environments without a cloud provider. Omnia deploys MetalLB automatically in the Kubernetes cluster.

**Calico**
:   A CNI (Container Network Interface) plugin for Kubernetes that provides pod-to-pod networking and network policy enforcement. Omnia deploys Calico as the default CNI in the Kubernetes cluster.

**NFS CSI**
:   NFS Container Storage Interface driver. A Kubernetes CSI driver that provisions persistent volumes backed by NFS shares, enabling shared storage across pods and Slurm compute nodes.

**Apptainer**
:   Formerly known as Singularity. A container runtime designed for HPC environments that allows users to run containers without root privileges. Supported on Slurm compute nodes in Omnia 2.1+.

**ROCm**
:   Radeon Open Compute. AMD's open-source software platform for GPU-accelerated computing. Omnia supports ROCm installation on nodes with AMD Instinct GPUs for AI/ML and HPC workloads.

**BuildStreaM**
:   Omnia's GitLab CI-based automation pipeline for catalog-driven deployment. Administrators define a deployment catalog (YAML manifest), and BuildStreaM generates a CI/CD pipeline that executes the required Ansible playbooks in order. See [Components](components.md).

**Functional Groups**
:   Named role definitions in Omnia's role assignment system. Each functional group (e.g., `slurm_node`, `service_kube_control_plane`) determines which software and configuration is applied to a server. Functional groups are assigned via the PXE mapping file during provisioning.

**Pulp**
:   An open-source repository management platform. Omnia deploys Pulp as a Podman container on the **OIM** to mirror RPM repositories, container images, and Python packages locally. Essential for air-gapped deployments. See [Components](components.md).

**Kafka**
:   Apache Kafka. A distributed event-streaming platform used as the central message broker in Omnia's telemetry pipeline. All metrics from **iDRAC** and **LDMS** flow through Kafka before reaching **VictoriaMetrics**. See [Telemetry Architecture](telemetry_architecture.md).

**VictoriaMetrics**
:   A high-performance time-series database that stores all telemetry data in Omnia's monitoring pipeline. Supports PromQL and MetricsQL for querying, and achieves high compression ratios for efficient long-term metric retention. See [Telemetry Architecture](telemetry_architecture.md).

**Grafana**
:   An open-source analytics and visualization platform. Omnia deploys Grafana with pre-built dashboards for cluster monitoring, GPU performance, power and thermal analysis, and Slurm job metrics. Connects to **VictoriaMetrics** as its data source. See [Telemetry Architecture](telemetry_architecture.md).
