================================================
Configure Deployment Required for PowerScale Telemetry
================================================

Using Omnia, you can deploy PowerScale Telemetry to collect storage performance metrics and logs from Dell PowerScale storage nodes. The deployment includes configuring PowerScale Telemetry components on the service Kubernetes cluster, integrating with Dell CSM Metrics for PowerScale with an OpenTelemetry Collector, and ingesting logs via the syslog pipeline.

PowerScale Telemetry collects storage performance metrics and logs. PowerScale Telemetry includes these components:

- **CSM Metrics for PowerScale:** Queries the OneFS API and emits metrics to an OpenTelemetry Collector.
- **OpenTelemetry Collector:** Receives metrics from CSM Metrics and exposes a Prometheus endpoint for scraping.
- **vmagent:** Scrapes the OpenTelemetry Collector Prometheus endpoint over TLS and forwards metrics to VictoriaMetrics.
- **VLAgent:** Receives PowerScale syslog events and forwards them to VictoriaLogs.
- **CSI Driver for Dell PowerScale:** Required for Omnia-orchestrated deployment mode.
- **cert-manager:** Required for TLS certificate management in Omnia-orchestrated mode.

Supported Metrics and Logs
---------------------------

**Metrics:**

The PowerScale metrics include the following:

- **Performance:** Protocol-level IOPS (NFS, SMB, S3), throughput (bytes/s), read/write latency
- **Capacity:** Total cluster capacity, used capacity, available capacity, per-node capacity
- **Health:** Node online/offline status, disk health, cluster rebalance status, protection group status
- **Topology:** Cluster node membership, node roles, interconnect layout, protection domain mapping

For more details on PowerScale metrics, see `Supported PowerScale Metrics <https://dell.github.io/csm-docs/docs/concepts/observability/metrics/powerscale/>`_

**Logs**

The PowerScale logs include the following:

- Capacity warnings, disk failures, node state changes, protocol errors
- Events are labeled with host/cluster, severity, and facility

Prerequisites
---------------

* Ensure that the ``provision.yml`` playbook has been executed successfully with ``service_kube_control_plane`` and ``service_kube_node`` in the mapping file.
* For Omnia-orchestrated mode, ensure the service Kubernetes cluster has sufficient resources to run CSM Metrics, OpenTelemetry Collector, CSI Driver, and cert-manager.
* For operator-provided mode, ensure the external OpenTelemetry Collector endpoint is accessible from the service cluster over TLS.
* Ensure network connectivity between the PowerScale cluster and the Omnia log agent for syslog integration.
* For PowerScale log collection, configure the following settings on the PowerScale cluster:

    * Enable syslog forwarding from PowerScale to Omnia using the following command::

        .. code-block:: bash

            isi audit setting modify --syslog-forwarding-enabled true

    .. image:: ../../../images/powerscale_syslog_logs_prereq.png


    .. note::
       To disable syslog forwarding, run the following command::
 
        isi audit setting modify --syslog-forwarding-enabled false

       To completely disable syslog forwarding and clear syslog servers, run the following command::

         isi audit settings global modify --config-syslog-enabled=0 --clear-config-syslog-servers
         isi audit settings global modify --system-syslog-enabled=0 --clear-system-syslog-servers
         isi audit settings global modify --clear-protocol-syslog-serverss

   
    * Configure the vlagent loadbalancer IP address (e.g., ``172.16.107.1``) for log delivery.

        .. image:: ../../../images/powerscale_vmselect_logs_prereq.png

Procedure
----------

1. Specify the following entries in the ``software_config.json``.  For detailed information on updating the ``software_config.json``, see :doc:`../CreateLocalRepo/InputParameters`.

    .. note:: The entry must be present when ``telemetry_sources > powerscale > metrics_enabled`` is set to ``true`` in the ``telemetry_config.yml`` file.

    .. code-block:: json

        {"name": "service_k8s", "version": "1.34.1", "arch": ["x86_64"]},
        {"name": "csi_driver_powerscale", "arch": ["x86_64"]}

