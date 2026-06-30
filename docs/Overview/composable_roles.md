
# Composable Roles


Omnia uses a *composable roles* system that lets administrators define what
each server does by assigning it to one or more **functional groups**. Rather
than hard-coding server purposes, Omnia reads a mapping file that declaratively
associates physical servers with the roles they should perform. This page
explains the concept, the mapping file format, and the design decisions behind
this approach.

## What are composable roles?


In a traditional cluster deployment, each server typically serves a single
purpose: it is either a compute node, a login node, or a management node. This
one-to-one mapping is simple but inflexible---it wastes resources on
under-utilized servers and makes it difficult to adapt the cluster as workloads
change.

Omnia's composable roles system decouples *physical servers* from *logical
functions*. A single Dell PowerEdge server can simultaneously act as:

- A Slurm compute node **and** a Kubernetes worker node.
- A Slurm control node **and** a login node (common in small clusters).
- A Kubernetes control-plane node **and** an authentication server.

This composability allows administrators to right-size their clusters, making
full use of available hardware without deploying dedicated machines for every
function.


## Functional groups


A **functional group** is a named role that defines a set of software and
configuration to be applied to a server. Omnia defines the following built-in
functional groups:

**Built-in functional groups**

| Functional group | Description |
| --- | --- |
| `slurm_control_node` | Runs the Slurm controller daemon (`slurmctld`). Manages job queues, scheduling, and resource accounting. Exactly one node per Slurm cluster should hold this role. |
| `slurm_node` | Runs the Slurm compute daemon (`slurmd`). Executes batch jobs and parallel workloads. This is the most common role in an HPC cluster. |
| `login_node` | Provides an interactive shell environment for users to submit jobs, compile code, and manage data. Login nodes do not run compute workloads. |
| `login_compiler_node` | A login node that also includes development toolchains (compilers, debuggers, profilers) for users who need to build software on the cluster. |
| `service_kube_control_plane` | Runs the Kubernetes control-plane components (API server, etcd, scheduler, controller-manager). For high availability, multiple nodes can hold this role. |
| `service_kube_node` | Runs Kubernetes worker components (kubelet, kube-proxy). Hosts containerized application pods. |
| `auth_server` | Runs centralized authentication services (OpenLDAP in a Podman container). Provides the LDAP directory that all cluster nodes authenticate against. |

!!! note

    Functional groups are **additive**. Assigning a server to both
    `slurm_node` and `service_kube_node` causes Omnia to install and
    configure both Slurm and Kubernetes on that server. There is no conflict
    resolution---the administrator is responsible for ensuring that combined
    roles make sense for the workload.

## Groups based on physical characteristics


In addition to functional groups, Omnia supports grouping servers by their
**physical characteristics**---such as CPU architecture, GPU type, memory
capacity, or network connectivity. These physical groups enable administrators
to target Ansible playbooks at specific hardware profiles.

For example:

- A group named `gpu_a100` might contain all servers with NVIDIA A100 GPUs.
- A group named `arm_nodes` might contain all servers with NVIDIA Grace ARM
  CPUs.
- A group named `high_memory` might contain servers with 1 TB+ RAM for
  large-memory workloads.

These groups are user-defined and can be combined freely with functional groups
in the mapping file.


## The mapping file


The mapping file is a CSV file that tells Omnia which servers exist, what roles
they should play, and how they connect to the network. It is the single source
of truth for cluster composition.

### Format


Each row in the mapping file represents one server. The columns are:

**Mapping file columns**

| Column | Required | Description |
| --- | --- | --- |
| `FUNCTIONAL_GROUP_NAME` | Yes | The functional group(s) this server belongs to (e.g., `slurm_node`, `service_kube_node`). |
| `GROUP_NAME` | Yes | A user-defined group name for physical characteristics or organizational grouping (e.g., `gpu_a100`, `rack_01`). |
| `SERVICE_TAG` | Yes | The Dell service tag uniquely identifying the server (found on the physical chassis or via iDRAC). |
| `PARENT_SERVICE_TAG` | No | For blade servers or multi-node chassis, the service tag of the parent chassis. |
| `HOSTNAME` | No | The desired hostname for the server. If omitted, Omnia generates one automatically. |
| `ADMIN_MAC` | No | MAC address of the server's admin network NIC. Used for PXE boot identification. |
| `ADMIN_IP` | No | Static IP address to assign on the admin network. |
| `BMC_MAC` | No | MAC address of the server's BMC/iDRAC interface. |
| `BMC_IP` | No | IP address of the server's BMC/iDRAC interface for out-of-band management. |

