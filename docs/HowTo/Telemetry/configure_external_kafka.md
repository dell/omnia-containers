# Collect Telemetry Data from External Clients to Kafka

Connect an external Telemetry producer to the Kafka cluster deployed in the
Service Kubernetes cluster.

## Overview

External clients send Telemetry data to the Strimzi Kafka cluster in the
`telemetry` namespace through its native LoadBalancer endpoint. The connection
uses mutual TLS (mTLS). The `external_kafka` utility validates the Kafka
deployment and exports the project-specific endpoint, HTTP Bridge endpoint,
cluster CA certificate, and client credentials.

## Prerequisites

- Deploy Kafka through the Telemetry workflow.
- Ensure the Kafka pods in the `telemetry` namespace are Running and Ready.
- Ensure the `kafka-kafka-external-bootstrap` and `bridge-bridge-lb` services
  have LoadBalancer external IP addresses.
- Ensure the external client can reach the native Kafka LoadBalancer port.
- Ensure the OIM can reach the Kubernetes VIP over root SSH.
- Export `OMNIA_DATA_PATH` and `OMNIA_PROJECT_NAME` for the project whose
  connection details must be retrieved.
- Install OpenSSL, Java `keytool`, and Kafka command-line tools on the external
  client, or make them available in a container.

## Procedure

1. Optional: create a Kafka topic for the external producer. Save the following
   manifest as
   `$OMNIA_DATA_PATH/telemetry/input/$OMNIA_PROJECT_NAME/external-kafka-topic.yml`:

    ```yaml
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

    Apply and verify the topic from the Kubernetes control plane:

    ```bash title="Run on: Kubernetes control plane"
    kubectl apply -f "$OMNIA_DATA_PATH/telemetry/input/$OMNIA_PROJECT_NAME/external-kafka-topic.yml"
    kubectl get kafkatopics -n telemetry
    ```

2. Retrieve the Kafka connection details. Choose one execution method; do not
   run both commands for the same operation.

    === "Using omnia.sh (recommended)"

        ```bash title="Run on: OIM"
        cd src/main
        ./omnia.sh --run telemetry --tags external_kafka
        ```

    === "Using ansible-playbook"

        ```bash title="Run on: OIM"
        source "$OMNIA_DATA_PATH/activate-omnia.sh"
        cd <OMNIA_SOURCE_PATH>/src/telemetry/playbooks
        ansible-playbook telemetry.yml --tags external_kafka
        ```

3. Review the project-specific output:

    ```text
    $OMNIA_DATA_PATH/telemetry/output/$OMNIA_PROJECT_NAME/external_kafka/
    |-- ca.crt
    |-- user.crt
    |-- user.key
    `-- external_kafka_connect_details.yml
    ```

    Use `kafka.bootstrap_server` for a native Kafka client and
    `kafka.bridge.endpoint` for an HTTP client. In a multi-domain environment,
    always use the output below the applicable `OMNIA_PROJECT_NAME`.

4. If the external application requires a PKCS#12 certificate, create it in
   the project output directory:

    ```bash title="Run on: OIM"
    KAFKA_OUTPUT_DIR="$OMNIA_DATA_PATH/telemetry/output/$OMNIA_PROJECT_NAME/external_kafka"
    cd "$KAFKA_OUTPUT_DIR"
    openssl pkcs12 -export -out user.pfx -inkey user.key -in user.crt
    ```

    Each export run removes and recreates the `external_kafka` directory.
    Generate `user.pfx` after the final export and copy it to a secure location
    before rerunning the utility.

5. Optional: create Java truststore and keystore files for Kafka
   command-line tools. Replace the example passwords before production use.

    ```bash title="Run on: external Kafka client"
    cd /opt/omnia/telemetry/external_kafka/

    keytool -import -trustcacerts -alias kafka-ca -file ca.crt \
      -keystore kafka.truststore.jks -storepass changeit -noprompt

    openssl pkcs12 -export -in user.crt -inkey user.key \
      -out kafkapump.p12 -name kafkapump -password pass:changeit

    keytool -importkeystore \
      -srckeystore kafkapump.p12 -srcstoretype PKCS12 -srcstorepass changeit \
      -destkeystore kafka.keystore.jks -deststorepass changeit -noprompt
    ```

6. Create `producer-mtls.properties` in `KAFKA_OUTPUT_DIR`. The `/certs`
   paths assume that this directory is mounted at `/certs` in a Kafka tools
   container:

    ```properties
    security.protocol=SSL
    ssl.truststore.location=/certs/kafka.truststore.jks
    ssl.truststore.password=changeit
    ssl.keystore.location=/certs/kafka.keystore.jks
    ssl.keystore.password=changeit
    ssl.key.password=changeit
    ```

7. Mount the project output directory in a Kafka tools container, if the
   external host does not have Kafka command-line tools:

    ```bash title="Run on: external Kafka client"
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

## Troubleshooting

- **No Kafka pods are found:** Deploy a source that targets Kafka and rerun the
  Telemetry deployment.
- **Kafka pods are not Running or Ready:** Inspect them with
  `kubectl get pods -n telemetry -l app.kubernetes.io/name=kafka`.
- **An endpoint is empty:** Ensure both Kafka LoadBalancer services have an
  external IP address and service port.
- **TLS validation fails:** Recreate the keystore and truststore from the files
  in the current project's export directory and verify their passwords.
- **The VIP cannot be reached:** Restore root SSH access from the OIM to the
  configured Kubernetes VIP.

## Next steps

- Use the exported native endpoint and certificates to
  [configure OME](telemetry_from_ome.md).
- Protect `user.key`, `user.pfx`, and the Java keystore as client credentials.
