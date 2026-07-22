# Set Up Service Kubernetes

Deploy a highly available Kubernetes service cluster using Omnia. This
guide walks through every input file, playbook, and verification step
required.

## Overview

Omnia deploys the service Kubernetes cluster on designated nodes via
cloud-init during provisioning. The cluster hosts platform services
such as storage provisioners and monitoring.

### Functional Groups

| Functional Group | Architecture | Role |
|---|---|---|
| `service_kube_control_plane_x86_64` | x86_64 only | HA control plane (runs `kube-apiserver`, `etcd`, `kube-scheduler`, `kube-controller-manager`, kube-vip) |
| `service_kube_node_x86_64` | x86_64 only | Worker node (runs NFS subdir provisioner, MetalLB speaker) |

### Components Deployed

- **kube-vip** -- Floating VIP for HA API server access
- **Calico** or **Flannel** -- CNI plugin for pod networking
- **MetalLB** -- Bare-metal load balancer for external service IPs
- **NFS subdir provisioner** -- Persistent volume provisioner backed by NFS
- **Helm** -- Kubernetes package manager
- **CRI-O** -- Container runtime

!!! important
    The service K8s cluster is supported **only in HA mode** with a
    minimum of 3 control-plane nodes + 1 worker node.

## Prerequisites

- The OIM is prepared and the `omnia_core` container is accessible (see
  [Prepare OIM](../Setup/prepare_oim.md)).
- At least **3 physical nodes** available for `service_kube_control_plane`
  and **1 node** for `service_kube_node`.
- An NFS server is configured and reachable from the admin network.
- A free IPv4 address on the admin subnet for the kube-vip virtual IP.

### K8s Storage Architecture

Service Kubernetes requires shared storage mounts to function correctly across all cluster nodes. Omnia uses NFS mounts for persistent storage, serving distinct purposes during provisioning and at runtime.

#### Primary NFS mount (nfs_storage_name)

The NFS mount referenced by `nfs_storage_name` in `omnia_config.yml` is the backbone of the service K8s cluster's persistent storage. It must be accessible from the OIM, all K8s control-plane nodes, and all K8s worker nodes. Omnia uses this mount for:

- **Kubernetes persistent volumes** — The NFS subdir provisioner creates persistent volumes backed by this NFS share, allowing pods to store data that persists across pod restarts and node failures.
- **Helm chart storage** — Helm charts and their values files are stored on the NFS share for distribution across the cluster.
- **Shared application data** — Applications deployed on the service K8s cluster use this mount for shared data storage and configuration.

!!! warning

    Set `mount_on_oim: true` for the NFS mount in `storage_config.yml`. The OIM must write initial configuration and helm charts to this share during provisioning. If the OIM cannot access the share, the cluster may not initialize correctly.

#### Mount summary

| Mount | Parameter | Purpose | Required |
|---|---|---|---|
| Primary NFS | `nfs_storage_name` | K8s persistent volumes, Helm charts, shared application data | Yes |

For detailed mount configuration including NFS options and functional group targeting, see [Configure Mounts](../Storage/configure_mounts.md).

## Procedure

### Step 1: Enter the omnia_core Container

```bash title="Run on: OIM host"
ssh omnia_core
```

All subsequent commands run inside the `omnia_core` container unless
stated otherwise.

### Step 2: Set Credentials

Run the credential utility to securely store passwords for
provisioning, iDRAC, and other services.

```bash title="Run on: omnia_core container"
cd /omnia/utils/credential_utility
ansible-playbook get_config_credentials.yml
```

You will be prompted for the **provision password** (used to set the
root password on provisioned nodes) and **BMC credentials** (used for
iDRAC-based PXE boot).

### Step 3: Create the PXE Mapping File

The PXE mapping file defines which nodes belong to which functional
group. You need at least **3 rows** with
`service_kube_control_plane_x86_64` and **1 row** with
`service_kube_node_x86_64`.

