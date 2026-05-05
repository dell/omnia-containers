Step 15: Initialize and Verify Telemetry
==================================================

Prerequisites
---------------

* Ensure that the ``discovery.yml`` playbook has been executed successfully with ``service_kube_control_plane`` and ``service_kube_node`` in the mapping file.

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
