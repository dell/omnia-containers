# Copyright 2026 Dell Inc. or its subsidiaries. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Network interface and connectivity functions for OIM prerequisite checks."""

from typing import Dict, List

from ...core.formatting import log as _log
from ..messages.oim_prereq_msgs import OIM_PREREQ_MSGS
from ..vars.oim_prereq_vars import OIM_PREREQ_VARS, OMNIA_TEST_CONFIG_PATH
from .system import run_command, run_shell


def get_interface_info(interface_name: str) -> Dict:
    """Get info for a specific interface."""
    info = {"name": interface_name, "exists": False, "state": "", "ip": ""}

    # Check if interface exists
    rc, state_out, _ = run_shell(f"cat /sys/class/net/{interface_name}/operstate 2>/dev/null")
    if rc == 0:
        info["exists"] = True
        info["state"] = state_out.strip()

    # Get IP address
    rc, ip_out, _ = run_shell(f"ip -4 addr show {interface_name} 2>/dev/null | "
                              f"grep inet | awk '{{print $2}}'")
    if rc == 0 and ip_out:
        info["ip"] = ip_out.split("\n")[0]

    return info


def get_network_interfaces() -> List[Dict]:
    """Get list of all network interfaces."""
    interfaces = []
    rc, stdout, _ = run_shell("ls /sys/class/net/ 2>/dev/null")
    if rc == 0:
        for iface in stdout.split():
            if iface and iface != "lo":
                interfaces.append(get_interface_info(iface))
    return interfaces


def validate_network_interfaces() -> Dict:
    """Validate PXE and Public interfaces are available and UP."""
    _log("Validating network interfaces...", "INFO")
    pxe_iface = OIM_PREREQ_VARS["pxe_interface"]
    public_iface = OIM_PREREQ_VARS["public_interface"]

    results = {"passed": True, "checks": [], "interfaces": []}

    # Check PXE interface
    if pxe_iface:
        pxe_info = get_interface_info(pxe_iface)
        results["interfaces"].append(pxe_info)

        if not pxe_info["exists"]:
            results["passed"] = False
            results["checks"].append({
                "name": "pxe_interface",
                "passed": False,
                "message": OIM_PREREQ_MSGS["iface_pxe_not_found"].format(interface=pxe_iface),
                "instruction": OIM_PREREQ_MSGS["iface_pxe_not_found_instruction"].format(
                    interface=pxe_iface, config_path=OMNIA_TEST_CONFIG_PATH)
            })
        elif pxe_info["state"] != "up":
            results["passed"] = False
            results["checks"].append({
                "name": "pxe_interface",
                "passed": False,
                "message": OIM_PREREQ_MSGS["iface_pxe_down"].format(interface=pxe_iface),
                "instruction": OIM_PREREQ_MSGS["iface_pxe_down_instruction"].format(
                    interface=pxe_iface)
            })
        else:
            results["checks"].append({
                "name": "pxe_interface",
                "passed": True,
                "message": OIM_PREREQ_MSGS["iface_pxe_found"].format(interface=pxe_iface)
            })
    else:
        results["checks"].append({
            "name": "pxe_interface",
            "passed": False,
            "message": OIM_PREREQ_MSGS["iface_omnia_test_configured"],
            "instruction": (f"ACTION REQUIRED: Set 'pxe_interface' in {OMNIA_TEST_CONFIG_PATH} "
                           f"with your PXE network interface name.")
        })
        results["passed"] = False

    # Check Public interface
    if public_iface:
        public_info = get_interface_info(public_iface)
        results["interfaces"].append(public_info)

        if not public_info["exists"]:
            results["passed"] = False
            results["checks"].append({
                "name": "public_interface",
                "passed": False,
                "message": OIM_PREREQ_MSGS["iface_public_not_found"].format(interface=public_iface),
                "instruction": OIM_PREREQ_MSGS["iface_public_not_found_instruction"].format(
                    interface=public_iface, config_path=OMNIA_TEST_CONFIG_PATH)
            })
        elif public_info["state"] != "up":
            results["passed"] = False
            results["checks"].append({
                "name": "public_interface",
                "passed": False,
                "message": OIM_PREREQ_MSGS["iface_public_down"].format(interface=public_iface),
                "instruction": OIM_PREREQ_MSGS["iface_public_down_instruction"].format(
                    interface=public_iface)
            })
        else:
            results["checks"].append({
                "name": "public_interface",
                "passed": True,
                "message": OIM_PREREQ_MSGS["iface_public_found"].format(interface=public_iface)
            })
    else:
        results["checks"].append({
            "name": "public_interface",
            "passed": False,
            "message": OIM_PREREQ_MSGS["iface_omnia_test_configured"],
            "instruction": f"ACTION REQUIRED: Set 'public_interface' in {OMNIA_TEST_CONFIG_PATH} with your public network interface name."
        })
        results["passed"] = False

    return results


