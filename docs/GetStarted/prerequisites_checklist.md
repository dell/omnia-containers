# Prerequisites Checklist


Complete **every** item on this checklist before starting any deployment path.
Skipping a prerequisite is the single most common cause of failed deployments.

!!! tip

    Print this page and physically check off each item as you verify it in
    your datacenter. Hand it to your rack-and-stack technician alongside the
    server placement diagram.

## Hardware Requirements


| ☑ | Requirement | Details |
| --- | --- | --- |
| ☐ | Dell PowerEdge servers (14th generation or later) | Supported models include R650, R750, R760, C6620, XE8640, XE9680. Check the [Omnia Support Matrix](https://github.com/dell/omnia) for the full list. |
| ☐ | Minimum node count for your chosen path | Path A: 4 nodes \| Path B: 8 nodes \| Path C: 5 nodes \| Path D: 8+ nodes. |
| ☐ | Supported NICs installed in every target node | Mellanox ConnectX-6/7 (InfiniBand or Ethernet) or Intel E810 recommended. At least one NIC port must be PXE-capable. |
| ☐ | Network switches racked and cabled | One admin/data switch and one BMC management switch at minimum. InfiniBand switch required only if using IB fabric. |


## OIM (Management Node) Requirements


The **Omnia Infrastructure Manager (OIM)** is the single node from which
all Omnia playbooks execute. It does *not* participate in the compute
cluster.

| ☑ | Requirement | Details |
| --- | --- | --- |
| ☐ | 64 GB RAM minimum (128 GB recommended) | The `omnia_core` Podman container, local repos, and image-building tasks are memory-intensive. |
| ☐ | RHEL 8.8+ or Rocky Linux 8.8+ with **Server with GUI** group | Minimal installs are **not** supported. The GUI group pulls in required libraries used by Ansible and Podman. |
| ☐ | Podman 4.x or later installed | Verify: `podman --version`. If missing, install via `dnf install -y podman`. |
| ☐ | Two active NIC ports | **NIC 1 (public):** Internet-facing, for downloading packages and container images. **NIC 2 (internal/admin):** Connected to the admin switch for PXE provisioning and cluster management. |
| ☐ | Internet access (direct or via proxy) | Required during `local_repo.yml` to pull OS packages, Python modules, and container images. After repo sync, air-gapped operation is possible. |
| ☐ | Git 2.x+ installed | `dnf install -y git`. Needed to clone the Omnia repository. |
| ☐ | 500 GB+ free disk on `/` | Local repos, container images, and node OS images consume significant space. Use `df -h /` to check. |
| ☐ | SELinux set to **permissive** or **disabled** | `setenforce 0 && sed -i 's/^SELINUX=.*/SELINUX=permissive/' /etc/selinux/config` |
| ☐ | Firewall allows required ports | DHCP (67-68/udp), TFTP (69/udp), HTTP (80, 8080/tcp), NFS (111, 2049/tcp+udp), SSH (22/tcp), and Kubernetes API (6443/tcp). |

## Networking Prerequisites


| ☑ | Requirement | Details |
| --- | --- | --- |
| ☐ | Admin network switch configured | A dedicated VLAN or flat L2 segment connecting OIM NIC 2 to all target-node admin NICs. DHCP must **not** already be running on this segment (Omnia provides its own). |
| ☐ | BMC network switch configured | A separate VLAN or segment connecting OIM to all target-node iDRAC BMC ports. Can share a physical switch with admin if VLANs are used. |
| ☐ | IP ranges planned for admin and BMC subnets | You will enter these CIDRs in `network_spec.yml`. Example: admin `10.5.0.0/16`, BMC `10.3.0.0/16`. |
| ☐ | No conflicting DHCP servers on admin or BMC subnets | Omnia's DHCP (via `prepare_oim.yml`) must be the sole DHCP source on the PXE/admin network. |
| ☐ | InfiniBand OpenSM configured (if using IB fabric) | Install `opensm` on the OIM or a dedicated subnet manager. Verify: `ibstat` shows ports **Active**. |
| ☐ | DNS resolution working on OIM | `nslookup google.com` must succeed. Configure `/etc/resolv.conf` or NetworkManager DNS if needed. |

## NFS / Storage Prerequisites


| ☑ | Requirement | Details |
| --- | --- | --- |
| ☐ | NFS server reachable from OIM and all cluster nodes | Dell PowerScale (Isilon), PowerStore, or any NFSv3-capable appliance. |
| ☐ | **NFSv3 enabled**, NFSv4 **disabled** | PowerScale: set protocol to NFSv3 only in the share configuration. Omnia does not support NFSv4 locking semantics. |
| ☐ | Export permissions: `755`, `no_root_squash` | `no_root_squash` is required so Ansible (running as root) can write to NFS-mounted paths during provisioning. |
| ☐ | Minimum storage capacity allocated | **Kubernetes PVs:** 200 GB \| **Slurm shared home:** 50 GB \| **OIM local repos:** 200 GB. |
| ☐ | NFS exports tested from OIM | `mount -t nfs -o vers=3 <nfs_server>:/export /mnt/test && ls /mnt/test` |

## RHEL Subscriptions and Repositories


| ☑ | Requirement | Details |
| --- | --- | --- |
| ☐ | RHEL subscription active on OIM | `subscription-manager status` must show **Current**. Required for `AppStream` and `BaseOS` repos. |
| ☐ | `AppStream` and `BaseOS` repos enabled | `dnf repolist` must list both. Enable with: `subscription-manager repos --enable=rhel-8-for-x86_64-appstream-rpms --enable=rhel-8-for-x86_64-baseos-rpms` |
| ☐ | Docker Hub credentials available | A Docker Hub account (free tier is sufficient) is needed for pulling container images during `local_repo.yml`. You will enter these in `local_repo_config.yml`. |
| ☐ | (Optional) Red Hat container registry credentials | Required only if pulling UBI-based images from `registry.redhat.io`. |

## BIOS Settings on Target Nodes


Apply these settings to **every** target node (compute, head, login, K8s)
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
| ☐ | iDRAC firmware updated to latest version | Download from [Dell Support](https://www.dell.com/support). Minimum recommended: iDRAC 6.10.x+ for 15th-gen, 5.10.x+ for 14th-gen. |
| ☐ | Datacenter license installed (for telemetry) | **Required only for Paths B and C.** The Datacenter license enables streaming telemetry via iDRAC. Enterprise license is insufficient. |
| ☐ | iDRAC IP assigned on BMC network | Can be DHCP (Omnia will assign) or static. If static, record each iDRAC IP for the mapping file. |
| ☐ | Default iDRAC credentials known | Factory default is `root` / `calvin`. If changed, you must provide the current credentials in `provision_config.yml`. |

## Service Kubernetes (K8s) Requirements


These apply only to **Paths B, C, and D** where a Kubernetes service
cluster is deployed.

| ☑ | Requirement | Details |
| --- | --- | --- |
| ☐ | Minimum **3 control-plane nodes** allocated | Kubernetes HA requires an odd number of control-plane nodes (3 or 5). Each must have 64 GB RAM minimum and 4+ CPU cores. |
| ☐ | At least **1 worker node** allocated | Worker nodes run telemetry collectors, Grafana, and VictoriaMetrics. 64 GB RAM recommended. |
| ☐ | Dedicated IP range for K8s pod and service networks | Defaults: pod CIDR `10.244.0.0/16`, service CIDR `10.96.0.0/12`. These must not overlap with admin or BMC subnets. |
| ☐ | Virtual IP (VIP) reserved for K8s API HA | A single unused IP on the admin network that `kube-vip` will float across control-plane nodes. Enter this in `ha_config.yml`. |

## Final Pre-Flight Checks


Run these commands on the OIM **before** starting any deployment path:

```shell title="Run on OIM (as root)"
# Verify OS and kernel
cat /etc/redhat-release
uname -r

# Verify RAM (expect >= 64 GB)
free -h | grep Mem

# Verify disk space (expect >= 500 GB free on /)
df -h /

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

# Verify repos
dnf repolist
```


!!! warning

    If any of the above checks fail, resolve the issue **before** proceeding.
    Deploying with unmet prerequisites will produce difficult-to-debug errors
    deep in the Ansible playbook execution.

You are now ready to choose your deployment path. Return to [Index](index.md).
