# K8s & Telemetry Upgrade - Test Case Coverage Analysis

**Source**: `K8s-Telemetry-upgrade-test-cases-v2.xls`
**Date**: 2026-06-30
**Assumption**: The upgrade/rollback playbook is run externally. Pre-checks run before, post-checks run after.

---

## Pytest Markers / Tags

Every test is tagged with one or more `@pytest.mark.*` markers so you can run
subsets selectively. The available markers for upgrade tests are:

| Marker | Description | Usage |
|--------|-------------|-------|
| `sanity` | Core functionality checks (default for all tests) | `pytest -m sanity` |
| `security` | Permissions and access-control checks (TC-S001/S002) | `pytest -m security` |
| `rollback` | Post-rollback state verification (TC-R*) | `pytest -m rollback` |
| `idempotency` | Re-run consistency verification (TC-I*) | `pytest -m idempotency` |
| `negative` | Error injection / failure handling (NOT automatable) | Reserved — requires fault-injection framework |
| `stress` | Performance / load testing (NOT automatable) | Reserved — requires runtime timing |

### Marker Assignment per Test

#### Pre-Check Tests (`test_k8s_telemetry_precheck.py`)

| Test | Markers |
|------|---------|
| TC-01 to TC-23 | `sanity` |
| TC-24 (security permissions) | `sanity`, `security` |
| TC-25 to TC-37 | `sanity` |

#### Post-Check Tests (`test_k8s_telemetry_postcheck.py`)

| Test | Markers |
|------|---------|
| TC-01 to TC-41 | `sanity` |
| TC-42 (security permissions) | `sanity`, `security` |
| TC-43 (idempotency) | `sanity`, `idempotency` |
| TC-44 (rollback: nodes at source) | `sanity`, `rollback` |
| TC-45 (rollback: etcd restored) | `sanity`, `rollback` |
| TC-46 (rollback: Helm restored) | `sanity`, `rollback` |
| TC-47 (rollback: telemetry healthy) | `sanity`, `rollback` |
| TC-48 (rollback: MetalLB cleaned) | `sanity`, `rollback` |
| TC-49 (rollback: CSI cleaned) | `sanity`, `rollback` |

#### Negative & Performance Tests (`test_k8s_telemetry_negative.py`)

| Test | Markers |
|------|---------|
| TC-E001 to TC-E015 (K8s error injection) | `negative` |
| TC-TEL-E001 to TC-TEL-E007 (Telemetry error injection) | `negative` |
| TC-P001 to TC-P003, TC-TEL-P001 (Performance) | `stress` |
| TC-R004, TC-R005, TC-R008, TC-R011 (Partial rollback) | `rollback`, `negative` |

### Example CLI Usage

```bash
# Run all upgrade sanity tests
pytest -m sanity

# Run only security tests
pytest -m security

# Run only rollback verification tests
pytest -m rollback

# Run sanity tests but EXCLUDE rollback
pytest -m "sanity and not rollback"

# Run security + idempotency tests
pytest -m "security or idempotency"

# Run negative (error injection) tests — DESTRUCTIVE, use dedicated env
pytest -m negative

# Run performance/stress tests
pytest -m stress

# Run rollback-specific tests (includes partial rollback negatives)
pytest -m rollback
```

---

## 1. Covered Test Cases (Automated as Pre-Check / Post-Check)

### Pre-Check Tests (37 tests in `test_k8s_telemetry_precheck.py`)

> **NOTE**: DCGM, PowerScale, VAST, UFM, Vector, VictoriaLogs are new in Omnia 2.2
> and do not exist in 2.1. No pre-check baseline to collect for these components.
> Post-check validates them based on `telemetry_config.yml` flags.

