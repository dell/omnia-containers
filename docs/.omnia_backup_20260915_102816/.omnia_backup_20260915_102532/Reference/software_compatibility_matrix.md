# Software Compatibility Matrix

This matrix provides a quick reference to the external software products and firmware versions that have been validated with the current Omnia release. These versions are recommended for supported deployments to ensure optimal compatibility and stability.

## Validated Software and Firmware Versions

| Software Product | Omnia Validated Version |
| --- | --- |
| OpenManage Enterprise (OME) | 4.7.0.191 |
| Smart Fabric Manager (SFM) | 2.1.0.0746 |
| PowerScale OneFS | 9.14.0.0 |
| Enterprise SONiC | 4.5.2 |
| NVIDIA Unified Fabric Manager (UFM) for InfiniBand | 6.25.1-7 |
| VAST | 5.4.3 |
| iDRAC 9 (16G) | 7.30.30.51 |
| iDRAC 10 (17G) | 1.30.30.50 |
| XE8712 iDRAC Firmware | 1.30.03.10 |

## Version Notes

- **OpenManage Enterprise (OME)**: Required for BMC discovery and management features. Ensure OME API access is configured for automated discovery workflows.
- **Smart Fabric Manager (SFM)**: Required for fabric telemetry collection. Telemetry integration supports SFM 2.1.0.0746 and later.
- **PowerScale OneFS**: Validated for storage telemetry integration. Ensure CSI drivers are compatible with the OneFS version.
- **Enterprise SONiC**: Validated for Dell SmartFabric Manager SONiC deployments. Network telemetry integration requires SONiC 4.5.2 or later.
- **NVIDIA Unified Fabric Manager (UFM)**: Required for InfiniBand fabric monitoring and telemetry. UFM 6.25.1-7 provides the Prometheus exporter endpoints used by Omnia.
- **VAST**: Validated for VAST storage telemetry integration. Ensure VAST client compatibility with the deployed version.
- **iDRAC Firmware**: Validated firmware versions for Dell PowerEdge servers. iDRAC 9 supports 16G platforms, iDRAC 10 supports 17G platforms, and XE8712 is specific to certain PowerEdge models. Ensure iDRAC API access is enabled for automated operations.

## Related Documentation

- [Installed Software Matrix](SupportMatrix/installed_software.md) - Complete list of software components installed by Omnia
- [Cluster Requirements](ClusterRequirements/) - Hardware and infrastructure prerequisites
- [Troubleshooting](../Troubleshooting/) - Common issues and resolutions
