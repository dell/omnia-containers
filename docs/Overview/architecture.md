# Architecture

## OMNIA Domain-Based Architecture

Omnia introduces a domain-based architecture that organizes functionality into independent, reusable domains with clear contracts and workflows. This architecture improves maintainability, scalability, and modularity of the infrastructure management platform.

## Architecture Overview

The domain-based architecture centers around the Omnia Infrastructure Manager (OIM) as the central control plane, with functionality organized into seven distinct domains:

## What Are Domains?

Omnia domains are specialized components that each handle a specific aspect of cluster deployment. Each domain:

- **Has a clear responsibility**: Each domain focuses on one aspect (e.g., discovery finds hardware, repo_manager handles packages)
- **Works independently**: Domains can run on their own without depending on other domains
- **Communicates through contracts**: Domains exchange information via standardized YAML files
- **Can be combined**: You can use just the domains you need for your specific deployment

This approach makes Omnia more flexible, easier to maintain, and simpler to scale as your cluster grows.

## OMNIA Architecture

![Omnia Architecture](../assets/images/omnia_arch_s.svg)

Omnia provides a comprehensive infrastructure management platform that orchestrates the deployment, configuration, and monitoring of HPC clusters. The architecture centers around the Omnia Infrastructure Manager (OIM), which serves as the central control plane for managing all cluster operations.

## OIM Role and Responsibilities

The OIM is the primary management node that coordinates all cluster activities.

- **Provisioning**: Manages the Bare System Setup (BSS) and cloud-init configurations to provision nodes from bare metal
- **Package Deployment**: Handles software distribution and configuration management across the cluster
- **Monitoring**: Collects and aggregates metrics, logs, and telemetry data from all cluster components
- **Orchestration**: Coordinates workflows for cluster operations including upgrades, scaling, and maintenance

## Node Relationships

The OIM (Omnia Infrastructure Manager) sits at the center and manages all provisioned nodes. It PXE-boots, configures, and monitors every node via OpenCHAMI, Ansible, and cloud-init.

- **Service Cluster**: Kubernetes cluster (k8s control-plane + worker nodes) running core services such as telemetry, logging, and scheduling
- **Slurm Control Node**: Runs Slurm management services (slurmctld, slurmdbd) and dispatches jobs to compute nodes
- **Compute Nodes**: Slurm-managed workload execution nodes
- **Login Nodes**: User access points for job submission and cluster interaction (includes login_compiler_node variant)
- **Storage Nodes**: Shared storage providers (NFS, PowerScale, VAST, MinIO) mounted by compute, login, and service nodes

All nodes receive their OS image, hostname, IP, and functional group from the OIM during provisioning. The OIM communicates over the admin network (SSH/Ansible) and optionally the BMC network (IPMI/Redfish) for out-of-band management. The OIM is the authoritative source of truth for cluster state and configuration.

## Component Integration

The architecture integrates three primary subsystems.

1. **Monitoring Service**: Collects metrics and logs from all cluster components using VictoriaMetrics and VictoriaLogs for time-series data storage and analysis
2. **Provisioning System**: Automates node provisioning through BSS and cloud-init, ensuring consistent configuration across the cluster
3. **Package Management**: Deploys and manages software packages using local repositories and build pipelines

These subsystems work together through the OIM's orchestration layer to provide a unified, automated infrastructure management experience.

- **repo_manager** - Repository mirroring and synchronization
- **image_build_manager** - Image building and S3 storage
- **discovery** - Node discovery and mapping file generation
- **orchestrator** - Slurm, Kubernetes, networking, storage, authentication
- **telemetry** - Monitoring and metrics collection
- **build_stream** - GitOps-based CI/CD pipelines
- **utils** - Helper utilities (backup, install, prepare)
- **main** - Setup, initialization, and cross-domain coordination

