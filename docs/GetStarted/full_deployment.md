# Path B: Full Deployment (Slurm + K8s + Telemetry)


Deploy a production-grade 8-node cluster with Slurm job scheduling, a
highly available Kubernetes service cluster, LDAP/FreeIPA authentication,
and full telemetry. This is the canonical Omnia deployment that exercises
every major subsystem.

**What you will build:**

| Role | Functional Group | Count | Purpose |
| --- | --- | --- | --- |
| OIM (management) | -- | 1 | Runs `omnia_core`; orchestrates the entire deployment. |
| Slurm head node | `slurm_control_node` | 1 | Slurm controller (`slurmctld`), accounting (`slurmdbd`). |
| Compute nodes | `slurm_node` | 1 | Execute HPC jobs via `slurmd`. |
| Login node | `login_node` | 1 | User-facing SSH gateway for `sbatch`/`srun`. |
| K8s control plane | `service_kube_control_plane` | 3 | HA Kubernetes control plane (`kube-apiserver`, `etcd`). |
| K8s worker node | `service_kube_node` | 1 | Runs telemetry stack (Grafana, VictoriaMetrics, Kafka). |

**Estimated time:** ~4 hours.

!!! note

    Complete the [Prerequisites Checklist](prerequisites_checklist.md) before proceeding. Pay
    special attention to the **Service Kubernetes Requirements** section --
    you need 3 control-plane nodes with 64 GB RAM each.

## Step 1 -- Deploy the omnia_core Container


```shell title="Run on OIM (as root)"
cd /opt
git clone https://github.com/dell/omnia.git
cd omnia

# Build container images
bash build_images.sh

# Install the omnia_core container
bash omnia.sh --install

# Verify
systemctl status omnia_core
```


```shell title="Run on OIM (as root)"
# Confirm container access
ssh omnia_core
exit
```



## Step 2 -- Create the Mapping File


This mapping file includes both Slurm and Kubernetes roles across all 7
managed nodes (the OIM is node 8 but is not listed in the mapping).

```shell title="Run on OIM (as root)"
cat > /opt/omnia/input/project_default/mapping.csv << 'EOF'
FUNCTIONAL_GROUP_NAME,GROUP_NAME,SERVICE_TAG,PARENT_SERVICE_TAG,HOSTNAME,ADMIN_MAC,ADMIN_IP,BMC_MAC,BMC_IP
slurm_control_node,slurm,SVCTAG01,,head01,24:6E:96:AA:01:01,10.5.0.101,,10.3.0.101
slurm_node,slurm,SVCTAG02,,compute01,24:6E:96:AA:01:02,10.5.0.102,,10.3.0.102
login_node,slurm,SVCTAG03,,login01,24:6E:96:AA:01:03,10.5.0.103,,10.3.0.103
service_kube_control_plane,kube,SVCTAG04,,kube-cp01,24:6E:96:AA:02:01,10.5.0.201,,10.3.0.201
service_kube_control_plane,kube,SVCTAG05,,kube-cp02,24:6E:96:AA:02:02,10.5.0.202,,10.3.0.202
service_kube_control_plane,kube,SVCTAG06,,kube-cp03,24:6E:96:AA:02:03,10.5.0.203,,10.3.0.203
service_kube_node,kube,SVCTAG07,,kube-wk01,24:6E:96:AA:02:04,10.5.0.204,,10.3.0.204
EOF
```


!!! warning

    Replace **all** placeholder values (`SVCTAG*`, MAC addresses, IPs)
    with your actual hardware values. The 3 `service_kube_control_plane`
    entries are required for Kubernetes HA -- do not reduce to fewer than 3.

!!! tip

    To collect service tags and MAC addresses in bulk, use Omnia's
    `racadm` integration or query iDRAC Redfish endpoints:
    `curl -sk -u root:calvin https://<bmc_ip>/redfish/v1/Systems/System.Embedded.1`

## Step 3 -- Provide Inputs


Copy the template that includes service K8s support.

