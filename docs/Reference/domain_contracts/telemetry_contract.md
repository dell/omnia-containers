# Telemetry Input/Output Contract

## Input Contract

### Input Files

| File | Location | Required | Description |
|------|----------|----------|-------------|
| `telemetry_config.yml` | `/opt/omnia/input/project_default/` | Yes | Telemetry configuration |
| `omnia_config.yml` | `/opt/omnia/input/project_default/` | Yes | Omnia cluster configuration |
| `network_spec.yml` | `/opt/omnia/input/project_default/` | Yes | Network configuration |

### Input Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `idrac_enabled` | boolean | No | false | Enable iDRAC telemetry |
| `ldms_enabled` | boolean | No | false | Enable LDMS telemetry |
| `powerscale_enabled` | boolean | No | false | Enable PowerScale telemetry |
| `ufm_enabled` | boolean | No | false | Enable UFM telemetry |
| `vast_enabled` | boolean | No | false | Enable VAST telemetry |
| `ome_enabled` | boolean | No | false | Enable OME telemetry |

## Output Contract

### Output Files

| File | Location | Description |
|------|----------|-------------|
| `telemetry_status.yml` | `/opt/omnia/telemetry/output/` | Telemetry deployment status |
| `telemetry_config.yml` | `/opt/omnia/telemetry/output/` | Generated telemetry configuration |

### Output Artifacts

- Deployed monitoring stack (Kafka, VictoriaMetrics)
- Configured telemetry samplers
- Telemetry dashboards
- Metrics storage

## Execution Flow

1. **Validate Configuration**: Check telemetry configuration
2. **Deploy Monitoring Stack**: Deploy Kafka and VictoriaMetrics
3. **Configure Samplers**: Configure iDRAC, LDMS, and other samplers
4. **Configure Bridges**: Configure metric bridges and sinks
5. **Start Collection**: Start telemetry data collection
6. **Verify Dashboards**: Verify dashboards are receiving data

## Related Documentation

- [Domain Overview](../../HowTo/Telemetry/index.md)
- [Configuration Reference](../../Reference/Configuration/telemetry_config.md)






