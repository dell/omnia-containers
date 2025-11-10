Omnia Common Prerequisites
==========================

This section outlines the key prerequisites for setting up Omnia components, including
NFS configuration, OIM setup, and service Kubernetes cluster preparation.


NFS Server Prerequisites
----------------------------

* Choose an NFS server located outside your cluster.
* The NFS share has **755 permissions** and ``no_root_squash`` is enabled during mount.
* To enable ``no_root_squash``, edit the ``/etc/exports`` file on the NFS server and include the option for the exported path, run the following command:

  .. code-block:: bash

     /<your_exported_path>  *(rw,sync,no_root_squash,no_subtree_check)

* Ensure that the external NFS share is accessible from all nodes (both diskless and diskful)
  and is reachable via the admin network.


OIM (Omnia Infrastructure Manager) Prerequisites
-------------------------------------------------

* Choose a **server outside of your intended cluster** that meets the required `storage requirements <RHELSpace.html>`_ to function as the Omnia Infrastructure Manager (OIM).
* Ensure that the OIM has a full-featured RHEL operating system (OS) installed. For a complete list of supported RHEL versions, see the `Support Matrix <../../Overview/SupportMatrix/OperatingSystems/index.html>`_.
* Ensure that **Podman** container engine is installed on the OIM.
* The OIM must have **two active Network Interface Cards (NICs)**:
   * One connected to the **public network** (for downloading and storing packages and images).
   * One dedicated to **internal cluster communication**.
* Ensure that the OIM has **internet access**.
* Verify that **Git** is installed. If not, install it using:

     .. code-block:: bash

        dnf install git -y

* All target bare-metal servers (cluster nodes) must be **reachable from the OIM**.
* Clone the `Omnia artifacts repository <https://github.com/dell/omnia-artifactory/tree/omnia-container>`_  and build the container images as shown below:

     .. code-block:: bash

        git clone https://github.com/dell/omnia-artifactory.git -b omnia-container-v2.0.0.0-rc2 
        cd omnia-artifactory
        ./build_images.sh all omnia_branch=v2.0.0.0-rc2

   * For detailed build instructions, refer to the
     `Omnia Artifacts README <https://github.com/dell/omnia-artifactory/blob/omnia-container/README.md>`_.

* Make sure that the required ports are open on the OIM node for cluster deployment. For detailed information on the required ports, refer to the :doc:`Omnia Ports <omnia_ports>`.


Repository Prerequisites
---------------------------

* Enable the **AppStream** and **BaseOS** repositories via the RHEL subscription manager.
* Ensure that RHEL has an **active subscription** or is configured to access **local repositories**.
* Verify that all **repository URLs** for the software packages are **accessible** — downloads will fail for inaccessible packages.
* For RHEL systems without a subscription, the repository URLs for ``x86_64_codeready-builder``, ``x86_64_appstream``, and ``x86_64_baseos`` are mandatory.
* Docker credentials are a mandatory requirement to pull in the essential packages during local repository deployment. 


Service Kubernetes Cluster Prerequisites
-------------------------------------

* A minimum of **three Kubernetes controller nodes** are available.
* Each controller node must have a **full-featured RHEL operating system** installed.
* The OIM and all three controller nodes must have **internet access**.
* Each controller node must have **two active NICs**:

  * One connected to the **public network** (for downloading and storing packages/images).
  * One dedicated to **internal cluster communication**.

    *Refer to supported network topologies in the Omnia documentation.*

* Verify that all **hostname prerequisites** are met on the Kubernetes controller nodes.


iDRAC Telemetry Metric Collection Prerequisites
-----------------------------------------------

* **Redfish** is enabled in iDRAC.
* **iDRAC firmware** is updated to the latest version.
* A **Datacenter license** is installed on all iDRAC interfaces.
* **Correct node service tags** are displayed on the iDRAC interface.
* For telemetry collection on the service cluster, ensure all **BMC (iDRAC) IPs** are **reachable** from the service cluster nodes.

LDAP Prerequisites
------------------------

* Configure the proxy on the OIM node using the ``omnia_auth`` container. To configure the proxy, after deploying the ``omnia_auth`` container, perform the steps described in `Configure OpenLDAP as a Proxy Server <Authentication/OpenLDAP.html>`_.