| Test # | Excel TC | Function | Description |
|--------|----------|----------|-------------|
| TC-01 | TC-F001 | `collect_k8s_node_versions` | K8s node versions (current) |
| TC-02 | TC-F015 Gate 3 | `collect_node_readiness` | All nodes Ready |
| TC-03 | TC-F013 | `collect_kube_system_pods` | kube-system pods healthy |
| TC-04 | TC-F015 Gate 4 | `collect_etcd_health` | etcd cluster healthy |
| TC-05 | TC-F013 | `collect_calico_status` | Calico pods running |
| TC-06 | TC-F013 | `collect_metallb_status` | MetalLB pods running |
| TC-07 | TC-E016 | `collect_lb_service_ips` | LoadBalancer service IPs recorded |
| TC-08 | TC-TEL-F003 | `collect_helm_releases` | Helm releases in telemetry namespace |
| TC-09 | TC-F020 | `collect_telemetry_pods` | Telemetry pods running |
| TC-10 | TC-TEL-F005 | `collect_vm_pvcs` | VictoriaMetrics PVCs Bound |
| TC-11 | TC-TEL-F004/F003 | `collect_kafka_state` | Kafka brokers healthy, topics recorded |
| TC-12 | TC-F019 | `collect_csi_status` | CSI driver pods and PVCs |
| TC-13 | Precondition | `collect_nfs_provisioner` | NFS provisioner deployed |
| TC-14 | TC-F006 | `collect_crio_version` | CRI-O version per node |
| TC-15 | TC-F007 | `collect_calico_version` | Calico controller image version |
| TC-16 | TC-F007 | `collect_network_policies` | Network policies snapshot |
| TC-17 | TC-F008 | `collect_metallb_version` | MetalLB version + IPAddressPool CRDs |
| TC-18 | TC-F009 | `collect_helm_version` | Helm binary version |
| TC-19 | TC-TEL-F006 | `collect_idrac_telemetry_status` | iDRAC telemetry pod status |
| TC-20 | TC-TEL-F007 | `collect_ldms_status` | LDMS sampler/aggregator pods |
| TC-21 | TC-F015 Gate 2 | `verify_ssh_connectivity` | SSH connectivity to all nodes |
| TC-22 | TC-F015 Gate 5 / TC-F017 | `verify_version_hop_valid` | Version hop is exactly one minor |
| TC-23 | TC-F003 | `collect_etcd_backup_status` | etcd snapshot readiness + backup dir |
| TC-24 | TC-S001/S002 | `collect_security_permissions` | SSH key and backup dir permissions |
| TC-25 | TC-F015 Gate 1 | `verify_pulp_images_available` | Target K8s images in registry |
| TC-26 | TC-F018 | `verify_addon_compatibility` | Calico/MetalLB/Helm healthy pre-upgrade |
| TC-27 | TC-F011 | `collect_bss_boot_params` | BSS boot params baseline (kernel, OS) |
| TC-28 | TC-TEL-F004/F016 | `collect_strimzi_version` | Strimzi operator, Kafka version, KRaft status |
| TC-29 | TC-F006 | `collect_crio_storage_config` | CRI-O storage config baseline |
| TC-30 | TC-F014 | `collect_kube_vip_status` | kube-vip pod status + VIP reachability |
| TC-31 | TC-F005 | `collect_pod_disruption_budgets` | PDBs across cluster |
| TC-32 | TC-F002/F004 | `collect_node_roles` | Node roles (CPs vs workers) + IPs |
| TC-33 | TC-TEL-F002 | `verify_telemetry_preflight` | Telemetry pre-flight checks |
| TC-34 | TC-TEL-F009-F014 | `collect_telemetry_config_flags` | Telemetry config flags for Phase 2 |
| TC-35 | TC-TEL-F001 | `verify_k8s_at_target_for_telemetry` | K8s at target for telemetry upgrade |
| TC-36 | TC-F016 | `verify_oim_upgrade_completed` | OIM upgrade completion status |
| TC-37 | -- | `save_precheck_snapshot` | Persist snapshot to JSON on OIM |

