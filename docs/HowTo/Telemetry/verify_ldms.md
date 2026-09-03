
# Verify LDMS Telemetry

## Overview

This page provides verification steps for the LDMS telemetry data flow from Kafka.

## Prerequisites


- The [Configure LDMS Telemetry](configure_ldms.md) procedure is complete.
- The service Kubernetes cluster is running with telemetry pods deployed.


## Verify LDMS Messages in Kafka

To verify that LDMS telemetry data is being successfully published to the `ldms` Kafka topic:

1. Log in to the Service Kubernetes control plane.

2. Set the required variables:

    ```bash title="Run on K8s control plane"
    KAFKA_LB_IP=<external IP of bridge-bridge-lb service>
    TOPIC=ldms
    GROUP=ldms-consumer-group
    INSTANCE=ldms-consumer-1
    ```

3. Create a Kafka consumer:

    ```bash title="Run on K8s control plane"
    curl -X POST http://$KAFKA_LB_IP:8080/consumers/ldms-consumer-group \
    -H 'content-type: application/vnd.kafka.v2+json' \
    -d '{
            "name": "ldms-consumer-1",
            "format": "json",
            "auto.offset.reset": "latest",
            "enable.auto.commit": true
        }'
    ```

4. View the list of LDMS Kafka topics configured:

    ```bash title="Run on K8s control plane"
    curl -s -X GET "http://$KAFKA_LB_IP:8080/topics" | jq '.'
    ```

5. Subscribe the consumer to the LDMS topic:

    ```bash title="Run on K8s control plane"
    curl -X POST http://$KAFKA_LB_IP:8080/consumers/ldms-consumer-group/instances/ldms-consumer-1/subscription \
    -H 'content-type: application/vnd.kafka.v2+json' \
    -d '{"topics": ["ldms"]}'
    ```

6. Consume messages from the topic:

    ```bash title="Run on K8s control plane"
    while true; do curl -X GET http://$KAFKA_LB_IP:8080/consumers/ldms-consumer-group/instances/ldms-consumer-1/records \
    -H 'accept: application/vnd.kafka.json.v2+json' | jq '.' ;  sleep 2; done
    ```

If telemetry is flowing correctly, the output contains JSON-formatted LDMS telemetry records.

!!! note

    When new nodes are added, ensure the nodes are up and cloud-init has completed successfully (check `/var/log/cloud-init-output.log` on each node). Then, create a new Kafka consumer group with a unique name (e.g., `ldms-new-nodes-group`) to verify metrics from the newly added nodes. Wait 2-3 minutes after discovery completes before checking.

## Verify TLS Connectivity

To verify TLS connectivity for Kafka, run the Kafka TLS test job:

```bash title="Run on K8s control plane"
cd /<nfs client mount path of the service k8s cluster>/telemetry/deployments/test
kubectl apply -f kafka.tls_test_job.yaml
```

After the job completes, check the logs to confirm that the TLS connection is successful:

```bash title="Run on K8s control plane"
kubectl logs kafka-tls-test-xxx -n telemetry
```


## View LDMS Metrics in VictoriaMetrics UI (VMUI)

LDMS metrics are routed to VictoriaMetrics via the Vector-LDMS pipeline. For VMUI verification steps, see [Verify Vector-LDMS Pipeline](verify_vector_ldms.md).




















