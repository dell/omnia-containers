Telemetry Storage Configuration
===============================

This procedure describes how to configure storage and resource settings for telemetry components deployed by Omnia.

Prerequisites
-------------

* Understand your cluster size and expected telemetry data volume to appropriately size resources.

Procedure
----------

1. Open the ``telemetry_storage_config.yml`` file available at ``/opt/omnia/input/project_default``.

2. Review the default settings and adjust the values based on your cluster size and expected telemetry data volume. The following table describes all configurable parameters in ``telemetry_storage_config.yml``:

.. csv-table:: telemetry_storage_config.yml
   :file: ../../../Tables/telemetry_storage_config.csv
   :header-rows: 1
   :keepspace:

3. Save the ``telemetry_storage_config.yml`` file.

