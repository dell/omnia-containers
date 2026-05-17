#!/bin/bash
#SBATCH --job-name=omnia_apptainer_array
#SBATCH --array=1-{{ARRAY_SIZE}}
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --output={{OUTPUT_PATH}}/omnia_apptainer_array_%A_%a.out
#SBATCH --error={{OUTPUT_PATH}}/omnia_apptainer_array_%A_%a.out
#SBATCH --time=00:10:00

SIF_FILE="{{SIF_FILE}}"

echo "Array task $SLURM_ARRAY_TASK_ID of job $SLURM_ARRAY_JOB_ID starting on $(hostname)"
echo "Using SIF: $SIF_FILE"

apptainer exec "$SIF_FILE" bash -c "
echo \"Container: SLURM_ARRAY_TASK_ID=\${SLURM_ARRAY_TASK_ID}\"
echo \"Container: SLURM_ARRAY_JOB_ID=\${SLURM_ARRAY_JOB_ID}\"
echo \"Container: hostname=\$(hostname)\"
echo \"OMNIA_ARRAY_TASK_DONE=\${SLURM_ARRAY_TASK_ID}\"
"
APPTAINER_RC=$?

if [ $APPTAINER_RC -eq 0 ]; then
    echo "Array task $SLURM_ARRAY_TASK_ID completed successfully"
else
    echo "Array task $SLURM_ARRAY_TASK_ID failed with exit code $APPTAINER_RC"
    exit $APPTAINER_RC
fi
