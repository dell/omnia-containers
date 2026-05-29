Omnia Deployment Requirements
=============================

This section outlines the key requirements for the components used by Omnia to deploy HPC clusters. For more information about the supported devices and software, see :doc:`Support Matrix <Overview/SupportMatrix/index>`.


NFS Server
-----------

* If PowerScale is configured as the NFS server, navigate to **Protocols** > **NFS** > **Global Settings** and ensure NFSv3 is enabled while NFSv4 is disabled.
* If PowerScale is configured as the NFS server using **NFSv4** protocol, 
  the following settings must be enabled on the PowerScale cluster 
  to prevent file ownership from displaying as `nobody:nobody`:

  From the PowerScale web interface, navigate to **Protocols** > **NFS** > **Zone settings** and enable:
  - `nfsv4-no-names = true`
  - `nfsv4-no-domain = true`
  - `nfsv4-no-domain-uids = true`
  - `nfsv4-allow-numeric-ids = true`

  .. image:: images/powerscale_nfs_zone_settings.png
    :alt: PowerScale NFS Zone Settings

  Alternatively, run the following CLI command:

    isi nfs settings zone modify \
      --nfsv4-no-names=true \
      --nfsv4-no-domain=true \
      --nfsv4-no-domain-uids=true \
      --nfsv4-allow-numeric-ids=true \
      --zone=System

  **Note:**  
  - This configures PowerScale to send numeric UIDs/GIDs instead of 
    string-based identity (`user@domain`), which eliminates the 
    `nobody:nobody` ownership issue caused by NFSv4 domain mismatch.
  - Ensure that **UID/GID mappings are consistent** across all NFS 
    client nodes and the PowerScale cluster. Since numeric ID mode 
    bypasses name-based identity resolution, mismatched UIDs/GIDs 
    between clients will result in incorrect file ownership.
  - This setting **degrades NFSv4 ACL support**. If your environment 
    requires NFSv4 ACLs, consider aligning the NFSv4 domain between 
    PowerScale and all clients instead.
  - For more details, see `Dell KB 000023023 <https://www.dell.com/support/kbdoc/en-us/000023023>`_.
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




PowerScale S3 Storage
---------------------

* PowerScale cluster must be deployed within the admin subnet and should be accessible from all cluster nodes.
* Omnia uses HTTP access only when connecting to PowerScale, using the default port 9020.
* Ensure both S3 and HTTP services are enabled in the S3 bucket configuration.
* Ensure that valid S3 Access Key ID and S3 Secret Access Key are provided for authentication when accessing the PowerScale S3 service.
* S3 Access Key ID and S3 Secret Access Key are tightly associated with the S3 buckets. You need S3 Access Key ID and S3 Secret Access Key to access the S3 buckets created using the key.
* For detailed configuration instructions, see :ref:`PowerScale S3 configuration <powerscale-s3-config>`.

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

HPC Benchmark Image Layer
^^^^^^^^^^^^^^^^^^^^^^^^^

- Omnia supports an HPC Benchmark Image Layer for Slurm deployments.
- This capability is runtime script-driven:
  - Provisioning deploys ``pull_benchmarks.sh`` and ``benchmark_tools.list`` to ``/hpc_tools/scripts``.
  - Runtime staging is executed via ``/hpc_tools/scripts/pull_benchmarks.sh``.
- Benchmark artifacts are pulled from the local Pulp mirror path to ``/hpc_tools/<tool>/``.
- The feature is staging-only; Omnia does not compile or execute benchmark workloads.
- Ensure Slurm shared storage (``/hpc_tools``) is available and local repository content is prepared before runtime staging.

**Operational notes**

- ``msr-safe`` is ``x86_64`` only and is automatically skipped on ``aarch64``.
- If a destination directory already contains files, the tool is skipped to prevent overwrite.
- Runtime summary and per-tool outcomes are logged at:

.. code-block:: bash

   /var/log/pull_benchmarks.log

CUDA and DCGM Prerequisites for Slurm GPU Nodes
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The following prerequisites must be satisfied before deploying Omnia on Slurm clusters where
GPU-capable nodes are present. These apply in addition to general Slurm prerequisites.

Repository Requirements

- CUDA repository: Must be reachable from Slurm compute nodes. The CUDA repository must be accessible through the local Pulp repository configured during ``local_repo.yml`` execution.
- DCGM repository: ``datacenter-gpu-manager-4-cuda<N>`` must be available in the configured local repository. For CUDA 12+, ``datacenter-gpu-manager-4-multinode-cuda<N>`` must also be available.
- DKMS and kernel headers: Required only for ``nvidia-peermem``. The ``kernel-devel`` package for the running kernel must be present in the local repository. Verify kernel headers exist at ``/lib/modules/$(uname -r)/build`` prior to provisioning.

NFS Requirements

- The shared NFS path configured for Slurm HPC tools must be reachable from all Slurm compute
  nodes and all login/compiler nodes at provisioning time.
- Minimum recommended space for the ``hpc_tools/cuda`` NFS path is **30 GB**.
- The NFS share must be exported with ``no_root_squash``.

Hardware Requirements

- NVIDIA GPU hardware: Must be present on any Slurm node intended for GPU workloads. Nodes without GPU hardware are automatically skipped at runtime.
- Kernel headers: Required only for ``nvidia-peermem`` DKMS build.
- DKMS: Must be installed on nodes where ``nvidia-peermem`` is required.

.. note:: If repositories are not reachable or the NFS path is unavailable at provisioning time,
   GPU setup will fail on affected nodes and the DCGM service will not be started. Refer to the
   Manual Recovery section for remediation steps.

BuildStreaM
------------
* A dedicated node is required for BuildStreaM GitLab deployment.
* The node must have sufficient system resources for BuildStreaM (minimum 4 GB RAM, 2 CPU cores, 20GB free disk space)
* GitLab requires a minimum of 2 CPU cores. More cores may be needed for production workloads.
* Network connectivity for GitLab services.
* Ensure that Omnia BuildStreaM container, PostgreSQL container, and Playbook Watcher service are deployed on the OIM node. See :ref:`Prepare the Omnia Infrastructure Manager <prepare-oim-buildstream>`.







