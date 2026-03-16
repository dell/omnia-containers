===============
OIM Cleanup
===============

The ``oim_cleanup.yml`` playbook can be utilized to roll back any configurations made on the OIM. 

Tasks performed by the playbook
================================

The ``oim_cleanup.yml`` playbook performs the following tasks:

* Clean up all containers, log files, and metadata on the OIM node.
* Clean up any PostgreSQL database deployed as part of BuildstreaM on the OIM.
* Rollback the firewall ports on the OIM node to its default setting.

Steps
=========

1. To clean up the OIM and the PostgreSQL database which is deployed as part of BuildStreaM, perform one of the following:

    
    * If the BuildStreaM PostgreSQL database is not deployed on the OIM node, and you want to clean up the OIM, run the following command: ::

        ssh omnia_core
        cd /omnia/utils
        ansible-playbook utils/oim_cleanup.yml 
    
    * If the BuildStreaM PostgreSQL database is deployed on the OIM node, and you want to clean up the OIM and the PostgreSQL database, run the following command: ::

        ssh omnia_core
        cd /omnia/utils
        ansible-playbook utils/oim_cleanup.yml -e postgres_backup=false
    
    .. note:: 

        * The ``postgres_backup`` parameter determines whether the PostgreSQL database should be backed up before cleanup.
        * If ``postgres_backup`` is set to ``true``, the database will be backed up before cleanup.
        * If ``postgres_backup`` is set to ``false``, the database will not be backed up before cleanup.

    * If the BuildStreaM PostgreSQL database is deployed on the OIM node, and you want to clean up the OIM but retain the PostgreSQL database, run the following command: ::

        ssh omnia_core
        cd /omnia/utils
        ansible-playbook utils/oim_cleanup.yml -e postgres_backup=true

    .. important:: When prompted to back up the PostgreSQL database that you want to retain, record the database credentials. These credentials are required to restore the database when running the ``prepare_oim.yml`` playbook.


2. After running the ``oim_cleanup.yml`` playbook, do the following:

    1. Reboot the OIM node to ensure all changes take effect.

    2. The playbook does **not** remove data stored under the NFS ``server_share_path`` (See ``storage_config.yml``).
            
        - Reusing the same ``server_share_path`` for new deployments can cause deployment failures or inconsistent Kubernetes/Slurm behavior.
        - For a fresh deployment, either manually clean this directory or use a new NFS export/path.

    3. The ``omnia_core`` container is **not** removed by ``oim_cleanup.yml``.

        - To delete it, log in to the OIM node and run::
                    
            omnia.sh --uninstall

.. caution::
    * After a clean-up, when re-provisioning your cluster by re-running the ``discovery.yml`` playbook, ensure to use a different ``admin_nic_subnet`` in ``input/provision_config.yml`` to avoid a conflict with newly assigned servers. Alternatively, disable any OS available in the ``Boot Option Enable/Disable`` section of your BIOS settings (``BIOS Settings`` > ``Boot Settings`` > ``UEFI Boot Settings``) on all target nodes.
    * On subsequent runs of ``discovery.yml``, if users are unable to log into the server, refresh the ssh key manually and retry. ::

        ssh-keygen -R <node IP>

