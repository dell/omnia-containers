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

### Step 1: Provide Inputs

For Slurm deployment, update the following input files in
`/opt/omnia/input/project_default/`:

**Key files for this deployment:**

- [`network_spec.yml`](../../Reference/Configuration/network_spec.md) -- Network CIDRs and interfaces
- [`provision_config.yml`](../../Reference/Configuration/provision_config.md) -- OS provisioning settings
- [`pxe_mapping_file.csv`](../../Reference/SampleFiles/pxe_mapping_file.md) -- Node-to-role mapping for PXE boot
- [`omnia_config.yml`](../../Reference/Configuration/omnia_config.md) -- Slurm cluster settings
- [`storage_config.yml`](../../Reference/Configuration/storage_config.md) -- NFS storage mount configuration
- [`software_config.json`](../../Reference/Configuration/software_config.md) -- Software stack (Slurm packages)
- [`local_repo_config.yml`](../../Reference/Configuration/local_repo_config.md) -- Repository mirror settings
- [`telemetry_config.yml`](../../Reference/Configuration/telemetry_config.md) -- Telemetry pipeline configuration (optional)

### Step 2: Set Credentials

Run the credential utility playbook to securely store passwords for
provisioning, iDRAC, and other services.

```bash title="Run on: omnia_core container"
cd /omnia/utils/credential_utility
ansible-playbook get_config_credentials.yml
```

**Credentials required for a Slurm deployment:**

| Credential | Parameter | Required | Details |
|---|---|---|---|
| Provision password | `provision_password` | Mandatory | Root password for provisioned nodes. Min 8 characters. |
| BMC (iDRAC) username | `bmc_username` | Mandatory | Must be the same across all servers. |
| BMC (iDRAC) password | `bmc_password` | Mandatory | Min 3 characters. |
| Pulp container password | `pulp_password` | Mandatory | Used for the Pulp repository container. Min 8 characters. |
| Minio S3 bucket password | `minio_s3_password` | Mandatory | 5–128 characters. Must not be set to `admin`. |
| Slurm database password | `slurm_db_password` | Mandatory for Slurm | Password for SlurmDB (MariaDB). Username is auto-generated (`slurm`). Must not contain `-`, `'`, `"`, or `\`. |
| MySQL DB username | `mysqldb_user` | Mandatory | Required for iDRAC telemetry services. |
| MySQL DB password | `mysqldb_password` | Mandatory | Required for iDRAC telemetry services. |
| MySQL DB root password | `mysqldb_root_password` | Mandatory | Root password for the MySQL database. |

!!! caution
    Passwords must not contain commas (`,`), hyphens (`-`), single
    quotes (`'`), double quotes (`"`), or backslashes (`\`) unless
    otherwise specified.

### Step 3: Create the PXE Mapping File

Create a `pxe_mapping_file.csv` in `/opt/omnia/input/project_default/` and
set the `pxe_mapping_file_path` variable in `provision_config.yml` to point
to it.

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

#### Alternative: Discover Nodes via OME

If you did not create the `pxe_mapping_file.csv` manually, you can use
OpenManage Enterprise (OME) to automatically discover servers and
generate the PXE mapping file.

