#!/bin/bash
#SBATCH --job-name=omnia_apptainer_fail
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --output={{OUTPUT_PATH}}/omnia_apptainer_fail_%j.out
#SBATCH --error={{OUTPUT_PATH}}/omnia_apptainer_fail_%j.out
#SBATCH --time=00:05:00

SIF_FILE="{{SIF_FILE}}"

echo "Job $SLURM_JOB_ID starting - intentional failure test"
echo "Using SIF (does not exist): $SIF_FILE"

apptainer exec "$SIF_FILE" hostname
APPTAINER_RC=$?

echo "Apptainer exit code: $APPTAINER_RC"
exit $APPTAINER_RC
