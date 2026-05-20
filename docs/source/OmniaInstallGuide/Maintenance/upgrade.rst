Upgrade Omnia
================

Omnia supports only upgrading Omnia core container and migrating the respctive input files.

Prerequisites
--------------

* Ensure Omnia version 2.0.0.0 core container is running (core tag - 1.0).

* Omnia 2.1 image must be available in the OIM. If the image is not available, run the following command to download the image. ::

    ./build_images.sh core core_tag=2.1 omnia_branch=v2.1.0.0-rc2

For more information about deploying the Omnia core container, see `Deploy Omnia Core Container <OmniaInstallGuide/RHEL_new/omnia_startup.html>`_.

Upgrade Steps
--------------

If the ``omnia.sh`` script from version v2.0.0.0 already exists, either replace it with the newer version or place the new script in a different directory and run it from there.

1. Download the omnia.sh script using the following commands:
    
    * To use the tagged version of Omnia, run the following command: ::

        wget https://raw.githubusercontent.com/dell/omnia/refs/tags/${OMNIA_VERSION}/omnia.sh

    * To use the specific branch of Omnia, run the following command: ::

        wget https://raw.githubusercontent.com/dell/omnia/refs/heads/${OMNIA_VERSION}/omnia.sh

.. note:: Replace ``${OMNIA_VERSION}`` with the target version (for example, ``v2.1.0.0``).

The following operations can be performed on the Omnia Core Containers: Install, uninstall, version, upgrade, and rollback. ::

    ./omnia.sh --help

    Usage: ./omnia.sh [--install | --uninstall | --upgrade | --rollback | --version | --help]
        -i, --install     Install and start the Omnia core container
        -u, --uninstall   Uninstall the Omnia core container and clean up configuration
        --upgrade     Upgrade the Omnia core container to newer version
        --rollback    Rollback the Omnia core container to previous version
        -v, --version     Display Omnia version information
        -h, --help        More information about usage

For more information on usage instructions, see `Deploy Omnia Core Container <OmniaInstallGuide/RHEL_new/omnia_startup.html>`_.

.. note:: Upgrade is not supported from version v2.1.0.0-rc2 to v2.1.0.0
        
2. To perform an upgrade on the Omnia core container, run the following command: ::
    
    ./omnia.sh --upgrade

3. Select the relevant version and press **Enter**. An approval gate is generated and the destination location of the backup files is displayed. 
The upgrade process runs inside the ``Omnia_core`` container.

.. note::
    By default, the backup files are created and stored in the directory ``/opt/omnia/backups/upgrade/<version>``, in the OIM share path.

4. To proceed with the upgrade, enter **yes**.

The backup is created and a container swap is initiated. The health of the container is checked.

After successful completion, the container is swapped and the upgrade is completed. A success message with the latest updated version is displayed.

5. Run the ``upgrade_omnia.yml`` playbook. ::

    ansible-playbook /omnia/upgrade/upgrade_omnia.yml

.. note::
    * Run the command after the container is healthy and stable.
    * Running playbooks other than the ``upgrade_omnia.yml`` before ``./omnia.sh --upgrade`` generates an error with instructions.


The input files are migrated from 2.0 to 2.1 format.

The system displays guidance after successful migration completes.

If any configuration files are missing from the backup, a warning is generated before reprovisioning is started.

.. note::
    If you have not run any playbooks in Omnia 2.0, remove the upgrade lock using the following command: ::

        rm /opt/omnia/.data/upgrade_in_progress.lock

    After the lock is removed, manually reconfigure default input files of the upgraded version. Other playbooks are allowed to run normally.

6. To view the Omnia version, run the following command: ::
    
    ./omnia.sh --version

LocalRepo Upgrade
-----------------

Omnia's LocalRepo functionality now supports RHEL minimum version upgrades, enabling seamless repository management across multiple RHEL versions. It allows clean upgrades without repository conflicts while maintaining separate logs, metadata, and cleanup for each version. Existing RHEL 10.0 setups remain fully supported. Managing multiple versions at the same time is currently not supported.

SLURM Cluster Upgrade
---------------------

