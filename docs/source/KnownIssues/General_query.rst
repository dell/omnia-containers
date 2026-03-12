General Issues
================

⦾ **Why are Omnia containers not coming up after rebooting the OIM?**

**Potential Cause**: The Admin NIC on the OIM may have its autoconnect settings disabled (``autoconnect=no``), which stops it from reconnecting automatically after a reboot.

**Resolution**: Ensure that the Admin NIC on the OIM is configured with ``autoconnect=yes`` so it automatically reconnects after reboot. If you changed this configuration, reboot your OIM once to nullify any cache-related or stale configuration issues.

⦾ **Why are cluster nodes getting incorrect hostname (nid) after OIM reboot?**

**Potential Cause**: If OIM is rebooted after clusters are deployed, cloud-init files are no longer retained on the OIM. When compute nodes are PXE booted afterwards, they cannot access the cloud-init configuration on OIM. This results in default hostnames like ``nid00...`` instead of the configured hostnames from the PXE mapping file.

**Resolution**: Run the ``discovery.yml`` playbook again with the same PXE mapping file. This ensures cloud-init files are properly recreated and compute nodes receive their correct configured hostnames from the PXE mapping file.
