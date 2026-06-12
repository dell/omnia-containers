.. _howto-cluster-dns-configuration:

Configuring Cluster DNS
=======================

This section describes how to enable and configure Cluster DNS for dynamic hostname resolution in Omnia.

Prerequisites
-------------

Before enabling Cluster DNS, ensure the following:

- Omnia is deployed on the OIM node with OpenCHAMI services running
- ``/opt/omnia/input/project_default/provision_config.yml`` exists and is validated
- The OIM node is accessible on the admin network

Enabling Cluster DNS
--------------------

To enable Cluster DNS for dynamic hostname resolution:

1. Edit the ``/opt/omnia/input/project_default/provision_config.yml`` file on the OIM node::

    vi /opt/omnia/input/project_default/provision_config.yml

2. Set the ``dns_enabled`` parameter to ``true``::

    dns_enabled: true

   .. note::
      The default value is ``false``, which preserves the legacy ``/etc/hosts`` behavior.

3. Deploy or redeploy OpenCHAMI with coresmd (if not already deployed)::

    ansible-playbook prepare_oim/prepare_oim.yml

4. Run the provisioning playbook to provision nodes with cloud-init containing ``/etc/resolv.conf``::

    ansible-playbook provision/provision.yml

5. Reprovision (reboot) all compute nodes to apply the new cloud-init configuration.

   .. important::
      Nodes must be reprovisioned (rebooted) after setting ``dns_enabled: true`` for the change to take effect. Existing nodes retain their previous configuration until reprovisioned.

Disabling Cluster DNS (Reverting to /etc/hosts)
------------------------------------------------

To revert to the legacy ``/etc/hosts`` behavior:

1. Edit ``input/provision_config.yml`` and set ``dns_enabled`` to ``false``::

    dns_enabled: false

2. Re-run the provisioning playbook to regenerate cloud-init configs::

    ansible-playbook provision/provision.yml

3. Reprovision (reboot) all compute nodes to apply the new cloud-init configuration.

4. Verify that ``/etc/hosts`` contains all peer entries on compute nodes.

5. Verify that OIM and Slurm node ``/etc/hosts`` are updated by the playbook.

.. note::
   No coresmd or OpenCHAMI changes are needed for rollback. coresmd continues running but compute nodes no longer query it.


Verification
------------

After enabling Cluster DNS, verify the configuration using the following commands.

Verify Compute Node Resolver Configuration
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

On any compute node, verify that ``/etc/resolv.conf`` is configured correctly::

    cat /etc/resolv.conf

Expected output::

    search <domain_name>
    nameserver <admin_nic_ip>
    options timeout:1 attempts:2

Replace ``<domain_name>`` with your cluster domain (e.g., ``hpc.cluster``) and ``<admin_nic_ip>`` with the OIM admin IP.

Verify No Peer Entries in /etc/hosts
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

On any compute node, verify that ``/etc/hosts`` contains only localhost entries::

    cat /etc/hosts

Expected output should show only localhost entries (e.g., ``127.0.0.1 localhost.localdomain localhost``). No peer node entries should be present.

Verify Forward DNS Resolution
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

On any compute node, test forward resolution for a cluster hostname::

    getent hosts <hostname>

Replace ``<hostname>`` with a cluster node hostname (e.g., ``nid001.hpc.cluster``).

Expected output::

    <admin_ip> <hostname>.<domain>

Example::

    172.16.0.1 nid001.hpc.cluster

Query coresmd Directly
~~~~~~~~~~~~~~~~~~~~~~

From the OIM node or any node with network access to the OIM, query coresmd directly using ``dig``::

    dig <hostname>.<domain> @<admin_nic_ip>

Replace ``<hostname>`` with a cluster node hostname, ``<domain>`` with your cluster domain, and ``<admin_nic_ip>`` with the OIM admin IP.

Expected output should show an A record with the admin IP address.

Example::

    dig nid001.hpc.cluster @172.16.107.254

    ; <<>> DiG <<>> nid001.hpc.cluster @172.16.107.254
    ;; global options: +cmd
    ;; Got answer:
    ;; ->>HEADER<<- opcode: QUERY, status: NOERROR, id: 12345
    ;; flags: qr aa rd ra; QUERY: 1, ANSWER: 1, AUTHORITY: 0, ADDITIONAL: 1

    ;; QUESTION SECTION:
    ;nid001.hpc.cluster.         IN      A

    ;; ANSWER SECTION:
    nid001.hpc.cluster.  30      IN      A       172.16.0.1

Verify Kubernetes CoreDNS Patching (if K8s is Deployed)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If Kubernetes is deployed, verify that the K8s CoreDNS ConfigMap contains the forward zone::

    kubectl -n kube-system get configmap coredns -o yaml

