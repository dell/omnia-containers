#!/bin/bash
#SBATCH --job-name=omnia_test_sbatch
#SBATCH --nodes={{SLURM_NUM_NODES}}
#SBATCH --output=/scratch/%u/results/omnia_test_sbatch_%j.out
#SBATCH --error=/scratch/%u/results/omnia_test_sbatch_%j.err
#SBATCH --time=00:05:00

# Basic sbatch job for OMNIA Slurm test automation.
# This script runs hostname on all allocated nodes to verify job execution.

srun hostname
echo "Job $SLURM_JOB_ID completed on $SLURM_NNODES node(s)"
