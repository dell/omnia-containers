# Configure Kernel Version Override

## Overview

Use `kernel_version_override` to make Orchestrator select boot-image artifacts
whose kernel path contains a specific kernel version. The setting applies to
both `x86_64` and `aarch64` functional groups.

When the value is empty, Orchestrator uses the available image selected by its
normal image-validation flow. When the value is set, validation fails unless
every applicable functional-group image in `build_status.yml` has a matching
kernel artifact in S3.

The setting selects an image already produced by Image Build Manager. It does
not install a kernel package or create a new image.

## Prerequisites

- Complete [Repository Manager](../repo_manager/configure_repos.md) with the
  kernel packages required by the selected catalog or package groups.
- Complete [Image Build Manager](../image_build_manager/build_images.md) and
  confirm that its `build_status.yml` reports `overall_status: success`.
- Place `orchestrator_config.yml` in the active project's Orchestrator input
  directory.
- Know the exact kernel version contained in the required S3 kernel artifact.

## Procedure

1. If the required kernel is not already represented in `build_status.yml`,
   update the source repository or catalog configuration, rerun Repo Manager,
   and rebuild the affected functional-group images. Follow the linked module
   guides rather than editing their generated status files.

2. Edit the Orchestrator configuration:

    ```bash title="Run on: OIM"
    source /etc/profile.d/omnia-env.sh
    orchestrator_path="${OMNIA_DATA_PATH}/orchestrator"
    source "$OMNIA_DATA_PATH/activate-omnia.sh"
    vi "$orchestrator_path/input/$OMNIA_PROJECT_NAME/orchestrator_config.yml"
    ```

3. Set the exact version string. The accepted format begins with three numeric
   components followed by a hyphen and release suffix:

    ```yaml title="File: orchestrator_config.yml"
    kernel_version_override: "6.12.0-55.76.1.el10_0"
    ```

    To return to automatic image selection, use:

    ```yaml
    kernel_version_override: ""
    ```

4. Validate the Orchestrator input and upstream image output:

    === "Using omnia.sh (recommended)"

        ```bash title="Run on: OIM"
        cd <OMNIA_SOURCE_PATH>/src/main
        ./omnia.sh --run orchestrator --tags validate
        ./omnia.sh --run orchestrator --tags precheck
        ```

    === "Using ansible-playbook"

        ```bash title="Run on: OIM"
        source /opt/omnia/activate-omnia.sh
        cd <OMNIA_SOURCE_PATH>/src/orchestrator/playbooks
        ansible-playbook orchestrator.yml --tags validate
        ansible-playbook orchestrator.yml --tags precheck
        ```

5. Provision and PXE boot the nodes:

    === "Using omnia.sh (recommended)"

        ```bash title="Run on: OIM"
        cd <OMNIA_SOURCE_PATH>/src/main
        ./omnia.sh --run orchestrator --tags provision
        ./omnia.sh --run orchestrator --tags pxeboot
        ```

    === "Using ansible-playbook"

        ```bash title="Run on: OIM"
        source /opt/omnia/activate-omnia.sh
        cd <OMNIA_SOURCE_PATH>/src/orchestrator/playbooks
        ansible-playbook orchestrator.yml --tags provision
        ansible-playbook orchestrator.yml --tags pxeboot
        ```

## Verification

On each provisioned node, verify the running kernel:

```bash title="Run on: provisioned node"
uname -r
```

The result must match `kernel_version_override`. Also confirm that the active
project's Orchestrator `orchestrator_status.yml` reports a successful
provisioning run.

## Next steps

- Continue with [Provision Nodes](provision_nodes.md) when other provisioning
  options still need to be configured.
- Use [Configure PXE Boot](configure_pxe_boot.md) when PXE timing or boot-target
  behavior needs adjustment.

## Troubleshooting

- **The value fails input validation**: Use the format
  `X.Y.Z-release-suffix`, such as `6.12.0-55.76.1.el10_0`.
- **The override does not match an image**: Inspect Image Build Manager's
  `build_status.yml` and its S3 kernel paths. Rebuild the images when the
  required version is absent; do not edit `build_status.yml` manually.
- **Only one architecture matches**: Build the required image for every
  architecture present in the PXE mapping, because the override applies to
  both supported architectures.
- **Nodes still run the earlier kernel**: Confirm that provisioning and the PXE
  boot workflow both completed after the configuration change.
