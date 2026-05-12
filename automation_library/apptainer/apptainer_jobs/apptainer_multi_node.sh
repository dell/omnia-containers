#!/bin/bash
#SBATCH --job-name=omnia_apptainer_multi
#SBATCH --nodes={{SLURM_NUM_NODES}}
#SBATCH --ntasks={{SLURM_NUM_NODES}}
#SBATCH --output={{OUTPUT_PATH}}/omnia_apptainer_multi_%j.out
#SBATCH --error={{OUTPUT_PATH}}/omnia_apptainer_multi_%j.out
#SBATCH --time=00:10:00

SIF_FILE="{{SIF_FILE}}"

echo "Job $SLURM_JOB_ID starting on $SLURM_NNODES node(s)"
echo "Nodes: $SLURM_NODELIST"
echo "Using SIF: $SIF_FILE"

srun apptainer exec "$SIF_FILE" hostname
APPTAINER_RC=$?

if [ $APPTAINER_RC -eq 0 ]; then
    echo "Apptainer multi-node job $SLURM_JOB_ID completed successfully on $SLURM_NNODES node(s)"
else
    echo "Apptainer srun exec failed with exit code $APPTAINER_RC"
    exit $APPTAINER_RC
fi
