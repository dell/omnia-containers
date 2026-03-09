Integrate Smart Fabric Manager with VictoriaMetrics for Secure Telemetry Data Streaming
============================================================================================

This section describes how to configure Smart Fabric Manager (SFM) to securely stream
telemetry metrics to the Service Kubernetes cluster.

This procedure assumes that VictoriaMetrics is deployed in **cluster mode** in the
``telemetry`` namespace of the Service Kubernetes cluster.
For more information, see the `VictoriaMetrics cluster mode documentation
<https://docs.victoriametrics.com/victoriametrics/cluster-victoriametrics/>`_.

Prerequisites
-------------

Make sure the following prerequisites are met:

* Ensure that the ``pod_external_ip_range`` parameter is set in the ``omnia_config.yml`` file for the Service Kubernetes cluster and it is reachable from the SFM network.
* Ensure VictoriaMetrics (Cluster Mode) is installed and running in the Service Kubernetes cluster.
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

   .. image:: ../../../images/sfm_observability_settings.png

3. Under **Prometheus Remote Write**, select the option button next to ``vminsert-target``, and then select **Edit**.

4. Configure the following settings:
      - **Enable**: ON
      - **URL**: ``https://vminsert.telemetry.svc.cluster.local:8480/insert/0/prometheus/api/v1/write``
      - **Message Version**: v1
      - **TLS Config**: Upload ``ca.crt`` from ``/opt/omnia/telemetry/victoria-certs/`` as the Server Certificate File

   .. note::
      If SFM is installed on a different system than the OIM host, copy ``ca.crt`` to that system before uploading it in the UI.

   .. image:: ../../../images/sfm_observability_settings_prometheus_remote_write.png

   .. image:: ../../../images/sfm_observability_remote_write_settings.png

   .. image:: ../../../images/sfm_observability_TLS_config.png    

5. SSH to the SFM IP with admin credentials and log in to secure shell. 

   For detailed instructions on SSH login to SFM, see the `SmartFabric Manager for SONiC User Guide <https://www.dell.com/support/manuals/en-us/smartfabric-manager-for-sonic/sfm-100-user-guide-pub/change-the-admin-user-password?guid=guid-32777160-040a-4266-83a3-e7d0fa5e5ced&lang=en-us>`_.

   **SSH Login Steps:**

   a. Use SSH to connect to the SFM VM IP address::

       ssh admin@<SFM-IP-ADDRESS>

   b. Enter the admin user password when prompted,

   c. The SFM Main Menu appears after successful login.

   For additional SSH configuration information, see the `Dell Networking SONiC SSH documentation <https://www.dell.com/support/kbdoc/en-us/000218783/dell-networking-sonic-ssh-based-login>`_.

6. From the control_plane host, SSH to the SFM VM to access the SFM command line interface::

      ssh admin@<SFM-IP-ADDRESS>

   This step provides access to the SFM VM where you can execute kubectl commands to manage the SFM Prometheus pod in the next step.

7. Update the ``/etc/hosts`` file only inside the SFM Prometheus pod. To update the ``/etc/hosts`` file, perform the following steps:

   a. List all namespaces to locate the SFM namespace::

       kubectl get namespaces | grep sfm

   b. Find the SFM Prometheus pod in the identified namespace (replace <sfm-namespace> with the actual namespace found)::

       kubectl get pods -n <sfm-namespace> | grep prometheus

   c. Once you have the pod name and namespace, update the ``/etc/hosts`` file inside the SFM Prometheus pod::

       kubectl exec -it <sfm-prometheus-pod-name> -n <sfm-namespace> -- /bin/sh
       echo "<vminsert-IP> vminsert.telemetry.svc.cluster.local" >> /etc/hosts
       echo "<vmselect-IP> vmselect.telemetry.svc.cluster.local" >> /etc/hosts

   For vminsert and vmselect IP, use the values retrieved by the ``external_victoria_connect_details.yml`` playbook in Step 1.

   .. note:: The ``/etc/hosts`` update must be repeated if the SFM Prometheus pod restarts.
      

View Collected SFM Telemetry Data using VictoriaMetrics UI (VMUI) - Cluster Mode Deployment
----------------------------------------------------------------------------------------------
To view the SFM telemetry data that is streamed to VictoriaMetrics, do the following:

1. Run the following command to verify that the VictoriaMetrics pod is running::

    kubectl get pods -n telemetry -o wide | grep vm

.. image:: ../../../images/victoria_metrics_pod_cluster_mode.png

2. Run the following command to verify that the VictoriaMetrics vmselect service is running::

    kubectl get service -n telemetry -o wide | grep vmselect

.. image:: ../../../images/victoria_metrics_service_cluster.png

3. Note the **External IP** and **port number** of the VictoriaMetrics vmselect service. The external IP and port number will be used to access the VictoriaMetrics UI (VMUI).

4. Access the VMUI in a web browser using::

    https://<external vmselect loadbalancer IP>:8481/select/0/vmui 

5. Filter and view telemetry metrics using queries in VMUI.

   **SFM Metrics Reference:**

   For a comprehensive list of available SFM telemetry metrics and OpenConfig models, see:

      * `SONiC gNMI Documentation <https://github.com/sonic-net/sonic-gnmi/blob/master/doc/gNMI_usage_examples.md>`_ - Contains supported OpenConfig models and sensor paths
      * `SmartFabric Manager for SONiC User Guide <https://www.dell.com/support/manuals/en-us/smartfabric-manager-for-sonic/sfm-141-user-guide-pub/about-this-guide?guid=guid-cade55b2-3c66-4829-aca0-efbc3fff5792&lang=en-us>`_ - SFM-specific telemetry information

   **Example Queries:**

   *View all SFM interface metrics:*

   .. code-block:: text

       {__name__=~"sonic.*interface.*"}

   *View interface operational status:*

   .. code-block:: text

       {__name__="openconfig_interfaces_oper_status"}

   *View system temperature metrics:*

   .. code-block:: text

       {__name__=~"openconfig_platform.*temperature.*"}

   *View PowerEdge hardware metrics:*

   .. code-block:: text

       {__name__=~"<SFM Metric Key>"}

   Replace ``<SFM Metric Key>`` with specific metric names from the SFM telemetry data. Use the VMUI metric explorer to discover available metric names.

.. image:: ../../../images/victoria_metrics_vmui_cluster.png