1. In OME, discover the cluster nodes. See the
   [OpenManage Enterprise User Guide](https://dl.dell.com/content/manual4/en/openmanage-enterprise-user-guide-en)
   for details.

2. Create static groups in OME for each functional group you plan to
   use (e.g., `slurm_control_node_x86_64`, `slurm_node_x86_64`,
   `login_node_x86_64`). Group names must exactly match the Omnia
   functional group names.

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

!!! note
    Devices not assigned to any Omnia-supported static group in OME
    default to `slurm_node_aarch64` in the generated PXE mapping file.

### Step 4: Edit Input Files

#### 4a. Edit omnia_config.yml

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

#### 4b. Edit storage_config.yml

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

#### 4c. Edit software_config.json

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

#### 4d. Edit local_repo_config.yml

Edit [`local_repo_config.yml`](../../Reference/Configuration/local_repo_config.md) and add
your Slurm RPM repository URL under `user_repo_url_x86_64` (and
`user_repo_url_aarch64` for ARM nodes):

```yaml title="File: /opt/omnia/input/project_default/local_repo_config.yml"
user_repo_url_x86_64:
  - { url: "http://<your-slurm-repo>/x86_64/", gpgkey: "", name: "slurm_custom" }
```

!!! important
    The repository `name` must be `slurm_custom` to match the
    `software_config.json` entry.

#### 4e. Edit telemetry_config.yml (optional)

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
    For Slurm-only deployments without service K8s, set
    `telemetry_sources.idrac.metrics_enabled` to `false`.

### Step 6: Prepare the OIM

Run `prepare_oim.yml` to configure the OIM for cluster deployment.

```bash title="Run on: omnia_core container"
cd /omnia/prepare_oim
ansible-playbook prepare_oim.yml
```

The `prepare_oim.yml` playbook deploys the following on the OIM:

- OpenCHAMI containers
- PostgreSQL database container
- Omnia Auth container
- Pulp container

### Step 7: Verify OIM Services

After `prepare_oim.yml` completes, verify that all Omnia-managed
services are running:

```bash title="Run on: OIM host"
systemctl list-dependencies omnia.target
```

Every listed service should show a green circle indicating `active`.
Key services to verify:

- `omnia_core.service`
- `pulp.service`
- `registry.service`
- `openchami.target` and its dependent services

!!! note
    After `prepare_oim.yml` execution, `ssh omnia_core` may fail if you
    switch from a non-root to root user using `sudo`. Log in directly as
    root before executing the playbook.

### Step 8: Create Local Repositories

Download required packages and repositories for offline node
provisioning.

!!! tip
    If you need to build custom Slurm RPMs from source or host them on
    a local server, complete these steps first:

    - [Build Slurm RPM Repository](build_slurm_repo.md)
    - [Host Slurm RPM Repository](host_slurm_repo.md)

```bash title="Run on: omnia_core container"
ansible-playbook local_repo.yml
```

Confirm repository synchronization completed successfully by checking
the repository logs.

### Step 9: Build Node Images

Build diskless images for each functional group defined in the mapping
file.

#### x86_64

```bash title="Run on: omnia_core container"
cd /omnia/build_image_x86_64
ansible-playbook build_image_x86_64.yml
```

#### aarch64

1. Navigate to the image build directory and run the playbook with an
   inventory file specifying the aarch64 node IP:

    ```bash title="Run on: omnia_core container"
    cd /omnia/build_image_aarch64
    ansible-playbook build_image_aarch64.yml -i inventory
    ```

    ```ini title="Example: inventory"
    [admin_aarch64]
    10.0.0.1
    ```

Verify that images are created for each functional group:

```bash title="Run on: OIM host"
s3cmd ls -Hr s3://boot-images
```

### Step 10: Provision Nodes

Run `provision.yml` to discover cluster nodes, configure boot scripts,
and generate cloud-init files based on the functional groups in the PXE
mapping file.

```bash title="Run on: omnia_core container"
ansible-playbook provision.yml
```

Verify that:

- Nodes are discovered successfully.
- Cloud-init files are generated.
- Provision logs show successful configuration.

During provisioning, Omnia automatically configures each node based on
its functional group:

- **Slurm controller**: Installs MariaDB, generates munge key, starts
  `slurmdbd` and `slurmctld`, configures firewall ports
- **Compute nodes**: Mounts NFS-shared Slurm configuration, starts
  `slurmd` in configless mode
- **Login / compiler nodes**: Mounts shared configuration, enables Slurm
  client commands (`srun`, `sbatch`, `squeue`)

### Step 11: PXE Boot Nodes

After `provision.yml` completes, PXE boot all Slurm-related nodes:

- Controller node
- Compute nodes
- Login nodes
- Login/compiler nodes

**Option 1: Manual PXE Boot**

Configure each node to boot from the network via iDRAC or BIOS settings.

**Option 2: Automated PXE Boot**

```bash title="Run on: omnia_core container"
ansible-playbook utils/set_pxe_boot.yml
```

Ensure all nodes boot successfully and become reachable.

## Slurm Configuration

### Default Configuration

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

### Custom Configuration

For detailed information on custom Slurm configuration, merge control,
node discovery modes, and configuration validation, see
[Configure Slurm](configure_slurm.md).

## Verification

1. **Check Slurm controller status**:

    ```bash title="Run on: Slurm controller node"
    systemctl status slurmctld
    sinfo
    ```

    ```text title="Expected output"
    PARTITION AVAIL  TIMELIMIT  NODES  STATE NODELIST
    normal*      up   infinite      2   idle compute-node[1-2]
    ```

2. **Run a test job**:

    ```bash title="Run on: Slurm controller node"
    srun -N 1 hostname
    sbatch --wrap="echo Hello from \$(hostname)" --output=/tmp/hello.out
    cat /tmp/hello.out
    ```

3. **Verify from login node**:

    ```bash title="Run on: login/login_compiler node"
    srun -N 1 hostname
    ```

4. **Check Slurm accounting**:

    ```bash title="Run on: Slurm controller node"
    sacctmgr show cluster
    ```

!!! tip
    Run `srun -N 1 --pty bash` to get an interactive shell on a compute
    node -- useful for debugging and verifying software installations.

## Next Steps

- [Slurm with GPU](slurm_with_gpu.md) -- Configure GPU support for Slurm nodes
- [Add Slurm Nodes](add_slurm_nodes.md) -- Add more compute nodes to the cluster
- [Config Backup](slurm_config_backup.md) -- Back up Slurm configuration
- [Run HPC Benchmarks](run_hpc_benchmarks.md) -- Validate cluster performance

## Troubleshooting

For Slurm troubleshooting, see
[Slurm Issues](../../Troubleshooting/slurm.md).
