# Path B: Kubernetes + Telemetry Only


Deploy a Kubernetes service cluster (minimum 5 nodes) with the full Omnia
telemetry pipeline -- without Slurm. Use this path when your goal is infrastructure
monitoring via iDRAC metrics, OS-level telemetry, and time-series storage,
with no HPC job scheduler required.

**What you will build:**

| Role | Functional Group | Count | Purpose |
| --- | --- | --- | --- |
| OIM (management) | -- | 1 | Runs `omnia_core`; orchestrates the deployment. |
| K8s control plane | `service_kube_control_plane_x86_64` | 3 | HA Kubernetes control plane (`kube-apiserver`, `etcd`, `kube-scheduler`, `kube-controller-manager`). |
| K8s worker node | `service_kube_node_x86_64` | 1 | Runs the telemetry stack: iDRAC collector, LDMS aggregator, Kafka, VictoriaMetrics, VictoriaLogs, and Vector pipeline. |

**Telemetry pipeline architecture:**

Omnia's telemetry pipeline collects metrics and logs from multiple sources,
routes them through Kafka and dedicated agents, and stores them in
VictoriaMetrics (time-series metrics) and VictoriaLogs (log data). The
pipeline is organized into **sources**, **bridges**, and **sinks**.

```text title="Core telemetry data flows"
iDRAC (Redfish) ─> iDRAC Collector ─> ActiveMQ ─┬─ KafkaPump ─> Kafka 'idrac' topic
                                                └─ VictoriaPump ─> vmagent ─> VictoriaMetrics

LDMS (OS-level) ─> Aggregator ─> Store ─> Kafka 'ldms' topic
                                           └─> Vector-LDMS ─> vmagent-vector ─> VictoriaMetrics
```

```text title="Storage, fabric, and external data flows"
PowerScale ─> CSM Metrics ─> OTEL Collector ─> vmagent(shared) ─> VictoriaMetrics
                                            └─> vlagent ─> VictoriaLogs

UFM (InfiniBand) ─> vmagent(shared) ─> VictoriaMetrics / vlagent ─> VictoriaLogs
VAST (Storage)   ─> vmagent(shared) ─> VictoriaMetrics / vlagent ─> VictoriaLogs

OME (Fleet Mgmt) ─> Kafka 'ome.*' ─> Vector-OME ─> vmagent-vector ─> VictoriaMetrics
                                                └─> vlagent-vector ─> VictoriaLogs
```

**Core telemetry sources:**

- **iDRAC collector** polls each server's Redfish endpoint for hardware
  metrics (temperatures, power consumption, fan speeds, storage health,
  CPU/memory errors). Data flows through ActiveMQ and is routed to both
  Kafka and VictoriaMetrics via KafkaPump and VictoriaPump.
- **LDMS** (Lightweight Distributed Metric Service) collects OS-level
  metrics (CPU, memory, network, disk) from compute nodes via sampler
  plugins (meminfo, procstat2, vmstat, loadavg, procnetdev2). Data flows
  through the LDMS aggregator and store to Kafka. Enable Vector-LDMS to
  route LDMS metrics from Kafka to VictoriaMetrics.
- **DCGM** (NVIDIA Data Center GPU Manager) is available on GPU nodes for
  collecting GPU metrics (temperature, utilization, memory, ECC errors, power).
  Users can manually run DCGM commands on GPU nodes to read GPU metrics directly.
- **PowerScale** collects storage metrics from Dell PowerScale (OneFS)
  clusters via CSM Observability (Karavi). Metrics flow through OTEL
  Collector to VictoriaMetrics; logs are sent to VictoriaLogs.
- **UFM** collects NVIDIA InfiniBand Fabric Manager metrics (IB port
  state, transmit/receive data, error counters) and syslog logs. Metrics
  go to VictoriaMetrics; logs go to VictoriaLogs.
- **VAST** collects storage metrics and syslog events from VAST Storage
  appliances. Metrics go to VictoriaMetrics; logs go to VictoriaLogs.
- **OME** (OpenManage Enterprise) collects server inventory, health, alerts,
  and firmware metrics from Dell OME. OME publishes data to Kafka `ome.*`
  topics. Enable Vector-OME bridge to route OME data from Kafka to
  VictoriaMetrics and VictoriaLogs.

