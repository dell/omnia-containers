.. _concept-cluster-dns-overview:

Cluster DNS Overview
====================

Cluster DNS provides dynamic hostname resolution for Omnia-managed cluster nodes using CoreDNS-based DNS services instead of static ``/etc/hosts`` file management. This feature eliminates O(N) SSH-based hosts file updates during provisioning and provides automatic hostname resolution for newly inventoried nodes without requiring playbook re-runs.

What is Cluster DNS
-------------------

Cluster DNS is a DNS-based hostname resolution system that leverages **coresmd**, the CoreDNS instance already deployed as part of the OpenCHAMI stack on the Omnia Infrastructure Manager (OIM) node. coresmd queries the OpenCHAMI State Manager Daemon (SMD) inventory every 30 seconds and automatically generates forward A records for all inventoried nodes.

When enabled, compute nodes resolve hostnames via DNS queries to the OIM instead of reading from local ``/etc/hosts`` files. This provides a single source of truth for hostname-to-IP mappings and eliminates the need for manual hosts file synchronization across the cluster.

DNS Ownership Boundaries
-------------------------

Omnia Cluster-Scoped DNS
~~~~~~~~~~~~~~~~~~~~~~~~~

Omnia manages and is responsible for the following DNS aspects:

**Cluster Node Resolution**
- Forward (A record) hostname resolution for all compute, Slurm controller, login, and Kubernetes nodes
- Dynamic DNS record generation from OpenCHAMI SMD inventory via coresmd
- DNS zone serving for the cluster domain (e.g., ``hpc.cluster``)
- Cloud-init-based ``/etc/resolv.conf`` configuration on compute nodes
- Kubernetes CoreDNS ConfigMap patching to forward cluster domain queries to OIM coresmd

**Admin Network DNS Forwarding**
- coresmd forwards non-cluster DNS queries (e.g., ``google.com``, ``internal.company.com``) to upstream DNS servers configured in ``admin_network.dns`` from ``input/network_spec.yml``
- This enables cluster nodes to resolve external and enterprise DNS names through the OIM

Enterprise DNS (Site Administrator Responsibility)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The site network administrator retains responsibility for:

**Enterprise DNS Infrastructure**
- Upstream DNS server configuration and maintenance (specified in ``admin_network.dns``)
- Enterprise-wide DNS zones and records (e.g., ``company.com``, internal services)
- DNS security policies (DNSSEC, filtering, etc.)
- External DNS resolution for non-cluster resources

**Out-of-Band (OOB) Network DNS**
- BMC/iDRAC hostname resolution on the OOB management network
- DNS configuration for switch management interfaces
- Any DNS services running on networks outside the Omnia-managed admin network

**InfiniBand Fabric DNS**
- InfiniBand-specific hostname records (e.g., ``nid001-ib.cluster.domain``)
- Subnet Manager (SM) hostname resolution
- Fabric management tool DNS integration

.. note::
   Omnia does not manage InfiniBand fabric DNS. MPI over InfiniBand uses UCX auto-detection for transport selection and does not rely on DNS for IB fabric discovery.

DNS Architecture
----------------

Legacy Behavior: /etc/hosts (dns_enabled: false)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

By default (``dns_enabled: false``), Omnia uses static ``/etc/hosts`` file management:

**At Boot (Cloud-Init)**
- Cloud-init renders the ``ip_name_map`` dictionary (hostname-to-IP mapping for all cluster nodes) into ``/etc/hosts`` as append entries
- The mapping is a snapshot at provisioning time and does not update if nodes are added or removed later

**OIM /etc/hosts Update**
- During ``provision.yml`` execution, the ``update_hosts.yml`` task iterates through every entry in the PXE mapping file
- Removes stale entries and adds fresh ``<ADMIN_IP> <HOSTNAME>`` lines
- This is an O(N) shell loop that takes several minutes for large clusters

**Slurm Node /etc/hosts Update**
- The ``update_hosts_munge.yml`` task SSHes into each reachable Slurm node
- Removes stale entries and adds fresh ``<IP> <hostname>`` entries for all current nodes
- This is an O(N x M) operation (N nodes visited, M lineinfile operations per node)

**Limitations**
- New nodes added after boot are not resolvable until the node is reprovisioned or the playbook re-pushes ``/etc/hosts``
- Removed nodes leave stale entries until the next playbook run
- Inconsistent ``/etc/hosts`` across the cluster due to race conditions or unreachable nodes

