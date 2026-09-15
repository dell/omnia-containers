
# Verify VAST Telemetry

## Overview

This page provides verification steps for the VAST telemetry data flow to VictoriaMetrics and VictoriaLogs.

## Prerequisites


- The [Configure VAST Telemetry](configure_vast.md) procedure is complete.
- The service Kubernetes cluster is running with telemetry pods deployed.


## Verify VAST Telemetry Pods

1. Verify that the VictoriaMetrics pods are running:

    ```bash title="Run on K8s control plane"
    kubectl get pods -n telemetry -o wide | grep vm
    ```

    ![VictoriaMetrics Pods](../../assets/images/vast_telemetry_1.png)

2. Verify that the VictoriaMetrics service is running:

    ```bash title="Run on K8s control plane"
    kubectl get service -n telemetry -o wide | grep vm
    ```

    ![VictoriaMetrics Service](../../assets/images/vast_telemetry_2.png)
    ![VictoriaMetrics Service Detail](../../assets/images/vast_telemetry_3.png)

3. Verify VMagent logs for VAST scraping to view recent logs:

    ```bash title="Run on K8s control plane"
    VMAGENT_POD=$(kubectl get pods -n telemetry -l app.kubernetes.io/name=vmagent -o jsonpath='{.items[0].metadata.name}')
    kubectl logs $VMAGENT_POD -n telemetry -c vmagent --tail=10
    ```

    ![VMAgent VAST Logs](../../assets/images/vast_telemetry_4.png)


## View VAST Metrics in VictoriaMetrics UI (VMUI)

Use the VMUI to validate that VAST telemetry data is being collected.

1. Note the **External IP** and **port number** of the VictoriaMetrics service:

    ```bash title="Run on K8s control plane"
    kubectl get svc -n telemetry | grep vmselect
    ```

    ![vmselect Service](../../assets/images/vast_telemetry_5.png)

2. Access the VMUI in a web browser:

    ```
    https://<external vmselect loadbalancer IP>:8481/select/0/vmui
    ```

    ![VMUI for VAST](../../assets/images/vast_telemetry_7.png)

## View VAST Logs in VictoriaLogs

1. Retrieve the VLAgent LoadBalancer IP and configure it on the VAST appliance:

    ```bash title="Run on K8s control plane"
    kubectl get svc -n telemetry | grep -E "(vlagent|victoria-logs)"
    ```

    ![VLAgent Service](../../assets/images/view_vast_logs_1.png)

2. Retrieve the external IP and port of the vlselect service:

    ```bash title="Run on K8s control plane"
    kubectl get svc -n telemetry | grep vlselect
    ```

    ![vlselect Service](../../assets/images/view_vast_logs_3.png)

3. Access the VictoriaLogs UI in a web browser:

    ```
    https://<external vlselect loadbalancer IP>:9471/select/vmui
    ```

    ![VAST Logs in VictoriaLogs](../../assets/images/view_vast_logs_4.png)
