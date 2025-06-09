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
import pytest
import getpass
import re

script_dir = os.path.dirname(os.path.abspath(__file__))
input_path = os.path.join(script_dir, 'inputs')

import os
import re

def update_config(ip, password, username):
    config_path = os.path.join(script_dir, '../config.py')

    # Read existing lines
    with open(config_path, 'r') as file:
        lines = file.readlines()

    updated_lines = []
    found_ip = found_pass = found_username = False

    for line in lines:
        if re.match(r'^\s*OIM_IP\s*=', line):
            updated_lines.append(f'OIM_IP = "{ip}"\n')
            found_ip = True
        elif re.match(r'^\s*OIM_PASS\s*=', line):
            updated_lines.append(f'OIM_PASS = "{password}"\n')
            found_pass = True
        elif re.match(r'^\s*OIM_USERNAME\s*=', line):  # Match actual key in your config
            updated_lines.append(f'OIM_USERNAME = "{username}"\n')
            found_username = True
        else:
            updated_lines.append(line)

    # Append any missing variables
    if not found_ip:
        updated_lines.append(f'OIM_IP = "{ip}"\n')
    if not found_pass:
        updated_lines.append(f'OIM_PASS = "{password}"\n')
    if not found_username:
        updated_lines.append(f'OIM_USERNAME = "{username}"\n')

    # Write back updated config
    with open(config_path, 'w') as file:
        file.writelines(updated_lines)


def copy_dell_certificate(nfs_user, nfs_ip, nfs_password, ip, password, cert_path):
    
    # Step 1: Copy the certificate directory from NFS/Gateway to the OIM.
    print("Copying certificate from NFS/Gateway to the OIM.")
    
    scp_command = [
    "sshpass", "-p", password,
    "ssh", "-o", "StrictHostKeyChecking=no",
    f"root@{ip}",
    f"sshpass -p {nfs_password} scp -r {nfs_user}@{nfs_ip}:{cert_path} /root/"
    ]
    
    try:
        result = subprocess.run(scp_command, capture_output=True, text=True)
        if result.returncode == 0:
            print("certificate copied successfully")
        else:
            print("Failed to copy certificate:")
            print(result.stderr)
    except Exception as e:
        print(f"Error: {e}")

     # Step 2: SSH into the remote machine and install the certificate
    remote_cmd = (
        "cd /root/ && "
        "yum install -y ca-certificates && "
        "update-ca-trust force-enable && "
        "cp dellca2018-bundle.crt /etc/pki/ca-trust/source/anchors/ && "
        "update-ca-trust extract"
    )
    ssh_command = [
        "sshpass", "-p", password,
        "ssh", "-o", "StrictHostKeyChecking=no",
        f"root@{ip}", remote_cmd
    ]
    result = subprocess.run(ssh_command, capture_output=True, text=True)
    if result.returncode == 0:
        print("Certificate installed successfully")
        print(result.stdout)
    else:
        print("Failed to install certificate:")
        print(result.stderr)
        
def login_to_registry(ip, password, username, registry_password):
    ssh_command = [
        "sshpass", "-p", password,
        "ssh", "-o", "StrictHostKeyChecking=no", f"root@{ip}",
        f"podman login nssm.artifactory.cec.lab.emc.com -u {username} -p {registry_password}"
    ]
    result = subprocess.run(ssh_command, capture_output=True, text=True)
    if result.returncode == 0:
        print("Registry login successful")
        return True
    else:
        print("Registry login failed:")
        print(result.stderr)
        return False

def pull_podman_images(ip, password, image_name):
    ssh_command = [
        "sshpass", "-p", password,
        "ssh", "-o", "StrictHostKeyChecking=no", f"root@{ip}",
        f"podman pull {image_name}"
    ]
    
    try:
        print(f"\nPulling image on {ip}: {image_name}")
        result = subprocess.run(ssh_command, capture_output=True, text=True)
        if result.returncode == 0:
            print("Success:")
            print(result.stdout)
        else:
            print("Failed:")
            print(result.stderr)
    except Exception as e:
        print(f"Error: {e}")
    
def handle_common_tasks(oim_ip, oim_pass, registry_user, registry_pass, images, oim_username):
    if login_to_registry(oim_ip, oim_pass, registry_user, registry_pass):
        for img in images:
            pull_podman_images(oim_ip, oim_pass, img)
    else:
        print("\nFailed to log in to the registry.")
    
def main():
    oim_ip = input("Enter OIM IP: ")
    oim_username = input("Enter OIM username: ")
    oim_pass = getpass.getpass("Enter OIM user password: ")
    registry_user = input("Enter Artifactory username: ")
    registry_pass = getpass.getpass("Enter Artifactory password: ")

    images = [
        "nssm.artifactory.cec.lab.emc.com/openmanage-docker/omnia_core:latest",
        "nssm.artifactory.cec.lab.emc.com/openmanage-docker/omnia_kubespray:v2.27.0",
        "nssm.artifactory.cec.lab.emc.com/openmanage-docker/omnia_pcs:latest",
        "nssm.artifactory.cec.lab.emc.com/openmanage-docker/omnia_provision:latest"
    ]
    
    update_config(oim_ip, oim_pass, oim_username)

    while True:
        cert = input("\n---Ensure you have an NFS server with the Dell certificate already present---\nDo you want to copy the Dell certificate? [yes or no]: ").strip().lower()

        if cert == 'yes':
            nfs_ip = input("\nEnter NFS/gateway IP: ")
            nfs_user = input("\nEnter NFS/gateay user: ")
            nfs_pass = getpass.getpass("\nEnter NFS/gateway password: ")
            cert_path = input("\nEnter the certificate path on your NFS/gateway: ")

            copy_dell_certificate(nfs_user, nfs_ip, nfs_pass, oim_ip, oim_pass, cert_path)
            handle_common_tasks(oim_ip, oim_pass, registry_user, registry_pass, images, oim_username)
            break  # exit the loop after successful processing

        elif cert == 'no':
            handle_common_tasks(oim_ip, oim_pass, registry_user, registry_pass, images, oim_username)
            break  # exit the loop after successful processing

        else:
            print("\nInvalid input. Please enter 'yes' or 'no'.")
        
if __name__ == "__main__":
    main()