When upgrading, the SLURM cluster requires configuration migration and reprovisioning to ensure compatibility with the latest version.

Prerequisites
~~~~~~~~~~~~~

Before upgrading your SLURM cluster, ensure the following:

* Omnia core container has been successfully upgraded to version v2.1.0.0
* The ``upgrade_omnia.yml`` playbook has been executed
* All input configuration files have been migrated to the v2.1.0.0 format
* Ensure the NFS storage is accessible and the NFS share paths are correctly configured
* If SLURM cluster is already deployed and running, ensure it is in a stable state with no active jobs or maintenance operations in progress

Configuration Migration
~~~~~~~~~~~~~~~~~~~~~~

Review Updated Input Files
*************************

After upgrading Omnia core, review and update the following configuration files in ``/opt/omnia/input/project_default/``:

network_spec.yml
================

If any new InfiniBand fabric settings need to be defined in the ``ib_network`` section:

.. code-block:: yaml

    - ib_network:
        subnet: <subnet_manager_ip>
        netmask_bits: <netmask_bits>

Ensure host InfiniBand interfaces map to the IB network entries.

omnia_config.yml
================

With upgrade_omnia.yml, all the essential inputs will be migrated to the new structure. If required, update the ``slurm_cluster`` section with the new input parameters. The new additional fields are optional:

.. code-block:: yaml

    slurm_cluster:
      - cluster_name: <cluster_name>
        nfs_storage_name: <nfs_storage_name>
        config_sources:
          <config_name>: <path> or <mapping>
        skip_merge: <true|false>
        node_discovery_mode: <homogeneous|heterogeneous>
        node_hardware_defaults:
          <group_name>:
            sockets: <value>
            cores_per_socket: <value>
            threads_per_core: <value>
            real_memory: <value>

storage_config.yml - PowerVault Configuration
==============================================

If your SLURM cluster uses PowerVault storage, review and update the PowerVault configuration in ``storage_config.yml``:

.. code-block:: yaml

    powervault_config:
      ip:
        - <powervault_controller_ip>
      port: <iscsi_port>
      iscsi_initiator: <iqn_identifier>
      volume_id: <volume_wwn_identifier>

After configuration migration, reprovision the cluster to apply new settings and enable new features. Run the following playbooks in order:

Step 1: Build Local Repository
******************************

.. code-block:: bash

    ansible-playbook local_repo/local_repo.yml

This prepares the local repository with required packages for cluster provisioning.

Step 2: Build x86_64 Compute Node Image
****************************************

.. code-block:: bash

    ansible-playbook build_image_x86_64/build_image_x86_64.yml

This creates the base compute node image for x86_64 architecture.

Step 3: Build aarch64 Compute Node Image (if applicable)
*******************************************************

Only run this step if your cluster includes aarch64 nodes:

.. code-block:: bash

    ansible-playbook build_image_aarch64/build_image_aarch64.yml

Run this after the x86_64 image build completes.

Step 4: Discover and Configure Cluster
**************************************

.. code-block:: bash

    ansible-playbook discovery/discovery.yml

Step 5: PXE boot the nodes preferably in the following order
*************************************************************

* slurm_control_node 
* slurm_node 
* login_node

Adding or Removing SLURM Nodes
*******************************

With v2.1.0.0, SLURM supports adding new nodes or removing existing nodes by modifying the PXE mapping file. The discovery playbook automatically detects changes and updates the SLURM configuration accordingly. Refer to the `Add New SLURM Nodes <https://omnia-devel.readthedocs.io/en/omnia-docs-v2.1.0.0-rc2/OmniaInstallGuide/RHEL_new/OmniaCluster/BuildingCluster/install_slurm.html#add-new-slurm-nodes>`_ section for more details.

Backup and restore slurm configuration
**************************************

With v2.1.0.0, SLURM supports backup, rollback, and cleanup of configuration files using the ``utils/slurm_config_util.yml`` playbook. This utility helps manage SLURM configuration states and recover from configuration issues. Refer to the `Backup and Restore SLURM Configuration <https://omnia-devel.readthedocs.io/en/omnia-docs-v2.1.0.0-rc2/OmniaInstallGuide/RHEL_new/OmniaCluster/BuildingCluster/install_slurm.html#slurm-configuration-utilities>`_ section for more details.

