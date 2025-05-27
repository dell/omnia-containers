import subprocess
import sys
import os
import pytest
import getpass

script_dir = os.path.dirname(os.path.abspath(__file__))
input_path = os.path.join(script_dir, 'inputs')

def update_config(ip, password):
    config_content = f'''
OIM_IP = "{ip}"
OIM_PASS = "{password}"
'''
    config_path = os.path.join(script_dir, '../config.py')
    with open(config_path, "w") as config_file:
        config_file.write(config_content)

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
            print("✅ certificate successfully")
        else:
            print("❌ Failed to copy certificate:")
            print(result.stderr)
    except Exception as e:
        print(f"❌ Error: {e}")

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
        print("✅ Certificate installed successfully")
        print(result.stdout)
    else:
        print("❌ Failed to install certificate:")
        print(result.stderr)
        
def login_to_registry(ip, password, username, registry_password):
    ssh_command = [
        "sshpass", "-p", password,
        "ssh", "-o", "StrictHostKeyChecking=no", f"root@{ip}",
        f"podman login nssm.artifactory.cec.lab.emc.com -u {username} -p {registry_password}"
    ]
    result = subprocess.run(ssh_command, capture_output=True, text=True)
    if result.returncode == 0:
        print("✅ Registry login successful")
        return True
    else:
        print("❌ Registry login failed:")
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
            print("✅ Success:")
            print(result.stdout)
        else:
            print("❌ Failed:")
            print(result.stderr)
    except Exception as e:
        print(f"❌ Error: {e}")

