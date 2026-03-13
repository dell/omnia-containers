============================
Troubleshooting guide
============================

Troubleshooting Core Container Failures
=========================================

The deployment of the Omnia core container may fail for the following reasons:

- The ``omnia.sh`` script aborts early.
- ``podman pull`` fails.
- The Omnia core container starts but cannot write to the shared path.

**Resolution:**

Peform the following steps:

1.  Verify the Omnia core container status using the following command:

.. code-block:: bash

   podman ps --format 'table {{.Names}}\t{{.Status}}'

2. Review Omnia core container logs using the following command:

.. code-block:: bash

   podman logs -n 200 omnia_core

3. Verify time synchronization on the OIM. TLS communication between Omnia containers
   depends on accurate time synchronization.

   Use the following commands to check time synchronization status:

   .. code-block:: bash

      timedatectl status
      chronyc tracking || chronyc sources -v

   If time drift is detected, enable Chrony or NTP and re-synchronize time before
   proceeding.

4. Ensure that the OIM hostname meets the following requirements. If not, rename the host to comply with the hostname rules and re-run the ``omnia.sh`` script.

 - No dot (``.``), underscore (``_``), or comma (``,``)
 - No leading or trailing hyphen (``-``)
 - No uppercase characters
 - Must not start with a digit
 - Fully qualified domain name (FQDN) length must be ≤ 64 characters

5. Check whether Podman is installed and able to pull images. If not, install podman and verify podman login.

6. Verify outbound network connectivity from the OIM.

7. Validate the NFS shared path and SELinux context. To fix any issues related to NFS, export the NFS share with ``no_root_squash`` enabled, ensure the shared path has 755 permissions, and bind the shared path with SELinux relabeling.

.. code-block:: bash

   podman run --rm -v /shared:/mnt:z registry.access.redhat.com/ubi10/ubi sh -lc 'touch /mnt/.rw'

If unsure, start with a **local** shared path and switch to NFS later.

8. After applying the fixes, re-run the ``omnia.sh`` script to deploy the Omnia core
container.

Troubleshooting failures during prepare OIM 
================================================

The prepare OIM playbook may fail for the following reasons:

- Certificate or TLS failures
- Expected container not created
- Service is running but unreachable

**Resolution**

Verify container inventory:

.. code-block:: bash

   podman ps --format 'table {{.Names}}\t{{.Image}}\t{{.Status}}'

Common Container Logs and Debugging Shortcuts
==============================================

Use the following commands to troubleshoot container issues across Omnia services.

* To view list of all Omnia containers, run the following command:

.. code-block:: bash

   podman ps -a

* To view container logs, run the following command:

.. code-block:: bash

   podman logs -n 200 <container>

* To test outbound connectivity from a container, run the following command:

.. code-block:: bash

   podman exec -it <container> sh -lc 'curl -I https://example.com'


PXE Boot Hangs During Node Replacement
=====================================

When an existing node is replaced with a new node and ``discovery.yml`` is rerun, the new node may hang during PXE boot at ``nm-wait-online-initrd.service``.

**Cause**: An IP address conflict occurs when the new node is assigned an IP address that is still in use by the old node on the network.

**Resolution**: Before adding the new node, complete the following steps:

- Ensure the old node is powered off or disconnected from the network.
- Verify that the IP address is not in use by any other device.
- Rerun ``discovery.yml`` after confirming that no IP conflicts exist.


Checking and updating encrypted parameters
=============================================

1. Move to the file path where the parameters are saved (as an example, we will be using ``omnia_config_credentials.yml``): ::

        cd /opt/omnia/input/project_default/

2. To view the encrypted parameters: ::

        ansible-vault view omnia_config_credentials.yml --vault-password-file .omnia_config_credentials_key


3. To edit the encrypted parameters: ::

        ansible-vault edit omnia_config_credentials.yml --vault-password-file .omnia_config_credentials_key


Checking podman container status from the OIM
===============================================
   
   * Use this command to get a list of all running podman conatiners: ``podman ps``
   * Check the status of any specific podman containers: ``podman ps -f name=<container_name>``


Packages download issues during ``local_repo.yml`` playbook execution
=========================================================================

1. The ``local_repo.yml`` playbook generates and provides log files as part of its execution. For example, if the local repository is partially unsuccessful for nfs, analyze the issue using the following steps: 

.. image:: ../images/troubleshoot_local_repo.png

