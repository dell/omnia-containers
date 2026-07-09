# All Softwares

This page provides a consolidated, filterable view of every software component that Omnia installs across the OIM and cluster nodes. Use the dropdown filters to narrow the table by category, type, license, or installation target.

<style>
.filter-row select {
  padding: 4px 8px;
  border: 1px solid #ccc;
  border-radius: 4px;
  font-size: 0.85rem;
  background: var(--md-default-bg-color, #fff);
  color: var(--md-default-fg-color, #333);
  min-width: 100px;
  max-width: 180px;
}
.filter-row select:focus {
  outline: 2px solid var(--md-accent-fg-color, #448aff);
}
#software-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.85rem;
}
#software-table th,
#software-table td {
  border: 1px solid var(--md-typeset-table-color, #ccc);
  padding: 8px 10px;
  text-align: left;
  vertical-align: top;
}
#software-table thead th {
  background: var(--md-accent-fg-color, #448aff);
  color: #fff;
  position: sticky;
  top: 0;
  z-index: 2;
  font-weight: 600;
}
#software-table tbody tr:nth-child(even) {
  background: var(--md-code-bg-color, #f5f5f5);
}
#software-table tbody tr:hover {
  background: color-mix(in srgb, var(--md-accent-fg-color, #448aff) 12%, transparent);
}
#software-table tbody tr.hidden {
  display: none;
}
.filter-row th {
  background: var(--md-default-bg-color, #fff) !important;
  padding: 6px 10px;
  border-bottom: 2px solid var(--md-accent-fg-color, #448aff);
}
#row-count {
  font-size: 0.85rem;
  margin: 8px 0 0 0;
  color: var(--md-default-fg-color--light, #666);
}
</style>

<table id="software-table">
<thead>
  <tr>
    <th>Component</th>
    <th>Version</th>
    <th>Category</th>
    <th>Type</th>
    <th>License</th>
    <th>Installed On</th>
    <th>Purpose</th>
  </tr>
  <tr class="filter-row">
    <th><select id="filter-component"><option value="">All</option></select></th>
    <th></th>
    <th><select id="filter-category"><option value="">All</option></select></th>
    <th><select id="filter-type"><option value="">All</option></select></th>
    <th><select id="filter-license"><option value="">All</option></select></th>
    <th><select id="filter-installed"><option value="">All</option></select></th>
    <th></th>
  </tr>
</thead>
<tbody>
<!-- OIM -->
<tr><td>Omnia Core</td><td>1.0.0</td><td>OIM</td><td>container</td><td>Apache-2.0</td><td>OIM</td><td>Foundational container for cluster orchestration on the OIM.</td></tr>
<tr><td>OpenCHAMI</td><td>0.5.3</td><td>OIM</td><td>quadlet</td><td>Apache-2.0</td><td>OIM</td><td>Open Composable Heterogeneous Adaptable Management Infrastructure for node discovery and lifecycle management.</td></tr>
<tr><td>SMD (State Manager Daemon)</td><td>2.18.0</td><td>OIM</td><td>quadlet</td><td>MIT</td><td>OIM</td><td>Monitors, tracks, and manages hardware components and node state.</td></tr>
<tr><td>BSS (Boot Script Service)</td><td>1.32.1</td><td>OIM</td><td>quadlet</td><td>MIT</td><td>OIM</td><td>Generates per-node boot scripts and provides Level 2 boot services for PXE/iPXE provisioning.</td></tr>
<tr><td>Image Builder</td><td>0.1.2</td><td>OIM</td><td>quadlet</td><td>MIT</td><td>OIM</td><td>Wrapper around buildah commands for layered image creation.</td></tr>
<tr><td>Magellan</td><td>0.3.1</td><td>OIM</td><td>quadlet</td><td>MIT</td><td>OIM</td><td>Redfish-based BMC discovery tool.</td></tr>
<tr><td>CoreSMD</td><td>0.3.1</td><td>OIM</td><td>quadlet</td><td>MIT</td><td>OIM</td><td>CoreDHCP plugin with a pull-through cache that communicates with SMD.</td></tr>
<tr><td>cloud-init</td><td>24.4</td><td>OIM</td><td>quadlet</td><td>MIT</td><td>OIM</td><td>Micro-service for serving cloud-init payloads during node provisioning.</td></tr>
<tr><td>HAProxy</td><td>3.3-dev2</td><td>OIM</td><td>quadlet</td><td>GPL-2.0-only</td><td>OIM</td><td>Reverse proxy for routing all OpenCHAMI microservices through a single HTTP(S) host.</td></tr>
<tr><td>Step-CA</td><td>0.28.6</td><td>OIM</td><td>quadlet</td><td>Apache-2.0</td><td>OIM</td><td>Zero-trust certificate authority for X.509 certificate management.</td></tr>
<tr><td>Ory Hydra</td><td>2.3.0</td><td>OIM</td><td>quadlet</td><td>Apache-2.0</td><td>OIM</td><td>OpenID Connect and OAuth 2.0 provider for service authentication.</td></tr>
<tr><td>Pulpcore</td><td>3.80.1</td><td>OIM</td><td>container</td><td>GPL-2.0-only</td><td>OIM</td><td>Repository management platform for mirroring RHEL and third-party repos.</td></tr>
<tr><td>pulp-cli</td><td>0.33.0</td><td>OIM</td><td>pip</td><td>GPL-2.0-only</td><td>OIM</td><td>Command-line interface for Pulp REST API operations.</td></tr>
<tr><td>pulp-deb</td><td>3.5.2</td><td>OIM</td><td>pip</td><td>GPL-2.0-only</td><td>OIM</td><td>Pulp plugin for managing Debian/Ubuntu package repositories.</td></tr>
<tr><td>pulp-cli-deb</td><td>0.3.0</td><td>OIM</td><td>pip</td><td>GPL-2.0-only</td><td>OIM</td><td>Pulp CLI extension for Debian repository commands.</td></tr>
<tr><td>pulp-glue</td><td>0.33.0</td><td>OIM</td><td>pip</td><td>GPL-2.0-only</td><td>OIM</td><td>Version-agnostic library for Pulp REST API communication.</td></tr>
<tr><td>pulp-glue-deb</td><td>0.3.0</td><td>OIM</td><td>pip</td><td>GPL-2.0-only</td><td>OIM</td><td>Pulp-glue extension for Debian repository operations.</td></tr>
<tr><td>Fedora CoreOS</td><td>40</td><td>OIM</td><td>image</td><td>MIT</td><td>OIM</td><td>Immutable, container-focused Linux distribution for provisioning base images.</td></tr>
<tr><td>MinIO</td><td>latest</td><td>OIM</td><td>quadlet</td><td>AGPLv3</td><td>OIM</td><td>High-performance S3-compatible object storage for boot images and artifacts.</td></tr>
<tr><td>Docker Registry</td><td>latest</td><td>OIM</td><td>quadlet</td><td>Apache-2.0</td><td>OIM</td><td>OCI image registry service for container image distribution.</td></tr>
<tr><td>PostgreSQL</td><td>16.8</td><td>OIM</td><td>container</td><td>PostgreSQL</td><td>OIM</td><td>Relational database management system used by OIM services.</td></tr>
<!-- Kubernetes -->
<tr><td>Kubernetes Core Components</td><td>1.35.1</td><td>Kubernetes</td><td>rpm, pod</td><td>Apache-2.0</td><td>service_kube_control_plane<br>service_kube_node</td><td>Control plane and node components: kubectl, kubelet, kubeadm, kube-apiserver, kube-controller-manager, kube-scheduler, kube-proxy, and cri-o.</td></tr>
<tr><td>etcd</td><td>3.6.6-0</td><td>Kubernetes</td><td>pod</td><td>Apache-2.0</td><td>service_kube_control_plane</td><td>Distributed key-value store backing the Kubernetes API server.</td></tr>
<tr><td>CoreDNS</td><td>1.13.1</td><td>Kubernetes</td><td>pod</td><td>Apache-2.0</td><td>service_kube_control_plane</td><td>DNS server for Kubernetes service discovery.</td></tr>
<tr><td>Calico</td><td>3.31.4</td><td>Kubernetes</td><td>pod</td><td>Apache-2.0</td><td>service_kube_control_plane</td><td>CNI plugin for pod networking and network policy enforcement.</td></tr>
<tr><td>Flannel</td><td>0.22.0</td><td>Kubernetes</td><td>pod</td><td>Apache-2.0</td><td>service_kube_control_plane</td><td>Network fabric for containers designed for Kubernetes.</td></tr>
<tr><td>Flannel CNI Plugin</td><td>1.1.2</td><td>Kubernetes</td><td>pod</td><td>Apache-2.0</td><td>service_kube_control_plane</td><td>CNI plugin for use in conjunction with Flannel.</td></tr>
<tr><td>Multus</td><td>v4.2.2</td><td>Kubernetes</td><td>pod</td><td>Apache-2.0</td><td>service_kube_control_plane</td><td>CNI meta-plugin for multi-homed pods in Kubernetes.</td></tr>
<tr><td>Whereabouts</td><td>v0.9.2</td><td>Kubernetes</td><td>pod</td><td>Apache-2.0</td><td>service_kube_control_plane</td><td>CNI IPAM plugin that assigns IP addresses cluster-wide.</td></tr>
<tr><td>MetalLB</td><td>v0.15.3</td><td>Kubernetes</td><td>pod</td><td>Apache-2.0</td><td>service_kube_control_plane<br>service_kube_node</td><td>Bare-metal load balancer; assigns external IPs to LoadBalancer services.</td></tr>
<tr><td>kube-vip</td><td>0.8.9</td><td>Kubernetes</td><td>pod</td><td>Apache-2.0</td><td>service_kube_control_plane</td><td>Kubernetes control plane virtual IP and load balancer.</td></tr>
<tr><td>Helm</td><td>3.20.1</td><td>Kubernetes</td><td>tarball</td><td>Apache-2.0</td><td>service_kube_control_plane</td><td>Kubernetes package manager.</td></tr>
<tr><td>containerd</td><td>2.0.5</td><td>Kubernetes</td><td>rpm</td><td>Apache-2.0</td><td>service_k8s</td><td>Open and reliable container runtime.</td></tr>
<tr><td>CRI</td><td>1.35.1</td><td>Kubernetes</td><td>rpm</td><td>Apache-2.0</td><td>service_k8s</td><td>CLI and validation tools for Kubelet Container Runtime Interface.</td></tr>
<tr><td>CNI</td><td>1.4.1</td><td>Kubernetes</td><td>rpm</td><td>Apache-2.0</td><td>service_k8s</td><td>Networking plugins for Linux containers.</td></tr>
<tr><td>runc</td><td>1.2.6</td><td>Kubernetes</td><td>rpm</td><td>Apache-2.0</td><td>service_k8s</td><td>CLI tool for spawning and running containers per OCI specification.</td></tr>
<tr><td>nerdctl</td><td>2.0.5</td><td>Kubernetes</td><td>rpm</td><td>Apache-2.0</td><td>service_k8s</td><td>Docker-compatible CLI for containerd with Compose, Rootless, and eStargz support.</td></tr>
<tr><td>pause</td><td>3.10.1</td><td>Kubernetes</td><td>pod</td><td>Apache-2.0</td><td>service_kube_control_plane</td><td>Kubernetes pause container.</td></tr>
<tr><td>Cluster Proportional Autoscaler</td><td>1.8.8</td><td>Kubernetes</td><td>pod</td><td>Apache-2.0</td><td>service_kube_control_plane</td><td>Kubernetes cluster proportional autoscaler container.</td></tr>
<tr><td>k8s-dns-node-cache</td><td>1.25.0</td><td>Kubernetes</td><td>pod</td><td>Apache-2.0</td><td>service_kube_control_plane</td><td>Kubernetes DNS node-level caching service.</td></tr>
<tr><td>MPI Operator</td><td>0.6.0</td><td>Kubernetes</td><td>pod</td><td>Apache-2.0</td><td>service_k8s</td><td>Kubernetes operator for MPI-based distributed training and HPC applications.</td></tr>
<tr><td>Spark Operator</td><td>v1beta2-1.3.8-3.1.1</td><td>Kubernetes</td><td>pod</td><td>Apache-2.0</td><td>service_k8s</td><td>Kubernetes operator for Apache Spark workloads.</td></tr>
<tr><td>Kubernetes Python Client</td><td>33.1.0</td><td>Kubernetes</td><td>pip</td><td>Apache-2.0</td><td>service_kube_control_plane</td><td>Official Python client library for Kubernetes API.</td></tr>
<tr><td>alpine/kubectl</td><td>1.35.1</td><td>Kubernetes</td><td>pod</td><td>Apache-2.0</td><td>service_kube_control_plane</td><td>Lightweight Alpine-based container image providing kubectl CLI.</td></tr>
<tr><td>NFS Subdir External Provisioner</td><td>4.0.18</td><td>Kubernetes</td><td>helm</td><td>Apache-2.0</td><td>service_kube_control_plane</td><td>Dynamic sub-directory volume provisioner on a remote NFS server.</td></tr>
<tr><td>NFS Subdir External Provisioner (image)</td><td>4.0.2</td><td>Kubernetes</td><td>pod</td><td>Apache-2.0</td><td>service_kube_node</td><td>Container image for the NFS subdir external provisioner.</td></tr>
<tr><td>Prometheus</td><td>v3.4.1</td><td>Kubernetes</td><td>pod</td><td>Apache-2.0</td><td>service_k8s</td><td>Monitoring and alerting toolkit for metrics collection.</td></tr>
<!-- Storage and CSI -->
<tr><td>CSI PowerScale Driver</td><td>v2.17.0</td><td>Storage / CSI</td><td>pod</td><td>Apache-2.0</td><td>csi_driver_powerscale</td><td>CSI driver for Dell PowerScale storage arrays.</td></tr>
<tr><td>Dell Helm Charts</td><td>csi-isilon-2.15.0</td><td>Storage / CSI</td><td>helm</td><td>Apache-2.0</td><td>csi_driver_powerscale</td><td>Helm charts for Dell CSI driver deployment.</td></tr>
<tr><td>CSI Provisioner</td><td>v6.2.0</td><td>Storage / CSI</td><td>pod</td><td>Apache-2.0</td><td>csi_driver_powerscale</td><td>Sidecar that watches PersistentVolumeClaim objects and triggers CreateVolume/DeleteVolume against a CSI endpoint.</td></tr>
<tr><td>CSI Attacher</td><td>v4.11.0</td><td>Storage / CSI</td><td>pod</td><td>Apache-2.0</td><td>csi_driver_powerscale</td><td>Sidecar that watches VolumeAttachment objects and triggers ControllerPublish/Unpublish against a CSI endpoint.</td></tr>
<tr><td>CSI Snapshotter</td><td>v8.5.0</td><td>Storage / CSI</td><td>pod</td><td>Apache-2.0</td><td>csi_driver_powerscale</td><td>Sidecar that watches Snapshot CRD objects and triggers CreateSnapshot/DeleteSnapshot against a CSI endpoint.</td></tr>
<tr><td>CSI Resizer</td><td>v2.1.0</td><td>Storage / CSI</td><td>pod</td><td>Apache-2.0</td><td>csi_driver_powerscale</td><td>Sidecar that watches PersistentVolumeClaims and triggers controller-side expansion against a CSI endpoint.</td></tr>
<tr><td>CSI Node Driver Registrar</td><td>v2.16.0</td><td>Storage / CSI</td><td>pod</td><td>Apache-2.0</td><td>csi_driver_powerscale</td><td>Sidecar that registers a CSI driver with the kubelet plugin registration mechanism.</td></tr>
<tr><td>CSI External Health Monitor Controller</td><td>v0.17.0</td><td>Storage / CSI</td><td>pod</td><td>Apache-2.0</td><td>csi_driver_powerscale</td><td>Sidecar controller for volume health monitoring.</td></tr>
<tr><td>CSI Replicator</td><td>v1.15.0</td><td>Storage / CSI</td><td>pod</td><td>Apache-2.0</td><td>csi_driver_powerscale</td><td>Dell CSM for Replication; extends Kubernetes to support storage array-based disaster recovery.</td></tr>
<tr><td>CSM Metadata Retriever</td><td>v1.14.0</td><td>Storage / CSI</td><td>pod</td><td>Apache-2.0</td><td>csi_driver_powerscale</td><td>Dell CSI metadata retriever controller for cluster metadata via Kube API.</td></tr>
<tr><td>Snapshot Controller</td><td>v8.5.0</td><td>Storage / CSI</td><td>pod</td><td>Apache-2.0</td><td>csi_driver_powerscale</td><td>Manages creation and lifecycle of volume snapshots for CSI drivers.</td></tr>
<!-- Slurm -->
<tr><td>Slurm Workload Manager</td><td>25.05.2</td><td>Slurm</td><td>rpm</td><td>GPL-2.0-only</td><td>slurm_control_node<br>slurm_node<br>login_node<br>login_compiler_node</td><td>HPC workload manager: job scheduling, resource allocation, and accounting.</td></tr>
<tr><td>Munge</td><td>0.5.15</td><td>Slurm</td><td>rpm</td><td>GPL-2.0-only</td><td>slurm_control_node<br>slurm_node<br>login_node<br>login_compiler_node</td><td>Authentication service for creating and validating user credentials across Slurm daemons.</td></tr>
<tr><td>MariaDB</td><td>10.11.11</td><td>Slurm</td><td>rpm</td><td>GPL-2.0-only</td><td>slurm_control_node</td><td>Open-source relational database used by Slurm for job accounting.</td></tr>
<tr><td>MySQL</td><td>9.3</td><td>Slurm</td><td>pod</td><td>MIT</td><td>service_k8s</td><td>Relational database management system (alternative backend for slurmdbd).</td></tr>
<tr><td>python3-PyMySQL</td><td>1.1.2</td><td>Slurm</td><td>pip</td><td>MIT</td><td>slurm_control_node<br>service_kube_control_plane</td><td>Pure-Python MySQL client library for database connectivity.</td></tr>
<tr><td>OpenMPI</td><td>5.0.8</td><td>Slurm</td><td>tarball</td><td>BSD-3-Clause</td><td>openmpi</td><td>Open-source MPI implementation for distributed parallel computing.</td></tr>
<!-- GPU -->
<tr><td>CUDA Toolkit</td><td>13.0.2</td><td>GPU</td><td>rpm</td><td>NVIDIA Software License</td><td>slurm_node<br>service_kube_node</td><td>Development environment for GPU-accelerated applications.</td></tr>
<tr><td>NVIDIA Container Runtime</td><td>3.4.2</td><td>GPU</td><td>rpm</td><td>Apache-2.0</td><td>slurm_node<br>service_kube_node</td><td>Enables GPU access from within containers.</td></tr>
<tr><td>NVIDIA Device Plugin</td><td>0.14.4</td><td>GPU</td><td>pod</td><td>Apache-2.0</td><td>service_k8s</td><td>Kubernetes device plugin for NVIDIA GPU registration.</td></tr>
<tr><td>NCCL</td><td>2.25.1</td><td>GPU</td><td>rpm</td><td>Apache-2.0</td><td>slurm_node</td><td>Optimized primitives for collective multi-GPU communication.</td></tr>
<tr><td>OFED</td><td>24.10-1.1.4.0</td><td>GPU</td><td>rpm</td><td>NVIDIA Software License</td><td>slurm_control_node<br>slurm_node<br>login_node<br>login_compiler_node<br>service_k8s</td><td>OpenFabrics Enterprise Distribution for InfiniBand and RDMA.</td></tr>
<!-- Authentication -->
<tr><td>OpenLDAP</td><td>2.6.9</td><td>Authentication</td><td>container</td><td>GPL-3.0-only</td><td>OIM</td><td>Open-source LDAP directory server for centralized user authentication.</td></tr>
<tr><td>openldap-clients</td><td>2.6.9</td><td>Authentication</td><td>rpm</td><td>OLDAP-2.8</td><td>openldap</td><td>Command-line tools for LDAP directory operations.</td></tr>
<tr><td>389 Directory Server</td><td>2.6.1</td><td>Authentication</td><td>container</td><td>GPL-3.0-or-later</td><td>OIM</td><td>Lightweight Directory Access Protocol server.</td></tr>
<tr><td>FreeIPA</td><td>4.12.2</td><td>Authentication</td><td>container</td><td>GPL-3.0-only</td><td>OIM</td><td>Integrated identity management (alternative to standalone OpenLDAP).</td></tr>
<tr><td>Omnia Auth</td><td>1.0.0</td><td>Authentication</td><td>container</td><td>Apache-2.0</td><td>OIM</td><td>Authentication services container for centralized access control with OpenLDAP integration.</td></tr>
<!-- Telemetry -->
<tr><td>Strimzi Kafka</td><td>0.48.0-kafka-4.1.0</td><td>Telemetry</td><td>pod</td><td>Apache-2.0</td><td>service_k8s</td><td>Apache Kafka running on Kubernetes for telemetry data streaming.</td></tr>
<tr><td>Strimzi Kafka Operator</td><td>0.48.0</td><td>Telemetry</td><td>pod</td><td>Apache-2.0</td><td>service_k8s</td><td>Deploys and manages Apache Kafka clusters on Kubernetes.</td></tr>
<tr><td>Strimzi Kafka Operator Helm Chart</td><td>0.48.1</td><td>Telemetry</td><td>helm</td><td>Apache-2.0</td><td>service_k8s</td><td>Helm chart for deploying the Strimzi Kafka Operator.</td></tr>
<tr><td>Strimzi Kafka Bridge</td><td>0.33.1</td><td>Telemetry</td><td>pod</td><td>Apache-2.0</td><td>service_k8s</td><td>HTTP-based API for Apache Kafka, enabling REST clients to produce and consume messages.</td></tr>
<tr><td>VictoriaMetrics</td><td>1.128.0</td><td>Telemetry</td><td>pod</td><td>Apache-2.0</td><td>service_k8s</td><td>High-performance time-series database for metric storage.</td></tr>
<tr><td>vmagent</td><td>1.128.0</td><td>Telemetry</td><td>pod</td><td>Apache-2.0</td><td>service_k8s</td><td>Lightweight agent for collecting, filtering, and forwarding metrics to VictoriaMetrics.</td></tr>
<tr><td>vmstorage</td><td>1.128.0</td><td>Telemetry</td><td>pod</td><td>Apache-2.0</td><td>service_k8s</td><td>Storage node for VictoriaMetrics cluster mode.</td></tr>
<tr><td>vminsert</td><td>1.128.0</td><td>Telemetry</td><td>pod</td><td>Apache-2.0</td><td>service_k8s</td><td>Ingestion handler for VictoriaMetrics cluster mode.</td></tr>
<tr><td>vmselect</td><td>1.128.0</td><td>Telemetry</td><td>pod</td><td>Apache-2.0</td><td>service_k8s</td><td>Query execution handler for VictoriaMetrics cluster mode.</td></tr>
<tr><td>victoriapump</td><td>1.0.0</td><td>Telemetry</td><td>pod</td><td>Apache-2.0</td><td>service_k8s</td><td>Pushes telemetry metrics from the Omnia pipeline into VictoriaMetrics.</td></tr>
<tr><td>kafkapump</td><td>1.0.0</td><td>Telemetry</td><td>pod</td><td>Apache-2.0</td><td>service_k8s</td><td>Consumes telemetry data from Kafka topics and forwards it to downstream systems.</td></tr>
<tr><td>iDRAC Telemetry Reference Tools</td><td>commit 97ace09</td><td>Telemetry</td><td>git</td><td>Apache-2.0</td><td>OIM</td><td>Collects power, thermal, and health metrics from iDRAC via Redfish.</td></tr>
<tr><td>idrac-telemetry-receiver</td><td>1.0.0</td><td>Telemetry</td><td>pod</td><td>Apache-2.0</td><td>service_k8s</td><td>Collects and streams telemetry data from Dell iDRAC interfaces.</td></tr>
<tr><td>LDMS</td><td>4.5.1</td><td>Telemetry</td><td>rpm</td><td>GPL-2.0</td><td>ldms</td><td>Lightweight Distributed Metric Service for high-speed OS-level metric collection.</td></tr>
<tr><td>NERSC-LDMS</td><td>commit 1f46921</td><td>Telemetry</td><td>helm</td><td>BSD-3-Clause</td><td>service_k8s</td><td>Helm chart, image build, and dashboards for LDMS.</td></tr>
<tr><td>LDMS Aggregator (image)</td><td>1.0.0</td><td>Telemetry</td><td>pod</td><td>Apache-2.0, GPL-2.0</td><td>service_k8s</td><td>Ubuntu-based container with LDMS tools for telemetry and metric collection.</td></tr>
<tr><td>Prometheus</td><td>v3.4.1</td><td>Telemetry</td><td>pod</td><td>Apache-2.0</td><td>service_k8s</td><td>Monitoring and alerting toolkit for metrics collection.</td></tr>
<!-- Container / Runtime -->
<tr><td>Podman</td><td>5.4.0</td><td>Container / Runtime</td><td>rpm</td><td>Apache-2.0</td><td>OIM<br>service_k8s</td><td>Daemonless container runtime used on the OIM and cluster nodes.</td></tr>
<tr><td>containerd</td><td>2.0.5</td><td>Container / Runtime</td><td>rpm</td><td>Apache-2.0</td><td>service_k8s</td><td>Open and reliable container runtime for Kubernetes workloads.</td></tr>
<tr><td>nerdctl</td><td>2.0.5</td><td>Container / Runtime</td><td>rpm</td><td>Apache-2.0</td><td>service_k8s</td><td>Docker-compatible CLI for containerd.</td></tr>
<tr><td>runc</td><td>1.2.6</td><td>Container / Runtime</td><td>rpm</td><td>Apache-2.0</td><td>service_k8s</td><td>CLI tool for spawning and running containers per OCI specification.</td></tr>
<tr><td>BusyBox (base image)</td><td>1.36</td><td>Container / Runtime</td><td>image</td><td>Apache-2.0</td><td>service_k8s</td><td>Minimal UNIX utilities base image for lightweight containers.</td></tr>
<!-- Ansible -->
<tr><td>containers.podman</td><td>1.16.2</td><td>Ansible</td><td>ansible collection</td><td>GPL-3.0-or-later</td><td>omnia_core</td><td>Ansible collection for Podman container management.</td></tr>
<tr><td>community.grafana</td><td>2.1.0</td><td>Ansible</td><td>ansible collection</td><td>GPL-3.0-only</td><td>omnia_core</td><td>Ansible collection for Grafana automation.</td></tr>
<tr><td>community.mysql</td><td>3.10.3</td><td>Ansible</td><td>ansible collection</td><td>GPL-3.0-only</td><td>omnia_core</td><td>Ansible collection for MySQL/MariaDB management.</td></tr>
<tr><td>kubernetes.core</td><td>5.2.0</td><td>Ansible</td><td>ansible collection</td><td>GPL-3.0-only</td><td>omnia_core</td><td>Ansible collection for Kubernetes and OpenShift cluster automation.</td></tr>
<tr><td>community.kubernetes</td><td>2.0.1</td><td>Ansible</td><td>ansible collection</td><td>GPL-3.0-or-later</td><td>omnia_core</td><td>Ansible collection for Kubernetes resources.</td></tr>
<tr><td>ansible-pylibssh</td><td>1.2.3</td><td>Ansible</td><td>pip</td><td>LGPL-2.1-only</td><td>omnia_core</td><td>Python bindings for libssh specific to Ansible.</td></tr>
<tr><td>python3-netaddr</td><td>0.8.0</td><td>Ansible</td><td>pip</td><td>BSD-2-Clause, BSD-3-Clause</td><td>omnia_core</td><td>Network address manipulation library for Python.</td></tr>
<tr><td>libssh</td><td>0.10.6</td><td>Ansible</td><td>rpm</td><td>LGPL-2.1-or-later</td><td>omnia_core</td><td>SSH library for secure remote access.</td></tr>
<tr><td>python3.12</td><td>3.12</td><td>Ansible</td><td>rpm</td><td>PSF</td><td>omnia_core<br>service_kube_control_plane</td><td>Python interpreter and standard library.</td></tr>
<!-- BuildStreaM -->
<tr><td>GitLab</td><td>Latest compatible</td><td>BuildStreaM</td><td>container</td><td>MIT</td><td>OIM</td><td>CI/CD platform for BuildStreaM catalog-driven pipelines.</td></tr>
<tr><td>GitLab Runner</td><td>Latest compatible</td><td>BuildStreaM</td><td>container</td><td>MIT</td><td>OIM</td><td>Executes CI/CD pipeline jobs dispatched by GitLab.</td></tr>
<tr><td>BuildStreaM Catalog</td><td>Bundled with Omnia</td><td>BuildStreaM</td><td>container</td><td>Apache-2.0</td><td>OIM</td><td>Declarative infrastructure catalog consumed by GitLab pipelines.</td></tr>
</tbody>
</table>

<p id="row-count"></p>

<script>
document.addEventListener("DOMContentLoaded", function () {
  const table = document.getElementById("software-table");
  const tbody = table.querySelector("tbody");
  const rows  = Array.from(tbody.querySelectorAll("tr"));

  const filterIds = {
    component: { el: document.getElementById("filter-component"), col: 0 },
    category:  { el: document.getElementById("filter-category"),  col: 2 },
    type:      { el: document.getElementById("filter-type"),       col: 3 },
    license:   { el: document.getElementById("filter-license"),    col: 4 },
    installed: { el: document.getElementById("filter-installed"),  col: 5 }
  };

  function textOf(td) {
    return td ? td.textContent.trim() : "";
  }

  function populateDropdown(select, col) {
    const values = new Set();
    rows.forEach(function (r) {
      const cell = r.cells[col];
      if (cell) {
        var raw = cell.innerHTML;
        raw.split(/<br\s*\/?>/).forEach(function (v) {
          var t = v.replace(/<[^>]*>/g, "").trim();
          if (t) values.add(t);
        });
      }
    });
    Array.from(values).sort(function (a, b) {
      return a.localeCompare(b, undefined, { sensitivity: "base" });
    }).forEach(function (v) {
      var opt = document.createElement("option");
      opt.value = v;
      opt.textContent = v;
      select.appendChild(opt);
    });
  }

  Object.keys(filterIds).forEach(function (key) {
    populateDropdown(filterIds[key].el, filterIds[key].col);
  });

  function applyFilters() {
    var visible = 0;
    rows.forEach(function (row) {
      var show = true;
      Object.keys(filterIds).forEach(function (key) {
        var sel = filterIds[key].el;
        var col = filterIds[key].col;
        var val = sel.value;
        if (val) {
          var cellHTML = row.cells[col] ? row.cells[col].innerHTML : "";
          var parts = cellHTML.split(/<br\s*\/?>/).map(function (p) {
            return p.replace(/<[^>]*>/g, "").trim();
          });
          if (parts.indexOf(val) === -1) {
            show = false;
          }
        }
      });
      if (show) {
        row.classList.remove("hidden");
        visible++;
      } else {
        row.classList.add("hidden");
      }
    });
    document.getElementById("row-count").textContent =
      "Showing " + visible + " of " + rows.length + " components";
  }

  Object.keys(filterIds).forEach(function (key) {
    filterIds[key].el.addEventListener("change", applyFilters);
  });

  applyFilters();
});
</script>

!!! info "Related References"

    - [Installed Software](installed_software.md) -- Category-wise view of installed software.
    - [Software Config](../Configuration/software_config.md) -- How software packages are selected for installation via `software_config.json`.
    - [Local Repo Config](../Configuration/local_repo_config.md) -- Repository mirror configuration for package sources.
