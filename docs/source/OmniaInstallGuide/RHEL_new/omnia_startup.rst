Step 1: Deploy Omnia Core Container
=========================================

The Omnia core container is deployed on the Omnia Infrastructure Manager (OIM) and it is managed as a Systemd service (``omnia_core.service``). 
The Omnia core container contains the following:

 * The open-source code to deploy and manage Omnia clusters. The source code is available at `https://github.com/dell/omnia <https://github.com/dell/omnia>`_.
 * Python and Ansible preinstalled. 

Use the ``omnia.sh`` script to install, uninstall, and view help on the actions that you can perform on the Omnia core container. 

Prerequisites for Deploying the Omnia Core Container
-----------------------------------------------------

* The OIM has internet access to download necessary packages for cluster deployment and configuration.
* The OIM must have two active Network Interface Cards (NICs):  

  * One connected to the public network.  
  * One dedicated to internal cluster communication. 
* Ensure that Podman container engine is installed on your OIM.
* If PowerScale is configured as the NFS server, navigate to **Protocols** > **NFS** > **Global Settings** and ensure NFSv3 is enabled while NFSv4 is disabled.
* If you want to use a NFS share for the omnia shared path, ensure the following:

  * The NFS share has 755 permissions and ``no_root_squash`` is enabled on the mounted NFS share. 
  * Edit the ``/etc/exports`` file on the NFS server to include the ``no_root_squash`` option for the exported path.
    
    ::
        
        /<your_exported_path>  *(rw,sync,no_root_squash,no_subtree_check)

* Ensure that the following OIM hostname prerequisites are met.

    .. include:: ../../Appendices/hostnamereqs.rst

Steps to Deploy Omnia Core Container
------------------------------------

You can deploy the ``omnia_core`` container images on the Omnia Infrastructure Manager (OIM) in one of the following ways:

 * From Docker Hub (recommended for production), available at `Docker Hub <https://hub.docker.com/u/dellhpcomniaaisolution>`_

 * From Omnia Artifactory repository (recommended for custom development), available at `Omnia Artifactory <https://github.com/dell/omnia-artifactory.git>`_

Deploy Omnia Core Container from Docker Hub (Recommended)
----------------------------------------------------------

To deploy the container images from DockerHub, do the following:  

1. Download the ``omnia.sh`` script using the following commands:
        
   * To use the tagged version of Omnia, run the following command::

      wget https://raw.githubusercontent.com/dell/omnia/refs/tags/${OMNIA_VERSION}/omnia.sh

   * In the DockerHub, by default Omnia source code points to the ``v2.0.0.0`` branch. To use the specific branch of Omnia, run the following command::

      wget https://raw.githubusercontent.com/dell/omnia/refs/heads/${OMNIA_VERSION}/omnia.sh


  **Example:** 
    * **Specifc verion:** ``wget https://raw.githubusercontent.com/dell/omnia/refs/heads/main/omnia.sh`` 
    * **Tagged version:** ``wget https://raw.githubusercontent.com/dell/omnia/refs/tags/v2.0.0.0/omnia.sh``

2. Run the following command to make the script executable::

    chmod +x omnia.sh

3. On the OIM, run the following command to deploy the ``omnia_core`` container and configure passwordless SSH. The ``omnia.sh`` command internally pulls 
   the ``omnia_core`` container image from Docker Hub::

   ./omnia.sh --install

   If there are issues pulling images from Docker Hub, manually pull the image using Podman::
       
       podman pull dellhpcomniaaisolution/omnia_auth:1.0  

4. When prompted for the shared path, enter the path for the Omnia shared directory. This can be a local file path or an NFS share path.
5. When prompted for the password, enter a secure alphanumeric password for accessing the Omnia core container.
   
