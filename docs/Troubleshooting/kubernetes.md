# Kubernetes Issues

Issues related to the Kubernetes service cluster, including image pulls, pod scheduling, DNS, storage, CSI drivers, control plane join, and networking.

## ImagePullBackOff / ErrImagePull

???+ note "Symptom"

    Pods fail to start with `ImagePullBackOff` or `ErrImagePull` status.

??? note "Cause"

    - Docker rate limits exceeded.
    - Local repository missing required container images.

??? note "Resolution"

    1. Add Docker credentials to `omnia_config_credentials.yml`.
    2. Ensure `local_repo.yml` completed successfully.

## Pods not in running state

???+ note "Symptom"

    Pods are not in `Running` state. Status values observed include `Pending`, `CrashLoopBackOff`, `ImagePullBackOff`, or `OOMKilled` (visible in `kubectl describe pod` Events section).

??? note "Cause"

    Pod startup failures due to resource constraints, image pull failures, or application errors.

??? note "Resolution"

    1. Identify the failing pods:

        ```bash title="Run on: K8s control plane"
        kubectl get pods --all-namespaces
        ```

    2. Delete and allow the controller to recreate:

        ```bash title="Run on: K8s control plane"
        kubectl delete pod <pod-name> -n <namespace>
        ```

## Cluster nodes reboot

???+ note "Symptom"

    Cluster nodes reboot unexpectedly or require reboot after configuration changes.

??? note "Cause"

    - Configuration changes requiring node restart.
    - Kernel updates.
    - System instability.

??? note "Resolution"

    1. Wait 15 minutes for the node to rejoin the cluster.
    2. Verify cluster status:

        ```bash title="Run on: K8s control plane"
        kubectl get nodes
        kubectl cluster-info
        ```

## DNS unresponsive / CoreDNS issues

???+ note "Symptom"

    DNS resolution fails or CoreDNS is unresponsive in the cluster.

??? note "Cause"

    - CoreDNS pod not running.
    - DNS configuration errors.
    - Network connectivity issues.

??? note "Resolution"

    Restart CoreDNS:

    ```bash title="Run on: K8s control plane"
    kubectl rollout restart deployment coredns -n kube-system
    ```

## PowerScale SmartConnect DNS resolution issues

???+ note "Symptom"

    DNS resolution fails for PowerScale SmartConnect zone entries.

??? note "Cause"

    CoreDNS is unaware of external SmartConnect zone.

??? note "Resolution"

    1. Edit the CoreDNS ConfigMap:

        ```bash title="Run on: K8s control plane"
        kubectl -n kube-system edit configmap coredns
        ```

    2. Add a hosts block:

        ```text title="Example"
        hosts {
            10.x.x.x management.ps.com
            fallthrough
        }
        ```

    3. Restart CoreDNS:

        ```bash title="Run on: K8s control plane"
        kubectl rollout restart deployment coredns -n kube-system
        ```

## Control-plane join fails due to certificate key expiry

???+ note "Symptom"

    Control-plane node fails to join the cluster due to certificate key expiry.

??? note "Cause"

    The kubeadm certificate key expires after approximately 2 hours.

??? note "Resolution"

    1. On a healthy control-plane, regenerate the join script:

        ```bash title="Run on: K8s control plane"
        {{ k8s_client_mount_path }}/generate-control-plane-join.sh
        ```

    2. Reboot the failed node.

## Static pods show stale running state after node shutdown

???+ note "Symptom"

    After a control plane node is powered off or rebooted, static pods on the affected node may show `1/1 Running` (stale) even though the node is `NotReady`. This is most commonly observed with `kube-apiserver` pods, but can affect `etcd`, `kube-controller-manager`, `kube-scheduler`, and `kube-vip`.

    !!! note

        This is an intermittent issue caused by a race condition. The behavior varies depending on shutdown timing, network conditions, and system load.

??? note "Cause"

    During graceful shutdown, all critical pods receive SIGTERM simultaneously. A circular dependency exists: kubelet needs the API server to update the API server's own status. When the VIP is released before `kube-apiserver` fully terminates, the container state remains stale.

    **Impact**: No functional impact on cluster operations. The cluster continues to operate normally with remaining control planes. Pods are properly garbage collected based on `--terminated-pod-gc-threshold`.

??? note "Resolution"

    This behavior is expected and does not require action. When the node powers back on, pods restart automatically with incremented restart count.

    **Related Kubernetes issues:**

    - [Issue #110755](https://github.com/kubernetes/kubernetes/issues/110755) -- Kubelet doesn't finish killing pods before shutdown.
    - [Issue #124448](https://github.com/kubernetes/kubernetes/issues/124448) -- GracefulNodeShutdown fails to update Pod status.
    - [Issue #109531](https://github.com/kubernetes/kubernetes/issues/109531) -- Pods in Running/Terminating state after shutdownGracePeriod expiry.

## NFS-client provisioner CrashLoopBackOff

???+ note "Symptom"

    NFS-client provisioner pod enters `CrashLoopBackOff` state.

??? note "Cause"

    NFS server not active at `server_share_path`.

??? note "Resolution"

    Ensure NFS server is active and reachable from the Kubernetes worker nodes.

## PowerScale CSI controller issues

???+ note "Symptom"

    PowerScale (Isilon) CSI controller pod in `CrashLoopBackOff` after node reboot.

??? note "Cause"

    - CSI controller fails to reconnect to PowerScale storage after node reboot.
    - Storage connectivity issues or configuration problems.
    - PowerScale (Isilon) service unavailability.

??? note "Resolution"

    1. Inspect recent logs from the controller deployment:

        ```bash title="Run on: K8s control plane"
        kubectl logs deploy/isilon-controller -n isilon --all-containers=true | tail -n 60
        ```

    2. Restart the Isilon controller deployment:

        ```bash title="Run on: K8s control plane"
        kubectl rollout restart deployment isilon-controller -n isilon
        ```

    3. Restart the Isilon node daemonset:

        ```bash title="Run on: K8s control plane"
        kubectl rollout restart daemonset isilon-node -n isilon
        ```

## Missing PowerScale CSI driver

???+ note "Symptom"

    PowerScale CSI driver is not deployed or available in the cluster.

??? note "Cause"

    Driver not listed in `software_config.json`.

??? note "Resolution"

    1. Add the required entry to `software_config.json`:

        ```json title="Example"
        {
          "name": "csi_driver_powerscale",
          "version": "v2.17.0",
          "arch": ["x86_64"]
        }
        ```

    2. Re-run the playbook.

!!! info

    - [Setup Service K8S](../HowTo/Kubernetes/setup_service_k8s.md) -- Kubernetes cluster setup.
    - [Configure HA](../HowTo/Kubernetes/configure_ha.md) -- High availability configuration.
    - [Deploy PowerScale CSI](../HowTo/Kubernetes/deploy_powerscale_csi.md) -- PowerScale CSI driver deployment.
    - [Add Remove Nodes](../Operations/add_remove_nodes.md) -- Adding worker nodes.
