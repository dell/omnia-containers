Accessing the MySQL Database
============================

After ``telemetry.yml`` has been executed for the service cluster, you can check the MySQL database inside the ``mysqldb`` container. To view these logs, do the following:

1. Use the following command to get the names of all the telemetry pods::

    kubectl get pods -n telemetry -l app=idrac-telemetry

.. note:: The ``idrac-telemetry-0`` pod will always be responsible for collecting the telemetry data of the management nodes (``oim``, ``service_kube_control_plane_x86_64``, ``service_kube_node_x86_64``, ``login_node_x86_64``, etc.).

2. Execute the following command::

    kubectl exec -it -n telemetry <iDRAC_telemetry_pod_name> -c mysqldb -- mysql -u <MYSQL_USER> -p

3. When prompted, enter the mysql password to log in.

4. To enter into the ``idrac_telemetry_db``, use the following command::

    use idrac_telemetrydb;

5. To access the services table::

    select * from services;
