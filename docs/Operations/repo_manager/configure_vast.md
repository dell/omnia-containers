# Configure VAST Storage

## Overview

Build the VAST NFS repository and install the VAST client on cluster nodes. The VAST repository must be built from the official package, hosted on an HTTP server, and configured as a user repository in Omnia before provisioning.

!!! note

    The VAST repository must be hosted on an HTTP server (such as Apache) before it can be used as a user repository in Omnia.

## Prerequisites

Configure the following settings on the VAST Storage appliance before building the VAST repository:

1. **Log in to the VAST Dashboard** and click on **Element Store**.

    ![VAST Dashboard Element Store](../../assets/images/vast_storage_prereq_1.png)

2. **Configure Tenant** -- Verify that a tenant is configured on the VAST Storage appliance.

    ![VAST Tenant Configuration](../../assets/images/vast_storage_prereq_2.png)

3. **Configure Policies** -- Verify that the required policies are configured.

    ![VAST Policy Configuration](../../assets/images/vast_storage_prereq_3.png)

    Verify the policy options are configured as follows:

    ![VAST Policy Options](../../assets/images/vast_storage_prereq_4.png)

4. **Create New Configuration** -- Right-click on the empty space to display the **Create** option.

    ![VAST Create Option](../../assets/images/vast_storage_prereq_5.png)

    ![VAST Create Configuration](../../assets/images/vast_storage_prereq_6.png)

    Click **Create** to complete the configuration.

## Procedure

### Step 1: Download VAST

Download the VAST NFS package:

```bash title="Run on: OIM host"
curl -sSf https://vast-nfs.s3.amazonaws.com/download.sh | bash -s -- --version 4.5.5
```

![VAST Download](../../assets/images/vastrepo1.png)

### Step 2: Extract the package

Extract the downloaded tarball:

```bash title="Run on: OIM host"
tar -xf vastnfs-4.5.5.tar.xz vastnfs-4.5.5/
```

![VAST Extract](../../assets/images/vastrepo2.png)

### Step 3: Build the VAST repository

Navigate to the extracted directory and build the repository:

```bash title="Run on: OIM host"
cd vastnfs-4.5.5/
./build.sh bin
```

![VAST Build](../../assets/images/vastrepo3.png)

Once the build completes, the RPM files are created and ready to be hosted as a user repository. The VAST RPMs are located in the `dist/` directory within `vastnfs-4.5.5/`.

![VAST Build Output](../../assets/images/vastrepo4.png)

![VAST RPMs in dist directory](../../assets/images/vastrepo5.png)

```text title="Expected output"
========== Vast repo build completed ==========
```

### Step 4: Host the RPMs on an HTTP server

Host the built RPMs on an HTTP server (such as Apache) that serves as your user repository. You can use the OIM host as the HTTP server.

![VAST RPMs Hosted](../../assets/images/vastrepo6.png)

```text title="Expected output"
========== Vast rpms hosted for user_Repo ==========
```

!!! tip

    Refer to [Create Local Repositories](../../HowTo/repo_manager/configure_repos.md) for instructions on configuring repositories in Repo Manager.

### Step 5: Select a VAST-enabled catalog

Select a Slurm catalog that includes the `vast_stack_driver_groupv1` software
group. Catalog names ending in `_no_vast.json` do not contain the VAST client.
See [Select or Update the Catalog](../../HowTo/main/update_catalog.md) for the
available catalog selectors and selection procedure.

### Step 6: Configure the VAST user repository

Edit the project-scoped Repo Manager configuration:

```bash title="Run on: OIM host"
vi "$OMNIA_DATA_PATH/repo_manager/input/$OMNIA_PROJECT_NAME/repo_manager_config.yml"
```

Add the URL that hosts the VAST RPMs under the applicable operating-system
version and architecture. The repository name must be `vast` because the
VAST-enabled catalogs map the `vastnfs` package to that name.

```yaml
repositories:
  "10.0":
    x86_64:
      user_repos:
        vast:
          url: "https://<repository-host>/<vast-repository>/"
          gpgkey: ""
          sslcacert: ""
          sslclientkey: ""
          sslclientcert: ""
          priority: 10
```