### Post-Check Tests (49 tests in `test_k8s_telemetry_postcheck.py`)

| Test # | Excel TC | Function | Description |
|--------|----------|----------|-------------|
| TC-01 | -- | `load_precheck_snapshot` | Load pre-upgrade snapshot |
| TC-02 | TC-F001 | `verify_k8s_target_version` | All nodes at target K8s version |
| TC-03 | TC-F013 | `verify_all_nodes_ready` | All nodes Ready |
| TC-04 | TC-F013 | `verify_kube_system_healthy` | kube-system pods healthy |
| TC-05 | TC-F013 | `verify_etcd_healthy` | etcd cluster healthy |
| TC-06 | TC-F013/F014 | `verify_api_server_reachable` | API server reachable via VIP |
| TC-07 | TC-F013 | `verify_dns_resolution` | DNS resolution working |
| TC-08 | TC-F013 | `verify_calico_healthy` | Calico pods running |
| TC-09 | TC-E016 | `verify_metallb_ips_preserved` | MetalLB LB IPs preserved |
| TC-10 | TC-F020 | `verify_telemetry_pods_running` | Telemetry pods running |
| TC-11 | TC-TEL-F005/R002 | `verify_vm_pvcs_preserved` | VictoriaMetrics PVCs preserved |
| TC-12 | TC-TEL-F005 | `verify_vm_data_accessible` | VM historical data accessible |
| TC-13 | TC-TEL-F004/R003 | `verify_kafka_topics_preserved` | Kafka topics preserved |
| TC-14 | TC-F019 | `verify_csi_pvcs_preserved` | CSI PVCs remain Bound |
| TC-15 | TC-TEL-F003 | `verify_helm_releases_present` | Helm releases still present |
| TC-16 | TC-F006 | `verify_crio_at_target` | CRI-O at target K8s minor |
| TC-17 | TC-F007 | `verify_calico_version_upgraded` | Calico version upgraded |
| TC-18 | TC-F007 | `verify_network_policies_preserved` | Network policies preserved |
| TC-19 | TC-F008 | `verify_metallb_version_upgraded` | MetalLB version + IP pools preserved |
| TC-20 | TC-F009 | `verify_helm_at_target` | Helm binary at/above pre-upgrade |
| TC-21 | TC-F010 | `verify_nfs_provisioner_running` | NFS provisioner running |
| TC-22 | TC-TEL-F006 | `verify_idrac_telemetry_running` | iDRAC telemetry pods running |
| TC-23 | TC-TEL-F007 | `verify_ldms_collecting` | LDMS pods running |
| TC-24 | TC-TEL-F009 | `verify_dcgm_running` | DCGM nvidia-dcgm.service on GPU nodes (2.2, config-gated) |
| TC-25 | TC-TEL-F010 | `verify_powerscale_telemetry_running` | PowerScale karavi + otel-collector pods (2.2, config-gated) |
| TC-26 | TC-TEL-F011 | `verify_vast_telemetry_running` | VAST VMServiceScrape (vast-storage-metrics) (2.2, config-gated) |
| TC-27 | TC-TEL-F012 | `verify_ufm_telemetry_running` | UFM VMServiceScrape (ufm-infiniband-metrics) (2.2, config-gated) |
| TC-28 | TC-TEL-F013 | `verify_vector_running` | Vector vector-ldms/vector-ome deployments (2.2, config-gated) |
| TC-29 | TC-TEL-F014 | `verify_victorialogs_running` | VictoriaLogs vlstorage/vlinsert/vlselect/vlagent (2.2, config-gated) |
| TC-30 | TC-F013/TEL-F015 | `verify_upgrade_manifest` | upgrade_manifest.yml status |
| TC-31 | TC-F002 | `verify_cps_at_target` | All CPs at target version + Ready |
| TC-32 | TC-F004 | `verify_workers_at_target` | All workers at target version + Ready |
| TC-33 | TC-F003 | `verify_etcd_backup_exists` | etcd snapshot + /etc/kubernetes backup exist |
| TC-34 | TC-F005 | `verify_pdbs_healthy` | PDBs satisfied after upgrade |
| TC-35 | TC-F006 | `verify_crio_storage_preserved` | CRI-O storage config unchanged |
| TC-36 | TC-F011 | `verify_bss_params_updated` | BSS boot params updated |
| TC-37 | TC-F014 | `verify_kube_vip_ha` | kube-vip running + VIP reachable |
| TC-38 | TC-TEL-F004 | `verify_strimzi_upgraded` | Strimzi/Kafka upgraded + brokers running |
| TC-39 | TC-TEL-F016 | `verify_kraft_migration` | Kafka using KRaft (no ZooKeeper) |
| TC-40 | TC-TEL-F008 | `verify_telemetry_phase1_gate` | Phase 1 gate: pods + Kafka + VM healthy |
| TC-41 | TC-TEL-F009-F014 | `verify_new_telemetry_components` | Phase 2 components deployed/absent per config |
| TC-42 | TC-S001/S002 | `verify_security_permissions` | Backup dir (0700), SSH keys (0600) |
| TC-43 | TC-I001/I002/TEL-I | `verify_cluster_unchanged` | Cluster state consistent (idempotency) |
| TC-44 | TC-R001/R006/R007 | `verify_rollback_to_source` | All nodes at source version |
| TC-45 | TC-R002/R003 | `verify_rollback_etcd_restored` | etcd healthy after rollback |
| TC-46 | TC-R012 | `verify_rollback_helm_restored` | Helm restored to pre-upgrade version |
| TC-47 | TC-R007/TEL-R001 | `verify_rollback_telemetry_healthy` | Telemetry stack healthy after rollback |
| TC-48 | TC-R009 | `verify_rollback_metallb_cleaned` | MetalLB healthy (stale IPs cleaned) |
| TC-49 | TC-R010 | `verify_rollback_csi_cleaned` | No stale CSI VolumeAttachments |

