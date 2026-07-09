
# Supported Storage


Omnia v2.1 supports the following Dell storage platforms for shared
filesystems and persistent volumes.

## Storage support matrix


| Platform | Version | Protocol | Notes |
| --- | --- | --- | --- |
| Dell PowerScale (Isilon) | OneFS 9.x | NFS, SMB | Scale-out NAS; ideal for shared home directories and scratch filesystems. Omnia configures NFS client mounts on cluster nodes. |
| Dell PowerVault ME5 | ME5 Series | iSCSI, FC, SAS | Block storage; suitable for databases, boot volumes, and high-IOPS workloads. Omnia configures iSCSI initiators on target nodes. |

## PowerScale (OneFS) integration


| Parameter | Description |
| --- | --- |
| OneFS version | 9.x (9.4 or later recommended) |
| Access zone | Configure a dedicated access zone for HPC exports to isolate permissions and authentication. |
| Protocol | NFS v3 or NFS v4.x -- configured in `storage_config.yml` (see [Storage Config](../Configuration/storage_config.md)). |
| Authentication | Local, LDAP, or Active Directory. Must match the cluster authentication method configured in `security_config.yml`. |
| SMB support | Supported for Windows or mixed-OS clients. Not used by default in Omnia HPC deployments. |

!!! note

    Omnia mounts PowerScale NFS exports on cluster nodes using the mount
    parameters specified in `storage_config.yml`. The PowerScale cluster
    itself must be configured and operational before running `omnia.yml`.

## PowerVault ME5 integration


| Parameter | Description |
| --- | --- |
| Series | ME5012, ME5024, ME5084 |
| Protocol | iSCSI (default for Omnia integration), Fibre Channel, SAS |
| Volumes | Pre-create LUNs and map them to host groups before running Omnia storage playbooks. |
| Multipath | DM-Multipath (`device-mapper-multipath`) is recommended for redundancy and load balancing. |
| Configuration | `storage_config.yml` specifies the PowerVault management IP, volume mappings, and mount points. |
