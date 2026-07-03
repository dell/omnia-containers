
# Slurm with GPUs


Configure GPU-enabled Slurm compute nodes with automatic driver installation
for NVIDIA (CUDA), AMD (ROCm), and Intel Gaudi accelerators.

## Overview


Omnia automatically detects GPU hardware on compute nodes and installs the
appropriate drivers and runtime libraries:

- **NVIDIA GPUs** -- CUDA toolkit and NVIDIA driver via the local CUDA
  repository.
- **AMD GPUs** -- ROCm runtime and driver.
- **Intel Gaudi** -- Habana Labs driver and runtime.

Slurm is configured with **GRES (Generic RESource)** definitions so jobs can
request specific GPU types and quantities.


## Prerequisites


- Compute nodes with GPUs are provisioned and in the Slurm cluster.
- The `software_config.json` includes the GPU software stack:

  ```json title="File: /opt/omnia/input/project_default/software_config.json"
  {
      "softwares": [
          {"name": "slurm"},
          {"name": "cuda", "version": "12.2"},
          {"name": "rocm", "version": "6.0"}
      ]
  }
  ```


- Local repositories are synced with GPU packages (see
  [Create Local Repos](../Setup/create_local_repos.md)).
- GPU nodes are assigned to the `slurm_node` functional group in the
  mapping file.


## Procedure


1. **Enter the omnia_core container**:

   ```bash title="Run on: OIM host"
   ssh omnia_core
   ```


2. **Verify GPU software is listed in software_config.json**:

   ```bash title="Run on: omnia_core container"
   cat /opt/omnia/input/project_default/software_config.json | python3 -m json.tool
   ```


3. **Configure GPU-related parameters in omnia_config.yml**:

   ```bash title="Run on: omnia_core container"
   vi /opt/omnia/input/project_default/omnia_config.yml
   ```


   GPU-related parameters:

   ```yaml title="File: /opt/omnia/input/project_default/omnia_config.yml"
   ---
   # GPU configuration
   cuda_toolkit_path: "/usr/local/cuda"
   rocm_install_path: "/opt/rocm"

   # Slurm GRES configuration (auto-detected if left empty)
   slurm_gres_config: ""
   ```


4. **Run the omnia.yml playbook** (or re-run if Slurm is already deployed):

   ```bash title="Run on: omnia_core container"
   cd /omnia
   ansible-playbook omnia.yml --ask-vault-pass
   ```


   The playbook will:

   - Detect GPU hardware on each compute node.
   - Install CUDA, ROCm, or Gaudi drivers as appropriate.
   - Generate `gres.conf` with GPU device mappings.
   - Update `slurm.conf` with GRES definitions.
   - Restart Slurm services to apply changes.

5. **Reconfigure Slurm** to load GRES definitions:

   ```bash title="Run on: Slurm control node"
   scontrol reconfigure
   ```



## Verification


1. **Verify GPU drivers are installed** on a compute node:

   For NVIDIA:

   ```bash title="Run on: GPU compute node"
   nvidia-smi
   ```


   Expected output shows GPU model, driver version, and memory usage.

   For AMD:

   ```bash title="Run on: GPU compute node"
   rocm-smi
   ```


   For Intel Gaudi:

   ```bash title="Run on: GPU compute node"
   hl-smi
   ```


2. **Check Slurm GRES configuration**:

   ```bash title="Run on: Slurm control node"
   scontrol show nodes | grep -i gres
   ```


   Expected output:

   ```text title="Expected output on: Slurm control node"
   Gres=gpu:nvidia_a100:4
   GresUsed=gpu:nvidia_a100:0
   ```


3. **Submit a GPU job**:

   ```bash title="Run on: Slurm control node"
   srun --gres=gpu:1 nvidia-smi
   ```


4. **Submit a multi-GPU batch job**:

   ```bash title="Run on: Slurm control node"
   cat <<'EOF' > /tmp/gpu_test.sh
   #!/bin/bash
   #SBATCH --job-name=gpu_test
   #SBATCH --gres=gpu:2
   #SBATCH --nodes=1
   #SBATCH --time=00:05:00

   echo "Running on $(hostname)"
   echo "CUDA_VISIBLE_DEVICES=$CUDA_VISIBLE_DEVICES"
   nvidia-smi
   EOF

   sbatch /tmp/gpu_test.sh
   ```


5. **Verify CUDA toolkit** (NVIDIA):

   ```bash title="Run on: GPU compute node"
   nvcc --version
   ls /usr/local/cuda/
   ```



## Next Steps


- [Run Hpc Benchmarks](run_hpc_benchmarks.md) -- Run GPU-accelerated benchmarks.
- [Use Apptainer](../AdvancedConfigurations/use_apptainer.md) -- Run GPU containers with Apptainer.


## Troubleshooting


**nvidia-smi reports "no devices found"**
   - Verify the GPU is physically seated and powered.
   - Check that the NVIDIA driver module is loaded:

     ```bash title="Run on: GPU compute node"
     lsmod | grep nvidia
     dmesg | grep -i nvidia
     ```


   - Reinstall the driver:

     ```bash title="Run on: GPU compute node"
     dnf reinstall nvidia-driver cuda-toolkit
     ```


**GRES not showing in scontrol**
   Check `gres.conf` on the compute node:

   ```bash title="Run on: GPU compute node"
   cat /etc/slurm/gres.conf
   ```


   The file should list each GPU device:

   ```text title="Expected content on: GPU compute node"
   NodeName=compute01 Name=gpu Type=nvidia_a100 File=/dev/nvidia[0-3]
   ```


**"Invalid GRES" error when submitting jobs**
   Ensure `slurm.conf` on the control node includes the `GresTypes`
   directive:

   ```bash title="Run on: Slurm control node"
   grep GresTypes /etc/slurm/slurm.conf
   ```


   Expected: `GresTypes=gpu`

**ROCm driver fails to install**
   Verify the ROCm repository was synced successfully:

   ```bash title="Run on: omnia_core container"
   curl -s http://localhost:8080/pulp/content/rocm/ | head
   ```
