Omnia Deployment Requirements
=============================

This section outlines the key requirements for the components used by Omnia to deploy HPC clusters. For more information about the supported devices and software, see :doc:`Support Matrix <Overview/SupportMatrix/index>`.


NFS Server
-----------

* If PowerScale is configured as the NFS server, navigate to **Protocols** > **NFS** > **Global Settings** and ensure NFSv3 is enabled while NFSv4 is disabled.
* Choose an NFS server located outside your cluster.
* The NFS share has **755 permissions** and ``no_root_squash`` is enabled during mount.
* To enable ``no_root_squash``, edit the ``/etc/exports`` file on the NFS server and include the option for the exported path, run the following command:

  .. code-block:: bash

     /<your_exported_path>  *(rw,sync,no_root_squash,no_subtree_check)

* Ensure that the external NFS share is accessible from all nodes (both diskless and diskful)
  and is reachable via the admin network.

NFS Server for K8s
^^^^^^^^^^^^^^^^^^^^^

* Minimum NFS for Kubernetes is 200 GB. The storage is recommended based on small cluster deployments. Increase the storage based on cluster size and telemetry data.
* Ensure that there is a dedicated mount point for each NFS.

NFS Server for Slurm
^^^^^^^^^^^^^^^^^^^^^

* Minimum NFS for Slurm is 50 GB. Increase the storage based on job data.
* Ensure that there is a dedicated mount point for each NFS.

NFS Server for Omnia Infrastructure Manager (OIM)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

* Omnia recommends using an NFS share with at least 200 GB storage for OIM and cluster configuration.
* Ensure that there is a dedicated mount point for each NFS.

Networking
----------

* Ensure admin and BMC switches are configured and reachable. 

InfiniBand
------------
* Before deploying Omnia on clusters using InfiniBand (IB) networking, ensure that the Subnet Manager (SM) service is enabled and running on the InfiniBand switch or host.

.. note:: Failure to meet this prerequisite may result in InfiniBand ports on hosts remaining in the Initializing state and prevent IB communication between nodes.

Omnia Infrastructure Manager (OIM)
----------------------------------

* Choose a **server outside of your intended cluster** that meets the required :doc:`Storage Requirements <OmniaInstallGuide/RHEL_new/RHELSpace>` to function as the Omnia Infrastructure Manager (OIM).
* Ensure the OIM has at least 64 GB RAM. To check the free RAM size, use the ``free -h`` command. To check the disk space, use the ``df -h`` command.
* Ensure that the OIM has the RHEL operating system installed with the **Server with GUI** Base Environment. For a complete list of supported RHEL versions, see the :doc:`supported operating systems <Overview/SupportMatrix/OperatingSystems/index>`.
* Ensure that **Podman** container engine is installed on the OIM.
* The OIM must have access to public/internet (for downloading packages and images) network and admin (PXE) network.
* Verify that **Git** is installed. If not, install it using:

     .. code-block:: bash

        dnf install git -y

* All target bare-metal servers (cluster nodes) must be **reachable from the OIM**.
* Make sure that the required ports are open on the OIM node for cluster deployment. For detailed information on the required ports, refer to the :doc:`Omnia Ports <OmniaInstallGuide/RHEL_new/omnia_ports>`.
* The ``omnia_core`` and ``omnia_auth`` container images are deployed on the OIM. For instructions to deploy containers, see :doc:`Deploy Omnia Core Container <OmniaInstallGuide/RHEL_new/omnia_startup>`.

Aarch64 Node Prerequisites
---------------------------

* Ensure that a disk is available to the aarch64 node for Full OS installation and you must install the OS manually.
* Ensure that an IP address is assigned to the aarch64 node and the node has connectivity to the PXE network.
* Ensure that the same NFS share used in OIM is reachable on the aarch64 node.

Repository
-----------

* Enable the **AppStream** and **BaseOS** repositories via the RHEL subscription manager.
* To pin specific RHEL version in the subscription manager, use the following commands::

    subscription-manager release --show
    subscription-manager release --set=10.0

