Step 14: Verify Slurm Cluster and Kubernetes on the Service Cluster
============================================================================================================

**Slurm cluster**


After booting the nodes, verify the following to ensure slurm is deployed successfully: 
On slurm controller node

    * Verify if the required services are running. Run the following commands and confirm that each service is active (running):
    
    ::

          systemctl status munge
          systemctl status slurmctld
          systemctl status slurmdbd
          systemctl status mariadb

    * Verify the node status with sinfo:

          .. image:: ../../images/sinfo.jpg
   
          * Ensure that the compute nodes are listed and the node state should be idle.

It is recommended to store job output and error files in NFS-mounted directories (``/var/log/slurm/``) so that job logs are persisted.

**Slurm cluster with GPU**

* On Slurm nodes that have GPUs, it may take some time for Slurmd to start because of the GPU driver installation. To view the logs during this process, you can run: ::
      
      tail -f /var/log/cloud-init-output.log

* The CUDA installation path on the OIM and nodes must be ``{client_share_path}/slurm/cuda``. 
* The ``client_share_path`` is the same as mentioned in ``storage_config.yml`` for ``nfs_slurm``. 


**PAM Feature for Slurm**

Slurm PAM restricts SSH access to compute nodes for non-root users. You can log in only while their job is actively running on the node. After the job is completed, you are automatically logged out.  

On login node: Switch to the LDAP user:
::
      ssh <ldap_user>@<login_node_hostname>
      sbatch job.sh

While the job is running, ssh as ``<ldap_user>`` to the slurm node where the job is running. After the job is completed, ``<ldap_user>`` is logged out.


**Kubernetes on the service cluster**

Run the following commands on Kubernetes controller node: 

:: 

    kubectl get pods -A -o wide
    kubectl get nodes -o wide
 