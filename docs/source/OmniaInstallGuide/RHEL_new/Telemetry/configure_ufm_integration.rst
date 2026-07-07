Configure NVIDIA Unified Fabric Manager (UFM) Integration with Omnia Telemetry for Secure Metrics and Logs Streaming
====================================================================================================================

This section describes how to configure NVIDIA Unified Fabric Manager (UFM) to securely stream telemetry metrics and logs to the Service Kubernetes cluster.

This procedure assumes that VictoriaMetrics is deployed in **cluster mode** in the ``telemetry`` namespace of the Service Kubernetes cluster.
For more information, see the `VictoriaMetrics cluster mode documentation <https://docs.victoriametrics.com/victoriametrics/cluster-victoriametrics/>`_.

Using Omnia, you can deploy UFM Telemetry to collect InfiniBand fabric performance metrics and syslog events from NVIDIA Unified Fabric Manager (UFM) appliances. The deployment includes configuring the UFM Telemetry components on the service Kubernetes cluster, integrating with the UFM Prometheus exporter via vmagent, and ingesting syslog events via the VLAgent pipeline.

UFM Telemetry collects InfiniBand fabric metrics and logs. UFM Telemetry includes these components:

* **UFM Prometheus Exporter**: Exposes InfiniBand fabric metrics on a Prometheus-compatible HTTPS endpoint (default port 9001).
* **vmagent (shared)**: Scrapes the UFM Prometheus exporter endpoint over TLS and forwards metrics to VictoriaMetrics.
* **VMServiceScrape CR**: Kubernetes custom resource that declares the UFM scrape target for the VictoriaMetrics operator.
* **VLAgent**: Receives UFM syslog events (RFC 3164/5424) and forwards them to VictoriaLogs.
* **Kubernetes Service + Endpoints**: Abstracts the external UFM appliance as a discoverable Kubernetes service for vmagent.

Supported Metrics and Logs
---------------------------

**Metrics:**

The UFM metrics include the following:

* **Port State**: InfiniBand port operational state (up, down, disabled)
* **Traffic Counters**: Transmit/receive data rates (bytes/sec), packet counts per port
* **Error Counters**: Symbol errors, link error recovery, link downed, VL15 dropped, excessive buffer overrun errors
* **Fabric Topology**: Switch information, port mapping, node GUIDs, LID assignments
* **Telemetry Health**: Scrape success rate, scrape duration, ingest latency

**Logs:**

The UFM logs include the following:

* Fabric topology change events, port state transitions, error/warning messages
* SM (Subnet Manager) events, SHARP events, UFM health events
* Events are labeled with hostname, severity, and facility

Prerequisites
-------------

Ensure that the following prerequisites are met:

* Ensure that the ``provision.yml`` playbook has been executed successfully with ``service_kube_control_plane`` and ``service_kube_node`` in the mapping file.
* Ensure the service Kubernetes cluster has sufficient resources to run vmagent (shared instance) and VLAgent.
* Ensure network connectivity between the service Kubernetes cluster and the NVIDIA UFM appliance.
* Ensure that the ``telemetry_config.yml`` has the entries specific for UFM Telemetry deployment enabled. For more details on configuring ``telemetry_config.yml``, see `Service Cluster Telemetry Configuration <https://omnia-devel.readthedocs.io/en/omnia-docs-v2.2.0.0-rc1/OmniaInstallGuide/RHEL_new/Telemetry/service_cluster_telemetry.html#id2>`_.

.. note::
   UFM Telemetry supports independent feature flags for metric collection and log collection. You can enable or disable each independently. For more details, see `Configure Deployment Required for iDRAC Telemetry Service <https://omnia.readthedocs.io/en/latest/OmniaInstallGuide/RHEL_new/Telemetry/service_cluster_telemetry.html>`_.

**For UFM metrics collection, configure the following settings on the UFM appliance:**

The UFM Prometheus exporter must be enabled and accessible from the service cluster.

* **Enable UFM Telemetry**: Ensure UFM Telemetry is enabled in the ``gv.cfg`` configuration file::

    [Telemetry]
    telemetry_provider = telemetry

* **Verify Prometheus endpoint**: Confirm that the UFM Prometheus exporter is accessible at ``https://<ufm_ip>:9001/metrics``.
* **Configure SSL certificates (optional)**: If using CA-signed TLS, set up SSL and CA certificates in UFM. For detailed steps, see `Setting Up SSL and CA Certificates in UFM - Optional Configurations <https://docs.nvidia.com/networking/display/ufmenterpriseumv6242/optional-configurations>`_.

**For UFM log collection, configure the following settings on the UFM appliance:**

* **Enable syslog forwarding using the UFM Web UI:**

    Configure using the UFM Web UI to send syslog messages to the VLAgent LoadBalancer IP:

    1. From the left navigation menu, select **Settings → Data Streaming**
    2. Select **System log** and complete the fields:

       * **Destination**: Enter the VLAgent LoadBalancer IP address
       * **Syslog Port**: Enter 514 (default)
       * **System logs Level**: Select syslog level from the dropdown based on your requirements
       * **Streaming Data**: Select UFM logs

    3. Click **Save**

* **Enable syslog forwarding using the UFM CLI:**

    Configure using the UFM CLI to send syslog messages to the VLAgent LoadBalancer IP. Modify the ``[Logging]`` section in ``/opt/ufm/conf/gv.cfg``::

      [Logging]
      syslog = true
      syslog_addr = <external vlagent loadbalancer IP>:514
      ufm_syslog = true
      event_syslog = true
      syslog_level = WARNING

    For detailed information on UFM syslog configuration parameters, see `NVIDIA UFM Enterprise User Manual - Configuring Syslog <https://docs.nvidia.com/networking/display/ufmenterpriseumv6242/optional-configurations#src-4813172567_OptionalConfigurations-ConfiguringSyslog>`_.

* **Set VLAgent LoadBalancer IP**: Configure the VLAgent LoadBalancer IP address for syslog delivery. Retrieve the VLAgent external IP from the service Kubernetes cluster::

    kubectl get svc -n telemetry | grep vlagent
