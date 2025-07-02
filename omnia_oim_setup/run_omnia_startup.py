
# Copyright 2025 Dell Inc. or its subsidiaries. All Rights Reserved.
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.

import subprocess
import sys
import os
import argparse
import re

script_dir = os.path.dirname(os.path.abspath(__file__))
input_path = "/home/omnia_input/inputs"

def update_config(ip, password, username):
    config_path = os.path.join(script_dir, '../config.py')

    with open(config_path, 'r') as file:
        lines = file.readlines()

    updated_lines = []
    found_ip = found_pass = found_username = found_ha_ip = found_ha_pass = False

    for line in lines:
        if re.match(r'\s*OIM_IP\s*=\s*', line):
            updated_lines.append(f'OIM_IP = "{ip}"\n')
            found_ip = True
        elif re.match(r'\s*OIM_PASS\s*=\s*', line):
            updated_lines.append(f'OIM_PASS = "{password}"\n')
            found_pass = True
        elif re.match(r'\s*OIM_USERNAME\s*=\s*', line):
            updated_lines.append(f'OIM_USERNAME = "{username}"\n')
            found_username = True
        elif re.match(r'\s*OIM_HA_IP\s*=\s*', line):
            updated_lines.append(f'OIM_HA_IP = "{ip}"\n')
            found_ha_ip = True
        elif re.match(r'\s*OIM_HA_PASS\s*=\s*', line):
            updated_lines.append(f'OIM_HA_PASS = "{password}"\n')
            found_ha_pass = True
        else:
            updated_lines.append(line)

    if not found_ip:
        updated_lines.append(f'OIM_IP = "{ip}"\n')
    if not found_pass:
        updated_lines.append(f'OIM_PASS = "{password}"\n')
    if not found_username:
        updated_lines.append(f'OIM_USERNAME = "{username}"\n')
    if not found_ha_ip:
        updated_lines.append(f'OIM_HA_IP = "{ip}"\n')
    if not found_ha_pass:
        updated_lines.append(f'OIM_HA_PASS = "{password}"\n')

    with open(config_path, 'w') as file:
        file.writelines(updated_lines)

def inv_creation(ip, user, password):
    inv_path = os.path.join(script_dir, '../molecule/inv')
    content = f"""[oim]
{ip} ansible_user={user} ansible_password={password}
"""
    with open(inv_path, 'w') as f:
        f.write(content)
    print("Inventory file 'inv' has been created.")

def download_omnia_startup(ip, password, branch_name):
    url = f"https://raw.githubusercontent.com/dell/omnia/{branch_name}/omnia_startup.sh"
    cmd = ["sshpass", "-p", password, "ssh", "-o", "StrictHostKeyChecking=no",
           f"root@{ip}", f"rm -f omnia_startup.sh && wget {url}"]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            print("omnia_startup.sh downloaded successfully")
        else:
            print("Download failed:", result.stderr)
    except Exception as e:
        print(f"Error: {e}")

def cleanup_omnia_container(ip, password):
    try:
        cleanup_cmd = ["sshpass", "-p", password, "ssh", "-o", "StrictHostKeyChecking=no",
                       f"root@{ip}",
                       "podman exec omnia_core bash -c 'cd /omnia/utils && ansible-playbook oim_cleanup.yml'"]
        cleanup = subprocess.run(cleanup_cmd, capture_output=True, text=True)
        print(cleanup.stdout)
        if cleanup.returncode != 0:
            print("Cleanup failed:", cleanup.stderr)
            return False

        remove_cmd = ["sshpass", "-p", password, "ssh", "-o", "StrictHostKeyChecking=no",
                      f"root@{ip}",
                      "podman rm -f omnia_core && podman rmi -f $(podman images -q)"]
        remove = subprocess.run(remove_cmd, capture_output=True, text=True)
        print(remove.stdout)
        return remove.returncode == 0
      
    except Exception as e:
        print(f"Cleanup error: {e}")
        return False



def execute_omnia_startup(ip, password, startup_input):
    file_map = {1: "nfs_input.txt", 2: "local_input.txt"}
    if startup_input not in file_map:
        print("Invalid input type.")
        return False

    local_input = os.path.join(input_path, file_map[startup_input])
    remote_dir = "/root/inputs"
    remote_input = f"{remote_dir}/cleaned_input.txt"
    clean_local = "cleaned_input.txt"

    try:
        with open(local_input, "r") as f:
            lines = [line.strip().split(":", 1)[1].strip() for line in f if ":" in line]
        with open(clean_local, "w") as f:
            f.write("\n".join(lines))

        subprocess.run(["sshpass", "-p", password, "ssh", "-o", "StrictHostKeyChecking=no",
                        f"root@{ip}", f"mkdir -p {remote_dir}"], check=True)

        subprocess.run(["sshpass", "-p", password, "scp", "-o", "StrictHostKeyChecking=no",
                        clean_local, f"root@{ip}:{remote_input}"], check=True)

        cmd = ["sshpass", "-p", password, "ssh", "-o", "StrictHostKeyChecking=no",
               f"root@{ip}", f"chmod +x omnia_startup.sh && ./omnia_startup.sh < {remote_input}"]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            print("omnia_startup.sh executed successfully")
            print(result.stdout)
            # Clean up remote input file
            cleanup_cmd = ["sshpass", "-p", password, "ssh", "-o", "StrictHostKeyChecking=no",
                          f"root@{ip}", f"rm -f {remote_input}"]
            try:
                subprocess.run(cleanup_cmd, capture_output=True, text=True)
                print("Remote input file cleaned up")
            except Exception as e:
                print(f"Warning: Failed to clean up remote input file: {e}")
            return True
        else:
            print("Execution failed:", result.stderr)
            return False
    except Exception as e:
        print(f"Execution error: {e}")
        return False
    finally:
        if os.path.exists(clean_local):
            os.remove(clean_local)

