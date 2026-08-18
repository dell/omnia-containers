
# UFM Metrics


This page catalogs the InfiniBand fabric metrics collected by the NVIDIA
Unified Fabric Manager (UFM) Prometheus exporter. These metrics are scraped
by vmagent and stored in VictoriaMetrics.

## Collection Method


| Property | Value |
| --- | --- |
| **Collection tool** | UFM Prometheus Exporter |
| **Protocol** | Prometheus scrape over HTTPS |
| **Default port** | 9001 |
| **Default interval** | 30 seconds (configurable via `scrape_interval` in `telemetry_config.yml`) |
| **Storage** | VictoriaMetrics time-series database |

!!! info

    - [Telemetry Config](../Configuration/telemetry_config.md) -- UFM telemetry
      configuration parameters.
    - [NVIDIA UFM Enterprise User Manual](https://docs.nvidia.com/networking/display/ufmenterpriseumv6242/) -- UFM documentation.
    - [Idrac Metrics](idrac_metrics.md) -- Hardware-level metrics from iDRAC.
    - [Ldms Metrics](ldms_metrics.md) -- OS-level metrics from LDMS.
