.. _configure-victorialogs-sources:

Collect External Client Nodes to Send Logs to VictoriaLogs (Cluster Mode)
================================================================================

Configure external log sources (network devices, storage systems, fabric managers) to send logs to VictoriaLogs for centralized log collection and analysis.

Prerequisites
-------------

Before configuring log sources:

* Ensure that VictoriaLogs cluster is deployed.
* Ensure that you have recorded VLAgent endpoint information
* Ensure that you have the TLS CA certificate for VictoriaLogs
* Ensure that network connectivity exists from log sources to the Service Kubernetes cluster

.. important::
   Ensure that ``pod_external_ip_range`` in ``omnia_config.yml`` is reachable from external log sources.

Obtain Endpoint Information
----------------------------

Retrieve the VLAgent endpoint information from the VictoriaLogs deployment output.

1. Check the vlagent LoadBalancer service to get the external IP.

   .. code-block:: bash

      kubectl get svc vlagent -n telemetry

2. Record the following endpoints:

   * **Syslog plaintext**: ``<LoadBalancer IP>:514``
   * **Syslog TLS**: ``<LoadBalancer IP>:6514``
   * **HTTP forwarder**: ``https://<LoadBalancer IP>:9481/insert/jsonline``

3. Retrieve the TLS CA certificate from the victoria-tls-certs secret.

   .. code-block:: bash

      kubectl get secret victoria-tls-certs -n telemetry -o jsonpath='{.data.ca\.crt}' | base64 -d > victoria-ca.crt

.. note::
   VLAgent provides platform-managed syslog receivers. No additional configuration is needed on the Omnia side.

Configure Syslog Sources
-------------------------

Configure external devices to send syslog messages to VLAgent.

**Plaintext Syslog (Port 514)**

1. Access the configuration interface of your log source device.
2. Configure syslog forwarding to the VLAgent plaintext endpoint.

   Example configuration::

      Syslog server: <LoadBalancer IP>
      Port: 514
      Protocol: TCP or UDP

.. note::
   DNS mapping may be required in some devices for TLS certificate validation. Use the LoadBalancer IP if DNS is not configured.

**TLS Syslog (Port 6514)**

1. Copy the VictoriaLogs CA certificate to the log source device.
2. Access the configuration interface of your log source device.
3. Configure syslog forwarding to the VLAgent TLS endpoint.

   Example configuration::

      Syslog server: <LoadBalancer IP>
      Port: 6514
      Protocol: TCP
      TLS: Enabled
      CA certificate: victoria-ca.crt

4. Verify TLS handshake.

   .. code-block:: bash

      openssl s_client -connect <LoadBalancer IP>:6514 -CAfile victoria-ca.crt

.. AI_REVIEW::
   Device-specific syslog configuration examples may need SME verification for accuracy. The examples above provide general guidance; actual configuration steps vary by device vendor and firmware version.

Configure HTTP Forwarding Sources
-----------------------------------

Configure log sources that support HTTP forwarding to send logs in JSON Lines format to the vlinsert endpoint.

1. Access the configuration interface of your log source device.
2. Configure HTTP log forwarding to the vlinsert endpoint.

   Example configuration::

      Endpoint URL: https://<LoadBalancer IP>:9481/insert/jsonline
      Method: POST
      Format: JSON Lines
      Headers:
        Content-Type: application/json

3. Example JSON Lines payload format:

   .. code-block:: json

      {"time":"2024-01-01T12:00:00Z","stream":"device-01","_msg":"System started"}
      {"time":"2024-01-01T12:01:00Z","stream":"device-01","_msg":"Connection established"}

.. note::
   The vlinsert endpoint expects one JSON object per line (JSON Lines format).

Verify Log Ingestion
--------------------

1. Access the VictoriaLogs query interface.

   .. code-block:: bash

      curl -k https://<LoadBalancer IP>:9491/select/logsql/query -d 'query="{}"'

2. Query for logs from the configured source.

   .. code-block:: text

      query="{_stream='device-01'}"

3. Verify that logs from the external source appear in the query results.

.. note::
   Query latency depends on time range and data volume. Narrow the time range for faster results.

.. note::
   VictoriaLogs does not return an error when log entries with timestamps outside the configured retention window (-retentionPeriod) are submitted. These entries are discarded during the retention process.