def executing_omnia_startup(ip, password, startup_input):
    check_cmd = ["sshpass", "-p", password, "ssh", "-o", "StrictHostKeyChecking=no",
                 f"root@{ip}", "podman ps | grep omnia_core"]
    check = subprocess.run(check_cmd, capture_output=True, text=True)

    if check.returncode == 0 or "Failed to initiate omnia_core container cleanup." in check.stdout:
        if not cleanup_omnia_container(ip, password):
            print("Cleanup failed. Aborting.")
            return False

    return execute_omnia_startup(ip, password, startup_input)

def login_to_registry(ip, password, username, registry_password):
    cmd = ["sshpass", "-p", password, "ssh", "-o", "StrictHostKeyChecking=no",
           f"root@{ip}", f"podman login nssm.artifactory.cec.lab.emc.com -u {username} -p {registry_password}"]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode == 0:
        print("Registry login successful")
        return True
    else:
        print("Registry login failed:", result.stderr)
        return False

def pull_podman_images(ip, password, image_name):
    cmd = ["sshpass", "-p", password, "ssh", "-o", "StrictHostKeyChecking=no",
           f"root@{ip}", f"podman pull {image_name}"]
    try:
        print(f"Pulling {image_name} on {ip}...")
        result = subprocess.run(cmd, capture_output=True, text=True)
        print(result.stdout if result.returncode == 0 else result.stderr)
    except Exception as e:
        print(f"Error pulling image: {e}")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--oim-ip', required=True)
    parser.add_argument('--oim-username', required=True)
    parser.add_argument('--oim-password', required=True)
    parser.add_argument('--oim-ha-ip', required=True)
    parser.add_argument('--oim-ha-password', required=True)
    parser.add_argument('--branch-name', default='staging')
    parser.add_argument('--startup-type', required=True, type=int)
    parser.add_argument('--registry-user', required=True)
    parser.add_argument('--registry-password', required=True)
    args = parser.parse_args()

    if args.startup_type not in [1, 2]:
        print("Startup type must be 1 (NFS) or 2 (Local)")
        sys.exit(1)

    ip = args.oim_ip
    password = args.oim_password
    user = args.oim_username
    ha_ip = args.oim_ha_ip
    ha_password = args.oim_ha_password

    update_config(ip, password, user)
    update_config(ha_ip, ha_password, user)
    download_omnia_startup(ip, password, args.branch_name)
    inv_creation(ip, user, password)

    # Check if branch is not staging and perform cleanup if needed
    

    # Check if omnia_core is running and clean up if so
    check_cmd = ["sshpass", "-p", password, "ssh", "-o", "StrictHostKeyChecking=no",
                 f"root@{ip}", "podman ps | grep omnia_core"]
    check = subprocess.run(check_cmd, capture_output=True, text=True)

    if check.returncode == 0:
        print("omnia_core is running. Performing cleanup...")
        if not cleanup_omnia_container(ip, password):
            print("Cleanup failed. Aborting.")
            sys.exit(1)

    # Login and pull fresh images
    if login_to_registry(ip, password, args.registry_user, args.registry_password):
        images = [
            "nssm.artifactory.cec.lab.emc.com/openmanage-docker/omnia_core:latest",
            "nssm.artifactory.cec.lab.emc.com/openmanage-docker/omnia_kubespray:v2.28.0",
            "nssm.artifactory.cec.lab.emc.com/openmanage-docker/omnia_pcs:latest",
            "nssm.artifactory.cec.lab.emc.com/openmanage-docker/omnia_provision:latest"
        ]
        for img in images:
            pull_podman_images(ip, password, img)
    else:
        print("Skipping image pulls due to registry login failure.")
        sys.exit(1)

    # Run the omnia startup only after everything else is clean
    if not execute_omnia_startup(ip, password, args.startup_type):
        print("Omnia startup failed.")
        sys.exit(1)
    
    if args.branch_name != 'staging':
        print(f"Branch is {args.branch_name}, performing omnia folder cleanup and clone...")
        
        # SSH into omnia_core and remove omnia folder
        remove_cmd = [
            "sshpass", "-p", password, "ssh", "-o", "StrictHostKeyChecking=no",
            f"root@{ip}",
            "podman exec omnia_core bash -c 'rm -rf /omnia'"
        ]
        try:
            result = subprocess.run(remove_cmd, capture_output=True, text=True)
            if result.returncode != 0:
                print(f"Error removing omnia folder: {result.stderr}")
                sys.exit(1)
            print("Successfully removed and recreated omnia folder")
        except Exception as e:
            print(f"Error during omnia folder cleanup: {e}")
            sys.exit(1)

        # Clone the specific branch into omnia folder
        clone_cmd = [
            "sshpass", "-p", password, "ssh", "-o", "StrictHostKeyChecking=no",
            f"root@{ip}",
            f"podman exec omnia_core bash -c 'cd / && git clone -b {args.branch_name} https://github.com/dell/omnia.git'",
        ]
        try:
            result = subprocess.run(clone_cmd, capture_output=True, text=True)
            if result.returncode != 0:
                print(f"Error cloning branch {args.branch_name}: {result.stderr}")
                sys.exit(1)
            print(f"Successfully cloned branch {args.branch_name} into omnia folder")
        except Exception as e:
            print(f"Error during branch clone: {e}")
            sys.exit(1)

if __name__ == "__main__":
    main()
