Discovery
=========

⦾ **Why does discovery.yml generate incorrect GROUP_NAME and PARENT_SERVICE_TAG values in BMC PXE mapping file?**

**Potential Cause**: In Dell Omnia deployments integrated with OpenManage Enterprise (OME), server identification and mapping during PXE boot rely on information retrieved from OME and iDRAC inventory. Depending on the DNS environment, the DnsName value may match the intended iDRAC hostname, or may return a reverse DNS name (For example, pool‑<IP‑based>), which may not align with naming conventions required for cluster configuration.

**Resolution**: Due to differences between iDRAC configuration and OME‑reported hostnames, users must explicitly define GROUP_NAME and PARENT_SERVICE_TAG in the pxe_mapping_file to ensure accurate PXE provisioning and cluster setup in Omnia.