def validate_ip_configuration(pxe_ip: str, idrac_ip: str = None, network_type: str = "dedicated") -> Dict:
    """Validate IP configuration for conflicts and format."""
    import ipaddress

    try:
        # Validate PXE IP format
        pxe_network = ipaddress.IPv4Network(pxe_ip, strict=False)
        pxe_addr = ipaddress.IPv4Address(pxe_ip.split('/')[0])

        validation_result = {
            "valid": True,
            "pxe_ip_valid": True,
            "idrac_ip_valid": True,
            "conflict": False,
            "message": "IP configuration is valid"
        }

        # For LOM, validate iDRAC IP and check for conflicts
        if network_type.lower() == "lom" and idrac_ip:
            idrac_network = ipaddress.IPv4Network(idrac_ip, strict=False)
            idrac_addr = ipaddress.IPv4Address(idrac_ip.split('/')[0])

            # Check if IPs are the same
            if pxe_addr == idrac_addr:
                validation_result.update({
                    "valid": False,
                    "conflict": True,
                    "message": f"PXE IP and iDRAC IP cannot be the same: {pxe_addr}"
                })
                return validation_result

            # Check if IPs are in the same subnet (which is actually OK for LOM)
            if pxe_network.network_address == idrac_network.network_address:
                _log(f"PXE and iDRAC IPs are in the same subnet: {pxe_network.network_address} (OK for LOM)", "INFO")

        return validation_result

    except (ipaddress.AddressValueError, ValueError) as e:
        return {
            "valid": False,
            "pxe_ip_valid": "/" in pxe_ip,
            "idrac_ip_valid": "/" in idrac_ip if idrac_ip else True,
            "conflict": False,
            "message": f"Invalid IP format: {str(e)}"
        }


