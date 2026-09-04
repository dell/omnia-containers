# discovery Config Reference

The `discovery_config.yml` file configures node discovery and mapping file generation.

## Location

```
/opt/omnia/discovery/input/project_default/discovery_config.yml
```

## Configuration Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `discovery_mechanism` | string | Yes | - | Discovery mechanism (ome, manual) |
| `ome_host` | string | No | - | OME server hostname |
| `ome_username` | string | No | - | OME username |
| `ome_password` | string | No | - | OME password |
| `static_group_name` | string | No | - | OME static group name |

## Usage Example

```yaml title="File: /opt/omnia/discovery/input/project_default/discovery_config.yml"
discovery_mechanism: ome
ome_host: ome.example.com
ome_username: admin
ome_password: your_password
static_group_name: omnia-cluster
```

## Related Configuration

- [network_spec.md](network_spec.md)
- [Domain Contract](../domain_contracts/discovery_contract.md)




