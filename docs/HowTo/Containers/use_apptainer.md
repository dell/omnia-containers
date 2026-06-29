
# Use Apptainer


Pull and run containerized HPC applications across Slurm compute nodes using
Apptainer (formerly Singularity), with SIF images stored on NFS shared
storage.

## Overview


Apptainer is the standard container runtime for HPC environments. Unlike
Docker, Apptainer:

- Runs without a daemon or root privileges.
- Integrates natively with Slurm job scheduling.
- Supports GPU pass-through (`--nv` for NVIDIA, `--rocm` for AMD).
- Uses SIF (Singularity Image Format) images that are single-file,
  read-only, and easily shared via NFS.

The workflow is:

1. Pull a container image (Docker or SIF format) to shared NFS storage.
2. Submit Slurm jobs that execute commands inside the container.
3. All compute nodes access the same SIF image via NFS -- no per-node
   image installation required.


## Prerequisites


- Apptainer is installed on compute nodes (included via
  `software_config.json` with `{"name": "apptainer"}`).
- NFS shared storage is configured (see [Configure Nfs](../Storage/configure_nfs.md)).
- Slurm is deployed and functional (see [Setup Slurm](../Slurm/setup_slurm.md)).
- For GPU containers: GPU drivers installed (see
  [Slurm With Gpu](../Slurm/slurm_with_gpu.md)).


## Procedure


1. **Verify Apptainer is installed** on compute nodes:

   ```bash title="Run on: omnia_core container"
   ansible slurm_node -m shell -a "apptainer --version"
   ```


2. **Create a shared images directory** on NFS:

   ```bash title="Run on: Slurm control node or login node"
   mkdir -p /home/containers/images
   chmod 755 /home/containers/images
   ```


3. **Pull a Docker image** and convert to SIF:

   ```bash title="Run on: Slurm control node or login node"
   apptainer pull /home/containers/images/ubuntu.sif docker://ubuntu:22.04
   ```


4. **Pull an HPC application container**:

   ```bash title="Run on: Slurm control node or login node"
   # Example: GROMACS molecular dynamics
   apptainer pull /home/containers/images/gromacs.sif docker://nvcr.io/hpc/gromacs:2023.2

   # Example: TensorFlow for AI workloads
   apptainer pull /home/containers/images/tensorflow.sif docker://nvcr.io/nvidia/tensorflow:24.01-tf2-py3
   ```


5. **Run an interactive container** on a compute node:

   ```bash title="Run on: Slurm control node"
   srun -N 1 --pty apptainer shell /home/containers/images/ubuntu.sif
   ```


   This opens an interactive shell inside the container on a compute node.

6. **Run a batch job** with Apptainer:

   ```bash title="Run on: Slurm control node"
   cat <<'EOF' > /home/containers/run_gromacs.sh
   #!/bin/bash
   #SBATCH --job-name=gromacs-test
   #SBATCH --nodes=2
   #SBATCH --ntasks-per-node=4
   #SBATCH --time=02:00:00
   #SBATCH --output=/home/containers/results/gromacs-%j.out

   apptainer exec /home/containers/images/gromacs.sif \
     mpirun -np 8 gmx_mpi mdrun -s input.tpr -deffnm output
   EOF

   sbatch /home/containers/run_gromacs.sh
   ```


7. **Run a GPU container** with Apptainer:

   ```bash title="Run on: Slurm control node"
   cat <<'EOF' > /home/containers/run_tensorflow.sh
   #!/bin/bash
   #SBATCH --job-name=tf-test
   #SBATCH --nodes=1
   #SBATCH --gres=gpu:1
   #SBATCH --time=01:00:00
   #SBATCH --output=/home/containers/results/tf-%j.out

   apptainer exec --nv /home/containers/images/tensorflow.sif \
     python3 -c "import tensorflow as tf; print(tf.config.list_physical_devices('GPU'))"
   EOF

   sbatch /home/containers/run_tensorflow.sh
   ```


8. **Build a custom SIF image** from a definition file:

   ```bash title="Run on: Slurm control node"
   cat <<'EOF' > /home/containers/custom.def
   Bootstrap: docker
   From: ubuntu:22.04

   %post
       apt-get update
       apt-get install -y python3 python3-pip
       pip3 install numpy scipy

   %runscript
       python3 "$@"
   EOF

   apptainer build /home/containers/images/custom.sif /home/containers/custom.def
   ```



## Verification


1. **Verify SIF images are accessible** from all compute nodes:

   ```bash title="Run on: omnia_core container"
   ansible slurm_node -m shell -a "ls -la /home/containers/images/"
   ```


2. **Run a quick test** across multiple nodes:

   ```bash title="Run on: Slurm control node"
   srun -N 2 apptainer exec /home/containers/images/ubuntu.sif hostname
   ```


3. **Verify GPU access** inside containers:

   ```bash title="Run on: Slurm control node"
   srun -N 1 --gres=gpu:1 apptainer exec --nv /home/containers/images/tensorflow.sif nvidia-smi
   ```


4. **Check job output**:

   ```bash title="Run on: Slurm control node"
   cat /home/containers/results/*.out
   ```



## Next Steps


- [Deploy Additional Packages](deploy_additional_packages.md) -- Install additional packages alongside
  containers.
- [Run Hpc Benchmarks](../Slurm/run_hpc_benchmarks.md) -- Run benchmark containers.


## Troubleshooting


**"apptainer: command not found"**
   Verify Apptainer is installed:

   ```bash title="Run on: compute node"
   dnf install -y apptainer
   ```


**Pull fails with "permission denied"**
   - Ensure the NFS directory has write permissions.
   - Apptainer uses `/tmp` for build cache; ensure sufficient space:

     ```bash title="Run on: compute node"
     df -h /tmp
     export APPTAINER_TMPDIR=/scratch/tmp
     ```


**GPU not accessible inside container**
   - Use `--nv` for NVIDIA or `--rocm` for AMD GPUs.
   - Verify the host GPU driver is compatible with the container's CUDA
     version.

**SIF image corrupted**
   Re-pull the image:

   ```bash title="Run on: Slurm control node"
   rm /home/containers/images/broken.sif
   apptainer pull /home/containers/images/fixed.sif docker://source-image
   ```


**MPI inside container fails**
   Ensure the MPI version inside the container is compatible with the host
   MPI. Use `--bind` to mount the host MPI libraries:

   ```bash title="Run on: Slurm control node"
   srun -N 2 apptainer exec --bind /usr/lib64/openmpi:/host-mpi \
     /home/containers/images/app.sif mpirun -np 8 /app/benchmark
   ```
