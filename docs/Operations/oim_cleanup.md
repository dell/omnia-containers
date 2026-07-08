
# OIM Cleanup


The `oim_cleanup.yml` playbook tears down the Omnia Infrastructure Manager
(OIM) configuration, removing containers, services, and state so you can start
fresh. This is a **destructive operation** --- use it only when you need to
completely reset the OIM.

## When to Use OIM Cleanup


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
  - `/opt/omnia/input/project_default/` (mapping files, configuration files)

## Tasks Performed by the Playbook


The `oim_cleanup.yml` playbook performs the following tasks:

- Clean up all containers, log files, and metadata on the OIM node.
- Clean up any PostgreSQL database deployed as part of BuildStreaM on the OIM.
- Rollback the firewall ports on the OIM node to its default setting.


## Steps


1. To clean up the OIM and the PostgreSQL database which is deployed as part
   of BuildStreaM, perform one of the following:

   - **If the BuildStreaM PostgreSQL database is not deployed on the OIM node**,
     and you want to clean up the OIM, run the following command:

      ```bash title="Run on: omnia_core container"
      ssh omnia_core
      cd /omnia/utils
      ansible-playbook oim_cleanup.yml
      ```

   - **If the BuildStreaM PostgreSQL database is deployed on the OIM node**,
     and you want to clean up the OIM and the PostgreSQL database, run the
     following command:

      ```bash title="Run on: omnia_core container"
      ssh omnia_core
      cd /omnia/utils
      ansible-playbook oim_cleanup.yml -e postgres_backup=false
      ```

!!! note

    The `postgres_backup` parameter determines whether the PostgreSQL
    database should be backed up before cleanup.

    - If `postgres_backup` is set to `true`, the database will be backed
      up before cleanup.
    - If `postgres_backup` is set to `false`, the database will not be
      backed up before cleanup.

   - **If the BuildStreaM PostgreSQL database is deployed on the OIM node**,
     and you want to clean up the OIM but **retain** the PostgreSQL database,
     run the following command:

      ```bash title="Run on: omnia_core container"
      ssh omnia_core
      cd /omnia/utils
      ansible-playbook oim_cleanup.yml -e postgres_backup=true
      ```

!!! important

    When prompted to back up the PostgreSQL database that you want to
    retain, record the database credentials. These credentials are
    required to restore the database when running the `prepare_oim.yml`
    playbook.

2. After running the `oim_cleanup.yml` playbook, do the following:

   - Reboot the OIM node to ensure all changes take effect.
   - The `omnia_core` container is **not** removed by `oim_cleanup.yml`.
     To delete it, log in to the OIM node and run:

      ```bash title="Run on: OIM host"
      omnia.sh --uninstall
      ```

!!! warning

    - After a clean-up, when re-provisioning your cluster by re-running the
      `provision.yml` playbook, ensure to use a different `admin_nic_subnet` in
      `input/provision_config.yml` to avoid a conflict with newly assigned
      servers. Alternatively, disable any OS available in the
      **Boot Option Enable/Disable** section of your BIOS settings
      (**BIOS Settings > Boot Settings > UEFI Boot Settings**) on all target
      nodes.
    - On subsequent runs of `provision.yml`, if users are unable to log into
      the server, refresh the SSH key manually and retry:

      ```bash
      ssh-keygen -R <node IP>
      ```
