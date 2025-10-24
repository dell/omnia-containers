==========================================
Set up High Availability (HA) Kubernetes on the service cluster
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
           "repo_config": "always",
           "softwares": [
                {"name": "default_packages", "arch": ["x86_64","aarch64"]}
                {"name": "nfs", "arch": ["x86_64","aarch64"]},
                {"name": "service_k8s","version": "1.31.4", "arch": ["x86_64"]}
            ],

         "service_k8s": [
                {"name": "service_kube_control_plane"},
                {"name": "service_etcd"},
                {"name": "service_kube_node"}
        ]

    }
 
* Omnia supports only Kubernetes version 1.31.4.
* If you want to install CSI PowerScale driver, ensure that you provide the required values. Click `Deploy CSI drivers for Dell PowerScale storage solutions <../../AdvancedConfigurations/PowerScale_CSI.html>`_ for more information.
* Ensure that there are a minimum of  three ``kube_control_planes``.
* Ensure that the ``kube_control_planes`` has a full-featured RHEL operating system (OS) installed. 
* The ``kube_control_planes`` has internet access to download necessary packages for cluster deployment and configuration.
* Ensure that the nfs server is reachable on all the diskless and diskfull nodes.
* The ``kube_control_planes`` must  be equipped with two active Network Interface Cards (NICs):  

  * One connected to the public network.  It is used for accessing the internet.
  * One dedicated to internal cluster communication. It is used for internal cluster communication, Kubernetes deployment activities, and for accessing the Pulp repositories hosted on the OIM. The Admin interface must be assigned an IP address from the admin network range and must be reachable from the OIM.
* To use NFS for service Kubernetes cluster, ensure the following prerequisites are met:

  * The NFS share has 755 permissions and ``no_root_squash`` is enabled on the mounted NFS share. 
  * Edit the ``/etc/exports`` file on the NFS server to include the ``no_root_squash`` option for the ``server_share_path``.
    
    ::
        
        /<your_server_share_path>  *(rw,sync,no_root_squash,no_subtree_check)

* Ensure that the following ``kube_control_planes`` hostname prerequisites are met. See `Prerequisites <https://omnia-devel.readthedocs.io/en/latest/Appendices/hostnamereqs.html>`_.

    .. include:: ../../Appendices/hostnamereqs.rst

Steps
=======

1. Run ``local_repo.yml`` playbook to download the artifacts required to set up Kubernetes on the service cluster nodes.

2. Fill in the service cluster details in the ``functional_groups_config.yml``: `Create groups and assign functional roles to the nodes <../composable_roles.html>`_.

.. csv-table:: functional_groups_config.yml
   :file: ../../../../../Tables/service_k8s_roles.csv
   :header-rows: 1
   :keepspace:

3. Fill  the ``omnia_config.yml``,  ``high_availability_config.yml`` (for `service cluster HA <../HighAvailability/service_cluster_ha.html>`_), and ``storage_config.yml``. The nfs_name mentioned in ``storage_config.yml`` should match the ``nfs_storage_name`` of the entries for the ``service_k8s_cluster`` in ``omnia_config.yml`` where deployment is set to true.
   See `Input parameters for the cluster <../OmniaCluster/schedulerinputparams.html>`_. See the following sample:

    ::

        nfs_client_params:
        -{
           nfs_name: "nfs_storage_default"
           server_ip: "", # Provide the IP of the NFS server
           server_share_path: "", # Provide server share path of the NFS Server
           client_share_path: /opt/omnia,,
           client_mount_options: "nosuid,rw,sync,hard,intr",
           nfs_name: nfs_k8s
        }
       

.. csv-table:: omnia_config.yml
   :file: ../../../../Tables/scheduler_k8s_rhel.csv
   :header-rows: 1
   :keepspace:

.. csv-table:: high_availability_config.yml
   :file: ../../../../Tables/service_k8s_high_availability.csv
   :header-rows: 1
   :keepspace:

4. Run ``ansible-playbook utils/connect_external_server.yml -i <inv>``. 
    
    This playbook is used to set up passwordless SSH to the ``kube_control_planes`` and updating the repositories and plup repository certificates. The Ansible inventory must be created using the Admin network IPs of the control plane nodes because these IPs are used for Kubernetes deployment. See the following sample:
   

   Sample for inv:

    ::

        [kube_control_plane]
        10.5.0.211  ansible_user=root ansible_ssh_pass=****
        10.5.0.212  ansible_user=root ansible_ssh_pass=****
        10.5.0.213  ansible_user=root ansible_ssh_pass=****        

5. Run ``ansible-playbook service_k8s_cluster.yml -i <inv>``. 
    
    This playbook deploys the service_k8s cluster with diskfull kube controller nodes and also extracts the configuration required for diskless kube nodes. It generates the kubeadm token and cloud-init vars for diskless kube node.  The token expires after 24 hours. The step 5 and step 6 need to be executed within 24 hours and pxe boot also needs to be completed. If the token gets expired , use the script ``ansible-playbook scheduler/generate_token_and_pod_status.yml -i <inv>  --tags kubeadm_token`` to generate the new token and run ``discovery.yml`` again and pxe boot the nodes. 

Once all the required input files are filled up, use the below commands to set up Kubernetes on the service cluster: ::

    ssh omnia_core
    ansible-playbook omnia.yml - i <inv>
    
    OR,

    cd /omnia/scheduler
    ansible-playbook service_k8s_cluster.yml - i <inv>


    Sample for inv:
     

        [kube_control_plane]
        10.5.0.211
        10.5.0.212
        10.5.0.213 
        [etcd]
        10.5.0.211
        10.5.0.212
        10.5.0.213


6. Run ``build.image.yml`` playbook to build diskless images for cluster nodes. See `Build cluster node images <../build_images.html>`_.

7. Run ``discovery.yml`` playbook to discover the potential cluster nodes, configure the boot script, and cloud-init based on the functional groups. See `Discover cluster nodes <../Provision/index.html>`_
    
    After successfully running the ``discovery.yml`` playbook, you can either manually PXE boot the nodes or use the ``set_pxe_boot.yml`` playbook. PXE booting allows the nodes to load diskless images from the Omnia Infrastructure Manager (OIM). For detailed steps on using ``set_pxe_boot.yml``, see :ref:`set-pxe-boot-order`.

8. After all the diskless nodes are pxebooted, use the utility to check the status of service cluster nodes and pods: ``ansible-playbook scheduler/generate_token_and_pod_status.yml -i <inv>  --tags pod_status``




Additional installations
=========================

After deploying Kubernetes, the following additional packages are installed on top of the Kubernetes stack on the service cluster:

1. **nfs-client-provisioner**

        * NFS subdir external provisioner is an automatic provisioner that use your existing and already configured external NFS server to support dynamic provisioning of Kubernetes Persistent Volumes via Persistent Volume Claims (PVC).
        * The nfs_name mentioned in ``storage_config.yml`` should match the ``nfs_storage_name`` of the entries for the ``service_k8s_cluster``.
        * The path to PVC is mentioned under ``{{ nfs_server_share_path }}``.

    Click `here <https://github.com/kubernetes-sigs/nfs-subdir-external-provisioner>`_ for more information.



Next step
===========

To know how to deploy the iDRAC telemetry containers on the service cluster, `click here <../../../Telemetry/service_cluster_telemetry.html>`_.