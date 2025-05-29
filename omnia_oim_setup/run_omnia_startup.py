import subprocess
import sys
import os
import pytest
import getpass
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))
import config


ip = config.OIM_IP
password = config.OIM_PASS
user = config.USERNAME

script_dir = os.path.dirname(os.path.abspath(__file__))
input_path = os.path.join(script_dir, 'inputs')

def download_omnia_startup(branch_name):
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

def executing_omnia_startup(startup_input):
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

def inv_creation():
    # Generate inventory file content
    inventory_content = f"""[oim]
    {ip} ansible_user={user} ansible_password={password}
    """
    
    inv_path = os.path.join(script_dir, '../molecule/oim_inv')
    
    # Write to a file
    with open(inv_path, "w") as file:
        file.write(inventory_content)

    print("Inventory file 'inv' has been created.")
    


def main():

    branch_name = input("Enter branch name you want to download: ")

    while True:
        startup_input = int(input("Choose the type of Omnia shared path\n1. NFS\n2. Local\nEnter choice: "))
        if startup_input == 1 or startup_input == 2:
            break
        else:
            print("\nInvalid input. Please enter '1' or '2'.")

    download_omnia_startup(branch_name)
    inv_creation()
    executing_omnia_startup(startup_input)
    run_pytest_for()

if __name__ == "__main__":
    main()
