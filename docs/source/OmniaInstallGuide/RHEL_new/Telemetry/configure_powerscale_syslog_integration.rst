Configure PowerScale Syslog Integration with Omnia Telemetry for Secure Logs Streaming
======================================================================================

This section describes the configuration for PowerScale syslog integration.

Prerequisites
-------------

Ensure that the following prerequisites are met:

* Ensure that the ``provision.yml`` playbook has been executed successfully with ``service_kube_control_plane`` and ``service_kube_node`` in the mapping file.
* Ensure network connectivity between the PowerScale cluster and the Omnia log agent for syslog integration.
* For PowerScale log collection, configure the following settings on the PowerScale cluster:

    * Enable syslog forwarding from PowerScale to Omnia using the following command::

         isi audit setting modify --syslog-forwarding-enabled true

      .. image:: ../../../images/powerscale_syslog_logs_prereq.png

    * Enable for required zones using the following command::

        isi audit settings global modify --add-audited-zones=<comma separated zone names>

    * Configure the vlagent loadbalancer IP address (e.g., 10.43.1.27) for log delivery to Victoria logs configured using Omnia::

        isi audit settings global modify --config-syslog-enabled=1 --config-syslog-servers=<vlagent loadbalancer ip>:514 --config-syslog-tls-enabled=0
        isi audit settings global modify --protocol-syslog-servers=<vlagent loadbalancer ip>:514 --protocol-syslog-tls-enabled=0
        isi audit settings global modify --system-syslog-enabled=1 --system-syslog-servers=<vlagent loadbalancer ip>:514 --system-syslog-tls-enabled=0

      .. image:: ../../../images/powerscale_audited_zones_logs_prereq.png

Configuration Steps
------------------

1. Specify the following entries in the ``software_config.json``. For detailed information on updating the ``software_config.json``, see :doc:`../CreateLocalRepo/InputParameters`.

    .. note:: The entry must be present when ``telemetry_sources > powerscale > metrics_enabled`` is set to ``true`` in the ``telemetry_config.yml`` file.

    .. code-block:: json

        {"name": "service_k8s", "version": "1.35.1", "arch": ["x86_64"]},
        {"name": "csi_driver_powerscale", "version": "2.17.0", "arch": ["x86_64"]}

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

    * **telemetry_sources > powerscale > metrics_enabled:** Enable or disable PowerScale metric collection (``true`` or ``false``)
    * **telemetry_sources > powerscale > logs_enabled:** Enable or disable PowerScale log collection (``true`` or ``false``)


