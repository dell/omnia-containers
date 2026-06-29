
# Configure External VictoriaMetrics


Replace Omnia's built-in VictoriaMetrics deployment with an external
VictoriaMetrics instance for telemetry data storage.

## Overview


For organizations with existing monitoring infrastructure or requirements for
a dedicated time-series database, Omnia can be configured to write telemetry
data to an external VictoriaMetrics instance instead of deploying one on the
K8s service cluster.

Benefits:

- Centralized metric storage across multiple clusters.
- Dedicated compute and storage resources for time-series data.
- Integration with existing Grafana instances and alerting rules.


## Prerequisites


- An external VictoriaMetrics instance (single-node or cluster mode) is
  operational and accessible.
- The VictoriaMetrics write endpoint (`/api/v1/write`) is reachable from
  the K8s service cluster.
- The [Setup Telemetry](setup_telemetry.md) procedure has been reviewed.


## Procedure


1. **Enter the omnia_core container**:

   ```bash title="Run on: OIM host"
   ssh omnia_core
   ```


2. **Configure external VictoriaMetrics** in `omnia_config.yml`:

   ```bash title="Run on: omnia_core container"
   vi /opt/omnia/input/project_default/omnia_config.yml
   ```


   ```yaml title="File: /opt/omnia/input/project_default/omnia_config.yml"
   ---
   # External VictoriaMetrics configuration
   victoriametrics_external: true
   victoriametrics_write_url: "http://victoria.example.com:8428/api/v1/write"
   victoriametrics_read_url: "http://victoria.example.com:8428"

   # Optional: authentication
   victoriametrics_auth_enabled: false
   victoriametrics_username: ""
   victoriametrics_password: ""

   # Optional: custom labels added to all metrics
   victoriametrics_extra_labels:
     cluster: "omnia-prod"
     datacenter: "dc1"
   ```


3. **Verify connectivity** to the external VictoriaMetrics:

   ```bash title="Run on: K8s control plane node"
   curl -s http://victoria.example.com:8428/api/v1/status/tsdb
   ```


   Expected: JSON response with database statistics.

4. **Run the telemetry playbook** to reconfigure:

   ```bash title="Run on: omnia_core container"
   cd /omnia
   ansible-playbook telemetry.yml --ask-vault-pass
   ```


   The playbook will:

   - Skip deploying the built-in VictoriaMetrics pod.
   - Configure Kafka consumers to write to the external VictoriaMetrics.
   - Update Grafana data source to point to the external instance.

5. **Update Grafana data source** (if not automatically configured):

   ```bash title="Run on: K8s control plane node"
   GRAFANA_POD=$(kubectl get pod -n telemetry -l app=grafana -o jsonpath='{.items[0].metadata.name}')
   kubectl exec -n telemetry $GRAFANA_POD -- \
     curl -s -X POST http://localhost:3000/api/datasources \
       -H "Content-Type: application/json" \
       -u admin:YourGrafanaPassword \
       -d '{
         "name": "VictoriaMetrics External",
         "type": "prometheus",
         "url": "http://victoria.example.com:8428",
         "access": "proxy",
         "isDefault": true
       }'
   ```



## Verification


1. **Verify data is being written** to the external VictoriaMetrics:

   ```bash title="Run on: any node with curl"
   curl -s "http://victoria.example.com:8428/api/v1/query?query=up" | python3 -m json.tool
   ```


2. **Check metric count** on the external instance:

   ```bash title="Run on: any node with curl"
   curl -s "http://victoria.example.com:8428/api/v1/status/tsdb" | python3 -m json.tool
   ```


3. **Verify no built-in VictoriaMetrics pod** is running:

   ```bash title="Run on: K8s control plane node"
   kubectl get pods -n telemetry | grep victoriametrics
   ```


4. **Verify Grafana dashboards** show data from the external instance by
   opening the Grafana web UI and checking the data source configuration.


## Next Steps


- [Verify Telemetry](verify_telemetry.md) -- End-to-end telemetry verification.
- [Telemetry From Ome](telemetry_from_ome.md) -- Add OME telemetry to the external instance.


## Troubleshooting


**Write endpoint returns 403 or 401**
   Verify authentication credentials are correct:

   ```bash title="Run on: K8s control plane node"
   curl -s -u user:password \
     "http://victoria.example.com:8428/api/v1/query?query=up"
   ```


**Connection timeout to external VictoriaMetrics**
   Check network connectivity and firewall rules:

   ```bash title="Run on: K8s worker node"
   curl -v http://victoria.example.com:8428/health
   ```


**Grafana shows "No data" with external source**
   - Verify the data source URL in Grafana settings.
   - Check that the external VictoriaMetrics is receiving data:

     ```bash title="Run on: any node"
     curl -s "http://victoria.example.com:8428/api/v1/series?match[]={cluster='omnia-prod'}"
     ```


**Metrics have wrong labels**
   Check the `victoriametrics_extra_labels` configuration in
   `omnia_config.yml`.
