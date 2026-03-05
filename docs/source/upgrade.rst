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

        wget https://raw.githubusercontent.com/dell/omnia/refs/heads/${OMNIA_VERSION}/omnia.sh

    * To use the specific branch of Omnia, run the following command: ::

        wget https://raw.githubusercontent.com/dell/omnia/refs/tags/${OMNIA_VERSION}/omnia.sh

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