# Engineering Specification Document - Kafka Vector Telemetry Pipeline

| | |
|---|---|
| **Template Version** | 2.46 |
| **Current Version** | 1.0 |
| **Reviewers** | Vatam, Venkateswara; N, Ravishankar |
| **Approved By** | N, Ravishankar |
| **Approval Date** | 04/22/2026 |
| **Date** | 04/06/2026 |
| **Author** | Abhishek S A |
| **Team** | Dell Omnia |
| **Document Type** | Engineering Specification |

---

**Dell Confidential - Internal Use Only**

This document contains confidential and proprietary information of Dell Technologies. It is intended solely for the use of Dell employees and authorized partners. Unauthorized distribution, reproduction, or use of this document is strictly prohibited.

Copyright 2026 Dell Inc. or its subsidiaries. All Rights Reserved.

---

## Revision History

| Version | Date | Description | Author(s) |
|---------|------|-------------|-----------|
| 0.1 | 04/02/2026 | Initial draft — Kafka-to-Victoria ingestion pipeline via Vector with cluster-mode Victoria deployments | Abhishek Sa |
| 0.2 | 04/03/2026 | Converted to HLD format per SDD methodology — removed all code snippets (TOML, YAML, Python, Ansible) and moved to Component Spec. Added Error Handling (§6) and Backward Compatibility (§7) sections. Updated Vector version to 0.54.0. Replaced inline ACL/config YAML with descriptive tables. Added Component Spec reference (CSPEC-VECTOR-2026-001). | AI-assisted (human review required) |
| 0.3 | 04/06/2026 | Major revision — rewrote based on actual omnia-bsm telemetry code review. Split Vector-iDRAC-LDMS combined pod into separate Vector-iDRAC and Vector-LDMS pods to match existing producer pipeline separation. Corrected current-state architecture: KafkaPump and store_avro_kafka are Kafka producers (not consumers); VictoriaPump writes to VictoriaMetrics via vmagent scrape (not via Kafka); LDMS has no current path to VictoriaMetrics. Updated all data flows, sequence diagrams, topic registry, ACLs, resource tables, and traceability matrix. | Abhishek Sa |
| 0.4 | 04/06/2026 | KafkaUser consolidation — Vector-iDRAC and Vector-LDMS now reuse the existing `kafkapump` Strimzi KafkaUser instead of creating dedicated KafkaUsers. Separate consumer groups retained (`vector-idrac-group`, `vector-ldms-group`) to match established verification patterns. Only `vector-ome-user` is created as a new KafkaUser. Updated §3.2, §4.1.1, §4.1.3, §4.1.4, §4.4.2 accordingly. | Abhishek Sa |
| 0.5 | 04/06/2026 | Expanded §4.1.3.6 "Upgrade Scenarios" → "Redeploy and Upgrade Behaviour" — added deployment lifecycle state diagram, idempotent redeploy behaviour table, step-by-step procedures for fresh deploy (U1), config change (U7), image upgrade (U8), full teardown (U9), and redeploy after teardown (U10). Integrated cleanup script (`cleanup_telemetry.sh vector`) into teardown flow. Added graceful shutdown note (`terminationGracePeriodSeconds: 30`); no custom rolling update strategy specified (Kubernetes defaults used). | Abhishek Sa |
| 0.6 | 04/07/2026 | Major Q2 scope revision — (1) Vector-iDRAC removed from Q2 release: current Dell iDRAC telemetry produces to a single `idrac` topic with mixed metrics and events, which is insufficient for proper Vector routing; future releases will adopt NERSC iDRAC collector (https://github.com/NERSC/nersc-idrac) which publishes to separate log and metrics topics. (2) Vector-OME deferred from Q2 release scope. (3) Q2 scope reduced to Vector-LDMS only (Omnia-deployed). (4) Renamed feature flags to `vector_idrac_support`, `vector_ldms_support`, `vector_ome_support`. (5) Moved all CPU, memory, and replica variables from `telemetry_config.yml` to `roles/telemetry/vars/main.yml`. (6) Removed `batch_max_events`, `batch_timeout_secs`, and `kafka_fetch_max_bytes` — Vector built-in defaults are sufficient; exposing these as user-configurable adds unnecessary complexity. Updated all sections accordingly. | Abhishek Sa |
| 0.7 | 04/07/2026 | Architecture update — (1) Added **vmagent-vector** as a dedicated write-buffer between Vector pods and vminsert. Vector pods now sink to vmagent-vector (`prometheus_remote_write` on port 8429) instead of writing directly to vminsert. vmagent-vector provides disk-based write-ahead buffering and automatic retry, decoupling Vector from vminsert availability. This is a **new vmagent instance**, separate from the existing scraper vmagent (which continues to scrape VictoriaPump:2112 unchanged). (2) Documented **vlagent-vector** (future, not Q2) as the equivalent log-buffer between Vector pods and vlinsert for log/event data. Not needed in Q2 since Vector-LDMS is metrics-only. (3) Analyzed the OME OpenManage-Enterprise repository (`Kafka/Telemetry/` and `Kafka/Alerts/`) — existing codebase has Docker Compose reference implementations with Vector YAML configs but **no K8s manifests**. Updated all data flows, sequence diagrams, interfaces, resource tables, and error handling accordingly. | Abhishek Sa |
| 0.8 | 04/07/2026 | OME Vector ownership & scope change — (1) **Vector-OME is now Omnia-deployed and part of Q2 scope**: the Omnia team owns Vector-OME deployment, creating K8s manifests (Deployment, ConfigMap, Service) in the Omnia telemetry roles (`roles/telemetry/templates/telemetry/vector/`), consistent with Vector-LDMS. The previous v0.6–v0.7 model where the OME team managed Vector-OME from the OpenManage Enterprise repository has been removed. (2) Vector-OME moved from "deferred / future release" to **current Q2 scope** — all "future", "deferred", "not in Q2" labels for OME removed. (3) Removed Appendix B (OME Repository PR Plan) — no longer applicable since Omnia owns the full Vector-OME lifecycle. (4) Vector-OME K8s templates added to Appendix A file structure. (5) `vector_ome_support` flag now controls full Vector-OME pipeline deployment (pod + Kafka resources), not just Kafka provisioning. (6) Q2 now delivers two Vector pods: Vector-LDMS and Vector-OME (Vector-iDRAC remains deferred). (7) vlagent-vector added to Q2 scope — required for Vector-OME log/event sinks. Updated all sections accordingly. | Abhishek Sa |
| 1.0 | 04/22/2026 | Engineering spec approved | Abhishek Sa |
---

## Table of Contents

- [1 Glossary](#1-glossary)
- [2 Introduction](#2-introduction)
  - [2.1 Scope](#21-scope)
    - [2.1.1 In Scope](#211-in-scope)
    - [2.1.2 Out of Scope](#212-out-of-scope)
  - [2.2 References](#22-references)
- [3 Solution Architecture](#3-solution-architecture)
  - [3.1 Constraints and Assumptions](#31-constraints-and-assumptions)
    - [3.1.1 Constraints](#311-constraints)
    - [3.1.2 Assumptions](#312-assumptions)
  - [3.2 Control Flow](#32-control-flow)
  - [3.3 Data Flow Diagram](#33-data-flow-diagram)
  - [3.4 Actor/Action Matrix](#34-actoraction-matrix)
  - [3.5 Threat Model](#35-threat-model)
- [4 High Level Design](#4-high-level-design)
  - [4.1 Vector — Kafka-to-Victoria Ingestion Pipeline](#41-vector--kafka-to-victoria-ingestion-pipeline)
    - [4.1.1 Component Description](#411-component-description)
    - [4.1.2 Constraints and Assumptions](#412-constraints-and-assumptions)
    - [4.1.3 Component Design](#413-component-design)
      - [4.1.3.1 Control Flow](#4131-control-flow)
      - [4.1.3.2 Data Flow](#4132-data-flow)
      - [4.1.3.3 Interfaces](#4133-interfaces)
      - [4.1.3.4 Configuration Processing](#4134-configuration-processing)
      - [4.1.3.5 Cross-Feature Interactions](#4135-cross-feature-interactions)
      - [4.1.3.6 Redeploy and Upgrade Behaviour](#4136-redeploy-and-upgrade-behaviour)
    - [4.1.4 Security](#414-security)
    - [4.1.5 Resource Utilization](#415-resource-utilization)
    - [4.1.6 Open Source](#416-open-source)
    - [4.1.7 Component Test](#417-component-test)
    - [4.1.8 API Documentation](#418-api-documentation)
    - [4.1.9 Known Issues and Limitations](#419-known-issues-and-limitations)
    - [4.1.10 Unresolved Issues](#4110-unresolved-issues)
  - [4.2 VictoriaMetrics Cluster Mode](#42-victoriametrics-cluster-mode)
    - [4.2.1 Component Description](#421-component-description)
    - [4.2.2 Constraints and Assumptions](#422-constraints-and-assumptions)
    - [4.2.3 Component Design](#423-component-design)
      - [4.2.3.1 Control Flow](#4231-control-flow)
      - [4.2.3.2 Data Flow](#4232-data-flow)
      - [4.2.3.3 Interfaces](#4233-interfaces)
      - [4.2.3.4 Configuration Processing](#4234-configuration-processing)
    - [4.2.4 Security](#424-security)
    - [4.2.5 Resource Utilization](#425-resource-utilization)
  - [4.3 VictoriaLogs Cluster Mode](#43-victorialogs-cluster-mode)
    - [4.3.1 Component Description](#431-component-description)
    - [4.3.2 Component Design](#432-component-design)
      - [4.3.2.1 Control Flow](#4321-control-flow)
      - [4.3.2.2 Data Flow](#4322-data-flow)
      - [4.3.2.3 Interfaces](#4323-interfaces)
    - [4.3.3 Security](#433-security)
    - [4.3.4 Resource Utilization](#434-resource-utilization)
  - [4.4 Kafka Topic Architecture](#44-kafka-topic-architecture)
    - [4.4.1 Component Description](#441-component-description)
    - [4.4.2 Component Design](#442-component-design)
      - [4.4.2.1 Topic Registry](#4421-topic-registry)
      - [4.4.2.2 Kafka User & ACL Design](#4422-kafka-user--acl-design)
      - [4.4.2.3 OME Multi-Topic Architecture](#4423-ome-multi-topic-architecture)
    - [4.4.3 Security](#443-security)
- [5 Traceability Matrix](#5-traceability-matrix)
- [6 Error Handling](#6-error-handling)
- [7 Backward Compatibility](#7-backward-compatibility)
- [Appendix A: Ansible Role File Structure](#appendix-a-ansible-role-file-structure)

---

## 1. Glossary

| Term | Definition |
|------|-----------|
| **Vector** | High-performance, open-source data pipeline tool (Datadog) for collecting, transforming, and routing logs and metrics. Licensed under MPL 2.0. |
| **VictoriaMetrics** | High-performance, cost-effective time-series database for metrics storage and PromQL querying. Deployed in cluster mode with vmstorage, vminsert, and vmselect components. |
| **VictoriaLogs** | Centralized log management engine in the VictoriaMetrics ecosystem, supporting JSON Lines, syslog RFC 5424, and Elasticsearch bulk API ingestion. |
| **vlstorage** | VictoriaLogs cluster component — persistent log storage node storing compressed log data on PVCs. |
| **vlinsert** | VictoriaLogs cluster component — stateless ingestion gateway accepting logs and distributing to vlstorage nodes. |
| **vlselect** | VictoriaLogs cluster component — stateless query gateway fanning out LogsQL queries across vlstorage nodes. |
| **vmstorage** | VictoriaMetrics cluster component — persistent time-series storage node. |
| **vminsert** | VictoriaMetrics cluster component — stateless ingestion gateway accepting Prometheus remote_write. |
| **vmselect** | VictoriaMetrics cluster component — stateless PromQL query gateway. |
| **vmagent** | VictoriaMetrics agent — Prometheus-compatible metrics scraper and forwarder using Kubernetes service discovery. Currently scrapes VictoriaPump on port 2112. |
| **vmagent-vector** | Dedicated vmagent instance deployed as a `prometheus_remote_write` receiver and write-buffer for Vector pods. Accepts remote_write on port 8429, buffers to disk, and forwards to vminsert. Separate from the existing scraper vmagent to isolate failure domains. |
| **VictoriaPump** | Container within the iDRAC telemetry StatefulSet that reads from ActiveMQ and exposes metrics on port 2112 for vmagent to scrape. This is the current iDRAC-to-VictoriaMetrics data path. |
| **KafkaPump** | Container within the iDRAC telemetry StatefulSet that reads from ActiveMQ and produces to the Kafka `idrac` topic. This is a Kafka **producer**, not a consumer. |
| **store_avro_kafka** | LDMS storage daemon plugin that produces metric data to the Kafka `ldms` topic in Avro/JSON encoding. This is a Kafka **producer**, not a consumer. |
| **ActiveMQ** | Embedded message broker (port 61616) within the iDRAC telemetry StatefulSet, acting as the internal bus between the iDRAC Telemetry Receiver and the pump containers (KafkaPump, VictoriaPump). |
| **VLAgent** | VictoriaLogs agent — syslog receiver that forwards logs to VictoriaLogs vlinsert. |
| **vlagent-vector** | Dedicated VictoriaLogs forwarding agent deployed as a log write-buffer for Vector pods. Accepts JSON Lines on an HTTP endpoint (port 9427), buffers to disk, and forwards to vlinsert. **Q2 — required for Vector-OME** log/event sinks. Also required when Vector-iDRAC (future) writes log/event data to VictoriaLogs. |
| **Kafka** | Apache Kafka — distributed streaming platform used as the telemetry data bus. Deployed via Strimzi in KRaft mode. |
| **Strimzi** | Kubernetes operator for managing Apache Kafka clusters, topics, users, and bridges declaratively. |
| **KRaft** | Kafka Raft — Kafka's metadata management protocol replacing ZooKeeper. |
| **iDRAC** | Integrated Dell Remote Access Controller — out-of-band hardware management on Dell PowerEdge servers. |
| **LDMS** | Lightweight Distributed Metric Service — in-band OS-level metric collection for HPC compute nodes. Uses a three-tier architecture: samplers → aggregators → storage daemons. |
| **OME** | OpenManage Enterprise — Dell server management and monitoring console. Publishes telemetry to Kafka via mTLS. |
| **SFM** | Smart Fabric Manager — Dell management console for SONiC-based Ethernet switches. |
| **mTLS** | Mutual TLS — both client and server authenticate via X.509 certificates. |
| **Prometheus remote_write** | Standard HTTP-based protocol for pushing time-series metrics to compatible backends. |
| **PromQL** | Prometheus Query Language — used for querying time-series data in VictoriaMetrics. |
| **LogsQL** | VictoriaLogs query language for searching and filtering log data. |
| **PVC** | Persistent Volume Claim — Kubernetes abstraction for requesting persistent storage. |
| **StatefulSet** | Kubernetes workload API for managing stateful applications with stable network identities and persistent storage. |
| **Deployment** | Kubernetes workload API for managing stateless applications with rolling updates. |
| **ConfigMap** | Kubernetes API object for storing non-confidential configuration data as key-value pairs. |
| **Kustomize** | Kubernetes-native configuration management tool for customizing resource manifests. |
| **Jinja2** | Python-based templating engine used by Ansible for generating configuration files. |
| **Ansible Vault** | Ansible feature for encrypting sensitive data (passwords, keys) at rest. |
| **LoadBalancer** | Kubernetes Service type that provisions an external IP via MetalLB for cluster-external access. |
| **MetalLB** | Bare-metal Kubernetes LoadBalancer implementation using `pod_external_ip_range`. |
| **TOML** | Tom's Obvious, Minimal Language — Vector's native configuration format. |
| **Consumer Group** | Kafka mechanism enabling multiple consumers to share the work of reading a topic in parallel. |
| **Partition** | Kafka topic subdivision enabling parallelism and ordering within each partition. |
| **ACL** | Access Control List — Kafka authorization mechanism for topic/group-level permissions. |
| **RFC 5424** | The Syslog Protocol standard defining structured syslog message format. |
| **SNMP** | Simple Network Management Protocol — used for collecting network device telemetry (Skyway). |
| **OID** | Object Identifier — SNMP address for a manageable resource. |
| **DCGM** | NVIDIA Data Center GPU Manager — daemon and exporter for GPU telemetry. |
| **UFM** | NVIDIA Unified Fabric Manager — management platform for InfiniBand fabrics. |
| **NetQ** | NVIDIA NetQ — Ethernet fabric monitoring and telemetry platform. |
| **Skyway** | NVIDIA Skyway — InfiniBand-to-Ethernet gateway device. |
| **VAST** | VAST Data Platform — flash-based parallel storage cluster. |
| **PowerScale** | Dell PowerScale — scale-out NAS storage platform (OneFS). |
| **PowerVault ME5** | Dell PowerVault ME5 — SAN/DAS block storage array. |
| **OIM** | Omnia Infrastructure Manager — central management host. |
| **Pulp** | Local container/package repository for air-gapped deployments. |

---

## 2. Introduction

### 2.1 Scope

This engineering specification defines **HOW** to build the Kafka-to-Victoria ingestion pipeline using Vector, along with the cluster-mode deployments of VictoriaMetrics and VictoriaLogs, and the Kafka topic architecture supporting iDRAC, LDMS, and OME telemetry sources.

**Q2 Release Scope:**

> **Important:** For the CY26Q2 release, **only Vector-LDMS is deployed by Omnia**. Vector-iDRAC and Vector-OME are **not** part of the Q2 release. See below for rationale.

**Current State (from omnia-bsm code review):**

The existing telemetry codebase has two distinct Kafka producer pipelines and no Kafka consumers:

| Source | Kafka Producer | Kafka Topic | Consumer | Path to VictoriaMetrics |
|--------|---------------|-------------|----------|------------------------|
| **iDRAC** | KafkaPump container (reads ActiveMQ, writes to Kafka) | `idrac` | **None** — topic has no consumer | VictoriaPump container (reads ActiveMQ, exposes port 2112) → vmagent scrapes → VictoriaMetrics |
| **LDMS** | store_avro_kafka plugin (in LDMS storage daemons) | `ldms` | **None** — topic has no consumer | **None** — LDMS metrics are not stored in VictoriaMetrics |

**Critical gap this spec addresses (Q2):**
1. **LDMS metrics have no path to VictoriaMetrics.** LDMS data lands in Kafka via the `store_avro_kafka` plugin but nothing consumes it. Vector-LDMS fills this gap.

**Gap deferred beyond Q2:**
2. **iDRAC Kafka data has no consumer (deferred — not in Q2).** The `idrac` topic receives data from KafkaPump but nothing reads it. The current Dell iDRAC telemetry pipeline produces to a **single `idrac` topic** containing both metrics and events mixed together, which is insufficient for proper Vector content-type routing. Omnia will adopt the **NERSC iDRAC collector** ([https://github.com/NERSC/nersc-idrac](https://github.com/NERSC/nersc-idrac)) which publishes to **two separate Kafka topics** — one for metrics and one for logs — enabling clean Vector routing without content-type classification heuristics. Vector-iDRAC will be enabled in a future release once the NERSC iDRAC collector is integrated.
3. **OME topics need a consumer (Q2 — Omnia-deployed).** OME publishes to `ome.*` topics via the external mTLS listener. Vector-OME is deployed by Omnia in Q2 to consume these topics. Omnia provisions the Kafka topics, ACLs, KafkaUser resources, and deploys the Vector-OME pod (Deployment, ConfigMap, Service) from the telemetry roles.

This spec introduces **Vector-LDMS** and **Vector-OME** as the Q2 Kafka consumers deployed by Omnia, with Vector-iDRAC as the remaining target-state component for a future release.

**Design Principles:**
1. **One consumer per source** — Dedicated Vector pods per source domain (iDRAC, LDMS, OME) to match the existing producer pipeline separation, isolate failure blast radius, and enable independent scaling
2. **Topic-per-source** — Clear Kafka topic naming with regex-based subscription for multi-topic sources (OME)
3. **Cluster-first** — VictoriaMetrics and VictoriaLogs deployed in cluster mode for production HA
4. **Idempotent deployment** — Re-running playbooks produces no unintended changes
5. **Air-gap ready** — All container images served from local Pulp repository
6. **NERSC iDRAC collector for future iDRAC support** — Two-topic architecture (metrics + logs) enables clean Vector routing without heuristic content-type classification
7. **Omnia-owned Vector for all sources** — Omnia team owns the Vector deployment lifecycle for all telemetry sources (iDRAC, LDMS, OME); K8s manifests created in the Omnia telemetry roles

#### 2.1.1 In Scope

**Q2 Release (Omnia-deployed):**

1. **Vector-LDMS pod deployment**: Consumes `ldms` topic — routes metrics to VictoriaMetrics via vmagent-vector (LDMS produces pure metrics, no log routing needed). This is the only Vector pod deployed by Omnia in Q2.
2. **vmagent-vector deployment**: Dedicated vmagent instance acting as a write-buffer between Vector pods and vminsert. Accepts `prometheus_remote_write` on port 8429, buffers to disk, forwards to vminsert. Separate from the existing scraper vmagent.
3. Schema normalization and metric enrichment transforms for LDMS data
4. VictoriaMetrics cluster-mode integration (vmagent-vector → vminsert endpoint)
5. Kafka topic architecture — topic definitions, partitions, ACLs for LDMS
6. Ansible role for Vector-LDMS and vmagent-vector deployment (Jinja2 templates, Kustomize)
7. Configuration via `telemetry_config.yml` with JSON schema validation (feature flags: `telemetry_sources.ldms.metrics_enabled`, `telemetry_bridges.vector_ldms.enabled`)
8. TLS/mTLS for Kafka consumer connections (reusing existing `kafkapump` KafkaUser)
9. Teardown and cleanup of Vector-LDMS and vmagent-vector resources
10. Upgrade scenarios (fresh deploy, redeploy, teardown+redeploy) for Vector-LDMS

**Q2 Release (Omnia infrastructure provisioning for OME):**

11. Kafka topic and ACL provisioning for OME topics (`ome.events`, `ome.alerts`, `ome.inventory`, `ome.telemetry`, `ome.logs`)
12. KafkaUser creation (`vector-ome-user`) with mTLS credentials for Vector-OME to consume from Kafka
13. Feature flags `telemetry_bridges.vector_ome.metrics_enabled` and `telemetry_bridges.vector_ome.logs_enabled` to control provisioning of OME Kafka resources and Vector-OME deployment

**Future Release Design (documented for architecture continuity):**

14. Vector-iDRAC pod design — documented as target-state architecture pending NERSC iDRAC collector integration (separate metrics and logs topics)

#### 2.1.2 Out of Scope

| Item | Rationale |
|------|-----------|
| **Vector-iDRAC deployment (Q2)** | **Not part of Q2 release.** Current Dell iDRAC telemetry produces to a single `idrac` topic with mixed metrics and events. This single-topic architecture does not support clean Vector content-type routing. Omnia will adopt the NERSC iDRAC collector ([https://github.com/NERSC/nersc-idrac](https://github.com/NERSC/nersc-idrac)) which publishes to two separate Kafka topics (one for metrics, one for logs). Vector-iDRAC will be enabled in a future release after NERSC iDRAC collector integration. |
| Grafana dashboard provisioning | Separate capability; not part of data pipeline |
| VLAgent syslog receiver design | Covered in VictoriaLogs cluster HLD (ESPEC-VL-2026-001) |
| UFM/NetQ/Skyway/PowerScale/VAST/PowerVault collector design | Each has dedicated engineering spec |
| SFM direct remote_write to VictoriaMetrics | SFM writes directly to vminsert; no Kafka/Vector path |
| LDMS producer (sampler/aggregator/storage daemon) deployment on compute nodes | Covered in existing LDMS infrastructure |
| Kafka cluster deployment (Strimzi operator, brokers, controllers) | Existing infrastructure; this spec covers topic/user additions only |
| Log-based alerting rules | Out of scope per BSpec |
| Multi-tenant log isolation | Out of scope per BSpec |
| Performance/load testing procedures | Separate test spec |
| Modifications to iDRAC StatefulSet (KafkaPump, VictoriaPump, ActiveMQ, MySQL) | Existing infrastructure unchanged |
| Modifications to LDMS aggregator/storage daemon deployment | Existing infrastructure unchanged |
| VictoriaLogs integration for LDMS | LDMS data is pure metrics; no log/event routing needed |

### 2.2 References

| Source | Type | Title | Description |
|--------|------|-------|-------------|
| Dell Omnia | Internal | FSPEC-TELEM-2026-001 v1.1 | Omnia Telemetry Functional Specification — system behavior requirements |
| Dell Omnia | Internal | BSPEC-TELEM-2026-001 v2.0 | Omnia Telemetry Behaviour Specification — customer-facing behavior |
| Dell Omnia | Internal | ESPEC-VL-2026-001 | VictoriaLogs Cluster Engineering Spec (HLD) |
| Dell Omnia | Internal | ESPEC-PS-2026-001 | PowerScale Telemetry Engineering Spec (HLD) |
| Dell Omnia | Internal | Spec-Driven Development Approach | SDD methodology document |
| Dell Omnia | Confluence | Capability 12691 | Kafka to VictoriaMetrics ingestion via Vector |
| Dell Omnia | Confluence | Capability 23732 | VictoriaLogs database installation |
| Dell Omnia | Codebase | `omnia-bsm/discovery/roles/telemetry/` | Current telemetry Ansible role — source of truth for existing architecture |
| External | Docs | [Vector Documentation](https://vector.dev/docs/) | Upstream Vector configuration reference |
| External | Docs | [VictoriaMetrics Cluster Docs](https://docs.victoriametrics.com/cluster-victoriametrics/) | Upstream cluster deployment reference |
| External | Docs | [VictoriaLogs Cluster Docs](https://docs.victoriametrics.com/victorialogs/) | Upstream log management reference |
| External | Docs | [Strimzi Documentation](https://strimzi.io/docs/operators/latest/overview) | Kafka operator reference |
| External | GitHub | [NERSC iDRAC Collector](https://github.com/NERSC/nersc-idrac) | NERSC iDRAC telemetry collector — publishes to two separate Kafka topics (metrics and logs). Omnia will adopt this in a future release to replace the single-topic Dell iDRAC telemetry pipeline for Vector support. |
| External | GitHub | [OpenManage Enterprise](https://github.com/dell/OpenManage-Enterprise/tree/main) | OME repository — includes Docker Compose reference implementations for Vector-based telemetry consumption. Omnia creates K8s-native Vector-OME manifests in the telemetry roles (not sourced from OME repo). |

---

## 3. Solution Architecture

### 3.1 Constraints and Assumptions

#### 3.1.1 Constraints

| ID | Constraint | Impact |
|----|-----------|--------|
| C-01 | Air-gapped environments have no external registry access | All Vector, VictoriaMetrics, and VictoriaLogs images must be pre-loaded into the local Pulp repository |
| C-02 | VictoriaMetrics cluster mode requires minimum 3 Service K8s worker nodes | Pod anti-affinity rules cannot be satisfied with fewer workers; fallback to single-node mode |
| C-03 | **iDRAC single-topic limitation** — Current Dell iDRAC telemetry produces to a single `idrac` Kafka topic containing both metrics and events mixed together | Vector cannot cleanly route metrics vs. logs from a single mixed-content topic without error-prone heuristic classification. **This is why Vector-iDRAC is not part of Q2.** |
| C-04 | Kafka topic `ldms` uses a fixed name — the store_avro_kafka plugin produces to this topic via `topic=ldms` in ldms config | Vector-LDMS consumer config must match this exact topic name |
| C-05 | OME publishes to 5 topics with `ome.` prefix pattern | Vector-OME (Omnia-deployed, Q2) must use regex subscription `^ome\..*$` to capture all OME topics dynamically |
| C-06 | Strimzi operator must be deployed before Kafka topics/users can be created | Playbook dependency ordering must enforce Strimzi readiness before Vector KafkaUser creation |
| C-07 | Vector pods require mTLS certificates from Strimzi KafkaUser resources | KafkaUser CRs must be created and certificate secrets provisioned before Vector pod startup |
| C-08 | VictoriaLogs cluster mode is relatively new upstream | Pin to a tested release version; perform soak testing at target scale |
| C-09 | LDMS schema is externally managed (NERSC codebase) and uses store_avro_kafka with Avro/JSON encoding | Vector-LDMS transforms must be version-pinned; schema changes may break pipeline |
| C-10 | `pod_external_ip_range` must be configured in `omnia_config.yml` | LoadBalancer services for vminsert/vmselect/vlinsert/vlselect require externally reachable IPs |
| C-11 | KafkaPump and store_avro_kafka both use the existing `kafkapump` Strimzi KafkaUser for mTLS credentials | Vector-LDMS reuses the same `kafkapump` KafkaUser — its broad ACLs (Read/Write on all topics, Read on all consumer groups) already cover consumer access. Only OME Vector requires a new KafkaUser (`vector-ome-user`) because OME is an external producer with a different security domain. |
| C-12 | **NERSC iDRAC collector required for Vector-iDRAC (future)** — The NERSC iDRAC collector ([https://github.com/NERSC/nersc-idrac](https://github.com/NERSC/nersc-idrac)) publishes to two separate Kafka topics (metrics and logs) | Vector-iDRAC support is blocked until Omnia integrates the NERSC iDRAC collector, replacing the current single-topic Dell iDRAC telemetry pipeline |
| C-13 | **Vector-OME is Omnia-deployed (Q2)** — The Omnia team creates Vector-OME K8s manifests in the telemetry roles (`roles/telemetry/templates/telemetry/vector/`) | Omnia provisions both Kafka infrastructure (topics, ACLs, KafkaUser) and the Vector-OME pod when `vector_ome_support=true`. |

#### 3.1.2 Assumptions

| ID | Assumption | Validation |
|----|-----------|------------|
| A-01 | LDMS store_avro_kafka plugin is producing to topic `ldms` when `ldms_support=true` — storage daemons write Avro/JSON encoded metrics to Kafka via mTLS on port 9093 | Verify via topic offset check |
| A-02 | OME is configured externally and produces to `ome.*` topics via external mTLS listener (port 9094) when `vector_ome_support=true` | Operator has run `external_kafka_connect_details.yml` and configured OME |
| A-03 | `telemetry_config.yml` has been validated by L1 JSON schema validation | Playbook entry-point validation |
| A-04 | LDMS data on Kafka topic `ldms` is pure metrics (no log/event content) — LDMS store_avro_kafka uses Avro/JSON encoding with metric fields | Vector-LDMS does not need VictoriaLogs routing |
| A-05 | NERSC iDRAC collector will be integrated in a future release, providing two separate Kafka topics (metrics and logs) to enable Vector-iDRAC | Integration planning in progress |
| A-06 | Omnia team deploys and manages Vector for all telemetry sources (iDRAC, LDMS, OME) using K8s manifests in the telemetry roles | Vector-OME K8s templates created in `roles/telemetry/templates/telemetry/vector/` |

### 3.2 Control Flow

```
Telemetry Playbook Execution (telemetry/telemetry.yml)
    |
    +-- [1] L1 Schema Validation (telemetry_config.yml)
    |       +-- JSON schema validates vector_ldms_support, vector_ome_support, etc.
    |
    +-- [2] L2 Pre-deployment Validation (Python + Ansible)
    |       +-- Check telemetry namespace exists
    |       +-- Check Kafka bootstrap endpoint reachable
    |       +-- Check VictoriaMetrics vminsert endpoint reachable
    |       +-- Check pod_external_ip_range configured
    |
    +-- [3] Feature Flag Evaluation
    |       +-- telemetry_sources.ldms.metrics_enabled?     -> Enable LDMS collection
    |       +-- telemetry_bridges.vector_ldms.enabled?      -> Deploy Vector-LDMS pod (Q2)
    |       +-- telemetry_bridges.vector_ome.metrics_enabled? -> Deploy Vector-OME metrics routing (Q2)
    |       +-- telemetry_bridges.vector_ome.logs_enabled?    -> Deploy Vector-OME logs routing (Q2)
    |       +-- vector_idrac?                               -> NOT SUPPORTED IN Q2 (deferred)
    |
    +-- [4] Secret Provisioning
    |       +-- Verify existing kafkapump KafkaUser secret exists (reused by Vector-LDMS)
    |       +-- Create KafkaUser CR for vector-ome-user (if vector_ome_support=true)
    |       +-- Wait for Strimzi to provision vector-ome-user mTLS certificate secret
    |       +-- Extract TLS CA cert from kafka-cluster-ca-cert
    |
    +-- [5] Generate Vector Configuration (Jinja2 Templates) — LDMS only in Q2
    |       +-- vector-ldms-config.toml.j2  -> ConfigMap
    |       +-- vmagent-vector deployment manifest
    |       +-- Kustomize resource list update
    |
    +-- [6] Apply Kubernetes Manifests (Kustomize)
    |       +-- vmagent-vector Deployment (write-buffer for Vector → vminsert)
    |       +-- Vector-LDMS Deployment + ConfigMap + Service (if vector_ldms_support=true)
    |       +-- KafkaUser CR (vector-ome-user, if vector_ome_support=true)
    |       +-- KafkaTopic CRs for OME topics (if vector_ome_support=true)
    |
    +-- [7] Readiness Verification
    |       +-- Wait for vmagent-vector pod to reach Ready state
    |       +-- Wait for Vector-LDMS pod to reach Ready state
    |       +-- Verify Kafka consumer group registration
    |       +-- Verify data flow: produce test message -> Vector-LDMS -> vmagent-vector -> VictoriaMetrics
    |
    +-- [8] Emit Deployment Report
            +-- Write status to /opt/omnia/telemetry/vector_deployment_report.yml
```

**Deployment Gate Logic:**

| Gate | Check | Condition | Action on Failure |
|------|-------|-----------|-------------------|
| **Gate 1: Feature Flags** | Evaluate `vector_ldms_support` and `vector_ome_support` | All disabled | Skip Vector deployment entirely |
| **Gate 2a: Namespace** | Verify `telemetry` namespace exists | Missing | Fail playbook with prerequisite error |
| **Gate 2b: Kafka** | Verify Kafka bootstrap endpoint reachable (`kafka-kafka-bootstrap:9092`) | Unreachable | Fail playbook with connectivity error |
| **Gate 2c: LDMS Topic** | Verify `ldms` topic exists and has messages | Topic absent | Fail if `vector_ldms_support=true` |
| **Gate 2d: External Listener (OME)** | Kafka external listener (port 9094) configured | Not configured | Fail if `vector_ome_support=true` |
| **Gate 3a: vminsert** | Verify vminsert endpoint reachable (`vminsert:8480`) | Unreachable | Fail playbook |
| **Deploy: vmagent-vector** | Deploy vmagent-vector write-buffer pod | Any Vector pipeline enabled | vmagent-vector must be Ready before Vector pods |
| **Deploy: LDMS** | Verify kafkapump secret exists, deploy Vector-LDMS pod | `vector_ldms_support=true` | — |
| **Provision: OME Kafka** | Create vector-ome-user KafkaUser CR, provision OME topic ACLs | `vector_ome_support=true` | — |

Detailed implementation of gate logic and deployment tasks is specified in the Component Spec.

### 3.3 Data Flow Diagram

#### 3.3.1 Current State — Existing Producer Pipelines (Before Vector)

```
+============================================================================================+
|                     Service Kubernetes Cluster (telemetry namespace)                         |
|                                                                                             |
|  IDRAC TELEMETRY STATEFULSET (single pod, 5 containers)                                    |
|  +---------------------------------------------------------------------------+              |
|  |                                                                           |              |
|  |  iDRAC Devices ----> iDRAC Telemetry Receiver (container)                 |              |
|  |                            |                                              |              |
|  |                            v                                              |              |
|  |                      ActiveMQ (container, port 61616)                     |              |
|  |                        /                       \                          |              |
|  |                       v                         v                         |              |
|  |  KafkaPump (container)              VictoriaPump (container)              |              |
|  |  [Kafka PRODUCER]                   [Metrics exporter, port 2112]         |              |
|  |  Reads ActiveMQ -> produces         Reads ActiveMQ -> exposes /metrics    |              |
|  |  to Kafka topic "idrac"             for vmagent to scrape                 |              |
|  |  via mTLS on port 9093              (Prometheus exposition format)        |              |
|  |       |                                     |                             |              |
|  +-------|-------------------------------------|-----------------------------+              |
|          |                                     |                                            |
|          v                                     v                                            |
|  +---------------+                    +-----------------+                                   |
|  | Kafka Broker  |                    | vmagent         |                                   |
|  | Topic: idrac  |                    | (scrapes :2112) |                                   |
|  | [NO CONSUMER] |                    +--------+--------+                                   |
|  +---------------+                             |                                            |
|                                                v                                            |
|                                     +-------------------+                                   |
|                                     | VictoriaMetrics   |                                   |
|  LDMS THREE-TIER PIPELINE           | (vminsert:8480)   |                                   |
|                                     +-------------------+                                   |
|  Compute Nodes (LDMS Samplers, port 10001)                                                  |
|          |                                                                                  |
|          v                                                                                  |
|  LDMS Aggregators (nersc-ldms-aggr StatefulSet, port 6001)                                  |
|          |                                                                                  |
|          v                                                                                  |
|  LDMS Storage Daemons (nersc-ldms-store StatefulSets, port 7001)                            |
|          |                                                                                  |
|          v                                                                                  |
|  store_avro_kafka plugin [Kafka PRODUCER]                                                   |
|  Encodes metrics as Avro/JSON -> produces                                                   |
|  to Kafka topic "ldms" via mTLS on port 9093                                                |
|          |                                                                                  |
|          v                                                                                  |
|  +---------------+                                                                          |
|  | Kafka Broker  |                                                                          |
|  | Topic: ldms   |                                                                          |
|  | [NO CONSUMER] |   <---- GAP: LDMS metrics are NOT in VictoriaMetrics                     |
|  +---------------+                                                                          |
|                                                                                             |
+============================================================================================+
```

#### 3.3.2 Target State — With Vector Consumers

> **Note:** For Q2, Vector-LDMS and Vector-OME are deployed by Omnia. Vector-iDRAC is deferred pending NERSC iDRAC collector integration. The diagram below shows the full target-state architecture; Q2-active components are marked.

```
+============================================================================================+
|                     Service Kubernetes Cluster (telemetry namespace)                         |
|                                                                                             |
|  PRODUCERS (existing, unchanged)       KAFKA BUS             VECTOR CONSUMERS               |
|  --------------------------------      ---------             ----------------------         |
|                                                                                             |
|  +------------------+                +-------------+                                        |
|  | iDRAC StatefulSet|                |             |                                        |
|  | +----------+     |    produce     | Topic:idrac |   [FUTURE — NOT IN Q2]                 |
|  | |KafkaPump |-----+-------------->| (single      |   Vector-iDRAC deferred:               |
|  | +----------+     |  (mTLS:9093)  |  mixed topic)|   Current iDRAC telemetry has           |
|  | +----------+     |               |             |   single topic with mixed content.       |
|  | |Victoria- |     |               +-------------+   NERSC iDRAC collector will provide     |
|  | |Pump:2112 |--> vmagent (existing path)             2 separate topics (metrics + logs).    |
|  | +----------+     |                                  Repo: github.com/NERSC/nersc-idrac    |
|  +------------------+                                                                        |
|                                                                                             |
|  +------------------+                                                                        |
|  | LDMS Storage     |                                                                        |
|  | Daemons          |                                                                        |
|  | +----------+     |               +-------------+                                         |
|  | |store_avro|     |    produce    |             |   +------------------------------+      |
|  | |_kafka    |-----+------------>| Topic: ldms  |   | Vector-LDMS Pod [Q2 ACTIVE]  |      |
|  | +----------+     |  (mTLS:9093) | (configurable|-->| Consumer group:              |      |
|  +------------------+              |  partitions) |   |   vector-ldms-group          |      |
|                                    |             |   |                              |      |
|                                    +-------------+   | Source:                      |      |
|                                                      |   kafka_ldms (topic: ldms)   |      |
|                                                      |                              |      |
|                                                      | Transforms:                  |      |
|                                                      |   ldms_schema_normalizer     |      |
|                                                      |   metric_enricher            |      |
|                                                      |                              |      |
|                                                      | Sinks:                       |      |
|                                                      |   metrics -> vmagent-vector  |      |
|                                                      |             :8429            |      |
|                                                      +------------------------------+      |
|                                                                    |                        |
|                                                                    v                        |
|                                                      +------------------------------+      |
|                                                      | vmagent-vector [Q2 ACTIVE]   |      |
|                                                      | (write-buffer)               |      |
|                                                      | Accepts: remote_write :8429  |      |
|                                                      | Buffers: disk WAL            |      |
|                                                      | Forwards: -> vminsert:8480   |      |
|                                                      +------------------------------+      |
|                                                                    |                        |
|  +------------------+              +---------------+               v                        |
|  | OME Appliance    |   produce    |               |  +-------------------+                 |
|  | (External)       |------------>| Topics:        |  | VictoriaMetrics   |                 |
|  |                  | mTLS:9094   |  ome.events    |  | (vminsert:8480)   |                 |
|  +------------------+              |  ome.alerts   |  +-------------------+                 |
|                                    |  ome.inventory |                                        |
|                                    |  omnia.telem  |  | Vector-OME Pod               |      |
|                                    |  ome.logs     |  | [Q2 ACTIVE — OMNIA-DEPLOYED] |      |
|                                    +---------------+->|                              |      |
|                                                       |                              |      |
|   +-------------------+                               |  metrics -> vmagent-vector   |      |
|   | vlagent-vector    |<--- logs (from OME)-----------|  logs -> vlagent-vector      |      |
|   | [Q2 ACTIVE —      |                               +------------------------------+      |
|   |  OMNIA-DEPLOYED]  |                                                                     |
|   | Accepts: HTTP     |                                                                     |
|   | :9427             |                                                                     |
|   | Forwards: ->      |                                                                     |
|   |  vlinsert:9428    |                                                                     |
|   +-------------------+                                                                     |
+============================================================================================+
```

#### 3.3.3 Sequence Diagram — Vector-iDRAC Ingestion (FUTURE — Not in Q2)

> **Note:** This sequence diagram documents the future-state design for Vector-iDRAC, pending NERSC iDRAC collector integration. The current Dell iDRAC telemetry produces to a single `idrac` topic with mixed content. The NERSC iDRAC collector ([https://github.com/NERSC/nersc-idrac](https://github.com/NERSC/nersc-idrac)) will provide two separate Kafka topics (metrics and logs), enabling the clean routing shown below.

```
iDRAC         ActiveMQ      KafkaPump      Kafka Broker    Vector-iDRAC   vmagent-vector  vminsert  vlagent-vector  vlinsert
Receiver         |              |               |               |              |            |            |            |
  |-- push ----->|              |               |               |              |            |            |            |
  |              |-- deliver -->|               |               |              |            |            |            |
  |              |              |-- produce --->|               |              |            |            |            |
  |              |              | (idrac topic) |               |              |            |            |            |
  |              |              |               |-- fetch ----->|              |            |            |            |
  |              |              |               |<-- messages --|              |            |            |            |
  |              |              |               |               |              |            |            |            |
  |              |              |               |               |-- classify ->|            |            |            |
  |              |              |               |               | (is_metric?) |            |            |            |
  |              |              |               |               |              |            |            |            |
  |              |              |               |               |== IF METRIC =|            |            |            |
  |              |              |               |               |-- remote_ -->|            |            |            |
  |              |              |               |               |   write      |            |            |            |
  |              |              |               |               |              |-- fwd ---->|            |            |
  |              |              |               |               |              |<-- 204 ----|            |            |
  |              |              |               |               |              |            |            |            |
  |              |              |               |               |== IF LOG/EVT |============|============|            |
  |              |              |               |               |-- POST json -|------------|----------->|            |
  |              |              |               |               |              |            |            |-- fwd ---->|
  |              |              |               |               |              |            |            |<-- 200 ----|
  |              |              |               |               |              |            |            |            |
  |              |              |               |               |-- commit --->|            |            |            |
  |              |              |               |               |  (offset)    |            |            |            |
```

#### 3.3.4 Sequence Diagram — Vector-LDMS Ingestion (Q2 Active — Omnia-deployed)

```
LDMS Samplers    Aggregators   Storage Daemons   Kafka Broker   Vector-LDMS    vmagent-vector   vminsert
     |               |              |                 |              |               |              |
     |-- metrics --->|              |                 |              |               |              |
     |               |-- forward -->|                 |              |               |              |
     |               |              |-- produce ----->|              |               |              |
     |               |              | (store_avro_    |              |               |              |
     |               |              |  kafka plugin)  |              |               |              |
     |               |              | (ldms topic)    |              |               |              |
     |               |              |                 |-- fetch ---->|               |              |
     |               |              |                 |<-- messages -|               |              |
     |               |              |                 |              |               |              |
     |               |              |                 |              |-- normalize ->|              |
     |               |              |                 |              | (LDMS schema  |              |
     |               |              |                 |              |  to Prometheus)|              |
     |               |              |                 |              |               |              |
     |               |              |                 |              |-- remote_ --->|              |
     |               |              |                 |              |   write       |              |
     |               |              |                 |              |               |-- fwd ------>|
     |               |              |                 |              |               |<-- 204 ------|
     |               |              |                 |              |               |              |
     |               |              |                 |              |-- commit ---->|              |
     |               |              |                 |              |  (offset)     |              |
```

#### 3.3.5 Sequence Diagram — Vector-OME Ingestion (Q2 — Omnia-deployed)

> **Note:** Vector-OME is deployed by Omnia from the telemetry roles (K8s manifests in `roles/telemetry/templates/telemetry/vector/`). Omnia provisions both the Kafka infrastructure (topics, ACLs, KafkaUser `vector-ome-user`) and the Vector-OME pod.

```
OME Appliance   Kafka External     Kafka Broker     Vector-OME      vmagent-vector  vminsert  vlagent-vector  vlinsert
    |           Listener(9094)        |                 |                |            |            |            |
    |-- mTLS -->|                     |                 |                |            |            |            |
    | produce   |-- route ----------->|                 |                |            |            |            |
    | ome.*     |                     |                 |                |            |            |            |
    |           |                     |-- fetch ------->|                |            |            |            |
    |           |                     |<-- messages ----|                |            |            |            |
    |           |                     |                 |                |            |            |            |
    |           |                     |                 |-- route by --->|            |            |            |
    |           |                     |                 |   topic name   |            |            |            |
    |           |                     |                 |                |            |            |            |
    |           |                     |                 |  ome.inventory-|-> vmagent  |            |            |
    |           |                     |                 |  omnia.telem --|-> -vector  |            |            |
    |           |                     |                 |                |-- fwd ---->|            |            |
    |           |                     |                 |                |            |            |            |
    |           |                     |                 |  ome.events ---|------------|-> vlagent  |            |
    |           |                     |                 |  ome.alerts ---|------------|-> -vector  |            |
    |           |                     |                 |  ome.logs -----|------------|            |-- fwd ---->|
    |           |                     |                 |                |            |            |            |
```

### 3.4 Actor/Action Matrix

| Actor | Action | Authorization | Notes |
|-------|--------|---------------|-------|
| **Administrator** | Deploy/redeploy/teardown Vector-LDMS pipeline | Allowed | Full OIM access; runs telemetry playbook |
| **Administrator** | Configure `telemetry_config.yml` | Allowed | Sets feature flags in `telemetry_sources` (e.g., `ldms.metrics_enabled`, `dcgm.metrics_enabled`) and `telemetry_bridges` (e.g., `vector_ldms.enabled`, `vector_ome.metrics_enabled`, `vector_ome.logs_enabled`) |
| **Administrator** | Query metrics via vmselect (PromQL) | Allowed | Read access to all telemetry data |
| **Administrator** | Query logs via vlselect (LogsQL) | Allowed | Read access to all log data |
| **OME Appliance** | Produce to `ome.*` Kafka topics | Allowed (mTLS) | External producer; authenticated via Strimzi KafkaUser certs |
| **Omnia Team** | Deploy and manage all Vector pods (LDMS, OME, iDRAC) | Allowed | K8s manifests in Omnia telemetry roles; Vector-LDMS and Vector-OME are Q2 active; Vector-iDRAC is a future release |
| **iDRAC KafkaPump** | Produce to `idrac` Kafka topic | Allowed (mTLS) | Uses existing `kafkapump` KafkaUser; internal producer within iDRAC StatefulSet |
| **LDMS store_avro_kafka** | Produce to `ldms` Kafka topic | Allowed (mTLS) | Uses existing `kafkapump` KafkaUser; internal producer within LDMS storage daemons |
| **Vector-LDMS** | Consume from `ldms` topic | Allowed (mTLS) | KafkaUser: `kafkapump` (reused); consumer group: `vector-ldms-group`. Q2 active — deployed by Omnia. |
| **Vector-OME** | Consume from `ome.*` topics | Allowed (mTLS) | KafkaUser: `vector-ome-user` (provisioned by Omnia). Q2 active — Omnia-deployed. |
| **Vector-LDMS** | Write metrics to vmagent-vector | Allowed (HTTP) | In-cluster HTTP to vmagent-vector:8429; vmagent-vector forwards to vminsert |
| **Non-Admin** | View Vector pod status | Allowed (read-only) | `kubectl get pods -n telemetry` |
| **Viewer** | Query metrics/logs | Allowed (read-only) | Via vmselect/vlselect endpoints |

### 3.5 Threat Model

| Threat ID | Threat | Attack Vector | Likelihood | Impact | Mitigation | Residual Risk |
|-----------|--------|---------------|------------|--------|------------|---------------|
| T-01 | Unauthorized Kafka consumption | Rogue consumer joins consumer group | Low | High — data exfiltration | mTLS authentication enforced on all Kafka listeners; ACL-based authorization per KafkaUser | Low — requires compromised mTLS cert |
| T-02 | Man-in-the-middle on Kafka traffic | Network interception between Vector and Kafka | Low | High — data tampering | TLS encryption on all Kafka listeners (9092, 9093, 9094); no plaintext allowed | Negligible |
| T-03 | Credential exposure in Vector config | Secrets embedded in ConfigMap | Medium | High — mTLS cert leak | Certificates mounted as Kubernetes Secret volumes; `no_log: true` in Ansible tasks; no certs in ConfigMaps | Low — requires K8s API access |
| T-04 | Data injection via Kafka | Malicious producer writes to telemetry topics | Low | Medium — polluted metrics/logs | ACL enforcement: only authorized KafkaUsers can produce to specific topics | Low |
| T-05 | Denial of service via topic flooding | OME or rogue producer floods Kafka topics | Medium | High — pipeline saturation | Kafka quotas, partition count limits, Vector rate limiting via `max_bytes` config | Medium — large-scale attacks may still impact |
| T-06 | Supply chain — compromised Vector image | Tampered container image | Low | Critical — arbitrary code execution | Pin to specific image digest; air-gapped environments use verified local Pulp images | Low |
| T-07 | VictoriaMetrics unauthorized writes | Rogue writer pushes to vminsert | Low | Medium — data pollution | In-cluster TLS on vminsert; network policies limit source pods | Low |
| T-08 | Log data loss during Vector restart | Vector pod restart loses in-flight data | Medium | Medium — temporary data gap | Kafka consumer offsets committed only after successful write to Victoria; on restart, replay from last committed offset | Low — at-least-once delivery |

---

## 4. High Level Design

### 4.1 Vector — Kafka-to-Victoria Ingestion Pipeline

#### 4.1.1 Component Description

Vector is the data routing and transformation layer that consumes telemetry data from Kafka topics and delivers it to VictoriaMetrics (metrics) and VictoriaLogs (logs/events). It replaces the need for custom consumer applications and provides a declarative, configuration-driven pipeline.

> **Q2 Scope:** **Vector-LDMS** and **Vector-OME** are deployed by Omnia in Q2. Vector-iDRAC is deferred (see below).

**Architecture Decision: Per-Source Vector Pods**

| Pod | Topics Consumed | Consumer Group | Q2 Status | Rationale |
|-----|----------------|----------------|-----------|-----------|
| **vector-ldms** | `ldms` | `vector-ldms-group` | **Q2 Active — Omnia-deployed** | LDMS produces pure metrics in Avro/JSON format via `store_avro_kafka`; requires LDMS-specific schema normalization (NERSC format to Prometheus labels). No VictoriaLogs routing needed. |
| **vector-idrac** | `idrac-metrics`, `idrac-logs` (NERSC collector topics) | `vector-idrac-group` | **Deferred — Not in Q2** | Current Dell iDRAC telemetry produces to a single `idrac` topic with mixed metrics and events — insufficient for clean Vector routing. Omnia will adopt the NERSC iDRAC collector ([https://github.com/NERSC/nersc-idrac](https://github.com/NERSC/nersc-idrac)) which publishes to two separate topics (metrics and logs). |
| **vector-ome** | `ome.events`, `ome.alerts`, `ome.inventory`, `ome.telemetry`, `ome.logs` | `vector-ome-group` | **Q2 Active — Omnia-deployed** | Omnia deploys Vector-OME from telemetry roles when `vector_ome_support=true`. OME publishes to 5 topics via external mTLS listener. Omnia provisions Kafka infrastructure (topics, ACLs, KafkaUser) and the Vector-OME pod. |

**Why Vector-iDRAC is Not Part of Q2:**

The current Dell iDRAC telemetry pipeline has a fundamental limitation: KafkaPump produces all iDRAC data (metrics, events, logs, lifecycle messages) to a **single `idrac` Kafka topic**. This means Vector would need heuristic content-type classification (e.g., "is `MetricValue` numeric?") to route metrics to VictoriaMetrics and logs to VictoriaLogs. Such heuristics are fragile and error-prone.

The NERSC iDRAC collector ([https://github.com/NERSC/nersc-idrac](https://github.com/NERSC/nersc-idrac)) solves this by publishing to **two separate Kafka topics** — one for metrics and one for logs. This clean topic-level separation enables deterministic Vector routing without content-type guessing. Vector-iDRAC will be enabled in a future release once the NERSC iDRAC collector is integrated into Omnia.

**Separate Consumer Groups:** Each Vector pod uses its own consumer group (`vector-ldms-group`, `vector-ome-group`, `vector-idrac-group` (future)), matching the established Kafka Bridge verification pattern. Separate groups ensure: (1) no rebalance coupling — restarting one pod does not pause the other, (2) independent offset tracking and lag monitoring per source, (3) independent scaling per topic.

**Component Summary (Q2):**

| Component | K8s Type | Replicas | Image | Purpose | Managed By |
|-----------|----------|----------|-------|---------|------------|
| vmagent-vector | Deployment | 1 | victoriametrics/vmagent:v1.117.1 | Write-buffer: accepts `prometheus_remote_write` from Vector pods on port 8429, buffers to disk, forwards to vminsert:8480 | **Omnia (Q2)** |
| vector-ldms | Deployment | 1 | timberio/vector:0.54.0 | Consume `ldms` → transform → vmagent-vector (metrics only) | **Omnia (Q2)** |
| vector-ldms-config | ConfigMap | — | — | Vector TOML configuration for LDMS pipeline | **Omnia (Q2)** |
| vector-ome-user | KafkaUser (Strimzi) | — | — | mTLS credentials and ACLs for OME consumer | **Omnia provisions** |
| kafkapump | KafkaUser (Strimzi) | — | — | Existing mTLS credentials reused by Vector-LDMS (shared with store_avro_kafka producers) | Existing |
| vlagent-vector | Deployment | 1 | (TBD) | Log write-buffer: accepts JSON Lines from Vector pods on port 9427, buffers to disk, forwards to vlinsert:9428 | **Omnia (Q2)** |
| vector-ome | Deployment | 1 | timberio/vector:0.54.0 | Consume `ome.*` topics → vmagent-vector (metrics) + vlagent-vector (logs) | **Omnia (Q2)** |
| vector-idrac | Deployment | 1 | timberio/vector:0.54.0 | Consume NERSC iDRAC topics → vmagent-vector (metrics) + vlagent-vector (logs) | **Future release** |

#### 4.1.2 Constraints and Assumptions

**Component-Level Constraints:**

| ID | Component | Constraint |
|----|-----------|-----------|
| CC-01 | Vector-LDMS | Must consume from exactly one topic: `ldms` — name is fixed by the store_avro_kafka plugin config (`topic=ldms`) |
| CC-02 | Vector-OME | Must use regex topic subscription `^ome\..*$` to handle all 5 OME topics |
| CC-03 | All Vector pods | Must commit Kafka offsets only after successful write to Victoria backend (at-least-once semantics) |
| CC-04 | All Vector pods | TOML config format required (Vector native); not YAML |
| CC-05 | Vector-OME | All OME topics follow consistent `ome.*` naming pattern — single regex `^ome\..*$` captures all topics |
| CC-06 | All Vector pods | Must support idempotent redeployment — `kubectl apply` of same manifests produces no side effects |
| CC-07 | Vector-LDMS | No VictoriaLogs sink needed — LDMS data is pure metrics from the store_avro_kafka plugin |
| CC-08 | Vector-iDRAC (future) | **Blocked on NERSC iDRAC collector integration.** Current single `idrac` topic with mixed content does not support clean Vector routing. NERSC collector provides separate metrics and logs topics. |
| CC-09 | Vector-OME | **Omnia-deployed (Q2).** K8s manifests created in Omnia telemetry roles. Omnia provisions both Kafka resources and the Vector-OME pod when `vector_ome_support=true`. |

**Component-Level Assumptions:**

| ID | Component | Assumption |
|----|-----------|-----------|
| CA-01 | Vector-LDMS | LDMS data on Kafka `ldms` topic is Avro/JSON encoded by the `store_avro_kafka` plugin with `decomposition=/ldms_bin/decomp.json`. Fields vary by LDMS sampler plugin. |
| CA-02 | Vector-OME | OME data is JSON; topic name indicates data type (events/alerts → logs, inventory/telemetry → metrics) |
| CA-03 | Vector-LDMS | Vector sinks to vmagent-vector on `http://vmagent-vector.telemetry.svc.cluster.local:8429/api/v1/write` (HTTP); vmagent-vector forwards to vminsert on `https://vminsert.telemetry.svc.cluster.local:8480/insert/0/prometheus/api/v1/write` (TLS) |
| CA-04 | Vector-iDRAC (future) | NERSC iDRAC collector will produce to two separate Kafka topics; exact topic names to be confirmed during integration |
| CA-05 | Vector-OME | Omnia team owns Vector-OME pod deployment, configuration, and lifecycle; K8s manifests created in telemetry roles |

#### 4.1.3 Component Design

##### 4.1.3.1 Control Flow

**Vector-iDRAC Pod Lifecycle (FUTURE — Not in Q2):**

> **Note:** This control flow is documented for architecture continuity. Vector-iDRAC is not deployed in Q2. It will be enabled in a future release once the NERSC iDRAC collector ([https://github.com/NERSC/nersc-idrac](https://github.com/NERSC/nersc-idrac)) is integrated, providing separate metrics and logs Kafka topics instead of the current single mixed-content `idrac` topic.

```
+===================== Vector-iDRAC Control Flow ========================+
|                                                                        |
|  Pod Start                                                             |
|    |                                                                   |
|    v                                                                   |
|  Load Configuration (from ConfigMap: vector-idrac-config)              |
|    |-- [sources] kafka_idrac: topic=idrac, group=vector-idrac-group    |
|    |-- [transforms] content_type_router                                |
|    |-- [transforms] idrac_schema_normalizer                            |
|    |-- [transforms] metric_enricher                                    |
|    |-- [sinks] victoria_metrics: prometheus_remote_write -> vmagent-vector:8429  |
|    |-- [sinks] victoria_logs: http json -> vlagent-vector:9427                  |
|    |                                                                   |
|    v                                                                   |
|  Initialize Kafka Consumer                                             |
|    |-- Connect to kafka-kafka-bootstrap:9093 (mTLS)                    |
|    |-- Load TLS certs from /etc/vector/kafka-certs/                    |
|    |-- Join consumer group: vector-idrac-group                         |
|    |-- Subscribe to topic: idrac                                       |
|    |                                                                   |
|    v                                                                   |
|  +-- Main Processing Loop --+                                          |
|  |  [1] Fetch batch from Kafka (max_bytes per partition)               |
|  |  [2] Deserialize messages (JSON from KafkaPump)                     |
|  |  [3] Route: content_type_router                                     |
|  |      +-- Numeric telemetry (MetricValue) -> metric path             |
|  |      +-- Event/log/lifecycle messages -> log path                   |
|  |  [4] Transform: idrac_schema_normalizer (iDRAC JSON -> Prom labels) |
|  |  [5] Enrich: add source_subsystem=idrac, topic_name, ingestion_ts  |
|  |  [6] Sink: metrics -> vmagent-vector via prometheus_remote_write    |
|  |  [7] Sink: logs -> vlagent-vector via HTTP POST (JSON Lines)        |
|  |  [8] Commit Kafka offsets on success                                |
|  +-------------------------------+                                     |
|                                                                        |
|  Health Check: /health endpoint on port 8686                           |
|  Metrics: /metrics endpoint on port 9598 (Vector internal metrics)     |
|                                                                        |
+========================================================================+
```

**Vector-LDMS Pod Lifecycle (Q2 Active — Omnia-deployed):**

```
+===================== Vector-LDMS Control Flow =========================+
|                                                                        |
|  Pod Start                                                             |
|    |                                                                   |
|    v                                                                   |
|  Load Configuration (from ConfigMap: vector-ldms-config)               |
|    |-- [sources] kafka_ldms: topic=ldms, group=vector-ldms-group       |
|    |-- [transforms] ldms_schema_normalizer                             |
|    |-- [transforms] metric_enricher                                    |
|    |-- [sinks] victoria_metrics: prometheus_remote_write -> vmagent-vector:8429 |
|    |-- (NO victoria_logs sink -- LDMS is pure metrics)                 |
|    |                                                                   |
|    v                                                                   |
|  Initialize Kafka Consumer                                             |
|    |-- Connect to kafka-kafka-bootstrap:9093 (mTLS)                    |
|    |-- Load TLS certs from /etc/vector/kafka-certs/                    |
|    |-- Join consumer group: vector-ldms-group                          |
|    |-- Subscribe to topic: ldms                                        |
|    |                                                                   |
|    v                                                                   |
|  +-- Main Processing Loop --+                                          |
|  |  [1] Fetch batch from Kafka (max_bytes per partition)               |
|  |  [2] Deserialize messages (Avro/JSON from store_avro_kafka)         |
|  |  [3] Transform: ldms_schema_normalizer                              |
|  |      Convert LDMS fields to Prometheus labels:                      |
|  |        __name__ = "{plugin}_{metric_name}"                          |
|  |        instance = host                                              |
|  |        job = "ldms"                                                 |
|  |        plugin = plugin                                              |
|  |        component = component                                        |
|  |  [4] Enrich: add source_subsystem=ldms, topic_name, ingestion_ts   |
|  |  [5] Sink: metrics -> vmagent-vector via prometheus_remote_write    |
|  |  [6] Commit Kafka offsets on success                                |
|  +-------------------------------+                                     |
|                                                                        |
|  Health Check: /health endpoint on port 8687                           |
|  Metrics: /metrics endpoint on port 9599 (Vector internal metrics)     |
|                                                                        |
+========================================================================+
```

**Vector-OME Pod Lifecycle (Q2 — Omnia-deployed):**

> **Note:** Vector-OME is deployed by Omnia from the telemetry roles when `vector_ome_support=true`. Omnia provisions both the Kafka resources (topics, ACLs, `vector-ome-user` KafkaUser) and the Vector-OME pod (Deployment, ConfigMap, Service).

```
+===================== Vector-OME Control Flow ==========================+
|                                                                        |
|  Pod Start                                                             |
|    |                                                                   |
|    v                                                                   |
|  Load Configuration (from ConfigMap: vector-ome-config)                |
|    |-- [sources] kafka_ome: topic_regex=^(ome\..*|omnia\.telemetry)$   |
|    |             group=vector-ome-group                                |
|    |-- [transforms] ome_topic_router (route by topic name)             |
|    |-- [transforms] metric_enricher                                    |
|    |-- [sinks] victoria_metrics -> vmagent-vector:8429                 |
|    |-- [sinks] victoria_logs -> vlagent-vector:9427                    |
|    |                                                                   |
|    v                                                                   |
|  Initialize Kafka Consumer                                             |
|    |-- Connect to kafka-kafka-bootstrap:9093 (mTLS)                    |
|    |-- Load TLS certs from /etc/vector/kafka-certs/                    |
|    |-- Join consumer group: vector-ome-group                           |
|    |-- Subscribe via regex: ^(ome\..*|omnia\.telemetry)$               |
|    |                                                                   |
|    v                                                                   |
|  +-- Main Processing Loop --+                                          |
|  |  [1] Fetch batch from Kafka                                         |
|  |  [2] Deserialize messages (JSON)                                    |
|  |  [3] Route by topic name:                                           |
|  |      +-- ome.events     -> logs path -> vlagent-vector              |
|  |      +-- ome.alerts     -> logs path -> vlagent-vector              |
|  |      +-- ome.logs       -> logs path -> vlagent-vector              |
|  |      +-- ome.inventory  -> metrics path -> vmagent-vector           |
|  |      +-- ome.telemetry -> metrics path -> vmagent-vector           |
|  |  [4] Enrich: add source=ome, topic_name labels                     |
|  |  [5] Sink to appropriate Victoria backend                           |
|  |  [6] Commit Kafka offsets on success                                |
|  +-------------------------------+                                     |
|                                                                        |
|  Health Check: /health endpoint on port 8688                           |
|  Metrics: /metrics endpoint on port 9600 (Vector internal metrics)     |
|                                                                        |
+========================================================================+
```

##### 4.1.3.2 Data Flow

**iDRAC Data Transformation Chain (FUTURE — Not in Q2):**

> **Note:** This transformation chain will be redesigned when the NERSC iDRAC collector is integrated. The NERSC collector publishes to separate metrics and logs topics, eliminating the need for the `content_type_router` heuristic shown below.

```
Kafka Topic: idrac
    |
    | [source: kafka] JSON message (produced by KafkaPump from ActiveMQ)
    | Fields: MetricId, MetricValue, Timestamp, Context, SystemInfo
    v
content_type_router transform
    |
    +-- MetricValue is numeric -> METRIC PATH
    |   |
    |   v
    |   idrac_schema_normalizer transform
    |   |  Convert iDRAC JSON to Prometheus labels:
    |   |    __name__ = MetricId
    |   |    value = MetricValue
    |   |    context = Context
    |   v
    |   metric_enricher transform
    |   |  Add labels:
    |   |    source_subsystem = "idrac"
    |   |    topic_name = "idrac"
    |   |    ingestion_timestamp = now()
    |   v
    |   Prometheus remote_write -> vmagent-vector:8429 -> vminsert:8480
    |
    +-- Event/log/lifecycle message -> LOG PATH
        |
        v
        log_enricher transform
        |  Add fields:
        |    _msg_source = "idrac"
        |    _msg_topic = "idrac"
        |    _msg_timestamp = Timestamp
        v
        HTTP POST JSON Lines -> vlagent-vector:9427 -> vlinsert:9428
```

**LDMS Data Transformation Chain (Q2 Active):**

```
Kafka Topic: ldms
    |
    | [source: kafka] Avro/JSON message (produced by store_avro_kafka plugin)
    | Fields: metric_name, value, timestamp, host, plugin, component
    | Encoding: Avro/JSON per decomp.json decomposition config
    v
ldms_schema_normalizer transform
    |  Convert LDMS fields to Prometheus labels:
    |    __name__ = "{plugin}_{metric_name}"
    |    instance = host
    |    job = "ldms"
    |    plugin = plugin
    |    component = component
    v
metric_enricher transform
    |  Add labels:
    |    source_subsystem = "ldms"
    |    topic_name = "ldms"
    |    ingestion_timestamp = now()
    v
Prometheus remote_write -> vmagent-vector:8429 -> vminsert:8480
    (NO VictoriaLogs routing -- LDMS is pure metrics)
```

**OME Data Routing by Topic (Q2 — Omnia-deployed):**

| Topic | Data Type | Destination | Transform |
|-------|-----------|-------------|-----------|
| `ome.events` | Server events (JSON) | vlagent-vector → VictoriaLogs (vlinsert) | Enrich with `_msg_source=ome`, `_msg_topic=ome.events` |
| `ome.alerts` | Alert notifications (JSON) | vlagent-vector → VictoriaLogs (vlinsert) | Enrich with severity, alert_type labels |
| `ome.logs` | Operational logs (JSON) | vlagent-vector → VictoriaLogs (vlinsert) | Enrich with log_level, component labels |
| `ome.inventory` | Hardware inventory metrics (JSON) | vmagent-vector → VictoriaMetrics (vminsert) | Convert to Prometheus format with device/component labels |
| `ome.telemetry` | Server telemetry metrics (JSON) | vmagent-vector → VictoriaMetrics (vminsert) | Convert to Prometheus format with server/metric labels |

##### 4.1.3.3 Interfaces

**Provided Interfaces (Vector Pods):**

| Interface | Type | Port | Pod | Q2 Status | Purpose |
|-----------|------|------|-----|-----------|---------|
| `/health` | HTTP GET | 8686 | Vector-iDRAC | Future | Kubernetes liveness/readiness probe |
| `/health` | HTTP GET | 8687 | Vector-LDMS | **Q2 Active** | Kubernetes liveness/readiness probe |
| `/health` | HTTP GET | 8688 | Vector-OME | **Q2 Active** | Kubernetes liveness/readiness probe |
| `/metrics` | HTTP GET (Prometheus) | 9598 | Vector-iDRAC | Future | Vector internal metrics for self-monitoring |
| `/metrics` | HTTP GET (Prometheus) | 9599 | Vector-LDMS | **Q2 Active** | Vector internal metrics for self-monitoring |
| `/metrics` | HTTP GET (Prometheus) | 9600 | Vector-OME | **Q2 Active** | Vector internal metrics for self-monitoring |

**Internal Interfaces (Within K8s Cluster) — Q2 Active:**

| Source | Destination | Protocol | Port | Authentication | Purpose |
|--------|------------|----------|------|----------------|---------|
| Vector-LDMS | Kafka bootstrap | Kafka (TLS) | 9093 | mTLS (kafkapump certs) | Consume ldms topic |
| Vector-LDMS | vmagent-vector | HTTP | 8429 | None (intra-K8s) | Write metrics via prometheus_remote_write |
| Vector-OME | Kafka bootstrap | Kafka (TLS) | 9093 | mTLS (vector-ome-user certs) | Consume ome.* topics |
| Vector-OME | vmagent-vector | HTTP | 8429 | None (intra-K8s) | Write metrics via prometheus_remote_write |
| Vector-OME | vlagent-vector | HTTP | 9427 | None (intra-K8s) | Write logs via JSON Lines |
| vmagent-vector | vminsert | HTTPS | 8480 | TLS (cluster CA) | Forward buffered metrics to VictoriaMetrics |
| vlagent-vector | vlinsert | HTTP | 9428 | None (intra-K8s) | Forward buffered logs to VictoriaLogs |

**Internal Interfaces (Future — Not in Q2):**

| Source | Destination | Protocol | Port | Authentication | Purpose |
|--------|------------|----------|------|----------------|---------|
| Vector-iDRAC (future) | Kafka bootstrap | Kafka (TLS) | 9093 | mTLS (kafkapump certs) | Consume NERSC iDRAC topics |
| Vector-iDRAC (future) | vmagent-vector | HTTP | 8429 | None (intra-K8s) | Write metrics via prometheus_remote_write |
| Vector-iDRAC (future) | vlagent-vector | HTTP | 9427 | None (intra-K8s) | Write logs via JSON Lines |

**Note:** Vector pods do **not** connect directly to vminsert or vlinsert. All writes go through the buffer agents (vmagent-vector for metrics, vlagent-vector for logs). This provides disk-based write-ahead buffering and decouples Vector from Victoria backend availability.

**Kubernetes Secrets:**

| Secret Name | Created By | Consumed By | Contents |
|------------|-----------|-------------|----------|
| `kafkapump` | Strimzi (from existing KafkaUser CR) | Vector-LDMS pod (shared with store_avro_kafka producers) | `user.crt`, `user.key`, `ca.crt` |
| `vector-ome-user` | Strimzi (from new KafkaUser CR, provisioned by Omnia) | Vector-OME pod (Omnia-deployed, Q2) | `user.crt`, `user.key`, `ca.crt` |
| `kafka-cluster-ca-cert` | Strimzi (existing) | All Vector pods | `ca.crt` (Kafka cluster CA) |
| `victoria-tls-certs` | Victoria cert gen script (existing) | vmagent-vector pod | CA cert for vminsert TLS (Vector pods no longer need this — only vmagent-vector connects to vminsert) |

**Generated Kubernetes Manifests (Q2 — Omnia-deployed):**

| # | Manifest | Scope | Component |
|---|----------|-------|-----------|
| 1 | `vector-ldms-deployment.yaml` | Deployment | Vector-LDMS pod |
| 2 | `vector-ldms-configmap.yaml` | ConfigMap | TOML configuration for LDMS pipeline |
| 3 | `vector-ldms-service.yaml` | Service (ClusterIP) | Health/metrics endpoints |
| 4 | `vmagent-vector-deployment.yaml` | Deployment | vmagent-vector write-buffer pod |
| 5 | `vmagent-vector-service.yaml` | Service (ClusterIP) | Exposes port 8429 for Vector pods |
| 6 | `vector-ome-kafkauser.yaml` | KafkaUser | mTLS user for OME consumer (provisioned by Omnia for Vector-OME) |
| 7 | `vector-ome-deployment.yaml` | Deployment | Vector-OME pod |
| 8 | `vector-ome-configmap.yaml` | ConfigMap | TOML configuration for OME pipeline |
| 9 | `vector-ome-service.yaml` | Service (ClusterIP) | Health/metrics endpoints |
| 10 | `vlagent-vector-deployment.yaml` | Deployment | vlagent-vector log write-buffer pod |
| 11 | `vlagent-vector-service.yaml` | Service (ClusterIP) | Exposes port 9427 for Vector pods |

**Manifests deferred to future release (Vector-iDRAC):**

Vector-iDRAC Deployment, ConfigMap, and Service manifests will be created when the NERSC iDRAC collector is integrated.

##### 4.1.3.4 Configuration Processing

**Configuration Parameters (telemetry_config.yml) — User-Facing Feature Flags:**

The `telemetry_config.yml` file uses a three-layer architecture: `telemetry_sources` (data collectors), `telemetry_bridges` (Vector pipelines), and `telemetry_sinks` (storage backends). All resource tuning parameters (CPU, memory, replicas) are internal defaults in the Ansible role vars, not user-configurable.

**Telemetry Sources:**

| Parameter | Source File | Section/Key | Default | Validation | Description |
|-----------|-----------|-------------|---------|------------|-------------|
| `idrac.metrics_enabled` | telemetry_config.yml | `telemetry_sources.idrac.metrics_enabled` | `true` | Boolean | Enable/disable iDRAC metrics collection |
| `ldms.metrics_enabled` | telemetry_config.yml | `telemetry_sources.ldms.metrics_enabled` | `true` | Boolean | Enable/disable LDMS metrics collection |
| `dcgm.metrics_enabled` | telemetry_config.yml | `telemetry_sources.dcgm.metrics_enabled` | `true` | Boolean | Enable/disable DCGM GPU metrics collection |
| `powerscale.metrics_enabled` | telemetry_config.yml | `telemetry_sources.powerscale.metrics_enabled` | `true` | Boolean | Enable/disable PowerScale metrics collection |
| `powerscale.logs_enabled` | telemetry_config.yml | `telemetry_sources.powerscale.logs_enabled` | `false` | Boolean | Enable/disable PowerScale logs collection |

**Telemetry Bridges:**

| Parameter | Source File | Section/Key | Default | Validation | Description |
|-----------|-----------|-------------|---------|------------|-------------|
| `vector_ldms.enabled` | telemetry_config.yml | `telemetry_bridges.vector_ldms.enabled` | `true` | Boolean | Enable/disable Vector-LDMS bridge (Kafka→VictoriaMetrics for LDMS metrics) |
| `vector_ome.metrics_enabled` | telemetry_config.yml | `telemetry_bridges.vector_ome.metrics_enabled` | `true` | Boolean | Enable/disable Vector-OME metrics routing (Kafka `ome.*` topics→VictoriaMetrics) |
| `vector_ome.logs_enabled` | telemetry_config.yml | `telemetry_bridges.vector_ome.logs_enabled` | `true` | Boolean | Enable/disable Vector-OME logs routing (Kafka `ome.*` topics→VictoriaLogs) |
| `vector_ome.ome_identifier` | telemetry_config.yml | `telemetry_bridges.vector_ome.ome_identifier` | `"ome"` | String | Topic prefix identifier for Vector-OME (used in regex `^{ome_identifier}\..*$`) |

**Notes:**
- **iDRAC, LDMS, DCGM**: Only support metrics (no `logs_enabled` field)
- **PowerScale**: Supports both metrics and logs
- **Vector-iDRAC**: Not supported in Q2 — requires NERSC iDRAC collector integration (deferred to future release)
- **Auto-enablement**: Sinks (VictoriaMetrics, VictoriaLogs, Kafka) are auto-enabled when sources target them

**Internal Configuration Parameters (roles/telemetry/vars/main.yml):**

Resource limits, replica counts, and other tuning parameters are defined as Ansible role variables in `roles/telemetry/vars/main.yml`. These are internal defaults and are **not** exposed in `telemetry_config.yml` to keep the user-facing configuration simple and focused on feature enablement.

| Parameter | Default | Description |
|-----------|---------|-------------|
| `vector_image` | `timberio/vector:0.54.0` | Vector container image (also referenced in `service_k8s.json`) |
| `vector_ldms_replicas` | `1` | Replica count for Vector-LDMS pod |
| `vector_ldms_memory_request` | `256Mi` | Memory request for Vector-LDMS |
| `vector_ldms_memory_limit` | `512Mi` | Memory limit for Vector-LDMS |
| `vector_ldms_cpu_request` | `100m` | CPU request for Vector-LDMS |
| `vector_ldms_cpu_limit` | `500m` | CPU limit for Vector-LDMS |
| `vmagent_vector_replicas` | `1` | Replica count for vmagent-vector (write-buffer) |
| `vmagent_vector_memory_request` | `256Mi` | Memory request for vmagent-vector |
| `vmagent_vector_memory_limit` | `512Mi` | Memory limit for vmagent-vector |
| `vmagent_vector_cpu_request` | `100m` | CPU request for vmagent-vector |
| `vmagent_vector_cpu_limit` | `500m` | CPU limit for vmagent-vector |
| `vmagent_vector_image` | `victoriametrics/vmagent:v1.117.1` | vmagent-vector container image |
| `vmagent_vector_remote_write_url` | `http://vminsert.telemetry.svc.cluster.local:8480/insert/0/prometheus/api/v1/write` | Upstream vminsert remote write endpoint |
| `vmagent_vector_tmp_data_path` | `/vmagent-buffer` | Disk WAL buffer path (emptyDir volume) |
| `vector_idrac_replicas` | `1` | Replica count for Vector-iDRAC pod (future) |
| `vector_idrac_memory_request` | `256Mi` | Memory request for Vector-iDRAC (future) |
| `vector_idrac_memory_limit` | `512Mi` | Memory limit for Vector-iDRAC (future) |
| `vector_idrac_cpu_request` | `100m` | CPU request for Vector-iDRAC (future) |
| `vector_idrac_cpu_limit` | `500m` | CPU limit for Vector-iDRAC (future) |
| `vector_ome_replicas` | `1` | Replica count for Vector-OME pod |
| `vector_ome_memory_request` | `512Mi` | Memory request for Vector-OME |
| `vector_ome_memory_limit` | `1Gi` | Memory limit for Vector-OME |
| `vector_ome_cpu_request` | `250m` | CPU request for Vector-OME |
| `vector_ome_cpu_limit` | `1000m` | CPU limit for Vector-OME |

**Removed Configuration Parameters:**

The following parameters have been removed. They are not needed because Vector's built-in defaults are well-tuned for the target workloads:

| Removed Parameter | Previous Default | Rationale for Removal |
|-------------------|-----------------|----------------------|
| `vector_batch_max_events` | `1000` | Vector's `prometheus_remote_write` and `http` sinks have built-in batch defaults (typically 1000 events) that are already well-tuned by the upstream project. Exposing this as user-configurable adds unnecessary complexity without meaningful benefit. |
| `vector_batch_timeout_secs` | `5` | Vector's per-sink default batch timeout (typically 1s for `prometheus_remote_write`) is optimized for low-latency delivery. The previous 5s default was actually worse than Vector's built-in. |
| `vector_kafka_fetch_max_bytes` | `1048576` | Vector's Kafka source uses a sensible default fetch size (1 MB). This is an internal Kafka consumer tuning knob that operators should not need to adjust in normal operation. |

Refer to the Component Spec for the full `telemetry_config.yml` schema definition, JSON schema validation rules, and example configuration.

**Two-Level Validation:**

| Level | Tool | Scope | Actions |
|-------|------|-------|---------|
| **L1 — JSON Schema** | `telemetry_config.json` schema | Pre-playbook | Validate `telemetry_sources` and `telemetry_bridges` structure: `metrics_enabled`/`logs_enabled` are boolean; `collection_targets` are valid; `ome_identifier` is string |
| **L2 — Python** | Custom validation script | Pre-deployment | Check: Kafka bootstrap reachable, vmagent-vector endpoint up, vminsert endpoint up, image available in registry |
| **L2 — Ansible** | Ansible modules | Deployment-time | Check: `telemetry` namespace exists, Strimzi operator running, KafkaUser secrets provisioned |

##### 4.1.3.5 Cross-Feature Interactions

| Interaction | Components | Description |
|-------------|-----------|-------------|
| **LDMS new path to VictoriaMetrics (Q2)** | store_avro_kafka → Kafka → Vector-LDMS → vmagent-vector → vminsert | Currently LDMS metrics go to Kafka but have no consumer. Vector-LDMS is the **first and only** path for LDMS metrics to reach VictoriaMetrics (via vmagent-vector write-buffer). This is the primary Q2 deliverable. |
| **Kafka Producer users unchanged** | `kafkapump` KafkaUser | store_avro_kafka (LDMS) uses the existing `kafkapump` Strimzi KafkaUser with broad ACLs. Vector-LDMS also reuses the same `kafkapump` user for Kafka consumption — the user's wildcard topic/group ACLs cover both producer and consumer operations. |
| **OME external producer** | OME → Kafka external listener → Vector-OME (Omnia-deployed, Q2) | OME produces via mTLS to port 9094. Omnia deploys Vector-OME and provisions Kafka topics, ACLs, and `vector-ome-user` KafkaUser. |
| **Vector-LDMS self-metrics → vmagent** | Vector-LDMS /metrics → vmagent | vmagent can optionally scrape Vector-LDMS's `/metrics` endpoint on port 9599 for self-monitoring (requires scrape job addition) |
| **Cleanup independence** | Vector teardown | Vector-LDMS and vmagent-vector pods can be removed without impacting Kafka producers (store_avro_kafka), VictoriaMetrics, or Kafka topics. Consumer group is deleted; topics and producer pipelines remain unchanged. |
| **iDRAC dual data paths (existing, unchanged)** | VictoriaPump → vmagent (only active path in Q2) | iDRAC metrics continue to reach VictoriaMetrics only via VictoriaPump → vmagent scrape path. No Kafka-based iDRAC consumer exists in Q2. Vector-iDRAC will add the Kafka-based path in a future release using NERSC iDRAC collector topics. |
| **OME Vector integration model** | Omnia (full pipeline) | Omnia provisions `vector-ome-user` KafkaUser, OME topic ACLs, and the Vector-OME pod (Deployment, ConfigMap, Service) from telemetry roles. |

##### 4.1.3.6 Redeploy and Upgrade Behaviour

**Deployment Lifecycle States (Q2 — Vector-LDMS and Vector-OME):**

```
  No Vector ──[U1]──▶ Vector-LDMS Running ──[U9]──▶ No Vector
       │                    │  ▲                       │
       │                    │  │                       │
       │               [U7] │  │ [U7]                  │
       │                    ▼  │                       │
       │               Config Change /                 │
       │               Rolling Restart                 │
       │                                               │
       └──────────────[U10]────────────────────────────┘
```

**Scenario Matrix (Q2):**

| # | Scenario | From State | To State | Actions |
|---|----------|-----------|----------|---------|
| U1 | Fresh deployment (LDMS) | No Vector deployed | Vector-LDMS running | Verify kafkapump secret exists → render LDMS ConfigMap → deploy Deployment + Service → verify |
| U2 | Enable OME pipeline | No OME resources | OME resources + Vector-OME running | Create `vector-ome-user` KafkaUser CR → wait for Strimzi to provision mTLS secret → create OME KafkaTopic CRs → deploy Vector-OME pod (Omnia-deployed, Q2) |
| U7 | Configuration change (resources, transforms) | Running with old config | Running with new config | Re-render Jinja2 templates → `kubectl apply` → rolling restart of Vector-LDMS Deployment |
| U8 | Vector image upgrade | Running old image | Running new image | Update `vector_image` in vars/service_k8s.json → re-render Deployment → rolling update |
| U9 | Full teardown | Vector-LDMS running | No Vector deployed | Run `cleanup_telemetry.sh vector` or Ansible teardown task; deletes Vector-LDMS Deployment, ConfigMap, Service |
| U10 | Redeploy after teardown | No Vector deployed | Vector-LDMS running | Same as U1 (idempotent) |

**Idempotent Redeploy Behaviour:**

Re-running the telemetry playbook on an already-deployed Vector pipeline must produce no side effects:

| Resource | Redeploy Behaviour | Pod Impact |
|----------|-------------------|------------|
| KafkaUser CR (`vector-ome-user`) | `kubectl apply` — no-op if unchanged | None |
| KafkaUser secret (Strimzi-managed) | Not touched by playbook — Strimzi owns lifecycle | None |
| `kafkapump` secret | Read-only — playbook verifies existence but never modifies | None |
| ConfigMap (TOML config for Vector-LDMS) | `kubectl apply` — no-op if template renders identically | None (no restart unless checksum changes) |
| Deployment (Vector-LDMS) | `kubectl apply` — no-op if spec unchanged | None (no rolling restart) |
| Service (Vector-LDMS) | `kubectl apply` — no-op if spec unchanged | None |

Key invariant: If the rendered templates produce identical manifests, `kubectl apply` results in zero changes and zero pod restarts. Only when a ConfigMap checksum changes does the playbook patch the `restartedAt` annotation to trigger a rolling restart.

**Fresh Deploy Procedure (U1):**

1. **Pre-flight validation** — Verify kafkapump KafkaUser secret exists in the telemetry namespace (fails fast if Kafka cluster or Strimzi operator is not ready)
2. **KafkaUser creation (OME)** — If `vector_ome_support=true`, apply `vector-ome-user` KafkaUser CR; wait for Strimzi to provision the mTLS certificate secret
3. **ConfigMap rendering** — Render Jinja2 TOML template for Vector-LDMS using values from role vars (`roles/telemetry/vars/main.yml`) and `service_k8s.json`
4. **Manifest application** — Apply Vector-LDMS Deployment, Service, and ConfigMap via Kustomize (`kubectl apply`)
5. **Readiness verification** — Wait for Vector-LDMS pod to report Ready; verify consumer group lag via Kafka consumer group describe

**Configuration Change Procedure (U7):**

1. Detect configuration change by comparing rendered template checksum against deployed ConfigMap annotation
2. Re-render Vector-LDMS TOML configuration template via Jinja2
3. Apply updated manifests via Kustomize (`kubectl apply`)
4. Trigger rolling restart of Vector-LDMS Deployment by patching the `restartedAt` annotation
5. Wait for pod to reach Ready state

**Image Upgrade Procedure (U8):**

1. Update `vector_image` and `vector_tag` in `service_k8s.json` (or `roles/telemetry/vars/main.yml`)
2. Re-render Deployment manifests — image field changes
3. Apply updated Deployment via `kubectl apply` — Kubernetes triggers a rolling update automatically (no manual restart annotation needed)
4. Kubernetes creates new ReplicaSet, schedules new pod, drains old pod via default rolling update strategy
5. Verify new pod reaches Ready state and resumes consuming from last committed Kafka offset

**Full Teardown Procedure (U9):**

Teardown can be invoked via the cleanup script or the Ansible teardown task. Both follow the same deletion order:

1. Delete Deployment: `vector-ldms`
2. Delete ConfigMap: `vector-ldms-config`
3. Delete Service: `vector-ldms`
4. Optionally delete KafkaUser: `vector-ome-user` (if OME Kafka provisioning was enabled; triggers Strimzi to delete the associated mTLS secret)
5. Force-delete remaining pods with label `component=vector` (grace period 0)
6. Verify no Vector resources remain

Resources explicitly **NOT** deleted during Vector teardown:

| Resource | Reason |
|----------|--------|
| `kafkapump` KafkaUser + secret | Shared with store_avro_kafka (LDMS producer) and KafkaPump (iDRAC producer) |
| Kafka topics (`ldms`, `ome.*`) | Topics and their data are retained for other consumers or replay |
| Consumer group offsets | Automatically expired by Kafka after `offsets.retention.minutes` (default 7 days) |
| VictoriaMetrics / VictoriaLogs | Independent components; Vector removal does not affect stored metrics or logs |
| Vector-OME pod (if deployed) | Managed by Omnia; teardown includes Vector-OME Deployment, ConfigMap, and Service when `vector_ome_support` was enabled |

**Cleanup Script Integration:**

The cleanup script `cleanup_telemetry.sh` supports a `vector` argument (see Component Spec CD-16):

```
cleanup_telemetry.sh vector          # Teardown Vector pipeline only
cleanup_telemetry.sh all             # Teardown everything including Vector
cleanup_telemetry.sh idrac vector    # Teardown iDRAC and Vector together
```

When `CLEAN_ALL=true` (no arguments or `all` argument), `CLEAN_VECTOR=true` is set automatically, ensuring Vector resources are included in full-stack teardown.

**Redeploy After Teardown (U10):**

U10 is identical to U1 — the playbook is fully idempotent. After teardown:
- `vector-ome-user` KafkaUser CR and secret are recreated by Strimzi (if `vector_ome_support=true`)
- `kafkapump` secret still exists (not deleted during Vector teardown) — no re-provisioning needed
- Consumer group is recreated on first consume; Kafka assigns partitions starting from `auto.offset.reset=earliest` (configurable) since no committed offsets exist
- Vector-LDMS ConfigMap, Deployment, and Service are recreated from templates

**Graceful Shutdown:**

The Vector-LDMS Deployment sets `terminationGracePeriodSeconds: 30`, giving in-flight batches time to flush to VictoriaMetrics before the pod is terminated. This applies during upgrades, teardown, and node drains. The Kubernetes default rolling update strategy (`RollingUpdate` with `maxUnavailable: 25%`, `maxSurge: 25%`) is used — no custom strategy is specified in the Deployment manifests since fresh install is the primary deployment path.

Detailed Ansible task implementations for all upgrade scenarios are specified in the Component Spec (§20).

#### 4.1.4 Security

**TLS/mTLS Configuration (Q2 Active):**

| Connection | Protocol | Certificate Source | Verification |
|-----------|----------|-------------------|--------------|
| Vector-LDMS → Kafka (9093) | mTLS | Existing `kafkapump` KafkaUser secret (`user.crt`, `user.key`) + cluster CA (`ca.crt`) | Server cert verified against cluster CA; client cert verified by Kafka |
| Vector-LDMS → vmagent-vector (8429) | HTTP | None | In-cluster; no TLS required for intra-namespace communication |
| vmagent-vector → vminsert (8480) | TLS | Victoria cluster CA (`ca.crt`) from `victoria-tls-certs` secret | Server cert verified against Victoria CA; no client cert required |

**TLS/mTLS Configuration (Q2 — Vector-OME):**

| Connection | Protocol | Certificate Source | Verification |
|-----------|----------|-------------------|--------------|
| Vector-OME → Kafka | mTLS | KafkaUser secret `vector-ome-user` (provisioned by Omnia) | Server cert verified against cluster CA; client cert verified by Kafka |
| Vector-OME → vmagent-vector | HTTP | None | In-cluster; same as Vector-LDMS |
| Vector-OME → vlagent-vector | HTTP | None | In-cluster; no TLS for intra-namespace log writes |
| vlagent-vector → vlinsert | HTTP | None | In-cluster; per Cap 23732 (intra-K8s, no TLS) |

**TLS/mTLS Configuration (Future — Not in Q2):**

| Connection | Protocol | Certificate Source | Verification |
|-----------|----------|-------------------|--------------|
| Vector-iDRAC → Kafka (future) | mTLS | Existing `kafkapump` KafkaUser secret | Same as Vector-LDMS |
| Vector-iDRAC → vmagent-vector | HTTP | None | In-cluster; same as Vector-LDMS |
| Vector-iDRAC → vlagent-vector | HTTP | None | In-cluster; no TLS for intra-namespace log writes |

**Credential Management:**
- All mTLS certificates are managed by Strimzi via KafkaUser custom resources
- Certificates are mounted as Kubernetes Secret volumes — never embedded in ConfigMaps or environment variables
- Ansible tasks use `no_log: true` when handling certificate data
- No credentials appear in Vector TOML configuration — only volume mount paths
- Vector-LDMS reuses the existing `kafkapump` KafkaUser (shared with store_avro_kafka producers). Credential reuse is acceptable because the `kafkapump` user already has equivalent permissions and operates in the same trust domain.
- `vector-ome-user` is provisioned by Omnia for the Vector-OME deployment (Omnia-deployed, Q2)

**KafkaUser ACL Design:**

| KafkaUser | Resource Type | Resource Name | Pattern | Operations | Purpose |
|-----------|--------------|---------------|---------|------------|---------|
| `kafkapump` (existing, reused) | Topic | `*` | Literal (wildcard) | Read, Write, Create, Delete, Describe, Alter, AlterConfigs | Covers Vector-LDMS consumption of `ldms` (plus producer operations) |
| `kafkapump` (existing, reused) | Group | `*` | Literal (wildcard) | Read, Describe | Covers `vector-ldms-group` consumer group membership |
| `vector-ome-user` (new, provisioned by Omnia) | Topic | `ome.` | Prefix | Read, Describe | Consume all `ome.*` topics (used by Vector-OME, Omnia-deployed) |
| `vector-ome-user` (new) | Topic | `omnia.telemetry` | Literal | Read, Describe | Consume `omnia.telemetry` (non-`ome.` prefix) |
| `vector-ome-user` (new) | Group | `vector-ome-group` | Literal | Read | Consumer group membership |

**Principle:** The existing `kafkapump` user's broad ACLs (`name: "*"`) already cover all consumer operations needed by Vector-LDMS. Only `vector-ome-user` is created with least-privilege ACLs because OME is an external producer with a different security lifecycle. Full KafkaUser CR definition for `vector-ome-user` is provided in the Component Spec.

**Risk Assessment:**

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| LDMS schema change breaks Vector-LDMS transforms | High | Medium — LDMS metrics stop flowing to Victoria | Version-pin LDMS schema in transforms; automated transform testing in CI; monitor `vector_component_errors_total` on Vector-LDMS |
| OME publishes to new topic not matching regex | Low | Medium — new topic data not consumed by Vector-OME | Document topic naming convention; regex `^(ome\..*\|omnia\.telemetry)$` covers known patterns |
| Kafka consumer lag builds up during Victoria outage | Medium | Low — data buffered in Kafka (7-day retention) | Monitor consumer lag; alert on lag > threshold; Kafka retention provides buffer |
| NERSC iDRAC collector integration delayed | Medium | Low — Vector-iDRAC remains deferred | iDRAC metrics continue via existing VictoriaPump → vmagent path |
| OME schema changes break Vector-OME transforms | Low | Medium — OME telemetry not flowing | Version-pin OME schema in transforms; validate against real OME data before enabling |

#### 4.1.5 Resource Utilization

| Component | CPU Request | CPU Limit | Memory Request | Memory Limit | PVC | Notes |
|-----------|------------|-----------|----------------|--------------|-----|-------|
| vmagent-vector **(Q2 Active)** | 100m | 500m | 256 Mi | 512 Mi | None | Write-buffer for Vector pods → vminsert. Disk buffer uses emptyDir (ephemeral). Defined in `roles/telemetry/vars/main.yml`. |
| vector-ldms **(Q2 Active)** | 100m | 500m | 256 Mi | 512 Mi | None | Stateless; metrics-only pipeline (no VictoriaLogs sink). Schema normalization may require more CPU for high-cardinality LDMS data. Resource values defined in `roles/telemetry/vars/main.yml`. |
| vector-idrac **(Future)** | 100m | 500m | 256 Mi | 512 Mi | None | Deferred; will route to both vmagent-vector and vlagent-vector when NERSC iDRAC collector is integrated. |
| vlagent-vector **(Q2)** | 100m | 500m | 256 Mi | 512 Mi | None | Log write-buffer for Vector-OME log/event sinks → vlinsert. |
| vector-ome **(Q2 — Omnia-deployed)** | 250m | 1000m | 512 Mi | 1 Gi | None | Omnia-deployed; resource values defined in `roles/telemetry/vars/main.yml`. |
| **Total Vector pipeline (Q2 — LDMS + OME + vmagent-vector + vlagent-vector)** | **550m** | **2500m** | **1280 Mi** | **2560 Mi** | **None** | |

**Note:** All CPU, memory, and replica values are defined in `roles/telemetry/vars/main.yml` (not in `telemetry_config.yml`). The `telemetry_config.yml` file only contains feature flags (`vector_ldms_support`, `vector_ome_support`, `vector_idrac_support`).

**Scaling Guidelines:**
- If consumer lag on `ldms` exceeds 10 minutes, increase `vector_ldms_replicas` in `roles/telemetry/vars/main.yml` (requires increasing partition count first — default is configurable via `kafka_configurations.topic_partitions`)
- Maximum effective parallelism per topic = number of partitions in that topic
- Vector-LDMS can scale independently via replica count adjustment in role vars

#### 4.1.6 Open Source

| Component | License | Version | Notes |
|-----------|---------|---------|-------|
| Vector | Mozilla Public License 2.0 (MPL-2.0) | 0.54.0 | Debian-based full image (`timberio/vector:0.54.0`). Rust-based, high-performance data pipeline. Includes shell and debugging utilities for operational troubleshooting. Deployed as unmodified binary — no MPL disclosure obligations triggered. |

#### 4.1.7 Component Test

**Deployment Validation Tests (Q2):**

| # | Test | Procedure | Expected Result |
|---|------|-----------|-----------------|
| T-01 | Vector-LDMS pod reaches Ready state | `kubectl get pods -n telemetry -l app=vector-ldms` | Vector-LDMS pod in Running/Ready state within 120s |
| T-02 | Kafka consumer group registered | `kubectl exec kafka-kafka-0 -- kafka-consumer-groups.sh --bootstrap-server localhost:9092 --list` | `vector-ldms-group` visible |
| T-03 | mTLS connectivity | Check Vector-LDMS logs for successful Kafka connection | No TLS handshake errors in Vector-LDMS pod logs |
| T-04 | End-to-end LDMS flow | Produce test message to `ldms` topic → query VictoriaMetrics | Test metric queryable in VictoriaMetrics within 30s (first time LDMS data reaches VictoriaMetrics) |
| T-05 | LDMS metrics-only routing | Produce test message to `ldms` → verify no VictoriaLogs write | Metric in VictoriaMetrics; no corresponding entry in VictoriaLogs |
| T-06 | Idempotent redeployment | Run playbook twice | No errors; no pod restarts on second run |
| T-07 | Teardown | Run cleanup playbook | All Vector-LDMS resources removed; Kafka topics, producers, and Victoria data retained |
| T-08 | Consumer lag monitoring | Stop Victoria backend → resume → check lag recovery | Consumer lag increases then drains to zero on Victoria recovery |
| T-09 | Feature flag validation | Set `vector_idrac_support=true` in telemetry_config.yml | Playbook fails with clear error message indicating iDRAC Vector is not supported in Q2 |
| T-10 | OME Kafka provisioning | Set `vector_ome_support=true` | `vector-ome-user` KafkaUser CR created; mTLS secret provisioned; no Vector-OME pod deployed by Omnia |

**Performance Validation Targets (from FSpec §5.2.4):**

| Metric | Target |
|--------|--------|
| Ingestion success rate | >= 99.9% over 24 hours |
| End-to-end latency (Kafka → queryable in VM) | <= 30 seconds (p99) |
| Pipeline uptime | >= 99.5% |
| New topic auto-discovery (OME regex) | <= 60 seconds |

#### 4.1.8 API Documentation

**Vector Health API (Q2 Active):**

| Endpoint | Method | Port | Pod | Response |
|----------|--------|------|-----|----------|
| `/health` | GET | 8687 | Vector-LDMS | `200 OK` if healthy |

**Vector Metrics API (Q2 Active — Prometheus Format):**

| Endpoint | Method | Port | Pod | Key Metrics |
|----------|--------|------|-----|-------------|
| `/metrics` | GET | 9599 | Vector-LDMS | `vector_kafka_consumer_lag`, `vector_events_in_total`, `vector_events_out_total`, `vector_buffer_events`, `vector_component_errors_total` |

**Sink Endpoints Used by Vector Pods (via buffer agents):**

| Sink | Vector Writes To | Buffer Agent Forwards To | Protocol | Used By |
|------|-----------------|-------------------------|----------|---------|
| VictoriaMetrics | `http://vmagent-vector.telemetry.svc.cluster.local:8429/api/v1/write` | `https://vminsert.telemetry.svc.cluster.local:8480/insert/0/prometheus/api/v1/write` | Prometheus remote_write (protobuf/snappy) | Vector-LDMS (Q2); Vector-OME (Q2); Vector-iDRAC (future) |
| VictoriaLogs | `http://vlagent-vector.telemetry.svc.cluster.local:9427/insert/jsonline` | `http://vlinsert.telemetry.svc.cluster.local:9428/insert/jsonline` | JSON Lines | Vector-OME (Q2); Vector-iDRAC (future) — not Vector-LDMS (metrics-only) |

**vmagent-vector Write-Buffer Endpoint (Q2 Active):**

| Property | Value |
|----------|-------|
| URL (accepts from Vector) | `http://vmagent-vector.telemetry.svc.cluster.local:8429/api/v1/write` |
| Protocol | Prometheus remote_write (protobuf + snappy compression) |
| Authentication | None (intra-K8s) |
| Forwards to | `https://vminsert.telemetry.svc.cluster.local:8480/insert/0/prometheus/api/v1/write` |
| Buffer | Disk-based write-ahead log (`-remoteWrite.tmpDataPath`) |
| Retry | Automatic with exponential backoff on vminsert failure |

#### 4.1.9 Known Issues and Limitations

1. **iDRAC single-topic limitation (blocking Vector-iDRAC)** — The current Dell iDRAC telemetry produces to a single `idrac` Kafka topic containing mixed metrics and events. This prevents clean Vector routing without fragile heuristic classification. This is the primary reason Vector-iDRAC is not part of Q2. The NERSC iDRAC collector ([https://github.com/NERSC/nersc-idrac](https://github.com/NERSC/nersc-idrac)) solves this with two separate topics (metrics and logs).

2. **LDMS schema variability** — LDMS data format depends on sampler plugin and NERSC codebase version. The `store_avro_kafka` plugin uses `decomposition=/ldms_bin/decomp.json` to control Avro/JSON field layout. Vector-LDMS transforms are version-pinned; schema changes in `decomp.json` or the LDMS sampler plugins require corresponding transform updates and redeployment.

3. **OME topic auto-creation** — OME auto-creates topics on first publish. If OME publishes to a topic outside the regex pattern `^(ome\..*\|omnia\.telemetry)$`, Vector-OME will not consume it. New topic patterns require regex update in the Vector-OME TOML configuration.

4. **Partition count limits consumer parallelism** — Topic partition count (configured via `kafka_configurations.topic_partitions` in the existing `kafka.topic.yaml.j2`) determines maximum consumer parallelism. Scaling Vector replicas beyond the partition count provides only HA, not throughput improvement.

5. **No dead-letter queue** — Messages that fail transformation are logged and dropped. A dead-letter topic could be added in future iterations.

6. **LDMS has no VictoriaLogs routing** — Vector-LDMS only routes to VictoriaMetrics. If LDMS log/event data is needed in VictoriaLogs in the future, a vlinsert sink must be added to the Vector-LDMS configuration.

7. **OME Vector schema coordination required** — Since OME publishes data and Omnia deploys Vector-OME, changes to OME's topic structure or JSON schema require corresponding updates to the Vector-OME TOML configuration in the Omnia telemetry roles.

#### 4.1.10 Unresolved Issues

1. **OME message schema documentation** — Exact JSON schema for each OME topic needs confirmation. The Omnia team will create and maintain the Vector-OME TOML transforms based on the confirmed schemas.

2. **LDMS Avro/JSON field mapping** — The `store_avro_kafka` plugin uses `decomp.json` for decomposition. Detailed field-level mapping from the decomposed Avro/JSON format to Prometheus labels requires validation with NERSC team and review of the actual `decomp.json` file.

3. **External Omni DB dual-write from Vector** — FSpec mentions dual-destination delivery for some collectors. Vector supports multiple sinks natively, but external Omni DB endpoint specification is TBD.

4. **NERSC iDRAC collector integration timeline** — Exact timeline for integrating the NERSC iDRAC collector into Omnia is TBD. This blocks Vector-iDRAC enablement. The NERSC collector's two-topic architecture (metrics and logs) needs to be validated with the actual iDRAC data format.

5. **NERSC iDRAC topic naming convention** — The exact Kafka topic names used by the NERSC iDRAC collector (e.g., `idrac-metrics` and `idrac-logs` or similar) need to be confirmed from the NERSC codebase.

---

### 4.2 VictoriaMetrics Cluster Mode

#### 4.2.1 Component Description

VictoriaMetrics runs in cluster mode as the metrics storage backend for all telemetry data. This is an existing deployment; this section documents the interfaces relevant to Vector integration.

Refer to the existing VictoriaMetrics cluster deployment in `omnia-bsm` for full deployment details. This section focuses on the Vector integration touchpoints.

| Component | Type | Replicas | Port | Purpose |
|-----------|------|----------|------|---------|
| vmstorage | StatefulSet | 3 | 8482 (query), 8400 (insert), 8401 (select) | Persistent time-series storage |
| vminsert | Deployment | 2 | 8480 (external LoadBalancer) | Ingestion gateway — accepts Prometheus remote_write |
| vmselect | Deployment | 2 | 8481 (external LoadBalancer) | Query gateway — serves PromQL queries and VMUI |
| vmagent | Deployment | 1 | — | Scrapes Prometheus /metrics endpoints (currently configured to scrape VictoriaPump on port 2112) |
| **vmagent-vector** | **Deployment** | **1** | **8429** | **NEW (Q2) — Write-buffer for Vector pods. Accepts `prometheus_remote_write` on port 8429, buffers to disk via `-remoteWrite.tmpDataPath`, forwards to vminsert:8480. Separate from vmagent (scraper) to isolate failure domains.** |

#### 4.2.2 Constraints and Assumptions

| ID | Constraint/Assumption |
|----|----------------------|
| VM-C-01 | Minimum 3 K8s worker nodes for vmstorage anti-affinity |
| VM-C-02 | `pod_external_ip_range` configured for LoadBalancer services |
| VM-C-03 | Deduplication interval = 1 minute (handles iDRAC dual-write when both VictoriaPump and Vector-iDRAC paths are active) |
| VM-A-01 | Cluster is already deployed before Vector; vminsert endpoint reachable |
| VM-A-02 | TLS certificates generated by `gen_victoria_certs.sh.j2` are available in `victoria-tls-certs` secret |

#### 4.2.3 Component Design

##### 4.2.3.1 Control Flow

Vector writes to VictoriaMetrics **indirectly via vmagent-vector**, which acts as a write-buffer. vmagent-vector accepts `prometheus_remote_write` from Vector pods on port 8429, buffers to disk, and forwards to vminsert:8480. This decouples Vector from vminsert availability — if vminsert is temporarily down, vmagent-vector buffers writes and retries automatically.

**Why a separate vmagent-vector (not the existing vmagent):**

| Aspect | Existing vmagent | vmagent-vector (new) |
|--------|-----------------|---------------------|
| **Role** | Prometheus scraper — pulls /metrics from VictoriaPump:2112, Vector pods | Write-buffer — accepts pushes from Vector via `remote_write`, buffers, forwards |
| **Mode** | Scrape mode (`-promscrape.config`) | Import/receiver mode (`-httpListenAddr=:8429`, `-remoteWrite.url`) |
| **Failure domain** | Scraping VictoriaPump | Buffering Vector writes |
| **Impact of restart** | VictoriaPump metrics temporarily gap | Vector writes buffer in Kafka (replay from offset) |
| **Scaling** | Scales with scrape target count | Scales with Vector write throughput |

**vmagent Scrape Job Addition for Vector Metrics:**

To enable self-monitoring of the Vector-LDMS pod (Q2), a new scrape job is added to the existing vmagent configuration (alongside the existing `idrac-telemetry` job that scrapes VictoriaPump on port 2112):

| Job Name | Target Pod Label | Metrics Port | Condition |
|----------|-----------------|-------------|-----------|
| `vector-ldms` | `app: vector-ldms` | 9599 | `vector_ldms_support = true` |

All jobs use Kubernetes pod service discovery (`role: pod`) scoped to the `telemetry` namespace. Relabel configs filter by pod label and port number. Scrape job YAML definitions are provided in the Component Spec.

##### 4.2.3.2 Data Flow

```
Vector pods                   vmagent-vector             VictoriaMetrics Cluster
    |                              |                            |
    |-- POST prometheus_         |                            |
    |   remote_write ----------->|                            |
    |   http://vmagent-vector    |                            |
    |   :8429/api/v1/write       |                            |
    |                              |-- POST prometheus_       |
    |                              |   remote_write --------->|
    |                              |   https://vminsert:8480  |
    |                              |   /insert/0/prometheus   |
    |                              |   /api/v1/write          |
    |                              |                          |
    |                              |<-- 204 No Content -------|
    |<-- 204 No Content ----------|                            |
    |                              |                            |
    |                              |  [If vminsert down:]     |
    |                              |  Buffer to disk WAL      |
    |                              |  Retry with backoff      |
    |                              |  Replay on recovery      |
    |                              |                        vminsert
    |                              |                          |
    |                              |                  hash(metric) % N
    |                              |                    /     |     \
    |                              |             vmstorage-0  -1   -2
```

**Note:** Vector pods now write to vmagent-vector (not directly to vminsert). vmagent-vector provides disk-based write-ahead buffering and automatic retry. The existing vmagent continues its scraping role (VictoriaPump on port 2112) unchanged.

##### 4.2.3.3 Interfaces

**vminsert Ingestion Endpoint (used by vmagent-vector, not directly by Vector):**

| Property | Value |
|----------|-------|
| URL | `https://vminsert.telemetry.svc.cluster.local:8480/insert/0/prometheus/api/v1/write` |
| Protocol | Prometheus remote_write (protobuf + snappy compression) |
| Authentication | TLS (server cert verified by Vector using Victoria CA from `victoria-tls-certs` secret) |
| Max request size | 64 MB (default) |
| Concurrency | vminsert handles up to 100 concurrent write requests |

##### 4.2.3.4 Configuration Processing

No new configuration parameters for VictoriaMetrics cluster. Existing `victoria_configurations` in `telemetry_config.yml` governs deployment:

| Parameter | Default | Description |
|-----------|---------|-------------|
| `deployment_mode` | `cluster` | `cluster` or `single-node` |
| `persistence_size` | `8Gi` | PVC size per vmstorage pod |
| `retention_period` | `168` | Hours (7 days) |

#### 4.2.4 Security

- All intra-cluster traffic uses TLS with auto-generated certificates (via `gen_victoria_certs.sh.j2`)
- vminsert/vmselect exposed externally via LoadBalancer with TLS
- No additional security changes required for Vector integration

#### 4.2.5 Resource Utilization

Existing resource allocation (no changes for Vector integration):

| Component | Memory Request | Memory Limit | CPU Request | CPU Limit | PVC |
|-----------|---------------|-------------|-------------|-----------|-----|
| vmstorage (x3) | 2 Gi | 4 Gi | 500m | 2000m | 8 Gi each |
| vminsert (x2) | 512 Mi | 1 Gi | 250m | 1000m | — |
| vmselect (x2) | 512 Mi | 1 Gi | 250m | 1000m | — |
| vmagent (x1) | 256 Mi | 512 Mi | 100m | 500m | — |
| **vmagent-vector (x1) — NEW** | **256 Mi** | **512 Mi** | **100m** | **500m** | **—** |
| **Total** | **~10.5 Gi** | | | | **24 Gi** |

---

### 4.3 VictoriaLogs Cluster Mode

#### 4.3.1 Component Description

VictoriaLogs runs in cluster mode as the log storage backend for all event/log data. Detailed deployment design is covered in the VictoriaLogs Cluster Engineering Spec (ESPEC-VL-2026-001). This section documents Vector integration touchpoints.

| Component | Type | Replicas | Port | Purpose |
|-----------|------|----------|------|---------|
| vlstorage | StatefulSet | 2+ | Internal | Persistent log storage |
| vlinsert | Deployment | 2 | 9428 | Ingestion gateway — accepts JSON Lines, syslog, Elasticsearch bulk |
| vlselect | Deployment | 2 | 9428 | Query gateway — serves LogsQL queries |

**Note:** In Q2, Vector-LDMS and Vector-OME are deployed by Omnia. Vector-LDMS does **not** route to VictoriaLogs (LDMS data is pure metrics). Vector-OME routes log/event data (from `ome.events`, `ome.alerts`, `ome.logs` topics) to VictoriaLogs via the **vlagent-vector** log write-buffer. VictoriaLogs integration from Vector-iDRAC will be relevant in a future release when the NERSC iDRAC collector is integrated.

#### 4.3.2 Component Design

##### 4.3.2.1 Control Flow

Vector-OME (Q2, Omnia-deployed) writes logs to VictoriaLogs via the **vlagent-vector** log write-buffer, which accepts JSON Lines on port 9427 and forwards to vlinsert:9428. Vector-iDRAC (future) will also use vlagent-vector when the NERSC iDRAC collector is integrated. No changes to VictoriaLogs deployment are required for Vector integration. Vector-LDMS is metrics-only and does not write to VictoriaLogs.

##### 4.3.2.2 Data Flow

```
Vector-iDRAC / Vector-OME       vlagent-vector            VictoriaLogs Cluster
    |                                |                            |
    |-- POST /insert/jsonline ----->|                            |
    |   http://vlagent-vector       |                            |
    |   :9427/insert/jsonline       |                            |
    |                                |-- POST /insert/jsonline ->|
    |                                |   http://vlinsert:9428    |
    |                                |   /insert/jsonline        |
    |                                |                            |
    |   {"_msg":"event text",       |                            |
    |    "_time":"2026-04-02...",    |                            |
    |    "_msg_source":"idrac",     |                            |
    |    "severity":"warning",      |                            |
    |    "host":"server-01"}        |                            |
    |                                |                            |
    |                                |<-- 200 OK ----------------|
    |<-- 200 OK --------------------|                            |
    |                                |                            |
    |                                |  [If vlinsert down:]      |
    |                                |  Buffer to disk            |
    |                                |  Retry with backoff        |
    |                                |                        vlinsert
    |                                |                            |
    |                                |                      vlstorage nodes
```

**Log Enrichment Labels (added by Vector transforms):**

| Field | Source | Description |
|-------|--------|-------------|
| `_msg` | Original message body | Required by VictoriaLogs |
| `_time` | Source timestamp or ingestion time | ISO 8601 format |
| `_msg_source` | Vector transform | Source subsystem: `ome` (Q2, Omnia-deployed) or `idrac` (future, via NERSC collector) — not `ldms` (LDMS does not route to VictoriaLogs) |
| `_msg_topic` | Kafka topic name | Original Kafka topic |
| `severity` | Source message (if available) | Log severity level |
| `host` | Source message | Originating host/device |

##### 4.3.2.3 Interfaces

**vlinsert Ingestion Endpoint (used by vlagent-vector, not directly by Vector):**

| Property | Value |
|----------|-------|
| URL | `http://vlinsert.telemetry.svc.cluster.local:9428/insert/jsonline` |
| Protocol | HTTP JSON Lines (one JSON object per line) |
| Authentication | None (intra-K8s; per Cap 23732) |
| Content-Type | `application/x-ndjson` |

#### 4.3.3 Security

- Intra-K8s ingestion does not require TLS per Cap 23732
- External access to vlselect requires mTLS
- No additional security changes for Vector integration

#### 4.3.4 Resource Utilization

Refer to VictoriaLogs Cluster Engineering Spec (ESPEC-VL-2026-001) for full resource allocation. Estimated resources:

| Scale | RAM | CPU | Storage (7-day retention) |
|-------|-----|-----|--------------------------|
| 500 nodes | 8 Gi | 4 cores | ~70 GB |
| 2,000 nodes | 8 Gi | 4 cores | ~350 GB |

---

### 4.4 Kafka Topic Architecture

#### 4.4.1 Component Description

This section defines the complete Kafka topic architecture supporting all telemetry sources that flow through Vector. It extends the existing topic design (iDRAC, LDMS) with the OME multi-topic structure.

**Existing Kafka infrastructure (from code):**
- Strimzi operator in KRaft mode (3 controllers + 3 brokers)
- Listeners: internal (9092), TLS with mTLS (9093), external LoadBalancer with mTLS (9094)
- Authorization: Simple ACL-based
- Existing KafkaUser: `kafkapump` (used by both KafkaPump and store_avro_kafka for producing)
- Existing Kafka Bridge: HTTP bridge on port 8080 via LoadBalancer (`bridge-bridge-lb`)

#### 4.4.2 Component Design

##### 4.4.2.1 Topic Registry

| Topic | Partitions | Replication Factor | Producer | Consumer | Consumer Group | Data Type |
|-------|------------|-------------------|----------|----------|---------------|-----------|
| `idrac` | Configurable (from `kafka_configurations.topic_partitions`) | 2 | KafkaPump container (in iDRAC StatefulSet, reads ActiveMQ) | Vector-iDRAC | `vector-idrac-group` | Mixed (metrics + events) |
| `ldms` | Configurable (from `kafka_configurations.topic_partitions`) | 2 | store_avro_kafka plugin (in LDMS storage daemons) | Vector-LDMS | `vector-ldms-group` | Metrics (Avro/JSON) |
| `ome.events` | 3 | 2 | OME (external) | Vector-OME | `vector-ome-group` | Events (logs) |
| `ome.alerts` | 2 | 2 | OME (external) | Vector-OME | `vector-ome-group` | Alerts (logs) |
| `ome.inventory` | 2 | 2 | OME (external) | Vector-OME | `vector-ome-group` | Inventory metrics |
| `omnia.telemetry` | 3 | 2 | OME (external) | Vector-OME | `vector-ome-group` | Server telemetry metrics |
| `ome.logs` | 2 | 2 | OME (external) | Vector-OME | `vector-ome-group` | Operational logs |

**Topic Configuration (Common):**

| Property | Value | Rationale |
|----------|-------|-----------|
| `cleanup.policy` | `delete` | Time-based retention; no compaction needed for telemetry |
| `retention.ms` | `604800000` (7 days) | Default retention; configurable via `log_retention_hours` in Kafka cluster config |
| `segment.bytes` | `1073741824` (1 GB) | Standard segment size for efficient cleanup |
| `min.insync.replicas` | `2` | Ensure write durability with replication factor 3 |

**Topic Naming Convention:**
- Internal Omnia sources: `{source}` (e.g., `idrac`, `ldms`)
- OME sources: `ome.{datatype}` (e.g., `ome.events`, `ome.alerts`)
- Cross-cutting Omnia topics: `omnia.{domain}` (e.g., `omnia.telemetry`)

##### 4.4.2.2 Kafka User & ACL Design

**Existing Users (Extended Usage):**

| KafkaUser | Authentication | Purpose | Topic Access | Notes |
|-----------|---------------|---------|-------------|-------|
| `kafkapump` | mTLS | iDRAC KafkaPump + LDMS store_avro_kafka producer + **Vector-LDMS consumer (Q2)** | Broad ACLs: Read/Write/Create/Delete/Describe/Alter/AlterConfigs on all topics (`*`); Read/Describe on all consumer groups | Existing user with broad permissions; now also used by Vector-LDMS for consuming. Consumer group `vector-ldms-group` is covered by the wildcard group ACL. |

**New Users (Added for Vector):**

| KafkaUser | Authentication | Purpose | Topic Access |
|-----------|---------------|---------|-------------|
| `vector-ome-user` | mTLS | OME Vector consumer (provisioned by Omnia; used by Omnia-deployed Vector-OME pod) | Read/Describe on `ome.*` (Prefix), `omnia.telemetry` (Literal); Read on consumer group `vector-ome-group` |

**Note:** Vector-LDMS does **not** have a dedicated KafkaUser. It reuses the existing `kafkapump` user because: (1) `kafkapump` already has sufficient permissions, (2) it operates in the same trust domain, and (3) avoiding new KafkaUser CRs eliminates secret provisioning wait time. Only `vector-ome-user` is created as a new KafkaUser because OME is an external producer with a different security domain. The `vector-ome-user` is provisioned by Omnia and consumed by the Omnia-deployed Vector-OME pod.

##### 4.4.2.3 OME Multi-Topic Architecture

OME publishes telemetry data to 5 Kafka topics via the external mTLS listener (port 9094). Topics are auto-created by OME on first publish (Kafka `auto.create.topics.enable=true` on external listener). **Note:** Vector-OME is deployed by Omnia from the telemetry roles (K8s manifests in `roles/telemetry/templates/telemetry/vector/`). Omnia provisions the Kafka topics, `vector-ome-user` KafkaUser, and the Vector-OME pod.

**OME Topic → Vector Routing Matrix:**

```
OME Appliance
    |
    | mTLS (port 9094)
    |
    +-- ome.events -------> Vector-OME --> VictoriaLogs (events)
    +-- ome.alerts -------> Vector-OME --> VictoriaLogs (alerts)
    +-- ome.logs ---------> Vector-OME --> VictoriaLogs (operational logs)
    +-- ome.inventory ----> Vector-OME --> VictoriaMetrics (inventory metrics)
    +-- omnia.telemetry --> Vector-OME --> VictoriaMetrics (server telemetry)
```

The Omnia-deployed Vector-OME `ome_topic_router` transform uses VRL (Vector Remap Language) to route by topic name: topics matching `ome.inventory` or `omnia.telemetry` are sent to the metrics sink (vmagent-vector → vminsert), while `ome.events`, `ome.alerts`, and `ome.logs` are sent to the logs sink (vlagent-vector → vlinsert, or directly to vlinsert initially). The TOML configuration is maintained in the Omnia telemetry roles.

#### 4.4.3 Security

- All Kafka listeners enforce TLS — no plaintext
- Internal listener (9092): TLS, no client auth (intra-cluster only)
- TLS listener (9093): mTLS for internal producers/consumers (KafkaPump, store_avro_kafka, Vector pods)
- External listener (9094): mTLS via LoadBalancer for OME
- ACLs enforce least-privilege: Vector consumers can only Read from assigned topics
- Existing `kafkapump` user retains its broad ACLs for producer operations — no changes to existing ACLs
- Topic-level ACL: OME user can only produce to `ome.*` topics (enforced by OME KafkaUser ACLs, configured separately)

---

## 5. Traceability Matrix

### 5.1 Capability → Functional Spec → Engineering Spec

| Capability | FSpec Requirement | ESpec Section | Implementation |
|------------|------------------|---------------|----------------|
| 12691 — Kafka→VM via Vector | VEC-SB-01: Deploy Vector for Kafka→VM/VL | §4.1 | Vector-LDMS Deployment (Q2); Vector-OME (Omnia-deployed, Q2); Vector-iDRAC deferred |
| 12691 | VEC-SB-02: Dynamic topic discovery (60s) | §4.1.3.1 | Vector-OME regex subscription (Q2) |
| 12691 | VEC-SB-03: Content-type splitting (metrics→VM, logs→VL) | §4.1.3.2 | `ome_topic_router` (Q2, Omnia-deployed); Vector-LDMS metrics-only; Vector-iDRAC deferred (will use NERSC two-topic approach) |
| 12691 | VEC-SB-04: Configurable transforms | §4.1.3.2 | `ldms_schema_normalizer`, `metric_enricher` transforms (Q2) |
| 12691 | VEC-SB-05: LDMS primary path via Vector | §4.1.1 | Vector-LDMS — first and only path for LDMS metrics to reach VictoriaMetrics (Q2) |
| 12691 | VEC-SB-06: Unique topic names per subsystem | §4.4.2.1 | Topic registry with distinct names per source |
| 12691 | VEC-SB-07: Auto-discover new topics | §4.1.3.1 | Regex subscription in Vector-OME (Q2, Omnia-deployed) |
| — | KF-SB-05: idrac and ldms topics with configurable partitions | §4.4.2.1 | Topic registry (partitions from `kafka_configurations.topic_partitions`) |
| — | KF-SB-06: `omnia.<subsystem>.<datatype>` naming | §4.4.2.1 | Topic naming convention |
| — | KF-SB-09: KafkaUser mTLS + ACLs | §4.4.2.2 | `kafkapump` (reused for LDMS), `vector-ome-user` KafkaUser CR (provisioned by Omnia) |
| 23732 | VL-SB-02 Path B: Kafka→Vector→VictoriaLogs | §4.3.2.2 | Vector-OME (Q2, Omnia-deployed) sinks to vlinsert via vlagent-vector; Vector-iDRAC (future); not applicable for LDMS (metrics-only) |
| 23732 | VL-SB-05: Intra-K8s ingestion without TLS | §4.3.2.3 | HTTP (no TLS) to vlinsert within cluster |
| — | VM-SB-04: vminsert accepts remote_write on 8480 | §4.2.3.3 | Vector-LDMS→vmagent-vector:8429→vminsert:8480 (Q2, two-hop via buffer agent) |
| — | SEC-01: TLS for all intra-cluster traffic | §4.1.4 | TLS on Vector-LDMS→Kafka; HTTP within cluster for Vector-LDMS→vmagent-vector→vminsert |
| — | SEC-03: Credentials in Vault/Secrets, never plaintext | §4.1.4 | mTLS certs as K8s Secret volumes; `no_log: true` |
| — | DEP-01: JSON schema validation | §4.1.3.4 | L1 schema validates `telemetry_sources` and `telemetry_bridges` structure |
| — | DEP-02: Idempotent deployment | §4.1.3.6 | `kubectl apply` with Kustomize; no side effects on re-run |
| — | DEP-03: Air-gapped support | §4.1.2 C-01 | Images from local Pulp repository |
| — | DEP-04: Feature toggles | §4.1.3.4 | `telemetry_sources.*.metrics_enabled`, `telemetry_bridges.vector_*.enabled`, `telemetry_bridges.vector_ome.metrics_enabled/logs_enabled` |

### 5.2 BSpec Acceptance Criteria → Engineering Spec Validation

| BSpec Section | Acceptance Criterion | ESpec Test | ESpec Reference |
|---------------|---------------------|------------|-----------------|
| §5.9.3 | Data from LDMS topics stored in VM | T-04 | §4.1.7 |
| §5.9.3 | New topics discovered within 60s | Vector-OME regex (Q2) | §4.1.7 |
| §5.9.3 | Ingestion success rate >= 99.9% | Performance test | §4.1.7 |
| §5.9.3 | E2E latency <= 30s (p99) | Performance test | §4.1.7 |
| §5.9.3 | Pipeline uptime >= 99.5% | Reliability test | §4.1.7 |
| §5.1.3 | TLS connectivity validated | T-03 | §4.1.7 |
| §5.1.3 | Idempotent redeployment | T-06 | §4.1.7 |

---

## 6. Error Handling

| Error Condition | Detection | Behavior | Recovery |
|----------------|-----------|----------|----------|
| Kafka bootstrap unreachable | Vector startup log: connection refused | Pod enters CrashLoopBackOff | Auto-retry with K8s restart backoff; fix Kafka cluster |
| KafkaUser secret not provisioned (C-07) | Ansible `wait_for` task times out | Playbook fails at deployment wait step | Re-run playbook after Strimzi operator is healthy |
| mTLS handshake failure | Vector log: TLS error | Pod fails to consume; health check fails | Verify KafkaUser CR labels match Kafka cluster name |
| vminsert unreachable | vmagent-vector log: remote write error; `vmagent_remotewrite_errors_total` increments | vmagent-vector buffers to disk WAL; retries with exponential backoff | Fix VictoriaMetrics; vmagent-vector replays buffered writes automatically on recovery |
| vmagent-vector unreachable | Vector log: sink error; `vector_component_errors_total` increments | Vector buffers in memory; retries with backoff | Fix vmagent-vector pod; Vector replays from Kafka offset on restart |
| Unparseable message (bad Avro/JSON) | Vector log: parse error | Message dropped; `vector_component_errors_total` increments | Fix producer; no dead-letter queue in v1 |
| Pod OOM killed | K8s event: OOMKilled | Pod restarts; resumes from last committed Kafka offset | Increase memory limit in `roles/telemetry/vars/main.yml` |
| LDMS schema mismatch (store_avro_kafka format change) | LDMS metrics stop appearing in VictoriaMetrics; Vector-LDMS `vector_component_errors_total` increments | Transform produces no output for changed fields | Update VRL transforms in TOML template and redeploy Vector-LDMS |
| LDMS store_avro_kafka not producing | No messages on `ldms` topic; Vector-LDMS consumer lag at zero | Vector-LDMS idles; no errors | Check LDMS storage daemon pods, `store_avro_kafka` plugin config, Kafka connectivity from store pods |
| `vector_idrac_support=true` in Q2 | L1 schema validation | Playbook fails with clear error | Set `vector_idrac_support=false`; iDRAC Vector not supported in Q2 |

**At-least-once delivery guarantee:** Vector commits Kafka offsets only after successful write to vmagent-vector. vmagent-vector independently buffers and retries writes to vminsert. This two-stage buffering provides resilience against both vmagent-vector and vminsert failures. If Vector crashes mid-batch, it replays from the last committed offset on restart. This may produce duplicate writes, which VictoriaMetrics deduplication handles.

---

## 7. Backward Compatibility

This change is **fully additive** — no existing functionality is modified or removed.

| Existing Component | Impact | Reason |
|--------------------|--------|--------|
| iDRAC StatefulSet (Receiver, ActiveMQ, KafkaPump, VictoriaPump, MySQL) | None | All 5 containers continue operating unchanged. KafkaPump continues producing to `idrac` topic. VictoriaPump continues exposing port 2112 for vmagent scrape. **No Vector-iDRAC consumer in Q2** — the `idrac` topic remains without a consumer until NERSC iDRAC collector is integrated. |
| LDMS Aggregators / Storage Daemons | None | store_avro_kafka plugin continues writing to `ldms` topic unchanged. LDMS three-tier pipeline (samplers → aggregators → storage) unaffected. |
| `kafkapump` KafkaUser | Extended usage — not modified | Existing KafkaUser with broad ACLs continues to work for KafkaPump and store_avro_kafka producers. Vector-LDMS also mounts the `kafkapump` secret for consumer operations. No ACL changes needed — existing wildcard permissions cover consumer access. |
| Kafka cluster (brokers, controllers) | None | New topics and users are additive; existing ACLs unchanged |
| Kafka Bridge | None | HTTP bridge on port 8080 continues operating; no changes |
| VictoriaMetrics cluster | None | New writer (vmagent-vector) is additive; existing vmagent scrape of VictoriaPump unchanged. vmagent-vector is a separate vmagent instance with a different role (write-buffer vs. scraper). |
| vmagent | Additive only | New scrape job for Vector-LDMS self-metrics; existing `idrac-telemetry` job (scraping VictoriaPump:2112) unchanged. The new vmagent-vector is a separate Deployment — existing vmagent is not modified. |
| Existing telemetry_config.yml files | Backward compatible | Old `idrac_telemetry_support`, `ldms_support`, `dcgm_support` mapped to new `telemetry_sources.*.metrics_enabled` structure internally by Ansible |
| OME appliance | None | OME continues producing to Kafka topics as before. Vector-OME is deployed by Omnia in Q2 to consume these topics. |

**Migration:** Backward compatible. Operators upgrading from a previous Omnia version have old config keys (`idrac_telemetry_support`, `ldms_support`, `dcgm_support`) automatically mapped to new structure (`telemetry_sources.*.metrics_enabled`) by Ansible roles. Vector-LDMS is enabled by default (`telemetry_bridges.vector_ldms.enabled=true`). Vector-iDRAC is not available in Q2 (deferred to future release). OME bridges are off by default (`telemetry_bridges.vector_ome.metrics_enabled=true`, `logs_enabled=true` when explicitly enabled).

**LDMS metrics visibility improvement:** Enabling Vector-LDMS provides LDMS metrics in VictoriaMetrics for the first time. Previously, LDMS data was only accessible via the Kafka Bridge HTTP API or direct Kafka consumer tooling.

**Configuration evolution:** The new three-layer architecture (`telemetry_sources` → `telemetry_bridges` → `telemetry_sinks`) replaces the previous `vector_configurations` section. This provides:
- Separate control for metrics vs. logs (e.g., `vector_ome.metrics_enabled`, `vector_ome.logs_enabled`)
- Clear data flow visibility (sources define what to collect, bridges define routing, sinks define storage)
- Simplified user input (only enablement flags exposed; resource limits in Ansible vars)

---

## Appendix A: Ansible Role File Structure

```
discovery/roles/telemetry/
+-- tasks/
|   +-- main.yml                              # Existing -- add Vector task includes
|   +-- generate_telemetry_deployments.yml     # Existing -- add Vector template generation
|   +-- generate_vector_deployments.yml        # NEW -- Vector-LDMS + vmagent-vector deployment generation (Q2)
|   +-- teardown_vector.yml                    # NEW -- Vector + vmagent-vector cleanup tasks
|   +-- apply_vector_on_upgrade.yml            # NEW -- Vector upgrade handling
+-- templates/
|   +-- telemetry/
|       +-- vector/                            # NEW directory
|       |   +-- vector-ldms-deployment.yaml.j2   # Q2 — Omnia-deployed
|       |   +-- vector-ldms-configmap.yaml.j2    # Q2 — Omnia-deployed
|       |   +-- vector-ldms-service.yaml.j2      # Q2 — Omnia-deployed
|       |   +-- vmagent-vector-deployment.yaml.j2  # Q2 — write-buffer agent between Vector and vminsert
|       |   +-- vmagent-vector-service.yaml.j2     # Q2 — ClusterIP service exposing port 8429
|       |   +-- vector-ome-kafkauser.yaml.j2     # Q2 — Kafka resource provisioned by Omnia for Vector-OME
|       |   +-- vector-ome-deployment.yaml.j2    # Q2 — Vector-OME pod (Omnia-deployed)
|       |   +-- vector-ome-configmap.yaml.j2     # Q2 — Vector-OME TOML configuration
|       |   +-- vector-ome-service.yaml.j2       # Q2 — Vector-OME health/metrics endpoints
|       |   +-- vlagent-vector-deployment.yaml.j2  # Q2 — log write-buffer agent between Vector-OME and vlinsert
|       |   +-- vlagent-vector-service.yaml.j2     # Q2 — ClusterIP service exposing port 9427
|       +-- victoria/
|       |   +-- vmagent-scrape-config.yaml.j2  # MODIFIED -- add Vector-LDMS + vmagent-vector scrape jobs
|       +-- kafka/
|           +-- kafka.topic.yaml.j2            # MODIFIED -- add OME topic definitions (if vector_ome_support=true)
+-- vars/
    +-- main.yml                               # MODIFIED -- add Vector + vmagent-vector resource variables
```

> **Note:** Vector-iDRAC templates (`vector-idrac-deployment.yaml.j2`, `vector-idrac-configmap.yaml.j2`, `vector-idrac-service.yaml.j2`) are **not created in Q2** — they will be added when NERSC iDRAC collector is integrated. Vector-OME templates (`vector-ome-deployment.yaml.j2`, `vector-ome-configmap.yaml.j2`, `vector-ome-service.yaml.j2`) are created and deployed by Omnia in Q2 when `vector_ome_support=true`. The `vlagent-vector` (VictoriaLogs buffer agent) templates are **created in Q2** — required for Vector-OME log/event sinks to VictoriaLogs.

> **Note:** Full Jinja2/TOML/YAML template content for all files listed above is provided in the **Component Spec** (CSPEC-VECTOR-2026-001). This HLD defines the architecture and design; the Component Spec contains the implementation-ready code artifacts.

---

*Document Version: 0.8 | Last Updated: 2026-04-07*
*SDD Phase: 3 — Engineering Specification (HLD)*
*Companion: Functional Specification FSPEC-TELEM-2026-001 v1.1*
*Companion: Behaviour Specification BSPEC-TELEM-2026-001 v2.0*
*Companion: Component Specification CSPEC-VECTOR-2026-001*
*Capability: 12691 (Kafka→VictoriaMetrics via Vector), 23732 (VictoriaLogs)*
