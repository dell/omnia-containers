Upgrade Omnia
================

Omnia supports only upgrading Omnia core container and migrating the respctive input files.

Prerequisites
--------------

* Ensure that Omnia 2.0 core container is running.

* Omnia 2.1 image must be available in the OIM. If the image is not available, run the following command to download the image. ::

    ./build_images.sh core core_tag=2.1 omnia_branch=v2.1.0.0-rc2

For more information about deploying the Omnia core container, see `Deploy Omnia Core Container <OmniaInstallGuide/RHEL_new/omnia_startup.html>`_.

Omnia Configurations
--------------------

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

1. Run the following command to retrieve the omnia.sh file for 2.1 version. ::

    wget https://raw.githubusercontent.com/dell/omnia/refs/heads/pub/q1_dev/omnia.sh

2. To perform an upgrade on the Omnia core container, run the following command: ::
    
    ./omnia.sh --upgrade

3. Select the relevant version and press **Enter**. An approval gate is generated and the destination location of the backup files is displayed. 
The upgrade process runs inside the ``Omnia_core`` container.

.. Note::
    By default, the backup files are created and stored in the directory ``/opt/omnia/backups/upgrade/<version>``, in the OIM share path.

4. To proceed with the upgrade, enter **yes**.

The backup is created and a container swap is initiated. The health of the container is checked.

After successful completion, the container is swapped and the upgrade is completed. A success message with the latest updated version is displayed.

5. Run ``upgrade_omnia.yml`` to complete the process.

.. Note::
    * Run the command after the container is healthy and stable.
    * Running playbooks other than the ``upgrade_omnia.yml`` before ``./omnia.sh --upgrade`` generates an error with instructions.

6. Run the ``upgrade_omnia.yml`` playbook. ::

    ansible-playbook /omnia/upgrade/upgrade_omnia.yml

The input files are migrated from 2.0 to 2.1 format.

The system displays guidance after successful migration completes.

If any configuration files are missing from the backup, a warning is generated before reprovisioning is started.

.. Note::
    If you have not run any playbooks in Omnia 2.0, remove the upgrade lock using the following command: ::

    rm /opt/omnia/.data/upgrade_in_progress.lock

 After the lock is removed, manually reconfigure default input files of the upgraded version. Other playbooks are allowed to run normally.

7. To view the Omnia version, run the following command: ::
    
    ./omnia.sh --version