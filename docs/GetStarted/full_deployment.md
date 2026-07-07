# Path B: Full Deployment (Slurm + K8s + Telemetry)

Deploy a production-grade cluster with Slurm job scheduling, a highly
available Kubernetes service cluster, and telemetry. This is the canonical
Omnia deployment that exercises every major subsystem.

**What you will build:**

| Role | Functional Group | Count | Purpose |
| --- | --- | --- | --- |
| OIM (management) | -- | 1 | Runs `omnia_core`; orchestrates the deployment. |
| K8s control plane | `service_kube_control_plane_x86_64` | 3 | HA Kubernetes control plane (`kube-apiserver`, `etcd`, `kube-scheduler`, `kube-controller-manager`). |
| K8s worker node | `service_kube_node_x86_64` | 1 | Runs the telemetry stack: iDRAC collector, LDMS aggregator, Kafka, VictoriaMetrics. |
| Slurm control node | `slurm_control_node_x86_64` | 1 | Runs `slurmctld` (Slurm controller), `slurmdbd` (accounting), and MariaDB. |
| Slurm compute node(s) | `slurm_node_x86_64` / `slurm_node_aarch64` | 1+ | Run `slurmd`; execute jobs submitted to the cluster. |
| Login / compiler node | `login_compiler_node_x86_64` / `login_compiler_node_aarch64` | 1 | User-facing SSH gateway with compiler toolchains for job submission and building applications. |

**Estimated time:** ~4 hours.

!!! note

    Complete the [Prerequisites Checklist](prerequisites_checklist.md)
    before proceeding.

## Step 1 -- Deploy the omnia_core Container

Clone the Omnia artifacts repository, build the `omnia_core` container
image, and deploy the container on the OIM. The container packages the
complete Omnia codebase and Ansible engine.

For details, see
[Deploy Omnia Core](../HowTo/Setup/deploy_omnia_core.md){target="_blank"}.

1. **Clone the Omnia Artifactory repository and build the container image**:

    ```bash title="Run on: OIM host"
    git clone https://github.com/dell/omnia-artifactory.git -b omnia-container-v2.2.0.0
    cd omnia-artifactory
    ./build_images.sh core omnia_branch=v2.2.0.0 core_tag=2.2
    ```

2. **Download the `omnia.sh` script**:

    ```bash title="Run on: OIM host"
    wget https://raw.githubusercontent.com/dell/omnia/refs/tags/v2.2.0.0/omnia.sh
    chmod +x omnia.sh
    ```

3. **Install the omnia_core container**:

    ```bash title="Run on: OIM host"
    ./omnia.sh --install
    ```

    When prompted, enter the **shared directory path** (local or NFS) and a
    **secure alphanumeric password** for container access.

#### Verification

1. **Verify the `omnia_core` container is running**:

    ```bash title="Run on: OIM host"
    podman ps --filter name=omnia_core --format "table {{.Names}}\t{{.Image}}\t{{.Status}}\t{{.Ports}}"
    ```

    Expected output:

    ```text title="Expected output"
    NAMES        IMAGE                       STATUS       PORTS
    omnia_core   localhost/omnia_core:2.2     Up 1 day     2222/tcp
    ```

2. **Access the omnia_core container**:

    ```bash title="Run on: OIM host"
    ssh omnia_core
    ```

    You will be automatically logged in to the `omnia_core` container.

## Step 2 -- Create the Mapping File

Omnia supports two methods for creating the PXE mapping file:

- **Manual** -- Collect PXE NIC information and fill in the
  `pxe_mapping_file.csv` manually.
- **OME-based discovery (recommended)** -- Use OpenManage Enterprise (OME)
  to discover cluster nodes and auto-generate the mapping file using
  `discovery.yml`.

#### Option A: Fill the PXE mapping file manually

```bash title="Run on: omnia_core container"
vi /opt/omnia/input/project_default/pxe_mapping_file.csv
```

