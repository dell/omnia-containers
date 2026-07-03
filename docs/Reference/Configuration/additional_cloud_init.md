
# additional_cloud_init.yml Reference

File path: `/opt/omnia/input/additional_cloud_init.yml`

This file provides additional cloud-init configuration for stateless node
provisioning. It allows writing files and running commands on nodes during
the cloud-init final stage.

## Additional cloud-init Configuration Parameters

--8<-- "html/additional_cloud_init.html"

## Usage example
```yaml title="File: /opt/omnia/input/additional_cloud_init.yml"
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
  slurm_node_x86_64:
    runcmd:
      - echo "Slurm node setup" >> /var/log/custom.log
  os_x86_64:
    write_files:
      - path: /etc/profile.d/cluster.sh
        content: |
          export CLUSTER_NAME=mycluster
        permissions: '0644'
```

!!! warning "Prohibited keys"

    The following keys are platform-managed and must **not** be used in this file:
    `bootcmd`, `network`, `network-config`, `packages`.
    Validation will fail if any of these are present.

!!! note

    - Platform-defined defaults always take precedence (`merge_how: no_replace`).
    - User entries are appended to platform lists (`write_files`, `runcmd`).
    - Group-specific entries are merged **after** common entries.
    - Group names must match functional groups defined in `pxe_mapping_file.csv`.

!!! info

    - This file is optional and can be used to add custom cloud-init configuration to the platform.
    - Refer official cloud-init documentation for [`write_files`](https://docs.cloud-init.io/en/latest/reference/modules.html#write-files) and [`runcmd`](https://docs.cloud-init.io/en/latest/reference/modules.html#runcmd) for more details.