### Example


```text title="Example: mapping.csv"
FUNCTIONAL_GROUP_NAME,GROUP_NAME,SERVICE_TAG,PARENT_SERVICE_TAG,HOSTNAME,ADMIN_MAC,ADMIN_IP,BMC_MAC,BMC_IP
slurm_control_node,manager,ABC1234,,head01,aa:bb:cc:dd:ee:01,10.10.1.10,aa:bb:cc:dd:ff:01,10.20.1.10
slurm_node,gpu_a100,DEF5678,,gpu01,aa:bb:cc:dd:ee:02,10.10.1.11,aa:bb:cc:dd:ff:02,10.20.1.11
slurm_node,gpu_a100,GHI9012,,gpu02,aa:bb:cc:dd:ee:03,10.10.1.12,aa:bb:cc:dd:ff:03,10.20.1.12
service_kube_control_plane,kube_mgmt,JKL3456,,k8s-cp01,aa:bb:cc:dd:ee:04,10.10.1.20,aa:bb:cc:dd:ff:04,10.20.1.20
service_kube_node,kube_workers,MNO7890,,k8s-w01,aa:bb:cc:dd:ee:05,10.10.1.21,aa:bb:cc:dd:ff:05,10.20.1.21
login_node,login,PQR1234,,login01,aa:bb:cc:dd:ee:06,10.10.1.30,aa:bb:cc:dd:ff:06,10.20.1.30
auth_server,auth,STU5678,,auth01,aa:bb:cc:dd:ee:07,10.10.1.40,aa:bb:cc:dd:ff:07,10.20.1.40
```


In this example:

- `ABC1234` is the Slurm controller.
- `DEF5678` and `GHI9012` are GPU compute nodes grouped as `gpu_a100`.
- `JKL3456` is the Kubernetes control-plane node.
- `MNO7890` is a Kubernetes worker node.
- `PQR1234` is a login node.
- `STU5678` runs the authentication server.


## How Omnia processes the mapping file


When you run Omnia's provisioning or deployment playbooks, the following
sequence occurs:

1. **Parsing** -- Omnia reads the mapping file and constructs an Ansible
   inventory dynamically. Each `FUNCTIONAL_GROUP_NAME` becomes an Ansible
   host group; each `GROUP_NAME` becomes a child group.

2. **Validation** -- The input validator checks for duplicate service tags,
   conflicting IP assignments, and missing required fields. Errors are reported
   before any changes are made to the cluster.

3. **Role application** -- Ansible playbooks are executed against the
   appropriate host groups. For example, the Slurm playbook targets the
   `slurm_control_node` and `slurm_node` groups, while the Kubernetes
   playbook targets `service_kube_control_plane` and `service_kube_node`.

4. **Idempotent convergence** -- Playbooks are idempotent; re-running them
   with the same mapping file produces no changes. Modifying the mapping file
   (e.g., adding a new `slurm_node` row) and re-running the playbook
   provisions only the new node.

!!! tip

    Always run the Omnia input validator before applying changes. The validator
    catches common mistakes---such as assigning the same IP to two servers or
    using an invalid service tag---before any disruptive changes are made.

## Design rationale


**Declarative over imperative** -- The mapping file is a declarative
specification of the cluster's desired state. Administrators say *what* they
want, not *how* to get there. Omnia figures out the steps.

**Single source of truth** -- All node-to-role assignments live in one file.
There is no need to maintain separate inventory files for Slurm, Kubernetes,
and provisioning---the mapping file drives all of them.

**Flexibility for heterogeneous hardware** -- HPC clusters often contain a mix
of server generations, CPU architectures, and accelerators. The combination of
functional groups and physical groups allows administrators to target specific
configurations to specific hardware without duplication.

**Multi-role servers** -- In small or budget-constrained clusters, dedicating a
server to each role is impractical. Composable roles let a three-server cluster
run a Slurm controller, Kubernetes control plane, and login node on a single
machine, with the remaining two servers handling compute workloads.

!!! info

    - [Architecture](architecture.md) -- How the three cluster types map to functional
      groups.
    - [Network Topologies](network_topologies.md) -- How Admin and BMC IP addresses in the mapping
      file relate to network segments.