New Behavior: CoreDNS via coresmd (dns_enabled: true)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

When ``dns_enabled: true``, Omnia uses dynamic DNS resolution:

**At Boot (Cloud-Init)**
- Cloud-init writes ``/etc/resolv.conf`` with the OIM IP as the nameserver
- Does not append any peer entries to ``/etc/hosts``
- The ``search <domain_name>`` directive enables short-name resolution

**OIM /etc/hosts Update --- Skipped**
- The ``update_hosts.yml`` task detects ``dns_enabled: true`` and skips the entire ``/etc/hosts`` update block
- Only the localhost entry is ensured

**Slurm Node /etc/hosts Update --- Skipped**
- The ``update_hosts_munge.yml`` task detects ``dns_enabled: true`` and skips the entire SSH-based ``/etc/hosts`` management block
- Munge key distribution and Slurm service restart logic continue to function normally

Hybrid Mode: Custom Hostnames with DNS
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

When ``dns_enabled: true``, Omnia supports a **hybrid mode** that combines DNS-based resolution for NID-based hostnames with static ``/etc/hosts`` entries for custom hostnames defined in the PXE mapping file.

**CoreDNS Hostname Generation**
- CoreDNS generates DNS records automatically from the OpenCHAMI SMD inventory
- Hostnames follow a fixed NID-based pattern: ``{cluster_shortname}{zero_padded_id}.{cluster_domain}``
- Example: With ``cluster_shortname=nid`` and ``cluster_nidlength=3``, Node ID 1 produces ``nid001.hpc.cluster``
- CoreDNS does **not** use custom hostnames defined in the PXE mapping file (e.g., ``headnode``, ``compute1``)

**Custom Hostnames via /etc/hosts**
- Custom hostnames from the PXE mapping file are resolved via ``/etc/hosts``
- ``/etc/hosts`` is always populated from the PXE mapping regardless of the ``dns_enabled`` setting
- This enables sites to use descriptive custom names alongside the NID-based DNS names

**Resolution Order**
The system resolves hostnames in this order (defined by ``/etc/nsswitch.conf``):

1. ``/etc/hosts`` (checked first)
2. DNS / CoreDNS (checked if not found in ``/etc/hosts``)

**Example Resolution Table**

+----------------+------------------------+------------------------------------------+
| Hostname       | Resolution Source      | Example                                  |
+================+========================+==========================================+
| ``nid001.hpc.cluster`` | CoreDNS (coresmd) | FQDN from SMD NID pattern               |
+----------------+------------------------+------------------------------------------+
| ``nid001``     | CoreDNS (via ``search`` domain in resolv.conf) | Short name appended with cluster domain |
+----------------+------------------------+------------------------------------------+
| ``headnode``   | ``/etc/hosts``         | Custom name from PXE mapping             |
+----------------+------------------------+------------------------------------------+
| ``compute1``   | ``/etc/hosts``         | Custom name from PXE mapping             |
+----------------+------------------------+------------------------------------------+

**DNS Resolution Flow**

.. code-block:: text

   Compute Node                    OIM Node
   +----------------+             +------------------+
   | Application    |             | coresmd          |
   | (Slurm/MPI)   |             | (CoreDNS + SMD)  |
   |    |           |             |    |             |
   |    v           |    DNS      |    v             |
   | glibc resolver | ---------->| coresmd plugin   |
   | /etc/resolv.conf|   UDP:53  | queries SMD      |
   |    |           |             | every 30s        |
   |    v           |  A record   |    |             |
   | IP address     | <----------| cached response  |
   +----------------+             +------------------+
                                       |
                                       v (non-cluster queries)
                                  upstream DNS forwarders
                                  (admin_network.dns)

**coresmd Record Generation**
- Every 30 seconds, coresmd queries SMD for the current node inventory
- For each node, it creates a record: ``{cluster_shortname}{zero_padded_id}.{cluster_domain} -> <admin_ip>``
- Example: Node ID 1 with ``cluster_shortname=nid``, ``cluster_nidlength=3``, ``cluster_domain=hpc.cluster`` produces: ``nid001.hpc.cluster -> 172.16.0.1``
- Non-cluster queries are forwarded to upstream DNS servers from ``admin_network.dns``

