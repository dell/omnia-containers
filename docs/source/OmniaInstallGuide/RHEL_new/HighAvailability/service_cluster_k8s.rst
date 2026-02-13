==========================================
Set up High Availability (HA) Kubernetes on the Service Cluster
==========================================

With Omnia, you can deploy a service Kubernetes cluster on the designated service nodes to efficiently distribute workload and manage resources for telemetry data collection. 
This setup reduces the processing load on the OIM node and enhances overall scalability. Each ``service_kube_node`` is responsible for collecting telemetry data from its assigned subset of compute nodes.
Federated way of telemetry data collection improves efficiency for large-scale clusters.

Prerequisites
==============

* To deploy Kubernetes on service cluster, ensure that ``service_k8s`` is added under ``softwares`` in the ``/opt/omnia/input/project_default/software_config.json``. Refer the sample config file below: ::

    {

         "cluster_os_type": "rhel",
          "cluster_os_version": "10.0",
           "repo_config": "partial",
           "softwares": [

                {"name": "service_k8s","version": "1.34.1", "arch": ["x86_64"]}
            ],

         "service_k8s": [
                {"name": "service_kube_control_plane_first"},
                {"name": "service_kube_control_plane"},
                {"name": "service_kube_node"}
        ]

    }
 
* Omnia supports only Kubernetes version 1.34.1.
* If you want to install CSI PowerScale driver, ensure that you provide the required values. Click `Deploy CSI drivers for Dell PowerScale storage solutions <../../AdvancedConfigurations/PowerScale_CSI.html>`_ for more information.
* Ensure that there are at least three ``service_kube_control_plane`` entries and one ``service_kube_node`` entry in the ``pxe_mapping_file.csv`` for the Kubernetes controller HA scenario. 
.. note:: The above requirement is the minimum needed to deploy the service Kubernetes cluster. High availability applies only to the control plane. For workload and pod failover, it is recommended to have at least two ``service_kube_node`` nodes, so that pods can be rescheduled automatically if one worker node fails.
* Ensure that the nfs server is reachable on all the diskless nodes.
* The nodes must be equipped with two active Network Interface Cards (NICs):  

    * One dedicated to internal cluster communication. It is used for internal cluster communication, Kubernetes deployment activities, and for accessing the Pulp repositories hosted on the OIM. The Admin interface must be assigned an IP address from the admin network range and must be reachable from the OIM.
    * One dedicated to Internet. If you want to install a CSI driver, ensure that the storage network must be accessible through the Internet-facing NIC. This NIC must be configured via DHCP.
  
* To use NFS for service Kubernetes cluster, ensure the following prerequisites are met:

  * The NFS share has 755 permissions and ``rw,sync,no_root_squash,no_subtree_check`` are enabled on the mounted NFS share. 
  * Edit the ``/etc/exports`` file on the NFS server to include the ``rw,sync,no_root_squash,no_subtree_check`` option for the ``server_share_path``.
    
    ::
        
        /<your_server_share_path>  *(rw,sync,no_root_squash,no_subtree_check)


Steps
=======

1. Run ``local_repo.yml`` playbook to download the artifacts required to set up Kubernetes on the service cluster nodes.

2. Fill  the ``omnia_config.yml``,  ``high_availability_config.yml`` (for `service cluster HA <../HighAvailability/service_cluster_ha.html>`_), and ``storage_config.yml``. The nfs_name mentioned in ``storage_config.yml`` should match the ``nfs_storage_name`` of the entries for the ``service_k8s_cluster`` in ``omnia_config.yml`` where deployment is set to true.
   See `Input parameters for the cluster <../OmniaCluster/schedulerinputparams.html>`_. The NFS share is utilized by the Kubernetes cluster to mount necessary resources. See the following sample:
    
    ::

        nfs_client_params:
        -{
           server_ip: "", # Provide the IP of the NFS server
           server_share_path: "", # Provide server share path of the NFS Server
           client_share_path: /opt/omnia,,
           client_mount_options: "nosuid,rw,sync,hard,intr",
           nfs_name: nfs_k8s
        }
       
.. note:: In case of CSI support, ensure that the ``server_share_path`` must be the same as the isiPath value in ``values.yml`` file and the ``server_ip`` should be the Powerscale NFS server IP.
.. note:: Ensure that the ``server_share_path`` and ``client_share_path`` do not have any content before you deploy Kubernetes. To delete the content, go to ``server_share_path`` on NFS server and remove the content available in the path.

.. csv-table:: omnia_config.yml
   :file: ../../../../Tables/scheduler_k8s_rhel.csv
   :header-rows: 1
   :keepspace:

.. csv-table:: high_availability_config.yml
   :file: ../../../../Tables/service_k8s_high_availability.csv
   :header-rows: 1
   :keepspace:


3. Run ``build_image_x86_64.yml`` playbook to build diskless images for cluster nodes. See `Build cluster node images <../build_images.html>`_.

4. Run ``discovery.yml`` playbook to discover the potential cluster nodes, configure the boot script, and cloud-init based on the functional groups. See `Discover cluster nodes <../Provision/index.html>`_
    
    After successfully running the ``discovery.yml`` playbook, you can either manually PXE boot the nodes or use the ``set_pxe_boot.yml`` playbook. PXE booting allows the nodes to load diskless images from the Omnia Infrastructure Manager (OIM). For detailed steps on using ``set_pxe_boot.yml``, see :ref:`set-pxe-boot-order`.





Additional Installations
=========================

After deploying Kubernetes, the following additional packages are installed on top of the Kubernetes stack on the service cluster:

1. **nfs-client-provisioner**

        * NFS subdir external provisioner is an automatic provisioner that use your existing and already configured external NFS server to support dynamic provisioning of Kubernetes Persistent Volumes via Persistent Volume Claims (PVC).
        * The nfs_name mentioned in ``storage_config.yml`` should match the ``nfs_storage_name`` of the entries for the ``service_k8s_cluster``.
        * The path to PVC is mentioned under ``{{ nfs_server_share_path }}``.

    Click `here <https://github.com/kubernetes-sigs/nfs-subdir-external-provisioner>`_ for more information.

2. **Doca-ofed installation**
    After running ``discovery.yml`` and PXE-booting the nodes, DOCA-OFED is installed on nodes that have Mellanox InfiniBand cards. A static IP is assigned to the InfiniBand interface only if the interface is up. If the interface is down, the user must bring it up to enable IP assignment.

Next Step
===========

To know how to deploy the iDRAC telemetry containers on the service cluster, `click here <../Telemetry/initialize_and_verify_telemetry.html>`_.