---

## 2. Negative, Performance, Execute & Partial-Rollback Tests

These tests are now implemented as test stubs in
`molecule/Upgrade/Negative/K8s_telemetry/tests/negative/test_k8s_telemetry_negative.py`.

**⚠️ WARNING**: These tests perform **DESTRUCTIVE operations** (killing processes,
filling disks, partitioning networks). Run ONLY in dedicated test environments.

**Scenario**: `upgrade_negative_k8s_telemetry`
**Usage**: `./run_molecule.sh upgrade_negative_k8s_telemetry verify -- -m negative`

### Category A: K8s Upgrade Error Injection (marker: `negative`)

These tests inject faults during the upgrade to verify error handling,
halt behavior, and recovery.

| Excel TC | Description | Specific Reason |
|----------|-------------|-----------------|
| **TC-E001** | Simulate etcd snapshot failure (disk full / etcd unreachable). Verify upgrade does NOT proceed. | Requires injecting disk-full or etcd-down conditions on CP-01 mid-upgrade. Needs the upgrade playbook to be running and encounter the failure at the etcd snapshot step. |
| **TC-E002** | Simulate etcd quorum loss during CP upgrade. Verify upgrade halts, rollback restores cluster. | Requires killing 2 of 3 etcd members while `kubeadm upgrade` is actively running. Tests runtime halt + rollback behavior. |
| **TC-E003** | CP-02 fails during upgrade; CP-01+CP-03 healthy. Verify quorum maintained, can delete/re-join, resume. | Requires mid-upgrade process kill on CP-02 (e.g., `kill -9 kubeadm`). Validates recovery from a partial failure state that must be artificially created. |
| **TC-E004** | Worker W-02 fails during rolling upgrade. Verify halt, already-upgraded workers healthy. | Requires simulated kubelet upgrade failure on a specific worker. Needs control over the upgrade process to fail at a precise node. |
| **TC-E005** | CP fails `kubeadm upgrade node` on multiple retries. Verify kept at old version, upgrade stops. | Requires repeated deterministic `kubeadm` failures — needs a stub/mock that makes kubeadm fail on demand. |
| **TC-E006** | Worker fails kubelet upgrade on multiple attempts. Kept at old version, others unaffected. | Requires simulating kubelet package install failure (e.g., corrupt RPM, broken repo). Not observable from outside the upgrade process. |
| **TC-E007** | CP-01 at 1.35.x, CP-02 fails. Verify rollback restores all to 1.34.1; no inconsistent state. | Requires creating a mixed-version cluster state (CP-01 upgraded, CP-02 failed) by interrupting the upgrade at a specific CP. |
| **TC-E008** | All CPs + W-01 at 1.35.x, W-02 fails. Verify rollback returns to consistent pre-upgrade state. | Requires partial upgrade (all CPs + 1 worker done) plus deliberate worker failure, then rollback. |
| **TC-E009** | Failure after backup but before kubeadm. Cluster unchanged, no rollback needed, re-run works. | Requires interrupting the upgrade at a precise point (after etcd snapshot + /etc/kubernetes backup, before kubeadm apply). Needs process-level control. |
| **TC-E010** | Network partition during worker upgrade. Already-upgraded workers healthy. Re-run resumes. | Requires injecting network partition (e.g., `iptables DROP` between OIM and a worker). Infrastructure-level fault injection. |
| **TC-E011** | PDB `maxUnavailable=0` blocks drain. Verify timeout, worker not forcefully drained, error reported. | Requires creating a PDB with maxUnavailable=0 and then attempting drain. Tests the upgrade playbook's drain timeout behavior — runtime logic, not cluster state. |
| **TC-E012** | Worker upgrades kubelet but stays NotReady. Post-upgrade validation detects. | Requires corrupting kubelet config so it starts but fails to rejoin. Needs deliberate misconfiguration injection. |
| **TC-E013** | `kubeadm upgrade apply` fails on CP-01. Verify halt, CP-01 at source (atomic), no other nodes affected. | Requires making `kubeadm upgrade apply` fail (e.g., invalid image, broken manifest). Needs the upgrade to be running and to fail. |
| **TC-E014** | SSH loss during CP/worker upgrade. Task fails. After restoring SSH, re-run resumes (idempotency). | Requires dropping SSH mid-upgrade (e.g., firewall rule on target node). Tests Ansible's SSH resilience and playbook idempotency. |
| **TC-E015** | Monitor connectivity during Calico upgrade. At most brief blip. Policies enforced. | Requires continuous network monitoring (ping/curl loop) DURING Calico pod restarts. Needs real-time observation while the upgrade runs, not a snapshot. |

