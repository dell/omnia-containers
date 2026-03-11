LDMS Telemetry
==============

⦾ **Manual Workaround for LDMS Data Collection After Adding New Slurm Nodes**

**Post-Node Addition Telemetry Verification**

When new nodes are added to the Slurm cluster and telemetry is enabled using LDMS, perform the following steps to ensure that metrics from the newly added nodes are successfully collected and stored.

**1. Allow Newly Added Nodes to Boot**

After executing the node discovery playbook, allow sufficient time for the newly added nodes to complete their boot sequence.

Typical boot and initialization time: 5–10 minutes

**2. Verify Cloud-Init Completion**

SSH into each newly added node and confirm that the cloud initialization process has completed successfully.

::

    ssh <new-slurm-node-hostname>
    # Check cloud-init output logs
    tail -100 /var/log/cloud-init-output.log

Verify the following:

- The log ends with a message similar to: ``Cloud-init v.X.X.X finished``
- No errors are present related to LDMS sampler setup or configuration.

**3. Verify LDMS Sampler Service**

Confirm that the LDMS sampler service is active and collecting metrics on the new node.

::

    # Check service status
    sudo systemctl status ldmsd.sampler.service

Verify that the sampler is collecting metrics:

::

    /opt/ovis-ldms/sbin/ldms_ls -a ovis \
    -A conf=/opt/ovis-ldms/etc/ldms/ldmsauth.conf \
    -p 10001 -h localhost

Successful output indicates that the sampler is running and exporting metrics locally.

**4. Restart the LDMS Store Daemon**

SSH into the Kubernetes control plane node where kube vip is configured and restart the LDMS store daemon so it can detect and ingest metrics from the newly added nodes.

::

    ssh <service-kube-control-plane-first-node>
    # Restart the store daemon StatefulSet
    kubectl rollout restart statefulset nersc-ldms-store-slurm-cluster -n telemetry

Monitor the pod restart process:

::

    kubectl get pods -n telemetry -w | grep store

**5. Verify Telemetry Data Collection**

Allow 2–5 minutes for the store daemon to reconnect to the aggregator and begin processing metrics from the new nodes.

Check the store daemon logs:

::

    kubectl logs -n telemetry nersc-ldms-store-slurm-cluster-0-0 --tail=200 | grep <new-node-hostname>

Confirm that metrics are being published to Apache Kafka:

::

    curl -s -X GET http://${KAFKA_LB_IP}:8080/consumers/ldms-consumer-group/instances/ldms-consumer-1/records \
      -H 'accept: application/vnd.kafka.json.v2+json' | \
      jq '.[] | select(.value.hostname == "<new-node-hostname>.domain.test")'

Successful output indicates that telemetry data from the newly added node is being collected and forwarded through the telemetry pipeline.
