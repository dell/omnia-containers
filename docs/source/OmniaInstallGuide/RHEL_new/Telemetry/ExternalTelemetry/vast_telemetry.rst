=======================================================
Integrate VAST Storage with Omnia Telemetry for Secure Metrics and Logs Streaming
=======================================================

This section describes how to configure VAST Storage to securely stream telemetry metrics and logs to the Service Kubernetes cluster.

This procedure assumes that VictoriaMetrics is deployed in cluster mode in the telemetry namespace of the Service Kubernetes cluster. For more information, see the `VictoriaMetrics cluster mode documentation <https://docs.victoriametrics.com/victoriametrics/cluster-victoriametrics/>`_.

Using Omnia, you can deploy VAST Telemetry to collect storage performance metrics and syslog events from VAST Storage appliances. The deployment includes configuring the VAST Telemetry components on the service Kubernetes cluster, integrating with the VAST Prometheus exporter via vmagent, and ingesting syslog events via the VLAgent pipeline.

VAST Telemetry collects storage metrics and logs. VAST Telemetry includes these components:

- **VAST Prometheus Exporter:** Exposes storage metrics on a Prometheus-compatible HTTPS endpoint (default port 443).
- **vmagent (shared):** Scrapes the VAST Prometheus exporter endpoint over TLS and forwards metrics to VictoriaMetrics.
- **VMServiceScrape CR:** Kubernetes custom resource that declares the VAST scrape target for the VictoriaMetrics operator.
- **VLAgent:** Receives VAST syslog events (RFC 3164/5424) and forwards them to VictoriaLogs.
- **Kubernetes Service + Endpoints:** Abstracts the external VAST appliance as a discoverable Kubernetes service for vmagent.

Supported Metrics and Logs
--------------------------

**Metrics**

The VAST metrics include the following:

- **Storage Performance:** Read/write throughput (bytes/sec), IOPS per volume, latency metrics
- **Capacity Metrics:** Total capacity, used capacity, available capacity, thin provisioning ratios
- **Volume Metrics:** Volume state, volume performance counters, snapshot metrics
- **Device Metrics:** Device health status, device performance, device error counters
- **Cluster Health:** Node status, cluster connectivity, replication status
- **Telemetry Health:** Scrape success rate, scrape duration, ingest latency

**Logs**

The VAST logs include the following:

- **Storage Events:** Volume creation/deletion events, snapshot events, capacity threshold alerts
- **System Events:** Node health events, cluster state changes, replication events
- **Alarm Events:** Critical alarms, warning alarms, informational events
- Events are labeled with hostname, severity, and facility

Prerequisites
-------------

Make sure the following prerequisites are met:

- Ensure that the ``telemetry_config.yml`` has the entries specific for VAST Telemetry deployment enabled. For more details on configuring ``telemetry_config.yml``, see :doc:`../service_cluster_telemetry`.
- Ensure that the ``provision.yml`` playbook has been executed successfully with ``service_kube_control_plane`` and ``service_kube_node`` in the mapping file.
- Ensure the service Kubernetes cluster has sufficient resources to run vmagent (shared instance) and VLAgent.
- Ensure network connectivity between the service Kubernetes cluster and the VAST Storage appliance.

.. note::
   VAST Telemetry supports independent feature flags for metric collection and log collection. You can enable or disable each independently. For more details, see :doc:`../service_cluster_telemetry`.

For VAST Metrics Collection
----------------------------

Configure the following settings on the VAST appliance:

The VAST Prometheus exporter must be enabled and accessible from the service cluster.

- **Enable VAST Telemetry:** Ensure VAST Telemetry is enabled in the VAST cluster configuration.

- **Verify Prometheus endpoint:** Confirm that the VAST Prometheus exporter is accessible at::

    https://<vast_ip>:443/api/prometheusmetrics/all
    https://<vast_ip>:443/api/prometheusmetrics/views
    https://<vast_ip>:443/api/prometheusmetrics/devices
    https://<vast_ip>:443/api/prometheusmetrics/alarms

