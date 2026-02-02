Default Admin Debug Packages 
============================
To install admin debug packages on the cluster nodes, add the following entry to the ``softwares`` list in the ``software_config.json`` file::

    {"name": "admin_debug_packages", "arch": ["x86_64", "aarch64"]}

.. note:: Deploying ``admin_debug_packages`` increases the size of the local repository and requires additional disk space.

The following table lists the default admin debug packages installed on the cluster nodes:

.. csv-table:: Admin debug packages
   :file: ../../../Tables/admin_debug_packages_rhel10_x86_64.csv
   :header-rows: 1
   :keepspace:
   :widths: auto