## Domain Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                     OIM (Omnia Infrastructure Manager)          │
│                                                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │ repo_manager │  │image_build_  │  │  discovery   │     │
│  │              │  │   manager    │  │              │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
│                                                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │ orchestrator │  │  telemetry   │  │ build_stream │     │
│  │              │  │              │  │              │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
│                                                               │
│  ┌──────────────┐  ┌──────────────┐                        │
│  │    utils     │  │    main      │                        │
│  │              │  │              │                        │
│  └──────────────┘  └──────────────┘                        │
└─────────────────────────────────────────────────────────────┘
```

## Domain Responsibilities

### repo_manager

The repo_manager domain handles repository mirroring, package synchronization, and local repository management using Pulp.

**Responsibilities**:
- Mirror external repositories to local storage
- Synchronize packages from remote to local
- Manage repository metadata and package inventory
- Support air-gapped deployments

**Dependencies**: None

**Output**: Synchronized package repositories in Pulp

### image_build_manager

The image_build_manager domain handles image creation, package installation, and image upload to S3 storage.

**Responsibilities**:
- Build diskless cluster images
- Install packages from repositories
- Upload images to S3 storage
- Generate image manifests with checksums

**Dependencies**: repo_manager

**Output**: Bootable diskless images in S3

### discovery

The discovery domain handles node inventory collection, mapping file generation, and hardware discovery.

**Responsibilities**:
- Discover cluster nodes via OME or manual methods
- Generate PXE mapping files
- Collect BMC and NIC information
- Validate node inventory

**Dependencies**: None

**Output**: PXE mapping files for node provisioning

### orchestrator

The orchestrator domain handles workload orchestration, service deployment, and cluster management.

**Responsibilities**:
- Deploy Slurm job scheduler
- Deploy Kubernetes services
- Configure networking (InfiniBand, Cluster DNS)
- Configure storage (NFS, PowerScale)
- Configure authentication (LDAP)
- Deploy OpenCHAMI provisioning stack
- PXE boot orchestration
- Telemetry deployment

**Dependencies**: repo_manager, image_build_manager, discovery

**Output**: Configured Slurm and/or Kubernetes clusters

### telemetry

The telemetry domain handles metrics collection, monitoring, and data aggregation.

**Responsibilities**:
- Collect iDRAC hardware telemetry
- Collect LDMS node-level metrics
- Collect storage metrics (PowerScale, VAST)
- Collect fabric metrics (UFM)
- Deploy monitoring stack (Kafka, VictoriaMetrics)

**Dependencies**: orchestrator

**Output**: Monitoring dashboards and metrics storage

### build_stream

The build_stream domain handles GitOps-based CI/CD pipelines for automated image building and deployment.

**Responsibilities**:
- Deploy GitLab CI/CD infrastructure
- Execute build pipelines from catalog
- Execute deploy pipelines to nodes
- Manage pipeline retries and cleanup

**Dependencies**: image_build_manager, orchestrator

**Output**: Automated image build and deploy workflows

### utils

The utils domain provides helper utilities for backup, installation, and node preparation.

**Responsibilities**:
- Backup Slurm configuration
- Perform unattended OS installation
- Prepare aarch64 nodes
- Provide auxiliary utilities

**Dependencies**: None

**Output**: Configuration backups, installation artifacts

### main

The main domain handles setup, initialization, and cross-domain coordination.

**Responsibilities**:
- Environment configuration (omnia.env)
- Setup and initialization (omnia.sh)
- Virtual environment creation
- Dependency installation
- Input file staging
- Cross-domain coordination

**Dependencies**: None

**Output**: Configured OIM environment, installed dependencies

## Domain Execution Model

### omnia.sh CLI

Omnia introduces the `omnia.sh` CLI for domain-based execution:

```bash
# Setup (one-time)
./omnia.sh -s

# Initialize domains
./omnia.sh --init

# Execute a single domain
./omnia.sh --run <domain> --tags <tag>

# Execute multiple domains
./omnia.sh --run repo_manager,image_build_manager --tags execute

# Validate configuration
./omnia.sh --validate

