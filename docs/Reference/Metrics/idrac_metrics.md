
# iDRAC Metrics


This page catalogs the metrics collected by the Omnia iDRAC telemetry
collector via the Redfish API. These metrics are streamed to Kafka and stored
in VictoriaMetrics for visualization in Victoria Metrics UI.

For the complete list of iDRAC telemetry metrics, see [Dell iDRAC Telemetry Reference Guide](https://dl.dell.com/content/manual43363890-dell-idrac-telemetry-reference-guide.pdf?language=en-us) and [iDRAC Telemetry Reference Tools](https://github.com/dell/iDRAC-Telemetry-Reference-Tools).

Some iDRAC telemetry metrics are not available on all server platforms. For example, PowerEdge XE8712 servers with NVIDIA GB200 accelerators support a limited set of iDRAC telemetry metrics. For details, see [Known Limitations: Limited iDRAC Telemetry Metrics for PowerEdge XE8712](https://omnia-devel.readthedocs.io/en/v2.2.0.0/Troubleshooting/known_limitations.html#limited-idrac-telemetry-metrics-for-poweredge-xe8712).

## Collection Method


| Property | Value |
| --- | --- |
| **Protocol** | Redfish SSE (HTTPS REST API) |
| **Source** | iDRAC on each managed Dell PowerEdge server |
| **Default interval** | 300 seconds (configurable via `idrac_telemetry_interval` in `telemetry_config.yml`) |
| **Kafka topic** | `idrac` |
| **Storage** | VictoriaMetrics time-series database |

## Power Metrics

Redfish reports: `PowerMetrics`, `PowerStatistics`, `Sensor`

| Metric | Unit | Description |
| --- | --- | --- |
| `SystemPowerConsumption` | Watts | Current total server power consumption. |
| `SystemInputPower` | Watts | Total input power to the server. |
| `SystemOutputPower` | Watts | Total output power from PSUs. |
| `SystemHeadRoomInstantaneous` | Watts | Instantaneous headroom between consumed and capped power. |
| `TotalCPUPower` | Watts | Total power consumed by all CPUs. |
| `TotalMemoryPower` | Watts | Total power consumed by all DIMMs. |
| `TotalFanPower` | Watts | Total power consumed by all fans. |
| `TotalPciePower` | Watts | Total power consumed by PCIe devices. |
| `TotalStoragePower` | Watts | Total power consumed by storage devices. |
| `LastHourAvgPower` | Watts | Average power consumption over the last hour. |
| `LastHourMaxPower` | Watts | Peak power consumption in the last hour. |
| `LastDayAvgPower` | Watts | Average power consumption over the last day. |
| `LastWeekAvgPower` | Watts | Average power consumption over the last week. |
| `WattsReading` | Watts | Per-PSU power reading. |

## Thermal Metrics

Redfish reports: `ThermalSensor`, `ThermalMetrics`, `CPUSensor`, `MemorySensor`, `StorageSensor`

| Metric | Unit | Description |
| --- | --- | --- |
| `TemperatureReading` | Celsius | Temperature reading from each sensor (inlet, outlet, CPU, DIMM, storage, etc.). Labeled by sensor location. |
| `SysRackTempDelta` | Celsius | Temperature delta between inlet and outlet (rack-level thermal efficiency). |
| `SysNetAirflow` | CFM | Net system airflow. |
| `SysAirflowUtilization` | Percent | System airflow utilization as a percentage of total capacity. |
| `ComputePower` | Watts | Compute subsystem power (thermal context). |
| `ITUE` | Ratio | IT Usage Efficiency ratio. |
| `TotalPSUHeatDissipation` | BTU/hr | Total heat dissipation from all PSUs. |

## Fan Metrics

Redfish report: `FanSensor`

| Metric | Unit | Description |
| --- | --- | --- |
| `RPMReading` | RPM | Current fan rotational speed. One metric per fan. |

## Sensor Metrics

Redfish report: `Sensor`

| Metric | Unit | Description |
| --- | --- | --- |
| `VoltageReading` | Volts | Voltage reading from each voltage sensor. |
| `AmpsReading` | Amps | Current (amperage) reading from each PSU. |
| `TemperatureReading` | Celsius | Temperature reading from generic sensors. |
| `CPUUsagePctReading` | Percent | CPU utilization percentage. |
| `IOUsagePctReading` | Percent | I/O subsystem utilization percentage. |
| `MemoryUsagePctReading` | Percent | Memory utilization percentage. |
| `SystemUsagePctReading` | Percent | Overall system usage percentage. |

## CPU and Memory Metrics

Redfish report: `CPUMemMetrics`

| Metric | Unit | Description |
| --- | --- | --- |
| `CPUC0ResidencyHigh` | Count | CPU C0 residency counter (high word). Higher values indicate more active CPU time. |
| `CPUC0ResidencyLow` | Count | CPU C0 residency counter (low word). |
| `AvgFrequencyAcrossCores` | MHz | Average frequency across all CPU cores. |
| `CPUPkgEnergy` | Joules | CPU package energy consumed. |
| `DRAMPkgEnergy` | Joules | DRAM package energy consumed. |
| `PkgPwr` | Watts | CPU package power. |
| `DRAMPwr` | Watts | DRAM power. |
| `TJMax` | Celsius | Maximum junction temperature for the CPU. |
| `PkgThermalStatus` | Enum | CPU package thermal status. |
| `DRAMThrottling` | Enum | DRAM throttling state. |
| `CPUViolationCounter` | Count | CPU power/thermal violation counter. |
| `DDRLimitingCounter` | Count | DDR power limiting event counter. |

## Memory Health Metrics

Redfish report: `MemoryMetrics`

| Metric | Unit | Description |
| --- | --- | --- |
| `CorrectableECCError` | Count | Correctable ECC error count per DIMM. Non-zero values may indicate impending DIMM failure. |
| `UncorrectableECCError` | Count | Uncorrectable ECC error count per DIMM. |
| `AddressParityError` | Count | Address parity error count. |
| `DataLossDetected` | Enum | Whether data loss has been detected on the DIMM. |
| `MemorySpareBlock` | Count | Spare block availability status. |
| `PredictedMediaLifeLeftPercent` | Percent | Predicted media life remaining (persistent memory). |
| `TemperatureThresholdAlarm` | Enum | Temperature threshold alarm state. |

## Storage Health Metrics

Redfish reports: `StorageDiskSMARTData`, `NVMeSMARTData`

| Metric | Unit | Description |
| --- | --- | --- |
| `DriveTemperature` | Celsius | Current drive temperature. |
| `PercentDriveLifeRemaining` | Percent | Estimated drive life remaining. |
| `PowerOnHours` | Hours | Total power-on hours. |
| `PowerCycleCount` | Count | Total power cycle count. |
| `ReadErrorRate` | Count | Read error rate. |
| `CRCErrorCount` | Count | CRC error count. |
| `ReallocatedBlockCount` | Count | Reallocated sector/block count. |
| `UncorrectableErrorCount` | Count | Uncorrectable error count. |
| `MediaWriteCount` | Count | Total media write count (SSD wear indicator). |
| `CommandTimeout` | Count | Command timeout count. |
| `AvailableSpare` | Percent | NVMe available spare capacity percentage. |
| `AvailableSpareThreshold` | Percent | NVMe available spare threshold. |
| `PercentageUsed` | Percent | NVMe percentage of drive life used. |
| `CriticalWarning` | Bitmask | NVMe critical warning flags. |
| `CompositeTemparature` | Celsius | NVMe composite temperature. |

## GPU Metrics (via iDRAC)

iDRAC collects out-of-band GPU metrics from installed GPUs via the Redfish API. 

Redfish reports: `GPUMetrics`, `GPUStatistics`

**GPUMetrics:**

| Metric | Unit | Description |
| --- | --- | --- |
| `GPUUsage` | Percent | GPU utilization percentage. |
| `GPUMemoryUsage` | Percent | GPU memory utilization percentage. |
| `GPUClockFrequency` | MHz | Current GPU clock frequency. |
| `GPUMemoryClockFrequency` | MHz | Current GPU memory clock frequency. |
| `PowerConsumption` | Watts | Current GPU power consumption. |
| `PrimaryTemperature` | Celsius | Primary GPU temperature. |
| `SecondaryTemperature` | Celsius | Secondary GPU temperature. |
| `BoardTemperature` | Celsius | GPU board temperature. |
| `MemoryTemperature` | Celsius | GPU memory temperature. |
| `GPUHealth` | Enum | GPU health status. |
| `GPUStatus` | Enum | GPU operational status. |
| `BoardPowerSupplyStatus` | Enum | GPU board power supply status. |
| `PowerSupplyStatus` | Enum | GPU power supply status. |
| `PowerBrakeState` | Enum | GPU power brake state. |
| `ThermalAlertState` | Enum | GPU thermal alert state. |
| `GPUArbitratedPowerLimit` | Watts | GPU arbitrated power limit. |
| `GPUEnforcedPowerLimit` | Watts | GPU enforced power limit. |
| `GPUPCIeLinkSpeed` | GT/s | Current PCIe link speed. |
| `GPUPCIeLinkSpeedMax` | GT/s | Maximum PCIe link speed. |
| `GPUPCIeRxThroughput` | KB/s | PCIe receive throughput. |
| `GPUPCIeTxThroughput` | KB/s | PCIe transmit throughput. |
| `GPUPCIeCorrectableErrorCount` | Count | PCIe correctable error count. |
| `GPUMemBandwidthUsage` | Percent | GPU memory bandwidth usage. |
| `GPUClockEventReason` | Bitmask | Reason for GPU clock frequency changes. |
| `GPUSMActivity` | Percent | SM (Streaming Multiprocessor) activity. |
| `GPUSMOccupancy` | Percent | SM occupancy. |
| `GPUTensorCoreUsage` | Percent | Tensor core utilization. |
| `GPUHmmaUsage` | Percent | HMMA (Half-precision Matrix Multiply Accumulate) usage. |

**GPUStatistics (ECC error counters):**

| Metric | Unit | Description |
| --- | --- | --- |
| `SBECounterFB` | Count | Single-bit ECC errors in framebuffer. |
| `DBECounterFB` | Count | Double-bit ECC errors in framebuffer. |
| `SBECounterFBL2Cache` | Count | Single-bit ECC errors in FB L2 cache. |
| `DBECounterFBL2Cache` | Count | Double-bit ECC errors in FB L2 cache. |
| `SBECounterGRL1Cache` | Count | Single-bit ECC errors in GR L1 cache. |
| `DBECounterGRL1Cache` | Count | Double-bit ECC errors in GR L1 cache. |
| `SBECounterGRRF` | Count | Single-bit ECC errors in GR register file. |
| `DBECounterGRRF` | Count | Double-bit ECC errors in GR register file. |
| `SBECounterGRTex` | Count | Single-bit ECC errors in GR texture memory. |
| `DBECounterGRTex` | Count | Double-bit ECC errors in GR texture memory. |
| `CumulativeSBECounterFB` | Count | Cumulative single-bit ECC errors in framebuffer. |
| `CumulativeDBECounterFB` | Count | Cumulative double-bit ECC errors in framebuffer. |
| `CumulativeSBECounterGR` | Count | Cumulative single-bit ECC errors in GR. |
| `CumulativeDBECounterGR` | Count | Cumulative double-bit ECC errors in GR. |
| `SBERetiredPages` | Count | Memory pages retired due to single-bit errors. |
| `DBERetiredPages` | Count | Memory pages retired due to double-bit errors. |

## NIC Metrics

Redfish reports: `NICStatistics`, `NICSensor`

| Metric | Unit | Description |
| --- | --- | --- |
| `RxBytes` | Bytes | Total bytes received (cumulative). |
| `TxBytes` | Bytes | Total bytes transmitted (cumulative). |
| `RxUnicast` | Count | Unicast packets received. |
| `TxUnicast` | Count | Unicast packets transmitted. |
| `RxBroadcast` | Count | Broadcast packets received. |
| `TxBroadcast` | Count | Broadcast packets transmitted. |
| `LanFCSRxErrors` | Count | LAN FCS receive errors. |
| `LinkStatus` | Enum | NIC link status. |
| `OSDriverState` | Enum | OS driver state. |
| `TemperatureReading` | Celsius | NIC temperature. |

## PSU Metrics

Redfish report: `PSUMetrics`

| Metric | Unit | Description |
| --- | --- | --- |
| `PSURPMReading` | RPM | PSU fan speed. |
| `PSUTemperatureReading` | Celsius | PSU temperature. |

## System Usage Metrics

Redfish report: `SystemUsage`

| Metric | Unit | Description |
| --- | --- | --- |
| `CPUUsage` | Percent | Overall CPU usage. |
| `IOUsage` | Percent | Overall I/O usage. |
| `MemoryUsage` | Percent | Overall memory usage. |
| `AggregateUsage` | Percent | Aggregate system usage. |

## Metric Labels


All iDRAC metrics include the following common labels:

| Label | Description |
| --- | --- |
| `host` | Hostname of the server (as assigned in the PXE mapping file). |
| `service_tag` | Dell service tag of the server. |
| `bmc_ip` | IP address of the iDRAC interface. |

!!! info

    - [Telemetry Config](../Configuration/telemetry_config.md) -- iDRAC telemetry
      configuration parameters.
    - [Ldms Metrics](ldms_metrics.md) -- OS-level metrics from LDMS.
