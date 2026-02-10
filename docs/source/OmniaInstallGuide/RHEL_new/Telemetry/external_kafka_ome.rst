Collect Telemetry Data from OpenManage Enterprise to Omnia Service Kubernetes Clusters
=======================================================================================

This section describes how to configure OpenManage Enterprise to securely stream metrics into the Service Kubernetes clusters using mutual TLS (mTLS).

Prerequisites
--------------

- Ensure that the ``telemetry.yml`` file has been executed.

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

3. In OpenManage Enterprise, navigate to **Configuration > Remote Connectivity**, and select **Enable**.

4. In the Kafka Connectivity wizard, select the **Enable Kafka Connectivity** check box to turn on Kafka integration.

5. In the **OME Identifier** field, enter a unique identifier to be used as the topic prefix for publishing OpenManage Enterprise metrics.

6. In the **Kafka Bootstrap Server** field, enter the Kafka external endpoint displayed by the playbook, along with the port number.

   Example::

      <Kafka LoadBalancer External IP>:<Port Number>

7. From the **Authentication Mode** list, select **SSL**.

8. Under **Server Certificate Validation**, select the **Enable Server Certificate Validation** check box, and upload ``ca.crt`` from ``/opt/omnia/telemetry/external_kafka/``.

9. Under **Client Certificate Configuration**, select the **Enable Client Certificate for mTLS** check box, and upload the client certificate (``user.pfx``) generated in Step 2.  
   Enter the password or passphrase used to generate the certificate, and click **Next**.

10. On the **Data Configuration** page, select the metrics to stream to the Omnia Kubernetes Service cluster, and click **Next**.

11. On the **Group Configuration** page, select the devices and device groups from which metrics should be collected, and click **Next**.

12. Navigate to **Configuration > Remote Connectivity** and verify the following:

    - Under **Connectivity**, a green check mark next to **Connected since** indicates successful connectivity between OpenManage Enterprise and the Omnia Service Kubernetes cluster.
    - Under **Transfer status**, green check marks next to each metric indicate that the selected metrics are being successfully transmitted without errors.
