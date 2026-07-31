# Known Limitations

Review this page before planning your deployment to understand the current limitations and constraints of Omnia 2.2.0.0.

## General Limitations

- Omnia supports only diskless provisioning of servers.
- Dell Technologies provides support only for Dell-developed Omnia components. Third-party software deployed by Omnia is not covered under Dell support.
- Containerized benchmark jobs are not supported on Slurm clusters.
- All iDRACs must be configured with the same username and password.

### InfiniBand Restrictions

As described in the Red Hat documentation for InfiniBand and RDMA networking, Mellanox ConnectX-4 and newer adapters running RHEL 8 or later use Enhanced IPoIB mode by default. Enhanced IPoIB supports only datagram mode; connected mode is not supported.

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

### OS NIC MAC Address Retrieval on Belton Platforms

**Affected configurations:**

- Dell Belton platforms
- Shared LOM (LAN on Motherboard) configurations
- Mellanox ConnectX-6 and ConnectX-7 network adapters
- Systems in a bare-metal state (no operating system installed)

**Issue:**

When the system is in a bare-metal state, the host operating system NIC MAC address cannot be retrieved using standard management interfaces, including:

- iDRAC GUI
- OpenManage Enterprise (OME)
- Redfish APIs
- RACADM CLI
- Lifecycle Controller inventory

!!! note

    The iDRAC MAC address remains visible and is reported correctly through iDRAC and OME. NIC devices are detected, but their host MAC address fields remain empty or unavailable.

**Workarounds:**

To obtain the host NIC MAC address, use one of the following methods:

- Monitor DHCP or PXE boot traffic
- Check network switch MAC address tables
- Use factory-provided MAC address inventories
- Review PXE boot logs

Capture DHCP discovery traffic to identify the host NIC MAC address:

```bash title="Run on: OIM host"
tcpdump -i <interface> -nne port 67 or port 68
```

```text title="Expected output"
DHCPDISCOVER from 3c:ec:ef:12:34:56
```

In this example, `3c:ec:ef:12:34:56` is the host operating system NIC MAC address.

### PXE Mapping File GROUP_NAME and PARENT_SERVICE_TAG Values From OME Discovery

**Affected configurations:**

- Dell Omnia deployments integrated with OpenManage Enterprise (OME) discovery.

**Issue:**

Server identification and mapping during PXE boot rely on information retrieved from OME and iDRAC inventory. Depending on the DNS environment, the `DnsName` value may match the intended iDRAC hostname, or may return a reverse DNS name (for example, `pool-<IP-based>`), which may not align with naming conventions required for cluster configuration. This can result in incorrect `GROUP_NAME` and `PARENT_SERVICE_TAG` values in the generated BMC PXE mapping file.

!!! note

    Due to differences between iDRAC configuration and OME-reported hostnames, you must explicitly define `GROUP_NAME` and `PARENT_SERVICE_TAG` in the `pxe_mapping_file` to ensure accurate PXE provisioning and cluster setup in Omnia.

### ADMIN_IP and BMC_IP Correlation in Single-Subnet /24 Environments

**Affected configurations:**

- Deployments using OME discovery to auto-generate `pxe_mapping_file.csv`.
- Single-subnet /24 environments where the BMC and Admin networks differ only at the 3rd octet.

**Issue:**

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

!!! note

    This is by-design behavior for the current Omnia 2.2 release. The correlation is designed for /16 subnet environments or multi-subnet topologies where multiple /24 subnets fall within the same /16 range, and differentiation is based on the 3rd and 4th octets. In single-subnet /24 environments where BMC and Admin networks differ only at the 3rd octet, the auto-generated mapping file will produce incorrect Admin and IB IP addresses.

**Workaround:**

Manually edit the generated `pxe_mapping_file.csv` to correct the `ADMIN_IP` and `IB_IP` columns before running `provision.yml`.


## Telemetry Limitations

### Telemetry Service Failover Delay

When a Kubernetes worker node fails, affected telemetry services may take time to fail over to available worker nodes.

**Resolution:** No manual intervention is required. Wait for the telemetry services to recover and fail over automatically. Do not restart pods or nodes during this period, as it may extend recovery time.

### Telemetry Pods Enter CrashLoopBackOff After Worker Node Reboot

**Description:** In Omnia deployments that use PowerScale as NFS-backed persistent storage, telemetry pods (Kafka and iDRAC/MySQL) may enter a CrashLoopBackOff state following an abrupt worker node reboot or network interruption.

**Cause:** During normal operation, Kafka and MySQL write lock files (`.lock`, `.pid`, `.sock`) to their persistent volumes to prevent concurrent access. When a pod terminates unexpectedly, these lock files are not released. Because PowerScale operates as an external, highly available NFSv3 server, it retains the lock state across client failures. When the pod restarts, it cannot acquire the existing locks and fails to initialize, resulting in a crash loop.

**Resolution:** Use the following scripts to automate lock cleanup and data corruption recovery. These scripts check for the type of failure and apply the appropriate resolution automatically.

