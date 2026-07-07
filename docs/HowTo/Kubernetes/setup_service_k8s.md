# Set Up Service Kubernetes

Deploy and configure a highly available Kubernetes service cluster using
Omnia. This guide covers input configuration, deployment, and
verification.

## Overview

Omnia deploys the service Kubernetes cluster on designated nodes via
cloud-init during provisioning. The cluster hosts platform services
such as the telemetry pipeline, storage provisioners, and monitoring.

### Functional Groups

| Functional Group | Architecture | Role |
|---|---|---|
| `service_kube_control_plane_x86_64` | x86_64 only | HA control plane (runs `kube-apiserver`, `etcd`, `kube-scheduler`, `kube-controller-manager`, kube-vip) |
| `service_kube_node_x86_64` | x86_64 only | Worker node (runs telemetry stack, NFS subdir provisioner, MetalLB speaker) |

### Components Deployed

- **kube-vip** -- Floating VIP for HA API server access
- **Calico** or **Flannel** -- CNI plugin for pod networking
- **MetalLB** -- Bare-metal load balancer for external service IPs
- **NFS subdir provisioner** -- Persistent volume provisioner backed by NFS
- **CRI-O** -- Container runtime

!!! important
    The service K8s cluster is supported **only in HA mode** with a
    minimum of 3 control-plane nodes + 1 worker node.

## Prerequisites

- The OIM is prepared and the `omnia_core` container is accessible (see
  [Prepare OIM](../Setup/prepare_oim.md)).
- HA configuration is complete (see
  [Configure HA](configure_ha.md)).
- At least **3 nodes** assigned to `service_kube_control_plane` and
  **1 node** assigned to `service_kube_node` in the PXE mapping file.

## Procedure

### Step 1: Provide Inputs

For service K8s deployment, update the following input files in
`/opt/omnia/input/project_default/`:

**Key files for this deployment:**

