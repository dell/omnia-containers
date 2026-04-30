Step 10: Build and configure your cluster
===========================================

The ``omnia.yml`` playbook allows you to set up the following on your cluster:

    * **Centralized authentication**: Once all the required parameters in `security_config.yml <schedulerinputparams.html#security-config-yml>`_ are filled in, ``omnia.yml`` can be used to set up FreeIPA/OpenLDAP.

    * **Slurm**: Once all the required parameters in `omnia_config.yml <schedulerinputparams.html#id13>`_ are filled in, ``omnia.yml`` can be used to set up Slurm.

    * **Kubernetes**: Once all the required parameters in `omnia_config.yml <schedulerinputparams.html#id12>`_ are filled in, ``omnia.yml`` can be used to set up Kubernetes.

.. toctree::
    :maxdepth: 2

    schedulerprereqs
    schedulerinputparams
    BuildingCluster/index






