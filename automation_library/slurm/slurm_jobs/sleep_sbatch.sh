#!/bin/bash
#SBATCH --job-name=omnia_test_sleep
#SBATCH --nodes=1
#SBATCH --output={{OUTPUT_PATH}}/omnia_test_sleep_%j.out
#SBATCH --error={{OUTPUT_PATH}}/omnia_test_sleep_%j.out
#SBATCH --time=00:05:00

# Sleep job for OMNIA Slurm PAM test automation.
# This job sleeps for a configurable duration to allow PAM login verification
# while the job is running on the allocated slurm node(s).

echo "Job $SLURM_JOB_ID started on $(hostname) at $(date)"
echo "Sleeping for {{SLEEP_DURATION}} seconds..."
sleep {{SLEEP_DURATION}}
echo "Job $SLURM_JOB_ID completed on $(hostname) at $(date)"
