# Installed Software

This page lists all software components that Omnia installs and configures across the OIM and cluster nodes. Versions are pinned to those validated with this release.

## OIM software

|| Component | Version | License | Purpose |
| --- | --- | --- | --- |
|| Omnia Core | 2.2.0.0 | Apache License 2.0 | The omnia_core image is the foundational container for Dell's Omnia solution, which is an open-source toolkit designed to deploy and manage high-performance computing (HPC), AI, and data analytics clusters. This container runs on the Omnia Infrastructure Manager (OIM) and acts as the central service for cluster orchestration. |
|| OpenCHAMI | 0.1.7-1 | Apache-2.0 | Open Composable Heterogeneous Adaptable Management Infrastructure |
|| SMD | v2.20.6 | MIT | The State Management Database (SMD) is a robust service designed for monitoring, tracking, and managing hardware components in high-performance computing (HPC) environments. |
|| BSS | v1.32.4 | MIT | The Boot Script Service (BSS) provides boot arguments (initrd, kernel arguments, etc.) and Level 2 boot services for static images in HPE Shasta systems. |
|| Image builder | 1.2 | MIT | A wrapper around various buildah commands that makes creating images in layers easier. |

|| coresmd | v0.6.3 | MIT | A CoreDHCP plugin with a pull-through cache that communicates with SMD |
|| cloud-init | v1.4.9 | GPL-3.0 | Micro-service for serving cloud-init payloads |
|| haproxy | latest | GPL-2.0-only | Reverse proxy for allowing all microservices to be accessible through a single http(s) host |
|| Step-CA | v0.2.6 | Apache-2.0 | A zero trust swiss army knife for working with X509, OAuth, JWT, OATH OTP, etc. |
|| Ory Hydra | v2.3 | Apache-2.0 | The only web-scale, fully customizable OpenID Certified™ OpenID Connect and OAuth2 Provider in the world. Become an OpenID Connect and OAuth2 Provider over night. Written in Go, cloud native, headless, API-first. Available as a service on Ory Network and for self-hosters. Relied upon by OpenAI and others for web-scale security. |
|| Pulp container | 3.114.2 | GPL-2.0-only | Pulp 3 pulpcore package |
|| pulpcore | 3.114.2 | GPL-2.0-only | Pulp Django Application and Related Modules |
|| pulp-cli | 0.40.1 | GPL-2.0-only | Command line interface to talk to pulpcore's REST API. |

|| minio | RELEASE.2026-08-04T00-00-00Z | GNU Affero General Public License v3.0 (AGPLv3) | MinIO is a high-performance object storage system compatible with the Amazon S3 API. |
|| registry | 3.1.1 | Apache-2.0 license | Docker Registry is the official image registry service for storing and distributing Docker images. |
|| postgresSQL (OpenCHAMI) | 17-alpine | PostgreSQL | PostgreSQL, also known as Postgres, is a free and open-source relational database management system emphasizing extensibility and SQL compliance. |
|| postgresSQL (Build Stream) | 16 | PostgreSQL | PostgreSQL, also known as Postgres, is a free and open-source relational database management system emphasizing extensibility and SQL compliance. |

## Kubernetes

|| Component | Version | License | Purpose |
| --- | --- | --- | --- |
|| Kubernetes Core Components | 1.35.1 | Apache-2.0 | Includes essential Kubernetes control plane and node components such as kubectl, kubelet, kubeadm, kube-apiserver, kube-controller-manager, kube-scheduler, kube-proxy, and cri-o for cluster management and container runtime. |
|| etcd | 3.6.6-0 | Apache-2.0 | Relational database used by Kubernetes |
|| coreDNS | v1.13.1 | Apache-2.0 | DNS server that chains plugins. |
|| calico/cni | v3.32.1 | Apache-2.0 | Cloud native networking and network |
|| calico/kube-controllers | v3.32.1 | Apache-2.0 | Cloud native networking and network |
|| calico/node | v3.32.1 | Apache-2.0 | Cloud native networking and network |
|| metallb | v0.16.1 | Apache-2.0 | A network load-balancer implementation for Kubernetes using standard routing protocols |
|| kube-vip | v1.2.2 | Apache-2.0 | Kubernetes Control Plane Virtual IP and Load-Balancer |