High Availability Behavior
--------------------------

Current Implementation
~~~~~~~~~~~~~~~~~~~~~

**Single coresmd Instance**
- coresmd runs as a single container on the OIM node
- No VIP failover or load balancing is currently implemented
- If the OIM node or coresmd container is down, DNS queries from compute nodes fail

**Failure Mode**
- DNS queries time out after 1 second (``options timeout:1``), retry once (``options attempts:2``), then fail
- All hostname resolution fails until coresmd is restored
- Slurm jobs cannot start; running MPI jobs that need to resolve new peers will fail
- Already-connected TCP sessions (e.g., active MPI communications) continue until a new resolution is needed

**Mitigation**
- Restart coresmd container on the OIM node
- Future HA enhancement will provide VIP failover (deferred to OIM HA specification)

.. warning::
   In the current implementation, the OIM node is a single point of failure for DNS resolution. For production deployments requiring high availability, ensure the OIM node is deployed with appropriate redundancy and monitoring.

Fabric-Aware Resolution
-----------------------

Ethernet (Admin/PXE Network)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Supported Resolution**
- coresmd returns the admin/PXE IP address for each node from SMD
- This is the IP address used for Slurm hostname resolution and cluster management
- MPI over Ethernet uses this IP for peer discovery

**Record Format**
- Forward A records only: ``nid001.hpc.cluster -> 172.16.0.1``
- No reverse DNS (PTR) records are generated
- No fabric-specific suffixes (e.g., ``-ib``) are supported

InfiniBand Fabric
~~~~~~~~~~~~~~~~~

**Not Supported**
- coresmd does not generate InfiniBand-specific DNS records
- No ``nid001-ib.hpc.cluster`` records are available
- Reverse DNS for IB addresses is not provided

**MPI Behavior**
- MPI implementations typically use UCX auto-detection for InfiniBand transport selection
- UCX discovers IB interfaces directly via the RDMA/Verbs API, not via DNS
- Explicit IB DNS records are rarely required for MPI job execution

**Workaround**
- If your MPI implementation requires IB-specific hostnames, configure them manually in ``/etc/hosts`` on the relevant nodes
- This is a site-specific configuration outside of Omnia's automated management

Interaction with admin_network.dns
----------------------------------

Upstream DNS Forwarding
~~~~~~~~~~~~~~~~~~~~~~~

**Configuration**
- Upstream DNS servers are specified in ``input/network_spec.yml`` under ``admin_network.dns``
- These servers are used by coresmd to forward non-cluster DNS queries

**Query Flow**

.. code-block:: text

   Compute Node              coresmd (OIM)           Upstream DNS
   +-----------+             +-----------+           +-----------+
   | getaddrinfo|             | CoreDNS   |           | Enterprise |
   | (google.com)| ---------->| forward   | ---------->| DNS Server |
   +-----------+   DNS query | plugin    |  forward  +-----------+
                       |           |
                       v           v
                   Response cached and returned to compute node

**Use Cases**
- Cluster nodes need to resolve external services (e.g., package repositories, authentication servers)
- Cluster nodes need to resolve internal enterprise services outside the cluster domain
- Kubernetes pods need to resolve external APIs

**Configuration Example**

.. code-block:: yaml

   Networks:
   - admin_network:
       dns:
         - 8.8.8.8
         - 8.8.4.4

.. note::
   The ``admin_network.dns`` configuration is used by both coresmd and Kubernetes CoreDNS for external resolution.

Interaction with Kubernetes CoreDNS
-----------------------------------

K8s CoreDNS ConfigMap Patching
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**When DNS is Enabled**
- The first Kubernetes control plane node's cloud-init script patches the K8s CoreDNS ConfigMap
- Adds a forward zone block: ``<domain_name>:53 { errors; cache 30; forward . <admin_nic_ip> }``
- The patch is idempotent: if the zone already exists, it is not added again
- After patching, the K8s CoreDNS deployment is restarted via ``kubectl rollout restart``

**Pod Resolution Flow**

.. code-block:: text

   K8s Pod
       |
       v  getaddrinfo("nid001.hpc.cluster")
   K8s CoreDNS (kube-system)
       |
       v  Corefile: hpc.cluster:53 { forward . <OIM_IP> }
   UDP query -> OIM_IP:53
       |
       v
   coresmd -> A record

