#!/bin/bash
#SBATCH --job-name=omnia_upgrade_precheck
#SBATCH --nodes=1
#SBATCH --output=/home/omnia_upgrade_precheck_%j.out
#SBATCH --error=/home/omnia_upgrade_precheck_%j.err
#SBATCH --time=00:05:00

# Upgrade precheck sbatch job for OMNIA Slurm upgrade test automation.
# Runs hostname on 1 compute node to verify job execution before upgrade.

srun hostname
echo "Job $SLURM_JOB_ID completed on $SLURM_NNODES node(s)"
