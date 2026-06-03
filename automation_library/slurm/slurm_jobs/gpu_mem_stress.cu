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
    
    size_t alloc_size = free_mem * 0.8;
    float *d_data;
    cudaMalloc(&d_data, alloc_size);
    
    auto start = std::chrono::steady_clock::now();
    int iterations = 0;
    
    while (std::chrono::duration_cast<std::chrono::seconds>(
        std::chrono::steady_clock::now() - start).count() < 300) {
        
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
    printf("Found %d GPU(s)\n", device_count);
    
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
