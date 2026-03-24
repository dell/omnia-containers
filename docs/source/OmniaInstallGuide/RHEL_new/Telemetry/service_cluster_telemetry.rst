=======================================================
Configure Deployment Required for iDRAC Telemetry Service
=======================================================

To deploy iDRAC telemetry service on the service cluster, do the following:

Prerequisites
--------------

* Redfish must be enabled in iDRAC.
* If an internet connection is required on the service Kube node, configure it after the node is booted. 
* iDRAC firmware must be updated to the latest version. 
* Datacenter license must be installed on the nodes.
* Ensure that the correct node service tags are displayed on the iDRAC interface. Otherwise, telemetry data cannot be collected by the ``idrac_telemetry_receiver`` container.
* For telemetry collection on service cluster, all BMC (iDRAC) IPs must be reachable from the service cluster nodes. If the service cluster does not have direct access to the BMC network, configure routing from OIM.
* Ensure that the ``discovery.yml`` playbook has been executed successfully with both ``service_kube_control_plane_x86_64`` and  ``service_kube_node_x86_64`` in the mapping file, and the ``bmc_group_data.csv`` file has been generated.
* Before running the ``telemetry.yml`` playbook for the service cluster, ensure that all the service K8s compute nodes are reachable and booted and have been configured in the service K8s cluster.

Steps
-----------

1. In the mapping file, ensure that the service tag of the service kube node is specified as the parent for the slurm nodes.
2. Configure the ``omnia_config.yml``:

    .. csv-table:: omnia_config.yml
        :file: ../../../Tables/omnia_config_service_cluster.csv
        :header-rows: 1
        :keepspace: 
3. Ensure that the ``telemetry_config.yml`` has the entries specific to iDRAC telemetry support, Victoria, and Kafka based on your requirement.

    .. csv-table:: telemetry_config.yml
        :file: ../../../Tables/telemetry_config.csv
        :header-rows: 1
        :keepspace:

.. note::
    If there is a dedicated setup and BMC IPs are not reachable, enable masquerading to make BMC IP reachable.

    .. code-block:: bash

        iptables -t nat -A POSTROUTING -o "<external interface which has internet>" -j MASQUERADE

        iptables -A FORWARD -i "<local interface which has internet>" -o "<external interface which has internet>" -j ACCEPT
        iptables -A FORWARD -i "<external interface which has internet>" -o "<Local interface which has internet>" -m state --state RELATED,ESTABLISHED -j ACCEPT

    These commands set up Network Address Translation (NAT) and packet forwarding to allow devices on one network interface to access the internet through another interface.


