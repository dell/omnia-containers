
# Deploy the Service K8s Cluster


Deploy a highly available Kubernetes service cluster for running platform
services such as telemetry, monitoring, storage provisioners, and
authentication proxies.

## Overview


The Omnia Service Kubernetes cluster provides a container orchestration layer
for platform services that support the broader HPC environment. Omnia deploys
Kubernetes with the following components pre-configured:

- **MetalLB** -- Bare-metal load balancer for exposing services with external
  IPs.
- **NFS CSI driver** -- Persistent volume provisioner backed by NFS shares.
- **Calico** -- CNI plugin for pod-to-pod networking and network policies.

The minimum topology is 3 control-plane nodes + 1 worker node for high
availability.


## Prerequisites


- Nodes are provisioned and assigned to `kube_control_plane` and
  `kube_node` functional groups in the mapping file.
- At least 3 nodes designated as `kube_control_plane` for HA (a single
  control-plane node is supported for non-production use).
- At least 1 node designated as `kube_node` (worker).
- `omnia_config.yml` is configured with Kubernetes parameters.
- Local repositories are synced (see [Create Local Repos](../Setup/create_local_repos.md)).


## Procedure


1. **Enter the omnia_core container**:

   ```bash title="Run on: OIM host"
   ssh omnia_core
   ```


2. **Configure Kubernetes parameters** in `omnia_config.yml`:

   ```bash title="Run on: omnia_core container"
   vi /opt/omnia/input/project_default/omnia_config.yml
   ```


   Key Kubernetes parameters:

   ```yaml title="File: /opt/omnia/input/project_default/omnia_config.yml"
   ---
   # Kubernetes configuration
   k8s_version: "1.28"
   k8s_cni: "calico"
   k8s_pod_network_cidr: "10.244.0.0/16"
   k8s_service_cidr: "10.96.0.0/16"

   # MetalLB IP range (must be on the same subnet as worker nodes)
   metallb_address_range: "10.5.0.220-10.5.0.240"

   # NFS CSI configuration
   nfs_server: "10.5.0.1"
   nfs_path: "/home"
   ```


3. **Verify the mapping file** has K8s node assignments:

   ```bash title="Run on: omnia_core container"
   grep -E "kube_control_plane|kube_node" /opt/omnia/input/project_default/pxe_mapping_file.csv
   ```


   You should see at least 3 `kube_control_plane` entries and 1
   `kube_node` entry.

4. **Run the omnia.yml playbook** to deploy Kubernetes:

   ```bash title="Run on: omnia_core container"
   cd /omnia
   ansible-playbook omnia.yml --ask-vault-pass
   ```


   The playbook performs the following:

   - Installs container runtime (containerd) on all K8s nodes.
   - Initializes the first control-plane node.
   - Joins additional control-plane nodes for HA.
   - Joins worker nodes.
   - Deploys MetalLB, Calico, and NFS CSI driver.
   - Configures kubeconfig for cluster administration.

   Execution time: **20-40 minutes** depending on cluster size and network
   speed.


## Verification


1. **Check Kubernetes node status**:

   ```bash title="Run on: K8s control plane node"
   kubectl get nodes -o wide
   ```


   Expected output:

   ```text title="Expected output on: K8s control plane node"
   NAME          STATUS   ROLES           AGE   VERSION    INTERNAL-IP
   k8s-cp01      Ready    control-plane   10m   v1.28.x    10.5.0.105
   k8s-cp02      Ready    control-plane   10m   v1.28.x    10.5.0.106
   k8s-cp03      Ready    control-plane   10m   v1.28.x    10.5.0.107
   k8s-worker01  Ready    <none>          10m   v1.28.x    10.5.0.108
   ```


   All nodes must show `Ready` status.

2. **Verify system pods are running**:

   ```bash title="Run on: K8s control plane node"
   kubectl get pods -A
   ```


   All pods in `kube-system`, `calico-system`, and `metallb-system`
   namespaces should be `Running`.

3. **Verify MetalLB is operational**:

   ```bash title="Run on: K8s control plane node"
   kubectl get pods -n metallb-system
   kubectl get ipaddresspool -n metallb-system
   ```


4. **Verify NFS CSI driver**:

   ```bash title="Run on: K8s control plane node"
   kubectl get pods -n kube-system | grep nfs
   kubectl get storageclass
   ```


5. **Test pod scheduling**:

   ```bash title="Run on: K8s control plane node"
   kubectl run test --image=busybox --restart=Never -- echo "K8s is working"
   kubectl logs test
   kubectl delete pod test
   ```


6. **Test a LoadBalancer service**:

   ```bash title="Run on: K8s control plane node"
   kubectl create deployment nginx --image=nginx
   kubectl expose deployment nginx --type=LoadBalancer --port=80
   kubectl get svc nginx
   ```


   The `EXTERNAL-IP` column should show an IP from the MetalLB range.

   ```bash title="Run on: K8s control plane node"
   # Cleanup
   kubectl delete svc nginx
   kubectl delete deployment nginx
   ```



## Next Steps


- [Configure Ha](configure_ha.md) -- Configure HA with virtual IP for the K8s API server.
- [Deploy Powerscale Csi](deploy_powerscale_csi.md) -- Deploy PowerScale CSI for enterprise
  storage.
- [Setup Telemetry](../Telemetry/setup_telemetry.md) -- Deploy telemetry services on
  the K8s cluster.


## Troubleshooting


**Nodes show "NotReady" status**
   Check kubelet on the affected node:

   ```bash title="Run on: affected K8s node"
   systemctl status kubelet
   journalctl -u kubelet --no-pager -n 30
   ```


**Calico pods stuck in "Pending" or "CrashLoopBackOff"**
   Check Calico logs:

   ```bash title="Run on: K8s control plane node"
   kubectl logs -n calico-system -l k8s-app=calico-node --tail=50
   ```


**MetalLB not assigning external IPs**
   Verify the IP address pool configuration:

   ```bash title="Run on: K8s control plane node"
   kubectl get ipaddresspool -n metallb-system -o yaml
   kubectl get l2advertisement -n metallb-system
   ```


**NFS CSI PersistentVolumeClaim stuck in "Pending"**
   Verify the NFS server is reachable and the export is configured:

   ```bash title="Run on: K8s worker node"
   showmount -e <nfs-server-ip>
   ```


**kubeconfig not found**
   Copy the admin kubeconfig:

   ```bash title="Run on: K8s control plane node"
   mkdir -p $HOME/.kube
   cp /etc/kubernetes/admin.conf $HOME/.kube/config
   chown $(id -u):$(id -g) $HOME/.kube/config
   ```
