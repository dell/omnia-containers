Input Parameters for the Cluster
===================================

The ``service_k8s_cluster`` depends on the inputs provided in the following files:

* ``/opt/omnia/input/project_default/omnia_config.yml``
* ``/opt/omnia/input/project_default/security_config.yml``
* ``/opt/omnia/input/project_default/storage_config.yml``
* ``/opt/omnia/input/project_default/high_availability_config.yml``

.. caution:: Do not remove, edit, or comment any lines in the above mentioned input files.

``/opt/omnia/input/project_default/omnia_config.yml``
-------------------------------------------------------

.. dropdown:: Parameters for kubernetes setup on service Kubernetes cluster

   .. csv-table::
      :file: ../../../Tables/omnia_config_service_cluster.csv
      :header-rows: 1
      :keepspace:

::
 
   service_k8s_cluster:
      - cluster_name: service_cluster
        deployment: true
        k8s_cni: "calico"
        pod_external_ip_range: ""
        k8s_service_addresses: "10.233.0.0/18"
        k8s_pod_network_cidr: "10.233.64.0/18"
        nfs_storage_name: "nfs_k8s"
        csi_powerscale_driver_secret_file_path: ""
        csi_powerscale_driver_values_file_path: "
        k8s_crio_storage_size: "20G"


.. csv-table:: Parameters for slurm setup
   :file: ../../../Tables/scheduler_slurm.csv
   :header-rows: 1
   :keepspace:

See the following sample:
::

      slurm_cluster:
      - cluster_name: slurm_cluster
        nfs_storage_name: nfs_slurm
        config_sources:
          slurm:
            SlurmctldTimeout: 60
            SlurmdTimeout: 150
          cgroup:
            CgroupPlugin: autodetect
            AllowedRAMSpace: 100

      slurm_cluster:
      - cluster_name: slurm_cluster
        nfs_storage_name: nfs_slurm
        config_sources:
         slurm: /path/to/custom_slurm.conf
         cgroup: /path/to/custom_cgroup.conf
         slurmdbd: /path/to/custom_slurmdbd.conf
         gres: /path/to/custom_gres.conf
         
``/opt/omnia/input/project_default/security_config.yml``
----------------------------------------------------------

.. csv-table:: Parameters for OpenLDAP configuration
   :file: ../../../Tables/security_config_ldap.csv
   :header-rows: 1
   :keepspace:

``/opt/omnia/input/project_default/storage_config.yml``
----------------------------------------------------------

.. csv-table:: Parameters for Storage
   :file: ../../../Tables/storage_config.csv
   :header-rows: 1
   :keepspace:



``/opt/omnia/input/project_default/high_availability_config.yml``
----------------------------------------------------------

See the following sample:
::

      service_k8s_cluster_ha:
        - cluster_name: service_cluster
          enable_k8s_ha: true
          virtual_ip_address: "172.16.107.1"


.. csv-table:: Parameters for Service Cluster HA
        :file: ../../../Tables/service_k8s_high_availability.csv
        :header-rows: 1
        :keepspace:

.. caution:: Ensure that the external NFS is accessible by all the nodes intended to be booted and is reachable by the admin network. 