Add the corresponding entry under `aarch64` when the selected catalog builds
aarch64 functional groups. Preserve the other repository definitions already
present in `repo_manager_config.yml`.

### Step 7: Synchronize the repository with Repository Manager

Run the Repository Manager domain workflow. Its canonical entry point is
`src/repo_manager/playbooks/repo_manager.yml`.

=== "Using omnia.sh (recommended)"

    ```bash title="Run on: OIM host"
    cd <OMNIA_SOURCE_PATH>/src/main
    ./omnia.sh --run repo_manager
    ```

=== "Using ansible-playbook"

    ```bash title="Run on: OIM host"
    source "$OMNIA_DATA_PATH/activate-omnia.sh"
    cd <OMNIA_SOURCE_PATH>/src/repo_manager/playbooks
    ansible-playbook repo_manager.yml
    ```

Repository Manager synchronizes the catalog-selected VAST content to Pulp and
publishes:

```text
$OMNIA_DATA_PATH/repo_manager/output/$OMNIA_PROJECT_NAME/repo_status.yml
```

Before building images, verify that `overall_status` is `success` and that
`repositories.<version>.<architecture>.vast.url` contains the generated Pulp
distribution URL.

### Step 8: Build the functional-group images

Run the Image Build Manager domain workflow. Its canonical entry point is
`src/image_build_manager/playbooks/image_build_manager.yml`; it invokes the
appropriate x86_64 and aarch64 build sub-playbooks for the selected catalog.

=== "Using omnia.sh (recommended)"

    ```bash title="Run on: OIM host"
    cd <OMNIA_SOURCE_PATH>/src/main
    ./omnia.sh --run image_build_manager
    ```

=== "Using ansible-playbook"

    ```bash title="Run on: OIM host"
    source "$OMNIA_DATA_PATH/activate-omnia.sh"
    cd <OMNIA_SOURCE_PATH>/src/image_build_manager/playbooks
    ansible-playbook image_build_manager.yml
    ```

Image Build Manager consumes `repo_status.yml` and publishes:

```text
$OMNIA_DATA_PATH/image_build_manager/output/$OMNIA_PROJECT_NAME/build_status.yml
```

Verify that `overall_status` is `success` and that the required functional-group
images reference their expected S3 artifacts.

### Step 9: Provision the nodes with Orchestrator

Complete the Orchestrator `precheck`, `prepare`, and `provision` workflows as
described in [Provision Nodes](../../HowTo/orchestrator/provision_nodes.md).
The canonical entry point is `src/orchestrator/playbooks/orchestrator.yml`.
Orchestrator consumes the successful `repo_status.yml` and `build_status.yml`
contracts and writes its results under:

```text
$OMNIA_DATA_PATH/orchestrator/output/$OMNIA_PROJECT_NAME/
```

Verify `orchestrator_status.yml` and `provisioning_report.yml` before validating
the VAST client on the target nodes.

## Next Steps

- [Configure Mounts](../../HowTo/orchestrator/configure_storage.md) -- Configure NFS and other storage mounts.

## Verification

After provisioning, verify that the VAST client is installed on the target nodes:

```bash title="Run on: target node"
rpm -qa | grep vast
mount | grep vast
```

Confirm that the VAST NFS mount is active and accessible.

## Troubleshooting

- **VAST repository is absent from `repo_status.yml`**: Verify that the selected
  catalog includes `vast_stack_driver_groupv1`, the `vast` URL is correct in
  `repo_manager_config.yml`, and the HTTP server hosting the repository is
  reachable. Then rerun Repository Manager.
- **VAST client is absent from the built image**: Verify that
  `repo_status.yml` and `build_status.yml` report `overall_status: success` and
  that the selected functional group includes the VAST software group.
- **VAST client installation fails**: Confirm that the VAST RPM package is
  compatible with the target operating-system version and architecture.

!!! info "Related References"

    - [Create Local Repositories](../../HowTo/repo_manager/configure_repos.md) -- Host and sync RPM repositories.
    - [Repo Manager Config](../../Reference/Configuration/repo_manager_config.md) -- User repository configuration parameters.
