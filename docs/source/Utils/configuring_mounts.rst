.. _configuring-mounts:

Configuring Mounts
==================

The storage configuration in Omnia allows you to configure various storage mounts, PowerVault iSCSI volumes, and swap space for cluster nodes. This configuration is defined in the ``/opt/omnia/input/project_default/storage_config.yml`` file.

.. csv-table:: storage_config.yml parameters
   :file: ../Tables/config_mounts.csv
   :header-rows: 1
   :keepspace:


.. note::
   The storage configuration is applied during node provisioning and can be customized for different node groups using functional group prefixes or group names.



Overview
--------

The ``storage_config.yml`` file contains the following main sections:

* **mounts** - Array of mount configurations for network and local storage
* **mount_params** - Named profiles for filesystem types and mount options
* **powervault_config** - PowerVault iSCSI volume connection definitions
* **swap** - Swap file configurations

mounts
------

The ``mounts`` section defines cloud-init compatible mount configurations. Each mount entry specifies a source device or network path, mount point, and optional filesystem parameters.

.. note::
     Cloud-init mounts require the source to be available at boot time.
     Runtime-discovered devices (iSCSI, multipath) must be configured using powervault_config.
     When node_key is set, bind mount behavior is automatically enforced.
     functional_group_prefix and groups are mutually exclusive.

The following parameters are supported for each mount:

* **name** (required) - Unique identifier for this mount entry
* **source** (required) - Device name or network path (e.g., 192.168.1.100:/export/share, /dev/sdc, UUID=xxx)
* **mount_point** (required) - Mount point path
* **fs_type** - Filesystem type (overrides mount_params profile when specified)
* **mnt_opts** - Mount options (overrides mount_params profile when specified)
* **dump_freq** - Dump frequency (overrides mount_params profile when specified)
* **fsck_pass** - Fsck pass number (overrides mount_params profile when specified)
* **mount_params** - Name of the mount_params profile to use for unspecified fields
* **mount_on_oim** - Whether to mount this filesystem on the OIM node (default: false)
* **node_key** - cloud-init datasource variable accessible via 'cloud-init query <var_name>' (e.g., local_hostname, ds.meta_data.instance_data.local_ipv4, instance_id). The variable chosen must be unique per host to ensure isolation between nodes. 
* **node_mount_point** - List of bind mount target paths (required when node_key is set)
* **functional_group_prefix** - List of oChaMI functional group prefixes to apply this mount to (mutually exclusive with groups)
* **groups** - List of GROUP_NAME values from pxe_mapping_file.csv (mutually exclusive with functional_group_prefix)
* **permissions** - Directory ownership and mode applied to mount_point after mount
  * **owner** - User owner of the mount point (default: root)
  * **group** - Group owner of the mount point (default: root)
  * **mode** - Octal permission mode (e.g., 0755, 1777, default: 0755)

.. note::
When node_key is specified, fs_type is forced to ``none`` and mnt_opts is forced to ``bind`` regardless of user input.

Example mounts configuration::

    mounts:
      # NFS mount for Slurm
      - name: "nfs_slurm"
        source: "172.16.0.254:/mnt/share/omnia"
        mount_point: "/opt/omnia/slurm_mount"
        fs_type: "nfs"
        mnt_opts: "nosuid,rw,sync,hard,intr"
        mount_on_oim: true
        functional_group_prefix: ["slurm", "login"]

      # NFS mount for Kubernetes
      - name: "nfs_k8s"
        source: "172.16.0.254:/mnt/share/omnia_k8s"
        mount_point: "/opt/omnia/k8s_mount"
        fs_type: "nfs"
        mnt_opts: "nosuid,rw,sync,hard,intr"
        mount_on_oim: true
        functional_group_prefix: ["service_kube"]

      # VAST NFS home directories using mount_params profile
      - name: "vast_home"
        source: "172.16.0.201:/home"
        mount_point: "/home"
        mount_params: "vast_nfs"
        functional_group_prefix: ["slurm"]

      # Per-node bind mount from shared scratch
      - name: "scratch_isolation"
        source: "172.16.0.201:/mnt/scratch"
        mount_point: "/mounted/scratch"
		fs_type: nfs
        node_key: "local_hostname"
        node_mount_point:
          - "/scratch"
          - "/tmp"
        groups: ["grp1"]

mount_params
------------

The ``mount_params`` section defines named profiles that provide default values for filesystem type, mount options, dump frequency, and fsck pass number. These profiles can be referenced in the ``mounts`` and ``powervault_config`` sections to avoid repetitive configuration.

The following parameters are supported in each mount_params profile:

* **fs_type** - Filesystem type (e.g., nfs, xfs, ext4, none)
* **mnt_opts** - Mount options (comma-separated)
* **dump_freq** - Dump frequency (usually 0)
* **fsck_pass** - Fsck pass number (usually 0 or 2)

