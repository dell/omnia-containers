# Kubernetes Issues

Issues related to the Kubernetes service cluster, including image pulls, pod scheduling, DNS, storage, CSI drivers, control plane join, and networking.

## ImagePullBackOff / ErrImagePull

???+ note "Symptom"

    - Pods fail to start with `ImagePullBackOff` or `ErrImagePull` status
    - Container images cannot be pulled from the local repository
    - Pod events show image pull errors

??? note "Cause"

    - Docker rate limits exceeded
    - Local repository missing required container images

??? note "Resolution"

    1. Add Docker credentials to `omnia_config_credentials.yml`.
    2. Ensure `local_repo.yml` completed successfully.

    For more information, see [Pull an Image from a Private Registry](https://kubernetes.io/docs/tasks/configure-pod-container/pull-image-private-registry/).

## Pods Not in Running State

???+ note "Symptom"

    Kubernetes pods are not in a healthy state and remain in Pending, CrashLoopBackOff, ImagePullBackOff, ErrImagePull, or OOMKilled status.

??? note "Cause"

    The pod may be affected by insufficient resources, image pull failures, unavailable storage, invalid configuration, or an unhealthy dependent service.

??? note "Resolution"

    1. Identify the pod and collect diagnostic information:

        ```bash title="Run on: K8s control plane"
        kubectl get pods -A -o wide
        kubectl describe pod <pod_name> -n <namespace>
        kubectl logs <pod_name> -n <namespace> --all-containers
        kubectl logs <pod_name> -n <namespace> --all-containers --previous
        ```

    2. Resolve the reported condition:

        **Pending**: Check node readiness, scheduling events, resource availability, and PVC status.

        ```bash title="Run on: K8s control plane"
        kubectl get nodes
        kubectl get pvc -n <namespace>
        ```

        For storage-dependent Omnia pods, verify NFS or PowerScale availability.

        **CrashLoopBackOff**: Review current and previous logs. Verify ConfigMaps, Secrets, PVC mounts, DNS, certificates, and dependent Omnia services.

        **ImagePullBackOff or ErrImagePull**: Verify the image name and tag, node access to the Pulp registry, and registry certificate trust. See Section 4.1 ImagePullBackOff / ErrImagePull.

        **OOMKilled**: Check container memory usage and limits:

        ```bash title="Run on: K8s control plane"
        kubectl top pod <pod_name> -n <namespace> --containers
        ```

    3. After correcting the root cause, restart the controller-managed workload:

        ```bash title="Run on: K8s control plane"
        kubectl rollout restart deployment/<deployment_name> -n <namespace>
        kubectl rollout status deployment/<deployment_name> -n <namespace>
        ```

    **Validation**

        ```bash title="Run on: K8s control plane"
        kubectl get pods -n <namespace> -o wide
        kubectl get events -n <namespace> --sort-by=.metadata.creationTimestamp
        ```

        Confirm that the pod becomes ready, restart counts stop increasing, PVCs remain Bound, and no new warning events appear.

## Cluster Nodes Reboot

???+ note "Symptom"

    Cluster nodes reboot unexpectedly or remain NotReady after restarting.

??? note "Cause"

    Possible causes include power or hardware faults, kernel panic, out-of-memory events, automated updates, or failure of Kubernetes, network, or storage services.

??? note "Resolution"

    1. Check the node and affected pods:

        ```bash title="Run on: K8s control plane"
        kubectl get nodes -o wide
        kubectl describe node <node_name>
        kubectl get pods -A -o wide --field-selector spec.nodeName=<node_name>
        ```

    2. On the affected node, identify the reboot cause:

        ```bash title="Run on: compute node"
        last -x | head
        journalctl -b -1 -p warning..alert --no-pager
        journalctl -k -b -1 --no-pager
        ```

    3. Verify node services and Omnia dependencies:

        ```bash title="Run on: compute node"
        systemctl --failed
        systemctl status crio kubelet --no-pager
        ```

        Also verify network connectivity, time synchronization, and required NFS or PowerScale mounts.

    4. After correcting the root cause, restart only the failed services:

        ```bash title="Run on: compute node"
        systemctl restart crio kubelet
        ```

        !!! caution

            Do not repeatedly reboot or reprovision the node before collecting the previous boot logs. Waiting alone does not resolve recurring hardware, kernel, memory, network, or storage failures.

    **Validation**

    ```bash title="Run on: K8s control plane"
    kubectl get nodes
    kubectl get pods -A -o wide
    ```

    Confirm that the node returns to Ready, its pods recover, and required storage mounts are accessible.

## DNS Unresponsive / CoreDNS Issues

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

## PowerScale SmartConnect DNS Resolution Issues

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

## Control-Plane Join Fails Due to Certificate Key Expiry

???+ note "Symptom"

    Control-plane node fails to join the cluster due to certificate key expiry.

??? note "Cause"

    The kubeadm certificate key expires after approximately 2 hours, preventing new control-plane nodes from joining the cluster.

??? note "Resolution"

    1. On a healthy control-plane, regenerate the join script:

        ```bash title="Run on: K8s control plane"
        {{ k8s_client_mount_path }}/generate-control-plane-join.sh
        ```

        !!! note

            `k8s_client_mount_path` is the `mount_point` specified in `storage_config.yml` for the NFS mount whose name matches the `nfs_storage_name` defined in the `service_k8s_cluster` section of `omnia_config.yml`.

            For example, if `nfs_storage_name: "nfs_k8s"` in `omnia_config.yml`, and in `storage_config.yml` the mount named `nfs_k8s` has `mount_point: "/opt/omnia/k8s_mount"`, then the command would be:

            ```bash
            /opt/omnia/k8s_mount/generate-control-plane-join.sh
            ```

    2. Reboot the failed node.

## Static Pods Show Stale "Running" State After Node Shutdown or Reboot

???+ note "Symptom"

    After a control plane node is powered off, shut down, or rebooted (using `systemctl poweroff`, `poweroff`, or `systemctl reboot`), static pods on the affected node may intermittently show:

    - Pod STATUS column: `1/1 Running` (appears healthy)
    - Pod Phase: `Running` (incorrect - should be Failed)
    - Pod Ready Condition: `True` or `False` (varies)
    - Container State: `running` (stale/incorrect - should be terminated)

    This is most commonly observed with `kube-apiserver` pods, but can affect all static pods (`etcd`, `kube-controller-manager`, `kube-scheduler`, `kube-vip`).

    !!! note

        This is an intermittent issue caused by a race condition. The behavior varies depending on timing - sometimes all pods show correct "Failed/Terminated" status, sometimes only certain pods (especially `kube-apiserver`) show stale "Running" status, and sometimes all pods show stale status. This inconsistency is expected and depends on shutdown timing, network conditions, and system load.

    **Example**

    ```bash title="Run on: K8s control plane"
    kubectl get pods -n kube-system | grep 172.10.5.16
    # Output shows:
    etcd-172.10.5.16                         1/1     Running   3      4h27m
    kube-apiserver-172.10.5.16               1/1     Running   3      4h27m
    kube-controller-manager-172.10.5.16      1/1     Running   3      4h26m
    kube-scheduler-172.10.5.16               1/1     Running   3      4h27m

    kubectl get node 172.10.5.16
    # Output shows:
    NAME          STATUS     ROLES           AGE     VERSION
    172.10.5.16   NotReady   control-plane   4h27m   v1.35.1
    ```

??? note "Cause"

    This is a known Kubernetes limitation with graceful node shutdown. During shutdown:

    - All critical pods receive SIGTERM simultaneously
    - Kubelet attempts to update pod status to the API server
    - Race condition occurs:
        - Fast-exiting pods (`kube-controller-manager`, `kube-scheduler`) terminate quickly and status is updated successfully
        - `kube-apiserver` takes longer to shutdown (handling final requests)
        - `kube-vip` releases the VIP before `kube-apiserver` fully terminates
        - When kubelet tries to update `kube-apiserver` container status, the API server is unreachable (VIP down or network unavailable)
        - Container state remains stale as "running"

    **Root Cause**: Circular dependency - kubelet needs the API server to update the API server's own status.

??? note "Impact"

    - No functional impact on cluster operations
    - Pod-level status may show correct Phase (Failed) and Ready (False)
    - Only container-level state remains stale
    - Cluster continues to operate normally with remaining control planes
    - Pods are properly garbage collected based on `--terminated-pod-gc-threshold` setting

??? note "Resolution"

    This behavior is expected and does not require action. The cluster continues to operate normally with the remaining control planes. When the node powers back on, pods restart automatically with incremented restart count.

    **Related Kubernetes issues:**

    - [Issue #110755](https://github.com/kubernetes/kubernetes/issues/110755) -- Kubelet doesn't finish killing pods before shutdown
    - [Issue #124448](https://github.com/kubernetes/kubernetes/issues/124448) -- GracefulNodeShutdown fails to update Pod status for system critical pods
    - [Issue #109531](https://github.com/kubernetes/kubernetes/issues/109531) -- Pods in Running/Terminating state after shutdownGracePeriod expiry

    **Official Kubernetes documentation:**

    - [Kubernetes Node Shutdowns](https://kubernetes.io/docs/concepts/cluster-administration/node-shutdown/)
    - [Kubelet Configuration Reference](https://kubernetes.io/docs/reference/config-api/kubelet-config.v1beta1/)

## NFS-Client Provisioner CrashLoopBackOff

???+ note "Symptom"

    NFS-client provisioner pod enters `CrashLoopBackOff` state.

??? note "Cause"

    NFS server not active at `server_share_path`.

??? note "Resolution"

    Ensure NFS server is active and reachable from the Kubernetes worker nodes. For NFS setup requirements, see the [NFS/Storage Prerequisites](../GetStarted/prerequisites_checklist.md#nfs--storage-prerequisites).

## PowerScale CSI Controller Issues

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

## Missing PowerScale CSI Driver

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
