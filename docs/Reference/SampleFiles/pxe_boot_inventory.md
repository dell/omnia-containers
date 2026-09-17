
# Retry inventory for the PXE boot playbook

The PXE boot playbook normally reads `pxe_mapping_file.csv`. Use a custom CSV
inventory to retry or operate on a subset of mapped nodes. An Ansible INI
inventory and a `[bmc]` host group are not accepted by this input.

## PXE boot inventory

Retain the same named columns as `pxe_mapping_file.csv`. Column order is not
significant, but the header names are.

```csv title="File: pxe_boot_inventory.csv"
FUNCTIONAL_GROUP_NAME,GROUP_NAME,SERVICE_TAG,PARENT_SERVICE_TAG,HOSTNAME,ADMIN_MAC,ADMIN_IP,BMC_MAC,BMC_IP,IB_NIC_NAME,IB_IP
slurm_node_rhel_10_0_x86_64,grp1,ABC1234,,nid001,02:00:00:00:01:01,172.16.107.51,02:00:00:00:02:01,172.17.107.51,,
service_kube_node_rhel_10_0_x86_64,grp2,DEF5678,,nid002,02:00:00:00:01:02,172.16.107.52,02:00:00:00:02:02,172.17.107.52,,
```

Run the retry through the Orchestrator entry point:

=== "Using omnia.sh (recommended)"

    ```bash title="Run on: OIM host"
    cd <OMNIA_SOURCE_PATH>/src/main
    ./omnia.sh --run orchestrator --tags pxeboot \
      -e pxeboot_inventory=/absolute/path/pxe_boot_inventory.csv
    ```

=== "Using ansible-playbook"

    ```bash title="Run on: OIM host"
    source /opt/omnia/activate-omnia.sh
    cd <OMNIA_SOURCE_PATH>/src/orchestrator/playbooks
    ansible-playbook orchestrator.yml --tags pxeboot \
      -e pxeboot_inventory=/absolute/path/pxe_boot_inventory.csv
    ```

The custom file must contain only nodes already prepared for provisioning. It
does not replace the project PXE mapping or rerun prior phases.

!!! info

    - [PXE boot playbook](../../HowTo/orchestrator/configure_pxe_boot.md) -- PXE boot playbook documentation

















