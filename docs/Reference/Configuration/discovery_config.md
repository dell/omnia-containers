# discovery_config.yml

The Discovery configuration identifies the OME appliance used for discovery.

## Location

```text
$OMNIA_DATA_PATH/discovery/input/$OMNIA_PROJECT_NAME/discovery_config.yml
```

The default location is
`/opt/omnia/discovery/input/project_default/discovery_config.yml`.

## Configuration parameters

| Parameter | Type | Required | Default | Description |
|---|---|---|---|---|
| `ome_ip` | IPv4 string | Yes | `""` (empty string) | OME IPv4 address. It must be valid and must not be a loopback address. |

The staged template supplies an empty `ome_ip` placeholder. Replace it with the
OME appliance's IPv4 address before validating or running Discovery.

OME credentials are not stored in this file. The credential workflow creates
the encrypted `discovery_credentials.yml` and its Vault key in the same
project directory.

OME is the only supported Discovery backend.

## Usage example

```yaml title="File: /opt/omnia/discovery/input/project_default/discovery_config.yml"
ome_ip: "192.168.1.100"
```

## Related configuration

- [Network specification](network_spec.md)
- [Discovery contract](../domain_contracts/discovery_contract.md)
- [Discover nodes using OME](../../HowTo/discovery/discover_nodes.md)
