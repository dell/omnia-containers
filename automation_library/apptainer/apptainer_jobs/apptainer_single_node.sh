#!/bin/bash
#SBATCH --job-name=omnia_apptainer_single
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --output={{OUTPUT_PATH}}/omnia_apptainer_single_%j.out
#SBATCH --error={{OUTPUT_PATH}}/omnia_apptainer_single_%j.out
#SBATCH --time=00:10:00

SIF_FILE="{{SIF_FILE}}"

echo "Job $SLURM_JOB_ID starting on node $(hostname)"
echo "Using SIF: $SIF_FILE"

apptainer exec "$SIF_FILE" hostname
APPTAINER_RC=$?

if [ $APPTAINER_RC -eq 0 ]; then
    echo "Apptainer single-node job $SLURM_JOB_ID completed successfully on $SLURM_NNODES node(s)"
else
    echo "Apptainer exec failed with exit code $APPTAINER_RC"
    exit $APPTAINER_RC
fi