# Check domain status
omnia-cli status
```

### Execution Tags

Each domain supports standardized execution tags:

| Tag | Description |
|-----|-------------|
| `validate` | Validate configuration only |
| `credentials` | Collect and encrypt credentials |
| `prepare` | Deploy prerequisites (containers, services) |
| `execute` | Main domain workflow |
| `cleanup` | Remove infrastructure and artifacts |

### Domain Contracts

Each domain has input/output contracts that define:

- **Input files** - Required configuration files
- **Input parameters** - Configuration parameters
- **Output files** - Generated output files
- **Output artifacts** - Produced artifacts
- **Execution flow** - Step-by-step execution

See [Domain Contracts](../Reference/domain_contracts/) for detailed contract documentation.

## Typical Execution Order

When deploying a full cluster end-to-end, domains are executed in this order:

| Step | Domain | Purpose | Required |
|------|--------|---------|----------|
| 1 | **main** | Setup environment, install dependencies | Yes |
| 2 | **repo_manager** | Mirror RPM repos, generate `repo_status.yml` | Yes |
| 3 | **image_build_manager** | Build OS images using mirrored repos, upload to S3 | Yes |
| 4 | **discovery** | Discover servers via OME, generate PXE mapping | Optional |
| 5 | **orchestrator** | PXE boot nodes, deploy K8s/Slurm, configure services | Yes |
| 6 | **telemetry** | Enable iDRAC/UFM telemetry collection | Optional |

**BuildStream** orchestrates this sequence automatically via GitLab CI/CD pipeline, but each domain can also be run manually via `omnia.sh`.

## Node Relationships

The OIM (Omnia Infrastructure Manager) sits at the center and manages all provisioned nodes. It PXE-boots, configures, and monitors every node via domain-based execution.

- **Service Cluster**: Kubernetes cluster (k8s control-plane + worker nodes) running core services such as telemetry, logging, and scheduling
- **Slurm Control Node**: Runs Slurm management services (slurmctld, slurmdbd) and dispatches jobs to compute nodes
- **Compute Nodes**: Slurm-managed workload execution nodes
- **Login Nodes**: User access points for job submission and cluster interaction
- **Storage Nodes**: Shared storage providers (NFS, PowerScale, VAST, MinIO) mounted by compute, login, and service nodes

All nodes receive their OS image, hostname, IP, and functional group from the OIM during provisioning. The OIM communicates over the admin network (SSH/Ansible) and optionally the BMC network (IPMI/Redfish) for out-of-band management.

## Component Integration

The architecture integrates three primary subsystems through domain-based execution:

1. **Monitoring Service**: Collects metrics and logs from all cluster components using VictoriaMetrics and VictoriaLogs
2. **Provisioning System**: Automates node provisioning through BSS and cloud-init via the orchestrator domain
3. **Package Management**: Deploys and manages software packages using local repositories via the repo_manager domain

These subsystems work together through the OIM's domain-based orchestration layer to provide a unified, automated infrastructure management experience.

## Omnia Stack

Omnia provides two distinct deployment models tailored to different workload requirements: the Kubernetes Stack for containerized applications and the Slurm Stack for high-performance computing (HPC) workloads. These stacks can be deployed independently or in a converged configuration where both Kubernetes and Slurm coexist on the same infrastructure, enabling organizations to support diverse workload types within a single management framework.

The following diagrams illustrate the architectural layers and component relationships for each deployment model.

### Omnia Kubernetes Stack

![Omnia Kubernetes Stack](../assets/images/omnia-k8s.svg)

The Kubernetes stack provides a complete container orchestration platform for deploying and managing containerized applications. Key components include:

- **Hardware / Virtual Hardware**: Physical Dell servers or virtualized infrastructure that provide the compute resources for the Kubernetes cluster
- **Host OS / Virtual OS**: The operating system running on physical or virtual nodes that hosts Kubernetes components
- **Accelerator / Fabric Drivers**: Drivers and software that enable access to GPUs, accelerators, and high-speed networking fabrics
- **Container Runtime**: The runtime layer (such as containerd) responsible for creating and managing containers on each node
- **Orchestration**: Kubernetes services that schedule, deploy, scale, and manage containerized workloads across the cluster
- **Operators and Extensions**: Kubernetes operators, controllers, and add-ons that automate operations and extend cluster functionality
- **Load Balance and Ingress**: Services that provide traffic routing, load balancing, and external access to applications
- **Container**: An isolated environment that packages application components and dependencies for consistent execution
- **Libraries**: Shared software dependencies required by applications running within containers
- **Frameworks**: Development frameworks and platforms used to build and run containerized applications
- **User Application**: The application or workload deployed and managed within the Kubernetes environment
- **User**: Developers, administrators, or end users who interact with applications and services running on the cluster

### Omnia Slurm Stack

![Omnia Slurm Stack](../assets/images/omnia-slurm.svg)

The Slurm stack provides a workload manager optimized for HPC and batch job scheduling. Key components include:

- **Hardware / Virtual Hardware**: Physical Dell servers or virtualized infrastructure that provide compute resources for the cluster
- **Host OS / Virtual OS**: The operating system running on physical or virtual nodes that hosts the Slurm environment
- **Accelerator / Fabric Drivers**: Drivers and software that enable GPUs, accelerators, and high-performance networking fabrics for HPC workloads
- **Scheduling**: The Slurm workload manager that allocates resources, schedules jobs, and manages workload execution
- **Compilers and Runtimes**: Development toolchains and runtime environments required to build and execute HPC applications
- **Libraries**: Shared HPC and application libraries that provide functionality for scientific and compute-intensive workloads
- **User Application**: HPC applications, batch jobs, AI/ML workloads, and MPI programs executed on the cluster
- **User**: Researchers, developers, and administrators who submit, monitor, and manage workloads on the cluster

## Virtual Deployment Considerations

The diagrams show Virtual OS and Virtual Hardware blocks to represent scenarios where Omnia can be deployed on virtualized infrastructure. However, Omnia is primarily designed and tested for bare-metal deployments to ensure optimal performance for both Kubernetes and Slurm workloads. Virtual deployments may be supported for specific test or development scenarios, but production environments should use bare-metal hardware to avoid performance limitations and ensure full compatibility with all Omnia features.

## Migration from v2.2

For information on migrating from Omnia 2.2 to 2.3, see the [Migration Guide](../GetStarted/migration_guide.md).

## Related Documentation

- [Domain Execution](domain_execution.md)
- [Domain Contracts](../Reference/domain_contracts/repo_manager_contract.md)
- [Migration Guide](../GetStarted/migration_guide.md)


