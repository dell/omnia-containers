
# OIM Cleanup


The `oim_cleanup.yml` playbook tears down the Omnia Infrastructure Manager
(OIM) configuration, removing containers, services, and state so you can start
fresh. This is a **destructive operation** --- use it only when you need to
completely reset the OIM.

## When to use OIM cleanup


- **Fresh start** -- You want to redeploy Omnia from scratch after a failed or
  experimental deployment.
- **Version upgrade** -- You are upgrading to a new major version of Omnia that
  requires a clean OIM.
- **Environment reset** -- Lab or test environments where the OIM is frequently
  rebuilt.

!!! danger

    `oim_cleanup.yml` removes Podman containers, configuration files, and
    state data from the OIM. **This operation cannot be undone.** Ensure you
    have backed up any critical data (mapping files, custom configurations,
    credentials) before proceeding.

## Prerequisites


- You are logged in as `root` on the OIM host (not inside the `omnia_core`
  container).
- All cluster workloads have been drained or stopped.
- Critical data has been backed up:

  - `/omnia/input/` (mapping files, configuration files)
  - Custom Ansible inventories
  - Any modified playbook files
  - AES-256 encrypted credential vaults


## Procedure


1. **Log in to the OIM as root:**

   ```bash
   ssh root@<oim_ip>
   ```


   !!! note

       Do **not** run this playbook from inside the `omnia_core` container.
       The cleanup process removes the container itself.

2. **Navigate to the Omnia utils directory:**

   ```bash
   cd /omnia/utils/
   ```


3. **Run the cleanup playbook:**

   ```bash
   ansible-playbook oim_cleanup.yml
   ```


   The playbook performs the following actions:

   - Stops and removes all Omnia-managed Podman containers (`omnia_core`,
     OpenCHAMI, CoreDHCP, TFTP, Pulp, telemetry services).
   - Removes Podman pods and networks created by Omnia.
   - Deletes OIM service configuration files.
   - Cleans up SSH keys and known_hosts entries for provisioned nodes.
   - Removes cached OS images and repository data.

4. **Verify the cleanup:**

   ```bash
   # Confirm no Omnia containers remain
   podman ps -a | grep -i omnia

   # Confirm no Omnia pods remain
   podman pod ls
   ```



## Selective cleanup options


If you do not need a full teardown, `oim_cleanup.yml` supports selective
cleanup through extra variables:

| Option | Description |
| --- | --- |
| `cleanup_provisioning=true` | Remove only provisioning-related services (OpenCHAMI, CoreDHCP, TFTP) while keeping the `omnia_core` container and telemetry stack. |
| `cleanup_telemetry=true` | Remove only telemetry services (Kafka, VictoriaMetrics, Grafana) while keeping provisioning and core services. |
| `cleanup_repos=true` | Remove Pulp repository data and cached packages, freeing disk space without affecting running services. |

Example of selective cleanup:

```bash title="Run on: OIM host"
cd /omnia/utils/
ansible-playbook oim_cleanup.yml -e "cleanup_telemetry=true"
```


!!! tip

    Selective cleanup is useful when troubleshooting a specific subsystem. For
    example, if telemetry is misconfigured, you can tear down only the telemetry
    stack and redeploy it without disturbing the rest of the OIM.

## Post-cleanup steps


After a full cleanup, you will need to redeploy Omnia from the beginning:

1. Re-run the OIM preparation playbook (see [Prepare Oim](../HowTo/Setup/prepare_oim.md)).
2. Rebuild the `omnia_core` container (see [Deploy Omnia Core](../HowTo/Setup/deploy_omnia_core.md)).
3. Reconfigure inputs and credentials (see [Configure Inputs](../HowTo/Setup/configure_inputs.md)
   and [Configure Credentials](../HowTo/Setup/configure_credentials.md)).
4. Re-discover and provision nodes (see [Discover Nodes](../HowTo/Setup/discover_nodes.md)).


!!! info

    - [Reprovision Cluster](reprovision_cluster.md) -- Re-image individual nodes without tearing
      down the entire OIM.
    - [General](../Troubleshooting/general.md) -- Common issues that may arise after
      cleanup and redeployment.
