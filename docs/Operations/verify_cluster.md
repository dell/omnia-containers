# Verify Cluster

Verify the provisioned Slurm cluster and the Kubernetes service cluster after
their nodes boot.

## Overview

After booting the nodes, verify the following:

- Orchestrator reports a successful provisioning and, when used, PXE phase.
- Required Slurm services are active and every expected node is available to
  the scheduler.
- GPU-enabled Slurm nodes have a working driver, CUDA toolkit, and Slurm GRES
  configuration.
- The Slurm PAM feature permits an LDAP user to access a compute node only
  while that user has a running job on the node.
- The Kubernetes API is healthy, all expected nodes are `Ready`, and pods are
  `Running` or have completed successfully.

## Prerequisites

- The applicable Orchestrator provisioning flow completed. Physical nodes
  were also PXE booted and completed cloud-init.
- Slurm and/or Kubernetes were deployed. See
  [Setup Slurm](../HowTo/orchestrator/deploy_slurm.md) or
  [Setup Service K8S](../HowTo/orchestrator/deploy_kubernetes.md).
- You have root access to the cluster nodes. Run Kubernetes commands on a
  control-plane node.
- For GPU verification, GPU-enabled Slurm nodes are configured. See
  [Slurm With GPU](../HowTo/orchestrator/slurm_with_gpu.md).
- For PAM verification, the selected catalog enables OpenLDAP, the OIM-hosted
  `omnia_auth` service is running, and a test LDAP user exists. See
  [Deploy OpenLDAP](../HowTo/orchestrator/deploy_openldap.md).

## Procedure

### Verify the Orchestrator result

1. On the OIM, inspect the current project's provisioning and aggregate status:

    ```bash title="Run on: OIM"
    source /etc/profile.d/omnia-env.sh
    orchestrator_path="${OMNIA_DATA_PATH}/orchestrator"
    output_dir="$orchestrator_path/output/$OMNIA_PROJECT_NAME"

    cat "$output_dir/provisioning_report.yml"
    cat "$output_dir/orchestrator_status.yml"
    ```

    Confirm that the reports belong to the active inventory, all expected
    nodes are registered, and the completed provisioning phase reports
    `success`.

    If the PXE flow ran, also inspect its per-node result:

    ```bash title="Run on: OIM"
    cat "$output_dir/pxeboot_status.yml"
    ```

    Confirm that every intended node reports a successful PXE and
    node-registration result. When registration verification is enabled,
    Orchestrator requires a fresh boot and `cloud-init status --long` to report
    `done`.

### Verify the Slurm cluster

2. On the Slurm controller, verify the controller services:

    ```bash title="Run on: Slurm control node"
    systemctl status munge mariadb slurmdbd slurmctld
    ```

    Confirm that each service is active and running.

3. On each Slurm compute node, verify the compute services:

    ```bash title="Run on: Slurm compute node"
    systemctl status munge slurmd
    ```

4. Verify that Slurm reports every expected node and inspect the detailed state:

    ```bash title="Run on: Slurm control node"
    sinfo -N -l
    scontrol show node <compute_hostname>
    ```

    When no jobs are running, healthy compute nodes normally report `idle`.
    Nodes running jobs can report `alloc` or `mix`. Investigate expected nodes
    that are absent or in states such as `down`, `drain`, or `fail`.

### Verify Slurm with GPUs

5. On every GPU-enabled compute node, verify cloud-init, the NVIDIA driver, and
   the shared CUDA toolkit:

    ```bash title="Run on: GPU compute node"
    cloud-init status --long
    nvidia-smi
    /usr/local/cuda/bin/nvcc --version
    mountpoint /hpc_tools/cuda
    mountpoint /usr/local/cuda
    systemctl is-active slurmd
    ```

    Then confirm that Slurm reports the expected GPU resources and can run a
    GPU workload:

    ```bash title="Run on: Slurm control node"
    scontrol show node <gpu_compute_hostname> | grep -i gres
    srun --nodes=1 --gres=gpu:1 nvidia-smi
    ```

    If driver installation is still running or failed, inspect
    `/var/log/nvidia_install.log` and `/var/log/cloud-init-output.log` on the
    GPU node. Orchestrator publishes the CUDA toolkit below the selected Slurm
    storage at `slurm/hpc_tools/cuda`; GPU-enabled Slurm nodes expose it at
    `/hpc_tools/cuda` and bind it at `/usr/local/cuda`.

### Verify the Slurm PAM feature

Slurm PAM restricts compute-node SSH access for non-root users. An LDAP user
is admitted only while that user has a running job on the target node. The
configured Slurm epilog terminates the user's remaining processes and SSH
session after the job ends.

6. From a login node, verify that the LDAP user cannot access a compute node
   before a job is running:

    ```bash title="Run on: login node"
    ssh <ldap_user>@<compute_hostname>
    ```

    The connection must be denied.

