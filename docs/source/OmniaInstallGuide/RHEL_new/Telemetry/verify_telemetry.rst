Step 16: Verify Telemetry Services Deployed on the Cluster
===========================================================

This section outlines the steps to validate telemetry services and their components, including checking pod status, 
verifying message flow, confirming TLS connectivity, and reviewing collected telemetry data.


.. note:: For the list of iDRAC telemetry metrics collected by Kafka and VictoriaMetrics, see `iDRAC Telemetry Reference Tools <https://github.com/dell/iDRAC-Telemetry-Reference-Tools>`_.


Verify Telemetry-Related Pods Are Running
-------------------------------------------

To verify that the iDRAC Telemetry, Kafka, LDMS, VictoriaMetrics, and VictoriaLogs pods are running, do the following::

1. Run the following command::

    kubectl get pods -n telemetry

2. Ensure that the following pods are in a running state in the output:

    * iDRAC Telemetry pods
    * Kafka broker, controller, and operator pods
    * LDMS aggregator and store pods
    * VictoriaMetrics and vmagent pods
    * VictoriaLogs pods (vlstorage, vlinsert, vlselect, vlagent)

The following is the sample output file:

.. image:: ../../../images/verify_telemetry_pods.png

Verify Kubernetes Telemetry Services Attached to Telemetry 
----------------------------------------------------------

To verify Kubernetes telemetry services attached to the iDRAC Telemetry, Kafka, LDMS, VictoriaMetrics, and VictoriaLogs pods, do the following:

1. Run the following command::

    kubectl get svc -n telemetry

2. Ensure the following service entries exist:

    * iDRAC Telemetry service
    * Kafka broker, controller, and bridge services
    * LDMS aggregator and store services
    * VictoriaMetrics service
    * VictoriaLogs services (vlselect, vlinsert, vlstorage)

The following is the sample output file:

.. image:: ../../../images/verify_kube_telemetry.png


Verify iDRAC Telemetry Messages in Kafka
-------------------------------------------

To verify that iDRAC telemetry data is being successfully published to the ``idrac`` Kafka topic, do the following:

1. Log in to the Service Kubernetes Control plane.

2. Create a Kafka consumer using the following command::

    KAFKA_LB_IP=<external load balancer IP of the bridge-bridge-lb service>
    curl -X POST http://$KAFKA_LB_IP:8080/consumers/idrac-consumer-group \
    -H 'content-type: application/vnd.kafka.v2+json' \
    -d '{
            "name": "idrac-consumer-1",
            "format": "json",
            "auto.offset.reset": "earliest"
        }'

3. Subscribe the consumer to the telemetry topic using the following command::

    curl -X POST http://$KAFKA_LB_IP:8080/consumers/idrac-consumer-group/instances/idrac-consumer-1/subscription \
    -H 'content-type: application/vnd.kafka.v2+json' \
    -d '{"topics": ["idrac"]}'

4. Consume messages from the topic using the following command::

    while true; do curl -X GET http://$KAFKA_LB_IP:8080/consumers/idrac-consumer-group/instances/idrac-consumer-1/records \
    -H 'accept: application/vnd.kafka.json.v2+json' | jq '.' ;  sleep 2; done

If telemetry metrics are collected correctly, the output contains JSON-formatted iDRAC telemetry records.

.. _verify_ldms_messages_in_kafka:

Verify LDMS Messages in Kafka
-----------------------------

To verify that LDMS telemetry data is being successfully published to the ``ldms`` Kafka topic, do the following:

1. Log in to the Service Kubernetes Control plane.

2. Create a Kafka consumer using the following command::

    KAFKA_LB_IP=<external load balancer IP of the bridge-bridge-lb service>
    curl -X POST http://$KAFKA_LB_IP:8080/consumers/ldms-consumer-group \
    -H 'content-type: application/vnd.kafka.v2+json' \
    -d '{
            "name": "ldms-consumer-1",
            "format": "json",
            "auto.offset.reset": "latest",
            "enable.auto.commit": true
        }'