def configure_pxe_nic() -> Dict:
    """
    Configure PXE NIC IP address based on network type.

    Network Types:
    - dedicated: Configure only PXE IP on the interface
    - lom: Configure both PXE IP and iDRAC IP on the same interface (LOM setup)

    Logic:
    1. Validate interface exists and can be brought UP
    2. Validate IP configuration for conflicts
    3. If PXE NIC already has IP and force_configure_pxe is False:
       - Return success with message showing existing IP
    4. If PXE NIC already has IP and force_configure_pxe is True:
       - Remove existing IP and configure new one
    5. If PXE NIC has no IP:
       - Configure with user-provided IP or default (172.16.107.254/24)
    6. For LOM network type: Configure both PXE and iDRAC IPs
    7. Ensure interface is UP after configuration
    """
    _log(OIM_PREREQ_MSGS["pxe_nic_check_start"], "INFO")

    pxe_iface = OIM_PREREQ_VARS.get("pxe_interface", "")
    pxe_ip = OIM_PREREQ_VARS.get("pxe_ip", "172.16.107.254/24")
    network_type = OIM_PREREQ_VARS.get("network_type", "dedicated")
    idrac_ip = OIM_PREREQ_VARS.get("idrac_ip", "172.16.107.253/24")
    force_configure = OIM_PREREQ_VARS.get("force_configure_pxe", False)

    _log(f"Network type: {network_type}", "INFO")

    # Validate interface name
    if not pxe_iface:
        return {
            "passed": False,
            "configured": False,
            "message": OIM_PREREQ_MSGS["pxe_interface_omnia_test_configured"],
            "details": OIM_PREREQ_MSGS["pxe_interface_omnia_test_configured_details"]
        }

    # Check if interface exists
    pxe_info = get_interface_info(pxe_iface)
    if not pxe_info["exists"]:
        return {
            "passed": False,
            "configured": False,
            "message": OIM_PREREQ_MSGS["pxe_interface_not_exist"].format(interface=pxe_iface),
            "details": OIM_PREREQ_MSGS["pxe_interface_not_exist_details"].format(interface=pxe_iface)
        }

    # Validate IP configuration for conflicts
    ip_validation = validate_ip_configuration(pxe_ip, idrac_ip if network_type.lower() == "lom" else None, network_type)
    if not ip_validation["valid"]:
        return {
            "passed": False,
            "configured": False,
            "message": OIM_PREREQ_MSGS["ip_validation_failed"].format(message=ip_validation['message']),
            "details": f"PXE IP: {pxe_ip}" + (f"\niDRAC IP: {idrac_ip}" if network_type.lower() == "lom" else "")
        }

    # Check initial interface state
    initial_state = pxe_info.get("state", "unknown")
    _log(OIM_PREREQ_MSGS["interface_state_check"].format(interface=pxe_iface, state=initial_state), "INFO")

    # Ensure interface is UP before configuration
    if initial_state != "up":
        _log(OIM_PREREQ_MSGS["interface_bring_up"].format(interface=pxe_iface), "INFO")
        rc, _, stderr = run_command(["ip", "link", "set", pxe_iface, "up"])
        if rc != 0:
            _log(OIM_PREREQ_MSGS["interface_bring_up_warning"].format(error=stderr), "WARN")

    # Get current IP
    current_ip = pxe_info.get("ip", "")
    _log(f"PXE interface {pxe_iface} current IP: {current_ip or 'None'}", "INFO")
    _log(f"Target IP: {pxe_ip}", "INFO")
    _log(f"Force configure: {force_configure}", "INFO")

    # Case 1: Already configured and not forcing reconfigure
    if current_ip and not force_configure:
        _log(OIM_PREREQ_MSGS["pxe_nic_already_configured"].format(interface=pxe_iface, ip=current_ip), "INFO")
        return {
            "passed": True,
            "configured": True,
            "already_configured": True,
            "current_ip": current_ip,
            "message": OIM_PREREQ_MSGS["pxe_nic_already_configured"].format(interface=pxe_iface, ip=current_ip),
            "details": f"To reconfigure, set 'force_configure_pxe: true' in {OMNIA_TEST_CONFIG_PATH}"
        }

    # Case 2: Force reconfigure - flush ALL IPs first
    if force_configure:
        _log(OIM_PREREQ_MSGS["pxe_nic_force_reconfigure"].format(interface=pxe_iface), "INFO")

        # Get the NetworkManager connection name for this interface
        rc, nm_conn, _ = run_shell(f"nmcli -t -f NAME,DEVICE con show --active 2>/dev/null | grep ':{pxe_iface}$' | cut -d: -f1")
        nm_conn = nm_conn.strip() if rc == 0 else ""

        if nm_conn:
            _log(f"Found NetworkManager connection '{nm_conn}' for {pxe_iface}", "INFO")
            # Completely reset NetworkManager connection IPv4 settings
            run_shell(f"nmcli con mod '{nm_conn}' ipv4.addresses '' 2>/dev/null")
            run_shell(f"nmcli con mod '{nm_conn}' ipv4.method disabled 2>/dev/null")
            run_shell(f"nmcli con mod '{nm_conn}' ipv4.gateway '' 2>/dev/null")
            run_shell(f"nmcli con mod '{nm_conn}' ipv4.dns '' 2>/dev/null")

            # Also directly edit the NetworkManager config file to ensure old IPs are removed
            config_file = f"/etc/NetworkManager/system-connections/{nm_conn}.nmconnection"
            _log(f"Clearing NetworkManager config file: {config_file}", "INFO")
            run_shell(f"sed -i '/^address[0-9]*=/d' '{config_file}' 2>/dev/null")

            # Reload NetworkManager to pick up config changes
            run_shell("nmcli con reload 2>/dev/null")

            # Bring connection down and up to apply changes
            run_shell(f"nmcli con down '{nm_conn}' 2>/dev/null")
            run_shell("sleep 3")
            run_shell(f"nmcli con up '{nm_conn}' 2>/dev/null")
            run_shell("sleep 2")

        # Multiple attempts to remove all IPs
        for attempt in range(3):
            _log(f"IP removal attempt {attempt + 1}/3...", "INFO")

            # Get all current IPs before removal
            rc, all_ips_output, _ = run_shell(f"ip -4 addr show {pxe_iface} 2>/dev/null | grep 'inet ' | awk '{{print $2}}'")
            all_ips = [ip.strip() for ip in all_ips_output.strip().split("\n") if ip.strip()] if all_ips_output.strip() else []

            if not all_ips:
                _log(f"No IPs found on {pxe_iface}", "OK")
                break

            _log(f"Found {len(all_ips)} IP(s) to remove: {', '.join(all_ips)}", "INFO")

            # Remove each IP individually first
            for ip in all_ips:
                if ip.strip():
                    _log(f"Removing IP: {ip}", "INFO")
                    run_shell(f"ip addr del {ip} dev {pxe_iface} 2>/dev/null")

            # Then do a flush
            _log(f"Flushing all IPv4 addresses from {pxe_iface}...", "INFO")
            run_shell(f"ip -4 addr flush dev {pxe_iface} 2>/dev/null")

            # Brief pause to let changes take effect
            run_shell("sleep 1")

        # Final verification
        rc, remaining_output, _ = run_shell(f"ip -4 addr show {pxe_iface} 2>/dev/null | grep 'inet ' | wc -l")
        remaining_count = remaining_output.strip() if remaining_output else "0"

        if remaining_count == "0":
            _log(f"All IPs successfully removed from {pxe_iface}", "OK")
        else:
            _log(f"Warning: {remaining_count} IP(s) may still remain on {pxe_iface}", "WARN")
            # Show what's still there
            rc, remaining_ips, _ = run_shell(f"ip -4 addr show {pxe_iface} 2>/dev/null | grep 'inet ' | awk '{{print $2}}'")
            if remaining_ips.strip():
                _log(f"Remaining IPs: {remaining_ips.strip()}", "WARN")

    # Case 3: Configure new IP(s) based on network type
    if network_type.lower() == "lom":
        _log(f"Configuring LOM network: PXE IP {pxe_ip} and iDRAC IP {idrac_ip} on {pxe_iface}...", "INFO")
        ips_to_configure = [pxe_ip, idrac_ip]
    else:
        _log(f"Configuring dedicated network: PXE IP {pxe_ip} on {pxe_iface}...", "INFO")
        ips_to_configure = [pxe_ip]

    # Validate IP formats (should be CIDR notation like 172.16.107.254/24)
    validated_ips = []
    for ip in ips_to_configure:
        if "/" not in ip:
            ip = f"{ip}/24"  # Add default subnet if not provided
            _log(f"Added default subnet, using: {ip}", "DEBUG")
        validated_ips.append(ip)

    # Try to configure via NetworkManager first (persistent)
    rc, nm_conn, _ = run_shell(f"nmcli -t -f NAME,DEVICE con show --active 2>/dev/null | grep ':{pxe_iface}$' | cut -d: -f1")
    nm_conn = nm_conn.strip() if rc == 0 else ""

    if nm_conn:
        _log(f"Configuring IPs via NetworkManager connection '{nm_conn}'...", "INFO")
        # Ensure NetworkManager is completely reset first
        run_shell(f"nmcli con mod '{nm_conn}' ipv4.addresses '' 2>/dev/null")
        run_shell(f"nmcli con mod '{nm_conn}' ipv4.method disabled 2>/dev/null")
        run_shell(f"nmcli con down '{nm_conn}' 2>/dev/null")
        run_shell("sleep 2")

        # Set all IPs via NetworkManager (space-separated for multiple IPs)
        ip_list = " ".join(validated_ips)
        run_shell(f"nmcli con mod '{nm_conn}' ipv4.addresses '{ip_list}'")
        run_shell(f"nmcli con mod '{nm_conn}' ipv4.method manual")
        # Apply changes
        run_shell(f"nmcli con up '{nm_conn}' 2>/dev/null")
        run_shell("sleep 2")

    # Also add IPs directly (immediate effect)
    for ip in validated_ips:
        _log(f"Adding IP {ip} to {pxe_iface}...", "INFO")
        rc, _, stderr = run_shell(f"ip addr replace {ip} dev {pxe_iface}")
        if rc != 0:
            return {
                "passed": False,
                "configured": False,
                "message": f"Failed to configure IP {ip} on {pxe_iface}",
                "details": f"Command: ip addr replace {ip} dev {pxe_iface}\nError: {stderr}"
            }

    # Ensure interface is UP after configuration
    _log(f"Ensuring interface {pxe_iface} is UP after configuration...", "INFO")
    rc, _, stderr = run_command(["ip", "link", "set", pxe_iface, "up"])
    if rc != 0:
        _log(f"Warning: Could not bring interface up: {stderr}", "WARN")

    # Verify interface state after configuration
    final_info = get_interface_info(pxe_iface)
    final_state = final_info.get("state", "unknown")
    _log(f"Interface {pxe_iface} final state: {final_state}", "INFO")

    # Verify configuration - get all IPs on the interface
    rc, all_ips_output, _ = run_shell(f"ip -4 addr show {pxe_iface} 2>/dev/null | grep 'inet ' | awk '{{print $2}}'")
    all_configured_ips = [ip.strip() for ip in all_ips_output.strip().split("\n") if ip.strip()] if all_ips_output.strip() else []

    if all_configured_ips:
        configured_ips_str = ", ".join(all_configured_ips)

        # Warn if interface is not UP
        if final_state != "up":
            _log(f"Warning: Interface {pxe_iface} is {final_state}, not UP", "WARN")

        # Build success message based on network type
        if network_type.lower() == "lom":
            _log(f"LOM network configured successfully with IPs: {configured_ips_str}", "OK")
            message = f"LOM network configured on {pxe_iface}"
            details = f"Network Type: {network_type}\nConfigured IPs: {configured_ips_str}\nPXE IP: {pxe_ip}\niDRAC IP: {idrac_ip}\nInterface State: {final_state}"
        else:
            _log(f"Dedicated network configured successfully with IP: {configured_ips_str}", "OK")
            message = f"Dedicated network configured on {pxe_iface}"
            details = f"Network Type: {network_type}\nPXE IP: {configured_ips_str}\nInterface State: {final_state}"

        return {
            "passed": True,
            "configured": True,
            "already_configured": False,
            "network_type": network_type,
            "configured_ips": configured_ips_str,
            "all_ips": all_configured_ips,
            "interface_state": final_state,
            "message": message,
            "details": details
        }

    return {
        "passed": False,
        "configured": False,
        "message": f"IP configuration failed - could not verify IP on {pxe_iface}",
        "details": f"Network type: {network_type}\nAttempted to configure: {', '.join(validated_ips)}"
    }