### Category B: Telemetry Upgrade Error Injection (marker: `negative`)

Error injection tests specific to the telemetry upgrade phase.

| Excel TC | Description | Specific Reason |
|----------|-------------|-----------------|
| **TC-TEL-E001** | Simulate Kafka broker failure during Strimzi rolling restart. Verify failure detected, upgrade halts. | Requires killing a Kafka broker pod (`kubectl delete pod`) during Strimzi's rolling restart. Needs the telemetry upgrade to be actively running Phase 1. |
| **TC-TEL-E002** | Simulate VM data loss (vmagent targets down). Verify detected, PV verified, rollback restores. | Requires making vmagent targets unresponsive (scale down vmagent, or block scrape endpoints). Must happen during VM upgrade phase. |
| **TC-TEL-E003** | Simulate iDRAC receiver failing to connect to ActiveMQ. Verify detected, operator can recover. | Requires blocking ActiveMQ connectivity for the iDRAC receiver pod (network policy or port block). Infrastructure-level fault. |
| **TC-TEL-E004** | Simulate LDMS aggregator CrashLoopBackOff after config update. Verify configs restored from backup. | Requires corrupting the LDMS ConfigMap to cause CrashLoopBackOff, then verifying the upgrade's backup restoration logic kicks in. |
| **TC-TEL-E005** | Simulate Helm install failure for a new Phase 2 component. Verify failure reported, rollback removes it. | Requires making `helm install` fail (invalid chart, missing values, quota exceeded). Tests the upgrade playbook's error handling. |
| **TC-TEL-E006** | Simulate Phase 1 validation gate failure. Verify Phase 2 components are NOT deployed. | Requires inducing Phase 1 failure (e.g., Kafka not Running after upgrade) and verifying the playbook's gating logic prevents Phase 2. Tests playbook control flow. |
| **TC-TEL-E007** | Verify upgrade detects Strimzi/Kafka version incompatibility and halts with clear error. | Requires providing an incompatible Strimzi/Kafka version pair in config. Tests the playbook's pre-upgrade validation logic, not cluster state. |

