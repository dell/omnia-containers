OMNIA Logs
===========
OMNIA maintains comprehensive logs across all playbook executions, container operations, and cluster activities. These logs are essential for monitoring, debugging, and troubleshooting Omnia deployments across OIM, Kubernetes, and Slurm environments.

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

Playbook logs

Logs corresponding to every playbook run can be found under ``/opt/omnia/log/core/playbooks``.

+--------------------------------------------------------------------+--------------------------------------+-----------------------------------------------+
| Location                                                           | Purpose                              | Playbook                                      |
+====================================================================+======================================+===============================================+
| /opt/omnia/log/core/playbooks/discovery.log                        | Discovery logs                       | discovery/discovery.yml                       |
+--------------------------------------------------------------------+--------------------------------------+-----------------------------------------------+
| /opt/omnia/log/core/playbooks/local_repo.log                       | Local Repository logs                | local_repo/local_repo.yml                     |
+--------------------------------------------------------------------+--------------------------------------+-----------------------------------------------+
| /opt/omnia/log/core/playbooks/prepare_oim.log                      | Prepare OIM Logs                     | prepare_oim/prepare_oim.yml                   |
+--------------------------------------------------------------------+--------------------------------------+-----------------------------------------------+
| /opt/omnia/log/core/playbooks/provision.log                        | Provision Logs                       | provision/provision.yml                       |
+--------------------------------------------------------------------+--------------------------------------+-----------------------------------------------+
| /opt/omnia/log/core/playbooks/scheduler.log                        | Scheduler Logs                       | scheduler/scheduler.yml                       |
+--------------------------------------------------------------------+--------------------------------------+-----------------------------------------------+
| /opt/omnia/log/core/playbooks/telemetry.log                        | Telemetry logs                       | telemetry/telemetry.yml                       |
+--------------------------------------------------------------------+--------------------------------------+-----------------------------------------------+
| /opt/omnia/log/core/playbooks/utils.log                            | Utility logs                         | utils/*.yml                                   |
+--------------------------------------------------------------------+--------------------------------------+-----------------------------------------------+
| /opt/omnia/log/core/playbooks/validation_omnia_project_default.log | Omnia input validation report logs   |                                               |
+--------------------------------------------------------------------+--------------------------------------+-----------------------------------------------+
| /opt/omnia/log/core/playbooks/credential_utility.log               | Credential utility logs              | credential_utility/get_config_credentials.yml |
+--------------------------------------------------------------------+--------------------------------------+-----------------------------------------------+
| /opt/omnia/log/core/playbooks/input_validation.log                 | Omnia input validation playbook logs | input_validation/validate_config.yml          |
+--------------------------------------------------------------------+--------------------------------------+-----------------------------------------------+
| /opt/omnia/log/core/playbooks/gitlab_build_stream.log              | GitLab BuildStreaM logs              |                                               |
+--------------------------------------------------------------------+--------------------------------------+-----------------------------------------------+
| /opt/omnia/log/core/playbooks/build_image_<arch>.log               | Build image logs                     | build/build_image_<arch>.yml                  |
+--------------------------------------------------------------------+--------------------------------------+-----------------------------------------------+

Core and other container logs

+--------------------------------------------------------------------+--------------------------------------+
| Location                                                           | Purpose                              |
+====================================================================+======================================+
| /opt/omnia/log/openchami/*log                                      | OpenCHAMI playbook logs              |
+--------------------------------------------------------------------+--------------------------------------+
| /opt/omnia/log/pulp/*log                                           | Pulp container logs                  |
+--------------------------------------------------------------------+--------------------------------------+
| /opt/omnia/log/local_repo/*log                                     | Local repo logs                      |
+--------------------------------------------------------------------+--------------------------------------+
| /opt/omnia/log/core/container/*log                                 | Core container logs                  |
+--------------------------------------------------------------------+--------------------------------------+
| /opt/omnia/log/build_stream/                                       | build_stream pipeline log path       |
+--------------------------------------------------------------------+--------------------------------------+

.. note:: The BuildStreaM and GitLab log paths are available inside the BuildStreaM container.


Logs of Individual Podman Containers in OIM
------------------------------------------------
1. To view the containers running on OIM, run the following command:

   ``podman ps -a``

   The following table shows the status of Omnia containers running on the OIM:

::

    CONTAINER ID   IMAGE                                                        COMMAND                  CREATED        STATUS        PORTS                                        NAMES
    222d8d96554b   localhost/omnia_auth:1.0                                     /bin/sh -c mkdi…         2 days ago     Up 2 days     0.0.0.0:389->389/tcp, 0.0.0.0:636->636/tcp   omnia_auth
    0640a9adfce3   localhost/omnia_core:2.2                                                              2 days ago     Up 2 days     2222/tcp                                     omnia_core
    42515184e9ba   docker.io/pgsty/minio:RELEASE.2026-04-17T00-00-00Z           server /data –co…        2 days ago     Up 2 days     0.0.0.0:9000-9001->9000-9001/tcp             minio-server
    5bbce8efdc27   docker.io/pulp/pulp:3.80                                     /init                    2 days ago     Up 2 days     0.0.0.0:2225->2225/tcp, 80/tcp               pulp
    d0b76ac340c7   docker.io/library/postgres:16                                postgres                 2 days ago     Up 2 days     5432/tcp                                     omnia postgres
    0608aa923b7c   docker.io/dellhpcomniaaisolution/omnia_build_stream:1.1                               2 days ago     Up 2 days                                                  omnia_build_stream
    251709e17ec2   docker.io/library/registry:3.1.0                             /etc/distribution…       2 days ago     Up 2 days     0.0.0.0:5000->5000/tcp                       registry
    992a9ca91d5d   docker.io/library/postgres:11.5-alpine                       postgres                 2 days ago     Up 2 days     5432/tcp                                     postgres
    b731b88c87ff   ghcr.io/openchami/local-ca:v0.2.6                            /step-ca.sh              2 days ago     Up 2 days     9000/tcp                                     step-ca
    ec2a4422424d   docker.io/oryd/hydra:v2.3                                    serve -c /etc/con…       2 days ago     Up 2 days                                                  hydra
    0751a15ca614   ghcr.io/openchami/opaal:v0.3.12                              /opaal/opaal serv…       2 days ago     Up 2 days                                                  opaal-idp
    72e566933565   ghcr.io/openchami/smd:v2.19.3                                /smd                     2 days ago     Up 2 days     27779/tcp                                    smd
    e95d50f8da14   ghcr.io/openchami/opaal:v0.3.12                              /opaal/opaal logi…       2 days ago     Up 2 days                                                  opaal
    3fac48412fe9   ghcr.io/openchami/bss:v1.32.2                                /bin/sh -c /usr/l…       2 days ago     Up 2 days     27778/tcp                                    bss
    81f488e6b5cb   ghcr.io/openchami/cloud-init:v1.3.0                          /usr/local/bin/cl…       2 days ago     Up 2 days                                                  cloud-init-server
    7e970ad459ca   cgr.dev/chainguard/haproxy:latest                            haproxy -f /usr/l…       2 days ago     Up 2 days     0.0.0.0:8081->80/tcp, 0.0.0.0:8443->443/tcp  haproxy
    5f5028bab1cd   ghcr.io/openchami/coresmd:v0.4.3                             /coredhcp                2 days ago     Up 2 days                                                  coresmd-coredhcp
    354f3305a7b8   ghcr.io/openchami/coresmd:v0.4.3                             /coredns                 2 days ago     Up 2 days                                                  coresmd-coredns  

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


Log Management
--------------

This section describes log rotation configuration on the OIM system.

Use ``/etc/logrotate.conf`` to customize how often logs are rotated. For detailed information about logrotate configuration options, see the `official logrotate documentation <https://linux.die.net/man/8/logrotate>`_.

The default settings for ``logrotate.conf`` are: ::

    cat /etc/logrotate.conf
    # see "man logrotate" for details
    # rotate log files weekly
    weekly
    # keep 4 weeks worth of backlogs
    rotate 4
    # create new (empty) log files after rotating old ones
    create
    # use date as a suffix of the rotated file
    dateext
    # uncomment this if you want your log files compressed
    #compress
    # RPM packages drop log rotation information into this directory
    include /etc/logrotate.d
    # system-specific logs may also be configured here.

With the above settings:

* Logs are backed up weekly.

* Data up to 4 weeks old is backed up. Any log backup older than four weeks will be deleted.

.. caution:: Since these logs take up ``/var`` space, sufficient space must be allocated to ``/var`` partition if it's created. If ``/var`` partition space fills up, OIM might crash.