2. Configure the ``omnia_config.yml``:

    .. csv-table:: omnia_config.yml
        :file: ../../../Tables/omnia_config_service_cluster.csv
        :header-rows: 1
        :widths: 35,30,35
        :keepspace:

3. Ensure that the ``telemetry_config.yml`` has the entries specific for PowerScale Telemetry deployment.

    .. note:: PowerScale Telemetry supports independent feature flags for metric collection and log collection. You can enable or disable each independently.

    .. csv-table:: telemetry_config.yml
        :file: ../../../Tables/telemetry_config.csv
        :header-rows: 1
        :keepspace:

4. Configure PowerScale-specific parameters in ``telemetry_config.yml``:

    - **powerscale_telemetry_support:** Enable or disable PowerScale Telemetry (``true`` or ``false``)
    - **powerscale_metrics_enabled:** Enable or disable PowerScale metric collection (``true`` or ``false``)
    - **powerscale_logs_enabled:** Enable or disable PowerScale log collection (``true`` or ``false``)
    - **powerscale_cluster_address:** PowerScale cluster address
    - **powerscale_credentials:** PowerScale credentials for CSM Metrics access
    - **deployment_mode:** Select deployment mode (``omnia-orchestrated`` or ``operator-provided``)
    - **external_otel_endpoint:** (Optional) External OpenTelemetry Collector endpoint URL for operator-provided mode

