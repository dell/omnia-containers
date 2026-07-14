# Set Up Slurm

Deploy and configure Slurm 25.05 on cluster nodes using Omnia. This guide
covers input configuration, deployment, and Slurm configuration
customization.

!!! caution
    Omnia is validated for Slurm version 25.05. Other versions may have
    compatibility issues.

## Overview

Omnia deploys Slurm on designated nodes via cloud-init during
provisioning. The setup includes Slurm controller, compute, login, and
login/compiler nodes with DOCA-OFED support configured automatically.

### Functional Groups

| Functional Group | Architecture | Role |
|---|---|---|
| `slurm_control_node_x86_64` | x86_64 only | Slurm controller (runs `slurmctld` and `slurmdbd`) |
| `slurm_node_x86_64` | x86_64 | Compute nodes (runs `slurmd`) |
| `slurm_node_aarch64` | aarch64 | Compute nodes (runs `slurmd`) |
| `login_node_x86_64` | x86_64 | Login nodes for user access |
| `login_node_aarch64` | aarch64 | Login nodes for user access |
| `login_compiler_node_x86_64` | x86_64 | Login/compile nodes with compilation tools |
| `login_compiler_node_aarch64` | aarch64 | Login/compile nodes with compilation tools |

!!! note
    The Slurm controller (`slurm_control_node_x86_64`) is supported on
    x86_64 architecture only.

## Prerequisites

- The OIM is prepared and the `omnia_core` container is accessible (see
  [Prepare OIM](../Setup/prepare_oim.md)).
- A user-built Slurm 25.05 RPM repository is available (see
  [Build Slurm Repo](build_slurm_repo.md)).
- For Slurm-only deployments (no service K8s), set
  `idrac_telemetry_support` to `false` in `telemetry_config.yml`.

### InfiniBand Requirements

If any Slurm nodes have an InfiniBand interface and `ib_network` is
defined in `network_spec.yml`:

- The Slurm user repository must **not** include `ucx`, `ucx-devel`,
  `openmpi`, or `openmpi-devel` packages.
- Slurm itself must be compiled **without** UCX and OpenMPI support.
- DOCA-OFED provides its own UCX and OpenMPI stack that is configured
  automatically during provisioning.

!!! tip
    For InfiniBand network configuration details, see
    [Configure InfiniBand](../Networking/configure_infiniband.md).

## Procedure

### Step 1: Create the PXE Mapping File

Omnia supports two methods for creating the PXE mapping file:

- **Manual** -- Collect PXE NIC information and fill in the
  `pxe_mapping_file.csv` manually.
- **OME-based discovery (recommended)** -- Use OpenManage Enterprise (OME)
  to discover cluster nodes and auto-generate the mapping file using
  `discovery.yml`.

**Option A: Fill the PXE mapping file manually**

Create a `pxe_mapping_file.csv` in
`/opt/omnia/input/project_default/` and set the `pxe_mapping_file_path`
variable in `provision_config.yml` to point to it.

```text title="File: /opt/omnia/input/project_default/pxe_mapping_file.csv"
FUNCTIONAL_GROUP_NAME,GROUP_NAME,SERVICE_TAG,PARENT_SERVICE_TAG,HOSTNAME,ADMIN_MAC,ADMIN_IP,BMC_MAC,BMC_IP,IB_NIC_NAME,IB_IP
slurm_control_node_x86_64,grp0,SVCTAG01,,head01,a1:b2:c3:d4:e5:f6,172.16.107.52,a2:b3:c4:d5:e6:f7,172.17.107.52,,
slurm_node_x86_64,grp1,SVCTAG02,,compute01,b1:c2:d3:e4:f5:a6,172.16.107.43,b2:c3:d4:e5:f6:a7,172.17.107.43,,
login_node_x86_64,grp2,SVCTAG03,,login01,c1:d2:e3:f4:a5:b6,172.16.107.44,c2:d3:e4:f5:a6:b7,172.17.107.44,,
login_compiler_node_x86_64,grp3,SVCTAG04,,login-compiler01,d1:e2:f3:a4:b5:c6,172.16.107.45,d2:e3:f4:a5:b6:c7,172.17.107.45,,
```

!!! warning
    Replace all placeholder values (`SVCTAG*`, MAC addresses, IPs) with
    your actual hardware data.