**Verification**
- After patching, K8s pods can resolve compute node hostnames::

    kubectl exec -it <pod> -- getent hosts nid001.hpc.cluster

**Use Case**
- Enables MPI-over-Kubernetes workloads to resolve Slurm/compute hostnames from within pods
- Allows host-network pods and jobs to resolve compute node hostnames

Operational Expectations
-------------------------

Resolution Latency
~~~~~~~~~~~~~~~~~~

**Cached Queries**
- DNS queries are served from coresmd's in-memory cache (30s TTL)
- Cached lookup latency: < 1 millisecond
- Sub-millisecond response times for cached lookups

**Cache Refresh**
- coresmd queries SMD every 30 seconds to refresh its inventory cache
- New nodes added to SMD are resolvable within 30 seconds of registration
- Removed nodes stop resolving after the next cache refresh (up to 30 seconds)

**Uncached Queries**
- First lookup for a new node requires coresmd to query SMD
- Latency depends on SMD API response time (typically < 100ms)

Node Lifecycle Behavior
~~~~~~~~~~~~~~~~~~~~~~~

**Node Add**
1. Register node in SMD via discovery playbook
2. coresmd picks it up within 30s (next cache refresh)
3. slurmctld can resolve it via DNS
4. Node transitions to ``IDLE`` state
5. No playbook re-run needed for DNS resolution

**Node Remove**
1. Remove node from SMD
2. coresmd drops the record within 30s (next cache refresh)
3. slurmctld marks node as ``DOWN``
4. No ``/etc/hosts`` cleanup needed

**Node Reprovision**
- Changing ``dns_enabled`` requires node reprovisioning (reboot into cloud-init)
- Cloud-init writes the appropriate resolver configuration (``/etc/resolv.conf`` or ``/etc/hosts``)
- This is a deployment-time decision, not expected to change frequently

Common Failure Scenarios
------------------------

coresmd Unreachable
~~~~~~~~~~~~~~~~~~~

**Scenario**
- OIM node is down or coresmd container is stopped

**Behavior**
- DNS queries from compute nodes time out after 1 second (``options timeout:1``)
- Queries retry once (``options attempts:2``), then fail
- All hostname resolution fails until coresmd is restored

**Impact**
- Slurm jobs cannot start
- Running MPI jobs that need to resolve new peers will fail
- Already-connected TCP sessions continue until a new resolution is needed

**Mitigation**
- Restart coresmd container: ``podman restart coresmd``
- Monitor coresmd health via Prometheus metrics on port 9153
- Future HA enhancement will provide VIP failover

SMD Unreachable from coresmd
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Scenario**
- SMD API is down but coresmd is running

**Behavior**
- coresmd continues serving records from its last cached SMD query (up to 30s stale)
- New nodes added during the outage are not resolvable until SMD recovers and coresmd refreshes its cache

**Impact**
- Existing nodes continue to resolve (stale data)
- New nodes cannot be resolved until SMD recovery

**Mitigation**
- Restart SMD service
- Monitor SMD health and connectivity

Node Not in SMD
~~~~~~~~~~~~~~~

**Scenario**
- A node is provisioned but not registered in SMD

**Behavior**
- coresmd has no record for the node
- DNS queries for its hostname return ``NXDOMAIN``
- Slurm marks the node as ``DOWN``

**Mitigation**
- Ensure discovery playbook has been run to register the node in SMD
- Verify SMD inventory: ``curl -k https://<oim_ip>:8443/v1/nodes``

Domain Misconfiguration
~~~~~~~~~~~~~~~~~~~~~~

**Scenario**
- ``domain_name`` in OIM metadata does not match the zone configured in coresmd Corefile

**Behavior**
- Compute nodes search for ``<hostname>.<wrong_domain>`` which coresmd does not serve
- Resolution fails with ``NXDOMAIN``

**Mitigation**
- ``domain_name`` is set once during ``prepare_oim.yml`` and used consistently across all templates
- User does not configure the domain separately
- Verify OIM metadata if resolution fails

Upstream DNS Failure
~~~~~~~~~~~~~~~~~~~~

**Scenario**
- All upstream DNS servers specified in ``admin_network.dns`` are unreachable

**Behavior**
- Non-cluster DNS queries (e.g., ``google.com``) fail
- Cluster internal resolution (e.g., ``nid001.hpc.cluster``) continues to work

