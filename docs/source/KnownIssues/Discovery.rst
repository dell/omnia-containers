Discovery
=========

⦾ **Why does discovery.yml generate incorrect GROUP_NAME and PARENT_SERVICE_TAG values in BMC PXE mapping file?**

**Potential Cause**: In Dell Omnia deployments integrated with OpenManage Enterprise (OME), server identification and mapping during PXE boot rely on information retrieved from OME and iDRAC inventory. Depending on the DNS environment, the DnsName value may match the intended iDRAC hostname, or may return a reverse DNS name (For example, pool‑<IP‑based>), which may not align with naming conventions required for cluster configuration.

**Resolution**: Due to differences between iDRAC configuration and OME‑reported hostnames, users must explicitly define GROUP_NAME and PARENT_SERVICE_TAG in the pxe_mapping_file to ensure accurate PXE provisioning and cluster setup in Omnia.

⦾ **Why does the generated pxe_mapping_file.csv have the same ADMIN_IP and BMC_IP?**

**Potential Cause**: When Omnia generates the pxe_mapping_file.csv via OME discovery, it derives Admin (PXE) and InfiniBand IP addresses from the BMC (iDRAC) IP using a fixed octet-substitution algorithm. The first two octets are taken from the configured admin/IB subnet, and the last two octets (3rd and 4th) are copied from the BMC IP address:

ADMIN_IP = <admin_subnet octet 1>.<admin_subnet octet 2>.<BMC octet 3>.<BMC octet 4>
IB_IP = <ib_subnet octet 1>.<ib_subnet octet 2>.<BMC octet 3>.<BMC octet 4>

This correlation works correctly only when the BMC and Admin networks differ in the first two octets (i.e., effective /16 boundary differentiation).

**Example — Working (networks differ at 2nd octet):**

- BMC: 10.10.43.0/24
- Admin: 10.20.43.0/24
- BMC IP 10.10.43.100 → Admin IP 10.20.43.100 ✅

**Example — Failing (networks differ only at 3rd octet):**

- BMC: 172.20.43.0/24
- Admin: 172.20.44.0/24
- BMC IP 172.20.43.100 → Admin IP 172.20.43.100 ❌ (same as BMC IP — 3rd octet 43 is copied from BMC instead of using 44 from admin subnet)

**Impact**: In network environments where the BMC and Admin subnets share the same first two octets and differ only at the 3rd octet (common in /24 deployments), the generated ADMIN_IP will be identical to the BMC_IP. The same issue applies to IB IP generation.

**Scope**: This is by-design behavior for the current Omnia 2.2 release. The correlation is designed for /16 subnet environments or multi-subnet topologies where multiple /24 subnets fall within the same /16 range, and differentiation is based on the 3rd and 4th octets. In single-subnet /24 environments where BMC and Admin networks differ only at the 3rd octet, the auto-generated mapping file will produce incorrect Admin and IB IP addresses.

**Resolution**: Manually edit the generated pxe_mapping_file.csv to correct the ADMIN_IP and IB_IP columns before running provision.yml.