* Ensure that RHEL has an **active subscription** or is configured to access **local repositories**.
* Verify that all **repository URLs** for the software packages are **accessible** — downloads will fail for inaccessible packages.
* For RHEL systems without a subscription, the repository URLs for ``x86_64_codeready-builder``, ``x86_64_appstream``, and ``x86_64_baseos`` are mandatory.
* Docker credentials are a mandatory requirement to pull in the essential packages during local repository deployment. 
* If the Slurm RPMS is already available, update the value in the URL of the ``user_repo_url_x86_64`` or ``user_repo_url_aarch64`` parameter in ``/opt/omnia/input/project_default/local_repo_config.yml``.
* In a mixed architecture environment where the Slurm control node and compute nodes use different architectures (for example, control node with x86_64 and compute nodes with aarch64), ensure that Slurm binaries for both architectures are compiled and available in the user repository.  
* If the repository is hosted, use the URL created in the ``local_repo_config.yml`` file.

  user_repo_url_x86_64::

    - { url: "http://<ipaddress>/ldms-repo/x86_64", gpgkey: "", sslcacert: "", sslclientkey: "", sslclientcert: "", name: "x86_64_slurm_custom" }

  user_repo_url_aarch64::

    - { url: "http://<ipaddress>/ldms-repo/aarch64", gpgkey: "", sslcacert: "", sslclientkey: "", sslclientcert: "", name: "aarch64_slurm_custom" }

Run ``ansible-playbook local_repo/local_repo.yml``.

* Create Slurm repository build for x86_64. See `Build Slurm repository for x86_64 <OmniaInstallGuide/RHEL_new/OmniaCluster/BuildingCluster/build_slurm_repo.html>`_ and `Host RPMS on Apache server <OmniaInstallGuide/RHEL_new/OmniaCluster/BuildingCluster/hosting_RPMS_on_Apache_server.html>`_.
.. note:: 
    *  If any user repository is already hosted externally, update the value of the ``user_repo_url_x86_64`` or ``user_repo_url_aarch64`` parameter in ``/opt/omnia/input/project_default/local_repo_config.yml`` with the hosted repository URL based on the architecture.
    * If the RPMs are already available but are not externally hosted, place the RPMs in the OIM and follow the steps in `Host RPMS on Apache server <OmniaInstallGuide/RHEL_new/OmniaCluster/BuildingCluster/hosting_RPMS_on_Apache_server.html>`_. After hosting the RPMs, update the ``user_repo_url_x86_64`` or ``user_repo_url_aarch64`` parameter with the newly created repository URL.


Service Kubernetes Cluster 
---------------------------

* A minimum of **three Kubernetes controller nodes** and **one kube node** must be available.
* Ensure that each Service Kubernetes Cluster node has at least 64 GB RAM.

iDRAC Telemetry Metrics Collection 
----------------------------------

* **Redfish** is enabled in iDRAC.
* **iDRAC firmware** is updated to the latest version.
* A **Datacenter license** is installed on all iDRAC interfaces.
* **Correct node service tags** are displayed on the iDRAC interface.
* For telemetry collection on the service cluster, ensure all **BMC (iDRAC) IPs** are **reachable** from the service cluster nodes.

Lightweight Directory Access Protocol (LDAP)
--------------------------------------------

* The LDAP server details are required to configure the ``omnia_auth`` container and OpenLDAP as a proxy server. See :doc:`Configure OpenLDAP as a proxy server <OmniaInstallGuide/RHEL_new/Authentication/OpenLDAP>`.
* To deploy an external OpenLDAP server for authentication, ensure that the OpenLDAP server is deployed and configured with the required directory structure (users and groups). For the detailed steps, see :doc:`External LDAP Deployment <OmniaInstallGuide/ExternalDeploymentGuide/external_ldap_deployment>`.

Lightweight Distributed Metric Service (LDMS)
---------------------------------------------

