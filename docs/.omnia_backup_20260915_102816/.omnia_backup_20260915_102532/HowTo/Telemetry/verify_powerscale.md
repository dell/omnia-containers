
# Verify PowerScale Telemetry

## Overview

This page provides verification steps for the PowerScale telemetry data flow to VictoriaMetrics and VictoriaLogs.

## Prerequisites


- The [Configure PowerScale Telemetry](configure_powerscale.md) procedure is complete.
- The service Kubernetes cluster is running with telemetry pods deployed.


## Verify PowerScale Telemetry Pods

1. Verify that the VictoriaMetrics pods are running:

    ```bash title="Run on K8s control plane"
    kubectl get pods -n telemetry -o wide | grep vm
    ```

    ![VictoriaMetrics Pods](../../assets/images/victoria_metrics_pod_cluster_mode.png)

2. Verify that the VictoriaMetrics service is running:

    ```bash title="Run on K8s control plane"
    kubectl get service -n telemetry -o wide | grep vm
    ```

    ![VictoriaMetrics Service](../../assets/images/victoria_metrics_service_cluster.png)


## View PowerScale Metrics in VictoriaMetrics UI (VMUI)

Use the VMUI to validate that PowerScale telemetry data is being collected and stored successfully.

1. Note the **External IP** and **port number** of the VictoriaMetrics service.

2. Access the VMUI in a web browser:

    ```
    https://<external vmselect loadbalancer IP>:8481/select/0/vmui
    ```

3. Filter and view telemetry metrics using queries in VMUI. For example, the following query displays detailed PowerScale metrics for each hardware component:

    ```
    {__name__=~"powerscale"}
    ```

    ![PowerScale Metrics in VMUI](../../assets/images/powerscale_metrics_vmui_cluster.png)

## View PowerScale Logs in VictoriaLogs

Use the VictoriaLogs UI to validate that PowerScale log data is being collected.

1. Verify that the VictoriaLogs pods are running:

    ```bash title="Run on K8s control plane"
    kubectl get pods -n telemetry -o wide | grep vl
    ```

    ![VictoriaLogs Pods](../../assets/images/victoria_logs_pod_cluster_mode.png)

2. Verify that the VictoriaLogs service is running:

    ```bash title="Run on K8s control plane"
    kubectl get service -n telemetry -o wide | grep vl
    ```

    ![VictoriaLogs Service](../../assets/images/victoria_logs_service_cluster.png)

3. Note the **External IP** and **port number** of the VictoriaLogs service.

4. Access the VictoriaLogs UI in a web browser:

    ```
    https://<external vlselect loadbalancer IP>:9471/select/vmui
    ```

5. Filter and view PowerScale logs using queries in VictoriaLogs UI. For example, use the `*` query to display all logs.

    ![PowerScale Logs in VictoriaLogs UI](../../assets/images/powerscale_logs_vlui_cluster.png)