2. To view the overall download status of all software in the .csv format, run the following command:

::

        opt/omnia/log/local_repo/<arch>/software.csv

Example: :: 

        /opt/omnia/log/local_repo/x86_64/software.csv

.. image:: ../images/troubleshoot_local_repo_1.png

3. To view the overall download status of all packages and the log filenames for a specific software, run the following command:

::

        /opt/omnia/log/local_repo/<sw>_task_results.log

Example: For nfs: ::

         /opt/omnia/log/local_repo/x86_64/nfs_task_results.log

.. image:: ../images/troubleshoot_local_repo_2.png

4. To view the package level status, run the following command: 

::

         /opt/omnia/log/local_repo/x86_64/<sw>/status.csv

Example: ::

        /opt/omnia/log/local_repo/x86_64/nfs/status.csv

.. image:: ../images/troubleshoot_local_repo_3.png

5. To view the issues information and the reason for job being unsuccessful, see the ``package_status_<pid>.log`` file mentioned in the ``<sw>_task_result.log``.

Example: ::
        
        /opt/omnia/log/local_repo/x86_64/nfs/logs/package_status_41422.log

.. image:: ../images/troubleshoot_local_repo_4.png


local_repo.yml playbook fails when run multiple times
======================================================

The ``local_repo.yml`` playbook fails at ``TASK: [parse_and_download : Process URL mirrors from local_repo_config]`` if it is run multiple times.

**Cause**: This occurs due to resource saturation on the Pulp container.

**Resolution**: If you are running ``local_repo.yml`` playbook multiple times and encounter a failure at the task ``Process URL mirrors from local_repo_config``, it is recommended to let the system remain idle for approximately one hour before re-running the ``local_repo.yml`` playbook.


Troubleshooting logs
=================================================================

For more information, see `Logs <../Logging/OIM_logs.html>`_.



Troubleshooting PowerScale isilon pods after node reboot
========================================================================================================================

Why is the PowerScale (Isilon) CSI controller pod in CrashLoopBackOff after a node reboot, and how can it be resolved?

.. image:: ../images/troubleshoot_powerscale_1.png

.. image:: ../images/troubleshoot_powerscale.jpg


**Resolution**: Do the following:

1. Inspect recent logs from the controller deployment: ::

        kubectl logs deploy/isilon-controller -n isilon --all-containers=true | tail -n 60

2. Restart the Isilon controller deployment: ::

        kubectl rollout restart deployment isilon-controller -n isilon

3. Restart the Isilon node daemonset: ::

        kubectl rollout restart daemonset isilon-node -n isilon

These actions ensure that any components affected by the reboot are recreated properly and resume normal operation.


Troubleshooting LDMS on the slurm nodes
=============================================


.. image:: ../images/troubleshoot_ldms_1.png

1. Check the ldms aggregator and ldms store logs. ::

        kubectl logs -n telemetry nersc-ldms-aggr-0
        kubectl logs -n telemetry nersc-ldms-store-slurm-cluster-0

2. SSH to the slurm node from where the LDMS metrics are not retrieved.
3. Run ``sudo systemctl status ldmsd.sampler.service`` and check ldmsd service is running on the slurm nodes.

.. image:: ../images/troubleshoot_ldms_2.png

4. If the ldmsd daemon is running, check whether supported plugins are loaded using the following command: ::

                /opt/ovis-ldms/sbin/ldms_ls -a ovis -A conf=/opt/ovis-ldms/etc/ldms/ldmsauth.conf -p 10001 -h localhost

.. image:: ../images/troubleshoot_ldms_3.png

5. If ldms plugins are loaded, check the metrics of each plugin using the following command: 

.. image:: ../images/troubleshoot_ldms_4.png

Get the ldsm_port from the file /opt/ovis-ldms/etc/ldms/ldmsd.sampler.env and run the following command: ::

        ldms_ls -l -a ovis -A conf=/opt/ovis-ldms/etc/ldms/ldmsauth.conf -p <ldms_port> -h localhost $(hostname)/<plugin_name>
        
Example: ::
                
                ldms_ls -l -a ovis -A conf=/opt/ovis-ldms/etc/ldms/ldmsauth.conf -p 10001 -h localhost $(hostname)/meminfo





.. image:: ../images/troubleshoot_ldms_5.png
        

Pulp Repository Sync and Publication Failures
===============================================


1. No Space Left on NFS Share (where Pulp is mounted).

