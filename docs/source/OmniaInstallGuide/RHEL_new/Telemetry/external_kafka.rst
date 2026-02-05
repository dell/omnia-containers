Collect Telemetry Data from External Client Nodes to Kafka
===========================================================
This section describes how to create a Kafka topic in the Omnia Service Kubernetes cluster
and configure an external telemetry producer to stream metrics securely into the Service Kubernetes clusters using mutual TLS (mTLS).

This procedure assumes that Kafka is deployed using Strimzi inside the telemetry namespace of the Service Kubernetes clusters. For more details, see
`Strimzi Kafka Operator Documentation <https://strimzi.io/docs/operators/latest/overview>`_.

To configure OpenManage Enterprise to stream telemetry data to Kafka, see :doc:`Collect Telemetry Data from OpenManage Enterprise <external_kafka_ome>`.


Prerequisites
---------------

Ensure the following prerequisites are met before proceeding:

* A Service Kubernetes cluster is running with Kafka deployed via Strimzi in the ``telemetry`` namespace.
* External access to Kafka is available through a LoadBalancer on port ``9094``.
* A Kafka Pump is available outside the Service Kubernetes cluster, deployed as a container using Kubernetes, Podman, or Docker.


(Optional) Create a Kafka Topic
-------------------------

On the Service Kubernetes cluster, do the following:

1. Create a file named ``kafka.topic_name.yaml`` that includes parameters such as topic name, number of partitions, 
replication factor, and retention policies::

       apiVersion: kafka.strimzi.io/v1beta2
       kind: KafkaTopic
       metadata:
        name: my-new-topic
        namespace: telemetry
        labels:
         strimzi.io/cluster: kafka
       spec:
        partitions: 3
        replicas: 3
        topicName: my-new-topic

Replace ``topic_name`` with the desired Kafka topic name.

2. Use the following command to apply the topic configuration file on the Service Kube Control Plane node::

       kubectl apply -f kafka.topic_name.yaml

3. To verify that the topic was created, run the following command::

       kubectl get kafkatopics -n telemetry


Extract Server and Client Certificates from Service Kubernetes Cluster
----------------------------------------------------------------------

To extract the server and client certificates, on the Service Kubernetes cluster, do the following:

1. Retrieve the Kafka LoadBalancer external IP using the following command::

       kubectl get svc -n telemetry kafka-kafka-external-bootstrap -o wide

   Sample output:

   .. image:: ../../../images/external_ip_loadbalances.png

.. note:: Note the Kafka LoadBalancer external IP. This external IP will be used by the external client node to connect to Kafka.

2. Extract the required server certificate for mTLS authentication using the following command::

       kubectl get secret kafka-cluster-ca-cert -n telemetry -o jsonpath='{.data.ca\.crt}' | base64 -d > ca.crt

.. note:: For OpenManage Enterprise kafka client, the ca.crt certificate can be directly used. To know more about OpenManage Enterprise, refer `OpenManage Enterprise <https://www.dell.com/en-in/lp/dt/open-manage-enterprise>`_.
     
3. Extract the required client certificate for mTLS authentication using the following commands::

       kubectl get secret kafkapump -n telemetry -o jsonpath='{.data.user\.crt}' | base64 -d > user.crt
       kubectl get secret kafkapump -n telemetry -o jsonpath='{.data.user\.key}' | base64 -d > user.key

4. On the external client node (Kafka Pump host), create a working directory using the following command and set appropriate permissions::

       mkdir -p ~/kafka-mtls-test
       cd ~/kafka-mtls-test

5. From the Service Kubernetes cluster, copy the extracted certificates to the directory created on the external client node using the following command::

       scp ca.crt user.crt user.key <username>@<external_node_ip>:~/kafka-mtls-test


Establish Secure Connection Between External Client Node and Service Kubernetes Cluster
---------------------------------------------------------------------------------------

1. On the external client node, navigate to the target directory::

       cd ~/kafka-mtls-test

   Make sure the following files are present in the directory::

       ca.crt 
       user.crt
       user.key 

2. Run the following command to create certificate in .pfx format and provide the password when prompted::

       openssl pkcs12 -export -out user.pfx -inkey user.key -in user.crt

.. note:: For OpenManage Enterprise Kafka client, the client certificate must be in .pfx format. To know more about OpenManage Enterprise, refer `OpenManage Enterprise <https://www.dell.com/en-in/lp/dt/open-manage-enterprise>`_.

3. (Optional) Run the following commands to create Java truststore and keystore::

       keytool -import -trustcacerts -alias kafka-ca -file ca.crt \
       -keystore kafka.truststore.jks -storepass changeit -noprompt

       openssl pkcs12 -export -in user.crt -inkey user.key \
       -out kafkapump.p12 -name kafkapump -password pass:changeit

       keytool -importkeystore \
       -srckeystore kafkapump.p12 -srcstoretype PKCS12 -srcstorepass changeit \
       -destkeystore kafka.keystore.jks -deststorepass changeit -noprompt

.. note::  The steps for converting certificates into JKS format are required **only for Java-based Kafka clients**. If your client does not use a Java keystore (JKS), these conversion steps are not necessary.


4. Create the Kafka client SSL configuration file::

   Sample SSL configuration file::

       cat > producer-mtls.properties << 'EOF'
       security.protocol=SSL
       ssl.truststore.location=/certs/kafka.truststore.jks
       ssl.truststore.password=changeit
       ssl.keystore.location=/certs/kafka.keystore.jks
       ssl.keystore.password=changeit
       ssl.key.password=changeit
       ssl.endpoint.identification.algorithm=
       EOF

5. Run a Kafka tools container with certificates mounted::

       podman run -it --rm \
       --name kafka-mtls-producer \
       -v ~/kafka-mtls-test:/certs:Z \
       apache/kafka:4.1.0 bash


Produce and Verify Telemetry Data
----------------------------------------

1. To verify the available Kafka topics, run the following command::

       KAFKA_LB_IP=<external load balancer IP of the bridge-bridge-lb service>
       /opt/kafka/bin/kafka-topics.sh \
       --bootstrap-server $KAFKA_LB_IP:9094 \
       --command-config /certs/producer-mtls.properties \
       --list

2. Inside the Kafka tools container, produce test data to the Kafka topic that you have created::

       /opt/kafka/bin/kafka-console-producer.sh \
       --bootstrap-server $KAFKA_LB_IP:9094 \
       --topic <kafka topic> \
       --producer.config /certs/producer-mtls.properties

   Sample data::

       Type messages (press Enter after each):
       {"device_id": "xyz-001", "metric": "power", "value": 250, "timestamp": "2024-11-18T10:25:00Z"}
       {"device_id": "xyz-002", "metric": "temperature", "value": 25.5, "timestamp": "2024-11-18T10:25:10Z"}
       {"device_id": "xyz-003", "metric": "fan_speed", "value": 4500, "timestamp": "2024-11-18T10:25:20Z"}
       
       Press Ctrl+D to exit

3. In a new terminal, verify if the messages are received::

       /opt/kafka/bin/kafka-console-consumer.sh \
       --bootstrap-server $KAFKA_LB_IP:9094 \
       --consumer.config /certs/producer-mtls.properties \
       --topic <kafka topic> \
       --group <kafka topic>-consumer-group \
       --from-beginning

You can view the messages in JSON format.