Populate one row per managed node with the required columns
(`FUNCTIONAL_GROUP_NAME`, `GROUP_NAME`, `SERVICE_TAG`, `HOSTNAME`,
`ADMIN_MAC`, `ADMIN_IP`, `BMC_IP`, etc.). For the complete column
reference and sample files, see
[PXE Mapping File Reference](../Reference/SampleFiles/pxe_mapping_file.md){target="_blank"}.

#### Option B: Create PXE file using OME

Use the `discovery.yml` playbook to auto-generate the mapping file from
an OME inventory. For detailed instructions including OME prerequisites,
static group setup, and iDRAC hostname conventions, see
[Discover Nodes Using OME](../HowTo/Setup/discover_nodes.md){target="_blank"}.

```bash title="Run on: omnia_core container"
cd /omnia/discovery
ansible-playbook discovery.yml -e "discovery_mechanism=ome"
```

The playbook generates a `bmc_pxe_mapping_file_<timestamp>.csv` in
`/opt/omnia/input/project_default/`. Verify and edit the file as needed.

!!! warning

    For a full deployment, ensure at least **3 rows** use the
    `service_kube_control_plane` functional group and at least **1 row**
    uses `service_kube_node`. HA requires a minimum of 3 control-plane
    nodes.

## Step 3 -- Provide Inputs

For a full deployment, update the following input files in
`/opt/omnia/input/project_default/`. Click each file name to view the
full parameter reference.

| Input File | Purpose |
| --- | --- |
| [`network_spec.yml`](../Reference/Configuration/network_spec.md){target="_blank"} | Network CIDRs, interfaces, and IP ranges |
| [`provision_config.yml`](../Reference/Configuration/provision_config.md){target="_blank"} | OS provisioning and PXE settings |
| [`high_availability_config.yml`](../Reference/Configuration/high_availability_config.md){target="_blank"} | Kubernetes HA virtual IP configuration |
| [`telemetry_config.yml`](../Reference/Configuration/telemetry_config.md){target="_blank"} | Telemetry sources, bridges, and sinks |
| [`telemetry_storage_config.yml`](../Reference/Configuration/telemetry_storage_config.md){target="_blank"} | Telemetry storage resources and retention |
| [`software_config.json`](../Reference/Configuration/software_config.md){target="_blank"} | Software stack (K8s, Slurm, telemetry components) |
| [`local_repo_config.yml`](../Reference/Configuration/local_repo_config.md){target="_blank"} | Repository mirror settings |
| [`storage_config.yml`](../Reference/Configuration/storage_config.md){target="_blank"} | NFS storage mount configuration |
| [`omnia_config.yml`](../Reference/Configuration/omnia_config.md){target="_blank"} | Slurm and service cluster K8s settings |
| [`security_config.yml`](../Reference/Configuration/security_config.md){target="_blank"} | OpenLDAP authentication settings |
| [`discovery_config.yml`](../Reference/Configuration/discovery_config.md){target="_blank"} | BMC discovery and OME integration |
| [`build_stream_config.yml`](../Reference/Configuration/build_stream_config.md){target="_blank"} | BuildStreaM CI/CD pipeline settings (optional) |
| [`additional_cloud_init.yml`](../Reference/Configuration/additional_cloud_init.md){target="_blank"} | Custom cloud-init scripts (optional) |

For the full procedure and parameter reference, see
[Configure Inputs](../HowTo/Setup/configure_inputs.md){target="_blank"}.

!!! note

    When you run `prepare_oim.yml` in the next step, you will be prompted
    for a **Vault password**. This password encrypts the credential file
    and is required for all subsequent playbook runs. Store it securely --
    if lost, you must re-run the credential utility. For details on which
    credentials are prompted, see
    [Configure Credentials](../HowTo/Setup/configure_credentials.md){target="_blank"}.

## Step 4 -- Prepare the OIM

Deploys the OIM infrastructure: OpenCHAMI provisioning stack, Pulp
local repository, container registry, MinIO S3 storage, OpenLDAP
authentication, and step-ca certificate authority.

