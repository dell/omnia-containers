# Omnia Telemetry — Behaviour Specification (BSpec)

**Document ID:** BSPEC-TELEM-2026-001
**Version:** 2.2
**Date:** 2026-04-27
**Status:** Approved
**Author:** Ravishankar N

**Revision History:**

| Version | Date | Changes | Author |
|---------|------|---------|--------|
| 0.1 | 2026-03-23 | Initial draft | Ravishankar N |
| 1.0 | 2026-03-23 | Complete rewrite covering full telemetry and monitoring scope | Ravishankar N |
| 2.0 | 2026-03-30 | SDD-aligned rewrite — separated customer-facing behavior from internal system behavior (moved to Functional Spec FSPEC-TELEM-2026-001) | Ravishankar N |
| 2.2 | 2026-03-31 | Rewrote Section 5.15 (PowerScale Storage Telemetry) from scratch per Capability 19101: CSM Metrics for PowerScale + OpenTelemetry Collector as sole metrics architecture; removed legacy gostats/bearer-token references; two deployment modes; added topology metric category and Operational Health Visibility user story; dual-destination delivery; operational health monitoring; rewrote all acceptance criteria, constraints, performance, and assets at risk. Updated Section 5.16 (VAST Storage Telemetry) with enhanced multi-cluster support, endpoint domain selection, and detailed acceptance criteria. | Ravishankar N |

**SDD Phase:** Phase 2a — Behaviour Specification (parallel with Functional Spec)

**Companion Document:** Functional Specification FSPEC-TELEM-2026-001 (internal system behavior)

> **SDD Scope Boundary:** This document defines **customer interaction** — what operators see, configure, and observe. Internal system behavior (component topology, data routing, resource allocation, protocols) is documented in the Functional Specification.

---

## 1. References

| LOB | Type | Document Name | Description |
|-----|------|---------------|-------------|
| Global Large Enterprise | Confluence | Product Requirements Document (PRD) Omnia 2.x | Omnia PRD covering telemetry requirements |
| Dell Omnia | External Docs | Omnia v2.1.0.0-rc2 Documentation | Official release documentation |
| VictoriaMetrics | External Docs | VictoriaMetrics Cluster Mode | Upstream cluster deployment reference |
| VictoriaLogs | External Docs | VictoriaLogs Documentation | Upstream log management reference |
| NVIDIA | External Docs | NVIDIA DCGM Documentation | Data Center GPU Manager reference |

---

## 2. Glossary

| Term | Definition |
|------|-----------|
| **HPC** | High Performance Computing |
| **OIM** | Omnia Infrastructure Manager — central management host |
| **iDRAC** | Integrated Dell Remote Access Controller — out-of-band hardware management on Dell PowerEdge servers |
| **LDMS** | Lightweight Distributed Metric Service — in-band OS-level metric collection for HPC compute nodes |
| **VictoriaMetrics** | High-performance time-series database for metric storage and querying |
| **VictoriaLogs** | Centralised log management component of the VictoriaMetrics ecosystem |
| **vmagent** | VictoriaMetrics agent — metrics scraper and forwarder |
| **VLAgent** | VictoriaLogs agent — syslog receiver that forwards logs to VictoriaLogs |
| **Kafka** | Apache Kafka — distributed streaming platform used as a telemetry data bus |
| **Vector** | High-performance data pipeline tool for transforming and routing logs and metrics |
| **SFM** | Smart Fabric Manager — Dell management console for SONiC-based Ethernet switches |
| **OME** | OpenManage Enterprise — Dell server management and monitoring console |
| **UFM** | NVIDIA Unified Fabric Manager — management and monitoring platform for InfiniBand fabrics |
| **NetQ** | NVIDIA NetQ — Ethernet fabric monitoring and telemetry platform |
| **Skyway** | NVIDIA Skyway — InfiniBand-to-Ethernet gateway |
| **DCGM** | NVIDIA Data Center GPU Manager — daemon and exporter for GPU telemetry |
| **VAST** | VAST Data Platform — flash-based parallel storage cluster |
| **PowerScale** | Dell PowerScale — scale-out NAS storage platform (OneFS) |
| **PowerVault** | Dell PowerVault ME5 — SAN/DAS block storage array |
| **mTLS** | Mutual Transport Layer Security — both client and server authenticate via certificates |

---

## 3. Edit History

| **Revision** | **Date** | **Changes** | **Author** |
|---|---|---|---|
| 0.1 | 2026-03-23 | Initial draft | Ravishankar N |
| 1.0 | 2026-03-23 | Complete rewrite covering full telemetry scope | Ravishankar N |
| 2.0 | 2026-03-30 | Rewritten per SDD methodology; separated customer behavior from system internals | Ravishankar N |
| 2.2 | 2026-03-31 | Rewrote Section 6.15 (PowerScale Storage Telemetry) from scratch per Capability 19101: CSM Metrics for PowerScale + OpenTelemetry Collector as sole metrics architecture; removed legacy gostats/bearer-token references; two deployment modes; added topology metric category and Operational Health Visibility user story; dual-destination delivery; operational health monitoring; rewrote all acceptance criteria, constraints, performance, and assets at risk | Ravishankar N |

---

## 4. Overview

The Omnia Telemetry subsystem provides a unified, enterprise-grade observability platform purpose-built for Dell HPC, AI, and data-analytics clusters at scale. It collects, transports, stores, and exposes operational data—encompassing both time-series metrics and timestamped log/event records—from every major hardware and software domain in the cluster. The subsystem is designed to support environments of 2,000 or more compute nodes, delivering the throughput, reliability, and security characteristics demanded by mission-critical production workloads.

Telemetry data falls into two primary categories. **Metrics** are numeric time-series observations (for example, CPU utilization, GPU temperature, network port error counts, storage IOPS) that are collected at regular intervals and stored in a high-performance time-series database. **Logs and Events** are timestamped textual records (for example, hardware fault alerts, link-state changes, audit entries) that are ingested into a centralized log management database. Both categories flow through a common set of transport, storage, and query interfaces, giving operators a single pane of glass for cluster-wide observability.

From the operator's perspective, the telemetry subsystem delivers the following key capabilities: high-availability metric storage with no single point of failure, centralized log management with configurable retention, a reliable and encrypted streaming bus for data transport, TLS-secured communications across all data paths, fully automated deployment through the Omnia provisioning workflow, and support for air-gapped (disconnected) environments where internet access is unavailable. All telemetry data is queryable through industry-standard interfaces—PromQL for metrics and log-specific query languages for events—enabling integration with third-party dashboards, alerting systems, and analytical tools.

