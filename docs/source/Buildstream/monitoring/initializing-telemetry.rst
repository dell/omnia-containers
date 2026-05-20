.. _buildstream-telemetry:

Step 7: Initialize and Verify Telemetry
==========================================

Prerequisites
---------------

* Ensure that the nodes are powered on and accessible via BMC.

Steps
------

1. To initiate the iDRAC telemetry service on the service cluster, run the ``telemetry.yml`` playbook::

    cd telemetry
    ansible-playbook telemetry.yml 


.. note::
   Service cluster metadata automatically captures the service cluster kube control plane virtual IP.
   As a result, the ``telemetry.yml`` playbook is executed against the VIP rather than an
   individual control plane node.

.. note:: You do not need to run ``telemetry.yml`` if the service cluster is configured only for LDMS. By default, LDMS begins collecting data after the nodes are deployed with the appropriate configuration.

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
