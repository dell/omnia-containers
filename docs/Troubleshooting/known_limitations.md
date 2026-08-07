# Known Limitations

Review this page before planning your deployment to understand the current limitations and constraints of Omnia 2.2.0.0.

## General Limitations

- Omnia supports only diskless provisioning of servers.
- Dell Technologies provides support only for Dell-developed Omnia components. Third-party software deployed by Omnia is not covered under Dell support.
- Containerized benchmark jobs are not supported on Slurm clusters.
- All iDRACs must be configured with the same username and password.

### InfiniBand Restrictions

As described in the Red Hat documentation for InfiniBand and RDMA networking, NVIDIA ConnectX-4 and newer adapters running RHEL 8 or later use Enhanced IPoIB mode by default. Enhanced IPoIB supports only datagram mode; connected mode is not supported.

### Local Repository GPG Validation

The `local_repo.yml` playbook completes successfully even when an invalid GPG key is provided during repository configuration. GPG key validation is currently not enforced during Pulp remote creation. Although local repositories support GPG keys, this functionality is not yet enabled in Pulp.

For tracking, see: [pulp_rpm issue #4241](https://github.com/pulp/pulp_rpm/issues/4241)

### BuildStreaM Limitations

- BuildStreaM does not support customization of `catalog_rhel.json`.
- BuildStreaM does not support installation of additional packages through the catalog.
- BuildStreaM does not support automatic retry of failed pipeline jobs.

### GPU Software Deployment Limitations

- DCGM and CUDA Toolkit are deployed only on Slurm compute nodes where NVIDIA GPUs are detected during provisioning.
- Nodes provisioned without GPUs will not have DCGM or CUDA configured and cannot be converted into GPU-enabled nodes without reprovisioning.
- DCGM installation depends on successful detection of the CUDA major version from an initialized NVIDIA driver. If driver initialization is incomplete during provisioning, DCGM deployment is deferred and must be completed manually.

## Upgrade and Rollback Limitations

- Omnia supports in-place upgrades only from **2.1.0.0** to **2.2.0.0**. Direct upgrades that skip releases (for example, **2.0.0.0** to **2.2.0.0**) are not supported. Upgrade one version at a time.
- Rollback is intended for recovery from failed or partially completed upgrades. Rolling back a successfully completed upgrade is not recommended and is blocked by default. It can be forced using:

    ```bash title="Run on: omnia_core container"
    ansible-playbook rollback.yml -e force_rollback=true
    ```

    However, consistency across all components cannot be guaranteed.

- New VAST storage mounts added after an upgrade are not retained during rollback.
- Slurm and Kubernetes upgrade or rollback operations reboot all affected nodes simultaneously, resulting in temporary cluster downtime. Schedule these operations during a maintenance window.

### Upgrade Gets Stuck at omnia.sh --upgrade with External NFS

**Applicable to:** Omnia Core upgrade (2.1.0.0 → 2.2.0.0 and later) when using an external NFS share (for example, Dell PowerScale, generic NFS server).

**Issue:**

During the upgrade, Omnia Core performs backup operations (Phase 3) and a container swap (Phase 4) that involve significant I/O to the NFS-mounted shared path. If the NFS server is under-provisioned, misconfigured, or experiences high latency (for example, OIM and NFS server on different subnets crossing a gateway), these operations may take longer than expected or cause the NFS service to become temporarily unresponsive.

**Symptoms:**

- Upgrade appears to hang during Phase 3 (Backup Creation) or Phase 4 (Container Swap).
- The external NFS share becomes temporarily unresponsive to all connected clients.
- These symptoms are related to the NFS environment, not the Omnia upgrade code.

**Recommendations before running upgrade:**

1. **NFS Server Thread Count** -- Ensure the NFS server is configured with a minimum of 64 NFS daemon threads (`nfsd` threads).

    - On a Linux-based NFS server, verify with: `cat /proc/fs/nfsd/threads`
    - Set in `nfs.conf` or `/etc/sysconfig/nfs`: `RPCNFSDCOUNT=64`
    - On Dell PowerScale, ensure the NFS service has adequate worker threads for the expected concurrent I/O load.

2. **Network Connectivity** -- Verify that the OIM host and the NFS server have low-latency, reliable connectivity.

    - If OIM and NFS are on different subnets, ensure the gateway/router between them is not introducing packet loss or high latency.
    - Test with: `ping -c 10 <nfs_server_ip>` — round-trip times should be consistently under 5 ms.

3. **NFS Server Health** -- Confirm the NFS server is not under heavy load from other clients during the upgrade window.

    - Check NFS server-side logs for any export or connectivity errors before starting the upgrade:

        ```bash title="Run on: NFS server"
        dmesg -T | grep -iE 'nfs|rpc|mountd|lockd'
        ```

        If the output contains messages such as `nfsd: too many open connections` or `consider increasing the number of threads`, increase the NFS daemon thread count as described in the **NFS Server Thread Count** recommendation above.

    - Ensure the NFS export is configured with `no_root_squash` (already validated by Omnia) and has sufficient disk space.

4. **Upgrade Window** -- Plan the upgrade during a low-activity window to minimize concurrent NFS load from other clients accessing the same share.

### BuildStream Upgrade Restrictions

When BuildStream is enabled during an upgrade:

- Kubernetes, Slurm, Telemetry, and related components are redeployed as new clusters through the GitLab CI/CD pipeline.
- Existing cluster state, jobs, and custom configurations are not preserved.
- The GitLab pipeline must be triggered manually after the upgrade.
- BuildStream is intended primarily for test-bed environments.

Additionally:

- Disabling BuildStream during upgrade is not supported if it was enabled in Omnia 2.1.0.0.
- Selective execution using `--tags` is not supported for upgrade or rollback operations. The complete playbook must be executed. On reruns, previously completed components are automatically skipped.

### Telemetry and GitLab Rollback Restrictions

- Telemetry data stored in VictoriaMetrics and Kafka is not preserved during rollback. Any telemetry collected after the upgrade is lost when the telemetry stack is reverted.
- GitLab project rollback requires the upgrade commit to be the latest commit in the repository. If additional commits exist after the upgrade, automatic rollback will not restore GitLab content. In such cases, manually revert GitLab repository changes before performing the rollback.

## BMC Discovery Limitations

### OS NIC MAC Address Retrieval on PowerEdge XE8712 Platforms

**Symptom:**

When the system is in a bare-metal state, the host operating system NIC MAC address cannot be retrieved using standard management interfaces, including:

- iDRAC GUI
- OpenManage Enterprise (OME)
- Redfish APIs
- RACADM CLI
- Lifecycle Controller inventory

The iDRAC MAC address remains visible and is reported correctly through iDRAC and OME. NIC devices are detected, but their host MAC address fields remain empty or unavailable.

This behavior is observed in the following configurations:

- PowerEdge XE8712
- Shared LOM (LAN on Motherboard) configurations
- NVIDIA ConnectX-6 and ConnectX-7 network adapters
- Systems in a bare-metal state (no operating system installed)

**Cause:**

In a bare-metal state, the host operating system NIC MAC address is not populated in the standard out-of-band management interfaces.

**Resolution:**

Use one of the following methods to obtain the host NIC MAC address:

- Monitor DHCP or PXE boot traffic
- Check network switch MAC address tables
- Use factory-provided MAC address inventories
- Review PXE boot logs

Capture DHCP discovery traffic by running the following command on the OIM host:

```bash title="Run on: OIM host"
tcpdump -i <interface> -nne port 67 or port 68
```

```text title="Expected output"
DHCPDISCOVER from 3c:ec:ef:12:34:56
```

In this example, `3c:ec:ef:12:34:56` is the host operating system NIC MAC address.

### PXE Mapping File GROUP_NAME and PARENT_SERVICE_TAG Values From OME Discovery

**Symptom:**

Server identification and mapping during PXE boot rely on information retrieved from OME and iDRAC inventory. Depending on the DNS environment, the `DnsName` value may match the intended iDRAC hostname, or may return a reverse DNS name (for example, `pool-<IP-based>`), which may not align with naming conventions required for cluster configuration. This can result in incorrect `GROUP_NAME` and `PARENT_SERVICE_TAG` values in the generated BMC PXE mapping file.

This behaviour is observed in Dell Omnia deployments integrated with OpenManage Enterprise (OME) discovery.

**Cause:**

Differences between iDRAC configuration and OME-reported hostnames can lead to DNS name mismatches, causing incorrect `GROUP_NAME` and `PARENT_SERVICE_TAG` values in the generated PXE mapping file.

**Resolution:**

Explicitly define `GROUP_NAME` and `PARENT_SERVICE_TAG` in the `pxe_mapping_file` to ensure accurate PXE provisioning and cluster setup in Omnia.

### ADMIN_IP and BMC_IP Correlation in Single-Subnet /24 Environments

**Symptom:**

When Omnia generates `pxe_mapping_file.csv` via OME discovery, it derives Admin (PXE) and InfiniBand IP addresses from the BMC (iDRAC) IP using a fixed octet-substitution algorithm. The first two octets are taken from the configured admin/IB subnet, and the last two octets (3rd and 4th) are copied from the BMC IP address:

```text title="Octet-substitution algorithm"
ADMIN_IP = <admin_subnet octet 1>.<admin_subnet octet 2>.<BMC octet 3>.<BMC octet 4>
IB_IP = <ib_subnet octet 1>.<ib_subnet octet 2>.<BMC octet 3>.<BMC octet 4>
```

This correlation works correctly only when the BMC and Admin networks differ in the first two octets (that is, an effective /16 boundary differentiation).

**Example -- Working (networks differ at 2nd octet):**

- BMC: `10.10.43.0/24`
- Admin: `10.20.43.0/24`
- BMC IP `10.10.43.100` -> Admin IP `10.20.43.100`

**Example -- Failing (networks differ only at 3rd octet):**

- BMC: `172.20.43.0/24`
- Admin: `172.20.44.0/24`
- BMC IP `172.20.43.100` -> Admin IP `172.20.43.100` (same as BMC IP -- 3rd octet 43 is copied from BMC instead of using 44 from the admin subnet)

In network environments where the BMC and Admin subnets share the same first two octets and differ only at the 3rd octet (common in /24 deployments), the generated `ADMIN_IP` will be identical to the `BMC_IP`. The same issue applies to IB IP generation.

This behavior is observed in the following configurations:
- Deployments using OME discovery to auto-generate `pxe_mapping_file.csv`.
- Single-subnet /24 environments where the BMC and Admin networks differ only at the 3rd octet.

**Cause:**

This is by-design behavior for the current Omnia 2.2 release. The correlation is designed for /16 subnet environments or multi-subnet topologies where multiple /24 subnets fall within the same /16 range, and differentiation is based on the 3rd and 4th octets. In single-subnet /24 environments where BMC and Admin networks differ only at the 3rd octet, the auto-generated mapping file will produce incorrect Admin and IB IP addresses.

**Resolution:**

Manually edit the generated `pxe_mapping_file.csv` to correct the `ADMIN_IP` and `IB_IP` columns before running `provision.yml`.


## Telemetry Limitations

### Telemetry Service Failover Delay

**Symptom:**

When a Kubernetes worker node hosting telemetry pods (such as Kafka, VictoriaMetrics, VictoriaLogs, or iDRAC/MySQL) fails, the affected telemetry services may take time to failover to available another node. During this period, telemetry data collection or ingestion may be delayed or temporarily unavailable.

**Cause:**

Kubernetes reschedules pods to healthy nodes based on pod disruption budgets, persistent volume availability, and StatefulSet or Deployment readiness. Telemetry workloads that use persistent volumes and StatefulSets require additional time to safely attach storage and complete initialization on the new node.

**Resolution:**

No manual intervention is required. Wait for the telemetry services to recover and fail over automatically. Do not restart pods or nodes during this period, as it may extend recovery time.


### Limited iDRAC Telemetry Metrics for PowerEdge XE8712

**Symptom:**

On PowerEdge XE8712 servers with NVIDIA GB200 accelerators, the iDRAC Telemetry Service provides a limited set of telemetry metrics compared to other supported PowerEdge platforms. As a result, some telemetry data expected by monitoring and observability solutions may not be available.

**Cause:**

This limitation is due to the current iDRAC Telemetry Service implementation on the PowerEdge XE8712 platform.

**Resolution:**

There is currently no workaround available.

An enhancement request has been submitted to enable support for the complete set of iDRAC telemetry metrics on the PowerEdge XE8712 platform:

**GitHub Enhancement Request:** [Enhancement Request: Support Complete iDRAC Telemetry Metrics on PowerEdge XE8712 with NVIDIA GB200](https://github.com/dell/iDRAC-Telemetry-Reference-Tools/issues/190)
