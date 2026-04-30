Configuring Mounts
==================

The storage configuration in Omnia allows you to define and manage various storage mounts, PowerVault configurations, and swap settings. This configuration is specified in the ``/opt/omnia/input/project_default/storage_config.yml`` file.

.. note:: The storage configuration supports multiple storage types including NFS, iSCSI (PowerVault), local filesystems, and swap files. Each storage type can be targeted to specific functional groups or node groups.

mounts
-------

The ``mounts`` section defines cloud-init compatible mount configurations that are applied during node provisioning. These mounts can include network filesystems, local devices, or bind mounts.

**Parameters**

- **name** (string, required): Unique identifier for this mount entry
- **source** (string, required): Device name or network path (e.g., ``/dev/sdc``, ``UUID=xxx``, ``192.168.1.100:/export/share``, ``powervault:<name>``)
- **mount_point** (string, required): Mount point path
- **fs_type** (string, optional): Filesystem type. Overrides mount_params profile when specified. Supported values: ``auto``, ``ext2``, ``ext3``, ``ext4``, ``xfs``, ``btrfs``, ``nfs``, ``nfs4``, ``cifs``, ``tmpfs``, ``cephfs``, ``vfat``, ``ntfs``, ``none``, ``beegfs``, ``fuse.s3fs``
- **mnt_opts** (string, optional): Mount options. Overrides mount_params profile when specified
- **dump_freq** (string, optional): Dump frequency (usually 0). Default: ``0``
- **fsck_pass** (string, optional): Fsck pass number (usually 0 or 2). Default: ``0``
- **mount_params** (string, optional): Name of the mount_params profile to use for unspecified fields
- **mount_on_oim** (boolean, optional): Whether to mount this filesystem on the OIM node. Default: ``false``
- **node_key** (string, optional): ds.meta_data key for per-node bind mounts. When present, fs_type is forced to none and mnt_opts to bind
- **node_mount_point** (array, optional): List of bind mount target paths. Required when node_key is set
- **functional_group_prefix** (array, optional): List of functional group prefixes for node targeting. Mutually exclusive with groups
- **groups** (array, optional): List of GROUP_NAME values from pxe_mapping_file.csv. Mutually exclusive with functional_group_prefix
- **permissions** (object, optional): Directory ownership and mode applied to mount_point after mount
  - **owner** (string, optional): User owner of the mount point. Default: ``root``
  - **group** (string, optional): Group owner of the mount point. Default: ``root``
  - **mode** (string, optional): Octal permission mode (e.g., ``0755``, ``1777``). Default: ``0755``

**Sample Configuration**

::

    mounts:
      - name: "nfs_slurm"
        source: "172.16.0.254:/mnt/share/omnia"
        mount_point: "/opt/omnia/slurm_mount"
        fs_type: "nfs"
        mnt_opts: "nosuid,rw,sync,hard,intr"
        mount_on_oim: true
        functional_group_prefix: ["slurm", "login"]

      - name: "vast_home"
        source: "{{ vast_nfs_ip }}:/home"
        mount_point: "/home"
        mount_params: "vast_nfs"
        functional_group_prefix: ["slurm"]

      - name: "scratch_isolation"
        source: "/mnt/scratch"
        mount_point: "/mounted/scratch"
        node_key: "local_hostname"
        node_mount_point:
          - "/scratch"
          - "/tmp"
        groups: ["grp1"]

powervault_config
------------------

The ``powervault_config`` section defines PowerVault iSCSI volume connection definitions. These configurations are processed via runcmd script because device path is only known after iSCSI login and multipath scan.

**Parameters**

- **name** (string, required): Unique identifier for this PowerVault volume
- **ip** (array, required): List of target controller IP addresses for iSCSI discovery
- **port** (integer, optional): TCP port for iSCSI target. Default: ``3260``
- **iscsi_initiator** (string, required): iSCSI initiator IQN
- **volume_id** (string, required): Volume identifier (hex string / WWN) for multipath device matching
- **mount_point** (string, required): Where the discovered device gets mounted
- **fs_type** (string, optional): Filesystem type. Overrides mount_params profile when specified
- **mnt_opts** (string, optional): Mount options. Overrides mount_params profile when specified
- **dump_freq** (string, optional): Dump frequency. Default: ``0``
- **fsck_pass** (string, optional): Fsck pass number. Default: ``0``
- **mount_params** (string, optional): Named profile for fs_type/mnt_opts
- **node_key** (string, optional): cloud_init variable for per-node bind mounts (e.g., ``local_hostname``, ``ds.meta_data.instance_data.local_ipv4``)
- **node_mount_point** (array, optional): List of bind mount target paths. Required when node_key is set
- **functional_group_prefix** (array, optional): List of functional group prefixes for node targeting. Mutually exclusive with groups
- **groups** (array, optional): List of GROUP_NAME values from pxe_mapping_file.csv. Mutually exclusive with functional_group_prefix
- **permissions** (object, optional): Directory ownership and mode applied to mount_point after mount