!!! note
    - All header fields are case-sensitive.
    - Leave the `PARENT_SERVICE_TAG` column empty for Slurm-only deployments
      (without K8s).
    - `IB_NIC_NAME` and `IB_IP` are optional. Leave them empty if
      InfiniBand is not used.
    - The `ADMIN_MAC` and `BMC_MAC` addresses should refer to the PXE
      NIC and BMC NIC on the target nodes respectively.
    - Target servers should be configured to boot in PXE mode with the
      appropriate NIC as the first boot device.
    - Hostnames should not contain the domain name of the nodes.

For detailed information on PXE mapping file format and parameters, see
[PXE Mapping File](../../Reference/SampleFiles/pxe_mapping_file.md).

**Option B: Create PXE file using OME**

Use the `discovery.yml` playbook to auto-generate the mapping file from
an OME inventory. For detailed instructions including OME prerequisites,
static group setup, and iDRAC hostname conventions, see
[Discover Nodes Using OME](../Setup/discover_nodes.md){target="_blank"}.

```bash title="Run on: omnia_core container"
cd /omnia/discovery
ansible-playbook discovery.yml -e "discovery_mechanism=ome"
```

The playbook generates a `bmc_pxe_mapping_file_<timestamp>.csv` in
`/opt/omnia/input/project_default/`. Verify and edit the file as needed.

### Step 2: Provide Inputs

For Slurm deployment, update the following input files in
`/opt/omnia/input/project_default/`:

**Key files for this deployment:**

| Input File | Purpose |
| --- | --- |
| [`network_spec.yml`](../../Reference/Configuration/network_spec.md) | Network CIDRs, interfaces, and IP ranges |
| [`provision_config.yml`](../../Reference/Configuration/provision_config.md) | OS provisioning and PXE settings |
| [`software_config.json`](../../Reference/Configuration/software_config.md) | Software stack selections |
| [`omnia_config.yml`](../../Reference/Configuration/omnia_config.md) | Slurm cluster configuration |
| [`storage_config.yml`](../../Reference/Configuration/storage_config.md) | NFS storage mount configuration |
| [`local_repo_config.yml`](../../Reference/Configuration/local_repo_config.md) | Repository mirror settings |
| [`telemetry_config.yml`](../../Reference/Configuration/telemetry_config.md) | Telemetry and monitoring settings |
| [`security_config.yml`](../../Reference/Configuration/security_config.md) | OpenLDAP authentication settings |


#### Edit omnia_config.yml

Edit [`omnia_config.yml`](../../Reference/Configuration/omnia_config.md) and configure the
`slurm_cluster` section:

```yaml title="File: /opt/omnia/input/project_default/omnia_config.yml"
slurm_cluster:
  - cluster_name: slurm_cluster
    nfs_storage_name: nfs_slurm
    # vast_storage_name: vast_storage  # Optional: omit if not using VAST storage
```

| Parameter | Description |
|---|---|
| `cluster_name` | Name of the Slurm cluster (required) |
| `nfs_storage_name` | Must match a `name` in `storage_config.yml` mounts |
| `vast_storage_name` | VAST storage name for HPC tools (`/hpc_tools`). Must match a `name` in `storage_config.yml` mounts. Optional; if omitted, defaults to `nfs_storage_name` |

!!! note
    Only specify `vast_storage_name` if you have a separate VAST storage
    appliance for HPC tools and benchmarks. If you are using a single NFS
    share for all Slurm data, omit this parameter.

#### Edit storage_config.yml

Edit [`storage_config.yml`](../../Reference/Configuration/storage_config.md) and define the
NFS mount entries referenced by `nfs_storage_name` and
`vast_storage_name` in `omnia_config.yml`.

```yaml title="File: /opt/omnia/input/project_default/storage_config.yml"
mounts:
  - name: "nfs_slurm"
    source: "172.16.107.168:/mnt/share/omnia"
    mount_point: "/share_omnia"
    fs_type: "nfs"
    mnt_opts: "nosuid,rw,sync,hard,intr"
    mount_on_oim: true
    functional_group_prefix: ["slurm", "login"]

  - name: "vast_storage"
    source: "172.16.107.77:/share/vast"
    mount_point: "/mnt/vast"
    mount_params: "vast_rdma"
    mount_on_oim: true
    functional_group_prefix: ["slurm_node", "login"]
```

