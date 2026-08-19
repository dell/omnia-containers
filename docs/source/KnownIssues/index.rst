Known Issues
==============

.. toctree::
    
    General_query
    Login
    Provision
    Telemetry

**Slurm Version Pinning Issue**

EPEL repositories now ship **Slurm 26.x** packages, which conflicts with the **Slurm 25.05.2** packages expected by Omnia v2.1.0.0. For detailed troubleshooting steps and resolution, see `Slurm Version Mismatch (26.x vs 25.05.2) <../troubleshootingguide.html#slurm-version-mismatch-26-x-vs-25-05-2>`_ in the Troubleshooting Guide.

For the complete workaround with JSON configuration files, see `Slurm Version Pinning Workaround <../OmniaInstallGuide/RHEL_new/CreateLocalRepo/SlurmVersionPinningWorkaround.html>`_.