**Sample Configuration**

::

    powervault_config:
      - name: powervault1
        ip:
          - 172.1.2.3
        port: 3260
        iscsi_initiator: iqn.2025-01.com.dell:scontrol-node
        volume_id: 00c0ff4343f1f1f1001c8c4e6901000000
        mount_point: "/mnt/slurm"
        mount_params: "powervault_iscsi"
        node_key: "local_hostname"
        node_mount_point:
          - "/var/lib/mysql"
          - "/var/spool/slurm"
        functional_group_prefix: ["slurm_control_node"]
        permissions:
          owner: "slurm"
          group: "slurm"
          mode: "0750"

      - name: powervault2
        ip:
          - 172.1.2.4
        port: 3260
        iscsi_initiator: iqn.2025-01.com.dell:slurmd-node
        volume_id: 00c0ff4343f1f1f1001c8c4e6901000001
        mount_point: "/mnt/slurmd-persist"
        mount_params: "powervault_iscsi"
        groups: ["grp1", "grp2"]

swap
----

The ``swap`` section defines swap file configurations that are created on nodes during provisioning.

**Parameters**

- **filename** (string, required): Path to the swap file to create
- **size** (string, required): Size in bytes, ``auto``, or human-readable format (e.g., ``2G``, ``512M``)
- **maxsize** (string, optional): Maximum size (used with size: auto)
- **functional_group_prefix** (array, optional): List of functional group prefixes to apply this swap to. Mutually exclusive with groups
- **groups** (array, optional): List of GROUP_NAME values from pxe_mapping_file.csv. Mutually exclusive with functional_group_prefix

**Sample Configuration**

::

    swap:
      - name: "compute_swap"
        filename: "/swapfile"
        size: "2G"
        maxsize: "4G"
        functional_group_prefix: ["slurm_node"]

mount_params
------------

The ``mount_params`` section defines named mount parameter profiles. Each profile provides defaults for filesystem type, mount options, dump frequency, and fsck pass number. Custom fields are allowed for backend-specific metadata.

**Parameters**

- **fs_type** (string, required): Default filesystem type
- **mnt_opts** (string, required): Default mount options
- **dump_freq** (string, optional): Default dump frequency
- **fsck_pass** (string, optional): Default fsck pass number

**Sample Configuration**

::

    mount_params:
      # Default NFS mount - standard NFS4.1 with high-performance options
      default:
        fs_type: "nfs"
        mnt_opts: "nfsvers=4.1,hard,intr,noatime,nconnect=16,rsize=1048576,wsize=1048576"
        dump_freq: "0"
        fsck_pass: "0"

      # VAST NFS storage - standard configuration
      vast_nfs:
        fs_type: "nfs"
        mnt_opts: "proto=rdma,hard,intr,noatime,nconnect=16,rsize=1048576,wsize=1048576"
        dump_freq: "0"
        fsck_pass: "0"
        vast_nfs_ip: "192.168.1.100"

      # PowerVault iSCSI storage - block device with XFS
      powervault_iscsi:
        fs_type: "xfs"
        mnt_opts: "defaults,_netdev,noatime,x-systemd.requires=iscsi.service"
        dump_freq: "0"
        fsck_pass: "0"

      # Bind mount defaults
      bind_mounts:
        fs_type: "none"
        mnt_opts: "bind"
        dump_freq: "0"
        fsck_pass: "0"

.. note:: When configuring storage, ensure that all required storage devices and network shares are accessible from the target nodes. For network storage, verify network connectivity and proper firewall configuration.

.. seealso:: :doc:`schedulerinputparams` for information on how storage configuration integrates with cluster setup.
