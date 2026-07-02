
# discovery_config.yml Reference

File path: `/opt/omnia/input/discovery_config.yml`

This file configures node discovery settings, including BMC discovery via
Dell OpenManage Enterprise (OME).

## Parameters

--8<-- "html/discovery_config.html"

## Usage example
```yaml title="File: /opt/omnia/input/discovery_config.yml"
---
#### BMC Discovery
enable_bmc_discovery: false

# IP address of the Dell OpenManage Enterprise (OME) instance
ome_ip: ""
```

!!! note

    - When `enable_bmc_discovery` is set to `true`, OME credentials (`ome_username`, `ome_password`) are managed separately via `get_config_credentials`.
    - The `ome_ip` field is required only when BMC discovery is enabled.
