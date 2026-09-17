# Image Build Manager Issues

Use this page to diagnose Image Build Manager input validation, repository,
image-build, S3, and aarch64 host failures.

## Input and playbook reference

Image Build Manager uses the following files. Replace `<project>` with
`OMNIA_PROJECT_NAME`; the default project is `project_default`.

| File | Location and purpose |
|---|---|
| `image_build_config.yml` | `<IMAGE_BUILD_MANAGER_DATA_PATH>/input/<project>/image_build_config.yml`; required domain configuration. When `IMAGE_BUILD_MANAGER_DATA_PATH` is not set, the domain root is `<OMNIA_DATA_PATH>/image_build_manager`. |
| `package_groups.yml` | `<IMAGE_BUILD_MANAGER_DATA_PATH>/input/<project>/package_groups.yml`; provides packages and functional groups when `functional_groups_source: "config"`. |
| Catalog JSON | Exact file selected by `CATALOG_FILE_PATH`; provides packages and functional layers when `functional_groups_source: "catalog"`. |
| `image_build_credentials.yml` | `<IMAGE_BUILD_MANAGER_DATA_PATH>/input/<project>/image_build_credentials.yml`; generated and encrypted during credential collection. Its Vault key is `.image_build_credentials_key` in the same directory. |
| `repo_status.yml` | Upstream Repo Manager output at the path configured by `repo_manager_output_path` in `image_build_config.yml`. |
| `build_status.yml` | `<IMAGE_BUILD_MANAGER_DATA_PATH>/output/<project>/build_status.yml`; generated after a successful build. |

The customer-facing playbook entry point is:

```text
<OMNIA_SOURCE_PATH>/src/image_build_manager/playbooks/image_build_manager.yml
```

Choose one execution method:

=== "Using omnia.sh (recommended)"

    ```bash title="Run on: OIM host"
    cd <OMNIA_SOURCE_PATH>/src/main
    ./omnia.sh --run image_build_manager --tags <tag>
    ```

=== "Using ansible-playbook"

    ```bash title="Run on: OIM host"
    source /opt/omnia/activate-omnia.sh
    cd <OMNIA_SOURCE_PATH>/src/image_build_manager
    ansible-playbook playbooks/image_build_manager.yml --tags <tag>
    ```

Supported troubleshooting tags include `precheck`, `validate`, `prepare`, and
`build`. Run one tag at a time. The top-level `image_build_manager.yml`
playbook imports the phase playbooks below `playbooks/build/`,
`playbooks/prepare/`, and the other phase directories.

## An input file is missing or rejected

???+ note "Symptom"

    Validation reports that `image_build_config.yml`, `package_groups.yml`, a
    catalog JSON file, or `repo_status.yml` cannot be found or is invalid.

??? note "Cause"

    - The Image Build Manager inputs were not staged for the current project.
    - `functional_groups_source` does not match the selected package source.
    - `CATALOG_FILE_PATH` is unset or does not identify an existing JSON file.
    - `repo_manager_output_path` does not identify the successful Repo Manager
      output for the current project.

??? note "Resolution"

    1. Confirm the active project and Image Build Manager data path:

        ```bash title="Run on: OIM host"
        printf 'Project: %s\n' "${OMNIA_PROJECT_NAME:-project_default}"
        printf 'Image Build Manager path: %s\n' \
          "${IMAGE_BUILD_MANAGER_DATA_PATH:-${OMNIA_DATA_PATH}/image_build_manager}"
        ```

    2. If initialization did not stage the inputs, run it from Main:

        ```bash title="Run on: OIM host"
        cd <OMNIA_SOURCE_PATH>/src/main
        ./omnia.sh --init image_build_manager
        ```

    3. In the staged `image_build_config.yml`, set
       `functional_groups_source` to `catalog` or `config`:

        - For `catalog`, follow
          [Select or update the catalog](../../HowTo/main/update_catalog.md)
          and verify `CATALOG_FILE_PATH`.
        - For `config`, verify `package_groups.yml` in the same runtime project
          input directory.

    4. Confirm that `repo_manager_output_path` identifies the Repo Manager
       `repo_status.yml` for the current project.

    5. Validate the corrected inputs:

        === "Using omnia.sh (recommended)"

            ```bash title="Run on: OIM host"
            cd <OMNIA_SOURCE_PATH>/src/main
            ./omnia.sh --run image_build_manager --tags validate
            ```

        === "Using ansible-playbook"

            ```bash title="Run on: OIM host"
            source /opt/omnia/activate-omnia.sh
            cd <OMNIA_SOURCE_PATH>/src/image_build_manager
            ansible-playbook playbooks/image_build_manager.yml --tags validate
            ```

## No functional groups are selected

???+ note "Symptom"

    The build reports that no functional groups were found for `x86_64` or
    `aarch64`, or the expected functional-group image is absent from
    `build_status.yml`.

