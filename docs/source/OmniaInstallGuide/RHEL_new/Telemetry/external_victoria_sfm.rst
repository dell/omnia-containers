Collect telemetry data from Smart Fabric Manager to Victoria DB (cluster mode)
=============================================================================

This section describes how to configure Smart Fabric Manager to securely stream
telemetry metrics to the Service Kubernetes cluster.

This procedure assumes that VictoriaMetrics is deployed in **cluster mode** in the
``telemetry`` namespace of the Service Kubernetes cluster.
For more information, see the `VictoriaMetrics cluster mode documentation
<https://docs.victoriametrics.com/victoriametrics/cluster-victoriametrics/>`_.

Prerequisites
-------------

Make sure the following prerequisites are met:

* A Service Kubernetes cluster is running with VictoriaMetrics deployed in the
  ``telemetry`` namespace.
* External access to VictoriaMetrics is available through the following
  LoadBalancer ports:

  * ``8480`` for ingesting data
  * ``8481`` for querying data

Steps
-----

1. Run the following playbook to retrieve the VictoriaMetrics connection details and TLS certificate from the Service Kubernetes cluster::

      cd /omnia/utils
      ansible-playbook external_victoria_connect_details.yml

   The ``external_victoria_connect_details.yml`` playbook performs the following:
      - Retrieves the VictoriaMetrics vminsert and vmselect LoadBalancer IPs.
      - Extracts the server CA certificate for TLS.
      - Writes the connection details to ``/opt/omnia/telemetry/external_victoria_connect_details.yml``.
      - Saves the CA certificate at ``/opt/omnia/telemetry/victoria-certs/ca.crt``.

2. In the Smart Fabric Manager for SONiC UI, navigate to **Observability**, and then select the **Settings** tab.

3. Under **Prometheus Remote Pump**, select the option button next to ``vminsert-target``, and then select **Edit**.

4. Configure the following settings:
      - **Enable**: ON
      - **URL**: ``https://vminsert.telemetry.svc.cluster.local:8480/insert/0/prometheus/api/v1/write``
      - **Message Version**: v1
      - **TLS Config**: Upload ``ca.crt`` from ``/opt/omnia/telemetry/victoria-certs/`` as the Server Certificate File

   .. note::
      If SFM is installed on a different system than the OIM host, copy ``ca.crt`` to that system before uploading it in the UI.

5. SSH to the SFM IP with admin credentials and log in to secure shell.

6. Update the ``/etc/hosts`` file only inside the SFM Prometheus pod. This is required only inside the pod, not on the SFM server host)::

      kubectl exec -it <sfm-prometheus-pod-name> -n sfm-ui -- /bin/sh
      echo "<vminsert-IP> vminsert.telemetry.svc.cluster.local" >> /etc/hosts
      echo "<vmselect-IP> vmselect.telemetry.svc.cluster.local" >> /etc/hosts

   For vminsert and vmselect IP, use the values retrieved by the ``external_victoria_connect_details.yml`` playbook in Step 1.
   .. note::
      The ``/etc/hosts`` update must be repeated if the SFM Prometheus pod restarts.
