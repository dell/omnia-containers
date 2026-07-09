
# Preparing aarch64 Node

Before building aarch64 compute images with `build_image_aarch64.yml`,
you must manually install RHEL 10 on one aarch64 bare-metal node.


## Prerequisites

- A disk is available to the aarch64 node for OS installation.
- The aarch64 node is network-accessible from the OIM.


## Procedure

1. **Install RHEL 10** on one of the aarch64 nodes with root password
   enabled.

    !!! warning

        - The root password must be at least 8 characters long, contain
          alphanumeric characters, and must **not** include commas (`,`),
          hyphens (`-`), single quotes (`'`), double quotes (`"`), or
          backslashes (`\`).
        - The password set during RHEL installation must match the
          `provision_password` supplied when running `discovery.yml`.

2. **Create an inventory file** with the aarch64 node admin IP:

    ```ini title="Example: /omnia/build_image_aarch64/inventory/admin_aarch64"
    [admin_aarch64]
    <aarch64_node_admin_ip>
    ```

    Replace `<aarch64_node_admin_ip>` with the actual admin IP address
    of the node where RHEL 10 was installed.
