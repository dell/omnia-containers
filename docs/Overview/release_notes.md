
# Release Notes


This page summarizes the features, enhancements, and changes introduced in each
Omnia release. For detailed upgrade instructions, see the migration guide in
[Index](../GetStarted/index.md).

## Omnia 2.1.0.0


*Release type: Feature release*

Omnia 2.1 builds on the containerized architecture introduced in 2.0, adding
CI/CD-driven automation, expanded hardware support, and enhanced telemetry
capabilities.

### BuildStreaM -- GitLab CI automation


Omnia 2.1 introduces **BuildStreaM**, a GitLab CI-based automation pipeline
that enables catalog-driven deployment. Administrators define the desired
cluster state in a YAML catalog, and BuildStreaM translates it into an ordered
pipeline of CI/CD jobs that execute Ansible playbooks.

- Declarative catalog format for specifying roles, packages, and
  configurations.
- Automatic pipeline generation from catalog definitions.
- Full audit trail via GitLab commit history and merge-request reviews.
- Idempotent re-execution---pipelines can be safely re-run.

See [Components](components.md) for a detailed explanation of BuildStreaM's architecture.

### Additional packages and software


- **Apptainer** (formerly Singularity) support for running HPC containers on
  Slurm compute nodes without requiring root privileges.
- Expanded package deployment options for scientific libraries and AI/ML
  frameworks.
- Support for deploying additional custom RPM packages via the local Pulp
  repository.

### Slurm cluster management


- **Add and remove Slurm nodes** dynamically without disrupting running jobs.
  Administrators update the mapping file and re-run the Slurm playbook to
  scale the cluster up or down.
- Improved Slurm configuration management for heterogeneous node types.

### Telemetry enhancements


- **OpenManage Enterprise (OME) telemetry** -- Ingest fleet-level health and
  compliance data from OME into the Kafka → VictoriaMetrics → Grafana pipeline.
- **Smart Fabric Manager (SFM) telemetry** -- Collect network fabric metrics
  (switch port utilization, link errors, fabric health) for unified
  infrastructure monitoring.
- Enhanced Grafana dashboards for OME and SFM data.

### Storage integration


- **Dell PowerVault integration** -- Configure and mount PowerVault storage
  arrays as shared storage for Slurm compute nodes and Kubernetes persistent
  volumes.

### Network enhancements


- **InfiniBand support** -- Automated configuration of InfiniBand adapters and
  subnet manager settings for high-speed MPI and RDMA workloads.


## Omnia 2.0.0.0


*Release type: Major release*

Omnia 2.0 is a major architectural evolution that introduces Podman
containerization, local repository management, centralized authentication,
and a comprehensive telemetry pipeline.

### Podman containerization


Omnia 2.0 moves the entire control plane into Podman containers running on
the OIM:

- **omnia_core container** -- All Ansible playbooks execute inside a Podman
  container, ensuring reproducible and isolated management operations.
- **Service containers** -- OpenCHAMI, Pulp, OpenLDAP, and telemetry services
  each run as dedicated Podman containers.
- Rootless container execution for improved security.
- No Docker daemon required; Podman is available in default RHEL / Rocky Linux
  repositories.

See [Architecture](architecture.md) for the full containerization architecture.

### Local repository management with Pulp


- **Pulp** deployed as a Podman container on the OIM, mirroring RPM
  repositories, container images, and Python packages.
- Full support for air-gapped deployments---all packages are served from local
  Pulp mirrors.
- Repository snapshots ensure consistent package versions across all nodes.
- Dramatically faster provisioning via local high-speed network access.

See [Components](components.md) for details on Pulp's capabilities.

### Centralized authentication


- **OpenLDAP** deployed as a Podman container for centralized user and group
  management.
- **SSSD** configured on all managed nodes for LDAP-based authentication with
  local credential caching.
- Consistent UIDs and GIDs across all cluster nodes.

See [Security Configuration Guide](security_configuration_guide.md) for the full authentication architecture.

### Telemetry pipeline


- **iDRAC telemetry** -- Out-of-band hardware metrics (power, thermal, health)
  collected via Redfish and streamed through Kafka.
- **LDMS telemetry** -- In-band OS metrics (CPU, memory, network, I/O)
  collected via Lightweight Distributed Metric Service.
- **Apache Kafka** as the central message broker for decoupled, buffered
  metric transport.
- **VictoriaMetrics** for high-performance time-series storage with PromQL
  compatibility.
- **Grafana** with pre-built HPC dashboards for cluster, node, GPU, and job
  monitoring.

See [Telemetry Architecture](telemetry_architecture.md) for the full pipeline architecture.

### Kubernetes high availability


- Support for multiple `kube_control_plane` nodes behind a virtual IP for
  Kubernetes control-plane high availability.
- Automatic failover if the primary control-plane node becomes unavailable.

### Composable functional groups


- **Functional groups system** -- Servers are assigned to functional groups via
  a CSV mapping file, decoupling physical hardware from logical roles.
- A single server can hold multiple roles (e.g., Slurm control node + login
  node).
- User-defined groups for physical characteristics (GPU type, CPU
  architecture, memory capacity).

### Stateless boot


- **Stateless (diskless) boot** support for RHEL-based nodes, where the OS
  runs entirely from a network-delivered image. This simplifies node
  replacement (swap hardware, PXE boot, ready) and reduces local disk
  requirements.

### GPU and accelerator support


- **CUDA auto-install** -- Automatic detection and installation of NVIDIA GPU
  drivers and CUDA toolkit on nodes with NVIDIA GPUs.
- **ROCm support** -- AMD ROCm platform support for nodes with AMD Instinct
  GPUs.
- Slurm GRES (Generic RESource) configuration for GPU-aware job scheduling.

### Security enhancements


- **AES-256 encryption** via Ansible Vault for all credentials at rest.
- **step-ca** internal certificate authority for automated TLS certificate
  management.
- **Hydra** OAuth 2.0 / OIDC provider for service-to-service authentication.
- Credential utility for generating, rotating, and rekeying encrypted
  passwords.

See [Security Configuration Guide](security_configuration_guide.md) for details.

### Multi-architecture support


- **x86_64** (Intel and AMD) -- Full support for Intel Xeon and AMD EPYC
  processors.
- **aarch64** (ARM) -- Support for NVIDIA Grace CPU-based servers (e.g.,
  PowerEdge configurations with Grace ARM processors).

### Input templates and validator


- **YAML input templates** -- Pre-filled configuration templates that guide
  administrators through all required settings.
- **Input validator** -- A pre-flight check tool that validates all
  configuration files before playbook execution, catching errors (duplicate
  IPs, invalid service tags, missing fields) before any changes are made to
  the cluster.


## Supported platforms


| Category | Details |
| --- | --- |
| **Operating systems** | RHEL 8.8+, RHEL 9.2+, Rocky Linux 8.x, Rocky Linux 9.x |
| **Architectures** | x86_64 (Intel, AMD), aarch64 (NVIDIA Grace ARM) |
| **Dell PowerEdge servers** | R660, R760, R770, C6620, XE9680 (and other 15th/16th generation models) |
| **License** | Apache License 2.0 (open source) |