Create a `pxe_mapping_file.csv` in `/opt/omnia/input/project_default/`
and set the `pxe_mapping_file_path` variable in
[`provision_config.yml`](../../Reference/Configuration/provision_config.md)
to point to it.

```csv title="/opt/omnia/input/project_default/pxe_mapping_file.csv"
FUNCTIONAL_GROUP_NAME,GROUP_NAME,SERVICE_TAG,PARENT_SERVICE_TAG,HOSTNAME,ADMIN_MAC,ADMIN_IP,BMC_MAC,BMC_IP,IB_NIC_NAME,IB_IP
service_kube_control_plane_x86_64,grp4,SVCTAG01,,kcp1,a1:b2:c3:d4:e5:f6,172.16.107.96,a2:b3:c4:d5:e6:f7,100.10.1.99,,
service_kube_control_plane_x86_64,grp5,SVCTAG02,,kcp2,b1:c2:d3:e4:f5:a6,172.16.107.97,b2:c3:d4:e5:f6:a7,100.10.1.100,,
service_kube_control_plane_x86_64,grp5,SVCTAG03,,kcp3,c1:d2:e3:f4:a5:b6,172.16.107.98,c2:d3:e4:f5:a6:b7,100.10.1.101,,
service_kube_node_x86_64,grp6,SVCTAG04,,kn,d1:e2:f3:a4:b5:c6,172.16.107.95,d2:e3:f4:a5:b6:c7,100.10.0.209,,
```

!!! warning
    Replace all placeholder values (`SVCTAG*`, MAC addresses, IPs) with
    your actual hardware data.

!!! note
    - All header fields are case-sensitive.
    - `PARENT_SERVICE_TAG` is not required for service K8s nodes. Leave
      it empty.
    - `ADMIN_MAC` and `BMC_MAC` refer to the PXE NIC and BMC NIC on
      the target nodes respectively.
    - Target servers must be configured to boot in PXE mode with the
      appropriate NIC as the first boot device.
    - Hostnames must not contain the domain name of the nodes.

For the full column reference, see
[PXE Mapping File](../../Reference/SampleFiles/pxe_mapping_file.md).

#### Alternative: Discover Nodes via OME

If you did not create the `pxe_mapping_file.csv` manually, you can use
OpenManage Enterprise (OME) to automatically discover servers and
generate the PXE mapping file.

