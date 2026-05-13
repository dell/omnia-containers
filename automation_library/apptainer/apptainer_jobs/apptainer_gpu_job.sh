#!/bin/bash
#SBATCH --job-name=omnia_apptainer_gpu
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --gres=gpu:1
#SBATCH --output={{OUTPUT_PATH}}/omnia_apptainer_gpu_%j.out
#SBATCH --error={{OUTPUT_PATH}}/omnia_apptainer_gpu_%j.out
#SBATCH --time=00:10:00

SIF_FILE="{{SIF_FILE}}"

echo "Job $SLURM_JOB_ID starting on node $(hostname) - GPU access test"
echo "Using SIF: $SIF_FILE"

echo "=== Host GPU info ==="
nvidia-smi --query-gpu=name --format=csv,noheader 2>/dev/null || echo "nvidia-smi not available on host"

echo ""
echo "=== Container GPU info (--nv flag) ==="
apptainer exec --nv "$SIF_FILE" nvidia-smi --query-gpu=name --format=csv,noheader 2>/dev/null
APPTAINER_RC=$?

echo ""
echo "=== Container GPU count ==="
HOST_GPU_COUNT=$(nvidia-smi --query-gpu=name --format=csv,noheader 2>/dev/null | wc -l)
CONTAINER_GPU_COUNT=$(apptainer exec --nv "$SIF_FILE" nvidia-smi --query-gpu=name --format=csv,noheader 2>/dev/null | wc -l)
echo "HOST_GPU_COUNT=$HOST_GPU_COUNT"
echo "CONTAINER_GPU_COUNT=$CONTAINER_GPU_COUNT"

if [ "$HOST_GPU_COUNT" -eq "$CONTAINER_GPU_COUNT" ] && [ $APPTAINER_RC -eq 0 ]; then
    echo "GPU access in Apptainer container verified: $CONTAINER_GPU_COUNT GPU(s)"
else
    echo "GPU access check failed: host=$HOST_GPU_COUNT container=$CONTAINER_GPU_COUNT rc=$APPTAINER_RC"
    exit 1
fi
