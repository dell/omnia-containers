# Add an RPM Repository and Packages

## Overview

Add an RPM source by defining it in `repo_manager_config.yml` and referencing
the same name from a selected catalog package. Repository mappings are scoped by
OS minor version and architecture.

Use `user_repos` for independent custom repositories. Repository names may
also be defined directly under the architecture. Both locations are resolved
as one lookup map. `user_repos` is the recommended location for new custom
repositories. The examples show two single-version configurations and one
multi-version configuration using RHEL 10.0 and RHEL 10.2. For another
catalog-selected RHEL 10.x minor version, use that version consistently in the
repository mapping and catalog package source. If a selected catalog later
provides another supported minor version, such as RHEL 10.4, the corresponding
configuration uses `"10.4"` throughout.

## Prerequisites

- Complete [Create Local Repositories](configure_repos.md).
- Know the repository URL, target RHEL minor version, architecture, and any GPG
  or TLS material.
- Ensure the repository exposes `repodata/repomd.xml` and is reachable from
  the OIM.
- Identify the catalog package or group that will consume the repository. See
  [Select or update the catalog](../main/update_catalog.md) to confirm which
  catalog file is active.

## Procedure

1. Add the repository below the matching version and architecture in
   `$OMNIA_DATA_PATH/repo_manager/input/$OMNIA_PROJECT_NAME/repo_manager_config.yml`
   (default `/opt/omnia/repo_manager/input/project_default/repo_manager_config.yml`).
   If the staged file does not exist, run `domain-init.sh` from
   `src/repo_manager/` first:

    === "Single-version example: RHEL 10.0"

        ~~~yaml
        repositories:
          "10.0":
            x86_64:
              user_repos:
                slurm_custom:
                  url: "https://repo.example.com/slurm/10.0/"
                  policy: partial
                  caching: true
                  priority: 99
        ~~~

    === "Single-version example: RHEL 10.2"

        ~~~yaml
        repositories:
          "10.2":
            x86_64:
              user_repos:
                slurm_custom:
                  url: "https://repo.example.com/slurm/10.2/"
                  policy: partial
                  caching: true
                  priority: 99
        ~~~

    === "Multi-version (hybrid) example: RHEL 10.0 and RHEL 10.2"

        ~~~yaml
        repositories:
          "10.0":
            x86_64:
              user_repos:
                slurm_custom:
                  url: "https://repo.example.com/slurm/10.0/"
                  policy: partial
                  caching: true
                  priority: 99
          "10.2":
            x86_64:
              user_repos:
                slurm_custom:
                  url: "https://repo.example.com/slurm/10.2/"
                  policy: partial
                  caching: true
                  priority: 99
        ~~~

    The repository name may contain letters, numbers, underscores, periods, and
    hyphens. Configure a separate mapping for `aarch64` when that architecture
    is selected; an `x86_64` URL is never reused for `aarch64`.

2. Reference the exact repository key in the catalog package source:

    === "Single-version example: RHEL 10.0"

        ~~~json
        {
          "name": "slurm-slurmctld",
          "packagetype": "rpm",
          "sources": [
            {
              "architecture": "x86_64",
              "name": "rhel",
              "version": ["10.0"],
              "reponame": "slurm_custom"
            }
          ]
        }
        ~~~

    === "Single-version example: RHEL 10.2"

        ~~~json
        {
          "name": "slurm-slurmctld",
          "packagetype": "rpm",
          "sources": [
            {
              "architecture": "x86_64",
              "name": "rhel",
              "version": ["10.2"],
              "reponame": "slurm_custom"
            }
          ]
        }
        ~~~

    === "Multi-version (hybrid) example: RHEL 10.0 and RHEL 10.2"

        ~~~json
        {
          "name": "slurm-slurmctld",
          "packagetype": "rpm",
          "sources": [
            {
              "architecture": "x86_64",
              "name": "rhel",
              "version": ["10.0"],
              "reponame": "slurm_custom"
            },
            {
              "architecture": "x86_64",
              "name": "rhel",
              "version": ["10.2"],
              "reponame": "slurm_custom"
            }
          ]
        }
        ~~~

    Also add the package key to a group that is reachable from the intended
    functional layer. See
    [Configure Catalog Content](adding_additional_packages.md).

3. Validate, synchronize, and publish a new status file:

    === "Using omnia.sh (recommended)"

        ~~~bash title="Run on: OIM host"
        cd <OMNIA_SOURCE_PATH>/src/main
        ./omnia.sh --run repo_manager \
          --tags "precheck,download,status"
        ~~~

    === "Using ansible-playbook"

        ~~~bash title="Run on: OIM host"
        source /opt/omnia/activate-omnia.sh
        cd <OMNIA_SOURCE_PATH>/src/repo_manager/playbooks
        ansible-playbook repo_manager.yml \
          --tags "precheck,download,status"
        ~~~

## Verification

The complete Pulp RPM name has this form:

~~~text
<architecture>_<os-type>_<os-version>_<repository>
~~~

Inspect the version-qualified Pulp name for every RHEL 10.x minor version
selected by the catalog. The following commands verify the 10.0-only,
10.2-only, and combined examples; run the applicable command or commands:

~~~bash title="Run on: OIM host"
pulp rpm repository show --name x86_64_rhel_10.0_slurm_custom
pulp rpm distribution show --name x86_64_rhel_10.0_slurm_custom
pulp rpm repository show --name x86_64_rhel_10.2_slurm_custom
pulp rpm distribution show --name x86_64_rhel_10.2_slurm_custom
~~~

Confirm that each selected repository URL is present under
`repositories."<version>".x86_64` in
`$OMNIA_DATA_PATH/repo_manager/output/<project>/repo_status.yml`. Replace
`<version>` with each RHEL 10.x minor version selected by the catalog.

## Next steps

- [Configure and add packages](adding_additional_packages.md) that use the new
  `reponame`.
- [Build Cluster Images](../image_build_manager/build_images.md) after
  `repo_status.yml` reports success.
- [Force an RPM resynchronization](../../Operations/repo_manager/local_repository_resync.md) when the upstream
  repository changes.

## Troubleshooting

- **The mapping is ignored**: Repository Manager validates and synchronizes only
  repositories referenced by packages in selected catalog functional layers.
- **The URL is reported missing**: Only `baseos`, `appstream`, and
  `codeready-builder` are eligible for subscription discovery. Every other
  referenced repository needs an explicit URL.
- **Metadata validation fails**: Verify
  `<url-without-trailing-slash>/repodata/repomd.xml` is reachable from the OIM.
- **A priority is rejected**: Use an integer from 1 through 100.
- **An architecture is missing**: Define the same repository name independently
  under every architecture selected by the catalog.
