.. _telemetry-vector-configuration:

=========================================================================
Configure Vector Telemetry Pipeline to Route Data to Victoria from Kafka
=========================================================================

Using Omnia, you can deploy Vector as a high-performance data pipeline tool for collecting, transforming, and routing telemetry data from LDMS and OpenManage Enterprise (OME) sources to VictoriaMetrics and VictoriaLogs. The deployment includes Vector-LDMS and Vector-OME pods as Kafka consumers, vmagent-vector as a dedicated write-buffer for metrics, and vlagent-vector as a log forwarding agent.

Vector provides the following components:

- **Vector-LDMS:** Kafka consumer for LDMS metrics, consumes from the `ldms` topic and routes to VictoriaMetrics via vmagent-vector
- **Vector-OME:** Kafka consumer for OME telemetry, consumes from `ome.*` topics and routes metrics to VictoriaMetrics and logs to VictoriaLogs
- **vmagent-vector:** Dedicated vmagent instance as a write-buffer between Vector pods and vminsert. Accepts `prometheus_remote_write` on port 8429, buffers to disk, and forwards to vminsert. Separate from the existing scraper vmagent to isolate failure domains.
- **vlagent-vector:** Dedicated VictoriaLogs forwarding agent deployed as a log write-buffer for Vector pods. Accepts JSON Lines on an HTTP endpoint (port 9427), buffers to disk, and forwards to vlinsert. Required for Vector-OME log/event sinks.

For more details on Vector, see `Vector Documentation <https://vector.dev/docs/>`_

Vector enables the following data flows:

- **LDMS metrics:** LDMS Store (store_avro_kafka) → Kafka 'ldms' topic → Vector-LDMS → vmagent-vector → vminsert → VictoriaMetrics
- **OME metrics:** OME → Kafka 'ome.*' topics → Vector-OME → vmagent-vector → vminsert → VictoriaMetrics
- **OME logs:** OME → Kafka 'ome.*' topics → Vector-OME → vlagent-vector → vlinsert → VictoriaLogs


Prerequisites
---------------

* Ensure that the ``provision.yml`` playbook has been executed successfully with ``service_kube_control_plane`` and ``service_kube_node`` in the mapping file.
* Ensure that Kafka is deployed and operational via Strimzi operator.
* Ensure that VictoriaMetrics cluster mode is deployed with vminsert, vmstorage, and vmselect components.
* Ensure that VictoriaLogs cluster mode is deployed with vlinsert, vlstorage, and vlselect components (required for Vector-OME logs).

Steps
-------

1. Specify the following entries in the ``software_config.json``. If any entry is missing, Omnia skips Vector deployment and logs an informational message. 
   For more information, see :doc:`../CreateLocalRepo/InputParameters`.

.. code-block:: json

    {"name": "service_k8s", "version": "1.34.1", "arch": ["x86_64"]}

2. Configure the ``telemetry_config.yml`` to enable Vector telemetry bridges:

   .. note:: Vector telemetry bridges are controlled by feature flags in ``telemetry_config.yml``. Set ``telemetry_bridges > vector_ldms > metrics_enabled`` to enable Vector-LDMS, and ``telemetry_bridges > vector_ome > metrics_enabled`` to enable Vector-OME metrics routing. For Vector-OME logs routing, set ``telemetry_bridges > vector_ome > logs_enabled``.

   .. csv-table:: telemetry_config.yml
        :file: ../../../Tables/telemetry_config.csv
        :header-rows: 1
        :keepspace:

3. For Vector-LDMS, ensure that LDMS is configured and the ``store_avro_kafka`` plugin is producing to the Kafka `ldms` topic. Vector-LDMS consumes from this topic.

4. For Vector-OME, ensure that OME is configured externally and producing to Kafka `ome.*` topics via the external mTLS listener (port 9094). Run the ``external_kafka_connect_details.yml`` playbook to configure OME connectivity.

5. Run the ``telemetry.yml`` playbook to deploy Vector components::

    cd /opt/omnia/telemetry
    ansible-playbook telemetry.yml

The playbook deploys the following components based on the configured feature flags:

- **vmagent-vector:** Dedicated vmagent instance as a write-buffer (deployed when any Vector pipeline is enabled)
- **Vector-LDMS:** Kafka consumer for LDMS metrics (deployed when ``telemetry_bridges > vector_ldms > metrics_enabled = true``)
- **Vector-OME:** Kafka consumer for OME telemetry (deployed when ``telemetry_bridges > vector_ome > metrics_enabled = true`` or ``telemetry_bridges > vector_ome > logs_enabled = true``)
- **vlagent-vector:** VictoriaLogs forwarding agent for logs (deployed when ``telemetry_bridges > vector_ome > logs_enabled = true``)
- **Kafka topics and ACLs:** For OME topics (deployed when ``telemetry_bridges > vector_ome > metrics_enabled = true`` or ``telemetry_bridges > vector_ome > logs_enabled = true``)
- **KafkaUser resources:** For Vector-OME mTLS credentials (deployed when ``telemetry_bridges > vector_ome > metrics_enabled = true`` or ``telemetry_bridges > vector_ome > logs_enabled = true``)

.. note:: Vector-LDMS reuses the existing ``kafkapump`` KafkaUser for mTLS credentials. Vector-OME requires a new KafkaUser (``vector-ome-user``) because OME is an external producer with a different security domain.