```shell title="Run on OIM (inside omnia_core container)"
ssh omnia_core

# Copy the full deployment template
cp -r /opt/omnia/examples/input_template/bare_metal_slurm/x86_64/with_service_k8s/* \
    /opt/omnia/input/project_default/

ls -la /opt/omnia/input/project_default/
```


This template includes all the files from Path A plus:

- `ha_config.yml` -- Kubernetes HA virtual IP configuration
- `telemetry_config.yml` -- Telemetry pipeline settings
- `security_config.yml` -- LDAP/FreeIPA authentication settings

Review and edit each file as described in the following steps.


## Step 4 -- Set Credentials


```shell title="Run on OIM (inside omnia_core container)"
cd /opt/omnia
ansible-playbook credentials_utility.yml
```


In addition to the credentials from Path A (provisioning OS, iDRAC,
MariaDB), you will also be prompted for:

- **FreeIPA admin password** -- used for the IPA directory manager.
- **Kubernetes service account credentials** -- for K8s API access.
- **Grafana admin password** -- for the telemetry dashboard.

!!! warning

    The FreeIPA admin password must meet complexity requirements: minimum
    8 characters, at least one uppercase, one lowercase, one digit, and one
    special character.

## Step 5 -- Prepare the OIM


### **5a. Edit** `network_spec.yml`


```shell title="Run on OIM (inside omnia_core container)"
vi /opt/omnia/input/project_default/network_spec.yml
```


```yaml title="Example network_spec.yml for full deployment"
admin_network:
  nic: eno2
  cidr: 10.5.0.0/16
  static_range: 10.5.0.100-10.5.0.250
  gateway: 10.5.0.1

bmc_network:
  nic: eno2
  cidr: 10.3.0.0/16
  static_range: 10.3.0.100-10.3.0.250
```


!!! tip

    Expand your `static_range` to accommodate both Slurm and K8s nodes.
    In this deployment, you need at least 7 admin IPs and 7 BMC IPs.

### **5b. Edit** `provision_config.yml`


```shell title="Run on OIM (inside omnia_core container)"
vi /opt/omnia/input/project_default/provision_config.yml
```


```yaml title="Example provision_config.yml excerpt"
iso_path: /opt/isos/RHEL-8.8-x86_64-dvd.iso
timezone: America/Chicago
domain_name: omnia.local
```


### **5c. Edit** `ha_config.yml` **(K8s HA)**


This file configures the floating virtual IP (VIP) used by `kube-vip`
to provide HA access to the Kubernetes API server.

```shell title="Run on OIM (inside omnia_core container)"
vi /opt/omnia/input/project_default/ha_config.yml
```


```yaml title="Example ha_config.yml"
# Virtual IP for the Kubernetes API server (must be unused on admin network)
k8s_vip: 10.5.0.250

# Interface on K8s control plane nodes facing the admin network
k8s_vip_interface: eno2
```


!!! warning

    The `k8s_vip` must be an IP address on the admin subnet that is
    **not** assigned to any node in `mapping.csv` or used by any other
    device. `kube-vip` floats this IP across the 3 control-plane nodes.

### **5d. Run** `prepare_oim.yml`


```shell title="Run on OIM (inside omnia_core container)"
cd /opt/omnia
ansible-playbook prepare_oim.yml -i /opt/omnia/input/project_default/mapping.csv
```



## Step 6 -- Verify OIM Services


```shell title="Run on OIM (inside omnia_core container)"
systemctl list-dependencies omnia.target

# Quick check
for svc in dhcpd tftp.socket httpd nfs-server; do
    echo -n "$svc: "; systemctl is-active $svc
done
```



## Step 7 -- Set Up Authentication


Configure LDAP or FreeIPA for centralized user management across the
entire cluster.

### **7a. Edit** `security_config.yml`


```shell title="Run on OIM (inside omnia_core container)"
vi /opt/omnia/input/project_default/security_config.yml
```


```yaml title="Example security_config.yml excerpt"
# Authentication method: 'freeipa' or 'ldap'
auth_type: freeipa

# FreeIPA realm (uppercase, typically your domain)
realm: OMNIA.LOCAL

# FreeIPA domain
directory_domain: omnia.local

# Admin username for the IPA server
admin_user: admin
```