The subsystem collects data across five operational domains: **Hardware** (iDRAC out-of-band server telemetry), **Compute** (in-band OS-level and GPU metrics via LDMS and DCGM), **Network** (SFM for SONiC switches, OME for server management, UFM for InfiniBand, NetQ for Ethernet fabrics, and Skyway for IB-to-Ethernet gateways), and **Storage** (PowerVault ME5 block storage, PowerScale NAS, and VAST parallel storage). Each data source is independently configurable, allowing operators to enable only the telemetry domains relevant to their cluster topology.

### 4.1 Telemetry Data Sources and Paths

The following diagram illustrates the telemetry data source types and the transport paths used by each source. Mutual TLS (mTLS) secures all traffic between entities external to the service infrastructure, while TLS secures intra-cluster traffic.

*Figure 1: Data Source Types and Transport Paths (mTLS external, TLS internal).*

![Data Source Types and Transport Paths diagram](../images/telemetry_data_source_path.png)

The following table summarizes every supported data source, the path its metrics and logs follow through the telemetry subsystem, and the transport protocols employed.

| **Data Source** | **Metrics Path** | **Logs / Events Path** | **Transport Protocol** |
|---|---|---|---|
| iDRAC (Dell PowerEdge servers) | Collected and stored in time-series database; optionally published to streaming bus | Hardware events published to streaming bus, routed to log database | Secure management API, streaming protocols |
| LDMS (Compute nodes) | Sampled, aggregated, published to streaming bus, routed to time-series database | N/A | In-band collection protocol, streaming bus |
| SFM (SONiC switches) | Streamed to time-series database via metrics forwarding protocol | N/A | Metrics forwarding over HTTPS |
| OME (Server management) | Published to streaming bus via external secure listener | N/A | Streaming bus with mutual authentication |
| NVIDIA UFM (InfiniBand) | Scraped from metrics exporter, stored in time-series database | Syslog events forwarded to log database | Metrics scraping, syslog |
| NVIDIA NetQ (Ethernet) | Scraped from query API, stored in time-series database | Syslog events forwarded to log database | Query API, syslog |
| NVIDIA Skyway (IB-to-Eth) | Polled via management protocol, stored in time-series database | Syslog events forwarded to log database | Management polling, syslog |
| NVIDIA DCGM (GPUs) | GPU metrics collected via in-band sampler pipeline | N/A | Metrics endpoint, in-band collection |
| PowerVault ME5 (Block storage) | Collected via management API, stored in time-series database | Event logs collected and stored in log database | Management API |
| PowerScale (NAS storage) | Scraped from metrics exporter, stored in time-series database | Syslog events forwarded to log database | Metrics exporter over TLS, syslog |
| VAST (Parallel storage) | Scraped from metrics exporter endpoints, stored in time-series database | Syslog events forwarded to log database | Metrics exporter over HTTPS, syslog |

---

## 5. Description of Features

The following table enumerates every feature covered by this Behaviour Specification, grouped by operational domain.

| **Section** | **Feature** | **Domain** |
|---|---|---|
| 5.1 | VictoriaMetrics Cluster Mode | Metrics Infrastructure |
| 5.2 | vmagent — Metrics Scraping and Forwarding | Metrics Infrastructure |
| 5.3 | Apache Kafka Streaming Bus | Data Transport |
| 5.4 | iDRAC Hardware Telemetry | Hardware Monitoring |
| 5.5 | LDMS In-Band Metric Collection | Compute Monitoring |
| 5.6 | SFM Telemetry Integration | Network Monitoring |
| 5.7 | OME Telemetry Integration | Server Management |
| 5.8 | VictoriaLogs Cluster Mode | Log Infrastructure |
| 5.9 | Kafka to VictoriaMetrics Ingestion via Vector | Data Pipeline |
| 5.10 | NVIDIA DCGM GPU Metrics | Compute Monitoring |
| 5.11 | NVIDIA UFM InfiniBand Telemetry | Network Monitoring |
| 5.12 | NVIDIA NetQ Ethernet Telemetry | Network Monitoring |
| 5.13 | NVIDIA Skyway IB-to-Ethernet Telemetry | Network Monitoring |
| 5.14 | PowerVault ME5 Storage Telemetry | Storage Monitoring |
| 5.15 | PowerScale Storage Telemetry | Storage Monitoring |
| 5.16 | VAST Storage Telemetry | Storage Monitoring |

---

## 6. Behavioural Descriptions

### 6.1 VictoriaMetrics — Metrics Database

#### 6.1.1 Marketing User Stories

| Theme | MRD Excerpt / Feature Description |
|-------|-----------------------------------|
| AI/HPC | Omnia provides a highly-available time-series database for telemetry metrics, deployed on the Service Kubernetes cluster. The database supports both cluster and single-node deployment modes, with cluster mode recommended for production environments. |

#### 6.1.2 Operator Interaction

The operator configures telemetry via `telemetry_config.yml`. After running the telemetry deployment playbook:

- **Cluster mode** (default, recommended for production): The operator receives two externally-accessible endpoints — one for metric ingestion and one for metric querying (including a built-in web UI).
- **Single-node mode** (for dev/test environments with <10 nodes): A single endpoint serves both ingestion and querying.

All endpoints are TLS-secured. External clients (SFM, OME) can connect using the provided CA certificate. Metrics persist across restarts and are automatically purged after the configured retention period (default: 7 days).

The operator can selectively remove VictoriaMetrics without affecting other telemetry services (Kafka, VictoriaLogs).

#### 6.1.3 Acceptance Criteria

- All database components reach healthy state after telemetry deployment
- Ingestion and query endpoints obtain externally-accessible IPs reachable from outside the cluster
- TLS connectivity is validated automatically
- Metrics persist across component restarts
- Data older than the configured retention period is automatically purged
- Re-running the deployment playbook produces no unintended changes (idempotent)

#### 6.1.4 Feature Constraints

- Cluster mode requires at least 3 Service Kubernetes worker nodes
- `pod_external_ip_range` must be configured in `omnia_config.yml` and reachable from external telemetry sources (SFM, OME)
- Storage sizing must account for metric volume and retention period

#### 6.1.5 Performance

- Cluster mode provides approximately 4× ingestion throughput and 2× query speed compared to single-node mode
- Total cluster memory footprint: approximately 10 Gi

#### 6.1.6 Assets / Resources at Risk

