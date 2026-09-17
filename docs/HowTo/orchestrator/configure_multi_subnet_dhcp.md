# Configure Multi-Subnet DHCP

## Overview

Orchestrator can serve PXE leases to routed admin-network subnets through DHCP
relay agents. Each entry under `Networks.admin_network.additional_subnets` in
`network_spec.yml` defines the remote subnet, its prefix length, the router
address supplied by DHCP, and its dynamic address range.

The primary admin-network settings remain under `admin_network`. Additional
subnets extend that configuration; they do not define additional OIM
interfaces or BMC networks.

## Prerequisites

- Configure a DHCP relay on every remote subnet to forward requests to the OIM
  admin-network address.
- Ensure routing and firewall policy allow DHCP relay traffic between each
  subnet and the OIM.
- Reserve non-overlapping dynamic ranges that exclude gateways, statically
  assigned node addresses, and infrastructure addresses.
- Ensure the PXE mapping file uses admin addresses from the configured primary
  or additional subnets.

## Procedure

1. Edit the shared network specification:

    ```bash title="Run on: OIM"
    source /etc/profile.d/omnia-env.sh
    orchestrator_path="${ORCHESTRATOR_DATA_PATH:-${OMNIA_DATA_PATH}/orchestrator}"
    source "$OMNIA_DATA_PATH/activate-omnia.sh"
    vi "$orchestrator_path/input/$OMNIA_PROJECT_NAME/network_spec.yml"
    ```

2. Add each routed subnet beneath `admin_network.additional_subnets`:

    ```yaml title="File: network_spec.yml"
    Networks:
      - admin_network:
          primary_oim_admin_ip: "10.40.1.111"
          primary_oim_bmc_ip: ""
          oim_nic_name: "eno1"
          subnet: "10.40.1.0"
          netmask_bits: "24"
          dynamic_range: "10.40.1.201-10.40.1.250"
          router: "10.40.1.1"
          dns: []
          ntp_servers: []
          additional_subnets:
            - subnet: "10.40.2.0"
              netmask_bits: "24"
              router: "10.40.2.1"
              dynamic_range: "10.40.2.190-10.40.2.200"
            - subnet: "10.40.3.0"
              netmask_bits: "24"
              router: "10.40.3.1"
              dynamic_range: "10.40.3.190-10.40.3.200"
    ```

    Use `additional_subnets: []` when no relay-served subnet is required. Omit
    the `ib_network` list item when InfiniBand is unused; if it is present, its
    `subnet` and `netmask_bits` values cannot be empty.

3. Validate the Orchestrator inputs:

    === "Using omnia.sh (recommended)"

        ```bash title="Run on: OIM"
        cd <OMNIA_SOURCE_PATH>/src/main
        ./omnia.sh --run orchestrator --tags validate
        ./omnia.sh --run orchestrator --tags precheck
        ```

    === "Using ansible-playbook"

        ```bash title="Run on: OIM"
        source /opt/omnia/activate-omnia.sh
        cd <OMNIA_SOURCE_PATH>/src/orchestrator
        ansible-playbook playbooks/orchestrator.yml --tags validate
        ansible-playbook playbooks/orchestrator.yml --tags precheck
        ```

4. Deploy or refresh OpenCHAMI so CoreDHCP receives the new configuration:

    === "Using omnia.sh (recommended)"

        ```bash title="Run on: OIM"
        cd <OMNIA_SOURCE_PATH>/src/main
        ./omnia.sh --run orchestrator --tags prepare
        ```

    === "Using ansible-playbook"

        ```bash title="Run on: OIM"
        source /opt/omnia/activate-omnia.sh
        cd <OMNIA_SOURCE_PATH>/src/orchestrator
        ansible-playbook playbooks/orchestrator.yml --tags prepare
        ```

## Verification

- Confirm the validation and precheck runs complete without subnet or range
  errors.
- Inspect the CoreDHCP service logs and confirm that each configured subnet is
  loaded:

    ```bash title="Run on: OIM"
    podman logs coresmd-coredhcp
    ```

- PXE boot one node on each routed subnet and confirm it receives an address
  from that subnet's configured `dynamic_range`.

## Next steps

- [Configure PXE Boot](configure_pxe_boot.md) for the server restart and boot
  workflow.
- Review the [Network Spec reference](../../Reference/Configuration/network_spec.md)
  for the complete shared input schema.

## Troubleshooting

- **Remote nodes receive no lease**: Verify the switch or router DHCP-relay
  destination and confirm that the relay can reach the OIM.
- **A node receives an address from the wrong range**: Verify the relay gateway
  address and the corresponding `subnet`, `netmask_bits`, and `router` entry.
- **Orchestrator rejects the file**: Confirm that `additional_subnets` is nested
  under `admin_network` and that every entry contains all four required fields.
- **CoreDHCP does not show the new subnet**: Rerun the Orchestrator `prepare`
  tag and inspect `journalctl -u coresmd-coredhcp` and the container logs.
