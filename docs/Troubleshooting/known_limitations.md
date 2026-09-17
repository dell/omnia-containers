---
nav:
  parent: Cross-Module Issues
---

# Known Limitations

Review this page before planning your deployment to understand the current
limitations and constraints of Omnia.

## General Limitations

- Omnia supports only diskless provisioning of servers.
- Dell Technologies provides support only for Dell-developed Omnia components. Third-party software deployed by Omnia is not covered under Dell support.
- Containerized benchmark jobs are not supported on Slurm clusters.
- All iDRACs must be configured with the same username and password.

### InfiniBand Restrictions

As described in the Red Hat documentation for InfiniBand and RDMA networking, NVIDIA ConnectX-4 and newer adapters running RHEL 8 or later use Enhanced IPoIB mode by default. Enhanced IPoIB supports only datagram mode; connected mode is not supported.

### Local Repository GPG Validation

The Repository Manager workflow can complete even when an invalid GPG key is
provided in `repo_manager_config.yml`. GPG key validation is currently not
enforced during Pulp remote creation. Although local repositories support GPG
keys, this functionality is not yet enabled in Pulp.

For tracking, see: [pulp_rpm issue #4241](https://github.com/pulp/pulp_rpm/issues/4241)

### Container Image Multi-Registry Distribution

When the same container image path (e.g. `library/mysql`) is synced from
multiple remote registries, Pulp rejects the second and subsequent
distributions with a `base_path` uniqueness error. This is a Pulp
limitation: each image path can have only one distribution, so tags from
different registries cannot be served under the same namespace.

To use multiple tags of the same image, sync all tags from a single
registry rather than from multiple registries. Multiple tags of the same
image from the same registry sync and distribute correctly.

For tracking, see: [pulp_container issue #2495](https://github.com/pulp/pulp_container/issues/2495)

### BuildStreaM Limitations

- BuildStreaM does not support customization of `catalog_rhel.json`.
- BuildStreaM does not support automatic retry of failed pipeline jobs.

### GPU Software Deployment Limitations

- DCGM and CUDA Toolkit are deployed only on Slurm compute nodes where NVIDIA GPUs are detected during provisioning.
- Nodes provisioned without GPUs will not have DCGM or CUDA configured and cannot be converted into GPU-enabled nodes without reprovisioning.
- DCGM installation depends on successful detection of the CUDA major version from an initialized NVIDIA driver. If driver initialization is incomplete during provisioning, DCGM deployment is deferred and must be completed manually.

### OpenCHAMI Deployment May Fail When the SMD Certificate Expires

**Issue:**

During `configure_ochami` execution, the `Get SMD group data` task may fail
with an error similar to:

```text
failed to verify certificate: x509: certificate has expired or is not yet valid
```

The failure occurs when OpenCHAMI components attempt to retrieve group
information from SMD using an expired TLS certificate.

**Example error:**

```text
GetGroups(): error getting groups:
failed to execute HTTP request:
tls: failed to verify certificate: x509: certificate has expired or is not yet valid
```

**Workaround:**

Regenerate the OpenCHAMI access token, update the OpenCHAMI certificates, and
restart the OpenCHAMI services:

```bash title="Run on: OIM host"
export <OIM_HOSTNAME>_ACCESS_TOKEN=$(sudo bash -lc 'gen_access_token')
sudo openchami-certificate-update update <OIM_hostname>.<domain>
sudo systemctl restart openchami.target
```

**Verification:**

After executing these commands, rerun the failed Omnia deployment command. The
`configure_ochami` role should complete successfully without the certificate
validation error.

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

Server identification and mapping during PXE boot rely on information retrieved from OME and iDRAC inventory. Depending on the DNS environment, the `DnsName` value may match the intended iDRAC hostname, or may return a reverse DNS name (for example, `pool-<IP-based>`), which may not align with naming conventions required for cluster configuration. This can result in incorrect generated `GROUP_NAME` or optional `PARENT_SERVICE_TAG` values in the BMC PXE mapping file.

This behaviour is observed in Dell Omnia deployments integrated with OpenManage Enterprise (OME) discovery.

**Cause:**

Differences between iDRAC configuration and OME-reported hostnames can lead to DNS name mismatches and incorrect generated mapping metadata.

**Resolution:**

Review both `GROUP_NAME` and optional `PARENT_SERVICE_TAG` in the generated `pxe_mapping_file`. Correct either value as needed before using the file with Orchestrator. Orchestrator does not require a parent value or validate it against `GROUP_NAME`.

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

The current Discovery mapping generator uses this fixed octet-substitution
behavior. It is suitable only when the intended admin or InfiniBand address
keeps the BMC address's third and fourth octets. In environments where the
networks differ at either of those octets, the generated mapping contains an
incorrect address.

**Resolution:**

Manually edit the generated mapping to correct `ADMIN_IP` and `IB_IP`, copy the
reviewed file to the Orchestrator project input directory, and validate it
before provisioning.


## Telemetry Limitations

### Telemetry Service Failover Delay

**Symptom:**

When a Kubernetes worker node hosting telemetry pods such as Kafka,
VictoriaMetrics, VictoriaLogs, or iDRAC/MySQL fails, the affected services may
take time to recover on another node. During this period, telemetry collection
or ingestion may be delayed or temporarily unavailable.

**Cause:**

Kubernetes reschedules pods to healthy nodes based on persistent-volume
availability and StatefulSet or Deployment readiness. The iDRAC MySQL database
runs as a single replica and uses a ReadWriteOnce PVC. It does not provide
database-level high availability; recovery depends on pod rescheduling, volume
detachment and reattachment, and successful MySQL initialization.

**Resolution:**

No manual intervention is required. Wait for the telemetry services to recover and fail over automatically. Do not restart pods or nodes during this period, as it may extend recovery time.

### Limited iDRAC Telemetry Metrics for PowerEdge XE8712

**Symptom:**

On PowerEdge XE8712 servers with NVIDIA GB200 accelerators, the iDRAC Telemetry Service provides a limited set of telemetry metrics compared to other supported PowerEdge platforms. As a result, some telemetry data expected by monitoring and observability solutions may not be available.

In addition, iDRAC does not support the following metrics:

- **AMD nodes:** Memory metrics are not supported.
- **ARMPowerEddsfvffv and memory metrics are not supported.

**Cause:**

This limitation is due to the current iDRAC Telemetry Service implementation on these platforms.

**Resolution:**

There is currently no workaround available.

An enhancement request has been submitted to enable support for the complete set of iDRAC telemetry metrics on the PowerEdge XE8712 platform:

**GitHub Enhancement Request:** [Enhancement Request: Support Complete iDRAC Telemetry Metrics on PowerEdge XE8712 with NVIDIA GB200](https://github.com/dell/iDRAC-Telemetry-Reference-Tools/issues/190)