1. In OME, discover the cluster nodes. See the
   [OpenManage Enterprise User Guide](https://dl.dell.com/content/manual4/en/openmanage-enterprise-user-guide-en)
   for details.

2. Create static groups in OME for each functional group you plan to
   use (e.g., `service_kube_control_plane_x86_64`,
   `service_kube_node_x86_64`). Group names must exactly match the
   Omnia functional group names.

3. Add discovered servers to the corresponding static groups.

4. Configure `discovery_config.yml` in
   `/opt/omnia/input/project_default/`:

    ```yaml title="File: /opt/omnia/input/project_default/discovery_config.yml"
    enable_bmc_discovery: true
    ome_ip: "192.168.1.100"
    ```

5. Run the discovery playbook:

    ```bash title="Run on: omnia_core container"
    cd /omnia/discovery
    ansible-playbook discovery.yml -e "discovery_mechanism=ome"
    ```

The playbook generates a PXE mapping file
(`bmc_pxe_mapping_file_<timestamp>.csv`) in
`/opt/omnia/input/project_default/`. Verify and edit the file if
necessary.

### Step 4: Edit Input Files

Edit the following input files in `/opt/omnia/input/project_default/`.
Each sub-step shows the K8s-relevant section of the file.

#### 4a. Edit network_spec.yml

Edit [`network_spec.yml`](../../Reference/Configuration/network_spec.md)
and configure the admin network interface and CIDR. This defines the
network used by the K8s cluster for node communication.

For the full parameter reference, see
[network_spec.yml Reference](../../Reference/Configuration/network_spec.md).

#### 4b. Edit provision_config.yml

Edit [`provision_config.yml`](../../Reference/Configuration/provision_config.md)
and set `pxe_mapping_file_path` to the PXE mapping file created in
Step 3.

For the full parameter reference, see
[provision_config.yml Reference](../../Reference/Configuration/provision_config.md).

#### 4c. Edit omnia_config.yml

Edit [`omnia_config.yml`](../../Reference/Configuration/omnia_config.md)
and configure the `service_k8s_cluster` section:

```yaml title="File: /opt/omnia/input/project_default/omnia_config.yml"
service_k8s_cluster:
  - cluster_name: service_cluster
    deployment: true
    k8s_cni: "calico"
    pod_external_ip_range: "172.16.107.170-172.16.107.200"
    k8s_service_addresses: "10.233.0.0/18"
    k8s_pod_network_cidr: "10.233.64.0/18"
    nfs_storage_name: "nfs_k8s"
    k8s_crio_storage_size: "20G"
```

| Parameter | Description |
|---|---|
| `cluster_name` | Name of the K8s cluster (must match `high_availability_config.yml`) |
| `deployment` | Must be `true` for the cluster to be deployed |
| `k8s_cni` | CNI plugin: `calico` (default) or `flannel` (required for RoCE NIC) |
| `pod_external_ip_range` | MetalLB IP range for LoadBalancer services. Must not overlap with any node `ADMIN_IP` or the VIP |
| `k8s_service_addresses` | Internal network for K8s services (default: `10.233.0.0/18`) |
| `k8s_pod_network_cidr` | Internal network for pods (default: `10.233.64.0/18`) |
| `nfs_storage_name` | Must match a `name` in `storage_config.yml` (see Step 4e) |
| `k8s_crio_storage_size` | Disk size for CRI-O container storage (default: `20G`) |

#### 4d. Edit high_availability_config.yml

Edit [`high_availability_config.yml`](../../Reference/Configuration/high_availability_config.md)
and configure the virtual IP for the K8s API server. Omnia deploys
**kube-vip** as a static pod on each control-plane node to provide a
floating VIP. If the active control-plane node fails, kube-vip
migrates the VIP to a healthy node automatically.

```yaml title="File: /opt/omnia/input/project_default/high_availability_config.yml"
service_k8s_cluster_ha:
  - cluster_name: service_cluster
    enable_k8s_ha: true
    virtual_ip_address: "172.16.107.1"
```

| Parameter | Description |
|---|---|
| `cluster_name` | Must match `cluster_name` in `omnia_config.yml` where `deployment` is `true` |
| `enable_k8s_ha` | Must be `true` -- service K8s is supported only in HA mode |
| `virtual_ip_address` | Free IPv4 address on the admin subnet. Must not overlap with any `ADMIN_IP` in the PXE mapping file, MetalLB `pod_external_ip_range`, or the OIM admin IP |

For HA architecture details and troubleshooting, see
[Configure HA](configure_ha.md).

#### 4e. Edit storage_config.yml

Edit [`storage_config.yml`](../../Reference/Configuration/storage_config.md)
and define the NFS mount referenced by `nfs_storage_name` in
`omnia_config.yml`:

```yaml title="File: /opt/omnia/input/project_default/storage_config.yml"
mounts:
  - name: "nfs_k8s"
    source: "172.16.107.254:/home/nfs/k8s"
    mount_point: "/opt/omnia/k8s_mount"
    fs_type: "nfs"
    mnt_opts: "nosuid,rw,sync,hard,intr"
    mount_on_oim: true
    functional_group_prefix: ["service_kube"]
```

| Parameter | Description |
|---|---|
| `name` | Must exactly match `nfs_storage_name` in `omnia_config.yml` |
| `source` | NFS server IP and export path |
| `mount_point` | Local mount path on each node |
| `mount_on_oim` | Must be `true` so the OIM can write K8s configuration to the NFS share during provisioning |
| `functional_group_prefix` | Functional group prefixes that should mount this share. Use `["service_kube"]` for K8s nodes |

#### 4f. Edit software_config.json

Edit [`software_config.json`](../../Reference/Configuration/software_config.md)
and include `service_k8s` in the `softwares` list:

```json title="File: /opt/omnia/input/project_default/software_config.json"
{
    "cluster_os_type": "rhel",
    "cluster_os_version": "10.0",
    "repo_config": "partial",
    "softwares": [
        {"name": "default_packages", "arch": ["x86_64"]},
        {"name": "service_k8s", "arch": ["x86_64"]}
    ]
}
```

The `service_k8s` entry ensures that K8s packages (kubeadm, kubelet,
CRI-O, Calico, MetalLB, Helm, NFS provisioner) are downloaded during
the `local_repo.yml` step.

#### 4g. Edit local_repo_config.yml

Edit [`local_repo_config.yml`](../../Reference/Configuration/local_repo_config.md)
and configure the repository mirror settings. This file controls how
packages are downloaded and cached in the Pulp repository.

For the full parameter reference, see
[local_repo_config.yml Reference](../../Reference/Configuration/local_repo_config.md).

### Step 5: Prepare the OIM

Run `prepare_oim.yml` to deploy the OIM infrastructure (OpenCHAMI, Pulp,
registry, and supporting containers).

```bash title="Run on: omnia_core container"
cd /omnia/prepare_oim
ansible-playbook prepare_oim.yml
```

### Step 6: Create Local Repositories

Run `local_repo.yml` to download all required K8s packages, container
images, and manifests into the Pulp repository.

```bash title="Run on: omnia_core container"
cd /omnia/local_repo
ansible-playbook local_repo.yml
```

### Step 7: Build Node Images

Build diskless boot images for the service K8s functional groups.

```bash title="Run on: omnia_core container"
cd /omnia/build_image_x86_64
ansible-playbook build_image_x86_64.yml
```

Verify that images are created for each functional group:

```bash title="Run on: OIM host"
s3cmd ls -Hr s3://boot-images
```

### Step 8: Provision Nodes

Run `provision.yml` to configure boot scripts and generate cloud-init
files based on the functional groups in the PXE mapping file.

```bash title="Run on: omnia_core container"
cd /omnia/provision
ansible-playbook provision.yml
```

During provisioning, Omnia writes the K8s cluster configuration to the
NFS share and generates cloud-init scripts for each node. When the
nodes boot, cloud-init automatically:

- **Control plane nodes**: Installs CRI-O, initializes `kubeadm`,
  forms the HA cluster, deploys kube-vip static pod, runs `etcd`,
  applies Calico/Flannel CNI, deploys MetalLB, installs Helm
- **Worker nodes**: Installs CRI-O, joins the cluster via `kubeadm join`,
  deploys NFS subdir external provisioner, runs MetalLB speaker

### Step 9: PXE Boot Nodes

After `provision.yml` completes, PXE boot all service K8s nodes:

- Control plane nodes (3 nodes)
- Worker nodes (1+ nodes)

**Option 1: Manual PXE Boot**

Configure each node to boot from the network via iDRAC or BIOS settings.

**Option 2: Automated PXE Boot via iDRAC**

```bash title="Run on: omnia_core container"
cd /omnia/utils
ansible-playbook set_pxe_boot.yml
```

Wait for all nodes to complete booting and cloud-init to finish. This
typically takes 10–20 minutes depending on the number of nodes and
network speed.

## Verification

After PXE boot completes, verify the cluster is operational. In all
examples below, replace `<control_plane_hostname>` and
`<worker_hostname>` with the hostnames from your PXE mapping file
(e.g., `kcp1`, `kn`).

### 1. Check cloud-init status

Run this on **every node** listed in the PXE mapping file:

```bash title="Run on: omnia_core container"
ssh <control_plane_hostname> 'cloud-init status'
ssh <worker_hostname> 'cloud-init status'
```

Expected output: `status: done`

!!! note
    All nodes must report `status: done` before proceeding. If a node
    shows `status: running`, wait and re-check. If it shows `error`,
    check `/var/log/cloud-init-output.log` on the node.

### 2. Check Kubernetes node status

```bash title="Run on: omnia_core container"
ssh <control_plane_hostname> 'kubectl get nodes'
```

Expected output (4 nodes: 3 control-plane + 1 worker):

```text title="Expected output"
NAME              STATUS   ROLES           AGE    VERSION
172.16.107.95     Ready    <none>          5d     v1.35.1
172.16.107.96     Ready    control-plane   5d     v1.35.1
172.16.107.97     Ready    control-plane   5d     v1.35.1
172.16.107.98     Ready    control-plane   5d     v1.35.1
```

All nodes must show `Ready` status.

### 3. Verify kube-vip HA

Ping the virtual IP address configured in `high_availability_config.yml`:

```bash title="Run on: omnia_core container"
ping -c 3 <virtual_ip_address>
```

Verify the kube-vip container is running on a control-plane node:

```bash title="Run on: omnia_core container"
ssh <control_plane_hostname> 'crictl ps | grep kube-vip'
```

### 4. Verify system pods

```bash title="Run on: omnia_core container"
ssh <control_plane_hostname> 'kubectl get pods -n kube-system'
```

All pods in `kube-system` should be `Running`. Key pods to check:

- `calico-node-*` (or `kube-flannel-*` if using Flannel)
- `coredns-*`
- `etcd-*`
- `kube-apiserver-*`
- `kube-controller-manager-*`
- `kube-scheduler-*`

### 5. Verify MetalLB

```bash title="Run on: omnia_core container"
ssh <control_plane_hostname> 'kubectl get pods -n metallb-system'
```

All MetalLB pods (`controller` and `speaker`) should be `Running`.

### 6. Verify NFS subdir provisioner

```bash title="Run on: omnia_core container"
ssh <control_plane_hostname> 'kubectl get pods -n default | grep nfs'
ssh <control_plane_hostname> 'kubectl get storageclass'
```

The NFS subdir external provisioner pod should be `Running` and a
`StorageClass` should be available.

## Next Steps

- [Deploy PowerScale CSI](deploy_powerscale_csi.md) -- Deploy PowerScale
  CSI driver for enterprise storage.
- [Set Up Telemetry](../Telemetry/setup_telemetry.md) -- Deploy the
  telemetry pipeline on the service K8s cluster.

## Troubleshooting

### Nodes show "NotReady" status

Check kubelet logs on the affected node:

```bash title="Run on: omnia_core container"
ssh <control_plane_hostname> 'journalctl -u kubelet --no-pager -n 50'
```

Common causes: CNI plugin not ready, CRI-O not running, NFS mount
failed. Check `cloud-init status` and `/var/log/cloud-init-output.log`
on the node.

### Calico pods stuck in CrashLoopBackOff

```bash title="Run on: omnia_core container"
ssh <control_plane_hostname> 'kubectl logs -n kube-system -l k8s-app=calico-node --tail=50'
```

Common cause: `k8s_pod_network_cidr` in `omnia_config.yml` conflicts
with the admin network CIDR. Ensure they do not overlap.

### MetalLB not assigning external IPs

```bash title="Run on: omnia_core container"
ssh <control_plane_hostname> 'kubectl get ipaddresspool -n metallb-system -o yaml'
```

Verify that `pod_external_ip_range` in `omnia_config.yml` does not
overlap with node IPs or the kube-vip VIP.

### NFS provisioner PVC stuck in Pending

```bash title="Run on: omnia_core container"
ssh <worker_hostname> 'showmount -e <nfs-server-ip>'
```

Verify the NFS server is reachable and the export path in
`storage_config.yml` is correct.

### VIP not reachable

```bash title="Run on: omnia_core container"
ssh <control_plane_hostname> 'crictl ps | grep kube-vip'
ssh <control_plane_hostname> 'cat /etc/kubernetes/manifests/kube-vip.yaml'
```

If kube-vip is not running, check that `virtual_ip_address` in
`high_availability_config.yml` does not conflict with any node IP or
MetalLB range. For detailed HA troubleshooting, see
[Configure HA](configure_ha.md).
