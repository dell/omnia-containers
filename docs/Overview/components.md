
# Components


Omnia is not a single monolithic application. It is a composition of
purpose-built components, each addressing a specific aspect of cluster
lifecycle management---from provisioning bare-metal servers to managing local
software repositories to running authentication services. This page explains
what each component does, why it exists, and how it fits into the broader
Omnia architecture.

## omnia_core container


The `omnia_core` container is the heart of Omnia's control plane. It is a
Podman container that runs on the **OIM** and encapsulates the entire
Ansible toolchain---playbooks, roles, collections, Python dependencies, and
configuration templates.

**Why a container?**

Running Ansible inside a container solves several problems at once:

- **Reproducibility** -- Every Omnia deployment uses the exact same Ansible
  version, Python libraries, and role dependencies, regardless of what is
  installed on the host OS.
- **Isolation** -- The container's dependencies never conflict with system
  packages on the OIM.
- **Portability** -- The same container image works on RHEL 8.x, RHEL 9.x,
  Rocky 8.x, and Rocky 9.x without modification.
- **Upgradability** -- Upgrading Omnia is as simple as pulling a new container
  image; the previous image can be kept for rollback.

**What runs inside omnia_core?**

All Omnia playbooks execute from within this container, including:

- `prepare_oim.yml` -- Prepares the OIM node with required services.
- `provision.yml` -- Discovers and provisions bare-metal nodes.
- `omnia.yml` -- Deploys Slurm, Kubernetes, and supporting software.
- `telemetry.yml` -- Configures the monitoring and metrics pipeline.
- `security.yml` -- Sets up authentication and credential management.

The container mounts the Omnia configuration directory from the host so that
administrators can edit input templates (YAML files) using their preferred
editor before running playbooks.

!!! note

    The `omnia_core` container runs as a rootless Podman container by default.
    It uses host networking to reach managed nodes over SSH and escalates
    privileges on remote nodes via `become` (sudo), not via container
    privileges.

## OpenCHAMI


**OpenCHAMI** (Composable Hierarchical Automated Management Infrastructure) is
the provisioning engine at the core of Omnia's bare-metal lifecycle management.
Originally developed by the HPC community, OpenCHAMI provides a modern,
API-driven approach to discovering, inventorying, and provisioning large fleets
of servers.

OpenCHAMI replaces traditional tools like Cobbler or Foreman with a lightweight,
microservices-based architecture that runs entirely as Podman containers on the
OIM.

### State Manager Daemon (SMD)


SMD is the inventory and state-tracking service within OpenCHAMI. It maintains
a real-time view of every node in the cluster, including:

- **Hardware inventory** -- CPU model, core count, memory capacity, GPU
  presence, NIC details, and storage devices.
- **Node state** -- Whether a node is powered on, provisioning, ready, or in an
  error state.
- **Component hierarchy** -- Relationships between chassis, blades, nodes, and
  their BMC endpoints.

SMD populates its inventory automatically by querying each node's **iDRAC**
via the Redfish API during the discovery phase. Administrators can also update
inventory records via the `ochami-cli` command-line tool or the SMD REST API.

### Boot Script Service (BSS)


BSS dynamically generates boot scripts for each node based on its hardware
profile and the role assigned to it in the [Composable Roles](composable_roles.md) mapping file.
When a node PXE-boots, the following sequence occurs:

1. The node's NIC sends a DHCP request; **CoreDHCP** responds with an IP
   address and the location of the iPXE binary.
2. The node loads **iPXE** over TFTP and chains to the BSS endpoint.
3. BSS looks up the node's MAC address or service tag in SMD, determines the
   correct OS image and kernel parameters, and returns a customized boot script.
4. The node boots the assigned OS image.

This per-node customization means that heterogeneous clusters---where different
nodes run different OS versions or kernel configurations---are handled
seamlessly.

### ochami-cli


`ochami-cli` is the command-line interface for interacting with OpenCHAMI
services. It provides commands for:

- Listing and inspecting node inventory from SMD.
- Triggering node discovery and reprovisioning.
- Managing boot configurations in BSS.
- Querying node state and health.

!!! tip

    Use `ochami-cli node list` to quickly verify that all expected nodes have
    been discovered and are in the correct state before running deployment
    playbooks.

## Pulp