7. As the same LDAP user, submit a job, wait until it is running, and identify
   its assigned compute node:

    ```bash title="Run on: login node as LDAP user"
    job_id=$(sbatch --parsable --wrap='sleep 300')
    squeue --jobs="$job_id" --format='%.18i %.2t %.20N'
    ```

    When the job state is `R`, connect to the node shown by `squeue`:

    ```bash title="Run on: login node as LDAP user"
    ssh <compute_hostname>
    ```

    The connection must succeed while the job is running. After the job ends,
    confirm that the active session is closed and a new connection is denied.

### Verify Kubernetes on the service cluster

8. As root on a Kubernetes control-plane node, select the administrator
   kubeconfig and verify the API, nodes, and pods:

    ```bash title="Run on: K8s control-plane node as root"
    test -r /root/.kube/config || export KUBECONFIG=/etc/kubernetes/admin.conf

    kubectl get --raw='/readyz?verbose'
    kubectl get nodes -o wide
    kubectl get pods -A -o wide
    ```

    Orchestrator creates `/root/.kube/config` on each control-plane node, so
    root normally does not need to export `KUBECONFIG`. When that default root
    kubeconfig is unavailable, use `/etc/kubernetes/admin.conf` from a
    privileged shell.

    Confirm that the API readiness checks return `ok`, every expected node is
    `Ready`, and workload pods are `Running`. Pods created by completed jobs
    can report `Completed` (`Succeeded`). Investigate `Pending`, `Failed`,
    `Unknown`, `CrashLoopBackOff`, and prolonged `ContainerCreating` states.

9. On every Kubernetes control-plane and worker node, verify the initialization
   marker and cloud-init status:

    ```bash title="Run on: each K8s control-plane and worker node as root"
    test -f /etc/kubernetes/.cluster_initialized && echo "Initialization marker present"
    cloud-init status --long
    ```

    Orchestrator creates `/etc/kubernetes/.cluster_initialized` on control-plane
    and worker nodes after their initial Kubernetes setup. The marker prevents
    one-time initialization or join steps from running again after a reboot.
    It records historical initialization only; it does not prove that the API,
    kubelet, node, or workloads are currently healthy. Use the checks in step 8
    for current cluster health.

## Verification

| Check | Command | Expected Result |
| --- | --- | --- |
| Orchestrator provisioning | `cat "$output_dir/orchestrator_status.yml"` | Completed provisioning phase reports `success` for the active inventory |
| Slurm controller services | `systemctl status munge mariadb slurmdbd slurmctld` | All services are `active (running)` |
| Slurm compute services | `systemctl status munge slurmd` | Both services are `active (running)` |
| Slurm nodes | `sinfo -N -l` | All expected nodes are present; unused nodes are `idle` and active nodes can be `alloc` or `mix` |
| GPU runtime | `nvidia-smi` and `srun --gres=gpu:1 nvidia-smi` | Driver responds locally and through a Slurm allocation |
| PAM access | SSH before, during, and after an LDAP user's job | Denied before and after the job; permitted on the assigned node while the job runs |
| Kubernetes API | `kubectl get --raw='/readyz?verbose'` | Readiness checks return `ok` |
| Kubernetes nodes | `kubectl get nodes -o wide` | All expected nodes are `Ready` |
| Kubernetes pods | `kubectl get pods -A -o wide` | Workloads are `Running`; completed jobs can be `Completed` |
| Kubernetes initialization history | Marker and cloud-init commands in step 9 | Marker exists and cloud-init reports `done` on every Kubernetes node |

## Troubleshooting

- **Orchestrator reports a failed or incomplete node**: Review
  `provisioning_report.yml`, `orchestrator_status.yml`, and, when PXE ran,
  `pxeboot_status.yml` before troubleshooting services on the node.
- **Slurm services are not running**: Check the controller log at
  `/var/log/slurm/slurmctld.log`, the database and `slurmdbd` services, and
  verify that munge keys are synchronized across all nodes.
- **A Slurm node is `down` or `drain`**: Inspect `slurmd`, the node reason in
  `scontrol show node <node>`, and node reachability. After correcting the
  reported cause, run `scontrol update NodeName=<node> State=RESUME`.
- **A GPU check fails**: Inspect `/var/log/nvidia_install.log` and
  `/var/log/cloud-init-output.log`, verify the CUDA mounts, and follow
  [Slurm With GPU](../HowTo/orchestrator/slurm_with_gpu.md).
- **A Kubernetes node is not ready**: Inspect `systemctl status kubelet`,
  `journalctl -u kubelet`, the CRI-O service, CNI pods, and the corresponding
  Orchestrator result.
- **A Kubernetes pod is in an unexpected state**: Run
  `kubectl describe pod <pod_name> -n <namespace>` and
  `kubectl logs <pod_name> -n <namespace> --all-containers` from the privileged
  Kubernetes shell used in step 8.
- **The initialization marker exists but Kubernetes is unhealthy**: Do not
  treat the marker as a health result or delete it as a first recovery step.
  Diagnose the API, kubelet, runtime, network, and pod state with step 8.

## Next Steps

- [Slurm With GPU](../HowTo/orchestrator/slurm_with_gpu.md) -- Configure and
  validate GPU support for Slurm.
- [Deploy OpenLDAP](../HowTo/orchestrator/deploy_openldap.md) -- Deploy and
  validate the OIM-hosted authentication service used by Slurm nodes.
