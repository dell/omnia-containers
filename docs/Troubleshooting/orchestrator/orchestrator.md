# Orchestrator issues

Start with the active project inputs and the phase that failed. Load the Omnia
environment before using any paths:

```bash title="Run on: OIM"
source /etc/profile.d/omnia-env.sh
orchestrator_path="${OMNIA_DATA_PATH}/orchestrator"
project_input="$orchestrator_path/input/$OMNIA_PROJECT_NAME"
project_output="$orchestrator_path/output/$OMNIA_PROJECT_NAME"
```

The main Ansible execution log is
`/var/log/omnia/orchestrator/orchestrator.log`. Generated status and inventory
files are under `$project_output`.

## Input or precheck failure

Run the phases separately so the failing contract is clear:

=== "Using omnia.sh (recommended)"

    ```bash title="Run on: OIM host"
    cd <OMNIA_SOURCE_PATH>/src/main
    ./omnia.sh --run orchestrator --tags validate
    ./omnia.sh --run orchestrator --tags precheck
    ```

=== "Using ansible-playbook"

    ```bash title="Run on: OIM host"
    source /opt/omnia/activate-omnia.sh
    cd <OMNIA_SOURCE_PATH>/src/orchestrator/playbooks
    ansible-playbook orchestrator.yml --tags validate
    ansible-playbook orchestrator.yml --tags precheck
    ```

Review the named file in `$project_input`. Common causes are an invalid PXE
mapping header, duplicate node identifiers, a missing referenced storage name,
or an image absent from Image Build Manager's successful `build_status.yml`.
Do not edit generated content under `$project_output` to correct an input
failure.

## Provisioning or PXE failure

1. Review the mapping selected by `pxe_mapping_file_path` in
   `orchestrator_config.yml`.
2. Check OpenCHAMI and DHCP services on the OIM:

    ```bash title="Run on: OIM"
    systemctl status openchami.target --no-pager
    systemctl list-dependencies openchami.target --plain
    podman logs --tail 100 coresmd-coredhcp
    ```

3. Review the generated result files:

    ```bash title="Run on: OIM"
    cat "$project_output/provisioning_report.yml"
    cat "$project_output/pxeboot_status.yml"
    cat "$project_output/failed_nodes.json"
    ```

4. Use `failure_stage` to distinguish an iDRAC PXE operation from the later
   node-registration wait. See [Provisioning Issues](provisioning.md) and
   [OpenCHAMI Issues](openchami.md).

## Slurm failure

Run diagnostics on the Slurm controller, not on the OIM:

```bash title="Run on: Slurm controller"
systemctl status munge slurmctld slurmdbd mariadb --no-pager
sinfo -Nel
journalctl -u slurmctld -b -n 200 --no-pager
```

On an affected compute node, check `slurmd`, Munge, shared mounts, and
cloud-init. See [Slurm Issues](slurm.md) for targeted recovery procedures.

## Kubernetes failure

Run cluster diagnostics on the first Kubernetes control-plane node:

```bash title="Run on: first Kubernetes control-plane node"
kubectl get nodes -o wide
kubectl get pods -A -o wide
kubectl get events -A --sort-by=.lastTimestamp
```

Describe the first failing node, pod, PVC, or service before restarting it.
See [Kubernetes Issues](kubernetes.md).

## Authentication failure

OpenLDAP runs as the `omnia_auth` Quadlet service on the OIM; there is no
OIM-hosted `slapd` service to manage directly:

```bash title="Run on: OIM"
systemctl status omnia_auth --no-pager
podman logs --tail 100 omnia_auth
```

The LDAP base is derived from `SYSTEM_DOMAIN_NAME`. On clients, verify SSSD and
the generated search base rather than using a fixed example DN. See
[Authentication Issues](authentication.md).

## Storage failure

Use the mount selected by `nfs_storage_name` or `vast_storage_name` in the
active `omnia_config.yml`; a storage entry that is merely present in
`storage_config.yml` is not necessarily selected.

```bash title="Run on: affected host"
findmnt -t nfs,nfs4
systemctl status nfs-client.target --no-pager
```

If the OIM itself exports the selected share, also inspect `exportfs -v` and
`nfs-server`. For an external appliance, perform those server-side checks
through its supported administration interface. See
[Configure Storage](../../HowTo/orchestrator/configure_storage.md).

## Related topics

- [Configure PXE Boot](../../HowTo/orchestrator/configure_pxe_boot.md)
- [Deploy Slurm](../../HowTo/orchestrator/deploy_slurm.md)
- [Deploy Kubernetes](../../HowTo/orchestrator/deploy_kubernetes.md)
- [Configure InfiniBand](../../HowTo/orchestrator/configure_infiniband.md)
- [Configure Cluster DNS](../../HowTo/orchestrator/configure_cluster_dns.md)
