# Orchestrator Issues

Issues related to the orchestrator domain: Slurm job scheduling, Kubernetes services, networking (InfiniBand, DNS), storage configuration, authentication (LDAP), and node provisioning.

## Provisioning Issues

???+ note "Symptom"

    - Nodes fail to PXE boot
    - Nodes boot but don't complete cloud-init
    - Nodes get stuck in provisioning loop
    - IP address conflicts on cluster

??? note "Cause"

    - Incorrect PXE mapping file entries
    - DHCP server not responding
    - Network configuration errors
    - Cloud-init script failures
    - NFS mount issues

??? note "Resolution"

    1. Verify PXE mapping file:

        ```bash title="Run on: OIM host"
        cat /opt/omnia/input/project_default/pxe_mapping_file.csv
        ```

    2. Check DHCP logs:

        ```bash title="Run on: OIM host"
        podman logs coresmd-coredhcp
        ```

    3. Verify network configuration:

        ```bash title="Run on: OIM host"
        cat /opt/omnia/input/project_default/network_spec.yml
        ```

    4. Check cloud-init logs on node:

        ```bash title="Run on: Provisioned node"
        journalctl -u cloud-init
        ```

## Slurm Issues

???+ note "Symptom"

    - Slurmctld fails to start
    - Nodes show as DOWN in `sinfo`
    - Jobs fail to submit or start
    - GPU scheduling not working

??? note "Cause"

    - Incorrect Slurm configuration
    - Munge authentication failure
    - Network connectivity between nodes
    - Missing or incorrect GRES configuration

??? note "Resolution"

    1. Check Slurm controller status:

        ```bash title="Run on: Slurm control node"
        systemctl status slurmctld
        ```

    2. Verify node status:

        ```bash title="Run on: Slurm control node"
        sinfo -Nel
        ```

    3. Check Slurm logs:

        ```bash title="Run on: Slurm control node"
        journalctl -u slurmctld -n 100
        ```

    4. Verify Munge is running:

        ```bash title="Run on: All Slurm nodes"
        systemctl status munge
        ```

## Kubernetes Issues

???+ note "Symptom"

    - Kubernetes pods fail to start
    - Nodes show as NotReady
    - Persistent volume claims fail
    - PowerScale CSI driver not working

??? note "Cause"

    - Incorrect Kubernetes configuration
    - Network plugin (CNI) issues
    - Storage class not configured
    - Resource constraints

??? note "Resolution"

    1. Check cluster status:

        ```bash title="Run on: Kubernetes control plane"
        kubectl get nodes
        ```

    2. Check pod status:

        ```bash title="Run on: Kubernetes control plane"
        kubectl get pods -A
        ```

    3. Check pod logs:

        ```bash title="Run on: Kubernetes control plane"
        kubectl logs <pod-name> -n <namespace>
        ```

    4. Verify storage classes:

        ```bash title="Run on: Kubernetes control plane"
        kubectl get storageclass
        ```

## Networking Issues

???+ note "Symptom"

    - InfiniBand fabric not detected
    - Cluster DNS not resolving
    - Network connectivity between nodes
    - Multi-subnet DHCP not working

??? note "Cause"

    - Incorrect InfiniBand configuration
    - DNS server not running
    - Firewall blocking traffic
    - Incorrect network CIDRs

??? note "Resolution"

    1. Check InfiniBand status:

        ```bash title="Run on: Node with InfiniBand"
        ibstat
        ```

    2. Check DNS resolution:

        ```bash title="Run on: Any node"
        nslookup <hostname>
        ```

    3. Check firewall rules:

        ```bash title="Run on: OIM host"
        firewall-cmd --list-all
        ```

    4. Verify network configuration:

        ```bash title="Run on: OIM host"
        cat /opt/omnia/input/project_default/network_spec.yml
        ```

## Authentication Issues

???+ note "Symptom"

    - LDAP authentication fails
    - Users cannot log in
    - OpenLDAP service not running
    - Kerberos errors

??? note "Cause"

    - Incorrect LDAP configuration
    - OpenLDAP service down
    - Network connectivity to LDAP server
    - Invalid credentials

??? note "Resolution"

    1. Check OpenLDAP status:

        ```bash title="Run on: OIM host"
        systemctl status slapd
        ```

        Or in container:

        ```bash title="Run on: OIM host"
        podman ps | grep ldap
        ```

    2. Test LDAP connectivity:

        ```bash title="Run on: OIM host"
        ldapsearch -x -H ldap://localhost -b dc=omnia,dc=local
        ```

    3. Check LDAP configuration:

        ```bash title="Run on: OIM host"
        cat /opt/omnia/input/project_default/security_config.yml
        ```

## Storage Issues

???+ note "Symptom"

    - NFS mounts fail
    - PowerScale not accessible
    - Storage quotas exceeded
    - Slow I/O performance

??? note "Cause"

    - NFS server not running
    - Incorrect mount points
    - Network connectivity to storage
    - Insufficient disk space

??? note "Resolution"

    1. Check NFS service:

        ```bash title="Run on: OIM host"
        systemctl status nfs-server
        ```

    2. Verify NFS exports:

        ```bash title="Run on: OIM host"
        exportfs -v
        ```

    3. Check mount status:

        ```bash title="Run on: Mounted node"
        df -h
        ```

    4. Check storage configuration:

        ```bash title="Run on: OIM host"
        cat /opt/omnia/input/project_default/storage_config.yml
        ```

## Related Topics

- [Configure PXE Boot](../HowTo/orchestrator/configure_pxe_boot.md)
- [Deploy Slurm](../HowTo/orchestrator/deploy_slurm.md)
- [Deploy Kubernetes](../HowTo/orchestrator/deploy_kubernetes.md)
- [Configure InfiniBand](../HowTo/orchestrator/configure_infiniband.md)
- [Configure Cluster DNS](../HowTo/orchestrator/configure_cluster_dns.md)
- [Configure Storage](../HowTo/orchestrator/configure_storage.md)

















