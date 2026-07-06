# Installed Software

This page lists all software components that Omnia installs and configures across the OIM and cluster nodes. Versions are pinned to those validated with this release.

## OIM (Management Node) software

| Component | Version | Type | License | Installed On | Purpose |
| --- | --- | --- | --- | --- | --- |
| Omnia Core | 1.0.0 | container | Apache-2.0 | OIM | Foundational container for cluster orchestration on the OIM. |
| OpenCHAMI | 0.5.3 | quadlet | Apache-2.0 | OIM | Open Composable Heterogeneous Adaptable Management Infrastructure for node discovery and lifecycle management. |
| SMD (State Manager Daemon) | 2.18.0 | quadlet | MIT | OIM | Monitors, tracks, and manages hardware components and node state. |
| BSS (Boot Script Service) | 1.32.1 | quadlet | MIT | OIM | Generates per-node boot scripts and provides Level 2 boot services for PXE/iPXE provisioning. |
| Image Builder | 0.1.2 | quadlet | MIT | OIM | Wrapper around buildah commands for layered image creation. |
| Magellan | 0.3.1 | quadlet | MIT | OIM | Redfish-based BMC discovery tool. |
| CoreSMD | 0.3.1 | quadlet | MIT | OIM | CoreDHCP plugin with a pull-through cache that communicates with SMD. |
| cloud-init | 24.4 | quadlet | MIT | OIM | Micro-service for serving cloud-init payloads during node provisioning. |
| HAProxy | 3.3-dev2 | quadlet | GPL-2.0-only | OIM | Reverse proxy for routing all OpenCHAMI microservices through a single HTTP(S) host. |
| Step-CA | 0.28.6 | quadlet | Apache-2.0 | OIM | Zero-trust certificate authority for X.509 certificate management. |
| Ory Hydra | 2.3.0 | quadlet | Apache-2.0 | OIM | OpenID Connect and OAuth 2.0 provider for service authentication. |
| Pulpcore | 3.80.1 | container | GPL-2.0-only | OIM | Repository management platform for mirroring RHEL and third-party repos. |
| pulp-cli | 0.33.0 | pip | GPL-2.0-only | OIM | Command-line interface for Pulp REST API operations. |
| pulp-deb | 3.5.2 | pip | GPL-2.0-only | OIM | Pulp plugin for managing Debian/Ubuntu package repositories. |
| pulp-cli-deb | 0.3.0 | pip | GPL-2.0-only | OIM | Pulp CLI extension for Debian repository commands. |
| pulp-glue | 0.33.0 | pip | GPL-2.0-only | OIM | Version-agnostic library for Pulp REST API communication. |
| pulp-glue-deb | 0.3.0 | pip | GPL-2.0-only | OIM | Pulp-glue extension for Debian repository operations. |
| Fedora CoreOS | 40 | image | MIT | OIM | Immutable, container-focused Linux distribution for provisioning base images. |
| MinIO | latest | quadlet | AGPLv3 | OIM | High-performance S3-compatible object storage for boot images and artifacts. |
| Docker Registry | latest | quadlet | Apache-2.0 | OIM | OCI image registry service for container image distribution. |
| PostgreSQL | 16.8 | container | PostgreSQL | OIM | Relational database management system used by OIM services. |

## Kubernetes cluster software

