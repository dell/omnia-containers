
# Installed Software


This page lists all software components that Omnia v2.1 installs and
configures across the OIM and cluster nodes. Versions are pinned to those
validated with this Omnia release.

## OIM (Management Node) software


| Component | Version | Purpose |
| --- | --- | --- |
| Podman | Latest (RHEL repo) | Container runtime for all OIM services. No Docker daemon required. |
| OpenCHAMI | Bundled with Omnia | Composable Hierarchical Automated Management Infrastructure for node discovery and lifecycle management. |
| ochami-cli | Bundled with Omnia | Command-line interface for interacting with OpenCHAMI. |
| SMD (State Manager Daemon) | Bundled with Omnia | Maintains hardware inventory and node state within OpenCHAMI. |
| BSS (Boot Script Service) | Bundled with Omnia | Generates per-node boot scripts for PXE/iPXE provisioning. |
| CoreDHCP | Bundled with Omnia | Lightweight DHCP server for IP assignment during provisioning. |
| TFTP / iPXE | Bundled with Omnia | Network boot services for bare-metal node provisioning. |
| Pulp | 3.x | Repository management platform; mirrors RHEL and third-party repos to the OIM for air-gapped or bandwidth-efficient deployments. |
| Ansible (inside omnia_core) | ansible-core 2.16.x | Automation engine for all Omnia playbooks. |
| AWX (optional) | Latest compatible | Web-based Ansible UI and REST API. Optional; Omnia can run from CLI. |

## Slurm cluster software


| Component | Version | Purpose |
| --- | --- | --- |
| Slurm | 23.11.x | HPC workload manager: job scheduling, resource allocation, accounting. |
| slurmctld | 23.11.x | Slurm controller daemon (runs on `slurm_control_node`). |
| slurmd | 23.11.x | Slurm compute daemon (runs on `slurm_node`). |
| slurmdbd | 23.11.x | Slurm database daemon for job accounting (runs on `slurm_control_node`). |
| Munge | Latest (RHEL repo) | Authentication service for Slurm inter-daemon communication. |
| MariaDB / MySQL | Latest (RHEL repo) | Backend database for `slurmdbd` job accounting. |
| OpenLDAP | Latest (RHEL repo) | Centralized user authentication (runs on `auth_server` node). |
| FreeIPA (optional) | Latest (RHEL repo) | Integrated identity management (alternative to standalone OpenLDAP). |

## Kubernetes cluster software


| Component | Version | Purpose |
| --- | --- | --- |
| Kubernetes (K8s) | 1.29.x | Container orchestration platform for service workloads. |
| kubelet | 1.29.x | Node agent that manages pod lifecycle on each worker. |
| kubeadm | 1.29.x | Cluster bootstrap and lifecycle tool. |
| kubectl | 1.29.x | Command-line tool for Kubernetes cluster management. |
| Calico | 3.27.x | CNI plugin for pod networking and network policy enforcement. |
| MetalLB | 0.14.x | Bare-metal load balancer; assigns external IPs to `LoadBalancer` services. |
| NFS CSI Driver | Latest compatible | Container Storage Interface driver for NFS-backed persistent volumes. |
| etcd | 3.5.x | Distributed key-value store backing the Kubernetes API server. |
| CoreDNS | Latest (bundled with K8s) | DNS server for Kubernetes service discovery. |

## GPU software stack


| Component | Version | GPU Vendor | Purpose |
| --- | --- | --- | --- |
| NVIDIA Driver | 550.x or latest | NVIDIA | Kernel module and userspace libraries for GPU access. |
| CUDA Toolkit | 12.x | NVIDIA | GPU programming framework; includes nvcc, cuBLAS, cuDNN. |
| NVIDIA Container Toolkit | Latest compatible | NVIDIA | Enables GPU access from within containers (Podman/Docker). |
| ROCm | 6.x | AMD | AMD GPU programming framework (equivalent to CUDA). |
| AMD GPU Driver | Bundled with ROCm | AMD | Kernel module for AMD Instinct GPUs. |

## Telemetry software stack


| Component | Version | Purpose |
| --- | --- | --- |
| Apache Kafka | 3.x | Distributed event streaming platform for telemetry data ingestion. |
| VictoriaMetrics | Latest compatible | High-performance time-series database for metric storage. |
| Grafana | 10.x | Visualization and dashboarding platform for metrics. |
| iDRAC Telemetry Collector | Bundled with Omnia | Collects power, thermal, and health metrics from iDRAC via Redfish. |
| LDMS (Lightweight Distributed Metric Service) | 4.x | High-speed metric collection from compute node OS (meminfo, vmstat, procstat, procnetdev). |
| Node Exporter | Latest compatible | Prometheus-compatible exporter for OS-level metrics. |

## Container and runtime software


| Component | Version | Purpose |
| --- | --- | --- |
| Podman | Latest (RHEL repo) | Daemonless container runtime used on the OIM and optionally on nodes. |
| Buildah | Latest (RHEL repo) | OCI container image builder (used with Podman). |
| Skopeo | Latest (RHEL repo) | Container image inspection and transfer tool. |

## BuildStreaM software (optional)


| Component | Version | Purpose |
| --- | --- | --- |
| GitLab | Latest compatible | CI/CD platform for BuildStreaM catalog-driven pipelines. |
| GitLab Runner | Latest compatible | Executes CI/CD pipeline jobs dispatched by GitLab. |
| BuildStreaM Catalog | Bundled with Omnia | Declarative infrastructure catalog consumed by GitLab pipelines. |

!!! info

    - [Software Config](../Configuration/software_config.md) -- How software packages
      are selected for installation via `software_config.json`.
    - [Local Repo Config](../Configuration/local_repo_config.md) -- Repository mirror
      configuration for package sources.
    - [Software Config Json](../SampleFiles/software_config_json.md) -- Sample
      `software_config.json` for different deployment scenarios.
