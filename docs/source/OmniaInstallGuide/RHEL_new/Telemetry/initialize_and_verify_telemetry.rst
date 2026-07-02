Step 15: Initialize telemetry
=============================

Prerequisites
---------------

* Ensure that the ``provision.yml`` playbook has been executed successfully with ``service_kube_control_plane`` and ``service_kube_node`` in the mapping file.
* Ensure that all the nodes are booted and pods are running before executing the telemetry playbook.

.. note::
   If you want to enable any of the telemetry components after making changes in ``telemetry_config.yml`` after the first successful deployment of telemetry and if Kubernetes is already up and running, you will have to execute the ``telemetry.sh`` script on kube-control-plane present at path ``<K8s_NFS_mount_point>/telemetry/telemetry.sh``.

Steps
------

To initiate the iDRAC telemetry service on the service cluster, run the ``telemetry.yml`` playbook::

    cd telemetry
    ansible-playbook telemetry.yml 


.. caution:: The ``telemetry.yml`` playbook will fail if you run it before executing the ``discovery.yml`` playbook.

.. note::
   Service cluster metadata automatically captures the service cluster kube control plane virtual IP.
   As a result, the ``telemetry.yml`` playbook is executed against the VIP rather than an
   individual control plane node.

.. note:: Run the ``telemetry.yml`` playbook only if iDRAC telemetry is enabled. It is not required for other telemetry types.

Collect Telemetry from External Nodes
------------------------------------

To collect telemetry from the external nodes, do the following:

1. Update the BMC IP of the external nodes in the ``/opt/omnia/telemetry/bmc_group_data.csv``.  
   The ``GROUP_NAME`` and ``PARENT`` fields must be left blank.

2. Run the ``telemetry.yml`` playbook using the following command::

       ansible-playbook telemetry.yml

Sample::

    BMC_IP,GROUP_NAME,PARENT
    <IP Address>,,
