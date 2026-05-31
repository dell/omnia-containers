.. _howto-cluster-dns-configuration:

Configuring Cluster DNS
=======================

This section describes how to enable and configure Cluster DNS for dynamic hostname resolution in Omnia.

Prerequisites
-------------

Before enabling Cluster DNS, ensure the following:

- Omnia is deployed on the OIM node with OpenCHAMI services running
- ``input/network_spec.yml`` is configured with valid ``admin_network.dns`` entries for upstream DNS forwarding
- ``input/provision_config.yml`` exists and is validated
- The OIM node is accessible on the admin network
- SMD (State Manager Daemon) is running and accessible from the OIM node

Enabling Cluster DNS
--------------------

To enable Cluster DNS for dynamic hostname resolution:

1. Edit the ``input/provision_config.yml`` file on the OIM node::

    vi input/provision_config.yml

2. Set the ``dns_enabled`` parameter to ``true``::

    dns_enabled: true

   .. note::
      The default value is ``false``, which preserves the legacy ``/etc/hosts`` behavior.

3. Validate the configuration using the input validator::

    python3 common/library/module_utils/input_validation/input_validator.py -i input/

   Ensure no validation errors are reported.

4. Deploy or redeploy OpenCHAMI with coresmd (if not already deployed)::

    ansible-playbook prepare_oim/prepare_oim.yml

5. Run the discovery playbook to populate SMD with node inventory::

    ansible-playbook discovery/discovery.yml

6. Run the provisioning playbook to provision nodes with cloud-init containing ``/etc/resolv.conf``::

    ansible-playbook provision/provision.yml

7. Reprovision (reboot) all compute nodes to apply the new cloud-init configuration.

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

Configuration Parameters
-------------------------

User-Facing Configuration
~~~~~~~~~~~~~~~~~~~~~~~~~~

**dns_enabled** (boolean, default: ``false``)
- Location: ``input/provision_config.yml``
- When ``true``, nodes use coresmd for hostname resolution instead of ``/etc/hosts``
- DNS records are auto-generated from SMD inventory
- The cluster domain is read from OIM metadata (``domain_name``)

Existing Parameters Used
~~~~~~~~~~~~~~~~~~~~~~~~~

The following existing parameters are used by Cluster DNS:

**admin_network.dns**
- Location: ``input/network_spec.yml``
- DNS forwarders for coresmd and K8s CoreDNS external resolution
- Used to forward non-cluster DNS queries (e.g., ``google.com``)

**admin_network.primary_oim_admin_ip**
- Location: ``input/network_spec.yml``
- Nameserver IP written to compute node ``/etc/resolv.conf``
- The IP address that coresmd listens on for DNS queries

**admin_network.additional_subnets**
- Location: ``input/network_spec.yml``
- Triggers multi-subnet CoreDHCP config format (if defined)
- Does not directly affect DNS configuration

**domain_name**
- Location: OIM metadata (set during ``prepare_oim.yml``)
- Cluster domain used as DNS zone and ``search`` domain in resolv.conf
- Example: ``hpc.cluster``

**cluster_shortname**
- Location: OpenCHAMI config
- Hostname pattern prefix (e.g., ``nid``)
- Used to generate DNS record names

**cluster_nidlength**
- Location: OpenCHAMI config
- Zero-padded node ID length (e.g., ``3`` produces ``nid001``)
- Used to generate DNS record names

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

1. Add a new node to SMD via the discovery playbook::

    ansible-playbook discovery/discovery.yml

2. Wait up to 30 seconds for coresmd to refresh its cache.

3. From any compute node, test resolution of the new node::

    getent hosts <new_hostname>

Expected output should show the new node's IP address without requiring any playbook re-run.

Troubleshooting
--------------

DNS Queries Failing
~~~~~~~~~~~~~~~~~~~

**Symptom**: ``getent hosts <hostname>`` returns no results or times out.

**Possible Causes**:

1. coresmd container is not running
2. OIM node is unreachable
3. ``dns_enabled`` is not set to ``true`` on the compute node
4. Node is not registered in SMD

**Resolution Steps**:

1. Check coresmd status on the OIM node::

    podman ps | grep coresmd

   If not running, start it::

    podman start coresmd

2. Verify OIM network connectivity from the compute node::

    ping <admin_nic_ip>

3. Verify that ``/etc/resolv.conf`` is configured correctly on the compute node::

    cat /etc/resolv.conf

4. Verify that the node is registered in SMD::

    curl -k https://<oim_ip>:8443/v1/nodes | jq '.[] | select(.hostname=="<hostname>")'

5. Check coresmd logs for errors::

    podman logs coresmd

