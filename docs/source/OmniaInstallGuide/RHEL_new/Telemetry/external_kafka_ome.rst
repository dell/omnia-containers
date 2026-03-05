Integrate OpenManage Enterprise with Omnia Kafka Pipeline for Secure Telemetry Data Streaming
===========================================================================================

This section describes how to configure OpenManage Enterprise to securely stream metrics into the Service Kubernetes clusters using mutual TLS (mTLS).

Prerequisites
--------------
* Ensure that the ``pod_external_ip_range`` parameter is set in the ``omnia_config.yml`` file for the Service Kubernetes cluster and it is reachable from the OpenManage Enterprise appliance network.
* Ensure Kafka is installed and running in the Service Kubernetes cluster.
* External access to Kafka is available through the following LoadBalancer ports:

  * ``9094`` for ingesting and querying data.

Steps
-----

1. Run the following playbook to retrieve the Kafka connection details and TLS certificates from the Service Kubernetes cluster::

      cd /omnia/utils
      ansible-playbook external_kafka_connect_details.yml

   The ``external_kafka_connect_details.yml`` playbook performs the following:
      - Retrieves the Kafka LoadBalancer external IP.
      - Extracts the server CA certificate and client certificates/keys from the telemetry namespace.
      - Writes the Kafka endpoint and TLS file locations to ``/opt/omnia/telemetry/external_kafka_connect_details.yml``.
      - Saves the TLS files in ``/opt/omnia/telemetry/external_kafka/``:
      - ``ca.crt`` (server certificate)
      - ``user.crt`` (client certificate)
      - ``user.key`` (client key)

   .. note:: If OpenManage Enterprise is installed on a different system than the OIM host, copy ``ca.crt`` to that system before uploading it in the UI.

2. Create a client certificate in ``.pfx`` format for mTLS by running the following command. Provide a passphrase when prompted::

      cd /opt/omnia/telemetry/external_kafka/
      openssl pkcs12 -export -out user.pfx -inkey user.key -in user.crt

   .. image:: ../../../images/ome_certificate_pfx_format.png  

3. In OpenManage Enterprise, navigate to **Configuration > Remote Connectivity**, and select **Enable**.

   .. image:: ../../../images/ome_remote_connectivity.png

4. In the Kafka Connectivity wizard, select the **Enable Kafka Connectivity** check box to turn on Kafka integration.

5. In the **OME Identifier** field, enter a unique identifier to be used as the topic prefix for publishing OpenManage Enterprise metrics.

6. In the **Kafka Bootstrap Server** field, enter the Kafka external endpoint displayed by the playbook, along with the port number.

   Example::

      <Kafka LoadBalancer External IP>:<Port Number>

7. From the **Authentication Mode** list, select **SSL**.

8. Under **Server Certificate Validation**, select the **Enable Server Certificate Validation** check box, and upload ``ca.crt`` from ``/opt/omnia/telemetry/external_kafka/``.

9. Under **Client Certificate Configuration**, select the **Enable Client Certificate for mTLS** check box, and upload the client certificate (``user.pfx``) generated in Step 2.  
   Enter the password or passphrase used to generate the certificate, and click **Next**.

   .. image:: ../../../images/ome_kafka_connectivity.png

10. On the **Data Configuration** page, select the metrics to stream to the Omnia Kubernetes Service cluster, and click **Next**.

   .. image:: ../../../images/ome_data_configuration.png

11. On the **Group Configuration** page, select the devices and device groups from which metrics should be collected, and click **Next**.

   .. image:: ../../../images/ome_group_configuration.png

12. Navigate to **Configuration > Remote Connectivity** and verify the following:

    - Under **Connectivity**, a green check mark next to **Connected since** indicates successful connectivity between OpenManage Enterprise and the Omnia Service Kubernetes cluster.
    - Under **Transfer status**, green check marks next to each metric indicate that the selected metrics are being successfully transmitted without errors.

   .. image:: ../../../images/ome_connectivity_verification.png

Verify OME Telemetry Data in Kafka
---------------------------------------
To verify that OME telemetry data is being successfully published to the OME Kafka topics, do the following:

1. Log in to Service Kubernetes Control plane.

2. Set the required variables using the following command::

      KAFKA_LB_IP=<external IP of bridge-bridge-lb service>
      TOPIC=<OME Topic Name>
      GROUP=ome-consumer-group
      INSTANCE=<a-unique-instance-name>

2. Create a Kafka consumer using the following command::

      curl -s -X POST "http://$KAFKA_LB_IP:8080/consumers/$GROUP" \
        -H 'content-type: application/vnd.kafka.v2+json' \
        -d '{
              "name": "'"$INSTANCE"'",
              "format": "json",
              "auto.offset.reset": "earliest"
            }'

3. Subscribe the consumer to the telemetry topic using the following command::

      curl -s -X POST "http://$KAFKA_LB_IP:8080/consumers/$GROUP/instances/$INSTANCE/subscription" \
        -H 'content-type: application/vnd.kafka.v2+json' \
        -d '{"topics": ["'"$TOPIC"'"]}'

4. Consume messages from the topic using the following command::

      while true; do
        curl -s -X GET "http://$KAFKA_LB_IP:8080/consumers/$GROUP/instances/$INSTANCE/records" \
          -H 'accept: application/vnd.kafka.json.v2+json' | jq '.'
        sleep 2
      done

5. (Optional) Cleanup the consumer using the following command::

      curl -s -X DELETE "http://$KAFKA_LB_IP:8080/consumers/$GROUP/instances/$INSTANCE"

 .. note::
   * **From beginning**: Ensure ``"auto.offset.reset": "earliest"`` when creating the consumer if you want existing data.
   * **Message format**: Use ``"format": "json"`` only if producers publish JSON. Otherwise use ``"binary"`` and decode base64 payloads.
   * **Throughput**: Adjust polling interval; bridge returns empty array when no new records.
   * **404/409 errors**: 404 usually means wrong group/instance name; 409 means already subscribed.
