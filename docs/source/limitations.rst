Limitations
===========

- Omnia supports only diskless provisioning of servers.
- Omnia supports nodes discovered only through the mapping file. 
- Dell Technologies provides support only for the Dell-developed modules of Omnia. Third-party tools deployed by Omnia are not covered by Dell support.
- In a single-node cluster, the login node and Slurm functionalities are not applicable.
- Containerized benchmark jobs are not supported on Slurm clusters.
- All iDRACs must use the same username and password.
- Omnia playbooks will fail if the OIM is unable to access online resources or the Internet.
- LDMS Slurm sampler metrics are not supported in the current telemetry deployment.