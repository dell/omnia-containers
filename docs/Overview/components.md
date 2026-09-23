
# Components

Omnia is a composition of purpose-built components, each addressing a specific aspect of cluster lifecycle management---from provisioning bare-metal servers to managing local software repositories to running authentication services. This page explains what each component does and how it fits into the broader Omnia architecture.

## OIM control plane

The Omnia Infrastructure Manager (OIM) is the control plane for Omnia.
Administrators run `src/main/omnia.sh` directly on the OIM. The script installs
the shared environment, creates the Python virtual environment, initializes
the selected deployment modules, and invokes each module's Ansible entry
playbook from the source tree.

The module playbooks run locally on the OIM and connect to managed nodes over
SSH when remote configuration is required. Podman remains responsible for
service containers such as Pulp, OpenCHAMI, MinIO, the OCI registry, and Build
Stream components.

See [Running Deployment Modules](domain_execution.md) for the supported setup
and execution commands.

## OpenCHAMI

[OpenCHAMI](https://openchami.org/) (Open Composable Heterogeneous Adaptable Management
Infrastructure) is the provisioning engine at the core of Omnia's bare-metal
lifecycle management. OpenCHAMI provides an API-driven approach to discovering,
inventorying, and provisioning servers.

OpenCHAMI runs as a set of Podman containers on the OIM. The Orchestrator
`prepare` phase deploys and validates the OpenCHAMI services.

### State Management Database (SMD)

SMD is the inventory and state-tracking service within OpenCHAMI. Orchestrator
registers nodes and functional groups from the validated PXE mapping so that
the other provisioning services can resolve node identity and state. SMD
tracks information such as:

- **Node identity** -- xname, service tag, BMC address, and network identifiers.
- **Node state** -- The current state recorded for a managed node.
- **Group membership** -- The functional groups used to select boot and
  metadata configuration.

Administrators can query the registered inventory through the `ochami` CLI or
the SMD REST API exposed by the OpenCHAMI gateway.

### Boot service

`boot-service` stores the kernel, initrd, root-image, and kernel-parameter
configuration generated for each functional group. When a node PXE-boots, the
following sequence occurs:

1. The node's NIC sends a DHCP request; **CoreDHCP** responds with an IP address and the location of the iPXE binary.
2. The node loads **iPXE** over TFTP and requests the boot script through the
   HAProxy HTTP endpoint on port 8081.
3. `boot-service` matches the node to its registered boot configuration and
   returns the corresponding image locations and kernel parameters.
4. The node boots the assigned OS image and requests its first-boot data from
   `metadata-service`.

### Metadata service

`metadata-service` serves the NoCloud-compatible metadata and cloud-init
payloads that Orchestrator registers for common settings, functional groups,
and individual nodes. These payloads configure networking, hostnames, SSH
keys, package repositories, and other node-specific settings during first
boot.

### CoreDHCP and CoreDNS

- **CoreDHCP** (`coresmd-coredhcp`) -- Lightweight DHCP server for assigning IP addresses during PXE boot.
- **CoreDNS** (`coresmd-coredns`) -- DNS server that queries SMD every 30 seconds and automatically generates forward A records for all inventoried nodes, providing dynamic hostname resolution when `dns_enabled` is `true`. The source default is `false`.

### ochami CLI

`ochami` is the command-line interface for interacting with OpenCHAMI services. It provides commands for:

- Listing and inspecting node inventory from SMD.
- Managing `boot-service` configurations through the compatibility
  `ochami bss` command namespace.
- Querying node state and health.

### Supporting OpenCHAMI Services

| Service | Description |
| --- | --- |
| **HAProxy** | Routes host-facing HTTP and HTTPS requests to the internal OpenCHAMI services. |
| **TokenSmith** | Issues and validates tokens used for authenticated OpenCHAMI API operations. |
| **step-ca and ACME services** | Issue and deploy TLS certificates for the OpenCHAMI gateway. |
| **PostgreSQL** | Persistent database backend for SMD. |
| **boot-service** | Stores boot configurations and serves node boot scripts; it listens on port 8081 inside the Podman network. |
| **metadata-service** | Serves cloud-init data; it listens on port 8080 inside the Podman network. |
| **iPXE** | Network bootloader that retrieves its boot script through the HAProxy endpoint. |

MinIO and the local OCI registry are deployed by Image Build Manager rather
than as OpenCHAMI services. Orchestrator consumes the Image Build Manager S3
contract when it creates OpenCHAMI boot configurations.

## Pulp

