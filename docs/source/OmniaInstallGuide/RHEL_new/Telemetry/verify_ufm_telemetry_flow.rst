Verify UFM Telemetry Flow
==============================================

This section outlines the steps to verify UFM telemetry data in VictoriaMetrics.

View Collected UFM Telemetry Data using VictoriaMetrics UI (VMUI) - Cluster Mode Deployment
--------------------------------------------------------------------------------------------

After applying the ``telemetry.yml`` configuration using the VictoriaMetrics deployment mode as ``cluster``, 
use the (VMUI) to validate that UFM telemetry data is being collected and stored 
successfully in a cluster mode VictoriaMetrics deployment. For more details, see 
`VictoriaMetrics Cluster deployment documentation <https://docs.victoriametrics.com/victoriametrics/cluster-victoriametrics/>`_.

1. Run the following command to verify that the VictoriaMetrics pod is running::

    kubectl get pods -n telemetry -o wide | grep vm

.. image:: ../../../../images/verify_umf_telemetry_1.png

2. Run the following command to verify that the VictoriaMetrics service is running::

    kubectl get service -n telemetry -o wide | grep vm

.. image:: ../../../../images/verify_umf_telemetry_2.png

3. Run the following command to verify VMagent logs for UFM scraping to view recent logs::

    VMAGENT_POD=$(kubectl get pods -n telemetry -l app.kubernetes.io/name=vmagent -o jsonpath='{.items[0].metadata.name}')
    kubectl logs $VMAGENT_POD -n telemetry -c vmagent --tail=50

.. image:: ../../../../images/verify_umf_telemetry_3.png

4. Note the **External IP** and **port number** of the VictoriaMetrics service. The external IP and port number will be used to access the VictoriaMetrics UI (VMUI)::

    kubectl get svc -n telemetry | grep vmselect

.. image:: ../../../../images/verify_umf_telemetry_4.png

5. Access the VMUI in a web browser using::

   ``https://<external vmselect loadbalancer IP>:8481/select/vmui``

.. image:: ../../../../images/verify_umf_telemetry_5.png

6. Filter and view UFM InfiniBand metrics using queries in VMUI.
For example, the following query displays UFM InfiniBand metrics::

    {source="ufm", subsystem="infiniband"}

7. Key UFM Metrics

.. csv-table:: Key UFM InfiniBand Metrics
   :header: "Metric Name", "Description", "Unit"
   :widths: 30, 50, 20
   :file: ../../../../Tables/UFM_Metrics.csv

View UFM Logs using VictoriaLogs
---------------------------------

1. Configure the VLAgent LoadBalancer IP address for syslog delivery. Retrieve the VLAgent LoadBalancer IP and configure it on the UFM appliance by following the steps outlined in the prerequisites section above::

    kubectl get svc -n telemetry | grep -E "(vlagent|victoria-logs)"

.. image:: ../../../../images/view_umf_telemetry_1.png

2. Retrieve the external IP and port of the vlselect service::

    kubectl get svc -n telemetry | grep vlselect

.. image:: ../../../../images/view_umf_telemetry_2.png

3. Access the VMUI in a web browser using::

   ``https://<external vlselect loadbalancer IP>:9471/select/0/vmui``

.. image:: ../../../../images/view_umf_telemetry_3.png