[Pulp](https://pulpproject.org/) is an open-source repository management
platform that Omnia deploys as a Podman container on the OIM. It acts as a
local mirror for all software packages required by the cluster.

**Why local repositories?**

- **Air-gapped deployments** -- Many HPC environments operate without direct
  internet access for security or compliance reasons. Pulp allows administrators
  to synchronize repositories once (or import them from portable media) and
  serve packages to all cluster nodes locally.
- **Bandwidth efficiency** -- In a 500-node cluster, downloading the same RPM
  package 500 times from the internet is wasteful. Pulp downloads each package
  once and serves it to all nodes over the local network.
- **Version consistency** -- Pulp snapshots ensure that every node installs the
  same package versions, preventing subtle configuration drift.
- **Speed** -- Local repository access over a high-speed admin network is
  dramatically faster than internet downloads, reducing provisioning time.

**What Pulp mirrors**

Pulp can mirror the following repository types:

- **RPM repositories** -- RHEL BaseOS, AppStream, EPEL, CUDA, ROCm, Slurm, and
  any custom RPM repositories.
- **Container images** -- OCI container images required by Kubernetes services
  and Omnia's own Podman containers.
- **Python packages** -- pip packages for data science and AI frameworks.

!!! note

    Pulp runs as a Podman container on the OIM and stores mirrored content on
    local disk. Plan disk capacity accordingly---a full RHEL + EPEL + CUDA mirror
    can require 200+ GB of storage.

## BuildStreaM


BuildStreaM is Omnia's GitLab CI-based automation pipeline that enables
catalog-driven deployment. Rather than running individual Ansible playbooks
manually, administrators define a deployment *catalog* (a YAML manifest) that
specifies the desired cluster state, and BuildStreaM translates that catalog
into an ordered pipeline of CI jobs.

**Key concepts**

- **Catalog** -- A declarative YAML file that describes which roles, packages,
  and configurations should be applied to which node groups.
- **Pipeline** -- A GitLab CI/CD pipeline auto-generated from the catalog. Each
  stage maps to an Ansible playbook or role.
- **Idempotency** -- Pipelines can be re-run safely; Ansible's idempotent design
  ensures that only necessary changes are applied.

**When to use BuildStreaM**

BuildStreaM is designed for environments where:

- Multiple administrators manage the same cluster and need an audit trail of
  changes (GitLab provides commit history and merge-request reviews).
- Deployments must be repeatable and version-controlled.
- The organization follows GitOps or Infrastructure-as-Code practices.

!!! tip

    BuildStreaM is optional. Omnia works perfectly well by running Ansible
    playbooks directly from the `omnia_core` container. BuildStreaM adds a
    CI/CD layer on top for teams that want automation, auditability, and
    catalog-driven workflows.

## Omnia Auth


Omnia Auth provides centralized identity and authentication services for the
cluster using **OpenLDAP**, deployed as a Podman container on a designated
`auth_server` node.

**What Omnia Auth provides**

- **User directory** -- A central LDAP directory where user accounts, groups,
  and SSH public keys are stored. All cluster nodes (Slurm and Kubernetes)
  authenticate against this single directory.
- **Consistent UIDs/GIDs** -- LDAP ensures that user and group IDs are
  identical across all nodes, which is critical for NFS file permissions and
  Slurm job accounting.
- **SSSD integration** -- Omnia configures SSSD (System Security Services
  Daemon) on every managed node to cache LDAP credentials locally, ensuring
  that users can still log in if the LDAP server is temporarily unreachable.

**Design rationale**

Centralized authentication is essential in multi-user HPC environments.
Without it, administrators would need to synchronize `/etc/passwd` and
`/etc/group` across hundreds of nodes manually---an error-prone and
unscalable approach. OpenLDAP is a mature, well-understood technology that
integrates with virtually every Linux distribution and application.

!!! info

    - [Security Configuration Guide](security_configuration_guide.md) -- How Omnia protects credentials and manages TLS
      certificates.
    - [Architecture](architecture.md) -- Where each component runs in the three-cluster
      model.

## Supporting services


In addition to the major components described above, Omnia deploys several
supporting services:

| Service | Description |
| --- | --- |
| **CoreDHCP** | Lightweight DHCP server for assigning IP addresses during PXE boot. Runs on the OIM. |
| **TFTP** | Trivial File Transfer Protocol server for delivering iPXE binaries to booting nodes. |
| **iPXE** | Network bootloader that replaces legacy PXE with HTTP-based boot, enabling more flexible boot script generation via BSS. |
| **AWX** *(optional)* | Web-based UI and REST API for Ansible Tower. Provides a graphical interface for running playbooks, managing inventories, and scheduling jobs. |
| **step-ca** | Internal certificate authority for issuing TLS certificates to cluster services. See [Security Configuration Guide](security_configuration_guide.md). |
| **Hydra** | OAuth 2.0 and OpenID Connect (OIDC) provider for token-based authentication between services. |

!!! info

    [Architecture](architecture.md) for a visual diagram of how these components are
    deployed across the OIM, Slurm, and Kubernetes clusters.