- **Configure SSL certificates (optional):** If using CA-signed TLS, set up SSL and CA certificates in VAST. For detailed steps, see `VAST Data Documentation - Security Configuration <https://docs.vastdata.com/>`_.

For VAST Log Collection
-----------------------

Configure the following settings on the VAST appliance:

- **Enable syslog forwarding:** Configure VAST to send syslog messages to the VLAgent LoadBalancer IP:

  1. From the left navigation menu, select **Settings → Notifications**
  
  2. Select **Syslog Setup** and complete the fields:

     - **Syslog Host:** Enter the VLAgent LoadBalancer IP address
     - **Syslog Port:** Enter 514 (default)
     - **Syslog Protocol:** Select UDP or TCP based on your requirements

  3. Click **Save**

For detailed information on VAST syslog configuration parameters, see `VAST Data Documentation - Default Notification Actions <https://docs.vastdata.com/>`_.

- **Set VLAgent LoadBalancer IP:** Configure the VLAgent LoadBalancer IP address for syslog delivery. Retrieve the VLAgent external IP from the service Kubernetes cluster::

    kubectl get svc -n telemetry | grep vlagent

Verify VAST Telemetry Flow
---------------------------

This section outlines the steps to verify VAST telemetry data in VictoriaMetrics.

View Collected VAST Telemetry Data using VictoriaMetrics UI (VMUI) - Cluster Mode Deployment
-------------------------------------------------------------------------------------------

After applying the ``telemetry.yml`` configuration using the VictoriaMetrics deployment mode as cluster, use the VictoriaMetrics UI (VMUI) to validate that VAST telemetry data is being collected and stored successfully in a cluster mode VictoriaMetrics deployment. For more details, see `VictoriaMetrics Cluster deployment documentation <https://docs.victoriametrics.com/victoriametrics/cluster-victoriametrics/>`_.

1. Run the following command to verify that the VictoriaMetrics pod is running::

    kubectl get pods -n telemetry -o wide | grep vm

    .. image:: ../../../../images/vast_telemetry_1.png

2. Run the following command to verify that the VictoriaMetrics service is running::

    kubectl get service -n telemetry -o wide | grep vm

    .. image:: ../../../../images/vast_telemetry_2.png
    .. image:: ../../../../images/vast_telemetry_3.png

3. Run the following command to verify VMagent logs for VAST scraping to view recent logs::

    VMAGENT_POD=$(kubectl get pods -n telemetry -l app.kubernetes.io/name=vmagent -o jsonpath='{.items[0].metadata.name}')
    kubectl logs $VMAGENT_POD -n telemetry -c vmagent --tail=10

    .. image:: ../../../../images/vast_telemetry_4.png

4. Note the **External IP** and **port number** of the VictoriaMetrics service. The external IP and port number will be used to access the VictoriaMetrics UI (VMUI)::

    kubectl get svc -n telemetry | grep vmselect

    .. image:: ../../../../images/vast_telemetry_5.png

5. Access the VMUI in a web browser using::

    https://<external vmselect loadbalancer IP>:8481/select/0/vmui

    .. image:: ../../../../images/vast_telemetry_7.png

Key VAST Metrics
----------------

.. csv-table:: Key VAST Metrics
   :file: ../../../../Tables/vast_metrics.csv
   :header-rows: 1
   :widths: 40, 40, 20
   :keepspace:

View VAST Logs using VictoriaLogs
----------------------------------

1. Configure the VLAgent LoadBalancer IP address for syslog delivery. Retrieve the VLAgent LoadBalancer IP and configure it on the VAST appliance by following the steps outlined in the prerequisites section above::

    kubectl get svc -n telemetry | grep -E "(vlagent|victoria-logs)"

    .. image:: ../../../../images/view_vast_logs_1.png

2. Retrieve the external IP and port of the vlselect service::

    kubectl get svc -n telemetry | grep vlselect

    .. image:: ../../../../images/view_vast_logs_3.png

3. Access the VictoriaLogs UI in a web browser using::

    https://<external vlselect loadbalancer IP>:9471/select/vmui

    .. image:: ../../../../images/view_vast_logs_4.png
