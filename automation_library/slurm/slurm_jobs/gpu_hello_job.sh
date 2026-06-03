#!/bin/bash
#SBATCH --job-name=omnia_gpu_hello
#SBATCH --nodes=2
#SBATCH --ntasks=2
#SBATCH --gres=gpu:2
#SBATCH --time=00:10:00
#SBATCH --output=/scratch/%u/results/omnia_gpu_hello_%j.out
#SBATCH --error=/scratch/%u/results/omnia_gpu_hello_%j.err
#SBATCH --partition=normal

# Suppress UCX warning
export UCX_WARN_UNUSED_ENV_VARS=n

# Create temp directory
TEMP_DIR="$HOME/tmp/slurm_job_$SLURM_JOB_ID"
mkdir -p "$TEMP_DIR"
cd "$TEMP_DIR"

echo "=== GPU Hello Test ==="
echo "Job ID: $SLURM_JOB_ID"
echo "Nodes allocated: $SLURM_JOB_NODELIST"
echo "Total tasks: $SLURM_NTASKS"
echo "=========================================="

# Run diagnostic info on EACH node using srun
echo "Node GPU allocation:"
srun bash -c 'echo "  Node: $(hostname) | GPUs: $CUDA_VISIBLE_DEVICES"'
echo "=========================================="

# Copy CUDA source and compile
cat > gpu_hello.cu << 'CUDA_EOF'
#include <stdio.h>

__global__ void helloGPU() {
    int tid = threadIdx.x + blockIdx.x * blockDim.x;
    printf("Hello from GPU thread %d (block %d, thread %d)\n",
           tid, blockIdx.x, threadIdx.x);
}

int main() {
    int deviceCount = 0;
    cudaGetDeviceCount(&deviceCount);
    printf("Number of GPUs detected: %d\n", deviceCount);

    if (deviceCount == 0) {
        printf("ERROR: No CUDA-capable GPUs detected\n");
        return 1;
    }

    for (int i = 0; i < deviceCount; i++) {
        cudaDeviceProp prop;
        cudaGetDeviceProperties(&prop, i);
        printf("  GPU %d: %s (Compute Capability %d.%d)\n",
               i, prop.name, prop.major, prop.minor);
        printf("         Memory: %.2f GB\n",
               prop.totalGlobalMem / (1024.0 * 1024.0 * 1024.0));
        printf("         SM Count: %d\n", prop.multiProcessorCount);
    }

    printf("\nLaunching kernel with 2 blocks x 4 threads...\n");
    helloGPU<<<2, 4>>>();
    cudaError_t err = cudaDeviceSynchronize();
    
    if (err != cudaSuccess) {
        printf("ERROR: Kernel execution failed: %s\n", cudaGetErrorString(err));
        return 1;
    }

    printf("\nGPU job completed successfully!\n");
    return 0;
}
CUDA_EOF

echo "Compiling GPU hello program..."
echo "nvcc location: $(which nvcc 2>/dev/null || echo 'not found')"
echo "CUDA_HOME: $CUDA_HOME"

nvcc -o gpu_hello gpu_hello.cu 2>&1
if [ $? -eq 0 ]; then
    echo "Compilation successful"
    echo ""
    echo "Running GPU hello on all allocated nodes..."
    srun ./gpu_hello
    echo ""
    echo "GPU hello test completed successfully"
else
    echo "Compilation failed"
    exit 1
fi
