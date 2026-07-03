# Prerequisites Checklist


Complete **every** item on this checklist before starting any deployment path.
Skipping a prerequisite is the single most common cause of failed deployments.

!!! tip

    Print this page and physically check off each item as you verify it in
    your datacenter. Hand it to your rack-and-stack technician alongside the
    server placement diagram.

## Hardware Requirements


### Servers

| ☑ | Requirement | Details |
| --- | --- | --- |
| ☐ | Dell PowerEdge servers (16th or 17th generation) | Omnia v2.2 supports 16G and 17G PowerEdge servers. |
| ☐ | Intel 16G models | Supported: C6620, R660, R760, R760xa, R760xd2, R260, R360. Validated: R660, R260, C6620. |
| ☐ | AMD 16G models | Supported: R6625, R7625, R6615. Validated: R7625. |
| ☐ | AMD 17G models | Supported: R6725, R7725, R6715, R7715, R7725xd. Validated: R7725xd. |
| ☐ | NVIDIA Grace 17G models | Supported: XE8712 with GB200. Validated: XE8712 with GB200. |

!!! note

    For aarch64 architecture platforms, limited validation has been performed on early access systems.

### NICs

| ☑ | Requirement | Details |
| --- | --- | --- |
| ☐ | Supported NICs installed in every target node | At least one NIC port must be PXE-capable. |
| ☐ | Intel NICs | Supported: Ethernet 10G 4P X710/I350 rNDC, Ethernet Converged Network Adapter X710, 25GbE Ethernet Network Adapter E810, 100GbE Ethernet Network Adapter E810, I350GbE Ethernet Controller. |
| ☐ | Broadcom NICs | Supported: 10GBASE-T Ethernet, Gigabit Ethernet BCM5720, Adv Dual 10GBASE-T Ethernet, Adv Dual 25Gb Ethernet, NetXtreme Gigabit Ethernet, BCM5760x. |

### Switches

| ☑ | Requirement | Details |
| --- | --- | --- |
| ☐ | Network switches racked and cabled | One admin/data switch and one BMC management switch at minimum. InfiniBand switch required only if using IB fabric. |
| ☐ | Dell PowerSwitch models | Supported: S3048-ON, S5232F-ON, Z9264F-ON, N3248TE-ON, S4148, Z9664F, Z9432-ON, Z9864F-ON.<br>Validated: S3048-ON, S5232F-ON, S4148, Z9432-ON. |
| ☐ | OS10 installed on Ethernet switches | Omnia requires **OS10** on Ethernet switches. Switches running SONiC OS must be configured manually. |

!!! note

    Switches that have reached EOL might not function properly. Use switch models listed in the support matrix.

### Storage

| ☑ | Requirement | Details |
| --- | --- | --- |
| ☐ | Dell PowerScale (if applicable) | Supported and validated models: H500, F600. |
| ☐ | Dell PowerVault (if applicable) | Supported and validated model: ME5084. |


## OIM (Management Node) Requirements


The **Omnia Infrastructure Manager (OIM)** is the single node from which
all Omnia playbooks execute. It does *not* participate in the compute
cluster.