Loss of a storage volume results in partial metric data loss. Mitigation: replicas spread across different worker nodes, regular backup of critical metrics.

---

### 6.2 vmagent — Metrics Collection

#### 6.2.1 Marketing User Stories

| Theme | MRD Excerpt / Feature Description |
|-------|-----------------------------------|
| AI/HPC | Omnia deploys a Prometheus-compatible metrics scraper that automatically discovers telemetry endpoints within the Kubernetes cluster and forwards collected metrics to VictoriaMetrics. |

#### 6.2.2 Operator Interaction

The metrics collection agent is deployed automatically as part of telemetry setup. The operator does not interact with vmagent directly — it automatically discovers and scrapes all telemetry endpoints.

As new telemetry sources are enabled (UFM, NetQ, PowerScale, VAST), the agent automatically includes them in its collection cycle.

#### 6.2.3 Acceptance Criteria

- Agent discovers new telemetry endpoints within 30 seconds of them becoming available
- Scraped metrics are queryable in VictoriaMetrics within 20 seconds (2 scrape intervals)
- All scraped metrics carry identifying labels for source tracking

#### 6.2.4 Feature Constraints

- Currently collects within the telemetry namespace only; external endpoint scraping (UFM, NetQ, PowerScale, VAST) requires additional configuration

#### 6.2.5 Performance

Lightweight, minimal overhead. Default scrape interval: 10 seconds.

#### 6.2.6 Assets / Resources at Risk

N/A

---

### 6.3 Apache Kafka — Telemetry Data Bus

#### 6.3.1 Marketing User Stories

| Theme | MRD Excerpt / Feature Description |
|-------|-----------------------------------|
| AI/HPC | Omnia deploys a reliable, TLS-secured message streaming bus for telemetry data, enabling multiple independent consumers to access telemetry streams without impacting each other. |

#### 6.3.2 Operator Interaction

Kafka is deployed automatically as part of telemetry setup. The operator interacts with Kafka in two scenarios:

1. **OME integration**: The operator runs a connection details playbook to obtain the external Kafka endpoint and mTLS certificates, then configures OME to publish telemetry to Kafka.
2. **Custom consumers**: External systems can consume telemetry data via the HTTP REST bridge or direct Kafka connections using mTLS.

All Kafka traffic is TLS-encrypted. No plaintext connections are permitted.

#### 6.3.3 Acceptance Criteria

- All Kafka components reach healthy state after deployment
- Telemetry topics are auto-created based on enabled telemetry features
- TLS/mTLS connectivity is validated automatically
- External endpoint accepts mTLS connections from authorised clients
- HTTP REST bridge provides functional access to topics

#### 6.3.4 Feature Constraints

- Strimzi operator must be deployed before Kafka components
- Default data retention: 7 days

#### 6.3.5 Performance

3-broker cluster provides adequate throughput for clusters up to 2,000+ nodes. Default retention: 7 days.

#### 6.3.6 Assets / Resources at Risk

Total storage: 48 Gi (default). Must be sized to accommodate retention period and message volume.

---

### 6.4 iDRAC Hardware Telemetry

#### 6.4.1 Marketing User Stories

| Theme | MRD Excerpt / Feature Description |
|-------|-----------------------------------|
| AI/HPC | Omnia provides and configures iDRAC collector to push iDRAC metrics to VictoriaMetrics and/or Kafka. Telemetry data includes power, thermal, CPU, memory, storage SMART, NIC statistics, GPU metrics, and SFP transceiver metrics. |

#### 6.4.2 Operator Interaction

The operator provides a list of BMC (iDRAC) IP addresses in the inventory file. After deployment:

- The operator chooses the collection destination: **VictoriaMetrics only**, **Kafka only**, or **both** (recommended for dual-write).
- All 37 supported telemetry reports are automatically enabled on target servers (covering CPU, memory, storage, NIC, power, thermal, GPU, and OME metrics). Supports iDRAC 9 and iDRAC 10.
- A telemetry status report is generated listing all configured iDRAC endpoints and their status.

#### 6.4.3 Acceptance Criteria

- All iDRAC telemetry components reach healthy state
- All 37 iDRAC telemetry reports are enabled on target servers
- When dual-write is enabled, metrics are queryable in VictoriaMetrics AND consumable from the Kafka topic
- Credential data persists across restarts
- Telemetry report is generated listing all configured iDRAC endpoints and their status

#### 6.4.4 Feature Constraints

- Redfish must be enabled on all target iDRAC interfaces
- iDRAC firmware must be updated to the latest version
- Datacenter license is required on the target servers
- All BMC IPs must be reachable from the Service Kubernetes cluster

#### 6.4.5 Performance

Service node worker load should not exceed 40% when iDRAC collector is configured at maximum collection frequency.

#### 6.4.6 Assets / Resources at Risk

Loss of credential storage requires re-initialisation of iDRAC telemetry configuration.

---

### 6.5 LDMS In-Band Metric Collection

#### 6.5.1 Marketing User Stories

| Theme | MRD Excerpt / Feature Description |
|-------|-----------------------------------|
| AI/HPC | Build LDMSd producers for RHEL 10 and deploy on Slurm cluster nodes (login, login/compiler, controller & workers). Build and configure LDMS aggregator framework and deploy on Service Node K8s workers. |

#### 6.5.2 Operator Interaction

The operator configures LDMS via `telemetry_config.yml`, selecting which sampler plugins to enable. LDMS is automatically deployed to compute nodes during provisioning.

Available sampler plugins: `meminfo` (memory), `procstat2` (processes), `vmstat` (virtual memory), `loadavg` (system load), `procnetdev2` (network interfaces), `slurm_sampler` (HPC workload monitoring).

When compute nodes are added or removed from the cluster, the aggregator automatically picks up the new topology.

#### 6.5.3 Acceptance Criteria

- On Slurm controller, worker, and login nodes, LDMS producer is installed and captures local host metrics
- Aggregator framework is deployed on Service K8s workers
- LDMS data is pushed to the Kafka message bus
- Aggregator automatically adapts when cluster node topology changes

#### 6.5.4 Feature Constraints

- This feature relies on NERSC codebase availability for LDMS framework components
- Omnia builds and configures the LDMS framework but does not address functional defects in LDMS itself

#### 6.5.5 Performance

Load on each K8s worker node should not exceed 40% when all LDMS producers are publishing at maximum frequency.

#### 6.5.6 Assets / Resources at Risk

N/A

---

### 6.6 SFM Telemetry Integration

#### 6.6.1 Marketing User Stories

