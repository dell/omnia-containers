OIM Logs
----------

.. caution:: It is not recommended to delete the below log files or the directories they reside in.

.. note:: If you want log files for specific playbook execution, ensure to use the ``cd`` command to move into the specific directory before executing the playbook. For example, if you want local repo logs, ensure to enter ``cd local_repo`` before executing the playbook. If the directory is not changed, all the playbook execution log files will be consolidated and provided as part of omnia logs located in ``/opt/omnia/log/core/playbooks``.


Cluster Log Collection
-----------------------

Omnia provides a one-shot log collection playbook for gathering cluster logs from Kubernetes and Slurm nodes for debugging and support handoff. For detailed information on log collection, see :doc:`../Omnia/log_collector`.

**Usage**

To collect logs from the cluster, execute the following commands::

    ssh omnia_core
    cd omnia/log_collector
    ansible-playbook collect.yml

**Collection modes**

* **Full mode** (default): Collects all logs from target nodes

::

    ansible-playbook collect.yml

* **Curated support mode**: Excludes temporary and stale log files

::

    ansible-playbook collect.yml --tags curated_support

**Output artifacts**

* Workspace: ``/opt/omnia/collector_logs``
* Bundle: ``omnia_logs_<YYYYMMDD-HHMMSS>.tar.gz``
* Metadata: ``metadata.json`` (included in bundle)
* Checksum: ``.sha256`` file for integrity verification

**Prerequisites**

* PXE mapping file must exist at ``/opt/omnia/input/project_default/pxe_mapping_file.csv``
* Nodes must be reachable from OIM

   
Omnia playbook and container logs
---------------------------------

The following table provides an overview of the various Omnia log files, their locations, and their purposes for monitoring.

+------------------------------------------------------------------------+---------------------------------------------+
| Location                                                               | Purpose                                     |
+========================================================================+=============================================+
| /opt/omnia/log/core/playbooks/discovery.log                            | Discovery logs                              |
+------------------------------------------------------------------------+---------------------------------------------+
| /opt/omnia/log/core/playbooks/local_repo.log                           | Local Repository logs                       |
+------------------------------------------------------------------------+---------------------------------------------+
| /opt/omnia/log/core/playbooks/prepare_oim.log                          | Prepare OIM Logs                            |
+------------------------------------------------------------------------+---------------------------------------------+
| /opt/omnia/log/core/playbooks/provision.log                            | Provision Logs                              |
+------------------------------------------------------------------------+---------------------------------------------+
| /opt/omnia/log/core/playbooks/scheduler.log                            | Scheduler Logs                              |
+------------------------------------------------------------------------+---------------------------------------------+
| /opt/omnia/log/core/playbooks/telemetry.log                            | Telemetry logs                              |
+------------------------------------------------------------------------+---------------------------------------------+
| /opt/omnia/log/core/playbooks/utils.log                                | Utility logs                                |
+------------------------------------------------------------------------+---------------------------------------------+
| /opt/omnia/log/core/playbooks/credential_utility.log                   | Credential utility logs                     |
+------------------------------------------------------------------------+---------------------------------------------+
| /opt/omnia/log/openchami/*log                                          | OpenCHAMI playbook logs                     |
+------------------------------------------------------------------------+---------------------------------------------+
| /opt/omnia/log/pulp/*log                                               | Pulp container logs                         |
+------------------------------------------------------------------------+---------------------------------------------+
| /opt/omnia/log/local_repo/*log                                         | Local repo logs                             |
+------------------------------------------------------------------------+---------------------------------------------+
| /opt/omnia/log/core/container/*log                                     | Core container logs                         |
+------------------------------------------------------------------------+---------------------------------------------+
| /opt/omnia/log/core/playbooks/validation_omnia_project_default.log     | Omnia input validation report logs          |
+------------------------------------------------------------------------+---------------------------------------------+
| /opt/omnia/log/core/playbooks/input_validation.log                     | Omnia input validation playbook logs        |
+------------------------------------------------------------------------+---------------------------------------------+
| /opt/omnia/log/core/playbooks/gitlab_build_stream.log                  | GitLab BuildStreaM logs                     |
+------------------------------------------------------------------------+---------------------------------------------+
| /opt/omnia/log/build_stream/                                           | BuildStreaM logs                            |
+------------------------------------------------------------------------+---------------------------------------------+


Logs of Individual Podman Containers in OIM
------------------------------------------------
1. To view the containers running on OIM, run the following command:

   ``podman ps -a``

   The following table shows the status of Omnia containers running on the OIM:

.. csv-table:: Podman Logs
   :file: ../Tables/podman_logs.csv
   :header-rows: 1
   :keepspace:  

2. To view the logs from a specific container, run the following command:

   ``podman logs <container name>``
     
3. Alternatively, if the container is managed as a systemd service, you can view the logs using the following command:

   ``journalctl -xeu <container name>``


Logs of Individual K8s Containers on Service Cluster
-----------------------------------------------------
   1. A list of namespaces and their corresponding pods can be obtained using:

      ``kubectl get pods -A``

   2. Get a list of containers for the pod in question using:

      ``kubectl get pods <pod_name> -o jsonpath='{.spec.containers[*].name}'``

   3. Once you have the namespace, pod and container names, run the below command to get the required logs:

      ``kubectl logs pod <pod_name> -n <namespace> -c <container_name>``