Example mount_params configuration::

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

      # PowerVault iSCSI storage - block device with XFS
      powervault_iscsi:
        fs_type: "xfs"
        mnt_opts: "defaults,_netdev,noatime,x-systemd.requires=iscsi.service"
        dump_freq: "0"
        fsck_pass: "0"


powervault_config
-----------------

The ``powervault_config`` section defines PowerVault iSCSI volume connection definitions.

.. warning::
   PowerVault configuration requires proper iSCSI initiator setup and network connectivity to the PowerVault controllers.

The following parameters are supported for each PowerVault configuration:

* **name** (required) - Unique identifier for this PowerVault volume
* **ip** (required) - List of target controller IP addresses for iSCSI discovery
* **port** - TCP port for iSCSI target (default: 3260)
* **iscsi_initiator** (required) - iSCSI initiator IQN
* **volume_id** (required) - Volume identifier (hex string / WWN) for multipath device matching
* **mount_point** (required) - Where the discovered device gets mounted
* **fs_type** - Filesystem type (overrides mount_params profile when specified)
* **mnt_opts** - Mount options (overrides mount_params profile when specified)
* **dump_freq** - Dump frequency (overrides mount_params profile when specified)
* **fsck_pass** - Fsck pass number (overrides mount_params profile when specified)
* **mount_params** - Named profile for fs_type/mnt_opts (read by the runcmd script)
* **node_key** - cloud-init datasource variable accessible via 'cloud-init query <var_name>' (e.g., local_hostname, ds.meta_data.instance_data.local_ipv4, instance_id). The variable chosen must be unique per host to ensure isolation between nodes
* **node_mount_point** - List of bind mount target paths (required when node_key is set)
* **functional_group_prefix** - List of functional group prefixes for node targeting
* **permissions** - Directory ownership and mode applied to mount_point after mount
  * **owner** - User owner of the mount point (default: root)
  * **group** - Group owner of the mount point (default: root)
  * **mode** - Octal permission mode (e.g., 0750, default: 0755)

.. note::
When node_key is specified, fs_type is forced to ``none`` and mnt_opts is forced to ``bind`` regardless of user input.

Example powervault_config configuration::

    powervault_config:
      # PowerVault for slurm control node
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

      # PowerVault for kube nodes
      - name: powervault2
        ip:
          - 172.1.2.4
        port: 3260
        iscsi_initiator: iqn.2025-01.com.dell:slurmd-node
        volume_id: 00c0ff4343f1f1f1001c8c4e6901000001
        mount_point: "/mnt/slurmd-persist"
        mount_params: "powervault_iscsi"
        functional_group_prefix: ["service_kube_node"]

swap
----

The ``swap`` section defines swap file configurations for cluster nodes. Swap files are created and enabled during node provisioning.

The following parameters are supported for each swap configuration:

* **filename** (required) - Path to the swap file to create
* **size** (required) - Size in bytes, 'auto', or human-readable format (e.g., 2G, 512M)
* **maxsize** - Maximum size (used with size: auto)
* **functional_group_prefix** - List of oChaMI functional group prefixes to apply this swap to 

Example swap configuration::

    swap:
      - name: "compute_swap"
        filename: "/swapfile"
        size: "2G"
        maxsize: "4G"
        functional_group_prefix: ["slurm_node"]

Complete Example
----------------

The following is a complete example of a ``storage_config.yml`` file::

    ---
    # Mount parameter profiles
    mount_params:
      default:
        fs_type: "nfs"
        mnt_opts: "nfsvers=4.1,hard,intr,noatime,nconnect=16,rsize=1048576,wsize=1048576"
        dump_freq: "0"
        fsck_pass: "0"

      vast_nfs:
        fs_type: "nfs"
        mnt_opts: "proto=rdma,hard,intr,noatime,nconnect=16,rsize=1048576,wsize=1048576"
        dump_freq: "0"
        fsck_pass: "0"
        vast_nfs_ip: "192.168.1.100"

      powervault_iscsi:
        fs_type: "xfs"
        mnt_opts: "defaults,_netdev,noatime,x-systemd.requires=iscsi.service"
        dump_freq: "0"
        fsck_pass: "0"

    # Mount configurations
    mounts:
      - name: "nfs_slurm"
        source: "172.16.0.254:/mnt/share/omnia"
        mount_point: "/opt/omnia/slurm_mount"
        fs_type: "nfs"
        mnt_opts: "nosuid,rw,sync,hard,intr"
        mount_on_oim: true
        functional_group_prefix: ["slurm", "login"]

      - name: "vast_home"
        source: "172.16.0.202:/home"
        mount_point: "/home"
        mount_params: "vast_nfs"
        functional_group_prefix: ["slurm"]

    # PowerVault configurations
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

    # Swap configurations
    swap:
      - name: "compute_swap"
        filename: "/swapfile"
        size: "2G"
        maxsize: "4G"
        functional_group_prefix: ["slurm_node"]

.. note::
   After updating the ``storage_config.yml`` file, re-run the appropriate provisioning playbooks to apply the storage configuration to the nodes.