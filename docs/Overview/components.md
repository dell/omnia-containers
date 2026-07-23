
# Components

Omnia is a composition of purpose-built components, each addressing a specific aspect of cluster lifecycle management---from provisioning bare-metal servers to managing local software repositories to running authentication services. This page explains what each component does and how it fits into the broader Omnia architecture.

## omnia_core Container

The `omnia_core` container is the control plane for Omnia. It is a Podman container that runs on the **OIM** and encapsulates the entire Ansible toolchain---playbooks, roles, collections, Python dependencies, and configuration templates.

**Why a container?**

Running Ansible inside a container solves several problems at once:

- **Reproducibility** -- Every Omnia deployment uses the exact same Ansible version, Python libraries, and role dependencies, regardless of what is installed on the host OS.
- **Isolation** -- The container's dependencies never conflict with system packages on the OIM.
- **Portability** -- The same container image works across supported RHEL versions without modification.
- **Upgradability** -- Upgrading Omnia is as simple as pulling a new container image; the previous image can be kept for rollback.

**What runs inside omnia_core?**

All Omnia playbooks execute from within this container, including:

- `prepare_oim.yml` -- Prepares the OIM node with required services and containers.
- `local_repo.yml` -- Synchronizes software repositories via Pulp.
- `provision.yml` -- Provisions bare-metal nodes via cloud-init, configures Slurm, Kubernetes, storage, and telemetry.
- `telemetry.yml` -- Deploys the telemetry and monitoring stack.

The container mounts the Omnia configuration directory from the host so that administrators can edit input files (YAML/JSON) using their preferred editor before running playbooks.

!!! note

    The `omnia_core` container is deployed and managed via the `omnia.sh` script on the OIM host. It uses host networking to reach managed nodes over SSH and escalates privileges on remote nodes via `become` (sudo), not via container privileges.

## OpenCHAMI

**OpenCHAMI** (Composable Hierarchical Automated Management Infrastructure) is the provisioning engine at the core of Omnia's bare-metal lifecycle management. OpenCHAMI provides an API-driven approach to discovering, inventorying, and provisioning servers.

OpenCHAMI runs as a set of Podman containers on the OIM, deployed during `prepare_oim.yml`.

### State Manager Daemon (SMD)

SMD is the inventory and state-tracking service within OpenCHAMI. It maintains a real-time view of every node in the cluster, including:

- **Hardware inventory** -- CPU model, core count, memory capacity, GPU presence, NIC details, and storage devices.
- **Node state** -- Whether a node is powered on, provisioning, ready, or in an error state.
- **Component hierarchy** -- Relationships between chassis, blades, nodes, and their BMC endpoints.

SMD populates its inventory by querying each node's **iDRAC** via the Redfish API during the discovery phase. Administrators can also query inventory via the `ochami` CLI or the SMD REST API.

### Boot Script Service (BSS)

BSS dynamically generates boot scripts for each node based on its hardware profile and the role assigned to it in the PXE mapping file. When a node PXE-boots, the following sequence occurs:

1. The node's NIC sends a DHCP request; **CoreDHCP** responds with an IP address and the location of the iPXE binary.
2. The node loads **iPXE** over TFTP and chains to the BSS endpoint.
3. BSS looks up the node's MAC address or service tag in SMD, determines the correct OS image and kernel parameters, and returns a customized boot script.
4. The node boots the assigned OS image with cloud-init configuration.

### Cloud-Init Server

The cloud-init server generates per-node cloud-init payloads that configure networking, hostname, SSH keys, package repositories, and other node-specific settings during the first boot.

### CoreDHCP and CoreDNS

- **CoreDHCP** (`coresmd-coredhcp`) -- Lightweight DHCP server for assigning IP addresses during PXE boot.
- **CoreDNS** (`coresmd-coredns`) -- DNS server that queries SMD every 30 seconds and automatically generates forward A records for all inventoried nodes, providing dynamic hostname resolution when `dns_enabled` is set to `true`.

### ochami CLI

`ochami` is the command-line interface for interacting with OpenCHAMI services. It provides commands for:

- Listing and inspecting node inventory from SMD.
- Managing boot configurations in BSS.
- Querying node state and health.

