# Resynchronize Local RPM Repositories

## Overview

Use `resync_repos` with the `download` tag to force catalog-required RPM
repositories to check their upstream remotes. Without this variable, Repo
Manager synchronizes missing repositories and skips repositories already marked
as synchronized.

Resynchronization applies only to RPM repositories. Container images, File
artifacts, and Python packages keep their normal idempotent behavior.
For a multi-version catalog, repository names include the OS minor version and
each selected version is reconciled in its own execution context.

## Prerequisites

- Complete [Create Local Repositories](../../HowTo/repo_manager/configure_repos.md).
- Ensure Pulp is running and the upstream RPM URLs are reachable.
- Export the same catalog and project environment used for the original
  synchronization.
- Obtain the exact, case-sensitive Pulp repository name for targeted
  resynchronization.

## Procedure

### Resynchronize all required RPM repositories

=== "Using omnia.sh (recommended)"

    ~~~bash title="Run on: OIM host"
    cd <OMNIA_SOURCE_PATH>/src/main
    ./omnia.sh --run repo_manager --tags download \
      -e "resync_repos=all"
    ~~~

=== "Using ansible-playbook"

    ~~~bash title="Run on: OIM host"
    source /opt/omnia/activate-omnia.sh
    cd <OMNIA_SOURCE_PATH>/src/repo_manager/playbooks
    ansible-playbook repo_manager.yml --tags download \
      -e "resync_repos=all"
    ~~~

This forces every catalog-required RPM repository in every selected
OS-version and architecture context to check upstream.

### Resynchronize selected RPM repositories

Use complete names in the form
`<architecture>_<os-type>_<os-version>_<repository>`:

=== "Using omnia.sh (recommended)"

    ~~~bash title="Run on: OIM host"
    cd <OMNIA_SOURCE_PATH>/src/main
    ./omnia.sh --run repo_manager --tags download \
      -e "resync_repos=x86_64_rhel_10.0_baseos"
    ~~~

=== "Using ansible-playbook"

    ~~~bash title="Run on: OIM host"
    source /opt/omnia/activate-omnia.sh
    cd <OMNIA_SOURCE_PATH>/src/repo_manager/playbooks
    ansible-playbook repo_manager.yml --tags download \
      -e "resync_repos=x86_64_rhel_10.0_baseos"
    ~~~

Use a comma-separated value for more than one repository:

=== "Using omnia.sh (recommended)"

    ~~~bash title="Run on: OIM host"
    cd <OMNIA_SOURCE_PATH>/src/main
    ./omnia.sh --run repo_manager --tags download \
      -e "resync_repos=x86_64_rhel_10.0_baseos,x86_64_rhel_10.0_appstream"
    ~~~

=== "Using ansible-playbook"

    ~~~bash title="Run on: OIM host"
    source /opt/omnia/activate-omnia.sh
    cd <OMNIA_SOURCE_PATH>/src/repo_manager/playbooks
    ansible-playbook repo_manager.yml --tags download \
      -e "resync_repos=x86_64_rhel_10.0_baseos,x86_64_rhel_10.0_appstream"
    ~~~

To target repositories from different RHEL versions in the same catalog, keep
the version in each complete Pulp repository name:

=== "Using omnia.sh (recommended)"

    ~~~bash title="Run on: OIM host"
    cd <OMNIA_SOURCE_PATH>/src/main
    ./omnia.sh --run repo_manager --tags download \
      -e "resync_repos=x86_64_rhel_10.0_baseos,x86_64_rhel_10.2_baseos"
    ~~~

=== "Using ansible-playbook"

    ~~~bash title="Run on: OIM host"
    source /opt/omnia/activate-omnia.sh
    cd <OMNIA_SOURCE_PATH>/src/repo_manager/playbooks
    ansible-playbook repo_manager.yml --tags download \
      -e "resync_repos=x86_64_rhel_10.0_baseos,x86_64_rhel_10.2_baseos"
    ~~~

During a targeted resync, Repository Manager does not force unrelated RPM remotes to
resynchronize, but it validates their readiness and repairs missing
publications or distributions before package downloads continue.

After a successful resync, regenerate the consumer status file:

=== "Using omnia.sh (recommended)"

    ~~~bash title="Run on: OIM host"
    cd <OMNIA_SOURCE_PATH>/src/main
    ./omnia.sh --run repo_manager --tags status
    ~~~

=== "Using ansible-playbook"

    ~~~bash title="Run on: OIM host"
    source /opt/omnia/activate-omnia.sh
    cd <OMNIA_SOURCE_PATH>/src/repo_manager/playbooks
    ansible-playbook repo_manager.yml --tags status
    ~~~

## Verification

Inspect the exact repository and its distribution:

~~~bash title="Run on: OIM host"
pulp rpm repository show --name x86_64_rhel_10.0_baseos
pulp rpm distribution show --name x86_64_rhel_10.0_baseos
~~~

Review `$OMNIA_DATA_PATH/repo_manager/log/<os>/<version>/standard.log` and confirm
the regenerated `repo_status.yml` reports `overall_status: success`. For a
multi-version catalog, confirm every `overall_status_by_version` value is also
`success` and inspect each selected
`repositories.<version>.<architecture>` map. When upstream content changed,
Repository Manager creates the required publication and updates the existing
distribution without changing its URL.

`repo_status.yml` is the downstream consumer contract. The separate
`repo_resync_status.yml` file, when produced by the standalone exact-RPM
reconciliation operation, is an administrative result and does not replace
`repo_status.yml`.

## Next steps

- [Build Cluster Images](../../HowTo/image_build_manager/build_images.md).
- [Update Local Repositories](updating_local_repositories.md) when the catalog,
  rather than only the upstream RPM content, changed.
- [Add an RPM Repository and Packages](../../HowTo/repo_manager/adding_additional_repositories.md).

## Troubleshooting

- **A target name is rejected**: Use the complete, case-sensitive Pulp name and
  ensure it belongs to a context selected by the current catalog.
- **A prior interrupted sync is active**: Repository Manager attempts to recover the
  active Pulp task before deciding whether to start or skip another sync. Do
  not launch a second Repository Manager process.
- **The operation appears idle**: Follow
  `$OMNIA_DATA_PATH/repo_manager/log/<os>/<version>/standard.log` for the
  approximately 60-second progress heartbeat.
- **The remote fails**: Verify the repository URL, GPG key, subscription
  access, and available storage, then inspect `podman logs --tail 200 pulp`.
- **A later OS version remains pending**: Repository Manager processes versions
  numerically and stops after a failed context. Correct the earlier version,
  rerun the download and status phases, and verify all per-version states
  before starting Image Build Manager.
