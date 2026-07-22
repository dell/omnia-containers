
# Verify iDRAC Telemetry

## Overview

This page provides verification steps for the iDRAC telemetry data flow from Kafka to VictoriaMetrics.

!!! note

    For the list of iDRAC telemetry metrics collected by Kafka and VictoriaMetrics, see [iDRAC Telemetry Reference Tools](https://github.com/dell/iDRAC-Telemetry-Reference-Tools).

## Prerequisites


- The [Configure iDRAC Telemetry](configure_idrac.md) procedure is complete.
- The service Kubernetes cluster is running with telemetry pods deployed.


## Verify iDRAC Telemetry Pods

1. Verify that the VictoriaMetrics pods are running:

    ```bash title="Run on K8s control plane"
    kubectl get pods -n telemetry -o wide | grep vm
    ```

    ![VictoriaMetrics Pods](../../assets/images/victoria_metrics_pod_cluster_mode.png)

2. Verify that the VictoriaMetrics service is running:

    ```bash title="Run on K8s control plane"
    kubectl get service -n telemetry | grep vm
    ```

    ![VictoriaMetrics Service](../../assets/images/victoria_metrics_service_cluster.png)


## Verify iDRAC Messages in Kafka

To verify that iDRAC telemetry data is being successfully published to the `idrac` Kafka topic:

1. Log in to the Service Kubernetes control plane.

2. Set the required variables:

    ```bash title="Run on K8s control plane"
    KAFKA_LB_IP=<external IP of bridge-bridge-lb service>
    TOPIC=idrac
    GROUP=idrac-consumer-group
    INSTANCE=idrac-consumer-1
    ```

3. Create a Kafka consumer:

    ```bash title="Run on K8s control plane"
    curl -X POST http://$KAFKA_LB_IP:8080/consumers/idrac-consumer-group \
    -H 'content-type: application/vnd.kafka.v2+json' \
    -d '{
            "name": "idrac-consumer-1",
            "format": "json",
            "auto.offset.reset": "earliest"
        }'
    ```

4. View the list of iDRAC Kafka topics configured:

    ```bash title="Run on K8s control plane"
    curl -s -X GET "http://$KAFKA_LB_IP:8080/topics" | jq '.'
    ```

5. Subscribe the consumer to the telemetry topic:

    ```bash title="Run on K8s control plane"
    curl -X POST http://$KAFKA_LB_IP:8080/consumers/idrac-consumer-group/instances/idrac-consumer-1/subscription \
    -H 'content-type: application/vnd.kafka.v2+json' \
    -d '{"topics": ["idrac"]}'
    ```

6. Consume messages from the topic:

    ```bash title="Run on K8s control plane"
    while true; do curl -X GET http://$KAFKA_LB_IP:8080/consumers/idrac-consumer-group/instances/idrac-consumer-1/records \
    -H 'accept: application/vnd.kafka.json.v2+json' | jq '.' ;  sleep 2; done
    ```

If telemetry metrics are collected correctly, the output contains JSON-formatted iDRAC telemetry records.

## Verify TLS Connectivity

**VictoriaMetrics TLS** -- Run the VictoriaMetrics TLS test job:

```bash title="Run on K8s control plane"
cd /<nfs client mount path of the service k8s cluster>/telemetry/deployments/test
kubectl apply -f victoria-tls-test-job.yaml
```

After the job completes, check the logs to confirm that the TLS connection is successful:

```bash title="Run on K8s control plane"
kubectl logs victoria-tls-test-xxx -n telemetry
```

**Kafka TLS** -- Run the Kafka TLS test job:

```bash title="Run on K8s control plane"
cd /<nfs client mount path of the service k8s cluster>/telemetry/deployments/test
kubectl apply -f kafka.tls_test_job.yaml
```

After the job completes, check the logs to confirm that the TLS connection is successful:

```bash title="Run on K8s control plane"
kubectl logs kafka-tls-test-xxx -n telemetry
```

## View iDRAC Metrics in VictoriaMetrics UI (VMUI)

Use the VMUI to validate that iDRAC telemetry data is being collected and stored successfully.

1. Note the **External IP** and **port number** of the VictoriaMetrics service.

2. Access the VMUI in a web browser:

    ```
    https://<external vmselect loadbalancer IP>:8481/select/0/vmui
    ```

3. Filter and view telemetry metrics using queries in VMUI. For example, the following `PowerEdge_TemperatureReading` query displays all available metrics:

    ![VictoriaMetrics VMUI](../../assets/images/victoria_metrics_vmui.png)


## Access the MySQL Database

After `telemetry.yml` has been executed for the service cluster, you can check the MySQL database inside the `mysqldb` container.

1. Get the names of all the telemetry pods:

    ```bash title="Run on K8s control plane"
    kubectl get pods -n telemetry -l app=idrac-telemetry
    ```

    !!! note

        The `idrac-telemetry-0` pod will always be responsible for collecting the telemetry data of the management nodes (`oim`, `service_kube_control_plane_x86_64`, `service_kube_node_x86_64`, `login_node_x86_64`, etc.).

2. Execute the following command:

    ```bash title="Run on K8s control plane"
    kubectl exec -it -n telemetry <iDRAC_telemetry_pod_name> -c mysqldb -- mysql -u <MYSQL_USER> -p
    ```

3. When prompted, enter the MySQL password to log in.

4. To enter into the `idrac_telemetry_db`:

    ```sql
    use idrac_telemetrydb;
    ```

5. To access the services table:

    ```sql
    select * from services;
    ```