For details, see
[Prepare OIM](../HowTo/Setup/prepare_oim.md){target="_blank"}.

```bash title="Run on: omnia_core container"
cd /omnia/prepare_oim
ansible-playbook prepare_oim.yml
```

#### Verification -- OIM Infrastructure

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

## Step 5 -- Create Local Repositories

Downloads all required RPM packages, container images, and tarballs
into Pulp based on `software_config.json` for air-gapped provisioning.

For details, see
[Create Local Repos](../HowTo/Setup/create_local_repos.md){target="_blank"}.

```bash title="Run on: omnia_core container"
cd /omnia/local_repo
ansible-playbook local_repo.yml
```

!!! note

    Expect **45--90 minutes** depending on network speed. Total download
    size is typically **20--40 GB**.

#### Verification -- Local Repository Status

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
    admin_debug_packages,success
    openldap,success
    service_k8s,success
    slurm_custom,success
    csi_driver_powerscale,success
    ldms,success
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
    `"arch": ["aarch64"]` appears in the aarch64 status file. Components
    such as `service_k8s` and `csi_driver_powerscale` are typically
    x86_64-only. All entries must show `success` status before proceeding.

## Step 6 -- Build Node Images

Builds diskless OS images for each functional group in the PXE mapping
file and uploads them to MinIO (S3) for PXE boot delivery.

For details, see
[Build Cluster Images](../HowTo/Setup/build_cluster_images.md){target="_blank"}.

#### Build x86_64 Images

```bash title="Run on: omnia_core container"
cd /omnia/build_image_x86_64
ansible-playbook build_image_x86_64.yml
```

#### Build aarch64 Images

If your PXE mapping file contains aarch64 functional groups, you must
first prepare an aarch64 build node. See
[Prepare aarch64 Node](../HowTo/Setup/prepare_aarch64_node.md){target="_blank"}
for the complete procedure (manual RHEL 10 installation, inventory file
creation, etc.).

```bash title="Run on: omnia_core container"
cd /omnia/build_image_aarch64
ansible-playbook build_image_aarch64.yml -i inventory
```

#### Verification -- Boot Images in S3

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
                        DIR  s3://boot-images/service_kube_control_plane_first_x86_64/
                        DIR  s3://boot-images/service_kube_control_plane_x86_64/
                        DIR  s3://boot-images/service_kube_node_x86_64/
                        DIR  s3://boot-images/slurm_control_node_x86_64/
                        DIR  s3://boot-images/slurm_node_x86_64/
                        DIR  s3://boot-images/slurm_node_aarch64/
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

## Step 7 -- Set PXE Boot and Provision Nodes

Sets PXE boot order on all nodes via iDRAC Redfish, reboots them, and
waits for cloud-init to complete provisioning (K8s, Slurm, NFS, SSH).

For details, see
[Configure PXE Boot](../HowTo/Setup/configure_pxe_boot.md){target="_blank"}.

```bash title="Run on: omnia_core container"
cd /omnia/utils
ansible-playbook set_pxe_boot.yml
```

!!! note

    With 8 nodes, provisioning can take **30--60 minutes**. Nodes are
    provisioned in parallel.

#### Verification -- Cloud-Init Provisioning Status

After the nodes PXE boot, verify that cloud-init has completed on all
nodes. SSH from `omnia_core` into each node using its hostname from the
PXE mapping file (`HOSTNAME` column):

```bash title="Run on: omnia_core container (example for 2 nodes)"
ssh scnode 'cloud-init status'
ssh kcp1 'cloud-init status'
```

Expected output on each node:

```text title="Expected output"
status: done
```

!!! note

    Check **every node** in your cluster. Open your PXE mapping file
    (`/opt/omnia/input/project_default/pxe_mapping_file.csv`) and run
    `ssh <HOSTNAME> 'cloud-init status'` for each entry. All nodes must
    report `status: done` before proceeding.

#### Verification -- Kubernetes Service Cluster