def check_pxe_is_public_interface() -> Dict:
    """
    Warn the user if the PXE interface is the same as the public interface,
    or if the PXE interface can reach the internet (8.8.8.8).

    If 8.8.8.8 is reachable from the PXE interface, it is likely an
    internet-facing NIC and probably should NOT be used for PXE provisioning.

    Returns:
        Dict with 'warning' (bool), 'message', 'details'.
        'warning' is True only when a potential misconfiguration is detected.
    """
    pxe_iface = OIM_PREREQ_VARS.get("pxe_interface", "")
    public_iface = OIM_PREREQ_VARS.get("public_interface", "")

    if not pxe_iface:
        return {"warning": False, "message": "PXE interface not set, skipping overlap check"}

    # Case 1: PXE and public interface names are identical
    if pxe_iface and public_iface and pxe_iface == public_iface:
        return {
            "warning": True,
            "message": (f"WARNING: pxe_interface and public_interface are both set to "
                        f"'{pxe_iface}'. This is likely a misconfiguration."),
            "details": (
                f"The PXE interface is used for node provisioning and should be an "
                f"isolated network.\nHaving the same NIC for PXE and public internet "
                f"can cause provisioning issues.\n"
                f"Please verify your settings in {OMNIA_TEST_CONFIG_PATH}:\n"
                f"  pxe_interface: {pxe_iface}\n"
                f"  public_interface: {public_iface}"
            ),
        }

    # Case 2: PXE interface can reach 8.8.8.8 (internet reachable = likely public NIC)
    _log(f"Testing if PXE interface '{pxe_iface}' can reach 8.8.8.8...", "INFO")
    rc, _, _ = run_command(["ping", "-c", "1", "-W", "3", "-I", pxe_iface, "8.8.8.8"])

    if rc == 0:
        return {
            "warning": True,
            "message": (f"WARNING: PXE interface '{pxe_iface}' can reach the internet "
                        f"(8.8.8.8). It may be an internet-facing NIC, not a PXE NIC."),
            "details": (
                f"The PXE interface should be on an isolated provisioning network.\n"
                f"If '{pxe_iface}' is intentionally used for both PXE and internet, "
                f"you can ignore this warning.\n"
                f"Otherwise, update 'pxe_interface' in {OMNIA_TEST_CONFIG_PATH}."
            ),
        }

    # No overlap detected
    return {"warning": False, "message": "PXE interface does not overlap with public network"}


def check_internet() -> Dict:
    """Check internet connectivity via ping to public DNS servers."""
    _log("Checking internet connectivity...", "INFO")

    # Test multiple DNS servers
    dns_servers = ["8.8.8.8", "1.1.1.1", "208.67.222.222"]

    for dns in dns_servers:
        rc, _, _ = run_command(["ping", "-c", "1", "-W", "5", dns])
        if rc == 0:
            return {
                "available": True,
                "message": f"Internet connectivity available via {dns}",
                "details": f"Ping successful to {dns}"
            }

    return {
        "available": False,
        "message": "Internet connectivity NOT available",
        "details": f"Failed to ping any DNS servers: {', '.join(dns_servers)}"
    }
