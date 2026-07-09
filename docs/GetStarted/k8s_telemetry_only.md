# Path C: Kubernetes + Telemetry Only


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

DCGM (GPU) ─> vmagent ─> VictoriaMetrics
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
- **DCGM** (NVIDIA Data Center GPU Manager) collects GPU metrics
  (temperature, utilization, memory, ECC errors, power) from nodes with
  NVIDIA GPUs. Metrics are sent directly to VictoriaMetrics via vmagent.
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


The `omnia_core` container is deployed on the OIM and managed as a systemd service. It contains the Omnia source code with Python and Ansible preinstalled.

```shell title="Run on OIM (as root)"
cd /opt
git clone https://github.com/dell/omnia.git
cd omnia

# Build container images
bash build_images.sh

# Install and start the omnia_core container
bash omnia.sh --install

# Verify
systemctl status omnia_core
```


```shell title="Run on OIM (as root)"
# Test container access
ssh omnia_core
exit
```



## Step 2 -- Create the Mapping File


The mapping file defines the cluster node roles and network details. For this path, it contains **only** Kubernetes roles -- no Slurm functional groups.

```shell title="Run on OIM (as root)"
cat > /opt/omnia/input/project_default/pxe_mapping.csv << 'EOF'
FUNCTIONAL_GROUP_NAME,GROUP_NAME,SERVICE_TAG,PARENT_SERVICE_TAG,HOSTNAME,ADMIN_MAC,ADMIN_IP,BMC_MAC,BMC_IP
service_kube_control_plane_x86_64,kube,SVCTAG01,,kube-cp01,24:6E:96:BB:01:01,10.5.0.201,,10.3.0.201
service_kube_control_plane_x86_64,kube,SVCTAG02,,kube-cp02,24:6E:96:BB:01:02,10.5.0.202,,10.3.0.202
service_kube_control_plane_x86_64,kube,SVCTAG03,,kube-cp03,24:6E:96:BB:01:03,10.5.0.203,,10.3.0.203
service_kube_node_x86_64,kube,SVCTAG04,,kube-wk01,24:6E:96:BB:02:01,10.5.0.204,,10.3.0.204
EOF
```


!!! warning

    Replace **all** placeholder values with your actual hardware data.
    The 3 `service_kube_control_plane_x86_64` entries are mandatory for
    Kubernetes HA -- do not reduce below 3.

## Step 3 -- Provide Inputs


Configure the input files that define your cluster's network, provisioning, telemetry, and storage settings. For K8s + telemetry deployment, update the following input files in
`/opt/omnia/input/project_default/`. Click each file name to view the
full parameter reference.

| Input File | Purpose |
| --- | --- |
| [`network_spec.yml`](../Reference/Configuration/network_spec.md) | Network CIDRs, interfaces, and IP ranges |
| [`provision_config.yml`](../Reference/Configuration/provision_config.md) | OS provisioning and PXE settings |
| [`high_availability_config.yml`](../Reference/Configuration/ha_config.md) | Kubernetes HA virtual IP configuration |
| [`telemetry_config.yml`](../Reference/Configuration/telemetry_config.md) | Telemetry sources, bridges, and sinks |
| [`software_config.json`](../Reference/Configuration/software_config.md) | Software stack for K8s and telemetry |
| [`local_repo_config.yml`](../Reference/Configuration/local_repo_config.md) | Repository mirror settings |
| [`storage_config.yml`](../Reference/Configuration/storage_config.md) | NFS storage mount configuration |
| [`omnia_config.yml`](../Reference/Configuration/omnia_config.md) | Service cluster K8s settings (cluster name, CNI, pod IP range, NFS storage) |
| [`telemetry_storage_config.yml`](../Reference/Configuration/telemetry_storage_config.md) (optional) | Storage and resource settings for telemetry components |

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

!!! caution

    LDMS telemetry requires Slurm to be deployed. To enable LDMS along with the full Slurm + K8s stack, refer to the [Full Deployment](full_deployment.md) guide.

## Step 4 -- Prepare the OIM


The `prepare_oim.yml` playbook sets up the OIM by deploying the OpenCHAMI containers, Pulp container, and other required services.

```shell title="Run on omnia_core container"
cd /omnia/prepare_oim
ansible-playbook prepare_oim.yml
```

**Verify OIM Services**

```shell title="Run on omnia_core container"
systemctl list-dependencies omnia.target
```

All services must show `active`.


## Step 5 -- Create Local Repositories


The `local_repo.yml` playbook downloads and saves software packages and container images to the Pulp container, making them available to all cluster nodes.

```shell title="Run on omnia_core container"
cd /omnia/local_repo
ansible-playbook local_repo.yml
```


!!! warning

    This step downloads Kubernetes packages, container images for the
    telemetry stack (VictoriaMetrics, VictoriaLogs, Kafka, Vector), and
    base OS packages. Allow **30--60 minutes** and ~20 GB disk space.

