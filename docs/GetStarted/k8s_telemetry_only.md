# Path C: Kubernetes + Telemetry Only


Deploy a 5-node Kubernetes service cluster with the full Omnia telemetry
pipeline -- without Slurm. Use this path when your goal is infrastructure
monitoring via iDRAC metrics, OS-level telemetry, and Grafana dashboards,
with no HPC job scheduler required.

**What you will build:**

| Role | Functional Group | Count | Purpose |
| --- | --- | --- | --- |
| OIM (management) | -- | 1 | Runs `omnia_core`; orchestrates the deployment. |
| K8s control plane | `service_kube_control_plane` | 3 | HA Kubernetes control plane (`kube-apiserver`, `etcd`, `kube-scheduler`, `kube-controller-manager`). |
| K8s worker node | `service_kube_node` | 1 | Runs the telemetry stack: iDRAC collector, LDMS aggregator, Kafka, VictoriaMetrics, and Grafana. |

**Telemetry pipeline architecture:**

```text title="Telemetry pipeline architecture"
iDRAC (Redfish) ──┐
                  ├──> Kafka ──> VictoriaMetrics ──> Grafana
LDMS (OS-level) ──┘
```


- **iDRAC collector** polls each server's Redfish endpoint for hardware
  metrics (temperatures, power consumption, fan speeds, storage health).
- **LDMS** (Lightweight Distributed Metric Service) collects OS-level
  metrics (CPU, memory, network I/O, GPU utilization) from monitored nodes.
- **Kafka** acts as the message broker, decoupling collectors from storage.
- **VictoriaMetrics** provides high-performance time-series storage with
  configurable retention.
- **Grafana** delivers pre-built dashboards with drill-down views.

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
cat > /opt/omnia/input/project_default/mapping.csv << 'EOF'
FUNCTIONAL_GROUP_NAME,GROUP_NAME,SERVICE_TAG,PARENT_SERVICE_TAG,HOSTNAME,ADMIN_MAC,ADMIN_IP,BMC_MAC,BMC_IP
service_kube_control_plane,kube,SVCTAG01,,kube-cp01,24:6E:96:BB:01:01,10.5.0.201,,10.3.0.201
service_kube_control_plane,kube,SVCTAG02,,kube-cp02,24:6E:96:BB:01:02,10.5.0.202,,10.3.0.202
service_kube_control_plane,kube,SVCTAG03,,kube-cp03,24:6E:96:BB:01:03,10.5.0.203,,10.3.0.203
service_kube_node,kube,SVCTAG04,,kube-wk01,24:6E:96:BB:02:01,10.5.0.204,,10.3.0.204
EOF
```


!!! warning

    Replace **all** placeholder values with your actual hardware data.
    The 3 `service_kube_control_plane` entries are mandatory for
    Kubernetes HA -- do not reduce below 3.

!!! tip

    You can monitor additional servers (that are not part of this K8s
    cluster) via iDRAC telemetry. Simply ensure their iDRAC BMC ports are
    reachable from the K8s worker node and add their BMC IPs to
    `telemetry_config.yml` later in Step 7.

## Step 3 -- Provide Inputs


Since this deployment has no Slurm, use the `with_service_k8s` template
and remove any Slurm-specific settings.

```shell title="Run on OIM (inside omnia_core container)"
ssh omnia_core

