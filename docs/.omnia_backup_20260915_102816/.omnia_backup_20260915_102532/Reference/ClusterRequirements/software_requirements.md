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
- For RHEL systems without a subscription, the repository URLs for `x86_64_codeready-builder`, `x86_64_appstream`, and `x86_64_baseos` are mandatory.
- Docker credentials are a mandatory requirement to pull in the essential packages during local repository deployment.
- If the Slurm RPMS is already available, update the value in the URL of the `user_repo_url_x86_64` or `user_repo_url_aarch64` parameter in `/opt/omnia/input/project_default/local_repo_config.yml`.
- In a mixed architecture environment where the Slurm control node and compute nodes use different architectures (for example, control node with x86_64 and compute nodes with aarch64), ensure that Slurm binaries for both architectures are compiled and available in the user repository.
- If the repository is hosted, use the URL created in the `local_repo_config.yml` file.

    ```yaml title="File: /opt/omnia/input/project_default/local_repo_config.yml"
    user_repo_url_x86_64:
      - { url: "http://<ipaddress>/slurm-repo/x86_64", gpgkey: "", sslcacert: "", sslclientkey: "", sslclientcert: "", name: "slurm_custom" }

    user_repo_url_aarch64:
      - { url: "http://<ipaddress>/slurm-repo/aarch64", gpgkey: "", sslcacert: "", sslclientkey: "", sslclientcert: "", name: "slurm_custom" }
    ```

    Run `ansible-playbook local_repo/local_repo.yml`.

- Create Slurm repository build for x86_64. See [Build Slurm repository for x86_64](../../HowTo/Slurm/build_slurm_repo.md) and [Host RPMS on Apache server](../../HowTo/Slurm/host_slurm_repo.md).

!!! note

    - If any user repository is already hosted externally, update the value of the `user_repo_url_x86_64` or `user_repo_url_aarch64` parameter in `/opt/omnia/input/project_default/local_repo_config.yml` with the hosted repository URL based on the architecture.
    - If the RPMs are already available but are not externally hosted, place the RPMs in the OIM and follow the steps in [Host RPMS on Apache server](../../HowTo/Slurm/host_slurm_repo.md). After hosting the RPMs, update the `user_repo_url_x86_64` or `user_repo_url_aarch64` parameter with the newly created repository URL.

## Lightweight Directory Access Protocol (LDAP)

- The LDAP server details are required to configure the `omnia_auth` container and OpenLDAP as a proxy server.
- To deploy an external OpenLDAP server for authentication, ensure that the OpenLDAP server is deployed and configured with the required directory structure (users and groups). For the detailed steps, see [External LDAP Deployment](../../HowTo/Authentication/deploy_external_ldap.md).

## Lightweight Distributed Metric Service (LDMS)

- Ensure that EPEL and AppStream repositories are configured and the python3-devel and python3-Cython packages are installed. To install the packages, run the following command:

    ```bash title="Run on: OIM host"
    sudo dnf install -y python3-devel python3-Cython
    ```

- The LDMS RPM must be available in the user repository, and the `ldms.json` file should be updated accordingly. If the LDMS RPM is not available, refer to [Building LDMS PRODUCER RPM Package](https://github.com/dell/omnia-containers?tab=readme-ov-file#building-ldms-producer-rpm-package) for instructions on building LDMS RPMs.
- If the LDMS RPMS are already available, update the value (`<hosted LDMS repository url>`) in the URL of the `user_repo_url_x86_64` or `user_repo_url_aarch64` parameter in `/opt/omnia/input/project_default/local_repo_config.yml`.
- If the repository is hosted, use the URL created in the `local_repo_config.yml` file.

    ```yaml title="File: /opt/omnia/input/project_default/local_repo_config.yml"
    user_repo_url_x86_64:
      - { url: "http://<ipaddress>/ldms-repo/x86_64", gpgkey: "", sslcacert: "", sslclientkey: "", sslclientcert: "", name: "ldms" }

    user_repo_url_aarch64:
      - { url: "http://<ipaddress>/ldms-repo/aarch64", gpgkey: "", sslcacert: "", sslclientkey: "", sslclientcert: "", name: "ldms" }
    ```

    Run `ansible-playbook local_repo/local_repo.yml`.

## BuildStreaM

- A dedicated node is required for BuildStreaM GitLab deployment.
- The node must have sufficient system resources for BuildStreaM (minimum 4 GB RAM, 2 CPU cores, 20GB free disk space)
- GitLab requires a minimum of 2 CPU cores. More cores may be needed for production workloads.
- Network connectivity for GitLab services.
- Ensure that Omnia BuildStreaM container, PostgreSQL container, and Playbook Watcher service are deployed on the OIM node. See [Prepare the Omnia Infrastructure Manager](../../HowTo/Setup/prepare_oim.md).

!!! info

    - [Installed Software](../SupportMatrix/installed_software.md) -- Refer to this document for the list of software installed in OMNIA.