5. For Omnia-orchestrated mode, configure the CSM Observability values file:

    - Provide the path to the CSM Observability (Karavi Observability) values.yaml file in ``telemetry_config.yml``
    - Reference: https://raw.githubusercontent.com/dell/helm-charts/refs/heads/release-v1.16.3/charts/karavi-observability/values.yaml
    - **Important**: In the values.yaml file, only set ``karaviMetricsPowerscale > enabled: true``. All other parameters should be set to ``false``.
    - **Health Metrics**: For CSI PowerScale health metrics, enable ``controller > healthMonitor > enabled: true`` and ``node > healthMonitor > enabled: true`` in the CSI PowerScale values.yaml (https://raw.githubusercontent.com/dell/helm-charts/csi-isilon-2.15.0/charts/csi-isilon/values.yaml).

6. For dual-destination delivery (optional), configure an external observability endpoint:

    - Specify the external VictoriaMetrics endpoint in ``telemetry_config.yml``
    - Metrics will be delivered to both the internal time-series database and the external endpoint independently

Health Monitor Metrics
----------------------

When the CSI PowerScale health monitor is enabled (``controller > healthMonitor > enabled: true`` and ``node > healthMonitor > enabled: true`` in the CSI PowerScale values.yaml), Omnia collects the following additional health metrics:

**PV Metrics:**

- ``powerscale_volume_status`` - PV phase (1=Bound, 0=Other) [pv_name, phase]
- ``powerscale_volume_count`` - Total PowerScale PVs by phase [phase]
- ``powerscale_volume_capacity_bytes`` - PV capacity in bytes [pv_name]
- ``powerscale_volume_info`` - PV metadata [pv_name, phase, storage_class, reclaim_policy, access_modes, volume_handle, pvc_name, pvc_namespace]
- ``powerscale_volume_age_seconds`` - Seconds since PV creation [pv_name]

**PVC Metrics:**

- ``powerscale_pvc_status_phase`` - PVC phase (1=Bound, 0=Other) [pvc_name, pvc_namespace, phase]
- ``powerscale_pvc_requested_bytes`` - PVC requested storage in bytes [pvc_name, pvc_namespace]
- ``powerscale_pvc_count`` - Total PowerScale PVCs by phase [phase]

**Health Event Metrics:**

- ``powerscale_volume_health_abnormal`` - Volume condition abnormal (1=abnormal, 0=healthy) [pvc_name, pvc_namespace, pv_name]
- ``powerscale_volume_abnormal_events_total`` - Total VolumeConditionAbnormal events [pvc_name, pvc_namespace]
- ``powerscale_node_failure_events_total`` - Total node failure events [node]

**Node Metrics:**

- ``powerscale_node_ready`` - Node Ready condition (1=True, 0=False) [node]

**Storage Class Metrics:**

- ``powerscale_storageclass_info`` - StorageClass metadata [storageclass, provisioner, reclaim_policy, volume_binding_mode, allow_volume_expansion]

**Aggregate Summary:**

- ``powerscale_total_capacity_bytes`` - Total capacity of all PowerScale PVs in bytes

Feature Flags and Deployment Modes
------------------------------------

**Independent Feature Flags**

You can independently enable or disable PowerScale metric collection and PowerScale log collection. Disabling one flag does not affect the other.

**Deployment Mode Selection**

Select one of two deployment modes in ``telemetry_config.yml``:

*Omnia-orchestrated:* Omnia deploys CSM Metrics, the OpenTelemetry Collector, the CSI Driver for Dell PowerScale, and cert-manager on the service cluster. This mode requires CSI Driver for Dell PowerScale and cert-manager to be installed on the service Kubernetes cluster.

*Operator-provided endpoint:* The operator provides the Prometheus endpoint URL of an externally managed OpenTelemetry Collector. Omnia configures vmagent to scrape that endpoint without deploying CSM Metrics or OTel Collector pods.

TLS and Authentication
---------------------

All metric scraping uses TLS. Authentication uses Kubernetes service-account tokens. Mutual TLS (mTLS) is not required—the connection is encrypted but the PowerScale-side endpoint does not validate client identity via certificate exchange. TLS is enforced for all off-cluster communications.

Operational Health Monitoring
------------------------------

The PowerScale telemetry integration exposes operational health metrics including:

- Scrape success rate
- Scrape error count
- Ingest latency
- Log delivery error rate

These metrics are available for alerting and monitoring via the same observability stack. The OpenTelemetry Collector endpoint maintains availability exceeding 98% over a 24-hour period.

Feature Constraints
-------------------

- Supports a single PowerScale cluster per Omnia deployment
- Omnia-orchestrated mode requires CSI Driver for Dell PowerScale and cert-manager to be installed on the service Kubernetes cluster
- Mutual TLS is not required on the metrics exporter endpoint; transport is encrypted but client identity is not verified via certificate exchange
- Syslog integration requires network connectivity between the PowerScale cluster and the Omnia log agent
- The metric set is aligned with Dell CSM Metrics capabilities; metrics not exposed by CSM Metrics are not available

Performance Requirements
-------------------------

- Key PowerScale metrics appear in the time-series database within one scrape interval of emission
- Syslog events arrive in the log database with less than 1-minute end-to-end latency under nominal load
- OpenTelemetry Collector endpoint availability exceeds 98% over a 24-hour period
- Scrape interval is configurable between 30 and 60 seconds


Enable and Disable PowerScale Telemetry
--------------------------------------

You can enable or disable PowerScale telemetry using the following commands:

**To disable PowerScale telemetry:**

.. code-block:: bash

   ansible-playbook telemetry/telemetry_disable.yml --tags powerscale

**After disabling PowerScale telemetry, to enable PowerScale telemetry again:**

.. code-block:: bash

   ansible-playbook telemetry/telemetry_enable.yml --tags powerscale


.. note::
   * Set ``powerscale.metrics_enabled`` to ``true`` or ``false`` in the ``telemetry_config.yml`` file.
   * The ``powerscale`` tag is mandatory to perform the action.

Enable and Disable PowerScale Logs
-----------------------------------

You can enable or disable PowerScale logs using the following commands:

**To disable PowerScale logs:**

.. code-block:: bash

   ansible-playbook telemetry/telemetry_disable.yml --tags powerscale

**After disabling PowerScale logs, to enable PowerScale logs again:**

.. code-block:: bash

   ansible-playbook telemetry/telemetry_enable.yml --tags powerscale

.. note::
   To disable PowerScale logs, remove the IP from the command and set ``enabled`` to ``no``.