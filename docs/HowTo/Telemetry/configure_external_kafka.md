# Collect Telemetry Data from External Clients to Kafka


Stream telemetry data from external client nodes to the Omnia Kafka pipeline in the Service Kubernetes cluster using mutual TLS (mTLS).

## Overview


This procedure describes how to collect telemetry data from external client nodes and stream it to Kafka deployed in the Service Kubernetes cluster. External clients authenticate with the Kafka broker using mutual TLS (mTLS) certificates.


## Prerequisites


This is a post-deployment procedure. The Omnia telemetry stack (including Kafka)
must already be deployed and running before you connect external clients.

- The cluster is deployed and the telemetry stack is running. See
  [Deploy the Telemetry Stack](deploy_telemetry.md).
- `pod_external_ip_range` is set in `omnia_config.yml` so MetalLB can assign an
  external IP to the Kafka mTLS listener.
- Kafka is deployed and operational in the telemetry namespace (enable a Kafka-
  backed telemetry source, such as iDRAC, LDMS, or OME, before deployment).


## Procedure


### Step 1: Create a Kafka Topic (Optional)

If you need a custom topic for your external data, create it from the Omnia Core Container:

```bash title="Run on omnia_core container"
curl -s -X POST "http://$KAFKA_LB_IP:8080/topics/<topic-name>" \
  -H 'content-type: application/vnd.kafka.v2+json' \
  -d '{
      "partitions": [{"partition": 0}],
      "configs": {"retention.ms": "604800000"}
  }'
```

### Step 2: Extract Kafka Connection Details and TLS Certificates

1. Log in to the Service Kubernetes control plane.

2. Extract the Kafka LoadBalancer external IP:

    ```bash title="Run on K8s control plane"
    kubectl get svc -n telemetry | grep kafka
    ```

    Note the **External IP** of the Kafka LoadBalancer service (port 9094 for mTLS connections).

3. Extract the TLS certificates:

    ```bash title="Run on K8s control plane"
    kubectl get secret -n telemetry kafka-external-tls -o jsonpath='{.data.ca\.crt}' | base64 --decode > ca.crt
    kubectl get secret -n telemetry kafka-external-tls -o jsonpath='{.data.user\.crt}' | base64 --decode > user.crt
    kubectl get secret -n telemetry kafka-external-tls -o jsonpath='{.data.user\.key}' | base64 --decode > user.key
    ```

### Step 3: Create Client Certificate in .pfx Format (Optional)

If the external client requires a `.pfx` format certificate:

```bash title="Run on K8s control plane"
openssl pkcs12 -export -in user.crt -inkey user.key -certfile ca.crt -out client.pfx -password pass:<password>
```

### Step 4: Create Java Truststore and Keystore (Optional)

If the external client is a Java application (e.g., Kafka console consumer/producer):

```bash title="Run on K8s control plane"
keytool -import -trustcacerts -alias kafka-ca -file ca.crt -keystore truststore.jks -storepass <password> -noprompt
openssl pkcs12 -export -in user.crt -inkey user.key -certfile ca.crt -out user.p12 -password pass:<password>
keytool -importkeystore -srckeystore user.p12 -srcstoretype PKCS12 -srcstorepass <password> -destkeystore keystore.jks -deststoretype JKS -deststorepass <password>
```

### Step 5: Create Kafka Client SSL Configuration File

Create a properties file for the Kafka client:

```properties title="File: client-ssl.properties"
security.protocol=SSL
ssl.truststore.location=/path/to/truststore.jks
ssl.truststore.password=<password>
ssl.keystore.location=/path/to/keystore.jks
ssl.keystore.password=<password>
ssl.key.password=<password>
```

### Step 6: Produce Telemetry Data

Use the Kafka console producer to send test data to the Kafka broker:

```bash title="Run on external client node"
kafka-console-producer.sh --bootstrap-server <kafka-external-ip>:9094 \
  --topic <topic-name> \
  --producer.config client-ssl.properties
```

Type messages and press Enter to send each one.

### Step 7: Verify Telemetry Data

Use the Kafka console consumer to verify that the data was received:

```bash title="Run on external client node"
kafka-console-consumer.sh --bootstrap-server <kafka-external-ip>:9094 \
  --topic <topic-name> \
  --from-beginning \
  --consumer.config client-ssl.properties
```


## Next Steps


- [Configure OpenManage Enterprise Telemetry (OME)](telemetry_from_ome.md) -- Integrate OME with Kafka using mTLS.
- [Setup Telemetry](setup_telemetry.md) -- Overview of all telemetry sources.
