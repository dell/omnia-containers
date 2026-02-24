Upgrade Omnia
================
This section describes how to upgrade Omnia Core containers.

Upgrade omnia core container
----------------------------

Prerequisites
--------------

* Run the following command to retrieve the omnia.sh file for 2.1 version. ::

    wget https://raw.githubusercontent.com/dell/omnia/refs/heads/pub/q1_dev/omnia.sh

* Omnia 2.1 image must be available in the OIM. If the image is not available, run the following command to download the image. ::

    ./build_images.sh core core_tag=2.1 omnia_branch=pub/q1_dev

* Ensure that Omnia 2.0 core container is running.
* Go to the directory where the omnia.sh file for version 2.1 is located.

Omnia Configurations
--------------------

The following operations can be performed on the Omnia Core Containers: Install, uninstall, version, upgrade, and rollback.

.. image:: images/omnia_configurations_list.png

For more information on usage instructions, see :ref:`View Usage Instructions for Omnia Core Container <view_omnia_core_container>`.

View Omnia Version and Upgrade Options
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

1. To view the Omnia version, run the following command: ::
    
    ./omnia.sh --version

.. image:: images/omnia_output_version.png

2. To perform an upgrade, run the following command: ::
    
    ./omnia.sh --upgrade

   The available upgrade versions are displayed.

.. image:: images/omnia_upgrade_options.png

3. Select the relevant version and press **Enter**. An approval gate is generated and the destination location of the backup files is displayed. 
The upgrade process runs inside the ``Omnia_core`` container.

.. Note::
    By default, the backup files are created and stored in the directory ``/opt/omnia/backups/upgrade/<version>``, in the NFS share path.

4. Enter **yes** to backup the current input files.

The backup is created and a container swap is initiated. The health of the container is checked.

After successful completion, the container is swapped and the upgrade is completed. A success message is displayed.

.. image:: images/upgrade_successful.png

Run ``upgrade_omnia.yml`` to complete the process.

.. Note::
    Run the command after the container is healthy and stable.

.. image:: images/upgrade_running.png

Running playbooks other than the ``upgrade_omnia.yml`` before ``./omnia.sh --upgrade`` generates an error with instructions.

.. image:: images/upgrade_error_trigger.png

Choose one of the following options when the error is displayed:

**Option 1: Migrate Input Files**

Run the ``upgrade_omnia.yml`` playbook. ::

    ansible-playbook /omnia/upgrade/upgrade_omnia.yml

The input files are migrated from 2.0 to 2.1 format.

.. image:: images/successful_input_migration.png

The system displays guidance after successful migration completes.

If any configuration files are missing from the backup, a warning is generated before reprovisioning is started.

.. image:: images/missing_config_files_warning.png

**Option 2: Skip Migration**

Remove the upgrade lock using the following command: ::

    rm /opt/omnia/.data/upgrade_in_progress.lock

After the lock is removed, manually reconfigure default input files of the upgraded version

Other playbooks are allowed to run normally.