.. caution:: The password must not contain special characters such as \ , | , & , ; , ` , < > , * , ? , ! , $ , ( ) , { } , [ ] . 

  
Deploy the Omnia Core Container from Omnia Artifactory (Alternative)
--------------------------------------------------------------------

To deploy the container images from any Omnia branch, available at `Omnia Artifactory Repository <https://github.com/dell/omnia-artifactory.git>`_, do the following:

  
 1. Clone the Omnia artifacts repository and build the ``omnia_core`` container images. Run the following commands:

    .. code-block:: bash

      git clone https://github.com/dell/omnia-artifactory.git
      cd omnia-artifactory
      ./build_images.sh omnia_branch=<branch_name_or_tag>

    Examples:

    To build from a branch:

    .. code-block:: bash

      ./build_images.sh omnia_branch=main

    To build from a tag:

    .. code-block:: bash

      ./build_images.sh omnia_branch=v2.0.0.0

  * For detailed build instructions, refer to the `Omnia Artifacts README <https://github.com/dell/omnia-artifactory/blob/omnia-container/README.md>`_.

2. Run the following command to make the script executable::

    chmod +x omnia.sh

3. On the OIM, run the following command to deploy the ``omnia_core`` container and configure passwordless SSH::

    ./omnia.sh --install

3. When prompted for the shared path, enter the path for the Omnia shared directory. This can be a local file path or an NFS share path.
4. When prompted for the password, enter a secure alphanumeric password for accessing the Omnia core container.
   
.. caution:: The password must not contain special characters such as \ , | , & , ; , ` , < > , * , ? , ! , $ , ( ) , { } , [ ] . 


Tasks Performed by ``omnia.sh``
---------------------------------

The ``omnia.sh`` script performs the following tasks:

* Deploys and starts the ``omnia_core`` container as a Systemd service.
* Generates an SSH key pair and stores them in the ``/root/.ssh`` folder in the core container.
* Initializes the Podman container engine.
* Creates the following directories within the Omnia Core Container:

  ``/opt/omnia``:  Shared directory that is mapped to the Omnia shared path used by OIM.  

  ``/opt/omnia/input/project_default``: Contains the input files for the playbooks.  

  ``/omnia``:  Contains the Omnia source code.  

  ``/opt/omnia/log/core/playbooks``: Contains the playbook execution logs.  

.. note::

   Provide any file paths (for example, mapping file) that are mentioned in input files in the ``/opt/omnia`` directory. 

.. caution::

   - Do not delete any key pairs generated by Omnia from ``/root/.ssh`` because this will lead to ``omnia_core.service`` execution failure.
   - Do not manually delete any files from the OMNIA shared directory. Use the following command to safely remove the entire OMNIA shared directory::

        ./omnia.sh --uninstall


Access the Omnia Core Container
----------------------------------------

You can access the Omnia core container using either of the following methods:

1. **Podman**: To access the Omnia core container using Podman, run the following command::

       podman exec -it -u root omnia_core bash

2. **SSH**: To access the Omnia core container using SSH, run the following command::

       ssh omnia_core


Uninstall Omnia Core Container
-------------------------------

The ``omnia.sh --uninstall`` command removes the ``omnia_core`` container and its associated Systemd service 
(``omnia_core.service``). It also cleans up the Omnia shared directory and generated files, while preserving 
user-generated files such as inventory and mapping files.

.. note::

    Before you uninstall the ``omnia_core`` container, ensure that no other containers are running on the OIM except ``omnia_core``. 
    If other containers are present, log in to the ``omnia_core`` container and run the following Ansible playbook to remove the containers::

      cd /omnia/utils
      ansible-playbook oim_cleanup.yml

To uninstall the Omnia core container, on the OIM, run the following script::

   ./omnia.sh --uninstall

View Usage Instructions for Omnia Core Container
-------------------------------------------------

The ``omnia.sh --help`` command provides usage instructions for managing the Omnia core container. 
The help menu lists the supported actions you can perform, such as installing and uninstalling the Omnia Core Container.

To view the usage instructions, on the OIM, run the following command::

  ./omnia.sh --help

The help menu includes:

  * ``--install``: Deploys the ``omnia_core`` container and configures it as a Systemd service.
  * ``--uninstall``: Stops and removes the ``omnia_core`` container and its associated service.
  * ``--help``: Display usage information.
