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

    // Print GPU info
    for (int i = 0; i < deviceCount; i++) {
        cudaDeviceProp prop;
        cudaGetDeviceProperties(&prop, i);
        printf("  GPU %d: %s (Compute Capability %d.%d)\n",
               i, prop.name, prop.major, prop.minor);
        printf("         Memory: %.2f GB\n",
               prop.totalGlobalMem / (1024.0 * 1024.0 * 1024.0));
        printf("         SM Count: %d\n", prop.multiProcessorCount);
    }

    // Launch a simple kernel
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