| Theme | MRD Excerpt / Feature Description |
|-------|-----------------------------------|
| AI/HPC | Omnia enables Smart Fabric Manager (SFM) to securely stream SONiC switch telemetry metrics to VictoriaMetrics, providing visibility into network fabric health, interface counters, transceiver health, and queue statistics. |

#### 6.6.2 Operator Interaction

The operator runs the connection details playbook (`external_victoria_connect_details.yml`) to obtain VictoriaMetrics endpoint IPs and the TLS CA certificate. The operator then configures the SFM UI to enable Prometheus remote write with the extracted URL and uploads the CA certificate.

A DNS mapping entry is required inside SFM for TLS certificate validation — this entry is ephemeral and must be re-applied if the SFM monitoring component restarts.

Key metrics available to the operator: transceiver health (DOM temperature), per-queue traffic and congestion, throughput, and per-interface counters (in/out octets and errors).

#### 6.6.3 Acceptance Criteria

- Connection details playbook produces valid endpoints and CA certificate
- SFM switch metrics (interface counters, transceiver DOM, queue statistics) are queryable in VictoriaMetrics after configuration
- TLS handshake succeeds between SFM and VictoriaMetrics

#### 6.6.4 Feature Constraints

- `pod_external_ip_range` must be configured and reachable from the SFM network
- SSH must be enabled on the SFM virtual machine
- DNS mapping must be re-applied if the SFM monitoring component restarts

#### 6.6.5 Performance

Metrics forwarded every 15–30 seconds (configurable). End-to-end latency approximately 15–35 seconds.

#### 6.6.6 Assets / Resources at Risk

N/A

---

### 6.7 OME Telemetry Integration

#### 6.7.1 Marketing User Stories

| Theme | MRD Excerpt / Feature Description |
|-------|-----------------------------------|
| AI/HPC | Omnia enables OpenManage Enterprise to securely stream server management telemetry to the Omnia Kafka bus using mutual TLS, providing integration with the broader telemetry pipeline. |

#### 6.7.2 Operator Interaction

The operator runs the connection details playbook (`external_kafka_connect_details.yml`) to obtain the Kafka external endpoint and mTLS certificates. The operator generates a `.pfx` client certificate and configures the OME UI to enable Kafka connectivity with SSL authentication, uploading the certificates.

The OME Kafka integration wizard allows the operator to select specific metrics to stream and device groups to collect from. A green checkmark confirms successful connectivity.

#### 6.7.3 Acceptance Criteria

- Connection details playbook produces valid Kafka endpoint, CA certificate, and client certificates
- OME connectivity status shows "Connected since" with green checkmark in the OME UI
- OME telemetry messages are consumable from the Kafka topic

#### 6.7.4 Feature Constraints

- `pod_external_ip_range` must be configured and reachable from the OME appliance network
- If OME is on a different system than the OIM host, certificates must be manually copied

#### 6.7.5 Performance

Streaming frequency and metric selection are configurable within the OME UI.

#### 6.7.6 Assets / Resources at Risk

N/A

---

### 6.8 VictoriaLogs — Log Database

#### 6.8.1 Marketing User Stories

| Theme | MRD Excerpt / Feature Description |
|-------|-----------------------------------|
| AI/HPC | Omnia deploys a centralised log management system alongside VictoriaMetrics, enabling operators to ingest, store, and query infrastructure logs (syslog from network devices, iDRAC events, system audit trails) from a single observability interface. |

#### 6.8.2 Operator Interaction

VictoriaLogs is deployed alongside VictoriaMetrics using the same deployment modes (cluster or single-node). The operator does not need to configure separate retention or storage settings — existing VictoriaMetrics settings govern both metrics and logs.

Two log ingestion paths are available simultaneously:

- **Real-time syslog**: Network and storage devices (UFM, SFM, Skyway, PowerScale, VAST) send syslog messages that are ingested in real time.
- **Kafka-buffered events**: iDRAC events and control plane logs flow through Kafka for buffered, reliable delivery.

All external access requires TLS/mTLS. VictoriaLogs can be removed independently without affecting VictoriaMetrics or Kafka.

#### 6.8.3 Acceptance Criteria

- Log database components deploy and reach healthy state within 5 minutes
- A test log submitted to the ingestion endpoint is queryable within 10 seconds
- Syslog messages are retrievable with preserved severity, timestamp, and source
- TLS is enforced on all external endpoints; plaintext connections are rejected
- Logs persist across component restarts
- Retention policy automatically deletes logs older than the configured period
- Both ingestion paths (syslog and Kafka-sourced) operate simultaneously
- Air-gapped deployment succeeds using offline container image repository
- No new configuration knobs for storage/retention are added (per Cap 23732)

#### 6.8.4 Feature Constraints

- Log agent deployment on compute nodes is out of scope
- Grafana dashboard provisioning for logs is out of scope
- Log-based alerting rules are out of scope
- Multi-tenant log isolation is out of scope

#### 6.8.5 Performance

Estimated storage: ~70 GB for 7-day retention at 500 nodes; ~350 GB at 2,000 nodes.

#### 6.8.6 Assets / Resources at Risk

VictoriaLogs cluster mode is relatively new in the upstream project. Mitigation: pin to a tested release and perform soak testing at target scale before production deployment.

---

### 6.9 Kafka → VictoriaMetrics Ingestion via Vector

#### 6.9.1 Marketing User Stories

| Theme | MRD Excerpt / Feature Description |
|-------|-----------------------------------|
| AI/HPC | Telemetry data from LDMS, iDRAC, and OME published to Kafka topics is automatically ingested into VictoriaMetrics for long-term time-series storage and querying, using Vector as the transformation and routing layer. |

#### 6.9.2 Operator Interaction

Vector operates transparently — the operator does not interact with it directly. It automatically:

- Consumes telemetry data from Kafka topics
- Separates metrics from logs/events
- Routes metrics to VictoriaMetrics and logs/events to VictoriaLogs
- Dynamically discovers new Kafka topics and begins consuming within 60 seconds of topic creation

New telemetry subsystems that publish to Kafka are automatically picked up without operator intervention.

#### 6.9.3 Acceptance Criteria

- Data from LDMS, OME, and iDRAC Kafka topics is stored in VictoriaMetrics
- New topics are discovered and consumed within 60 seconds of creation
- Ingestion success rate ≥99.9% over 24 hours
- End-to-end latency (Kafka to queryable in VictoriaMetrics) ≤30 seconds at p99
- Pipeline uptime ≥99.5%

