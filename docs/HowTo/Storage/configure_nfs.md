
# Configure NFS


Set up Network File System (NFS) shared storage for your Omnia cluster. NFS
provides a common filesystem accessible by all compute and login nodes for
home directories, job data, and shared applications.

## Overview


Omnia supports two NFS deployment models:

1. **Internal NFS** (managed by Omnia) -- Omnia configures an NFS server on a
   designated node (typically the Slurm control node or a dedicated storage
   node) and auto-mounts it on all compute and login nodes.

2. **External NFS** -- You provide an existing NFS server (e.g., Dell
   PowerScale, NetApp, or a standalone NFS appliance), and Omnia configures
   the mount on all cluster nodes.

![NFS Configuration Flowchart](../../assets/images/nfs_flowchart_2.0.jpg)

Both models use:

- **NFSv3** protocol (for broad compatibility with HPC workloads).
- **755 permissions** on shared directories.
- `no_root_squash` option for root-level access from compute nodes.


## Prerequisites


- Cluster nodes are provisioned and reachable.
- For **internal NFS**: the designated NFS server node has sufficient local
  disk space for the shared data.
- For **external NFS**: the NFS server is configured and exporting the
  desired path, and the server IP is reachable from all cluster nodes.
- `nfs-utils` package is available in the local repositories.


## Procedure


### Internal NFS (Omnia-Managed)


1. **Configure NFS in omnia_config.yml**:

   ```bash title="Run on: omnia_core container"
   vi /opt/omnia/input/project_default/omnia_config.yml
   ```


   Set the NFS parameters:

   ```yaml title="File: /opt/omnia/input/project_default/omnia_config.yml"
   ---
   enable_omnia_nfs: true
   nfs_node_group: "slurm_control_node"
   omnia_nfs_path: "/home"
   omnia_nfs_opts: "rw,sync,no_root_squash,no_subtree_check"
   ```


2. **Run the omnia.yml playbook** to deploy NFS:

   ```bash title="Run on: omnia_core container"
   cd /omnia
   ansible-playbook omnia.yml --ask-vault-pass
   ```


   The playbook will:

   - Install `nfs-utils` on the NFS server node.
   - Create the shared directory with 755 permissions.
   - Configure `/etc/exports` with `no_root_squash`.
   - Start and enable the `nfs-server` service.
   - Mount the NFS share on all compute and login nodes.
   - Add the mount to `/etc/fstab` for persistence across reboots.


### External NFS


3. **Configure external NFS in omnia_config.yml**:

   ```bash title="Run on: omnia_core container"
   vi /opt/omnia/input/project_default/omnia_config.yml
   ```


   ```yaml title="File: /opt/omnia/input/project_default/omnia_config.yml"
   ---
   enable_omnia_nfs: false
   external_nfs_server: "10.5.1.100"
   external_nfs_path: "/ifs/omnia/home"
   external_nfs_mount_point: "/home"
   external_nfs_opts: "rw,hard,intr,nfsvers=3"
   ```


4. **Run the omnia.yml playbook**:

   ```bash title="Run on: omnia_core container"
   cd /omnia
   ansible-playbook omnia.yml --ask-vault-pass
   ```


5. **(Alternative) Manual NFS mount** on a specific node:

   ```bash title="Run on: compute node"
   dnf install -y nfs-utils
   mkdir -p /home
   mount -t nfs -o rw,hard,intr,nfsvers=3 10.5.1.100:/ifs/omnia/home /home
   ```


   Add to `/etc/fstab` for persistence:

   ```bash title="Run on: compute node"
   echo "10.5.1.100:/ifs/omnia/home /home nfs rw,hard,intr,nfsvers=3 0 0" >> /etc/fstab
   ```



## Verification


1. **Verify the NFS server is exporting** (internal NFS):

   ```bash title="Run on: NFS server node"
   exportfs -v
   ```


   Expected output:

   ```text title="Expected output on: NFS server node"
   /home  <network>(rw,sync,wdelay,no_root_squash,no_subtree_check,...)
   ```


2. **Verify NFS is mounted on compute nodes**:

   ```bash title="Run on: omnia_core container"
   ansible slurm_node -m shell -a "df -h /home"
   ```


3. **Test read/write from a compute node**:

   ```bash title="Run on: compute node"
   echo "NFS test $(date)" > /home/nfs_test.txt
   cat /home/nfs_test.txt
   rm /home/nfs_test.txt
   ```


4. **Verify permissions**:

   ```bash title="Run on: NFS server node"
   ls -ld /home
   # Expected: drwxr-xr-x (755)
   ```


5. **Verify mount persists across reboot**:

   ```bash title="Run on: compute node"
   grep "/home" /etc/fstab
   ```



## Next Steps


- [Configure Mounts](configure_mounts.md) -- Advanced mount configuration via `storage_config.yml`.
- [Configure Powervault](configure_powervault.md) -- Configure block storage for additional
  performance.
- [Configure Vast](configure_vast.md) -- Build the Vast repository and install the Vast client.
- [Setup Slurm](../Slurm/setup_slurm.md) -- Slurm uses NFS for shared job scripts
  and results.
- [Use Apptainer](../AdvancedConfigurations/use_apptainer.md) -- Store SIF images on NFS for
  cluster-wide access.


## Troubleshooting


**Mount fails with "access denied"**
   Verify the NFS export allows the client IP:

   ```bash title="Run on: NFS server node"
   exportfs -v
   cat /etc/exports
   ```


   Ensure the export includes the admin network range:

   ```text title="File: /etc/exports on NFS server node"
   /home 10.5.0.0/24(rw,sync,no_root_squash,no_subtree_check)
   ```


**"mount.nfs: Connection timed out"**
   Check firewall rules on the NFS server:

   ```bash title="Run on: NFS server node"
   firewall-cmd --add-service=nfs --permanent
   firewall-cmd --add-service=mountd --permanent
   firewall-cmd --add-service=rpc-bind --permanent
   firewall-cmd --reload
   ```


**Stale NFS handles after server restart**
   Remount on affected nodes:

   ```bash title="Run on: affected compute node"
   umount -l /home
   mount /home
   ```


**Performance is slow**
   - Use NFSv3 instead of NFSv4 for HPC workloads (NFSv3 has lower latency).
   - Increase the NFS read/write block size:

     ```text title="File: /etc/fstab on compute node"
     10.5.1.100:/ifs/omnia/home /home nfs rw,hard,intr,nfsvers=3,rsize=1048576,wsize=1048576 0 0
     ```
