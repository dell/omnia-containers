Telemetry
==========

⦾ **When a Kubernetes worker node fails, affected telemetry services may take 10 to 15 minutes to fail over to available worker nodes.**

**Resolution**: Wait for some time for the telemetry services to recover and fail over automatically.


⦾ **LDMS telemetry data is not collected from newly added cluster nodes**

When new nodes are added to the Slurm cluster and telemetry is enabled using LDMS, perform the following steps to ensure that metrics from the newly added nodes are successfully collected and stored.

1. After executing the ``discovery.yaml`` playbook, allow sufficient time for the newly added nodes to complete their boot sequence. The newly added nodes may take 5 to 10 minutes to boot and initialize.

2. SSH into each newly added node and confirm that the cloud initialization (Cloud-Init) process has completed successfully. Use the following command:

    ::

        ssh <new-slurm-node-hostname>
        # Check cloud-init output logs
        tail -100 /var/log/cloud-init-output.log

   Verify the following:

      - The log ends with a message similar to: ``Cloud-init v.X.X.X finished``
      - No errors are present related to LDMS sampler setup or configuration.

3. Confirm that the LDMS sampler service is active and collecting metrics on the new node.

   To verify that the sampler is collecting metrics, run the following command:

    ::

        # Check service status
        sudo systemctl status ldmsd.sampler.service

    To verify that the sampler is collecting metrics, run the following command:

    ::

        /opt/ovis-ldms/sbin/ldms_ls -a ovis \
        -A conf=/opt/ovis-ldms/etc/ldms/ldmsauth.conf \
        -p 10001 -h localhost

Successful output indicates that the sampler is running and exporting metrics locally.

4. SSH into kube vip and restart the LDMS store daemon so it can detect and ingest metrics from the newly added nodes.

    ::

        ssh <kube-vip>
        # Restart the store daemon StatefulSet
        kubectl rollout restart statefulset nersc-ldms-store-slurm-cluster -n telemetry

    To monitor the pod restart process, run the following command:

    ::

        kubectl get pods -n telemetry -w | grep store

5. Allow 2–5 minutes for the store daemon to reconnect to the aggregator and begin processing metrics from the new nodes. To check the store daemon logs, run the following command:

    ::

        kubectl logs -n telemetry nersc-ldms-store-slurm-cluster-0-0 --tail=200 | grep <new-node-hostname>

    To Confirm that metrics are being published to Apache Kafka, run the following command.

    .. note:: Ensure that the Kafka consumer is created and it is subscribed to the LDMS topic. If not, run the steps 2 and 3 from :ref:`verify_ldms_messages_in_kafka`. 

    ::

        curl -s -X GET http://${KAFKA_LB_IP}:8080/consumers/ldms-consumer-group/instances/ldms-consumer-1/records \
        -H 'accept: application/vnd.kafka.json.v2+json' | \
        jq '.[] | select(.value.hostname == "<new-node-hostname>.domain.test")'

Successful output indicates that telemetry data from the newly added node is being collected and forwarded through the telemetry pipeline.