| Parameter | Description |
|---|---|
| `name` | Unique identifier; must match `nfs_storage_name` or `vast_storage_name` in `omnia_config.yml` |
| `source` | NFS server IP and export path (e.g., `192.168.1.100:/export/share`) |
| `mount_point` | Absolute path where the share is mounted on nodes |
| `fs_type` | Filesystem type (`nfs`, `nfs4`, etc.). Can be omitted when using `mount_params` |
| `mnt_opts` | Mount options string. Can be omitted when using `mount_params` |
| `mount_on_oim` | Set to `true` so the OIM can write Slurm config and HPC tools to the share during provisioning |
| `mount_params` | Named profile from the `mount_params` section (e.g., `vast_rdma` for RDMA-optimized NFS) |
| `functional_group_prefix` | List of prefixes to target nodes (e.g., `["slurm"]` matches all Slurm functional groups) |

!!! note
    The `nfs_storage_name` value in `omnia_config.yml` must exactly match
    the `name` field of a mount entry in `storage_config.yml`. Omnia uses
    this mount to store Slurm configuration files, munge keys, and shared
    directories.

!!! important
    Set `mount_on_oim: true` for both NFS and VAST mounts used by Slurm.
    The OIM must access these shares during provisioning to populate Slurm
    configuration, munge keys, and HPC tools.

#### Edit software_config.json

Edit [`software_config.json`](../../Reference/Configuration/software_config.md) and add
`slurm_custom` to the `softwares` list with the required subgroups:

```json title="File: /opt/omnia/input/project_default/software_config.json"
{
    "cluster_os_type": "rhel",
    "cluster_os_version": "10.0",
    "repo_config": "partial",
    "softwares": [
        {"name": "default_packages", "arch": ["x86_64", "aarch64"]},
        {"name": "slurm_custom", "arch": ["x86_64", "aarch64"]}
    ],
    "slurm_custom": [
        {"name": "slurm_control_node"},
        {"name": "slurm_node"},
        {"name": "login_node"},
        {"name": "login_compiler_node"}
    ]
}
```

The `slurm_custom` subgroups map to the Slurm RPM packages installed on
each functional group:

| Subgroup | Packages installed |
|---|---|
| `slurm_control_node` | `slurm-slurmctld`, `slurm-slurmdbd`, `mariadb-server`, `python3-PyMySQL` |
| `slurm_node` | `slurm-slurmd`, `slurm-pam_slurm`, `kernel-devel`, `kernel-headers` |
| `login_node` | `slurm`, `slurm-slurmd` |
| `login_compiler_node` | `slurm`, `slurm-slurmd` |

#### Edit local_repo_config.yml

Edit [`local_repo_config.yml`](../../Reference/Configuration/local_repo_config.md) and add
your Slurm RPM repository URL under `user_repo_url_x86_64` (and
`user_repo_url_aarch64` for ARM nodes):

```yaml title="File: /opt/omnia/input/project_default/local_repo_config.yml"
user_repo_url_x86_64:
  - { url: "http://<your-slurm-repo>/x86_64/", gpgkey: "", name: "slurm_custom" }
```
!!! tip
    If you need to build custom Slurm RPMs from source or host them on
    a local server, complete these steps first:

    - [Build Slurm RPM Repository](build_slurm_repo.md)
    - [Host Slurm RPM Repository](host_slurm_repo.md)
    
!!! important
    The repository `name` must be `slurm_custom` to match the
    `software_config.json` entry.

#### Edit telemetry_config.yml (optional)

Edit [`telemetry_config.yml`](../../Reference/Configuration/telemetry_config.md) to control
DCGM installation on GPU nodes:

```yaml title="File: /opt/omnia/input/project_default/telemetry_config.yml"
telemetry_sources:
  dcgm:
    metrics_enabled: true
```

- When `metrics_enabled` is `true` (default), DCGM is installed on
  GPU-capable Slurm compute nodes during provisioning.
- When `metrics_enabled` is `false`, DCGM installation is skipped.