!!! tip

    FreeIPA is recommended for new deployments because it bundles Kerberos,
    LDAP, DNS, and certificate authority into a single solution. Use
    `ldap` only if you are integrating with an existing Active Directory
    or OpenLDAP server.

### **7b. Run** `auth.yml`


```shell title="Run on OIM (inside omnia_core container)"
cd /opt/omnia
ansible-playbook auth.yml
```


This playbook:

- Installs FreeIPA server on the OIM (or connects to an external LDAP).
- Enrolls all cluster nodes as FreeIPA clients.
- Configures SSH key distribution and Kerberos authentication.
- Creates initial user accounts if specified in `security_config.yml`.


## Step 8 -- Configure Telemetry


### **8a. Edit** `telemetry_config.yml`


```shell title="Run on OIM (inside omnia_core container)"
vi /opt/omnia/input/project_default/telemetry_config.yml
```


```yaml title="Example telemetry_config.yml excerpt"
# Enable iDRAC telemetry collection
idrac_telemetry: true

# Enable LDMS (Lightweight Distributed Metric Service) on compute nodes
ldms_telemetry: true

# Grafana dashboard access port
grafana_port: 3000

# VictoriaMetrics retention period
victoriametrics_retention: 30d

# Kafka message broker settings (deployed on K8s worker)
kafka_enabled: true
```


!!! tip

    If you only need basic iDRAC hardware metrics (temperatures, fan
    speeds, power draw), set `ldms_telemetry: false` to skip OS-level
    metric collection. This reduces agent overhead on compute nodes.

**8b. Telemetry will be deployed in Step 14** after the cluster is
provisioned and K8s is running. Continue with the next step.


## Step 9 -- Create Local Repositories


```shell title="Run on OIM (inside omnia_core container)"
cd /opt/omnia
ansible-playbook local_repo.yml
```


!!! warning

    This step now mirrors additional packages for Kubernetes (`kubeadm`,
    `kubelet`, container runtime) and telemetry (Grafana, VictoriaMetrics,
    Kafka). Expect 45--90 minutes and ~30 GB of downloaded content.

## Step 10 -- Set Up Service Kubernetes Cluster


Deploy the 3-node HA Kubernetes cluster that will host telemetry services,
monitoring dashboards, and other infrastructure workloads.

```shell title="Run on OIM (inside omnia_core container)"
cd /opt/omnia
ansible-playbook k8s.yml
```


`k8s.yml` orchestrates:

- `kubeadm init` on the first control-plane node (`kube-cp01`).
- `kubeadm join` for the remaining control-plane nodes (`kube-cp02`,
  `kube-cp03`) with `--control-plane` flag.
- `kubeadm join` for the worker node (`kube-wk01`).
- `kube-vip` deployment for API server HA using the VIP from
  `ha_config.yml`.
- Calico CNI installation for pod networking.
- MetalLB setup for `LoadBalancer` service type support.

```shell title="Run on OIM (inside omnia_core container)"
# Verify K8s cluster from OIM (kubeconfig is auto-copied)
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


!!! tip

    If a control-plane node shows `NotReady`, SSH to it and check
    `journalctl -u kubelet`. Common causes: incorrect `k8s_vip`
    in `ha_config.yml` or the Calico CNI pods failing to start.

## Step 11 -- Build Node Images


```shell title="Run on OIM (inside omnia_core container)"
cd /opt/omnia
ansible-playbook build_image_x86_64.yml