??? note "Cause"

    - In catalog mode, the selected catalog has no functional layer ending in
      the target `_x86_64` or `_aarch64` suffix.
    - In config mode, `package_groups.yml` has no matching key under
      `functional_groups`.
    - All matching catalog layers begin with `baseos`, so the catalog parser
      classifies them as base-image layers instead of functional-group images.

??? note "Resolution"

    1. Check `functional_groups_source` in the staged
       `image_build_config.yml`.
    2. For catalog mode, verify the `catalog.functionallayer[].name` values in
       the file selected by `CATALOG_FILE_PATH`.
    3. For config mode, verify the keys under `functional_groups` in the staged
       `package_groups.yml`.
    4. Run validation, and then rerun the build:

        === "Using omnia.sh (recommended)"

            ```bash title="Run on: OIM host"
            cd <OMNIA_SOURCE_PATH>/src/main
            ./omnia.sh --run image_build_manager --tags validate
            ./omnia.sh --run image_build_manager --tags build
            ```

        === "Using ansible-playbook"

            ```bash title="Run on: OIM host"
            source /opt/omnia/activate-omnia.sh
            cd <OMNIA_SOURCE_PATH>/src/image_build_manager
            ansible-playbook playbooks/image_build_manager.yml --tags validate
            ansible-playbook playbooks/image_build_manager.yml --tags build
            ```

## Repository input or package resolution fails

???+ note "Symptom"

    - `repo_status.yml` is missing or rejected.
    - A repository URL is unreachable.
    - A build reports `No match for argument: <package-name>`.
    - The Repo Manager certificate referenced by `repo_status.yml` does not
      exist.

??? note "Cause"

    Repo Manager did not publish a successful contract for the selected
    catalog, or the selected package is not available through one of the
    repository URLs in that contract.

??? note "Resolution"

    1. Open the `repo_status.yml` identified by `repo_manager_output_path` and
       confirm that `overall_status` is `success`.
    2. Confirm that `repositories` contains a non-empty URL for at least one
       supported architecture and that each required URL is reachable from
       the build host.
    3. If `repo_manager.certificates.server_crt` is set, confirm that the
       referenced certificate exists.
    4. Correct or synchronize the package through
       [Repo Manager](../../HowTo/repo_manager/configure_repos.md), and then
       regenerate `repo_status.yml`.
    5. Rerun the Image Build Manager build phase:

        === "Using omnia.sh (recommended)"

            ```bash title="Run on: OIM host"
            cd <OMNIA_SOURCE_PATH>/src/main
            ./omnia.sh --run image_build_manager --tags build
            ```

        === "Using ansible-playbook"

            ```bash title="Run on: OIM host"
            source /opt/omnia/activate-omnia.sh
            cd <OMNIA_SOURCE_PATH>/src/image_build_manager
            ansible-playbook playbooks/image_build_manager.yml --tags build
            ```

## S3 upload fails

???+ note "Symptom"

    The `build` phase fails while uploading an image, or expected artifacts do
    not appear in the `boot-images` bucket.

??? note "Cause"

    - The configured S3 endpoint is unavailable.
    - The generated `image_build_credentials.yml` does not contain valid S3
      credentials.
    - The storage backend does not have sufficient capacity.

??? note "Resolution"

    1. List the configured S3 buckets and image objects:

        ```bash title="Run on: OIM host"
        s3cmd ls
        s3cmd ls -r s3://boot-images
        ```

    2. When `s3_configurations.provider` is `minio`, verify the local service:

        ```bash title="Run on: OIM host"
        systemctl status minio.service
        ```

       MinIO is not deployed when the provider is `powerscale`; verify the
       configured external `endpoint_url` instead.

    3. Correct the endpoint, credentials, service, or storage issue. Run the
       `prepare` tag when the local service or credentials must be refreshed:

        === "Using omnia.sh (recommended)"

            ```bash title="Run on: OIM host"
            cd <OMNIA_SOURCE_PATH>/src/main
            ./omnia.sh --run image_build_manager --tags prepare
            ```

        === "Using ansible-playbook"

            ```bash title="Run on: OIM host"
            source /opt/omnia/activate-omnia.sh
            cd <OMNIA_SOURCE_PATH>/src/image_build_manager
            ansible-playbook playbooks/image_build_manager.yml --tags prepare
            ```

    4. Rerun the build:

        === "Using omnia.sh (recommended)"

            ```bash title="Run on: OIM host"
            cd <OMNIA_SOURCE_PATH>/src/main
            ./omnia.sh --run image_build_manager --tags build
            ```

        === "Using ansible-playbook"

            ```bash title="Run on: OIM host"
            source /opt/omnia/activate-omnia.sh
            cd <OMNIA_SOURCE_PATH>/src/image_build_manager
            ansible-playbook playbooks/image_build_manager.yml --tags build
            ```

## Kernel or image artifact is not found