|| cert-manager | v1.10.0 | Apache-2.0 | X.509 certificate management for Kubernetes |
|| helm | v3.20.1 | Apache-2.0 | Kubernetes Package Manager |
|| pause | 3.10.1 | Apache-2.0 | kubernetes pause container |
|| alpine/kubectl | 1.35.1 | Apache-2.0 | Lightweight Alpine-based container image providing kubectl CLI for Kubernetes cluster management. |
|| Kubernetes pip module | 33.1.0 | Apache-2.0 | Official Python client library for kubernetes |
|| kubernetes pip module (legacy) | 32.0.1 | Apache-2.0 | Legacy Python client library for kubernetes |
|| kubernetes | 33.1.0 | Apache-2.0 | Python client for talk to a kubernetes cluster |
|| cri-o | 1.35.1 | Apache-2.0 | CLI and validation tools for Kubelet Container Runtime Interface (CRI) |
|| cni | 1.4.1 | Apache-2.0 | Networking for Linux containers |

## Storage and CSI drivers

|| Component | Version | License | Purpose |
| --- | --- | --- | --- |
|| csi powerscale driver | v2.17.0 | Apache-2.0 | CSI Driver for Dell PowerScale |
|| Dell helm-charts | container-storage-modules-1.10.0 | Apache-2.0 license | The source for Dell Helm charts |
|| CSI provisioner | v6.2.0 | Apache-2.0 license | Sidecar container that watches Kubernetes PersistentVolumeClaim objects and triggers CreateVolume/DeleteVolume against a CSI endpoint |
|| CSI attacher | v4.11.0 | Apache-2.0 license | Sidecar container that watches Kubernetes VolumeAttachment objects and triggers ControllerPublish/Unpublish against a CSI endpoint |
|| CSI snapshotter | v8.5.0 | Apache-2.0 license | Sidecar container that watches Kubernetes Snapshot CRD objects and triggers CreateSnapshot/DeleteSnapshot against a CSI endpoint. |
|| CSI resizer | v2.1.0 | Apache-2.0 license | Sidecar container that watches Kubernetes PersistentVolumeClaims objects and triggers controller side expansion operation against a CSI endpoint |
|| CSI node driver registrar | v2.16.0 | Apache-2.0 license | Sidecar container that registers a CSI driver with the kubelet using the kubelet plugin registration mechanism. |
|| CSI external health monitor controller | v0.17.0 | Apache-2.0 license | This repo contains sidecar controller and agent for volume health monitoring. |
|| CSI replicator | v1.15.0 | Apache-2.0 license | Dell Container Storage Modules (CSM) for Replication aims at extending native Kubernetes functionality to support Disaster Recovery workflows by utilizing storage array based replication. |
|| csm metadata retriever | v1.14.0 | Apache-2.0 license | Dell csi-metadata-retriever controller to retrieve various metadata from the cluster using kubeapi. |
|| snapshot controller | v8.5.0 | Apache-2.0 license | The snapshot-controller in Kubernetes manages the creation and management of volume snapshots, enabling point-in-time copies of your data for CSI drivers |
|| karavi-observability | v1.15.0 | Apache-2.0 license | Dell CSM Observability for PowerScale |
|| CSM Metrics PowerScale | v1.12.0 | Apache-2.0 | Dell CSM Metrics PowerScale exporter for storage telemetry |
|| nfs-subdir-external-provisioner | v4.0.2 | Apache-2.0 | Dynamic sub-dir volume provisioner on a remote NFS server. |
|| nfs-subdir-external-provisioner image | v4.0.2 | Apache License 2.0 | A dynamic storage provisioner for Kubernetes that uses an existing NFS server to create subdirectories for Persistent Volumes automatically. |
|| VAST Repo and Client | 4.5.5 | GPL-2.0 | VAST NFS client installation and repository for storage telemetry integration |
|| iscsi-initiator-utils | Latest | GPL-2.0-or-later | iSCSI initiator utilities |
|| device-mapper-multipath | Latest | GPL-2.0-or-later | Device mapper multipath tools |
|| sg3_utils | Latest | GPL-2.0-or-later | SCSI utility tools |
|| lsscsi | Latest | GPL-2.0-or-later | List SCSI devices utility |

## Slurm