BMC Discovery Configuration
---------------------------

Omnia supports automated BMC (Baseboard Management Controller) discovery via Dell OpenManage Enterprise (OME). This feature enables large-scale server discovery and automatic PXE mapping file generation, which is particularly useful for deployments with thousands of nodes.

Prerequisites
~~~~~~~~~~~~~

Before using BMC Discovery, ensure the following:

* Dell OpenManage Enterprise (OME) appliance must be operational and have already discovered the target servers
* ``prepare_oim`` must have been run to set up OME credentials in the Ansible Vault
* The OME appliance must be reachable from the OIM on port 443

Discovery Configuration
~~~~~~~~~~~~~~~~~~~~~~~

Create the ``input/discovery_config.yml`` file with the OME IP address:

.. code-block:: yaml

    # IP address or hostname of the Dell OpenManage Enterprise instance
    ome_ip: "<ome_ip_address>"

Replace ``<ome_ip_address>`` with the IP address or hostname of your OME appliance.

OME Credentials
~~~~~~~~~~~~~~~

OME credentials are stored in an Ansible Vault-encrypted file (``omnia_config_credentials.yml``) and are set up during the ``prepare_oim`` phase. The vault key is stored separately at ``.omnia_config_credentials_key``.

.. note::
    * Credentials are marked ``no_log: true`` and are never written to logs
    * The credential file is decrypted only during playbook execution and re-encrypted after use

Network Configuration
~~~~~~~~~~~~~~~~~~~~~

The ``input/network_spec.yml`` file is used for BMC Discovery IP address derivation. Ensure the following sections are configured:

.. code-block:: yaml

    Networks:
      - admin_network:
          oim_nic_name: "<nic_name>"
          subnet: "<admin_subnet>"
          netmask_bits: "<netmask_bits>"
          primary_oim_admin_ip: "<primary_oim_admin_ip>"
          primary_oim_bmc_ip: ""
          dynamic_range: "<dynamic_range>"
          dns: []
          ntp_servers: []

      - ib_network:
          subnet: "<ib_subnet>"
          netmask_bits: "<ib_netmask_bits>"

The ``admin_network.subnet`` and ``ib_network.subnet`` are used to derive host IP addresses from discovered BMC IPs:

* **ADMIN_IP:** ``{admin_subnet[0:2]}.{bmc_ip[2:4]}``
* **IB_IP:** ``{ib_subnet[0:2]}.{bmc_ip[2:4]}`` (only if InfiniBand NIC is detected)

Running BMC Discovery
~~~~~~~~~~~~~~~~~~~~~

To perform BMC discovery using OME, run the following command:

.. code-block:: bash

    ansible-playbook discovery/discovery.yml -e "discovery_mechanism=ome"

This will:

1. Authenticate with the OME REST API
2. Collect server inventory (service tags, iDRAC details, NIC MACs, group membership)
3. Generate a timestamped PXE mapping file: ``bmc_pxe_mapping_file_<timestamp>.csv``

The generated CSV file contains the following columns:

``FUNCTIONAL_GROUP_NAME,GROUP_NAME,SERVICE_TAG,PARENT_SERVICE_TAG,HOSTNAME,ADMIN_MAC,ADMIN_IP,BMC_MAC,BMC_IP,IB_MAC,IB_IP``

Post-Discovery Steps
~~~~~~~~~~~~~~~~~~~~

After discovery completes:

1. Review the timestamped ``bmc_pxe_mapping_file_<timestamp>.csv``
2. Adjust ``FUNCTIONAL_GROUP_NAME`` if needed (e.g., ``slurm_control_node_x86_64``, ``service_kube_control_plane_x86_64``)
3. Adjust ``GROUP_NAME`` if needed
4. Update ``HOSTNAME`` values if the auto-generated sequence is not desired
5. Copy or rename the desired timestamped file to ``pxe_mapping_file.csv`` to hand off to Provisioning
6. For incremental updates, add or remove server entries as needed

.. note::
    Magellan-based discovery is planned for a future release. Currently, only OME-based discovery is supported.
