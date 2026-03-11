================================================
Configure Deployment Required for LDMS Telemetry 
================================================

Using Omnia, you can deploy Lightweight Distributed Metric Service (LDMS) to collect in-band telemetry from Slurm clusters. The deployment includes installing LDMS producers on Slurm nodes, deploying LDMS aggregator and store components on Service Kubernetes nodes, and integrating LDMS with Kafka for downstream telemetry processing.

LDMS collects system metrics such as CPU, memory, network, I/O, and Slurm job statistics. LDMS includes these components:

- **LDMS producer (collector):** Collects local system metrics and runs on Slurm controller, compute, and login nodes.
- **LDMS aggregator:** Receives and aggregates metrics from producers. Runs as a Kubernetes pod.
- **LDMS store:** Buffers and stores metric batches reliably. Runs as a Kubernetes pod.
- **Kafka broker:** Handles telemetry streaming for consumption by downstream systems.

For more details on LDMS, see `Lightweight Distributed Metric Service <https://github.com/ovis-hpc/ldms>`_


During deployment, Omnia attaches LDMS aggregator and store pods to the admin network. This configuration improves throughput between Slurm nodes and the Kubernetes cluster.

Supported LDMS Plugins
-----------------------

The following LDMS plugins are supported in Omnia:

* **meminfo:** Memory usage statistics
* **procstat2:** Process statistics
* **vmstat:** Virtual memory statistics
* **loadavg:** System load average
* **procnetdev2:** Network interface statistics

.. note:: The LDMS Slurm sampler metrics are not supported in the current telemetry deployment.

Prerequisites
---------------

* Ensure that the ``discovery.yml`` playbook has been executed successfully with ``service_kube_control_plane`` and ``service_kube_node`` in the mapping file.

Steps
-------

1. Specify the following entries in the ``software_config.json``. If any entry is missing, Omnia skips LDMS deployment and logs an informational message. 
   For more information, see :doc:`../CreateLocalRepo/InputParameters`.

.. code-block:: json

    {"name": "slurm_custom", "arch": ["x86_64","aarch64"]},
    {"name": "service_k8s", "version": "1.34.1", "arch": ["x86_64"]},
    {"name": "ldms", "arch": ["x86_64", "aarch64"]}

3. Ensure the ``ldms.json`` file contains the following entries.

 .. note:: If the LDMS RPM is not available, refer to  `Building LDMS Producer RPM Package <https://github.com/dell/omnia-artifactory?tab=readme-ov-file#building-ldms-producer-rpm-package>`_ for instructions on building LDMS RPMs. 


The following ``ldms.json`` sample is for ``x86_64``. For ``aarch64`` architecture, update the repo name accordingly in the ``ldms.json`` file.

.. code-block:: json

    {
        "ldms": {
            "cluster": [
                {"package": "python3-devel", "type": "rpm", "repo_name": "x86_64_appstream"},
                {"package": "python3-cython", "type": "rpm", "repo_name": "x86_64_appstream"},
                {"package": "openssl-libs", "type": "rpm", "repo_name": "x86_64_baseos"},
                {"package": "ovis-ldms", "type": "rpm", "repo_name": "x86_64_ldms"}
            ]
        }
    }
    
4. In ``local_repo_config.yml``, specify the paths for the ``ovis-ldms`` RPMs accordingly for the ``user_repo_url_x86_64`` and ``user_repo_url_aarch64``.

5. Configure the ``omnia_config.yml``:

    .. csv-table:: omnia_config.yml
        :file: ../../../Tables/omnia_config_service_cluster.csv
        :header-rows: 1
        :widths: 35,30,35
        :keepspace: 

6. Ensure that the ``telemetry_config.yml`` has the entries specific for LDMS and Kafka deployment.

    .. note:: For LDMS telemetry configuration, at least one sampler plugin is mandatory to collect system metrics.

    .. csv-table:: telemetry_config.yml
        :file: ../../../Tables/telemetry_config.csv
        :header-rows: 1
        :keepspace: