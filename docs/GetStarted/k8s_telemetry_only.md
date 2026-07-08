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


The mapping file for this path contains **only** Kubernetes roles -- no
Slurm functional groups.

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


For K8s + telemetry deployment, update the following input files in
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

### K8s + Telemetry specific guidance

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

**`telemetry_config.yml`** -- Enable the telemetry sources you need
before running `prepare_oim.yml` so all required packages are included
in the local repo. Set `metrics_enabled: true` for each source (iDRAC,
LDMS, DCGM, PowerScale, UFM, VAST, OME).

```yaml title="Example: Enable iDRAC telemetry"
telemetry_sources:
  idrac:
    metrics_enabled: true
    collection_targets: [victoria_metrics, kafka]
  ...
```

**`high_availability_config.yml`** -- Configure the virtual IP for K8s
API server HA.

```yaml title="Example high_availability_config.yml"
service_k8s_cluster_ha:
- cluster_name: service_cluster
  enable_k8s_ha: true
  virtual_ip_address: 182.11.5.101
```

!!! warning

    The `virtual_ip_address` must not belong to `dynamic_range` in
    `network_spec.yml` or conflict with any IP in `mapping.csv`.

## Step 4 -- Prepare the OIM


```shell title="Run on omnia_core container"
cd /omnia/prepare_oim
ansible-playbook prepare_oim.yml
```


## Step 5 -- Verify OIM Services


```shell title="Run on omnia_core container"
systemctl list-dependencies omnia.target
```


All services must show `active`.


## Step 6 -- Create Local Repositories


```shell title="Run on omnia_core container"
cd /omnia/local_repo
ansible-playbook local_repo.yml
```


!!! warning

    This step downloads Kubernetes packages, container images for the
    telemetry stack (VictoriaMetrics, VictoriaLogs, Kafka, Vector), and
    base OS packages. Allow **30--60 minutes** and ~20 GB disk space.

## Step 7 -- Build Node Images


```shell title="Run on omnia_core container"
cd /omnia/build_image_x86_64
ansible-playbook build_image_x86_64.yml
```


```shell title="Run on OIM"
# Verify the image was created
s3cmd ls -Hr s3://boot-images
```



## Step 8 -- Provision Nodes


The `provision.yml` playbook provisions the cluster nodes. It configures
boot scripts, cloud-init, deploys iDRAC telemetry service, and deploys
LDMS on the service cluster.

```shell title="Run on omnia_core container"
cd /omnia/provision
ansible-playbook provision.yml
```


!!! note

    - After executing `provision.yml`, check log files at `/opt/omnia/log`
      for details.
    - To identify boot issues on a node, check `/var/log/cloud-init-output.log`
      on the target node.
    - Omnia does not track OS installation on the target node. Verify
      installation status manually.
    - Post execution, IPs/hostnames cannot be re-assigned by changing
      the mapping file.

!!! warning

    - In case of any IP route conflict between Admin network and
      additional NIC, delete the Admin route or configure the IP route
      priority based on your cluster requirements.
    - Do not run `ssh-keygen` post execution of `provision.yml` to avoid
      breaking the password-less SSH channel on the OIM.
    - Do not delete the Omnia shared path or the NFS directory.

**Optional: Set PXE boot order using `set_pxe_boot.yml`**

After running `provision.yml`, you can either manually PXE boot the
nodes or use the `set_pxe_boot.yml` utility. This playbook sets the PXE
boot order on target nodes via iDRAC so they automatically boot into the
diskless image from the OIM.

!!! warning

    This playbook will restart your servers and power them on if they
    are off. Any unsaved data will be lost.

```shell title="Run on omnia_core container (with inventory)"
cd /omnia/utils
ansible-playbook set_pxe_boot.yml -i inventory
```


```shell title="Run on omnia_core container (all nodes from mapping file)"
cd /omnia/utils
ansible-playbook set_pxe_boot.yml
```


## Step 9 -- Deploy Telemetry


The `provision.yml` playbook (Step 8) deploys the service Kubernetes
cluster and the core telemetry infrastructure. The `telemetry.yml`
playbook initiates the iDRAC telemetry service on the service cluster
based on the enabled components in `telemetry_config.yml`.

**Prerequisites:**

- `provision.yml` has been executed successfully with
  `service_kube_control_plane_x86_64` and `service_kube_node_x86_64` in the mapping file.
- All nodes are booted and pods are running.

!!! note

    Run the `telemetry.yml` playbook only if iDRAC telemetry is enabled.
    It is not required for other telemetry types.

