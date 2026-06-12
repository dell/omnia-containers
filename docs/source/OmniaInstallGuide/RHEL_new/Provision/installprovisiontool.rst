Provision the Cluster Nodes
============================

The ``provision.yml`` playbook provisions the probable bare-metal cluster nodes. This playbook is dependent on inputs from the pxe mapping file:

* ``/opt/omnia/input/project_default/provision_config.yml``
* ``/opt/omnia/input/project_default/network_spec.yml``

.. note:: The first PXE device on target nodes should be the designated active NIC for PXE booting.

    .. image:: ../../../images/BMC_PXE_Settings.png
        :width: 600px

Configurations made by the ``provision.yml`` playbook
------------------------------------------------------

* Provisions all target servers.
* Configures the boot script based on the functional groups.
* Configures the cloud-init based on the functional groups.
* Applies additional cloud-init configurations (if configured). See `Additional Cloud-Init Configuration <../../AdvancedConfigurations/additional_cloud_init.html>`_.
* Deploys iDRAC telemetry service on the service cluster.
* Deploys LDMS on the service cluster.


Playbook execution
----------------------

**Prerequisites**

Before running the ``provision.yml`` playbook:

* Ensure that the images are created for each functional group. To verify that the images are created, run the following command on the OIM::

    s3cmd ls -Hr s3://boot-images

To deploy the Omnia provision tool, execute the following commands: ::

    ssh omnia_core
    cd /omnia/provision
    ansible-playbook provision.yml

.. note::

    * After executing ``provision.yml`` playbook, you can check the log files available at ``/opt/omnia/log`` for more information.

    * To identify any issues on the node booted, check the ``/var/log/cloud-init-output.log``.

    * Omnia does not track the OS installation on the target node. User has verify the installation status manually.

    * Ansible playbooks by default run concurrently on 5 nodes. To change this, update the ``forks`` value in ``ansible.cfg`` present in the respective playbook directory.

    * While the ``admin_nic`` on cluster nodes is configured by Omnia to be static, the public NIC IP address should be configured by user.

    * All ports required by OpenCHAMI will be opened (For a complete list, see :doc:`Omnia Ports <omnia_ports>`).

    * After running ``provision.yml``, the file ``/opt/omnia/input/project_default/omnia_config_credentials.yml`` will be encrypted. To edit the file, use the command: ``ansible-vault edit omnia_config_credentials.yml --vault-password-file .omnia_config_credentials_key``

    * Post execution of ``provision.yml``, IPs/hostnames cannot be re-assigned by changing the mapping file.

.. caution::

    * In case of any IP route conflict between Admin network and additional NIC (for example: Internet NIC), delete the Admin route or configure the IP route priority based on your cluster requirements.

    * If the internet connection is required on the target node, configure it after the node is booted. 
    
    * To avoid breaking the password-less SSH channel on the OIM, do not run ``ssh-keygen`` commands post execution of ``provision.yml`` to create a new key.

    * Do not delete the Omnia shared path or the NFS directory.

**Next steps**:

* After successfully running the ``provision.yml`` playbook, you can either manually PXE boot the nodes or use the ``set_pxe_boot.yml`` playbook. PXE booting allows the nodes to load diskless images from the Omnia Infrastructure Manager (OIM). For detailed steps on using ``set_pxe_boot.yml``, see :ref:`set-pxe-boot-order`.
* Execute ``telemetry.yml`` to start the telemetry collection.