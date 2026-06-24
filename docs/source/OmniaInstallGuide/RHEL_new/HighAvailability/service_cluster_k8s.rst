==========================================
Set up High Availability (HA) Kubernetes on the Service Cluster
==========================================

Overview
========

With Omnia, you can deploy a service Kubernetes cluster on designated service nodes to efficiently distribute workload and manage resources for telemetry data collection. This setup reduces the processing load on the Omnia Infrastructure Manager (OIM) node and enhances overall scalability. Each service_kube_node is responsible for collecting telemetry data from its assigned subset of compute nodes. This federated approach to telemetry data collection improves efficiency for large-scale clusters.

Supported Version
=================

**Kubernetes Version**: 1.35.1

Omnia supports only Kubernetes version 1.35.1 for the service cluster deployment.

Functional Groups
=================

The service cluster uses the following functional groups:

* **service_kube_control_plane_x86_64**: Control plane nodes for managing the Kubernetes cluster (minimum 3 nodes for HA)
* **service_kube_node_x86_64**: Worker nodes for running Kubernetes workloads

.. note:: All control plane nodes use the same functional group name ``service_kube_control_plane_x86_64``. The first control plane node is automatically initialized with ``kubeadm init``, and additional control plane nodes are joined using ``kubeadm join``. No separate "first" functional group is required.

Prerequisites
=============

Hardware Requirements
---------------------

Minimum Node Requirements
~~~~~~~~~~~~~~~~~~~~~~~~~

* **Control Plane Nodes**: Minimum 3 nodes for HA
* **Worker Nodes**: Minimum 1 node (recommended 2+ for workload failover)
* **CPU**: 2 cores minimum per node
* **RAM**: 64 GB minimum per node
* **Disk**: 20 GB minimum for ETCD data partition (if using local disk)

Network Interface Cards (NICs)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Each node must be equipped with active Network Interface Cards:

1. **Admin NIC** (Internal Cluster Communication)

   * Used for internal cluster communication
   * Used for Kubernetes deployment activities
   * Used for accessing Pulp repositories hosted on the OIM
   * Must be assigned an IP address from the admin network range
   * Must be reachable from the OIM
   * If installing CSI driver, storage network must be accessible through this NIC

ETCD Local Disk Requirements (Optional)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If deploying ETCD on local disk instead of NFS:

**Hardware Options**:

* Dell BOSS Card (BOSS-N1/N2) with pre-configured RAID 1 or RAID 10, OR
* SSD or SATA disks if BOSS card is not available

**Requirements**:

* Minimum disk size: 20 GB for ETCD data partition
* RAID must be pre-configured on BOSS cards before deployment
* Omnia does not configure RAID automatically

**Disk Selection Priority**:

1. BOSS card (BOSS-N1/N2) if available
2. Falls back to SSD or SATA disks if BOSS card is not present
3. Mount point: ``/var/lib/etcd``

.. caution:: Migration from NFS to local disk is not supported during upgrades. This configuration is only applicable for fresh installations.

.. note:: When ``etcd_on_local_disk`` is set to ``false`` or omitted, ETCD storage is provisioned using NFS, and no local disk configuration is performed for ETCD.

Operating System
~~~~~~~~~~~~~~~~

* RHEL 10.0

Network Requirements
--------------------

IP Address Planning
~~~~~~~~~~~~~~~~~~~

You must plan the following IP ranges:

* **Admin Network**: For internal cluster communication
* **Pod Network**: For Kubernetes pod communication (default: 10.233.64.0/18)
* **Service Network**: For Kubernetes services (default: 10.233.0.0/18)
* **External IP Range**: For load balancer external IPs (e.g., 192.168.0.183-192.168.0.240)
* **Virtual IP**: For HA control plane (default: 172.16.107.1)

.. caution:: The virtual IP address must not belong to the dynamic_range or static_range mentioned in ``network_spec.yml``. In multi-subnet DHCP deployments, the virtual IP address must be allocated from the IP range assigned to the service cluster nodes.

.. caution:: Ensure that the ``pod_external_ip_range`` defined in ``omnia_config.yml`` is reachable from the OpenManage Enterprise appliance and the SFM network.

NFS Server Requirements
~~~~~~~~~~~~~~~~~~~~~~~~

If using NFS for ETCD storage:

* NFS server must be reachable on all diskless nodes
* NFS share must have 755 permissions
* NFS share must have ``rw,sync,no_root_squash,no_subtree_check`` options enabled
* Edit ``/etc/exports`` on NFS server:

  ::

      /<your_server_share_path>  *(rw,sync,no_root_squash,no_subtree_check)

.. caution:: Ensure that the ``server_share_path`` and ``client_share_path`` do not have any content before you deploy Kubernetes. Delete any existing content from the path on the NFS server.

Configuration
=============

1. Software Configuration
--------------------------

