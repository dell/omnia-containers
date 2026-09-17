
# additional_cloud_init.yml

This file provides additional cloud-init configuration for stateless node
provisioning. It allows writing files and running commands on nodes during
the cloud-init final stage.

Set `additional_cloud_init_config_file` in `orchestrator_config.yml` to the
absolute path of this file. Orchestrator validates the file and publishes its
common and per-functional-group directives through the OpenCHAMI provisioning
workflow. Leave the setting empty to disable additional cloud-init.

## Parameter Reference

--8<-- "html/additional_cloud_init.html"

## Usage example
```yaml title="File: $OMNIA_DATA_PATH/orchestrator/input/$OMNIA_PROJECT_NAME/additional_cloud_init.yml"
---
# Common cloud-init applied to ALL nodes
common:
  write_files:
    - path: /etc/motd
      content: "Welcome to the HPC cluster\n"
      permissions: '0644'
  runcmd:
    - echo "Custom node setup complete" >> /var/log/custom_setup.log

# Per-functional-group cloud-init overrides
groups:
  slurm_node_rhel_10_0_aarch64:
    runcmd:
      - echo "Slurm node setup" >> /var/log/custom.log
  os_rhel_10_0_x86_64:
    write_files:
      - path: /etc/profile.d/cluster.sh
        content: |
          export CLUSTER_NAME=mycluster
        permissions: '0644'
```

!!! warning "Unsupported keys"

    The following keys are platform-managed and must **not** be used in this file:
    `bootcmd`, `network`, `network-config`, `packages`.
    Orchestrator input validation rejects these keys before provisioning.

!!! note

    - Platform-defined defaults always take precedence (`merge_how: no_replace`).
    - User entries are appended to platform lists (`write_files`, `runcmd`).
    - Group-specific entries are merged **after** common entries.
    - Group names must exactly match `FUNCTIONAL_GROUP_NAME` values in
      `pxe_mapping_file.csv`; copy the value from the active project rather
      than deriving or shortening it.

## Validation

The Orchestrator `validate` phase checks that the configured file exists, is
readable YAML, and contains only `common` and `groups` at the top level. It
validates `write_files` entries, `runcmd` strings, permissions, encodings,
boolean `append` values, prohibited keys, and functional-group names against
the active PXE mapping file.

!!! info

    - This file is optional and can be used to add custom cloud-init configuration to the platform.
    - Refer official cloud-init documentation for [`write_files`](https://docs.cloud-init.io/en/latest/reference/modules.html#write-files) and [`runcmd`](https://docs.cloud-init.io/en/latest/reference/modules.html#runcmd) for more details.













