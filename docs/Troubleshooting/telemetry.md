# Telemetry Issues

Issues related to the telemetry pipeline: Kafka, iDRAC telemetry, LDMS samplers, VictoriaMetrics (cluster mode), VictoriaLogs, and Grafana dashboards.

## Kafka pods CrashLoopBackOff

???+ note "Symptom"

    Kafka pods enter `CrashLoopBackOff` state.

??? note "Cause"

    - No service kube nodes available.
    - Missing CSI driver.
    - Persistent volume full.

??? note "Resolution"

    1. Ensure service kube nodes are booted.
    2. Add PowerScale CSI driver (see [Missing PowerScale CSI Driver](kubernetes.md#missing-powerscale-csi-driver)).
    3. Increase Kafka volume and configure log retention.

## Kafka "No space left on device"

???+ note "Symptom"

    Kafka pods crash with "No space left on device" errors.

??? note "Cause"

    Configured `persistence_size` for Kafka has reached capacity limit.

??? note "Resolution"

    The default `8Gi` persistent volume size is suitable for small clusters (typically fewer than 5 nodes). For larger clusters, increase `persistence_size` and configure Kafka retention settings `log_retention_hours` and `log_retention_bytes` so that old logs are deleted before the persistent volume reaches its limit.

## LDMS metrics missing

???+ note "Symptom"

    LDMS metrics do not appear in the telemetry dashboard or are missing expected data points.

??? note "Cause"

    - LDMS aggregator pods are not running or experiencing errors.
    - LDMS store daemon service is inactive.
    - LDMS sampler service is not functioning correctly.

??? note "Resolution"

    Check the status of LDMS components and review logs for errors:

    ```bash title="Run on: K8s control plane"
    kubectl logs -n telemetry nersc-ldms-aggr-0
    kubectl logs -n telemetry nersc-ldms-store-slurm-cluster-0
    ```

    ```bash title="Run on: compute node"
    sudo systemctl status ldmsd.sampler.service
    ```

    Query the LDMS sampler set directly:

    ```bash title="Run on: compute node"
    /opt/ovis-ldms/sbin/ldms_ls <host>:<port>
    ```

## iDRAC telemetry — no metrics reaching VictoriaMetrics / Kafka

???+ note "Symptom"

    iDRAC metrics (power, thermal, fan, CPU) do not appear in Grafana or VictoriaMetrics, or data is stale. The iDRAC telemetry receiver pods restart repeatedly or remain in `0/1 Ready` state. New nodes do not appear as telemetry sources after provisioning.

    Example errors in VictoriaPump / KafkaPump container logs:

    - `ERROR failed to subscribe to Redfish event service: 401 Unauthorized`
    - `ERROR redfish: event subscription rejected (SubscriptionLimitExceeded)`
    - `WARN activemq: connection refused tcp 127.0.0.1:61616`
    - `ERROR victoriapump: post to vmagent failed: dial tcp <vmagent-svc>:8429: connect: connection refused`

??? note "Cause"

    - Incorrect or expired iDRAC credentials in the vault (`idrac_username` / `idrac_password`).
    - Redfish subscription limit reached on iDRAC (stale subscriptions from prior runs).
    - iDRAC firmware does not support Redfish Telemetry/EventService.
    - Pipeline component failure (ActiveMQ, KafkaPump, or VictoriaPump not ready).
    - `idrac_telemetry_collection_type` misconfiguration.
    - Firewall blocking OIM from reaching iDRAC on port 443, or receiver from reaching vmagent:8429 or Kafka brokers.

??? note "Resolution"

    **Diagnostics:**

    ```bash title="Run on: K8s control plane"
    kubectl get pods -A | grep -Ei 'telemetry|idrac|victoria|kafka'
    kubectl -n telemetry-and-visualizations logs <idrac-telemetry-pod> -c victoriapump --tail=100
    kubectl -n telemetry-and-visualizations logs <idrac-telemetry-pod> -c kafkapump --tail=100
    ```

    Verify Redfish reachability and credentials:

    ```bash title="Run on: OIM host"
    curl -sk -u "$IDRAC_USER:$IDRAC_PASS" https://<idrac-ip>/redfish/v1/EventService | head
    ```

    List and delete stale Redfish subscriptions:

    ```bash title="Run on: OIM host"
    curl -sk -u "$IDRAC_USER:$IDRAC_PASS" https://<idrac-ip>/redfish/v1/EventService/Subscriptions
    ```

    Confirm metrics landed in VictoriaMetrics:

    ```bash title="Run on: OIM host"
    curl -s 'http://<vmselect-svc>:8481/select/0/prometheus/api/v1/query?query=up' | head
    ```

    **Resolution steps:**

    1. Correct `idrac_username` / `idrac_password` in the Ansible vault, then re-run `telemetry.yml`.
    2. Delete orphaned Redfish subscriptions using `curl -X DELETE ...`, then allow the receiver to re-subscribe.
    3. Update iDRAC firmware to a version that supports Redfish EventService/Telemetry.
    4. If ActiveMQ/KafkaPump/VictoriaPump is unhealthy, check container logs and restart the receiver pod after confirming the root cause.
    5. Set `idrac_telemetry_collection_type` to `victoria`, `kafka`, or `victoria,kafka` to match where you expect data.
    6. Ensure OIM can reach iDRAC on port 443 and the receiver can reach vmagent:8429 and Kafka on port 9092.

    !!! note

        iDRAC telemetry is enabled by `idrac_telemetry_support: true` and routed per `idrac_telemetry_collection_type` in `input/telemetry_config.yml`. The receiver (MySQL + ActiveMQ + KafkaPump + VictoriaPump) is a generated StatefulSet — modify inputs and re-run rather than editing the pod.

## VictoriaMetrics (cluster mode) — pods down, PVC full, or queries failing

???+ note "Symptom"

    Grafana panels show "No data" or queries time out. One or more `vmstorage`, `vminsert`, or `vmselect` pods are in `CrashLoopBackOff`, `Pending`, or `Evicted` state. Recent samples are missing while older data is present.

    Omnia deploys VictoriaMetrics in cluster mode with TLS: vmstorage (3 replicas), vminsert (2), vmselect (2), and vmagent (2), with replication factor 2.

    Example errors:

    - vmstorage: `panic: cannot open storage at "/storage": no space left on device`
    - vminsert: `cannot send data to vmstorage node "vmstorage-1:8400": connection timed out`
    - vmselect: `error during search: cannot fetch data from vmstorage nodes: not enough healthy storage nodes`

??? note "Cause"

    - vmstorage PVC is full (retention or ingest volume exceeded provisioned storage).
    - Insufficient healthy replicas (with replication factor 2, losing 2+ vmstorage pods prevents vmselect from satisfying reads).
    - Resource pressure (pods Pending or Evicted due to insufficient memory or node disk pressure).
    - TLS or certificate mismatch between vminsert/vmselect and vmstorage.
    - vmagent backlog (vmagent cannot reach vminsert, queues fill, remote_write stalls).

??? note "Resolution"

    **Diagnostics:**

    ```bash title="Run on: K8s control plane"
    kubectl -n telemetry-and-visualizations get pods -l 'app in (vmstorage,vminsert,vmselect,vmagent)' -o wide
    kubectl -n telemetry-and-visualizations get pvc | grep -i vmstorage
    kubectl -n telemetry-and-visualizations describe pod <vmstorage-pod> | sed -n '/Events/,$p'
    kubectl -n telemetry-and-visualizations exec <vmstorage-pod> -- df -h /storage
    kubectl -n telemetry-and-visualizations logs <vminsert-pod> --tail=100
    kubectl -n telemetry-and-visualizations logs <vmselect-pod> --tail=100
    kubectl -n telemetry-and-visualizations logs <vmagent-pod> --tail=100 | grep -Ei 'remote_write|error|drop'
    ```

    **Resolution steps:**

    1. Expand the vmstorage PVC (if the StorageClass allows `allowVolumeExpansion`) or reduce retention via the telemetry input config, then re-run `telemetry.yml`.
    2. Restore quorum by bringing failed vmstorage pods back (resolve node disk pressure or memory issues).
    3. Free node resources or adjust requests/limits via the input config.
    4. Regenerate or rotate telemetry certificates via the playbook.
    5. Once vminsert is reachable, vmagent flushes its queue automatically.

    !!! note

        Cluster mode, replica counts, replication factor, TLS, and retention are rendered from `input/telemetry_config.yml` and `input/service_k8s.json`. Modify inputs and re-run; pod edits are transient. Size vmstorage capacity for peak source count (iDRAC + LDMS + DCGM + PowerScale + UFM + VAST + OME), not initial node count.

## VictoriaLogs (cluster mode) — logs missing or unsearchable

???+ note "Symptom"

    Log queries return nothing or only old data; new node or syslog events never appear. `vlstorage`, `vlinsert`, or `vlselect` pods restart repeatedly or remain unready. There is ingestion lag between event time and searchability.

    Example errors:

    - vlstorage: `cannot create new part: no space left on device`
    - vlinsert: `cannot proxy request to vlstorage: dial tcp <vlstorage-svc>:9491: i/o timeout`
    - vlselect: `cannot perform query: some vlstorage nodes are unavailable`
    - VLAgent: `syslog: failed to forward to vlinsert: connection refused`

??? note "Cause"

    - vlstorage PVC is full (log volume exceeded provisioned storage).
    - vlstorage nodes are unavailable (vlselect cannot complete queries).
    - VLAgent to vlinsert path is broken (firewall, wrong service endpoint, or TLS mismatch).
    - No source configured (a device or service is not shipping syslog to VLAgent).

??? note "Resolution"

    **Diagnostics:**

    ```bash title="Run on: K8s control plane"
    kubectl -n telemetry-and-visualizations get pods -l 'app in (vlinsert,vlstorage,vlselect)' -o wide
    kubectl -n telemetry-and-visualizations get pvc | grep -i vlstorage
    kubectl -n telemetry-and-visualizations exec <vlstorage-pod> -- df -h /vlstorage
    kubectl -n telemetry-and-visualizations logs <vlinsert-pod> --tail=100
    ```

    Confirm logs are ingesting (LogsQL count over the last 5 minutes):

    ```bash title="Run on: K8s control plane"
    curl -s 'http://<vlselect-svc>:9471/select/logsql/query' --data-urlencode 'query=*' --data-urlencode 'limit=1'
    ```

    **Resolution steps:**

    1. Expand the vlstorage PVC or reduce log retention via the telemetry input config, then re-run `telemetry.yml`.
    2. Recover unavailable vlstorage pods so vlselect can query them.
    3. Verify the syslog source points at the VLAgent service, the firewall permits the syslog port, and TLS matches.
    4. Ensure the device or service (PowerScale, UFM, VAST, NetQ, Skyway, OS syslog) is configured to emit syslog to VLAgent.

    !!! note

        VictoriaLogs is enabled and sized through the telemetry input config; component layout and TLS are generated. Modify inputs and re-run.

## Telemetry failover delay after Kubernetes worker node failure

???+ note "Symptom"

    When a Kubernetes worker node fails, affected telemetry services take time to fail over to available worker nodes.

??? note "Resolution"

    No manual intervention is required. Wait for the telemetry services to recover and fail over automatically. Do not restart pods or nodes during this period, as it may extend recovery time.

!!! info

    - [Setup Telemetry](../HowTo/Telemetry/setup_telemetry.md) -- Telemetry pipeline setup.
    - [Verify Telemetry](../HowTo/Telemetry/verify_telemetry.md) -- Verification procedures.
    - [Log Management](../Operations/log_management.md) -- Log locations for telemetry services.
