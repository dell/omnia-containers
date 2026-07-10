# Configure DCGM Telemetry


Configure NVIDIA Data Center GPU Manager (DCGM) to collect GPU metrics from compute nodes with NVIDIA GPUs.

## Overview


DCGM Telemetry collects GPU metrics from nodes with NVIDIA GPUs. DCGM is installed on each GPU-capable Slurm node during provisioning. The installed DCGM package is selected automatically based on the CUDA version present on the node. On clusters running CUDA 12 or later, the multinode diagnostic plugin is installed in addition to the base DCGM package.

### Components

- **DCGM** -- NVIDIA Data Center GPU Manager service running on each GPU-capable node. Exposes GPU metrics via a Prometheus-compatible endpoint.
- **VMAgent** -- Scrapes the DCGM Prometheus endpoint and forwards metrics to VictoriaMetrics.

### Data Flow

```
GPU Nodes → DCGM → VMAgent → VictoriaMetrics
```

### Supported Metrics

- **Temperature** -- GPU core temperature, memory temperature
- **Utilization** -- GPU utilization percentage, memory utilization, encoder/decoder utilization
- **Memory** -- Total memory, used memory, free memory
- **ECC Errors** -- Single-bit (correctable) and double-bit (uncorrectable) ECC error counts
- **Power** -- Current power draw, power limit, power violation duration
- **Clock Speeds** -- SM clock, memory clock, application clock
- **PCIe** -- PCIe throughput (TX/RX), PCIe replay errors


## Prerequisites


Complete the following before you configure DCGM telemetry. Provisioning the
cluster happens **after** this configuration, as part of the deployment sequence.

- The `omnia_core` container is deployed on the OIM. See
  [Deploy Omnia Core](../Setup/deploy_omnia_core.md).
- The mapping file (`pxe_mapping_file.csv`) is created. See
  [Create Mapping File](../Setup/create_mapping_file.md).
- Compute nodes must have NVIDIA GPUs installed.

!!! note

    DCGM is installed during the cloud-init provisioning phase on GPU-capable
    Slurm nodes. It is **not** deployed via the `telemetry.yml` playbook. During
    provisioning, Omnia detects the NVIDIA GPU and CUDA version and installs the
    matching `datacenter-gpu-manager-4-cuda<version>` package. If no NVIDIA GPU or
    driver is detected, DCGM setup is skipped automatically.


## Procedure


### Step 1: Add Required Software to software_config.json

DCGM runs on GPU-capable Slurm nodes and requires the NVIDIA driver and CUDA
toolkit. These are provided by the NVIDIA HPC SDK (NVHPC) bundled with the
`slurm_custom` software entry. Ensure `slurm_custom` is present in
`software_config.json`.

```json title="software_config.json -- required for DCGM telemetry"
{
    "softwares": [
        {"name": "slurm_custom", "arch": ["x86_64", "aarch64"]}
    ]
}
```

For the full file structure, see the
[software_config.json reference](../../Reference/Configuration/software_config.md).

### Step 2: Verify the CUDA Repository in local_repo_config.yml

The DCGM package (`datacenter-gpu-manager-4-cuda<version>`) is downloaded from the
NVIDIA `cuda` repository. This repository is included by default in
`omnia_repo_url_rhel_x86_64` (and `omnia_repo_url_rhel_aarch64`). Verify the entry
exists for each architecture in your cluster.

```yaml title="local_repo_config.yml -- CUDA repository (default)"
omnia_repo_url_rhel_x86_64:
  - {url: "https://developer.download.nvidia.com/compute/cuda/repos/rhel10/x86_64/", gpgkey: "https://developer.download.nvidia.com/compute/cuda/repos/rhel10/x86_64/repodata/repomd.xml.key", name: "cuda"}
```

For details, see the
[local_repo_config.yml reference](../../Reference/Configuration/local_repo_config.md).

### Step 3: Add Required Nodes to the Mapping File

Add your GPU-capable compute nodes to `pxe_mapping_file.csv` under the `slurm_node`
(or `slurm_control_node`) functional group.

```text title="pxe_mapping_file.csv -- example GPU compute node"
FUNCTIONAL_GROUP_NAME,GROUP_NAME,SERVICE_TAG,PARENT_SERVICE_TAG,HOSTNAME,ADMIN_MAC,ADMIN_IP,BMC_MAC,BMC_IP,IB_NIC_NAME,IB_IP
slurm_node_x86_64,grp1,1T8MN34,GZF6ZS3,snode1,04:32:01:DE:18:D0,172.16.107.92,6c:3c:8c:85:be:a6,100.10.0.116,,
```

For the full format, see the
[PXE mapping file reference](../../Reference/SampleFiles/pxe_mapping_file.md).

### Step 4: Enable DCGM in telemetry_config.yml

Enable DCGM in `telemetry_config.yml`. For details on all parameters, see the [telemetry_config.yml reference](../../Reference/Configuration/telemetry_config.md).

```yaml title="telemetry_config.yml -- DCGM section"
telemetry_sources:
  dcgm:
    metrics_enabled: true
```

| Value | Result |
| --- | --- |
| `true` | Install DCGM during cloud-init provisioning |
| `false` | Skip DCGM installation |

### Step 5: Deploy the Cluster

Deploy the cluster by running the full playbook sequence
(`prepare_oim.yml` -> `local_repo.yml` -> `build_image` -> `provision.yml`). See
[Deploy the Telemetry Stack](deploy_telemetry.md).

DCGM is installed and the `nvidia-dcgm` service is automatically enabled and
started on GPU-capable nodes via cloud-init during provisioning.

!!! important

    If you enable DCGM telemetry on an already-provisioned cluster, re-run
    `provision.yml` to regenerate the node configuration and re-PXE boot the GPU
    nodes. See
    [Update Telemetry on a Running Cluster](deploy_telemetry.md#update-telemetry-on-a-running-cluster).


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


- [Setup Telemetry](setup_telemetry.md) -- Overview of all telemetry sources.


## Troubleshooting


For common telemetry issues and resolutions, see [Troubleshooting Telemetry](../../Troubleshooting/telemetry.md).