**Cause**:  Pulp storage runs out of disk space during sync or publish. In this case , Pulp logs show the error "No space left on device." Check the available storage space on the NFS share.

**Resolution**:  Increase the size of the NFS share where Pulp is mounted to free up space.

2. Incorrect URL in ``local_repo_config.yml``.

**Cause**: The repository URLs in the ``local_repo_config.yml`` file may be incorrect . The URL must point to the repository root (where the repodata directory exists) and be reachable.

**Resolution**: Verify and update the URLs in the local_repo_config.yml file to ensure they are correct and accessible.

3. NFS storage configuration or performance

**Cause**: If Pulp is mounted on NFS, network delays can impact performance, potentially causing sync or publication issues.

**Resolution**: Reduce ``PULP_SYNC_CONCURRENCY`` and ``PULP_PUBLISH_CONCURRENCY`` to 1 in ``config.py``.

**Location**: ::

                vi  common/library/module_utils/local_repo/config.py
                PULP_SYNC_CONCURRENCY =  1
                PULP_PUBLISH_CONCURRENCY = 1

Re-run Failed Operations: After making the changes, re-run the Ansible playbook to retry the failed operations:
``ansible-playbook local_repo.yml``.


After job submission on the Slurm cluster, compute nodes intermittently enter the DRAINED state
=================================================================================================

When Slurm nodes go into a DRAINED state after job submission, one possible cause is a failure in an epilog script under ``/etc/slurm/epilog.d`` due to incorrect file permissions.

To resolve, ensure the epilog script is executable on all Slurm nodes.

For example: ::

        chmod 0755 /etc/slurm/epilog.d/logout_user.sh

After updating the permissions, reload the Slurm configuration: ::

        scontrol reconfigure
        
InfiniBand ports remain in initializing state on hosts
========================================================

In Omnia deployments using InfiniBand (IB) networking, compute or management hosts show InfiniBand ports stuck in the 
Initializing state after boot. Even though the physical link is up, InfiniBand communication between nodes does not work.
Running the following command on the host shows the port state as Initializing::
 
 ibstat

.. image:: ../images/troubleshooting_ib.png

**Cause:**

The Open Subnet Manager (OpenSM) service is not running on the InfiniBand (IB) switch.
Subnet Manager is a fabric‑level service that should be running on the IB switch. If OpenSM is not enabled on the IB switch, the 
InfiniBand fabric cannot complete initialization, causing host ports to remain in the Initializing state.

**Resolution:**

1. Ensure that the Open Subnet Manager service is enabled and running on the InfiniBand switch.
2. After enabling OpenSM on the IB switch, do the following:

    * PXE boot all the IB NIC based nodes.
    * Run the following command on the host: ibstat
    * Verify that the InfiniBand ports state transition to: ``State: Active``
 

Slurm controller functional group is missing
================================================

**Cause**

PXE mapping file missing ``slurm_control_node_*`` groups.

**Resolution**

Update ``pxe_mapping.csv`` with proper controller groups.

``slurm.conf`` missing from backup
================================================

**Cause**

Incomplete backup or corrupted backup directory.

**Resolution**

Choose a different backup or create new backup.


``slurmctld not active`` message during rollback
================================================

**Cause**

Slurm controller service not running.

**Resolution**

Start slurmctld service manually, then retry rollback.


Omnia containers not coming up after OIM reboot
================================================

**Cause**

The Admin NIC on the OIM may have its autoconnect settings disabled (``autoconnect=no``), which stops it from reconnecting automatically after a reboot.

**Resolution**

Ensure that the Admin NIC on the OIM is configured with ``autoconnect=yes`` so it automatically reconnects after reboot. If you changed this configuration, reboot your OIM once to nullify any cache-related or stale configuration issues.


local_repo.yml fails with connectivity errors
============================================

**Cause**

The OIM was unable to reach a required online resource due to a network glitch.

**Resolution**

Verify all connectivity and re-run the playbook.


Software installation fails with checksum error
===============================================

**Cause**

A local repository for the software has not been configured by the ``local_repo.yml`` playbook.

**Resolution**

Follow the steps below to resolve this issue:

1. Re-run the ``local_repo.yml`` playbook with proper inputs to download the software package to the Pulp repository.
2. Once the local repository has been configured successfully, re-run the failed installation script.


local_repo.yml fails due to Epel repository instability
======================================================

**Cause**

If the external Epel repository link mentioned in ``omnia_repo_url_rhel`` is not stable, then it can cause failures in ``local_repo.yml`` playbook execution.

