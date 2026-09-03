
# Supported Storage

| Platform                     | Models Supported | Models Validated | Protocols Supported |
| ---------------------------- | ---------------- | ---------------- | ------------------- |
| **Dell PowerScale (Isilon)** | F600, F710, H500, H700, H5600, H7000 | F600, H500, H700 | NFS, S3 |
| **Dell PowerVault** | ME4012, ME4024, ME4084, ME5012, ME5024, ME5084 | ME4024, ME5084 | iSCSI |

## Notes

!!! note "PowerScale Integration"

    Omnia configures NFS client mounts on cluster nodes for shared home directories and scratch filesystems. The PowerScale cluster must be configured and operational before running Omnia playbooks. Configure storage parameters in `storage_config.yml`.

!!! note "PowerVault Integration"

    Omnia configures iSCSI initiators on target nodes for block storage workloads. Pre-create LUNs and map them to host groups before running Omnia storage playbooks. DM-Multipath is recommended for redundancy.

!!! info "Related Configuration"

    - [Storage Configuration](../Configuration/storage_config.md)


















