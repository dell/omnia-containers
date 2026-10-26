# Migrate IPoIB from IPv4-only to Dual-Stack

This guide covers migrating an existing Omnia cluster from IPv4-only
InfiniBand configuration to dual-stack (IPv4 + IPv6 on the IB interface).

For a new deployment that starts with dual-stack or IPv6-only, follow
[Configure InfiniBand](configure_infiniband.md) instead.

---

## Overview

Omnia supports backward-compatible migration. Existing IPv4-only input files
continue to work without modification. To add IPv6, update your input files
and re-provision the affected nodes. No Omnia software upgrade is required —
the same orchestrator binary handles both address families.

Migration can be done incrementally: add `IB_IPV6` addresses to individual
rows and re-provision only those nodes. Nodes without an `IB_IPV6` value
remain IPv4-only.

---

## Step 1: Update `network_spec.yml`

Add `ipv6_subnet`, `ipv6_netmask_bits`, and `ib_addr_mode` to the
`ib_network` section. The existing `subnet` / `netmask_bits` fields (or the
canonical `ipv4_subnet` / `ipv4_netmask_bits`) are unchanged.

**Before (IPv4-only):**

```yaml
Networks:
  - ib_network:
      subnet: "192.168.0.0"
      netmask_bits: "24"
      dns: []
```

**After (dual-stack):**

```yaml
Networks:
  - ib_network:
      ipv4_subnet: "192.168.0.0"
      ipv4_netmask_bits: "24"
      ipv6_subnet: "fd00:1b::"
      ipv6_netmask_bits: "64"
      ib_addr_mode: "dual-stack"
      slurm_preferred_addr_family: "ipv6"
      dns: []
```

!!! note
    Renaming `subnet` to `ipv4_subnet` is optional. Both field names are
    accepted and normalized automatically. You can add `ipv6_subnet` and
    `ipv6_netmask_bits` alongside the legacy field names.

`slurm_preferred_addr_family` is required in dual-stack mode. Set it to
`ipv4` or `ipv6` depending on which address family Slurm should use for
inter-daemon communication (NodeAddr). In most dual-stack deployments, set
it to `ipv6`.

---

## Step 2: Update `pxe_mapping_file.csv`

Add the `IB_IPV6` column to each row that needs IPv6. The canonical
12-column format replaces the legacy `IB_IP` column with `IB_IPV4` and
`IB_IPV6`.

**Before (11-column legacy format):**

```csv
FUNCTIONAL_GROUP_NAME,GROUP_NAME,SERVICE_TAG,PARENT_SERVICE_TAG,HOSTNAME,ADMIN_MAC,ADMIN_IP,BMC_MAC,BMC_IP,IB_NIC_NAME,IB_IP
slurm_node_rhel_10_0_aarch64,grp1,ABCD34,,node001,02:00:00:00:01:02,172.16.107.43,02:00:00:00:02:02,172.17.107.43,InfiniBand.Slot.7-1,192.168.0.101
```

**After (12-column with IPv6):**

```csv
FUNCTIONAL_GROUP_NAME,GROUP_NAME,SERVICE_TAG,PARENT_SERVICE_TAG,HOSTNAME,ADMIN_MAC,ADMIN_IP,BMC_MAC,BMC_IP,IB_NIC_NAME,IB_IPV4,IB_IPV6
slurm_node_rhel_10_0_aarch64,grp1,ABCD34,,node001,02:00:00:00:01:02,172.16.107.43,02:00:00:00:02:02,172.17.107.43,InfiniBand.Slot.7-1,192.168.0.101,fd00:1b::101
```

**To convert the header in-place on the OIM:**

```bash title="Run on: OIM"
cd "$OMNIA_DATA_PATH/orchestrator/input/$OMNIA_PROJECT_NAME"

# Rename IB_IP to IB_IPV4 and add IB_IPV6 column header
sed -i '1s/,IB_IP$/,IB_IPV4,IB_IPV6/' pxe_mapping_file.csv

# Append empty IB_IPV6 cell to each data row (IPv4-only until you add addresses)
sed -i '2,$s/$/,/' pxe_mapping_file.csv
```

Then edit each row to add the IPv6 address in the `IB_IPV6` column.
Nodes you do not edit remain IPv4-only.

