
# Kubernetes Issues


Issues related to the Kubernetes service cluster, including control plane
initialization, pod scheduling, networking, storage, and load balancing.

## Control plane not initializing


???+ note "Symptom"

    The Kubernetes control plane fails to initialize. `kubectl get nodes`
    returns a connection error, or the `omnia.yml` playbook fails during the
    Kubernetes deployment phase.

??? note "Cause"

    - Required ports (6443, 2379-2380, 10250-10252) are blocked by a firewall.
    - The `kubelet` service failed to start.
    - Insufficient resources (CPU, memory) on the control plane node.
    - A previous Kubernetes installation was not fully cleaned up.

??? note "Resolution"

    1. Check `kubelet` status on the control plane node:

       ```bash
       ssh <kube_control_plane> systemctl status kubelet
       ssh <kube_control_plane> journalctl -u kubelet --no-pager -n 50
       ```


    2. Verify required ports are open:

       ```bash
       ssh <kube_control_plane> ss -tlnp | grep -E '6443|2379|10250'
       ```


    3. Check for leftover state from a previous installation:

       ```bash
       ssh <kube_control_plane> ls /etc/kubernetes/manifests/
       ```


       If stale files exist, reset Kubernetes:

       ```bash
       ssh <kube_control_plane> kubeadm reset -f
       ssh <kube_control_plane> rm -rf /etc/kubernetes/ /var/lib/etcd/
       ```


    4. Re-run the Omnia Kubernetes deployment:

       ```bash
       ssh omnia_core
       cd /omnia
       ansible-playbook playbooks/omnia.yml --tags kubernetes
       ```


## Pod scheduling failures


???+ note "Symptom"

    Pods remain in `Pending` state indefinitely. ``kubectl describe pod
    <pod_name>`` shows scheduling errors:

    ```text
    Warning  FailedScheduling  0/3 nodes are available: 3 node(s) had taint
    {node-role.kubernetes.io/control-plane: }, that the pod didn't tolerate.
    ```


??? note "Cause"

    - No worker nodes are available (only control plane nodes exist).
    - Worker nodes are in `NotReady` state.
    - Resource requests exceed available capacity on worker nodes.
    - Taints on nodes prevent pod scheduling.

??? note "Resolution"

    1. Check node status:

       ```bash
       kubectl get nodes
       ```


    2. If worker nodes are `NotReady`, check kubelet on those nodes:

       ```bash
       ssh <kube_worker> systemctl status kubelet
       ssh <kube_worker> journalctl -u kubelet --no-pager -n 50
       ```


    3. If only control plane nodes exist, either add worker nodes or allow
       scheduling on control planes (not recommended for production):

       ```bash
       # Add worker nodes via Omnia
       ssh omnia_core
       cd /omnia
       ansible-playbook playbooks/add_node.yml
       ```


    4. Check resource availability:

       ```bash
       kubectl describe nodes | grep -A 5 "Allocated resources"
       ```


    5. Remove problematic taints if appropriate:

       ```bash
       kubectl taint nodes <node_name> <taint_key>-
       ```


## MetalLB not assigning IP addresses


???+ note "Symptom"

    Services of type `LoadBalancer` remain in `<pending>` state and never
    receive an external IP:

    ```bash
    kubectl get svc
    # EXTERNAL-IP shows <pending>
    ```


??? note "Cause"

    - MetalLB is not deployed or its pods are not running.
    - The MetalLB IP address pool is not configured or is exhausted.
    - The MetalLB speaker pods cannot reach the network.

??? note "Resolution"

    1. Verify MetalLB pods are running:

       ```bash
       kubectl get pods -n metallb-system
       ```


    2. Check MetalLB logs:

       ```bash
       kubectl logs -n metallb-system -l app=metallb,component=controller
       kubectl logs -n metallb-system -l app=metallb,component=speaker
       ```


    3. Verify the IP address pool configuration:

       ```bash
       kubectl get ipaddresspool -n metallb-system -o yaml
       ```


       If no pool exists, create one:

       ```yaml
       apiVersion: metallb.io/v1beta1
       kind: IPAddressPool
       metadata:
         name: default-pool
         namespace: metallb-system
       spec:
         addresses:
         - 10.5.1.100-10.5.1.200
       ```


    4. Verify the L2 advertisement is configured:

       ```bash
       kubectl get l2advertisement -n metallb-system
       ```


## NFS CSI mount failures


???+ note "Symptom"

    Pods that use NFS-backed persistent volumes fail to start. ``kubectl
    describe pod`` shows mount errors:

    ```text
    Warning  FailedMount  Unable to attach or mount volumes: timed out waiting
    for the condition
    ```


??? note "Cause"

    - The NFS server is unreachable from the Kubernetes worker nodes.
    - The NFS CSI driver pods are not running.
    - The NFS export path is incorrect in the PersistentVolume definition.
    - Firewall rules block NFS traffic (ports 2049, 111).

??? note "Resolution"

    1. Verify the NFS CSI driver is running:

       ```bash
       kubectl get pods -n kube-system | grep nfs
       ```


    2. Test NFS connectivity from a worker node:

       ```bash
       ssh <kube_worker> showmount -e <nfs_server_ip>
       ```


    3. Verify the PersistentVolume configuration:

       ```bash
       kubectl get pv -o yaml | grep -A 5 nfs
       ```


    4. Check NFS firewall rules on the NFS server:

       ```bash
       ssh <nfs_server> firewall-cmd --list-all | grep -E 'nfs|2049|111'
       ```


    5. If the NFS server is unreachable, verify it is on the admin network:

       ```bash
       ssh <kube_worker> ping <nfs_server_ip>
       ```


    !!! tip

        For production environments, use the PowerScale CSI driver instead of
        external NFS. See [Deploy Powerscale Csi](../HowTo/Kubernetes/deploy_powerscale_csi.md).


## Calico networking issues


???+ note "Symptom"

    Pods cannot communicate with each other across nodes. `kubectl exec`
    into a pod and pinging another pod's IP fails. Calico pods may show errors
    in their logs.

??? note "Cause"

    - Calico pods are not running on all nodes.
    - The pod CIDR overlaps with an existing network range.
    - BGP peering is misconfigured (in BGP mode).
    - IP-in-IP or VXLAN encapsulation is blocked by network infrastructure.

??? note "Resolution"

    1. Check Calico pod status:

       ```bash
       kubectl get pods -n calico-system
       # or
       kubectl get pods -n kube-system | grep calico
       ```


    2. Check Calico node status:

       ```bash
       kubectl get nodes -o wide
       calicoctl node status    # if calicoctl is installed
       ```


    3. Verify the pod CIDR does not overlap with existing networks:

       ```bash
       kubectl cluster-info dump | grep -m 1 cluster-cidr
       ```


    4. Check Calico logs for errors:

       ```bash
       kubectl logs -n calico-system -l k8s-app=calico-node --tail=50
       ```


    5. If encapsulation is blocked, switch Calico to VXLAN mode:

       ```bash
       kubectl patch felixconfiguration default \
         --type='merge' \
         -p '{"spec":{"vxlanEnabled":true,"ipipEnabled":false}}'
       ```


!!! info

    - [Setup Service K8S](../HowTo/Kubernetes/setup_service_k8s.md) -- Kubernetes cluster setup.
    - [Configure Ha](../HowTo/Kubernetes/configure_ha.md) -- High availability configuration.
    - [Add Remove Nodes](../Operations/add_remove_nodes.md) -- Adding worker nodes.