!!! note "Usage instructions"

    Save each script to a file with the corresponding name (for example, `kafka_lock_cleanup.sh`, `idrac_lock_cleanup.sh`, `idrac_data_corruption_recovery.sh`).

    Make the scripts executable:

    ```bash title="Run on: omnia_core container or K8s control plane"
    chmod +x kafka_lock_cleanup.sh idrac_lock_cleanup.sh idrac_data_corruption_recovery.sh
    ```

    Run the scripts in the following order. If both Kafka and iDRAC scripts need to be executed, run the Kafka script first and wait for 1 minute before executing the iDRAC script.

    - For Kafka lock issues: `./kafka_lock_cleanup.sh`
    - For iDRAC lock issues: `./idrac_lock_cleanup.sh`
    - For iDRAC data corruption: `./idrac_data_corruption_recovery.sh`

#### Kafka Lock Cleanup Script

Save the following as `kafka_lock_cleanup.sh`:

```bash title="kafka_lock_cleanup.sh"
#!/bin/bash
set -euo pipefail
NAMESPACE="telemetry"

echo "=== Kafka Lock Cleanup ==="

# Step 1: Get PVC names before deleting pods
echo "[1] Collecting PVC names..."
PVCS=$(kubectl get pods -n "$NAMESPACE" -l strimzi.io/kind=Kafka \
  -o jsonpath='{.items[*].spec.volumes[*].persistentVolumeClaim.claimName}')
echo "PVCs found: $PVCS"

# Step 2: Force delete all Kafka pods
echo "[2] Force deleting Kafka pods..."
kubectl delete pod -n "$NAMESPACE" -l strimzi.io/kind=Kafka --force --grace-period=0

# Step 3: Clean lock files from each PVC
for PVC in $PVCS; do
  echo "[3] Cleaning lock files from PVC: $PVC"
  kubectl run kafka-lock-cleanup --image=busybox:1.36 -n "$NAMESPACE" --restart=Never --overrides="
  {
    \"spec\": {
      \"containers\": [{
        \"name\": \"cleanup\",
        \"image\": \"busybox:1.36\",
        \"command\": [\"sh\", \"-c\", \"find /data -type f \\\\( -name '*.lock' -o -name '*.sock' -o -name '*.pid' \\\\) -print -delete; echo Done\"],
        \"volumeMounts\": [{\"name\": \"data\", \"mountPath\": \"/data\"}]
      }],
      \"volumes\": [{\"name\": \"data\", \"persistentVolumeClaim\": {\"claimName\": \"$PVC\"}}]
    }
  }"

  # Step 4: Wait for completion
  echo "[4] Waiting for cleanup pod..."
  kubectl wait --for=jsonpath='{.status.phase}'=Succeeded pod/kafka-lock-cleanup -n telemetry --timeout=120s
  kubectl logs kafka-lock-cleanup -n "$NAMESPACE"
  kubectl delete pod kafka-lock-cleanup -n "$NAMESPACE"
done

echo "[5] Verify: kubectl get pods -n $NAMESPACE -l strimzi.io/kind=Kafka"
```

#### iDRAC Lock Cleanup Script

Save the following as `idrac_lock_cleanup.sh`:

```bash title="idrac_lock_cleanup.sh"
#!/bin/bash
set -euo pipefail
NAMESPACE="telemetry"

echo "=== iDRAC Lock Cleanup ==="

# Step 1: Check for corruption — abort if found
echo "[1] Checking logs for data corruption..."
for POD in $(kubectl get pods -n "$NAMESPACE" -l app=idrac-telemetry -o jsonpath='{.items[*].metadata.name}'); do
  LOGS=$(kubectl logs "$POD" -n "$NAMESPACE" --tail=50 2>/dev/null || echo "")

  # Check for corruption indicators
  if echo "$LOGS" | grep -qiE "trying to read page|corruption in the InnoDB tablespace|innodb_force_recovery"; then
    echo ""
    echo "============================================================"
    echo "ERROR: Data corruption detected in pod: $POD"
    echo ""
    echo "Errors found:"
    echo "$LOGS" | grep -iE "trying to read page|Unable to lock mysql.ibd|corruption|Assertion failure|innodb_force_recovery|Unable to read page" | head -5
    echo ""
    echo "Lock cleanup will NOT fix this issue."
    echo "Run: ./idrac_data_corruption_recovery.sh"
    echo "============================================================"
    exit 1
  fi
done

echo "No corruption detected. Proceeding with lock cleanup..."

# Step 2: Get PVC names
echo "[2] Collecting PVC names..."
PVCS=$(kubectl get pods -n "$NAMESPACE" -l app=idrac-telemetry \
  -o jsonpath='{.items[*].spec.volumes[*].persistentVolumeClaim.claimName}')
echo "PVCs found: $PVCS"

# Step 3: Force delete all iDRAC pods
echo "[3] Force deleting iDRAC pods..."
kubectl delete pod -n "$NAMESPACE" -l app=idrac-telemetry --force --grace-period=0

# Step 4: Clean lock files from each PVC
for PVC in $PVCS; do
  echo "[4] Cleaning lock files from PVC: $PVC"
  kubectl run mysql-lock-cleanup --image=busybox:1.36 -n "$NAMESPACE" --restart=Never --overrides="
  {
    \"spec\": {
      \"containers\": [{
        \"name\": \"cleanup\",
        \"image\": \"busybox:1.36\",
        \"command\": [\"sh\", \"-c\", \"find /data -type f \\\\( -name '*.sock' -o -name '*.pid' -o -name '*.lock' -o -name 'ibdata1.lock' \\\\) -print -delete; echo Done\"],
        \"volumeMounts\": [{\"name\": \"data\", \"mountPath\": \"/data\"}]
      }],
      \"volumes\": [{\"name\": \"data\", \"persistentVolumeClaim\": {\"claimName\": \"$PVC\"}}]
    }
  }"

  echo "[5] Waiting for cleanup pod..."
  kubectl wait --for=jsonpath='{.status.phase}'=Succeeded pod/mysql-lock-cleanup -n "$NAMESPACE" --timeout=120s
  kubectl logs mysql-lock-cleanup -n "$NAMESPACE"
  kubectl delete pod mysql-lock-cleanup -n "$NAMESPACE"
done

echo "[6] Verify: kubectl get pods -n $NAMESPACE -l app=idrac-telemetry"
```