!!! note "Legacy format is automatically accepted"
    If you prefer not to rename the header, leave the file as-is. The
    validator normalizes `IB_IP` to `IB_IPV4` automatically. You can add the
    `IB_IPV6` column alongside `IB_IP` if you prefer a gradual transition.

---

## Step 3: Validate the updated input files

```bash title="Run on: OIM"
cd <OMNIA_SOURCE_PATH>/src/main
./omnia.sh --run orchestrator --tags validate
```

Alternatively using ansible-playbook:

```bash title="Run on: OIM"
source /opt/omnia/activate-omnia.sh
cd <OMNIA_SOURCE_PATH>/src/orchestrator/playbooks
ansible-playbook orchestrator.yml --tags validate
```

Fix any reported errors before proceeding. Common issues:

- `IB_IPV6` value is not a valid IPv6 address — check for typos.
- Duplicate `IB_IPV6` values — each node must have a unique address.
- `IB_IPV6` does not belong to the configured `ipv6_subnet` — verify prefix
  consistency between `network_spec.yml` and the CSV.
- `slurm_preferred_addr_family` is missing — required when `ib_addr_mode` is
  `dual-stack`.

---

## Step 4: Re-provision the affected nodes

```bash title="Run on: OIM"
cd <OMNIA_SOURCE_PATH>/src/main
./omnia.sh --run orchestrator --tags provision
```

Or using ansible-playbook:

```bash title="Run on: OIM"
source /opt/omnia/activate-omnia.sh
cd <OMNIA_SOURCE_PATH>/src/orchestrator/playbooks
ansible-playbook orchestrator.yml --tags provision
```

Cloud-init configures both IPv4 and IPv6 on the IB interface during the next
node boot. Provisioning is idempotent — re-running it on nodes that already
have the correct configuration is safe.

!!! note
    Nodes must reboot (via re-provisioning and PXE boot) for the IPv6
    address to take effect. The existing IPv4 address and active connections
    are not disrupted by the configuration update itself.

---

## Verification

After the nodes have booted, verify the dual-stack configuration:

```bash title="Run on: compute node"
# Discover the IB interface name (predictable kernel name, not ib0)
IB_IFACE=$(ls /sys/class/net/ | grep '^ib' | head -1)
echo "IB interface: $IB_IFACE"

# Verify both addresses are assigned
ip addr show "$IB_IFACE"

# Expected output for dual-stack:
#   inet  192.168.0.101/24 scope global ibp161s0
#   inet6 fd00:1b::101/64 scope global

# Test IPv6 connectivity to another node
ping6 -c 5 fd00:1b::102
```

---

## Rollback

To remove IPv6 and return to IPv4-only:

1. Remove `ipv6_subnet`, `ipv6_netmask_bits`, and `ib_addr_mode` from
   `network_spec.yml` (or set `ib_addr_mode: "ipv4-only"`).
2. Clear the `IB_IPV6` column in `pxe_mapping_file.csv`, or revert to the
   11-column format.
3. Re-provision the affected nodes.

---

## FAQ

**Q: Do I need to stop workloads during the migration?**

A: No. IPv6 address assignment is additive for dual-stack. The existing IPv4
address and active connections are not disrupted. However, nodes must reboot
(via re-provisioning) for the IPv6 address to take effect.

**Q: Can I migrate nodes incrementally?**

A: Yes. Add `IB_IPV6` addresses only to the rows you want to migrate. Nodes
without an `IB_IPV6` value remain IPv4-only. Re-provision only the nodes that
need IPv6.

**Q: What if I use the legacy `subnet` / `netmask_bits` field names in network_spec.yml?**

A: They continue to work. You can add `ipv6_subnet`, `ipv6_netmask_bits`, and
`ib_addr_mode` alongside them without renaming the existing fields.

**Q: What if SMD or BSS publication fails for some nodes?**

A: Those nodes enter `RECOVERY_REQUIRED` state. Re-run provisioning — the
pipeline is idempotent and will complete the remaining publications without
duplicating what was already applied. Check
`$OMNIA_DATA_PATH/orchestrator/output/$OMNIA_PROJECT_NAME/orchestrator_status.yml`
for the `failure_stage` and `recommended_action`.

---

## Related documentation

- [Configure InfiniBand](configure_infiniband.md) -- Full procedure for new
  deployments, including all three addressing modes.
- [network_spec.yml reference](../../Reference/Configuration/network_spec.md)
- [PXE mapping file reference](../../Reference/SampleFiles/pxe_mapping_file.md)