#### 6.9.4 Feature Constraints

- Topic naming convention must be enforced by producers
- Schema changes in source data may require pipeline transform updates

#### 6.9.5 Performance

New subsystem onboardable in ≤4 hours. Pipeline designed for continuous operation with minimal operator intervention.

#### 6.9.6 Assets / Resources at Risk

LDMS schema changes may break pipeline transforms (HIGH risk). Mitigation: version-pinned schema definitions and automated transform testing.

---

### 6.10 NVIDIA DCGM GPU Metrics

#### 6.10.1 Marketing User Stories

| Theme | MRD Excerpt / Feature Description |
|-------|-----------------------------------|
| AI/HPC | Omnia deploys NVIDIA DCGM and DCGM Exporter on all NVIDIA-accelerated compute nodes, integrating GPU telemetry into the existing LDMS data pipeline for real-time monitoring of GPU utilisation, temperature, power, memory, and health. |

#### 6.10.2 Operator Interaction

The operator enables or disables DCGM via an inventory-level toggle (`omnia_dcgm_enabled`). When enabled:

- DCGM is automatically installed on every compute node with NVIDIA GPUs
- Non-GPU nodes are detected and skipped — no DCGM packages are installed
- GPU metrics are integrated into the LDMS data pipeline alongside standard OS metrics
- Per-functional-group configuration supports different GPU monitoring profiles for heterogeneous node types

Key GPU metrics available to the operator: utilisation percentage, framebuffer memory (used/free), temperature, power consumption, hardware error codes (XID), NVLink bandwidth.

Supported GPU architectures: Blackwell (B100/B200/GB200), Hopper (H100/H200), Ampere (A100) on x86_64 and aarch64. Packages are served from the Omnia local repository for air-gapped environments.

#### 6.10.3 Acceptance Criteria

- DCGM Exporter exposes metrics on 100% of GPU nodes within 5 minutes of deployment
- LDMS collects all required GPU metrics (GPU_UTIL, FB_USED, FB_FREE, GPU_TEMP, POWER_USAGE, XID_ERRORS, NVLINK_BANDWIDTH_TOTAL)
- Toggle to disable and re-enable DCGM works without requiring a node reboot
- Non-GPU nodes show no DCGM packages installed after deployment

#### 6.10.4 Feature Constraints

- Blackwell GPU support in DCGM depends on NVIDIA release timeline
- aarch64 DCGM package availability must be verified early in development

#### 6.10.5 Performance

DCGM overhead: ~2% GPU utilisation, ~200 MB host RAM (daemon + exporter combined).

#### 6.10.6 Assets / Resources at Risk

Blackwell GPU and aarch64 DCGM packages may not be available at development start (HIGH risk). Mitigation: engage NVIDIA early; fallback to `nvidia-smi` scraping if DCGM packages are unavailable.

---

### 6.11 NVIDIA UFM InfiniBand Telemetry

#### 6.11.1 Marketing User Stories

| Theme | MRD Excerpt / Feature Description |
|-------|-----------------------------------|
| AI/HPC | Omnia collects InfiniBand fabric metrics and events from NVIDIA UFM appliances, providing visibility into per-port traffic, link health, congestion indicators, and topology changes across the IB fabric. |

#### 6.11.2 Operator Interaction

The operator enables UFM telemetry collection and provides UFM appliance connection details. The system supports UFM Enterprise 6.15.x in HA configuration (active/standby pair).

Metrics collected include: per-port Tx/Rx bytes and packets, error counters, link down/recovery events, and congestion indicators. Labels preserve device/port identity, GUIDs, and node/port names.

Logs/events from UFM are collected via syslog and stored in VictoriaLogs.

Dual-destination forwarding to an external observability endpoint is planned (depends on API finalisation).

#### 6.11.3 Acceptance Criteria

- 100% of metrics exposed by the UFM Prometheus exporter appear in VictoriaMetrics within one scrape interval
- ≥95% of critical, error, and warning syslog events are ingested into VictoriaLogs within 60 seconds
- Metric batch failure rate <0.1% over 24 hours
- UFM HA failover: metrics resume from the surviving appliance within 2 scrape intervals

#### 6.11.4 Feature Constraints

- UFM exporter schema may change across UFM versions; version pinning required
- External destination API not finalised (TBD)

#### 6.11.5 Performance

End-to-end metric latency: <60 seconds. Syslog event latency: <60 seconds. Log and metric drop rate: <0.1% over 24 hours.

#### 6.11.6 Assets / Resources at Risk

Cardinality explosion (>800K series) may impact metrics database performance. Mitigation: filtering rules to drop high-churn metrics.

---

### 6.12 NVIDIA NetQ Ethernet Telemetry

#### 6.12.1 Marketing User Stories

| Theme | MRD Excerpt / Feature Description |
|-------|-----------------------------------|
| AI/HPC | Omnia collects Ethernet fabric telemetry from NVIDIA NetQ appliances, providing visibility into interface health, DOM optics, resource utilisation, fans, PSUs, temperature, and node health. |

#### 6.12.2 Operator Interaction

The operator enables NetQ telemetry and provides appliance connection details. Up to 4 NetQ appliances are supported. Metric domains include: interface/link statistics, DOM optics (transceiver health), system resource utilisation, environmental sensors (fans, PSUs, temperatures), node health, and per-process/per-device network counters.

Rsyslog events are collected and stored in VictoriaLogs. A 4-hour buffer provides resilience during destination outages.

#### 6.12.3 Acceptance Criteria

- ≥90% of metric families queryable within 2 scrape intervals of deployment start
- ≥95% of log events ingested into VictoriaLogs within 60 seconds
- Scrape failure rate <0.1% over 24 hours
- Deployment via a single Ansible playbook in <10 minutes for 4 appliances

#### 6.12.4 Feature Constraints

- NetQ PromQL schema may vary across versions
- Kafka integration is optional (Phase 2)

#### 6.12.5 Performance

Metrics available within scrape interval + 5 seconds. Log event latency: <60 seconds.

#### 6.12.6 Assets / Resources at Risk

Cardinality may exceed agent budget at scale. Mitigation: metric filtering and relabeling.

---

### 6.13 NVIDIA Skyway IB-to-Ethernet Telemetry

#### 6.13.1 Marketing User Stories

| Theme | MRD Excerpt / Feature Description |
|-------|-----------------------------------|
| AI/HPC | Omnia collects telemetry from NVIDIA Skyway InfiniBand-to-Ethernet gateways via SNMP and syslog, providing visibility into port statistics, system health, and link events across the gateway fabric. |

