
# Configure DCGM Telemetry


Configure NVIDIA Data Center GPU Manager (DCGM) to collect GPU metrics from compute nodes with NVIDIA GPUs.

## Overview


DCGM Telemetry collects GPU metrics from nodes with NVIDIA GPUs. DCGM is installed on each GPU-capable Slurm node during provisioning. The installed DCGM package is selected automatically based on the CUDA version present on the node. On clusters running CUDA 12 or later, the multinode diagnostic plugin is installed in addition to the base DCGM package.

### Data Flow

```
GPU Nodes → DCGM → VMAgent → VictoriaMetrics
```

### Components

- **DCGM** -- NVIDIA Data Center GPU Manager service running on each GPU-capable node. Exposes GPU metrics via a Prometheus-compatible endpoint.
- **VMAgent** -- Scrapes the DCGM Prometheus endpoint and forwards metrics to VictoriaMetrics.

### Supported Metrics

- **Temperature** -- GPU core temperature, memory temperature
- **Utilization** -- GPU utilization percentage, memory utilization, encoder/decoder utilization
- **Memory** -- Total memory, used memory, free memory
- **ECC Errors** -- Single-bit (correctable) and double-bit (uncorrectable) ECC error counts
- **Power** -- Current power draw, power limit, power violation duration
- **Clock Speeds** -- SM clock, memory clock, application clock
- **PCIe** -- PCIe throughput (TX/RX), PCIe replay errors


## Prerequisites


- `provision.yml` has been executed successfully with `service_kube_control_plane_x86_64` and `service_kube_node_x86_64` in the mapping file.
- Compute nodes must have NVIDIA GPUs installed.
- NVIDIA driver and CUDA toolkit must be installed on GPU-capable nodes (installed automatically during provisioning).

!!! note

    DCGM is installed during the cloud-init provisioning phase. It is not deployed via the `telemetry.yml` playbook.


## Procedure


1. **Ensure that `telemetry_config.yml` has the entries specific for DCGM Telemetry**. For details on all parameters, see the [telemetry_config.yml reference](../../Reference/Configuration/telemetry_config.md).

    ```yaml title="Example: Enable DCGM telemetry"
    telemetry_sources:
      dcgm:
        metrics_enabled: true
    ```

    | Value | Result |
    | --- | --- |
    | `true` | Install DCGM during cloud-init provisioning |
    | `false` | Skip DCGM installation |

2. **Run provisioning** to deploy DCGM on GPU-capable nodes:

    ```bash title="Run on omnia_core container"
    cd /omnia/provision
    ansible-playbook provision.yml
    ```

    DCGM is installed and the `nvidia-dcgm` service is automatically enabled and started on GPU-capable nodes during provisioning.

!!! important

    If you enable DCGM telemetry after the initial deployment, execute the `telemetry.sh` script on the K8s control plane:

    ```bash title="Run on K8s control plane"
    <K8s_NFS_mount_point>/telemetry/telemetry.sh
    ```


## Verification


### Verify DCGM Telemetry Service

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


### View DCGM Metrics in VictoriaMetrics UI (VMUI)

1. Access the VMUI in a web browser:

    ```
    https://<external vmselect loadbalancer IP>:8481/select/0/vmui
    ```

2. Query for DCGM metrics. For example:

    ```
    {__name__=~"DCGM_.*"}
    ```

3. Verify that GPU metrics (temperature, utilization, memory, power) are displayed.


## Next Steps


- [Telemetry Overview](setup_telemetry.md) -- Overview of all telemetry sources.


## Troubleshooting


For common telemetry issues and resolutions, see [Troubleshooting Telemetry](../../Troubleshooting/telemetry.md).