## Step 6 -- Build Node Images


The `build_image_x86_64.yml` playbook builds diskless images for cluster nodes based on the functional groups defined in the mapping file.

```shell title="Run on omnia_core container"
cd /omnia/build_image_x86_64
ansible-playbook build_image_x86_64.yml
```


```shell title="Run on OIM"
# Verify the image was created
s3cmd ls -Hr s3://boot-images
```



## Step 7 -- Provision Nodes


The `provision.yml` playbook provisions the cluster nodes. It configures boot scripts, cloud-init, deploys iDRAC telemetry service, and deploys LDMS on the service cluster.

```shell title="Run on omnia_core container"
cd /omnia/provision
ansible-playbook provision.yml
```

**Verify Provision Nodes**

- After executing `provision.yml`, check log files at `/opt/omnia/log` for details.
- Omnia does not track OS installation on the target node. Verify installation status manually.

!!! note

    Post execution of `provision.yml`, IPs and hostnames cannot be re-assigned by changing the mapping file.

!!! caution

    - Do not run `ssh-keygen` post execution of `provision.yml` to avoid breaking the password-less SSH channel on the OIM.
    - Do not delete the Omnia shared path or the NFS directory.

For troubleshooting boot issues, IP route conflicts, and cloud-init failures, see [Provisioning Issues](../Troubleshooting/provisioning.md).


## Step 8 -- Set PXE Boot Order (Optional)


After running `provision.yml`, you can either manually PXE boot the nodes or use the `set_pxe_boot.yml` utility. This playbook sets the PXE boot order on target nodes via iDRAC so they automatically boot into the diskless image from the OIM.

!!! warning

    This playbook will restart your servers and power them on if they
    are off. Any unsaved data will be lost.

```shell title="Run on omnia_core container"
cd /omnia/utils
ansible-playbook set_pxe_boot.yml
```


## Step 9 -- Deploy iDRAC Telemetry (Optional)


The `telemetry.yml` playbook initiates the iDRAC telemetry service on the service cluster. For prerequisites, configuration details, and collecting telemetry from external nodes, see [Configure iDRAC Telemetry](../HowTo/Telemetry/configure_idrac.md).

!!! note

    This step is required **only** when `idrac: metrics_enabled` is set to `true` in `telemetry_config.yml`. It is not required for other telemetry types.

```shell title="Run on omnia_core container"
cd /omnia/telemetry
ansible-playbook telemetry.yml
```

!!! caution

    If you want to enable additional telemetry components after the
    first successful deployment (by updating `telemetry_config.yml`),
    and Kubernetes is already up and running, execute the `telemetry.sh`
    script on kube-control-plane at path
    `<K8s_NFS_mount_point>/telemetry/telemetry.sh`.



## Step 10 -- Verify the Telemetry Pipeline


After deploying telemetry, verify that all telemetry pods and services are operational. Refer to the topics in the following table for instructions on verifying each telemetry service.

| Telemetry Service | Description | Topic |
| --- | --- | --- |
| iDRAC | Verify collection and ingestion of hardware telemetry metrics. | [Configure iDRAC Telemetry -- Verification](../HowTo/Telemetry/configure_idrac.md#verification) |
| LDMS | Verify collection and routing of node-level telemetry metrics. | [Configure LDMS Telemetry -- Verification](../HowTo/Telemetry/configure_ldms.md#verification) |
| DCGM | Verify collection and ingestion of GPU telemetry metrics. | [Configure DCGM Telemetry -- Verification](../HowTo/Telemetry/configure_dcgm.md#verification) |
| PowerScale | Verify collection and ingestion of storage metrics and logs. | [Configure PowerScale Telemetry -- Verification](../HowTo/Telemetry/configure_powerscale.md#verification) |
| UFM | Verify collection and ingestion of fabric metrics and logs. | [Configure UFM Telemetry -- Verification](../HowTo/Telemetry/configure_ufm.md#verification) |
| VAST | Verify collection and ingestion of storage metrics and logs. | [Configure VAST Telemetry -- Verification](../HowTo/Telemetry/configure_vast.md#verification) |
| OpenManage Enterprise | Verify collection and routing of OME metrics and logs. | [Configure OME Telemetry -- Verification](../HowTo/Telemetry/telemetry_from_ome.md#verification) |
| Vector-LDMS Pipeline | Verify routing of LDMS telemetry from Kafka to VictoriaMetrics. | [Configure Vector-LDMS Pipeline -- Verification](../HowTo/Telemetry/configure_vector_ldms.md#verification) |


## What's Next?


Your K8s telemetry cluster is operational. For post-deployment tasks such as adding or removing nodes, enabling additional telemetry sources, configuring storage, and managing upgrades, see the [Operations Guide](../Operations/index.md).