### Supporting OpenCHAMI Services

| Service | Description |
| --- | --- |
| **HAProxy** | Reverse proxy and TLS termination for OpenCHAMI API endpoints (port 8443). |
| **step-ca** | Internal certificate authority for issuing TLS certificates to OpenCHAMI services. |
| **Hydra** | OAuth 2.0 and OpenID Connect (OIDC) provider for token-based authentication between services. |
| **opaal** | Authentication and identity provider for OpenCHAMI API access. |
| **PostgreSQL** | Database backend for SMD, BSS, and Hydra. |
| **MinIO** | S3-compatible object storage for OS images and boot artifacts. |
| **Container Registry** | Local OCI container registry for storing container images used during provisioning. |
| **iPXE** | Network bootloader that enables HTTP-based boot and flexible boot script generation via BSS. |

## Pulp

[Pulp](https://pulpproject.org/) is an open-source repository management platform that Omnia deploys as a Podman container on the OIM. It acts as a local mirror for all software packages required by the cluster.

**Why local repositories?**

- **Air-gapped deployments** -- Many HPC environments operate without direct internet access. Pulp allows administrators to synchronize repositories once and serve packages to all cluster nodes locally.
- **Bandwidth efficiency** -- Pulp downloads each package once and serves it to all nodes over the local network, avoiding redundant internet downloads across hundreds of nodes.
- **Version consistency** -- Pulp snapshots ensure that every node installs the same package versions, preventing configuration drift.
- **Speed** -- Local repository access over a high-speed admin network is dramatically faster than internet downloads, reducing provisioning time.

**What Pulp mirrors**

Pulp can mirror the following repository types:

- **RPM repositories** -- RHEL BaseOS, AppStream, EPEL, CUDA, ROCm, Slurm, and any custom RPM repositories.
- **Container images** -- OCI container images required by Kubernetes services and Omnia's own containers.

The `local_repo.yml` playbook configures Pulp mirroring based on settings in `local_repo_config.yml`.

!!! note

    Pulp runs as a Podman container on the OIM and stores mirrored content on local or NFS-shared disk. Plan disk capacity accordingly---a full RHEL + EPEL + CUDA mirror can require significant storage.

## Omnia Auth

Omnia Auth provides centralized identity and authentication services for the cluster using **OpenLDAP**, deployed as the `omnia_auth` Podman container on the OIM during `prepare_oim.yml`.

**What Omnia Auth provides**

- **User directory** -- A central LDAP directory where user accounts, groups, and SSH public keys are stored. All cluster nodes authenticate against this single directory.
- **Consistent UIDs/GIDs** -- LDAP ensures that user and group IDs are identical across all nodes, which is critical for NFS file permissions and Slurm job accounting.
- **TLS encryption** -- LDAP communication is secured with TLS certificates.
- **SSSD integration** -- Omnia configures SSSD (System Security Services Daemon) on every managed node to cache LDAP credentials locally, ensuring that users can still log in if the LDAP server is temporarily unreachable.

Centralized authentication is configured via `security_config.yml`.

## BuildStream

BuildStream is an optional automation framework that provides a REST API and playbook execution pipeline for catalog-driven deployments. When enabled (`enable_build_stream: true` in `build_stream_config.yml`), Omnia deploys the following additional containers on the OIM during `prepare_oim.yml`:

- **omnia_build_stream** -- API server that manages deployment catalogs, job queues, and playbook execution.
- **omnia_postgres** -- PostgreSQL database for storing BuildStream state, job history, and image group metadata.

**Key capabilities**

- **Playbook watcher** -- A systemd service that monitors a playbook queue and executes Ansible playbooks in sequence.
- **JWT authentication** -- API access is secured via JSON Web Tokens.
- **GitLab integration** -- When used with the optional GitLab deployment (`gitlab/gitlab.yml`), BuildStream enables CI/CD pipeline execution for cluster deployments.

!!! tip

    BuildStream is optional. Omnia works by running Ansible playbooks directly from the `omnia_core` container. BuildStream adds an automation layer for teams that want API-driven, catalog-based workflows.

!!! info "Related Pages"

    - [Architecture](architecture.md) -- Visual diagram of how components are deployed across the OIM and cluster nodes.