!!! note

    Service cluster metadata automatically captures the service cluster
    kube control plane virtual IP. As a result, `telemetry.yml` is
    executed against the VIP rather than an individual control plane node.

**Collect telemetry from external nodes (optional):**

You can monitor additional servers (that are not part of this K8s
cluster) via iDRAC telemetry. Ensure their iDRAC BMC ports are reachable
from the K8s worker node and update the BMC IPs in
`/opt/omnia/telemetry/bmc_group_data.csv` inside the omnia_core
container. The `GROUP_NAME` and `PARENT` fields must be left blank.

```text title="Sample bmc_group_data.csv"
BMC_IP,GROUP_NAME,PARENT
10.3.0.101,,
10.3.0.102,,
```

```shell title="Run on omnia_core container"
cd /omnia/telemetry
ansible-playbook telemetry.yml
```


!!! note

    If you want to enable additional telemetry components after the
    first successful deployment (by updating `telemetry_config.yml`),
    and Kubernetes is already up and running, execute the `telemetry.sh`
    script on kube-control-plane at path
    `<K8s_NFS_mount_point>/telemetry/telemetry.sh`.

```shell title="Run on K8s control plane"
# Verify all telemetry pods are running
kubectl get pods -n omnia-telemetry
```


Expected output (all pods `Running` or `Completed`):

```text title="Expected output"
NAME                                     READY   STATUS    RESTARTS   AGE
vmstorage-victoria-cluster-0             1/1     Running   0          5m
vminsert-victoria-cluster-0              1/1     Running   0          5m
vmselect-victoria-cluster-0              1/1     Running   0          5m
vlstorage-victoria-logs-cluster-0        1/1     Running   0          5m
vlinsert-victoria-logs-cluster-0         1/1     Running   0          5m
vlselect-victoria-logs-cluster-0         1/1     Running   0          5m
kafka-0                                  1/1     Running   0          5m
vmagent-5d9f8b7c6-abc12                  1/1     Running   0          5m
idrac-collector-5d9f8b7c6-m3n7q          1/1     Running   0          5m
ldms-aggregator-7f4b9c8d2-p2r4s          1/1     Running   0          5m
ldms-store-8c6d3e9f1-q5t8u               1/1     Running   0          5m
vector-ldms-6b8c4f7d9-xk2p4             1/1     Running   0          5m
vmagent-vector-3a7f9d2e1-r4s6t           1/1     Running   0          5m
```



## Step 10 -- Verify the Telemetry Pipeline


Run a quick sanity check to confirm that all telemetry pods are running:

```shell title="Run on K8s control plane"
kubectl get pods -n telemetry
kubectl get svc -n telemetry
```

All pods should be in `Running` or `Completed` state. All expected services should be listed.

For comprehensive per-source verification (iDRAC, LDMS, PowerScale, UFM, VAST, OME, SFM) including Kafka consumer tests, TLS connectivity checks, and VictoriaMetrics/VictoriaLogs UI queries, see [Verify Telemetry](../HowTo/Telemetry/verify_telemetry.md).


## What's Next?


Your K8s telemetry cluster is operational. Common next steps:

**Monitor additional servers**
   Add BMC IPs of external nodes to `/opt/omnia/telemetry/bmc_group_data.csv`
   and re-run `telemetry.yml`.

**Add Slurm later**
   Follow [Full Deployment](full_deployment.md) (Path B) to add Slurm head, compute,
   and login nodes to this existing deployment. The K8s telemetry cluster
   you built here will seamlessly monitor the Slurm nodes.

**Enable additional telemetry sources**
   Enable DCGM, PowerScale, UFM, or VAST telemetry by setting their
   `metrics_enabled` fields to `true` in `telemetry_config.yml` and
   re-running `telemetry.yml`.

**Enable LDMS on external nodes**
   Install the `ldmsd` agent on any Linux server and point it to the
   LDMS aggregator on the K8s worker to collect OS metrics from machines
   outside the Omnia-managed cluster.

**Configure long-term retention**
   Adjust `retention_period` under `telemetry_sinks > victoria_metrics`
   and `telemetry_sinks > victoria_logs` in `telemetry_config.yml`.
   Increase `persistence_size` and attach persistent storage as needed.

!!! info

    - [Full Deployment](full_deployment.md) -- Add Slurm to this K8s deployment
    - [Prerequisites Checklist](prerequisites_checklist.md) -- Master checklist
    - [Telemetry Architecture](../Overview/telemetry_architecture.md) -- Deep dive into the telemetry pipeline
