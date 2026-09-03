# iDRAC Metrics


This page catalogs the metrics collected by the Omnia iDRAC telemetry collector via the Redfish API. These metrics are streamed to Kafka and stored in VictoriaMetrics for visualization in Victoria Metrics UI.

For the complete list of iDRAC telemetry metrics, see [Dell iDRAC Telemetry Reference Guide](https://dl.dell.com/content/manual43363890-dell-idrac-telemetry-reference-guide.pdf?language=en-us) and [iDRAC Telemetry Reference Tools](https://github.com/dell/iDRAC-Telemetry-Reference-Tools).

!!! note

    Some iDRAC telemetry metrics are not available on all server platforms. For example, PowerEdge XE8712 servers with NVIDIA GB200 accelerators support a limited set of iDRAC telemetry metrics. For details, see [Known Limitations: Limited iDRAC Telemetry Metrics for PowerEdge XE8712](https://omnia-devel.readthedocs.io/en/v2.2.0.0/Troubleshooting/known_limitations.html#limited-idrac-telemetry-metrics-for-poweredge-xe8712).

## Collection Method


| Property | Value |
| --- | --- |
| **Protocol** | Redfish SSE (HTTPS REST API) |
| **Source** | iDRAC on each managed Dell PowerEdge server |
| **Default interval** | 300 seconds (configurable via `idrac_telemetry_interval` in `telemetry_config.yml`) |
| **Kafka topic** | `idrac` |
| **Storage** | VictoriaMetrics time-series database |

