| Component | Version | Type | License | Installed On | Purpose |
| --- | --- | --- | --- | --- | --- |
| Kubernetes Core Components | 1.35.1 | rpm, pod | Apache-2.0 | service_kube_control_plane, service_kube_node | Control plane and node components: `kubectl`, `kubelet`, `kubeadm`, `kube-apiserver`, `kube-controller-manager`, `kube-scheduler`, `kube-proxy`, and `cri-o`. |
| etcd | 3.6.6-0 | pod | Apache-2.0 | service_kube_control_plane | Distributed key-value store backing the Kubernetes API server. |
| CoreDNS | 1.13.1 | pod | Apache-2.0 | service_kube_control_plane | DNS server for Kubernetes service discovery. |
| Calico | 3.31.4 | pod | Apache-2.0 | service_kube_control_plane | CNI plugin for pod networking and network policy enforcement. |
| Flannel | 0.22.0 | pod | Apache-2.0 | service_kube_control_plane | Network fabric for containers designed for Kubernetes. |
| Flannel CNI Plugin | 1.1.2 | pod | Apache-2.0 | service_kube_control_plane | CNI plugin for use in conjunction with Flannel. |
| Multus | v4.2.2 | pod | Apache-2.0 | service_kube_control_plane | CNI meta-plugin for multi-homed pods in Kubernetes. |
| Whereabouts | v0.9.2 | pod | Apache-2.0 | service_kube_control_plane | CNI IPAM plugin that assigns IP addresses cluster-wide. |
| MetalLB | v0.15.3 | pod | Apache-2.0 | service_kube_control_plane, service_kube_node | Bare-metal load balancer; assigns external IPs to `LoadBalancer` services. |
| kube-vip | 0.8.9 | pod | Apache-2.0 | service_kube_control_plane | Kubernetes control plane virtual IP and load balancer. |
| Helm | 3.20.1 | tarball | Apache-2.0 | service_kube_control_plane | Kubernetes package manager. |
| containerd | 2.0.5 | rpm | Apache-2.0 | service_k8s | Open and reliable container runtime. |
| CRI | 1.35.1 | rpm | Apache-2.0 | service_k8s | CLI and validation tools for Kubelet Container Runtime Interface. |
| CNI | 1.4.1 | rpm | Apache-2.0 | service_k8s | Networking plugins for Linux containers. |
| runc | 1.2.6 | rpm | Apache-2.0 | service_k8s | CLI tool for spawning and running containers per OCI specification. |
| nerdctl | 2.0.5 | rpm | Apache-2.0 | service_k8s | Docker-compatible CLI for containerd with Compose, Rootless, and eStargz support. |
| pause | 3.10.1 | pod | Apache-2.0 | service_kube_control_plane | Kubernetes pause container. |
| Cluster Proportional Autoscaler | 1.8.8 | pod | Apache-2.0 | service_kube_control_plane | Kubernetes cluster proportional autoscaler container. |
| k8s-dns-node-cache | 1.25.0 | pod | Apache-2.0 | service_kube_control_plane | Kubernetes DNS node-level caching service. |
| MPI Operator | 0.6.0 | pod | Apache-2.0 | service_k8s | Kubernetes operator for MPI-based distributed training and HPC applications. |
| Spark Operator | v1beta2-1.3.8-3.1.1 | pod | Apache-2.0 | service_k8s | Kubernetes operator for Apache Spark workloads. |
| Kubernetes Python Client | 33.1.0 | pip | Apache-2.0 | service_kube_control_plane | Official Python client library for Kubernetes API. |
| alpine/kubectl | 1.35.1 | pod | Apache-2.0 | service_kube_control_plane | Lightweight Alpine-based container image providing `kubectl` CLI. |
| NFS Subdir External Provisioner | 4.0.18 | helm | Apache-2.0 | service_kube_control_plane | Dynamic sub-directory volume provisioner on a remote NFS server. |
| NFS Subdir External Provisioner (image) | 4.0.2 | pod | Apache-2.0 | service_kube_node | Container image for the NFS subdir external provisioner. |
| Prometheus | v3.4.1 | pod | Apache-2.0 | service_k8s | Monitoring and alerting toolkit for metrics collection. |

## Storage and CSI drivers

| Component | Version | Type | License | Installed On | Purpose |
| --- | --- | --- | --- | --- | --- |
| CSI PowerScale Driver | v2.17.0 | pod | Apache-2.0 | csi_driver_powerscale | CSI driver for Dell PowerScale storage arrays. |
| Dell Helm Charts | csi-isilon-2.15.0 | helm | Apache-2.0 | csi_driver_powerscale | Helm charts for Dell CSI driver deployment. |
| CSI Provisioner | v6.2.0 | pod | Apache-2.0 | csi_driver_powerscale | Sidecar that watches PersistentVolumeClaim objects and triggers `CreateVolume`/`DeleteVolume` against a CSI endpoint. |
| CSI Attacher | v4.11.0 | pod | Apache-2.0 | csi_driver_powerscale | Sidecar that watches VolumeAttachment objects and triggers `ControllerPublish`/`Unpublish` against a CSI endpoint. |
| CSI Snapshotter | v8.5.0 | pod | Apache-2.0 | csi_driver_powerscale | Sidecar that watches Snapshot CRD objects and triggers `CreateSnapshot`/`DeleteSnapshot` against a CSI endpoint. |
| CSI Resizer | v2.1.0 | pod | Apache-2.0 | csi_driver_powerscale | Sidecar that watches PersistentVolumeClaims and triggers controller-side expansion against a CSI endpoint. |
| CSI Node Driver Registrar | v2.16.0 | pod | Apache-2.0 | csi_driver_powerscale | Sidecar that registers a CSI driver with the kubelet plugin registration mechanism. |
| CSI External Health Monitor Controller | v0.17.0 | pod | Apache-2.0 | csi_driver_powerscale | Sidecar controller for volume health monitoring. |
| CSI Replicator | v1.15.0 | pod | Apache-2.0 | csi_driver_powerscale | Dell CSM for Replication; extends Kubernetes to support storage array-based disaster recovery. |
| CSM Metadata Retriever | v1.14.0 | pod | Apache-2.0 | csi_driver_powerscale | Dell CSI metadata retriever controller for cluster metadata via Kube API. |
| Snapshot Controller | v8.5.0 | pod | Apache-2.0 | csi_driver_powerscale | Manages creation and lifecycle of volume snapshots for CSI drivers. |