!!! note
    For Slurm-only deployments, disable all telemetry metrics in
    `telemetry_config.yml` except DCGM, which can be enabled if GPU
    telemetry is required.
    For more information related to DCGM, see [DCGM](slurm_with_gpu.md#dcgm).
    
### Step 3: Configure Slurm

#### Default Configuration

Omnia applies a default Slurm configuration optimized for HPC clusters:

- **Default partition**: A partition named `normal` is created with all
  compute nodes from the PXE mapping file
- **Scheduler**: `sched/backfill` with `select/cons_tres` and
  `CR_Core_Memory`
- **GPU support**: `GresTypes=gpu` with `AutoDetect=nvml`
- **Configless mode**: Compute nodes use `--conf-server` to fetch
  configuration from the controller

!!! note
    The parameters `ClusterName`, `SlurmctldHost`, and
    `AccountingStorageHost` are managed by Omnia and cannot be overridden.

#### Custom Configuration

For detailed information on custom Slurm configuration, merge control,
node discovery modes, and configuration validation, see
[Configure Slurm](configure_slurm.md).

### Step 4 -- Prepare the OIM

Deploys the OIM infrastructure: OpenCHAMI provisioning stack, Pulp
local repository, container registry, MinIO S3 storage, OpenLDAP
authentication, and step-ca certificate authority.

For details, see
[Prepare OIM](../Setup/prepare_oim.md){target="_blank"}.

```bash title="Run on: omnia_core container"
cd /omnia/prepare_oim
ansible-playbook prepare_oim.yml
```

**Verification -- OIM Infrastructure**

After `prepare_oim.yml` completes, verify the OIM services on the
**OIM host** (not inside the container):

1. **Check `omnia.target` status**:

    ```bash title="Run on: OIM host"
    systemctl is-active omnia.target
    ```

    Expected output: `active`

2. **Verify all service dependencies**:

    ```bash title="Run on: OIM host"
    systemctl list-dependencies omnia.target
    ```

    Expected output:

    ```text title="Expected output"
    omnia.target
    ● ├─minio.service
    ● ├─omnia_auth.service
    ● ├─omnia_core.service
    ● ├─pulp.service
    ● ├─registry.service
    ● ├─network-online.target
    ● │ └─NetworkManager-wait-online.service
    ● └─openchami.target
    ●   ├─acme-deploy.service
    ●   ├─acme-register.service
    ●   ├─bss-init.service
    ●   ├─bss.service
    ●   ├─cloud-init-server.service
    ●   ├─coresmd-coredhcp.service
    ●   ├─coresmd-coredns.service
    ●   ├─haproxy.service
    ●   ├─hydra-gen-jwks.service
    ●   ├─hydra-migrate.service
    ●   ├─hydra.service
    ●   ├─opaal-idp.service
    ●   ├─opaal.service
    ●   ├─openchami-cert-trust.service
    ●   ├─postgres.service
    ●   ├─smd-init.service
    ●   ├─smd.service
    ●   └─step-ca.service
    ```

3. **Verify all containers are running**:

    ```bash title="Run on: OIM host"
    podman ps --format "table {{.Names}}\t{{.Status}}"
    ```

    Expected output:

    ```text title="Expected output"
    NAMES               STATUS
    bss                 Up 1 day
    cloud-init-server   Up 1 day
    coresmd-coredhcp    Up 1 day
    coresmd-coredns     Up 1 day
    haproxy             Up 1 day
    hydra               Up 1 day
    minio-server        Up 1 day
    omnia_auth          Up 1 day
    omnia_core          Up 1 day
    opaal               Up 1 day
    opaal-idp           Up 1 day
    postgres            Up 1 day
    pulp                Up 1 day
    registry            Up 1 day
    smd                 Up 1 day
    step-ca             Up 1 day
    ```

!!! note

    - The `minio-server` container will **not** be present if you configured
      PowerScale as the S3 endpoint (`s3_configurations.provider: "powerscale"`)
      in `storage_config.yml`. In that case, Omnia uses the external
      PowerScale S3 service instead of deploying a local MinIO container.
    - The `omnia_auth` container will **not** be present if `openldap` is
      not included in `software_config.json`.

For detailed OIM verification procedures, see
[Verify OIM Services](../Setup/verify_oim_services.md){target="_blank"}.

### Step 5 -- Create Local Repositories

Downloads all required RPM packages, container images, and tarballs
into Pulp based on `software_config.json` for air-gapped provisioning.

For details, see
[Create Local Repos](../Setup/create_local_repos.md){target="_blank"}.

```bash title="Run on: omnia_core container"
cd /omnia/local_repo
ansible-playbook local_repo.yml
```

!!! note

    Expect **45--90 minutes** depending on network speed. Total download
    size is typically **20--40 GB**.

**Verification -- Local Repository Status**

After `local_repo.yml` completes, verify that all software components
were downloaded successfully by checking the `software.csv` status file.
The components listed in this file correspond directly to the software
entries configured in `software_config.json`.

1. **Verify x86_64 package status**:

    ```bash title="Run on: omnia_core container"
    cat /opt/omnia/log/local_repo/rhel/10.0/x86_64/software.csv
    ```

    Expected output:

    ```text title="Expected output"
    name,status
    default_packages,success
    openldap,success
    slurm_custom,success
    ```

2. **Verify aarch64 package status** (if aarch64 is included in
   `software_config.json`):

    ```bash title="Run on: omnia_core container"
    cat /opt/omnia/log/local_repo/rhel/10.0/aarch64/software.csv
    ```

    Expected output:

    ```text title="Expected output"
    name,status
    default_packages,success
    openldap,success
    slurm_custom,success
    ```

!!! note

    The `software.csv` output reflects the software components configured
    in `software_config.json`. Each component with `"arch": ["x86_64"]`
    appears in the x86_64 status file, and each component with
    `"arch": ["aarch64"]` appears in the aarch64 status file. All entries
    must show `success` status before proceeding.


### Step 6 -- Build Node Images

Builds diskless OS images for each functional group in the PXE mapping
file and uploads them to MinIO (S3) for PXE boot delivery.

For details, see
[Build Cluster Images](../Setup/build_cluster_images.md){target="_blank"}.

**Build x86_64 Images**

```bash title="Run on: omnia_core container"
cd /omnia/build_image_x86_64
ansible-playbook build_image_x86_64.yml
```

**Build aarch64 Images**

If your PXE mapping file contains aarch64 functional groups, you must
first prepare an aarch64 build node. See
[Prepare aarch64 Node](../Setup/prepare_aarch64_node.md){target="_blank"}
for the complete procedure (manual RHEL 10 installation, inventory file
creation, etc.).

```bash title="Run on: omnia_core container"
cd /omnia/build_image_aarch64
ansible-playbook build_image_aarch64.yml -i inventory
```

```ini title="Example: inventory"
[admin_aarch64]
10.0.0.1
```

**Verification -- Boot Images in S3**

After the build playbooks complete, verify the images are uploaded to
MinIO (S3). Each functional group produces **3 image artifacts**:
`rootfs` (full OS root filesystem), `vmlinuz` (Linux kernel), and
`initramfs` (initial RAM filesystem for PXE boot).

1. **List all boot images in S3**:

    ```bash title="Run on: OIM host"
    s3cmd ls s3://boot-images/
    ```

    Expected output (one directory per functional group plus `efi-images`):

    ```text title="Expected output"
                        DIR  s3://boot-images/efi-images/
                        DIR  s3://boot-images/login_compiler_node_x86_64/
                        DIR  s3://boot-images/slurm_control_node_x86_64/
                        DIR  s3://boot-images/slurm_node_x86_64/
    ```

2. **Verify individual image artifacts for a specific functional group**:

    ```bash title="Run on: OIM host"
    s3cmd ls -Hr s3://boot-images/slurm_control_node_x86_64/
    s3cmd ls -Hr s3://boot-images/efi-images/slurm_control_node_x86_64/
    ```

    Expected output:

    ```text title="Expected output"
    2026-06-26 11:42  1449M  s3://boot-images/slurm_control_node_x86_64/rhel-slurm_control_node_x86_64_omnia_2.2.0.0/rhel10.0-rhel-slurm_control_node_x86_64_omnia_2.2.0.0-10.0
    2026-06-26 11:42    78M  s3://boot-images/efi-images/slurm_control_node_x86_64/rhel-slurm_control_node_x86_64_omnia_2.2.0.0/initramfs-6.12.0-55.82.1.el10_0.x86_64.img
    2026-06-26 11:42    15M  s3://boot-images/efi-images/slurm_control_node_x86_64/rhel-slurm_control_node_x86_64_omnia_2.2.0.0/vmlinuz-6.12.0-55.82.1.el10_0.x86_64
    ```

!!! note

    The directories listed in `s3://boot-images/` correspond to the
    functional groups defined in your PXE mapping file. Each functional
    group will have exactly **3 image artifacts** (`rootfs`, `vmlinuz`,
    `initramfs`). The `efi-images/` directory contains the `initramfs`
    and `vmlinuz` boot files used during PXE network boot, while the root
    filesystem is stored directly under each functional group directory.
    If any artifacts are missing, re-run the corresponding build playbook.

### Step 7 -- Provision Nodes

The `provision.yml` playbook provisions the cluster nodes. It configures
boot scripts, cloud-init, and prepares nodes for Slurm deployment.

```bash title="Run on: omnia_core container"
cd /omnia/provision
ansible-playbook provision.yml
```

**Verification -- nodes.yaml**

After `provision.yml` completes, verify that all nodes from your PXE
mapping file are present in the generated `nodes.yaml` file. Every
node defined in `pxe_mapping_file.csv` should have a corresponding
entry with its hostname, functional group, MAC address, and IP address.

```bash title="Run on: omnia_core container"
cat /opt/omnia/openchami/workdir/nodes/nodes.yaml
```

Expected output (one entry per node in the PXE mapping file):

```yaml title="Expected output"
nodes:
- name: head01
  xname: x1000c0s0b0n0
  description: SVCTAG01
  nid: 1
  group: slurm_control_node_x86_64
  bmc_mac: a2:b3:c4:d5:e6:f7
  bmc_ip: 10.3.0.XXX
  interfaces:
  - mac_addr: a1:b2:c3:d4:e5:f6
    ip_addrs:
    - name: management
      ip_addr: 10.5.0.XXX
- name: compute01
  xname: x1000c0s0b1n0
  description: SVCTAG02
  nid: 2
  group: slurm_node_x86_64
  bmc_mac: b2:c3:d4:e5:f6:a7
  bmc_ip: 10.3.0.XXX
  interfaces:
  - mac_addr: b1:c2:d3:e4:f5:a6
    ip_addrs:
    - name: management
      ip_addr: 10.5.0.XXX
...
```

!!! note

    Post execution of `provision.yml`, IPs and hostnames cannot be
    re-assigned by changing the mapping file.

!!! caution

    - Do not run `ssh-keygen` post execution of `provision.yml` to avoid
      breaking the password-less SSH channel on the OIM.
    - Do not delete the Omnia shared path or the NFS directory.

For troubleshooting boot issues, IP route conflicts, and cloud-init failures, see [Provisioning Issues](../../Troubleshooting/provisioning.md).

### Step 8 -- PXE Boot Nodes

After `provision.yml` completes, PXE boot all Slurm-related nodes.

**Option 1: Manual PXE Boot**

Configure each node to boot from the PXE enabled NIC, whose mac address is listed in `pxe_mapping_file.csv`, via iDRAC or BIOS settings.

**Option 2: Automated PXE Boot**
This option boots all nodes via PXE through the iDRAC Redfish API.
After reboot, the nodes boot from the network, retrieve their OS image from S3, and run `cloud-init` to complete provisioning.
For more information, see the [PXE Boot playbook](../Setup/configure_pxe_boot.md).


```bash title="Run on: omnia_core container"
cd /omnia/utils
ansible-playbook set_pxe_boot.yml
```

!!! warning

    This playbook will restart your servers and power them on if they
    are off. Any unsaved data will be lost.

!!! note
    
    - Setting the boot device order has to be done manually before executing this playbook. This is a one time setup.

**Verification -- Cloud-Init Provisioning Status**

After the nodes PXE boot, verify that cloud-init has completed on all
nodes. SSH from `omnia_core` into each node using its hostname from the
PXE mapping file (`HOSTNAME` column):

```bash title="Run on: omnia_core container (example for 2 nodes)"
ssh head01 'cloud-init status'
ssh compute01 'cloud-init status'
```

Expected output on each node:

```text title="Expected output"
status: done
```

!!! note

    Check **every node** in your cluster. Open your PXE mapping file 
    and run
    `ssh <HOSTNAME> 'cloud-init status'` for each entry. All nodes must
    report `status: done` before proceeding.


## Verification

1. **Check Slurm controller status**:

    ```bash title="Run on: Slurm controller node"
    systemctl status slurmctld
    ```

    Expected output:

    ```text title="Expected output"
    ● slurmctld.service - Slurm controller daemon
       Loaded: loaded (/usr/lib/systemd/system/slurmctld.service; enabled; preset: disabled)
       Active: active (running) since ...
    ```

2. **Check Slurm cluster status**:

    ```bash title="Run on: Slurm controller node"
    sinfo
    ```

    Expected output:

    ```text title="Expected output"
    PARTITION AVAIL  TIMELIMIT  NODES  STATE NODELIST
    normal*      up   infinite      2   idle compute-node[1-2]
    ```

3. **Run a test job**:

    ```bash title="Run on: Slurm controller node"
    srun -N 1 hostname
    sbatch --wrap="echo Hello from \$(hostname)" --output=/tmp/hello.out
    cat /tmp/hello.out
    ```

    Expected output:
 
    ```text title="Expected output"
    <node_name>
    Hello from <node_name>
    ```

4. **Verify from login node**:

    ```bash title="Run on: login/login_compiler node"
    srun -N 1 hostname
    ```
    
    Expected output:
 
    ```text title="Expected output"
    <node_name>
    ```
    
5. **Check Slurm accounting**:

    ```bash title="Run on: Slurm controller node"
    sacctmgr show cluster
    ```

    Expected output:

    ```text title="Expected output"
    Cluster     ControlHost  ControlPort  RPC     Share GrpJobs GrpNodes GrpSubmit GrpWall  GrpTRES   MaxJobs MaxNodes MaxSubmit MaxWall MaxTRES QOS   Default QOS
    slurm       head01       6817         6817    1     1        1        1         1        1         1        1        1         1       normal
    ```

## Next Steps

- [Slurm with GPU](slurm_with_gpu.md) -- Configure GPU support for Slurm nodes
- [NVIDIA HPC SDK Setup](setup_nvhpc_sdk.md) -- Install NVIDIA HPC SDK on compiler and compute nodes
- [Add Slurm Nodes](add_slurm_nodes.md) -- Add more compute nodes to the cluster
- [Config Backup](slurm_config_backup.md) -- Back up Slurm configuration
- [Run HPC Benchmarks](run_hpc_benchmarks.md) -- Validate cluster performance

## Troubleshooting

**`slurmctld` not starting**

   Check the slurmctld log and verify munge is running:

   ```bash title="Run on: Slurm controller node"
   tail -100 /var/log/slurm/slurmctld.log
   systemctl status munge
   ```

   Validate the configuration and fix spool directory permissions:

   ```bash title="Run on: Slurm controller node"
   slurmd -C
   chown -R slurm:slurm /var/spool/slurmctld/
   chmod 755 /var/spool/slurmctld/
   ```


**Nodes Entering DRAINED State**
   
   Fix the epilog script permissions and reconfigure Slurm:

   ```bash title="Run on: Slurm controller node"
   chmod 0755 /etc/slurm/epilog.d/logout_user.sh
   scontrol reconfigure
   ```


**Nodes stuck in DOWN state**
   
   Check the reason and verify `slurmd` is running on the compute node:

   ```bash title="Run on: Slurm controller node"
   scontrol show node <nodename> | grep -i reason
   ssh <nodename> systemctl status slurmd
   ```

   Resume the node after fixing the underlying issue:

   ```bash title="Run on: Slurm controller node"
   scontrol update NodeName=<nodename> State=RESUME
   ```

**`slurmdbd` connection issues**
   
   Check `slurmdbd` and MariaDB status:

   ```bash title="Run on: Slurm controller node"
   systemctl status slurmdbd
   systemctl status mariadb
   ```

   Test database connectivity and restart if needed:

   ```bash title="Run on: Slurm controller node"
   mysql -u slurm -p -h localhost slurm_acct_db -e "SELECT 1;"
   systemctl restart slurmdbd
   systemctl restart slurmctld
   ```

**`sacct` erroring out or returning empty results**
   
   Check `slurmdbd` service and port:

   ```bash title="Run on: Slurm controller node"
   systemctl status slurmdbd
   ss -tlnp | grep 6819
   ```

   Restart the services:

   ```bash title="Run on: Slurm controller node"
   systemctl restart slurmdbd
   systemctl restart mariadb
   ```

For the complete list, see [Slurm Issues](../../Troubleshooting/slurm.md).
