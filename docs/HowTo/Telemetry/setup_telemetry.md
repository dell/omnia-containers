
# Setup Telemetry


Deploy the Omnia telemetry pipeline using `telemetry.yml` to collect,
aggregate, and visualize hardware and OS metrics from across the cluster.

## Overview


The Omnia telemetry pipeline collects metrics from multiple sources and stores
them for visualization in Grafana. Running `telemetry.yml` deploys:

- **iDRAC Telemetry Collector** -- Collects hardware metrics (temperatures,
  power, fan speeds) from Dell iDRAC via Redfish.
- **LDMS (Lightweight Distributed Metric Service)** -- Collects OS-level
  metrics (CPU, memory, I/O) from compute nodes.
- **Kafka** -- Message broker for streaming metrics.
- **VictoriaMetrics** -- Time-series database for metric storage.
- **Grafana** -- Visualization dashboards.

The telemetry services run as pods on the Kubernetes service cluster.


## Prerequisites


- A Kubernetes service cluster is deployed (see
  [Setup Service K8S](../Kubernetes/setup_service_k8s.md)).
- The Slurm cluster is deployed (for LDMS agent deployment on compute nodes).
- `omnia_config.yml` is configured with telemetry parameters.
- iDRAC credentials are configured (see
  [Configure Credentials](../Setup/configure_credentials.md)).
- The K8s cluster has persistent storage available (NFS CSI or PowerScale CSI).


## Procedure


1. **Enter the omnia_core container**:

   ```bash title="Run on: OIM host"
   ssh omnia_core
   ```


2. **Configure telemetry parameters** in `omnia_config.yml`:

   ```bash title="Run on: omnia_core container"
   vi /opt/omnia/input/project_default/omnia_config.yml
   ```


   ```yaml title="File: /opt/omnia/input/project_default/omnia_config.yml"
   ---
   # Telemetry configuration
   enable_telemetry: true
   telemetry_collection_interval: 60  # seconds
   grafana_admin_password: ""  # Set via credentials utility

   # iDRAC telemetry
   idrac_telemetry_enabled: true
   idrac_telemetry_metrics:
     - "SystemBoardInletTemp"
     - "SystemBoardExhaustTemp"
     - "TotalPower"
     - "CPUUsage"
     - "MemoryUsage"
     - "FanSpeed"

   # LDMS configuration
   ldms_enabled: true
   ldms_samplers:
     - "meminfo"
     - "vmstat"
     - "procstat"
   ```


3. **Run the telemetry playbook**:

   ```bash title="Run on: omnia_core container"
   cd /omnia
   ansible-playbook telemetry.yml --ask-vault-pass
   ```


   The playbook performs:

   - Deploys Kafka on the K8s service cluster.
   - Deploys VictoriaMetrics for time-series storage.
   - Deploys Grafana with pre-configured dashboards.
   - Deploys the iDRAC telemetry collector.
   - Installs and configures LDMS samplers on compute nodes.
   - Installs LDMS aggregators on the K8s cluster.
   - Configures data flow: LDMS/iDRAC → Kafka → VictoriaMetrics → Grafana.

   Execution time: **15-30 minutes**.

4. **Access the Grafana dashboard**:

   ```bash title="Run on: K8s control plane node"
   kubectl get svc -n telemetry | grep grafana
   ```


   Note the external IP (from MetalLB). Open a browser and navigate to:

   `http://<grafana-external-ip>:3000`

   Default credentials:

   - Username: `admin`
   - Password: (as configured in omnia_config.yml or credentials utility)


## Verification


1. **Verify telemetry pods are running**:

   ```bash title="Run on: K8s control plane node"
   kubectl get pods -n telemetry
   ```


   Expected pods:

   ```text title="Expected output on: K8s control plane node"
   NAME                                    READY   STATUS    RESTARTS
   grafana-xxxxxxxxxx-xxxxx                1/1     Running   0
   kafka-0                                 1/1     Running   0
   victoriametrics-xxxxxxxxxx-xxxxx        1/1     Running   0
   idrac-collector-xxxxxxxxxx-xxxxx        1/1     Running   0
   ldms-aggregator-xxxxxxxxxx-xxxxx        1/1     Running   0
   ```


2. **Verify LDMS agents on compute nodes**:

   ```bash title="Run on: omnia_core container"
   ansible slurm_node -m shell -a "systemctl is-active ldmsd"
   ```


3. **Check Kafka topics** have telemetry data:

   ```bash title="Run on: K8s control plane node"
   kubectl exec -n telemetry kafka-0 -- kafka-topics.sh --list --bootstrap-server localhost:9092
   ```


4. **Verify VictoriaMetrics is receiving data**:

   ```bash title="Run on: K8s control plane node"
   VM_POD=$(kubectl get pod -n telemetry -l app=victoriametrics -o jsonpath='{.items[0].metadata.name}')
   kubectl exec -n telemetry $VM_POD -- curl -s "http://localhost:8428/api/v1/query?query=up" | python3 -m json.tool
   ```


5. **Verify Grafana dashboards** show data by opening the web UI and checking
   the pre-configured dashboards for active time-series data.


## Next Steps


- [Configure Ldms](configure_ldms.md) -- Fine-tune LDMS sampler plugins.
- [Configure External Kafka](configure_external_kafka.md) -- Use an external Kafka cluster.
- [Configure External Victoria](configure_external_victoria.md) -- Use an external VictoriaMetrics
  instance.
- [Verify Telemetry](verify_telemetry.md) -- End-to-end telemetry verification.


## Troubleshooting


**Telemetry pods stuck in Pending**
   Check for persistent volume issues:

   ```bash title="Run on: K8s control plane node"
   kubectl describe pvc -n telemetry
   ```


**iDRAC collector shows errors**
   Verify iDRAC credentials and Redfish access:

   ```bash title="Run on: K8s control plane node"
   kubectl logs -n telemetry -l app=idrac-collector --tail=30
   ```


**LDMS agents not running on compute nodes**
   Re-deploy LDMS:

   ```bash title="Run on: omnia_core container"
   ansible slurm_node -m shell -a "systemctl restart ldmsd"
   ```


**Grafana shows "No data"**
   - Verify the VictoriaMetrics data source is configured in Grafana.
   - Check the time range in Grafana (default to "Last 1 hour").
   - Verify data is flowing through Kafka:

     ```bash title="Run on: K8s control plane node"
     kubectl exec -n telemetry kafka-0 -- kafka-console-consumer.sh \
       --bootstrap-server localhost:9092 --topic telemetry --from-beginning --max-messages 5
     ```


**Kafka pod CrashLoopBackOff**
   Check disk space on the K8s worker node:

   ```bash title="Run on: K8s worker node"
   df -h
   ```
