
# Configure PowerVault


Integrate Dell PowerVault ME5 iSCSI storage with your Omnia cluster for
block-level storage on the Slurm controller, providing high-performance
local storage with multipath redundancy.

## Overview


Dell PowerVault ME5 provides iSCSI block storage that can be mapped to Slurm
controller or compute nodes as local disks. This is useful for:

- Slurm spool and state directories requiring high I/O throughput.
- MariaDB (Slurm accounting database) storage.
- Scratch storage for compute nodes.

Omnia configures:

- iSCSI initiator on the target node(s).
- Multipath I/O (DM-Multipath) for path redundancy.
- Automatic LUN discovery and attachment.


## Prerequisites


- A Dell PowerVault ME5 storage array is configured and accessible on the
  admin or storage network.
- iSCSI target ports on the PowerVault are configured with IP addresses.
- A volume (LUN) is created on the PowerVault and mapped to the target host.
- Network connectivity between the Slurm controller and the PowerVault iSCSI
  ports.
- The PowerVault management IP is accessible for initial configuration.


## Procedure


1. **Install iSCSI and multipath packages** on the Slurm controller:

   ```bash title="Run on: Slurm control node"
   dnf install -y iscsi-initiator-utils device-mapper-multipath
   ```


2. **Configure the iSCSI initiator name**:

   ```bash title="Run on: Slurm control node"
   cat /etc/iscsi/initiatorname.iscsi
   ```


   If the initiator name is not set, generate one:

   ```bash title="Run on: Slurm control node"
   echo "InitiatorName=$(iscsi-iname)" > /etc/iscsi/initiatorname.iscsi
   ```


3. **Configure DM-Multipath**:

   ```bash title="Run on: Slurm control node"
   cat <<'EOF' > /etc/multipath.conf
   defaults {
       polling_interval 10
       path_grouping_policy multibus
       find_multipaths yes
       no_path_retry 5
       user_friendly_names yes
   }

   devices {
       device {
           vendor "DellEMC"
           product "ME5"
           path_grouping_policy group_by_prio
           path_checker tur
           failback immediate
           no_path_retry queue
       }
   }
   EOF

   systemctl enable --now multipathd
   ```


4. **Discover iSCSI targets** on the PowerVault:

   ```bash title="Run on: Slurm control node"
   iscsiadm -m discovery -t sendtargets -p 10.5.2.100:3260
   iscsiadm -m discovery -t sendtargets -p 10.5.2.101:3260
   ```


   Replace `10.5.2.100` and `10.5.2.101` with your PowerVault iSCSI
   portal IPs.

5. **Log in to the iSCSI targets**:

   ```bash title="Run on: Slurm control node"
   iscsiadm -m node --login
   ```


6. **Start and enable the iSCSI service**:

   ```bash title="Run on: Slurm control node"
   systemctl enable --now iscsid
   systemctl enable --now iscsi
   ```


7. **Verify multipath devices**:

   ```bash title="Run on: Slurm control node"
   multipath -ll
   ```


   Expected output shows multipath devices with multiple paths:

   ```text title="Expected output on: Slurm control node"
   mpath0 (360000000000000001) dm-0 DellEMC,ME5
   size=500G features='1 queue_if_no_path' hwhandler='0' wp=rw
   |-+- policy='round-robin 0' prio=1 status=active
   | `- 3:0:0:0 sda 8:0  active ready running
   `-+- policy='round-robin 0' prio=1 status=enabled
     `- 4:0:0:0 sdb 8:16 active ready running
   ```


8. **Create a filesystem and mount the LUN**:

   ```bash title="Run on: Slurm control node"
   mkfs.xfs /dev/mapper/mpath0
   mkdir -p /var/spool/slurm
   mount /dev/mapper/mpath0 /var/spool/slurm
   ```


   Add to `/etc/fstab` for persistence:

   ```bash title="Run on: Slurm control node"
   echo "/dev/mapper/mpath0 /var/spool/slurm xfs defaults,_netdev 0 0" >> /etc/fstab
   ```



## Verification


1. **Verify iSCSI sessions**:

   ```bash title="Run on: Slurm control node"
   iscsiadm -m session
   ```


2. **Verify multipath status**:

   ```bash title="Run on: Slurm control node"
   multipath -ll
   ```


   All paths should show `active ready running`.

3. **Verify the mount**:

   ```bash title="Run on: Slurm control node"
   df -h /var/spool/slurm
   ```


4. **Test I/O performance**:

   ```bash title="Run on: Slurm control node"
   dd if=/dev/zero of=/var/spool/slurm/test bs=1M count=1024 oflag=direct
   rm /var/spool/slurm/test
   ```



## Next Steps


- [Configure Mounts](configure_mounts.md) -- Advanced mount configuration via `storage_config.yml`.
- [Configure Nfs](configure_nfs.md) -- Configure NFS for shared storage across compute
  nodes.
- [Setup Slurm](../Slurm/setup_slurm.md) -- Deploy Slurm using the PowerVault
  storage for spool data.


## Troubleshooting


**iSCSI discovery returns no targets**
   Verify network connectivity to the PowerVault iSCSI ports:

   ```bash title="Run on: Slurm control node"
   ping -c 3 10.5.2.100
   telnet 10.5.2.100 3260
   ```


**Multipath shows no paths**
   Check that iSCSI sessions are active:

   ```bash title="Run on: Slurm control node"
   iscsiadm -m session
   multipath -v3
   ```


**Path shows "failed faulty"**
   Check network connectivity on the failed path:

   ```bash title="Run on: Slurm control node"
   iscsiadm -m session -P 3 | grep -E "Target|iface|State"
   ```


**LUN not visible after login**
   Rescan SCSI buses:

   ```bash title="Run on: Slurm control node"
   iscsiadm -m session --rescan
   multipath -r
   ```


**Performance is below expectations**
   - Verify jumbo frames are enabled on the iSCSI network:

     ```bash title="Run on: Slurm control node"
     ip link show | grep mtu
     ```


   - Ensure multipath load balancing is active (multiple paths `running`).
