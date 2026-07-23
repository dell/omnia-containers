# Collect Telemetry Data from External Clients to Kafka


Stream telemetry data from external client nodes to the Omnia Kafka pipeline in the Service Kubernetes cluster using mutual TLS (mTLS).

## Overview


This procedure describes how to collect telemetry data from external client nodes and stream it to Kafka deployed in the Service Kubernetes cluster. Kafka is deployed via Strimzi in the `telemetry` namespace. External clients authenticate with the Kafka broker using mutual TLS (mTLS) certificates.


## Prerequisites


This is a post-deployment procedure. The Omnia telemetry stack (including Kafka)
must already be deployed and running before you connect external clients.

- A Service Kubernetes cluster is running with Kafka deployed via Strimzi in the `telemetry` namespace.
- External access to Kafka is available through a LoadBalancer on port `9094`.
- `pod_external_ip_range` is set in `omnia_config.yml` so MetalLB can assign an
  external IP to the Kafka mTLS listener.
- Kafka is deployed and operational in the telemetry namespace (enable a Kafka-
  backed telemetry source, such as iDRAC, LDMS, or OME, before deployment).
- A Kafka Pump is available outside the Service Kubernetes cluster, deployed as a container using Kubernetes, Podman, or Docker.


## Procedure


### Step 1: Create a Kafka Topic (Optional)

On the Service Kubernetes cluster, create a `KafkaTopic` resource using the Strimzi CRD:

1. Create a file named `kafka.<topic_name>.yaml`:

    ```yaml title="File: kafka.<topic_name>.yaml"
    apiVersion: kafka.strimzi.io/v1beta2
    kind: KafkaTopic
    metadata:
      name: my-new-topic
      namespace: telemetry
      labels:
        strimzi.io/cluster: kafka
    spec:
      partitions: 3
      replicas: 3
      topicName: my-new-topic
    ```

    Replace `my-new-topic` with the desired Kafka topic name.

2. Apply the topic configuration file on the Service Kube Control Plane node:

    ```bash title="Run on K8s control plane"
    kubectl apply -f kafka.<topic_name>.yaml
    ```

3. Verify that the topic was created:

    ```bash title="Run on K8s control plane"
    kubectl get kafkatopics -n telemetry
    ```

### Step 2: Extract Kafka Connection Details and TLS Certificates

Run the following playbook to retrieve the Kafka connection details and TLS certificates from the Service Kubernetes cluster:

```bash title="Run on omnia_core container"
cd /omnia/utils
ansible-playbook external_kafka_connect_details.yml
```

The `external_kafka_connect_details.yml` playbook does the following:

- Retrieves the Kafka LoadBalancer external IP.
- Extracts the server CA certificate and client certificates/keys from the `telemetry` namespace.
- Writes the Kafka endpoint and TLS file locations to `/opt/omnia/telemetry/external_kafka_connect_details.yml`.
- Saves the TLS files in `/opt/omnia/telemetry/external_kafka/`:
    - `ca.crt` (server certificate)
    - `user.crt` (client certificate)
    - `user.key` (client key)

### Step 3: Create Client Certificate in .pfx Format

Create a client certificate in `.pfx` format for mTLS by running the following command. Provide a passphrase when prompted:

```bash title="Run on omnia_core container"
cd /opt/omnia/telemetry/external_kafka/
openssl pkcs12 -export -out user.pfx -inkey user.key -in user.crt
```

!!! note

    For [OpenManage Enterprise](https://www.dell.com/en-in/lp/dt/open-manage-enterprise){target="_blank"} Kafka client, the client certificate must be in `.pfx` format. To configure OpenManage Enterprise to stream telemetry data to Kafka, see [Collect Telemetry Data from OpenManage Enterprise](telemetry_from_ome.md).

### Step 4: Create Java Truststore and Keystore (Optional)

The steps for converting certificates into JKS format are required only for Java-based Kafka clients. If your client does not use a Java keystore (JKS), these conversion steps are not necessary.

```bash title="Run on omnia_core container"
cd /opt/omnia/telemetry/external_kafka/

keytool -import -trustcacerts -alias kafka-ca -file ca.crt \
  -keystore kafka.truststore.jks -storepass changeit -noprompt

openssl pkcs12 -export -in user.crt -inkey user.key \
  -out kafkapump.p12 -name kafkapump -password pass:changeit

keytool -importkeystore \
  -srckeystore kafkapump.p12 -srcstoretype PKCS12 -srcstorepass changeit \
  -destkeystore kafka.keystore.jks -deststorepass changeit -noprompt
```

### Step 5: Create Kafka Client SSL Configuration File

Create a properties file for the Kafka client:

```properties title="File: producer-mtls.properties"
security.protocol=SSL
ssl.truststore.location=/certs/kafka.truststore.jks
ssl.truststore.password=changeit
ssl.keystore.location=/certs/kafka.keystore.jks
ssl.keystore.password=changeit
ssl.key.password=changeit
ssl.endpoint.identification.algorithm=
```

### Step 6: Run a Kafka Tools Container

Run a Kafka tools container with certificates mounted:

```bash title="Run on omnia_core container or external client"
podman run -it --rm \
  --name kafka-mtls-producer \
  -v ~/kafka-mtls-test:/certs:Z \
  apache/kafka:4.1.0 bash
```

## Verification


### Verify Telemetry Data in Kafka

1. To verify the available Kafka topics, run the following command:

    ```bash title="Run inside Kafka tools container"
    KAFKA_LB_IP=<external load balancer IP of the bridge-bridge-lb service>
    /opt/kafka/bin/kafka-topics.sh \
      --bootstrap-server $KAFKA_LB_IP:9094 \
      --command-config /certs/producer-mtls.properties \
      --list
    ```

2. Inside the Kafka tools container, produce test data to the Kafka topic:

    ```bash title="Run inside Kafka tools container"
    /opt/kafka/bin/kafka-console-producer.sh \
      --bootstrap-server $KAFKA_LB_IP:9094 \
      --topic <kafka topic> \
      --producer.config /certs/producer-mtls.properties
    ```

    Type messages and press Enter after each. Sample data:

    ```text
    {"device_id": "xyz-001", "metric": "power", "value": 250, "timestamp": "2024-11-18T10:25:00Z"}
    {"device_id": "xyz-002", "metric": "temperature", "value": 25.5, "timestamp": "2024-11-18T10:25:10Z"}
    {"device_id": "xyz-003", "metric": "fan_speed", "value": 4500, "timestamp": "2024-11-18T10:25:20Z"}
    ```

    Press `Ctrl+D` to exit.

3. In a new terminal, verify if the messages are received:

    ```bash title="Run inside Kafka tools container"
    /opt/kafka/bin/kafka-console-consumer.sh \
      --bootstrap-server $KAFKA_LB_IP:9094 \
      --consumer.config /certs/producer-mtls.properties \
      --topic <kafka topic> \
      --group <kafka topic>-consumer-group \
      --from-beginning
    ```

    You can view the messages in JSON format.


## Next Steps


- [Configure OpenManage Enterprise Telemetry (OME)](telemetry_from_ome.md) -- Integrate OME with Kafka using mTLS.
- [Setup Telemetry](setup_telemetry.md) -- Overview of all telemetry sources.