3. Subscribe the consumer to the LDMS topic using the following command::

    curl -X POST http://$KAFKA_LB_IP:8080/consumers/ldms-consumer-group/instances/ldms-consumer-1/subscription \
    -H 'content-type: application/vnd.kafka.v2+json' \ 
    -d '{"topics": ["ldms"]}'

4. Consume messages from the topic using the following command::

    while true; do curl -X GET http://$KAFKA_LB_IP:8080/consumers/ldms-consumer-group/instances/ldms-consumer-1/records \
    -H 'accept: application/vnd.kafka.json.v2+json' | jq '.' ;  sleep 2; done

If telemetry is flowing correctly, the output contains JSON-formatted LDMS telemetry records.

.. note:: When new nodes are added, ensure the nodes are up and cloud-init has completed successfully (check /var/log/cloud-init-output.log on each node). Then, create a new Kafka consumer group with a unique name (e.g., ldms-new-nodes-group) to verify metrics from the newly added nodes. Wait 2-3 minutes after discovery completes before checking.

Verify Kafka TLS Connectivity
-----------------------------
To verify TLS connectivity for Kafka, run the Kafka TLS test job to verify that
certificates, truststores, keystores, and mTLS communication are functioning correctly::

    cd /<nfs client mount path of the service k8s cluster>/telemetry/deployments/test
    kubectl apply -f kafka.tls_test_job.yaml

After the job completes, check the logs to confirm that the TLS connection is successful::

    kubectl logs kafka-tls-test-xxx -n telemetry


Verify VictoriaMetrics TLS Connectivity
---------------------------------------

To verify TLS connectivity for VictoriaMetrics, run the VictoriaMetrics TLS test job to
verify that certificates and secure connectivity are functioning correctly::

    cd /<nfs client mount path of the service k8s cluster>/telemetry/deployments/test
    kubectl apply -f victoria-tls-test-job.yaml

After the job completes, check the logs to confirm that the TLS connection is successful::

    kubectl logs victoria-tls-test-xxx -n telemetry    


Verify VictoriaLogs TLS Connectivity
--------------------------------------

To verify TLS connectivity for VictoriaLogs, run the VictoriaLogs TLS test job to
verify that certificates and secure connectivity are functioning correctly::

    cd /<nfs client mount path of the service k8s cluster>/telemetry/deployments/test
    kubectl apply -f victorialogs-tls-test-job.yaml

After the job completes, check the logs to confirm that the TLS connection is successful::

    kubectl logs victorialogs-tls-test-xxx -n telemetry


View Collected Logs using VictoriaLogs Query Interface
-----------------------------------------------------

After applying the ``telemetry.yml`` configuration with ``idrac_telemetry_collection_type`` set to ``victoria``,
you can access the VictoriaLogs query interface to validate that log data is being collected and stored
successfully. For more details on querying VictoriaLogs, see `Query VictoriaLogs <query_victorialogs.html>`_.

1. Run the following command to verify that the VictoriaLogs vlselect pod is running::

    kubectl get pods -n telemetry -o wide | grep vlselect

2. Run the following command to verify that the VictoriaLogs vlselect service is running::

    kubectl get service -n telemetry -o wide | grep vlselect

3. Note the **External IP** and **port number** of the VictoriaLogs vlselect service. The external IP and port number will be used to access the VictoriaLogs query interface.

4. Access the VictoriaLogs query interface in a web browser using::

    https://<external vlselect loadbalancer IP>:9480/select/0/vmui

5. Filter and view logs using LogsQL queries in the query interface.
For example, the following query displays recent log entries::

    * | sort by time desc

Verify VictoriaLogs Log Ingestion
---------------------------------

After recording the VictoriaLogs endpoint information from the deployment, verify that the VictoriaLogs deployment is fully functional by testing end-to-end log ingestion:

1. Test log ingestion by sending a test syslog message to VLAgent::

    echo "test message" | nc -u <LoadBalancer IP> 514

2. Verify the test message appears in VictoriaLogs query results::

    curl -k https://<LoadBalancer IP>:9491/select/logsql/query -d 'query="{_msg=\"test message\"}"'

3. Confirm the query returns the test log entry, indicating successful ingestion and query functionality.


View Collected iDRAC Telemetry Data using VictoriaMetrics UI (VMUI) - Single Mode Deployment
----------------------------------------------------------------------------------------------