**Telemetry bridges (Vector pipeline):**

- **Vector-LDMS** consumes LDMS metrics from the Kafka `ldms` topic,
  transforms them to Prometheus format, and writes to VictoriaMetrics
  via a dedicated vmagent-vector instance.
- **Vector-OME** consumes OpenManage Enterprise metrics and logs from
  Kafka `ome.*` topics, routing metrics to VictoriaMetrics and logs to
  VictoriaLogs via vlagent-vector.

**Telemetry sinks (storage):**

- **Kafka** (deployed via Strimzi operator) acts as the message broker,
  decoupling collectors from storage. Retains messages for a configurable
  period (default: 7 days).
- **VictoriaMetrics** (cluster mode with vminsert, vmstorage, vmselect)
  provides high-performance time-series storage with configurable retention.
- **VictoriaLogs** (cluster mode with vlinsert, vlstorage, vlselect)
  provides distributed log storage for telemetry logs and events.

**Estimated time:** ~2 hours.

!!! note

    Complete the [Prerequisites Checklist](prerequisites_checklist.md) before proceeding. Pay
    particular attention to the **iDRAC Settings** section (Datacenter
    license required for telemetry) and **Service Kubernetes Requirements**
    (3 control-plane nodes with 64 GB RAM each).

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

!!! caution
    The password must not contain special characters such as
    `, |, &, ;, \`, <>, *, ?, !, $, (), {}, []`.

**Verification**

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

!!! warning
    - Do not delete any key pairs generated by Omnia from `/root/.ssh`
      -- this causes `omnia_core.service` execution failure.
    - Do not manually delete files from the Omnia shared directory. Use
      `./omnia.sh --uninstall` to safely remove.



## Step 2 -- Create the Mapping File

Omnia supports two methods for creating the PXE mapping file:

- **Manual** -- Collect PXE NIC information and fill in the
  `pxe_mapping_file.csv` manually.
- **OME-based discovery (recommended)** -- Use OpenManage Enterprise (OME)
  to discover cluster nodes and auto-generate the mapping file using
  `discovery.yml`.

For this path, the mapping file contains **only** Kubernetes roles -- no
Slurm functional groups.

**Option A: Fill the PXE mapping file manually**

Create a `pxe_mapping_file.csv` in
`/opt/omnia/input/project_default/` and set the `pxe_mapping_file_path`
variable in `provision_config.yml` to point to it.

```csv title="/opt/omnia/input/project_default/pxe_mapping_file.csv"
FUNCTIONAL_GROUP_NAME,GROUP_NAME,SERVICE_TAG,PARENT_SERVICE_TAG,HOSTNAME,ADMIN_MAC,ADMIN_IP,BMC_MAC,BMC_IP
service_kube_control_plane_x86_64,kube,SVCTAG01,,kube-cp01,24:6E:96:BB:01:01,10.5.0.201,,10.3.0.201
service_kube_control_plane_x86_64,kube,SVCTAG02,,kube-cp02,24:6E:96:BB:01:02,10.5.0.202,,10.3.0.202
service_kube_control_plane_x86_64,kube,SVCTAG03,,kube-cp03,24:6E:96:BB:01:03,10.5.0.203,,10.3.0.203
service_kube_node_x86_64,kube,SVCTAG04,,kube-wk01,24:6E:96:BB:02:01,10.5.0.204,,10.3.0.204
```

!!! warning
    Replace all placeholder values (`SVCTAG*`, MAC addresses, IPs) with
    your actual hardware data.

!!! note
    - All header fields are case-sensitive.
    - The `ADMIN_MAC` and `BMC_MAC` addresses should refer to the PXE
      NIC and BMC NIC on the target nodes respectively.
    - Target servers should be configured to boot in PXE mode with the
      appropriate NIC as the first boot device.
    - Hostnames should not contain the domain name of the nodes.

For detailed information on PXE mapping file format and parameters, see
[PXE Mapping File](../Reference/SampleFiles/pxe_mapping_file.md).