## Slurm cluster software

| Component | Version | Type | License | Installed On | Purpose |
| --- | --- | --- | --- | --- | --- |
| Slurm Workload Manager | 25.05.2 | rpm | GPL-2.0-only | slurm_control_node, slurm_node, login_node | HPC workload manager: job scheduling, resource allocation, and accounting. |
| Munge | 0.5.15 | rpm | GPL-2.0-only | slurm_custom | Authentication service for creating and validating user credentials across Slurm daemons. |
| MariaDB | 10.11.11 | rpm | GPL-2.0-only | slurm_control_node | Open-source relational database used by Slurm for job accounting. |
| MySQL | 9.3 | pod | MIT | service_k8s | Relational database management system (alternative backend for `slurmdbd`). |
| python3-PyMySQL | 1.1.2 | pip | MIT | slurm_control_node, service_kube_control_plane | Pure-Python MySQL client library for database connectivity. |
| OpenMPI | 5.0.8 | tarball | BSD-3-Clause | openmpi | Open-source MPI implementation for distributed parallel computing. |

## GPU and accelerator software

| Component | Version | Type | License | Installed On | Purpose |
| --- | --- | --- | --- | --- | --- |
| CUDA Toolkit | 13.0.2 | rpm | NVIDIA Software License | slurm_node, service_kube_node | Development environment for GPU-accelerated applications. |
| NVIDIA Container Runtime | 3.4.2 | rpm | Apache-2.0 | slurm_node, service_kube_node | Enables GPU access from within containers. |
| NVIDIA Device Plugin | 0.14.4 | pod | Apache-2.0 | service_k8s | Kubernetes device plugin for NVIDIA GPU registration. |
| NCCL | 2.25.1 | rpm | Apache-2.0 | slurm_node | Optimized primitives for collective multi-GPU communication. |
| OFED | 24.10-1.1.4.0 | rpm | NVIDIA Software License | slurm_custom, service_k8s | OpenFabrics Enterprise Distribution for InfiniBand and RDMA. |

## Authentication software

| Component | Version | Type | License | Installed On | Purpose |
| --- | --- | --- | --- | --- | --- |
| OpenLDAP | 2.6.9 | container | GPL-3.0-only | OIM | Open-source LDAP directory server for centralized user authentication. |
| openldap-clients | 2.6.9 | rpm | OLDAP-2.8 | openldap | Command-line tools for LDAP directory operations. |
| 389 Directory Server | 2.6.1 | container | GPL-3.0-or-later | OIM | Lightweight Directory Access Protocol server. |
| FreeIPA | 4.12.2 | container | GPL-3.0-only | OIM | Integrated identity management (alternative to standalone OpenLDAP). |
| Omnia Auth | 1.0.0 | container | Apache-2.0 | OIM | Authentication services container for centralized access control with OpenLDAP integration. |

## Telemetry software stack

