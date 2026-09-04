# Telemetry

The telemetry domain (collection: `omnia.telemetry`) manages monitoring, metrics collection, and data aggregation for cluster health and performance.

## Overview

The telemetry domain deploys and manages a comprehensive telemetry stack for HPC and AI clusters. It collects metrics and logs from multiple sources (iDRAC, LDMS, OME, UFM, PowerScale, VAST, SFM) and stores them in sink backends (Kafka, VictoriaMetrics, VictoriaLogs). Telemetry runs as Kubernetes workloads on the kube_vip cluster.

**Note**: The orchestrator domain configures telemetry client-side integration on nodes (via telemetry_config.yml and iDRAC telemetry service). The telemetry domain deploys the full telemetry server stack.

## Prerequisites

Before using the telemetry domain, ensure the following prerequisites are met:

- **Main domain setup completed**: The omnia.sh CLI must be installed and configured (`./omnia.sh -s`)
- **Orchestrator domain completed**: Kubernetes service cluster must be deployed and operational
- **Kubernetes cluster**: kube_vip cluster must be running with sufficient resources for telemetry workloads
- **Storage resources**: Persistent storage must be available for VictoriaMetrics and VictoriaLogs PVCs
- **Network connectivity**: Cluster nodes must have network access to telemetry sources (iDRAC, OME, UFM, etc.)
- **Input files configured**: `telemetry_config.yml` and related configuration files must be properly configured

## System Context

```
  orchestrator_state.yml                      telemetry_config.yml
  +---------------------+     +---------------------+
  |    Orchestrator     |---->|                     |
  |  (upstream)           |     |    Telemetry        |---->  monitoring dashboards
  +---------------------+     |                     |     & metrics storage
                              |  (kafka, victoria,  |
                              |   sources, sinks)    |
                              +---------------------+
                                       |
                                  Kubernetes
                                 (kube_vip cluster)
```

## Domain Workflow

The telemetry domain supports the following execution tags:

| Tag | Description | Prerequisites |
|-----|-------------|---------------|
| `precheck` | Validate K8s prerequisites (kube_vip, nodes, pods) | No |
| `validate` | L1 schema + L2 logic validation of all input files | No |
| `deploy` / `execute` | Deploy sinks + sources + kustomize apply | Yes |
| `cleanup` | Remove telemetry runtime resources; preserve PVCs and Kafka identity metadata by default | No |
| `upgrade` | Upgrade telemetry (placeholder) | Yes |
| `rollback` | Rollback telemetry (placeholder) | Yes |

**Default flow (no tags)**: setup + validate + deploy

## Execution Flow

```
Step 0: Setup (always) — read omnia.env, derive paths, create dirs
Step 1: Validate       — L1 schema + L2 logic validation
Step 2: Deploy
  Phase 0: Prerequisites — load config, derive flags, resolve kube_vip
  Phase 1: Sink infrastructure — Kafka, VictoriaMetrics, VictoriaLogs
  Phase 2: Source components — each enabled source generates K8s manifests
  Phase 3: Root kustomization — generate root kustomization.yaml
  Phase 4: Full-stack apply — kubectl apply -k deployments/
```

## Key Inputs

| Input | Location | Purpose |
|-------|----------|---------|
| `telemetry_config.yml` | `/opt/omnia/telemetry/input/<project>/telemetry_config.yml` | Main configuration — kube_vip, sources, sinks, bridges, credentials |
| `telemetry_storage_config.yml` | `/opt/omnia/telemetry/input/<project>/telemetry_storage_config.yml` | Storage backend configuration (PVC sizes, retention) |
| `telemetry_packages.yml` | `/opt/omnia/telemetry/input/<project>/telemetry_packages.yml` | Container registry, image versions, cluster_mount |

**Input Sources:**
- **Administrator** - Provides telemetry configuration files
- **Domain initialization** - Stages input files from samples directory

## Key Outputs

| Output | Location | Purpose |
|--------|----------|---------|
| Telemetry status files | `/opt/omnia/telemetry/output/<project>/` | Deployment status and configuration |
| Monitoring dashboards | Kubernetes cluster | Grafana dashboards for metrics visualization |
| Metrics storage | Kubernetes cluster | VictoriaMetrics time-series database |
| Log storage | Kubernetes cluster | VictoriaLogs log aggregation |

## Output Contract

This contract is consumed by:
- **Administrators** - For monitoring cluster health and performance
- **Cluster workflows** - For ongoing operations and troubleshooting

## Telemetry Components

| Category | Source | Description |
|----------|--------|-------------|
| **Sinks** | Kafka (Strimzi) | Telemetry data streaming |
| | VictoriaMetrics | Time-series metrics storage and querying |
| | VictoriaLogs | Log aggregation and querying |
| **Compute** | iDRAC | Dell server BMC hardware telemetry |
| | LDMS | Lightweight Distributed Metric Service (HPC) |
| **Infrastructure** | OME | OpenManage Enterprise monitoring |
| | UFM | Unified Fabric Manager (InfiniBand) |
| | SFM | Smart Fabric Manager (network) |
| **Storage** | PowerScale | Dell PowerScale (Isilon) |
| | VAST | VAST Data storage |

## Related Guides

## Core Deployment
- [Telemetry Setup](setup_telemetry.md) -- Initialize telemetry domain
- [Deploy Telemetry](deploy_telemetry.md) -- Deploy telemetry stack

## Source Configuration
- [Configure iDRAC](configure_idrac.md) -- Configure iDRAC hardware telemetry
- [Configure LDMS](configure_ldms.md) -- Configure LDMS HPC metrics
- [Configure OME](telemetry_from_ome.md) -- Configure OpenManage Enterprise monitoring
- [Configure UFM](configure_ufm.md) -- Configure InfiniBand fabric metrics
- [Configure PowerScale](configure_powerscale.md) -- Configure PowerScale storage metrics
- [Configure VAST](configure_vast.md) -- Configure VAST storage metrics
- [Configure SFM](configure_sfm.md) -- Configure network fabric metrics

## External Sink Configuration
- [Configure External Kafka](configure_external_kafka.md) -- Use external Kafka sink
- [Configure External VictoriaMetrics](configure_external_victoria.md) -- Use external VictoriaMetrics sink
- [Configure External VictoriaLogs](configure_external_victoria_logs.md) -- Use external VictoriaLogs sink

## Verification
- [Verify iDRAC](verify_idrac.md) -- Verify iDRAC telemetry
- [Verify LDMS](verify_ldms.md) -- Verify LDMS telemetry
- [Verify OME](verify_ome.md) -- Verify OME telemetry
- [Verify PowerScale](verify_powerscale.md) -- Verify PowerScale telemetry
- [Verify UFM](verify_ufm.md) -- Verify UFM telemetry
- [Verify VAST](verify_vast.md) -- Verify VAST telemetry
- [Verify Vector LDMS](verify_vector_ldms.md) -- Verify Vector-LDMS bridge

## Additional
- [Worker Node VLAN Configuration](worker_node_vlan_configuration.md) -- Configure VLAN for worker nodes
- [Getting Started: Kubernetes & Telemetry](../../GetStarted/k8s_telemetry_only.md) -- Quick start guide
- [Domain Contract](../../Reference/domain_contracts/telemetry_contract.md) -- Telemetry domain contract




