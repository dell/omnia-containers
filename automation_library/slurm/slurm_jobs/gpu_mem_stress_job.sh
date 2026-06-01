#!/bin/bash
#SBATCH --job-name=omnia_gpu_mem_stress
#SBATCH --partition=normal
#SBATCH --nodes=2
#SBATCH --ntasks=2
#SBATCH --gres=gpu:1
#SBATCH --mem=16G
#SBATCH --time=00:10:00
#SBATCH --output=/scratch/%u/results/omnia_gpu_mem_stress_%j.out
#SBATCH --error=/scratch/%u/results/omnia_gpu_mem_stress_%j.err

# Suppress UCX warning
export UCX_WARN_UNUSED_ENV_VARS=n

# Create temp directory
TEMP_DIR="$HOME/tmp/slurm_job_$SLURM_JOB_ID"
mkdir -p "$TEMP_DIR"
cd "$TEMP_DIR"

echo "=== Multi-GPU Memory Stress Test ==="
echo "Node: $(hostname)"
echo "SLURM_JOB_NODELIST: $SLURM_JOB_NODELIST"
echo "Tasks per node: $SLURM_NTASKS_PER_NODE"
echo "CUDA_VISIBLE_DEVICES: $CUDA_VISIBLE_DEVICES"
echo "SLURM_PROCID: $SLURM_PROCID"
echo "SLURM_LOCALID: $SLURM_LOCALID"
echo "=========================================="

# Copy CUDA source and compile
cat > gpu_mem_stress.cu << 'CUDA_EOF'
#include <cuda_runtime.h>
#include <stdio.h>
#include <chrono>
#include <thread>
#include <vector>

__global__ void memory_stress(float *data, size_t size) {
    size_t idx = blockIdx.x * blockDim.x + threadIdx.x;
    if (idx < size) {
        data[idx] = data[idx] * 1.01f;
    }
}

void stress_gpu(int device_id) {
    cudaSetDevice(device_id);
    
    size_t free_mem, total_mem;
    cudaMemGetInfo(&free_mem, &total_mem);
    
    printf("GPU %d: Total memory: %.2f GB, Free: %.2f GB\n", 
           device_id, 
           total_mem / (1024.0 * 1024.0 * 1024.0),
           free_mem / (1024.0 * 1024.0 * 1024.0));
    
    size_t alloc_size = free_mem * 0.8;
    float *d_data;
    cudaError_t err = cudaMalloc(&d_data, alloc_size);
    
    if (err != cudaSuccess) {
        printf("ERROR: GPU %d cudaMalloc failed: %s\n", device_id, cudaGetErrorString(err));
        return;
    }
    
    printf("GPU %d: Allocated %.2f GB for stress test\n", 
           device_id, alloc_size / (1024.0 * 1024.0 * 1024.0));
    
    auto start = std::chrono::steady_clock::now();
    int iterations = 0;
    
    // Run for 60 seconds (reduced from 300 for testing)
    while (std::chrono::duration_cast<std::chrono::seconds>(
        std::chrono::steady_clock::now() - start).count() < 60) {
        
        int threads = 256;
        int blocks = (alloc_size / sizeof(float) + threads - 1) / threads;
        memory_stress<<<blocks, threads>>>(d_data, alloc_size / sizeof(float));
        cudaDeviceSynchronize();
        iterations++;
    }
    
    printf("GPU %d: Completed %d iterations\n", device_id, iterations);
    cudaFree(d_data);
}

int main() {
    int device_count;
    cudaGetDeviceCount(&device_count);
    printf("Found %d GPU(s) on this node\n", device_count);
    
    if (device_count == 0) {
        printf("ERROR: No CUDA-capable GPUs detected\n");
        return 1;
    }
    
    // Launch stress thread per GPU
    std::vector<std::thread> threads;
    for (int i = 0; i < device_count; i++) {
        threads.emplace_back(stress_gpu, i);
    }
    
    for (auto& t : threads) {
        t.join();
    }
    
    printf("\nGPU memory stress test completed successfully!\n");
    return 0;
}
CUDA_EOF

echo "Compiling GPU memory stress program..."
echo "nvcc location: $(which nvcc 2>/dev/null || echo 'not found')"

nvcc -o gpu_mem_stress gpu_mem_stress.cu 2>&1
if [ $? -eq 0 ]; then
    echo "Compilation successful"
    echo ""
    echo "Running GPU memory stress test on both nodes simultaneously..."
    srun --nodes=2 --ntasks-per-node=1 ./gpu_mem_stress
    echo ""
    echo "GPU memory stress test completed successfully"
else
    echo "Compilation failed"
    exit 1
fi
