# Update Local Repositories after Catalog Changes

## Overview

Repository Manager does not monitor the catalog for changes. After adding, updating,
or deleting catalog content, validate the revised catalog, synchronize it, and
regenerate `repo_status.yml`.

Successful content is tracked by exact package identity, so rerunning the
workflow reuses completed content instead of intentionally downloading
everything again.

When the active catalog contains more than one RHEL minor version, Repository
Manager applies the update to each selected version and architecture in numeric
version order. A failure in an earlier context prevents later contexts from
completing.

## Prerequisites

- Pulp is deployed and running.
- `SYSTEM_ADMIN_NIC_IPV4` and `CATALOG_FILE_PATH` are exported.
- The updated catalog remains an existing absolute `.json` file. To select a
  different catalog, follow
  [Select or update the catalog](../../HowTo/main/update_catalog.md).
- Any new RPM repositories or private registries are mapped in
  `repo_manager_config.yml`.
- For a multi-version catalog, `repo_manager_config.yml` contains the required
  mapping, subscription selection, or explicit URL for every selected version
  and architecture.

## Procedure

1. Change the catalog with one of the supported catalog operations:

    === "Using omnia.sh (recommended)"

        ~~~bash title="Run on: OIM host"
        cd <OMNIA_SOURCE_PATH>/src/main

        # Add or update packages and groups.
        ./omnia.sh --run repo_manager --tags catalog_add \
          -e "input_file=/absolute/path/to/additions.txt"

        # Or remove package references.
        ./omnia.sh --run repo_manager --tags catalog_delete \
          -e "input_file=/absolute/path/to/removals.txt"
        ~~~

    === "Using ansible-playbook"

        ~~~bash title="Run on: OIM host"
        source /opt/omnia/activate-omnia.sh
        cd <OMNIA_SOURCE_PATH>/src/repo_manager/playbooks

        # Add or update packages and groups.
        ansible-playbook repo_manager.yml --tags catalog_add \
          -e "input_file=/absolute/path/to/additions.txt"

        # Or remove package references.
        ansible-playbook repo_manager.yml --tags catalog_delete \
          -e "input_file=/absolute/path/to/removals.txt"
        ~~~

    The delete input lists package keys under their current group:

    ~~~ini
    [openldap_group]
    openldap_clients
    ~~~

    `catalog_delete` removes the package object only when no other group
    references it, and removes an empty group from its functional layers.

2. Validate the catalog and all active mappings:

    === "Using omnia.sh (recommended)"

        ~~~bash title="Run on: OIM host"
        cd <OMNIA_SOURCE_PATH>/src/main
        ./omnia.sh --run repo_manager --tags catalog_validate
        ./omnia.sh --run repo_manager --tags precheck
        ~~~

    === "Using ansible-playbook"

        ~~~bash title="Run on: OIM host"
        source /opt/omnia/activate-omnia.sh
        cd <OMNIA_SOURCE_PATH>/src/repo_manager/playbooks
        ansible-playbook repo_manager.yml --tags catalog_validate
        ansible-playbook repo_manager.yml --tags precheck
        ~~~

3. Synchronize selected content and regenerate the consumer contract:

    === "Using omnia.sh (recommended)"

        ~~~bash title="Run on: OIM host"
        cd <OMNIA_SOURCE_PATH>/src/main
        ./omnia.sh --run repo_manager --tags "download,status"
        ~~~

    === "Using ansible-playbook"

        ~~~bash title="Run on: OIM host"
        source /opt/omnia/activate-omnia.sh
        cd <OMNIA_SOURCE_PATH>/src/repo_manager/playbooks
        ansible-playbook repo_manager.yml --tags "download,status"
        ~~~

4. If content was removed from the catalog and must also be deleted from Pulp,
   use the matching selective cleanup target. Review the exact scope before
   confirming:

    === "Using omnia.sh (recommended)"

        ~~~bash title="Run on: OIM host"
        cd <OMNIA_SOURCE_PATH>/src/main
        # Exact RPM repository name.
        ./omnia.sh --run repo_manager --tags cleanup_repos \
          -e "cleanup_repos=x86_64_rhel_10.0_epel"

        # Exact container tag; sibling tags remain.
        ./omnia.sh --run repo_manager --tags cleanup_repos \
          -e "cleanup_containers=registry.example.com/team/image:v1"
        ~~~

    === "Using ansible-playbook"

        ~~~bash title="Run on: OIM host"
        source /opt/omnia/activate-omnia.sh
        cd <OMNIA_SOURCE_PATH>/src/repo_manager/playbooks
        # Exact RPM repository name.
        ansible-playbook repo_manager.yml --tags cleanup_repos \
          -e "cleanup_repos=x86_64_rhel_10.0_epel"

        # Exact container tag; sibling tags remain.
        ansible-playbook repo_manager.yml --tags cleanup_repos \
          -e "cleanup_containers=registry.example.com/team/image:v1"
        ~~~

    Selective cleanup invalidates the old `repo_status.yml`. Run
    `--tags "download,status"` afterward to restore still-required catalog
    content and publish current output.

## Verification

Inspect the current context summary, package state, and consumer output:

~~~text
$OMNIA_DATA_PATH/repo_manager/log/<os>/catalog_execution_summary.yml
$OMNIA_DATA_PATH/repo_manager/log/<os>/<version>/<architecture>/<group>/status.csv
$OMNIA_DATA_PATH/repo_manager/output/<project>/repo_status.yml
~~~

Confirm every selected context completed successfully and
`repo_status.yml` reports `overall_status: success` before starting an image
build. For a multi-version catalog, also confirm every value under
`overall_status_by_version` is `success` and each required
`repositories.<version>.<architecture>` map contains its synchronized URLs.

The downstream workflow consumes `repo_status.yml`. If an exact-RPM
reconciliation also produced `repo_resync_status.yml`, use that file only to
inspect the administrative reconciliation result; it does not replace the
consumer contract.

## Next steps

- [Build Cluster Images](../../HowTo/image_build_manager/build_images.md).
- [Resynchronize Local Repositories](local_repository_resync.md) when the goal
  is to check existing RPM remotes for upstream changes.
- [Configure Catalog Content](../../HowTo/repo_manager/adding_additional_packages.md).

## Troubleshooting

- **The changed package is not processed**: Confirm the package is reachable
  through a group and functional layer, and that its source matches the active
  version and architecture.
- **A later OS version remains pending**: Repository Manager processes contexts in
  numeric order and stops after a failed context. Fix the first failed version
  and rerun `download,status`.
- **Deleted catalog content still exists in Pulp**: Catalog deletion changes
  selection; it does not perform Pulp cleanup. Run a reviewed selective cleanup.
- **`repo_status.yml` is absent after cleanup**: This is intentional. Run
  `download,status` to synchronize the remaining catalog and regenerate it.