| Component | Version | Type | License | Installed On | Purpose |
| --- | --- | --- | --- | --- | --- |
| Strimzi Kafka | 0.48.0-kafka-4.1.0 | pod | Apache-2.0 | service_k8s | Apache Kafka running on Kubernetes for telemetry data streaming. |
| Strimzi Kafka Operator | 0.48.0 | pod | Apache-2.0 | service_k8s | Deploys and manages Apache Kafka clusters on Kubernetes. |
| Strimzi Kafka Operator Helm Chart | 0.48.1 | helm | Apache-2.0 | service_k8s | Helm chart for deploying the Strimzi Kafka Operator. |
| Strimzi Kafka Bridge | 0.33.1 | pod | Apache-2.0 | service_k8s | HTTP-based API for Apache Kafka, enabling REST clients to produce and consume messages. |
| VictoriaMetrics | 1.128.0 | pod | Apache-2.0 | service_k8s | High-performance time-series database for metric storage. |
| vmagent | 1.128.0 | pod | Apache-2.0 | service_k8s | Lightweight agent for collecting, filtering, and forwarding metrics to VictoriaMetrics. |
| vmstorage | 1.128.0 | pod | Apache-2.0 | service_k8s | Storage node for VictoriaMetrics cluster mode. |
| vminsert | 1.128.0 | pod | Apache-2.0 | service_k8s | Ingestion handler for VictoriaMetrics cluster mode. |
| vmselect | 1.128.0 | pod | Apache-2.0 | service_k8s | Query execution handler for VictoriaMetrics cluster mode. |
| victoriapump | 1.0.0 | pod | Apache-2.0 | service_k8s | Pushes telemetry metrics from the Omnia pipeline into VictoriaMetrics. |
| kafkapump | 1.0.0 | pod | Apache-2.0 | service_k8s | Consumes telemetry data from Kafka topics and forwards it to downstream systems. |
| iDRAC Telemetry Reference Tools | commit 97ace09 | git | Apache-2.0 | OIM | Collects power, thermal, and health metrics from iDRAC via Redfish. |
| idrac-telemetry-receiver | 1.0.0 | pod | Apache-2.0 | service_k8s | Collects and streams telemetry data from Dell iDRAC interfaces. |
| LDMS | 4.5.1 | rpm | GPL-2.0 | ldms | Lightweight Distributed Metric Service for high-speed OS-level metric collection. |
| NERSC-LDMS | commit 1f46921 | helm | BSD-3-Clause | service_k8s | Helm chart, image build, and dashboards for LDMS. |
| LDMS Aggregator (image) | 1.0.0 | pod | Apache-2.0, GPL-2.0 | service_k8s | Ubuntu-based container with LDMS tools for telemetry and metric collection. |
| Prometheus | v3.4.1 | pod | Apache-2.0 | service_k8s | Monitoring and alerting toolkit for metrics collection. |

## Container and runtime software

| Component | Version | Type | License | Installed On | Purpose |
| --- | --- | --- | --- | --- | --- |
| Podman | 5.4.0 | rpm | Apache-2.0 | OIM, service_k8s | Daemonless container runtime used on the OIM and cluster nodes. |
| containerd | 2.0.5 | rpm | Apache-2.0 | service_k8s | Open and reliable container runtime for Kubernetes workloads. |
| nerdctl | 2.0.5 | rpm | Apache-2.0 | service_k8s | Docker-compatible CLI for containerd. |
| runc | 1.2.6 | rpm | Apache-2.0 | service_k8s | CLI tool for spawning and running containers per OCI specification. |
| BusyBox (base image) | 1.36 | image | Apache-2.0 | service_k8s | Minimal UNIX utilities base image for lightweight containers. |

## Ansible collections and libraries

| Component | Version | Type | License | Installed On | Purpose |
| --- | --- | --- | --- | --- | --- |
| containers.podman | 1.16.2 | ansible collection | GPL-3.0-or-later | OIM | Ansible collection for Podman container management. |
| community.grafana | 2.1.0 | ansible collection | GPL-3.0-only | OIM | Ansible collection for Grafana automation. |
| community.mysql | 3.10.3 | ansible collection | GPL-3.0-only | OIM | Ansible collection for MySQL/MariaDB management. |
| kubernetes.core | 5.2.0 | ansible collection | GPL-3.0-only | OIM | Ansible collection for Kubernetes and OpenShift cluster automation. |
| community.kubernetes | 2.0.1 | ansible collection | GPL-3.0-or-later | OIM | Ansible collection for Kubernetes resources. |
| ansible-pylibssh | 1.2.3 | pip | LGPL-2.1-only | OIM | Python bindings for libssh specific to Ansible. |
| python3-netaddr | 0.8.0 | pip | BSD-2-Clause, BSD-3-Clause | OIM | Network address manipulation library for Python. |
| libssh | 0.10.6 | rpm | LGPL-2.1-or-later | OIM | SSH library for secure remote access. |
| python3.12 | 3.12 | rpm | PSF | OIM, service_kube_control_plane | Python interpreter and standard library. |

## BuildStreaM software (optional)

| Component | Version | Type | License | Installed On | Purpose |
| --- | --- | --- | --- | --- | --- |
| GitLab | Latest compatible | container | MIT | OIM | CI/CD platform for BuildStreaM catalog-driven pipelines. |
| GitLab Runner | Latest compatible | container | MIT | OIM | Executes CI/CD pipeline jobs dispatched by GitLab. |
| BuildStreaM Catalog | Bundled with Omnia | container | Apache-2.0 | OIM | Declarative infrastructure catalog consumed by GitLab pipelines. |

!!! info

    - [Software Config](../Configuration/software_config.md) -- How software packages are selected for installation via `software_config.json`.
    - [Local Repo Config](../Configuration/local_repo_config.md) -- Repository mirror configuration for package sources.
    - [Software Config Json](../SampleFiles/software_config_json.md) -- Sample `software_config.json` for different deployment scenarios.