|| Component | Version | License | Purpose |
| --- | --- | --- | --- |
|| Slurm Workload manager | 25.05.2 | GPL-2.0-only | HPC Workload Manager |
|| Munge | 0.5.16 | GPL-3.0 | MUNGE (MUNGE Uid 'N' Gid Emporium) is an authentication service for creating and validating user credentials. |
|| MariaDB | 10.11.11 | GPL-2.0-only | Open source relational database used by Slurm |
|| initscripts | 10.11.8 | GPL-2.0-only | Basic support for legacy System V init scripts |
|| mysql | 9.7.2 | GPL-2.0 | MySQL is an open-source relational database management system. |
|| python3-PyMySQL | 1.1.2 | MIT | Pure-Python MySQL client library |
|| PyMySQL | 1.1.2 | MIT | MySQL client library for Python |
|| OpenMPI | 5.0.10 | BSD-3-Clause-Clear | Open MPI main development repository |

## GPU and accelerator

|| Component | Version | License | Purpose |
| --- | --- | --- | --- |
|| CUDA | 13.2.1 | NVIDIA Software License | The NVIDIA® CUDA® Toolkit provides a development environment for creating high-performance, GPU-accelerated applications. |
|| NVidia container runtime | 3.4.2 | Apache-2.0 | Nvidia container runtime library |
|| rocm | 6.3.1 | MIT | AMD ROCm™ Software |
|| doca-ofed | 3.2.1 | NVIDIA DOCA EULA | NVIDIA DOCA OFED driver |
|| UCX | 1.19.0 | BSD-3-Clause | Unified Communication X - high-performance network communication library for HPC |

## Authentication

|| Component | Version | License | Purpose |
| --- | --- | --- | --- |
|| OpenLDAP | 2.6.9 | GPL-3.0-only | OpenLDAP is a free, open-source implementation of the Lightweight Directory Access Protocol (LDAP) developed by the OpenLDAP Project |
|| openldap-clients | 0:2.6.9-1.fc40 | OLDAP-2.8 | OpenLDAP client utilities provide command-line tools for interacting with LDAP directories, enabling operations such as searching, adding, modifying, and deleting directory entries. |
|| 389-ds | 2.6.1 | GPL-3.0-or-later | Light weight directory access protocol |
|| Omnia Auth | 1.0.0 | Apache License 2.0 | The omnia_auth image is part of Dell's Omnia toolkit and is responsible for authentication services within HPC, AI, and data analytics clusters. It primarily manages centralized user authentication and integrates with OpenLDAP to provide secure access control across the cluster. |

## Ansible collections

|| Component | Version | License | Purpose |
| --- | --- | --- | --- |
|| containers.podman | 1.16.2 | GPL-3.0-or-later | Repository for Ansible content that can include playbooks, roles, modules, and plugins for use with the Podman tool |
|| community.grafana | 2.1.0 | GPL-3.0-only | Ansible Community General Collection |
|| community.mysql | 3.10.3 | GPL-3.0-only | MySQL is an open-source relational database management system. |
|| kubernetes.core | 5.2.0 | GPL-3.0-only | The collection includes a variety of Ansible content to help automate the management of applications in Kubernetes and OpenShift clusters, as well as the provisioning and maintenance of clusters themselves. |
|| community.kubernetes | 2.0.1 | GPL-3.0-or-later | Kubernetes collection for ansible |
|| ansible.utils | 5.1.1 | Apache-2.0 | Ansible collection of utility modules |
|| community.crypto | 2.23.0 | Apache-2.0 | Ansible collection for cryptographic operations |
|| community.docker | 3.12.1 | Apache-2.0 | Ansible collection for Docker/Podman container management |
|| community.general | 10.3.0 | GPL-3.0-only | Ansible Community General Collection |
|| ansible.posix | 2.0.0 | GPL-3.0-or-later | Ansible collection for POSIX system management |
|| community.postgresql | 3.10.2 | PostgreSQL License | Ansible collection for PostgreSQL database management |
|| dellemc.os10 | 1.1.1 | Apache-2.0 | Ansible collection for Dell EMC OS10 switch management |
|| dellemc.openmanage | 9.6.0 | Apache-2.0 | Ansible collection for Dell EMC OpenManage |

## Telemetry stack

