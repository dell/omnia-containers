Collect Telemetry Data from External Client Nodes to Victoria DB (Cluster Mode)
===============================================================================

This section describes how to create a new metric in VictoriaMetrics and configure an external telemetry producer to stream metrics 
securely into the Service Kubernetes cluster using TLS.

This procedure assumes that VictoriaMetrics is deployed in **cluster mode** inside the ``telemetry`` namespace of the Service Kubernetes cluster.
For more details, see the `VictoriaMetrics Cluster Mode documentation <https://docs.victoriametrics.com/victoriametrics/cluster-victoriametrics/>`_.

For collecting telemetry data from Smart Fabric Manager (SFM) to Victoria DB, see :doc:`Collect telemetry data from Smart Fabric Manager to Victoria DB (cluster mode) <external_victoria_sfm>`.


Prerequisites
---------------

Ensure the following prerequisites are met:

* A Service Kubernetes cluster is running with VictoriaMetrics deployed in the ``telemetry`` namespace.
* External access to VictoriaMetrics is available through:
  
  * LoadBalancer port ``8480`` for ingesting (inserting) data.
  * LoadBalancer port ``8481`` for querying data.


Retrieve the Victoria Select and Insert LoadBalancer IP Addresses
------------------------------------------------------------------

Run the following playbook to retrieve the VictoriaMetrics connection details and TLS certificate from the Service Kubernetes cluster::

    cd /omnia/utils
    ansible-playbook external_victoria_connect_details.yml

The ``external_victoria_connect_details.yml`` playbook does the following:
 - Retrieves the VictoriaMetrics vminsert and vmselect LoadBalancer IPs.
 - Extracts the server CA certificate for TLS.
 - Writes the connection details to ``/opt/omnia/telemetry/external_victoria_connect_details.yml``.
 - Saves the CA certificate at ``/opt/omnia/telemetry/victoria-certs/ca.crt``.

   
Push Sample metrics from Omnia Core Container in the OIM
---------------------------------------------------------------
1. Add the LoadBalancer insert and select IP addresses to ``/etc/hosts``::

    echo "<vminsert-IP> vminsert.telemetry.svc.cluster.local" >> /etc/hosts
    echo "<vmselect-IP> vmselect.telemetry.svc.cluster.local" >> /etc/hosts

 For vminsert and vmselect IP, use the values retrieved by the ``external_victoria_connect_details.yml`` playbook.

    .. note::
      The ``/etc/hosts`` update must be repeated if the SFM Prometheus pod restarts.
  
2. Create a new test metric using the following command::
 
    curl --cacert ca.crt -X POST "https://vminsert.telemetry.svc.cluster.local:8480/insert/0/prometheus/api/v1/import/prometheus" \
    -H "Content-Type: text/plain" \
    -d "test_metric{source=\"external\"} 42"

.. note:: Use ``https://vminsert.telemetry.svc.cluster.local:8480//insert/0/prometheus/api/v1/write`` to push the metrics from an external client, such as SmartFabric Manager (SFM). To know more about SFM, refer to `SFM <https://www.dell.com/en-in/shop/ipovw/smartfabric-manager-for-sonic>`_.

.. note:: For collecting telemetry data from Smart Fabric Manager (SFM) to Victoria DB, see :doc:`Collect telemetry data from Smart Fabric Manager to Victoria DB (cluster mode) <external_victoria_sfm>`.

3. Push the sample test metrics to Victoria DB using the following command::

    curl --cacert ca.crt -X POST   "https://vminsert.telemetry.svc.cluster.local:8480/insert/0/prometheus/api/v1/import/prometheus"   -H "Content-Type: text/plain"   -d 'cpu_usage{host="server1",job="new"} 75.5
    memory_usage{host="server1",job="new"} 1024
    disk_usage{host="server1",job="new"} 512
    network_rx{host="server1",interface="eth0"} 1000000
    network_tx{host="server1",interface="eth0"} 500000'

4. Use the following commands to query the inserted data from Victoria DB::

    curl --cacert ca.crt -s "https://vmselect.telemetry.svc.cluster.local:8481/select/0/prometheus/api/v1/query?query=new_metric"
    curl --cacert ca.crt -s "https://vmselect.telemetry.svc.cluster.local:8481/select/0/prometheus/api/v1/query_range?query=cpu_usage&start=$(date -d '1 hour ago' +%s)&end=$(date +%s)&step=600s"