# Copy the template with K8s support
cp -r /opt/omnia/examples/input_template/bare_metal_slurm/x86_64/with_service_k8s/* \
    /opt/omnia/input/project_default/

ls -la /opt/omnia/input/project_default/
```


Key files for this deployment:

- `network_spec.yml` -- Network CIDRs and interfaces
- `provision_config.yml` -- OS provisioning settings
- `ha_config.yml` -- Kubernetes HA virtual IP
- `telemetry_config.yml` -- Telemetry pipeline configuration
- `software_config.json` -- Software stack (K8s components)
- `local_repo_config.yml` -- Repository mirror settings

!!! tip

    You can safely ignore `omnia_config.yml` for this path since Slurm
    will not be deployed. However, do not delete it -- Omnia expects the
    file to exist even if its values are unused.

## Step 4 -- Set Credentials


```shell title="Run on OIM (inside omnia_core container)"
cd /opt/omnia
ansible-playbook credentials_utility.yml
```


You will be prompted for:

- **Provisioning OS password** -- root password for provisioned K8s nodes.
- **iDRAC credentials** -- for Redfish access during discovery and
  telemetry collection.
- **Grafana admin password** -- for the telemetry visualization dashboard.


## Step 5 -- Prepare the OIM


### **5a. Edit** `network_spec.yml`


```shell title="Run on OIM (inside omnia_core container)"
vi /opt/omnia/input/project_default/network_spec.yml
```


```yaml title="Example network_spec.yml"
admin_network:
  nic: eno2
  cidr: 10.5.0.0/16
  static_range: 10.5.0.200-10.5.0.250
  gateway: 10.5.0.1

bmc_network:
  nic: eno2
  cidr: 10.3.0.0/16
  static_range: 10.3.0.200-10.3.0.250
```


### **5b. Edit** `provision_config.yml`


```shell title="Run on OIM (inside omnia_core container)"
vi /opt/omnia/input/project_default/provision_config.yml
```


```yaml title="Example provision_config.yml"
iso_path: /opt/isos/RHEL-8.8-x86_64-dvd.iso
timezone: America/Chicago
domain_name: omnia.local
```


### **5c. Edit** `ha_config.yml`


```shell title="Run on OIM (inside omnia_core container)"
vi /opt/omnia/input/project_default/ha_config.yml
```


```yaml title="Example ha_config.yml"
# Virtual IP for K8s API HA -- must be unused on the admin network
k8s_vip: 10.5.0.250
k8s_vip_interface: eno2
```


!!! warning

    The `k8s_vip` must not conflict with any IP in `mapping.csv` or in
    the `static_range`. Reserve it explicitly.

### **5d. Run** `prepare_oim.yml`


```shell title="Run on OIM (inside omnia_core container)"
cd /opt/omnia
ansible-playbook prepare_oim.yml -i /opt/omnia/input/project_default/mapping.csv
```



## Step 6 -- Verify OIM Services


```shell title="Run on OIM (inside omnia_core container)"
systemctl list-dependencies omnia.target

for svc in dhcpd tftp.socket httpd nfs-server; do
    echo -n "$svc: "; systemctl is-active $svc
done
```


All services must show `active`.


## Step 7 -- Configure Telemetry


Edit the telemetry configuration before creating local repos and deploying
the cluster, so that all required telemetry packages are included in the
local repository sync.

```shell title="Run on OIM (inside omnia_core container)"
vi /opt/omnia/input/project_default/telemetry_config.yml
```


```yaml title="Example telemetry_config.yml"
# Enable iDRAC hardware telemetry via Redfish
idrac_telemetry: true

# Enable LDMS OS-level metric collection
# Set to true if you want CPU/memory/GPU metrics from monitored nodes
ldms_telemetry: true

# Grafana settings
grafana_port: 3000

# VictoriaMetrics time-series database
victoriametrics_retention: 30d

# Kafka message broker
kafka_enabled: true

# List of additional iDRAC BMC IPs to monitor (beyond nodes in mapping.csv)
# Uncomment and add IPs to monitor servers not managed by this Omnia deployment
# additional_idrac_targets:
#   - 10.3.0.50
#   - 10.3.0.51
#   - 10.3.0.52
```


!!! tip

    The `additional_idrac_targets` field lets you monitor servers that
    are not part of this Omnia deployment. This is useful for monitoring
    existing clusters or standalone servers through the same Grafana
    instance.

## Step 8 -- Create Local Repositories


```shell title="Run on OIM (inside omnia_core container)"
cd /opt/omnia
ansible-playbook local_repo.yml
```


!!! warning

    This step downloads Kubernetes packages, container images for the
    telemetry stack (Grafana, VictoriaMetrics, Kafka), and base OS
    packages. Allow **30--60 minutes** and ~20 GB disk space.

## Step 9 -- Build Node Images


```shell title="Run on OIM (inside omnia_core container)"
cd /opt/omnia
ansible-playbook build_image_x86_64.yml

# Verify the image was created
s3cmd ls s3://omnia-images/
```



## Step 10 -- Discover and Provision Nodes


Power on your 4 target nodes with PXE boot priority, then run discovery.

```shell title="Run on OIM (inside omnia_core container)"
cd /opt/omnia
ansible-playbook discovery.yml
```


```shell title="Run on OIM (inside omnia_core container)"
# Verify all 4 nodes are reachable
ansible all -m ping -i /opt/omnia/inventories/project_default/inventory
```


Expected: all 4 nodes return `pong`.


## Step 11 -- Deploy Service Kubernetes Cluster


```shell title="Run on OIM (inside omnia_core container)"
cd /opt/omnia
ansible-playbook k8s.yml
```


This playbook:

- Initializes the Kubernetes cluster on `kube-cp01`.
- Joins `kube-cp02` and `kube-cp03` as additional control-plane nodes.
- Joins `kube-wk01` as the worker node.
- Deploys `kube-vip` for API server HA.
- Installs Calico CNI and MetalLB.

```shell title="Run on OIM (inside omnia_core container)"
# Verify the K8s cluster
export KUBECONFIG=/opt/omnia/k8s/admin.conf
kubectl get nodes
```


Expected output (all nodes `Ready`):

```text title="Expected output"
NAME        STATUS   ROLES           AGE   VERSION
kube-cp01   Ready    control-plane   10m   v1.28.x
kube-cp02   Ready    control-plane   8m    v1.28.x
kube-cp03   Ready    control-plane   8m    v1.28.x
kube-wk01   Ready    <none>          6m    v1.28.x
```


```shell title="Run on OIM (inside omnia_core container)"
# Verify all system pods are healthy
kubectl get pods -n kube-system
```


All pods should be `Running` or `Completed`.

!!! tip

    If `kube-vip` pods are in `CrashLoopBackOff`, verify that the
    `k8s_vip` in `ha_config.yml` is not in use by another device.
    Run `arping -D -I eno2 10.5.0.250` from the OIM to check for
    conflicts.

## Step 12 -- Deploy Telemetry


With the K8s cluster operational, deploy the full telemetry pipeline.

```shell title="Run on OIM (inside omnia_core container)"
cd /opt/omnia
ansible-playbook telemetry.yml
```


`telemetry.yml` deploys these components as Kubernetes workloads:

| Component | K8s Resource | Function |
| --- | --- | --- |
| iDRAC collector | Deployment | Polls iDRAC Redfish APIs on all BMC IPs for hardware telemetry (temperatures, power draw, fan RPM, storage health, memory errors). |
| LDMS aggregator | Deployment | Receives OS-level metrics from `ldmsd` daemons running on monitored nodes. Forwards to Kafka. |
| Kafka | StatefulSet | Message broker that buffers and routes metrics from collectors to VictoriaMetrics. |
| VictoriaMetrics | StatefulSet | Time-series database optimized for high-throughput metric ingestion. Data retained per `victoriametrics_retention` setting. |
| Grafana | Deployment | Visualization and dashboarding. Ships with pre-built Omnia dashboards for hardware and OS metrics. |

```shell title="Run on OIM (inside omnia_core container)"
# Verify all telemetry pods are running
export KUBECONFIG=/opt/omnia/k8s/admin.conf
kubectl get pods -n omnia-telemetry
```


Expected output (all pods `Running` or `Completed`):

```text title="Expected output"
NAME                                  READY   STATUS    RESTARTS   AGE
grafana-6b8c4f7d9-xk2p4              1/1     Running   0          5m
victoriametrics-0                     1/1     Running   0          5m
kafka-0                               1/1     Running   0          5m
idrac-collector-5d9f8b7c6-m3n7q      1/1     Running   0          5m
ldms-aggregator-7f4b9c8d2-p2r4s      1/1     Running   0          5m
```


```shell title="Run on OIM (inside omnia_core container)"
# Get the Grafana service endpoint
kubectl get svc -n omnia-telemetry grafana
```



## Step 13 -- Verify the Telemetry Pipeline


**13a. Access Grafana**

Open a browser and navigate to `http://<k8s_vip>:3000` (e.g.,
`http://10.5.0.250:3000`). Log in with:

- **Username:** `admin`
- **Password:** The Grafana password you set in Step 4.

You should see pre-built dashboards in the **Omnia** folder:

- **Cluster Overview** -- Summary of all monitored nodes.
- **iDRAC Hardware Metrics** -- Per-server temperature, power, fans.
- **System Metrics** -- CPU, memory, disk, and network utilization.

**13b. Verify data flow**

```shell title="Run on OIM (inside omnia_core container)"
export KUBECONFIG=/opt/omnia/k8s/admin.conf

# Check Kafka topics are receiving data
kubectl exec -n omnia-telemetry kafka-0 -- \
    kafka-topics.sh --list --bootstrap-server localhost:9092

# Check VictoriaMetrics has ingested metrics
curl -s "http://10.5.0.250:8428/api/v1/query?query=up" | python3 -m json.tool
```


!!! tip

    If Grafana dashboards show "No Data":

    1. Verify the iDRAC collector pod logs:
       `kubectl logs -n omnia-telemetry deployment/idrac-collector`
    2. Confirm iDRAC Redfish is reachable from the K8s worker:
       `kubectl exec -n omnia-telemetry deployment/idrac-collector -- curl -sk https://10.3.0.201/redfish/v1/`
    3. Check that the iDRAC **Datacenter** license is installed (Enterprise
       is not sufficient for streaming telemetry).

**13c. Verify iDRAC metrics specifically**

```shell title="Run on OIM (inside omnia_core container)"
# Query VictoriaMetrics for iDRAC temperature metrics
curl -s "http://10.5.0.250:8428/api/v1/query?query=idrac_inlet_temperature" \
    | python3 -m json.tool
```


You should see metric results with labels identifying each server by
service tag and BMC IP.

**13d. Test alerting (optional)**

In Grafana, navigate to **Alerting > Alert Rules** to see the default
Omnia alert rules (high temperature, disk failure, power anomaly). You can
configure notification channels (email, Slack, PagerDuty) under
**Alerting > Contact Points**.


## What's Next?


Your K8s telemetry cluster is operational. Common next steps:

**Monitor additional servers**
   Add more BMC IPs to `additional_idrac_targets` in
   `telemetry_config.yml` and re-run `telemetry.yml`.

**Add Slurm later**
   Follow [Full Deployment](full_deployment.md) (Path B) to add Slurm head, compute,
   and login nodes to this existing deployment. The K8s telemetry cluster
   you built here will seamlessly monitor the Slurm nodes.

**Create custom Grafana dashboards**
   Use VictoriaMetrics as a Prometheus-compatible data source to build
   dashboards tailored to your monitoring needs.

**Enable LDMS on external nodes**
   Install the `ldmsd` agent on any Linux server and point it to the
   LDMS aggregator on the K8s worker to collect OS metrics from machines
   outside the Omnia-managed cluster.

**Configure long-term retention**
   Increase `victoriametrics_retention` in `telemetry_config.yml` and
   attach persistent storage (NFS PV or local SSD) to the VictoriaMetrics
   StatefulSet.

!!! info

    - [Full Deployment](full_deployment.md) -- Add Slurm to this K8s deployment
    - [Prerequisites Checklist](prerequisites_checklist.md) -- Master checklist
    - [Telemetry Architecture](../Overview/telemetry_architecture.md) -- Deep dive into the telemetry pipeline
