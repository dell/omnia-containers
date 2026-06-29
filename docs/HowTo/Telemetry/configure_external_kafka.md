
# Configure External Kafka


Replace Omnia's built-in Kafka deployment with an external Kafka cluster for
telemetry data streaming.

## Overview


By default, Omnia deploys a single-node Kafka instance on the K8s service
cluster. For production environments with high metric volumes or existing
Kafka infrastructure, you can configure Omnia to use an external Kafka cluster.

Benefits of external Kafka:

- Higher throughput and replication for fault tolerance.
- Integration with existing data pipelines.
- Centralized message broker management.


## Prerequisites


- An external Kafka cluster (version 3.x or later) is operational and
  accessible from the K8s service cluster.
- Kafka topics for telemetry are created (or auto-create is enabled).
- Network connectivity between the OIM, K8s cluster, and the Kafka brokers.
- The [Setup Telemetry](setup_telemetry.md) procedure has been reviewed (understand the
  default telemetry architecture).


## Procedure


1. **Enter the omnia_core container**:

   ```bash title="Run on: OIM host"
   ssh omnia_core
   ```


2. **Configure external Kafka** in `omnia_config.yml`:

   ```bash title="Run on: omnia_core container"
   vi /opt/omnia/input/project_default/omnia_config.yml
   ```


   ```yaml title="File: /opt/omnia/input/project_default/omnia_config.yml"
   ---
   # External Kafka configuration
   kafka_external: true
   kafka_bootstrap_servers: "kafka-broker1.example.com:9092,kafka-broker2.example.com:9092,kafka-broker3.example.com:9092"
   kafka_telemetry_topic: "omnia-telemetry"
   kafka_idrac_topic: "omnia-idrac"
   kafka_ldms_topic: "omnia-ldms"

   # Optional: Kafka authentication
   kafka_security_protocol: "SASL_PLAINTEXT"  # or "PLAINTEXT", "SSL", "SASL_SSL"
   kafka_sasl_mechanism: "PLAIN"
   kafka_sasl_username: "omnia-telemetry"
   kafka_sasl_password: ""  # Set via credentials utility
   ```


3. **Create the required Kafka topics** on the external cluster (if auto-create
   is disabled):

   ```bash title="Run on: external Kafka broker"
   kafka-topics.sh --create \
     --bootstrap-server localhost:9092 \
     --topic omnia-telemetry \
     --partitions 6 \
     --replication-factor 3

   kafka-topics.sh --create \
     --bootstrap-server localhost:9092 \
     --topic omnia-idrac \
     --partitions 3 \
     --replication-factor 3

   kafka-topics.sh --create \
     --bootstrap-server localhost:9092 \
     --topic omnia-ldms \
     --partitions 6 \
     --replication-factor 3
   ```


4. **Run the telemetry playbook** to reconfigure:

   ```bash title="Run on: omnia_core container"
   cd /omnia
   ansible-playbook telemetry.yml --ask-vault-pass
   ```


   The playbook will:

   - Skip deploying the built-in Kafka pod.
   - Configure iDRAC and LDMS collectors to publish to the external Kafka.
   - Configure VictoriaMetrics consumer to read from the external Kafka.


## Verification


1. **Verify Kafka connectivity** from the K8s cluster:

   ```bash title="Run on: K8s control plane node"
   kubectl run kafka-test --image=bitnami/kafka:latest --restart=Never -- \
     kafka-topics.sh --list --bootstrap-server kafka-broker1.example.com:9092
   kubectl logs kafka-test
   kubectl delete pod kafka-test
   ```


2. **Verify topics have data**:

   ```bash title="Run on: external Kafka broker"
   kafka-console-consumer.sh \
     --bootstrap-server localhost:9092 \
     --topic omnia-telemetry \
     --from-beginning \
     --max-messages 5
   ```


3. **Verify no built-in Kafka pod** is running:

   ```bash title="Run on: K8s control plane node"
   kubectl get pods -n telemetry | grep kafka
   ```


   Should show no locally deployed Kafka pods.

4. **Verify data reaches VictoriaMetrics**:

   ```bash title="Run on: K8s control plane node"
   VM_POD=$(kubectl get pod -n telemetry -l app=victoriametrics -o jsonpath='{.items[0].metadata.name}')
   kubectl exec -n telemetry $VM_POD -- curl -s "http://localhost:8428/api/v1/query?query=up"
   ```



## Next Steps


- [Configure External Victoria](configure_external_victoria.md) -- Use an external VictoriaMetrics.
- [Verify Telemetry](verify_telemetry.md) -- End-to-end verification.


## Troubleshooting


**Collectors cannot connect to Kafka**
   Verify network connectivity:

   ```bash title="Run on: K8s worker node"
   telnet kafka-broker1.example.com 9092
   ```


**SASL authentication failure**
   Verify credentials are correct in the configuration. Check Kafka broker
   logs for authentication errors.

**Data not appearing in topics**
   Check collector logs:

   ```bash title="Run on: K8s control plane node"
   kubectl logs -n telemetry -l app=idrac-collector --tail=30
   kubectl logs -n telemetry -l app=ldms-aggregator --tail=30
   ```


**Consumer lag is high**
   Check consumer group status:

   ```bash title="Run on: external Kafka broker"
   kafka-consumer-groups.sh \
     --bootstrap-server localhost:9092 \
     --group omnia-victoria-consumer \
     --describe
   ```