After applying the ``telemetry.yml`` configuration using the VictoriaMetrics deployment mode as ``single-node``, 
use the (VMUI) to validate that iDRAC telemetry data is being collected and stored 
successfully in a single-mode VictoriaMetrics deployment. For more details, see
`VictoriaMetrics Single Server documentation <https://docs.victoriametrics.com/victoriametrics/single-server-victoriametrics/>`_.

.. note:: Metric availability depends on the server hardware configuration and iDRAC capabilities. Only telemetry metrics that are exposed and streamed by iDRAC can be retrieved and viewed. Metrics that appear as “NA” (Not Available) in iDRAC are not included in telemetry data and therefore do not appear in telemetry queries or views.

1. Run the following command to verify that the VictoriaMetrics pod is running::

    kubectl get pods -n telemetry -o wide -l app=victoriametrics

.. image:: ../../../images/victoria_metrics_pod.png

2. Run the following command to verify that the VictoriaMetrics service is running::

    kubectl get service -n telemetry -o wide -l app=victoriametrics

.. image:: ../../../images/victoria_metrics_service.png

3. Note the **External IP** and **port number** of the VictoriaMetrics service. The external IP and port number will be used to access the VictoriaMetrics UI (VMUI).

4. Access the VMUI in a web browser using::

    http://<external victoria metrics loadbalancer IP>:8443/vmui

5. Filter and view telemetry metrics using queries in VMUI.
For example, the following query displays detailed temperature
readings for each hardware component::

    {name="PowerEdge_TemperatureReading", FQDD!=""}

.. image:: ../../../images/victoria_metrics_vmui.png



View Collected iDRAC Telemetry Data using VictoriaMetrics UI (VMUI) - Cluster Mode Deployment
----------------------------------------------------------------------------------------------

After applying the ``telemetry.yml`` configuration using the VictoriaMetrics deployment mode as ``cluster``, 
use the (VMUI) to validate that iDRAC telemetry data is being collected and stored 
successfully in a cluster mode VictoriaMetrics deployment. For more details, see 
`VictoriaMetrics Cluster deployment documentation <https://docs.victoriametrics.com/victoriametrics/cluster-victoriametrics/>`_.

1. Run the following command to verify that the VictoriaMetrics pod is running::

    kubectl get pods -n telemetry -o wide | grep vm

.. image:: ../../../images/victoria_metrics_pod_cluster_mode.png

2. Run the following command to verify that the VictoriaMetrics service is running::

    kubectl get service -n telemetry -o wide | grep vm

.. image:: ../../../images/victoria_metrics_service_cluster.png

3. Note the **External IP** and **port number** of the VictoriaMetrics service. The external IP and port number will be used to access the VictoriaMetrics UI (VMUI).

4. Access the VMUI in a web browser using::

    https://<external vmselect loadbalancer IP>:8481/select/0/vmui 

5. Filter and view telemetry metrics using queries in VMUI.
For example, the following query displays detailed PowerEdge metrics for each hardware component::

    {__name__=~"PowerEdge_.*"}

.. image:: ../../../images/victoria_metrics_vmui_cluster.png
    


Accessing the MySQL Database
------------------------------------

After ``telemetry.yml`` has been executed for the service cluster, you can check the MySQL database inside the ``mysqldb`` container. To view these logs, do the following:

    1. Use the following command to get the names of all the telemetry pods: ::
        
        kubectl get pods -n telemetry -l app=idrac-telemetry

    .. note:: The ``idrac-telemetry-0`` pod will always be responsible for collecting the telemetry data of the management nodes (``oim``, ``service_kube_control_plane_x86_64``, ``service_kube_node_x86_64``, ``login_node_x86_64``, etc.).

    2. Execute the following command: ::

        kubectl exec -it -n telemetry <iDRAC_telemetry_pod_name> -c mysqldb -- mysql -u <MYSQL_USER> -p

    3. When prompted, enter the mysql password to log in.

    4. To enter into the ``idrac_telemetry_db``, use the following command: ::

        use idrac_telemetrydb;

    5. To access the services table: ::
        
        select * from services;