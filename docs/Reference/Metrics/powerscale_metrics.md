# PowerScale Metrics


This page catalogs the metrics collected by the Omnia PowerScale telemetry pipeline via the CSM Observability framework. These metrics are stored in VictoriaMetrics for visualization in Victoria Metrics UI.

For the complete list of PowerScale metrics, see [Dell CSM Observability PowerScale metrics](https://dell.github.io/csm-docs/docs/concepts/observability/metrics/powerscale/).

In addition to the standard PowerScale metrics, Omnia also supports the following:

- Health Metrics
- CSI Health Monitor Metrics

## Collection Method


| Property | Value |
| --- | --- |
| **Collection tool** | CSM Metrics for PowerScale (Karavi Observability) |
| **Protocol** | OneFS REST API → OpenTelemetry Collector → Prometheus scrape |
| **Default interval** | 30 seconds (configurable via `scrape_interval` in CSM Observability values.yaml) |
| **Storage** | VictoriaMetrics time-series database |