
# Verify Telemetry


Perform an end-to-end verification of the Omnia telemetry pipeline from data
collection through storage to visualization.

## Overview


A complete telemetry verification traces the data flow through every stage:

1. **Collection** -- iDRAC collectors and LDMS samplers are generating metrics.
2. **Transport** -- Kafka topics are receiving messages.
3. **Storage** -- VictoriaMetrics is ingesting and storing time-series data.
4. **Visualization** -- Grafana dashboards display live data.


## Prerequisites


- The [Setup Telemetry](setup_telemetry.md) procedure is complete.
- The K8s service cluster is running with telemetry pods.
- LDMS agents are deployed on compute nodes.
- Grafana is accessible via the browser.


## Procedure


### Stage 1: Verify Collection


1. **Check iDRAC collector** is retrieving metrics:

   ```bash title="Run on: K8s control plane node"
   kubectl logs -n telemetry -l app=idrac-collector --tail=10
   ```


   Look for successful metric retrieval messages.

2. **Check LDMS samplers** are running on compute nodes:

   ```bash title="Run on: omnia_core container"
   ansible slurm_node -m shell -a "systemctl is-active ldmsd"
   ```


3. **Query LDMS metrics** locally on a compute node:

   ```bash title="Run on: compute node"
   ldms_ls -h localhost -p 411 -v
   ```


   Should list active metric sets.


### Stage 2: Verify Transport (Kafka)


4. **List Kafka topics**:

   ```bash title="Run on: K8s control plane node"
   KAFKA_POD=$(kubectl get pod -n telemetry -l app=kafka -o jsonpath='{.items[0].metadata.name}')
   kubectl exec -n telemetry $KAFKA_POD -- kafka-topics.sh --list --bootstrap-server localhost:9092
   ```


5. **Check topic message counts**:

   ```bash title="Run on: K8s control plane node"
   kubectl exec -n telemetry $KAFKA_POD -- kafka-run-class.sh kafka.tools.GetOffsetShell \
     --broker-list localhost:9092 --topic omnia-telemetry
   ```


   Message offsets should be increasing.

6. **Read sample messages** from a topic:

   ```bash title="Run on: K8s control plane node"
   kubectl exec -n telemetry $KAFKA_POD -- kafka-console-consumer.sh \
     --bootstrap-server localhost:9092 \
     --topic omnia-telemetry \
     --from-beginning \
     --max-messages 3
   ```



### Stage 3: Verify Storage (VictoriaMetrics)


7. **Check VictoriaMetrics health**:

   ```bash title="Run on: K8s control plane node"
   VM_POD=$(kubectl get pod -n telemetry -l app=victoriametrics -o jsonpath='{.items[0].metadata.name}')
   kubectl exec -n telemetry $VM_POD -- curl -s http://localhost:8428/health
   ```


   Expected: `OK`

8. **Query stored metrics**:

   ```bash title="Run on: K8s control plane node"
   kubectl exec -n telemetry $VM_POD -- \
     curl -s "http://localhost:8428/api/v1/query?query=up" | python3 -m json.tool
   ```


9. **Check active time series count**:

   ```bash title="Run on: K8s control plane node"
   kubectl exec -n telemetry $VM_POD -- \
     curl -s "http://localhost:8428/api/v1/status/tsdb" | python3 -c "
   import sys, json
   data = json.load(sys.stdin)
   print(f'Active time series: {data.get(\"data\", {}).get(\"totalSeries\", \"unknown\")}')
   "
   ```


10. **Query a specific metric** (e.g., iDRAC temperature):

    ```bash title="Run on: K8s control plane node"
    kubectl exec -n telemetry $VM_POD -- \
      curl -s "http://localhost:8428/api/v1/query?query=idrac_SystemBoardInletTemp"
    ```



### Stage 4: Verify Visualization (Grafana)


11. **Get the Grafana external IP**:

    ```bash title="Run on: K8s control plane node"
    kubectl get svc -n telemetry grafana
    ```


12. **Open Grafana** in a browser: `http://<grafana-ip>:3000`

13. **Verify data sources**:

    Navigate to **Configuration** > **Data Sources**. The VictoriaMetrics
    data source should show a green "Data source is working" indicator.

14. **Check pre-configured dashboards**:

    Navigate to **Dashboards** > **Browse**. Verify the following dashboards
    exist and show data:

    - **Cluster Overview** -- Node status, overall health
    - **iDRAC Metrics** -- Temperatures, power, fan speeds
    - **LDMS Metrics** -- CPU, memory, I/O per node
    - **Network Fabric** -- (if SFM is configured) port throughput


## Verification


Use this checklist to confirm the entire pipeline is operational:

| Stage | Check | Expected Result |
| --- | --- | --- |
| Collection | `ldms_ls -h localhost -p 411` | Active metric sets |
| Collection | iDRAC collector pod logs | Successful retrieval |
| Transport | Kafka topic list | Topics exist |
| Transport | Console consumer | Messages readable |
| Storage | `/health` endpoint | `OK` |
| Storage | `/api/v1/query?query=up` | Non-empty results |
| Visualization | Grafana data source test | Green indicator |
| Visualization | Dashboard shows graphs | Data within last hour |

## Next Steps


- [Configure Ldms](configure_ldms.md) -- Fine-tune metric collection.
- [Configure External Kafka](configure_external_kafka.md) -- Scale the transport layer.
- [Configure External Victoria](configure_external_victoria.md) -- Scale the storage layer.


## Troubleshooting


**No data at any stage**
   Start from the collection stage and trace forward:

   1. Are LDMS/iDRAC collectors running?
   2. Are Kafka topics receiving messages?
   3. Is VictoriaMetrics ingesting data?
   4. Is Grafana configured with the correct data source?

**Data gap in Grafana (intermittent)**
   - Check for pod restarts:

     ```bash title="Run on: K8s control plane node"
     kubectl get pods -n telemetry -o wide
     ```


   - Check K8s node resources (CPU/memory):

     ```bash title="Run on: K8s control plane node"
     kubectl top nodes
     kubectl top pods -n telemetry
     ```


**Metrics have stale timestamps**
   - Verify NTP is synchronized on all nodes:

     ```bash title="Run on: omnia_core container"
     ansible all -m shell -a "chronyc tracking | grep 'System time'"
     ```


**VictoriaMetrics running out of disk**
   Check retention settings and disk usage:

   ```bash title="Run on: K8s control plane node"
   kubectl exec -n telemetry $VM_POD -- df -h /victoria-metrics-data
   ```
