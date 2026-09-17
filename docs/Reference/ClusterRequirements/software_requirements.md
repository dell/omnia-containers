# Software Requirements

This section outlines the key software and repository requirements for the components used by Omnia to deploy HPC clusters. For more information about the supported devices and software, see [Support Matrix](../index.md#support-matrix).

## Repository

- Enable the **AppStream** and **BaseOS** repositories via the RHEL subscription manager.
- To pin specific RHEL version in the subscription manager, use the following commands:

    ```bash title="Run on: OIM host"
    subscription-manager release --show
    subscription-manager release --set=10.0
    ```

- Ensure that RHEL has an **active subscription** or is configured to access **local repositories**.
- Verify that all **repository URLs** for the software packages are **accessible** -- downloads will fail for inaccessible packages.
- For RHEL systems without a subscription, configure non-empty URLs for `baseos`, `appstream`, and `codeready-builder` under each required RHEL 10.0 architecture in `repo_manager_config.yml`.
- Docker Hub credentials are optional. Configure them through the Repository
  Manager credentials flow when authenticated pulls are required or anonymous
  pull limits affect synchronization.
- If the Slurm RPMs are already available, configure the hosted repository under `repositories."10.0".<architecture>.user_repos.slurm_custom` in `$OMNIA_DATA_PATH/repo_manager/input/$OMNIA_PROJECT_NAME/repo_manager_config.yml` for each required architecture.
- In a mixed architecture environment where the Slurm control node and compute nodes use different architectures (for example, control node with x86_64 and compute nodes with aarch64), ensure that compatible Slurm packages for both architectures are available in the user repository.
- Ensure that the selected catalog references `slurm_custom` and that its Slurm package names match the hosted RPMs.

    ```yaml title="File: $OMNIA_DATA_PATH/repo_manager/input/$OMNIA_PROJECT_NAME/repo_manager_config.yml"
    repositories:
      "10.0":
        x86_64:
          user_repos:
            slurm_custom:
              url: "http://<host>/slurm-repo/x86_64"
        aarch64:
          user_repos:
            slurm_custom:
              url: "http://<host>/slurm-repo/aarch64"
    ```

    Synchronize the catalog content and verify the result:

    === "Using omnia.sh (recommended)"

        ```bash title="Run on: OIM host"
        cd <OMNIA_SOURCE_PATH>/src/main
        ./omnia.sh --run repo_manager --tags download
        ./omnia.sh --run repo_manager --tags status
        ```

    === "Using ansible-playbook"

        ```bash title="Run on: OIM host"
        source /opt/omnia/activate-omnia.sh
        cd <OMNIA_SOURCE_PATH>/src/repo_manager
        ansible-playbook playbooks/repo_manager.yml --tags download
        ansible-playbook playbooks/repo_manager.yml --tags status
        ```

!!! note

    Omnia consumes a reachable RPM repository; it does not build or host the
    Slurm RPMs. Set the repository URL in the matching `user_repos` entry for
    each required architecture. See
    [Add an RPM Repository and Packages](../../HowTo/repo_manager/adding_additional_repositories.md).

## Lightweight Directory Access Protocol (LDAP)

- Include the OpenLDAP group in the selected catalog when centralized
  authentication is required. Orchestrator deploys the `omnia_auth` OpenLDAP
  container on the OIM; it does not configure an external LDAP endpoint.
- Configure `SYSTEM_DOMAIN_NAME`, `SYSTEM_ADMIN_NIC_IPV4`, and
  `ldap_connection_type`. Provide the OpenLDAP database username and password
  when the Orchestrator credential phase prompts for them. See
  [Deploy OpenLDAP](../../HowTo/orchestrator/deploy_openldap.md).

## Lightweight Distributed Metric Service (LDMS)

- Ensure that EPEL and AppStream repositories are configured and the python3-devel and python3-Cython packages are installed. To install the packages, run the following command:

    ```bash title="Run on: OIM host"
    sudo dnf install -y python3-devel python3-Cython
    ```

- The LDMS RPM must be available in the user repository. If the LDMS RPM is not available, refer to [Building LDMS PRODUCER RPM Package](https://github.com/dell/omnia-containers?tab=readme-ov-file#building-ldms-producer-rpm-package) for instructions on building LDMS RPMs.
- Ensure that the selected catalog references `ldms` and that its LDMS package names match the hosted RPMs.
- For every required architecture, configure the hosted LDMS repository under `repositories."10.0".<architecture>.user_repos.ldms` in `$OMNIA_DATA_PATH/repo_manager/input/$OMNIA_PROJECT_NAME/repo_manager_config.yml`.

    ```yaml title="File: $OMNIA_DATA_PATH/repo_manager/input/$OMNIA_PROJECT_NAME/repo_manager_config.yml"
    repositories:
      "10.0":
        x86_64:
          user_repos:
            ldms:
              url: "http://<host>/ldms-repo/x86_64"
        aarch64:
          user_repos:
            ldms:
              url: "http://<host>/ldms-repo/aarch64"
    ```

    Synchronize the catalog content and verify the result:

    === "Using omnia.sh (recommended)"

        ```bash title="Run on: OIM host"
        cd <OMNIA_SOURCE_PATH>/src/main
        ./omnia.sh --run repo_manager --tags download
        ./omnia.sh --run repo_manager --tags status
        ```

    === "Using ansible-playbook"

        ```bash title="Run on: OIM host"
        source /opt/omnia/activate-omnia.sh
        cd <OMNIA_SOURCE_PATH>/src/repo_manager
        ansible-playbook playbooks/repo_manager.yml --tags download
        ansible-playbook playbooks/repo_manager.yml --tags status
        ```

## BuildStreaM

- A dedicated node is required for BuildStreaM GitLab deployment.
- The node must have sufficient system resources for BuildStreaM (minimum 4 GB RAM, 2 CPU cores, 20GB free disk space)
- GitLab requires a minimum of 2 CPU cores. More cores may be needed for production workloads.
- Network connectivity for GitLab services.
- Ensure that Omnia BuildStreaM container, PostgreSQL container, and Playbook Watcher service are deployed on the OIM node. See [Prepare the Omnia Infrastructure Manager](../../HowTo/main/setup_oim.md).

!!! info

    - [Installed Software](../SupportMatrix/installed_software.md) -- Refer to this document for the list of software installed in OMNIA.