|| Component | Version | License | Purpose |
| --- | --- | --- | --- |
|| idrac-telemetry-reference tools | commit ID: 97ace09 | Apache-2.0 | Reference toolset for PowerEdge telemetry metric collection and integration with analytics and visualization solutions. |
|| idrac-telemetry-receiver | 1.3 | Apache License 2.0 | The idrac_telemetry_receiver image is part of Dell's Telemetry Reference Tools for PowerEdge servers. It is designed to collect and stream telemetry data from Dell iDRAC (Integrated Dell Remote Access Controller) interfaces to external analytics platforms for monitoring and visualization. |
|| LDMS | 4.5.2 | GPL-2.0 | OVIS/LDMS High Performance Computing monitoring, analysis, and visualization project. |
|| NERSC-LDMS | commit 1f46921 | BSD-3-Clause | Helm Chart, Image Build, and Dashboards for the Light Weight Distributed Metric Service |
|| LDMS Aggregator image | 1.1 | Apache License 2.0 and GPL-2.0-or-later | Ubuntu-based container with LDMS tools for telemetry and metric collection in HPC/AI environments. |
|| Strimzi-Kafka | 1.1.0-kafka-4.3.0 | Apache-2.0 license | Apache Kafka® running on Kubernetes |
|| Strimzi Kafka Operator | 1.1.0 | Apache-2.0 license | Deploy and manage Apache Kafka clusters on Kubernetes/OpenShift |
|| Strimzi Kafka Operator Helm Chart | 1.1.0 | Apache-2.0 license | Deploy Strimzi Kafka Operator on Kubernetes using Helm 3 |
|| Strimzi Kafka Bridge | 1.0.0 | Apache-2.0 license | Provides an HTTP-based API for Apache Kafka, enabling REST clients to produce and consume messages without using Kafka protocol directly. |
|| apache/activemq | 6.3.0 | Apache-2.0 | Apache ActiveMQ message broker |
|| VictoriaMetrics | 1.149.0 | Apache-2.0 license | VictoriaMetrics: fast, cost-effective monitoring solution and time series database |
|| VictoriaMetrics operator | v0.68.3 | Apache-2.0 license | Kubernetes operator for VictoriaMetrics |
|| VictoriaLogs | v1.50.0 | Apache-2.0 license | Centralized log storage and querying for VictoriaMetrics |
|| VLAgent | v1.50.0 | Apache-2.0 license | VictoriaLogs agent for log collection |
|| vmagent | 1.149.0 | Apache License 2.0 | A lightweight agent for collecting metrics from various sources, filtering, relabeling, and sending them to VictoriaMetrics or other storage systems via Prometheus/VictoriaMetrics remote_write protocols. |
|| vmstorage | 1.149.0 | Apache License 2.0 | vmstorage is the storage node for VictoriaMetrics cluster mode, responsible for storing time-series data. |
|| vminsert | 1.149.0 | Apache License 2.0 | vminsert handles ingestion of metrics into VictoriaMetrics cluster mode. |
|| vmselect | 1.149.0 | Apache License 2.0 | vmselect handles query execution in VictoriaMetrics cluster mode. |
|| victoriapump | 1.3 | Apache License 2.0 | The victoriapump image is part of Dell's Omnia telemetry pipeline and is designed to push telemetry metrics into VictoriaMetrics, a high-performance time-series database optimized for large-scale monitoring and observability. |
|| Kafkapump | 1.3 | Apache License 2.0 | The kafkapump image is part of Dell's Omnia telemetry pipeline and is designed to consume telemetry data from Kafka topics and forward it to downstream systems such as time-series databases (e.g., VictoriaMetrics) or analytics platforms. |
|| Vector | 0.54.0-debian | Apache-2.0 | A high-performance observability data pipeline for logs, metrics, and traces |
|| OTEL Collector | 0.150.1 | Apache-2.0 | OpenTelemetry Collector for metrics and logs collection |
|| curlimages/curl | 8.17.0 | MIT | Lightweight container with curl utility |
|| nginx-unprivileged | 1.29 | BSD-2-Clause | Unprivileged NGINX container image |

## Container and runtime software

|| Component | Version | License | Purpose |
| --- | --- | --- | --- |
|| podman | 5.4.0 | Apache License 2.0 | Podman: A tool for managing OCI containers and pods. |
|| Busybox base image | 1.36 | Apache-2.0 license | BusyBox combines tiny versions of many common UNIX utilities into a single small executable |
|| apptainer | Latest | LGPL-2.1-or-later | Container runtime for HPC |

## Container Operating Systems

