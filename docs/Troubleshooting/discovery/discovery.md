# Discovery issues

Use the Ansible output and `/var/log/omnia/discovery/discovery.log` for every
Discovery failure. The OME execution role also writes
`$OMNIA_DATA_PATH/discovery/output/$OMNIA_PROJECT_NAME/discovery_status.yml`.
Failures during setup, validation, or credential handling occur before that
status file is updated, so an existing file can describe an earlier run.

## Configuration validation fails

???+ note "Symptom"

    Discovery reports an invalid or missing `discovery_config.yml`.

??? note "Resolution"

    - Confirm that the file is in the Discovery project input directory.
    - Set `ome_ip` to a valid, non-loopback OME IPv4 address.
    - Correct YAML errors and rerun
      `./omnia.sh --run discovery --tags validate` from `src/main`.

## OME is unreachable or authentication fails

???+ note "Symptom"

    Discovery cannot reach OME on port 443 or the OME API rejects the session.

??? note "Resolution"

    - Verify `ome_ip` and connectivity from the OIM to `<ome_ip>:443`.
    - Confirm that OME is running and accessible.
    - Test the OME API endpoint from the OIM without placing credentials on the
      command line:

        ```bash title="Run on: OIM host"
        curl --insecure --silent --show-error --connect-timeout 10 \
          --output /dev/null --write-out "HTTP status: %{http_code}\n" \
          https://<ome-ip>/api/SessionService/Sessions
        ```

      Any HTTP status confirms that the endpoint is reachable. An `HTTP
      status: 000`, timeout, refusal, or TLS error indicates a connectivity or
      certificate problem. Do not add the OME username or password to this
      diagnostic command.
    - Correct the OME username or password in the Discovery credential
      workflow. Rerun `./omnia.sh --run discovery --tags credentials` if a
      stored value must be updated.
    - Keep `.discovery_credentials_key` with an encrypted
      `discovery_credentials.yml`; the files are a matching pair.
    - Review the most recent log messages:

        ```bash title="Run on: OIM host"
        tail -n 100 /var/log/omnia/discovery/discovery.log
        ```

## No servers are discovered

???+ note "Cause"

    OME did not return a server device of type `1000` with a nonempty service
    tag.

??? note "Resolution"

    Confirm that the target devices are managed and visible in OME, are
    classified as servers, and report their service tags. Discovery reads the
    existing OME inventory; it does not add devices to OME.

## A server is missing from the mapping

???+ note "Cause"

    The server is assigned to an unsupported nonempty OME static group. Such a
    server remains in the discovery report but is skipped in the mapping.

??? note "Resolution"

    Assign the server to one of the exact supported groups listed in [Plan OME
    static groups](../../HowTo/discovery/discover_nodes.md#plan-ome-static-groups),
    or remove the assignment to use the current default group. Ensure that the
    server belongs to no more than one processed OME group.

## iDRAC hostname, group, or parent values are incorrect

???+ note "Resolution"

    - In OME, inspect the server's iDRAC instrumentation name, DNS name, and
      device name. Discovery uses the first available value in that order.
    - Make the selected OME-reported value contain an `SU...R...` sequence,
      such as `SU1R2OU1C5`. Otherwise, Discovery uses `grp0`. Correct the iDRAC
      hostname, refresh the OME inventory, and rerun Discovery.
    - Do not use the generated `HOSTNAME` to diagnose this value. Discovery
      generates `HOSTNAME` as an `nid` sequence and derives only `GROUP_NAME`
      from the OME-reported iDRAC hostname.
    - Review and correct optional `PARENT_SERVICE_TAG` metadata before handing
      the generated mapping to Orchestrator. Orchestrator does not require it
      or validate it against `GROUP_NAME`.
    - See [Plan iDRAC
      hostnames](../../HowTo/discovery/discover_nodes.md#plan-idrac-hostnames)
      for the complete naming convention.

## Ethernet NIC MAC or derived IP values are incorrect

???+ note "Resolution"

    - Find the service tag in the timestamped discovery report and inspect its
      Ethernet MAC and link-status values.
    - In OME, verify the Ethernet NIC order, current MAC addresses, and link
      states. Discovery prefers the first usable non-iDRAC, non-InfiniBand
      Ethernet port reported as `Up` and falls back to the first usable port.
    - For an unexpected or missing MAC, check the cable, switch port, and
      server BIOS/iDRAC NIC settings. Refresh the server inventory in OME and
      confirm the intended port is visible before rerunning Discovery.
    - If the primary server network-interface inventory has no usable MAC,
      Discovery attempts the OME `deviceNics` inventory. A blank `ADMIN_MAC`
      means neither inventory returned a usable Ethernet MAC.
    - Discovery derives the admin and InfiniBand addresses from the first two
      subnet octets and the final two BMC-address octets. The Discovery
      validator does not validate `network_spec.yml`.
    - See [The admin MAC address is unexpected or
      empty](../../HowTo/discovery/discover_nodes.md#the-admin-mac-address-is-unexpected-or-empty)
      for the detailed verification sequence.

## Discovery is blocked by the upgrade lock

???+ note "Resolution"

    Complete the Omnia upgrade before rerunning Discovery. Normal execution is
    blocked while `/opt/omnia/.data/upgrade_in_progress.lock` exists.

!!! info "Related documentation"

    - [Discover nodes using OME](../../HowTo/discovery/discover_nodes.md)
    - [Create a mapping file](../../HowTo/discovery/create_mapping_file.md)
    - [Discovery contract](../../Reference/domain_contracts/discovery_contract.md)