**Impact**
- Cluster nodes cannot resolve external services
- Package repositories, authentication servers, and external APIs may be unreachable

**Mitigation**
- Ensure at least two reliable upstream DNS servers are configured
- Monitor upstream DNS server availability
- Use local caching DNS servers if external connectivity is unreliable

For a complete list of Cluster DNS limitations and constraints, see :doc:`/limitations`.

Use Cases
---------

**Large-Scale Clusters (100+ Nodes)**
- Eliminates O(N x M) SSH operations for ``/etc/hosts`` management
- Reduces provisioning time significantly
- Provides consistent hostname resolution across the cluster

**Dynamic Node Environments**
- New nodes are automatically resolvable within 30 seconds
- No playbook re-run needed for DNS updates
- Ideal for environments with frequent node additions/removals

**MPI-Over-Kubernetes Workloads**
- K8s pods can resolve compute node hostnames via CoreDNS forwarding
- Enables hybrid Slurm/Kubernetes deployments
- Supports containerized MPI workloads

**Sites with Strict Network Policies**
- Eliminates SSH access requirement for ``/etc/hosts`` management
- Reduces attack surface by removing SSH-based configuration pushes
- DNS queries use UDP/TCP port 53 only

Verifying Hostname Resolution
------------------------------

Query DNS Only (Bypasses /etc/hosts)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To verify CoreDNS resolution directly without checking ``/etc/hosts``::

    dig <hostname>.<domain> @<admin_nic_ip>

Replace ``<hostname>`` with a cluster node hostname, ``<domain>`` with your cluster domain, and ``<admin_nic_ip>`` with the OIM admin IP.

Expected output includes an ``ANSWER SECTION`` with the node's IP address::

    ;; ANSWER SECTION:
    nid001.hpc.cluster.     60      IN      A       172.17.0.248

Query /etc/hosts Only
~~~~~~~~~~~~~~~~~~~~~

To verify custom hostname resolution via ``/etc/hosts``::

    getent ahosts <custom_hostname>

Replace ``<custom_hostname>`` with a custom hostname from the PXE mapping (e.g., ``headnode``).

Expected output::

    172.17.0.248    STREAM headnode
    172.17.0.248    DGRAM
    172.17.0.248    RAW

Query Using Full System Resolution Order
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To verify resolution using the system's configured order (``/etc/hosts`` first, then DNS)::

    getent ahosts <hostname>.<domain>

This follows the system's configured resolution order. If the name is in ``/etc/hosts``, it returns that entry. Otherwise, it queries DNS.

resolv.conf Configuration
--------------------------

When ``dns_enabled: true``, Omnia configures ``/etc/resolv.conf`` on both the **OIM host** and **omnia_core** to use CoreDNS as the primary nameserver::

    search <domain_name> <existing-search-domains>
    nameserver <cluster_boot_ip>
    nameserver <existing-nameservers>

- **``search <domain_name>``** -- Allows short hostnames (e.g., ``nid001``) to resolve as FQDNs (``nid001.hpc.cluster``)
- **``nameserver <cluster_boot_ip>``** -- CoreDNS listening on the cluster boot IP
- Existing nameservers are preserved as fallback for external DNS queries

.. note::
   The resolv.conf is protected with the immutable attribute (``chattr +i``) on the OIM host to prevent NetworkManager from overwriting it.

Architecture Summary
-------------------

.. code-block:: text

                    +------------------+
                    |   omnia_core     |
                    | (Ansible control)|
                    |                  |
                    | resolv.conf:     |
                    |  nameserver      |
                    |  172.17.0.254    |
                    | /etc/hosts:      |
                    |  custom names    |
                    +--------+---------+
                             |
                    +--------v---------+
                    |   OIM (testbed)  |
                    |                  |
                    | resolv.conf:     |
                    |  nameserver      |
                    |  172.17.0.254    |
                    | /etc/hosts:      |
                    |  custom names    |
                    +--------+---------+
                             |
              +--------------+--------------+
              |                             |
     +--------v---------+         +--------v---------+
     |    CoreDNS       |         |      SMD         |
     |  (coresmd)       +-------->+  (Node registry) |
     |  172.17.0.254:53 |         |                  |
     +------------------+         +------------------+
              |
     Resolves: nid001.hpc.cluster
               nid002.hpc.cluster
               nid003.hpc.cluster