| ☑ | Requirement | Details |
| --- | --- | --- |
| ☐ | Choose a server **outside** your intended cluster | The OIM must meet the required storage and system requirements. |
| ☐ | 64 GB RAM minimum | Verify with `free -h`. The `omnia_core` and `omnia_auth` Podman containers, local repos, and image-building tasks are memory-intensive. |
| ☐ | RHEL 10.0 with Server with GUI Base Environment | Minimal installs are not supported. The GUI group pulls in required libraries used by Ansible and Podman. See [supported operating systems](https://omnia.readthedocs.io/en/v2.2.0.0-rc1/Overview/SupportMatrix/OperatingSystems/index.html). |
| ☐ | Podman container engine installed | Verify: `podman --version`. If missing, install via `dnf install -y podman`. |
| ☐ | Two active NIC ports | **NIC 1 (public):** Internet-facing, for downloading packages and container images. **NIC 2 (internal/admin):** Connected to the admin switch for PXE provisioning and cluster management. |
| ☐ | Internet access (direct or via proxy) | Required during `local_repo.yml` to pull OS packages, Python modules, and container images. After repo sync, air-gapped operation is possible. |
| ☐ | Git installed | `dnf install git -y`. Needed to clone the Omnia repository. |
| ☐ | 500 GB+ free disk on / | Local repos, container images, and node OS images consume significant space. Use `df -h /` to check. |
| ☐ | Required ports open on OIM | See [Ports Used by the OIM](#ports-used-by-the-oim) below for the complete list of ports that must be available. |
| ☐ | `omnia_core` and `omnia_auth` containers deployed | See [Deploy Omnia Core Container](../HowTo/Setup/deploy_omnia_core.md) for instructions. |
| ☐ | All target bare-metal servers reachable from OIM | Ensure network connectivity from OIM to all cluster nodes. |

### Ports Used by the OIM

Omnia uses the following ports on the OIM. Ensure these ports are not assigned to any other services.

**Container Ports**

| Container Name | Port |
| --- | --- |
| Core Container | 2222 |
| Pulp Container | 2225 |

**OpenCHAMI Ports**

| Port | Protocol | Service |
| --- | --- | --- |
| 9000, 9001 | TCP | minio-server |
| 5000 | TCP | registry |
| 9000 | TCP | step-ca |
| 5432 | TCP | postgres |
| 27779 | TCP | smd |
| 27778 | TCP | bss |
| 80, 443 | TCP | haproxy |
| 22 | UDP | ssh-udp |
| 67 | UDP | dhcp-udp |
| 68 | UDP | bootpc |
| 69 | UDP | tftp-udp |
| 636, 389 | TCP | omnia_auth |

**Telemetry Ports**

| Port | Protocol | Service |
| --- | --- | --- |
| 6001–6100 | TCP | LDMS aggregator |
| 6001–6100 | TCP | LDMS store daemon |
| 10001–10100 | TCP | LDMS sampler |
| 9092, 9093 | TCP | Kafka |
| 9094 | TCP | Kafka LoadBalancer |
| 8443 | TCP | VictoriaMetrics service |
| 8480 | TCP | VictoriaMetrics LB Insert |
| 8481 | TCP | VictoriaMetrics LB Query |
| 4318 | TCP | CSM Metrics PowerScale exporter |
| 8889 | TCP | OTEL Collector (Prometheus) |
| 514 | TCP, UDP | PowerScale Syslog receiver |
| 9481 | TCP | VictoriaLogs vlinsert |
| 9471 | TCP | VictoriaLogs vlselect |
| 9491 | TCP | VictoriaLogs vlstorage (HTTP) |
| 9400 | TCP | VictoriaLogs vlstorage insert |
| 9401 | TCP | VictoriaLogs vlstorage select |
| 9429 | TCP | VictoriaLogs vlagent |

## Networking Prerequisites


| ☑ | Requirement | Details |
| --- | --- | --- |
| ☐ | Admin and BMC switches configured and reachable | Ensure admin and BMC switches are properly configured. |
| ☐ | Admin network switch configured | A dedicated VLAN or flat L2 segment connecting OIM NIC 2 to all target-node admin NICs. DHCP must not already be running on this segment (Omnia provides its own). |
| ☐ | BMC network switch configured | A separate VLAN or segment connecting OIM to all target-node iDRAC BMC ports. Can share a physical switch with admin if VLANs are used. |
| ☐ | IP ranges planned for admin and BMC subnets | You will enter these CIDRs in `network_spec.yml`. Example: admin `10.5.0.0/16`, BMC `10.3.0.0/16`. |
| ☐ | No conflicting DHCP servers on admin or BMC subnets | Omnia's DHCP (via `prepare_oim.yml`) must be the sole DHCP source on the PXE/admin network. |
| ☐ | InfiniBand Subnet Manager running (if using IB fabric) | Ensure the Subnet Manager (SM) service is enabled and running on the InfiniBand switch or host. Failure to meet this prerequisite may result in InfiniBand ports remaining in the Initializing state. |
| ☐ | DNS resolution working on OIM | `nslookup google.com` must succeed. Configure `/etc/resolv.conf` or NetworkManager DNS if needed. |

## NFS / Storage Prerequisites


| ☑ | Requirement | Details |
| --- | --- | --- |
| ☐ | NFS server reachable from OIM and all cluster nodes | Dell PowerScale (H500, F600), PowerVault (ME5084), or any NFS-capable appliance. Choose an NFS server located outside your cluster. |
| ☐ | NFS share accessible from all nodes | Ensure the external NFS share is accessible from all nodes (both diskless and diskful) and is reachable via the admin network. |
| ☐ | Export permissions: `755`, `no_root_squash` | `no_root_squash` is required so Ansible (running as root) can write to NFS-mounted paths. To enable, edit `/etc/exports`: `/<your_exported_path> *(rw,sync,no_root_squash,no_subtree_check)` |
| ☐ | PowerScale NFSv4 settings (if using NFSv4) | If PowerScale is configured with NFSv4, enable the following to prevent `nobody:nobody` ownership: `nfsv4-no-names=true`, `nfsv4-no-domain=true`, `nfsv4-no-domain-uids=true`, `nfsv4-allow-numeric-ids=true`. See [Dell KB 000023023](https://www.dell.com/support/kbdoc/en-us/000023023). |
| ☐ | Minimum storage capacity allocated | **Kubernetes NFS:** 200 GB \| **Slurm NFS:** 50 GB \| **OIM NFS:** 200 GB. Increase based on cluster size. |
| ☐ | Dedicated mount point for each NFS | Ensure there is a dedicated mount point for each NFS (K8s, Slurm, OIM). |
| ☐ | NFS exports tested from OIM | `mount -t nfs <nfs_server>:/export /mnt/test && ls /mnt/test` |

!!! info "PowerScale NFSv4 CLI Configuration"

    To configure PowerScale NFSv4 settings via CLI, run:

    ```shell
    isi nfs settings zone modify \
      --nfsv4-no-names=true \
      --nfsv4-no-domain=true \
      --nfsv4-no-domain-uids=true \
      --nfsv4-allow-numeric-ids=true \
      --zone=System
    ```

    **Important considerations:**

    - Ensure UID/GID mappings are consistent across all NFS client nodes and the PowerScale cluster. Numeric ID mode bypasses name-based identity resolution, so mismatched UIDs/GIDs will result in incorrect file ownership.
    - This setting degrades NFSv4 ACL support. If your environment requires NFSv4 ACLs, consider aligning the NFSv4 domain between PowerScale and all clients instead.

### PowerScale S3 Storage (if applicable)

| ☑ | Requirement | Details |
| --- | --- | --- |
| ☐ | PowerScale cluster within admin subnet | Must be accessible from all cluster nodes. |
| ☐ | S3 and HTTP services enabled | Omnia uses HTTP access only (default port 9020). |
| ☐ | Valid S3 Access Key ID and Secret Access Key | Required for authentication. S3 keys are tightly associated with S3 buckets. |

## RHEL Subscriptions and Repositories


| ☑ | Requirement | Details |
| --- | --- | --- |
| ☐ | RHEL subscription active on OIM | `subscription-manager status` must show **Current**. Required for `AppStream`, `BaseOS`, and `codeready-builder` repos. |
| ☐ | Docker Hub credentials available | A Docker Hub account (free tier is sufficient) is needed for pulling container images during `local_repo.yml`. |
| ☐ | OIM has access to public network | Required to download and store packages/images to the desired NFS share. |
| ☐ | Certificates stored using Ansible Vault | Ensure all required certificates are stored using Ansible Vault for confidentiality and integrity within the cluster. |
| ☐ | All repository URLs accessible | Verify that all repository URLs for software packages are accessible. If not, the download will fail for that specific package. |
| ☐ | RHEL release pinned to 10.0 | By default, an active RHEL subscription may configure the repository to RHEL 10.1. Omnia requires RHEL 10.0. Verify and set: `subscription-manager release --show` and `sudo subscription-manager release --set=10.0` |

## BIOS Settings on Target Nodes


Apply these settings to every target node (compute, head, login, K8s)
via iDRAC or BIOS Setup (F2 at POST).

| ☑ | Setting | Value |
| --- | --- | --- |
| ☐ | System Profile (Performance) | Set **System Profile** to `Performance` in BIOS > System Profile Settings. This maximizes CPU frequency and disables power-saving C-states. |
| ☐ | Power Cap disabled | BIOS > System Profile Settings > Power Cap Policy: **Disabled**. Power capping can throttle CPUs during Slurm jobs. |
| ☐ | PXE boot enabled on admin NIC | BIOS > Network Settings > NIC Configuration > enable **PXE Boot** on the NIC connected to the admin switch. Disable PXE on all other NICs to avoid boot-order confusion. |
| ☐ | Boot order: NIC first, then disk | BIOS > Boot Settings > Boot Sequence: move the PXE-enabled NIC above the hard drive. After initial provisioning, Omnia configures disk-first boot automatically. |
| ☐ | Virtualization Technology (VT-x/VT-d) enabled | Required for K8s nodes running containerized workloads. |
| ☐ | SR-IOV enabled (if using SR-IOV NICs) | BIOS > Integrated Devices > SR-IOV Global Enable: **Enabled**. |

## iDRAC Settings


| ☑ | Setting | Value |
| --- | --- | --- |
| ☐ | Redfish API enabled | iDRAC Settings > Network > Services: **Redfish** enabled. Omnia uses Redfish for out-of-band discovery and firmware inventory. |
| ☐ | iDRAC firmware updated to latest version | Download from [Dell Support](https://www.dell.com/support). |
| ☐ | Datacenter license installed (for telemetry) | The Datacenter license enables streaming telemetry via iDRAC. Enterprise license is insufficient. |
| ☐ | iDRAC IP assigned on BMC network | Can be DHCP (Omnia will assign) or static. If static, record each iDRAC IP for the mapping file. |
| ☐ | Default iDRAC credentials known | Factory default is `root` / `calvin`. If changed, you must provide the current credentials in `provision_config.yml`. |

## Aarch64 Node Prerequisites


| ☑ | Requirement | Details |
| --- | --- | --- |
| ☐ | Disk available for Full OS installation | You must install the OS manually on aarch64 nodes. |
| ☐ | IP address assigned with PXE network connectivity | Ensure the aarch64 node has an IP and connectivity to the PXE network. |
| ☐ | Same NFS share as OIM reachable | Ensure the NFS share used in OIM is also reachable on the aarch64 node. |

## Service Kubernetes (K8s) Requirements


| ☑ | Requirement | Details |
| --- | --- | --- |
| ☐ | Minimum 3 Kubernetes controller nodes allocated | Kubernetes HA requires an odd number of control-plane nodes (3 or 5). Each must have 64 GB RAM minimum. |
| ☐ | At least 1 kube node allocated | Kube nodes run telemetry collectors and monitoring services such as VictoriaMetrics. 64 GB RAM minimum. |
| ☐ | Dedicated IP range for K8s pod and service networks | Defaults: pod CIDR `10.244.0.0/16`, service CIDR `10.96.0.0/12`. These must not overlap with admin or BMC subnets. |
| ☐ | Virtual IP (VIP) reserved for K8s API HA | A single unused IP on the admin network that `kube-vip` will float across control-plane nodes. |

## Slurm Prerequisites


| ☑ | Requirement | Details |
| --- | --- | --- |
| ☐ | Each Slurm compute node has at least 64 GB RAM | Verify with `free -h`. |
| ☐ | Slurm RPMs available in user repository | If not available, refer to the [Slurm Quick Start Administrator Guide](https://slurm.schedmd.com/quickstart_admin.html) for building Slurm RPMs. |
| ☐ | Slurm repo URL configured in `local_repo_config.yml` | Update `user_repo_url_x86_64` or `user_repo_url_aarch64` in `/opt/omnia/input/project_default/local_repo_config.yml` with the hosted Slurm repository URL. |
| ☐ | Mixed architecture: Slurm binaries for both architectures | In environments with x86_64 control nodes and aarch64 compute nodes, ensure Slurm binaries for both architectures are compiled and available. |
| ☐ | Slurm RPM names match config | After generating Slurm RPMs, verify names match those in `input/config/x86_64/rhel/10.0/slurm_custom.json`. |

### CUDA and DCGM Prerequisites (for Slurm GPU Nodes)

| ☑ | Requirement | Details |
| --- | --- | --- |
| ☐ | NVIDIA GPU hardware present | Must be present on any Slurm node intended for GPU workloads. Nodes without GPU hardware are automatically skipped. |
| ☐ | CUDA repository accessible | Must be reachable via the local Pulp repository configured during `local_repo.yml` execution. |
| ☐ | DCGM repository available | Must be available in the configured local repository. |
| ☐ | NFS path for HPC tools reachable | The shared NFS path for Slurm HPC tools must be reachable from all Slurm compute and login/compiler nodes. Minimum 30 GB recommended for `hpc_tools/cuda`. The NFS share must be exported with `no_root_squash`. |

## LDAP Prerequisites


| ☑ | Requirement | Details |
| --- | --- | --- |
| ☐ | LDAP server details available | Required to configure the `omnia_auth` container and OpenLDAP. See [Deploy External LDAP](../HowTo/Authentication/deploy_external_ldap.md). |
| ☐ | External OpenLDAP server deployed (if applicable) | Ensure the OpenLDAP server is deployed and configured with the required directory structure (users and groups). See [External LDAP Deployment](../HowTo/Authentication/deploy_external_ldap.md). |

## LDMS Prerequisites


| ☑ | Requirement | Details |
| --- | --- | --- |
| ☐ | EPEL and AppStream repositories configured | Ensure `python3-devel` and `python3-Cython` are installed: `sudo dnf install -y python3-devel python3-Cython` |
| ☐ | LDMS RPM available in user repository | If not available, refer to [Building LDMS PRODUCER RPM Package](https://github.com/dell/omnia-artifactory?tab=readme-ov-file). Update `ldms.json` accordingly. |
| ☐ | LDMS repo URL configured in `local_repo_config.yml` | Update `user_repo_url_x86_64` or `user_repo_url_aarch64` in `/opt/omnia/input/project_default/local_repo_config.yml` with the hosted LDMS repository URL. |

## BuildStreaM Prerequisites


| ☑ | Requirement | Details |
| --- | --- | --- |
| ☐ | Dedicated node for BuildStreaM GitLab deployment | A separate node is required for GitLab. |
| ☐ | Minimum system resources for BuildStreaM node | 4 GB RAM, 2 CPU cores, 20 GB free disk space. GitLab requires a minimum of 2 CPU cores; more may be needed for production workloads. |
| ☐ | Network connectivity for GitLab services | Ensure the BuildStreaM node has network access. |
| ☐ | BuildStreaM containers deployed on OIM | Ensure that Omnia BuildStreaM container, PostgreSQL container, and Playbook Watcher service are deployed. See [Prepare OIM](../HowTo/Setup/prepare_oim.md). |

## Final Pre-Flight Checks


Run these commands on the OIM before starting any deployment path:

```shell title="Run on OIM (as root)"
# Verify OS and kernel
cat /etc/redhat-release
uname -r

# Verify RAM (expect >= 64 GB)
free -h | grep Mem

# Verify disk space
df -h

# Verify Podman
podman --version

# Verify Git
git --version

# Verify NICs (expect at least 2 interfaces up)
ip -br link show | grep UP

# Verify internet connectivity
curl -s -o /dev/null -w "%{http_code}" https://github.com

# Verify RHEL subscription
subscription-manager status

# Verify RHEL version pinning
subscription-manager release --show

# Verify repos
dnf repolist
```


!!! warning

    If any of the above checks fail, resolve the issue before proceeding.
    Deploying with unmet prerequisites will produce difficult-to-debug errors
    deep in the Ansible playbook execution.

You are now ready to choose your deployment path. Return to [Index](index.md).
