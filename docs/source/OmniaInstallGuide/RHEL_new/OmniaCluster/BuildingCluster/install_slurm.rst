Step 11: Set up Slurm on nodes
==============

**Prerequisites**

* Provide the Slurm 25.05.2 user repository.
* Fill the mandatory parameters in ``omnia_config.yml``: `Input parameters for the cluster <../schedulerinputparams.html#id13>`_
* Fill the parameters in ``storage_config.yml``: `Input parameters for the cluster <../schedulerinputparams.html#id13>`_
* Add ``slurm_custom`` to ``software_config.json`` and add ``slurm_custom`` subgroups.
* Add ``slurm_custom`` repository URL to ``user_repo_url_x86_64`` or ``user_repo_url_aarch64`` in ``local_repo_config.yml``.


**Setup Slurm:**

1. To download the artifacts required to set up Slurm on the nodes, run the ``local_repo.yml`` playbook.
2. To build diskless images for cluster nodes, run build_image_x86_64.yml or build_image_aarch64.yml: `Build cluster node images <../../build_images.html>`_
3. To discover the potential cluster nodes, configure the boot script, and cloud-init based on the functional groups, run  the ``discovery.yml`` playbook: `Discover cluster nodes <../../Provision/index.html>`_
4. After successfully executing the ``discovery.yml`` playbook, you can PXE boot the slurm node, login node, and login compiler node simultaneously.

.. note:: If you want to deploy only Slurm clusters (``slurm_custom``), the ``idrac_telemetry_support`` parameter must be set to ``false`` in the ``telemetry_config.yml`` file. Omnia is Validated for Slurm version 25.05. If you use any other version, some functionality like PAM may not work.

5. To export openmpi, do the following: ::

                export MPI_HOME=/share_omnia/benchmarks/openmpi

                export PATH=$MPI_HOME/bin:$PATH

                export LD_LIBRARY_PATH=$MPI_HOME/lib:$MPI_HOME/lib64:$LD_LIBRARY_PATH

                <share_omnia> : nfs client share path for slurm in storage_config.yml


**Slurm with GPU:**

**Prerequisites**

* You must have the ``user_repo`` which is compiled with nvml and cgroup-v2. If slurm-nodes have GPU then you must provide at least one ``login_compiler_node``.


.. note:: If the iDRAC of a Slurm node is not accessible through OIM—because of issues such as an incorrect iDRAC port configuration or invalid credentials—the node configuration specified in ``/etc/slurm/slurm.conf`` for ``NodeName`` will default to: ``Sockets=1 CoresPerSocket=1 ThreadsPerCore=1 RealMemory=3774873``. Update ``slurm.conf`` with the correct hardware values and run ``scontrol reconfigure`` to apply the changes.