- [`network_spec.yml`](../../Reference/Configuration/network_spec.md) -- Network CIDRs and interfaces
- [`provision_config.yml`](../../Reference/Configuration/provision_config.md) -- OS provisioning settings
- [`pxe_mapping_file.csv`](../../Reference/SampleFiles/pxe_mapping_file.md) -- Node-to-role mapping for PXE boot
- [`omnia_config.yml`](../../Reference/Configuration/omnia_config.md) -- Service K8s cluster settings
- [`high_availability_config.yml`](../../Reference/Configuration/high_availability_config.md) -- Kubernetes HA virtual IP
- [`storage_config.yml`](../../Reference/Configuration/storage_config.md) -- NFS storage mount configuration
- [`software_config.json`](../../Reference/Configuration/software_config.md) -- Software stack (K8s packages)
- [`local_repo_config.yml`](../../Reference/Configuration/local_repo_config.md) -- Repository mirror settings
- [`security_config.yml`](../../Reference/Configuration/security_config.md) -- OpenLDAP authentication settings (optional)
- [`telemetry_config.yml`](../../Reference/Configuration/telemetry_config.md) -- Telemetry pipeline configuration
- [`telemetry_storage_config.yml`](../../Reference/Configuration/telemetry_config.md#telemetry-storage-configuration-parameters) -- Telemetry pod resource and replica settings

### Step 2: Set Credentials

Run the credential utility playbook to securely store passwords for
provisioning, iDRAC, and other services.

```bash title="Run on: omnia_core container"
cd /omnia/utils/credential_utility
ansible-playbook get_config_credentials.yml
```

### Step 3: Create the PXE Mapping File

Create a `pxe_mapping_file.csv` in `/opt/omnia/input/project_default/`
and set the `pxe_mapping_file_path` variable in `provision_config.yml`
to point to it.

```text title="File: /opt/omnia/input/project_default/pxe_mapping_file.csv"
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
    - The `ADMIN_MAC` and `BMC_MAC` addresses should refer to the PXE
      NIC and BMC NIC on the target nodes respectively.
    - Target servers should be configured to boot in PXE mode with the
      appropriate NIC as the first boot device.
    - Hostnames should not contain the domain name of the nodes.

For detailed information on PXE mapping file format and parameters, see
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

#### 4a. Edit omnia_config.yml

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
| `pod_external_ip_range` | MetalLB IP range for LoadBalancer services. Must not overlap with node IPs |
| `k8s_service_addresses` | Internal network for K8s services (default: `10.233.0.0/18`) |
| `k8s_pod_network_cidr` | Internal network for pods (default: `10.233.64.0/18`) |
| `nfs_storage_name` | Must match a `name` in `storage_config.yml` |
| `k8s_crio_storage_size` | Disk size for CRI-O container storage (default: `20G`) |

#### 4b. Edit high_availability_config.yml

Edit [`high_availability_config.yml`](../../Reference/Configuration/high_availability_config.md)
and configure the virtual IP for the K8s API server:

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
| `virtual_ip_address` | Free IPv4 address on the admin subnet. Must not overlap with any `ADMIN_IP`, MetalLB range, or OIM IP |

#### 4c. Edit storage_config.yml

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

!!! note
    The `nfs_storage_name` value in `omnia_config.yml` must exactly match
    the `name` field of a mount entry in `storage_config.yml`. Set
    `mount_on_oim: true` so the OIM can write K8s configuration to the
    share during provisioning.

#### 4d. Edit software_config.json

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

### Step 5: Prepare the OIM

```bash title="Run on: omnia_core container"
cd /omnia/prepare_oim
ansible-playbook prepare_oim.yml
```

### Step 6: Create Local Repositories

```bash title="Run on: omnia_core container"
cd /omnia/local_repo
ansible-playbook local_repo.yml
```

### Step 7: Build Node Images

```bash title="Run on: omnia_core container"
cd /omnia/build_image_x86_64
ansible-playbook build_image_x86_64.yml
```

### Step 8: Provision Nodes

Run `provision.yml` to configure boot scripts and generate cloud-init
files based on the functional groups in the PXE mapping file.

```bash title="Run on: omnia_core container"
cd /omnia/provision
ansible-playbook provision.yml
```

During provisioning, Omnia automatically configures each node based on
its functional group:

- **Control plane nodes**: Initializes `kubeadm`, joins the HA cluster,
  deploys kube-vip static pod, runs `etcd`
- **Worker nodes**: Joins the cluster, receives telemetry workloads,
  runs NFS subdir provisioner and MetalLB speaker

### Step 9: PXE Boot Nodes

After `provision.yml` completes, PXE boot all service K8s nodes:

- Control plane nodes
- Worker nodes

**Option 1: Manual PXE Boot**

Configure each node to boot from the network via iDRAC or BIOS settings.

**Option 2: Automated PXE Boot**

```bash title="Run on: omnia_core container"
cd /omnia/utils
ansible-playbook set_pxe_boot.yml
```

Ensure all nodes boot successfully and become reachable.

## Verification

In the examples below, `kcp1` and `kn` are the hostnames assigned to
the control-plane and worker nodes in the PXE mapping file. Replace
them with the hostnames from your own mapping file.

1. **Check cloud-init status** on all K8s nodes:

    ```bash title="Run on: omnia_core container"
    ssh <control_plane_hostname> 'cloud-init status'
    ssh <worker_hostname> 'cloud-init status'
    ```

    Example:

    ```bash title="Run on: omnia_core container (example)"
    ssh kcp1 'cloud-init status'
    ssh kn 'cloud-init status'
    ```

    Expected output: `status: done`

    !!! note
        Check **every node** in your cluster. Open your PXE mapping file
        and run `ssh <HOSTNAME> 'cloud-init status'` for each entry.
        All nodes must report `status: done` before proceeding.

2. **Check Kubernetes node status**:

    ```bash title="Run on: omnia_core container (example)"
    ssh kcp1 'kubectl get nodes'
    ```

    Expected output:

    ```text title="Expected output"
    NAME              STATUS   ROLES           AGE    VERSION
    172.16.107.95     Ready    <none>          5d     v1.35.1
    172.16.107.96     Ready    control-plane   5d     v1.35.1
    172.16.107.97     Ready    control-plane   5d     v1.35.1
    172.16.107.98     Ready    control-plane   5d     v1.35.1
    ```

    All nodes must show `Ready` status.

3. **Verify system pods are running**:

    ```bash title="Run on: omnia_core container (example)"
    ssh kcp1 'kubectl get pods -n kube-system'
    ssh kcp1 'kubectl get pods -n metallb-system'
    ```

    All pods in `kube-system` and `metallb-system` should be `Running`.

4. **Verify kube-vip HA is operational**:

    ```bash title="Run on: omnia_core container"
    ping -c 3 <virtual_ip_address>
    ```

    ```bash title="Run on: omnia_core container (example)"
    ssh kcp1 'crictl ps | grep kube-vip'
    ```

5. **Verify NFS subdir provisioner**:

    ```bash title="Run on: omnia_core container (example)"
    ssh kcp1 'kubectl get pods -n default | grep nfs'
    ssh kcp1 'kubectl get storageclass'
    ```

## Next Steps

- [Deploy PowerScale CSI](deploy_powerscale_csi.md) -- Deploy PowerScale
  CSI driver for enterprise storage.
- [Set Up Telemetry](../Telemetry/setup_telemetry.md) -- Deploy telemetry
  services on the K8s cluster.

## Troubleshooting

**Nodes show "NotReady" status**

Check kubelet logs on the affected node:

```bash title="Run on: omnia_core container (example)"
ssh <control_plane_hostname> 'journalctl -u kubelet --no-pager -n 30'
```

**Calico pods stuck in "CrashLoopBackOff"**

Check Calico logs:

```bash title="Run on: omnia_core container (example)"
ssh <control_plane_hostname> 'kubectl logs -n kube-system -l k8s-app=calico-node --tail=50'
```

**MetalLB not assigning external IPs**

Verify the IP address pool configuration:

```bash title="Run on: omnia_core container (example)"
ssh <control_plane_hostname> 'kubectl get ipaddresspool -n metallb-system -o yaml'
```

**NFS provisioner PVC stuck in "Pending"**

Verify the NFS server is reachable from the worker node:

```bash title="Run on: omnia_core container (example)"
ssh <worker_hostname> 'showmount -e <nfs-server-ip>'
```