|| Component | Version | License | Purpose |
| --- | --- | --- | --- |
|| Fedora Core | 40 | MIT | Fedora CoreOS is a container-focused Linux distribution developed by the Fedora Project and sponsored by Red Hat. It provides an immutable, minimal, and secure operating system optimized for running container workloads at scale. |
|| Fedora 42 | 42 | MIT | Fedora is a Linux-based operating system, a collection of software that makes your computer run. |
|| Ubuntu 26.04 | 26.04 | GNU General Public License v2.0 or later | Ubuntu is a Linux distribution for desktop and server. |

## Utilities and libraries

|| Component | Version | License | Purpose |
| --- | --- | --- | --- |
|| gcc-c++ | 11.5.0 | GPL-3.0-only | This package adds C++ support to the GNU Compiler Collection. It includes support for most of the current C++ specification, including templates and exception handling. |
|| perl-Text-Tabs+Wrap | 2024.001 | TTWL | Unknown |
|| golang.org/x/crypto | v0.52.0 | BSD-3-Clause | This repository holds supplementary Go cryptography libraries |
|| golang.org/x/net | v0.54.0 | BSD-3-Clause | Unknown |
|| golang.org/x/sync | 0.12.0 | BSD-3-Clause | Unknown |
|| golang.org/x/sys | 0.31.0 | BSD-3-Clause | supplemental Go packages for low level interactions with the operating system |
|| golang.org/x/text | 0.23.0 | BSD-3-Clause | mirror Go text processing support |
|| Go | 1.25.10 | BSD-3-Clause | Go is an open source programming language that makes it easy to build simple, reliable, and efficient software. |
|| Git LFS | v3.7.1 | MIT | Git LFS is a command line extension and specification for managing large files with Git. |
|| ansible pylibssh | 1.2.3 | LGPL-2.1-only | Python bindings specific to Ansible use case for libssh |
|| python3-netaddr | 0.8.0 | BSD?2-Clause, BSD?3-Clause | A network address manipulation library for Python |
|| libssh-config | 0.10.6 | LGPL-2.1-OR-LATER | Unknown |
|| libssh | 0.11.1 | LGPL-2.1-OR-LATER | Unknown |
|| python3.12 | 3.12.9 | Python Software Foundation License (PSF) | Python 3.12 is the core interpreter and standard library for the Python programming language, enabling execution of Python applications and scripts on the system. |
|| python3.13 | 3.13 | Python Software Foundation License (PSF) | Python 3.13 is the core interpreter and standard library for the Python programming language, enabling execution of Python applications and scripts on the system. |
|| python3.14 | 3.14 | Python Software Foundation License (PSF) | Python 3.14 is the core interpreter and standard library for the Python programming language, enabling execution of Python applications and scripts on the system. |
|| uv | 0.11.15 | Apache-2.0 or MIT | An extremely fast Python package installer and resolver, written in Rust. |
|| uv (omnia_core) | 0.9.13 | Apache-2.0 or MIT | An extremely fast Python package installer and resolver, written in Rust. |
|| pip | 26 | MIT | The pip package installer is the standard package manager for Python. |
|| pip (ubuntu-ldms) | 26.1.1 | MIT | The pip package installer is the standard package manager for Python. |
|| wheel | 0.46.2 | MIT | A built-package format for Python. |
|| setuptools | 80.10.2 | MIT | A library for packaging Python projects. |
|| Cython | 3.0.12 | Apache-2.0 | Cython is a programming language that makes writing C extensions for the Python language as easy as Python itself. |
|| prettytable | 3.14.0 | BSD-3-Clause | Python library for displaying tabular data |
|| cryptography | 45.0.7 | Apache-2.0 | Python cryptography library |
|| omsdk | 1.2.518 | Apache-2.0 | Dell OpenManage SDK |
|| cffi | 1.17.1 | MIT | Python Foreign Function Interface for C |
|| prometheus_client | 0.20.0 | BSD-3-Clause | Python client for Prometheus |

!!! info

    - [Software Config](../Configuration/software_config.md) -- How software packages are selected for installation via `software_config.json`.
    - [Local Repo Config](../Configuration/local_repo_config.md) -- Repository mirror configuration for package sources.
    - [Software Config Json](../SampleFiles/software_config_json.md) -- Sample `software_config.json` for different deployment scenarios.
