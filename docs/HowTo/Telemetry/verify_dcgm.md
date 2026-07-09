
# Verify DCGM Telemetry


This page provides verification steps for the DCGM (NVIDIA Data Center GPU Manager) telemetry deployment.

## Prerequisites


- The [Configure DCGM Telemetry](configure_dcgm.md) procedure is complete.
- GPU-capable nodes are provisioned and running.


## Verify DCGM Telemetry Service

Verify that the DCGM service and GPU stack are operational on GPU-capable nodes:

1. Verify that the `nvidia-dcgm` service is running:

    ```bash title="Run on GPU-capable Slurm node"
    systemctl status nvidia-dcgm
    ```

2. Confirm that DCGM can discover all GPUs on the node:

    ```bash title="Run on GPU-capable Slurm node"
    dcgmi discovery -l
    ```

3. Confirm that the NVIDIA driver is loaded and GPUs are visible:

    ```bash title="Run on GPU-capable Slurm node"
    nvidia-smi
    ```

4. Confirm that the CUDA toolkit is available:

    ```bash title="Run on GPU-capable Slurm node"
    nvcc --version
    echo $CUDA_HOME
    ```


## View DCGM Metrics in VictoriaMetrics UI (VMUI)

1. Access the VMUI in a web browser:

    ```
    https://<external vmselect loadbalancer IP>:8481/select/0/vmui
    ```

2. Query for DCGM metrics. For example:

    ```
    {__name__=~"DCGM_.*"}
    ```

3. Verify that GPU metrics (temperature, utilization, memory, power) are displayed.