### Category C: Performance Tests (marker: `stress`)

These tests run the upgrade playbook and measure wall-clock time per
node/phase. Thresholds are enforced via assertions.

| Excel TC | Description | Specific Reason |
|----------|-------------|-----------------|
| **TC-P001** | Measure wall-clock per CP (drain->uncordon). Each <= 15 min. Document dominant steps. | Requires timing each step (drain start, kubeadm apply, kubelet restart, uncordon) as they execute. Pre/post checks don't run during the upgrade. |
| **TC-P002** | Measure per-worker time on 10+ worker cluster. Each <= 10 min. Parallelism reduces total time. | Requires real-time timing + a 10+ worker cluster. Cannot be measured from snapshot-based checks. |
| **TC-P003** | 50 workers (extrapolate to 500), max_parallel=10. Linear scaling, no bottlenecks. | A scale/stress test requiring a 50+ node cluster and timing the upgrade with parallelism settings. Entirely a runtime measurement. |
| **TC-TEL-P001** | Measure telemetry upgrade time: Phase 1 (Strimzi, VM, iDRAC, LDMS) and Phase 2 (new components). Kafka rolling restart should not exceed 10 min. | Same — needs real-time timing during the telemetry upgrade phases. |

### Category D: Partial/Complex Rollback Scenarios (markers: `rollback`, `negative`)

These tests create specific intermediate cluster states by interrupting
the upgrade at precise points, then run rollback and verify recovery.

| Excel TC | Description | Specific Reason |
|----------|-------------|-----------------|
| **TC-R004** | Rollback with only CPs upgraded (workers still at source). Verify all return to source. | Requires a partially upgraded cluster (CPs at 1.35, workers at 1.34). This state only exists if the upgrade is interrupted after CP phase but before worker phase. |
| **TC-R005** | Rollback with mixed CP+worker versions (CP-01 at 1.35, CP-02/03 + workers at 1.34). | Requires stopping the upgrade after just CP-01 and running rollback from that mixed state. Very specific intermediate state. |
| **TC-R008** | Rollback on cluster with CSI driver and active PVCs. Verify data accessible after rollback. | While we verify CSI state in TC-42 (post-rollback), this TC specifically requires running `rollback.yml` with an active CSI workload and verifying data integrity during the rollback process. |
| **TC-R011** | Rollback on HA cluster. Verify kube-vip split-brain resolved after etcd restore. | Requires the rollback process to encounter and resolve a kube-vip split-brain condition. Tests the rollback playbook's runtime behavior, not a state that can be checked before/after. |

### Category E: Upgrade Playbook Execution Verification (marker: `negative`)

These tests verify the upgrade playbook execution results (log, manifest, cluster access).
The converge step runs the upgrade playbook; these tests validate its output.

| Excel TC | Test Function | Description |
|----------|---------------|-------------|
| **TC-EX01** | `test_upgrade_log_exists` | Verify upgrade execution log exists and is non-empty |
| **TC-EX02** | `test_upgrade_manifest_updated` | Verify upgrade_manifest.yml shows k8s completed |
| **TC-EX03** | `test_cluster_accessible` | Verify kubectl get nodes works after upgrade |

