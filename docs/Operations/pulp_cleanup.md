# Cleanup Local Pulp Repositories

Use the Repository Manager cleanup flow to remove RPM repositories, file artifacts,
or container images that are no longer required. The cleanup runs on the OIM
and changes the Pulp content selected for the current catalog context.

!!! warning

    Cleanup permanently removes the selected content. Confirm the exact names
    before running the playbook. Removed content must be downloaded again if a
    later workflow requires it.

## Prerequisites

- Complete [OIM setup](../HowTo/main/setup_oim.md).
- Ensure the Pulp service is running and accessible from the OIM.
- Identify the exact repository, file, or container names to remove.
- Set `OMNIA_DATA_PATH` and `OMNIA_PROJECT_NAME` if you do not use their
  defaults.

## Clean up selected content

1. Activate the Omnia virtual environment and open the Repository Manager playbook
   directory:

    ```bash title="Run on: OIM host"
    source /opt/omnia/activate-omnia.sh
    cd src/repo_manager/playbooks
    ```

2. Run the command for the content type that you want to remove.

    Remove one RPM repository:

    === "Using omnia.sh (recommended)"

        ```bash title="Run on: OIM host"
        cd <OMNIA_SOURCE_PATH>/src/main
        ./omnia.sh --run repo_manager --tags cleanup_repos \
          -e "cleanup_repos=x86_64_rhel_10.0_epel"
        ```

    === "Using ansible-playbook"

        ```bash title="Run on: OIM host"
        source /opt/omnia/activate-omnia.sh
        cd <OMNIA_SOURCE_PATH>/src/repo_manager/playbooks
        ansible-playbook repo_manager.yml --tags cleanup_repos \
          -e "cleanup_repos=x86_64_rhel_10.0_epel"
        ```

    Remove one file artifact:

    === "Using omnia.sh (recommended)"

        ```bash title="Run on: OIM host"
        cd <OMNIA_SOURCE_PATH>/src/main
        ./omnia.sh --run repo_manager --tags cleanup_repos \
          -e "cleanup_files=cffi==1.17.1"
        ```

    === "Using ansible-playbook"

        ```bash title="Run on: OIM host"
        source /opt/omnia/activate-omnia.sh
        cd <OMNIA_SOURCE_PATH>/src/repo_manager/playbooks
        ansible-playbook repo_manager.yml --tags cleanup_repos \
          -e "cleanup_files=cffi==1.17.1"
        ```

    Remove one container image and all its tags:

    === "Using omnia.sh (recommended)"

        ```bash title="Run on: OIM host"
        cd <OMNIA_SOURCE_PATH>/src/main
        ./omnia.sh --run repo_manager --tags cleanup_repos \
          -e "cleanup_containers=docker.io/library/busybox"
        ```

    === "Using ansible-playbook"

        ```bash title="Run on: OIM host"
        source /opt/omnia/activate-omnia.sh
        cd <OMNIA_SOURCE_PATH>/src/repo_manager/playbooks
        ansible-playbook repo_manager.yml --tags cleanup_repos \
          -e "cleanup_containers=docker.io/library/busybox"
        ```

    To remove only one container tag, include the tag in the value, for
    example, `docker.io/library/busybox:1.36`.

## Clean up all selected content categories

Use `all` with `force=true` to remove every artifact in the specified
categories:

=== "Using omnia.sh (recommended)"

    ```bash title="Run on: OIM host"
    cd <OMNIA_SOURCE_PATH>/src/main
    ./omnia.sh --run repo_manager --tags cleanup_repos \
      -e "cleanup_repos=all" \
      -e "cleanup_files=all" \
      -e "cleanup_containers=all" \
      -e "force=true"
    ```

=== "Using ansible-playbook"

    ```bash title="Run on: OIM host"
    source /opt/omnia/activate-omnia.sh
    cd <OMNIA_SOURCE_PATH>/src/repo_manager/playbooks
    ansible-playbook repo_manager.yml --tags cleanup_repos \
      -e "cleanup_repos=all" \
      -e "cleanup_files=all" \
      -e "cleanup_containers=all" \
      -e "force=true"
    ```

You can omit categories that you do not want to clean. `force=true` is required
when a category is set to `all`.

!!! note

    Content cleanup does not remove the Pulp deployment. To remove Pulp itself,
    use the separate `cleanup_pulp` tag only when you intend to decommission the
    service.

## Verify cleanup

Review the Repository Manager log at:

```text
/var/log/omnia/repo_manager/repo_manager.log
```

Per-context cleanup results are written below:

```text
<OMNIA_DATA_PATH>/repo_manager/log/<os>/<version>/cleanup/
├── standard.log
└── cleanup_status.csv
```

For shared catalog contexts, the path can omit the version directory. Check
`standard.log` for detailed actions and `cleanup_status.csv` for the result of
each requested cleanup.