def download_omnia_startup(ip, password, branch_name):
    url = f"https://raw.githubusercontent.com/dell/omnia/{branch_name}/omnia_startup.sh"
    
    ssh_command = [
        "sshpass", "-p", password,
        "ssh", "-o", "StrictHostKeyChecking=no",
        f"root@{ip}",
        f"rm -f omnia_startup.sh && wget {url}"
    ]

    try:
        result = subprocess.run(ssh_command, capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ omnia_startup.sh downloaded successfully")
        else:
            print("❌ Failed to download omnia_startup.sh:")
            print(result.stderr)
    except Exception as e:
        print(f"❌ Error: {e}")

def executing_omnia_startup(ip, password, startup_input):
    if startup_input == 1:
        local_input_file = f"{input_path}/nfs_input.txt"
    elif startup_input == 2:
        local_input_file = f"{input_path}/local_input.txt"
    else:
        print("\n❌ Invalid input type.")
        sys.exit(1)

    filename = os.path.basename(local_input_file)
    remote_dir = "/root/inputs"
    remote_clean_input_path = f"{remote_dir}/cleaned_input.txt"


    clean_input_lines = []
    
    with open(local_input_file, "r") as f:
        for line in f:
            parts = line.strip().split(":", 1)
            if len(parts) == 2:
                clean_input_lines.append(parts[1].strip())

    clean_input_file = "cleaned_input.txt"
    with open(clean_input_file, "w") as f:
        f.write("\n".join(clean_input_lines))


    # Step 1: Ensure remote directory exists
    create_dir_cmd = [
        "sshpass", "-p", password,
        "ssh", "-o", "StrictHostKeyChecking=no",
        f"root@{ip}", f"mkdir -p {remote_dir}"
    ]
    try:
        subprocess.run(create_dir_cmd, check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to create directory on remote host:\n{e.stderr}")
        return

    # Step 2: Copy input file to remote host
    scp_command = [
        "sshpass", "-p", password,
        "scp", "-o", "StrictHostKeyChecking=no",
        clean_input_file, f"root@{ip}:{remote_clean_input_path}"
    ]
    try:
        scp_result = subprocess.run(scp_command, capture_output=True, text=True)
        if scp_result.returncode != 0:
            print("❌ Failed to copy input file to remote host:")
            print(scp_result.stderr)
            return
    except Exception as e:
        print(f"❌ SCP error: {e}")
        return

    # Step 3: Run script with input redirection on remote host
    ssh_command = [
    "sshpass", "-p", password,
    "ssh", "-o", "StrictHostKeyChecking=no", f"root@{ip}",
    f"chmod +x omnia_startup.sh && ./omnia_startup.sh < {remote_clean_input_path}"
    ]

    try:
        result = subprocess.run(ssh_command, capture_output=True, text=True)
        if "Omnia core container is already running" in result.stdout or "Failed to intiatiate omnia_core container cleanup." in result.stdout:
            print("\nOmnia core container is already running.")
            sys.exit(1)
        
        elif result.returncode == 0:
            print("✅ omnia_startup.sh executed successfully with automated input")
            print(result.stdout)
            
        else:
            print("❌ Script failed:")
            print(result.stderr)
    except Exception as e:
        print(f"❌ SSH error: {e}")

def run_pytest_for():
    exit_code = pytest.main([f'{script_dir}/tests/test_startup_validation.py'])
    if exit_code != 0:
        raise Exception(f"Tests for creating omnia core failed")

def inv_creation(ip, username, password):
    # Generate inventory file content
    inventory_content = f"""[oim]
    {ip} ansible_user={username} ansible_password={password}
    """
    
    inv_path = os.path.join(script_dir, '../molecule/inv')
    
    # Write to a file
    with open(inv_path, "w") as file:
        file.write(inventory_content)

    print("Inventory file 'inv' has been created.")
    
def handle_common_tasks(oim_ip, oim_pass, registry_user, registry_pass, images, branch_name, oim_username, startup_input):
    if login_to_registry(oim_ip, oim_pass, registry_user, registry_pass):
        for img in images:
            pull_podman_images(oim_ip, oim_pass, img)
        download_omnia_startup(oim_ip, oim_pass, branch_name)
        inv_creation(oim_ip, oim_username, oim_pass)
        executing_omnia_startup(oim_ip, oim_pass, startup_input)
        run_pytest_for()
    else:
        print("\nFailed to log in to the registry.")
    
def main():
    oim_ip = input("Enter OIM IP: ")
    oim_username = input("Enter OIM username: ")
    oim_pass = getpass.getpass("Enter OIM user password: ")
    registry_user = input("Enter Artifactory username: ")
    registry_pass = getpass.getpass("Enter Artifactory password: ")
    branch_name = input("Enter branch name you want to download: ")
    
    while True:
        startup_input = int(input("Choose the type of Omnia shared path\n1. NFS\n2. Local\nEnter choice: "))
        if startup_input == 1 or startup_input == 2:
            break
        else:
            print("\nInvalid input. Please enter '1' or '2'.")

    images = [
        "nssm.artifactory.cec.lab.emc.com/openmanage-docker/omnia_core:latest",
        "nssm.artifactory.cec.lab.emc.com/openmanage-docker/omnia_kubespray:v2.27.0",
        "nssm.artifactory.cec.lab.emc.com/openmanage-docker/omnia_pcs:latest",
        "nssm.artifactory.cec.lab.emc.com/openmanage-docker/omnia_provision:latest"
    ]
    
    update_config(oim_ip, oim_pass)
    download_sshpass_in_oim(oim_ip, oim_pass)

    while True:
        cert = input("\nDo you want to copy the Dell certificate? [yes or no]: \n---Ensure you have an NFS server with the Dell certificate already present--- ").strip().lower()

        if cert == 'yes':
            nfs_ip = input("\nEnter NFS/gateway IP: ")
            nfs_user = input("\nEnter NFS/gateay user: ")
            nfs_pass = getpass.getpass("\nEnter NFS/gateway password: ")
            cert_path = input("\nEnter the certificate path on your NFS/gateway: ")

            copy_dell_certificate(nfs_user, nfs_ip, nfs_pass, oim_ip, oim_pass, cert_path)
            handle_common_tasks(oim_ip, oim_pass, registry_user, registry_pass, images, branch_name, oim_username, startup_input)
            break  # exit the loop after successful processing

        elif cert == 'no':
            handle_common_tasks(oim_ip, oim_pass, registry_user, registry_pass, images, branch_name, oim_username, startup_input)
            break  # exit the loop after successful processing

        else:
            print("\nInvalid input. Please enter 'yes' or 'no'.")
        
if __name__ == "__main__":
    main()