Add the service_k8s software to ``/opt/omnia/input/project_default/software_config.json``:

::

    {
      "cluster_os_type": "rhel",
      "cluster_os_version": "10.0",
      "repo_config": "partial",
      "softwares": [
        {
          "name": "default_packages", "arch": ["x86_64"],
          "name": "service_k8s", "version": "1.35.1","arch": ["x86_64"]
        }
      ],
      "service_k8s": [
        {
          "name": "service_kube_control_plane_first"
        },
        {
          "name": "service_kube_control_plane"
        },
        {
          "name": "service_kube_control_plane"
        },
        {
          "name": "service_kube_node"
        }
      ]
    }

.. note:: Ensure there are at least three ``service_kube_control_plane_x86_64`` entries and one ``service_kube_node_x86_64`` entry in the ``pxe_mapping_file.csv`` for the Kubernetes controller HA scenario. For workload and pod failover, it is recommended to have at least two ``service_kube_node_x86_64`` nodes.

2. Omnia Configuration
----------------------

Configure the service Kubernetes cluster in ``omnia_config.yml``. For more details on input parameters, see `Input parameters for the cluster <../OmniaCluster/schedulerinputparams.html>`.

::

    service_k8s_cluster:
      - cluster_name: service_cluster
        deployment: true
        etcd_on_local_disk: false
        k8s_cni: "calico"
        pod_external_ip_range: "192.168.0.183-192.168.0.240"
        k8s_service_addresses: "10.233.0.0/18"
        k8s_pod_network_cidr: "10.233.64.0/18"
        nfs_storage_name: "nfs_k8s"
        k8s_crio_storage_size: "20G"
        csi_powerscale_driver_secret_file_path: "/opt/omnia/input/project_default/secret.yaml"
        csi_powerscale_driver_values_file_path: "/opt/omnia/input/project_default/values.yaml"

.. csv-table:: omnia_config.yml
   :file: ../../../Tables/omnia_config_service_cluster.csv
   :header-rows: 1
   :keepspace:

3. High Availability Configuration
------------------------------------

Configure HA settings in ``high_availability_config.yml``:

::

    service_k8s_cluster:
      - cluster_name: service_cluster
        enable_k8s_ha: true
        virtual_ip_address: "172.16.107.1"

.. csv-table:: high_availability_config.yml
   :file: ../../../Tables/service_k8s_high_availability.csv
   :header-rows: 1
   :keepspace:

4. Storage Configuration
------------------------

Configure NFS storage in ``storage_config.yml``:

::

    nfs_client_params:
      - server_ip: ""  # IP of the NFS server
        server_share_path: ""  # Server share path of the NFS Server
        client_share_path: /opt/omnia
        client_mount_options: "nosuid,rw,sync,hard,intr"
        nfs_name: nfs_k8s

.. caution:: The ``nfs_name`` must match the ``nfs_storage_name`` in ``omnia_config.yml``.

**CSI Support**: If using CSI support, ensure that:

* ``server_share_path`` matches the ``isiPath`` value in ``values.yml``
* ``server_ip`` is the PowerScale NFS server IP

.. note:: If you want to install CSI PowerScale driver, ensure that you provide the required values. Click `Deploy CSI drivers for Dell PowerScale storage solutions <../../AdvancedConfigurations/PowerScale_CSI.html>`_ for more information.

5. PXE Mapping Configuration
------------------------------

The PXE mapping file (``pxe_mapping_file.csv``) maps server inventory to functional groups. The file is typically generated automatically from OpenManage Enterprise (OME) discovery, but can be manually created if needed.

Supported Functional Groups
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

For Kubernetes service cluster, use these functional groups:

* ``service_kube_control_plane_x86_64`` - Control plane nodes
* ``service_kube_node_x86_64`` - Worker nodes

Example Configuration
~~~~~~~~~~~~~~~~~~~~~

Ensure your ``pxe_mapping_file.csv`` includes entries for:

* At least 3 ``service_kube_control_plane_x86_64`` nodes
* At least 1 ``service_kube_node_x86_64`` node (recommended 2+ for HA)

Example::

    FUNCTIONAL_GROUP_NAME,GROUP_NAME,SERVICE_TAG,PARENT_SERVICE_TAG,HOSTNAME,ADMIN_MAC,ADMIN_IP,BMC_MAC,BMC_IP,IB_NIC_NAME,IB_IP
    service_kube_control_plane_x86_64,grp0,SVCTAG001,,nid00001,00:1a:2b:3c:4d:5e,172.16.0.10,00:1a:2b:3c:4d:5f,10.0.0.10,ib0,192.168.2.10
    service_kube_control_plane_x86_64,grp1,SVCTAG002,,nid00002,00:1a:2b:3c:4d:6e,172.16.0.11,00:1a:2b:3c:4d:6f,10.0.0.11,ib0,192.168.2.11
    service_kube_control_plane_x86_64,grp1,SVCTAG003,,nid00003,00:1a:2b:3c:4d:7e,172.16.0.12,00:1a:2b:3c:4d:7f,10.0.0.12,ib0,192.168.2.12
    service_kube_node_x86_64,grp2,SVCTAG004,,nid00004,00:1a:2b:3c:4d:8e,172.16.0.20,00:1a:2b:3c:4d:8f,10.0.0.20,ib0,192.168.2.20
    service_kube_node_x86_64,grp2,SVCTAG005,,nid00005,00:1a:2b:3c:4d:9e,172.16.0.21,00:1a:2b:3c:4d:9f,10.0.0.21,ib0,192.168.2.21