**Resolution**

1. Check if the Epel repository link mentioned in ``omnia_repo_url_rhel`` is accessible.

2. Verify the required software listed in ``software_config.json``, by examining the corresponding ``<software>.json`` files located in the ``input/config/rhel/`` directory. Users can do either of the following, based on the findings:

   - If none of the packages are dependent on the Epel repository, users can remove the Epel repository URL from ``omnia_repo_url_rhel``.

   - If any package required from the Epel repository is listed in the ``software_config.json`` file, it's advisable to either wait for the Epel repository to stabilize or host those Epel repository packages locally. Afterward, remove the Epel repository link from ``omnia_repo_url_rhel`` and provide the locally hosted URL for the Epel repository packages via the ``user_repo_url`` variable.


Kubernetes Pods show ImagePullBackOff or ErrImagePull errors
===========================================================

**Cause**

The errors occur when the Docker pull limit is exceeded.

**Resolution**

* Ensure that the ``docker_username`` and ``docker_password`` are provided in ``/opt/omnia/input/project_default/omnia_config_credentials.yml``.

* For ``ErrImagePull`` and ``ImagePullBackOff`` issue, ensure that local_repo.yml playbook is executed successfully without any failures for packages. Check the local_repo logs for more details. `Click here for more info. <https://kubernetes.io/docs/tasks/configure-pod-container/pull-image-private-registry>`_


Kubernetes cluster nodes reboot
================================

**Resolution**

Wait for 15 minutes after the Kubernetes cluster reboots. To verify the status of the cluster nodes, run the following commands from the ``kube_control_plane``:

1. To get real-time kubernetes cluster status, run:

.. code-block:: bash

   kubectl get nodes

2. To check which pods are in the **Running** state, run:

.. code-block:: bash

   kubectl get pods --all-namespaces

3. To verify that both the kubernetes master and kubeDNS are in the **Running** state, run:

.. code-block:: bash

   kubectl cluster-info


Kubernetes pods not in Running state
====================================

**Resolution**

1. Run ``kubectl get pods --all-namespaces`` to get the status of all the pods.

2. If the pod(s) are not in ``Running`` state, delete it using the command: ``kubectl delete pods <name of pod>``


DNS servers unresponsive causing Kubernetes pods communication failure
==================================================================

**Cause**

The host network is faulty causing DNS to be unresponsive.

**Resolution**

1. In your Kubernetes cluster, run ``kubectl rollout restart deployments coredns -n kube-system`` on any of the ``kube_control_plane``.
2. Wait till the coredns pods are in the running state.


NFS-client provisioner in ContainerCreating or CrashLoopBackOff state
====================================================================

**Cause**

This issue usually occurs when ``server_share_path`` given in ``storage_config.yml`` for ``nfs_name`` does not have an NFS server running.

**Resolution**

* Ensure that ``server_share_path`` mentioned in ``storage_config.yml`` for ``nfs_name: nfs_k8s`` has an active nfs_server running on it.


NFS-client provisioner helm issue with pod describe output
==========================================================

**Cause**

This is a known issue. For more information, click `here. <https://github.com/helm/charts/issues/23743>`_

**Resolution**

1. Wait for some time for the pods to come up. **or**
2. Do the following:

   * Run the following command to delete the pod:

.. code-block:: bash

   kubectl delete pod <pod_name> -n <namespace>

   * Post deletion, the pod will be restarted and it will come to running state.


Kubernetes workloads fail to resolve PowerScale SmartConnect hostname
====================================================================

**Cause**

The SmartConnect hostname is not resolvable by the Kubernetes cluster's internal DNS (CoreDNS).
This typically happens when:
- CoreDNS is unaware of the external DNS zone used by PowerScale.
- The SmartConnect service IP or hostname is not defined in CoreDNS or the upstream DNS servers.

**Resolution**

Step 1 — Identify the SmartConnect Hostname and IP

1. In the PowerScale UI, go to:
   Cluster Management → Network Configuration → Subnets → <Your Subnet Name>
2. Note the following details:
   - SmartConnect Service Name: e.g., management.ps.com
   - SmartConnect IP Address: e.g., 10.x.x.x

Step 2 — Update the CoreDNS ConfigMap

1. On a control-plane node, edit the CoreDNS ConfigMap:

.. code-block:: bash

   kubectl -n kube-system edit configmap coredns

