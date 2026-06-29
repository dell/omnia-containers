
# Provisioning Issues


Issues related to PXE booting, node discovery, cloud-init configuration, and
the `discovery.yml` playbook.

## PXE boot failures


### NIC not set to PXE boot


???+ note "Symptom"

    The target node does not attempt a network boot. It boots directly to the
    local disk or enters the BIOS setup instead of requesting a PXE image from
    the OIM.

??? note "Cause"

    The node's BIOS/UEFI boot order does not include PXE/network boot, or PXE
    is disabled on the NIC connected to the admin network.

??? note "Resolution"

    1. Enter the node's BIOS/UEFI setup (press F2 during POST on Dell PowerEdge
       servers).
    2. Navigate to **System BIOS > Network Settings**.
    3. Enable **PXE Boot** on the NIC connected to the admin network.
    4. Navigate to **Boot Settings > BIOS Boot Settings** (or **UEFI Boot
       Settings**).
    5. Set **Network Boot** (PXE) as the first boot option.
    6. Save and exit BIOS. The node should now attempt PXE boot on the next
       restart.

    Alternatively, use `racadm` to configure remotely:

    ```bash
    racadm set NIC.NICConfig.1.LegacyBootProto PXE
    racadm set BIOS.BiosBootSettings.BootSeq NIC.Slot.1-1
    ```


### Wrong MAC address in mapping file


???+ note "Symptom"

    The node PXE boots but does not receive an IP address, or it receives an IP
    but is not recognized by OpenCHAMI.

??? note "Cause"

    The MAC address in `/omnia/input/mapping_file.csv` does not match the
    actual MAC address of the NIC being used for PXE boot.

??? note "Resolution"

    1. Verify the correct MAC address from iDRAC or the node's BIOS:

       ```bash
       # From iDRAC (using racadm)
       racadm getsysinfo | grep "MAC Address"
       ```


    2. Update the mapping file with the correct MAC:

       ```text
       # /omnia/input/mapping_file.csv
       AA:BB:CC:DD:EE:FF,compute-01,10.5.0.101
       ```


    3. Re-run the discovery playbook:

       ```bash
       ssh omnia_core
       cd /omnia
       ansible-playbook playbooks/discovery.yml
       ```


### DHCP not serving IP addresses


???+ note "Symptom"

    Nodes attempt PXE boot but fail with a DHCP timeout error:

    ```text
    PXE-E51: No DHCP or proxyDHCP offers were received
    ```


??? note "Cause"

    - The CoreDHCP container on the OIM is not running.
    - The DHCP range is exhausted.
    - A network misconfiguration prevents DHCP broadcasts from reaching the OIM.
    - Another DHCP server on the same network is interfering.

??? note "Resolution"

    1. Verify the CoreDHCP container is running:

       ```bash
       podman ps | grep coredhcp
       ```


       If it is not running, start it:

       ```bash
       podman start coredhcp
       ```


    2. Check CoreDHCP logs for errors:

       ```bash
       podman logs coredhcp
       ```


    3. Verify no rogue DHCP server exists on the admin network:

       ```bash
       nmap --script broadcast-dhcp-discover -e <admin_nic>
       ```


    4. Ensure the OIM's admin NIC is on the correct VLAN and subnet.

### TFTP timeout during PXE boot


???+ note "Symptom"

    The node receives a DHCP lease but fails to download the boot image:

    ```text
    PXE-E32: TFTP open timeout
    PXE-T02: TFTP packet timeout
    ```


??? note "Cause"

    - The TFTP service on the OIM is not running.
    - Firewall rules on the OIM are blocking TFTP traffic (UDP port 69).
    - The TFTP root directory does not contain the expected boot files.

??? note "Resolution"

    1. Verify the TFTP container is running:

       ```bash
       podman ps | grep tftp
       ```


    2. Check firewall rules:

       ```bash
       firewall-cmd --list-all | grep tftp
       ```


       If TFTP is not allowed:

       ```bash
       firewall-cmd --permanent --add-service=tftp
       firewall-cmd --reload
       ```


    3. Verify boot files exist in the TFTP root:

       ```bash
       ls /var/lib/tftpboot/
       ```


## cloud-init issues


???+ note "Symptom"

    Nodes boot the OS successfully but post-boot configuration fails. The node
    is accessible via console but network settings, hostname, or SSH keys are
    not configured correctly.

??? note "Cause"

    - The cloud-init data source is not configured.
    - The cloud-init configuration file has syntax errors.
    - The cloud-init service was disabled or removed from the OS image.

??? note "Resolution"

    1. Check cloud-init status on the affected node:

       ```bash
       cloud-init status --long
       ```


    2. Review cloud-init logs:

       ```bash
       cat /var/log/cloud-init.log
       cat /var/log/cloud-init-output.log
       ```


    3. Verify the data source configuration:

       ```bash
       cat /etc/cloud/cloud.cfg.d/
       ```


    4. If cloud-init was disabled, re-enable it:

       ```bash
       systemctl enable cloud-init
       cloud-init clean
       reboot
       ```


## `discovery.yml` failures


???+ note "Symptom"

    The `discovery.yml` playbook fails with errors related to OpenCHAMI, BMC
    connectivity, or inventory population.

??? note "Cause"

    - OpenCHAMI services (SMD, BSS) are not running on the OIM.
    - BMC/iDRAC credentials are incorrect.
    - The BMC network is unreachable from the OIM.

??? note "Resolution"

    1. Verify OpenCHAMI services are running:

       ```bash
       podman ps | grep ochami
       ```


    2. Test BMC connectivity:

       ```bash
       # Ping the BMC IP
       ping <bmc_ip>

       # Test Redfish API access
       curl -k -u <user>:<pass> https://<bmc_ip>/redfish/v1/Systems
       ```


    3. Verify BMC credentials in the configuration:

       ```bash
       ssh omnia_core
       ansible-vault view /omnia/input/credentials.yml
       ```


    4. Check discovery logs for detailed errors:

       ```bash
       cat /opt/omnia/log/core/playbooks/discovery.log
       ```


## Nodes not appearing after discovery


???+ note "Symptom"

    After running `discovery.yml` successfully, the expected nodes do not
    appear in `ochami-cli smd components list` or `sinfo`.

??? note "Cause"

    - The node's BMC did not respond during the discovery window.
    - The node's MAC address does not match any entry in the mapping file.
    - The node booted but failed cloud-init, so it did not register with the
      OIM.

??? note "Resolution"

    1. Check the OpenCHAMI inventory:

       ```bash
       ssh omnia_core
       ochami-cli smd components list
       ```


    2. Verify the node's BMC is responsive:

       ```bash
       ping <bmc_ip>
       curl -k -u <user>:<pass> https://<bmc_ip>/redfish/v1/Systems
       ```


    3. Re-run discovery for the specific node by power-cycling it via iDRAC:

       ```bash
       racadm -r <bmc_ip> -u <user> -p <pass> serveraction powercycle
       ```


    4. Monitor the discovery log in real time:

       ```bash
       tail -f /opt/omnia/log/core/playbooks/discovery.log
       ```


!!! info

    - [Discover Nodes](../HowTo/Setup/discover_nodes.md) -- Full node discovery procedure.
    - [Pxe Boot Nodes](../HowTo/Setup/pxe_boot_nodes.md) -- PXE boot configuration guide.
    - [Log Management](../Operations/log_management.md) -- Log locations for deeper diagnosis.
