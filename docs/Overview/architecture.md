# Architecture

## OMNIA v2.3 Domain-Based Architecture

Omnia v2.3 introduces a domain-based architecture that organizes functionality into independent, reusable domains with clear contracts and workflows. This architecture improves maintainability, scalability, and modularity of the infrastructure management platform.

## Architecture Overview

The domain-based architecture centers around the Omnia Infrastructure Manager (OIM) as the central control plane, with functionality organized into seven distinct domains:

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
- Configure networking (InfiniBand, DNS)
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

Omnia v2.3 introduces the `omnia.sh` CLI for domain-based execution:

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

Omnia provides two distinct deployment models tailored to different workload requirements: the Kubernetes Stack for containerized applications and the Slurm Stack for high-performance computing (HPC) workloads. These stacks can be deployed independently or in a converged configuration where both Kubernetes and Slurm coexist on the same infrastructure.

### Omnia Kubernetes Stack

The Kubernetes stack provides a complete container orchestration platform. Key components include:

- **Hardware / Virtual Hardware**: Physical Dell servers or virtualized infrastructure
- **Host OS / Virtual OS**: The operating system running on physical or virtual nodes
- **Accelerator / Fabric Drivers**: Drivers and software that enable access to GPUs, accelerators, and high-speed networking
- **Container Runtime**: Runtime layer (containerd) for managing containers
- **Orchestration**: Kubernetes services for scheduling and managing workloads
- **Operators and Extensions**: Kubernetes operators and add-ons for automation
- **Load Balance and Ingress**: Services for traffic routing and external access
- **Container**: Isolated environment for application components
- **Libraries**: Shared software dependencies
- **Frameworks**: Development platforms for applications
- **User Application**: Workloads deployed and managed in Kubernetes
- **User**: Developers and administrators managing workloads

### Omnia Slurm Stack

The Slurm stack provides a workload manager optimized for HPC and batch job scheduling. Key components include:

- **Hardware / Virtual Hardware**: Physical Dell servers or virtualized infrastructure
- **Host OS / Virtual OS**: The operating system running on nodes
- **Accelerator / Fabric Drivers**: Drivers for GPUs, accelerators, and high-performance networking
- **Scheduling**: Slurm workload manager for resource allocation and job scheduling
- **Compilers and Runtimes**: Development toolchains and runtime environments
- **Libraries**: Shared HPC and application libraries
- **User Application**: HPC applications, batch jobs, AI/ML workloads, MPI programs
- **User**: Researchers and administrators managing workloads

## Migration from v2.2

For information on migrating from Omnia 2.2 to 2.3, see the [Migration Guide](../GetStarted/migration_guide.md).

## Related Documentation

- [Domain Execution](domain_execution.md)
- [Domain Contracts](../Reference/domain_contracts/repo_manager_contract.md)
- [Migration Guide](../GetStarted/migration_guide.md)


