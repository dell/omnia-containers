# orchestrator_config.yml

This is the primary Orchestrator control file. It selects the PXE mapping,
provisioning behavior, optional overrides, and upstream Repo Manager and Image
Build Manager outputs.

## Location

```text
$ORCHESTRATOR_DATA_PATH/input/$OMNIA_PROJECT_NAME/orchestrator_config.yml
```

`ORCHESTRATOR_DATA_PATH` defaults to `$OMNIA_DATA_PATH/orchestrator`.

## Parameters

| Parameter | Type | Required | Default or behavior |
|---|---|---|---|
| `pxe_mapping_file_path` | string | Yes | Empty uses `pxe_mapping_file.csv` from the current project input directory. |
| `language` | string | Yes | `en_US.UTF-8`; this is the only language accepted by current validation. |
| `default_lease_time` | string or integer | Yes | `86400`; must resolve to a positive number of seconds. |
| `dns_enabled` | boolean | No | `false`; enables DNS-based hostname resolution through coresmd. |
| `kernel_version_override` | string | No | Empty selects the latest image; a value must match `X.Y.Z-suffix`. |
| `additional_cloud_init_config_file` | string | No | Empty disables additional cloud-init. Set an absolute path to a supported file; Orchestrator validates and applies its common and per-functional-group directives during provisioning. |
| `boot_kernel_params` | string | No | Additional kernel command-line parameters applied to all functional groups. |
| `catalog_file_path` | string | No | Empty uses the shared configured catalog path. |
| `enable_pxe_boot` | boolean | No | `true`; set to `false` for environments without iDRAC/BMC PXE control. |
| `image_build_manager_output_path` | string | No | Empty uses `$IMAGE_BUILD_MANAGER_DATA_PATH/output/$OMNIA_PROJECT_NAME/build_status.yml`; the component path defaults to `$OMNIA_DATA_PATH/image_build_manager`. |
| `repo_manager_output_path` | string | No | Empty uses `$OMNIA_DATA_PATH/repo_manager/output/$OMNIA_PROJECT_NAME/repo_status.yml`. |
| `dcgm_enabled` | boolean | No | `true`; enables NVIDIA DCGM installation on GPU nodes. |

The selected PXE mapping must contain the exact 11-column canonical header.
Nonempty service tags, hostnames, normalized admin MAC addresses, admin IP
addresses, and nonempty IB IP addresses must be unique. Admin IP addresses must
be valid and belong to a subnet defined in `network_spec.yml`.

## Usage example

```yaml title="File: $ORCHESTRATOR_DATA_PATH/input/$OMNIA_PROJECT_NAME/orchestrator_config.yml"
pxe_mapping_file_path: ""
language: "en_US.UTF-8"
default_lease_time: "86400"
dns_enabled: false
kernel_version_override: ""
additional_cloud_init_config_file: ""
boot_kernel_params: ""
catalog_file_path: ""
enable_pxe_boot: true
image_build_manager_output_path: ""
repo_manager_output_path: ""
dcgm_enabled: true
```

## Related configuration

- [PXE mapping file](../SampleFiles/pxe_mapping_file.md)
- [Network specification](network_spec.md)
- [Additional cloud-init](additional_cloud_init.md)
- [PXE boot configuration](set_pxe_boot_config.md)