**Option B: Create PXE file using OME**

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

    Ensure at least **3 rows** use the
    `service_kube_control_plane_x86_64` functional group and at least **1 row**
    uses `service_kube_node_x86_64`. HA requires a minimum of 3 control-plane
    nodes.

## Step 3 -- Provide Inputs

Configure the input files that define your cluster's network, provisioning,
telemetry, and storage settings. For a K8s + telemetry deployment, update the
following input files in `/opt/omnia/input/project_default/`. Click each file
name to view the full parameter reference.

| Input File | Purpose |
| --- | --- |
| [`network_spec.yml`](../Reference/Configuration/network_spec.md) | Network CIDRs, interfaces, and IP ranges |
| [`provision_config.yml`](../Reference/Configuration/provision_config.md) | OS provisioning and PXE settings |
| [`high_availability_config.yml`](../Reference/Configuration/high_availability_config.md) | Kubernetes HA virtual IP configuration |
| [`telemetry_config.yml`](../Reference/Configuration/telemetry_config.md) | Telemetry sources, bridges, and sinks |
| [`software_config.json`](../Reference/Configuration/software_config.md) | Software stack for K8s and telemetry |
| [`local_repo_config.yml`](../Reference/Configuration/local_repo_config.md) | Repository mirror settings |
| [`storage_config.yml`](../Reference/Configuration/storage_config.md) | NFS storage mount configuration |
| [`omnia_config.yml`](../Reference/Configuration/omnia_config.md) | Service cluster K8s settings (cluster name, CNI, pod IP range, NFS storage) |
| [`telemetry_storage_config.yml`](../Reference/Configuration/telemetry_config.md#telemetry-storage-configuration-parameters) (optional) | Storage and resource settings for telemetry components |

**K8s + Telemetry specific guidance**

**`software_config.json`** -- The `service_k8s` entry is **mandatory**.
Without it, Omnia skips telemetry deployment entirely.

```json title="Minimum required entries"
{
  "softwares": [
    {"name": "default_packages", "arch": ["x86_64"]},
    {"name": "service_k8s", "version": "1.35.1", "arch": ["x86_64"]}
  ]
}
```

For the full procedure and parameter reference, see
[Configure Inputs](../HowTo/Setup/configure_inputs.md){target="_blank"}.

!!! caution

    LDMS telemetry requires Slurm to be deployed. To enable LDMS along with the full Slurm + K8s stack, refer to the [Full Deployment](full_deployment.md) guide.

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
[Verify OIM Services](../HowTo/Setup/verify_oim_services.md){target="_blank"}.

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

    Expect **30--60 minutes** depending on network speed. This step
    downloads Kubernetes packages, container images for the telemetry
    stack (VictoriaMetrics, VictoriaLogs, Kafka, Vector), and base OS
    packages. Total download size is typically **~20 GB**.

**Verification -- Local Repository Status**

After `local_repo.yml` completes, verify that all software components
were downloaded successfully by checking the `software.csv` status file:

```bash title="Run on: omnia_core container"
cat /opt/omnia/log/local_repo/rhel/10.0/x86_64/software.csv
```

Expected output:

```text title="Expected output"
name,status
default_packages,success
service_k8s,success
```

!!! note

    The `software.csv` output reflects the software components configured
    in `software_config.json`. All entries must show `success` status
    before proceeding.

## Step 6 -- Build Node Images

Builds diskless OS images for each functional group in the PXE mapping
file and uploads them to MinIO (S3) for PXE boot delivery.

For details, see
[Build Cluster Images](../HowTo/Setup/build_cluster_images.md){target="_blank"}.

```bash title="Run on: omnia_core container"
cd /omnia/build_image_x86_64
ansible-playbook build_image_x86_64.yml
```

**Verification -- Boot Images in S3**

After the build playbook completes, verify the images are uploaded to
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
                        DIR  s3://boot-images/service_kube_control_plane_first_x86_64/
                        DIR  s3://boot-images/service_kube_control_plane_x86_64/
                        DIR  s3://boot-images/service_kube_node_x86_64/
    ```

2. **Verify individual image artifacts for a specific functional group**:

    ```bash title="Run on: OIM host"
    s3cmd ls -Hr s3://boot-images/service_kube_control_plane_x86_64/
    s3cmd ls -Hr s3://boot-images/efi-images/service_kube_control_plane_x86_64/
    ```

    Expected output:

    ```text title="Expected output"
    2026-06-26 11:43  1494M  s3://boot-images/service_kube_control_plane_x86_64/rhel-service_kube_control_plane_x86_64_omnia_2.2.0.0_k8s_1.35.1/rhel10.0-rhel-service_kube_control_plane_x86_64_omnia_2.2.0.0_k8s_1.35.1-10.0
    2026-06-26 11:42    78M  s3://boot-images/efi-images/service_kube_control_plane_x86_64/rhel-service_kube_control_plane_x86_64_omnia_2.2.0.0_k8s_1.35.1/initramfs-6.12.0-55.82.1.el10_0.x86_64.img
    2026-06-26 11:42    15M  s3://boot-images/efi-images/service_kube_control_plane_x86_64/rhel-service_kube_control_plane_x86_64_omnia_2.2.0.0_k8s_1.35.1/vmlinuz-6.12.0-55.82.1.el10_0.x86_64
    ```
!!! note

    The directories listed in `s3://boot-images/` correspond to the
    functional groups defined in your PXE mapping file. Each functional
    group will have exactly **3 image artifacts** (`rootfs`, `vmlinuz`,
    `initramfs`). If any artifacts are missing, re-run the build playbook.



## Step 7 -- Provision Nodes

The `provision.yml` playbook provisions the cluster nodes. It configures
boot scripts, cloud-init, deploys iDRAC telemetry service, and deploys
LDMS on the service cluster.

```shell title="Run on omnia_core container"
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
- name: kube-cp01
  xname: x1000c0s0b0n0
  description: SVCTAG01
  nid: 1
  group: service_kube_control_plane_x86_64
  bmc_mac: 24:6E:96:BB:01:01
  bmc_ip: 10.3.0.XXX
  interfaces:
  - mac_addr: 24:6E:96:BB:01:01
    ip_addrs:
    - name: management
      ip_addr: 10.5.0.XXX
- name: kube-cp02
  xname: x1000c0s0b1n0
  description: SVCTAG02
  nid: 2
  group: service_kube_control_plane_x86_64
  bmc_mac: 24:6E:96:BB:01:02
  bmc_ip: 10.3.0.XXX
  interfaces:
  - mac_addr: 24:6E:96:BB:01:02
    ip_addrs:
    - name: management
      ip_addr: 10.5.0.XXX
- name: kube-wk01
  xname: x1000c0s0b2n0
  description: SVCTAG04
  nid: 4
  group: service_kube_node_x86_64
  bmc_mac: 24:6E:96:BB:02:01
  bmc_ip: 10.3.0.XXX
  interfaces:
  - mac_addr: 24:6E:96:BB:02:01
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

For troubleshooting boot issues, IP route conflicts, and cloud-init failures, see [Provisioning Issues](../Troubleshooting/provisioning.md).

## Step 8 -- PXE Boot Nodes

After `provision.yml` completes, PXE boot all Kubernetes-related nodes.

**Option 1: Manual PXE Boot**

Configure each node to boot from the network via iDRAC or BIOS settings.

**Option 2: Automated PXE Boot**

Sets PXE boot order on all nodes via iDRAC Redfish and reboots them.
Nodes boot from the network, load their OS image from S3, and execute
cloud-init to complete provisioning.

```bash title="Run on: omnia_core container"
cd /omnia/utils
ansible-playbook set_pxe_boot.yml
```

!!! warning

    This playbook will restart your servers and power them on if they
    are off. Any unsaved data will be lost.

**Verification -- Cloud-Init Provisioning Status**

After the nodes PXE boot, verify that cloud-init has completed on all
nodes. SSH from `omnia_core` into each node using its hostname from the
PXE mapping file (`HOSTNAME` column):

```bash title="Run on: omnia_core container (example for 2 nodes)"
ssh kube-cp01 'cloud-init status'
ssh kube-wk01 'cloud-init status'
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

**Verification -- Kubernetes Service Cluster**

SSH into any `service_kube_control_plane` node and verify all nodes
are `Ready`:

```bash title="Run on: omnia_core container (example)"
ssh kube-cp01 'kubectl get nodes'
```

Expected output:

```text title="Expected output"
NAME        STATUS   ROLES           AGE   VERSION
kube-cp01   Ready    control-plane   1d    v1.35.1
kube-cp02   Ready    control-plane   1d    v1.35.1
kube-cp03   Ready    control-plane   1d    v1.35.1
kube-wk01   Ready    <none>          1d    v1.35.1
```

For detailed cluster verification procedures, see
[Verify Cluster](../HowTo/Setup/verify_cluster.md){target="_blank"}.

## Step 9 -- Deploy iDRAC Telemetry (Optional)


The `telemetry.yml` playbook initiates the iDRAC telemetry service on the service cluster. For prerequisites, configuration details, and collecting telemetry from external nodes, see [Configure iDRAC Telemetry](../HowTo/Telemetry/configure_idrac.md).

!!! note

    This step is required **only** when `idrac: metrics_enabled` is set to `true` in `telemetry_config.yml`. It is not required for other telemetry types.

```shell title="Run on omnia_core container"
cd /omnia/telemetry
ansible-playbook telemetry.yml
```

!!! important

    If you want to enable additional telemetry components after the
    first successful deployment (by updating `telemetry_config.yml`),
    and Kubernetes is already up and running, execute the `telemetry.sh`
    script on kube-control-plane at path
    `<K8s_NFS_mount_point>/telemetry/telemetry.sh`.



## Step 10 -- Verify the Telemetry Pipeline


After deploying telemetry, verify that all telemetry pods and services are operational. Refer to the topics in the following table for instructions on verifying each telemetry service.

| Telemetry Service | Description | Topic |
| --- | --- | --- |
| iDRAC | Verify collection and ingestion of hardware telemetry metrics. | [iDRAC Telemetry -- Verification](../HowTo/Telemetry/configure_idrac.md#verification) |
| LDMS | Verify collection and routing of node-level telemetry metrics. | [LDMS Telemetry -- Verification](../HowTo/Telemetry/configure_ldms.md#verification) |
| PowerScale | Verify collection and ingestion of storage metrics and logs. | [PowerScale Telemetry -- Verification](../HowTo/Telemetry/configure_powerscale.md#verification) |
| UFM | Verify collection and ingestion of fabric metrics and logs. | [UFM Telemetry -- Verification](../HowTo/Telemetry/configure_ufm.md#verification) |
| VAST | Verify collection and ingestion of storage metrics and logs. | [VAST Telemetry -- Verification](../HowTo/Telemetry/configure_vast.md#verification) |
| OpenManage Enterprise (OME) | Verify collection and routing of OME metrics and logs. | [OME Telemetry -- Verification](../HowTo/Telemetry/telemetry_from_ome.md#verification) |


## What's Next?


Your K8s telemetry cluster is operational. Common next steps:

**Enable additional telemetry sources**
   Configure iDRAC, DCGM, PowerScale, UFM, VAST, or OME telemetry
   collection. See [Telemetry Setup](../HowTo/Telemetry/setup_telemetry.md)
   for an overview of all supported sources.

**Deploy PowerScale CSI driver**
   Enable persistent storage for Kubernetes workloads using
   [Deploy PowerScale CSI](../HowTo/Kubernetes/deploy_powerscale_csi.md).

**Configure high availability**
   Tune Kubernetes HA settings and virtual IP configuration using
   [Configure HA](../HowTo/Kubernetes/configure_ha.md).

**Scale the cluster**
   Add or remove nodes with
   [Add / Remove Nodes](../Operations/add_remove_nodes.md).

**Add Slurm later**
   Follow [Full Deployment](full_deployment.md) to add Slurm scheduling
   to this existing K8s + telemetry deployment.

!!! info

    - [Telemetry Setup](../HowTo/Telemetry/setup_telemetry.md) -- Telemetry sources and configuration
    - [Full Deployment](full_deployment.md) -- Add Slurm to this K8s deployment
    - [Prerequisites Checklist](prerequisites_checklist.md) -- Master checklist
    - [Telemetry Troubleshooting](../Troubleshooting/telemetry.md) -- Troubleshoot telemetry issues
