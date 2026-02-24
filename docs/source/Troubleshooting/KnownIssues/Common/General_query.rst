General Issues
================

⦾ **Why are Omnia containers not coming up after rebooting the OIM?**

**Potential Cause**: The Admin NIC on the OIM may have its autoconnect settings disabled (``autoconnect=no``), which stops it from reconnecting automatically after a reboot.

**Resolution**: Ensure that the Admin NIC on the OIM is configured with ``autoconnect=yes`` so it automatically reconnects after reboot. If you changed this configuration, reboot your OIM once to nullify any cache-related or stale configuration issues.

⦾ **Why is IPoIB connected mode not working on nodes having Mellanox InfiniBand?**

**Potential Cause**: As per the RedHat documentation, `Configuring InfiniBand and RDMA networks <https://docs.redhat.com/en/documentation/red_hat_enterprise_linux/10/html/configuring_and_managing_networking/configuring-infiniband-and-rdma-networks>`_, on RHEL 8 and later, Mellanox InfiniBand adapters starting from ConnectX-4 and newer use Enhanced IPoIB mode by default, which supports datagram mode only. Connected mode is not supported on these devices.

**Resolution**: By default, MTU for datagram mode is limited and cannot be increased to 65520. If a higher MTU is required (for example, 65520 for RDMA traffic), ensure that the switch supports Jumbo frames and that all connected devices in the fabric are configured consistently for the desired MTU.

⦾ **Why are cluster nodes getting incorrect hostname (nid) after OIM reboot?**

**Potential Cause**: If OIM is rebooted after clusters are deployed, cloud-init files are no longer retained on the OIM. When compute nodes are PXE booted afterwards, they cannot access the cloud-init configuration on OIM. This results in default hostnames like ``nid00...`` instead of the configured hostnames from the PXE mapping file.

**Resolution**: Run the ``discovery.yml`` playbook again with the same PXE mapping file. This ensures cloud-init files are properly recreated and compute nodes receive their correct configured hostnames from the PXE mapping file.