* Ensure that EPEL and AppStream repositories are configured and the python3-devel and python3-Cython packages are installed. To install the packages, run the following command::

   sudo dnf install -y python3-devel python3-Cython 

* The LDMS RPM must be available in the user repository, and the ``ldms.json`` file should be updated accordingly. 
  If the LDMS RPM is not available, refer to  `Building LDMS PRODUCER RPM Package <https://github.com/dell/omnia-artifactory?tab=readme-ov-file#building-ldms-producer-rpm-package>`_ for instructions on building LDMS RPMs.
* If the LDMS RPMS are already available, update the value (<hosted LDMS repository url>) in the URL of the ``user_repo_url_x86_64`` or ``user_repo_url_aarch64`` parameter in ``/opt/omnia/input/project_default/local_repo_config.yml``.
  
* If the repository is hosted, use the URL created in the ``local_repo_config.yml`` file.

  user_repo_url_x86_64::

   { url: "http://<ipaddress>/ldms-repo/x86_64", gpgkey: "", sslcacert: "", sslclientkey: "", sslclientcert: "",  name: "x86_64_ldms" }

  user_repo_url_aarch64::

   { url: "http://<ipaddress>/ldms-repo/aarch64", gpgkey: "", sslcacert: "", sslclientkey: "", sslclientcert: "",  name: "aarch64_ldms" }

  Run ``ansible-playbook local_repo/local_repo.yml``.


Slurm
------
* Ensure that each slurm compute node has at least 64 GB RAM.
* In a mixed architecture environment where the Slurm control node and compute nodes use different architectures (for example, control node with x86_64 and compute nodes with aarch64), ensure that Slurm binaries for both architectures are compiled and available in the user repository.
* The Slurm RPM must be available in the user repository. If the Slurm RPM is not available, refer to `Slurm Quick Start Administrator Guide <https://slurm.schedmd.com/quickstart_admin.html>`_ for instructions on building Slurm RPMs.
* If the Slurm RPMS are already available, update the value (<hosted slurm repository url>) in the URL of the ``user_repo_url_x86_64`` or ``user_repo_url_aarch64`` parameter in ``/opt/omnia/input/project_default/local_repo_config.yml``.
  
* If the repository is hosted, use the URL created in the ``local_repo_config.yml`` file.

  user_repo_url_x86_64::
    
   - { url: "<hosted slurm repository url>", gpgkey: "", sslcacert: "", sslclientkey: "", sslclientcert: "",  name: "x86_64_slurm_custom" }

  user_repo_url_aarch64::
    
   - { url: "<hosted slurm repository url>", gpgkey: "", sslcacert: "", sslclientkey: "", sslclientcert: "",  name: "aarch64_slurm_custom" }

  Run ``ansible-playbook local_repo/local_repo.yml``.
* Create Slurm repository build for x86_64. See `Build Slurm repository for x86_64 <OmniaInstallGuide/RHEL_new/OmniaCluster/BuildingCluster/build_slurm_repo.html>`_ and `Host RPMS on Apache server <OmniaInstallGuide/RHEL_new/OmniaCluster/BuildingCluster/hosting_RPMS_on_Apache_server.html>`_.
* After Slurm RPMS are generated, change the rpms in corresponding role accordingly if the rpm names are not matching with rpms in ``input/config/x86_64/rhel/10.0/slurm_custom.json``.

BuildStreaM
------------
* A dedicated node is required for BuildStreaM GitLab deployment.
* The node must have sufficient system resources for BuildStreaM (minimum 4 GB RAM, 2 CPU cores, 20GB free disk space)
* GitLab requires a minimum of 2 CPU cores. More cores may be needed for production workloads.
* Network connectivity for GitLab services.
* Ensure that Omnia BuildStreaM container, PostgreSQL container, and Playbook Watcher service are deployed on the OIM node. See :ref:`Prepare the Omnia Infrastructure Manager <prepare-oim-buildstream>`.







