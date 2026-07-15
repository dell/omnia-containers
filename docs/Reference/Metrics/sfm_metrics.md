
# SFM Metrics


This page catalogs the network telemetry metrics collected by the Smart Fabric
Manager (SFM) via Prometheus Remote Write. These metrics are ingested into
VictoriaMetrics through the vminsert endpoint.

## Collection Method


| Property | Value |
| --- | --- |
| **Collection tool** | SFM Prometheus Exporter |
| **Protocol** | Prometheus Remote Write over TLS |
| **Ingestion endpoint** | vminsert (port 8480) |
| **Storage** | VictoriaMetrics time-series database |

## Transceiver DOM Metrics


| Metric | Unit | Description |
| --- | --- | --- |
| `sfm_transceiver_tx_power` | dBm | Optical transmit power per transceiver lane. |
| `sfm_transceiver_rx_power` | dBm | Optical receive power per transceiver lane. |
| `sfm_transceiver_temperature` | Celsius | Transceiver module temperature. |
| `sfm_transceiver_voltage` | Volts | Transceiver supply voltage. |
| `sfm_transceiver_bias_current` | mA | Laser bias current per transceiver lane. |

## Queue Statistics Metrics


| Metric | Unit | Description |
| --- | --- | --- |
| `sfm_queue_depth` | Count | Current queue depth. |
| `sfm_egress_queue_counters` | Count | Egress queue packet counters. |
| `sfm_multicast_queue_counters` | Count | Multicast queue packet counters. |

## Interface Counter Metrics


| Metric | Unit | Description |
| --- | --- | --- |
| `sfm_interface_tx_bytes` | Bytes | Total bytes transmitted on the interface (cumulative). |
| `sfm_interface_rx_bytes` | Bytes | Total bytes received on the interface (cumulative). |
| `sfm_interface_tx_packets` | Count | Total packets transmitted (cumulative). |
| `sfm_interface_rx_packets` | Count | Total packets received (cumulative). |
| `sfm_interface_tx_errors` | Count | Total transmit errors (cumulative). |
| `sfm_interface_rx_errors` | Count | Total receive errors (cumulative). |
| `sfm_interface_tx_drops` | Count | Total transmit drops (cumulative). |
| `sfm_interface_rx_drops` | Count | Total receive drops (cumulative). |

## Error Counter Metrics


| Metric | Unit | Description |
| --- | --- | --- |
| `sfm_crc_errors` | Count | CRC errors per interface (cumulative). |
| `sfm_alignment_errors` | Count | Alignment errors per interface (cumulative). |
| `sfm_symbol_errors` | Count | Symbol errors per interface (cumulative). |
| `sfm_fcs_errors` | Count | Frame Check Sequence errors per interface (cumulative). |

## Metric Labels


All SFM metrics include the following common labels:

| Label | Description |
| --- | --- |
| `instance` | SFM appliance identifier. |
| `interface` | Network interface name or port identifier. |
| `switch` | Switch name or identifier. |
| `lane` | Transceiver lane number (DOM metrics only). |

!!! info

    - [Telemetry Config](../Configuration/telemetry_config.md) -- SFM telemetry
      configuration parameters.
    - [Idrac Metrics](idrac_metrics.md) -- Hardware-level metrics from iDRAC.
    - [Ldms Metrics](ldms_metrics.md) -- OS-level metrics from LDMS.
