Space Requirements for the OIM
===================================

* For all available software packages that Omnia supports: 15GB
* For the complete set of software images: 10GB
* For Omnia Logs and configuration files: 30GB
* For PostgreSQL database used for BuildStreaM: 30GB
* For nodes with limited storage space, Omnia suggests to run the ``omnia.sh`` with NFS details.

.. note:: Ensure that the Omnia Infrastructure Manager (OIM) node, each Service Kubernetes cluster node, and each Slurm compute node have at least 64 GB of RAM.


.. csv-table:: Space requirements for images and packages on OIM / NFS share
   :file: ../../Tables/RHEL_space_req.csv
   :header-rows: 1
   :keepspace:
