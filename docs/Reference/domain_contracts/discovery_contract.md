# Discovery Input/Output Contract

## Input Contract

### Input Files

| File | Location | Required | Description |
|------|----------|----------|-------------|
| `discovery_config.yml` | `/opt/omnia/discovery/input/project_default/` | Yes | Discovery configuration |
| `network_spec.yml` | `/opt/omnia/discovery/input/project_default/` | Yes | Network configuration |

### Input Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `discovery_mechanism` | string | Yes | - | Discovery mechanism (ome, manual) |
| `ome_host` | string | No | - | OME server hostname |
| `ome_username` | string | No | - | OME username |
| `ome_password` | string | No | - | OME password |

## Output Contract

### Output Files

| File | Location | Description |
|------|----------|-------------|
| `pxe_mapping_file.csv` | `/opt/omnia/discovery/input/project_default/` | PXE mapping file |
| `discovery_status.yml` | `/opt/omnia/discovery/output/` | Discovery status |

### Output Artifacts

- PXE mapping file for node provisioning
- Discovery inventory report
- BMC and NIC information

## Execution Flow

1. **Validate Configuration**: Check discovery configuration
2. **Discover Nodes**: Query OME or manual inventory
3. **Generate Mapping File**: Create PXE mapping file
4. **Verify Mapping**: Validate mapping file entries

## Related Documentation

- [Domain Overview](../../HowTo/discovery/index.md)
- [Configuration Reference](../../Reference/Configuration/discovery_config.md)