[Pulp](https://pulpproject.org/) is an open-source repository management platform that Omnia deploys as a Podman container on the OIM. It acts as a local mirror for all software packages required by the cluster.

**Why local repositories?**

- **Air-gapped deployments** -- Many HPC environments operate without direct internet access. Pulp allows administrators to synchronize repositories once and serve packages to all cluster nodes locally.
- **Bandwidth efficiency** -- Pulp downloads each package once and serves it to all nodes over the local network, avoiding redundant internet downloads across hundreds of nodes.
- **Version consistency** -- Pulp snapshots ensure that every node installs the same package versions, preventing configuration drift.
- **Speed** -- Local repository access over a high-speed admin network is dramatically faster than internet downloads, reducing provisioning time.

**What Pulp mirrors**

Pulp can mirror the following repository types:

- **RPM repositories** -- RHEL BaseOS/AppStream/CodeReady Builder, EPEL, CUDA,
  NVIDIA HPC SDK, Kubernetes, CRI-O, DOCA, Docker CE, and user-required
  repositories (`slurm_custom`, `ldms`, and `vast`).
- **Container images** -- OCI container images required by Kubernetes services and Omnia's own containers.

The Repository Manager workflow configures Pulp mirroring from the selected
catalog and the project-scoped `repo_manager_config.yml`. Run it through
`./omnia.sh --run repo_manager` or select its documented phase tags.

!!! note

    Pulp runs as a Podman container on the OIM and stores mirrored content on
    local or NFS-shared disk. Plan disk capacity accordingly---a full RHEL +
    EPEL + CUDA mirror can require significant storage. For sizing guidance,
    see [Disk Space Requirements](../Reference/ClusterRequirements/disk_space.md).

## Omnia Auth

Omnia Auth provides centralized identity and authentication services for the
cluster using **OpenLDAP**. When OpenLDAP support is enabled, the Orchestrator
`prepare` phase deploys it as the `omnia_auth` Podman container on the OIM.

**What Omnia Auth provides**

- **User directory** -- A central LDAP directory for site-managed user and
  group entries. Omnia deploys the directory service but does not create users
  or groups.
- **Consistent UIDs/GIDs** -- LDAP provides consistent user and group IDs on
  configured clients, which is critical for NFS permissions and Slurm job
  accounting.
- **TLS encryption** -- LDAP communication is secured with TLS certificates.
- **SSSD integration** -- Omnia configures SSSD on the supported Slurm control,
  compute, and login functional groups. The current Kubernetes provisioning
  path does not configure an OpenLDAP client.

Centralized authentication is configured via `security_config.yml`.

## BuildStreaM

BuildStreaM is an optional automation framework that provides a REST API and
playbook execution pipeline for catalog-driven deployments. When enabled
(`enable_build_stream: true` in `build_stream_config.yml`), use the canonical
`src/build_stream/playbooks/build_stream.yml` domain entry point. The lifecycle
is divided into these operations:

- **`prepare`** -- Deploys the `omnia_build_stream` API server,
  `omnia_postgres` database, and playbook watcher on the OIM.
- **`execute`** -- Deploys and configures GitLab, creates the managed project
  and CI/CD configuration, and registers the project runner.
- **`build`** -- Runs both `prepare` and `execute` for a complete BuildStreaM
  deployment.

Run the complete flow through the Omnia wrapper:

```bash title="Run on: OIM host"
cd <OMNIA_SOURCE_PATH>/src/main
./omnia.sh --run build_stream --tags build
```

The `prepare` operation publishes the BuildStreaM output contract at:

```text
$OMNIA_DATA_PATH/build_stream/output/$OMNIA_PROJECT_NAME/build_stream_status.yml
```

A successful preparation records `overall_status: prepared`. GitLab pipeline
and job results are available through GitLab and BuildStreaM Manager rather
than through a separate pipeline-status file.

**Key capabilities**

- **Playbook watcher** -- A systemd service that monitors a playbook queue and executes Ansible playbooks in sequence.
- **JWT authentication** -- API access is secured via JSON Web Tokens.
- **GitLab integration** -- The BuildStreaM `execute` operation manages the
  GitLab project, pipeline files, triggers, and runner used for cluster
  deployments.

!!! tip

    BuildStreaM is optional. Omnia can run Ansible playbooks directly on the
    OIM through `omnia.sh`. BuildStreaM adds an automation layer for teams that
    want API-driven, catalog-based workflows.

!!! info "Related Pages"

    - [Architecture](architecture.md) -- Visual diagram of how components are deployed across the OIM and cluster nodes.
    - [BuildStreaM](../HowTo/build_stream/index.md) -- Configure and deploy the BuildStreaM domain.
    - [Module Playbook Entry Points](../Reference/Playbooks/playbook_reference.md) -- Review canonical domain entry points and operations.
    - [BuildStreaM Domain Contract](../Reference/domain_contracts/build_stream_contract.md) -- Review inputs, outputs, and managed services.





