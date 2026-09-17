# set_pxe_boot_config.yml

This file controls iDRAC PXE boot behavior and optional verification of a
fresh operating-system boot and cloud-init completion.

## Location

```text
$OMNIA_DATA_PATH/orchestrator/input/$OMNIA_PROJECT_NAME/set_pxe_boot_config.yml
```

The Orchestrator data root is `$OMNIA_DATA_PATH/orchestrator`.

## Parameters

| Parameter | Type | Source value | Description |
|---|---|---|---|
| `enable_node_registration` | boolean | `true` | Verify passwordless root SSH, boot freshness, and cloud-init completion after PXE boot. |
| `node_registration_pause_minutes` | integer | `3` | Initial wait before polling begins. |
| `node_registration_retries` | integer | `120` | Maximum number of registration polling attempts. |
| `node_registration_delay` | integer | `15` | Delay between polling attempts, in seconds. |
| `restart_host` | boolean | `true` | Restart the host after setting its boot source. |
| `force_restart` | boolean | `true` | Use `ForceRestart`; `false` selects `GracefulRestart`. |
| `boot_source_override_enabled` | string | `continuous` | `once`, `continuous`, or `disabled`. |
| `boot_source_override_target` | string | `pxe` | Redfish boot target such as `pxe`, `uefi_http`, `hdd`, `cd`, `floppy`, `sd_card`, `utilities`, `bios_setup`, or `none`. |

The maximum registration polling period, after the initial pause, is
`node_registration_retries` multiplied by `node_registration_delay`.

## Usage example

```yaml title="File: $OMNIA_DATA_PATH/orchestrator/input/$OMNIA_PROJECT_NAME/set_pxe_boot_config.yml"
enable_node_registration: true
node_registration_pause_minutes: 3
node_registration_retries: 120
node_registration_delay: 15
restart_host: true
force_restart: true
boot_source_override_enabled: continuous
boot_source_override_target: pxe
```

Legacy `phone_home_*` variable names remain accepted by the playbook but are
deprecated in the source. Use the `node_registration_*` names above.

## Related configuration

- [Orchestrator configuration](orchestrator_config.md)
- [PXE mapping file](../SampleFiles/pxe_mapping_file.md)
