# Telemetry

## Overview

The Telemetry deployment module deploys and manages Kubernetes workloads that collect HPC
and infrastructure metrics and logs. It supports iDRAC, LDMS, OpenManage
Enterprise (OME), PowerScale, NVIDIA UFM, and VAST sources. Depending on the
configured routes, it deploys Kafka, VictoriaMetrics, VictoriaLogs, and Vector
bridges in the `telemetry` namespace.

Telemetry runs from the Omnia Infrastructure Manager (OIM). Kubernetes actions
run through SSH on the control-plane VIP obtained from the configured
Orchestrator inventory.

```text
iDRAC ---------------------------> Kafka
   `-----------------------------> VictoriaMetrics

LDMS --> Kafka --> Vector-LDMS --> VictoriaMetrics
OME ---> Kafka --> Vector-OME ----> VictoriaMetrics
                               `--> VictoriaLogs

PowerScale --> OTEL/VMAgent ------> VictoriaMetrics
UFM/VAST ---> VMAgent ------------> VictoriaMetrics
External syslog producers --> VLAgent --> VictoriaLogs
```

`telemetry_status.yml` records deployment and cleanup results. The connection
export workflows write the endpoints and certificates needed by external
producers and consumers. Component status confirms the state checked by the
deployment workflow; verify data in the selected sink to establish end-to-end
collection.

## Prerequisites

| Requirement | Supported value |
|---|---|
| OIM operating system | RHEL 10.x |
| Python | 3.12 or later |
| Ansible | 2.20 or later |
| Kubernetes | A deployed service cluster reachable through `kube_vip` |
| Access | Root SSH access from the OIM to `kube_vip` |

Source-specific requirements are listed in each configuration guide. Review
the [Telemetry Domain Contract](../../Reference/domain_contracts/telemetry_contract.md)
before configuring the project inputs.

## Procedure

| Task | Use it to |
|---|---|
| [Build Telemetry Container Images](setup_telemetry.md) | Build the iDRAC pump and receiver images and the LDMS image maintained by the Telemetry source. |
| [Deploy the Telemetry Stack](deploy_telemetry.md) | Initialize and configure the shared runtime inputs required by the source-specific deployment guides. |
| [Configure iDRAC Telemetry](configure_idrac.md) | Collect Dell server BMC metrics into Kafka and VictoriaMetrics. |
| [Worker Node VLAN Configuration for iDRAC Telemetry](worker_node_vlan_configuration.md) | Prepare the worker VLAN and Redfish network path required by the iDRAC workflow. |
| [Configure LDMS Telemetry](configure_ldms.md) | Deploy LDMS samplers and Kubernetes aggregator/store components, with an optional Vector-to-VictoriaMetrics bridge. |
| [Configure PowerScale Telemetry](configure_powerscale.md) | Deploy CSM Metrics PowerScale and route metrics to VictoriaMetrics; prepare the VictoriaLogs syslog target when logs are enabled. |
| [Configure UFM Telemetry](configure_ufm.md) | Scrape an existing UFM Prometheus endpoint and prepare optional log ingestion through VLAgent. |
| [Configure VAST Telemetry](configure_vast.md) | Scrape an existing VAST Prometheus endpoint and prepare optional log ingestion through VLAgent. |
| [Configure OME Telemetry](telemetry_from_ome.md) | Route OME Kafka topics through Vector to VictoriaMetrics and VictoriaLogs. |
| [Connect SFM](configure_sfm.md) | Export the VictoriaMetrics connection settings generated for SFM remote write. |
| [External Kafka](configure_external_kafka.md) | Connect external Telemetry producers through the project-specific native Kafka mTLS endpoint. |
| [External VictoriaMetrics](configure_external_victoria.md) | Send and query external metrics through project-specific VictoriaMetrics endpoints. |
| [External VictoriaLogs](configure_external_victoria_logs.md) | Send JSON Lines or syslog records and query them through project-specific VictoriaLogs endpoints. |

The domain entry point exposes these lifecycle operations:

| Operation | Behavior |
|---|---|
| No tag | Run setup, input validation, and deployment. |
| `credentials` | Collect only the credentials required by the enabled sources and store them in the encrypted project credential file. |
| `prepare` / `validate` / `validation` | Run L1 schema and L2 logical and infrastructure validation, then collect the required credentials. |
| `precheck` | Check the Kubernetes VIP, cluster health, and enabled source prerequisites. |
| `deploy` / `execute` | Deploy Telemetry sinks, sources, and bridges. |
| `cleanup` | Remove all Telemetry runtime resources while preserving PVCs and Kafka identity by default. |
| `external_kafka` | Export Kafka endpoints and client TLS material. |
| `external_victoria` | Export VictoriaMetrics, VictoriaLogs, and VLAgent connection details. |

The `upgrade` and `rollback` operations are placeholders in the current source
and do not perform component lifecycle changes.

The source-specific guides include commands for inspecting deployed resources
and verifying enabled data paths.

### Contract reference

See the [Telemetry Domain Contract](../../Reference/domain_contracts/telemetry_contract.md)
for the complete validated input, status, cleanup, and connection-export
contracts.

Telemetry reads these project-scoped runtime inputs:

| Input | Effective runtime location |
|---|---|
| `telemetry_config.yml` | `<TELEMETRY_DATA_PATH>/input/<OMNIA_PROJECT_NAME>/` |
| `telemetry_storage_config.yml` | `<TELEMETRY_DATA_PATH>/input/<OMNIA_PROJECT_NAME>/` |
| `telemetry_packages.yml` | `<TELEMETRY_DATA_PATH>/input/<OMNIA_PROJECT_NAME>/` |
| `telemetry_credentials.yml` | Created and encrypted in the same directory when credentials are collected |

At runtime, `TELEMETRY_DATA_PATH` defaults to
`<OMNIA_DATA_PATH>/telemetry`, and `OMNIA_PROJECT_NAME` defaults to
`project_default`. The setup and deployment roles honor both overrides.

The initialization script has a narrower limitation: `domain-init.sh` honors
`OMNIA_PROJECT_NAME`, but stages templates under
`<OMNIA_DATA_PATH>/telemetry/input/<OMNIA_PROJECT_NAME>` and does not read a
`TELEMETRY_DATA_PATH` override. When the override points elsewhere, stage the
three input files in the effective runtime location shown above after running
initialization. Deployment output, including `telemetry_status.yml`, is
written under `<TELEMETRY_DATA_PATH>/output/<OMNIA_PROJECT_NAME>/`. The status
records the overall result, Kubernetes namespace, VIP, package mode, per-sink
and per-source results, bridge results, and LDMS nodes skipped as unreachable.

## Verification

After deployment, inspect:

```bash title="Run on: OIM host"
cat "${TELEMETRY_DATA_PATH:-${OMNIA_DATA_PATH:-/opt/omnia}/telemetry}/output/${OMNIA_PROJECT_NAME:-project_default}/telemetry_status.yml"
```

Confirm that `overall_status` is `success`, enabled components report
`deployed`, disabled components report `skipped`, and any node listed under
`deploy_unreachable_nodes.ldms` is intentionally unavailable. Use the
source-specific verification page when validating metrics or logs after the
initial deployment.

## Next steps

- Export Kafka or Victoria connection details for external producers and
  consumers when required.
- Use the source-specific configuration pages to add or change a telemetry
  route, then validate and redeploy.
- Preserve `telemetry_status.yml` when collecting evidence for a support case.

## Troubleshooting

- **The Kubernetes VIP is unavailable:** Verify the file selected by
  `cluster_inventory` and restore root SSH access from the OIM.
- **Input validation fails:** Check all three YAML inputs against the schemas
  under `src/telemetry/plugins/module_utils/input_validation/schema/`.
- **A component reports `failed`:** Inspect `/var/log/omnia/telemetry/` and
  the corresponding resources in the `telemetry` namespace.
- **LDMS nodes are skipped:** Check the hostnames under
  `deploy_unreachable_nodes.ldms` and restore their SSH reachability before
  redeploying.
