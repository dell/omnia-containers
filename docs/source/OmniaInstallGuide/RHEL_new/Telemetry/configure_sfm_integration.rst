Configure Smart Fabric Manager (SFM) Integration with VictoriaMetrics for Secure Telemetry Data Streaming
=========================================================================================================

This section describes how to configure Smart Fabric Manager to securely stream telemetry metrics to the Service Kubernetes cluster.

This procedure assumes that VictoriaMetrics is deployed in **cluster mode** in the ``telemetry`` namespace of the Service Kubernetes cluster.
For more information, see the `VictoriaMetrics cluster mode documentation <https://docs.victoriametrics.com/victoriametrics/cluster-victoriametrics/>`_.

Prerequisites
-------------

Ensure that the following prerequisites are met:

* Ensure that the Secure Shell (SSH) is enabled on the Smart Fabric Manager (SFM) virtual machine. For detailed steps on how to enable SSH, see the `Smart Fabric Manager documentation <https://www.dell.com/support/manuals/en-in/smartfabric-manager-for-sonic/sfm-141-user-guide-pub/enable-secure-shell-access-for-admin-user?guid=guid-a381d8a7-2f41-42c5-b597-aa651321e588&lang=en-us>`_.
* Ensure that the ``pod_external_ip_range`` parameter is set in the ``omnia_config.yml`` file for the Service Kubernetes cluster and it is reachable from the SFM network.
* Ensure VictoriaMetrics (Cluster Mode) is installed and running in the Service Kubernetes cluster.
* External access to VictoriaMetrics is available through the following LoadBalancer ports:

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
      - Writes the connection details to ``/omnia/utils/external_victoria_connect_details.yml``.
      - Saves the CA certificate at ``/omnia/utils/victoria-certs/ca.crt``.

2. In the Smart Fabric Manager for SONiC UI, navigate to **Observability**, and then select the **Settings** tab.

   .. image:: ../../../../images/sfm_observability_settings.png

3. Under **Prometheus Remote Write**, select the option button next to ``vminsert-target``, and then select **Edit**.

4. Configure the following settings:
      - **Enable**: ON
      - **URL**: ``https://vminsert.telemetry.svc.cluster.local:8480/insert/0/prometheus/api/v1/write``
      - **Message Version**: v1
      - **TLS Config**: Upload ``ca.crt`` from ``/omnia/utils/victoria-certs/`` as the Server Certificate File

   .. note::
      If SFM is installed on a different system than the OIM host, copy ``ca.crt`` to that system before uploading it in the UI.

   .. image:: ../../../../images/sfm_observability_settings_prometheus_remote_write.png

   .. image:: ../../../../images/sfm_observability_remote_write_settings.png

   .. image:: ../../../../images/sfm_observability_TLS_config.png

5. Update the ``etc/hosts`` file of the Kubernetes Prometheus pod in the SFM VM by performing the following steps:

   a. Log in to the SFM VM.
   b. Run the following command to connect to the SFM VM using SSH with your admin credentials::

       ssh <admin_user>@<sfm_vm_ip>

   c. From the **SFM - Main Menu**, enter **6** to select **Debug Menu**.

      .. image:: ../../../../images/telemetry_sfm_main_menu.png

   d. From the **Debug Menu**, enter **12** to select **Enter Secure Shell**. This will open a shell session on the SFM host VM.

      .. image:: ../../../../images/telemetry_sfm_debug_menu.png

   e. Identify the Prometheus pod using the following command::

         kubectl get pods -A | grep prometheus

     .. image:: ../../../../images/telemetry_sfm_identify_propmetheus_pod.png

   f. Inside the Prometheus pod, add the VictoriaMetrics insert LoadBalancer IP to ``/etc/hosts`` ::

         kubectl exec -it -n <Prometheus Namespace> <Prometheus Pod Name> -- /bin/sh
         echo "<vmselect loadbalancer ip> vminsert.telemetry.svc.cluster.local" >> /etc/hosts

      .. image:: ../../../../images/telemetry_sfm_propmetheus_pod.png
      .. image:: ../../../../images/telemetry_sfm_vminsert.png