#### iDRAC Data Corruption Recovery Script

Save the following as `idrac_data_corruption_recovery.sh`:

```bash title="idrac_data_corruption_recovery.sh"
#!/bin/bash
set -euo pipefail
NAMESPACE="telemetry"

echo "=== iDRAC Data Corruption Recovery ==="
echo "WARNING: This will DELETE all iDRAC PVCs and wipe stored data."
read -rp "Type DELETE to confirm: " CONFIRM
[[ "$CONFIRM" != "DELETE" ]] && echo "Aborted." && exit 0

# Step 1: List PVCs
echo "[1] Current iDRAC PVCs:"
kubectl get pvc -n "$NAMESPACE" -l app=idrac-telemetry

# Step 2: Force delete all pods FIRST (releases PVC binding)
echo "[2] Force deleting iDRAC pods..."
kubectl delete pod -n "$NAMESPACE" -l app=idrac-telemetry --force --grace-period=0

# Step 3: Wait for pods to terminate
echo "[3] Waiting for pods to terminate..."
sleep 10

# Step 4: Delete PVCs (now unbound)
echo "[4] Deleting iDRAC PVCs..."
kubectl delete pvc -n "$NAMESPACE" -l app=idrac-telemetry --wait=false

# Step 5: Verify PVCs are terminating
echo "[5] Checking PVC status..."
sleep 5
REMAINING=$(kubectl get pvc -n "$NAMESPACE" -l app=idrac-telemetry --no-headers 2>/dev/null | wc -l)

if [[ "$REMAINING" -gt 0 ]]; then
  echo "PVCs still terminating. Removing finalizers..."
  for PVC in $(kubectl get pvc -n "$NAMESPACE" -l app=idrac-telemetry -o jsonpath='{.items[*].metadata.name}'); do
    kubectl patch pvc "$PVC" -n "$NAMESPACE" -p '{"metadata":{"finalizers":null}}'
    echo "Finalizer removed from: $PVC"
  done
  sleep 5
fi

# Step 6: Final verification
echo "[6] Verifying cleanup..."
kubectl get pvc -n "$NAMESPACE" -l app=idrac-telemetry 2>/dev/null || echo "All PVCs deleted."
kubectl get pod -n "$NAMESPACE" -l app=idrac-telemetry 2>/dev/null || echo "All pods deleted."

# Step 7: Re-deploy
echo ""
echo "[7] Re-deploy with: ansible-playbook telemetry/telemetry.yml"
echo "    Use the SAME inputs as the previous deployment."
```

### GPU Usage Metrics Not Available via iDRAC Telemetry on PowerEdge XE8712

**Description:** On the PowerEdge XE8712 equipped with NVIDIA GB200 accelerators, GPU utilization metrics are not correctly reported through iDRAC telemetry. Downstream consumers such as Kafka and VictoriaMetrics show zero GPU usage, even though the GPUs are fully utilized. This behavior is inconsistent with on-host monitoring, where `nvidia-smi` reports 100% GPU utilization.

**Cause:** This issue is an iDRAC telemetry limitation specific to this platform and accelerator combination. It has been observed with iDRAC version 1.30.30.50 and lower.

**Resolution:** Until a fix is provided in a future iDRAC release, monitor GPU utilization directly from the host using `nvidia-smi` instead of relying on iDRAC-based telemetry for GPU usage metrics.


!!! info

    - [Release Notes](../Overview/release_notes.md) -- Release notes with version-specific changes and fixes.
    - [Prerequisites Checklist](../GetStarted/prerequisites_checklist.md) -- Full prerequisite list.
    - [Network Topologies](../Overview/network_topologies.md) -- Supported network configurations.
    - [Upgrade Omnia](../Operations/upgrade_omnia.md) -- Upgrade procedures and requirements.
    - [Rollback Omnia](../Operations/rollback_omnia.md) -- Rollback procedures.
