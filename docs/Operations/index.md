# Operations & Maintenance


Day-2 operations for managing a running Omnia cluster. These guides cover
common administrative tasks you will perform after the initial deployment is
complete---scaling or re-provisioning the cluster, managing repositories and
logs, and cleaning up domains or the OIM environment.

!!! tip

    If you have not yet deployed your cluster, start with the
    [Get Started Tutorials](../GetStarted/index.md). The procedures in this section assume a
    working Omnia environment.

## Environment and content lifecycle

- [Maintain the Main environment](maintain_main_environment.md) to audit
  dependency declarations or remove the installed OIM environment.
- [Clean up the OIM](oim_cleanup.md) by removing deployed domains in reverse
  dependency order before removing the shared execution environment.
- [Clean up built images](cleanup_built_images.md) selectively or completely
  from S3 and the local registry while preserving Image Build Manager
  services and configuration.

## Repository Manager

- [Configure VAST storage and build VAST RPMs](repo_manager/configure_vast.md)
  before adding the hosted VAST repository to Repository Manager.
- [Build Slurm RPMs](repo_manager/build_slurm_repo.md) for `x86_64` or
  `aarch64` nodes before adding the hosted repository to Repository Manager.
- [Update repositories after catalog changes](repo_manager/updating_local_repositories.md)
  to synchronize revised catalog content and regenerate `repo_status.yml`.
- [Resynchronize local RPM repositories](repo_manager/local_repository_resync.md)
  to force selected or all catalog-required RPM remotes to check upstream.

## Node lifecycle

- [Add nodes](add_nodes.md) through the direct Orchestrator workflow and use a
  custom inventory to PXE boot only the new physical nodes.
- [Remove Slurm compute nodes](remove_slurm_nodes.md) omitted from the current
  desired mapping, with source-defined handling for active jobs.
- [Add nodes through BuildStreaM](build_stream/add_nodes.md) by committing the
  revised Orchestrator mapping and running the deploy pipeline.
- [Reprovision a cluster](reprovision_cluster.md) when existing nodes must be
  provisioned again.

## BuildStreaM lifecycle

- [Update the BuildStreaM catalog](build_stream/update_catalog.md).
- [Clean up image groups](build_stream/cleanup_operations.md).
- [Retry a failed pipeline](build_stream/retry_pipelines.md).

## Diagnostics and recovery

- [Collect cluster logs](collect_cluster_logs.md) with the Utils `collect`
  workflow.
- [Back up OIM logs](../HowTo/utils/backup_oim_logs.md) with the Utils
  `backup_oim_logs` workflow to local or NFS storage.
- Use the [Slurm configuration utilities](../HowTo/utils/backup_slurm_config.md)
  to back up, remove, or restore the active Slurm configuration.
- Use [Log Management](log_management.md) for general log inspection.













