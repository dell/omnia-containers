import pytest

CONTAINER_NAME = "omnia_core"

def test_omnia_inventroy_files(run_sshpass_command):
    
    print("\nTesting for omnia_inventory files")
    
    files_to_be_created = ["cluster_layout", "compute_cpu_amd", "compute_cpu_intel", "compute_gpu_amd", "compute_gpu_intel", "compute_gpu_nvidia", "compute_hostname_ip"]
    
    files_created = []
    files_not_created = []
    
    cmd = f"podman exec -it {CONTAINER_NAME} ls /opt/omnia/omnia_inventory/"
    
    for inv in files_to_be_created:
        
    
        result = run_sshpass_command(cmd)
        if inv in result.stdout:
            files_created.append(inv)
        else:
            files_not_created.append(inv)
    
    if files_created:
        print("Following inventory files exist:\n" + "\n".join(files_created))
    
    assert files_created, print(f"\nNo inventory files exist in omnia_inventory.")
    
    assert not files_not_created, print("\nFollowing Inventory files are not created:\n" + "\n".join(files_not_created))
    
    print("\n✅ All the inventory files exist.")
    