2. Locate the Corefile: section and add a hosts block before the forward or proxy section.
   Example:

.. code-block:: bash

   hosts {
   10.x.x.x management.ps.com
   fallthrough
   }

Replace 10.x.x.x with your actual PowerScale DNS IP.
You can find the DNS IP inside the file:
``/opt/omnia/input/project_default/network_spec.yml → under [dns] field.``

Step 3 — Restart CoreDNS Pods

Apply the changes by restarting CoreDNS:

.. code-block:: bash

   kubectl -n kube-system rollout restart deployment coredns

Verify the CoreDNS pods are running:

.. code-block:: bash

   kubectl -n kube-system get pods -l k8s-app=kube-dns

Step 4 — Validate DNS Resolution

Launch a temporary pod to test name resolution:

.. code-block:: bash

   kubectl run -it dns-test --image=busybox --restart=Never -- sh

Inside the pod shell, test DNS:

.. code-block:: bash

   nslookup management.ps.com

Expected Output:
Server:    10.x.x.x
Address 1: management.ps.com


kubeadm join --control-plane fails with certificate error
=======================================================

**Cause**

During kubeadm init, encrypted control-plane certificates are uploaded to the cluster. These certificates require a certificate key, which expires after approximately two hours. If a control-plane node attempts to join after this window, it cannot download or decrypt certificates, resulting in join failure.

**Resolution**

1. On any existing and healthy control-plane node (not the affected node), run the script located on the shared NFS mount:

.. code-block:: bash

   {{ k8s_client_mount_path }}/generate-control-plane-join.sh

``k8s_client_mount_path`` is the local directory on every Kubernetes node where the NFS share is mounted, allowing all nodes to access and use shared resources automatically.
This script uploads fresh control-plane certificates to the cluster and automatically generates a refreshed control-plane join command. It saves it to ``{{ k8s_client_mount_path }}/control-plane-join-command.sh``

2. On the control-plane node where the join previously failed reboot the node.
3. After reboot, the node automatically reads the refreshed join command from the shared NFS path and successfully adds itself to the cluster. No manual join command execution is required.


Target servers not reachable after PXE booting
==============================================

**Cause**

1. The server hardware does not allow for auto rebooting

2. The process of PXE booting the node has stalled.

**Resolution**

1. Login to the iDRAC console to check if the server is stuck in boot errors (F1 prompt message). If true, clear the hardware error or disable POST (PowerOn Self Test).

2. Hard-reboot the server to bring up the server and verify that the boot process runs smoothly. (If it gets stuck again, disable PXE and try provisioning the server via iDRAC.)


PXE boot fails with tftp timeout or service timeout errors
==========================================================

**Cause**

* Two or more servers in the same network.

* The target cluster node does not have a configured PXE device with an active NIC.

* Additional NIC connected might cause network issues.

**Resolution**

* On the server, go to **BIOS Setup -> Network Settings -> PXE Device**. For each listed device (typically 4), configure an active NIC under ``PXE device settings``.

* Remove the Additional NIC and connect the NIC after the node is booted.


discovery.yml playbook fails at prepare_oim needs to be executed
================================================================

**Cause**

The OpenCHAMI container is not up and running.

**Resolution**

Perform a cleanup using ``oim_cleanup.yml`` and re-run the ``prepare_oim.yml`` playbook to bring up the OpenCHAMI containers. After ``prepare_oim.yml`` playbook has been executed successfully, re-deploy the cluster using the steps mentioned in the `Omnia deployment guide <../../../OmniaInstallGuide/RHEL_new/index.html>`_.


OpenCHAMI smd commands fail with certificate error
==================================================

**Cause**

This issue is because of OpenCHAMI certificate expiration. After sometime, the certificate expires and loses the validity because of which OpenCHAMI commands do not run.

**Resolution**

As part of ``discovery.yml`` execution, certificate updation is being taken care. However, if user still faces this issue, they can update the OpenCHAMI certificate manually by running the following command on OIM:

.. code-block:: bash

   sudo openchami-certificate-update update <OIM_hostname>.<Domain_Name>
   sudo systemctl restart openchami.target


ochami commands fail with token error
====================================

**Cause**

This issue is because of Access Token getting expired after sometime.

**Resolution**

Manually renew the access token by running the below command on OIM:

.. code-block:: bash

   export <OIM_hostname>_ACCESS_TOKEN=$(sudo bash -lc 'gen_access_token')
