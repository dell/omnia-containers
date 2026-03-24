Limitations
===========

- Omnia supports only diskless provisioning of servers.
- Omnia supports nodes discovered only through the mapping file. 
- Dell Technologies provides support only for the Dell-developed modules of Omnia. Third-party tools deployed by Omnia are not covered by Dell support.
- Containerized benchmark jobs are not supported on Slurm clusters.
- All iDRACs must use the same username and password.
- As per the RedHat documentation, `Configuring InfiniBand and RDMA networks <https://docs.redhat.com/en/documentation/red_hat_enterprise_linux/10/html/configuring_and_managing_networking/configuring-infiniband-and-rdma-networks>`_, on RHEL 8 and later, Mellanox InfiniBand adapters starting from ConnectX-4 and newer use Enhanced IPoIB mode by default, which supports datagram mode only. Connected mode is not supported on these devices.
- The ``local_repo.yml`` playbook passes even when an incorrect GPG key is provided during repository configuration. GPG key validation is currently not enforced during Pulp remote creation. Although ``localrepo`` includes support for GPG keys, this functionality is not yet enabled in Pulp. This issue has been raised with the Pulp team for tracking: `https://github.com/pulp/pulp_rpm/issues/4241 <https://github.com/pulp/pulp_rpm/issues/4241>`_.
- BuildStreaM does not support customization of catalog ``catalog_rhel.json`` or additional package installations.
- BuildStreaM does not support retry of failed pipeline jobs.
