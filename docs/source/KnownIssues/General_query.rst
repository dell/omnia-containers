General Issues
================

⦾ **Why are cluster nodes getting incorrect hostname (nid) after OIM reboot?**

**Potential Cause**: If OIM is rebooted after clusters are deployed, cloud-init files are no longer retained on the OIM. When compute nodes are PXE booted afterwards, they cannot access the cloud-init configuration on OIM. This results in default hostnames like ``nid00...`` instead of the configured hostnames from the PXE mapping file.

**Resolution**: Run the ``discovery.yml`` playbook again with the same PXE mapping file. This ensures cloud-init files are properly recreated and compute nodes receive their correct configured hostnames from the PXE mapping file.