#### 6.13.2 Operator Interaction

The operator enables Skyway telemetry and provides gateway connection details and SNMPv3 credentials. Up to 32 gateways (128 ports each, 4,096 total ports) are supported. Poll interval is configurable (15–30 seconds).

Metric domains: port bytes/packets, errors, discards, CRC, link state, speed, system temperature, fan/PSU status, alarms, CPU/memory utilisation.

An optional SNMP trap feature (toggle-controlled) provides event-driven notifications. Unsupported OIDs on specific firmware versions are reported in status output without failing the collection pipeline. Port subsets can be configured to manage metric volume at scale.

#### 6.13.3 Acceptance Criteria

- ≥90% of OIDs from the prioritised list are collected and queryable
- ≥95% of critical, error, and warning syslog events ingested within 60 seconds
- Metric batch failure rate <0.1% over 24 hours
- SNMPv3 authPriv enforced with zero credential exposure in logs
- Status output lists active telemetry source, enabled domains, and any failed OIDs

#### 6.13.4 Feature Constraints

- Skyway MIB OIDs may differ across firmware versions; an OID inventory per firmware version is required

#### 6.13.5 Performance

Metric end-to-end latency: poll interval + 10 seconds. Syslog event latency: <60 seconds.

#### 6.13.6 Assets / Resources at Risk

SNMP poll latency may exceed the poll interval at scale (32 gateways, 4,096 ports). Mitigation: parallel polling and configurable port subset filtering.

---

### 6.14 PowerVault ME5 Storage Telemetry

#### 6.14.1 Marketing User Stories

| Theme | MRD Excerpt / Feature Description |
|-------|-----------------------------------|
| AI/HPC | Omnia collects PowerVault ME5 performance, capacity, and health metrics along with event logs, enabling proactive identification of storage bottlenecks and hardware issues. |

#### 6.14.2 Operator Interaction

The operator enables PowerVault telemetry and provides array connection details. Metrics are collected via Redfish API (preferred) with CLI fallback. Up to 16 arrays are supported.

Metrics available: read/write IOPS, throughput, latency (average and max), queue depth, cache utilisation, destage statistics, capacity (free/used per pool and volume), and component health (controllers, disks, PSUs, fans, temperatures).

Event logs cover Critical, Error, Warning, Informational, and Resolved severity levels.

Independent feature toggles allow the operator to enable/disable metrics and event log collection separately. Dual remote write delivers to both internal VictoriaMetrics and external Omni DB endpoints.

#### 6.14.3 Acceptance Criteria

- ≥90% metric coverage achieved within 14 days of development
- ≥95% of events ingested within 60 seconds
- Failed metric batch rate <0.1% per destination over 24 hours
- During a 4-hour destination outage, the surviving destination continues uninterrupted; buffered data delivered on recovery without loss
- Zero plaintext credentials in logs or configuration

#### 6.14.4 Feature Constraints

- Redfish metric coverage may be below 90%, requiring CLI fallback
- ME5 may throttle concurrent management sessions
- Lab hardware must be secured for testing

#### 6.14.5 Performance

Sampling interval: 30–60 seconds (configurable). Event latency: <60 seconds.

#### 6.14.6 Assets / Resources at Risk

No ME5 lab hardware available for testing (HIGH risk). Mitigation: secure lab allocation early in Q2.

---

### 6.15 PowerScale Storage Telemetry

#### 6.15.1 Marketing User Stories

| Theme | MRD Excerpt / Feature Description |
|-------|-----------------------------------|
| NAS Storage Observability | As a storage administrator, I need IOPS, throughput, latency, capacity, topology, and cluster health metrics from PowerScale, plus syslog events for fault and capacity alerts, so that I can manage NAS performance and reliability alongside compute and fabric telemetry in a single observability stack. |
| Deployment Flexibility | As a site administrator, I need the choice between Omnia deploying the metrics collection stack on the service cluster and pointing Omnia at an operator-managed endpoint on an external cluster, so that I can integrate PowerScale telemetry regardless of where the collection components run. |
| Operational Health Visibility | As an SRE, I need scrape success/error counters, ingest latency, and error rates for the PowerScale telemetry integration itself, so that I can detect and respond to pipeline issues before they cause data gaps. |

#### 6.15.2 Overview

The PowerScale storage telemetry feature adds Dell PowerScale observability to Omnia by ingesting metrics via *Dell CSM Metrics for PowerScale* with an OpenTelemetry Collector scraped by vmagent, and ingesting logs/events via the existing syslog pipeline. TLS is enforced for all off-cluster communications; Kubernetes-native service-account authentication secures the metrics scrape path.

Metrics cover IOPS, throughput, latency, capacity, cluster health, and topology. Logs and events flow through syslog with host/cluster, severity, and facility labels. The operator configures the PowerScale cluster address, credentials, and feature flags through the Omnia input configuration.

Two deployment modes are supported. In **Omnia-orchestrated mode**, Omnia deploys CSM Metrics, the OpenTelemetry Collector, and required dependencies (CSI Driver, cert-manager) on the service cluster. In **operator-provided mode**, the operator runs these components externally and provides the Prometheus endpoint URL; Omnia configures its scraping agent to target that endpoint without deploying collection pods.

Independent feature flags allow the operator to enable or disable metric collection and log collection separately. Dual-destination delivery sends metrics to both the internal time-series database and an optional external observability endpoint; failure of one destination does not affect the other. The integration exposes operational health metrics—scrape success/error counters, ingest latency, and error rates—so operators can monitor the telemetry pipeline itself.

A single PowerScale cluster is supported per Omnia deployment.

#### 6.15.3 Detail

**Metric Collection**

The operator SHALL configure the PowerScale cluster address and credentials with the metrics feature flag enabled. The system SHALL deploy (or connect to) Dell CSM Metrics for PowerScale, which queries the OneFS API and emits metrics to an OpenTelemetry Collector. The metrics scraping agent SHALL periodically scrape the OpenTelemetry Collector Prometheus endpoint over TLS with Kubernetes service-account authentication. Collected metrics SHALL include:

- **Performance:** Protocol-level IOPS (NFS, SMB, S3), throughput (bytes/s), read/write latency.
- **Capacity:** Total cluster capacity, used capacity, available capacity, per-node capacity.
- **Health:** Node online/offline status, disk health, cluster rebalance status, protection group status.
- **Topology:** Cluster node membership, node roles, interconnect layout, protection domain mapping.