# Verify
s3cmd ls s3://omnia-images/
```



## Step 12 -- Discover and Provision Nodes


```shell title="Run on OIM (inside omnia_core container)"
cd /opt/omnia
ansible-playbook discovery.yml
```


!!! warning

    With 7 nodes, discovery takes longer than Path A. Allow **30--60
    minutes**. Nodes are provisioned in parallel when possible, but the
    OIM's DHCP and HTTP services can bottleneck with many simultaneous PXE
    requests.

```shell title="Run on OIM (inside omnia_core container)"
# Verify all nodes are reachable
ansible all -m ping -i /opt/omnia/inventories/project_default/inventory
```



## Step 13 -- Deploy Slurm


```shell title="Run on OIM (inside omnia_core container)"
cd /opt/omnia
ansible-playbook omnia.yml
```


This deploys the Slurm stack on the head, compute, and login nodes
(same as Path A, Step 10). It also configures NFS mounts and integrates
the FreeIPA/LDAP authentication set up in Step 7.

```shell title="Run on head node (head01)"
# Verify Slurm
ssh head01
sinfo
srun -N 1 hostname
```



## Step 14 -- Initialize Telemetry


With both the K8s service cluster and Slurm cluster running, deploy the
telemetry pipeline.

```shell title="Run on OIM (inside omnia_core container)"
cd /opt/omnia
ansible-playbook telemetry.yml
```


`telemetry.yml` deploys:

- **iDRAC telemetry collector** -- Polls iDRAC Redfish endpoints for
  hardware metrics (temperatures, power, fan speeds, storage health).
- **LDMS (Lightweight Distributed Metric Service)** -- Collects OS-level
  metrics (CPU, memory, network, GPU utilization) from compute nodes.
- **Kafka** -- Message broker that ingests metrics from collectors.
- **VictoriaMetrics** -- Time-series database for long-term metric storage.
- **Grafana** -- Visualization dashboards pre-configured with Omnia panels.

All telemetry components are deployed as Kubernetes pods on the service
cluster (`kube-wk01`).

```shell title="Run on OIM (inside omnia_core container)"
# Verify telemetry pods
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



## Step 15 -- Verify the Full Deployment


**Slurm verification:**

```shell title="Run on head node (head01)"
sinfo
srun -N 1 hostname
sacctmgr show cluster
```


**Kubernetes verification:**

```shell title="Run on OIM (inside omnia_core container)"
export KUBECONFIG=/opt/omnia/k8s/admin.conf
kubectl get nodes
kubectl get pods --all-namespaces | grep -v Running | grep -v Completed
```


Any pods not in `Running` or `Completed` state need investigation.

**Telemetry verification:**

```shell title="Run on OIM (inside omnia_core container)"
# Get the Grafana service URL
kubectl get svc -n omnia-telemetry grafana
```


Open `http://<kube-vip>:3000` in a browser. Log in with the Grafana
admin credentials set in Step 4. You should see pre-built dashboards for:

- **Cluster Overview** -- Node health, job counts, utilization summary.
- **iDRAC Hardware** -- Per-server temperatures, power, fan speeds.
- **Compute Metrics** -- CPU, memory, network, and GPU utilization.

!!! tip

    If Grafana shows "No Data" on dashboards, verify that the iDRAC
    collector pod is running and that iDRAC Redfish endpoints are
    reachable from the K8s worker node:
    `curl -sk -u root:calvin https://10.3.0.101/redfish/v1/`

**Authentication verification:**

```shell title="Run on any cluster node"
# Verify FreeIPA enrollment
ipa user-find --all

# Verify Kerberos
kinit admin
klist
```



## What's Next?


Your production cluster is fully operational with scheduling, monitoring,
and authentication. Consider these enhancements:

**Scale out compute nodes**
   Add more `slurm_node` entries to `mapping.csv`, re-run
   `discovery.yml`, then `omnia.yml`.

**Add GPU support**
   Edit `software_config.json` to include NVIDIA drivers and CUDA
   toolkit, then re-run `omnia.yml` on GPU-equipped nodes.

**Configure job accounting and fairshare**
   Edit `omnia_config.yml` to enable Slurm fairshare scheduling and
   detailed job accounting with `sacctmgr`.

**Set up alerts**
   Configure Grafana alerting rules to send notifications (email, Slack,
   PagerDuty) when hardware metrics exceed thresholds.

**Enable BuildStreaM for GitOps**
   See [Buildstream Deployment](buildstream_deployment.md) (Path D) to layer CI/CD automation
   on top of this deployment.

!!! info

    - [Slurm Quickstart](slurm_quickstart.md) -- Simplified 4-node Slurm deployment
    - [K8S Telemetry Only](k8s_telemetry_only.md) -- Telemetry without Slurm
    - [Prerequisites Checklist](prerequisites_checklist.md) -- Master checklist