### Category F: Documentation / Design Notes

| Excel TC | Description | Specific Reason |
|----------|-------------|-----------------|
| **TC-TEL-R004** | **NOTE**: k8s-telemetry rollback uses etcd snapshot restore, which reverts the entire K8s cluster state — including Phase 1 components. Selective rollback of Phase 2 while keeping Phase 1 is not supported. | This is a design documentation note, not an executable test case. No verification steps defined. |

---

## 3. Summary Statistics

| Category | Count | Marker | Scenario |
|----------|-------|--------|----------|
| Pre-check tests | 37 | `sanity` (+`security`) | `upgrade_pre_k8s_telemetry` |
| Post-check tests | 49 | `sanity` (+`security`,`rollback`,`idempotency`) | `upgrade_post_k8s_telemetry` |
| K8s error injection | 15 | `negative` | `upgrade_negative_k8s_telemetry` |
| Telemetry error injection | 7 | `negative` | `upgrade_negative_k8s_telemetry` |
| Performance tests | 4 | `stress` | `upgrade_negative_k8s_telemetry` |
| Partial rollback | 4 | `rollback`+`negative` | `upgrade_negative_k8s_telemetry` |
| Execute verification | 3 | `negative` | `upgrade_negative_k8s_telemetry` |
| Setup (env init) | 1 | `negative` | `upgrade_negative_k8s_telemetry` |
| Documentation notes | 1 | — | Not a test |
| **Total test functions** | **121** | | |

### File Locations

- **Pre-check functions**: `automation_library/upgrade_and_rollback/functions/precheck_func.py`
- **Post-check functions**: `automation_library/upgrade_and_rollback/functions/postcheck_func.py`
- **Snapshot persistence**: `automation_library/upgrade_and_rollback/functions/snapshot_func.py`
- **Variables**: `automation_library/upgrade_and_rollback/vars/k8s_telemetry_upgrade_vars.py`
- **Messages**: `automation_library/upgrade_and_rollback/messages/k8s_telemetry_upgrade_msgs.py`
- **Pre-check tests**: `molecule/Upgrade/Pre_check/K8s_telemetry/tests/sanity/test_k8s_telemetry_precheck.py`
- **Post-check tests**: `molecule/Upgrade/Post_check/K8s_telemetry/tests/sanity/test_k8s_telemetry_postcheck.py`
- **Negative/Perf tests**: `molecule/Upgrade/Negative/K8s_telemetry/tests/negative/test_k8s_telemetry_negative.py`
- **Excel source**: `K8s-Telemetry-upgrade-test-cases-v2.xls`

### Molecule Scenarios

| Scenario Name | Folder | Description |
|---|---|---|
| `upgrade_pre_k8s_telemetry` | `molecule/Upgrade/Pre_check/K8s_telemetry/` | Pre-upgrade state capture |
| `upgrade_post_k8s_telemetry` | `molecule/Upgrade/Post_check/K8s_telemetry/` | Post-upgrade state validation |
| `upgrade_negative_k8s_telemetry` | `molecule/Upgrade/Negative/K8s_telemetry/` | Negative, performance, execute & partial rollback |

### Recommended Execution Order

```bash
# 1. Capture pre-upgrade state
./run_molecule.sh upgrade_pre_k8s_telemetry test

# 2. Validate post-upgrade state
./run_molecule.sh upgrade_post_k8s_telemetry test

# 3. Run negative/execute/performance tests (runs upgrade playbook + tests in dedicated env)
./run_molecule.sh upgrade_negative_k8s_telemetry verify
./run_molecule.sh upgrade_negative_k8s_telemetry verify -- -m negative
./run_molecule.sh upgrade_negative_k8s_telemetry verify -- -m stress
```