NXDOMAIN Errors
~~~~~~~~~~~~~~~

**Symptom**: DNS queries return ``NXDOMAIN`` (non-existent domain).

**Possible Causes**:

1. Node is not registered in SMD
2. Domain name mismatch
3. Incorrect hostname format

**Resolution Steps**:

1. Verify SMD inventory::

    curl -k https://<oim_ip>:8443/v1/nodes

2. Verify the domain name in OIM metadata matches the query domain::

    cat /etc/resolv.conf  # on compute node
    # Check the 'search' domain

3. Verify the hostname format follows the pattern ``{cluster_shortname}{zero_padded_id}.{cluster_domain}``

4. Check coresmd Corefile configuration::

    podman exec coresmd cat /etc/coredns/Corefile

Slow DNS Resolution
~~~~~~~~~~~~~~~~~~~

**Symptom**: DNS queries take more than 1 second to respond.

**Possible Causes**:

1. coresmd cache miss (first lookup)
2. SMD API is slow or unreachable
3. Network latency between compute node and OIM

**Resolution Steps**:

1. Check if this is a cache miss by running the query twice (second should be fast)
2. Check SMD connectivity from coresmd::

    podman exec coresmd curl -k https://<smd_url>:8443/v1/nodes

3. Check network latency::

    ping <admin_nic_ip>

4. Monitor coresmd cache metrics::

    curl http://<admin_nic_ip>:9153/metrics | grep coredns_cache

K8s Pods Cannot Resolve Compute Hostnames
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Symptom**: ``kubectl exec <pod> -- getent hosts <hostname>`` fails.

**Possible Causes**:

1. K8s CoreDNS ConfigMap was not patched
2. Forward zone is missing or incorrect
3. Pod is using host network and lacks resolver configuration

**Resolution Steps**:

1. Verify K8s CoreDNS ConfigMap contains the forward zone::

    kubectl -n kube-system get configmap coredns -o yaml

2. If missing, manually patch the ConfigMap or reprovision the first control plane node
3. Check if the pod is using host network::

    kubectl get pod <pod> -o jsonpath='{.spec.hostNetwork}'

   If ``true``, the pod uses the node's resolver configuration.

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

Migration from /etc/hosts to DNS
---------------------------------

To migrate an existing cluster from ``/etc/hosts`` to DNS:

1. **Backup Current Configuration**
   - Document current ``/etc/hosts`` entries on a sample node
   - Record any manual hostname entries that may need special handling

2. **Enable DNS Mode**
   - Set ``dns_enabled: true`` in ``input/provision_config.yml``
   - Validate the configuration

3. **Reprovision Nodes**
   - Run ``ansible-playbook provision/provision.yml``
   - Reprovision all nodes (reboot into cloud-init)
   - Monitor node boot and cloud-init execution

4. **Verify DNS Resolution**
   - Test resolution from each node type (compute, Slurm controller, login, K8s)
   - Verify Slurm functionality with ``sinfo`` and test jobs
   - Verify MPI job execution
   - Verify K8s pod resolution if applicable

5. **Clean Up Stale /etc/hosts Entries**
   - After verification, ``/etc/hosts`` entries are no longer needed
   - The playbook skips ``/etc/hosts`` updates when DNS is enabled
   - Manual cleanup is not required but can be performed if desired

6. **Update Documentation**
   - Update cluster documentation to reflect DNS mode
   - Inform users about the change in hostname resolution method
   - Provide troubleshooting guidance for DNS-related issues

Rollback from DNS to /etc/hosts
-------------------------------

To rollback from DNS to ``/etc/hosts``:

1. **Disable DNS Mode**
   - Set ``dns_enabled: false`` in ``input/provision_config.yml``
   - Validate the configuration

2. **Reprovision Nodes**
   - Run ``ansible-playbook provision/provision.yml``
   - Reprovision all nodes (reboot into cloud-init)
   - Monitor node boot and cloud-init execution

3. **Verify /etc/hosts Entries**
   - Verify that ``/etc/hosts`` contains all peer entries on compute nodes
   - Verify that OIM and Slurm node ``/etc/hosts`` are updated by the playbook

4. **Verify Functionality**
   - Test resolution from each node type using ``getent hosts``
   - Verify Slurm functionality
   - Verify MPI job execution
   - Verify K8s functionality (pods use node's ``/etc/hosts``)

5. **Update Documentation**
   - Update cluster documentation to reflect ``/etc/hosts`` mode
   - Inform users about the change in hostname resolution method

.. note::
   coresmd continues running after rollback but compute nodes no longer query it. No coresmd or OpenCHAMI changes are needed for rollback.