Metrics SHALL be stored in the time-series database with labels identifying the cluster name, node name, and protocol. Labels SHALL follow existing Omnia naming/label conventions to distinguish PowerScale data from other sources.

**Event Collection**

The log collection feature flag SHALL control syslog event ingestion. When enabled, the PowerScale cluster's syslog events (capacity warnings, disk failures, node state changes, protocol errors) SHALL be received by the log agent and forwarded to the log database with host/cluster, severity, and facility labels. End-to-end latency SHALL be less than 1 minute under nominal load.

**Independent Feature Flags**

The operator SHALL be able to independently enable or disable PowerScale metric collection and PowerScale log collection. Disabling one flag SHALL NOT affect the other.

**Deployment Mode Selection**

The operator SHALL select one of two deployment modes:

- **Omnia-orchestrated:** Omnia deploys CSM Metrics, the OpenTelemetry Collector, the CSI Driver for Dell PowerScale, and cert-manager on the service cluster and manages their lifecycle.
- **Operator-provided endpoint:** The operator provides the Prometheus endpoint URL of an externally managed OpenTelemetry Collector. Omnia configures vmagent to scrape that endpoint without deploying CSM Metrics or OTel Collector pods.

**TLS and Authentication**

All metric scraping SHALL use TLS. Authentication SHALL use Kubernetes service-account tokens. Mutual TLS (mTLS) is not required—the connection is encrypted but the PowerScale-side endpoint does not validate client identity via certificate exchange. TLS SHALL be enforced for all off-cluster communications.

**Dual-Destination Delivery**

The operator MAY configure an external observability endpoint. When configured, metrics SHALL be delivered to both the internal time-series database and the external endpoint independently. Failure of one destination SHALL NOT block delivery to the other. Independent buffers SHALL ensure data continuity.

**Operational Health Monitoring**

The PowerScale telemetry integration SHALL expose operational health metrics including scrape success rate, scrape error count, ingest latency, and log delivery error rate. These metrics SHALL be available for alerting and monitoring via the same observability stack. The OpenTelemetry Collector endpoint SHALL maintain availability exceeding 98% over a 24-hour period.

#### 6.15.4 Acceptance Criteria

- PowerScale metrics (IOPS, throughput, latency, capacity, topology, cluster health) SHALL be queryable in the time-series database with expected labels within one scrape interval of emission, when the metrics feature flag is enabled.
- PowerScale syslog events SHALL be searchable in the log database with correct labels (host/cluster, severity, facility) and less than 1-minute end-to-end latency, when the log feature flag is enabled.
- Disabling the metrics feature flag SHALL stop metric collection without affecting log collection, and vice versa.
- Metric scraping SHALL use TLS; plaintext connections SHALL NOT be permitted.
- Kubernetes service-account authentication SHALL function without mTLS handshake failures.
- In Omnia-orchestrated mode, CSM Metrics and the OpenTelemetry Collector SHALL be deployed and operational without manual intervention beyond initial configuration.
- In operator-provided mode, vmagent SHALL successfully scrape the provided external endpoint over TLS.
- Dual-destination delivery SHALL function independently between internal and external endpoints when an external endpoint is configured.
- Operational health metrics (scrape success/error counters, ingest latency, error rates) SHALL be exposed and queryable.
- OpenTelemetry Collector endpoint availability SHALL exceed 98% over a 24-hour period.

#### 6.15.5 Feature Constraints

- Supports a single PowerScale cluster per Omnia deployment.
- Omnia-orchestrated mode requires CSI Driver for Dell PowerScale and cert-manager to be installed on the service Kubernetes cluster.
- Mutual TLS is not required on the metrics exporter endpoint; transport is encrypted but client identity is not verified via certificate exchange.
- Syslog integration requires network connectivity between the PowerScale cluster and the Omnia log agent.
- The metric set is aligned with Dell CSM Metrics capabilities; metrics not exposed by CSM Metrics are not available.

#### 6.15.6 Performance

- Key PowerScale metrics SHALL appear in the time-series database within one scrape interval of emission.
- Syslog events SHALL arrive in the log database with less than 1-minute end-to-end latency under nominal load.
- OpenTelemetry Collector endpoint availability SHALL exceed 98% over a 24-hour period.
- Scrape interval SHALL be configurable between 30 and 60 seconds.

#### 6.15.7 Assets / Resources at Risk

- **Data at Risk:** PowerScale performance metrics and syslog events in transit between the PowerScale cluster and Omnia databases. PowerScale credentials used for CSM Metrics access.
- **Operational Impact:** Loss of PowerScale telemetry removes visibility into NAS performance and health, potentially delaying detection of capacity exhaustion, disk failures, topology changes, and protocol-level performance degradation.
- **Mitigation:** TLS encryption protects data in transit. Credentials are stored securely within the service infrastructure. Dual-destination delivery provides redundancy for metrics. Operational health metrics enable proactive monitoring of the telemetry pipeline itself. Operators SHOULD monitor scraper health and syslog delivery. PowerScale's native management interface remains available for direct access during telemetry outages.

---

### 6.16 VAST Storage Telemetry

#### 6.16.1 Marketing User Stories

| Theme | MRD Excerpt / Feature Description |
|-------|-----------------------------------|
| Parallel Storage Observability | As a storage administrator managing VAST Data parallel storage, I need performance, capacity, and health metrics from multiple VAST clusters, plus event logs and audit records, so that I can manage storage at scale across a heterogeneous HPC environment. |
| Multi-Cluster Support | As a site planner, I need telemetry collection from up to 4 VAST clusters and 512 CNodes simultaneously, so that the telemetry system scales with our storage footprint. |

#### 6.16.2 Overview

The VAST storage telemetry feature collects comprehensive performance, capacity, and health metrics from VAST Data parallel-storage clusters, along with syslog-based events, alarms, and audit records. VAST exposes multiple metrics exporter domain endpoints (e.g., cluster-level, volume-level, protocol-level), and the operator can configure which endpoint domains to include or exclude based on operational relevance.

Metrics are scraped from the VAST metrics exporter endpoints over HTTPS and stored in the time-series database. Events, alarms, and audit logs are received via syslog and forwarded to the log database. The feature supports up to 4 VAST clusters and 512 CNodes (compute nodes within the VAST architecture) per Omnia deployment, accommodating large-scale storage environments.

The feature supports dual-destination delivery for metrics. Configurable endpoint inclusion/exclusion allows the operator to tailor the metrics collection scope, reducing data volume for environments that do not require all available metric domains. All communications use HTTPS for metric scraping and syslog for event delivery.