Look for a block similar to::

    hpc.cluster:53 {
        errors
        cache 30
        forward . 172.16.107.254
    }

Replace ``hpc.cluster`` with your cluster domain and ``172.16.107.254`` with your OIM admin IP.

Verify K8s Pod Resolution (if K8s is Deployed)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

From a Kubernetes pod, test resolution of a compute node hostname::

    kubectl exec -it <pod> -- getent hosts <hostname>.<domain>

Replace ``<pod>`` with a pod name and ``<hostname>.<domain>`` with a cluster node hostname.

Expected output::

    <admin_ip> <hostname>.<domain>

Verify Slurm Functionality
~~~~~~~~~~~~~~~~~~~~~~~~~~~

1. Verify that Slurm starts successfully::

    sinfo

   Expected output should show all nodes in the expected state (e.g., ``IDLE`` or ``ALLOCATED``).

2. Run a test Slurm job::

    srun -N <N> hostname

   Replace ``<N>`` with the number of nodes to test.

   Expected output should complete without DNS errors.

Verify MPI Functionality
~~~~~~~~~~~~~~~~~~~~~~~

Run a test MPI job::

    mpirun -np 4 -host <host1>,<host2> hostname

Replace ``<host1>`` and ``<host2>`` with cluster node hostnames.

Expected output should complete without DNS timeouts.

Verify New Node Auto-Resolution
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

1. Add a new node to SMD via the provision playbook::

    ansible-playbook provision/provision.yml

2. Wait up to 30 seconds for coresmd to refresh its cache.

3. From any compute node, test resolution of the new node::

    getent hosts <new_hostname>

Expected output should show the new node's IP address without requiring any playbook re-run.

Troubleshooting
--------------

Custom Hostnames Not Resolving
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Symptom**: Custom hostnames from the PXE mapping don't resolve.

**Possible Causes**:

1. Custom hostname not in ``/etc/hosts``
2. PXE mapping file not processed correctly

**Resolution Steps**:

1. Check ``/etc/hosts``::

    grep <hostname> /etc/hosts

2. Re-run provisioning to repopulate ``/etc/hosts``::

    ansible-playbook provision.yml

Mixed-State Cluster
~~~~~~~~~~~~~~~~~~

**Symptom**: Some nodes resolve via DNS while others use ``/etc/hosts``.

**Possible Causes**:

1. Only some nodes were reprovisioned after changing ``dns_enabled``
2. Inconsistent cloud-init configurations

**Resolution Steps**:

1. Check ``/etc/resolv.conf`` on affected nodes to determine which mode they are using
2. Reprovision all nodes to ensure consistent configuration::

    ansible-playbook provision/provision.yml

3. Reboot all nodes to apply the new cloud-init configuration

Best Practices
--------------

**Plan DNS Mode Before Deployment**
- Decide on DNS mode (``/etc/hosts`` vs DNS) before initial cluster deployment
- Changing mode after deployment requires reprovisioning all nodes

**Monitor coresmd Health**
- Monitor coresmd container status and logs
- Use Prometheus metrics (port 9153) to track DNS query performance
- Set up alerts for coresmd downtime

**Configure Reliable Upstream DNS**
- Configure at least two reliable upstream DNS servers in ``admin_network.dns``
- Test upstream DNS connectivity before enabling Cluster DNS
- Monitor upstream DNS server availability

**Test Resolution Before Production**
- Verify DNS resolution from compute nodes before running production workloads
- Test Slurm and MPI job execution with DNS enabled
- Verify K8s pod resolution if Kubernetes is deployed

**Document Domain Configuration**
- Record the cluster domain name (``domain_name``) for reference
- Document the hostname pattern (``cluster_shortname`` and ``cluster_nidlength``)
- Share this information with cluster users for hostname reference

**Plan for High Availability**
- In the current implementation, the OIM node is a single point of failure for DNS
- Plan for OIM HA deployment when high availability is required
- Monitor OIM node health and have a recovery plan

**Use Short-Name Resolution**
- Leverage the ``search <domain_name>`` directive in ``/etc/resolv.conf``
- Users can use short hostnames (e.g., ``nid001``) instead of FQDNs (e.g., ``nid001.hpc.cluster``)
- Simplifies Slurm and MPI job configuration

**Validate After Node Changes**
- After adding or removing nodes, verify DNS resolution within 30 seconds
- Check SMD inventory to confirm node registration
- Use ``dig`` or ``getent hosts`` to test resolution

**Limitations Considerations**
- Be aware that reverse DNS (PTR records) are not supported
- Plan for workarounds if applications require reverse DNS
- Note that InfiniBand-specific DNS is not provided
- Ensure MPI workloads use UCX auto-detection for IB transport