.. note:: The PXE mapping file is typically generated automatically using the OME discovery process. Manual creation is only required for special cases or testing.

Deployment Steps
================

Step 1: Prepare OIM
--------------------

Run the ``prepare_oim.yml`` playbook to prepare the Omnia Infrastructure Manager (OIM) for deployment.

::

    ansible-playbook prepare_oim.yml

**Verification**: Verify that OIM preparation completed successfully by checking the prepare_oim logs.

Step 2: Download Artifacts
---------------------------

Run the ``local_repo.yml`` playbook to download the required artifacts for Kubernetes setup on the service cluster nodes.

::

    ansible-playbook local_repo.yml

**Verification**: Verify that the artifacts are downloaded successfully by checking the repository logs.

Step 3: Configure Files
-----------------------

Fill in the configuration files:

* ``omnia_config.yml``
* ``high_availability_config.yml`` (for service cluster HA)
* ``storage_config.yml``

.. caution:: Ensure the ``nfs_name`` in ``storage_config.yml`` matches the ``nfs_storage_name`` in ``omnia_config.yml``.

Step 4: Build Diskless Images
------------------------------

Run the ``build_image_x86_64.yml`` playbook to build diskless images for cluster nodes. See `Build cluster node images <../build_images.html>`_ for more information.

::

    ansible-playbook build_image_x86_64.yml

**Verification**: Verify that the images are built successfully by checking the image build logs.

Step 5: Discover and Configure Nodes
-------------------------------------

Run the ``provision.yml`` playbook to discover potential cluster nodes, configure the boot script, and cloud-init based on the functional groups. See `Discover cluster nodes <../Provision/index.html>`_ for more information.

::

    ansible-playbook provision.yml

**Verification**: Verify that nodes are discovered and configured successfully by checking the provision logs.

Step 6: PXE Boot Nodes
----------------------

After successfully running the ``provision.yml`` playbook, PXE boot the nodes to load diskless images from the OIM. For detailed steps on using ``set_pxe_boot.yml``, see `Configure PXE Boot <../../Utils/configure_pxe_boot.html>`_.

**Option 1**: Manual PXE boot

* Configure nodes to boot from network
* Nodes will automatically load the diskless images

**Option 2**: Automated PXE boot

::

    ansible-playbook set_pxe_boot.yml

**Verification**: Verify that nodes boot successfully and join the cluster by checking node status.

Step 7: Verify Cluster Deployment
----------------------------------

Verify that the Kubernetes cluster is deployed successfully:

::

    # On control plane node
    kubectl get nodes
    kubectl get pods --all-namespaces
    kubectl cluster-info

**Expected Output**:

* All nodes should be in ``Ready`` status
* All system pods should be in ``Running`` status
* Cluster info should show the control plane endpoint





Additional Installations
=========================

After deploying Kubernetes, the following additional packages are automatically installed on the service cluster:

1. NFS Subdir External Provisioner

   The NFS subdir external provisioner is an automatic provisioner that uses your existing and already configured external NFS server to support dynamic provisioning of Kubernetes Persistent Volumes via Persistent Volume Claims (PVC).

   **Configuration**:

   * The ``nfs_name`` in ``storage_config.yml`` must match the ``nfs_storage_name`` in ``omnia_config.yml``
   * The path to PVC is specified under ``{{ nfs_server_share_path }}``

   **Documentation**: For more information, click `here <https://github.com/kubernetes-sigs/nfs-subdir-external-provisioner>`_.

2. DOCA-OFED

   After running ``provision.yml`` and PXE-booting the nodes, DOCA-OFED is installed on nodes that have Mellanox InfiniBand cards.

   **Behavior**:

   * A static IP is assigned to the InfiniBand interface only if the interface is up
   * If the interface is down, the user must bring it up to enable IP assignment

Next Steps
==========

After successfully deploying the HA Kubernetes service cluster:

**Deploy Telemetry**: To deploy iDRAC telemetry containers on the service cluster, see `Initialize and Verify Telemetry <../Telemetry/initialize_and_verify_telemetry.html>`_

Support
=======

For feedback or issues with Omnia documentation, please reach out at `omnia.readme@dell.com <mailto:omnia.readme@dell.com>`_.