#### 6.16.3 Detail

**Multi-Cluster Configuration**

The operator SHALL configure one or more VAST cluster addresses (up to 4) and their credentials in the Omnia input configuration. Each cluster SHALL be collected independently; a failure to reach one cluster SHALL NOT affect collection from others.

**Endpoint Domain Selection**

VAST exposes multiple metrics exporter domain endpoints. The operator MAY configure which domains to include or exclude. GIVEN the operator specifies an inclusion list, WHEN the collector is deployed, THEN it SHALL scrape only the listed domains. GIVEN the operator specifies an exclusion list, WHEN the collector is deployed, THEN it SHALL scrape all domains except the excluded ones. If neither is specified, all available domains SHALL be scraped.

**Metric Categories**

Collected metrics SHALL include (depending on domain selection):

- **Performance:** Protocol-level IOPS, throughput, latency, queue depth.
- **Capacity:** Total, used, available, thin-provisioned capacity; per-volume utilization.
- **Health:** CNode health status, DNode status, drive health, rebuild status.
- **Network:** CNode network interface throughput and error counts.

**Event, Alarm, and Audit Log Collection**

GIVEN syslog is configured on the VAST clusters, WHEN VAST emits events (system events, storage alarms, audit records), THEN the log agent SHALL receive and forward them to the log database with fields for severity, cluster name, timestamp, and message content.

**Dual-Destination Delivery**

The operator MAY configure an external analytics endpoint. Metrics SHALL be delivered to both the internal time-series database and the external endpoint when configured. Failure of one destination SHALL NOT affect delivery to the other.

**Scale Support**

The system SHALL support up to 4 VAST clusters with up to 512 CNodes total. Collection capacity SHALL scale with the number of configured clusters and CNodes.

#### 6.16.4 Acceptance Criteria

- Performance, capacity, health, and network metrics from VAST clusters SHALL be queryable in the time-series database.
- Syslog events, alarms, and audit records from VAST clusters SHALL be searchable in the log database.
- When an endpoint domain inclusion or exclusion list is configured, only the appropriate domains SHALL be scraped.
- Collection from one VAST cluster SHALL be independent of other configured clusters; failure to reach one SHALL NOT affect the others.
- Up to 4 VAST clusters and 512 CNodes SHALL be supported simultaneously.
- Dual-destination delivery SHALL function independently between internal and external endpoints.

#### 6.16.5 Feature Constraints

- Requires VAST Data Platform clusters with metrics exporter endpoints enabled.
- Maximum of 4 VAST clusters per Omnia deployment.
- VAST metrics exporter domain endpoints must be accessible over HTTPS from the service infrastructure.
- Syslog integration requires network connectivity between VAST clusters and the Omnia log agent.
- VAST cluster credentials must be provided by the operator and are stored securely.
- The set of available metrics exporter domains depends on the VAST software version; newer versions may expose additional domains.

#### 6.16.6 Performance

- The collector SHALL support 4 VAST clusters with up to 512 CNodes total without data loss.
- Scrape cycle duration SHALL remain below 60 seconds per cluster for the maximum supported CNode count.
- Syslog event ingestion SHALL handle at least 10,000 events per minute across all configured clusters.
- Collected metrics SHALL be available in the time-series database within 2 scrape intervals of collection.

#### 6.16.7 Assets / Resources at Risk

- **Data at Risk:** VAST storage metrics, events, alarms, and audit records in transit. VAST cluster credentials.
- **Operational Impact:** Loss of VAST telemetry removes visibility into parallel-storage health, potentially delaying detection of CNode failures, drive degradation, rebuild operations, and capacity exhaustion that directly impact HPC workload I/O performance.
- **Mitigation:** Per-cluster independent collection isolates failures. HTTPS encryption protects metric data in transit. Credentials are stored securely. Dual-destination delivery provides redundancy. Operators SHOULD monitor collector health and VAST API endpoint availability.

---

### 6.17 One-Shot Combined Log Extraction for Debugging

#### 6.17.1 Marketing User Stories

| Theme | MRD Excerpt / Feature Description |
|-------|-----------------------------------|
| AI/HPC | Omnia provides a single admin command that packages all relevant management logs into a timestamped archive for rapid troubleshooting and support engagement. |

#### 6.17.2 Operator Interaction

The operator runs a single CLI command to generate a log bundle. The command:

- Creates a compressed archive with filename pattern: `omnia-logs-<hostname>-<timestamp>.tar.gz`
- Prints the absolute path to the bundle and a SHA256 checksum
- Includes all documented Omnia/OIM log paths by default (configurable via pointers, not hardcoded)
- Allows the operator to add custom log file locations
- Supports utility flags for filesize limits and exclusion patterns (ignore temp/stale logs)
- Reports excluded items and warns about missing logs without failing

The archive includes a `metadata.json` capturing: timestamp (UTC+local), triggering user, OIM hostname/OS info, and checksum.

#### 6.17.3 Acceptance Criteria

- Running the command generates a `.tar.gz` file and prints its absolute path and SHA256 (Pass/Fail)
- `metadata.json` includes timestamp (UTC+local), triggering user, versions, and flags (Pass/Fail)
- Bundle contains logs from documented Omnia/OIM paths and system logs (Pass/Fail)
- Operator can pass exclusion patterns and max file size; excluded items are reported (Pass/Fail)

#### 6.17.4 Feature Constraints

- Requires network and container/pod connectivity to the OIM
- Software should be mostly self-contained; requires standard Linux utilities for metadata and checksum

#### 6.17.5 Performance

Target: Time to provide a complete bundle to engineering/support reduced by >50% vs manual collection.

#### 6.17.6 Assets / Resources at Risk

N/A

---

## 7. License Information

| # | Component | License |
|---|-----------|---------|
| 1 | VictoriaMetrics | Apache 2.0 |
| 2 | VictoriaLogs | Apache 2.0 |
| 3 | Apache Kafka (Strimzi) | Apache 2.0 |
| 4 | Vector | Mozilla Public License 2.0 |
| 5 | NVIDIA DCGM | NVIDIA proprietary (free for use on NVIDIA hardware) |
| 6 | LDMS (OVIS) | GPLv2 / open-source |

---

*Document Version: 2.2 | Last Updated: 2026-03-31*
*SDD Phase: 2a — Behaviour Specification*
*Companion: Functional Specification FSPEC-TELEM-2026-001 (internal system behavior)*

