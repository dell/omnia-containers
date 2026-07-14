
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

## Port State Metrics


| Metric | Unit | Description |
| --- | --- | --- |
| `ufm_port_state` | Enum | InfiniBand port operational state (`active`, `down`, `disabled`, `init`). |
| `ufm_port_physical_state` | Enum | Physical port state (`LinkUp`, `Disabled`, `Polling`, `Sleep`). |
| `ufm_port_link_width` | Count | Active link width (1x, 4x, 8x, 12x). |
| `ufm_port_link_speed` | Gbps | Active link speed (SDR, DDR, QDR, FDR, EDR, HDR, NDR). |

## Traffic Counter Metrics


| Metric | Unit | Description |
| --- | --- | --- |
| `ufm_port_xmit_data` | Bytes | Total data transmitted on the port (cumulative). |
| `ufm_port_rcv_data` | Bytes | Total data received on the port (cumulative). |
| `ufm_port_xmit_data_rate` | Bytes/s | Transmit data rate. |
| `ufm_port_rcv_data_rate` | Bytes/s | Receive data rate. |
| `ufm_port_xmit_packets` | Count | Total packets transmitted (cumulative). |
| `ufm_port_rcv_packets` | Count | Total packets received (cumulative). |

## Error Counter Metrics


| Metric | Unit | Description |
| --- | --- | --- |
| `ufm_port_symbol_errors` | Count | Total symbol errors detected (cumulative). |
| `ufm_port_link_error_recovery` | Count | Total link error recovery events (cumulative). |
| `ufm_port_link_downed` | Count | Total link downed events (cumulative). |
| `ufm_port_rcv_errors` | Count | Total receive errors (cumulative). |
| `ufm_port_rcv_remote_physical_errors` | Count | Remote physical receive errors (cumulative). |
| `ufm_port_rcv_switch_relay_errors` | Count | Switch relay errors (cumulative). |
| `ufm_port_xmit_discards` | Count | Transmit discards (cumulative). |
| `ufm_port_xmit_constraint_errors` | Count | Transmit constraint errors (cumulative). |
| `ufm_port_rcv_constraint_errors` | Count | Receive constraint errors (cumulative). |
| `ufm_port_local_link_integrity_errors` | Count | Local link integrity errors (cumulative). |
| `ufm_port_excessive_buffer_overrun_errors` | Count | Excessive buffer overrun errors (cumulative). |
| `ufm_port_vl15_dropped` | Count | VL15 packets dropped (cumulative). |

## Fabric Topology Metrics


| Metric | Unit | Description |
| --- | --- | --- |
| `ufm_switch_info` | Info | Switch metadata. Labels: `switch_name`, `guid`, `type`, `firmware`. |
| `ufm_port_mapping` | Info | Port-to-node mapping. Labels: `local_port`, `remote_guid`, `remote_port`. |
| `ufm_node_guid` | Info | Node GUID information. |
| `ufm_lid_assignment` | Count | LID assigned to each port. |

## Telemetry Health Metrics


| Metric | Unit | Description |
| --- | --- | --- |
| `scrape_duration_seconds` | Seconds | Duration of the Prometheus scrape for UFM endpoint. |
| `up` | Enum | Whether the UFM scrape target is reachable (1=up, 0=down). |

## Metric Labels


All UFM metrics include the following common labels:

| Label | Description |
| --- | --- |
| `instance` | UFM appliance endpoint (IP:port). |
| `node_guid` | InfiniBand node GUID. |
| `port_num` | Port number on the switch or HCA. |
| `switch_name` | Name of the InfiniBand switch (switch metrics only). |

!!! info

    - [Telemetry Config](../Configuration/telemetry_config.md) -- UFM telemetry
      configuration parameters.
    - [NVIDIA UFM Enterprise User Manual](https://docs.nvidia.com/networking/display/ufmenterpriseumv6242/) -- UFM documentation.
    - [Idrac Metrics](idrac_metrics.md) -- Hardware-level metrics from iDRAC.
    - [Ldms Metrics](ldms_metrics.md) -- OS-level metrics from LDMS.
