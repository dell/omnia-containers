# Omnia Telemetry Subsystem — Functional Specification

**Document ID:** FSPEC-TELEM-2026-001
**Version:** 1.2
**Date:** 2026-04-27
**Status:** Approved
**Author:** Ravishankar N

**Companion Document:** BSpec BSPEC-TELEM-2026-001 v2.2 (customer-facing behavior)

**Revision History:**

| Version | Date | Changes | Author |
|---------|------|---------|--------|
| 1.0 | 2026-03-30 | Initial creation per SDD methodology — companion to BSpec | Ravishankar N |
| 1.2 | 2026-03-31 | Rewrote Section 5.15 (PowerScale Storage Telemetry) from scratch per Capability 19101: CSM Metrics for PowerScale + OpenTelemetry Collector as sole metrics architecture; removed legacy gostats references; two deployment modes (Omnia-orchestrated, operator-provided endpoint); dual-destination delivery; operational health indicators; assumptions; updated Sections 4.2, 4.3, and Glossary accordingly | Ravishankar N |

**SDD Phase:** Phase 2b — Functional Specification (parallel with BSpec)

---

# 1 References

The following documents are included for reference.

| **LOB** | **Type** | **Document Name** | **Description** |
|---|---|---|---|
| Dell Omnia | Confluence | [Omnia Telemetry Behaviour Specification](https://confluence.gtie.dell.com/spaces/ISET/pages/1958330177/Omnia+Telemetry+Behaviour+Specification+CY26+Q2) | Companion BSpec defining customer-facing behavior |
| Dell Omnia | External Docs | [Omnia v2.1.0.0-rc2 Documentation](https://omnia.readthedocs.io/en/v2.1.0.0-rc2/) | Current release documentation |
| VictoriaMetrics | External Docs | [VictoriaMetrics Cluster Mode](https://docs.victoriametrics.com/cluster-victoriametrics/) | Upstream cluster deployment reference |
| VictoriaLogs | External Docs | [VictoriaLogs Documentation](https://docs.victoriametrics.com/victorialogs/) | Upstream log management reference |
| Strimzi | External Docs | [Strimzi Kafka Operator](https://strimzi.io/documentation/) | Kafka operator reference |
| Vector | External Docs | [Vector Documentation](https://vector.dev/docs/) | Data pipeline reference |
| NVIDIA | External Docs | [NVIDIA DCGM Documentation](https://docs.nvidia.com/datacenter/dcgm/latest/) | GPU Manager reference |

---

# 2 Glossary

| **Acronym / Term** | **Definition** |
|---|---|
| HPC | High Performance Computing |
| OIM | Omnia Infrastructure Manager — central management host |
| K8s | Kubernetes |
| iDRAC | Integrated Dell Remote Access Controller — out-of-band hardware management interface |
| LDMS | Lightweight Distributed Metric Service — in-band OS-level metric collection |
| VictoriaMetrics | High-performance time-series database for metric storage and querying |
| VictoriaLogs | Centralised log management component of the VictoriaMetrics ecosystem |
| vmagent | VictoriaMetrics agent — Prometheus-compatible metrics scraper and forwarder |
| VLAgent | VictoriaLogs agent — syslog receiver that forwards logs to VictoriaLogs |
| Kafka | Apache Kafka — distributed streaming platform used as telemetry data bus |
| Strimzi | Kubernetes operator for managing Apache Kafka clusters |
| KRaft | Kafka Raft — consensus protocol replacing ZooKeeper |
| Vector | High-performance data pipeline tool for transforming and routing logs and metrics |
| SFM | Smart Fabric Manager — Dell management console for SONiC-based Ethernet switches |
| OME | OpenManage Enterprise — Dell server management and monitoring console |
| UFM | NVIDIA Unified Fabric Manager — InfiniBand fabric management platform |
| NetQ | NVIDIA NetQ — Ethernet fabric monitoring and telemetry platform |
| Skyway | NVIDIA Skyway — InfiniBand-to-Ethernet gateway |
| DCGM | NVIDIA Data Center GPU Manager — daemon and Prometheus exporter for GPU telemetry |
| VAST | VAST Data Platform — flash-based parallel storage cluster |
| PowerScale | Dell PowerScale — scale-out NAS storage platform (OneFS) |
| PowerVault | Dell PowerVault ME5 — SAN/DAS block storage array |
| mTLS | Mutual Transport Layer Security — both client and server authenticate via certificates |
| TLS | Transport Layer Security |
| PVC | Persistent Volume Claim (Kubernetes persistent storage) |
| Redfish | DMTF standard RESTful API for server hardware management |
| SNMP | Simple Network Management Protocol |
| RBAC | Role-Based Access Control |
| StatefulSet | Kubernetes workload for stateful applications with stable network identity |
| Deployment | Kubernetes workload for stateless replicated applications |
| ConfigMap | Kubernetes object storing non-confidential configuration data |
| Helm | Kubernetes package manager |
| Kustomize | Kubernetes configuration customization tool |
| OpenChami | Cloud-init template generation system used by Omnia for node provisioning |
| NFS | Network File System — shared storage for configuration distribution |
| Pulp | Software repository management platform for air-gapped package distribution |
| STOMP | Simple Text Oriented Messaging Protocol |
| ActiveMQ | Open-source message broker using STOMP protocol |
| PromQL | Prometheus Query Language for time-series data |
| CSM Metrics for PowerScale | Dell Container Storage Modules (CSM) Observability component that collects PowerScale metrics (IOPS, throughput, latency, capacity, health, topology) and exposes them via OpenTelemetry |

---

# 3 Edit History

| **Revision** | **Date** | **Changes** | **Author** |
|---|---|---|---|
| 1.0 | 2026-03-30 | Initial creation per SDD methodology — companion to BSpec | Ravishankar N |
| 1.2 | 2026-03-31 | Rewrote Section 5.15 (PowerScale Storage Telemetry) from scratch per Capability 19101: CSM Metrics for PowerScale + OpenTelemetry Collector as sole metrics architecture; removed legacy gostats references; two deployment modes (Omnia-orchestrated, operator-provided endpoint); dual-destination delivery; operational health indicators; assumptions; updated Sections 4.2, 4.3, and Glossary accordingly | Ravishankar N |

---

# 4 Overview

## 4.1 Purpose and Scope

This Functional Specification defines **what the Omnia Telemetry subsystem does internally** to deliver the capabilities described in the companion Behaviour Specification (BSpec). It covers internal system behaviors, data flows, state management, component interactions, and conditional deployment logic.

**In scope:** Internal component topology, data flow paths with ports and protocols, configuration processing, feature flag logic, failure modes and recovery, system interfaces.

**Out of scope:** Customer-facing behavior (see BSpec), implementation code (see Engineering Spec/LLD).

## 4.2 Telemetry Namespace Architecture

The following diagram depicts the telemetry service architecture deployed on the Service Kubernetes cluster, showing VictoriaMetrics cluster components, vmagent, iDRAC collector, and their interactions.

*Figure 1: Telemetry Service Architecture on the Service Kubernetes cluster.*

![Telemetry Service Architecture](../images/dell_hpc_telemetry.png)



All telemetry components deploy into a dedicated Kubernetes namespace ("telemetry") on the Service Kubernetes cluster. The namespace contains:

- **StatefulSets:** vmstorage (3 replicas), vlstorage (2 replicas, Q2), Kafka brokers (3), Kafka controllers (3), iDRAC telemetry receiver (1), LDMS aggregator (1)
- **Deployments:** vminsert (2), vmselect (2), vlinsert (2, Q2), vlselect (2, Q2), vmagent (1), VLAgent (1, Q2), Vector (1, Q2), Skyway SNMP poller (1, Q2 conditional), PowerVault collector (1, Q2 conditional), CSM Metrics for PowerScale (1, Q2 conditional), OpenTelemetry Collector (1, Q2 conditional)
- **Services:** LoadBalancer (vminsert:8480, vmselect:8481, vlinsert:9481, vlselect:9491, Kafka external:9094, Kafka Bridge:8080), ClusterIP (internal)
- **Secrets:** TLS certificates (Victoria CA, Kafka cluster CA, client certs), MySQL credentials, Munge keys
- **ConfigMaps:** vmagent scrape configuration, LDMS sampler configuration
- **PVCs:** vmstorage (3×8Gi=24Gi), vlstorage (2×8Gi=16Gi, Q2), Kafka (6×8Gi=48Gi), MySQL (1Gi)
- **Jobs/CronJobs:** TLS test validation, pod cleanup maintenance

Manifests are organized using Kustomize with a kustomization.yaml that conditionally includes component-specific manifests based on feature flags.

## 4.3 Internal Data Flow Summary

The telemetry subsystem processes data through these internal paths:

- **iDRAC metrics:** iDRAC (Redfish) → Receiver → VictoriaPump(:2112) → vmagent → vminsert(:8480) → vmstorage
- **iDRAC to Kafka:** iDRAC (Redfish) → Receiver → KafkaPump → Kafka(topic:idrac, :9093 mTLS)
- **iDRAC events:** Kafka(idrac) → Vector → vlinsert
- **LDMS:** Samplers(:10001) → Aggregator(:6001) → Storage(:6001) → KafkaPump → Kafka(topic:ldms) → Vector → vminsert
- **SFM:** SFM Prometheus → remote_write HTTPS → vminsert(:8480 LB)
- **OME:** OME → Kafka(:9094 mTLS LB)
- **UFM metrics:** UFM exporter(:9090) → vmagent → vminsert + Omni
- **UFM logs:** UFM syslog → VLAgent → vlinsert
- **NetQ:** NetQ PromQL → vmagent → vminsert + Omni; rsyslog → VLAgent → vlinsert
- **Skyway:** SNMP polling → vminsert + Omni; syslog → VLAgent → vlinsert
- **DCGM:** DCGM Exporter(:9400) → LDMS sampler → Aggregator → Kafka(ldms)
- **PowerVault:** Redfish/CLI → collector → vminsert + Omni; CLI events → vlinsert
- **PowerScale:** CSM Metrics for PowerScale → OTel Collector → vmagent(TLS, K8s SA auth) → vminsert + Omni; syslog → VLAgent → vlinsert
- **VAST:** VAST exporter(HTTPS) → vmagent multi-scrape → vminsert + Omni; syslog → VLAgent → vlinsert

## 4.4 Configuration Input Processing

The system processes configuration through these inputs:

- **telemetry_config.yml:** Primary user configuration — iDRAC settings, VictoriaMetrics settings, Kafka settings, LDMS sampler configurations
- **telemetry_config.json (JSON Schema):** Validates all fields with conditional requirements (e.g., if idrac+kafka → kafka_configurations required)
- **software_config.json:** Auto-detects LDMS support (feature flag derivation)
- **service_k8s.json:** Container image references and versions
- **functional_groups_config.yml:** Maps nodes to functional groups
- **pxe_mapping_file.csv:** Node-to-group mapping, BMC IPs; changes trigger LDMS restart

---

# 5 Feature-by-Feature System Behavior

## 5.1 VictoriaMetrics Cluster Mode

### 5.1.1 Internal System Behavior

VictoriaMetrics is deployed within the telemetry namespace of the Service Kubernetes cluster as the central metrics store. In cluster mode, three independently scalable component types are deployed:

- **vmstorage** (3 replicas, StatefulSet) — Stores raw time-series data on persistent volumes. Each replica uses a dedicated PVC (default 8 Gi per pod, 24 Gi total). Data is distributed across replicas using consistent hashing. Resource allocation: 2 Gi memory request / 4 Gi limit, 500 m CPU request / 2000 m limit.
- **vminsert** (2 replicas, Deployment) — Accepts incoming metrics via the Prometheus remote_write API and routes them to the appropriate vmstorage node. Exposed externally via a LoadBalancer service on port 8480.
- **vmselect** (2 replicas, Deployment) — Handles PromQL queries by fanning out to all vmstorage nodes, merging results. Exposed externally via a LoadBalancer service on port 8481. Hosts the VMUI web interface.

All cluster components use TLS encryption with auto-generated self-signed certificates (valid for 10 years). Certificate Subject Alternative Names cover all service DNS names. Pod anti-affinity rules spread replicas across different worker nodes for resilience. Deduplication is configured at a 1-minute interval.

**Single-node mode:** 1 pod (StatefulSet), insert endpoint :8443, query endpoint :8443, 8 Gi storage. Suitable for dev/test or small environments.

Data retention: configurable via telemetry_config.yml (default 168 hours / 7 days). Data older than retention period is automatically purged by the retention engine. A dedicated cleanup script supports selective teardown of VictoriaMetrics components without affecting Kafka or other telemetry services.

### 5.1.2 Internal Data Flow

Metrics ingestion paths into VictoriaMetrics:

- vmagent scrape → vminsert:8480 (remote_write, TLS) → vmstorage (consistent hash routing)
- SFM Prometheus → remote_write HTTPS → vminsert:8480 (LoadBalancer)
- Vector (Kafka consumer) → remote_write → vminsert:8480
- External clients → vminsert:8480 (LoadBalancer, TLS)

Query path: Client/VMUI → vmselect:8481 → fan-out to all vmstorage replicas → merge → return.

### 5.1.3 Configuration Processing

Configuration parameters from telemetry_config.yml:

- victoria_configurations.deployment_mode: "single-node" | "cluster" (default: "cluster")
- victoria_configurations.persistence_size: Kubernetes storage format (default: "8Gi")
- victoria_configurations.retention_period: hours (default: 168, minimum: 24)

Conditional logic: If idrac_telemetry_collection_type contains "victoria", victoria_configurations is REQUIRED in the schema validation.

### 5.1.4 System Interfaces

- vminsert LoadBalancer: port 8480 — Prometheus remote_write API (TLS)
- vmselect LoadBalancer: port 8481 — PromQL query API + VMUI (TLS)
- Internal vmstorage: port 8482 — data replication between storage replicas
- TLS CA certificate: shared via Kubernetes Secret in telemetry namespace

### 5.1.5 Failure Modes and Recovery

- Single vmstorage pod failure: queries continue via remaining replicas; partial data gap for metrics hashed to that node. Recovery: pod restart with PVC data intact.
- vminsert pod failure: LoadBalancer routes to surviving replica; no data loss.
- vmselect pod failure: LoadBalancer routes to surviving replica; queries continue.
- PVC loss: partial permanent data loss for metrics on that volume. Mitigation: pod anti-affinity across nodes.
- Certificate expiry: auto-generated 10-year validity minimizes risk; manual renewal process required.

## 5.2 vmagent — Metrics Scraping and Forwarding

### 5.2.1 Internal System Behavior

vmagent is deployed as a single-replica Deployment in the telemetry namespace. It uses Kubernetes service discovery (pod role) to automatically find scrape targets. Currently, it discovers and scrapes the VictoriaPump container (port 2112) running inside the iDRAC telemetry pod, which exposes iDRAC hardware metrics in Prometheus format. The global scrape interval is 10 seconds.

Collected metrics are forwarded to VictoriaMetrics via Prometheus remote_write using TLS with the cluster CA certificate. In cluster mode, vmagent writes to vminsert on port 8480; in single-node mode, it writes to the VictoriaMetrics LoadBalancer on port 8443.

vmagent has its own ServiceAccount and RBAC role granting permission to discover pods in the telemetry namespace. Relabel rules add namespace, pod, and container labels to all scraped metrics. As new telemetry sources are added (UFM, NetQ, PowerScale, VAST), additional scrape jobs are added to the scrape configuration.

### 5.2.2 Internal Data Flow

Scrape targets → vmagent (Kubernetes pod discovery, label: idrac-telemetry, container: victoriapump, port: 2112) → remote_write → vminsert:8480 (cluster) or VM:8443 (single)

### 5.2.3 Configuration Processing

Scrape configuration defines jobs targeting pods with specific labels. Job name: "idrac-telemetry". Future scrape jobs for UFM, NetQ, PowerScale, VAST will be added as additional job entries in the ConfigMap.

Remote write URL computed from deployment_mode: cluster → vminsert.telemetry.svc.cluster.local:8480, single → victoria-loadbalancer.telemetry.svc.cluster.local:8443

### 5.2.4 System Interfaces

- Scrape target: VictoriaPump at port 2112 (Prometheus /metrics endpoint)
- Remote write: vminsert at port 8480 (cluster) or VM at port 8443 (single)
- Kubernetes API: pod discovery via ServiceAccount RBAC

### 5.2.5 Failure Modes and Recovery

- vmagent pod failure: metrics scraping stops until pod restarts. Remote_write buffer persists in-memory (lost on crash). No persistent queue.
- Scrape target unavailable: vmagent logs error and retries at next scrape interval. No data loss for other targets.

## 5.3 Apache Kafka Streaming Bus

### 5.3.1 Internal System Behavior

Apache Kafka is deployed using the Strimzi Kubernetes operator in KRaft mode (no ZooKeeper dependency). The cluster consists of 3 controller nodes and 3 broker nodes, each as StatefulSets with dedicated PVCs (default 8 Gi per pod, 48 Gi total across 6 pods).

Three listeners are configured:

- **Internal** (port 9092) — TLS-encrypted, no client authentication, for intra-cluster communication.
- **TLS** (port 9093) — TLS with mutual authentication (mTLS), used by internal producers (KafkaPump, LDMS).
- **External** (port 9094) — mTLS via LoadBalancer, used by external clients (OME).

A Kafka Bridge (HTTP REST interface) is deployed on port 8080 via a LoadBalancer service, enabling external systems to produce and consume messages via standard HTTP.

Two primary topics are managed: "idrac" (1 partition) and "ldms" (2 partitions). Topic names are fixed constants; only partition counts are configurable (1-100). Replication factor is 3 with minimum in-sync replicas of 2. Default log retention is 7 days, log segment size 1 GB, retention check interval 5 minutes.

The KafkaUser "kafkapump" is provisioned with mTLS client certificates and comprehensive ACLs covering topic creation, read, write, and consumer group management.

### 5.3.2 Internal Data Flow

- iDRAC KafkaPump → Kafka broker (topic: idrac, mTLS :9093)
- LDMS Kafka Pump → Kafka broker (topic: ldms, mTLS :9093)
- OME → Kafka broker (external mTLS :9094)
- Vector (consumer) ← Kafka broker (topics: idrac, ldms)
- Kafka Bridge :8080 ← External HTTP REST consumers

### 5.3.3 Configuration Processing

Configuration from telemetry_config.yml:

- kafka_configurations.persistence_size: per-pod storage (default "8Gi", total = 6 × value)
- kafka_configurations.log_retention_hours: default 168 (7 days)
- kafka_configurations.log_retention_bytes: default -1 (unlimited)
- kafka_configurations.log_segment_bytes: default 1073741824 (1 GB)
- kafka_configurations.topic_partitions: list of {name, partitions} — only "idrac" and "ldms" allowed

Conditional: kafka_support flag is TRUE if "kafka" is in idrac_telemetry_collection_type OR ldms_support is TRUE. Topic "idrac" required if iDRAC telemetry enabled with kafka. Topic "ldms" required if LDMS detected in software_config.json.

Strimzi operator tarball is downloaded during prerequisite setup and installed via Helm before Kafka cluster resources are created.

### 5.3.4 System Interfaces

- Internal listener: port 9092 (TLS, no auth)
- TLS listener: port 9093 (mTLS, internal producers)
- External listener: port 9094 (mTLS, LoadBalancer)
- Kafka Bridge: port 8080 (HTTP REST, LoadBalancer)
- Kafka cluster CA secret: "kafka-cluster-ca-cert" in telemetry namespace
- Client secret: "kafkapump" in telemetry namespace

### 5.3.5 Failure Modes and Recovery

- Single broker failure: replication factor 3, min in-sync 2 — no data loss, continued operation.
- Single controller failure: KRaft quorum maintained with 2/3 controllers.
- PVC loss: permanent data loss for messages on that broker. Mitigation: replication across brokers.
- External LoadBalancer failure: OME connectivity interrupted until restored.
- Strimzi operator failure: existing Kafka cluster continues; no new reconciliation until operator recovers.

## 5.4 iDRAC Hardware Telemetry

### 5.4.1 Internal System Behavior

iDRAC telemetry is deployed as a StatefulSet in the telemetry namespace containing up to five containers:

- **MySQL** — Stores iDRAC credentials and telemetry metadata. 1 Gi PVC. An init container cleans up stale lock files from previous ungraceful shutdowns to prevent startup failures. Credentials stored in Kubernetes secrets.
- **ActiveMQ** — Internal message bus using STOMP protocol for routing telemetry events between components.
- **iDRAC Telemetry Receiver** — Collects hardware telemetry from Dell PowerEdge iDRAC interfaces via Redfish API. Enables all 37 supported telemetry reports. Supports iDRAC 9 and iDRAC 10. Parallel processing for performance.
- **KafkaPump** (conditional) — Publishes telemetry data to the Kafka "idrac" topic using mTLS. Deployed only when "kafka" is in the collection type.
- **VictoriaPump** (conditional) — Exposes iDRAC metrics as a Prometheus endpoint on port 2112, scraped by vmagent. Deployed only when "victoria" is in the collection type.

The collection type is configurable: "victoria" only, "kafka" only, or "victoria,kafka" (recommended dual-write). Before deployment, all BMC (iDRAC) IP addresses in the inventory are validated for reachability from the service cluster. After deployment, a telemetry report is generated documenting the status of each iDRAC endpoint.

### 5.4.2 Internal Data Flow

- iDRAC endpoints (Redfish) → Receiver → ActiveMQ (STOMP) → VictoriaPump (:2112) → vmagent → vminsert
- iDRAC endpoints (Redfish) → Receiver → ActiveMQ (STOMP) → KafkaPump → Kafka (topic: idrac, mTLS :9093)
- Both paths active simultaneously when collection_type = "victoria,kafka"

### 5.4.3 Configuration Processing

- idrac_telemetry_support: true/false (default: true)
- idrac_telemetry_collection_type: "victoria" | "kafka" | "victoria,kafka" (default: "victoria,kafka")
- Conditional containers: KafkaPump deployed only if "kafka" in type; VictoriaPump only if "victoria" in type
- BMC IPs: validated from pxe_mapping_file.csv and OpenChami nodes.yaml
- MySQL credentials: stored in Kubernetes Secret

### 5.4.4 System Interfaces

- VictoriaPump Prometheus endpoint: port 2112 (/metrics)
- Redfish API: HTTPS to each iDRAC endpoint
- Kafka producer: mTLS to Kafka broker :9093
- MySQL: internal to StatefulSet pod (port 3306)
- ActiveMQ STOMP: internal to StatefulSet pod

### 5.4.5 Failure Modes and Recovery

- iDRAC endpoint unreachable: logged in telemetry report; other endpoints unaffected.
- MySQL PVC loss: requires re-initialisation of iDRAC telemetry configuration.
- MySQL stale lock: init container auto-cleans on pod restart.
- KafkaPump failure: VictoriaPump path continues independently (and vice versa).
- Pod crash: StatefulSet controller restarts; MySQL data persists on PVC.

## 5.5 LDMS In-Band Metric Collection

### 5.5.1 Internal System Behavior

The following diagram shows the LDMS framework architecture, including the LDMSd Aggregator, LDMSd Storage, and Kafka Pump deployed on Service Kubernetes workers.

![LDMS Framework Architecture](../images/ldms_flow.png)

*Figure 2: LDMS Framework Architecture (Aggregator, Storage, Kafka Pump).*



LDMS provides in-band OS-level metric collection from HPC compute nodes. LDMSd producers (samplers) run on all monitored compute nodes — Slurm controllers, workers, and login nodes. Each sampler binds to a configurable port (default 10001, range 10001-10100) and collects metrics at a configurable interval (default 1 second, specified in microseconds).

The aggregator framework is deployed on Service Kubernetes workers via a Helm chart and consists of:

- **LDMSd Aggregator** (StatefulSet) — Subscribes to groups of LDMSd producers and collects their metric streams (port 6001).
- **LDMSd Storage** (StatefulSet) — Subscribes to supported metric themes across all aggregators and persists data (port 6001).
- **Kafka Pump** — Publishes aggregated metric data to the Kafka "ldms" topic.

Supported sampler plugins: meminfo (memory), procstat2 (process stats), vmstat (virtual memory), loadavg (system load), procnetdev2 (network interfaces), slurm_sampler (HPC workload). Authentication uses Munge and OVIS auth. Samplers are deployed statelessly on compute nodes during provisioning via the provisioning system (OpenChami).

When compute nodes are added or removed (detected via PXE mapping file changes), the LDMS aggregator pod is automatically restarted to pick up the new topology.

### 5.5.2 Internal Data Flow

Compute nodes (samplers :10001) → LDMSd Aggregator (:6001, LDMS protocol) → LDMSd Storage (:6001) → Kafka Pump → Kafka (topic: ldms, mTLS) → Vector → vminsert

### 5.5.3 Configuration Processing

- ldms_support: auto-detected from software_config.json (not user-set)
- ldms_agg_port: 6001 (range 6001-6100)
- ldms_store_port: 6001 (range 6001-6100)
- ldms_sampler_port: 10001 (range 10001-10100)
- ldms_sampler_configurations: list of {plugin_name, config_parameters, activation_parameters}
- Activation format: "interval= [offset=]"
- slurm_sampler requires: component_id, stream, job_count, task_count in config_parameters
- procnetdev2 supports optional ifaces parameter (comma-separated interface names)
- Sampler config generated from telemetry_config.yml and applied via the provisioning system (OpenChami) during provisioning
- Helm chart values.yaml generated for aggregator framework

### 5.5.4 System Interfaces

- LDMS sampler port: 10001 (configurable, range 10001-10100)
- LDMS aggregator port: 6001 (configurable, range 6001-6100)
- Kafka producer: mTLS to Kafka broker
- Munge auth: shared key distributed via Kubernetes Secret
- NFS: sampler configuration files distributed via shared NFS mount

### 5.5.5 Failure Modes and Recovery

- Sampler failure on compute node: aggregator skips that producer; other nodes unaffected.
- Aggregator pod crash: Helm-managed StatefulSet restarts; metric gap during downtime.
- PXE mapping change detection: automatic aggregator restart to pick up topology.
- Kafka unavailable: Kafka Pump buffers in memory; data loss if pod restarts during outage.

## 5.6 SFM Telemetry Integration

### 5.6.1 Internal System Behavior

SFM telemetry integration is a semi-manual process. Omnia provides a utility playbook (external_victoria_connect_details.yml) that retrieves VictoriaMetrics LoadBalancer IPs and CA certificate from the Service Kubernetes cluster. The operator then manually configures the SFM UI to enable Prometheus remote_write.

The playbook writes connection details to /opt/omnia/telemetry/external_victoria_connect_details.yml and saves the CA certificate at /opt/omnia/telemetry/victoria-certs/ca.crt. It also generates /etc/hosts entry strings for the SFM Prometheus pod.

The operator must: (1) configure SFM UI Observability settings with remote_write URL and CA cert, (2) SSH into the SFM VM, access Debug Menu > Secure Shell, exec into the Prometheus pod, and add /etc/hosts entries mapping the vminsert DNS name to the LoadBalancer IP. The /etc/hosts entry is ephemeral — it is lost if the SFM Prometheus pod restarts.

### 5.6.2 Internal Data Flow

SFM Prometheus (embedded) → remote_write HTTPS → vminsert LoadBalancer:8480 (TLS, CA cert validation)

### 5.6.3 Configuration Processing

- Playbook output: vminsert/vmselect LoadBalancer IPs, CA certificate path
- SFM UI settings: Enable=ON, URL=vminsert write endpoint, Message Version=v1, TLS Config=upload ca.crt
- /etc/hosts mapping: vminsert.telemetry.svc.cluster.local → LoadBalancer IP
- Prerequisite: pod_external_ip_range set in omnia_config.yml and reachable from SFM network

### 5.6.4 System Interfaces

- vminsert LoadBalancer: port 8480 (Prometheus remote_write, TLS)
- vmselect LoadBalancer: port 8481 (PromQL queries, VMUI)
- SFM SSH: admin user via SSH to SFM VM

### 5.6.5 Failure Modes and Recovery

- SFM Prometheus pod restart: /etc/hosts entry lost; operator must re-apply manually. Kubernetes ExternalName service is a persistent alternative.
- Certificate mismatch: TLS handshake failure; operator must re-upload correct CA cert.
- vminsert LoadBalancer unreachable from SFM network: no metrics flow; requires network configuration.

## 5.7 OME Telemetry Integration

### 5.7.1 Internal System Behavior

OME telemetry integration is a semi-manual process. Omnia provides a utility playbook (external_kafka_connect_details.yml) that retrieves the Kafka LoadBalancer external IP and extracts mTLS certificates (CA cert, client cert, client key) from the Service Kubernetes cluster.

The playbook writes connection details to /opt/omnia/telemetry/external_kafka_connect_details.yml and saves TLS files in /opt/omnia/telemetry/external_kafka/ (ca.crt, user.crt, user.key). The operator then generates a .pfx client certificate and configures the OME UI.

OME UI configuration: Configuration > Remote Connectivity > Enable Kafka Connectivity. Set bootstrap server to Kafka LoadBalancer IP:9094, authentication mode SSL, upload ca.crt as server cert and user.pfx as client cert. Select metrics and device groups to stream. Connectivity verified by green checkmark in OME UI.

OME publishes telemetry data to Kafka via the external mTLS listener on port 9094. Metrics are organised under OME-prefixed topic names and are consumable via the Kafka Bridge HTTP REST interface on port 8080.

### 5.7.2 Internal Data Flow

OME → Kafka external listener :9094 (mTLS, LoadBalancer) → Kafka broker → Kafka Bridge :8080 (HTTP REST, for verification)

### 5.7.3 Configuration Processing

- Playbook output: Kafka LoadBalancer IP, CA cert, client cert, client key
- Operator generates: user.pfx from user.crt + user.key (openssl pkcs12)
- OME UI: Enable Kafka, bootstrap server, SSL auth, server cert upload, client cert upload
- OME selects: specific metrics to stream, device groups
- Prerequisite: pod_external_ip_range reachable from OME appliance network

### 5.7.4 System Interfaces

- Kafka external listener: port 9094 (mTLS, LoadBalancer)
- Kafka Bridge: port 8080 (HTTP REST, for consuming OME data)
- Certificate artifacts: ca.crt, user.crt, user.key, user.pfx

### 5.7.5 Failure Modes and Recovery

- Certificate mismatch: mTLS handshake failure; re-extract certs via playbook.
- Kafka LoadBalancer unreachable from OME: no data flow; requires network configuration.
- OME on different system than OIM: certificates must be manually copied before upload.

## 5.8 VictoriaLogs Cluster Mode

### 5.8.1 Internal System Behavior

VictoriaLogs is deployed in cluster mode within the telemetry namespace, consisting of three component types:

- **vlstorage** — Persistent log storage.
- **vlinsert** — Log ingestion and sharding.
- **vlselect** — Log query and aggregation.

Two ingestion paths are supported:

- **Path A — Real-time syslog:** External devices (UFM, Skyway, PowerScale, VAST) send syslog messages to VLAgent, which forwards them to vlinsert.
- **Path B — Kafka-buffered events:** iDRAC events and control plane logs published to Kafka, consumed by Vector, routed to vlinsert.

Supported ingestion formats: JSON Lines, syslog RFC 5424, Elasticsearch bulk API. TLS enforced for all in-cluster traffic; mTLS for external access. VLAgent dual-writes to VictoriaLogs (internal) and configurable external destinations. Cleanup is independent — VictoriaLogs can be removed without affecting VictoriaMetrics or Kafka.

Shares TLS certificate infrastructure with VictoriaMetrics.

### 5.8.2 Internal Data Flow

- External syslog → VLAgent (syslog receiver) → vlinsert → vlstorage
- Kafka topics → Vector (consumer) → vlinsert → vlstorage
- Query: client → vlselect → fan-out to vlstorage → merge → return
- VLAgent: dual-write to vlinsert (internal) + external destination

### 5.8.3 Configuration Processing

- Deployment mode: cluster (production) or single-node
- Storage: persistent volumes for vlstorage
- Retention: configurable log retention period
- TLS: shared certificate infrastructure with VictoriaMetrics
- VLAgent: configurable external destination endpoint

### 5.8.4 System Interfaces

- vlinsert: log ingestion endpoint (JSON Lines, syslog RFC 5424, ES bulk API)
- vlselect: log query endpoint
- VLAgent: syslog receiver (RFC 5424)

**Cluster Mode Resource Details (Q2):** vlstorage: 2 replicas (StatefulSet), 8 Gi PVC each (16 Gi total), 1 Gi/2 Gi memory, 250 m/1000 m CPU. vlinsert: 2 replicas (Deployment), LoadBalancer port 9481. vlselect: 2 replicas (Deployment), LoadBalancer port 9491. Total pod count: 6. Estimated: 8 Gi RAM, 4 CPU at 500-node scale. Storage: ~70 GB for 7-day retention at 500 nodes; ~350 GB at 2,000 nodes.

### 5.8.5 Failure Modes and Recovery

- vlstorage failure: log ingestion continues to buffer; queries degraded.
- VLAgent failure: syslog messages lost until restart; external devices may buffer.
- External destination unreachable: internal ingestion continues independently.

## 5.9 Kafka to VictoriaMetrics/VictoriaLogs Ingestion via Vector

### 5.9.1 Internal System Behavior

Vector is deployed as a single-replica Deployment in the telemetry namespace. Resource allocation: 512 Mi memory request / 1 Gi limit, 250 m CPU request / 1000 m limit. No PVC required (stateless consumer with in-memory buffering). Vector acts as a Kafka consumer that bridges the streaming bus to both the time-series database and log database. It consumes telemetry data from Kafka topics and writes metrics to VictoriaMetrics via Prometheus remote_write and events/logs to VictoriaLogs.

The primary data source is LDMS (iDRAC already writes directly via VictoriaPump). Vector dynamically discovers new Kafka topics matching the naming convention and begins consuming within 60 seconds of topic creation.

Vector splits metrics from events based on content type, enabling a single Kafka-to-observability pipeline serving both backends. Configurable transforms support schema normalisation and metric enrichment.

### 5.9.2 Internal Data Flow

- Kafka (topics: idrac, ldms, OME-*) → Vector (Kafka consumer, mTLS) → remote_write → vminsert:8480
- Kafka (event topics) → Vector → forward → vlinsert

### 5.9.3 Configuration Processing

- Kafka source: consumer group, topic pattern matching
- Dynamic topic discovery: new topics consumed within 60 seconds
- Transforms: content-type-based split (metrics vs events)
- Sinks: Prometheus remote_write (VictoriaMetrics), log forward (VictoriaLogs)
- Topic naming convention enforced by producers

### 5.9.4 System Interfaces

- Kafka consumer: mTLS connection to Kafka brokers
- VictoriaMetrics: remote_write to vminsert:8480
- VictoriaLogs: forward to vlinsert

### 5.9.5 Failure Modes and Recovery

- Kafka unavailable: Vector retries with backoff; no data loss if Kafka recovers within retention period.
- vminsert unavailable: Vector buffers and retries; metrics delayed but not lost.
- Schema change in LDMS/iDRAC: Vector transforms may break (HIGH risk). Mitigation: version-pinned schema definitions.
- Pipeline failure: Vector exposes self-metrics for monitoring.

## 5.10 NVIDIA DCGM GPU Metrics

### 5.10.1 Internal System Behavior

The NVIDIA DCGM daemon (nv-hostengine) and DCGM Exporter are installed as OS-level daemon services on every compute node with NVIDIA GPUs. DCGM packages (datacenter-gpu-manager) are included in the golden image for GPU functional groups and served from the Omnia local Pulp repository for air-gapped environments.

GPU detection: during provisioning, presence of NVIDIA GPUs is detected (via GPU hardware detection during the provisioning process). DCGM is installed ONLY on nodes with GPUs detected; non-GPU nodes skip gracefully. An inventory-level toggle (dcgm_enabled in software_config.json) allows enable/disable without rebooting nodes.

DCGM Exporter provides a Prometheus-compatible HTTP endpoint on port 9400 that LDMS samplers scrape to collect GPU metrics alongside standard OS metrics. Supported GPU architectures: Blackwell (B100/B200/GB200), Hopper (H100/H200), Ampere (A100) on both x86_64 and aarch64.

Key metrics: GPU_UTIL (utilisation %), FB_USED/FB_FREE (framebuffer memory), GPU_TEMP (temperature), POWER_USAGE (watts), XID_ERRORS (hardware errors), NVLINK_BANDWIDTH_TOTAL (interconnect). Per-functional-group configuration supports different GPU monitoring profiles across heterogeneous node types.

### 5.10.2 Internal Data Flow

DCGM Exporter (:9400, Prometheus /metrics) → LDMS sampler scrape → LDMS Aggregator → LDMS Storage → Kafka Pump → Kafka (topic: ldms) → Vector → vminsert

### 5.10.3 Configuration Processing

- dcgm_enabled: true/false in software_config.json
- DCGM version: configurable via software_config.json (default: latest stable)
- Per-functional-group configuration supported
- Packages: sourced from Pulp local repository (air-gapped)
- OS service: nvidia-dcgm, auto-restart on failure (max 3 retries), managed by the host init system

### 5.10.4 System Interfaces

- DCGM Exporter: port 9400 (Prometheus /metrics)
- DCGM daemon: nv-hostengine (localhost:5555, not exposed externally)
- LDMS sampler: scrapes DCGM Exporter endpoint

### 5.10.5 Failure Modes and Recovery

- Missing GPU driver: provisioning fails fast with clear error message (prerequisite check).
- DCGM daemon crash: systemd auto-restart (max 3 retries); logged to journal.
- Non-GPU node: DCGM packages not installed; no error.
- Blackwell/aarch64 packages unavailable: fallback to direct scraping if DCGM packages are unavailable (HIGH risk).

## 5.11 NVIDIA UFM InfiniBand Telemetry

### 5.11.1 Internal System Behavior

UFM telemetry collection is implemented via vmagent scrape job additions (no separate Deployment). A new scrape job entry is added to the vmagent ConfigMap targeting the UFM Prometheus exporter endpoint(s). VLAgent (Deployment, 1 replica) receives UFM syslog. Specifically, vmagent scrapes the UFM Prometheus exporter (port 9090) for metrics, and VLAgent receives UFM syslog events for log storage in VictoriaLogs.

Deployment supports UFM Enterprise ≥6.15.x in HA configuration (active/standby pair). Estimated cardinality: approximately 800,000 active time series (2 appliances × 2,000 IB ports × ~200 metrics per port). Labels preserve device/port identity, GUIDs, and node/port names.

Dual-destination forwarding: metrics and logs sent to both internal observability stack and external Omni endpoint. Independent buffers ensure failure of one destination does not block the other. During UFM HA failover, metrics continue from surviving appliance within 2 scrape intervals.

### 5.11.2 Internal Data Flow

- UFM Prometheus exporter (:9090) → vmagent scrape (15-30s) → remote_write → vminsert:8480 (internal) + Omni endpoint (external)
- UFM syslog → VLAgent (syslog receiver) → vlinsert (internal) + external log store

### 5.11.3 Configuration Processing

- vmagent scrape job: targeting UFM exporter endpoint(s)
- Scrape interval: 15-30 seconds configurable
- Dual remote_write: internal vminsert + external Omni endpoint
- VLAgent: syslog receiver with dual-destination forwarding
- Labels: device GUID, port name, switch name preserved via relabel rules

### 5.11.4 System Interfaces

- UFM Prometheus exporter: port 9090
- vmagent remote_write: vminsert:8480 (internal), Omni endpoint (external)
- VLAgent syslog: RFC 5424 from UFM

### 5.11.5 Failure Modes and Recovery

- UFM HA failover: metrics continue from surviving appliance within 2 scrape intervals.
- External Omni endpoint down: internal ingestion continues; buffered data delivered on recovery.
- High cardinality (>800K series): may impact VictoriaMetrics. Mitigation: relabeling rules to drop high-churn metrics.
- UFM exporter schema change across versions: version pinning required.

## 5.12 NVIDIA NetQ Ethernet Telemetry

### 5.12.1 Internal System Behavior

NetQ telemetry collection is implemented via vmagent scrape job additions (no separate Deployment). VLAgent receives rsyslog events. Specifically, NetQ telemetry collection is implemented via vmagent scrape job additions (no separate Deployment). VLAgent receives rsyslog events. Specifically, vmagent scrapes the NetQ PromQL/Prometheus API endpoint with a scrape interval matching NetQ's 10-second storage cadence (10-20 seconds configurable). Rsyslog events are collected via VLAgent. Up to 4 NetQ appliances supported with total cardinality up to 2 million time series.

Metric domains: interface/link statistics, DOM optics, system resource utilisation, environmental sensors (fans, PSUs, temperatures), node health, per-process/per-device network counters. Labels preserve device, port, role, VRF/VNI, tenant, and hostname context.

4-hour on-disk buffer provides resilience during destination outages. Dual-destination delivery to internal and external endpoints.

### 5.12.2 Internal Data Flow

- NetQ PromQL API → vmagent scrape (10-20s) → remote_write → vminsert (internal) + Omni (external)
- NetQ rsyslog → VLAgent → vlinsert (internal) + external log store

### 5.12.3 Configuration Processing

- Scrape interval: 10-20 seconds (aligned to NetQ 10s cadence)
- Up to 4 NetQ appliances
- 4-hour on-disk buffer for outage resilience
- Kafka integration optional (Phase 2)
- Dual remote_write configuration

### 5.12.4 System Interfaces

- NetQ PromQL API endpoint
- vmagent remote_write: vminsert (internal) + Omni (external)
- VLAgent: rsyslog receiver

### 5.12.5 Failure Modes and Recovery

- NetQ appliance down: vmagent logs scrape failure; other appliances unaffected.
- Destination outage: 4-hour buffer prevents data loss.
- NetQ PromQL schema change across versions: may require scrape config updates.

## 5.13 NVIDIA Skyway IB-to-Ethernet Telemetry

### 5.13.1 Internal System Behavior

Skyway telemetry collection requires a dedicated SNMP poller Deployment (1 replica, 256 Mi memory, 250 m CPU) in the telemetry namespace. VLAgent receives syslog events. The SNMP poller collects data via SNMPv3 polling (authPriv security level) of IF-MIB and MLNX-OS/Skyway MIBs for port statistics and system health. Syslog events forwarded to VLAgent. Supports up to 32 gateways with up to 128 ports each (4,096 total ports). Poll interval 15-30 seconds configurable with 30-minute memory ring buffer for outage resilience.

Metric domains: port bytes/packets, errors, discards, CRC, link state, speed, system temperature, fan/PSU status, alarms, CPU/memory. Optional SNMP trap feature (toggle-controlled). Unsupported OIDs reported in status output without failing pipeline. Port subsets can be configured to manage metric volume at scale. Dual-destination delivery.

### 5.13.2 Internal Data Flow

- Skyway SNMP (IF-MIB + MLNX-OS MIBs, SNMPv3 authPriv) → SNMP poller → vminsert (internal) + Omni (external)
- Skyway syslog → VLAgent → vlinsert (internal) + external log store
- Optional: SNMP traps → event notification

### 5.13.3 Configuration Processing

- SNMPv3: authPriv security level
- Poll interval: 15-30 seconds configurable
- Port subset selection: configurable to manage volume
- SNMP trap toggle: enable/disable
- 30-minute memory ring buffer
- Dual-destination remote_write

### 5.13.4 System Interfaces

- SNMP: SNMPv3 to gateway management interfaces
- Syslog: from Skyway to VLAgent
- Optional: SNMP traps

### 5.13.5 Failure Modes and Recovery

- Unsupported OIDs: reported in status without failing collection.
- Firmware version differences: OID inventory per firmware version required.
- Gateway unreachable: logged; other gateways unaffected.
- Destination outage: 30-minute ring buffer prevents data loss.

## 5.14 PowerVault ME5 Storage Telemetry

### 5.14.1 Internal System Behavior

PowerVault ME5 telemetry collection requires a dedicated collector Deployment (1 replica, 512 Mi memory, 250 m CPU) in the telemetry namespace. The collector communicates with ME5 arrays via Redfish API (preferred) with CLI fallback for metrics not available through Redfish. Up to 16 arrays (32 endpoints). Sampling interval 30-60 seconds.

Metrics: read/write IOPS, throughput, latency (average and max), queue depth, cache utilisation, destage statistics, capacity (free/used per pool/volume), component health (controllers, disks, PSUs, fans, temperatures). Event logs: CLI collection for Critical, Error, Warning, Informational, and Resolved severity levels.

Independent feature toggles for metrics and event log collection. Credentials managed securely with zero plaintext exposure in logs or configs. Collector exports self-health metrics for monitoring. Dual-destination remote_write to internal VictoriaMetrics and external Omni endpoint.

### 5.14.2 Internal Data Flow

- ME5 Redfish API / CLI → collector → remote_write → vminsert (internal) + Omni (external)
- ME5 CLI event logs → collector → vlinsert (internal) + external log store

### 5.14.3 Configuration Processing

- Redfish API preferred; CLI fallback for missing metrics
- Sampling interval: 30-60 seconds
- Independent toggles: metrics enable/disable, events enable/disable
- Up to 16 arrays (32 endpoints)
- Credentials: secured (no plaintext in logs)
- Dual-destination configuration

### 5.14.4 System Interfaces

- ME5 Redfish API: HTTPS to array management controllers
- ME5 CLI: SSH/serial for event logs and fallback metrics
- Collector remote_write: vminsert + Omni
- Collector self-metrics: Prometheus /metrics endpoint

### 5.14.5 Failure Modes and Recovery

- Redfish coverage below 90%: automatic CLI fallback for missing metrics.
- ME5 session throttling: collector respects concurrent session limits.
- Array unreachable: logged; other arrays unaffected.
- Destination outage: independent buffers per destination.

## 5.15 PowerScale Storage Telemetry

### 5.15.1 Internal System Behavior

PowerScale telemetry collection ingests metrics via *Dell CSM Metrics for PowerScale* with an OpenTelemetry Collector, and ingests logs/events via the existing syslog → VLAgent → vlinsert path. TLS is enforced for all off-cluster communications; Kubernetes-native service-account authentication secures the metrics scrape path (no mTLS handshake required).

**Metrics path:** Dell CSM Metrics for PowerScale is deployed via Helm charts on the service Kubernetes cluster. It queries the PowerScale OneFS API and emits metrics covering IOPS, throughput, latency, capacity, cluster health, and topology. An OpenTelemetry Collector instance receives these metrics and exposes a Prometheus-compatible endpoint. vmagent scrapes the OpenTelemetry Collector endpoint with TLS and Kubernetes service-account authentication, then forwards metrics to vminsert via Prometheus remote_write.

**Two deployment modes** are supported for the CSM Metrics + OpenTelemetry Collector stack:

- **Omnia-orchestrated (service cluster):** Omnia deploys CSM Metrics, the OpenTelemetry Collector, the CSI Driver for Dell PowerScale, and cert-manager on the service Kubernetes cluster and manages their lifecycle.
- **Operator-provided endpoint:** CSM Metrics and the OpenTelemetry Collector run on an external Kubernetes cluster managed by the operator. The operator provides the Prometheus endpoint URL. Omnia configures vmagent to scrape that external endpoint; no CSM Metrics or OTel Collector pods are deployed on the service cluster.

A single PowerScale cluster is supported per Omnia deployment. Metrics are labelled to distinguish PowerScale data from other sources in VictoriaMetrics using existing naming/label conventions.

**Logs/events path:** PowerScale syslog events flow through the existing pipeline: PowerScale → VLAgent (syslog receiver) → vlinsert. Labels include host/cluster, severity, and facility.

**Feature toggles:** Independent feature flags allow PowerScale metrics and PowerScale logs/events to be enabled or disabled separately.

**Operational health indicators:** The integration exposes scrape success/error counters, ingest latency, and error rates for both the metrics and log paths, enabling operators to monitor the health of the PowerScale telemetry pipeline itself.

**Dual-destination delivery:** When an external Omni observability endpoint is configured, metrics are sent to both internal VictoriaMetrics and the external endpoint. Independent buffers ensure failure of one destination does not block the other.

### 5.15.2 Internal Data Flow

- **Metrics:** Dell CSM Metrics for PowerScale → OpenTelemetry Collector (Prometheus endpoint) → vmagent scrape (TLS, K8s service-account auth) → vminsert (internal) + Omni (external, when configured)
- **Logs/events:** PowerScale syslog → VLAgent → vlinsert (internal) + external log store (when configured)

### 5.15.3 Configuration Processing

- **Deployment mode:** Omnia-orchestrated or operator-provided endpoint, configurable in telemetry_config.yml
- **Omnia-orchestrated mode:** CSM Metrics Helm values, CSI Driver configuration, cert-manager issuer, OpenTelemetry Collector Prometheus scrape endpoint—all provisioned automatically
- **Operator-provided mode:** Operator supplies the OpenTelemetry Collector Prometheus endpoint URL; Omnia adds a vmagent scrape job targeting that URL
- **Authentication:** TLS with Kubernetes service-account token for the scrape path. No mTLS required on the PowerScale side.
- Single PowerScale cluster per deployment
- Independent feature flags: `powerscale_metrics_enabled`, `powerscale_logs_enabled` (both true/false)
- Scrape interval: 30–60 seconds configurable (default aligned with CSM Metrics emission cadence)
- Retention: governed by VictoriaMetrics retention settings (default 7–30 days)
- Dual-destination: `external_omni_endpoint` (URL, optional)

### 5.15.4 System Interfaces

- **CSM Metrics → OpenTelemetry Collector:** internal service communication within the telemetry namespace
- **OpenTelemetry Collector Prometheus endpoint:** scraped by vmagent (TLS, K8s service-account auth)
- **vmagent remote_write:** vminsert (internal, port 8480) + Omni endpoint (external, when configured)
- **VLAgent:** syslog receiver (RFC 5424) from PowerScale; forwards to vlinsert
- **Operational health endpoint:** self-metrics exposed for scrape success rate, error counters, ingest latency

### 5.15.5 Dependencies

- **Omnia-orchestrated mode:**CSI Driver for Dell PowerScale (needs installation)
- cert-manager (needs installation)
- OpenTelemetry Collector (needs deployment)
- Dell CSM Metrics for PowerScale Helm charts

**Both modes:**- Service Kubernetes cluster (available)
- VictoriaMetrics + vminsert (deployed)
- vmagent (operational)
- VLAgent / VictoriaLogs (existing log pipeline)
- Kafka (if needed for log pipeline)

### 5.15.6 Assumptions

- Kubernetes cluster available for CSM Metrics deployment (high confidence)
- PowerScale CSI driver installed and configured (high)
- Single PowerScale cluster per Omnia environment (high)
- CSM Metrics metric set covers required observability signals including topology (high)
- Existing syslog/VLAgent/vlinsert protocols in Omnia are sufficient for PowerScale logs/events (medium)
- A 30–60 s scrape interval and 7–30 day retention are acceptable for storage telemetry (medium)

### 5.15.7 Failure Modes and Recovery

- **CSM Metrics pod failure:** Metrics emission stops until pod restarts; K8s Deployment controller auto-restarts. No data loss—vmagent simply has no new samples to scrape.
- **OpenTelemetry Collector failure:** Metrics flow from CSM Metrics to vmagent stops until pod restarts; K8s auto-restart via Deployment controller.
- **vmagent scrape failure:** vmagent retries at the next scrape interval; operational health metrics (scrape error counters) surface the issue.
- **TLS / certificate misconfiguration:** Kubernetes service-account authentication failures are logged; health metrics expose the error. Common integration issue—clear error messaging required.
- **External Omni endpoint down:** Internal VictoriaMetrics ingestion continues unaffected; buffered data delivered to Omni on recovery.
- **VLAgent failure:** Syslog messages lost until restart; metrics path is unaffected.
- **PowerScale unreachable:** CSM Metrics logs connection error; no metrics emitted. Other telemetry sources unaffected.

## 5.16 VAST Storage Telemetry

### 5.16.1 Internal System Behavior

VAST telemetry collection is implemented via vmagent multi-scrape job additions (no separate Deployment). VLAgent receives VAST syslog. Metrics are collected by scraping VAST Prometheus exporter domain endpoints via vmagent with multi-scrape jobs and multi-remote_write queues. By default, individual domain endpoints are scraped rather than the /all endpoint to manage metric volume at scale.

Available endpoints: /api/prometheusmetrics/ (cluster/CNode/per-protocol performance, hardware state), /views, /users, /quotas, /devices, /defrag, /alarms, /switches and /user_connections (VAST 5.2.2+). Operators can configure endpoint inclusion/exclusion; /all enabled for smaller clusters.

Supports up to 4 VAST clusters with up to 512 CNodes total. Estimated cardinality: ≤500,000 time series per cluster. Scrape interval 30-60 seconds configurable. VAST 5.2.2+ required (5.1.x best-effort). HTTPS with credentials stored securely.

Syslog events (system activities, alarms, protocol audit logs) forwarded to VLAgent. Dual-destination delivery with independent buffers. Collector exports self-metrics for health monitoring.

### 5.16.2 Internal Data Flow

- VAST /api/prometheusmetrics/* → vmagent multi-scrape (HTTPS) → remote_write → vminsert (internal) + Omni (external)
- VAST syslog → VLAgent → vlinsert (internal) + external log store

### 5.16.3 Configuration Processing

- Domain endpoints: configurable include/exclude list
- /all endpoint: optional for smaller clusters
- Scrape interval: 30-60 seconds
- Up to 4 VAST clusters, 512 CNodes
- VAST 5.2.2+ required
- Credentials: stored in secure vault
- Dual-destination remote_write

### 5.16.4 System Interfaces

- VAST Prometheus exporter: /api/prometheusmetrics/* (HTTPS)
- vmagent multi-scrape: multiple jobs per VAST cluster
- VLAgent: syslog receiver

### 5.16.5 Failure Modes and Recovery

- VAST API change between versions: version pinning and regression testing required.
- /api/prometheusmetrics/all endpoint: high cardinality on large clusters, particularly /user_connections. Mitigation: domain-specific endpoints by default.
- Destination outage: independent buffers per destination.
- VAST 5.1.x: best-effort support, degraded metric coverage.

---

# 6 Cross-Feature System Behaviors

## 6.1 TLS/mTLS Certificate Management

The telemetry subsystem manages two separate certificate chains:

- **VictoriaMetrics TLS:** Self-signed CA certificate generated during deployment (10-year validity). SANs cover all service DNS names (vminsert.telemetry.svc.cluster.local, vmselect.telemetry.svc.cluster.local, etc.). Stored as Kubernetes Secret in telemetry namespace.
- **Kafka mTLS:** Managed by Strimzi operator. Cluster CA for server authentication; per-user client certificates for mutual authentication. External clients (OME) use .pfx format certificates.

In-cluster traffic uses TLS (server authentication). Off-cluster traffic uses mTLS (mutual authentication) for Kafka; TLS with CA validation for VictoriaMetrics.

## 6.2 Dual-Destination Data Delivery Pattern

New Q2 features (UFM, NetQ, Skyway, PowerVault, PowerScale, VAST) implement a consistent dual-destination pattern:

- Internal destination: VictoriaMetrics (metrics) + VictoriaLogs (logs) within Service K8s cluster
- External destination: Omni observability endpoint (customer-configurable)
- Independent buffers/queues per destination
- Failure isolation: one destination down does not block the other
- Recovery: buffered data delivered without loss when destination recovers
- Agent self-metrics exposed for monitoring delivery health

## 6.3 Feature Flag Processing and Conditional Deployment

The telemetry subsystem uses a layered feature flag system. CY26 Q2 introduces additional feature flags for new components:

- **Primary flags** (user-set): idrac_telemetry_support (true/false), idrac_telemetry_collection_type (victoria|kafka|victoria,kafka)
- **Auto-detected flags:** ldms_support (from software_config.json)
- **Computed flags:** kafka_support = (kafka in collection_type OR ldms_support), victoria_cluster.enabled = (deployment_mode == cluster)
- **New Q2 flags:** victorialogs_enabled (true/false), vector_enabled (true/false), dcgm_enabled (true/false, per-functional-group), ufm_telemetry_enabled, netq_telemetry_enabled, skyway_telemetry_enabled, powervault_telemetry_enabled, powerscale_telemetry_enabled, vast_telemetry_enabled (all true/false), external_omni_endpoint (URL, optional, enables dual-destination)
- **New Q2 flags:** victorialogs_enabled (true/false), vector_enabled (true/false), dcgm_enabled (true/false, per-functional-group), ufm_telemetry_enabled, netq_telemetry_enabled, skyway_telemetry_enabled, powervault_telemetry_enabled, powerscale_telemetry_enabled, vast_telemetry_enabled (all true/false), external_omni_endpoint (URL, optional, enables dual-destination)

Five deployment scenarios:

- iDRAC + Victoria only: VictoriaMetrics, iDRAC receiver, vmagent, MySQL, ActiveMQ
- iDRAC + Kafka only: Kafka, iDRAC receiver, MySQL, ActiveMQ
- iDRAC + LDMS + Both: All components
- LDMS only: Kafka, LDMS aggregator
- Disabled: No telemetry components

## 6.4 Cleanup and Maintenance

- VictoriaMetrics: selective cleanup script removes VM components without affecting Kafka or other services
- VictoriaLogs: independent cleanup from VictoriaMetrics
- Kafka: topic retention (default 7 days) and log segment management (1 GB segments, 5-minute checks)
- LDMS: aggregator pod automatic restart on PXE mapping topology changes
- Pod cleanup: CronJob for telemetry namespace maintenance

---