SSH into any `service_kube_control_plane` node and verify all nodes
are `Ready`:

```bash title="Run on: omnia_core container (example)"
ssh kcp1 'kubectl get nodes'
```

Expected output:

```text title="Expected output"
NAME   STATUS   ROLES           AGE   VERSION
kcp1   Ready    control-plane   1d    v1.35.1
kcp2   Ready    control-plane   1d    v1.35.1
kcp3   Ready    control-plane   1d    v1.35.1
kn     Ready    <none>          1d    v1.35.1
```

#### Verification -- Slurm Cluster

SSH into the `slurm_control_node` and verify all compute nodes are
`idle`:

```bash title="Run on: omnia_core container (example)"
ssh scnode 'sinfo'
```

Expected output:

```text title="Expected output"
PARTITION  AVAIL  TIMELIMIT  NODES  STATE  NODELIST
normal*    up     infinite   2      idle   snode[1-2]
```

For detailed cluster verification procedures, see
[Verify Cluster](../HowTo/Setup/verify_cluster.md){target="_blank"}.

## Step 8 -- Deploy Telemetry

The telemetry infrastructure (Kafka, VictoriaMetrics, LDMS, vmagent)
is deployed automatically during provisioning (Step 7). The
`telemetry.yml` playbook deploys the **iDRAC telemetry** StatefulSet
that collects hardware metrics (power, thermal, fan, CPU) from each
server's iDRAC via Redfish.

For details, see
[Telemetry Configuration](../Reference/Configuration/telemetry_config.md){target="_blank"}.

```bash title="Run on: omnia_core container"
cd /omnia/telemetry
ansible-playbook telemetry.yml
```

!!! note

    You do **not** need to run `telemetry.yml` if the service cluster is
    configured only for LDMS. LDMS begins collecting data automatically
    after provisioning.

#### Verification -- iDRAC Telemetry

SSH into any `service_kube_control_plane` node and verify the
`idrac-telemetry` pods are running with 5/5 containers ready:

```bash title="Run on: omnia_core container (example)"
ssh kcp1 'kubectl get pods -n telemetry -l app=idrac-telemetry'
```

Expected output:

```text title="Expected output"
NAME                READY   STATUS    RESTARTS      AGE
idrac-telemetry-0   5/5     Running   2 (48m ago)   144m
idrac-telemetry-1   5/5     Running   9 (42m ago)   144m
```

!!! note

    The `PARENT_SERVICE_TAG` column in the PXE mapping file groups
    nodes under parent servers. Each unique parent group gets one
    `idrac-telemetry` pod that collects metrics from all child nodes
    mapped to that parent. Nodes without a parent (control plane,
    standalone nodes) are collected by one additional pod. For example,
    if your mapping has 2 parent groups with multiple child nodes each,
    expect 3 pods — one per parent group + 1 for unparented nodes.

## What's Next?

Your cluster is fully operational with Slurm scheduling, Kubernetes
service cluster, and telemetry monitoring. This full deployment is a
combination of the Slurm and K8s telemetry paths — refer to those
guides for component-specific operations:

- **Slurm operations** -- Scale compute nodes, configure GPU scheduling,
  tune partitions, and run benchmarks. See
  [Slurm Quickstart](slurm_quickstart.md) for details.
- **Telemetry operations** -- Enable additional telemetry sources (DCGM,
  PowerScale, UFM, VAST, OME), configure retention, and monitor
  external servers. See
  [K8S Telemetry Only](k8s_telemetry_only.md) for details.
- **Enable BuildStreaM for GitOps** -- See
  [BuildStreaM Deployment](buildstream_deployment.md) to automate
  image building and deployment via CI/CD pipelines.

!!! info

    - [Slurm Quickstart](slurm_quickstart.md) -- Slurm-only deployment and operations
    - [K8S Telemetry Only](k8s_telemetry_only.md) -- K8s + telemetry deployment and operations
    - [Prerequisites Checklist](prerequisites_checklist.md) -- Master checklist