???+ note "Symptom"

    Orchestrator cannot find the kernel, initramfs, or root filesystem recorded
    for a functional group.

??? note "Cause"

    - The Image Build Manager build did not complete successfully.
    - The S3 objects were removed or are not reachable.
    - The expected package or functional group was not resolved from the
      selected catalog or `package_groups.yml`.

??? note "Resolution"

    1. Inspect the current `build_status.yml`. Each `kernel`, `initrd`, and
       `image` value is the exact endpoint-relative S3 object path produced by
       the selected image builder.
    2. Join the configured `s3_configurations.endpoint_url` and the recorded
       artifact path once, without adding another bucket name or `s3://`
       prefix.
    3. Confirm that the recorded objects exist in `boot-images`:

        ```bash title="Run on: OIM host"
        s3cmd ls -r s3://boot-images
        ```

    4. Correct the package, repository, or functional-group selection, and
       rerun the build through the top-level playbook:

        === "Using omnia.sh (recommended)"

            ```bash title="Run on: OIM host"
            cd <OMNIA_SOURCE_PATH>/src/main
            ./omnia.sh --run image_build_manager --tags build
            ```

        === "Using ansible-playbook"

            ```bash title="Run on: OIM host"
            source /opt/omnia/activate-omnia.sh
            cd <OMNIA_SOURCE_PATH>/src/image_build_manager
            ansible-playbook playbooks/image_build_manager.yml --tags build
            ```

## aarch64 image build is skipped or fails

???+ note "Symptom"

    - The playbook reports that `aarch64_inventory_host_ip` is not set and
      skips the aarch64 build.
    - The configured aarch64 host is unreachable.
    - Passwordless SSH setup or the builder-image or `regctl` transfer fails.

??? note "Cause"

    The ARM build-host settings or credentials are missing, the host is not
    reachable, or neither the OIM nor the ARM host can obtain a required
    artifact.

??? note "Resolution"

    1. In the staged `image_build_config.yml`, set
       `aarch64_inventory_host_ip` and `aarch64_ssh_user`. An empty IP disables
       aarch64 builds.
    2. Confirm that the host responds to ping, accepts SSH connections on port
       22, and reports `aarch64` from `uname -m`.
    3. Run `prepare` to collect `aarch64_ssh_password` in the generated
       `image_build_credentials.yml`:

        === "Using omnia.sh (recommended)"

            ```bash title="Run on: OIM host"
            cd <OMNIA_SOURCE_PATH>/src/main
            ./omnia.sh --run image_build_manager --tags prepare
            ```

        === "Using ansible-playbook"

            ```bash title="Run on: OIM host"
            source /opt/omnia/activate-omnia.sh
            cd <OMNIA_SOURCE_PATH>/src/image_build_manager
            ansible-playbook playbooks/image_build_manager.yml --tags prepare
            ```

    4. Confirm that the OIM Repo Manager is reachable from the ARM host or that
       the fallback upstream sources are reachable.
    5. Rerun the build. The build phase uses the collected password to
       configure SSH connectivity:

        === "Using omnia.sh (recommended)"

            ```bash title="Run on: OIM host"
            cd <OMNIA_SOURCE_PATH>/src/main
            ./omnia.sh --run image_build_manager --tags build
            ```

        === "Using ansible-playbook"

            ```bash title="Run on: OIM host"
            source /opt/omnia/activate-omnia.sh
            cd <OMNIA_SOURCE_PATH>/src/image_build_manager
            ansible-playbook playbooks/image_build_manager.yml --tags build
            ```

    The playbook creates the `admin_aarch64` inventory group dynamically from
    `aarch64_inventory_host_ip`. Do not create or pass a separate inventory
    file for the ARM host.

## Local registry reports a TLS error

???+ note "Symptom"

    `regctl` reports `http: server gave HTTP response to HTTPS client`.

??? note "Cause"

    The local OCI registry listens on HTTP port 5000, but the client attempted
    to use HTTPS.

??? note "Resolution"

    Configure `regctl` to use HTTP for the local registry:

    ```bash title="Run on: OIM host"
    /usr/local/bin/regctl registry set --tls disabled \
      <SYSTEM_ADMIN_NIC_IPV4>:5000
    ```

## Logs and related information

| Information | Location |
|---|---|
| Main playbook log | `/var/log/omnia/image_build_manager/image_build_manager.log` |
| Runtime and per-image logs | `<IMAGE_BUILD_MANAGER_DATA_PATH>/log/<project>/` |
| Input-validation log | `<IMAGE_BUILD_MANAGER_DATA_PATH>/log/<project>/image_build_validation_<project>.log` |
| Image Build Manager procedure | [Build OS Images](../../HowTo/image_build_manager/build_images.md) |
| Catalog selection | [Select or update the catalog](../../HowTo/main/update_catalog.md) |
| Repository preparation | [Create Local Repositories](../../HowTo/repo_manager/configure_repos.md) |
